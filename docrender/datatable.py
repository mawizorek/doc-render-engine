"""Stage 01b -- render a TSV sitting next to a page as a table.

THE PURITY RULE, READ CORRECTLY.

"The content tree holds markdown and nothing else" was always a rule about
MACHINERY, not about file extensions. It exists so the green Download ZIP
button hands somebody the documents and nothing they have to be told to ignore:
no stylesheet, no config, no nav manifest, no build script.

A table of dimmer circuits is not machinery. It IS the documentation, and it is
precisely the thing a reader would want in that zip.

HOW A PAGE DECLARES AND PLACES A TABLE (Decision Log J4, J5, and Q8's `!!!`
form). Two halves of two DIFFERENT facts, which is why this is not the
declared-twice defect it replaced:

    ---
    type: reference
    data:
      schedule_table: circuits-and-dimmers.tsv     WHICH file, named by SLOT
      revision_log: circuits-revisions.tsv
    ---

    !!! data "schedule_table"                       WHERE it renders

    ...and mid-sentence, [the circuit schedule](@data:schedule_table) LINKS to
    it -- resolved by links.py through the reserved `data` prefix.

⭐ THE BODY NEVER NAMES A FILE. It names a slot. Renaming or repointing the TSV
is a one-line frontmatter edit and no prose changes, which is the entire point:
the same paragraphs can be copied between the audio, lighting and video pages
with only the header touched. Slot names are declared on the TYPE, closed
vocabulary -- see docrender/typespec.py for why that is not negotiable.

⚠️ `data:` IS A MAP NOW, NOT A LIST OF FILENAMES. The list form is reported and
not rendered. There is deliberately NO dual-form support: a second legal shape
is the sanctioned fallback this project keeps rejecting, and the blast radius at
the time of the change was two pages.

WHY `!!!` AND NOT A LINK OR AN HTML COMMENT.

  * The HTML comment it replaces (`<!-- dr:table file.tsv -->`) was invisible to
    everything: it could not reach doc-index.json, could not be validated by the
    type spec, and a misspelled filename inside it rendered NOTHING AT ALL,
    silently. Still honoured, loudly reported, migrate off it.
  * `![label](@data:slot)` was the first answer and it carried a label that was
    a second hand-maintained copy of the table's name. `!!!` needs no label.
  * `admonition` is already enabled and these pages already write
    `!!! warning "..."`, so this is the one block grammar the content set
    already speaks. With this hook disabled the line degrades to a visible
    admonition box, not to a broken image.
  * A cost, stated plainly: `data` is now a reserved admonition type. Nobody can
    write a genuine `!!! data` callout again.

OPTIONS, indented under the block like any admonition body:

    !!! data "revision_log"
        pin: none
        sort: timestamp
        hide: internal_notes, raw
        caption: Revision history

⚠️ AN OPTION THAT NAMES A COLUMN THAT IS NOT THERE IS REPORTED, NEVER SILENT
(Decision Log Q9, option A -- silence was asked for and refused). The reason is
in the content tree in Michael's own handwriting: this table shipped promising a
frozen header and first column, the promise was false for a fortnight, and
nobody found out until somebody scrolled a wide sheet on a desktop. `pin:
commitID` against a header that says `commit_id` would rebuild that bug and make
it policy. The build WARNS AND PUBLISHES -- the table renders without the
option, the page ships, the miss lands in the report.

⚠️ `pin:` FREEZES THE FIRST COLUMN AND ONLY THE FIRST COLUMN. Sticky offsets for
a second frozen column need pixel widths that do not exist until the browser has
laid the table out, so an engine that promised `pin: anything` would be lying in
CSS. What `pin:` buys is that the freeze is now DECLARED and CHECKED instead of
assumed: name the first column and a typo is caught, or say `pin: none` when
column one is not an identifier worth freezing. `hide:` is applied first, so
"first column" means first SURVIVING column.

It does NOT filter, total, or reinterpret. `sort` and `hide` are presentation;
editing belongs in the TSV, which stays the source of truth. Sorting happens
WITHIN each section block, never across one -- a sheet whose sections are RACK 1
and RACK 2 does not mean anything with its rows shuffled between them.

WHAT IT UNDERSTANDS ABOUT REAL SPREADSHEETS, because exported ones are messy:

  * SECTION ROWS. A row with a value in the first cell and nothing anywhere else
    (RACK 1, ML PANEL 2) is a heading inside the sheet, not a record. It renders
    as a spanning subheading rather than a mostly-empty row.
  * RAGGED WIDTH. Rows longer than the header keep their cells; the header is
    padded. Trailing columns that are empty in EVERY row are dropped. An
    exported sheet routinely carries both problems at once.
  * JUNK HEADERS. A header cell that is only punctuation (a stray backtick from
    an export) renders blank instead of as a column name.
  * BLANK ROWS are skipped.

🐛 THE DOWNLOAD LINK WAS A 404 AND THE OLD COMMENT ASSERTED IT WAS NOT. It said
the href "is simply its name relative to the page's own URL," which is true only
on an index page. Under `use_directory_urls: true` a page at `lighting/x.md` is
served from `lighting/x/`, while its TSV stays at `lighting/x.tsv` -- one level
UP. So a bare filename resolved to `lighting/x/x.tsv` and downloaded nothing.
Resolved through util.relative_url now, which is the same helper that fixed the
identical class of bug in links.py and router.py. Do not go back to a bare name.

⚠️ THE TABLE CARRIES A CLASS AND THAT IS LOAD-BEARING (fixed 2026-08-03).
Material styles `.md-typeset table:not([class])` with `display: block` so wide
tables can scroll. `display: block` on a table destroys the internal table
layout, and a `position: sticky` cell inside a non-table has no row context to
stick within -- so the frozen header and frozen first column silently did
nothing, which is exactly how it shipped and exactly how Michael found it.
The class makes `:not([class])` stop matching. Do not remove it.

⚠️ THE SCANNER MUST ALWAYS ADVANCE. This walks the page line by line rather than
substituting with one regex, because an indented option body is not something a
single expression reads honestly. Every branch below either consumes lines in
its own loop or increments `index`. A branch that falls through to `continue`
without advancing hangs the build forever on one line, which is exactly what the
first cut of this file did.
"""

from __future__ import annotations

import html
import posixpath
import re
from pathlib import Path

from . import prefixes, state, typespec
from .util import relative_url

#: The retired HTML-comment placement marker. Honoured, reported, going away.
_LEGACY_MARKER = re.compile(
    r"[ \t]*<!--[ \t]*dr:table[ \t]+(?P<name>[^\s>]+?)[ \t]*-->[ \t]*"
)
_BLOCK_OPEN = re.compile(r'^(?P<indent>[ \t]*)!!![ \t]+data[ \t]+"(?P<slot>[^"]*)"[ \t]*$')
_OPTION = re.compile(r"^[ \t]+(?P<key>[A-Za-z_][A-Za-z0-9_]*)[ \t]*:[ \t]*(?P<value>.*?)[ \t]*$")
_FENCE = re.compile(r"^[ \t]*(```+|~~~+)")
_JUNK_HEADER = re.compile(r"^[\W_]+$")

_KNOWN_OPTIONS = ("pin", "sort", "hide", "caption")

#: src_uri -> slot -> {"href": str, "anchor": str|None}
#: Read by links.py to resolve an inline `@data:slot` mention. Populated while
#: this hook rewrites the page, which is stage 01b -- two full stages before
#: links runs at 03, so the map is always complete by the time it is read.
PLACED: dict[str, dict[str, dict]] = {}


def _norm(label: str) -> str:
    """Column names compare loosely. `Commit ID`, `commit_id` and `commitid`
    are the same column to a human, and a human is who types the option."""
    return re.sub(r"[\W_]+", "", str(label)).lower()


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
    """Pad every row to the widest, then drop columns that are empty throughout.

    Both halves are needed and for opposite reasons: an exported sheet has rows
    that run PAST the header (real data nobody put a heading on) and columns
    that exist only as trailing tabs. Padding first means a real value in an
    over-long row is never lost by the trim.
    """
    if not rows:
        return rows
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    keep = [i for i in range(width) if any(r[i] for r in rows)]
    return [[r[i] for i in keep] for r in rows]


def _is_section(cells: list[str]) -> bool:
    return bool(cells) and bool(cells[0]) and not any(cells[1:])


def _parse_options(lines: list[str], where: str, slot: str) -> dict:
    opts: dict = {}
    for line in lines:
        match = _OPTION.match(line)
        if not match:
            if line.strip():
                state.note(
                    "notes",
                    where + ": data block '" + slot + "' has a line that is not an "
                    + "option (`key: value`) and is ignored: " + line.strip(),
                )
            continue
        key = match.group("key").lower()
        if key not in _KNOWN_OPTIONS:
            state.note(
                "notes",
                where + ": data block '" + slot + "' names unknown option `" + key
                + "` (known: " + ", ".join(_KNOWN_OPTIONS) + "). Ignored.",
            )
            continue
        opts[key] = match.group("value")
    return opts


def _apply_hide(header: list[str], body: list[list[str]], spec: str, where: str, slot: str):
    wanted = [w.strip() for w in spec.split(",") if w.strip()]
    lookup = {_norm(h): i for i, h in enumerate(header)}
    drop: set[int] = set()
    for name in wanted:
        index = lookup.get(_norm(name))
        if index is None:
            state.note(
                "notes",
                where + ": data block '" + slot + "' hides column '" + name
                + "' which is not in the sheet. Columns: " + ", ".join(header)
                + ". Rendered with every column.",
            )
            continue
        drop.add(index)
    if not drop:
        return header, body
    if len(drop) >= len(header):
        state.note(
            "notes",
            where + ": data block '" + slot + "' hides every column. Ignored.",
        )
        return header, body
    keep = [i for i in range(len(header)) if i not in drop]
    new_header = [header[i] for i in keep]
    new_body = []
    for cells in body:
        if _is_section(cells):
            new_body.append([cells[0]] + [""] * (len(keep) - 1))
        else:
            new_body.append([cells[i] if i < len(cells) else "" for i in keep])
    return new_header, new_body


def _apply_sort(header: list[str], body: list[list[str]], spec: str, where: str, slot: str):
    """Sort rows by a named column, WITHIN each section block.

    Never across a section break. A sheet divided into RACK 1 and RACK 2 means
    nothing with its rows redistributed between them, and a sort that silently
    did that would be the renderer having an opinion about the data.
    """
    index = {_norm(h): i for i, h in enumerate(header)}.get(_norm(spec))
    if index is None:
        state.note(
            "notes",
            where + ": data block '" + slot + "' sorts by column '" + spec.strip()
            + "' which is not in the sheet. Columns: " + ", ".join(header)
            + ". Rendered in sheet order.",
        )
        return body

    out: list[list[str]] = []
    run: list[list[str]] = []

    def flush():
        # Blanks last rather than first: an untraced value is not a value that
        # sorts before everything, and floating them to the top of every section
        # would bury the rows that actually carry data.
        run.sort(
            key=lambda r: (
                not (r[index] if index < len(r) else ""),
                (r[index] if index < len(r) else "").lower(),
            )
        )
        out.extend(run)
        run.clear()

    for cells in body:
        if _is_section(cells):
            flush()
            out.append(cells)
            continue
        run.append(cells)
    flush()
    return out


def _render(path: Path, href: str, slot: str, opts: dict, where: str) -> tuple[str, str]:
    rows = _trim_columns(_read_rows(path))
    if not rows:
        state.note("notes", where + ": data file " + path.name + " is empty or unreadable")
        return "", ""

    header, body = rows[0], rows[1:]

    if opts.get("hide"):
        header, body = _apply_hide(header, body, opts["hide"], where, slot)
    if opts.get("sort"):
        body = _apply_sort(header, body, opts["sort"], where, slot)

    # `pin` is validated AFTER hide, because hiding a column changes which one
    # is first, and the option is about the first surviving column.
    pinned = True
    pin = (opts.get("pin") or "").strip()
    if pin:
        if _norm(pin) == "none" or not header:
            pinned = False
        elif _norm(pin) != _norm(header[0]):
            if _norm(pin) in {_norm(h) for h in header}:
                state.note(
                    "notes",
                    where + ": data block '" + slot + "' pins column '" + pin
                    + "', which exists but is not the FIRST column ('" + header[0]
                    + "'). Only the first column can be frozen -- move it in the "
                    + "TSV or drop the option. Rendered with the first column "
                    + "frozen.",
                )
            else:
                state.note(
                    "notes",
                    where + ": data block '" + slot + "' pins column '" + pin
                    + "' which is not in the sheet. Columns: " + ", ".join(header)
                    + ". Rendered with the first column frozen.",
                )

    anchor = "dr-data--" + (re.sub(r"[^a-z0-9]+", "-", slot.lower()).strip("-") or "table")
    span = len(header)
    classes = "dr-data__table" if pinned else "dr-data__table dr-data__table--nopin"

    out = [
        '<div class="dr-data" id="' + anchor + '">',
        # The class is required, not decorative -- see the module docstring.
        '<table class="' + classes + '">',
        "<thead><tr>",
    ]
    for cell in header:
        label = "" if _JUNK_HEADER.match(cell) else html.escape(cell)
        out.append("<th>" + label + "</th>")
    out.append("</tr></thead>")
    out.append("<tbody>")

    for cells in body:
        if _is_section(cells):
            out.append(
                '<tr class="dr-data__section"><th colspan="' + str(span) + '">'
                + html.escape(cells[0]) + "</th></tr>"
            )
            continue
        out.append("<tr>")
        for cell in cells:
            out.append("<td>" + html.escape(cell) + "</td>")
        out.append("</tr>")

    out.append("</tbody></table>")
    out.append(
        '<p class="dr-data__source">'
        + str(len([c for c in body if not _is_section(c)])) + " rows &middot; "
        + '<a href="' + html.escape(href) + '" download>' + html.escape(path.name)
        + "</a></p>"
    )
    out.append("</div>")

    caption = (opts.get("caption") or "").strip()
    if caption:
        out.append('<p class="dr-data__caption">' + html.escape(caption) + "</p>")

    # Blank lines top and bottom: a raw HTML block glued to a prose line is not
    # a block to the markdown parser, and it gets wrapped in a stray <p>.
    return "\n" + "\n".join(out) + "\n", anchor


def _declared(page, where: str) -> dict[str, str] | None:
    """The page's slot -> filename map, or None if it declares no data."""
    meta = state.BY_SRC.get(page.file.src_uri, {})
    declared = meta.get("data")
    if not declared:
        return None

    if not isinstance(declared, dict):
        state.note(
            "missing_required",
            where + ": `data:` is a MAP of slot names to filenames now, not a list. "
            + "Write `data:` then an indented `schedule_table: file.tsv` per file, "
            + "and refer to the SLOT in the body. Nothing on this page rendered.",
        )
        return None

    type_name = meta.get("_type", "page")
    legal = typespec.data_slots(type_name)
    clean: dict[str, str] = {}
    for slot, filename in declared.items():
        slot = str(slot)
        if legal and slot not in legal:
            state.note(
                "missing_required",
                where + ": data slot '" + slot + "' is not declared on type '"
                + type_name + "'. Declared slots: " + ", ".join(legal)
                + ". Add it to objects/" + type_name + ".yml or use one of those "
                + "-- a slot only travels between pages if every page spells it "
                + "the same way.",
            )
            continue
        if not legal:
            state.note(
                "notes",
                where + ": type '" + type_name + "' declares no `data_slots:`, so slot '"
                + slot + "' is unchecked. Declare the vocabulary on the type.",
            )
        clean[slot] = str(filename)
    return clean


def on_page_markdown(markdown, page, config, files):
    where = page.file.src_uri
    declared = _declared(page, where)
    if not declared:
        return markdown

    here = Path(page.file.abs_src_path).parent
    folder = posixpath.dirname(where)
    by_file = {name: slot for slot, name in declared.items()}
    placed: dict[str, dict] = {}

    def href_for(filename: str) -> str:
        """The TSV's URL relative to the page ASKING for it. See the docstring:
        a bare filename is wrong on every page that is not an index."""
        site_path = posixpath.join(folder, filename) if folder else filename
        return relative_url(site_path, page.file.url)

    lines = markdown.splitlines()
    out: list[str] = []
    index = 0
    in_fence = False

    while index < len(lines):
        line = lines[index]

        if _FENCE.match(line):
            in_fence = not in_fence
            out.append(line)
            index += 1
            continue

        if in_fence:
            out.append(line)
            index += 1
            continue

        block = _BLOCK_OPEN.match(line)
        if block:
            slot = block.group("slot").strip()
            index += 1
            option_lines: list[str] = []
            while index < len(lines):
                nxt = lines[index]
                if not nxt.strip():
                    # A blank line inside an admonition body is legal, but a
                    # blank followed by unindented text ends the block.
                    if index + 1 < len(lines) and lines[index + 1].startswith(("    ", "\t")):
                        option_lines.append(nxt)
                        index += 1
                        continue
                    break
                if nxt.startswith(("    ", "\t")):
                    option_lines.append(nxt)
                    index += 1
                    continue
                break

            opts = _parse_options(option_lines, where, slot)
            filename = declared.get(slot)
            if not filename:
                state.note(
                    "missing_required",
                    where + ": `!!! data \"" + slot + "\"` but '" + slot + "' is not "
                    + "in this page's `data:` frontmatter. Declared: "
                    + (", ".join(sorted(declared)) or "nothing"),
                )
                out.append(
                    '\n<p class="docrender-dead">Undeclared data slot: '
                    + html.escape(slot) + "</p>\n"
                )
                continue

            path = here / filename
            if not path.is_file():
                state.note(
                    "missing_required",
                    where + ": slot '" + slot + "' points at '" + filename
                    + "' which does not exist beside this page",
                )
                out.append(
                    '\n<p class="docrender-dead">Missing data file: '
                    + html.escape(filename) + "</p>\n"
                )
                continue

            rendered, anchor = _render(path, href_for(filename), slot, opts, where)
            if rendered:
                out.append(rendered)
                placed[slot] = {"href": href_for(filename), "anchor": anchor}
            continue

        legacy = _LEGACY_MARKER.fullmatch(line)
        if legacy:
            index += 1
            name = legacy.group("name")
            slot = by_file.get(name)
            state.note(
                "notes",
                where + ": `<!-- dr:table " + name + " -->` is the RETIRED placement "
                + "marker and is still honoured for now. Replace it with `!!! data "
                + '"' + (slot or "<slot>") + '"` -- the comment form is invisible to '
                + "the type spec, and a typo inside it renders nothing at all, "
                + "silently.",
            )
            if slot and (here / name).is_file():
                rendered, anchor = _render(here / name, href_for(name), slot, {}, where)
                if rendered:
                    out.append(rendered)
                    placed[slot] = {"href": href_for(name), "anchor": anchor}
                    continue
            out.append(
                '\n<p class="docrender-dead">Undeclared data file: '
                + html.escape(name) + "</p>\n"
            )
            continue

        out.append(line)
        index += 1

    # ⚠️ NO TRAILING FALLBACK. A declared-but-unplaced table used to be dumped at
    # the foot of the page in declaration order. That is a second legal way for a
    # table to arrive, it was never the intended one, and a table silently
    # landing at the bottom of a long page is the kind of failure nobody notices
    # for a month. It is reported instead. The slot stays resolvable as a
    # DOWNLOAD by an inline `@data:` mention, which is a legitimate way to use a
    # sheet you never embed.
    for slot, filename in declared.items():
        if slot in placed:
            continue
        if not (here / filename).is_file():
            state.note(
                "missing_required",
                where + ": slot '" + slot + "' points at '" + filename
                + "' which does not exist beside this page",
            )
            continue
        placed[slot] = {"href": href_for(filename), "anchor": None}
        state.note(
            "notes",
            where + ": slot '" + slot + "' (" + filename + ") is declared but never "
            + 'placed. Add `!!! data "' + slot + '"` where the table belongs, or '
            + "remove the slot. Inline mentions of it link to the file itself.",
        )

    PLACED[where] = placed
    return "\n".join(out)


def reference(src_uri: str, slot: str) -> dict | None:
    """How an inline `@data:slot` on this page should resolve.

    Returns `{"href": ..., "anchor": ...}` where anchor is the id of the embedded
    table on this page, or anchor None when the slot is declared but not embedded
    -- in which case the mention becomes a download link to the TSV itself.
    """
    return (PLACED.get(src_uri) or {}).get(slot)


def slots_on(src_uri: str) -> list[str]:
    return sorted(PLACED.get(src_uri) or {})


prefixes.claim("data", reference, owner="docrender/datatable.py")
