"""Hook 07 -- the build stamp, the printed letterhead, and the RUNNING FURNITURE.

Answers one question from any page without opening Actions: is what I am looking at
the latest push? When a build fails, GitHub Pages keeps serving the previous commit
with no banner and no error page -- the site simply stops changing, and there is no
other signal that has happened.

    .buildstamp--corner   FIRST in flow, PRINT ONLY.   [logo]  URITP Safety - Fall 2026
    .buildstamp--foot     LAST in flow, SCREEN ONLY.   URITP Safety + a disclosure
    @page margin boxes    EVERY PRINTED PAGE.          header + footer + page number

🔴 **RATIONALE AND POST-MORTEMS LIVE IN `docrender/buildstamp-dl.md`.** Extracted
2026-08-29 at 21,149 B against a 22,528 B read limit: ~70% narrative over ~40 lines
of mechanism, which is the point where the file that must stay editable stops being
editable. Read that sibling before changing anything here -- every rule below was
paid for by an incident recorded there.

The number in the popup is parsed from the head commit SUBJECT:

    squash merge   'fix: repair the venue links (#16)'   -> PR #16
    direct push    'Update main-stage.md'                -> short SHA

The SHA fallback is load-bearing: most edits to a content repo are made from the
GitHub UI and never see a branch. Only the subject line is read -- a commit body
mentioning another issue number must not win.

=============================================================================
🔴 THE RUNNING FURNITURE (2026-08-30) -- AND IT REVERSES THIS FILE'S OWN REASON
=============================================================================
> Michael, 2026-08-30: *"i DOOO want to see the header repeated on every printed
> page now, and the footer that says 'revised' and my name now, also repeated as a
> footer on each page. so once printed, locking those two elements to true page
> headers and footers. this is a change from what i've said in the past."*

🔴 THE BLOCKER THIS FILE DOCUMENTED WAS TRUE AND IS NOW FALSE. The paragraph below
still explains why the corner copy is FIRST IN FLOW, and its stated reason was that
repeating it *"needs knowledge of where the page boundary falls, which is what
`@page` margin boxes do and no major browser implements."* **Chrome 131 shipped all
16 margin boxes in Nov 2024 and Safari 18.2 in Dec 2024**, with `counter(page)`,
`counter(pages)` and `content: url()`. ⚑ *A sentence asserting that a capability
does not exist is a fact with an expiry date, and nothing fails when it passes* --
third instance of that shape found in one session, so it is now a named class.

⭐ THE DESIGN TURN THAT MAKES THIS CHEAP. A margin box cannot read document content,
and `string-set` (the spec's answer) is unimplemented in Chrome. That normally kills
a running header carrying per-document values. **It does not bite here, because
`revised:` is per-DOCUMENT and every MkDocs page IS exactly one document** -- so the
engine writes that page's own values into that page's own `@page` rule at build
time. No named strings, no polyfill, no reader-time anything.

🔴 THE BLOCK AXIS IS OURS AND THE INLINE AXIS IS NOT. `print.css` sets
`@page { margin: 12mm }` and calls the inline half *"the load-bearing half"* because
the printed column is a container and the data table flips to list mode under 640px;
that same file states *"the BLOCK axis is free to change."* So `_page_css` below sets
ONLY `margin-top` / `margin-bottom` -- a margin box's height IS the page margin, so
the furniture needs the room -- and never touches left or right. ✅ Disjoint property
sets, exactly the argument `print-space.css` already makes for `h1` living in two
files: two rules on `@page`, no shared property, no cascade fight.

⚠️ AND IT IS EMITTED PER PAGE AS A `<style>` RATHER THAN LIVING IN A SHEET, which
looks wrong and is the only option. A stylesheet is shared by every page; the
revision date is not. This is the same reason the letterhead URL is written inline
by `_corner` instead of as a custom property.

🚩 FIREFOX PRINTS NO FURNITURE AT ALL and that is accepted, not overlooked (Michael,
2026-08-30). It supports `@page` margins but no margin boxes, so a Firefox printout
gets the wider margins and an empty band. Chrome and Safari only. ⚠️ The in-flow
corner copy is NOT kept as a Firefox fallback: it would double the header on every
Chrome sheet, and there is no CSS test for margin-box support. One or the other.

🚩 THE MARGIN TRAP, FLAGGED HERE BECAUSE IT IS A REGRESSION THIS FEATURE CREATES.
A margin box's height is the page margin, so **a reader who picks "None" in the
print dialog deletes the footer.** Measured: 40/32pt, 20pt and 10pt all render; at
2pt and 0 the posted-by line and the page number are GONE while the header survives.
Chrome's own docs add a worse quirk -- if page ONE has no room, later pages lose
their margin content too. Today's in-flow stamp survives any margin; this does not.
`specs/print-control.md` §8 carries it as the standing item.

=============================================================================
🚫 THE HARD RULES, WITH THEIR REASONS ONE FILE OVER
=============================================================================
🚫 **TWO FACTS ON THE PRINTED LINE. NOT THREE.** It has refused the PR number
(08-19) and a program name (08-28). A line carrying two facts is a stamp; three is
a header. § *The corner mark is SITE + DATE* in the sibling. ⚠️ THE FOOTER BAND IS
NOT GOVERNED BY THIS AND THE DISTINCTION IS MICHAEL'S: that rule was about ONE
line. The footer is three SEPARATE margin boxes -- left, centre, right -- each
carrying one fact, which is the opposite of crowding three onto one line.

✅ **A LOGO IS NOT A THIRD CLAUSE, IT IS A MARK** -- which is why the letterhead was
allowed on 2026-08-29 where two text additions were not. § *THE LETTERHEAD*.

🔴 **THE BUILD IDENTIFIER IS SCREEN-ONLY.** Provenance for the BUILDER is noise for
the READER, and print is the surface where the reader is not the builder.

🔴 **THE `hidden` ATTRIBUTE IS DOING REAL WORK.** The corner copy ships with
`hidden` (UA `display: none`); any AUTHOR `display` beats a UA one, so
`print-chrome.css`'s `@media print { display: block }` reveals it on paper and
nothing reveals it on screen. 🪦 **AS OF 2026-08-30 `print-identity.css` HIDES IT
AGAIN ON PAPER**, because the margin box replaced it. The mechanism is left intact
rather than deleted: it is one rule away from being the revert path.

⭐ **WHY THE CORNER COPY IS FIRST IN THE FLOW.** An element appended at the END of
the content cannot be moved to the TOP of sheet one by CSS: that needs knowledge of
where the page boundary falls, which is what `@page` margin boxes do -- and as of
2026-08-30 we USE them. First in flow IS the top of sheet one, for free, and that
is still why this element is shaped the way it is.

🚫 **`config.copyright` STAYS UNSET.** Material renders it inside the footer region,
which is the place this hook exists to have escaped.

=============================================================================
⭐ ONE COMPUTED VALUE PER FACT, TWO PRESENTATIONS -- NOT TWO CLAIMANTS
=============================================================================
`_label()`, the clock and the site name are each read exactly once per build; the
two nodes SELECT from those values rather than recomputing them, and the mutually
exclusive media scoping means a reader always sees exactly one stamp.

⚠️ **THE SEASON STRING IS STILL BUILT ONCE AT `on_config`** -- a build spanning a
boundary must not stamp two different periods onto one site. **What is per page is
the logo URL only**, because `util.relative_url` needs the consuming page and a
letterhead renders at every depth in the tree. One computed fact, one resolution per
page: still one claimant. § *The date is still built ONCE*. 🔴 THE RUNNING FURNITURE
READS THE SAME THREE VALUES and adds only the page's own `revised:` and the site's
`owner:` -- both drawn from where they already live, never re-derived here.

=============================================================================
⚠️ THE STYLING IS SPLIT ACROSS TWO SHEETS ON PURPOSE
=============================================================================
    print-chrome.css    the stamp's own BOX -- and `display: block`, which is what
                        overrides `hidden`. Delete it there and the letterhead
                        renders nothing, with nothing reporting it.
    print-identity.css  the LETTERHEAD ROW -- flex, the mark, the two weights --
                        and, as of 08-30, the rules that retire the in-flow copies
                        on paper now that the margin boxes carry them.

🔴 Every selector in `print-identity.css` is net-new **specifically so the print
group's "no two sheets share a selector-and-property pair" invariant stays true.**
`display: flex` on `.buildstamp--corner` would have been a genuine pair against
print-chrome.css's `display: block`. That is why `_row()` exists as an inner element
rather than the layout hanging off the `<p>`.
"""

from __future__ import annotations

import datetime
import html
import os
import re

from . import images, state
from .util import relative_url

_PR = re.compile(r"#(\d+)")

#: (first month, last month, label). Michael, 2026-08-29.
#:
#: 🔴 NO BUCKET MAY CROSS A YEAR BOUNDARY, and that is the whole design constraint
#: rather than a coincidence. His first proposal put December with January, which
#: makes the year of a December print undecidable -- the engine would have had to
#: pick one silently, forever, on a safety document. December belongs to Fall.
#:
#: ⭐ AND IT MATCHES A CODE THAT ALREADY EXISTS: `F26` is the live production code
#: for Big Love, and an academic Fall term ends in December. The stamp reads the
#: house's vocabulary instead of inventing a second one. § the sibling, § SEASONS.
#:
#: ⚠️ THREE LABELS, NOT FOUR. Four was asked for; three already partition all twelve
#: months, so a fourth would have to split one. Said out loud, not delivered quietly.
_SEASONS = (
    (8, 12, "Fall"),
    (1, 5, "Spring"),
    (6, 7, "Summer"),
)

#: The disclosure glyph: a console window with a prompt knocked OUT of it, which is
#: what `fill-rule="evenodd"` does to the two inner subpaths. One constant, so
#: swapping the symbol is one edit and no CSS changes.
#:
#: ⚠️ `aria-hidden` IS LOAD-BEARING. The glyph carries no information a screen reader
#: needs -- the popup text does -- and an unlabelled inline SVG otherwise reads as an
#: unnamed graphic in the middle of the footer.
_ICON = (
    '<svg class="buildstamp__icon" viewBox="0 0 16 16" aria-hidden="true"'
    ' focusable="false"><path fill-rule="evenodd" d="M2 1h12a2 2 0 012 2v10a2 2'
    ' 0 01-2 2H2a2 2 0 01-2-2V3a2 2 0 012-2Zm2.4 3.3L3.3 5.4 5.4 7.5 3.3 9.6'
    'l1.1 1.1L7.6 7.5ZM8 10.2h4.2v1.5H8Z"/></svg>'
)

#: Built once at `on_config`. `_CORNER_TEXT` is the two-fact line as markup;
#: `_FOOT` is the whole screen node; `_NAME` and `_PERIOD` are the raw values the
#: running header needs as CSS strings rather than as HTML.
_CORNER_TEXT = ""
_FOOT = ""
_NAME = ""
_PERIOD = ""

#: The block-axis room the margin boxes need. 🔴 BLOCK AXIS ONLY -- see the module
#: docstring. `print.css`'s `@page { margin: 12mm }` keeps the inline axis, which is
#: the half that decides whether a data table is still a table.
#:
#: ⚠️ 16mm rather than 12: the letterhead mark is 8.46mm tall and the footer's right
#: box is TWO lines at 8.5pt (~6mm). 12mm fits neither with air. Measured from the
#: shipped `print-identity.css` values, not chosen.
_BAND = "16mm"


def _label() -> str:
    """`PR #16`, or a short SHA, or an honest admission.

    ⚠️ SCREEN ONLY, and behind the disclosure. Nothing this returns reaches paper.
    It is the WHOLE popup as of 2026-08-19 (*"only a pr string"*), which makes the
    fallbacks below more load-bearing than they were, not less: they are the only
    thing standing between a reader and an empty popup.
    """
    subject = os.environ.get("DOCRENDER_COMMIT_SUBJECT", "").strip().splitlines()
    found = _PR.findall(subject[0]) if subject else []
    sha = os.environ.get("DOCRENDER_COMMIT_SHA", "")

    if found:
        return "PR #" + found[-1]
    if sha:
        return sha[:7]
    # A local build, or the workflow failed to pass the commit through. Said plainly
    # rather than dressed up: a stamp that lies about being a deploy is worse than
    # one that admits it does not know.
    return "unstamped"


def _period(when) -> str:
    """`Fall 2026`. A season and a calendar year, never an explicit date.

    > Michael, 2026-08-29: *"never the explicit date that it was printed."*

    ⭐ THE YEAR NEEDS NO RULE BECAUSE NO BUCKET CROSSES ONE. See `_SEASONS`.

    ⚠️ The fallthrough is unreachable while `_SEASONS` covers all twelve months, and
    it returns the bare year rather than raising: a stamp is furniture, and no
    formatting edge case may ever fail a build.
    """
    for lo, hi, name in _SEASONS:
        if lo <= when.month <= hi:
            return name + " " + str(when.year)
    return str(when.year)


def _css(text) -> str:
    """A CSS string literal, quoted and escaped.

    🔴 A BACKSLASH AND A DOUBLE QUOTE ARE THE WHOLE ATTACK SURFACE, and both are
    escaped rather than stripped. These values come from a config file and from
    frontmatter -- `revised:` is authored on every page in the content repo, which
    is a tree agents may not commit to and therefore may not sanitise either. An
    unescaped quote would not "look wrong": it would terminate the string, make the
    whole `@page` rule invalid, and drop the ENTIRE header and footer from every
    page of that document silently. Cheap guard, expensive failure.

    ⚠️ Newlines are collapsed for the same reason -- a raw newline inside a CSS
    string is a parse error, and YAML block scalars make one easy to write.
    """
    s = " ".join(str(text or "").split())
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _logo_url(page) -> str:
    """The declared letterhead mark, resolved for THIS page. `""` for none.

    ⭐ DECLARED BY NAME, NEVER BY PATH: `print: logo: <stem>` in the instance's
    `site.yml`, resolved through the index `images.on_files` has already built. The
    file lives in the CONTENT repo, can live anywhere in it, and can change format
    without touching config.

    🔴 A STEM SHARED BY TWO FILES IS REFUSED, LOUDLY, AND THIS IS THE LIVE TRAP FOR
    THIS FEATURE. `logo-horizontal.jpg` exists today; dropping `logo-horizontal.svg`
    beside it puts the name in `images.COLLISIONS`, out of `INDEX`, and the
    letterhead silently disappears. **The SVG replaces the JPEG, it does not join
    it.** Reported with the fix in the message rather than left as a blank corner.

    ⚠️ REPORTED ONCE PER BUILD, NOT ONCE PER PAGE. A misconfigured stem would
    otherwise emit one identical line per page and bury every other finding in the
    report -- the report is read by a person and a flood is the same as silence.

    ⚠️ Resolved through `util.relative_url` and never by counting separators: this
    element renders at every depth in the tree, so it is maximally exposed to the
    `../` arithmetic that shipped wrong three separate times.
    """
    stem = str((state.INSTANCE.get("print") or {}).get("logo") or "").strip().lower()
    if not stem:
        return ""

    if stem in images.COLLISIONS:
        if not state.REPORT.get("_logo_reported"):
            state.REPORT["_logo_reported"] = True
            state.note(
                "dead_links",
                "print.logo '" + stem + "' is ambiguous -- "
                + str(len(images.COLLISIONS[stem])) + " files share that name: "
                + ", ".join(images.COLLISIONS[stem])
                + ". No letterhead is printed until one is renamed or removed. An "
                + "image is named by the stem of its filename, so a .svg placed "
                + "beside the .jpg it replaces is a COLLISION rather than an "
                + "upgrade -- replace the file, do not add to it.",
            )
        return ""

    hit = images.INDEX.get(stem)
    if not hit:
        if not state.REPORT.get("_logo_reported"):
            state.REPORT["_logo_reported"] = True
            state.note(
                "dead_links",
                "print.logo names '" + stem + "' and no image in the content tree "
                + "has that filename stem. No letterhead is printed. The value is "
                + "the STEM of the filename -- no path and no extension.",
            )
        return ""

    return relative_url(hit["url"], page.file.url)


def _corner(page) -> str:
    """The printed letterhead: an optional mark, then the two-fact line.

    🪦 RETIRED FROM PAPER 2026-08-30 by `print-identity.css`, which now hides it --
    the `@top-*` margin boxes carry the header on every page instead. Still emitted,
    and that is deliberate: the element, its `hidden` trick and its stylesheet rules
    are the revert path, and deleting them would make going back a rebuild rather
    than a one-line change. ⚠️ It is NOT a Firefox fallback -- see the docstring.

    ⚠️ THE MARK SPAN IS OMITTED ENTIRELY WHEN NO LOGO RESOLVES rather than emitted
    empty. `print-identity.css` gives it a 5.5mm height, so an empty box would spend
    the whole of Michael's 140% height budget on nothing.

    🔴 THE URL IS AN INLINE `background-image`, AND IT WAS A `var()` UNTIL A RENDER
    PROVED THAT BLANK. A custom property read as `background-image: var(--dr-print-logo)`
    is the tidier shape and it produced an EMPTY BOX in WeasyPrint every way it was
    tried -- inline, and declared in the sheet itself. Browsers do substitute custom
    properties into `background-image`, so the tidy version is probably fine in
    Chrome; **"probably fine" is not a standard this element can be held to**, because
    its failure mode is a blank corner that reports nothing. The URL therefore lands
    in the one form that rendered in the engine available to test. § the sibling.

    ⚠️ AND IT IS STILL NOT FETCHED ON SCREEN, which is the whole reason this is a
    background rather than an `<img>`. The `<p>` carries `hidden`, so on screen the
    subtree is `display: none` and a background image on a non-rendered box is not
    requested -- where an `<img>` is fetched whether or not it is displayed
    (~168KB on every page load of a site whose readers mostly never print).

    🚫 NO `title` ON EITHER NODE. On the corner it was never readable (paper has no
    hover); on the foot it would draw a browser tooltip over our own popup.
    """
    url = _logo_url(page)
    mark = ""
    if url:
        mark = (
            '<span class="buildstamp__mark" aria-hidden="true"'
            ' style="background-image:url(&quot;' + html.escape(url, quote=True)
            + '&quot;)"></span>'
        )

    return (
        '<p class="buildstamp buildstamp--corner" hidden>'
        + '<span class="buildstamp__row">'
        + mark
        + '<span class="buildstamp__text">' + _CORNER_TEXT + "</span>"
        + "</span></p>"
    )


def _page_css(page) -> str:
    """The `@page` rule for THIS page: running header, running footer, page number.

    Emitted as a `<style>` in the page body, which is the only place a PER-PAGE
    declaration can live -- a stylesheet is shared by every page and the revision
    date is not. Full argument in the module docstring.

        @top-left      the mark          @top-right      site · period
        @bottom-left   Revised <date>    @bottom-centre  Page N of M
                                         @bottom-right   Posted by <name>
                                                         <email>

    ⭐ THE LAYOUT MIRRORS WHAT THE SCREEN ALREADY DOES, which is why it needed no
    design pass: `revised` has held the left of the screen footer since 08-07 and
    the ownership tag has held the right since 08-30. The page number takes the
    centre because it is the one fact that belongs to the SHEET rather than to the
    document -- Michael's call, 2026-08-30: *"i like center for page No."*

    ✅ `Page N of M` USES `counter(pages)` FOR THE TOTAL, which is the entire reason
    it is worth having on a safety sheet: a stapled packet found on a desk announces
    that it is incomplete. A bare page number cannot do that.

    ⚠️ THE EMAIL IS A SECOND LINE VIA `\\A` + `white-space: pre`, not a `<br>`: a
    margin box takes generated CONTENT, so there is no markup to put a break tag in.
    Same two-line shape the screen tag renders, reached a different way.

    🔴 EVERY VALUE IS OPTIONAL AND EACH BOX IS OMITTED RATHER THAN EMITTED EMPTY.
    A margin box with no `content` is not generated at all (`content: normal`
    computes to `none`), so an omitted box costs nothing -- but an emitted empty
    string still reserves the box. A site with no `owner:` therefore prints a header
    and a page number and no name, which is exactly the absent-means-off polarity
    `print:` and `routes.yml` already have.

    ⚠️ AND IT RETURNS `""` WHEN THERE IS NOTHING TO SAY, so the block-axis margin
    change never lands on a page that has no furniture to make room for. A page that
    would print two empty bands instead prints exactly as it did before.
    """
    boxes = []

    url = _logo_url(page)
    if url:
        # 🚩 CHROMIUM-ONLY AND NOT VERIFIED HERE. `content: url()` in a margin box is
        # supported in Chrome 131+ and Safari 18.2+; WeasyPrint 69 renders NOTHING
        # for it, proven against a working control (a body `<img>` rasterised 11,711
        # red pixels, the margin box zero, on three pages). ⚑ *The engine that could
        # be tested is not the engine that prints* -- Michael prints from Chrome, so
        # WeasyPrint is the proxy here and Chromium is the page. Stated rather than
        # implied, because every other measurement in this feature ran the other way.
        # If the mark is missing from a Chrome printout, this line is the suspect and
        # the revert is `print-identity.css`'s in-flow rules.
        boxes.append("@top-left{content:url(" + _css(url) + ")}")

    if _NAME and _PERIOD:
        boxes.append(
            "@top-right{content:" + _css(_NAME) + '" \\00B7 "' + _css(_PERIOD) + "}"
        )

    meta = state.BY_SRC.get(page.file.src_uri, {})
    revised = " ".join(str(meta.get("revised") or "").split())
    if revised:
        # The LABEL is engine-supplied here exactly as it is in `lede.revised()`.
        # Two emitters, one wording, and neither reformats the value -- see that
        # function for why a human's provenance string is passed through verbatim.
        boxes.append("@bottom-left{content:" + _css("Revised " + revised) + "}")

    boxes.append('@bottom-center{content:"Page " counter(page) " of " counter(pages)}')

    owner = state.INSTANCE.get("owner") or {}
    if isinstance(owner, str):
        name, email = owner, ""
    else:
        name, email = owner.get("name") or "", owner.get("email") or ""
    if name:
        line = "Posted by " + " ".join(str(name).split())
        if email:
            line += "\n" + " ".join(str(email).split())
        boxes.append(
            "@bottom-right{content:"
            + _css(line).replace("\\n", "\\A ")
            + ";white-space:pre}"
        )

    if len(boxes) <= 1:
        # Only the page counter -- not worth widening the sheet's margins for.
        return ""

    return (
        "<style>@page{margin-top:" + _BAND + ";margin-bottom:" + _BAND + ";"
        + "".join(boxes)
        + "}</style>"
    )


def on_config(config):
    global _CORNER_TEXT, _FOOT, _NAME, _PERIOD

    label = _label()

    # Runners are UTC. Stamp Eastern so the date means something to a human in
    # Rochester rather than needing mental arithmetic at 4am.
    eastern = datetime.timezone(datetime.timedelta(hours=-4))
    when = datetime.datetime.now(datetime.timezone.utc).astimezone(eastern)

    # The site name travels with the printed copy, because a printed sheet leaves
    # the system entirely and a bare period names nothing a reader can place.
    name = str(getattr(config, "site_name", "") or "").strip()
    period = _period(when)

    # 🔴 THE RAW VALUES ARE KEPT so the running header can quote them as CSS strings.
    # `_CORNER_TEXT` below is HTML-escaped markup and cannot be reused -- an escaped
    # `&amp;` inside a CSS string prints literally. One computed fact, two encodings.
    _NAME, _PERIOD = name, period

    # 🔴 PAPER GETS THE PERIOD AND NOT THE BUILD, and it gets TWO FACTS. The name is
    # bold and the period is not (`print-identity.css`) -- weight separates them
    # without adding a word, which is why the line can stay two facts after refusing
    # two additions.
    if name:
        _CORNER_TEXT = (
            '<span class="buildstamp__id">' + html.escape(name) + "</span>"
            + '<span class="buildstamp__sep"> \u00b7 </span>'
            + '<span class="buildstamp__when">' + html.escape(period) + "</span>"
        )
    else:
        _CORNER_TEXT = '<span class="buildstamp__when">' + html.escape(period) + "</span>"

    # 🚫 A `<span>` WITH `tabindex`, NOT A BUTTON: there is nothing to activate. The
    # popup is hidden with `opacity` rather than `display`, so it stays in the
    # accessibility tree.
    _FOOT = (
        '<p class="buildstamp buildstamp--foot">'
        + (html.escape(name) if name else "")
        + '<span class="buildstamp__debug" tabindex="0">'
        + _ICON
        + '<span class="buildstamp__pop">' + html.escape(label) + "</span>"
        + "</span></p>"
    )

    # 🚫 Deliberately NOT set. Material renders it inside the footer region, which is
    # the place this hook exists to have escaped.
    config.copyright = None
    return config


def on_page_content(html_body, page, config, files):
    """Wrap the page body: the `@page` rule, letterhead first, foot line last.

    ⚠️ THE CORNER IS PREPENDED, WHICH IS NET-NEW IN THIS ENGINE. Every other
    `on_page_content` consumer appends -- `pagefoot.py` (06), `router.py` (04b) and
    this hook until 2026-08-19. Nothing downstream depends on the first element of
    the body being the `h1`, and `print.css` already targets
    `.md-content__inner > :first-child` for a margin reset, which the corner mark
    now satisfies instead of the heading.

    ⚠️ THE `<style>` GOES AHEAD OF EVERYTHING, and its position is not a style
    choice: `print.css` zeroes the top margin of `.md-content__inner > :first-child`,
    so whatever lands first absorbs that rule. A `<style>` element generates no box,
    which makes it the one thing that can be first WITHOUT taking a margin reset
    away from the element that needs it. 🚩 If a future change moves it after the
    corner, check that reset -- this is the third element to be first in this flow
    and the first two both mattered.

    ⚠️ AND IT LANDS AHEAD OF `program.py`'s ARRIVAL MARKERS, which is safe: those
    promotion rules need the marker and `.dr-flows` to be SIBLINGS, and another
    sibling in front of both changes nothing.

    Unconditional on purpose. `pagefoot.py` skips generated pages because there is
    no source file to offer an edit link for; a build stamp has no such dependency,
    and a generated page is exactly as capable of being stale as an authored one.
    """
    if not _FOOT:
        return html_body
    return _page_css(page) + _corner(page) + html_body + _FOOT
