"""Reading a TSV and shaping it. Everything BEFORE the HTML.

Split out of `datatable.py` on 2026-08-04 because that module reached 25KB -- past the
line where a file stops coming back whole from a single read, which is when it stops
being safely editable. `seal.py` came out of `router.py` the same night for the same
reason. Trimming the docstring bought 2KB and was not enough; the module was simply doing
two jobs.

**The seam is where the data stops and the markup starts.** This file knows what a
spreadsheet is: rows, a header, section breaks, ragged widths, which column an option
names, what order the rows go in. It emits no HTML and imports nothing that does.
`datatable.py` keeps the frontmatter contract, the `!!! data` block, and the drawing.

It depends on `cells` for ONE thing: the plain text of a cell. A column name may be
written `**Count**` and an option says `sort: count`, so comparison happens on what a
reader sees rather than on what the author typed. Same for sorting -- see
`sort_within_sections`.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import cells


def norm(name) -> str:
    """Loose comparison key for a column name. Markup and case are not identity."""
    return re.sub(r"\s+", " ", cells.plain(name)).strip().lower()


def read_rows(path: Path) -> list[list[str]]:
    """Every non-blank line as a list of stripped cells. Unreadable file -> no rows.

    `utf-8-sig` because a sheet exported from Excel on Windows carries a BOM, and a BOM
    left on the first header cell makes that column impossible to name in an option.
    """
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


def trim_columns(rows: list[list[str]]) -> list[list[str]]:
    """Pad every row to the widest, then drop columns empty throughout.

    Both halves are needed, for opposite reasons: an exported sheet has rows running PAST
    the header (real data nobody titled) and columns that exist only as trailing tabs.
    Padding FIRST means a real value in an over-long row survives the trim.
    """
    if not rows:
        return rows
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    keep = [i for i in range(width) if any(r[i] for r in rows)]
    return [[r[i] for i in keep] for r in rows]


def is_section(row: list[str]) -> bool:
    """A heading INSIDE the sheet: first cell filled, everything else empty.

    `RACK 1`, `ML PANEL 2`, `WIRED MICROPHONES [8170]`. Not a record, and rendering it as
    a mostly-empty row is how a real exported sheet gets misread.
    """
    return bool(row) and bool(row[0]) and not any(row[1:])


def column_index(header: list[str], wanted) -> int:
    """Which column an option names, or -1. Never guesses at a near miss."""
    target = norm(wanted)
    for i, cell in enumerate(header):
        if norm(cell) == target:
            return i
    return -1


def header_line(header) -> str:
    """The header as prose, for a report line that has to say what IS there."""
    return ", ".join(cells.plain(c) for c in header if c)


def sort_within_sections(body, index: int):
    """Order rows by one column, never moving a record across a section heading.

    ⚠️ Three deliberate behaviours, each of which looks like a bug from outside.

    **Within sections only.** A sheet divided into `RACK 1` and `RACK 2` means nothing
    with its records redistributed between them, and a flat sort would do exactly that,
    silently.

    **Sorts on `cells.plain()`, not the raw cell.** A marked or linked value sorts on its
    text, so `[18'-0"]{.est}` sorts as `18'-0"`. Markup cannot reorder a sheet -- that was
    the one non-negotiable constraint on in-cell prose (DL J17).

    **Numeric when it can be.** A column whose every filled value parses as a number
    sorts numerically; otherwise `10` lands before `9`, which is the kind of wrong nobody
    reports because it reads as an ordering choice rather than an error. One non-numeric
    value drops the whole column back to text, on purpose: a half-numeric sort is less
    predictable than either.
    """
    records = [r for r in body if not is_section(r)]
    values = [cells.plain(r[index]) for r in records if index < len(r)]
    numeric = bool(values) and all(cells.number(v) is not None for v in values if v)

    def key(row):
        text = cells.plain(row[index] if index < len(row) else "")
        if not text:
            # Blanks last in both modes. A blank means "nobody has said", and floating it
            # to the top of every section buries the rows that carry data.
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
        if is_section(row):
            flush()
            out.append(row)
            continue
        block.append(row)
    flush()
    return out


KNOWN_OPTIONS = ("pin", "sort", "hide", "caption")


def apply_options(rows, options, slot, src, note):
    """Return (rows, pinned_index, caption_override_or_None).

    ⭐ AN OPTION NAMING A MISSING COLUMN IS REPORTED AND IGNORED, NEVER SILENT. Silence
    was asked for and refused: the evidence was a page in the content repo carrying a
    hand-written note that the frozen header and first column DO NOT freeze, discovered
    by accident weeks after shipping. `pin: commitID` against a header reading `commit_id`
    would rebuild that bug as policy -- a table that looks right, behaves wrong, and never
    says why. Warn, render without the option, publish, report.

    Never raises. A cosmetic typo must not be able to fail a build.
    """
    header, body = rows[0], rows[1:]
    pinned = -1

    for key in sorted(options):
        if key not in KNOWN_OPTIONS:
            note(
                "dead_links",
                src + ": data block '" + slot + "' sets unknown option '" + key
                + "'. Ignored. Known: " + ", ".join(KNOWN_OPTIONS) + ".",
            )

    drop: list[int] = []
    for name in [h for h in options.get("hide", "").split(",") if h.strip()]:
        index = column_index(header, name)
        if index < 0:
            note(
                "dead_links",
                src + ": data block '" + slot + "' hides column '" + name.strip()
                + "' which is not in the sheet. Nothing hidden. Header: "
                + header_line(header) + ".",
            )
            continue
        drop.append(index)

    if "sort" in options:
        index = column_index(header, options["sort"])
        if index < 0:
            note(
                "dead_links",
                src + ": data block '" + slot + "' sorts by '" + options["sort"]
                + "' which is not in the sheet. Rendered in sheet order. Header: "
                + header_line(header) + ".",
            )
        else:
            body = sort_within_sections(body, index)

    if "pin" in options:
        pinned = column_index(header, options["pin"])
        if pinned < 0:
            note(
                "dead_links",
                src + ": data block '" + slot + "' pins '" + options["pin"]
                + "' which is not in the sheet. Nothing pinned. Header: "
                + header_line(header) + ".",
            )

    if drop:
        keep = [i for i in range(len(header)) if i not in drop]
        pin_name = header[pinned] if pinned >= 0 else None
        header = [header[i] for i in keep]
        body = [
            r if is_section(r) else [c for j, c in enumerate(r) if j in keep]
            for r in body
        ]
        # Recomputed AFTER the drop: an index taken against the full header points at the
        # wrong column once earlier columns are gone.
        pinned = column_index(header, pin_name) if pin_name else -1

    return [header] + body, pinned, options.get("caption")
