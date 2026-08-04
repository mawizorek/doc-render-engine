"""Stage 01c -- the automatic revision log, read out of git at build time.

A page carrying `<!-- dr:revlog -->` gets a table of every commit that touched
a document in this content repo: when it landed, and what its message said.

WHY THIS IS DERIVED AND NOT APPENDED, because the obvious design is the other
one and it is worse in four separate ways.

The obvious design: a workflow in the content repo fires on push, appends a row
to a TSV, and commits it. That would mean

  1. **machinery in the content tree**, whose one rule is that it holds
     documents and nothing else -- the rule the green Download ZIP exists to
     protect;
  2. **a bot commit that is itself a commit**, so the workflow triggers itself
     and needs a path filter to stop, which is a loop guarded by a convention;
  3. **a second copy of something git already stores**, and the duplicate is
     always the one that rots (a force-push, a failed run, a rebase, and the
     file and the history disagree with nothing to reconcile them);
  4. **a log that can lie**, because a file is edited by hand and a history is
     not.

So the log is not a record of commits. **It is git, formatted.** There is
nothing to keep in sync, because there is only one copy.

WHAT IT COSTS, stated plainly: the page updates when the site is PUBLISHED, not
when a commit lands. That sounds like the weakness and is actually the point.
The site only changes on publish, so a log listing commits that are not live
yet would be describing changes no reader can see. The log is exactly as fresh
as the thing it describes, which is the only correctness available here.

🚫 NO LINKS TO COMMITS. The house rule is that a rendered site never advertises
a route back to its source (LOCKED 2026-08-03; see instance.py and base.css,
which remove the repo widget twice over). A commit hash column would walk that
rule back in through a side door, so the log carries WHEN and WHAT and nothing
clickable.

⚠️ SHALLOW CLONES ARE THE TRAP HERE and the reason `_shallow()` exists. A CI
checkout defaults to depth 1. `git log` in a shallow clone does not error --
it cheerfully returns the two commits it has, which renders as a complete-
looking revision log covering ten minutes of a two-year project. That is the
exact silent-degradation shape this repo keeps getting bitten by, so a shallow
repo renders a visible error instead of a plausible table.
"""

from __future__ import annotations

import html
import os
import re
import subprocess
from pathlib import Path

from . import state

_MARKER = re.compile(r"[ \t]*<!--[ \t]*dr:revlog[ \t]*-->[ \t]*")

#: What counts as "a doc". Markdown plus the data files a page can declare --
#: a TSV edit changes what a reader sees, so it is a revision like any other.
_PATHS = ("*.md", "*.tsv")

#: One record per line, tab-separated, with a unit separator between records so
#: a commit message containing a newline cannot be read as two commits.
_FORMAT = "%cI\t%s\x1e"

_LIMIT = 500


def _content_dir() -> Path:
    return Path(os.environ.get("DOCRENDER_CONTENT", "content")).resolve()


def _git(*args: str) -> str | None:
    """Run git in the content tree. None on any failure, never an exception.

    A build must not die because a revision log could not be read. The page
    says so instead.
    """
    try:
        done = subprocess.run(
            ("git", "-C", str(_content_dir())) + args,
            capture_output=True, text=True, timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def _shallow() -> bool:
    """Is the content checkout truncated.

    THE most important function in this file. A shallow clone answers `git log`
    without complaint and returns whatever it happens to hold, so the failure
    mode is a revision log that looks finished and covers an afternoon.
    """
    answer = _git("rev-parse", "--is-shallow-repository")
    return (answer or "").strip() == "true"


def _commits() -> list[tuple[str, str]]:
    raw = _git(
        "log", "--no-merges", "--date-order",
        "--max-count=" + str(_LIMIT),
        "--pretty=format:" + _FORMAT,
        "--", *_PATHS,
    )
    if raw is None:
        return []

    out = []
    for record in raw.split("\x1e"):
        record = record.strip("\n")
        if not record.strip():
            continue
        stamp, _, subject = record.partition("\t")
        out.append((stamp.strip(), " ".join(subject.split())))
    return out


def _when(iso: str) -> str:
    """`2026-08-03T23:31:07-04:00` -> `2026-08-03  11:31p`.

    Deliberately the same shape as the hand-written log this sits beside, so
    the two read as one habit rather than two systems.
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


def _table(rows: list[tuple[str, str]]) -> str:
    out = [
        '<div class="dr-data dr-revlog">',
        '<table class="dr-data__table">',
        "<thead><tr><th>When</th><th>Change</th></tr></thead>",
        "<tbody>",
    ]
    for stamp, subject in rows:
        out.append(
            "<tr><td>" + html.escape(_when(stamp)) + "</td><td>"
            + html.escape(subject) + "</td></tr>"
        )
    out.append("</tbody></table>")
    out.append(
        '<p class="dr-data__source">' + str(len(rows)) + " revisions &middot; "
        + '<a href="revision-log.tsv" download>revision-log.tsv</a></p>'
    )
    out.append("</div>")
    return "\n".join(out)


def on_page_markdown(markdown, page, config, files):
    if not _MARKER.search(markdown):
        return markdown

    if _git("rev-parse", "--git-dir") is None:
        message = _error(
            "the content tree is not a git checkout, so there is no history "
            "to read"
        )
        return _MARKER.sub(lambda _: message, markdown)

    if _shallow():
        message = _error(
            "the content checkout is SHALLOW, so its history is truncated. "
            "Refusing to render a partial log that would look complete. Set "
            "fetch-depth: 0 on the content checkout."
        )
        return _MARKER.sub(lambda _: message, markdown)

    rows = _commits()
    if not rows:
        message = _error("no commits touching a document were found")
        return _MARKER.sub(lambda _: message, markdown)

    state.REVLOG = rows
    table = _table(rows)
    return _MARKER.sub(lambda _: table, markdown)


def on_post_build(config):
    """Publish the raw TSV beside the site, so the table has a real source.

    Same bargain every data table on this site makes: what you are reading is
    drawn from a file you can download and open in a spreadsheet. Here the file
    is generated rather than committed, which is the only difference.
    """
    rows = state.REVLOG
    if not rows:
        return
    lines = ["when\tchange"]
    for stamp, subject in rows:
        lines.append(stamp + "\t" + subject.replace("\t", " "))
    try:
        (Path(config.site_dir) / "revision-log.tsv").write_text(
            "\n".join(lines) + "\n", encoding="utf-8"
        )
    except OSError:
        pass
