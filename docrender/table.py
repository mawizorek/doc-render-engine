"""A shaped sheet as finished HTML. The last step, and only that step.

Split out of `datatable.py` on 2026-08-04, when adding roles, labels and money carried
that module to 21.2KB -- past the 18KB warn line and within 1.4KB of the hard one, which
is the point where a file stops coming back whole from one read and therefore stops being
safely editable. **The trim is the reflex and the split is the answer**, for the fourth
time in two days: `seal.py` out of `router.py`, `sheet.py` out of `datatable.py`,
`data.css` out of `base.css`, this.

**And the seam is one `datatable.py` already claimed in prose and had stopped honouring.**
Its own docstring says it owns "the frontmatter contract, the `!!! data` block, and the
HTML" -- three jobs listed as though they were one. They are not, and the third had grown
larger than the first two together.

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


TWO THINGS THAT LOOK WRONG FROM OUTSIDE
=======================================

⚠️ **A MONEY CELL IS THE ONE PLACE THIS FEATURE EDITS A DISPLAYED VALUE.** It is padded to
two decimals, because a money column with ragged decimals cannot be scanned and scanning
is the entire reason the type exists. That is a real exception to the standing rule that
the sheet is the source of truth and the renderer does not reinterpret it (J10), so it is
held as narrow as it can be: only a cell that is NOTHING BUT a number is touched.
`[1200]{.est}` and `TBD` pass through verbatim, because rebuilding markup around a
reformatted number is how a renderer starts quietly rewriting a sheet.

⭐ **THE CURRENCY SYMBOL IS NOT HERE AT ALL.** `data.css` draws it with `::before` from
`--dr-money-symbol`. So the DATA stays a number -- still sortable, still summable, still
honest in the downloaded TSV -- and each site picks its own currency without this module
knowing any exist. A symbol written into the value would have been a second, worse copy of
the same decision.

⚠️ **`_BOOT` IS INLINE AND MUST STAY INLINE.** Detail cells are hidden only under
`html.dr-data-js`, and that class is set by a script that runs during PARSE. Two reasons,
both scars. A reader with no JavaScript gets the entire table rather than a list that
cannot be opened -- **fail OPEN**, because a list nobody can expand looks like data loss
and reports nothing. And setting the class from the deferred sheet instead would let the
detail rows paint and then vanish on every page load, which is precisely the flash PR #49
removed from the router the same day. A boot script is idempotent, so a page with three
tables emitting it three times costs nothing.
"""

from __future__ import annotations

import html
import re

from . import cells, sheet

_PURE_NUMBER = re.compile(r"^[-+]?\d+(?:\.\d+)?$")

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

    # ⚠️ THE TABLE CARRIES A CLASS AND THAT IS LOAD-BEARING (2026-08-03). Material styles
    # `.md-typeset table:not([class])` with `display: block`, which destroys the internal
    # table layout -- and a `position: sticky` cell inside a non-table has no row context
    # to stick within, so the frozen header and first column silently did nothing. The
    # class makes `:not([class])` stop matching. Do not remove it.
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
            # 🐛 THE LABEL IS THE STICKY ELEMENT, NOT THE CELL. The band is a `<th
            # colspan=N>`, so its width IS the scroll width and `sticky; left: 0` on it
            # has no slack to move within -- the heading scrolled away with the row and
            # read as `WARE [2000]` three columns in. The span can stick; the cell never
            # could. Same shape as the `display: block` trap above.
            out.append(
                '<tr class="dr-data__section"><th colspan="' + str(span) + '">'
                + '<span class="dr-data__section-label">' + cells.render(row[0], page)
                + "</span></th></tr>"
            )
            continue
        records += 1
        out.append("<tr>")
        for i, cell in enumerate(row):
            value = _money(cell) if i < len(kinds) and kinds[i] == "money" else cell
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
