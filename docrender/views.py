"""The `views:` registry -- an embedded ClickUp VIEW, named once in frontmatter.

WHY decisions here are the way they are: the doc-render-engine Decision Log, and
`specs/view-embed.md` (BUILD 7). Registered by NO hook of its own -- `forms.py`
calls in. See THE DELEGATION below.

    views:
      recently-created:
        src: https://sharing.clickup.com/36074068/l/h/12cwjm-61513/486ae60bf886d69
        text: Recently created notes
        height: 700px

    !!! view "recently-created"

✅ WORKS ON ANY SITE WITH NO CONFIGURATION. That is the whole shape of the
feature and it is deliberate -- see THE HOST below for why an earlier version got
it wrong.

Michael, 2026-08-28: *"could i embed a clickup TABLE VIEW into one of my doc
renderer pages??? like embedding a clickup form on the safety site but doing a
custom clickup table view to embed instead"* -- and on scope, 2026-08-29: *"i
want to know how to embed any clickup view in one of my pages. let me decide
what actually gets rendered... focus on the tool."*

🚫 THE CONTENT REPO NEVER HOLDS THE IFRAME, exactly as `forms.py` states it. The
page NAMES a view; the engine builds the element. Fourth registry to take that
shape, after `links:`, `data:` and `forms:`.

⚠️ ONLY THE `src=` URL GOES IN THE FRONTMATTER, NOT THE WHOLE `<iframe>`. The
first real paste did exactly that, which is the predictable mistake, so the
allow-list message below says so by name.

=============================================================================
🚫 THE ENGINE WRITES NO PROSE ONTO A PAGE. DELETED 2026-08-30, SAME DAY.
=============================================================================
> Michael, on seeing the rendered caption: *"WHAT THE FUCK IS THIS SLOP. DELETE
> IT IMMEDIATELY."*

v1 of this module emitted a caption under every frame reading *"Live from ClickUp
— updates automatically."* It is gone: no key, no constant, no CSS, no default.

🔴 THE DEFECT WAS NOT THE WORDING, IT WAS THE CATEGORY. Every other thing this
registry emits is STRUCTURE -- a frame, a link, a failure marker. The caption was
the engine deciding an editorial sentence belonged in Michael's content, in his
voice, on his page, unasked. ⚠️ It was reasoned into existence from a real
constraint (ClickUp's unremovable *Sign up free* chrome) and the reasoning was
sound, which is exactly what made it hard to see: **a good argument for WHY a
reader might want an explanation is not an argument for the ENGINE writing it.**
If a page wants that sentence, the author types it above the directive.

🔴 AND IT SHIPPED AN EM DASH INTO RENDERED OUTPUT, against a standing, absolute
house rule. That is the tell that should have caught it earlier: the rule exists
for prose, so a module emitting text that can VIOLATE a prose rule is a module
writing prose, which this one has no business doing.

✅ THE FALLBACK LINK IS NOT THE SAME THING AND STAYS. It is a control with a
function -- the answer to "the table did not load" and the only content on paper.
Its label is the author's `text:`. **Function stays, narration goes.**

⚠️ A LEFTOVER `caption:` KEY IS REPORTED, NOT SILENTLY EATEN. Pages written
against v1 still carry it, and a key that quietly does nothing is this repo's
least favourite shape (PR #197, one day earlier, same feature). One `notes` line
says it was removed and can be deleted.

=============================================================================
⭐ THE DELEGATION -- WHY THIS IS ITS OWN MODULE WITH NO HOOK
=============================================================================
`specs/view-embed.md` §2 argued for FOLDING this into `forms.py`: same verb,
validate a URL and emit an element, and a second module would be a second
implementation of one idea.

🔴 THE FOLD DIED ON A MEASUREMENT. `forms.py` was 11,740 B when that was written
and ~17.4KB when this was built -- PR #197 added the dead-reference marker on
08-30. Folding a second registry in lands ~21KB, past the 18KB warn line and into
the ~22KB read ceiling, and a file that cannot be read whole cannot be safely
edited.

⚠️ SO THE SEAM MOVED, BUT THE COHESION ARGUMENT DID NOT LOSE. Both halves still
hold, and the shape that honours both is DELEGATION:

  * `forms.py` keeps the ONLY hook and calls `views.on_page_markdown` last.
  * the shared vocabulary -- `_esc`, the `docrender-dead` span -- is IMPORTED
    from `forms.py`, never re-declared. One implementation, two callers.

🔴 AND THE ONE HOOK IS NOT TIDINESS, IT IS THE WHOLE REASON THIS IS CHEAP.
A second hook means an edit to `mkdocs.yml`, which is 28,158 B -- unreadable
whole, therefore unsafe to rewrite. The delegation buys a new directive for zero
edits to any file past the ceiling. `instance.py` (23,047 B) is dodged the same
way: the optional `view_hosts:` key is READ off `state.INSTANCE`, never parsed
per-key, which is the trick `urllinks.py` already uses for `links:`.

⚠️ IMPORT ORDER IS LOAD-BEARING AND LOOKS LIKE A CIRCLE. `forms.py` imports this
module INSIDE its hook function, not at module top; this module imports from
`forms.py` at module top. That is deliberate: by the time anything calls the
hook, `forms` is fully loaded, so there is no cycle. Do not "tidy" either import.

=============================================================================
🔴 THE HOST IS AN ENGINE DEFAULT. CORRECTED 2026-08-30, SAME DAY IT SHIPPED.
=============================================================================
> Michael, on being told the host goes in every site's config: *"in every sits
> congit?????????????????? so i can do this anywehre i want later?"*

He was right and this is the correction. v1 of this module required every site to
declare `view_hosts:` in its own `instances/<slug>/site.yml`, with NO default, on
the rule that *"this engine never guesses a third-party hostname."*

🔴 THE RULE WAS RIGHT AND IT WAS BEING APPLIED TO THE WRONG NOUN. "Never guess"
protects against inventing a value nobody has verified. `sharing.clickup.com` was
not guessed -- it was read out of a real embed code Michael pasted. **Once a value
is verified it is a FACT, and a fact does not need six copies to become true.**

⚠️ AND THE SIBLING FILE ALREADY SETTLED THIS. `forms.py` hardcodes
`_FORM_HOST = "https://forms.clickup.com/"` as a module constant and has since
day one. Both are ClickUp's own product hostnames, both single-valued, both
verified from real output. **Two files, one kind of fact, two different
mechanisms -- and the newer one was the inconsistent one.** The cheap tell I
missed: a per-site key whose correct value is identical on every site is not
configuration, it is a constant with extra steps.

🔴 THE REAL COST WAS A SILENT FAILURE ON EVERY FUTURE SITE. Six `instances/*`
configs exist today. A seventh site would embed a view, get a refusal, and the
author would have no reason to suspect a config key they never knew about --
which is precisely the class of defect PR #197 was fixing one file over, on the
same day, in the same feature.

✅ SO: `_DEFAULT_HOST` is the verified value, and `view_hosts:` survives as an
ADDITIVE per-site extension -- a site can allow an extra host, and cannot lose
the default by declaring one. It is now for the case the default cannot cover
(ClickUp ships a second surface, or a site is on a different tenant domain), not
for the ordinary case.

🚫 EVERYTHING THE ORIGINAL RULE ACTUALLY PROTECTED IS UNCHANGED:
  * an allow-list, never a scheme check, because this element embeds third-party
    content on a page that may carry a compliance instruction;
  * NEVER a `*.clickup.com` wildcard -- that also matches `app.clickup.com`, the
    LOGGED-IN application, so a page could embed a workspace URL and serve a
    login wall to the public, which reads as a broken table rather than as a
    misconfiguration;
  * a `src` off the list is refused, REPORTED, and marked on the page.

⚠️ AND IF THE DEFAULT EVER GOES STALE, THE FAILURE IS LOUD, WHICH IS WHY THIS IS
SAFE. A wrong host produces a refusal naming both the found URL and the allowed
hosts, on the page and in the build report -- not a silent empty frame. Fix the
constant, or add the new host to one site's `view_hosts:` to unblock immediately.

⚠️ UNVERIFIABLE AT BUILD TIME, the same reduction `forms.py` and `urllinks.py`
both state at the top of their own files. The host is checked. Nothing here can
prove the view is still shared, still exists, or shows what its author thinks.
🔴 A REVOKED SHARE RENDERS AN EMPTY FRAME WITH NO FINDING -- the fallback link is
the only thing that distinguishes "loading" from "gone."

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
⚠️ PRINT: A REAL LOSS, STATED RATHER THAN SOLVED
=============================================================================
An iframe prints as a blank rectangle, so the fallback link is ALWAYS rendered --
`forms.py`'s rule inherited whole. 🔴 IT IS A WORSE LOSS HERE THAN FOR A FORM: a
printed form-link is a fine substitute because the reader was going to click
something anyway, but for a table the frame IS the content, so paper gets a link
where information belongs. A second, build-time copy of the same table was
considered and refused -- it would be a mirror that disagrees with the live one
the first time a filter changes.
"""

from __future__ import annotations

import re

from . import state
from .forms import _dead, _esc
from .util import sub_outside_code

#: `!!! view "slot"` alone on its line. Same shape as `!!! form` and `!!! data`,
#: so the body vocabulary stays one pattern rather than three spellings.
_VIEW = re.compile(r'(?m)^[ \t]*!!![ \t]+view[ \t]+"([^"\n]+)"[ \t]*$')

#: Where ClickUp serves a publicly shared view. Read out of a real embed code on
#: 2026-08-30, not guessed -- and a module constant for exactly the reason
#: `_FORM_HOST` is one. See THE HOST in the docstring: this is what makes the
#: feature work on a brand-new site with no configuration at all.
_DEFAULT_HOST = "https://sharing.clickup.com/"

#: ClickUp's own literal for a shared view. See the docstring: their embed code
#: ships a real height, so ours does too.
_DEFAULT_HEIGHT = "700px"

#: A CSS length, loosely. Enough to catch a bare number or a stray unit typo
#: before it reaches an attribute, not a full CSS parser.
_LENGTH = re.compile(r"^\d+(\.\d+)?(px|rem|em|vh|%)$")

_DEAD_LABEL = "View"


def _hosts() -> list:
    """The allow-listed view hosts: the engine default, plus this site's extras.

    ✅ ADDITIVE, NOT AN OVERRIDE, and that is the load-bearing word. A site that
    declares `view_hosts:` ADDS to the default rather than replacing it, so no
    configuration can accidentally break the ordinary case. Declaring one host to
    allow a second ClickUp surface must not silently disallow the first.

    ⚠️ READ AT CALL TIME, never cached at import. `prefixes.py` documents the trap
    in its own header: the instance config is populated during the build, so a
    read at import time caches an empty answer for the whole run.
    """
    out = [_DEFAULT_HOST]
    raw = (state.INSTANCE or {}).get("view_hosts")
    if isinstance(raw, str):
        raw = [raw]
    if isinstance(raw, list):
        for item in raw:
            host = str(item).strip()
            if not host:
                continue
            if not host.endswith("/"):
                host += "/"
            if host not in out:
                out.append(host)
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
    mapping carries `src:`, `text:` and `height:`.
    """
    block = (state.BY_SRC.get(src, {}) or {}).get("views")
    if not isinstance(block, dict):
        return None
    raw = block.get(slot)
    if raw is None:
        return None
    if isinstance(raw, str):
        return (raw.strip(), "", "", False)
    if isinstance(raw, dict):
        return (
            str(raw.get("src", "")).strip(),
            str(raw.get("text", "")).strip(),
            str(raw.get("height", "")).strip(),
            "caption" in raw,
        )
    return ("", "", "", False)


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

    url, text, raw_height, had_caption = entry
    hosts = _hosts()

    if not any(url.startswith(host) for host in hosts):
        state.note(
            "dead_links",
            src + ": `views: " + slot + "` must start with an allow-listed host ("
            + ", ".join(hosts) + ") -- found '" + url + "'. NOT embedded. "
            "\u26a0\ufe0f If the value looks like a whole <iframe>, paste only the "
            "src= URL: the page names a view and the engine builds the element.",
        )
        # ⚠️ THE CASE WHERE A MARKER MATTERS MOST: the slot EXISTS, so an author
        # reading the page has every reason to think the embed is merely slow.
        return _dead(
            "view '" + slot + "' is not on an allow-listed host ("
            + ", ".join(hosts) + "), so it was not embedded.",
            _DEAD_LABEL,
        )

    # ⚠️ REPORTED RATHER THAN SILENTLY EATEN. `caption:` was removed 2026-08-30;
    # a key that quietly does nothing is the shape PR #197 fixed one day earlier.
    if had_caption:
        state.note(
            "notes",
            src + ": `views: " + slot + "` declares `caption:`, which was REMOVED "
            "on 2026-08-30 and does nothing. Delete the line. The engine does not "
            "write prose onto a page; if a note belongs there, type it above the "
            "directive.",
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
    # ✅ A CONTROL, NOT NARRATION. Always rendered: an iframe prints blank, and on
    # screen this is the answer to "the table did not load." Its words are the
    # author's `text:`, never the engine's.
    fallback = (
        '<p class="dr-view__fallback"><a href="' + _esc(url) + '">'
        + _esc(label) + "</a></p>"
    )
    return '<div class="dr-view">' + frame + fallback + "</div>"


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
