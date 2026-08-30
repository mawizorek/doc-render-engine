"""The `forms:` registry -- an embedded ClickUp form, named once in frontmatter.

    forms:
      completion:
        src: https://forms.clickup.com/36074068/f/...?Program_ID=ITPSAFE-1225
        text: General Safety completion form
        collapsed: false     # optional; THREE STATES -- see THE FOLD
        height: 40rem        # optional; the SCROLL WINDOW, not the form
        reload: false        # optional; the Reload button is ON by default

    !!! form "completion"
    !!! form "completion" align=center

🔴 **EVERY ARGUMENT LIVES IN `docrender/forms-dl.md`.** This file has crossed the
22,528 B read ceiling FOUR times while reasoning was written into it. **Warnings
stay here; why a warning exists is one file over.** ⚠️ Every overrun was predicted
by a size ESTIMATED rather than measured. Write the section in the sibling first.

🚫 THE CONTENT REPO NEVER HOLDS THE IFRAME. An `<iframe>` and a CDN `<script>`
are machinery, and machinery is the one thing the content tree may not contain.
The page NAMES a form; the engine builds the element -- the same split `data:`
slots and the `links:` registry use.

⭐ THIS MODULE ALSO DRIVES `docrender/views.py` (the `views:` registry), which has
no hook of its own: `on_page_markdown` calls it, and it imports `_esc` and `_dead`
from here. Argument: THE DELEGATION in `views.py`.

=============================================================================
⭐ THE FOLD -- THREE STATES, ONE KEY
=============================================================================
    collapsed: ABSENT   a bare embed, no disclosure at all.
    collapsed: false    `<details open>` -- expanded on arrival, collapsible.
    collapsed: true     `<details>` -- closed on arrival.

⭐ A MISSING KEY AND A KEY SET TO `false` ARE DIFFERENT FACTS. 🚫 Not a second
`collapsible:` key: two booleans give four states and one is unsatisfiable.

=============================================================================
🔴 THE STANDING TRAPS -- warnings only. Arguments: `forms-dl.md`.
=============================================================================
🔴 **THE SCROLL WINDOW IS THE WRAPPER, NEVER THE FRAME.** ClickUp's form app
expects the PARENT to size it, so capping the iframe CLIPS the form instead of
scrolling it. `height:` names the WINDOW. ⚠️ `-webkit-overflow-scrolling: touch`
is load-bearing -- iOS Safari refuses to scroll this exact shape without it, and
these pages are read on an iPad. ⚠️ At the default the window equals
`_FORM_MIN_HEIGHT`, so a CDN failure degrades to a clipped 40rem form: the
pre-existing failure, not a new one.

🔴 **NO FORM IFRAME PRINTS, AND EVERY PRINT `display` RULE MUST BE `!important`.**
`print-flow.css` sets `display: revert !important` on every direct child of a
`<details>`; importance beats specificity, so a plain `display: none` loses and a
folded form printed its whole frame. 🔴 **WeasyPrint CANNOT SEE THIS** -- it
discards `display: revert` as invalid, so the harness passes while Chrome prints
the form. Reproduce with `display: block !important`. ⚠️ The scroll wrapper is
released on paper or a capped window clips the sheet too.

🔴 **THE RELOAD BUTTON REPLACES THE NODE:** `cloneNode` + `replaceWith`, NEVER
`iframe.src = src`, which navigates the browsing context and pushes a
session-history entry -- after three reloads Back walks iframe states. 🔴 It
discards whatever was typed with no confirmation, BY REQUEST: **the label is the
safety mechanism.** 🚫 Not on a `views:` embed. ⚠️ It orphans the CDN listener, so
the reloaded frame falls back to `_FORM_MIN_HEIGHT`.

🔴 `height="100%"` WITH NO SIZED PARENT IS ~0px TALL, so a slow, blocked or moved
CDN asset makes the form INVISIBLE rather than broken -- a blank gap with nothing
in the build report. 🔴 FORM-ONLY: a shared VIEW ships a literal height, no script.

🔴 A BROKEN SLOT RENDERS A MARKER, NOT NOTHING. `_html` used to return `""` and
`swap` returns `""` on falsy, so a typo'd directive line VANISHED.

🔴 `?Program_ID=` IS THE RECORD. Without it, submissions match no program -- a
compliance failure that looks like a working page, so it is reported. ⚠️ Host and
scheme are checked; nothing here proves the form is active or still exists.

⚠️ THE FALLBACK LINK IS ALWAYS RENDERED -- an iframe prints blank, and on screen it
answers "the form did not load."

🔴 `align=` MOVES THE FURNITURE, NOT THE FRAME: the iframe is `width: 100%` and has
no slack to be moved within, so what aligns is the summary label, the Reload
button and the fallback link.
"""

from __future__ import annotations

import html
import re

from . import state
from .util import directive_options, sub_outside_code

#: `!!! form "slot"` plus optional trailing `key=value` options.
#:
#: 🔴 THE TRAILING GROUP IS A BUG FIX AND THE BUG WAS SILENT. This anchored
#: `"[ \t]*$` straight after the closing quote, so `!!! form "x" align=center` did
#: not match AT ALL -- the directive stayed on the page as literal text with
#: NOTHING in the build report, because nothing had matched to report on. Same
#: shape as `qr._QR`, which has accepted options since 2026-08-21.
_FORM = re.compile(
    r'(?m)^[ \t]*!!![ \t]+form[ \t]+"([^"\n]+)"(?P<opts>[^\n]*)$'
)

#: 🚫 NO MEDIA VOCABULARY. `qr.py` has `display=`/`print=` because a code can
#: legitimately exist in one medium only; a form embed always appears on screen and
#: never on paper. `align` is the only option, and `util` validates it.
_LEGAL_OPTS: tuple = ()

#: The one host an embedded form may come from. An allow-list rather than a scheme
#: check: this element executes a third-party script in the reader's browser on a
#: page that carries a compliance instruction.
#:
#: ⚠️ A LITERAL BECAUSE A FORM HAS ONE HOME. A shared VIEW does not, so `views.py`
#: reads its allow-list from the instance config. Do not unify these.
_FORM_HOST = "https://forms.clickup.com/"

#: ClickUp's own embed helper. What `clickup-dynamic-height` needs.
_FORM_SCRIPT = "https://app-cdn.clickup.com/assets/js/forms-embed/v1.js"

#: The floor that keeps a script failure from rendering an INVISIBLE form, and
#: what keeps a RELOADED frame from collapsing. One value, two consumers.
_FORM_MIN_HEIGHT = "40rem"

#: The default SCROLL WINDOW. Equal to the floor above by design, so the default
#: LOOK is unchanged and only the overflow behaviour is new.
_FORM_WINDOW = "40rem"

#: A CSS length, loosely. Enough to catch a bare number or a unit typo before it
#: reaches a style attribute, not a full CSS parser. Same shape as `views._LENGTH`
#: -- duplicated because a cross-import for one regex is the worse dependency.
_LENGTH = re.compile(r"^\d+(\.\d+)?(px|rem|em|vh|%)$")

_DEFAULT_LABEL = "Complete this program"

#: What a failed embed says on the PAGE. One word, matching `links.py` and
#: `qr.py`, so a reader meets one shape for every broken reference on the site.
_DEAD_LABEL = "Form"

#: 🔴 THE HONEST WORD IS THE SAFETY MECHANISM. This control throws away whatever is
#: typed, with no confirmation, BY REQUEST. `forms-dl.md` on why no confirm dialog.
_RESET_LABEL = "Reload form"

#: ONE DELEGATED LISTENER PER PAGE, so a two-form page binds once.
#:
#: 🔴 `cloneNode` + `replaceWith`, NEVER `f.src = src` -- that pushes a
#: session-history entry and hijacks the Back button.
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
#: past the read ceiling and cannot be rewritten safely. 🚩 These move there after
#: the split its own header prescribes.
#:
#: 🔴 EVERY PRINT `display` DECLARATION IS `!important` ON PURPOSE -- see THE
#: STANDING TRAPS. 🚫 DO NOT tidy these back to plain `display: none`.
#:
#: ⚠️ `overflow` IS `auto` BOTH WAYS, never `hidden`: a form wider than the column
#: is a layout problem, and hiding it would silently cut a field label off.
_RESET_CSS = (
    "<style>.dr-form__tools{margin:.6rem 0 0}"
    ".dr-form__scroll{overflow:auto;-webkit-overflow-scrolling:touch;"
    "overscroll-behavior:contain}"
    ".dr-form__reset{display:inline-block;padding:.3rem .7rem;"
    "border:1px solid var(--dr-border,var(--md-default-fg-color--lighter));"
    "border-radius:.25rem;background:transparent;"
    "color:var(--md-default-fg-color--light);font:inherit;font-size:.72rem;"
    "font-weight:600;cursor:pointer}"
    ".dr-form__reset:hover{border-color:var(--dr-accent,var(--md-typeset-a-color));"
    "color:var(--dr-accent,var(--md-typeset-a-color))}"
    "@media print{"
    ".dr-form__scroll,.md-typeset .dr-form__scroll"
    "{max-height:none !important;overflow:visible !important}"
    ".dr-form iframe,.md-typeset .dr-form iframe,"
    ".dr-form__open>iframe,.md-typeset .dr-form__open>iframe"
    "{display:none !important}"
    ".dr-form__tools,.md-typeset .dr-form__tools,"
    ".dr-form__open>.dr-form__tools,.md-typeset .dr-form__open>.dr-form__tools"
    "{display:none !important}"
    ".dr-form__open,.md-typeset .dr-form__open{margin:0;padding:0;"
    "border:0 !important;background:transparent}"
    ".dr-form__open>summary,.md-typeset .dr-form__open>summary"
    "{display:none !important}"
    "}</style>"
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

    🚫 DELIBERATELY NOT AN ANCHOR -- a form that failed to resolve must not offer a
    control. The `title` carries the diagnosis.

    ✅ AND IT PRINTS WITHOUT A PRINT RULE: `base.css` declares the `--dr-dead`
    dotted underline unscoped to any medium.

    ⭐ `label` IS A PARAMETER SO `views.py` SHARES THIS SPAN. Two copies of a
    failure vocabulary is how they start disagreeing about what broken looks like.
    """
    return (
        '<span class="docrender-dead" title="'
        + html.escape(reason, quote=True) + '">'
        + html.escape(label) + "</span>"
    )


def slot_anchor(slot: str) -> str:
    """The id a flow's last step links to, to open a collapsed form.

    ⭐ PUBLIC, AND program.py IS THE CALLER. One function owns the spelling of this
    id, because a link and its target computed in two places is the defect that
    produces a Next button landing on nothing -- SILENTLY, since a fragment
    matching no element is not an error.

    ✅ STILL CORRECT FOR AN ALREADY-OPEN FOLD: a fragment pointing inside a closed
    `<details>` expands it; inside an open one it just scrolls.
    """
    return "dr-form-" + re.sub(r"[^A-Za-z0-9_-]+", "-", str(slot)).strip("-")


def first_slot(meta: dict) -> str:
    """The first form slot a page declares, or "".

    Used by the flow strip to point the end of a program at its own form. FIRST
    rather than "the one named completion": a slot name is the author's vocabulary
    and hardcoding one here would be the engine inventing a magic word that works
    on some pages and silently does nothing on others.
    """
    block = (meta or {}).get("forms")
    if not isinstance(block, dict):
        return ""
    for name in block:
        return str(name)
    return ""


def _declared(src) -> list:
    """Every slot name this page declares, sorted. For the diagnosis only.

    ⭐ NAMING WHAT *IS* DECLARED IS MOST OF THE VALUE OF THE MESSAGE -- it turns a
    typo from a hunt into a glance. `sheet.apply_options` sets the precedent.
    """
    block = (state.BY_SRC.get(src, {}) or {}).get("forms")
    return sorted(str(k) for k in block) if isinstance(block, dict) else []


def _window(src, slot, declared) -> str:
    """The scroll window height: what the page declared, or the default.

    🔴 A BAD VALUE IS REPORTED AND REPLACED, NEVER PASSED THROUGH -- `height: 40`
    with no unit is invalid in a style attribute and would silently restore the
    unbounded frame this key exists to cap. Same ruling as `views._height`.
    """
    if not declared:
        return _FORM_WINDOW
    if _LENGTH.match(declared):
        return declared
    state.note(
        "notes",
        src + ": `forms: " + slot + "` has height '" + declared + "', which is "
        "not a CSS length (try 40rem, 700px, 80vh). Using " + _FORM_WINDOW
        + " instead -- a unitless height would silently un-cap the frame.",
    )
    return _FORM_WINDOW


def _entry(src, slot):
    """One entry out of a page's `forms:` map, or None.

    Returns `(src, text, fold, reloadable, height)` where `fold` is one of `""`
    (no disclosure), `"open"` or `"closed"`. See THE FOLD.

    ⭐ BOTH THREE-STATE TESTS TURN ON PRESENCE, NOT TRUTHINESS. `"collapsed" in
    raw` separates "no fold" from "a fold that starts open", and `reload` reads
    `is not False` so an omitted key still gets the button.
    """
    block = (state.BY_SRC.get(src, {}) or {}).get("forms")
    if not isinstance(block, dict):
        return None
    raw = block.get(slot)
    if raw is None:
        return None
    if isinstance(raw, str):
        return (raw.strip(), "", "", True, "")
    if isinstance(raw, dict):
        fold = ""
        if "collapsed" in raw:
            fold = "closed" if raw.get("collapsed") is True else "open"
        return (
            str(raw.get("src", "")).strip(),
            str(raw.get("text", "")).strip(),
            fold,
            raw.get("reload") is not False,
            str(raw.get("height", "")).strip(),
        )
    return ("", "", "", True, "")


def _html(src, slot, opts=None) -> str:
    opts = opts or {}
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

    url, text, fold, reloadable, raw_height = entry
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
    # 🔴 THE WRAPPER IS THE WINDOW, NOT THE FRAME. Capping the iframe CLIPS the
    # ClickUp form app rather than giving it a scrollbar -- it expects the parent
    # to size it. So the frame stays free to grow and this box does the scrolling.
    window = (
        '<div class="dr-form__scroll" style="max-height: '
        + _esc(_window(src, slot, raw_height)) + ';">' + frame + "</div>"
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

    # ⭐ ALIGNMENT IS A CLASS ON THE WRAPPER and `assets/align.css` owns what it
    # means -- the same seam `qr.py` uses for `dr-qr--align-*`. An inline style here
    # would be unoverridable by a site's own sheet.
    classes = "dr-form"
    if opts.get("align"):
        classes += " dr-form--align-" + opts["align"]

    if not fold:
        return '<div class="' + classes + '">' + window + tools + fallback + "</div>"

    # 🔴 THE ANCHOR SITS ON THE <summary>, NOT ON THE <details>. A fragment must
    # target something INSIDE the disclosure for auto-expand to apply; pointing it
    # at the <details> itself scrolls correctly and stays shut.
    #
    # ⭐ `open` IS AN ATTRIBUTE ON THE SAME ELEMENT, so "expanded" and "closed" are
    # ONE markup shape with one character of difference -- not two branches.
    return (
        '<div class="' + classes + '">'
        '<details class="dr-form__open"' + (" open" if fold == "open" else "")
        + '><summary id="' + _esc(slot_anchor(slot)) + '">'
        + _esc(text or _DEFAULT_LABEL) + "</summary>"
        + window + tools + fallback
        + "</details></div>"
    )


def on_page_markdown(markdown, page, config, files):
    """Replace each `!!! form "slot"` with the embed, and load the helper once.

    ⚠️ `sub_outside_code` IS NOT OPTIONAL. The authoring page that documents this
    directive contains the directive, and util's own docstring records the first
    time that bit this engine.

    ⭐ THE HELPER SCRIPT IS APPENDED ONCE PER PAGE, NOT ONCE PER FORM.

    🔴 THE STYLE BLOCK IS GATED ON A FRAME EXISTING, NOT ON A BUTTON EXISTING, and
    that distinction WAS the first 2026-08-30 regression: the print rules rode in
    the reload-button block, so a page setting `reload: false` printed its whole
    iframe. The LISTENER alone is gated on a button -- one with nothing to click is
    pure cost. Frames and buttons are different facts.

    ⚠️ EVERY OPTION PROBLEM IS REPORTED, NEVER DROPPED. `directive_options` is a
    pure function handing back sentences rather than logging them, so this is where
    they become findings.

    ⭐ THE `views:` PASS RUNS HERE TOO, LAST, because one hook keeps this feature
    out of `mkdocs.yml`. 🔴 The import is local ON PURPOSE -- `views.py` imports from
    here at its module top, and top-level imports both ways would be a cycle.
    ⚠️ Order is arbitrary: the patterns are disjoint and neither reads the other.
    """
    if "!!!" not in markdown:
        return markdown

    src = getattr(page.file, "src_uri", "")
    embedded = []
    reloadable = []

    def swap(match):
        slot = match.group(1).strip()
        opts, problems = directive_options(match.group("opts"), _LEGAL_OPTS)
        for problem in problems:
            state.note(
                "notes",
                src + ': `!!! form "' + slot + '"` carries ' + problem,
            )
        html_out = _html(src, slot, opts)
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
        out += "\n" + _RESET_CSS + "\n"
    if reloadable:
        out += "\n" + _RESET_JS + "\n"

    from . import views

    return views.on_page_markdown(out, page, config, files)
