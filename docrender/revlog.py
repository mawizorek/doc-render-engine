"""Stage 01c -- the automatic revision log, rendered from the committed TSV.

A page carrying `<!-- dr:revlog -->` gets a two-column table -- when a change
landed and what it said -- drawn from the tab-separated file sitting beside it
in the content repo.

ONE CANONICAL FILE, AND THAT IS THE WHOLE POINT OF THIS VERSION (2026-08-04,
Michael: *"make it one canonical version served by the local repo worker on
every doc commit and make that the display in the actual rendered (2) column
version"*).

WHAT THIS REPLACED, because the history explains the shape. This module used to
shell out to `git log` in the content checkout at build time AND generate its
own `revision-log.tsv` into the site. Then the content repo grew a workflow that
regenerates a committed TSV on every doc commit. That left TWO files with the
same four columns and different freshness, which is one fact with two homes --
the exact arrangement every rot note in this repo warns about.

So the generator is gone. The workflow in the content repo produces the file;
this renders it. **The engine no longer has an opinion about git history.**

WHAT THAT BUYS:

  * one file to download, one file to trust, nothing to reconcile;
  * the table and the download are now provably the same data, because the
    table IS the file. They cannot disagree about content, only about age;
  * the shallow-clone trap leaves this file entirely. There is no `git log` call
    left to be quietly truncated, so `_shallow()` and its guard are deleted
    rather than kept as scaffolding. The trap still exists -- it just belongs to
    the workflow now, which pins `fetch-depth: 0` for its own reasons.

⚠️ WHAT IT COSTS, AND IT IS A REAL COST, NOT A FOOTNOTE. This page is now
DOWNSTREAM of something the build cannot see. If the content repo's workflow
fails, gets disabled, or is removed, the TSV silently stops advancing and this
table renders a stale log that looks perfectly healthy. The old version could
not be stale relative to its checkout, because it read the checkout.

That is why `on_page_markdown` puts the row count AND the newest row's date into
the build report every time. It is not a gate, it is a number a human can look
at: a revision log whose newest entry is four days old during a busy week is
visible in one line of build output.

🚫 AND IT IS DELIBERATELY NOT A HARD FRESHNESS GATE, which is worth writing down
before somebody adds one. The obvious check -- does the newest row match the
content repo's HEAD -- FAILS IN THE HEALTHY CASE. The workflow's own refresh
commit is excluded from the log by design (it is the loop brake), so HEAD is
routinely a commit the file correctly does not contain. A gate built on that
comparison would cry wolf on every normal publish and then be switched off.

🚫 STILL NO COMMIT COLUMN ON THE PAGE. The TSV has four columns (`when`,
`commit`, `pr`, `change`) and this table shows two. No-route-back-to-source is
LOCKED (2026-08-03; see instance.py and base.css, which strip the repo widget
twice over), and a hash column here would walk it back through a side door. In a
file the reader downloaded, a hash is data; on the page it is a route. **If a
commit column ever appears in `_table()`, that is the lock being reversed and it
needs Michael, not a tidy-up.**

WHICH FILE, AND WHY IT IS NEVER CONFIGURED. The TSV is the page's own sibling:
same directory, same basename, `.tsv` instead of `.md`. `automatic-revision-log`
is therefore its own data source, derived rather than declared.

That matters more than it looks. A hardcoded `01-utility/...` path would have
put one site's content layout inside a multi-site engine, which is the thing
`hooks/08_sizecheck.py`'s leak scan exists to catch. Instead the marker works on
any page in any instance that has a TSV beside it, and there is nothing to keep
in step.

⚠️ THE DOWNLOAD HREF IS COMPUTED, NOT WRITTEN, and this is the bug that already
bit once. With `use_directory_urls: true` a page at `01-utility/foo.md` is served
from `/01-utility/foo/` while its sibling TSV publishes to `/01-utility/foo.tsv`
-- one level UP from where the page lives in URL space. A bare relative
`foo.tsv` therefore 404s, which is exactly how the previous generated file was
unreachable for its whole short life. `posixpath.relpath` against the page's own
DEST path is used instead, so the link is correct at any depth and correct under
both URL styles.

⚠️ COLUMNS ARE FOUND BY HEADER NAME, NEVER BY POSITION. The file is written by a
workflow in a DIFFERENT REPOSITORY, so the two halves of this feature can be
edited months apart by someone holding only one of them. Positional reads would
turn a harmless column reorder into a table that renders confidently wrong data.
A missing `when` or `change` column is an error on the page instead.
"""

from __future__ import annotations

import html
import posixpath
import re
from pathlib import Path

from . import state

_MARKER = re.compile(r"[ \t]*<!--[ \t]*dr:revlog[ \t]*-->[ \t]*")

#: The two columns this table shows, by header name. The file has four.
_WHEN = "when"
_CHANGE = "change"


def _source(page) -> Path:
    """The TSV beside the page: same basename, `.tsv`. Derived, not configured."""
    return Path(page.file.abs_src_path).with_suffix(".tsv")


def _href(page) -> str:
    """A relative link from the page's URL to the TSV's published location.

    MkDocs copies the TSV to the site as an ordinary static file, so it lands at
    the source path with a `.tsv` extension. The page, under directory URLs,
    lands one level deeper than that. Computed rather than assumed -- see the
    module docstring for the 404 this replaced.
    """
    target = posixpath.splitext(page.file.src_uri)[0] + ".tsv"
    here = posixpath.dirname(page.file.dest_uri) or "."
    return posixpath.relpath(target, here)


def _read(path: Path) -> tuple[list[tuple[str, str]], str | None]:
    """(rows, problem). Exactly one of the two is meaningful."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return [], (
            "the revision log file " + path.name + " is not in the content "
            "repository yet. It is generated by that repo's revision-log "
            "workflow on the first commit to a document after it was added."
        )
    except (OSError, UnicodeDecodeError) as problem:
        return [], path.name + " could not be read (" + str(problem) + ")"

    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) < 2:
        return [], path.name + " has a header but no revisions in it"

    header = [cell.strip().lower() for cell in lines[0].split("\t")]
    try:
        when_at = header.index(_WHEN)
        change_at = header.index(_CHANGE)
    except ValueError:
        return [], (
            path.name + " is missing a '" + _WHEN + "' or '" + _CHANGE
            + "' column. Found: " + ", ".join(header or ["nothing"])
        )

    width = max(when_at, change_at) + 1
    rows = []
    for line in lines[1:]:
        cells = line.split("\t")
        if len(cells) < width:
            cells = cells + [""] * (width - len(cells))
        when, change = cells[when_at].strip(), cells[change_at].strip()
        if when or change:
            rows.append((when, change))
    if not rows:
        return [], path.name + " has a header but no revisions in it"
    return rows, None


def _when(iso: str) -> str:
    """`2026-08-03T23:31:07-04:00` -> `2026-08-03  11:31p`.

    Deliberately the same shape as the hand-written log this sits beside, so the
    two read as one habit rather than two systems. The FILE keeps full ISO,
    because a data file should sort; the formatting is a display concern and
    stays here.

    Anything that is not an ISO stamp is passed through untouched rather than
    mangled -- the file comes from another repository and this renderer is not
    the right place to be strict about it.
    """
    date, _, rest = iso.partition("T")
    hh, _, rest = rest.partition(":")
    mm = rest[:2]
    try:
        hour = int(hh)
    except ValueError:
        return iso
    suffix = "a" if hour < 12 else "p"
    twelve = hour % 12 or 12
    return date + "  " + str(twelve) + ":" + mm + suffix


def _error(message: str) -> str:
    state.note("notes", "revision log: " + message)
    return (
        '<p class="docrender-dead">Revision log unavailable: '
        + html.escape(message) + "</p>"
    )


def _table(rows: list[tuple[str, str]], href: str, name: str) -> str:
    """Two columns. `commit` and `pr` are file-only -- see the docstring."""
    out = [
        '<div class="dr-data dr-revlog">',
        # The class is required, not decorative: Material styles an unclassed
        # table with `display: block`, which destroys the sticky header. Same
        # note as datatable.py, same reason.
        '<table class="dr-data__table">',
        "<thead><tr><th>When</th><th>Change</th></tr></thead>",
        "<tbody>",
    ]
    for when, change in rows:
        out.append(
            "<tr><td>" + html.escape(_when(when)) + "</td><td>"
            + html.escape(change) + "</td></tr>"
        )
    out.append("</tbody></table>")
    out.append(
        '<p class="dr-data__source">' + str(len(rows)) + " revisions &middot; "
        + '<a href="' + html.escape(href) + '" download>' + html.escape(name)
        + "</a></p>"
    )
    out.append("</div>")
    return "\n".join(out)


def on_page_markdown(markdown, page, config, files):
    if not _MARKER.search(markdown):
        return markdown

    source = _source(page)
    rows, problem = _read(source)
    if problem:
        message = _error(problem)
        return _MARKER.sub(lambda _: message, markdown)

    state.REVLOG = rows

    # The staleness signal. Not a gate -- see the docstring for why a hard one
    # would fire on healthy publishes -- but a number in the build report that
    # makes "the workflow stopped running" visible instead of invisible.
    state.note(
        "notes",
        "revision log: " + str(len(rows)) + " revisions from " + source.name
        + ", newest " + (rows[0][0] or "undated"),
    )

    table = _table(rows, _href(page), source.name)
    return _MARKER.sub(lambda _: table, markdown)
