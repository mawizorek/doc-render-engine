"""Hook 07 -- the footer stamp.

Answers one question from any page without opening Actions: is what I am
looking at the latest push?

This matters more than it sounds. When a build fails, GitHub Pages keeps
serving the previous commit with no banner and no error page. The site simply
stops changing. There is no other signal that has happened, which is why this
hook exists at all and why it runs on every page rather than on one status
page nobody visits.

Renders the PR number, parsed from the head commit SUBJECT passed in by the
workflow:

    squash merge   'fix: repair the venue links (#16)'        -> PR #16
    merge commit   'Merge pull request #16 from owner/x'      -> PR #16
    direct push    'Update main-stage.md'                     -> short SHA

The SHA fallback is load-bearing, not a nicety: most edits to a content repo
are made from the GitHub UI edit pencil and never see a branch, so a stamp that
could only render a PR number would be blank most of the time.

Only the subject line is read. A commit body that happens to mention another
issue number must not win.

Deploy time lives in the `title` attribute, not the visible text (v1, reversed
2026-08-01 by Michael: 'footer should just say pr# and not date and time'). A
designer looking up a grid height does not need a clock. Hover or view-source
still recovers it, which is enough for the two or three people who ever need
to diagnose a frozen deploy.
"""

from __future__ import annotations

import datetime
import os
import re

from . import state

_PR = re.compile(r"#(\d+)")


def on_config(config):
    repo = state.INSTANCE.get("content_repo", "")
    base = "https://github.com/" + repo if repo else ""

    subject = os.environ.get("DOCRENDER_COMMIT_SUBJECT", "").strip().splitlines()
    found = _PR.findall(subject[0]) if subject else []
    sha = os.environ.get("DOCRENDER_COMMIT_SHA", "")

    if found and base:
        source = '<a href="' + base + "/pull/" + found[-1] + '">PR #' + found[-1] + "</a>"
    elif sha and base:
        source = '<a href="' + base + "/commit/" + sha + '">' + sha[:7] + "</a>"
    elif sha:
        source = sha[:7]
    else:
        source = "local"

    # Runners are UTC. Stamp Eastern so the number means something to a human
    # in Rochester rather than needing mental arithmetic at 4am.
    eastern = datetime.timezone(datetime.timedelta(hours=-4))
    when = datetime.datetime.now(datetime.timezone.utc).astimezone(eastern)
    stamp = when.strftime("%d %b %Y, %H:%M ET")

    engine = os.environ.get("DOCRENDER_ENGINE_REF", "")
    engine_bit = " &middot; engine " + engine if engine else ""

    config.copyright = (
        (config.copyright or "")
        + ' &middot; <span class="buildstamp" title="Deployed '
        + stamp
        + '">'
        + source
        + "</span>"
        + engine_bit
    )
    return config
