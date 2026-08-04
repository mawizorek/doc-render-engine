"""Stage 01b -- render a TSV sitting next to a page as a table.

Decision history: doc-render-engine (repo) Decision Log in ClickUp, blocks J4/J5/J7/J17
and Q3/Q4/Q5/Q8/Q9. **The argument lives THERE; this file states the contract.** That
split is not a style preference -- this docstring has twice grown until the module
failed the size gate it enforces on everybody else.


WHY DATA FILES ARE ALLOWED IN THE CONTENT TREE
==============================================

"Markdown and nothing else" is a rule about MACHINERY -- no stylesheet, no config, no
nav manifest, no build script -- so the Download ZIP hands somebody the documents and
nothing they must be told to ignore. A table of dimmer circuits is not machinery, it IS
the documentation. TSVs stay TSV on disk: spreadsheet-editable, git-diffable, greppable.


THE CONTRACT
============

    ---
    type: reference
    data:
      inventory_table:
        file: audio-inventory.tsv
        caption: Audio inventory          # optional
    ---

    !!! data "inventory_table"            EMBED. Block level. Draws it here.
        sort: Count                       options, indented
        pin: ID
        hide: internal_notes
        caption: ...                      overrides the frontmatter one

    ...or [the inventory](@data:inventory_table)   MENTION. Inline. Links to it.

⭐ The body never names a FILE, only a SLOT. Swap the filenames in the frontmatter and
the body is byte-identical between Audio, LX and Video -- the whole reason this exists.

⚠️ Slot names belong to the TYPE (`objects/<type>.yml` → `data_slots`); an undeclared key
is reported. That is what makes a copied paragraph safe rather than merely conventional.

⚠️ ONE FRONTMATTER FORM. A slot is always a map with `file:`. Neither `slot: name.tsv`
nor the old `data: [x.tsv]` list is a second legal spelling; the list form is reported by
name, because an ignored key looks exactly like the feature never having worked.

⚠️ The embed carries NO label -- the slot name and the heading above it already say it,
and a label there is a second copy to keep in sync. The mention carries one because a
sentence needs words. `data` is now a reserved admonition type; no genuine `!!! data`
callout, ever again.


EVERY CELL IS PROSE
===================

    Grid height	[18'-0"]{.est}		measured off the old plot
    Console	[QL5](@term:yamaha-ql5)	1	**do not** repatch

A cell says anything a line of body text can say inline -- markers, `@` page/peer refs,
`@term:`, `@data:`, bold, emphasis, code -- and renders identically, because
`docrender/cells.py` hands it to the same hooks the page body goes through. **Read that
module before changing this one:** it carries the escaping order, the reason markers in
cells used to emerge as entity gibberish, and the limits (no block markdown, raw HTML
trusted).

⭐ MARKUP CANNOT REORDER A SHEET, which was the one non-negotiable. `sort:` orders on
`cells.plain()` and orders NUMERICALLY when every value in the column is a number, so
`[18'-0"]{.est}` sorts as `18'-0"` and `10` sorts after `9`.

⚠️ A SPREADSHEET CANNOT DO THIS and nothing here can fix it: any non-digit in a cell
makes it text to Excel and Numbers. A separate confidence COLUMN is still the end state
(J17); in-cell marking ships because that column needs a FileMaker field to feed it.


FAILURE POSTURE, WHICH MATTERS MORE THAN THE OPTIONS
====================================================

⭐ AN OPTION NAMING A MISSING COLUMN IS REPORTED, NEVER SILENT. Silence was asked for and
refused, on the evidence of a page in the content repo carrying a hand-written note that
the frozen header and first column DO NOT freeze -- found by accident, weeks late.
`pin: commitID` against a header reading `commit_id` would rebuild that bug as policy.
The real requirement was "do not fail my build over a typo in a cosmetic option", which
is the house posture already: warn, render without the option, publish, report.

NOT PROVIDED: filters, totals, renames, computed columns. Those edit the data and the
sheet is the source of truth. `hide` is allowed because dropping a column from a VIEW
does not change what the sheet says.

⚠️ `pin:` EMITS MARKUP THE STYLESHEET DOES NOT YET HONOUR. The class is on the cells; the
sticky rule is held until the older frozen-column claim is verified on the deployed site.
Shipping CSS onto an unverified mechanism is the same silent failure one layer up.


WHAT IT UNDERSTANDS ABOUT REAL SPREADSHEETS
===========================================

  * SECTION ROWS. First cell filled, everything else empty (RACK 1, ML PANEL 2) is a
    heading inside the sheet, not a record. Renders as a spanning subheading, and `sort`
    orders WITHIN each one -- sorting flat would move records out from under the heading
    that gives them meaning.
  * RAGGED WIDTH. Rows longer than the header keep their cells; the header is padded.
    Trailing columns empty in EVERY row are dropped.
  * JUNK HEADERS. A header cell that is only punctuation renders blank, not as a name.
  * BLANK ROWS are skipped.

🐛 The download link was a 404 on every non-index page until 2026-08-04 while the comment
beside it asserted a bare filename was correct: under `use_directory_urls` a page at
`lighting/x.md` serves from `lighting/x/` while its TSV stays a sibling at
`lighting/x.tsv`. It goes through `util.relative_url` now -- the helper that fixed the
same class of bug in links.py, router.py and revlog.py. Do not go back to a bare
filename, and do not count separators either.

⚠️ THE TABLE CARRIES A CLASS AND THAT IS LOAD-BEARING (2026-08-03). Material styles
`.md-typeset table:not([class])` with `display: block` so wide tables can scroll.
`display: block` destroys the internal table layout, and a `position: sticky` cell inside
a non-table has no row context to stick within -- so the frozen header and first column
silently did nothing. The class makes `:not([class])` stop matching. Do not remove it.
"""

from __future__ import annotations

import html
import posixpath
import re
from pathlib import Path

from . import cells, prefixes, state
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
    """Loose comparison key for a COLUMN NAME.

    Runs through cells.plain first, so `**Count**` in a header still matches
    `sort: count`. An option names what a reader sees, not what the author typed.
    """
    return re.sub(r"\s+", " ", cells.plain(name)).strip().lower()


def _read_rows(path: Path) -> list[list[str]]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return []
    rows = []
    for line in text.splitlines():
        row = [c.strip() for c in line.split("\t")]
        if any(row):
            rows.append(row)
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


def _is_section(row: list[str]) -> bool:
    return bool(row) and bool(row[0]) and not any(row[1:])


def _column_index(header: list[str], wanted) -> int:
    target = _norm(wanted)
    for i, cell in enumerate(header):
        if _norm(cell) == target:
            return i
    return -1


def _sort_within_sections(body, index: int):
    """Order rows by one column, never moving a record across a section heading.

    ⚠️ Two things this deliberately does NOT do.

    It does not sort on the raw cell: a marked or linked value sorts on `cells.plain()`,
    so markup cannot reorder a sheet. That was the constraint the whole in-cell-prose
    feature had to satisfy.

    It does not sort numbers as text unless it has to. A column whose every value is a
    number sorts numerically -- otherwise `10` lands before `9`, which is the kind of
    wrong nobody reports because it looks like an ordering choice.
    """
    records = [r for r in body if not _is_section(r)]
    values = [cells.plain(r[index]) for r in records if index < len(r)]
    numeric = bool(values) and all(
        cells.number(v) is not None for v in values if v
    )

    def key(row):
        text = cells.plain(row[index] if index < len(row) else "")
        if not text:
            # Blanks last in both modes. A blank is "nobody has said", and floating it to
            # the top of every section buries the rows that carry data.
            return (1, 0.0, "")
        if numeric:
            return (0, cells.number(text) or 0.0, "")
        return (0, 0.0, text.lower())

    out: list[list[str]] = []
    block: list[list[str]] = []

    def flush():
        block.sort(key=key)
        out.extend(block)
        block.clear()

    for row in body:
        if _is_section(row):
            flush()
            out.append(row)
            continue
        block.append(row)
    flush()
    return out


def _header_line(header) -> str:
    return ", ".join(cells.plain(c) for c in header if c)


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


def _draw(rows, href, filename, slot, caption, pinned, page) -> str:
    """The table as finished HTML. Every cell goes through cells.render exactly once."""
    header, body = rows[0], rows[1:]
    span = len(header)

    out = ['<div class="dr-data" id="data-' + html.escape(slot) + '">']
    if caption:
        out.append(
            '<p class="dr-data__caption">' + cells.render(caption, page) + "</p>"
        )
    # The class is required, not decorative -- see the module docstring.
    out.append('<table class="dr-data__table">')
    out.append("<thead><tr>")
    for i, cell in enumerate(header):
        label = "" if _JUNK_HEADER.match(cell) else cells.render(cell, page)
        klass = ' class="dr-data__pin"' if i == pinned else ""
        out.append("<th" + klass + ">" + label + "</th>")
    out.append("</tr></thead>")
    out.append("<tbody>")

    records = 0
    for row in body:
        if _is_section(row):
            out.append(
                '<tr class="dr-data__section"><th colspan="' + str(span) + '">'
                + cells.render(row[0], page) + "</th></tr>"
            )
            continue
        records += 1
        out.append("<tr>")
        for i, cell in enumerate(row):
            klass = ' class="dr-data__pin"' if i == pinned else ""
            out.append("<td" + klass + ">" + cells.render(cell, page) + "</td>")
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
    replacements: list[tuple[int, int, str]] = []

    def href_for(filename: str) -> str:
        """The TSV's URL as seen FROM THIS PAGE.

        🐛 Not the bare filename, which is what this used to emit. See the docstring:
        under directory URLs the page is one level deeper than its own sibling files,
        so every download link was a 404.
        """
        site_path = posixpath.join(folder, filename) if folder else filename
        return relative_url(site_path, page.file.url)

    # ⚠️ PLACED IS POPULATED BEFORE ANY CELL IS RENDERED, and the order is the point.
    # A cell may itself contain `[x](@data:other_slot)`, and cells.render resolves that
    # through links.py, which reads this map. Filling it afterwards would make a
    # same-page reference resolve as broken on the first table and fine on the second --
    # an ordering bug that reads as a typo.
    embedded = {b[2] for b in blocks}
    placed: dict[str, dict] = {
        slot: {"href": href_for(entry["file"]), "anchor": slot in embedded}
        for slot, entry in declared.items()
    }
    PLACED[src] = placed

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
            placed[slot]["anchor"] = False
            continue

        rows = _trim_columns(_read_rows(path))
        if not rows:
            state.note(
                "notes",
                src + ": data file " + entry["file"] + " is empty or unreadable.",
            )
            replacements.append((start, end, ""))
            placed[slot]["anchor"] = False
            continue

        rows, pinned, override = _apply_options(rows, options, slot, src, state.note)
        caption = override if override is not None else entry["caption"]
        replacements.append((
            start, end,
            _draw(rows, href_for(entry["file"]), entry["file"], slot, caption,
                  pinned, page),
        ))

    for slot in declared:
        if slot in embedded:
            continue
        # Declared and never drawn. It is NOT quietly appended at the page foot: a table
        # silently landing at the bottom of a long page is the failure nobody notices
        # for a month, and that fallback is the second legal path this rewrite removed.
        state.note(
            "missing_required",
            src + ": data slot '" + slot + "' is declared and never placed. Add "
            + '!!! data "' + slot + '" where the table belongs, or drop the slot. An '
            + "inline [mention](@data:" + slot + ") still resolves to the file "
            + "download, so this warns rather than breaking the page.",
        )

    for start, end, replacement in reversed(replacements):
        lines[start:end] = [replacement]
    return "\n".join(lines)
