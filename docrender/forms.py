"""The `forms:` registry -- an embedded ClickUp form, named once in frontmatter.

WHY decisions here are the way they are: the doc-render-engine Decision Log.
The flow strip is docrender/program.py; both are registered by stage 05b.

    forms:
      completion:
        src: https://forms.clickup.com/36074068/f/...?Program_ID=ITPSAFE-1225
        text: General Safety completion form
        collapsed: true

    !!! form "completion"

Michael, 2026-08-19: *"can i embed an actual clickup form as content in the
bottom of these pages... so that users dont have to leave the page"* and, on
where it is declared: *"love that i can define in frontmatter, well outside of
the actual body content."*

🚫 THE CONTENT REPO NEVER HOLDS THE IFRAME. An `<iframe>` and a CDN `<script>`
are machinery, and machinery is the one thing the content tree may not contain.
The page NAMES a form; the engine builds the element. Exactly the split `data:`
slots and the `links:` registry already use, and the reason the body directive
is `!!! form` rather than pasted HTML.

=============================================================================
🔴 A BROKEN SLOT USED TO RENDER **NOTHING**. FIXED 2026-08-30.
=============================================================================
> Michael, 2026-08-30: *"why wont the second form for NOTES render on my new
> rehearsal report page"*

The cause was a one-word typo -- the body said `rehearesl-note`, the frontmatter
declared `rehearsal-note`. **The cause is not the finding.** `_html` returned
`""` for an unknown slot and `swap` returns `""` on falsy, so the directive line
VANISHED: no marker, no gap, no clue.

⚑ AND THE TELL IS THAT ITS TWO SIBLINGS ALREADY GOT THIS RIGHT. `qr.py` renders
a struck-through `docrender-dead` span; `links.py` renders the same thing for a
dead reference and `markerlinks.py` states the rule outright -- *"a dead
reference never degrades into a span... falling back would be a silent second
legal path."* **Three directives share one pattern and one vocabulary, and the
only one that failed silently was the one whose absence a reader cannot infer.**
A missing QR is obviously missing. A missing form on a page that already shows
one form looks deliberate.

⚠️ IT WAS IN THE BUILD REPORT THE WHOLE TIME, under `dead_links`, naming the bad
slot and listing the legal ones. Nobody read it -- which is `next-build-spec.md`
BUILD 2's entire premise (*"the build report has no reader"*) acquiring a live
fourth instance. ⭐ **So the fix is not a new message. It is the message that
already existed, on a second SURFACE** -- the page -- rather than a second
claimant on one truth.

✅ AND IT REACHES PAPER FOR FREE. `assets/base.css` gives `.docrender-dead` a
`--dr-dead` dotted underline unscoped to any medium, and `print.css` carries a
whole block arguing AGAINST re-declaring it. Verified live on 2026-08-19: two
dead references printed in red on a policy sheet with no print rule at all.

🚫 NOT AN ANCHOR, on `qr.py`'s precedent: a form that failed to resolve must not
offer a control. The `title` carries the diagnosis; the span carries no href.

=============================================================================
⭐ SPLIT OUT OF program.py THE SAME DAY IT SHIPPED, AND THE REASON IS COHESION
=============================================================================
`program.py` held the flow strip and this embed and reached 16,949 B; adding
`collapsed:` would have pushed it past the ~22KB read ceiling. 🔴 BUT SIZE WAS
THE TRIGGER, NOT THE REASON -- `specs/visibility-split.md` §1 already ruled on
exactly this: *"The cut that is worth making follows the concerns. It also fixes
the bytes. If those two ever disagree, follow the concerns."*

They agree here. A strip is NAVIGATION -- it reads the chain graph, resolves
pages, and computes position. A form is an EMBED -- it validates a URL and emits
an element. They share no state and call none of each other's helpers. The only
thing they ever shared was a hook shim, and they still do.

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

⚠️ AND THE FALLBACK LINK IS ALWAYS RENDERED, not only for print. An iframe
prints as a blank rectangle and this engine has a print identity spec, so a
printed program packet would otherwise carry a hole where the completion form
belongs. On screen the same link is the answer to "the form did not load."

=============================================================================
⭐ `collapsed:` -- A PROGRAM PAGE IS BOTH THE ENTRANCE AND THE EXIT
=============================================================================
Michael, 2026-08-19: *"if the form could not be so stand out on the first
landing but then when we circle back to ending there on the same page - it's
easily found."*

That is a real sequencing problem rather than a styling preference. A reader
lands on the program page BEFORE reading anything and returns to it to submit.
An open form on arrival instructs somebody to certify material they have not
read yet, which is the pre-filled-checklist hazard `30-programs/index.md`
already warns about in its own words.

🔴 THE MECHANISM IS A FRAGMENT, NOT A SCRIPT. `collapsed: true` renders the embed
inside a closed `<details>`, and the LAST STEP of the flow links to the
`<summary>`'s own id. Per the HTML spec, a fragment navigation targeting content
inside a closed `<details>` expands it -- so arriving from the end of the program
opens the form, with no JavaScript, no query parameter and no state.

⚠️ IT DEGRADES HONESTLY WHERE THAT BEHAVIOUR IS MISSING, which is why it is safe
to ship without browser-support arithmetic nobody can verify from this chair: the
reader lands on a visible, obviously-clickable "Complete this program" control
and clicks once. One extra click, never a dead end.

🚫 NOT AUTOMATIC ON A PROGRAM PAGE, though it easily could be. It is a DECLARED
key, because a form on a single policy page acknowledging one rule wants to be
open, and an engine deciding that by type would be a rule nobody can see in the
content. Declared beats inferred; `objects/program.yml` carries the vocabulary.

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
_FORM_HOST = "https://forms.clickup.com/"

#: ClickUp's own embed helper. What `clickup-dynamic-height` needs.
_FORM_SCRIPT = "https://app-cdn.clickup.com/assets/js/forms-embed/v1.js"

#: The floor that keeps a script failure from rendering an invisible form.
_FORM_MIN_HEIGHT = "40rem"

_DEFAULT_LABEL = "Complete this program"

#: What a failed embed says on the PAGE. Deliberately one word: `links.py` and
#: `qr.py` both render a short label with the diagnosis in the `title`, so a
#: reader meets one consistent shape for every broken reference on the site.
_DEAD_LABEL = "Form"


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _dead(reason: str) -> str:
    """The same struck-through span `links.py` and `qr.py` render.

    🚫 DELIBERATELY NOT AN ANCHOR. A form that failed to resolve must not offer a
    control -- the dead-control rule this engine applies to `edit_links: false`,
    the retired PR number and the printed link policy. The `title` carries the
    diagnosis; there is nothing to click.

    ✅ AND IT PRINTS WITHOUT A PRINT RULE. `base.css` declares the `--dr-dead`
    dotted underline unscoped to any medium; `print.css` has a whole block
    arguing against re-declaring it. So a printed sheet shows the failure too,
    which matters on a compliance page more than on screen.
    """
    return (
        '<span class="docrender-dead" title="'
        + html.escape(reason, quote=True) + '">'
        + html.escape(_DEAD_LABEL) + "</span>"
    )


def slot_anchor(slot: str) -> str:
    """The id a flow's last step links to, to open a collapsed form.

    ⭐ PUBLIC, AND program.py IS THE CALLER. One function owns the spelling of
    this id, because a link and its target computed in two places is the defect
    that produces a Next button landing on nothing -- and it would land
    SILENTLY, since a fragment that matches no element is not an error.
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

    Two spellings, matching the `links:` registry: a bare string is the src, a
    mapping carries `src:`, `text:` and `collapsed:`.
    """
    block = (state.BY_SRC.get(src, {}) or {}).get("forms")
    if not isinstance(block, dict):
        return None
    raw = block.get(slot)
    if raw is None:
        return None
    if isinstance(raw, str):
        return (raw.strip(), "", False)
    if isinstance(raw, dict):
        return (
            str(raw.get("src", "")).strip(),
            str(raw.get("text", "")).strip(),
            raw.get("collapsed") is True,
        )
    return ("", "", False)


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
        # indistinguishable from a page that never asked for a form. See the
        # docstring: this is the report's own sentence on a second surface.
        return _dead(
            "form slot not declared on this page: " + slot
            + ". Declared here: " + (", ".join(known) or "nothing") + "."
        )

    url, text, collapsed = entry
    if not url.startswith(_FORM_HOST):
        state.note(
            "dead_links",
            src + ": `forms: " + slot + "` must be a " + _FORM_HOST
            + " address (found '" + url + "'). NOT embedded -- this element runs "
            "a third-party script in the reader's browser, so the host is an "
            "allow-list rather than a scheme check.",
        )
        # ⚠️ ALSO VISIBLE NOW, and this is the case where it matters most: the
        # slot EXISTS, so an author reading the page has every reason to believe
        # the embed is working and merely slow.
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
    fallback = (
        '<p class="dr-form__fallback"><a href="' + _esc(url) + '">'
        + _esc(label) + "</a></p>"
    )

    if not collapsed:
        return (
            '<div class="dr-form">' + frame + fallback + "</div>"
        )

    # 🔴 THE ANCHOR SITS ON THE <summary>, NOT ON THE <details>. A fragment must
    # target something INSIDE the disclosure for the auto-expand behaviour to
    # apply; pointing it at the <details> itself is the version of this that
    # scrolls correctly and stays shut.
    return (
        '<div class="dr-form">'
        '<details class="dr-form__open">'
        '<summary id="' + _esc(slot_anchor(slot)) + '">'
        + _esc(text or _DEFAULT_LABEL) + "</summary>"
        + frame + fallback
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

    🔴 AND IT IS APPENDED ONLY WHEN A FRAME WAS ACTUALLY EMITTED, which is why
    `embedded` is counted separately from "the directive matched". A page whose
    only form is broken now renders a visible marker and MUST NOT fetch the CDN
    asset for it -- there would be no frame for the script to size, so the
    request would be pure cost. ⚠️ Before 2026-08-30 the two were the same
    question, because a broken slot returned "" and could not be told apart from
    no directive at all.
    """
    if "!!!" not in markdown:
        return markdown

    src = getattr(page.file, "src_uri", "")
    embedded = []

    def swap(match):
        html_out = _html(src, match.group(1).strip())
        if not html_out:
            return ""
        if "<iframe" in html_out:
            embedded.append(1)
        return "\n\n" + html_out + "\n\n"

    out = sub_outside_code(_FORM, swap, markdown)
    if embedded:
        out += '\n\n<script async src="' + _FORM_SCRIPT + '"></script>\n'
    return out
