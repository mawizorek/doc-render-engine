"""Hook 07 -- the build stamp. Two placements, one fact.

Answers one question from any page without opening Actions: is what I am
looking at the latest push?

That matters more than it sounds. When a build fails, GitHub Pages keeps
serving the previous commit with no banner and no error page. The site simply
stops changing. There is no other signal that has happened, which is why this
exists at all and why it runs on every page rather than on a status page
nobody visits.

WHAT IS VISIBLE, and it is deliberately almost nothing:

    URITP Safety · PR #12

The deploy time, the engine version and the commit hash all live in the `title`
attribute. A designer looking up a grid height does not need a clock or a
forty-character hash, and the three or four times a year somebody debugs a
frozen deploy, a hover or a view-source recovers everything.

⚠️ NOT A LINK (2026-08-03). It used to link to the PR. The rendered site no
longer advertises its repository at all -- the header widget went for the same
reason -- so the stamp names the PR without offering a door to it.

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
⭐ TWO PLACEMENTS, ADDED 2026-08-19 -- AND WHY THAT IS NOT TWO CLAIMANTS
=============================================================================
> Michael: *"set a global for the app and on print you get a small icon in the
> top right header with the date… corner mark print only."*

So the stamp now has two homes, each visible in exactly ONE medium:

    .buildstamp--corner   FIRST in the content flow, PRINT ONLY.  Top right of
                          sheet one, which is where a document stamp belongs on
                          paper and where the icon will sit.
    .buildstamp--foot     LAST in the content flow, SCREEN ONLY.  The original
                          job -- a quiet line answering "is this the latest
                          push" while somebody is reading the site.

🔴 THIS REPO KILLS SECOND CLAIMANTS ON SIGHT, so the distinction has to be exact.
The defect that retired `roster.json`, `registry.json` and `app-index.md` is TWO
SOURCES OF ONE FACT, which can disagree. This is ONE computed string rendered
into two nodes: `_label()` runs once per build and both placements interpolate
the same `text` and the same `detail`. **They cannot drift, and because the media
scoping is mutually exclusive they can never both appear.** A reader sees exactly
one stamp, always.

⚠️ AND IT REVERSES A DESIGN WRITTEN EARLIER THE SAME DAY, which is recorded
rather than quietly re-specced. `specs/print-identity.md` §4a argued for a logo
at the HEAD answering *whose document is this* and a stamp at the FOOT answering
*how old is it* -- two facts, two ends, neither restating the other. Michael's
ruling deliberately COLLAPSES them into one corner mark. That is defensible on
its own terms (a database stamp is exactly one line carrying both) and it is a
reversal, not a refinement.

⭐ WHY THE CORNER COPY MUST BE FIRST IN THE FLOW, WHICH IS THE WHOLE MECHANISM.
An element appended at the END of the content cannot be moved to the TOP of sheet
one by CSS: that needs knowledge of where the page boundary falls, which is
exactly what `@page` margin boxes do and no major browser implements. First in
flow IS the top of sheet one, for free, with no pagination machinery. That is the
same finding that closed the letterhead ruling -- top of sheet one is cheap,
bottom of sheet one is not.

🔴 THE `hidden` ATTRIBUTE IS DOING REAL WORK AND IS NOT DECORATION. The corner
copy ships with `hidden`, which the UA stylesheet implements as `display: none`.
Any AUTHOR `display` declaration beats a UA one, so `@media print { display:
block }` reveals it on paper and nothing reveals it on screen. ⭐ That is what
keeps this change from touching a single screen stylesheet: no `@media screen`
block anywhere, no edit to base.css, and a build with no print sheet at all still
hides it correctly. ⚠️ It also drops the corner copy from the accessibility tree,
which is CORRECT here -- the foot copy is the one a screen reader should find,
and two identical announcements would be noise.

⚠️ THE ICON IS NOT WIRED YET, AND THERE IS DELIBERATELY NO DEAD CSS FOR IT.
The corner mark is text-only today. `uritp-safety/90-media-logos/` holds
`logo-horizontal.jpg` and `logo-square.jpg`, both already reachable as
`@img:logo-horizontal` / `@img:logo-square` with no engine change -- but Michael
asked for a line-art SVG instead, which does not exist yet. When it does, the
image lands as a print-scoped `background-image` on `.buildstamp--corner` (never
an `<img>`: a `display:none` image is still FETCHED, and that is ~168KB on every
page load of a site whose readers mostly never print). An unset custom property
with nothing behind it would be a dead control, and this engine kills those on
sight.

⚠️ THE LABEL IS STILL COMPUTED ONCE PER BUILD, at `on_config`, and only the emit
is per page. The inputs are three environment variables and a clock; reading them
per page would be waste, and worse, a build spanning midnight could stamp two
different dates onto one site.

🚫 AND `config.copyright` STAYS UNSET. Material would render it in the footer
region, which is the exact place this hook just escaped.
"""

from __future__ import annotations

import datetime
import html
import os
import re

_PR = re.compile(r"#(\d+)")

#: The two rendered elements, built once at `on_config` from ONE label. Both are
#: interpolated from the same strings -- see the docstring on why that is one
#: claimant and not two.
_CORNER = ""
_FOOT = ""


def _label() -> str:
    """`PR #16`, or a short SHA, or an honest admission."""
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

    # The site name travels with the label, because a printed sheet leaves the
    # system entirely and 'PR #12' alone names nothing a reader can place.
    name = str(getattr(config, "site_name", "") or "").strip()
    text = (name + " · " + label) if name else label

    # ⚠️ The corner carries a DATE as well as the label, because Michael asked
    # for "the date" specifically and paper has no hover to recover a `title`
    # from. The foot keeps the title-attribute behaviour it has always had: on
    # screen the detail is one hover away and does not need to be in the line.
    stamped = when.strftime("%d %b %Y")

    safe_detail = html.escape(detail, quote=True)

    _CORNER = (
        '<p class="buildstamp buildstamp--corner" title="' + safe_detail + '" hidden>'
        + html.escape(text) + " · " + html.escape(stamped)
        + "</p>"
    )
    _FOOT = (
        '<p class="buildstamp buildstamp--foot" title="' + safe_detail + '">'
        + html.escape(text) + "</p>"
    )

    # 🚫 Deliberately NOT set. Material renders it inside the footer region, which
    # is the place this hook exists to have escaped.
    config.copyright = None
    return config


def on_page_content(html_body, page, config, files):
    """Wrap the page body: corner mark first, foot line last.

    ⚠️ THE CORNER IS PREPENDED, WHICH IS NET-NEW IN THIS ENGINE. Every other
    `on_page_content` consumer appends -- `pagefoot.py` (06), `router.py` (04b)
    and this hook until now. Prepending is trivial and it has no precedent here,
    so it is stated rather than assumed: nothing downstream depends on the first
    element of the body being the `h1`, and `print.css` already targets
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
