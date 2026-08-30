"""The `views:` registry -- an embedded ClickUp VIEW, named once in frontmatter.

    views:
      recently-created:
        src: https://sharing.clickup.com/36074068/l/h/12cwjm-61513/486ae60bf886d69
        text: Recently created notes
        collapsed: true      # optional; REQUIRES text: -- see below
        height: 700px        # optional, defaults to 700px

    !!! view "recently-created"
    !!! view "recently-created" align=center

✅ WORKS ON ANY SITE WITH NO CONFIGURATION.

🔴 WHY ANY OF THIS IS THE WAY IT IS: `docrender/views-dl.md`. Read it before
changing behaviour here -- every rule below traces to a specific correction, and
four of them were Michael correcting this module in its first three days.
The standing law that came out of them:

    THE ENGINE EMITS STRUCTURE. THE AUTHOR DECIDES CONTENT.

So: no captions, no engine-authored labels, no default summary text. A frame, a
link, a failure marker. That is the whole vocabulary.

🚫 NOT A HOOK. `forms.py` owns the only registration and calls in; `_esc` and
`_dead` are imported from it. One hook keeps this feature out of `mkdocs.yml`
(28,158 B, unreadable whole). ⚠️ `forms.py` imports this module INSIDE its hook
function while this one imports from `forms` at module top -- deliberate, not a
cycle, and not tidy-able in either direction. views-dl.md D2.

⚠️ ONLY THE `src=` URL GOES IN THE FRONTMATTER, never the whole `<iframe>`.
⚠️ THE HOST IS CHECKED AND THAT IS ALL. Nothing here can prove a view is still
shared, still exists, or shows what its author thinks. A revoked share renders an
empty frame with NO build finding -- the fallback link is the only thing that
distinguishes "loading" from "gone."

🔴 `align=` MOVES THE FURNITURE, NOT THE FRAME, AND THAT IS PHYSICS RATHER THAN A
CHOICE: the iframe is `width: 100%`, so it has no slack to be moved within. What
aligns is the summary label and the fallback link. ⭐ The argument, the silent-regex
incident behind it and the shared parser live in **`forms-dl.md`**, under the
`align=` heading -- ONE claimant for a fact that spans both modules, rather than a
half-copy here that drifts.
"""

from __future__ import annotations

import re

from . import state
from .forms import _dead, _esc
from .util import directive_options, sub_outside_code

#: `!!! view "slot"` plus optional trailing `key=value` options.
#:
#: 🔴 THE TRAILING GROUP IS THE 2026-08-30 BUG FIX AND IT WAS A SILENT ONE. This
#: pattern anchored `"[ \t]*$` straight after the closing quote, so
#: `!!! view "x" align=center` did not match AT ALL -- the directive was left as
#: literal text on the page with NOTHING in the build report, because nothing had
#: matched to report on. ⚠️ A guard placed inside `_html` cannot see what the
#: pattern turned away. Full incident: `forms-dl.md` under `align=`.
_VIEW = re.compile(
    r'(?m)^[ \t]*!!![ \t]+view[ \t]+"([^"\n]+)"(?P<opts>[^\n]*)$'
)

#: Where ClickUp serves a publicly shared view. Read out of a real embed code,
#: not guessed -- a module constant for the same reason `_FORM_HOST` is one, and
#: what makes this work on a brand-new site with no config. views-dl.md D3.
_DEFAULT_HOST = "https://sharing.clickup.com/"

#: ClickUp's own literal for a shared view: their embed code ships a real height
#: and no sizing script, so ours does too. views-dl.md D4.
_DEFAULT_HEIGHT = "700px"

#: A CSS length, loosely. Enough to catch a bare number or a stray unit typo
#: before it reaches an attribute, not a full CSS parser.
_LENGTH = re.compile(r"^\d+(\.\d+)?(px|rem|em|vh|%)$")

#: 🚫 NO MEDIA VOCABULARY HERE. `qr.py` has `display=`/`print=` because a code can
#: legitimately exist in one medium only; an embed always appears on screen and
#: never on paper, so there is nothing to declare. `align` is the only option, and
#: `util.directive_options` validates it.
_LEGAL_OPTS: tuple = ()

_DEAD_LABEL = "View"


def _hosts() -> list:
    """The engine default plus this site's optional extras.

    ✅ ADDITIVE, NOT AN OVERRIDE, and that is the load-bearing word: declaring
    `view_hosts:` to allow a second ClickUp surface must not silently disallow the
    first. ⚠️ Read at CALL time, never cached at import -- `prefixes.py` documents
    the trap: the instance config is populated during the build, so an import-time
    read caches an empty answer for the whole run.
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


def slot_anchor(slot: str) -> str:
    """The id on a collapsed view's `<summary>`.

    ⚠️ THE ANCHOR SITS ON THE `<summary>`, NOT THE `<details>`. A fragment must
    target something INSIDE the disclosure for the HTML spec's auto-expand to
    apply; pointing it at the `<details>` scrolls correctly and stays shut.
    `forms.slot_anchor` records the same trap -- this re-uses its finding.

    ⭐ EMITTED SO AN AUTHOR CAN LINK TO IT (`#dr-view-<slot>`). Nothing in the
    engine links here today; said out loud so nobody hunts for a caller.
    """
    return "dr-view-" + re.sub(r"[^A-Za-z0-9_-]+", "-", str(slot)).strip("-")


def _declared(src) -> list:
    """Every view slot this page declares, sorted. For the diagnosis only.

    ⭐ NAMING WHAT *IS* DECLARED IS MOST OF THE VALUE OF THE MESSAGE -- it turns a
    typo from a hunt into a glance. Precedent: `forms._declared`.
    """
    block = (state.BY_SRC.get(src, {}) or {}).get("views")
    return sorted(str(k) for k in block) if isinstance(block, dict) else []


def _entry(src, slot):
    """One entry out of a page's `views:` map, or None.

    Two spellings, matching `links:` and `forms:`: a bare string is the src, a
    mapping carries `src:`, `text:`, `collapsed:` and `height:`.
    """
    block = (state.BY_SRC.get(src, {}) or {}).get("views")
    if not isinstance(block, dict):
        return None
    raw = block.get(slot)
    if raw is None:
        return None
    if isinstance(raw, str):
        return (raw.strip(), "", False, "", False)
    if isinstance(raw, dict):
        return (
            str(raw.get("src", "")).strip(),
            str(raw.get("text", "")).strip(),
            raw.get("collapsed") is True,
            str(raw.get("height", "")).strip(),
            "caption" in raw,
        )
    return ("", "", False, "", False)


def _height(src, slot, declared) -> str:
    """The frame height: what the page declared, or ClickUp's own default.

    🔴 A BAD VALUE IS REPORTED AND REPLACED, NEVER PASSED THROUGH. `height: 700`
    with no unit is invalid in an attribute and renders a collapsed, invisible
    frame -- the exact invisible-not-broken failure `forms.py` warns about, caught
    here where the fix is one line of frontmatter.
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


def _html(src, slot, opts=None) -> str:
    opts = opts or {}
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
        # indistinguishable from a page that never asked for a view.
        return _dead(
            "view slot not declared on this page: " + slot
            + ". Declared here: " + (", ".join(known) or "nothing") + ".",
            _DEAD_LABEL,
        )

    url, text, collapsed, raw_height, had_caption = entry
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
    # a key that quietly does nothing is this repo's least favourite shape.
    if had_caption:
        state.note(
            "notes",
            src + ": `views: " + slot + "` declares `caption:`, which was REMOVED "
            "on 2026-08-30 and does nothing. Delete the line. The engine does not "
            "write prose onto a page; if a note belongs there, type it above the "
            "directive.",
        )

    # 🔴 A DISCLOSURE NEEDS A LABEL AND THE ENGINE WILL NOT WRITE ONE. `forms.py`
    # can default to "Complete this program" because a completion form has one
    # purpose; a view has none, so naming it would be the engine writing page
    # copy -- the exact thing deleted one day earlier. So it renders OPEN and says
    # why: the frame still appears, nothing is lost, and the note names the fix.
    # views-dl.md D7.
    if collapsed and not text:
        state.note(
            "notes",
            src + ": `views: " + slot + "` asks for `collapsed:` but declares no "
            "`text:`, which is what labels the control. Rendered OPEN instead. "
            "Add a `text:` line and it will collapse -- the engine will not invent "
            "a label for it.",
        )
        collapsed = False

    height = _height(src, slot, raw_height)
    label = text or "Open this view in a new tab"

    # 🚫 `clickup-embed` ONLY. No `clickup-dynamic-height`, and no helper script:
    # ClickUp's own embed code for a view ships a literal height. views-dl.md D4.
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

    # ⭐ THE ALIGNMENT IS A CLASS ON THE WRAPPER, and `assets/align.css` owns what
    # it means -- the same seam `qr.py` uses for `dr-qr--align-*`. An inline style
    # here would be unoverridable by a site's own sheet.
    classes = "dr-view"
    if opts.get("align"):
        classes += " dr-view--align-" + opts["align"]

    if not collapsed:
        return '<div class="' + classes + '">' + frame + fallback + "</div>"

    # ⭐ ZERO JAVASCRIPT. Per the HTML spec a fragment targeting content inside a
    # closed <details> expands it, so `#dr-view-<slot>` opens this. The id is on
    # the <summary> for that reason -- see slot_anchor.
    return (
        '<div class="' + classes + '">'
        '<details class="dr-view__open">'
        '<summary id="' + _esc(slot_anchor(slot)) + '">' + _esc(text) + "</summary>"
        + frame + fallback
        + "</details></div>"
    )


def on_page_markdown(markdown, page, config, files):
    """Replace each `!!! view "slot"` with the embed.

    🔴 NOT A HOOK -- `forms.on_page_markdown` calls this. The signature matches a
    real hook deliberately, so if `forms.py` is ever split for size this becomes
    one registration and no edit.

    ⚠️ `sub_outside_code` IS NOT OPTIONAL. The page that documents this directive
    contains the directive, and `util.py`'s docstring records the first time that
    bit this engine.

    ⚠️ EVERY OPTION PROBLEM IS REPORTED, NEVER DROPPED. `directive_options` is a
    pure function that hands back sentences rather than logging them, so this is
    where they become findings -- and a mistyped option that vanished would leave
    an author staring at an unmoved block with no signal, which is the failure this
    whole change exists to end.

    🚫 NO SCRIPT APPEND, unlike the forms pass. Nothing to size.
    """
    if "!!!" not in markdown:
        return markdown
    src = getattr(page.file, "src_uri", "")

    def swap(match):
        slot = match.group(1).strip()
        opts, problems = directive_options(match.group("opts"), _LEGAL_OPTS)
        for problem in problems:
            state.note(
                "notes",
                src + ': `!!! view "' + slot + '"` carries ' + problem,
            )
        out = _html(src, slot, opts)
        return "\n\n" + out + "\n\n" if out else ""

    return sub_outside_code(_VIEW, swap, markdown)
