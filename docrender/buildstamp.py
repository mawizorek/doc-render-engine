"""Hook 07 -- the footer stamp.

Answers one question from any page without opening Actions: is what I am
looking at the latest push?

That matters more than it sounds. When a build fails, GitHub Pages keeps
serving the previous commit with no banner and no error page. The site simply
stops changing. There is no other signal that has happened, which is why this
exists at all and why it runs on every page rather than on a status page
nobody visits.

WHAT IS VISIBLE, and it is deliberately almost nothing:

    URITP Production Resources · PR #12

The deploy time, the engine version and the commit hash all live in the `title`
attribute. A designer looking up a grid height does not need a clock or a
forty-character hash, and the three or four times a year somebody debugs a
frozen deploy, a hover or a view-source recovers everything.

⚠️ NOT A LINK ANY MORE (2026-08-03). It used to link to the PR. The rendered
site no longer advertises its repository at all -- the header widget went for
the same reason -- so the stamp names the PR without offering a door to it.

The number is parsed from the head commit SUBJECT:

    squash merge   'fix: repair the venue links (#16)'   -> PR #16
    direct push    'Update main-stage.md'                -> short SHA

The SHA fallback is load-bearing: most edits to a content repo are made from
the GitHub UI and never see a branch, so a stamp that could only render a PR
number would be blank most of the time.

Only the subject line is read. A commit body that mentions another issue number
must not win.
"""

from __future__ import annotations

import datetime
import os
import re

from . import state

_PR = re.compile(r"#(\d+)")


def on_config(config):
    subject = os.environ.get("DOCRENDER_COMMIT_SUBJECT", "").strip().splitlines()
    found = _PR.findall(subject[0]) if subject else []
    sha = os.environ.get("DOCRENDER_COMMIT_SHA", "")

    if found:
        label = "PR #" + found[-1]
    elif sha:
        label = sha[:7]
    else:
        # A local build, or the workflow failed to pass the commit through.
        # Said plainly rather than dressed up: a stamp that lies about being a
        # deploy is worse than one that admits it does not know.
        label = "unstamped"

    # Runners are UTC. Stamp Eastern so the number means something to a human
    # in Rochester rather than needing mental arithmetic at 4am.
    eastern = datetime.timezone(datetime.timedelta(hours=-4))
    when = datetime.datetime.now(datetime.timezone.utc).astimezone(eastern)

    detail = "Deployed " + when.strftime("%d %b %Y, %H:%M ET")
    engine = os.environ.get("DOCRENDER_ENGINE_REF", "")
    if engine:
        detail += " · engine " + engine[:7]
    if sha:
        detail += " · content " + sha[:7]

    config.copyright = (
        '<span class="buildstamp" title="' + detail + '">' + label + "</span>"
    )
    return config
