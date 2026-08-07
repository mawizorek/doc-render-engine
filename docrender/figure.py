"""Stage 01e -- a captioned image becomes a real `<figure>`, in pure markdown.

    ![Light plot, 42 instruments over three electrics](rep-plot.png){ caption="Rep plot, Ogunquit 2026" }

becomes a `<figure>` wrapping the image with a `<figcaption>` under it.

> Michael, 2026-08-06: *"Images already embed. I want captioning. Fine if we
> lose title. Accessibility is a bonus next build."*


A CAPTION MAY BE WRAPPED ACROSS LINES, AND A BLANK LINE ENDS IT
===============================================================

    ![Rep plot, three electrics and two box booms](rep-plot.png){ caption="Rep
    plot as hung for the 2026 season. Supersedes the plot in the
    [venue binder](@spac-binder)." }

How it is wrapped in the source cannot change what renders: internal whitespace
is collapsed to single spaces, so the figcaption is always one line of prose.

⚠️ **THE COST, STATED RATHER THAN DISCOVERED: a two-space hard break inside a
caption is destroyed by that collapse.** A figcaption is one line of prose, not
a paragraph, and a caption that wants a line break is a caption that wants to be
body text.

🔴 **THE BLANK-LINE BOUND IS THE SAFETY PROPERTY, NOT A STYLE RULE.** The
caption may contain a newline only where the next line is not blank -- which is
markdown's own block terminator, so the grammar borrows a rule every author here
already knows. Without it, a caption missing its closing quote would let a lazy
match run to the next `" }` ANYWHERE later in the document and swallow every
heading, table and paragraph in between into a single figcaption. Bounded, the
worst case is one ruined paragraph, reported.


🔴 THE IMAGE MARKDOWN IS RE-EMITTED BYTE-IDENTICAL, AND THAT IS THE WHOLE
   SAFETY PROPERTY OF THIS STAGE
========================================================================

MkDocs rewrites the `src` of an image **it** produced, so that `rep-plot.png`
beside `lighting/x.md` resolves from `lighting/x/` once `use_directory_urls`
moves the page into a folder of its own. It does NOT touch raw HTML that
somebody else wrote.

So the instant this file emits its own `<img src=...>`, it owns that arithmetic
-- and gets a 404 on every non-index page in the site. **That is not a
prediction, it is the bug `datatable.py` carries on its wall**: the TSV download
link was a 404 on every non-index page until 2026-08-04 for exactly this reason,
while the comment beside it asserted a bare filename was correct.

Hence the shape: **the WRAPPER is HTML and the IMAGE never is.** The matched
image is copied through as the literal characters the author typed, and
Python-Markdown plus MkDocs do to it precisely what they already do today.
Michael's *"images already embed"* stays exactly as true after this as before.

⚠️ **AND THAT RULE IS ALSO THE LIMIT ON WHERE AN IMAGE MAY LIVE.** MkDocs only
knows files inside `docs_dir`. A relative path cannot climb out of the content
tree, because a file outside it is not in the file set, is never copied to
`site_dir`, and 404s. An image in a SIBLING repo is therefore reached by
absolute published URL or copied in -- there is no `@peer:` equivalent for an
image, and `@peer:id` cannot be one: it resolves a PAGE against the peer's
`doc-index.json`, which lists pages and nothing else.


WHY md_in_html RATHER THAN BUILDING THE HTML
============================================

`md_in_html` is already enabled in `mkdocs.yml`, and it is what makes the rule
above affordable:

  `markdown="1"` on the `<figure>`      keeps the image in Python-Markdown's hands
  `markdown="span"` on the `<figcaption>` renders the caption INLINE, no `<p>`

⚠️ Block mode wraps the image in a `<p>`, which is cosmetic and left alone.
Removing it would mean emitting the `<img>` here, which is the one thing this
stage must not do.

⭐ THE CAPTION STAYS MARKDOWN AND IS NOT PRE-RENDERED, which is the opposite of
what `datatable.py` does with a table caption, deliberately. A table caption
goes through `cells.render` because the table is emitted as finished HTML at
stage 01b and anything half-converted inside it gets escaped a second time by
the later hooks -- the whole argument in `cells.py`. **A figure caption is page
body text sitting in the page's own markdown.** Hooks 03 and 03b sub over the
whole document, so `@`-references and `{.tbc}` markers in a caption resolve on
their ordinary pass, through the ordinary path, with no second implementation
and no second escape. Running `cells.render` here would rebuild the exact defect
it was written to end.

That is also why this stage is 01e: it must land **before** 03 and 03b. Same
relationship `01d_audit` has with `03b`, one stage over.


WHAT IT REFUSES, AND WHY EACH REFUSAL IS LOUD
=============================================

**ZERO INDENT ONLY.** A figure is block level. An indented image inside a list
item, re-emitted at column zero, would walk that content out of the list -- a
silent structural edit to a page nobody asked us to restructure. Reported.

**WHOLE LINE ONLY.** An image mid-sentence is inline by intent; wrapping it in a
block element would break the paragraph in half. Reported.

**AN UNTERMINATED OR MALFORMED CAPTION.** Reported, and this one was NOT before
2026-08-06: the near-miss scan bounded its own search at a newline, so the
wrapped-caption case it most needed to catch was the one case it could not see.
A reporter with the same blind spot as the thing it reports on is not a
reporter. Fixed by dropping the closing brace from the scan entirely -- an
unclosed brace is precisely a near miss.

All three follow `sheet.apply_options`, which argues the general case at length:
silence was asked for and refused, because *a table that looks right, behaves
wrong, and never says why* is worse than a warning. **A caption that renders
nothing must not look like a caption that rendered nothing visible.**

**AND `title` IS NOT SUPPORTED, BY RULING RATHER THAN BY OMISSION.** The HTML
`title` attribute does not appear on touch devices at all, is announced
inconsistently by screen readers, and cannot be reached by keyboard. Accepting
the key would mean shipping something that does not do what the author writing
it believes it does -- the failure this engine writes down more often than any
other. Michael released it explicitly on 2026-08-06.

⚠️ **WHAT WE COULD NOT REMOVE IS MARKDOWN'S OWN TITLE**, and an author WILL find
it: `![alt](file.png "a title")` still emits a `title` attribute, through
Python-Markdown, with no involvement from this stage. So "no title support"
reads as false to anybody who tries it. That is a documentation obligation
rather than a code one -- the authoring page has to say *markdown's quoted title
still works, it does nothing useful, use a caption* -- and it is written here so
the next reader of this file knows the difference is deliberate.


⏳ THE SEAM FOR THE ACCESSIBILITY BUILD, NAMED NOT BUILT
========================================================

`alt` is captured by the pattern and deliberately unused. It already works --
it is the bracket text, and Python-Markdown puts it on the `<img>` -- so nothing
here needs to touch it.

What is PARKED (Michael: *"a bonus next build"*) is reporting a missing or
empty one, and the argument to have then rather than now:

  * **alt REPLACES the image; a caption ACCOMPANIES it.** They are different
    sentences. *"Rep plot, Ogunquit 2026"* labels the image and describes
    nothing, which is a fine caption and useless alt.
  * 🚫 **A caption must never be copied into an empty alt.** It is the
    convenient answer and it manufactures confidently wrong accessibility,
    silently, everywhere. Report the gap instead.
  * An empty `alt=""` is a real and correct value for a decorative image, so the
    check is *"did the author decide"*, not *"is the string non-empty"* -- which
    is the same shape as `summary` becoming a required field on 2026-08-03.


NO STYLESHEET SHIPS WITH THIS
=============================

Material already styles `.md-typeset figure` and `.md-typeset figcaption`, and
`assets/print.css` already carries `figure` and `img` in its `break-inside:
avoid` list. The `dr-figure` / `dr-figure__caption` classes exist as the hook for
a later sheet; they are not a promise of one. ⚠️ Print has no size cap on an
image yet, so a large screenshot can still own a whole sheet of paper -- known,
unfixed, and not this stage's job.

Code is skipped via `util.sub_outside_code` -- see that function for why. The
page documenting this syntax must not have its own example rewritten by it.
"""

from __future__ import annotations

import re

from . import state
from .util import sub_outside_code

#: A run of text that may wrap but may not cross a BLANK line. Used for the
#: caption body and for the near-miss scan, so both agree about how far a
#: caption is allowed to reach -- they disagreed until 2026-08-06 and the
#: reporter was blind to exactly the case the matcher could not handle.
#:
#: 🔴 The bound is what makes a lazy match safe. Without it, a missing closing
#: quote lets the pattern run to the next `" }` anywhere later in the document.
_WRAPPED = r"(?:[^\n]|\n(?![ \t]*\n))"

#: An image alone on its own line at zero indent, carrying a caption block.
#:
#: `image` is copied through untouched -- see the module docstring on why nothing
#: here may rebuild the `<img>`. `target` is whatever sits between the parens and
#: is never parsed; a markdown title inside it survives into Python-Markdown as
#: usual, which is not the same thing as this stage supporting `title=`.
#:
#: The caption is delimited by its QUOTES, not by the braces, so a caption may
#: contain `}` freely. Both quote styles are accepted so a caption may contain
#: the other one.
_FIGURE = re.compile(
    r"(?m)^(?P<image>!\[(?P<alt>[^\]\n]*)\]\((?P<target>[^\n]*?)\))"
    r"[ \t]*\{[ \t]*caption[ \t]*=[ \t]*(?P<q>[\"'])"
    r"(?P<caption>" + _WRAPPED + r"*?)"
    r"(?P=q)[ \t]*\}[ \t]*$"
)

#: An image followed by a brace block mentioning `caption`, closed or NOT. Run
#: over what is LEFT after the real pattern has done its work, so every hit is by
#: definition one this stage declined -- indented, mid-sentence, unterminated or
#: otherwise malformed.
#:
#: ⚠️ NO CLOSING BRACE IS REQUIRED, and that is the fix rather than sloppiness:
#: requiring one meant an unterminated caption -- the likeliest mistake once
#: wrapping is legal -- matched nothing and was reported nowhere.
#:
#: ⚠️ It cannot match this module's own output. The emitted block puts a blank
#: line between the image and the `<figcaption ...>` element, and this pattern
#: needs a `{` immediately after the image.
_ATTEMPT = re.compile(
    r"!\[[^\]\n]*\]\([^\n]*?\)[ \t]*\{" + _WRAPPED + r"*?caption"
)

_SPACE = re.compile(r"\s+")

_BLOCK = (
    '\n<figure class="dr-figure" markdown="1">\n'
    "\n"
    "{image}\n"
    "\n"
    '<figcaption class="dr-figure__caption" markdown="span">{caption}</figcaption>\n'
    "\n"
    "</figure>\n"
)


def on_page_markdown(markdown, page, config, files):
    if "caption" not in markdown or "![" not in markdown:
        return markdown

    src = page.file.src_uri

    def build(match):
        # Collapsed, so how the author wrapped the source cannot change what a
        # reader sees -- and so the emitted figcaption is always one line, which
        # keeps md_in_html's span mode away from content it has no reason to see.
        caption = _SPACE.sub(" ", match.group("caption")).strip()
        if not caption:
            # An empty figcaption is a blank line under a picture with a
            # stylesheet reserving space for it. The author wrote `caption=`
            # meaning to say something; say that they did not.
            state.note(
                "dead_links",
                src + ": an image carries an empty `caption=\"\"`. No figure was "
                + "built and the image renders exactly as before. Write the "
                + "caption, or drop the attribute.",
            )
            return match.group("image")
        return _BLOCK.format(image=match.group("image"), caption=caption)

    out = sub_outside_code(_FIGURE, build, markdown)

    def report(match):
        state.note(
            "dead_links",
            src + ": `" + _SPACE.sub(" ", match.group(0))[:80] + "` was NOT turned "
            + "into a figure. A caption needs the image alone on its own line at "
            + "zero indent, and a `caption=\"...\"` closed with a matching quote "
            + "and brace before the next blank line. It may wrap; it may not "
            + "cross a blank line. The image still renders; the caption does not.",
        )
        return match.group(0)

    return sub_outside_code(_ATTEMPT, report, out)
