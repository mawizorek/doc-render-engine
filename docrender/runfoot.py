"""THE RUNNING FURNITURE -- a page header and footer on every printed sheet.

🔴 **OPT IN PER SITE WITH `print: running: true`.** `uritp-safety` declares it.
Margin boxes need Chrome 131+ / Safari 18.2+; below that the @page rules are
parsed and discarded in silence, but the in-flow letterhead stays because the
hide rules were removed (see _HIDE_INFLOW below).

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
⚠️ THE HIDE RULES ARE GONE, AND THAT IS THE FIX (2026-10-21, Dexter)
=============================================================================
`_HIDE_INFLOW` used to emit `@media print` rules hiding the in-flow letterhead,
revision line and ownership tag. The intent was that the @page margin boxes
replace them. The problem: `@media print` fires in EVERY browser, while @page
margin boxes only paint in Chrome 131+ / Safari 18.2+. On any browser that
ignores @page, the hide rules stripped the letterhead with nothing replacing it.

Tested and failed: 2026-08-30, 2026-10-21 (twice).

The previous fix ("emit the hide rules in the SAME <style> block") was wrong:
the <style> block IS emitted whenever enabled() returns True. @media print rules
inside it fire regardless of whether @page margin boxes paint. The structural
guarantee only works when the entire <style> element is absent.

✅ FIX: the hide rules are removed entirely. On supporting browsers the user sees
DUPLICATION (margin box header + in-flow header). The print panel's existing
"Hide Header" / "Hide Footer" toggles (printfurn.js) let the user suppress the
in-flow copies. On non-supporting browsers, the in-flow letterhead stays.

Matches this file's own principle: *"Prefer a failure a reader will notice over
one that looks deliberate."* Duplication is noticeable; absence is not.

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

=============================================================================
🔴 THE BLOCK AXIS IS OURS. THE INLINE AXIS IS NOT.
=============================================================================
`print.css` sets `@page { margin: 12mm }` and calls the inline half *"the
load-bearing half"*: the printed column is a container query context and the data
table flips to list mode under 640px. The block axis it calls *"free to change."*
`page_css` sets ONLY `margin-top`/`margin-bottom`, because a margin box's height IS
the page margin. 🚫 Never add left or right here: it silently converts every data
table on the sheet into a key/value stack, at print time, with no report.
"""

from __future__ import annotations

from . import state

#: The block-axis room the margin boxes need.
BAND = "16mm"

#: 🔴 THE CLASS ON THE `<style>` ELEMENT, LOAD-BEARING RATHER THAN COSMETIC. A
#: `<style>` needs no styling, so it shipped unclassed and was **invisible to
#: `packet._cut`**, the class-based transform that strips per-section furniture --
#: which let N members' `@page` rules survive into one packet. Named as a constant so
#: the emitter and `packet._STRIP` cannot drift apart silently; `packet.py` imports it
#: rather than retyping the string.
STYLE_CLASS = "dr-runfoot"

#: 🪦 RETIRED 2026-10-21 (Dexter). Was `@media print` rules hiding the in-flow
#: letterhead, owner tag and revised line. Removed because `@media print` fires in
#: every browser while `@page` margin boxes only paint in Chrome 131+. On non-
#: supporting browsers, these rules stripped the letterhead with nothing replacing it.
#: Tested and failed 2026-08-30 and 2026-10-21.
#:
#: The user now controls duplication via the print panel's "Hide Header" / "Hide
#: Footer" toggles (printfurn.js). The constant is kept as an empty string so
#: `packet._STRIP` and any other consumer that references it does not break.
_HIDE_INFLOW = ""


def enabled() -> bool:
    """Does this site opt in to running headers and footers? DEFAULT: NO.

    `print: running: true` in `instances/<slug>/site.yml` turns it on for one site.
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
    splits on newlines too. Multi-line content is built as SEPARATE calls joined by
    an escaped line feed -- see `page_css` below.
    """
    s = " ".join(str(text or "").split())
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def page_css(page, logo_url: str, site: str, period: str) -> str:
    """The `@page` rule for THIS page. `""` when off.

    Takes the letterhead URL, site name and period from `buildstamp.py` rather than
    re-deriving them.

    ✅ `counter(pages)` gives the TOTAL, and that is the safety argument for having it
    rather than a bare number: **a stapled packet found on a desk announces that it is
    incomplete.**

    🔴 EVERY VALUE IS OPTIONAL AND EACH BOX IS OMITTED RATHER THAN EMITTED EMPTY.

    ⚠️ Returns `""` when the page counter would be the only occupant, and when
    `enabled()` is False.

    🪦 NO LONGER EMITS HIDE RULES (2026-10-21). The in-flow letterhead stays on
    paper. On browsers that paint the margin boxes, the user sees both and can use
    the print panel's Hide Header/Footer toggles to suppress the in-flow copies.
    """
    if not enabled():
        return ""

    boxes = []

    if logo_url:
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
        boxes.append("@bottom-left{content:" + css_string("Revised " + revised) + "}")

    boxes.append('@bottom-center{content:"Page " counter(page) " of " counter(pages)}')

    owner = state.INSTANCE.get("owner") or {}
    name = owner if isinstance(owner, str) else (owner.get("name") or "")
    email = "" if isinstance(owner, str) else (owner.get("email") or "")
    if str(name).strip():
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
