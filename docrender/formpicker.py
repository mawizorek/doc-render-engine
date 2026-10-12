"""`!!! formpicker "slot"` -- ONE generic form, every program in a menu.

    forms:
      completion:
        src: https://forms.clickup.com/36074068/f/...?Program_ID=ITPSAFE-1336
        text: Program completion form

    !!! formpicker "completion"

A staff surface. Michael, 2026-10-12: *"just a staff quick link (mostly me) i put
form for any student completing a form"*, and the rule that makes the menu
decidable: *"form ids only exist once they have a real canonical clickup program
id"*.

🔴 **EVERY ARGUMENT LIVES IN `docrender/formpicker-dl.md`.** Warnings stay here;
why a warning exists is one file over. `forms.py` crossed the 22,528 B read
ceiling four times by holding its own reasoning. Do not repeat that here.

=============================================================================
⭐ THE MENU IS DERIVED, NEVER DECLARED
=============================================================================
There is no `programs:` key and there is no registry file. Every program page
ALREADY states its own `Program_ID=` inside its `forms:` src, so this module
reads the build it is already part of. 🚫 A hand-maintained list would be a
second claimant on a fact each page already owns -- the defect that retired
`roster.json`, `registry.json` and `app-index.md`.

⭐ MICHAEL'S RULE IS THE MEMBERSHIP TEST, VERBATIM. A `Program_ID=` only exists
once a canonical ClickUp program exists, so "carries a Program_ID" IS "is a real
program" and nothing here has to decide that separately.

=============================================================================
🔴 THE STANDING TRAPS -- warnings only. Arguments: `formpicker-dl.md`.
=============================================================================
🔴 **THE FRAME IS `forms.py`'s, NOT THIS MODULE'S.** This module renders a
`<select>` and delegates to `forms._html` for the embed. ⚠️ Every iframe trap
lives there -- the scroll WINDOW is the wrapper never the frame, the CDN height
script, the `!important` print rules, the always-rendered fallback. 🚫 Do not
grow a second iframe renderer here: two renderers of one object disagree within
a month.

🚨 **AND DELEGATING THE FRAME MEANS INHERITING ITS PAGE-LEVEL ASSETS BY HAND.**
`forms.on_page_markdown` appends the CDN height script, the print CSS and the
Reload listener only when ITS OWN directive matched, so a page whose only embed
came from a picker would ship a frame with **no dynamic height, no print rules
and a Reload button bound to nothing** -- three silent failures, one of which
prints a whole iframe onto paper. `_inherit` below appends whichever are missing.
⚠️ IT TESTS FOR PRESENCE because a page may carry both directives, and this stage
runs AFTER forms in `hooks/05b_program.py`. 🚫 Never copy those three constants
here; import them, or they drift.

🔴 **NO `Program_ID=` ON THE BASE MEANS NO MENU AT ALL, AND THAT IS A REFUSAL
RATHER THAN A WARNING.** The swap rewrites an EXISTING parameter; it does not
append one, because appending would have to guess `?` versus `&` and would still
leave the arrival state unattributed. So a base without the parameter renders the
plain form and the menu is withheld. ⚠️ Rendering the `<select>` anyway was the
first version's behaviour and it is the exact dead control this engine kills on
sight: every pick appears to work and changes nothing. ⭐ `forms.py` files its own
compliance note on the same page, and the two are different facts -- that one says
submissions match no program, this one says the control was not offered.

🔴 **THE PAGE'S OWN src IS EXCLUDED FROM THE WALK.** Without that the picker's
default id is found twice -- once on the program that owns it, once here -- and
reported as a duplicate on every build. ⚠️ Any OTHER page embedding a program's
form is still reported, and that one is a real finding.

🔴 **A COLLISION IS BROKEN BY `type: program`, NEVER BY FILENAME ORDER.** The
first version of this module kept whichever page the sorted walk reached first,
so which page owned a Program_ID depended on its path -- something no author
thinks about and nothing in the report explained. A program page owns its own
completion form; a page that merely embeds one is the interloper. ⚠️ Two REAL
programs sharing an id still fall back to walk order, and that case is the one
worth reading the report for.

🔴 **SWAP BY `cloneNode` + `replaceWith`, NEVER `iframe.src =`.** Same ruling as
the Reload button: assigning `src` navigates the browsing context and pushes a
session-history entry, so after three picks the Back button walks iframe states.

⚠️ **UNPUBLISHED PAGES ARE ABSENT BY CONSTRUCTION.** Membership is `id in
state.PAGES`, which is the map built AFTER visibility prunes, so a draft
program cannot leak its title into a menu. 🚫 Do not switch this to `BY_SRC`
alone for "completeness" -- that reads frontmatter that was never published.

⚠️ **NOTHING HERE PROVES A PROGRAM_ID IS LIVE.** It proves a string is in a
page's frontmatter. A retired ClickUp program keeps rendering a confident option.
"""

from __future__ import annotations

import re

from . import forms, state
from .util import directive_options, sub_outside_code

#: `!!! formpicker "slot"` plus optional trailing `key=value` options.
#: Same shape as `forms._FORM`, including the trailing group that file's own
#: header records as a silent bug when it was missing.
_PICK = re.compile(
    r'(?m)^[ \t]*!!![ \t]+formpicker[ \t]+"([^"\n]+)"(?P<opts>[^\n]*)$'
)

#: 🚫 NO MEDIA VOCABULARY, for `forms.py`'s reason: a picker is a screen control
#: and never appears on paper. `align` is the only option and `util` validates it.
_LEGAL_OPTS: tuple = ()

#: The parameter that IS the record. Matched on `?` or `&` so a form id that
#: merely contains the words cannot be mistaken for the query parameter.
_PID = re.compile(r"[?&]Program_ID=([^&#]+)")

_PROMPT = "Record a completion for"


def _anchor(slot: str) -> str:
    """The id tying this picker's <label> to its <select>.

    One function owns the spelling, for `forms.slot_anchor`'s reason: a label
    whose `for` matches no element is not an error anywhere, it just silently
    stops being a label.
    """
    return "dr-pick-" + re.sub(r"[^A-Za-z0-9_-]+", "-", str(slot)).strip("-")


def catalog(skip: str = "") -> tuple:
    """Every published page carrying a `Program_ID=`, plus the id collisions.

    Returns `(rows, dupes)`. A row is `{"pid", "title", "id", "program"}`;
    `dupes` maps a Program_ID to the page ids claiming it, WINNER FIRST.

    ⭐ PUBLIC AND SORTED BY TITLE, which is the order a human scans. Sorting by
    Program_ID would order the menu by the accident of when each program task was
    created in ClickUp.

    ⚠️ `skip` IS THE PICKER'S OWN src. See THE STANDING TRAPS.
    """
    claims: dict = {}
    for src, meta in sorted((state.BY_SRC or {}).items()):
        if src == skip or not isinstance(meta, dict):
            continue
        page_id = str(meta.get("id", "")).strip()
        if not page_id or page_id not in (state.PAGES or {}):
            continue
        block = meta.get("forms")
        if not isinstance(block, dict):
            continue
        for raw in block.values():
            if isinstance(raw, str):
                url = raw.strip()
            elif isinstance(raw, dict):
                url = str(raw.get("src", "")).strip()
            else:
                continue
            match = _PID.search(url)
            if not match:
                continue
            pid = match.group(1).strip()
            if not pid:
                continue
            held = claims.setdefault(pid, [])
            if any(c["id"] == page_id for c in held):
                # One page declaring two slots on one program is not a
                # collision; it is one program, named twice.
                continue
            held.append({
                "pid": pid,
                "title": str(meta.get("title", "")).strip() or page_id,
                "id": page_id,
                "program": str(meta.get("type", "")).strip() == "program",
            })

    rows: list = []
    dupes: dict = {}
    for pid, candidates in claims.items():
        # ⭐ THE PROGRAM PAGE WINS. See THE STANDING TRAPS.
        programs = [c for c in candidates if c["program"]]
        winner = (programs or candidates)[0]
        rows.append(winner)
        if len(candidates) > 1:
            dupes[pid] = [winner["id"]] + [
                c["id"] for c in candidates if c["id"] != winner["id"]
            ]
    return (sorted(rows, key=lambda r: (r["title"].lower(), r["pid"])), dupes)


def _select(slot: str, rows: list, current: str) -> str:
    """The menu itself, with `current` pre-selected if it is in the list."""
    options = []
    for row in rows:
        options.append(
            '<option value="' + forms._esc(row["pid"]) + '"'
            + (" selected" if row["pid"] == current else "")
            + ">" + forms._esc(row["title"] + " (" + row["pid"] + ")")
            + "</option>"
        )
    ident = _anchor(slot)
    return (
        '<p class="dr-pick__tools">'
        '<label class="dr-pick__label" for="' + ident + '">'
        + forms._esc(_PROMPT) + "</label> "
        '<select class="dr-pick__select" id="' + ident + '">'
        + "".join(options) + "</select></p>"
    )


def _html(src: str, slot: str, opts=None) -> str:
    """The picker, or whatever `forms._html` said when the slot is unusable."""
    embed = forms._html(src, slot, opts)
    # 🔴 A DEAD SLOT IS PASSED STRAIGHT THROUGH. forms.py already rendered the
    # struck-through span and filed the finding; wrapping a menu around a form
    # that does not exist would offer a control that cannot work.
    if "<iframe" not in embed:
        return embed

    rows, dupes = catalog(skip=src)

    for pid in sorted(dupes):
        state.note(
            "notes",
            src + ': `!!! formpicker "' + slot + '"` found Program_ID ' + pid
            + " on more than one page: " + ", ".join(dupes[pid])
            + ". The first is the menu entry and the rest are not offered -- two"
            " pages claiming one program is how a completion lands against the"
            " wrong one.",
        )

    if not rows:
        state.note(
            "notes",
            src + ': `!!! formpicker "' + slot + '"` found no published page'
            " carrying a `Program_ID=` parameter, so there is nothing to pick"
            " between. The plain form is rendered instead.",
        )
        return embed

    entry = forms._entry(src, slot) or ("", "", "", True, "")
    found = _PID.search(entry[0] or "")
    if not found:
        # 🔴 WITHHELD, NOT RENDERED BROKEN. See THE STANDING TRAPS.
        state.note(
            "notes",
            src + ': `!!! formpicker "' + slot + '"` needs a `Program_ID=`'
            " parameter on its own `forms: " + slot + "` src -- the menu"
            " REWRITES that parameter and cannot append one. No menu was"
            " offered; the plain form is rendered. Point the slot at the"
            " program you record most often.",
        )
        return embed
    current = found.group(1).strip()
    if current and not any(row["pid"] == current for row in rows):
        state.note(
            "notes",
            src + ': `!!! formpicker "' + slot + '"` defaults to Program_ID '
            + current + ", which no published page declares. The menu still"
            " works; the form on ARRIVAL -- and with JavaScript off -- records"
            " against that id.",
        )

    classes = "dr-pick"
    if (opts or {}).get("align"):
        classes += " dr-pick--align-" + opts["align"]
    shown = next((r["title"] for r in rows if r["pid"] == current), "")
    now = (
        '<p class="dr-pick__now">Selected: <span class="dr-pick__nowtext">'
        + forms._esc(shown or "none") + "</span></p>"
    )
    return (
        '<div class="' + classes + '">' + _select(slot, rows, current)
        + now + embed + "</div>"
    )


#: ONE DELEGATED LISTENER PER PAGE.
#:
#: 🔴 `cloneNode` + `replaceWith`, NEVER `f.src = u` -- see THE STANDING TRAPS.
#: ⚠️ `closest` AND `classList` ARE BOTH GUARDED: `e.target` on a change event
#: can be a node without either, and a handler that throws on one stray event is
#: worse than one that does nothing.
#: ⭐ THE FALLBACK ANCHOR IS RETARGETED TOO. It is the control that works when the
#: frame does not, so leaving it pointed at the default would hand somebody the
#: wrong program precisely when they already have a problem.
_PICK_JS = (
    "<script>document.addEventListener('change',function(e){"
    "var t=e.target;"
    "if(!t||!t.classList||!t.classList.contains('dr-pick__select'))return;"
    "if(!t.closest)return;"
    "var w=t.closest('.dr-pick');if(!w)return;"
    "var o=w.querySelector('iframe');if(!o)return;"
    "var v=t.value;if(!v)return;"
    "var u=(o.getAttribute('src')||'').replace("
    "/([?&]Program_ID=)[^&#]*/,'$1'+encodeURIComponent(v));"
    "var f=o.cloneNode(false);f.setAttribute('src',u);o.replaceWith(f);"
    "var a=w.querySelector('.dr-form__fallback a');"
    "if(a)a.setAttribute('href',u);"
    "var n=w.querySelector('.dr-pick__nowtext');"
    "if(n)n.textContent=t.options[t.selectedIndex].text;"
    "});</script>"
)

#: Inline, once per page, for `forms.py`'s reason: `assets/flow.css` owns the
#: `.dr-*` families and is past the read ceiling, so it cannot be rewritten
#: safely. 🚩 These move there after the split its own header prescribes.
#:
#: 🔴 EVERY PRINT `display` DECLARATION IS `!important` ON PURPOSE.
#: `print-flow.css` sets `display: revert !important` on every direct child of a
#: `<details>`, and importance beats specificity, so a plain `display: none`
#: LOSES inside a folded form. 🔴 WeasyPrint discards `display: revert` as
#: invalid, so the print harness passes while Chrome prints the menu.
#:
#: ⭐ THE SELECT IS HIDDEN ON PAPER AND THE SELECTION IS NOT. A dropdown prints
#: as a grey box saying nothing; the line naming the chosen program is the only
#: part of this control that means anything once printed.
_PICK_CSS = (
    "<style>.dr-pick__tools{margin:.6rem 0 .2rem}"
    ".dr-pick__label{font-size:.78rem;font-weight:600;"
    "color:var(--md-default-fg-color--light)}"
    ".dr-pick__select{font:inherit;font-size:.82rem;padding:.25rem .4rem;"
    "border:1px solid var(--dr-border,var(--md-default-fg-color--lighter));"
    "border-radius:.25rem;background:var(--md-default-bg-color);"
    "color:var(--md-default-fg-color);max-width:100%}"
    ".dr-pick__now{margin:0 0 .5rem;font-size:.75rem;"
    "color:var(--md-default-fg-color--light)}"
    "@media print{"
    ".dr-pick__tools,.md-typeset .dr-pick__tools{display:none !important}"
    ".dr-pick__now,.md-typeset .dr-pick__now{display:block !important}"
    "}</style>"
)


def on_page_markdown(markdown, page, config, files):
    """Replace each `!!! formpicker "slot"` and load the helper once per page.

    ⚠️ `sub_outside_code` IS NOT OPTIONAL: the page documenting this directive
    contains this directive.

    ⭐ THE SCRIPT AND STYLE ARE GATED ON A MENU HAVING RENDERED, not on the
    directive having matched. A page whose slot was dead gets neither, because a
    listener with nothing to bind and a rule with nothing to paint are both dead
    controls -- and `forms.py` records what a print rule riding in the wrong
    block already cost this engine once.
    """
    if "!!!" not in markdown:
        return markdown

    src = getattr(page.file, "src_uri", "")
    picked = []

    def swap(match):
        slot = match.group(1).strip()
        opts, problems = directive_options(match.group("opts"), _LEGAL_OPTS)
        for problem in problems:
            state.note(
                "notes",
                src + ': `!!! formpicker "' + slot + '"` carries ' + problem,
            )
        html_out = _html(src, slot, opts)
        if "dr-pick__select" in html_out:
            picked.append(1)
        return "\n\n" + html_out + "\n\n"

    out = sub_outside_code(_PICK, swap, markdown)
    if picked:
        out += "\n" + _PICK_CSS + "\n" + _PICK_JS + "\n"
        out = _inherit(out)
    return out


def _inherit(out: str) -> str:
    """Append the page-level assets `forms.py` owns, if they are not here yet.

    🚨 See THE STANDING TRAPS. Three facts, three separate gates, deliberately:
    the height script needs a ClickUp frame, the print rules need ANY frame, and
    the listener needs a Reload button. `forms.py` records what collapsing the
    last two into one block already cost -- a page setting `reload: false`
    printed its entire iframe.
    """
    if "clickup-embed" in out and forms._FORM_SCRIPT not in out:
        out += '\n<script async src="' + forms._FORM_SCRIPT + '"></script>\n'
    if "<iframe" in out and forms._RESET_CSS not in out:
        out += "\n" + forms._RESET_CSS + "\n"
    if "dr-form__reset" in out and forms._RESET_JS not in out:
        out += "\n" + forms._RESET_JS + "\n"
    return out
