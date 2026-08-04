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

FOUR COLUMNS IN THE FILE, TWO ON THE PAGE (2026-08-04, Michael's call). The
asymmetry is the design and not an oversight, so it is written down here before
somebody "finishes" the table.

`revision-log.tsv` carries `when`, `commit`, `pr`, `change`. The rendered table
carries `When` and `Change`.

🚫 NO LINKS TO COMMITS, and no hash column ON THE PAGE. The house rule is that
a rendered site never advertises a route back to its source (LOCKED 2026-08-03;
see instance.py and base.css, which remove the repo widget twice over). A hash
column in the table would walk that rule back in through a side door.

A hash inside a DOWNLOADED DATA FILE is a different object: nothing is
clickable, nothing is composed into a URL, and a reader holding the TSV has
already opted into the machine-readable view. The lock governs what the SITE
points at, not which facts are allowed to exist. So the file is the full record
and the page is the readable one. **If a commit column ever appears in
`_table()`, that is the lock being walked back and it needs Michael rather than
a tidy-up.**

PR NUMBERS COME OUT OF THE SUBJECT LINE, because there is nowhere else to get
them. `git log` knows nothing about pull requests; the number survives only
because a squash merge writes it into the subject as a trailing `(#123)`. It is
parsed from there and REMOVED from the change text -- a number with its own
column should not also be trailing the sentence it was lifted out of.

⚠️ So the column is BLANK for anything that did not arrive by squash merge: a
direct commit, a rebase merge, a commit typed in the GitHub web editor. Blank
means "no number was recorded", never "no PR existed", and this column is not
evidence of process compliance.

⚠️ THE TSV IS WRITTEN BESIDE THE PAGE, NOT AT THE SITE ROOT (fixed 2026-08-04).
It used to land in `site_dir` while the table linked to it as a bare relative
`revision-log.tsv`. With `use_directory_urls: true` the log page is served from
`/01-utility/automatic-revision-log/`, so that href resolved to
`/01-utility/automatic-revision-log/revision-log.tsv` and 404'd. The file was
generated correctly, published correctly, and unreachable -- the same shape as
the root-index link bug fixed the day before, where a path was right in the
build directory and wrong in the URL space.

The fix is to put the file where the link already says it is, which is what
`state.REVLOG_DIRS` is for: on_page_markdown records the output directory of
every page carrying the marker, and on_post_build writes a copy into each. A
relative href then needs no knowledge of its own depth, and adding the marker
to a second page cannot break it.

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
#: Full `%H` rather than an abbreviation: this feeds a data column nobody reads
#: by eye, and an abbreviated hash is the one that can eventually collide.
_FORMAT = "%cI\t%H\t%s\x1e"

_LIMIT = 500

#: A trailing `(#123)` -- the only place in git where a PR number exists at all.
#: Anchored to the END of the subject on purpose: `(#4)` in the middle of a
#: sentence is somebody writing prose about an issue, not a merge.
_PR = re.compile(r"\s*\(#(\d+)\)\s*$")

_TSV_NAME = "revision-log.tsv"


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


def _commits() -> list[tuple[str, str, str, str]]:
    """(when, commit, pr, change) for every doc-touching commit, newest first."""
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
        stamp, _, rest = record.partition("\t")
        sha, _, subject = rest.partition("\t")
        subject = " ".join(subject.split())
        pr = ""
        found = _PR.search(subject)
        if found:
            pr = found.group(1)
            subject = _PR.sub("", subject).strip()
        out.append((stamp.strip(), sha.strip(), pr, subject))
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


def _table(rows: list[tuple[str, str, str, str]]) -> str:
    """Two columns. The commit and PR columns are FILE-ONLY -- see the docstring."""
    out = [
        '<div class="dr-data dr-revlog">',
        '<table class="dr-data__table">',
        "<thead><tr><th>When</th><th>Change</th></tr></thead>",
        "<tbody>",
    ]
    for stamp, _sha, _pr, subject in rows:
        out.append(
            "<tr><td>" + html.escape(_when(stamp)) + "</td><td>"
            + html.escape(subject) + "</td></tr>"
        )
    out.append("</tbody></table>")
    out.append(
        '<p class="dr-data__source">' + str(len(rows)) + " revisions &middot; "
        + '<a href="' + _TSV_NAME + '" download>' + _TSV_NAME + "</a></p>"
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

    # Where this page LANDS, not where it was written: the TSV has to be
    # published into the same directory the relative download link resolves
    # against. `foo/bar.md` -> `foo/bar/index.html` -> `foo/bar`.
    where = str(Path(page.file.dest_uri).parent)
    if where not in state.REVLOG_DIRS:
        state.REVLOG_DIRS.append(where)

    table = _table(rows)
    return _MARKER.sub(lambda _: table, markdown)


def on_post_build(config):
    """Publish the raw TSV beside every page that drew a table from it.

    Same bargain every data table on this site makes: what you are reading is
    drawn from a file you can download and open in a spreadsheet. Here the file
    is generated rather than committed, which is the only difference -- and it
    carries two columns the table does not.
    """
    rows = state.REVLOG
    if not rows:
        return

    if not state.REVLOG_DIRS:
        # Never fall back to the site root: that is exactly the bug this
        # replaced, and a file at an address nothing links to is worse than an
        # absent one because the build looks like it worked.
        state.note(
            "notes",
            "revision log: a table was rendered but no output directory was "
            "recorded, so " + _TSV_NAME + " was not written",
        )
        return

    lines = ["when\tcommit\tpr\tchange"]
    for stamp, sha, pr, subject in rows:
        lines.append("\t".join((stamp, sha, pr, subject.replace("\t", " "))))
    body = "\n".join(lines) + "\n"

    for where in state.REVLOG_DIRS:
        target = Path(config.site_dir) / where / _TSV_NAME
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
        except OSError as problem:
            # Not silent: the table on the page will be advertising a download
            # that is not there, and that is worth a line in the report.
            state.note(
                "notes",
                "revision log: could not write " + str(target) + " ("
                + str(problem) + ")",
            )
