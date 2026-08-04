"""Stage 01b -- render a TSV sitting next to a page as a table.

Decision history: doc-render-engine (repo) -- Decision Log in ClickUp, blocks J4/J5/J7
and Q3/Q4/Q5/Q8/Q9. The reasoning behind every rule below lives THERE, deliberately:
this file states the contract, the log keeps the argument. An earlier version of this
docstring re-argued all of it and pushed the module to 21.7KB, one edit from failing
the size gate this engine enforces on everybody else.


WHY DATA FILES ARE ALLOWED IN THE CONTENT TREE
==============================================

"Markdown and nothing else" is a rule about MACHINERY -- no stylesheet, no config, no
nav manifest, no build script -- so the Download ZIP button hands somebody the documents
and nothing they must be told to ignore. A table of dimmer circuits is not machinery, it
IS the documentation. TSVs stay TSV on disk: spreadsheet-editable, git-diffable,
greppable, useful to anything that is not this renderer.


A DATA FILE IS A NAMED SLOT, NOT A FILENAME
===========================================

    ---
    title: Audio Inventory
    type: reference
    status: public
    summary: Every microphone, cable and rack unit the audio department owns.
    data:
      inventory_table:
        file: audio-inventory.tsv
        caption: Audio inventory
      revision_log:
        file: audio-inventory-revisions.tsv
    ---

    ## What we own

    !!! data "inventory_table"

    New staff and designers should review the [inventory table](@data:inventory_table)
    before the first production meeting.

    ## Version History

    !!! data "revision_log"
        sort: Date
        pin: Commit

⭐ The body never names a file. Swap the two filenames in the frontmatter and that body
is byte-identical between Audio, LX and Video -- the whole reason this was asked for.
Renaming a TSV is a one-line frontmatter edit, not a hunt through prose.

⚠️ SLOT NAMES BELONG TO THE TYPE. `objects/<type>.yml` lists the `data_slots` that type
may carry; an undeclared key is reported. That is what makes the shared paragraph SAFE
rather than merely conventional -- under a page-local scheme, Audio writing
`inventory_table` and Video writing `inventory` breaks the copied paragraph silently on
a page that otherwise looks fine.

⚠️ ONE FRONTMATTER FORM. A slot is always a map with `file:`; `caption:` is optional.
The shorthand `inventory_table: audio-inventory.tsv` is NOT a second legal spelling. The
old LIST form (`data: [x.tsv, y.tsv]`) is retired and reported by name, because an
ignored key looks indistinguishable from the feature never having worked.


TWO VERBS, NOT INTERCHANGEABLE
==============================

    !!! data "revision_log"                   EMBED. Block level. Draws it here.
    [the revision log](@data:revision_log)    MENTION. Inline. Links to it.

The embed carries no label: the slot name and the heading above it already say
everything a label would, so a label there is a second copy for a human to keep in
sync. The mention carries a label because a sentence needs words, and those words change
with the sentence. The label survives exactly where it does work.

`!!!` is the admonition grammar this content set already writes, so it is nothing new to
learn. This hook runs BEFORE the admonition extension sees the text; if it is ever
disabled the block degrades to a visible box naming the slot, not to silence.

⚠️ `data` is now a RESERVED admonition type. No genuine `!!! data` callout, ever again.
One-way door, taken knowingly.


OPTIONS, AND A FAILURE POSTURE THAT MATTERS MORE THAN THE OPTIONS
================================================================

    pin:     freeze this column at the left while the table scrolls sideways
    sort:    order rows by this column, WITHIN each section
    hide:    drop these columns (comma separated)
    caption: override the slot's frontmatter caption for THIS embed

⭐ AN OPTION NAMING A MISSING COLUMN IS REPORTED, NEVER SILENT. Silence was asked for
and refused. The evidence was in the content repo: a page carried a hand-written note
saying the frozen header and first column DO NOT freeze, found by accident weeks after
shipping. `pin: commitID` against a header reading `commit_id` would rebuild that bug as
policy -- a table that looks fine, scrolls wrong, and never says why. The real
requirement was "do not fail my build over a typo in a cosmetic option", which is
already the house posture: warn, render without the option, publish, report.

NOT PROVIDED: filters, totals, renames, computed columns. Those edit the data, and the
sheet is the source of truth. `hide` is allowed because dropping a column from a VIEW
does not change what the sheet says.

⚠️ `pin:` EMITS MARKUP THE STYLESHEET DOES NOT YET HONOUR. The class is on the cells;
the sticky rule is a separate commit, held until the earlier frozen-column claim is
verified on the deployed site. Shipping CSS onto an unverified mechanism is the same
silent failure one layer up.


WHAT IT UNDERSTANDS ABOUT REAL SPREADSHEETS
===========================================

  * SECTION ROWS. First cell filled, everything else empty (RACK 1, ML PANEL 2) is a
    heading inside the sheet, not a record. Renders as a spanning subheading. `sort`
    orders within each section and never across one, because sorting flat would move
    records out from under the heading that gives them meaning.
  * RAGGED WIDTH. Rows longer than the header keep their cells; the header is padded.
    Trailing columns empty in EVERY row are dropped.
  * JUNK HEADERS. A header cell that is only punctuation renders blank, not as a name.
  * BLANK ROWS are skipped.

It does NOT sort, filter, total or reinterpret on its own. The raw file publishes beside
the page, so every table offers a download link to the exact TSV it was drawn from.

🐛 AND THAT DOWNLOAD LINK WAS A 404, WHILE THE COMMENT BESIDE IT ASSERTED OTHERWISE.
It said the href "is simply its name relative to the page's own URL", which is true only
on an index page. Under `use_directory_urls: true` a page at `lighting/x.md` is served
from `lighting/x/`, while its TSV stays a sibling file at `lighting/x.tsv` -- one level
UP. So a bare filename resolved to `lighting/x/x.tsv` and downloaded nothing, on every
data page in the family. Resolved through `util.relative_url` now, the same helper that
fixed this identical class of bug in links.py, router.py and revlog.py (#41). ⚠️ Do not
go back to a bare filename, and do not count separators either -- see that function for
why the arithmetic version was wrong on exactly one page per site.

⚠️ THE TABLE CARRIES A CLASS AND THAT IS LOAD-BEARING (fixed 2026-08-03). Material
styles `.md-typeset table:not([class])` with `display: block` so wide tables can scroll.
`display: block` on a table destroys the internal table layout, and a `position: sticky`
cell inside a non-table has no row context to stick within -- so the frozen header and
frozen first column silently did nothing. The class makes `:not([class])` stop matching.
Do not remove it.
"""

from __future__ import annotations

import html
import posixpath
import re
from pathlib import Path

from . import prefixes, state
from .util import relative_url

_BLOCK = re.compile(r"^[ \t]*!!![ \t]+data[ \t]+\"(?P<slot>[^\"\n]+)\"[ \t]*$")
_OPTION = re.compile(r"^[ \t]+(?P<key>[A-Za-z_]+)[ \t]*:[ \t]*(?P<value>.*?)[ \t]*$")
_JUNK_HEADER = re.compile(r"^[\W_]+$")

_KNOWN_OPTIONS = ("pin", "sort", "hide", "caption")

#: src_uri -> {slot: {"href": ..., "anchor": bool}}. Written at stage 01b, read by
#: links.py at stage 03 to resolve an inline @data: mention. The per-page event order
#: guarantees 01b has already run for THIS page.
#:
#: `href` is resolved RELATIVE TO THE PAGE, not a bare filename -- links.py hands it
#: straight to a reader, so a wrong value here is a 404 in two places rather than one.
PLACED: dict[str, dict[str, dict]] = {}


def _norm(name) -> str:
    return re.sub(r"\s+", " ", str(name)).strip().lower()


def _read_rows(path: Path) -> list[list[str]]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return []
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.split("\t")]
        if any(cells):
            rows.append(cells)
    return rows


def _trim_columns(rows: list[list[str]]) -> list[list[str]]:
    """Pad every row to the widest, then drop columns empty throughout.

    Both halves are needed, for opposite reasons: an exported sheet has rows running
    PAST the header (real data nobody titled) and columns that exist only as trailing
    tabs. Padding first means a real value in an over-long row survives the trim.
    """
    if not rows:
        return rows
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    keep = [i for i in range(width) if any(r[i] for r in rows)]
    return [[r[i] for i in keep] for r in rows]


def _is_section(cells: list[str]) -> bool:
    return bool(cells) and bool(cells[0]) and not any(cells[1:])


def _column_index(header: list[str], wanted) -> int:
    target = _norm(wanted)
    for i, cell in enumerate(header):
        if _norm(cell) == target:
            return i
    return -1


def _sort_within_sections(body, index: int):
    """Order rows by one column, never moving a record across a section heading."""
    out: list[list[str]] = []
    block: list[list[str]] = []

    def flush():
        block.sort(key=lambda r: _norm(r[index]) if index < len(r) else "")
        out.extend(block)
        block.clear()

    for cells in body:
        if _is_section(cells):
            flush()
            out.append(cells)
            continue
        block.append(cells)
    flush()
    return out


def _header_line(header) -> str:
    return ", ".join(c for c in header if c)


def _apply_options(rows, options, slot, src, note):
    """Return (rows, pinned_index, caption_override_or_None). Reports, never raises."""
    header, body = rows[0], rows[1:]
    pinned = -1

    for key in sorted(options):
        if key not in _KNOWN_OPTIONS:
            note(
                "dead_links",
                src + ": data block '" + slot + "' sets unknown option '" + key
                + "'. Ignored. Known: " + ", ".join(_KNOWN_OPTIONS) + ".",
            )

    drop: list[int] = []
    for name in [h for h in options.get("hide", "").split(",") if h.strip()]:
        index = _column_index(header, name)
        if index < 0:
            note(
                "dead_links",
                src + ": data block '" + slot + "' hides column '" + name.strip()
                + "' which is not in the sheet. Nothing hidden. Header: "
                + _header_line(header) + ".",
            )
            continue
        drop.append(index)

    if "sort" in options:
        index = _column_index(header, options["sort"])
        if index < 0:
            note(
                "dead_links",
                src + ": data block '" + slot + "' sorts by '" + options["sort"]
                + "' which is not in the sheet. Rendered in sheet order. Header: "
                + _header_line(header) + ".",
            )
        else:
            body = _sort_within_sections(body, index)

    if "pin" in options:
        pinned = _column_index(header, options["pin"])
        if pinned < 0:
            note(
                "dead_links",
                src + ": data block '" + slot + "' pins '" + options["pin"]
                + "' which is not in the sheet. Nothing pinned. Header: "
                + _header_line(header) + ".",
            )

    if drop:
        keep = [i for i in range(len(header)) if i not in drop]
        pin_name = header[pinned] if pinned >= 0 else None
        header = [header[i] for i in keep]
        body = [
            r if _is_section(r) else [c for j, c in enumerate(r) if j in keep]
            for r in body
        ]
        # Recomputed AFTER the drop: an index taken against the full header points at
        # the wrong column once earlier columns are gone.
        pinned = _column_index(header, pin_name) if pin_name else -1

    return [header] + body, pinned, options.get("caption")


def _draw(rows, href, filename, slot, caption, pinned) -> str:
    header, body = rows[0], rows[1:]
    span = len(header)

    out = ['<div class="dr-data" id="data-' + html.escape(slot) + '">']
    if caption:
        out.append('<p class="dr-data__caption">' + html.escape(caption) + "</p>")
    # The class is required, not decorative -- see the module docstring.
    out.append('<table class="dr-data__table">')
    out.append("<thead><tr>")
    for i, cell in enumerate(header):
        label = "" if _JUNK_HEADER.match(cell) else html.escape(cell)
        klass = ' class="dr-data__pin"' if i == pinned else ""
        out.append("<th" + klass + ">" + label + "</th>")
    out.append("</tr></thead>")
    out.append("<tbody>")

    records = 0
    for cells in body:
        if _is_section(cells):
            out.append(
                '<tr class="dr-data__section"><th colspan="' + str(span) + '">'
                + html.escape(cells[0]) + "</th></tr>"
            )
            continue
        records += 1
        out.append("<tr>")
        for i, cell in enumerate(cells):
            klass = ' class="dr-data__pin"' if i == pinned else ""
            out.append("<td" + klass + ">" + html.escape(cell) + "</td>")
        out.append("</tr>")

    out.append("</tbody></table>")
    out.append(
        '<p class="dr-data__source">' + str(records) + " rows &middot; "
        + '<a href="' + html.escape(href) + '" download>' + html.escape(filename)
        + "</a></p>"
    )
    out.append("</div>")
    return "\n".join(out)


def _slots_for_type(type_name: str) -> list[str]:
    """The `data_slots` a type may carry, flattened along its `extends` chain.

    ⚠️ Walks state.TYPES itself rather than reading meta["_spec"], because
    objects._resolve merges only requires/optional/renders. Folding `data_slots` into
    that merge is the right end state and is a named follow-up; until then this is the
    one place the chain is walked twice, and it is called out here so it does not become
    the quiet second copy this module spends its docstring arguing against.
    """
    slots: list[str] = []
    decl = state.TYPES.get(type_name)
    seen: set = set()
    chain = []
    while decl and decl.get("type") not in seen:
        seen.add(decl.get("type"))
        chain.append(decl)
        parent = decl.get("extends")
        decl = state.TYPES.get(parent) if parent else None
    for decl in reversed(chain):
        for value in decl.get("data_slots") or []:
            if str(value) not in slots:
                slots.append(str(value))
    return slots


def _declared(meta: dict, src: str, note) -> dict[str, dict]:
    """Validate `data:` and return {slot: {"file":..., "caption":...}}."""
    raw = meta.get("data")
    if not raw:
        return {}

    if isinstance(raw, (list, tuple, str)):
        note(
            "duplicate_key",
            src + ": `data:` is a MAP of named slots now, not a list of filenames. The "
            + "list form is IGNORED, which looks exactly like the tables never having "
            + "worked. Rewrite as `data:` / `  <slot>:` / `    file: <name>.tsv`.",
        )
        return {}

    legal = _slots_for_type(str(meta.get("_type") or meta.get("type") or "page"))
    out: dict[str, dict] = {}

    for slot, value in raw.items():
        slot = str(slot)
        if legal and slot not in legal:
            note(
                "missing_required",
                src + ": data slot '" + slot + "' is not declared on type '"
                + str(meta.get("_type")) + "'. Declared: " + (", ".join(legal) or "none")
                + ". Add it to the type, or use the name the type already has -- a slot "
                + "spelled two ways across two pages is prose that stopped being "
                + "portable.",
            )
            continue
        if not isinstance(value, dict) or not value.get("file"):
            note(
                "missing_required",
                src + ": data slot '" + slot + "' needs a `file:` key. A slot is always "
                + "a map (`file:` required, `caption:` optional); bare "
                + "`slot: name.tsv` is not a second legal form.",
            )
            continue
        out[slot] = {
            "file": str(value.get("file")),
            "caption": str(value.get("caption") or ""),
        }
    return out


def _resolve_mention(slot: str, page, label: str):
    """Resolve an inline `[label](@data:slot)`. Returns markdown, or None to decline.

    An embedded slot resolves to its anchor on this page; a declared-but-unembedded slot
    resolves to the TSV download, which is the honest answer -- there is no table on the
    page to jump to. An unknown slot returns None and links.py renders the existing
    broken-reference marker, never a plausible-looking guess.
    """
    entry = (PLACED.get(page.file.src_uri) or {}).get(slot)
    if not entry:
        return None
    target = "#data-" + slot if entry.get("anchor") else entry["href"]
    return "[" + label + "](" + target + ")"


prefixes.claim("data", __name__, _resolve_mention)


def _collect_blocks(markdown: str):
    """Find every `!!! data` block and its indented options.

    Returns (lines, [(start, end, slot, options)]) with end EXCLUSIVE. Line-based rather
    than one regex because the options are an indented run of arbitrary length, and a
    regex spanning them is a regex nobody can read six months from now. Fenced code is
    skipped for the same reason util.sub_outside_code exists: a page DOCUMENTING this
    syntax has not placed a table.
    """
    lines = markdown.split("\n")
    found = []
    i = 0
    in_fence = False
    while i < len(lines):
        stripped = lines[i].lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            i += 1
            continue
        match = None if in_fence else _BLOCK.match(lines[i])
        if not match:
            i += 1
            continue
        start = i
        options: dict[str, str] = {}
        i += 1
        while i < len(lines):
            option = _OPTION.match(lines[i])
            if not option:
                break
            options[option.group("key").lower()] = option.group("value")
            i += 1
        found.append((start, i, match.group("slot").strip(), options))
    return lines, found


def on_page_markdown(markdown, page, config, files):
    src = page.file.src_uri
    meta = state.BY_SRC.get(src, {})
    declared = _declared(meta, src, state.note)

    lines, blocks = _collect_blocks(markdown)
    if not declared and not blocks:
        return markdown

    here = Path(page.file.abs_src_path).parent
    folder = posixpath.dirname(src)
    placed: dict[str, dict] = {}
    replacements: list[tuple[int, int, str]] = []

    def href_for(filename: str) -> str:
        """The TSV's URL as seen FROM THIS PAGE.

        🐛 Not the bare filename, which is what this used to emit. See the docstring:
        under directory URLs the page is one level deeper than its own sibling files,
        so every download link was a 404.
        """
        site_path = posixpath.join(folder, filename) if folder else filename
        return relative_url(site_path, page.file.url)

    for start, end, slot, options in blocks:
        entry = declared.get(slot)
        if not entry:
            state.note(
                "dead_links",
                src + ': !!! data "' + slot + '" names a slot that is not in this '
                + "page's `data:` frontmatter. Declared here: "
                + (", ".join(sorted(declared)) or "nothing") + ".",
            )
            replacements.append((
                start, end,
                '<p class="docrender-dead">Undeclared data slot: '
                + html.escape(slot) + "</p>",
            ))
            continue

        path = here / entry["file"]
        if not path.is_file():
            state.note(
                "missing_required",
                src + ": data slot '" + slot + "' declares file '" + entry["file"]
                + "' which does not exist beside it.",
            )
            replacements.append((
                start, end,
                '<p class="docrender-dead">Missing data file: '
                + html.escape(entry["file"]) + "</p>",
            ))
            continue

        rows = _trim_columns(_read_rows(path))
        if not rows:
            state.note(
                "notes",
                src + ": data file " + entry["file"] + " is empty or unreadable.",
            )
            replacements.append((start, end, ""))
            continue

        rows, pinned, override = _apply_options(rows, options, slot, src, state.note)
        caption = override if override is not None else entry["caption"]
        href = href_for(entry["file"])
        replacements.append(
            (start, end, _draw(rows, href, entry["file"], slot, caption, pinned))
        )
        placed[slot] = {"href": href, "anchor": True}

    embedded_slots = {b[2] for b in blocks}
    for slot, entry in declared.items():
        if slot in placed:
            continue
        # Declared and never drawn. It is NOT quietly appended at the page foot: a table
        # silently landing at the bottom of a long page is the failure nobody notices
        # for a month, and that fallback is the second legal path this rewrite removed.
        placed[slot] = {"href": href_for(entry["file"]), "anchor": False}
        if slot in embedded_slots:
            continue
        state.note(
            "missing_required",
            src + ": data slot '" + slot + "' is declared and never placed. Add "
            + '!!! data "' + slot + '" where the table belongs, or drop the slot. An '
            + "inline [mention](@data:" + slot + ") still resolves to the file "
            + "download, so this warns rather than breaking the page.",
        )

    PLACED[src] = placed

    for start, end, replacement in reversed(replacements):
        lines[start:end] = [replacement]
    return "\n".join(lines)
