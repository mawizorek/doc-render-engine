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
reason -- so the stamp names the build without offering a door to it.


=============================================================================
🔴 IT NEVER PRINTED. FIXED 2026-08-19 BY MOVING IT OUT OF THE FOOTER ENTIRELY.
=============================================================================
This hook used to hand its markup to `config.copyright`, which Material renders
inside `.md-footer-meta`. `assets/print-chrome.css` hides that element in its
chrome-off list, with `!important`, and then separately tried to bring
`.buildstamp` back:

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
verification. The first two PDFs could not settle it either, because that page
carried `hide: [footer]` and no footer could print there regardless. A third PDF
-- footer NOT hidden -- showed no stamp, no PR number, no SHA, no `unstamped`.
That is the evidence.

🔴 AND THE CSS FIX WOULD HAVE BEEN THE WRONG FIX. Hoisting `.buildstamp` out of
the hidden subtree in the stylesheet repairs exactly one class of page and leaves
the hole open, because `hide: footer` is a CONTENT decision and pages already use
it. ⚑ A rule that can be switched off by a frontmatter key it does not know about
is not a guarantee.


=============================================================================
⭐ TWO PLACEMENTS, AND THEY CARRY DIFFERENT TEXT ON PURPOSE
=============================================================================
> Michael, 2026-08-19: *"corner mark print only."* Then, on seeing it:
> *"I definitely do not want that PR number in the header. I'm fine with URITP
> safety in the date, but I definitely do not want the PR number in that!"*

    .buildstamp--corner   FIRST in flow, PRINT ONLY.   `URITP Safety · 19 Aug 2026`
    .buildstamp--foot     LAST in flow, SCREEN ONLY.   `URITP Safety` + a disclosure

🔴 THE BUILD IDENTIFIER IS SCREEN-ONLY, AND THE REASON IS AUDIENCE RATHER THAN
TASTE. A screen reader of these sites is Michael or a collaborator, and `PR #157`
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
trade rather than a free win. Debugging a stale PRINTED page means finding the
page on screen and revealing the foot disclosure. Correct for these documents --
the date is the provenance a reader actually needs -- but if a printed sheet ever
has to be traced back to a specific build, THIS is the decision to revisit.


=============================================================================
⭐ THE CORNER MARK NAMES THE PROGRAM (2026-08-28)
=============================================================================
    URITP Safety · General Safety for All · 28 Aug 2026

🔴 IT IS A REPLACEMENT, NOT AN ADDITION, AND THAT IS WHY IT IS ALLOWED. The same
evening `.dr-flows` joined print-chrome.css's chrome-off list, so the flow strip
no longer prints -- and `program.py`'s own claim is that *"the PROGRAM NAME is the
payload; the arrows are the instruction."* Only the instruction is meaningless on
paper. ⚑ *When a medium drops an element, ask which of its facts were about the
MEDIUM and which were about the DOCUMENT.* The arrows were about the medium. The
name was not, and it was about to be lost with them.

✅ AND IT LANDS ON THE ONE LINE THAT ALREADY DOES THIS JOB. The corner mark exists
because *"a printed sheet leaves the system entirely"* -- site name so a reader
can place it, date so a reader can age it. Which program handed it to them is the
third question in exactly that family, and a reader holding one sheet of a
nine-page program has no other way to answer it.

🔴 IT ASKS `program.py` RATHER THAN DERIVING. `flow_names()` shares
`_participation()` with the strip renderer, so the printed names and the screen
strips cannot disagree. A second walk over `nav.declared()` here would agree today
and drift the first time either side changed -- and **nobody can diff a piece of
paper against a page**, which makes this the worst available place for that drift.

⚠️ THE DATE IS STILL COMPUTED ONCE PER BUILD AND ONLY THE NAME IS PER PAGE, which
is the whole reason `_STAMPED` survives as module state. The original rule stands:
a build spanning midnight must not stamp two different dates onto one site. ⚑ *Per
page is not the same as per fact -- the thing that varies is the one that has to
be recomputed, and nothing else.*

⚠️ A PAGE IN THREE PROGRAMS NAMES ALL THREE, comma-joined, and that is a real
cost. The SCREEN caps the strips at one open plus a disclosure; a printed line
cannot collapse, so a borrowed policy in several programs gets a long stamp. 🚩 If
that becomes ugly the answer is a cap with a count (`+2 more`), not a silent
truncation -- naming two of three programs is worse than naming none.


=============================================================================
✅ THE DISCLOSURE, AND WHAT IT IS ALLOWED TO SAY (2026-08-19)
=============================================================================
> Michael: *"hide behind a small new svg icon in the footer that reveals a popup
> when hovered that displays that text. purely for debugging - no link."*

So the foot line is the SITE NAME plus one icon, and the identifier lives in a
popup that appears on hover.

🔴 AND THE POPUP CARRIES THE PR STRING AND NOTHING ELSE. The first version put
the deploy timestamp, the engine SHA and the content SHA in there too, and the
verdict was immediate: *"did you add the word 'engine' to the footer icon????
remove that. only a pr string."*

⚑ HE IS RIGHT AND THE REASON GENERALISES: THE POPUP ANSWERS ONE QUESTION, AND
FOUR FACTS DO NOT ANSWER IT FASTER. "Is this the latest push" is settled by the
PR number alone -- it either matches the last merge or it does not. The timestamp
and both SHAs were things I could compute rather than things the question needed,
and the give-away is that they had to be joined with separators to fit on a line.
*A debugging readout that needs punctuation is carrying more than one fact.*

⚠️ WHAT IS GENUINELY LOST, STATED RATHER THAN GLOSSED: the ENGINE ref. Content
and engine are separate repos with separate deploys, so "the content is current
but the engine that rendered it is three commits behind" is now invisible here.
It is still in the build report on every build. 🚩 If that question starts getting
asked, the answer is a SECOND disclosure on the report page rather than a longer
string in this one -- the failure mode of a debugging readout is not being wrong,
it is being too long to read.

🪦 AND THE `title` ATTRIBUTE IS GONE FROM BOTH NODES. They used to share one, and
this file recorded that on the corner copy it was DEAD WEIGHT: paper has no hover,
so nobody could ever read it. Keeping it on the foot copy beside a CSS popup would
have drawn a browser tooltip over ours after a delay, saying the same thing in a
different box -- two renderings of one fact, which is the defect this repo has
retired three manifests over, arriving as a UI bug. Its removal also stops
shipping a commit SHA into printed HTML that never renders.

🚫 NOT A LINK, AND NOT A `<button>`. Michael asked for no link and there is
nothing to activate: the popup is the whole payload. A `<button>` would promise an
action that does not exist -- the same dead-control argument `edit_links: false`
and the print link policy already make. It is a `<span>` with `tabindex="0"`, so a
keyboard can reveal it via `:focus-visible` without claiming to be a control.

⚠️ THE POPUP IS HIDDEN WITH `opacity`, NOT `display: none`, AND THAT IS AN
ACCESSIBILITY DECISION. `display: none` and `visibility: hidden` remove an element
from the accessibility tree, so a screen reader would lose the identifier
entirely -- a hover-only fact is invisible to anybody not hovering. At zero opacity
with `pointer-events: none` the text stays in the tree and is read normally, and
it is absolutely positioned so it costs no layout. Styling: `assets/foot.css`.


=============================================================================
🔴 THE GLYPH SAYS BACK-END, NOT INFORMATION (2026-08-19)
=============================================================================
> Michael: *"I want an icon that says less 'this is info' and more 'this is a
> back-end check-in'."*

The first version was a disc with an `i` knocked out of it. ⚑ **An `i` in a circle
is a promise about the AUDIENCE: it means "there is something here for you to
read."** Every reader of these sites -- a student, a guest artist, somebody
holding a printed policy -- is invited by that glyph, and the one thing behind it
is a PR number they cannot use. The icon was advertising to the wrong person.

✅ SO IT IS A CONSOLE PROMPT: a rounded square with `>` and an underscore knocked
out. A terminal window is the least ambiguous "this is machinery" mark there is,
and it reads as *not for you* to anybody who is not looking for it -- which is
exactly the audience filter the `i` was failing at. Same knocked-out construction
as before, so it still inverts against the footer rather than sitting in it.

⚠️ AND THE PREVIOUS GLYPH WAS ALSO A GUESS AT AN AMBIGUOUS NOTE. Michael's
earlier instruction was *"vert icon that the 'i' tho"*, which read either as
INVERT the `i` or as USE SOMETHING OTHER THAN the `i`. The disc-with-`i` satisfied
the first reading; this satisfies the second, which turns out to have been the
intent. 🚩 One constant, so the next swap is one edit and touches no CSS.

🔴 IT IS AN INLINE `<svg>`, NEVER AN `<img>`. An `<img>` is FETCHED even when
hidden -- the same rule print.css states for the corner mark's future logo -- and a
request for a 16px debugging glyph on every page of every site is absurd. Inline
costs ~250 bytes of HTML and no request at all.


=============================================================================
⭐ ONE COMPUTED VALUE PER FACT, TWO PRESENTATIONS -- NOT TWO CLAIMANTS
=============================================================================
The defect that retired `roster.json`, `registry.json` and `app-index.md` is two
SOURCES of one fact, which can disagree. `_label()`, the clock and the site name
are each read exactly once per build; the two nodes SELECT from those values
rather than recomputing them. They cannot drift, and the mutually exclusive media
scoping means a reader always sees exactly one stamp.

⚠️ THE PROGRAM NAME IS THE ONE EXCEPTION AND IT IS NOT A SECOND CLAIMANT: it is
per-PAGE data by nature, and its single source is `program.py`. What stayed once
per build is everything that is a property of the BUILD.

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
the one a screen reader should find, and it carries the identifier too.

⚠️ THE PRINTED LOGO IS NOT WIRED YET, AND THERE IS DELIBERATELY NO DEAD CSS FOR
IT. `uritp-safety/90-media-logos/` holds two JPEGs, both already reachable as
`@img:` targets with no engine change -- but Michael asked for a line-art SVG,
which does not exist yet. When it does, the image lands as a print-scoped
`background-image` on `.buildstamp--corner`.

🚫 AND `config.copyright` STAYS UNSET. Material renders it inside the footer
region, which is the place this hook exists to have escaped.
"""

from __future__ import annotations

import datetime
import html
import os
import re

from . import program

_PR = re.compile(r"#(\d+)")

#: The disclosure glyph: a console window with a prompt knocked OUT of it, which
#: is what `fill-rule="evenodd"` does to the two inner subpaths. One constant, so
#: swapping the symbol is one edit and no CSS changes.
#:
#: ⚠️ `aria-hidden` IS LOAD-BEARING. The glyph carries no information a screen
#: reader needs -- the popup text does -- and an unlabelled inline SVG otherwise
#: reads as an unnamed graphic in the middle of the footer.
_ICON = (
    '<svg class="buildstamp__icon" viewBox="0 0 16 16" aria-hidden="true"'
    ' focusable="false"><path fill-rule="evenodd" d="M2 1h12a2 2 0 012 2v10a2 2'
    ' 0 01-2 2H2a2 2 0 01-2-2V3a2 2 0 012-2Zm2.4 3.3L3.3 5.4 5.4 7.5 3.3 9.6'
    'l1.1 1.1L7.6 7.5ZM8 10.2h4.2v1.5H8Z"/></svg>'
)

#: Properties of the BUILD, read once at `on_config`. The corner mark is composed
#: per page because one of its three facts is per page; these two are not.
_NAME = ""
_STAMPED = ""
_FOOT = ""


def _label() -> str:
    """`PR #16`, or a short SHA, or an honest admission.

    ⚠️ SCREEN ONLY, and behind the disclosure. Nothing this returns reaches paper.

    ⭐ AND IT IS NOW THE WHOLE POPUP. The timestamp and both SHAs were removed on
    2026-08-19 (Michael: *"only a pr string"*), so this one string is the entire
    debugging payload -- which makes the SHA and `unstamped` fallbacks below more
    load-bearing than they were, not less: they are the only thing standing
    between a reader and an empty popup.
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


def _corner(page, files) -> str:
    """The printed corner mark: site · program(s) · date.

    🔴 PER PAGE ONLY BECAUSE THE PROGRAM NAME IS. The site name and the date are
    read once at `on_config` and only selected here -- see the docstring on why a
    build spanning midnight must not stamp two dates onto one site.

    ⚠️ NEVER RAISES. A stamp is furniture on every page of every site, so a chain
    that cannot be resolved must cost the program name and nothing else. The
    failure mode is the stamp this file shipped for nine days.
    """
    parts = [_NAME] if _NAME else []
    try:
        names = program.flow_names(page, files)
    except Exception:
        names = []
    if names:
        parts.append(", ".join(names))
    if _STAMPED:
        parts.append(_STAMPED)
    if not parts:
        return ""
    return (
        '<p class="buildstamp buildstamp--corner" hidden>'
        + html.escape(" \u00b7 ".join(parts)) + "</p>"
    )


def on_config(config):
    global _NAME, _STAMPED, _FOOT

    label = _label()

    # Runners are UTC. Stamp Eastern so the date means something to a human in
    # Rochester rather than needing mental arithmetic at 4am.
    eastern = datetime.timezone(datetime.timedelta(hours=-4))
    when = datetime.datetime.now(datetime.timezone.utc).astimezone(eastern)

    # The site name travels with the printed copy, because a printed sheet leaves
    # the system entirely and a bare date names nothing a reader can place.
    _NAME = str(getattr(config, "site_name", "") or "").strip()

    # 🔴 PAPER GETS THE DATE AND NOT THE BUILD. See the docstring: a PR number is
    # provenance for the builder and unreachable plumbing for the reader.
    _STAMPED = when.strftime("%d %b %Y")

    # ⚠️ NO `title` ON EITHER NODE. On the corner it was never readable (paper has
    # no hover); on the foot it would draw a second tooltip over the popup.
    #
    # 🚫 A `<span>` WITH `tabindex`, NOT A BUTTON: there is nothing to activate.
    # The popup is hidden with `opacity` rather than `display`, so it stays in the
    # accessibility tree -- see the docstring.
    _FOOT = (
        '<p class="buildstamp buildstamp--foot">'
        + (html.escape(_NAME) if _NAME else "")
        + '<span class="buildstamp__debug" tabindex="0">'
        + _ICON
        + '<span class="buildstamp__pop">' + html.escape(label) + "</span>"
        + "</span></p>"
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

    ⚠️ AND IT LANDS AHEAD OF `program.py`'s ARRIVAL MARKERS, which is safe: those
    promotion rules need the marker and `.dr-flows` to be SIBLINGS, and another
    sibling in front of both changes nothing. Hook 07 runs after 05b, so the
    strips are already in `html_body` by the time this prepends.

    Unconditional on purpose. `pagefoot.py` skips generated pages because there
    is no source file to offer an edit link for; a build stamp has no such
    dependency, and a generated page is exactly as capable of being stale as an
    authored one.
    """
    if not _FOOT:
        return html_body
    return _corner(page, files) + html_body + _FOOT
