"""The build report, and the page that renders it. ONE renderer, N destinations.

WHAT MOVED HERE, AND WHY (2026-08-07). Michael: *"can the build report render
into a new UTILITY page on the site now?"*

The report was job 3 of `sizecheck.py`, where it lived as a `print()` loop with
its section list welded to it. That was fine while stdout was the only reader. It
stopped being fine the moment a second destination appeared, because a report
BUILT INSIDE ITS PRINTER cannot be rendered anywhere else without being written a
second time -- and two renderers of one object disagree within a month. This repo
has retired `roster.json`, `registry.json` and `app-index.md` for exactly that
shape, and `specs/scoped-theme.md` named this split as the thing to do first for
exactly that reason.

So `_LABELS` and `_INVENTORY` live here now, `sections()` is the single ordered
walk, and both renderers below call it. `sizecheck.py` keeps the size budget and
the leak scan -- those are CHECKS, not reports -- and prints what this returns.

⚠️ `_LABELS` STILL SETS THE PRINT ORDER, AND ADDING A SECTION IS STILL TWO EDITS.
Moving the dict between files changes nothing about that: `state.reset()` declares
the bucket, this file gives it a label and therefore a place in the walk. A bucket
declared in one and not the other is collected all build and dropped without a
word -- a check that runs, finds things, and tells nobody. The warning is in both
files; only the second address changed.


THE PAGE
========

    !!! report

One line in a content page, the same directive grammar as `!!! tokens` on the
theme audit. ⭐ THE PAGE IS AUTHORED AND ONLY THE BLOCK IS GENERATED, which is
deliberately NOT the `File.generated` design the spec sketched. An authored page
carries its own `status:`, takes its normal place behind the router, and can put
prose around the block explaining how to read it. A generated file can do none of
those things, and all three turned out to matter more than never touching the
content repo.


🔴 IT IS SUBSTITUTED AFTER THE BUILD, NOT RENDERED INTO THE MARKDOWN
====================================================================
The report is not finished until `on_post_build`. Every other `!!!` directive in
this engine draws something already known before a page renders -- the token audit
reads the theme, a data table reads a TSV. This one reads an ACCUMULATOR that is
still filling while the page is being written.

Rendering it at `on_page_markdown` would therefore emit a report missing every
finding from every page not yet walked, plus the whole of hook 08's own size
budget and leak scan. **And it would look completely correct.** A silently partial
report is worse than none, because it is the one document nobody thinks to doubt.

So `on_page_markdown` swaps the directive for an inert HTML comment, and
`on_post_build` -- registered AFTER hook 08 -- reads the built file back off disk
and replaces the comment with the finished thing.

⚠️ THAT ORDERING IS FORCED, NOT CHOSEN, and it is why the markdown swap happens so
late in the chain. MkDocs dispatches every event in hook-list order, so a stage
registered early enough to rewrite markdown early would ALSO run its
`on_post_build` before hook 08 had scanned anything. One registration, one
position, and the post-build end is the end that matters.

⭐ AND THE LATE SUBSTITUTION BUYS A SECOND THING WORTH MORE THAN IT COST. The
report is full of syntax this engine resolves: `@id` tokens, `{.tbc}` markers,
`!!! data` slot names, backticks, underscored filenames. Injected as MARKDOWN it
would be re-processed -- links.py trying to resolve a dead reference the report is
COMPLAINING about, markers.py painting a marker it is merely QUOTING, a path with
underscores coming out italic. Substituting into finished HTML means the report is
quoted, never executed, and escaped exactly once, by us.

⚠️ THE HEADINGS ARE ABSENT FROM THE TABLE OF CONTENTS, and that is the price. The
toc is built when the markdown is converted, which is long before this runs, so
Material's right-hand rail lists only the headings the author typed. Stated rather
than fixed: the alternative is emitting the report early and wrong.

🚫 NOTHING IS NOTED WHEN THE BLOCK RENDERS, DELIBERATELY. A `notes` entry saying
"this page drew the report" would appear in the report, on that page, on every
build -- and `notes` is not inventory, so the site would never print "No findings"
again. That is the `nav_default` lesson one bucket over: a signal that can never be
clean is not a signal.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from . import state

#: `!!! report`, alone on its line, with an optional quoted title that is
#: ignored. Deliberately the same shape as `tokenaudit._BLOCK`: one directive
#: grammar, learned once, and a reader who knows the audit page knows this one.
_BLOCK = re.compile(r"(?m)^!!![ \t]+report[ \t]*(?:\"[^\"]*\")?[ \t]*$")

#: What the directive leaves behind for `on_post_build` to find.
#:
#: An HTML COMMENT because Python-Markdown passes a block-level comment through
#: untouched, and because nothing downstream -- links, markers, the router, the
#: search indexer -- has any reason to look inside one. A `<div>` would have been
#: styled, indexed and possibly rewritten on the way past.
_MARK = "<!--dr-report-->"

#: Built output paths that carried the directive this build, keyed by
#: `abs_dest_path` -> src_uri.
#:
#: ⭐ ABS_DEST_PATH SO NOTHING RECOMPUTES A PATH MKDOCS ALREADY KNOWS. Every url
#: bug this engine has shipped came from redoing that arithmetic by hand -- see
#: util.relative_url for the root-index case and router.py for the sealed-url
#: one. MkDocs decided where it put the file; asking it is free.
#:
#: A module global rather than an entry in `state.py`, per that file's own
#: admission rule: its writer and its reader are both in HERE, so it is not
#: shared state, it is this module's business.
_PENDING: dict = {}

#: Buckets that are inventory, not defects. Present in the report, ignored when
#: deciding whether the build was clean.
#:
#: ⚠️ `nav_default` IS IN HERE AND HAS TO BE. It reports on EVERY build -- the
#: site default is always either declared or absent, and both are worth stating.
#: Counting it as a finding would mean no build on any site ever prints "No
#: findings" again, and a clean signal that can never fire is worse than none.
#:
#: ⚠️ `aliases` IS IN HERE FOR THE SAME REASON, added 2026-08-05. It also reports
#: on every build: a site either declares alternate names or it does not, and
#: "none declared" is a useful thing to read rather than a complaint.
_INVENTORY = {"markers", "routers", "nav_default", "aliases"}

#: ⭐ SECTION ORDER IS CAUSE-BEFORE-SYMPTOM, AND IT IS SET HERE. A duplicate
#: frontmatter KEY leads the page-level findings because it is usually the reason
#: for everything under it: a page with two `status:` lines silently uses the
#: second, so it is not built, so it is missing from the nav, so every link to it
#: renders broken -- three complaints, one cause, and only one of them worth
#: reading first.
#:
#: `leaks` is first of all, because a site name in engine code FAILS THE BUILD.
#:
#: ⚠️ THE WALK ITERATES THIS DICT, NOT `state.REPORT`. Reordering the dict in
#: state.py moves nothing; that file says so about itself.
_LABELS = {
    "leaks": "SITE NAME LEAKED INTO ENGINE CODE (build will fail)",
    "duplicate_key": "DUPLICATE FRONTMATTER KEYS -- read these first, they "
                     "usually explain everything below",
    "missing_status": "Pages with no usable status (NOT BUILT)",
    "missing_required": "Missing required fields",
    "body_lede": "Lede in the wrong place -- `summary:` is the lede now, and "
                 "these pages have it somewhere else (or nowhere)",
    # Beside body_lede because it is the same migration one field over. NOT
    # inventory: every entry is a page printing its revision date twice, or a
    # date the engine cannot see.
    "body_revised": "Revision date in the wrong place -- `revised:` is drawn "
                    "at the foot now, and these pages still type it into the "
                    "body",
    "unknown_type": "Undeclared types (fell back to 'page')",
    "duplicate_id": "Duplicate ids",
    "dead_links": "Broken references (rendered as visible markers)",
    "stale_xref": "Cross-site index problems",
    "markers": "Marked unresolved -- every tbc / verify / gap / conf / est / was",
    "nav_default": "SIDEBAR DEFAULT for this site -- `nav:` on the root "
                   "index.md, and what every folder inherits from it",
    "aliases": "NAMES THIS SITE ANSWERS TO -- what `publish <name>` accepts",
    "routers": "Routers on this site",
    "oversize": "Over the size budget",
    "notes": "Notes",
}


def sections() -> list:
    """The report as DATA: every non-empty bucket, in print order, once.

    ⭐ THE ONE WALK, and the reason this function exists at all. Both renderers
    below call it and neither iterates `_LABELS` itself, which makes "the page
    and the log cannot disagree" a property of the code rather than a promise in
    a comment. A third destination -- the Actions step summary, BUILD 2 Piece A
    -- is a third caller and nothing else.

    Each entry is `(bucket, label, entries, is_inventory)`. The list is COPIED
    because a renderer must not be able to mutate the report it is describing.
    """
    found = []
    for bucket, label in _LABELS.items():
        entries = state.REPORT.get(bucket) or []
        if entries:
            found.append((bucket, label, list(entries), bucket in _INVENTORY))
    return found


def is_clean(found: list) -> bool:
    """A build is clean when nothing but INVENTORY reported."""
    return not any(not inventory for _, _, _, inventory in found)


def as_text() -> str:
    """The console block. Byte-for-byte what hook 08 has always printed.

    Returned rather than printed, and the caller prints it. That is the whole
    move: a function that prints has one destination forever.

    ⚠️ NO TRAILING NEWLINE. The list opens and closes with an empty string, so
    `print(as_text())` reproduces the old output exactly -- blank line, rule,
    body, rule, blank line. Adding one here would double the last gap.
    """
    name = str(state.INSTANCE.get("name", "?"))
    slug = str(state.INSTANCE.get("slug", "?"))
    rule = "=" * 72
    found = sections()

    lines = ["", rule, "docrender build report -- " + name + " (" + slug + ")", rule]

    for _bucket, label, entries, _inventory in found:
        lines.append("")
        lines.append(label + " (" + str(len(entries)) + ")")
        lines.extend("  - " + entry for entry in entries)

    lines.append("")
    lines.append("Pages published: " + str(len(state.PAGES)))
    lines.append("Peer indexes loaded: " + (", ".join(sorted(state.PEERS)) or "none"))
    if is_clean(found):
        lines.append("No findings. Everything declared, everything resolved.")
    lines.append(rule)
    lines.append("")
    return "\n".join(lines)


def as_html() -> str:
    """The same report, as FINISHED html for the page.

    ⚠️ EVERY ENTRY IS ESCAPED. A report entry is quoted source: it contains the
    angle brackets, ampersands and quotes of the thing it is complaining about,
    and one unescaped `<span` in a dead-link message would close the document
    early. `html.escape` here is the only escaping in the path, because nothing
    downstream touches this string.

    ⚠️ CLASSES BUT NO STYLESHEET, and that is on purpose rather than unfinished.
    Sections, headings and lists are what Material already styles well; the
    `dr-report` classes are the hook for a later sheet, not a promise of one.
    The same call figure.py made, and for the same reason: a rule nobody needed
    yet is a rule that rots before its first reader.
    """
    found = sections()
    esc = html.escape
    parts = ['<div class="dr-report">']

    if is_clean(found):
        parts.append(
            '<p class="dr-report__clean">No findings. Everything declared, '
            "everything resolved.</p>"
        )

    for bucket, label, entries, inventory in found:
        parts.append(
            '<section class="dr-report__section" id="report-' + esc(bucket)
            + '" data-dr-report="' + ("inventory" if inventory else "finding")
            + '">'
        )
        parts.append(
            "<h2>" + esc(label) + " <small>(" + str(len(entries)) + ")</small></h2>"
        )
        parts.append("<ul>")
        parts.extend("<li>" + esc(entry) + "</li>" for entry in entries)
        parts.append("</ul>")
        parts.append("</section>")

    parts.append(
        '<p class="dr-report__footer">Pages published: '
        + str(len(state.PAGES)) + ". Peer indexes loaded: "
        + esc(", ".join(sorted(state.PEERS)) or "none") + ".</p>"
    )
    parts.append("</div>")
    return "\n".join(parts)


def on_files(files, config):
    """Per-build reset, the same job `state.reset()` does for shared state.

    `mkdocs serve` rebuilds in-process, so a module global outlives the build
    that filled it. Cheap insurance against a stale path from a previous save
    being rewritten -- and against the spurious warning that would follow it.
    """
    _PENDING.clear()
    return files


def on_page_markdown(markdown, page, config, files):
    """Swap the directive for the marker, and remember where the page landed."""
    if not _BLOCK.search(markdown):
        return markdown
    _PENDING[page.file.abs_dest_path] = page.file.src_uri
    return _BLOCK.sub(_MARK, markdown)


def on_post_build(config):
    """Read each built page back and substitute the finished report into it.

    ⚠️ THESE FAILURES PRINT INSTEAD OF CALLING `state.note`, AND THAT IS NOT AN
    OVERSIGHT. Hook 08 has already printed the report by the time this runs, so a
    note added here would be collected into a bucket nobody reads again -- the
    exact 'check that runs, finds things, and tells nobody' shape the bucket
    warning exists to prevent. An Actions warning annotation is the surface that
    still works this late.

    ⚠️ AND A LEAK FAILURE IN 08 RAISES BEFORE THIS RUNS, so the page keeps its
    marker. Correct: the build failed and nothing deploys. The marker is an HTML
    comment, so even a page served from that output shows an empty slot rather
    than debris.
    """
    if not _PENDING:
        return

    block = as_html()

    for dest, src in list(_PENDING.items()):
        path = Path(dest)
        try:
            built = path.read_text(encoding="utf-8")
        except OSError as exc:
            print(
                "::warning::docrender: " + src + " asked for the build report, "
                "and its built page could not be read back (" + str(exc)
                + "). The page shipped with an empty slot."
            )
            continue

        if _MARK not in built:
            print(
                "::warning::docrender: " + src + " asked for the build report, "
                "and the marker did not survive into the html. The directive "
                "must start its own line with a blank line either side -- "
                "indented, it is part of the block above it."
            )
            continue

        try:
            path.write_text(built.replace(_MARK, block), encoding="utf-8")
        except OSError as exc:
            print(
                "::warning::docrender: " + src + " built correctly, but the "
                "report could not be written into it (" + str(exc) + ")."
            )

    _PENDING.clear()
