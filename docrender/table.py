"""A shaped sheet as finished HTML. The last step, and only that step.

Split out of `datatable.py` on 2026-08-04, when adding roles, labels and money carried
that module to 21.2KB -- past the 18KB warn line and within 1.4KB of the hard one, which
is the point where a file stops coming back whole from one read and therefore stops being
safely editable. **The trim is the reflex and the split is the answer.**

**And the seam is one `datatable.py` already claimed in prose and had stopped honouring.**
Its docstring said it owned "the frontmatter contract, the `!!! data` block, and the
HTML" -- three jobs listed as though they were one, and the third had grown larger than
the other two together.

FOUR MODULES, ONE FEATURE:

    sheet.py     reading and shaping a TSV. Rows, header, sections, options, order, kind.
    cells.py     one cell as prose. Markers, @refs, inline markdown, escaping.
    this file    shaped rows -> markup. Column classes, roles, labels, the list shell.
    datatable.py the frontmatter contract and the `!!! data` block.


WHAT A CELL CARRIES, AND WHY EACH PART IS THERE
===============================================

    <td class="dr-col--num dr-detail" data-label="Credits">4</td>

`dr-col--<kind>` is the column's TYPE, from `sheet.column_kinds` -- derived from the
values, overridden by a `::type` in the header cell. `assets/data.css` decides what each
kind looks like; this module has no opinion beyond naming it.

`dr-key` / `dr-detail` is the column's ROLE, and it appears ONLY when some column declared
`.key`. No key, no roles, no restructure, and every sheet already on the site renders
exactly as it did before this existed (DL J15: shipping a feature must not re-shape a page
nobody touched).

`data-label` is the field name, and it is not redundant with the header. **Once list mode
stops drawing a grid, the header row is gone** -- so the label has to travel with the
value or a reader sees `4` with nothing to say what four means.

🐛 **AN EMPTY DETAIL CELL IS NOT EMITTED AT ALL, AND THAT IS TWO FIXES IN ONE.** A commit
with no pull request rendered a bare `PR` label with nothing beside it -- **a label with
no value is worse than an absent row, because it reads as data that failed to load.** And
it had disarmed a rule shipped hours earlier: `data-list.css` hides the chevron on
`tr:not(:has(td.dr-detail))`, which could never match while every row carried a detail
cell regardless of content. **A guard written against a condition the emitter never
produced.** ⚠️ An empty KEY cell is still emitted: keys hold their position in the
summary, and dropping one would slide the title up into the eyebrow slot.


TWO PLACES THIS EDITS A DISPLAYED VALUE, AND BOTH ARE THE SAME BARGAIN
======================================================================

The standing rule is that the sheet is the source of truth and the renderer does not
reinterpret it (J10). These are the two stated exceptions, and each is held as narrow as
it can be: **the DATA stays canonical in the cell, and only the PRESENTATION moves here.**

⚠️ **MONEY** is padded to two decimals, because a money column with ragged decimals cannot
be scanned and scanning is the entire reason the type exists. Only a cell that is NOTHING
BUT a number is touched -- `[1200]{.est}` and `TBD` pass through verbatim, because
rebuilding markup around a reformatted number is how a renderer starts quietly rewriting a
sheet. ⭐ The currency SYMBOL is not here at all: `data.css` draws it with `::before` from
`--dr-money-symbol`, so the cell keeps a real number and each site picks its own currency.

⚠️ **DATE** renders an ISO stamp as `Aug 4 · 7:58p`. The cell keeps the ISO, which sorts
correctly as plain text and opens correctly in a spreadsheet; the reader gets something
legible. **There is deliberately no format option.** The moment this takes a pattern
argument, every sheet decides what a date looks like on this site and they stop agreeing
-- which is the defect the whole `::type` grammar exists to prevent. Anything that is not
an ISO stamp passes through untouched rather than being mangled.


THE TWO STICKY TRAPS
====================

⚠️ THE TABLE CARRIES A CLASS AND THAT IS LOAD-BEARING (2026-08-03). Material styles
`.md-typeset table:not([class])` with `display: block`, which destroys the internal table
layout -- and a `position: sticky` cell inside a non-table has no row context to stick
within, so the frozen header and first column silently did nothing. Do not remove it.

🐛 A SECTION BAND'S LABEL LIVES IN AN INNER `<span>`. The band is a `<th colspan="N">`, so
its width IS the scroll width and `sticky; left: 0` on it has no slack to move within --
the heading scrolled away and read as `WARE [2000]` three columns in. The span can stick;
the cell never could. **Same shape as the trap above: sticky failing silently because the
box it sits in cannot honour it.**
"""

from __future__ import annotations

import html
import re

from . import cells, sheet

_PURE_NUMBER = re.compile(r"^[-+]?\d+(?:\.\d+)?$")

#: `2026-08-04T19:58:50-04:00`, and the time part is optional. Anchored whole: a cell that
#: merely CONTAINS a date is prose about a date, not a date.
_ISO = re.compile(
    r"^(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})"
    r"(?:[T ](?P<hh>\d{2}):(?P<mm>\d{2})(?::\d{2})?"
    r"(?:\.\d+)?(?:Z|[-+]\d{2}:?\d{2})?)?$"
)

_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

_BOOT = '<script>document.documentElement.classList.add("dr-data-js")</script>'


def _money(cell: str) -> str:
    """Two decimals, but ONLY on a cell that is nothing but a number."""
    raw = str(cell).strip()
    if not _PURE_NUMBER.match(raw):
        return cell
    try:
        return format(float(raw), ".2f")
    except ValueError:
        return cell


def _date(cell: str) -> str:
    """`2026-08-04T19:58:50-04:00` -> `Aug 4 · 7:58p`. Anything else, untouched.

    ⚠️ NO TIMEZONE CONVERSION. The offset in the stamp is discarded and the wall-clock
    time is printed as written, because the stamp was recorded in the timezone of whoever
    made the change and re-projecting it into some other zone would make the log disagree
    with the moment it describes. A date column is a record of when something happened,
    not an instant to do arithmetic on.

    ⚠️ The YEAR is dropped, and that is a real cost stated rather than hidden: this reads
    well on a log of recent activity and badly on one spanning years. If a sheet ever
    needs the year, that is the argument for a second type -- NOT for a format option,
    which would let every sheet answer this question differently.
    """
    match = _ISO.match(str(cell).strip())
    if not match:
        return cell
    try:
        month = _MONTHS[int(match.group("m")) - 1]
    except (ValueError, IndexError):
        return cell
    out = month + " " + str(int(match.group("d")))
    if match.group("hh") is None:
        return out
    hour = int(match.group("hh"))
    suffix = "a" if hour < 12 else "p"
    return out + " · " + str(hour % 12 or 12) + ":" + match.group("mm") + suffix


#: kind -> the function that turns a stored value into a displayed one.
_DISPLAY = {"money": _money, "date": _date}


def _attrs(index, pinned, kinds, keys, labels, listing) -> str:
    """The class and label attributes for one cell."""
    names = []
    if index < len(kinds):
        names.append("dr-col--" + kinds[index])
    if listing:
        names.append("dr-key" if keys[index] else "dr-detail")
    if index == pinned:
        names.append("dr-data__pin")
    out = ' class="' + " ".join(names) + '"' if names else ""
    if listing and index < len(labels) and not keys[index]:
        out += ' data-label="' + html.escape(labels[index], quote=True) + '"'
    return out


def draw(rows, specs, href, filename, slot, caption, pinned, page) -> str:
    """Shaped rows as one `.dr-data` block. Every cell goes through cells.render once."""
    header, body = rows[0], rows[1:]
    span = len(header)
    # Once per table, from the SHAPED rows -- so `hide:` has already run and both lists
    # line up with the columns that actually get drawn.
    kinds = sheet.column_kinds(rows, specs)
    keys = sheet.key_columns(rows, specs)
    listing = any(keys)
    labels = [cells.plain(c) for c in header]

    out = []
    if listing:
        out.append(_BOOT)
    out.append(
        '<div class="dr-data' + (" dr-data--list" if listing else "")
        + '" id="data-' + html.escape(slot) + '">'
    )
    if caption:
        out.append('<p class="dr-data__caption">' + cells.render(caption, page) + "</p>")

    out.append('<table class="dr-data__table">')
    out.append("<thead><tr>")
    for i, cell in enumerate(header):
        label = "" if sheet.is_junk(cell) else cells.render(cell, page)
        out.append(
            "<th" + _attrs(i, pinned, kinds, keys, labels, listing) + ">" + label + "</th>"
        )
    out.append("</tr></thead>")
    out.append("<tbody>")

    records = 0
    for row in body:
        if sheet.is_section(row):
            out.append(
                '<tr class="dr-data__section"><th colspan="' + str(span) + '">'
                + '<span class="dr-data__section-label">' + cells.render(row[0], page)
                + "</span></th></tr>"
            )
            continue
        records += 1
        out.append("<tr>")
        for i, cell in enumerate(row):
            kind = kinds[i] if i < len(kinds) else ""
            # An empty DETAIL is dropped entirely -- see the module docstring. An empty
            # KEY is kept, because it holds its place in the summary.
            if listing and not keys[i] and not str(cell).strip():
                continue
            display = _DISPLAY.get(kind)
            value = display(cell) if display else cell
            out.append(
                "<td" + _attrs(i, pinned, kinds, keys, labels, listing) + ">"
                + cells.render(value, page) + "</td>"
            )
        if listing:
            # A real button, so the row is reachable and announced without a pointer. The
            # whole row is also clickable (data.js), but a control that exists only inside
            # a click handler is a control a keyboard user does not have.
            out.append(
                '<td class="dr-data__more"><button type="button" '
                'class="dr-data__toggle" aria-expanded="false" aria-label="Show all '
                'fields for ' + html.escape(cells.plain(row[0]), quote=True)
                + '"></button></td>'
            )
        out.append("</tr>")

    out.append("</tbody></table>")
    out.append(
        '<p class="dr-data__source">' + str(records) + " rows &middot; "
        + '<a href="' + html.escape(href) + '" download>' + html.escape(filename)
        + "</a></p>"
    )
    out.append("</div>")
    return "\n".join(out)
