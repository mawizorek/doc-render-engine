"""THE RUNNING FURNITURE -- a real page header and footer on EVERY printed sheet.

Not a hook. A helper module that `buildstamp.py` (hook 07) imports and calls from its
existing `on_page_content`, which is the whole reason this file can exist at all --
see § WHY THIS IS NOT A HOOK.

    @top-left      the mark          @top-right      site · period
    @bottom-left   Revised <date>    @bottom-center  Page N of M
                                     @bottom-right   Posted by <name>
                                                     <email>

> Michael, 2026-08-30: *"i DOOO want to see the header repeated on every printed page
> now, and the footer that says 'revised' and my name now, also repeated as a footer
> on each page. so once printed, locking those two elements to true page headers and
> footers. this is a change from what i've said in the past, but looking at this
> print it's very clear to me what I want to see now."* Page number: *"i like center
> for page No."*

=============================================================================
🔴 THE BLOCKER OUR OWN CODE DOCUMENTED WAS TRUE, AND IS NOW FALSE
=============================================================================
`buildstamp.py` explains why the printed letterhead is FIRST IN FLOW rather than
repeated, and its stated reason was that repeating it *"needs knowledge of where the
page boundary falls, which is what `@page` margin boxes do and no major browser
implements."* That was correct when written.

**Chrome 131 shipped all sixteen margin boxes in November 2024. Safari 18.2 followed
in December 2024** -- including `counter(page)`, `counter(pages)` and `content: url()`.

⚑ **A SENTENCE ASSERTING THAT A CAPABILITY DOES NOT EXIST IS A FACT WITH AN EXPIRY
DATE, AND NOTHING FAILS WHEN IT PASSES.** Third instance of that shape found in one
session -- the others were `instances/uritp/site.yml` claiming the letterhead was
"NOT BUILT" the day after it shipped, and `foot.css` predicting the browser was the
unverified half when the browser was the half that worked. 🚩 The class is now named:
**a capability claim is the one kind of comment that rots without anybody editing it,
because the world moves instead of the code.** It cannot be caught by a doc-rot sweep
against HEAD, because HEAD still agrees with itself.

=============================================================================
⭐ THE DESIGN TURN THAT MAKES THIS CHEAP
=============================================================================
A margin box cannot read document content. The spec's answer is `string-set` /
`string()`, and **no browser implements it** -- normally that kills a running header
carrying per-document values, and it is why every guide on this reaches for Paged.js.

**It does not bite here, and the reason is structural rather than clever:**
`revised:` is a PER-DOCUMENT fact and every MkDocs page IS exactly one document. So
the engine writes that page's own values into that page's own `@page` rule at build
time. No named strings, no polyfill, nothing at read time, no new dependency.

⚠️ WHICH IS WHY THIS IS EMITTED AS A PER-PAGE `<style>` RATHER THAN LIVING IN A
SHEET. A stylesheet is shared by every page; the revision date is not. Same reason
`buildstamp._corner` writes the letterhead URL inline instead of as a custom
property -- one computed fact per page, resolved for that page.

=============================================================================
🔴 WHY THIS IS NOT A HOOK, AND WHY THAT IS THE POINT
=============================================================================
The obvious shape is a new hook module. `mkdocs.yml` is **28,158 B** and the GitHub
MCP standard forbids `create_or_update_file` on files over ~30KB, so a hook
registration has been an unavailable write for weeks -- it is the debt named in
`lede.py`, in `specs/print-control.md` §7, and twice in this session's PRs.

✅ **A PLAIN HELPER IMPORTED BY AN ALREADY-REGISTERED HOOK NEEDS NO REGISTRATION.**
Only hooks go in `mkdocs.yml`; a module that hook 07 imports is just Python. ⚑ *The
blocker was on the shape I assumed, not on the outcome I wanted* -- and it went
unexamined for three size-limit passes on `buildstamp.py` before anybody asked
whether the feature needed to be a hook at all.

🔴 AND THE SIZE PRESSURE IS THE REASON THIS FILE EXISTS, STATED PLAINLY. Keeping this
in `buildstamp.py` took that file to **27,760 B**, then 24,641 B, then 23,062 B
against a **22,528 B** read ceiling -- three trims, each one shaving narrative that
had been written to explain a real defect. ⚑ *A file that cannot absorb a feature's
reasoning is telling you the feature has its own subject.* `buildstamp.py` is back
to near its pre-feature size and keeps only a pointer.

=============================================================================
🔴 THE BLOCK AXIS IS OURS. THE INLINE AXIS IS NOT. DO NOT TOUCH IT.
=============================================================================
`print.css` sets `@page { margin: 12mm }` and calls the inline half **"the
load-bearing half"**: the printed column is a container query context, and the data
table flips to list mode under 640px. That same file states **"the BLOCK axis is free
to change."**

A margin box's height IS the page margin, so the furniture needs room. `page_css`
therefore sets ONLY `margin-top` and `margin-bottom`.

✅ TWO RULES ON `@page`, DISJOINT PROPERTY SETS, NO CASCADE FIGHT -- exactly the
argument `print-space.css` already makes for `h1` living in two files. 🚫 Adding
`margin-left` or `margin-right` here silently converts every data table on the sheet
into a key/value stack, at print time, with no build report to say so.

=============================================================================
🚩 THE MARGIN TRAP -- A REGRESSION THIS FEATURE INTRODUCES, MEASURED
=============================================================================
Because a margin box's height is the page margin, **a reader who picks "None" in the
print dialog deletes the footer.** Measured in the print engine:

    @page margin   header   posted-by   page number
    40/32pt          yes       yes         yes
    20pt             yes       yes         yes
    10pt             yes       yes         yes
     2pt             yes      GONE        GONE
     0               yes      GONE        GONE

Chrome's own documentation adds a worse quirk: **if page ONE has no room, later pages
lose their margin content too**, even where there is space.

⚠️ TODAY'S IN-FLOW STAMP SURVIVES ANY MARGIN. This does not. A dropdown in a print
dialog can now erase the author's name and the page numbers off a posted safety
sheet. `specs/print-control.md` §8 carries it as the standing item, with Michael's
two real use cases (binder gutter, half-sheet pamphlet) and the computed ceilings.

⚠️ AND THE FIRST MEASUREMENT OF THIS SAID EVERYTHING SURVIVED AT ZERO MARGIN. It
counted dark pixels in the top and bottom bands of the raster, and the tell that it
was lying was that the counts went UP as margins shrank -- body text moving into the
band, not furniture staying in it. Re-run with per-page text extraction for the exact
strings. ⚑ *A proxy metric that moves in the right direction for the wrong reason is
worse than no metric: it produces the reassuring answer.*

=============================================================================
🚩 FIREFOX PRINTS NO FURNITURE AT ALL, AND IT IS ACCEPTED
=============================================================================
Firefox supports `@page` margins but not margin boxes (Mozilla bug 1854974, unshipped
as of 2026). A Firefox printout therefore gets the wider block margins and an empty
band -- no header, no footer, no page number. **Michael accepted Chrome and Safari
only, 2026-08-30**, and he prints from Chrome.

⚠️ THE IN-FLOW CORNER COPY IS NOT KEPT AS A FALLBACK, and that is a real trade rather
than an oversight. There is no CSS test for margin-box support, so a visible in-flow
letterhead would DOUBLE the header on every Chrome sheet. One or the other; the
engine cannot have both without a feature query that does not exist.

=============================================================================
⚠️ WHAT IS VERIFIED, AND IN WHICH ENGINE -- READ THIS BEFORE TRUSTING ANY OF IT
=============================================================================
✅ **TEXT, COUNTERS AND THE TWO-LINE FOOTER: VERIFIED.** Rendered a multi-page
document and extracted text PER PAGE: header, `Revised <date>`, `Page N of M` with
the right N, `Posted by <name>` and the email on its own line, on every page, with
the in-flow copies suppressed and no value duplicated.

🔴 **THE LOGO IN A MARGIN BOX: NOT VERIFIED, AND THE ENGINE THAT FAILS IT IS NOT THE
ENGINE THAT MATTERS.** WeasyPrint 69 renders NOTHING for `content: url()` in a margin
box -- proven against a working control (a body `<img>` rasterised 11,711 red pixels;
the margin box zero, on three consecutive pages). Chrome 131+ and Safari 18.2+ both
document support.

⚑ **THE ENGINE THAT COULD BE TESTED IS NOT THE ENGINE THAT PRINTS.** WeasyPrint is
the harness; Michael prints from Chrome, and his screenshots are Chrome print
preview. **That inverts the verification posture every other measurement in this
feature relied on** -- and it is the same mistake `foot.css` made in the opposite
direction hours earlier, when it predicted the browser was the risky half and paper
was the proven one. 🚩 If the mark is missing from a Chrome printout, the `@top-left`
line below is the only suspect and `print-identity.css` holds the one-rule revert.
"""

from __future__ import annotations

from . import state

#: The block-axis room the margin boxes need.
#:
#: ⚠️ 16mm RATHER THAN 12, MEASURED FROM SHIPPED VALUES rather than chosen: the
#: letterhead mark is 8.46mm tall (`print-identity.css`) and the footer's right box is
#: TWO lines at 8.5pt (~6mm). 12mm fits neither with air.
BAND = "16mm"


def css_string(text) -> str:
    """ONE CSS string literal, quoted and escaped.

    🔴 A BACKSLASH AND A DOUBLE QUOTE ARE THE WHOLE ATTACK SURFACE, and both are
    escaped rather than stripped. `revised:` is authored on every page of a content
    repo that agents may not commit to -- and therefore may not sanitise either. An
    unescaped quote would not "look wrong": it would terminate the string, invalidate
    the entire `@page` rule, and drop the header AND footer from every page of that
    document, silently, with nothing reported.

    🔴 IT COLLAPSES WHITESPACE, SO NEVER HAND IT A MULTI-LINE VALUE. `" ".join(split())`
    splits on newlines too. The first version of the footer built `"line one\\nline
    two"`, passed it through here, and got one flat line -- the `\\A` substitution that
    followed had nothing left to match. **Caught by reading the code back, not by a
    render, because the output looked entirely plausible.** ⚑ *A helper that normalises
    its input silently defeats any caller encoding meaning in the characters it
    normalises.* Multi-line content is built as SEPARATE calls joined by an escaped
    line feed -- see `page_css`.
    """
    s = " ".join(str(text or "").split())
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def page_css(page, logo_url: str, site: str, period: str) -> str:
    """The `@page` rule for THIS page. `""` when there is nothing worth saying.

    Takes the letterhead URL, site name and period from `buildstamp.py` rather than
    re-deriving them: that module resolves the logo through the image index and builds
    the season string ONCE at `on_config`, and a second derivation here would be a
    second claimant on facts that already have one.

    ⭐ THE LAYOUT MIRRORS WHAT THE SCREEN ALREADY DOES, which is why it needed no
    design pass. `revised` has held the left of the screen footer since 2026-08-07 and
    the ownership tag the right since 2026-08-30. The page number takes the centre
    because it is the one fact belonging to the SHEET rather than to the document.

    ✅ `counter(pages)` GIVES THE TOTAL, and that is the safety argument for having it
    rather than a bare number: **a stapled packet found on a desk announces that it is
    incomplete.** On a safety document that is a real property, not a nicety.

    ⚠️ THE FOOTER IS THREE SEPARATE BOXES, WHICH IS WHY IT DOES NOT BREAK THE
    TWO-FACTS-ON-A-LINE RULE. `buildstamp.py` refused a PR number (08-19) and a
    program name (08-28) because *"a line carrying two facts is a stamp; three is a
    header."* That rule governs ONE line. Left, centre and right each carry one fact,
    which is the opposite of crowding.

    🔴 EVERY VALUE IS OPTIONAL AND EACH BOX IS OMITTED RATHER THAN EMITTED EMPTY. A
    margin box whose `content` computes to `none` is not generated at all, so an
    omitted box costs nothing -- an emitted empty string still reserves it. A site
    with no `owner:` prints a header and a page number and no name: the
    absent-means-off polarity `print:` and `routes.yml` already have.

    ⚠️ AND IT RETURNS `""` WHEN THE PAGE COUNTER WOULD BE THE ONLY OCCUPANT, so the
    block-axis margin change never lands on a page with no furniture to make room for.
    Such a page prints exactly as it did before this feature existed -- which is what
    keeps five of six sites untouched by this landing.
    """
    boxes = []

    if logo_url:
        # 🚩 CHROMIUM-ONLY AND UNVERIFIED. See § WHAT IS VERIFIED: WeasyPrint 69 renders
        # nothing for this, proven against a working control; Chrome 131+ documents
        # support. If the mark is missing from a Chrome printout, this is the suspect.
        boxes.append("@top-left{content:url(" + css_string(logo_url) + ")}")

    if site and period:
        boxes.append(
            "@top-right{content:"
            + css_string(site) + ' " \\00B7 " ' + css_string(period)
            + "}"
        )

    meta = state.BY_SRC.get(page.file.src_uri, {})
    revised = str(meta.get("revised") or "").strip()
    if revised:
        # The LABEL is engine-supplied exactly as in `lede.revised()`, and neither
        # emitter reformats the value -- that function carries why a human's
        # provenance string is passed through verbatim.
        boxes.append("@bottom-left{content:" + css_string("Revised " + revised) + "}")

    boxes.append('@bottom-center{content:"Page " counter(page) " of " counter(pages)}')

    owner = state.INSTANCE.get("owner") or {}
    name = owner if isinstance(owner, str) else (owner.get("name") or "")
    email = "" if isinstance(owner, str) else (owner.get("email") or "")
    if str(name).strip():
        # 🔴 TWO SEPARATE CALLS, NOT ONE JOINED STRING, and this is the newline bug's
        # fix rather than a style choice. `css_string` collapses whitespace, so a
        # `\n` handed to it vanishes before any substitution can see it. An escaped
        # line feed BETWEEN two literals cannot be normalised away.
        #
        # ⚠️ `white-space: pre` is what makes the `\A` a line break rather than a
        # space. Without it the two literals render on one line and the bug looks
        # like it came back.
        content = css_string("Posted by " + str(name))
        if str(email).strip():
            content += ' "\\A " ' + css_string(email)
        boxes.append("@bottom-right{content:" + content + ";white-space:pre}")

    if len(boxes) <= 1:
        return ""

    return (
        "<style>@page{margin-top:" + BAND + ";margin-bottom:" + BAND + ";"
        + "".join(boxes)
        + "}</style>"
    )
