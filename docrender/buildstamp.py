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


=============================================================================
🔴 IT NEVER PRINTED. FIXED 2026-08-19 BY MOVING IT OUT OF THE FOOTER ENTIRELY.
=============================================================================
This hook used to hand its markup to `config.copyright`, which Material renders
inside `.md-footer-meta`. `assets/print.css` hides that element in its chrome-off
list, with `!important`, and then separately tried to bring `.buildstamp` back:

    .md-footer-meta { display: none !important; }   <- the ancestor
    .buildstamp     { display: block; }             <- could never win

⚠️ `display: none` ON AN ANCESTOR REMOVES THE WHOLE SUBTREE FROM THE BOX TREE.
A descendant cannot opt back in -- it is not a specificity contest, the box does
not exist to style. So the exception print.css argues hardest for, in its own
words *"the one question nobody can answer about a piece of paper is how old it
is"*, has never once fired.

⭐ CONFIRMED FROM OUTPUT, NOT FROM REASONING, and that distinction is the reason
it took a day. The suspicion came from knowing Material's footer structure,
which is a PROXY read and this house has a scar about presenting one as a
verification (`instances/uritp-safety/site.yml`, the `database` theme claim).
The first two PDFs could not settle it either, because that page carried
`hide: [footer]` and no footer could print there regardless. A third PDF --
General Safety Responsibilities, `hide: [navigation, toc]`, footer NOT hidden --
showed no stamp, no PR number, no SHA, no `unstamped`. That is the evidence.

🔴 AND THE CSS FIX WAS THE WRONG FIX, WHICH IS THE FINDING WORTH KEEPING.
Hoisting `.buildstamp` out of the hidden subtree in the stylesheet would have
repaired exactly one class of page and left the hole open, because `hide: footer`
is a CONTENT decision and pages already use it -- `uritp-safety/20-policies/`
`11-fire.md` carries it today. Fix the CSS and that page still prints undated
forever, with nothing reporting it.

⚑ A rule that can be switched off by a frontmatter key it does not know about is
not a guarantee. The stamp had to leave the footer, not be rescued inside it.

✅ SO IT IS NOW CONTENT. `on_page_content` appends the same element to the end of
the page body, which is:

  - immune to `hide: footer`, because that key hides Material's footer region and
    has no opinion about the content column;
  - immune to the chrome-off list, because nothing in that list is an ancestor of
    the content column -- print.css no longer needs its `.buildstamp` exception
    to be a special case at all;
  - in the same place `specs/print-identity.md` §4 wants a printed provenance
    line to be, at the foot of the document rather than in page furniture.

⭐ AND IT IS THE PATTERN `pagefoot.py` ALREADY USES, one hook number earlier. Two
foot lines, one mechanism, and the ORDER IS FREE RATHER THAN LUCKY: MkDocs runs
`on_page_content` in hook order, `pagefoot` is 06 and this is 07, so the edit link
appends first and the stamp lands after it. Both append rather than insert, so
neither can displace the other.

⚠️ WHAT THIS COSTS ON SCREEN, STATED RATHER THAN DISCOVERED. The stamp used to
sit in the footer bar and now sits at the end of the content column, on all six
sites. That is a real visual change for readers who never print, and it is the
price of the fix rather than a bonus. It is defensible on the hook's own terms --
the stamp answers a question about THE PAGE, and it now sits with the page -- but
if Michael dislikes it, the argument to revisit is about SCREEN placement and
must not reintroduce a footer-only element.

🚫 AND `config.copyright` IS NOW UNSET RATHER THAN LEFT IN PLACE. Emitting both
would put two stamps on every screen page and two on every printed sheet: a
second claimant on one truth, which is the defect this repo has retired three
manifests over. One element, one home.

⚠️ THE LABEL IS STILL COMPUTED ONCE PER BUILD, at `on_config`, and only the
emit is per page. The inputs are three environment variables and a clock; reading
them on every page would be waste, and worse, a build spanning midnight could
stamp two different dates onto one site.
"""

from __future__ import annotations

import datetime
import html
import os
import re

from . import state

_PR = re.compile(r"#(\d+)")

#: The rendered element, built once at `on_config` and appended to every page.
#: Module-level rather than in `state` because nothing else consumes it and a
#: shared namespace is for shared facts.
_STAMP = ""


def on_config(config):
    global _STAMP

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

    # The site name travels with the label, because a printed sheet leaves the
    # system entirely and 'PR #12' alone names nothing a reader can place.
    name = str(getattr(config, "site_name", "") or "").strip()
    text = (name + " · " + label) if name else label

    _STAMP = (
        '<p class="buildstamp" title="' + html.escape(detail, quote=True) + '">'
        + html.escape(text) + "</p>"
    )

    # 🚫 Deliberately NOT set. See the docstring: two stamps would be two
    # claimants on one truth.
    config.copyright = None
    return config


def on_page_content(html_body, page, config, files):
    """Append the stamp to the end of the page body.

    Unconditional on purpose. `pagefoot.py` skips generated pages because there
    is no source file to offer an edit link for; a build stamp has no such
    dependency, and a generated page is exactly as capable of being stale as an
    authored one.
    """
    if not _STAMP:
        return html_body
    return html_body + _STAMP
