"""Stage 01e -- a captioned image becomes a real `<figure>`, in pure markdown.

    ![Light plot, 42 instruments over three electrics](rep-plot.png){ caption="Rep plot, Ogunquit 2026" }

becomes a `<figure>` wrapping the image with a `<figcaption>` under it.

> Michael, 2026-08-06: *"Images already embed. I want captioning. Fine if we
> lose title. Accessibility is a bonus next build."*


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

Both follow `sheet.apply_options`, which argues the general case at length:
silence was asked for and refused, because *a table that looks right, behaves
wrong, and never says why* is worse than a warning. **A caption that renders
nothing must not look like a caption that rendered nothing visible.**

**AND `title` IS NOT SUPPORTED, BY RULING RATHER THAN BY OMISSION.** The HTML
`title` attribute does not appear on touch devices at all, is announced
inconsistently by screen readers, and cannot be reached by keyboard. Accepting
the key would mean shipping something that does not do what the author writing
it believes it does -- the failure this engine writes down more often than any
other. Michael released it explicitly on 2026-08-06.


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

#: A whole line, at zero indent, that is an image followed by a caption block.
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
    r"[ \t]*\{[ \t]*caption[ \t]*=[ \t]*(?P<q>[\"'])(?P<caption>[^\n]*?)(?P=q)[ \t]*\}"
    r"[ \t]*$"
)

#: Any image carrying a caption brace, anywhere. Run over what is LEFT after the
#: real pattern has done its work, so every remaining hit is by definition one
#: this stage declined -- indented, mid-sentence, or malformed. It exists so a
#: near miss is reported rather than handed to attr_list, which would put
#: `caption="..."` on the `<img>` as an invalid attribute: no error, no render,
#: no clue.
_ATTEMPT = re.compile(r"!\[[^\]\n]*\]\([^\n]*?\)[ \t]*\{[^}\n]*caption[^}\n]*\}")

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
        caption = match.group("caption").strip()
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
            src + ": `" + match.group(0)[:80] + "` was NOT turned into a figure. "
            + "A caption needs the image alone on its own line at zero indent -- "
            + "an indented one would be lifted out of its list item, and one "
            + "mid-sentence would break the paragraph in half. The image still "
            + "renders; the caption does not.",
        )
        return match.group(0)

    return sub_outside_code(_ATTEMPT, report, out)
