"""Hook 07 -- the build stamp and the printed letterhead. Two placements, one fact.

Answers one question from any page without opening Actions: is what I am looking at
the latest push? When a build fails, GitHub Pages keeps serving the previous commit
with no banner and no error page -- the site simply stops changing, and there is no
other signal that has happened.

    .buildstamp--corner   FIRST in flow, PRINT ONLY.   [logo]  URITP Safety - Fall 2026
    .buildstamp--foot     LAST in flow, SCREEN ONLY.   URITP Safety + a disclosure

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
🚫 THE HARD RULES, WITH THEIR REASONS ONE FILE OVER
=============================================================================
🚫 **TWO FACTS ON THE PRINTED LINE. NOT THREE.** It has refused the PR number
(08-19) and a program name (08-28). A line carrying two facts is a stamp; three is
a header. § *The corner mark is SITE + DATE* in the sibling.

✅ **A LOGO IS NOT A THIRD CLAUSE, IT IS A MARK** -- which is why the letterhead was
allowed on 2026-08-29 where two text additions were not. § *THE LETTERHEAD*.

🔴 **THE BUILD IDENTIFIER IS SCREEN-ONLY.** Provenance for the BUILDER is noise for
the READER, and print is the surface where the reader is not the builder.

🔴 **THE `hidden` ATTRIBUTE IS DOING REAL WORK.** The corner copy ships with
`hidden` (UA `display: none`); any AUTHOR `display` beats a UA one, so
`print-chrome.css`'s `@media print { display: block }` reveals it on paper and
nothing reveals it on screen. That is what keeps this feature from touching a single
screen stylesheet. It also drops the corner copy from the accessibility tree, which
is correct -- the foot copy is the one a screen reader should find.

⭐ **WHY THE CORNER COPY IS FIRST IN THE FLOW.** An element appended at the END of
the content cannot be moved to the TOP of sheet one by CSS: that needs knowledge of
where the page boundary falls, which is what `@page` margin boxes do and no major
browser implements. First in flow IS the top of sheet one, for free.

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
page: still one claimant. § *The date is still built ONCE*.

=============================================================================
⚠️ THE STYLING IS SPLIT ACROSS TWO SHEETS ON PURPOSE
=============================================================================
    print-chrome.css    the stamp's own BOX -- and `display: block`, which is what
                        overrides `hidden`. Delete it there and the letterhead
                        renders nothing, with nothing reporting it.
    print-identity.css  the LETTERHEAD ROW -- flex, the mark, the two weights.

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
#: `_FOOT` is the whole screen node.
_CORNER_TEXT = ""
_FOOT = ""


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


def on_config(config):
    global _CORNER_TEXT, _FOOT

    label = _label()

    # Runners are UTC. Stamp Eastern so the date means something to a human in
    # Rochester rather than needing mental arithmetic at 4am.
    eastern = datetime.timezone(datetime.timedelta(hours=-4))
    when = datetime.datetime.now(datetime.timezone.utc).astimezone(eastern)

    # The site name travels with the printed copy, because a printed sheet leaves
    # the system entirely and a bare period names nothing a reader can place.
    name = str(getattr(config, "site_name", "") or "").strip()
    period = _period(when)

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
    """Wrap the page body: letterhead first, foot line last.

    ⚠️ THE CORNER IS PREPENDED, WHICH IS NET-NEW IN THIS ENGINE. Every other
    `on_page_content` consumer appends -- `pagefoot.py` (06), `router.py` (04b) and
    this hook until 2026-08-19. Nothing downstream depends on the first element of
    the body being the `h1`, and `print.css` already targets
    `.md-content__inner > :first-child` for a margin reset, which the corner mark
    now satisfies instead of the heading.

    ⚠️ AND IT LANDS AHEAD OF `program.py`'s ARRIVAL MARKERS, which is safe: those
    promotion rules need the marker and `.dr-flows` to be SIBLINGS, and another
    sibling in front of both changes nothing.

    Unconditional on purpose. `pagefoot.py` skips generated pages because there is
    no source file to offer an edit link for; a build stamp has no such dependency,
    and a generated page is exactly as capable of being stale as an authored one.
    """
    if not _FOOT:
        return html_body
    return _corner(page) + html_body + _FOOT
