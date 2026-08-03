"""Stage 01b -- render a TSV sitting next to a page as a table.

THE PURITY RULE, READ CORRECTLY.

"The content tree holds markdown and nothing else" was always a rule about
MACHINERY, not about file extensions. It exists so the green Download ZIP
button hands somebody the documents and nothing they have to be told to ignore:
no stylesheet, no config, no nav manifest, no build script.

A table of dimmer circuits is not machinery. It IS the documentation, and it is
precisely the thing a reader would want in that zip. Refusing it on a technical
reading of the rule would push real content out of the content repo, which is
the exact opposite of what the rule is for.

So: a page may declare data files beside it. They stay TSV on disk -- editable
in a spreadsheet, diffable in git, greppable, and useful to anything that is
not this renderer -- and the engine draws them.

    ---
    id: oph-lighting-circuits
    title: Circuits and dimmers
    type: reference
    status: public
    data:
      - circuits-and-dimmers.tsv
      - where-dimmers-run.tsv
    ---

PLACEMENT. By default each table renders at the end of the page, in the order
declared. To put one somewhere specific -- with prose either side of it, which
is usually what you want -- drop a marker where it belongs:

    <!-- dr:table circuits-and-dimmers.tsv -->

An HTML comment is used deliberately: it is invisible in every other markdown
renderer, on GitHub, and in a plain text editor. A page keeps working as a
document even where this engine is not involved, which is the same promise the
content repo itself makes.

WHAT IT UNDERSTANDS ABOUT REAL SPREADSHEETS, because exported ones are messy:

  * SECTION ROWS. A row with a value in the first cell and nothing anywhere
    else (RACK 1, ML PANEL 2) is a heading inside the sheet, not a record. It
    renders as a spanning subheading rather than a mostly-empty row.
  * RAGGED WIDTH. Rows longer than the header keep their cells; the header is
    padded. Trailing columns that are empty in EVERY row are dropped. An
    exported sheet routinely carries both problems at once.
  * JUNK HEADERS. A header cell that is only punctuation (a stray backtick from
    an export) renders blank instead of as a column name.
  * BLANK ROWS are skipped.

It does NOT sort, filter, total, or reinterpret. The sheet is the source of
truth and the renderer's job is to show it, not to have opinions about it.

The raw file is also published beside the page, so every table offers a
download link back to the exact TSV it was drawn from.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from . import state

_MARKER = re.compile(r"[ \t]*<!--[ \t]*dr:table[ \t]+(?P<name>[^\s>]+?)[ \t]*-->[ \t]*")
_JUNK_HEADER = re.compile(r"^[\W_]+$")


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


def _render(path: Path, href: str) -> str:
    rows = _trim_columns(_read_rows(path))
    if not rows:
        state.note("notes", "data file " + path.name + " is empty or unreadable")
        return ""

    header, body = rows[0], rows[1:]
    span = len(header)

    out = ['<div class="dr-data" markdown="0">', "<table>", "<thead><tr>"]
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
        + str(len(body)) + " rows &middot; "
        + '<a href="' + html.escape(href) + '" download>' + html.escape(path.name)
        + "</a></p>"
    )
    out.append("</div>")
    return "\n".join(out)


def on_page_markdown(markdown, page, config, files):
    meta = state.BY_SRC.get(page.file.src_uri, {})
    declared = meta.get("data")
    if not declared:
        return markdown
    if isinstance(declared, str):
        declared = [declared]

    here = Path(page.file.abs_src_path).parent
    placed: set[str] = set()
    rendered: dict[str, str] = {}

    for name in declared:
        name = str(name)
        path = here / name
        if not path.is_file():
            state.note(
                "missing_required",
                page.file.src_uri + ": declares data file '" + name
                + "' which does not exist beside it",
            )
            rendered[name] = (
                '<p class="docrender-dead">Missing data file: '
                + html.escape(name) + "</p>"
            )
            continue
        # The TSV is copied to the site as an ordinary static file, so the
        # download link is simply its name relative to the page's own URL.
        rendered[name] = _render(path, name)

    def swap(match):
        name = match.group("name")
        if name not in rendered:
            state.note(
                "missing_required",
                page.file.src_uri + ": marker for '" + name
                + "' but it is not listed in the page's `data:` frontmatter",
            )
            return (
                '<p class="docrender-dead">Undeclared data file: '
                + html.escape(name) + "</p>"
            )
        placed.add(name)
        return rendered[name]

    markdown = _MARKER.sub(swap, markdown)

    trailing = [rendered[n] for n in rendered if n not in placed]
    if trailing:
        markdown = markdown.rstrip() + "\n\n" + "\n\n".join(trailing) + "\n"
    return markdown
