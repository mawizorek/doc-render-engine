"""THE RUNNING FURNITURE -- a page header and footer on every printed sheet.

🔴 **OFF BY DEFAULT SINCE 2026-08-30 ~22:15. OPT IN PER SITE WITH `print: running:
true`, AND NO INSTANCE DECLARES IT TODAY.** It did not paint in the browser that
actually prints these documents. § WHY IT IS OFF, which is the first thing to read;
nothing else in this file matters until that section is resolved.

Not a hook. A helper `buildstamp.py` (hook 07) imports and calls from its existing
`on_page_content` -- see § WHY THIS IS NOT A HOOK.

    @top-left      the mark          @top-right      site · period
    @bottom-left   Revised <date>    @bottom-center  Page N of M
                                     @bottom-right   Posted by <name>
                                                     <email>

> Michael, 2026-08-30: *"i DOOO want to see the header repeated on every printed page
> now, and the footer that says 'revised' and my name now, also repeated as a footer
> on each page. so once printed, locking those two elements to true page headers and
> footers."* Page number: *"i like center for page No."*

=============================================================================
🔴 WHY IT IS OFF, AND WHAT WOULD TURN IT BACK ON
=============================================================================
Michael printed from Chrome with margins at **Default** and got Chrome's own UA
header (site name, URL) and none of ours. He printed again with **"Headers and
footers" UNTICKED** and got **nothing at all** -- no letterhead, no name, no page
number. Two dialog states, neither painted a single margin box.

⚠️ SO THE CAUSE IS STILL UNKNOWN, and this file must not pretend otherwise. What is
RULED OUT: the build (both sites serve the correct bytes and the emitted `@page`
block is present and well-formed in the built HTML), the packet's `@page` (there
isn't one), and the UA header stacking on top of ours (unticking removed the UA
furniture and revealed nothing underneath).

🚩 **THE ONE FACT THAT DECIDES IT IS THE CHROME VERSION.** Margin boxes need Chrome
**131+** (Nov 2024) or Safari **18.2+**; below that every `@page` margin at-rule is
parsed and discarded in silence. **There is no feature query for it** -- `@supports`
cannot test an at-rule -- so the engine cannot detect this and cannot fall back.
That asymmetry is the whole reason the default flipped rather than the code changing.

⚠️ A SECOND CANDIDATE, NOT RULED OUT: 16mm was chosen to fit an 8.46mm mark plus a
two-line footer, and an independent report puts Chrome's UA-furniture threshold at
~8mm -- so our band is comfortably inside the range where Chrome wants that space
for itself. Chrome's own documentation says it adds UA content *"even if you have
added content"*, which contradicts the third-party guides claiming author boxes
suppress the UA pair. ⚑ *Two sources disagreeing is not evidence, it is a prompt to
go look -- and the deciding artifact is the dialog, not the docs.*

=============================================================================
⚑ THE ARCHITECTURAL LESSON, WHICH OUTLIVES THIS FEATURE
=============================================================================
The damage was never the boxes failing. It was that `print-identity.css` hid the
in-flow letterhead, revision line and ownership tag **on paper**, on the promise
that these boxes replaced them -- a stylesheet making a promise about a mechanism in
ANOTHER FILE, with nothing linking the two. When the boxes did not paint, the CSS
fired anyway and took the fallback with it: **a bare, unsigned safety sheet**,
strictly worse than what it replaced.

🔴 **A RULE THAT HIDES A BECAUSE B EXISTS MUST BE EMITTED BY WHATEVER EMITS B.** So
`page_css` now writes those hide rules into the SAME `<style>` block that creates the
boxes. No boxes, no hiding -- structurally, not by anyone remembering. ⚠️ The
equivalent rules in `print-identity.css` are DELETED, not commented: two claimants on
one behaviour is how this repo loses an afternoon.

✅ AND THAT MAKES THE FEATURE SAFE TO SHIP EVEN WHILE IT IS BROKEN. Worst case on a
supporting browser is DUPLICATION (letterhead in the corner box and in flow), which a
reader can see and report. Worst case before was an absence, which nobody can see.
⚑ *Prefer a failure a reader will notice over one that looks deliberate.*

=============================================================================
🔴 THE CAPABILITY CLAIM THAT STARTED THIS, AND ITS MIRROR
=============================================================================
`buildstamp.py` said the letterhead is first-in-flow because repeating it *"needs
... `@page` margin boxes ... and no major browser implements"* them. That was true
when written and false by Nov 2024. ⚑ **A capability claim is the one kind of comment
that rots with nothing edited, because the WORLD moves instead of the code** -- no
doc-rot sweep against HEAD can catch it, since HEAD still agrees with itself. Four
instances in one session, including `packet.py` writing the same claim while this
module was already using the feature.

🔴 AND THE MIRROR IS THE LESSON THIS FILE ADDS: **the correction can be as wrong as
the claim.** "No browser implements it" became "Chrome 131 implements it, therefore
it works here," which is a documented capability standing in for a verified one.
Michael's browser is the only authority that mattered and it was never asked.

=============================================================================
⭐ THE DESIGN TURN THAT MADE IT CHEAP -- AND ITS ONE EXCEPTION
=============================================================================
A margin box cannot read document content, `string-set` is unimplemented everywhere,
and that normally forces Paged.js. It does not bite here: `revised:` is PER-DOCUMENT
and every MkDocs page IS one document, so the engine writes that page's own values
into that page's own `@page` rule at build time.

🔴 **FALSE FOR EXACTLY ONE PAGE: a BUILD 10 program PACKET**, which splices N members
into one document -- N `@page` rules, last one wins, section nine's date on every
sheet. Fixed by `STYLE_CLASS` below plus `packet._STRIP`; § `packet.py`.

=============================================================================
🔴 WHY THIS IS NOT A HOOK, AND WHY THAT IS THE POINT
=============================================================================
`mkdocs.yml` is **28,158 B** and the GitHub MCP standard forbids
`create_or_update_file` over ~30KB, so a hook registration has been an unavailable
write for weeks -- the debt named in `lede.py` and `specs/print-control.md` §7.

✅ **A PLAIN HELPER IMPORTED BY AN ALREADY-REGISTERED HOOK NEEDS NO REGISTRATION.**
⚑ *The blocker was on the shape I assumed, not the outcome I wanted* -- unexamined
for three size-limit passes on `buildstamp.py` (27,760 → 24,641 → 23,062 against
22,528) before anybody asked whether this had to be a hook at all.

=============================================================================
🔴 THE BLOCK AXIS IS OURS. THE INLINE AXIS IS NOT.
=============================================================================
`print.css` sets `@page { margin: 12mm }` and calls the inline half *"the
load-bearing half"*: the printed column is a container query context and the data
table flips to list mode under 640px. The block axis it calls *"free to change."*
`page_css` sets ONLY `margin-top`/`margin-bottom`, because a margin box's height IS
the page margin. 🚫 Never add left or right here: it silently converts every data
table on the sheet into a key/value stack, at print time, with no report.

🚩 AND THE BLOCK AXIS HAS ITS OWN TRAP, MEASURED: at 2pt and 0 the posted-by line and
the page number vanish while the header survives, because a margin box's height IS
the margin. Chrome adds that if page ONE has no room, later pages lose theirs too.
`specs/print-control.md` §8 carries it with Michael's binder and pamphlet cases.
⚠️ The first measurement of that said everything survived at zero margin: it counted
dark pixels in the top and bottom bands, and the tell was the counts going UP as
margins shrank -- body text moving into the band, not furniture staying in it.
⚑ *A proxy metric that moves in the right direction for the wrong reason produces
the reassuring answer.*

=============================================================================
⚠️ WHAT IS VERIFIED, AND IN WHICH ENGINE
=============================================================================
✅ TEXT, COUNTERS AND THE TWO-LINE FOOTER, in WeasyPrint: per-page extraction found
the header, `Revised <date>`, `Page N of M` with the right N, and the two-line
posted-by on every page, with the in-flow copies suppressed and nothing duplicated.
✅ The packet collision, both ways, against the real `packet._cut`: three surviving
`@page` rules before `STYLE_CLASS`, zero after, bodies intact.

🔴 **AND NONE OF IT REACHED PAPER IN THE BROWSER THAT PRINTS THESE.** The logo in a
margin box was already known-unverified (WeasyPrint renders nothing for
`content: url()` there, proven against a working control); the text boxes were
verified in WeasyPrint and then **failed in Chrome too**. ⚑ *The engine that could be
tested was not the engine that prints, and a green result in the harness is a
statement about the harness.*
"""

from __future__ import annotations

from . import state

#: The block-axis room the margin boxes need.
#:
#: ⚠️ 16mm RATHER THAN 12, MEASURED FROM SHIPPED VALUES rather than chosen: the
#: letterhead mark is 8.46mm tall (`print-identity.css`) and the footer's right box is
#: TWO lines at 8.5pt (~6mm). 12mm fits neither with air. 🚩 AND IT IS A SUSPECT IN THE
#: 08-30 failure -- see § WHY IT IS OFF: Chrome's UA-furniture threshold is reported at
#: ~8mm, so this band sits inside the range where Chrome wants the space itself.
BAND = "16mm"

#: 🔴 THE CLASS ON THE `<style>` ELEMENT, LOAD-BEARING RATHER THAN COSMETIC. A
#: `<style>` needs no styling, so it shipped unclassed and was **invisible to
#: `packet._cut`**, the class-based transform that strips per-section furniture --
#: which let N members' `@page` rules survive into one packet. Named as a constant so
#: the emitter and `packet._STRIP` cannot drift apart silently; `packet.py` imports it
#: rather than retyping the string.
STYLE_CLASS = "dr-runfoot"

#: 🔴 THE HIDE RULES TRAVEL WITH THE BOXES, AND THAT IS THE WHOLE POST-MORTEM OF THE
#: 08-30 regression. They lived in `print-identity.css` for six hours, hiding the
#: in-flow furniture on paper on the promise these boxes replaced it -- and when the
#: boxes did not paint, the promise was still enforced and the sheet came out bare.
#: Emitted here, they cannot outlive the thing they depend on.
#:
#: ⚠️ SPECIFICITY: (0,2,0) beats print-chrome.css's `.buildstamp--corner`
#: `display: block` at (0,1,0) outright, so source order is never consulted -- and it
#: creates no selector-and-property PAIR with any print sheet, which is the invariant
#: `assets.py` and print-chrome.css both assert.
#:
#: ⚠️ `.dr-revised` IS CHILD-ONLY AND THE THREE ARE DELIBERATELY NOT ALIKE. On an
#: ordinary page it is a direct child and hides; inside a packet SECTION it is a
#: grandchild and STAYS, because a packet's members were revised on different dates
#: and that per-section date exists nowhere else in the document. ⚑ *The ownership tag
#: is one fact repeated N times; a revision date is N facts sharing an element. Ask
#: whether the VALUE varies, not whether the element does.*
_HIDE_INFLOW = (
    "@media print{"
    ".md-typeset .buildstamp--corner,.md-typeset .dr-owner{display:none}"
    ".md-typeset > .dr-revised{display:none}"
    "}"
)


def enabled() -> bool:
    """Does this site opt in to running headers and footers? DEFAULT: NO.

    🔴 ABSENT MEANS OFF, which is the opposite of how this shipped and the whole point
    of the 08-30 correction. `print: running: true` in `instances/<slug>/site.yml`
    turns it on for one site; nothing declares it today.

    ⚠️ DO NOT FLIP THE DEFAULT WITHOUT A REAL PRINT PREVIEW. Margin boxes need Chrome
    131+ / Safari 18.2+, there is no feature query, and a browser below that discards
    every `@page` margin at-rule in silence. § WHY IT IS OFF.
    """
    return bool((state.INSTANCE.get("print") or {}).get("running"))


def css_string(text) -> str:
    """ONE CSS string literal, quoted and escaped.

    🔴 A BACKSLASH AND A DOUBLE QUOTE ARE THE WHOLE ATTACK SURFACE, and both are
    escaped rather than stripped. `revised:` is authored on every page of a content
    repo agents may not commit to -- and therefore may not sanitise either. An
    unescaped quote would not "look wrong": it would terminate the string, invalidate
    the entire `@page` rule, and drop the header AND footer from every page of that
    document, silently.

    🔴 IT COLLAPSES WHITESPACE, SO NEVER HAND IT A MULTI-LINE VALUE. `" ".join(split())`
    splits on newlines too. The first footer built `"line one\\nline two"`, passed it
    through here, and got one flat line -- the `\\A` substitution had nothing left to
    match. **Caught by reading the code back, not by a render, because the output
    looked entirely plausible.** ⚑ *A helper that normalises its input silently
    defeats any caller encoding meaning in the characters it normalises.* Multi-line
    content is built as SEPARATE calls joined by an escaped line feed -- see below.
    """
    s = " ".join(str(text or "").split())
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def page_css(page, logo_url: str, site: str, period: str) -> str:
    """The `@page` rule for THIS page, plus the rules it justifies. `""` when off.

    Takes the letterhead URL, site name and period from `buildstamp.py` rather than
    re-deriving them: that module resolves the logo through the image index and builds
    the season string ONCE at `on_config`, so a second derivation here would be a
    second claimant on facts that already have one.

    ⭐ THE LAYOUT MIRRORS THE SCREEN, which is why it needed no design pass: `revised`
    has held the left of the screen footer since 2026-08-07 and the ownership tag the
    right since 2026-08-30. The page number takes the centre because it is the one
    fact belonging to the SHEET rather than to the document.

    ✅ `counter(pages)` gives the TOTAL, and that is the safety argument for having it
    rather than a bare number: **a stapled packet found on a desk announces that it is
    incomplete.**

    ⚠️ THE FOOTER IS THREE SEPARATE BOXES, which is why it does not break the
    two-facts-on-a-line rule `buildstamp.py` enforces. That rule governs ONE line;
    left, centre and right each carry one fact.

    🔴 EVERY VALUE IS OPTIONAL AND EACH BOX IS OMITTED RATHER THAN EMITTED EMPTY. A
    margin box whose `content` computes to `none` is not generated at all, so an
    omitted box costs nothing -- an emitted empty string still reserves it.

    ⚠️ AND IT RETURNS `""` WHEN THE PAGE COUNTER WOULD BE THE ONLY OCCUPANT, so the
    block-axis margin change never lands on a page with no furniture to make room for.
    🔴 It also returns `""` when `enabled()` is False, which is every site today -- and
    because the hide rules ride in the same string, an empty return means the in-flow
    letterhead and footer print exactly as they did before this feature existed.
    """
    if not enabled():
        return ""

    boxes = []

    if logo_url:
        # 🚩 UNVERIFIED IN BOTH ENGINES. WeasyPrint 69 renders nothing for this (proven
        # against a working control); Chrome 131+ documents support and Michael's
        # Chrome painted no box at all on 08-30. § WHY IT IS OFF.
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
        # emitter reformats the value.
        boxes.append("@bottom-left{content:" + css_string("Revised " + revised) + "}")

    boxes.append('@bottom-center{content:"Page " counter(page) " of " counter(pages)}')

    owner = state.INSTANCE.get("owner") or {}
    name = owner if isinstance(owner, str) else (owner.get("name") or "")
    email = "" if isinstance(owner, str) else (owner.get("email") or "")
    if str(name).strip():
        # 🔴 TWO SEPARATE CALLS, NOT ONE JOINED STRING -- the newline bug's fix rather
        # than a style choice. `css_string` collapses whitespace, so a `\n` handed to
        # it vanishes before any substitution sees it. An escaped line feed BETWEEN
        # two literals cannot be normalised away. ⚠️ `white-space: pre` is what makes
        # the `\A` a break rather than a space.
        content = css_string("Posted by " + str(name))
        if str(email).strip():
            content += ' "\\A " ' + css_string(email)
        boxes.append("@bottom-right{content:" + content + ";white-space:pre}")

    if len(boxes) <= 1:
        return ""

    return (
        '<style class="' + STYLE_CLASS + '">@page{margin-top:' + BAND
        + ";margin-bottom:" + BAND + ";"
        + "".join(boxes)
        + "}"
        + _HIDE_INFLOW
        + "</style>"
    )
