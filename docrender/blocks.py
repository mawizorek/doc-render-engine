"""BLOCK FAMILY COLOURS -- generated CSS for the `!!!` and `???` callouts.

Not a hook. `build_css()` is called by docrender/assets.py and published as
`blocks.css`, exactly like markers.py's marker-class sheet.

    theme/blocks.tsv     the thirteen families. ADDING OR RECOLOURING ONE IS A
                         ROW THERE -- no code change, no CSS change.
    docs/CALLOUTS.md     WHY any of this is the way it is: Material's five
                         hardcoded surfaces, the focus-ring measurements, the
                         specificity argument, and two post-mortems.

⚠️ READ docs/CALLOUTS.md BEFORE CHANGING A SELECTOR OR A COLOUR CONSTRUCTION
HERE. This file used to carry all of that inline and reached 27,655 B against a
22,528 B hard read limit -- so the argument moved and only what an editor of the
EMITTER needs stayed. The trade is that a decision you disagree with is one file
away rather than in front of you, and it has almost certainly already been
measured.

=============================================================================
THE FOUR THINGS THAT WILL BITE SOMEBODY EDITING THIS FILE
=============================================================================

1 · SPECIFICITY. Every rule below matches Material's own selectors at (0,3,0) and
    wins on SOURCE ORDER, because our sheets load after `main.css`. ⚠️ That is a
    TIE and it is the only honest name for it -- there is nothing to delete.
    ⭐ THE PER-FAMILY FOCUS RULES ARE THE EXCEPTION: `.admonition.good:focus-
    within` carries one more class, so (0,4,0) beats Material outright and does
    not depend on load order. The BASE focus rule in build_css does tie.

2 · EVERY COLOUR CARRIES A FALLBACK INSIDE THE `var()`, and that is a mechanism
    rather than caution. A property invalid at computed-value time is set to
    `unset`, and earlier declarations in the same rule are DISCARDED rather than
    used -- so writing a plain `border-color` above a `var()` one does nothing.
    `var(--dr-x, currentColor)` is the only thing that works. On a nine-token
    local theme nine families name a token that is never emitted, and the icon is
    a MASK painted by `background-color`, so no colour means NO ICON.

3 · THE `details` SELECTORS ARE DEFENSIVE AND UNVERIFIED. Every rule is emitted
    for both `.admonition.<name>` and `details.<name>`. A selector that matches
    nothing costs a few bytes; a missing one costs a family that quietly stays
    blue.

4 · ROWS ARE INHERITED OR DECLARED, and only a DECLARED one needs an `icon`.
    Material's base rule sets the note pencil unconditionally, so a family it has
    never heard of wears the WRONG glyph rather than none. `_icon` reports that.

⚠️ AND A ROW HERE IS HALF THE JOB: template-docs `authoring/writing.md` is what
authors read and it does NOT derive from this file. On 2026-08-05 twelve governed
families shipped and that page told authors there were three, for four hours.
"""

from __future__ import annotations

from . import state
from .markers import _TOKEN, _known_tokens
from .util import load_tsv

#: Every property Material hardcodes on the admonition BOX, and the token that
#: should supply it. Structure, not colour -- the per-family colours are the
#: table's job.
#:
#: ⚠️ `font-size` IS THE ONE VISIBLE CHANGE NOBODY ASKED FOR. Material sets
#: 0.64rem, far below body text here; eos's `fs-sm` is 0.82rem against a 0.9rem
#: body. Callouts get bigger and sit just under the prose instead of looking like
#: a footnote. Stated so it is not mistaken for a regression.
_BOX = (
    ("border-width", "border-w", "1.5px"),
    ("border-radius", "radius-lg", "4px"),
    ("font-size", "fs-sm", "0.64rem"),
)

#: 🔴 THE TRANSITION, WHICH THIS FILE ONCE CLAIMED WAS ALREADY HANDLED.
#:
#: The old comment read: "a shadow and a transition, both of which Material states
#: as its own variables -- so those are mapped in chrome.css and NOT restated
#: here." HALF RIGHT, which is worse than wrong: `box-shadow: var(--md-shadow-z1)`
#: genuinely is a variable and genuinely is mapped; `transition: box-shadow 125ms`
#: is a bare literal chrome.css never touched. ⚑ A sentence true about one of two
#: things it names reads as verified, so nobody checks the other half.
#:
#: Fallbacks are Material's own literals: a bare `var()` inside `transition` is
#: invalid at computed-value time, which drops the property on local-theme sites.
_TRANSITION = (
    "  transition: box-shadow var(--dr-motion-fast, 125ms)"
    " var(--dr-ease, linear);"
)

#: The focus ring width.
#:
#: ⚠️ AN HONEST GAP, NOT AN OVERSIGHT. No token in any vector expresses a ring
#: width. `border-w` is the obvious candidate and is WRONG -- a hairline at
#: 1-1.5px would make the ring vanish. Naming a token that means something else to
#: avoid a literal is the bridge-row mistake PR #82 had to revert. 0.2rem is
#: Material's own 4px, kept.
_RING_W = "0.2rem"

#: What a family falls back to when its token is not emitted by the active theme.
#: `currentColor` rather than `accent`: accent would paint all nine unemitted
#: families identically and claim a family meaning that is not there, where
#: currentColor says plainly "no colour here" and still draws the icon.
_FALLBACK = "currentColor"

#: The twelve families Material ships, in its own order.
#:
#: ⭐ ONE CONSTANT, TWO QUESTIONS, deliberately rather than thriftily. It is the
#: set of legal `icon` values -- Material emits `--md-admonition-icon--<name>` for
#: exactly these -- AND it is how this module tells an INHERITED row from a
#: DECLARED one. A second list for the second question would be a second place
#: stating one fact, the defect this repo has killed in tokenaudit's sheet list,
#: three JSON manifests and the marker validator.
_MATERIAL = (
    "note", "abstract", "info", "tip", "success", "question",
    "warning", "failure", "danger", "bug", "example", "quote",
)

#: `mask-image`, both spellings, PREFIX FIRST.
#:
#: 🔴 NOT COURTESY. Unprefixed `mask-image` needs Safari 16.4; below that the
#: declaration is dropped, the mask is gone, and the ::before paints its full
#: background-color as a solid 20x20px square -- the exact failure `_icon` refuses
#: a bad NAME to prevent, arriving from a CORRECT name on an old browser.
#: Material's compiled stylesheet emits both, which is where this was read from.
#:
#: Prefix first: a browser understanding both takes the later unprefixed line; one
#: understanding only the prefix ignores what it cannot parse. Reversed, the old
#: browser would win.
_MASK = ("-webkit-mask-image", "mask-image")


def _rows() -> list[dict]:
    return load_tsv(state.ENGINE_ROOT / "theme" / "blocks.tsv")


def _colour(value: str, where: str, tokens: set[str], report: bool = True) -> str:
    """Resolve a `color` cell to something CSS can use, WITH a fallback.

    ⚠️ Deliberately NOT markers._colour, which is the same question with a
    different answer -- theirs has no fallback by design, and routing callouts
    through it would cost 10 of 12 families their icons on 3 of 4 sites. Importing
    it is what broke the build on 2026-08-05; see docs/CALLOUTS.md. The token LIST
    is still shared, because "which names exist" has exactly one correct answer.

    `report` is False at the build_css call site because assets._plan runs from
    BOTH on_config and on_files, so anything reported there is reported twice.
    `report()` below is the single honest complaint.
    """
    value = (value or "").strip()
    if not value:
        return _FALLBACK
    # Anything that is not a bare word -- #hex, oklch(...), rgb(...) -- passes
    # through as written. Same rule as markers.py, same regex, imported not
    # retyped.
    if not _TOKEN.match(value):
        return value
    if value in tokens:
        return "var(--dr-" + value + ", " + _FALLBACK + ")"
    if report:
        state.note(
            "notes",
            where + " asks for colour token '" + value + "', which is in neither "
            + "theme/colors.tsv nor theme/canonical/colors.tsv. Using the body "
            + "colour, so the family renders monochrome rather than invisibly.",
        )
    return _FALLBACK


def _wash(value: str) -> str:
    """The title bar tint: Material's 10% alpha, computed one layer later.

    Material does it at build time from a Sass colour; a custom property is not
    known until the browser resolves it, so `color-mix` does the same job one
    layer later. `in oklch` matches base.css's marker chips.

    🚫 DO NOT REUSE THIS FOR THE FOCUS RING. It was used there and measured
    1.12:1 against a 3.0 floor -- a 10% mix is 90% its own ground BY
    CONSTRUCTION, which is right for a tint behind bold text and useless for an
    indicator. Full table in docs/CALLOUTS.md.
    """
    return "color-mix(in oklch, " + value + " 10%, transparent)"


def _ring(value: str) -> str:
    """The focus ring for one family, at FULL STRENGTH.

    ⚠️ The strength is the decision and it is measured, not preferred. Material's
    10% alpha gives 1.12 dark / 1.13 light against WCAG 1.4.11's 3.0, and nothing
    below 100% clears both schemes because `text-faint` is a grey sitting near its
    own ground by design. The full-strength numbers are the ones this repo already
    holds the BORDER to. See docs/CALLOUTS.md.
    """
    return "  box-shadow: 0 0 0 " + _RING_W + " " + value + ";"


def _icon(name: str, icon: str, report: bool = True) -> str:
    """The mask declarations for one family, or "" to leave Material's.

    Returns COMPLETE CSS lines -- both spellings, newline separated -- so the
    caller extends a declaration list rather than concatenating a conditional into
    a string. See build_css.

    THREE CASES, and only one emits anything:

      inherited row, no icon    Material keys its own icon off the class name.
                                Nothing to do, nothing to say.
      DECLARED row, no icon     ⚠️ REPORTED. Material's base rule sets the note
                                pencil unconditionally, so this family wears the
                                WRONG glyph rather than none.
      icon names a non-family   ⚠️ REFUSED and reported. An undefined var with no
                                fallback removes the mask entirely and leaves the
                                ::before painting a solid 20x20px square. Keeping
                                the pencil is wrong and legible; the square is
                                wrong and alarming.
    """
    icon = (icon or "").strip()

    if not icon:
        if name not in _MATERIAL and report:
            state.note(
                "notes",
                "block '" + name + "' is not one of Material's families and "
                + "names no `icon`, so it inherits the NOTE PENCIL from "
                + "Material's base rule -- a wrong glyph, not a missing one. "
                + "Borrow one by naming a Material family in the icon column: "
                + ", ".join(_MATERIAL) + ".",
            )
        return ""

    if icon not in _MATERIAL:
        if report:
            state.note(
                "notes",
                "block '" + name + "' names icon '" + icon + "', which Material "
                + "does not define. REFUSED: emitting it would give an undefined "
                + "var() with no fallback, removing the mask entirely and "
                + "painting a solid square instead of a glyph. Keeping "
                + "Material's default. Valid: " + ", ".join(_MATERIAL) + ".",
            )
        return ""

    return "\n".join(
        "  " + prop + ": var(--md-admonition-icon--" + icon + ");"
        for prop in _MASK
    )


def _selectors(name: str) -> tuple[str, str, str, str, str]:
    """(box, focus, title, icon, marker) selector lists for one family.

    Both spellings of every selector, always -- see point 3 in the module
    docstring. `focus` is (0,4,0) and wins outright; the rest tie at (0,3,0).
    """
    box = (
        ".md-typeset .admonition." + name + ",\n"
        ".md-typeset details." + name
    )
    focus = (
        ".md-typeset .admonition." + name + ":focus-within,\n"
        ".md-typeset details." + name + ":focus-within"
    )
    title = (
        ".md-typeset ." + name + " > .admonition-title,\n"
        ".md-typeset ." + name + " > summary"
    )
    icon = (
        ".md-typeset ." + name + " > .admonition-title::before,\n"
        ".md-typeset ." + name + " > summary::before"
    )
    marker = (
        ".md-typeset ." + name + " > .admonition-title::after,\n"
        ".md-typeset ." + name + " > summary::after"
    )
    return box, focus, title, icon, marker


def build_css(report: bool = False) -> str:
    """One rule set per block family, plus the shared box structure.

    `report` defaults False because assets._plan is called from BOTH on_config
    and on_files, so anything reported here is reported twice. Same guard, same
    reason, as markers.build_css().
    """
    tokens = _known_tokens()
    rows = [r for r in _rows() if (r.get("block") or "").strip()]

    out = [
        "/* GENERATED by docrender/blocks.py -- do not edit.",
        "   One rule set per family, from theme/blocks.tsv.",
        "   Beats Material's flavour rules on source order at equal",
        "   specificity (0,3,0); the per-family FOCUS rules are (0,4,0) and",
        "   win outright. Argument in docs/CALLOUTS.md.",
        "   Every colour carries a currentColor fallback: the icon is a mask",
        "   painted by background-color, so an unresolved token would not be",
        "   a wrong colour, it would be no icon. */",
        "",
    ]

    # THE BOX, every family at once. Material hardcodes all of these.
    #
    # `box-shadow` is NOT restated: Material reads --md-shadow-z1, which
    # chrome.css maps to elev-1. One surface, one address. The TRANSITION on that
    # shadow IS a literal and is handled here -- see `_TRANSITION`.
    box_decls = [
        "  " + prop + ": var(--dr-" + token + ", " + fallback + ");"
        for prop, token, fallback in _BOX
    ]
    box_decls.append(_TRANSITION)
    out.append(
        ".md-typeset .admonition,\n.md-typeset details {\n"
        + "\n".join(box_decls)
        + "\n}"
    )
    out.append("")

    # ⭐ THE BASE RING, for a family with no row in the table. Material's base
    # rule is hardcoded blue, so without this an undeclared word gets an indigo
    # flash. `accent` is the honest choice: it says "this site" rather than
    # claiming a family meaning. ⚠️ (0,3,0) -- level with Material, taken on
    # SOURCE ORDER. The per-family rules below do not depend on load order.
    out.append(
        ".md-typeset .admonition:focus-within,\n"
        ".md-typeset details:focus-within {\n"
        + _ring(_colour("accent", "the base focus ring", tokens, report=False))
        + "\n}"
    )
    out.append("")

    for row in rows:
        name = (row.get("block") or "").strip()
        value = _colour(
            (row.get("color") or "").strip(),
            "block '" + name + "'",
            tokens,
            report=report,
        )
        box, focus, title, icon, marker = _selectors(name)

        # ⭐ A LIST OF COMPLETE LINES, NOT A CONCATENATED STRING. The icon rule
        # carries one declaration or three depending on the row, and joining a
        # conditional into a string is where a missing semicolon merges two
        # properties into one invalid declaration. Whole lines cannot do that --
        # which is why adding the `-webkit-` spelling later cost one line.
        icon_decls = ["  background-color: " + value + ";"]
        borrowed = _icon(name, row.get("icon", ""), report=report)
        if borrowed:
            icon_decls.append(borrowed)

        out += [
            box + " {\n  border-color: " + value + ";\n}",
            focus + " {\n" + _ring(value) + "\n}",
            title + " {\n  background-color: " + _wash(value) + ";\n}",
            icon + " {\n" + "\n".join(icon_decls) + "\n}",
            marker + " {\n  color: " + value + ";\n}",
            "",
        ]

    return "\n".join(out) + "\n"


def report() -> None:
    """Say which families are governed, once, from a caller that runs once.

    Separate from build_css for the double-call reason above. Called by hooks/01d
    via the token audit, the one place that already runs exactly once per build.

    ⭐ INHERITED AND DECLARED ARE COUNTED SEPARATELY, because they carry different
    risk. An inherited family is Material's vocabulary and gets its icon for free;
    a declared one is ours and is one blank cell away from wearing the note
    pencil. A single total would hide the number that matters.
    """
    tokens = _known_tokens()
    inherited = []
    declared = []
    for row in _rows():
        name = (row.get("block") or "").strip()
        if not name:
            continue
        _colour((row.get("color") or "").strip(), "block '" + name + "'", tokens)
        _icon(name, row.get("icon", ""))
        (inherited if name in _MATERIAL else declared).append(name)

    if not inherited and not declared:
        return

    message = (
        "blocks: " + str(len(inherited) + len(declared))
        + " callout families governed by theme/blocks.tsv -- "
        + str(len(inherited)) + " inherited from Material ("
        + ", ".join(sorted(inherited)) + ")"
    )
    if declared:
        message += (
            ", " + str(len(declared)) + " declared here ("
            + ", ".join(sorted(declared)) + "), each borrowing a Material icon"
        )
    state.note("notes", message + ".")
