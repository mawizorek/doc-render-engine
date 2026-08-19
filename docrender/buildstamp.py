"""Hook 07 -- the build stamp. Two placements, two audiences, one fact.

Answers one question from any page without opening Actions: is what I am
looking at the latest push?

That matters more than it sounds. When a build fails, GitHub Pages keeps
serving the previous commit with no banner and no error page. The site simply
stops changing. There is no other signal that has happened, which is why this
exists at all and why it runs on every page rather than on a status page
nobody visits.

The number is parsed from the head commit SUBJECT:

    squash merge   'fix: repair the venue links (#16)'   -> PR #16
    direct push    'Update main-stage.md'                -> short SHA

The SHA fallback is load-bearing: most edits to a content repo are made from
the GitHub UI and never see a branch, so a stamp that could only render a PR
number would be blank most of the time.

Only the subject line is read. A commit body that mentions another issue number
must not win.

⚠️ NOT A LINK (2026-08-03). It used to link to the PR. The rendered site no
longer advertises its repository at all -- the header widget went for the same
reason -- so the screen stamp names the PR without offering a door to it.


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
is"*, had never once fired.

⭐ CONFIRMED FROM OUTPUT, NOT FROM REASONING, and that distinction is the reason
it took a day. The suspicion came from knowing Material's footer structure,
which is a PROXY read and this house has a scar about presenting one as a
verification (`instances/uritp-safety/site.yml`, the `database` theme claim).
The first two PDFs could not settle it either, because that page carried
`hide: [footer]` and no footer could print there regardless. A third PDF --
General Safety Responsibilities, `hide: [navigation, toc]`, footer NOT hidden --
showed no stamp, no PR number, no SHA, no `unstamped`. That is the evidence.

🔴 AND THE CSS FIX WAS THE WRONG FIX. Hoisting `.buildstamp` out of the hidden
subtree in the stylesheet would have repaired exactly one class of page and left
the hole open, because `hide: footer` is a CONTENT decision and pages already use
it -- `uritp-safety/20-policies/11-fire.md` carries it today. ⚑ A rule that can be
switched off by a frontmatter key it does not know about is not a guarantee.


=============================================================================
⭐ TWO PLACEMENTS, AND THEY CARRY DIFFERENT TEXT ON PURPOSE
=============================================================================
> Michael, 2026-08-19: *"corner mark print only."* Then, on seeing it:
> *"I definitely do not want that PR number in the header. I'm fine with URITP
> safety in the date, but I definitely do not want the PR number in that!"*

    .buildstamp--corner   FIRST in flow, PRINT ONLY.   `URITP Safety · 19 Aug 2026`
    .buildstamp--foot     LAST in flow, SCREEN ONLY.   `URITP Safety · PR #157`

🔴 THE PR NUMBER IS SCREEN-ONLY, AND THE REASON IS AUDIENCE RATHER THAN TASTE.
A screen reader of these sites is Michael or a collaborator, and `PR #157`
answers *is this deploy current* for exactly that person. A printed sheet goes to
a guest artist, a student, a binder, a wall -- and to that reader a PR number is
unreadable internal plumbing on a safety document. ⚑ A build identifier is
provenance for the BUILDER and noise for the READER, and print is the surface
where the reader is not the builder.

⭐ AND IT IS THE SAME RULE THIS FAMILY ALREADY LOCKED, arriving from a new angle.
`assets/base.css` carries NO ROUTE BACK TO THE SOURCE; `pagefoot.py` records that
`repo_url` is unset so no repository widget appears; `instances/uritp-safety/`
`site.yml` sets `edit_links: false` because *"a link that looks like an invitation
and delivers a 404 is a DEAD CONTROL."* A PR number on a printed policy is the
same category: a reference to a system the reader cannot reach. **The rule was
already written down and the corner stamp was the first surface to break it.**

⚠️ SO THE PRINTED SHEET NO LONGER NAMES A COMMIT AT ALL, and that is a real
trade rather than a free win. Debugging a stale PRINTED page now means finding the
page on screen and reading the foot line. Correct for these documents -- the date
is the provenance a reader actually needs, and it is what Michael asked for -- but
if a printed sheet ever has to be traced back to a specific build, THIS is the
decision to revisit.

🔴 THE HOVER DETAIL IS DELIBERATELY UNCHANGED, AND ON THE CORNER IT IS DEAD
WEIGHT. Both nodes keep the same `title` (deploy time, engine SHA, content SHA).
On paper there is no hover, so the corner's copy is never readable by anybody --
it survives because the two nodes are built from one string and splitting the
detail as well would be a second divergence for no gain. ⚠️ It DOES mean a commit
SHA is present in the printed page's HTML source even though it never renders. If
that ever matters, drop the attribute from the corner only.

⭐ ONE COMPUTED VALUE PER FACT, TWO PRESENTATIONS -- NOT TWO CLAIMANTS. The defect
that retired `roster.json`, `registry.json` and `app-index.md` is two SOURCES of
one fact, which can disagree. `_label()` and the clock are each read exactly once
per build; the two nodes SELECT from those values rather than recomputing them.
They cannot drift, and the mutually exclusive media scoping means a reader always
sees exactly one stamp.

⭐ WHY THE CORNER COPY MUST BE FIRST IN THE FLOW, WHICH IS THE WHOLE MECHANISM.
An element appended at the END of the content cannot be moved to the TOP of sheet
one by CSS: that needs knowledge of where the page boundary falls, which is
exactly what `@page` margin boxes do and no major browser implements. First in
flow IS the top of sheet one, for free, with no pagination machinery.

🔴 THE `hidden` ATTRIBUTE IS DOING REAL WORK AND IS NOT DECORATION. The corner
copy ships with `hidden`, which the UA stylesheet implements as `display: none`.
Any AUTHOR `display` declaration beats a UA one, so `@media print { display:
block }` reveals it on paper and nothing reveals it on screen. ⭐ That is what
keeps this feature from touching a single screen stylesheet. ⚠️ It also drops the
corner copy from the accessibility tree, which is CORRECT here -- the foot copy is
the one a screen reader should find.

⚠️ THE ICON IS NOT WIRED YET, AND THERE IS DELIBERATELY NO DEAD CSS FOR IT.
`uritp-safety/90-media-logos/` holds `logo-horizontal.jpg` and `logo-square.jpg`,
both already reachable as `@img:` targets with no engine change -- but Michael
asked for a line-art SVG, which does not exist yet. When it does, the image lands
as a print-scoped `background-image` on `.buildstamp--corner`. 🚫 NEVER an `<img>`:
a `display: none` image is still FETCHED, ~168KB on every page load of a site
whose readers mostly never print.

⚠️ THE LABEL IS STILL COMPUTED ONCE PER BUILD, at `on_config`, and only the emit
is per page. The inputs are three environment variables and a clock; reading them
per page would be waste, and worse, a build spanning midnight could stamp two
different dates onto one site.

🚫 AND `config.copyright` STAYS UNSET. Material renders it inside the footer
region, which is the place this hook exists to have escaped.
"""

from __future__ import annotations

import datetime
import html
import os
import re

_PR = re.compile(r"#(\d+)")

#: The two rendered elements, built once at `on_config`. See the docstring on why
#: they carry different text and why that is still one claimant.
_CORNER = ""
_FOOT = ""


def _label() -> str:
    """`PR #16`, or a short SHA, or an honest admission.

    ⚠️ SCREEN ONLY as of 2026-08-19. Nothing this returns reaches paper.
    """
    subject = os.environ.get("DOCRENDER_COMMIT_SUBJECT", "").strip().splitlines()
    found = _PR.findall(subject[0]) if subject else []
    sha = os.environ.get("DOCRENDER_COMMIT_SHA", "")

    if found:
        return "PR #" + found[-1]
    if sha:
        return sha[:7]
    # A local build, or the workflow failed to pass the commit through. Said
    # plainly rather than dressed up: a stamp that lies about being a deploy is
    # worse than one that admits it does not know.
    return "unstamped"


def on_config(config):
    global _CORNER, _FOOT

    label = _label()
    sha = os.environ.get("DOCRENDER_COMMIT_SHA", "")

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
    safe_detail = html.escape(detail, quote=True)

    # The site name travels with both, because a printed sheet leaves the system
    # entirely and a bare date names nothing a reader can place.
    name = str(getattr(config, "site_name", "") or "").strip()

    # 🔴 PAPER GETS THE DATE AND NOT THE BUILD. See the docstring: a PR number is
    # provenance for the builder and unreachable plumbing for the reader.
    stamped = when.strftime("%d %b %Y")
    corner = (name + " · " + stamped) if name else stamped

    # Screen keeps the build identifier, which is the question a collaborator is
    # actually asking when they look at it.
    foot = (name + " · " + label) if name else label

    _CORNER = (
        '<p class="buildstamp buildstamp--corner" title="' + safe_detail + '" hidden>'
        + html.escape(corner) + "</p>"
    )
    _FOOT = (
        '<p class="buildstamp buildstamp--foot" title="' + safe_detail + '">'
        + html.escape(foot) + "</p>"
    )

    # 🚫 Deliberately NOT set. Material renders it inside the footer region, which
    # is the place this hook exists to have escaped.
    config.copyright = None
    return config


def on_page_content(html_body, page, config, files):
    """Wrap the page body: corner mark first, foot line last.

    ⚠️ THE CORNER IS PREPENDED, WHICH IS NET-NEW IN THIS ENGINE. Every other
    `on_page_content` consumer appends -- `pagefoot.py` (06), `router.py` (04b)
    and this hook until 2026-08-19. Prepending is trivial and it has no precedent
    here, so it is stated rather than assumed: nothing downstream depends on the
    first element of the body being the `h1`, and `print.css` already targets
    `.md-content__inner > :first-child` for a margin reset, which the corner mark
    now satisfies instead of the heading.

    Unconditional on purpose. `pagefoot.py` skips generated pages because there
    is no source file to offer an edit link for; a build stamp has no such
    dependency, and a generated page is exactly as capable of being stale as an
    authored one.
    """
    if not _FOOT:
        return html_body
    return _CORNER + html_body + _FOOT
