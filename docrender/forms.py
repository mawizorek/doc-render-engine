"""The `forms:` registry -- an embedded ClickUp form, named once in frontmatter.

    forms:
      completion:
        src: https://forms.clickup.com/36074068/f/...?Program_ID=ITPSAFE-1225
        text: General Safety completion form
        collapsed: false     # optional; see THE FOLD -- three states, one key
        reload: false        # optional; the Reload button is ON by default

    !!! form "completion"

🔴 **THE ARGUMENTS LIVE IN `docrender/forms-dl.md`.** This file reached 24,664 B
against a 22,528 B read ceiling on 2026-08-30 while the reload button's reasoning
was being written into it, so the accumulated arguments moved to the sibling.
The steps and the warnings stay here; **why a step exists at all is one file
over.** Same standard `buildstamp-dl.md` set. Decision history: the
doc-render-engine Decision Log.

Michael, 2026-08-19: *"can i embed an actual clickup form as content in the
bottom of these pages... so that users dont have to leave the page"* and, on
where it is declared: *"love that i can define in frontmatter, well outside of
the actual body content."*

🚫 THE CONTENT REPO NEVER HOLDS THE IFRAME. An `<iframe>` and a CDN `<script>`
are machinery, and machinery is the one thing the content tree may not contain.
The page NAMES a form; the engine builds the element. Exactly the split `data:`
slots and the `links:` registry already use, and the reason the body directive
is `!!! form` rather than pasted HTML.

⭐ THIS MODULE ALSO DRIVES `docrender/views.py` (the `views:` registry). It has no
hook of its own: `on_page_markdown` below calls it, and it imports `_esc` and
`_dead` from here rather than re-declaring them. 🔴 The full argument for one hook
and two files -- and the measurement that killed the fold -- lives in THE
DELEGATION in `views.py`, not here.

=============================================================================
⭐ THE FOLD -- THREE STATES, ONE KEY (2026-08-30)
=============================================================================
> Michael: *"although I said the rehearsal report should be expanded when the
> form opens, it is now permanently open with no option to collapse it. How do I
> set it to default as expanded but still allow the user to collapse it later?"*

    collapsed: ABSENT   a bare embed. No disclosure at all.
    collapsed: false    `<details open>` -- expanded on arrival, collapsible.
    collapsed: true     `<details>` -- closed on arrival.

⭐ A MISSING KEY AND A KEY SET TO `false` ARE DIFFERENT FACTS, which is the same
distinction `reload:` and `pagefoot._enabled` already turn on. "Not collapsed"
is a claim about a fold; **saying nothing is not a claim at all.** So `false`
asks for a fold that starts open, and silence asks for no fold.

✅ BACKWARDS COMPATIBLE WHERE IT MATTERS: every slot that OMITS the key renders
byte for byte what it rendered before. ⚠️ A slot that explicitly declares
`collapsed: false` GAINS a disclosure -- intended for the page that prompted
this, and `forms-dl.md` names the other live page it reaches.

🚫 NOT A SECOND KEY. `collapsible:` beside `collapsed:` would be two booleans
with four states, one of them unsatisfiable -- the shape `nav: hidden` +
`status: unlisted` already had to be reported as a contradiction.

=============================================================================
🔴 THE RELOAD BUTTON (2026-08-30) -- MECHANISM ONLY; ARGUMENT IN `forms-dl.md`
=============================================================================
🔴 `cloneNode` + `replaceWith`, NEVER `iframe.src = src`. Assigning `src`
NAVIGATES the existing browsing context and pushes a session-history entry, so
after three reloads the reader's Back button walks iframe states instead of
leaving the page. A fresh node is an initial load and pushes nothing. Verified by
executing the handler against a DOM model: zero history entries, one fresh load,
the other form on the page untouched.

🔴 IT DISCARDS WHATEVER WAS TYPED, WITH NO CONFIRMATION, AND THAT IS THE ASK --
refused on 08-29 on data-loss grounds and released by Michael the next morning.
**The label is the safety mechanism.**

🚫 NOT ON A `views:` EMBED. A shared view is read-only furniture with nothing
typed into it, so a reload control there answers a question nobody asked.

=============================================================================
🔴 A COLLAPSED EMBED USED TO PRINT AS A CALLOUT. FIXED 2026-08-30.
=============================================================================
> Michael, from a print preview: *"the rehearsal report is not in a collapsed
> iframe, so it prints correctly, but because the rehearsal note form is
> collapsed, it renders differently at print and breaks the system."*

Material `@extend`s `.admonition` onto EVERY `<details>`, so `print-callout.css`
gave the disclosure a 2pt coloured band and a 0.85em indent that its uncollapsed
sibling never got. ⚑ **Two embeds declared the same way, differing in one
SCREEN-only key, printed as two different KINDS of object.** `flow.css` fixed
exactly this for `.dr-flows__others` and nobody pointed the same fix at the form.

⚠️ THE SUMMARY IS HIDDEN ON PAPER, AND THAT IS PARITY RATHER THAN LOSS: it is a
control, and its text is the slot's own `text:`, which the fallback link already
carries. Both embeds now print as one line naming the form. `forms-dl.md` carries
the one edge case where a string genuinely goes.

⚠️ AND THE RULES ARE INLINE, NOT IN `flow.css`, WHICH OWNS `.dr-form*`. That file
is **23,485 B, already 957 B PAST the read ceiling** before this change -- it grew
by 2,365 B the same morning when the `.dr-view*` rules landed. 🚩 It needs the
split its own header prescribes; these rules move there when it happens.

=============================================================================
🔴 A BROKEN SLOT RENDERS A MARKER, NOT NOTHING (fixed 2026-08-30)
=============================================================================
`_html` used to return `""` for an unknown slot and `swap` returns `""` on falsy,
so a typo'd directive line VANISHED -- no marker, no gap, no clue, on a page that
already showed one working form. Its two siblings (`qr.py`, `links.py`) already
rendered the struck-through `docrender-dead` span.

⭐ THE MESSAGE IS THE ONE THAT WAS ALREADY GOING TO THE BUILD REPORT, on a second
SURFACE rather than as a second claimant. Full account: `forms-dl.md`.

=============================================================================
🔴 `height="100%"` COLLAPSES TO NOTHING WITHOUT THEIR SCRIPT
=============================================================================
The sharp edge in the embed code ClickUp hands you. `clickup-dynamic-height`
plus `forms-embed/v1.js` is what gives the frame a real height; an iframe with
`height="100%"` and no sized parent is ~0px tall. So if that CDN is slow, blocked
by an extension, or the asset ever moves, the form is not BROKEN, it is
INVISIBLE -- a blank gap on a compliance page, with nothing in the build report,
because an external script's runtime behaviour cannot be observed at build time.

`min-height` on the frame is the floor: a script failure degrades to a
scrollable form rather than a hole.

⚠️ AND THAT FLOOR IS THE ONLY REASON A RE-BINDING FAILURE IS SURVIVABLE. Anything
that replaces or re-creates this element at runtime -- a refresh control, for
instance -- orphans the CDN script's listener, so the frame falls back to exactly
this value instead of collapsing. Stated here because the floor reads like
defensive tidiness and is load-bearing for a feature nobody has built yet.

⭐ THAT FEATURE ARRIVED ON 2026-08-30 AND THE PARAGRAPH ABOVE IS UNCHANGED. It
named *"a refresh control, for instance"* before one existed, and the floor is now
its second consumer. **A guard written for a CDN outage is what made a later
feature safe** -- kept visible because the usual version of this note is written
after the damage.

🔴 AND THE WHOLE PROBLEM IS FORM-ONLY -- read this before copying the machinery.
ClickUp's embed code for a shared VIEW ships `clickup-embed` alone with a literal
`height="700px"`: no dynamic-height class, no helper script, nothing to fail.
`views.py` states the consequence.

⚠️ AND THE FALLBACK LINK IS ALWAYS RENDERED, not only for print. An iframe
prints as a blank rectangle and this engine has a print identity spec, so a
printed program packet would otherwise carry a hole where the completion form
belongs. On screen the same link is the answer to "the form did not load."

=============================================================================
🔴 THE PREFILL PARAM IS THE RECORD
=============================================================================
`?Program_ID=` on the src is what makes a submission attributable to a program.
It was already in uritp-safety's `links:` block before this key existed and moves
onto the src unchanged. A form embedded WITHOUT it collects rows nobody can match
to a program -- a compliance failure that looks like a working page, so it is
reported.

⚠️ UNVERIFIABLE AT BUILD TIME, the same reduction `urllinks.py` states at the top
of its own file. The host and the scheme are checked; nothing here can prove the
form is active, public, or still exists.
"""

from __future__ import annotations

import html
import re

from . import state
from .util import sub_outside_code

#: `!!! form "slot"` alone on its line. Deliberately the same shape as the
#: `!!! data "slot"` directive datatable.py owns, so the body vocabulary stays
#: one pattern rather than two spellings of one idea.
_FORM = re.compile(r'(?m)^[ \t]*!!![ \t]+form[ \t]+"([^"\n]+)"[ \t]*$')

#: The one host an embedded form may come from. An allow-list rather than a
#: scheme check: this element executes a third-party script in the reader's
#: browser on a page that carries a compliance instruction, so "any https URL"
#: is not a good enough answer.
#:
#: ⚠️ A LITERAL BECAUSE A FORM HAS ONE HOME. A shared VIEW does not, so
#: `views.py` reads its allow-list from the instance config. Do not unify these.
_FORM_HOST = "https://forms.clickup.com/"

#: ClickUp's own embed helper. What `clickup-dynamic-height` needs.
_FORM_SCRIPT = "https://app-cdn.clickup.com/assets/js/forms-embed/v1.js"

#: The floor that keeps a script failure from rendering an invisible form -- and,
#: since 2026-08-30, what keeps a RELOADED frame from collapsing. One value, two
#: consumers, and the second was named in the docstring before it was built.
_FORM_MIN_HEIGHT = "40rem"

_DEFAULT_LABEL = "Complete this program"

#: What a failed embed says on the PAGE. Deliberately one word: `links.py` and
#: `qr.py` both render a short label with the diagnosis in the `title`, so a
#: reader meets one consistent shape for every broken reference on the site.
_DEAD_LABEL = "Form"

#: 🔴 THE HONEST WORD IS THE SAFETY MECHANISM. This control throws away whatever
#: is typed in the frame, with no confirmation, BY REQUEST -- so the label must not
#: be coy about it. See `forms-dl.md` on why there is no confirm dialog.
_RESET_LABEL = "Reload form"

#: ONE DELEGATED LISTENER PER PAGE, so a two-form page binds once.
#:
#: 🔴 `cloneNode` + `replaceWith`, NEVER `f.src = src` -- see the docstring: that
#: pushes a session-history entry and hijacks the Back button.
#: ⚠️ `closest` IS GUARDED because `e.target` can be a node without it; a handler
#: that throws on one stray click is worse than one that does nothing.
_RESET_JS = (
    "<script>document.addEventListener('click',function(e){"
    "var b=e.target&&e.target.closest?e.target.closest('.dr-form__reset'):null;"
    "if(!b)return;"
    "var w=b.closest('.dr-form');var o=w&&w.querySelector('iframe');if(!o)return;"
    "var f=o.cloneNode(false);f.src=o.getAttribute('src');o.replaceWith(f);"
    "});</script>"
)

#: Inline, once per page, because `assets/flow.css` -- which owns `.dr-form*` -- is
#: **23,485 B and already past the 22,528 B read ceiling**. `forms-dl.md` carries
#: the measurement and the split this file is waiting on.
#:
#: ⚠️ THE PRINT HALF IS THE FIX FOR MICHAEL'S 08-30 PREVIEW, not decoration. The
#: first two rules strip the callout costume Material puts on every `<details>`;
#: the third hides the summary, which is a control whose text the fallback link
#: already carries. (0,2,0)/(0,2,1) beat print-callout's (0,1,1) outright rather
#: than on load order.
#:
#: ⚠️ AND THE BUTTON GOES TOO. A button on paper is a lie -- the same pen test
#: `print.css` applies to its whole chrome-off list.
_RESET_CSS = (
    "<style>.dr-form__tools{margin:.6rem 0 0}"
    ".dr-form__reset{display:inline-block;padding:.3rem .7rem;"
    "border:1px solid var(--dr-border,var(--md-default-fg-color--lighter));"
    "border-radius:.25rem;background:transparent;"
    "color:var(--md-default-fg-color--light);font:inherit;font-size:.72rem;"
    "font-weight:600;cursor:pointer}"
    ".dr-form__reset:hover{border-color:var(--dr-accent,var(--md-typeset-a-color));"
    "color:var(--dr-accent,var(--md-typeset-a-color))}"
    "@media print{.dr-form__tools{display:none}"
    ".dr-form__open,.md-typeset .dr-form__open{margin:0;padding:0;"
    "border:0 !important;background:transparent}"
    ".dr-form__open>summary,.md-typeset .dr-form__open>summary{display:none}}"
    "</style>"
)


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _dead(reason: str, label: str = _DEAD_LABEL) -> str:
    """The same struck-through span `links.py` and `qr.py` render.

    🚫 DELIBERATELY NOT AN ANCHOR. A form that failed to resolve must not offer a
    control -- the dead-control rule this engine applies to `edit_links: false`,
    the retired PR number and the printed link policy. The `title` carries the
    diagnosis; there is nothing to click.

    ✅ AND IT PRINTS WITHOUT A PRINT RULE. `base.css` declares the `--dr-dead`
    dotted underline unscoped to any medium; `print.css` has a whole block
    arguing against re-declaring it. So a printed sheet shows the failure too,
    which matters on a compliance page more than on screen.

    ⭐ `label` IS A PARAMETER SO `views.py` SHARES THIS SPAN. Two directives with
    two copies of a failure vocabulary is how they start disagreeing about what
    broken looks like. Callers pass their own noun; nobody re-implements it.
    """
    return (
        '<span class="docrender-dead" title="'
        + html.escape(reason, quote=True) + '">'
        + html.escape(label) + "</span>"
    )


def slot_anchor(slot: str) -> str:
    """The id a flow's last step links to, to open a collapsed form.

    ⭐ PUBLIC, AND program.py IS THE CALLER. One function owns the spelling of
    this id, because a link and its target computed in two places is the defect
    that produces a Next button landing on nothing -- and it would land
    SILENTLY, since a fragment that matches no element is not an error.

    ✅ STILL CORRECT FOR AN ALREADY-OPEN FOLD. A fragment pointing inside a closed
    `<details>` expands it; pointing inside an open one just scrolls. So the flow's
    last step lands the same way whichever state the slot declares.
    """
    return "dr-form-" + re.sub(r"[^A-Za-z0-9_-]+", "-", str(slot)).strip("-")


def first_slot(meta: dict) -> str:
    """The first form slot a page declares, or "".

    Used by the flow strip to point the end of a program at its own form. FIRST
    rather than "the one named completion": a slot name is the author's
    vocabulary and hardcoding one here would be the engine inventing a magic
    word that works on some pages and silently does nothing on others.
    """
    block = (meta or {}).get("forms")
    if not isinstance(block, dict):
        return ""
    for name in block:
        return str(name)
    return ""


def _declared(src) -> list:
    """Every slot name this page declares, sorted. For the diagnosis only.

    ⭐ NAMING WHAT *IS* DECLARED IS MOST OF THE VALUE OF THE MESSAGE, and it is
    what turns a typo from a hunt into a glance. `sheet.apply_options` sets the
    precedent -- it prints the sheet's real header beside a bad `hide:` -- and
    `datatable.py` does the same for an undeclared data slot.
    """
    block = (state.BY_SRC.get(src, {}) or {}).get("forms")
    return sorted(str(k) for k in block) if isinstance(block, dict) else []


def _entry(src, slot):
    """One entry out of a page's `forms:` map, or None.

    Returns `(src, text, fold, reloadable)` where `fold` is one of `""` (no
    disclosure), `"open"` or `"closed"`. See THE FOLD in the docstring.

    ⭐ BOTH THREE-STATE TESTS TURN ON PRESENCE, NOT TRUTHINESS. `"collapsed" in
    raw` separates "no fold" from "a fold that starts open", and `reload` reads
    `is not False` so an omitted key still gets the button. **A missing key and a
    key set to false are different facts** -- `pagefoot._enabled` reads
    `edit_links` the same way, for the same reason.
    """
    block = (state.BY_SRC.get(src, {}) or {}).get("forms")
    if not isinstance(block, dict):
        return None
    raw = block.get(slot)
    if raw is None:
        return None
    if isinstance(raw, str):
        return (raw.strip(), "", "", True)
    if isinstance(raw, dict):
        fold = ""
        if "collapsed" in raw:
            fold = "closed" if raw.get("collapsed") is True else "open"
        return (
            str(raw.get("src", "")).strip(),
            str(raw.get("text", "")).strip(),
            fold,
            raw.get("reload") is not False,
        )
    return ("", "", "", True)


def _html(src, slot) -> str:
    entry = _entry(src, slot)
    if entry is None:
        known = _declared(src)
        state.note(
            "dead_links",
            src + ': `!!! form "' + slot + '"` names a slot that is not in this '
            "page's `forms:` block. Declared here: "
            + (", ".join(known) or "nothing") + ". Nothing was embedded.",
        )
        # 🔴 A MARKER, NOT "". Returning empty deleted the line and made a typo
        # indistinguishable from a page that never asked for a form.
        return _dead(
            "form slot not declared on this page: " + slot
            + ". Declared here: " + (", ".join(known) or "nothing") + "."
        )

    url, text, fold, reloadable = entry
    if not url.startswith(_FORM_HOST):
        state.note(
            "dead_links",
            src + ": `forms: " + slot + "` must be a " + _FORM_HOST
            + " address (found '" + url + "'). NOT embedded -- this element runs "
            "a third-party script in the reader's browser, so the host is an "
            "allow-list rather than a scheme check.",
        )
        # ⚠️ ALSO VISIBLE, and this is the case where it matters most: the slot
        # EXISTS, so an author reading the page has every reason to believe the
        # embed is working and merely slow.
        return _dead(
            "form slot '" + slot + "' is not a " + _FORM_HOST + " address, so it "
            "was not embedded. This element runs a third-party script, so the "
            "host is an allow-list."
        )

    if "Program_ID=" not in url:
        state.note(
            "notes",
            src + ": `forms: " + slot + "` carries no `Program_ID=` parameter. "
            "It will embed and submit, and the submissions will not be "
            "attributable to this program -- a compliance gap that looks like a "
            "working page.",
        )

    label = text or "Open this form in a new tab"
    frame = (
        '<iframe class="clickup-embed clickup-dynamic-height" src="' + _esc(url)
        + '" onwheel="" width="100%" height="100%" title="' + _esc(label)
        + '" style="background: transparent; border: 1px solid #ccc; '
        "min-height: " + _FORM_MIN_HEIGHT + ';"></iframe>'
    )
    # ⚠️ A REAL `<button type="button">`, never a styled anchor: it acts on THIS
    # page rather than going anywhere, so it must be announced as a button and be
    # keyboard-reachable without a `tabindex` bolted on.
    tools = (
        '<p class="dr-form__tools"><button type="button" class="dr-form__reset">'
        + _esc(_RESET_LABEL) + "</button></p>"
    ) if reloadable else ""
    fallback = (
        '<p class="dr-form__fallback"><a href="' + _esc(url) + '">'
        + _esc(label) + "</a></p>"
    )

    if not fold:
        return (
            '<div class="dr-form">' + frame + tools + fallback + "</div>"
        )

    # 🔴 THE ANCHOR SITS ON THE <summary>, NOT ON THE <details>. A fragment must
    # target something INSIDE the disclosure for the auto-expand behaviour to
    # apply; pointing it at the <details> itself is the version of this that
    # scrolls correctly and stays shut.
    #
    # ⭐ `open` IS AN ATTRIBUTE ON THE SAME ELEMENT, so "expanded" and "closed" are
    # ONE markup shape with one character of difference -- not two branches. That
    # is what keeps the print rules, the anchor and the styles from needing to know
    # which state a slot asked for.
    return (
        '<div class="dr-form">'
        '<details class="dr-form__open"' + (" open" if fold == "open" else "")
        + '><summary id="' + _esc(slot_anchor(slot)) + '">'
        + _esc(text or _DEFAULT_LABEL) + "</summary>"
        + frame + tools + fallback
        + "</details></div>"
    )


def on_page_markdown(markdown, page, config, files):
    """Replace each `!!! form "slot"` with the embed, and load the helper once.

    ⚠️ `sub_outside_code` IS NOT OPTIONAL. The authoring page that documents this
    directive contains the directive, and util's own docstring records the first
    time that bit this engine: the page teaching `[Main Stage](@main-stage)`
    shipped with the resolved URL inside its own code fence.

    ⭐ THE HELPER SCRIPT IS APPENDED ONCE PER PAGE, NOT ONCE PER FORM. Two forms
    on a page would otherwise fetch and execute the same CDN asset twice.

    🔴 THREE COUNTERS, BECAUSE THESE ARE THREE DIFFERENT FACTS AND COLLAPSING ANY
    TWO OF THEM IS WHAT CAUSED THE LAST BUG: *a directive matched* · *a frame
    exists* · *a button exists*. The CDN script is gated on the second, because a
    page whose only form is broken has no frame for it to size and the request
    would be pure cost. The style/listener block is gated on the third.

    ⚠️ AND THE PRINT PARITY RULES RIDE IN THAT SAME BLOCK, which means a page whose
    every form sets `reload: false` ALSO loses them. Acceptable and stated: the
    rules only matter to a `.dr-form__open`, and a page with no button is a page
    nobody has asked to interact with. 🚩 If that combination ever ships, the block
    splits in two.

    ⭐ THE `views:` PASS RUNS HERE TOO, LAST, because one hook is what keeps this
    feature out of `mkdocs.yml`. 🔴 The import is local to this function ON PURPOSE
    -- `views.py` imports from here at its module top, and top-level imports in
    both directions would be a cycle. ⚠️ Order is arbitrary, not load-bearing:
    the patterns are disjoint and neither pass reads the other's output.
    """
    if "!!!" not in markdown:
        return markdown

    src = getattr(page.file, "src_uri", "")
    embedded = []
    reloadable = []

    def swap(match):
        html_out = _html(src, match.group(1).strip())
        if not html_out:
            return ""
        if "<iframe" in html_out:
            embedded.append(1)
        if "dr-form__reset" in html_out:
            reloadable.append(1)
        return "\n\n" + html_out + "\n\n"

    out = sub_outside_code(_FORM, swap, markdown)
    if embedded:
        out += '\n\n<script async src="' + _FORM_SCRIPT + '"></script>\n'
    if reloadable:
        out += "\n" + _RESET_CSS + "\n" + _RESET_JS + "\n"

    from . import views

    return views.on_page_markdown(out, page, config, files)
