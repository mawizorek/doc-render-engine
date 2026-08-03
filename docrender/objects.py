"""Hook 01 -- read every page's frontmatter, hold it to its type, and DRAW it.

This is the upgrade the whole redesign exists for. v1 had ONE page shape: every
file rendered the same way, so any structure a venue page had was structure the
author typed by hand, every time, slightly differently.

Here a page declares `type:` and objects/<type>.yml says what that kind of
thing must have, may have, and how it draws. Three consequences worth stating
plainly:

  * every space in the family gets the same spec table, because the TYPE draws
    it and not the author;
  * a missing required field is caught at build time, with the file and the
    field named;
  * adding a field to every venue is one line in one declaration, not thirty
    edits across three repos.

This is FileMaker thinking pointed at a static site. _base.yml is the parent
table, each type file is a table occurrence, requires/optional are the field
list, layout is the layout, and a page's frontmatter block is the record.

Runs FIRST, before visibility, deliberately: a page with a broken declaration
is broken whether or not it happens to be hidden today.

FAILURE POSTURE: warn, never die. v1 built with --strict and on 2026-08-01 a
single typo froze the entire live site twice in forty minutes while Pages
cheerfully kept serving a stale commit. Broken things get reported and render
as visible markers; the deploy continues.

⚠️ DUPLICATE FRONTMATTER KEYS ARE REPORTED FIRST, and the ordering is the
point. YAML resolves a duplicate silently by keeping the LAST value, so

    status: public
    status: routed

leaves the page on `status: routed`, which is not a real state, so the page is
not built and does not appear anywhere. Reporting only "status is 'routed'"
sends the author hunting for a typo they cannot see. Naming the duplicate first
points at the actual cause. Cost a real debugging round on 2026-08-03.

GENERATED CONTENT GOES IN ONE OF TWO PLACES, and which one is not a style
choice. A spec table describes the page, so it belongs at the top, under the
lede. A contents list points AWAY from the page, so it belongs at the foot,
after whatever the author had to say. Putting a list of links above the prose
turns every hub page into a menu and buries the one paragraph that explains
what the section is for.
"""

from __future__ import annotations

import re

from . import state
from .util import read_frontmatter_checked, slug_title, sub_outside_code

VALID_STATUS = {"hidden", "unlisted", "gated", "public"}

#: An `@id` reference in the body. Same shape links.py resolves, minus the
#: anchor: a page mentioned WITH an anchor is still mentioned.
_REFERENCED = re.compile(r"\]\(@(?P<token>[A-Za-z0-9_.:-]+)")


def _resolve(type_name: str) -> dict:
    """Flatten a declaration and its `extends` chain into one spec."""
    decl = state.TYPES.get(type_name)
    if not decl:
        return {}
    merged: dict = {"requires": [], "optional": [], "renders": []}
    chain, seen = [], set()
    while decl and decl.get("type") not in seen:
        seen.add(decl.get("type"))
        chain.append(decl)
        parent = decl.get("extends")
        decl = state.TYPES.get(parent) if parent else None
    for decl in reversed(chain):
        for key in ("requires", "optional", "renders"):
            for value in decl.get(key) or []:
                if value not in merged[key]:
                    merged[key].append(value)
        if decl.get("label"):
            merged["label"] = decl["label"]
    return merged


def on_files(files, config):
    seen_ids: dict[str, str] = {}

    for f in files.documentation_pages():
        meta, dupes = read_frontmatter_checked(f.abs_src_path)
        state.BY_SRC[f.src_uri] = meta

        # DUPLICATES FIRST: a duplicate is usually the REASON a later complaint
        # exists, so it has to be named before the symptom it caused.
        for key in dupes:
            state.note(
                "duplicate_key",
                f.src_uri + ": `" + key + ":` appears more than once. YAML keeps "
                + "the LAST one silently, so this page is using `" + key + ": "
                + str(meta.get(key)) + "`. Delete the line you did not mean.",
            )

        status = meta.get("status")
        if status not in VALID_STATUS:
            detail = (
                "is '" + str(status) + "', not one of " + str(sorted(VALID_STATUS))
                if status else "is missing"
            )
            state.note(
                "missing_status",
                f.src_uri + ": status " + detail + " -- PAGE WILL NOT BE BUILT, "
                + "so it is absent from the nav and every @link to it renders "
                + "as broken.",
            )

        page_id = meta.get("id")
        if page_id:
            if page_id in seen_ids:
                state.note(
                    "duplicate_id",
                    "'" + str(page_id) + "' claimed by both " + seen_ids[page_id]
                    + " and " + f.src_uri + ". Links to it are a coin flip.",
                )
            else:
                seen_ids[page_id] = f.src_uri

        type_name = meta.get("type", "page")
        if type_name not in state.TYPES:
            state.note(
                "unknown_type",
                f.src_uri + ": type '" + str(type_name) + "' is not declared. "
                + "Falling back to 'page'. Known: "
                + ", ".join(sorted(state.TYPES)),
            )
            type_name = "page"

        # `index` claims a POSITION, not a subject. The three behaviours it
        # names -- sorting first, titling the folder, being the section's
        # landing page -- all key on the filename, so on any other file the
        # declaration is simply untrue, and a reader of doc-index.json would
        # believe it. The reverse is NOT reported: an index.md is often
        # legitimately typed as its subject.
        if type_name == "index" and f.name != "index":
            state.note(
                "notes",
                f.src_uri + ": type 'index' on a file that is not an index page. "
                + "The section behaviours it implies all key on the FILENAME, so "
                + "nothing here sorts first or titles a folder. Rename the file "
                + "to index.md, or type this page as what it is about.",
            )

        spec = _resolve(type_name)
        missing = [k for k in spec.get("requires", []) if not meta.get(k)]
        if missing:
            state.note(
                "missing_required",
                f.src_uri + " (type: " + type_name + ") is missing required "
                + ", ".join(missing),
            )

        meta["_type"] = type_name
        meta["_spec"] = spec

    return files


def _spec_table(meta: dict, fields: list[str]) -> str:
    rows = []
    for field in fields:
        value = meta.get(field)
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        rows.append("| " + slug_title(field) + " | " + str(value) + " |")
    if not rows:
        return ""
    return "\n".join(
        ['<div class="dr-spec" markdown="1">', "", "| | |", "| --- | --- |"]
        + rows + ["", "</div>", ""]
    )


def _referenced_ids(markdown: str) -> set[str]:
    """Every id the body already links, ignoring code.

    Routed through sub_outside_code for the reason that function exists: a page
    DOCUMENTING `[Main Stage](@main-stage)` inside a fence has not filed Main
    Stage anywhere, and reading its example as a real reference would hide a
    genuinely unfiled page. The substitution here returns each match unchanged;
    it is a code-aware scan wearing a rewriter's clothes.
    """
    found: set[str] = set()

    def collect(match):
        found.add(match.group("token"))
        return match.group(0)

    sub_outside_code(_REFERENCED, collect, markdown)
    return found


def _child_list(page, markdown: str) -> str:
    """The pages directly beneath this one that the body has not mentioned.

    WHY THE REMAINDER AND NOT EVERYTHING. A good index page is prose: it says
    what the section is for and links its pages with a line each on why you
    would read them. Drawing the full list under that duplicates every link and
    trains people to skip the writing. Drawing what is LEFT does the opposite --
    a curated index renders no list at all, and the moment somebody adds a file
    without filing it, it appears here until they do. The gap becomes visible
    instead of staying silent, which is the same bargain callout_if_missing
    makes on a page with an undocumented field.

    DIRECT CHILDREN ONLY: a file in this folder, or the landing page of a folder
    one level down. Anything deeper belongs to THAT index, and hoisting it here
    would flatten the tree the sidebar just spent a hook arranging.

    THREE WAYS A PAGE STAYS OUT OF THIS LIST, and they are not the same lever:

        status: unlisted   out of the sidebar, out of search, out of here
        listed: false      IN the sidebar and search, out of here only
        a link in the body it is filed already, so it is not a loose end
    """
    src = page.file.src_uri
    folder = src.rpartition("/")[0]
    prefix = folder + "/" if folder else ""

    referenced = _referenced_ids(markdown)
    entries, suppressed = [], False

    for other, meta in state.BY_SRC.items():
        if other == src or not other.startswith(prefix):
            continue
        rest = other[len(prefix):]
        if "/" in rest and not (
            rest.count("/") == 1 and rest.endswith("/index.md")
        ):
            continue

        page_id = meta.get("id")
        if not page_id:
            continue

        # `is False` and not falsy: `listed: 0` is not a thing anybody means,
        # and an absent key must not read as an opt out.
        if meta.get("listed") is False:
            continue

        # state.PAGES is the PUBLISHED map: links.py fills it after visibility
        # has already pruned, so a page absent from it was never built and a
        # link to it would render as a broken marker. `unlisted` is a
        # deliberate absence from navigation, and this is navigation.
        published = state.PAGES.get(page_id)
        if not published or published.get("status") != "public":
            continue

        if page_id in referenced:
            suppressed = True
            continue

        order = meta.get("order")
        title = str(meta.get("title") or slug_title(page_id))
        entries.append(
            (order if isinstance(order, int) else 10_000, title.lower(), title, page_id)
        )

    if not entries:
        return ""

    # Same key instance.py sorts the sidebar by. Two orders for the same set of
    # pages on the same screen is the sort of disagreement nobody reports and
    # everybody notices.
    entries.sort()

    # "Also" means YOUR PROSE ALREADY COVERED SOME OF THESE, so it is set only
    # by a body link. A page that opted out with `listed: false` was never part
    # of the set and must not change the wording.
    heading = "## Also in this section" if suppressed else "## In this section"
    lines = [heading, ""]
    for _, _, title, page_id in entries:
        lines.append("- [" + title + "](@" + page_id + ")")
    return "\n".join(lines)


def _insert_after_lede(markdown: str, block: str) -> str:
    """Place generated content after the H1 and its opening paragraph.

    The first paragraph is the lede and is also what a search result shows, so
    nothing generated may come before it. Anything we cannot parse confidently
    goes at the top instead of guessing wrong and splitting a sentence.
    """
    lines = markdown.splitlines()
    heading = next((i for i, ln in enumerate(lines) if ln.startswith("# ")), None)
    if heading is None:
        return block + "\n" + markdown
    i = heading + 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    while i < len(lines) and lines[i].strip():
        i += 1
    return "\n".join(lines[:i] + ["", block] + lines[i:])


def _wants_children(meta: dict, renders: list) -> bool:
    """Does this page draw a contents list.

    Two ways in, because the ROLE and the LAYOUT are not the same question. A
    type declares `child_list` because pointing at its children is what that
    kind of page is for; `contents: auto` lets a page that is primarily about
    something else -- a building whose rooms are files under it -- borrow the
    behaviour without lying about its type. `contents: false` is the opt out,
    and it wins, since a page saying no is the least ambiguous signal here.

    Not to be confused with `listed:`, which is the other end of the same
    relationship: `contents:` is a PARENT deciding whether to draw a list at
    all, `listed:` is a CHILD deciding whether to appear in one.
    """
    contents = meta.get("contents")
    if contents is False:
        return False
    if isinstance(contents, str) and contents.strip().lower() == "auto":
        return True
    return any("child_list" in d for d in renders)


def on_page_markdown(markdown, page, config, files):
    """Draw whatever the page's type declares.

    Three directives are implemented:

        spec_table: [a, b, c]      a two-column table of those fields
        callout_if_missing: [a]    a visible note naming what is not known yet
        child_list: []            the section contents, at the FOOT of the page

    The second is the quiet one that earns its place. A venue page missing its
    grid height looks identical to a venue that genuinely has no grid. Saying
    'this is not documented yet' out loud turns a silent gap into a visible one,
    which is the only way it ever gets filled.

    `child_list` takes no field list and is read as a flag, because unlike the
    other two it cannot be drawn from frontmatter alone: it needs the whole
    page. It emits `@id` links rather than paths, so stage 03 resolves them by
    the same rules as hand-written ones -- including reporting one as dead if a
    page it lists somehow fails to publish.
    """
    meta = state.BY_SRC.get(page.file.src_uri, {})
    spec = meta.get("_spec") or {}
    renders = [d for d in spec.get("renders", []) if isinstance(d, dict)]
    blocks = []

    for directive in renders:
        for name, fields in directive.items():
            if name == "spec_table":
                table = _spec_table(meta, list(fields or []))
                if table:
                    blocks.append(table)
            elif name == "callout_if_missing":
                absent = [f for f in (fields or []) if not meta.get(f)]
                if absent:
                    blocks.append(
                        '!!! note "Not documented yet"\n\n    '
                        + ", ".join(slug_title(a) for a in absent)
                        + " for this page "
                        + ("has" if len(absent) == 1 else "have")
                        + " not been recorded. Treat as unknown, not as absent."
                    )

    # Read from the ORIGINAL body, before anything is inserted into it, so a
    # generated block can never be mistaken for something the author wrote.
    listing = _child_list(page, markdown) if _wants_children(meta, renders) else ""

    if blocks:
        markdown = _insert_after_lede(markdown, "\n\n".join(blocks))
    if listing:
        markdown = markdown.rstrip() + "\n\n" + listing + "\n"
    return markdown
