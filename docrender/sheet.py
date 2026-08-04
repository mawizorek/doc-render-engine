"""Reading a TSV and shaping it. Everything BEFORE the HTML.

**The seam is where the data stops and the markup starts.** This file knows what a
spreadsheet is: rows, a header, section breaks, ragged widths, which column an option
names, what order the rows go in, and what KIND of thing each column holds. It emits no
HTML and imports nothing that does. `table.py` turns the result into markup;
`datatable.py` owns the frontmatter contract and the `!!! data` block.

It depends on `cells` for ONE thing: the plain text of a cell. A column name may be
written `**Count**` and an option says `sort: count`, so comparison happens on what a
reader sees rather than on what the author typed. Same for sorting -- see
`sort_within_sections` -- and same for classification, so a marked value cannot change
what kind of column it sits in.


A HEADER CELL MAY DECLARE ITS COLUMN (2026-08-04, DL J21)
=========================================================

    thtr::id.key    slug    title::.key    credits::num    unit_cost::money

`name::type.role.role`. Both halves optional: `x::num` is a type with no role,
`x::.key` is a role with no type, plain `x` is neither and derives everything.

⭐ **DERIVATION STAYS AND STAYS FIRST. A DECLARATION IS AN OVERRIDE.** That ordering is
the whole reason this is safe to ship against a tree already full of TSVs: an
unannotated sheet renders byte-for-byte as it did before this existed, so nobody has to
migrate anything to keep what they have. If declaration replaced derivation, every sheet
on the site would need a header pass before it rendered correctly again.

⚠️ **AND IT IS NEEDED, WHICH `classify_columns` CANNOT ARGUE ITSELF OUT OF.** On the real
`02-courses/course-index.tsv`: `credits` holds `1-4` and `2-4`, so one non-numeric value
drops the whole column to text and the figures stop aligning -- the documented rule,
working exactly as designed, producing the wrong answer. `thtr` is all digits, so it
right-aligns course numbers as though they were quantities. **Derivation reads SHAPE and
cannot read MEANING.** Currency is the same gap and worse: `1200` is a number either way
and nothing in the values says dollars.

⚠️ **SPECS ARE CARRIED BY NAME, NEVER BY INDEX.** `apply_options` drops columns for
`hide:`, so an index taken against the original header points at the wrong column
afterwards -- the bug already written down two functions down, where `pinned` has to be
recomputed for exactly that reason. A name lookup cannot drift. ⚠️ Two columns sharing a
name therefore share a spec; a sheet with duplicate headers has a bigger problem.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import cells


def norm(name) -> str:
    """Loose comparison key for a column name. Markup and case are not identity."""
    return re.sub(r"\s+", " ", cells.plain(name)).strip().lower()


_JUNK = re.compile(r"^[\W_]+$")


def is_junk(cell) -> bool:
    """A cell that is punctuation or underscores and nothing else.

    `-`, `--`, `|`, `___`. An exported sheet is full of them: separator columns somebody
    drew by hand in Excel, and header cells that were never titled. They are not data and
    they are not a label, so nothing downstream should reserve space for them.
    """
    text = cells.plain(cell)
    return bool(text) and bool(_JUNK.match(text))


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
    """Pad every row to the widest, then drop columns that carry nothing.

    Both halves are needed, for opposite reasons: an exported sheet has rows running PAST
    the header (real data nobody titled) and columns that exist only as trailing tabs.
    Padding FIRST means a real value in an over-long row survives the trim.

    ⚠️ 'CARRIES NOTHING' MEANS EMPTY *OR JUNK*, AND THAT CHANGED ON 2026-08-04. A column
    whose every cell is blank except a header reading `-` used to survive: the drawing
    code blanked the junk LABEL and kept the COLUMN, so `thead th { min-width: 6rem }`
    reserved a sixth of a phone screen to render nothing, on every sheet that had one.

    A column is only dropped when NO cell in it is real -- a `Status` column full of `-`
    keeps its header and stays, because somebody titled it and a reader can see that the
    values are placeholders. The rule is about columns nobody meant to create.
    """
    if not rows:
        return rows
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    keep = [
        i for i in range(width)
        if any(r[i] and not is_junk(r[i]) for r in rows)
    ]
    return [[r[i] for i in keep] for r in rows]


def is_section(row: list[str]) -> bool:
    """A heading INSIDE the sheet: first cell filled, everything else empty.

    `RACK 1`, `ML PANEL 2`, `WIRED MICROPHONES [8170]`. Not a record, and rendering it as
    a mostly-empty row is how a real exported sheet gets misread.
    """
    return bool(row) and bool(row[0]) and not any(row[1:])


NUM = "num"
TOKEN = "tok"
PROSE = "prose"

#: What a header may DECLARE, mapped to the kind class the stylesheet knows.
#: `text` and `tok` are the same treatment under two names -- `text` is what an author
#: means, `tok` is what the derivation has called it since #54, and renaming the internal
#: one would churn the CSS for nothing.
TYPES = {
    "id": "id",
    "num": NUM,
    "money": "money",
    "text": TOKEN,
    "prose": PROSE,
}
ROLES = ("key",)

_SPEC = re.compile(r"^(?P<name>[^:]*)::(?P<spec>[A-Za-z0-9._-]*)$")


def split_header(rows, slot, src, note):
    """Strip `::type.role` off every header cell. Returns (rows, {norm_name: spec}).

    Runs immediately after `trim_columns` and BEFORE `apply_options`, because an option
    saying `sort: credits` has to match a column headed `credits::num`. By the time
    anything else in this module sees the header, the annotations are gone and the names
    are what a reader sees.

    ⚠️ An unknown type or role is REPORTED and IGNORED, never silent, for the reason
    `apply_options` spells out at length: `pros` for `prose` in a header would otherwise
    render a column that looks fine, behaves wrong, and never says why. A header is a
    worse place for that than an option, because the option at least gets re-read every
    time somebody edits the block.
    """
    if not rows:
        return rows, {}

    header = list(rows[0])
    specs: dict[str, dict] = {}

    for i, cell in enumerate(header):
        match = _SPEC.match(str(cell).strip())
        if not match:
            continue
        name = match.group("name").strip()
        parts = [p for p in match.group("spec").split(".") if p]
        kind = ""
        roles: list[str] = []

        # The type is the part BEFORE the first dot, and it is optional -- `::.key` is a
        # role with no type, which is the common case on a title column.
        if match.group("spec") and not match.group("spec").startswith("."):
            declared = parts.pop(0).lower() if parts else ""
            if declared in TYPES:
                kind = TYPES[declared]
            elif declared:
                note(
                    "dead_links",
                    src + ": data block '" + slot + "' column '" + name
                    + "' declares unknown type '" + declared + "'. Ignored, so the "
                    + "column falls back to the derived kind. Known: "
                    + ", ".join(sorted(TYPES)) + ".",
                )

        for role in parts:
            if role.lower() in ROLES:
                roles.append(role.lower())
            else:
                note(
                    "dead_links",
                    src + ": data block '" + slot + "' column '" + name
                    + "' declares unknown role '" + role + "'. Ignored. Known: "
                    + ", ".join(ROLES) + ".",
                )

        header[i] = name
        specs[norm(name)] = {"kind": kind, "roles": roles}

    return [header] + rows[1:], specs


#: A value is PROSE when it is long enough AND wordy enough that holding it on one line
#: is what sets the width of the whole table. Both tests, never either alone: `INV-433`
#: is short, `Spirit Folio Powered` is three words and 20 characters and still scans as a
#: label, and `Theatre and Cultural Context` is neither.
_PROSE_CHARS = 24
_PROSE_WORDS = 3


def classify_columns(rows) -> list[str]:
    """One kind per column -- `num`, `tok` or `prose` -- DERIVED FROM THE VALUES.

    ⭐ THE DEFAULT, AND STILL THE RIGHT DEFAULT. The sheet already knows whether a column
    holds inventory numbers or half a sentence, so the common case needs no authoring
    surface at all. `split_header` above lets a header override this where the values are
    genuinely ambiguous -- the two compose, and derivation is what runs when nobody said
    anything.

    Why it matters, and it is not decoration. `white-space: nowrap` was CORRECT when a
    cell was a value: a wrapped cell turns one row into three and destroys the horizontal
    scan. It stopped being correct the moment a cell became prose (PR #50), because then
    **the longest sentence in the sheet sets the scroll width of the entire table** and
    every column past it lives off the right edge of a phone.

    The rules, in order, first match wins:

      `num`    every filled value parses as a number (`cells.number`).
      `prose`  the longest value is over ~24 characters AND at least 3 words. Wraps.
      `tok`    everything else -- ids, codes, short labels, dimensions.

    ⚠️ MEASURED ON `cells.plain()`, NEVER THE RAW CELL, for the same reason `sort:` is:
    markup must not be able to change the shape of a sheet.

    ⚠️ SECTION ROWS ARE EXCLUDED. A section heading is one long string in column zero; it
    would make the identifier column prose on every sectioned sheet -- which is exactly
    the column that most needs to stay on one line.

    ⚠️ THE THRESHOLDS ARE A JUDGEMENT, NOT A MEASUREMENT. Set against two real sheets. A
    third sheet that classifies badly is evidence to move the numbers -- or now, to
    declare that one column in its header. It is not evidence for a new heuristic.
    """
    if not rows:
        return []
    header, body = rows[0], rows[1:]
    kinds: list[str] = []

    for i in range(len(header)):
        values = [
            cells.plain(r[i])
            for r in body
            if not is_section(r) and i < len(r) and str(r[i]).strip()
        ]
        values = [v for v in values if v]

        if not values:
            kinds.append(TOKEN)
            continue
        if all(cells.number(v) is not None for v in values):
            kinds.append(NUM)
            continue

        longest = max(values, key=len)
        if len(longest) > _PROSE_CHARS and len(longest.split()) >= _PROSE_WORDS:
            kinds.append(PROSE)
        else:
            kinds.append(TOKEN)

    return kinds


def column_kinds(rows, specs) -> list[str]:
    """The kind of every column: what its header declared, else what the values say."""
    derived = classify_columns(rows)
    out = []
    for i, cell in enumerate(rows[0] if rows else []):
        spec = specs.get(norm(cell)) or {}
        out.append(spec.get("kind") or derived[i])
    return out


def key_columns(rows, specs) -> list[bool]:
    """Which columns carry `.key` -- the ones that stay visible when space runs out.

    ⭐ A `.key` DECLARATION IS THE OPT-IN, and there is deliberately no second switch. A
    column marked key is only meaningful if something else collapses, so the declaration
    and the feature flag are the same fact; making them two would let a sheet be in a
    state where one is set and the other is not, which is a bug nobody can see. A sheet
    that marks nothing keeps the sideways scroll it has today, so shipping this cannot
    re-shape a page nobody touched (DL J15).
    """
    return [
        "key" in (specs.get(norm(cell)) or {}).get("roles", [])
        for cell in (rows[0] if rows else [])
    ]


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
    text. Markup cannot reorder a sheet -- that was the one non-negotiable constraint on
    in-cell prose (DL J17).

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
        # wrong column once earlier columns are gone. Specs do not need this treatment --
        # they are keyed by NAME for exactly this reason.
        pinned = column_index(header, pin_name) if pin_name else -1

    return [header] + body, pinned, options.get("caption")
