"""The `views:` registry -- an embedded ClickUp VIEW, named once in frontmatter.

WHY decisions here are the way they are: the doc-render-engine Decision Log, and
`specs/view-embed.md` (BUILD 7). Registered by NO hook of its own -- `forms.py`
calls in. See THE DELEGATION below.

    views:
      recently-created:
        src: https://sharing.clickup.com/36074068/l/h/12cwjm-61513/486ae60bf886d69
        text: Recently created notes
        caption: true
        height: 700px

    !!! view "recently-created"

Michael, 2026-08-28: *"could i embed a clickup TABLE VIEW into one of my doc
renderer pages??? like embedding a clickup form on the safety site but doing a
custom clickup table view to embed instead"* -- and on scope, 2026-08-29: *"i
want to know how to embed any clickup view in one of my pages. let me decide
what actually gets rendered... focus on the tool."*

🚫 THE CONTENT REPO NEVER HOLDS THE IFRAME, exactly as `forms.py` states it. The
page NAMES a view; the engine builds the element. Fourth registry to take that
shape, after `links:`, `data:` and `forms:`.

🚫 AND IT DOES NOT DECIDE WHAT BELONGS ON A PAGE. Every constraint recorded here
is a property of the MECHANISM. Which view, on which page, showing what, is the
author's call -- the filters travel with the share, so the control is in ClickUp.

=============================================================================
⭐ THE DELEGATION -- WHY THIS IS ITS OWN MODULE WITH NO HOOK
=============================================================================
`specs/view-embed.md` §2 argued for FOLDING this into `forms.py`: same verb,
validate a URL and emit an element, and a second module would be a second
implementation of one idea.

🔴 THE FOLD DIED ON A MEASUREMENT. `forms.py` was 11,740 B when that was written
and is 17,360 B at HEAD -- PR #197 added the dead-reference marker on 08-30.
Folding a second registry in lands ~21KB, past the 18KB warn line and into the
~22KB read ceiling, and a file that cannot be read whole cannot be safely edited.

⚠️ SO THE SEAM MOVED, BUT THE COHESION ARGUMENT DID NOT LOSE. Both halves still
hold, and the shape that honours both is DELEGATION:

  * `forms.py` keeps the ONLY hook and calls `views.on_page_markdown` last.
  * the shared vocabulary -- `_esc`, the `docrender-dead` span -- is IMPORTED
    from `forms.py`, never re-declared. One implementation, two callers.

🔴 AND THE ONE HOOK IS NOT TIDINESS, IT IS THE WHOLE REASON THIS IS CHEAP.
A second hook means an edit to `mkdocs.yml`, which is 28,158 B -- unreadable
whole, therefore unsafe to rewrite. The delegation buys a new directive for zero
edits to any file past the ceiling. `instance.py` (23,047 B) is dodged the same
way: `view_hosts:` is READ off `state.INSTANCE`, never parsed per-key, which is
the trick `urllinks.py` already uses for `links:`.

⚠️ IMPORT ORDER IS LOAD-BEARING AND LOOKS LIKE A CIRCLE. `forms.py` imports this
module INSIDE its hook function, not at module top; this module imports from
`forms.py` at module top. That is deliberate: by the time anything calls the
hook, `forms` is fully loaded, so there is no cycle. Do not "tidy" either import.

=============================================================================
🔴 NO CDN SCRIPT, AND CLICKUP'S OWN OUTPUT IS THE EVIDENCE
=============================================================================
`forms.py` leans on `class="clickup-embed clickup-dynamic-height"` plus
`forms-embed/v1.js` to give the frame a height, and documents the sharp edge:
`height="100%"` with no sized parent is ~0px, so a CDN failure renders an
INVISIBLE embed rather than a broken one.

⭐ A VIEW EMBED DOES NOT HAVE THAT PROBLEM, because ClickUp does not hand you
that mechanism. The real embed code for a shared view (Michael, 2026-08-30) is:

    <iframe class="clickup-embed" src="..." onwheel="" width="100%"
            height="700px" style="background: transparent; border: 1px solid #ccc;">

— `clickup-embed` only, NO `clickup-dynamic-height`, and a LITERAL `700px`. So
ClickUp itself answers the question the spec left open as ruling 2: for a view,
the height is declared, not scripted.

🚫 THEREFORE THIS MODULE NEVER APPENDS THE HELPER SCRIPT. Fetching a sizing
asset for a frame that is already sized is pure cost, and it would also mean two
registries racing to append the same asset once per page.

⚠️ THE FLOOR STAYS ANYWAY. `min-height` is set to the same value as `height`, so
a stylesheet that overrides the attribute cannot collapse the frame to nothing.
Cheap, and it is the one failure mode `forms.py` calls unobservable at build time.

=============================================================================
🔴 THE HOST IS DECLARED PER SITE. NEVER GUESSED, NEVER HARDCODED HERE.
=============================================================================
`_FORM_HOST` is a single literal because a form has exactly one home. A view does
not: the share surface is a ClickUp product decision that can move, and this
engine renders more than one site.

So the allow-list comes from the instance config:

    view_hosts:
      - https://sharing.clickup.com/

🚫 NO DEFAULT, AND NO FALLBACK. An absent or empty `view_hosts:` refuses every
embed and REPORTS it. A default would be this engine remembering a third-party
hostname on the reader's behalf, and the standing rule is that an unverifiable
external fact is declared or it does not exist.

🚫 AND NEVER A `*.clickup.com` WILDCARD, however tempting. That also matches
`app.clickup.com`, the LOGGED-IN application -- so a page could embed a workspace
URL and serve a login wall to the public, which reads as a broken table rather
than as a misconfiguration. Exact hosts, listed.

⚠️ UNVERIFIABLE AT BUILD TIME, the same reduction `forms.py` and `urllinks.py`
both state at the top of their own files. The host is checked. Nothing here can
prove the view is still shared, still exists, or shows what its author thinks.
🔴 A REVOKED SHARE RENDERS AN EMPTY FRAME WITH NO FINDING -- the fallback link is
the only thing that distinguishes "loading" from "gone."

=============================================================================
⚠️ WHAT THE READER GETS THAT A FORM READER DOES NOT: A CAPTION
=============================================================================
An embedded view carries ClickUp's own chrome -- *Sign up free* / *Login* and an
*Embed ClickUp* logo -- inside a cross-origin iframe, so it cannot be removed.
(Both are open, unresolved feature requests on ClickUp's board.)

⭐ So the caption is not decoration, it is the cheapest available answer to "why
is there a signup button in the middle of a policy page": it names the frame as
live ClickUp content, which turns the chrome from clutter into provenance. ON by
default, `caption: false` to suppress.

⚠️ AND THE FALLBACK LINK IS ALWAYS RENDERED, `forms.py`'s rule inherited whole.
An iframe prints as a blank rectangle. 🔴 IT IS A WORSE LOSS HERE THAN FOR A FORM,
and that is stated rather than solved: a printed form-link is a fine substitute
because the reader was going to click something anyway, but for a table the
frame IS the content, so paper gets a link where information belongs. A second,
build-time copy of the same table was considered and refused -- it would be a
mirror that disagrees with the live one the first time a filter changes.
"""

from __future__ import annotations

import re

from . import state
from .forms import _dead, _esc
from .util import sub_outside_code

#: `!!! view "slot"` alone on its line. Same shape as `!!! form` and `!!! data`,
#: so the body vocabulary stays one pattern rather than three spellings.
_VIEW = re.compile(r'(?m)^[ \t]*!!![ \t]+view[ \t]+"([^"\n]+)"[ \t]*$')

#: ClickUp's own literal for a shared view. See the docstring: their embed code
#: ships a real height, so ours does too.
_DEFAULT_HEIGHT = "700px"

#: A CSS length, loosely. Enough to catch a bare number or a stray unit typo
#: before it reaches an attribute, not a full CSS parser.
_LENGTH = re.compile(r"^\d+(\.\d+)?(px|rem|em|vh|%)$")

_DEFAULT_CAPTION = "Live from ClickUp \u2014 updates automatically."

_DEAD_LABEL = "View"


def _hosts() -> list:
    """The allow-listed view hosts for THIS site, normalised to end in "/".

    ⚠️ READ AT CALL TIME, never cached at import. `prefixes.py` documents the trap
    in its own header: the instance config is populated during the build, so a
    read at import time caches an empty answer for the whole run.
    """
    raw = (state.INSTANCE or {}).get("view_hosts")
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        host = str(item).strip()
        if host:
            out.append(host if host.endswith("/") else host + "/")
    return out


def _declared(src) -> list:
    """Every view slot this page declares, sorted. For the diagnosis only.

    ⭐ NAMING WHAT *IS* DECLARED IS MOST OF THE VALUE OF THE MESSAGE -- it turns a
    typo from a hunt into a glance. Precedent: `forms._declared`, and before it
    `sheet.apply_options` printing the real header beside a bad `hide:`.
    """
    block = (state.BY_SRC.get(src, {}) or {}).get("views")
    return sorted(str(k) for k in block) if isinstance(block, dict) else []


def _entry(src, slot):
    """One entry out of a page's `views:` map, or None.

    Two spellings, matching `links:` and `forms:`: a bare string is the src, a
    mapping carries `src:`, `text:`, `caption:` and `height:`.

    ⚠️ `caption` DEFAULTS TRUE, which is the one place this differs from every
    other optional key in the engine. Deliberate: the chrome it explains is
    always present, so the explanation should be too. `caption: false` opts out.
    """
    block = (state.BY_SRC.get(src, {}) or {}).get("views")
    if not isinstance(block, dict):
        return None
    raw = block.get(slot)
    if raw is None:
        return None
    if isinstance(raw, str):
        return (raw.strip(), "", True, "")
    if isinstance(raw, dict):
        return (
            str(raw.get("src", "")).strip(),
            str(raw.get("text", "")).strip(),
            raw.get("caption") is not False,
            str(raw.get("height", "")).strip(),
        )
    return ("", "", True, "")


def _height(src, slot, declared) -> str:
    """The frame height: what the page declared, or ClickUp's own default.

    🔴 A BAD VALUE IS REPORTED AND REPLACED, NEVER PASSED THROUGH. `height: 700`
    with no unit is invalid in an attribute and silently renders a collapsed
    frame -- the exact invisible-not-broken failure `forms.py` exists to warn
    about. So it is checked here, where the fix is one line of frontmatter.
    """
    if not declared:
        return _DEFAULT_HEIGHT
    if _LENGTH.match(declared):
        return declared
    state.note(
        "notes",
        src + ": `views: " + slot + "` has height '" + declared + "', which is "
        "not a CSS length (try 700px, 48rem, 80vh). Using " + _DEFAULT_HEIGHT
        + " instead -- a unitless height renders a collapsed, invisible frame.",
    )
    return _DEFAULT_HEIGHT


def _html(src, slot) -> str:
    entry = _entry(src, slot)
    if entry is None:
        known = _declared(src)
        state.note(
            "dead_links",
            src + ': `!!! view "' + slot + '"` names a slot that is not in this '
            "page's `views:` block. Declared here: "
            + (", ".join(known) or "nothing") + ". Nothing was embedded.",
        )
        # 🔴 A MARKER, NOT "". Returning empty deletes the line and makes a typo
        # indistinguishable from a page that never asked for a view -- the exact
        # defect PR #197 fixed for forms, inherited here rather than re-learned.
        return _dead(
            "view slot not declared on this page: " + slot
            + ". Declared here: " + (", ".join(known) or "nothing") + ".",
            _DEAD_LABEL,
        )

    url, text, caption, raw_height = entry
    hosts = _hosts()

    if not hosts:
        state.note(
            "dead_links",
            src + ": `views: " + slot + "` cannot be embedded because this site "
            "declares no `view_hosts:` in its instance config. Add the host from "
            "a real ClickUp embed code. NOT embedded -- the host is an "
            "allow-list, and this engine never guesses a third-party hostname.",
        )
        return _dead(
            "no `view_hosts:` is declared for this site, so view '" + slot
            + "' was not embedded.",
            _DEAD_LABEL,
        )

    if not any(url.startswith(host) for host in hosts):
        state.note(
            "dead_links",
            src + ": `views: " + slot + "` must start with one of this site's "
            "declared `view_hosts:` (" + ", ".join(hosts) + ") -- found '" + url
            + "'. NOT embedded. \u26a0\ufe0f If the value looks like a whole "
            "<iframe>, paste only the src= URL: the page names a view and the "
            "engine builds the element.",
        )
        # ⚠️ THE CASE WHERE A MARKER MATTERS MOST: the slot EXISTS, so an author
        # reading the page has every reason to think the embed is merely slow.
        return _dead(
            "view '" + slot + "' is not on an allow-listed host ("
            + ", ".join(hosts) + "), so it was not embedded.",
            _DEAD_LABEL,
        )

    height = _height(src, slot, raw_height)
    label = text or "Open this view in a new tab"

    # 🚫 `clickup-embed` ONLY. No `clickup-dynamic-height`, and no helper script:
    # ClickUp's own embed code for a view ships a literal height. See docstring.
    frame = (
        '<iframe class="clickup-embed" src="' + _esc(url)
        + '" onwheel="" width="100%" height="' + _esc(height)
        + '" title="' + _esc(label)
        + '" style="background: transparent; border: 1px solid #ccc; '
        "min-height: " + _esc(height) + ';"></iframe>'
    )
    caption_html = (
        '<p class="dr-view__caption">' + _esc(_DEFAULT_CAPTION) + "</p>"
        if caption else ""
    )
    # ⚠️ ALWAYS RENDERED, not only for print. An iframe prints blank, and on
    # screen this is the answer to "the table did not load."
    fallback = (
        '<p class="dr-view__fallback"><a href="' + _esc(url) + '">'
        + _esc(label) + "</a></p>"
    )
    return '<div class="dr-view">' + frame + caption_html + fallback + "</div>"


def on_page_markdown(markdown, page, config, files):
    """Replace each `!!! view "slot"` with the embed.

    🔴 NOT A HOOK. `forms.on_page_markdown` calls this; see THE DELEGATION in the
    module docstring. The signature matches a real hook deliberately, so that if
    `forms.py` is ever split for size this becomes one registration and no edit.

    ⚠️ `sub_outside_code` IS NOT OPTIONAL. The page that documents this directive
    contains the directive, and `util.py`'s own docstring records the first time
    that bit this engine.

    🚫 NO SCRIPT APPEND, unlike the forms pass. Nothing to size.
    """
    if "!!!" not in markdown:
        return markdown
    src = getattr(page.file, "src_uri", "")

    def swap(match):
        out = _html(src, match.group(1).strip())
        return "\n\n" + out + "\n\n" if out else ""

    return sub_outside_code(_VIEW, swap, markdown)
