"""BLOCK FAMILY COLOURS -- generated CSS for the `!!!` and `???` callouts.

Not a hook. `build_css()` is called by docrender/assets.py and published as
`blocks.css`, exactly like markers.py's marker-class sheet.

Defined in theme/blocks.tsv. Adding or recolouring a family is a row there.

=============================================================================
🔴 THIS FILE KILLED EVERY BUILD ON 2026-08-05, AT IMPORT TIME
=============================================================================

It imported `_token_sets` from markers.py. That function existed only in MY
version of markers.py, on a branch that was closed unmerged (PR #84) after a
parallel session shipped the same features first (#83). Their markers exports
`_known_tokens`. I kept the caller and lost the callee.

An ImportError here is not a render failure -- it is raised while mkdocs VALIDATES
its config, before a single page is read, so `strict: false` and the token audit's
own try/except cannot help. The chain is:

    hooks/01d_audit -> tokenaudit -> assets -> blocks -> markers

⚑ SECOND OCCURRENCE OF ONE SHAPE IN ONE DAY. This morning tokenaudit called
`theme._canonical_row()` after that function moved to vectors.py, with the same
result. A cross-module call whose callee moved. The post-mortem for the first one
was written eight hours before the second one shipped, which is the argument for
a CHECK rather than a lesson.

🔴 AND THE VERIFICATION THAT MISSED IT WAS THE REAL PROBLEM. The generator was
run in a sandbox before shipping and its output checked -- rule count, brace
balance, specificity against Material -- but the test script REIMPLEMENTED
`_colour` rather than importing it. So the logic was proven and the import was
never executed. A test that reimplements its subject tests the reimplementation.

=============================================================================
WHAT MATERIAL DOES, READ OUT OF ITS SOURCE AND NOT REMEMBERED
=============================================================================

`src/templates/assets/stylesheets/main/extensions/markdown/_admonition.scss`:

    $admonitions: ("note": pencil-circle $clr-blue-a200, ...12 entries)

    :root { --md-admonition-icon--#{$name}: svg-load(...) }

    .md-typeset .admonition {
      box-shadow: var(--md-shadow-z1);
      transition: box-shadow 125ms;                    <- A LITERAL
      &:focus-within { box-shadow: 0 0 0 4px rgba($clr-blue-a200, .1) }
    }
    .md-typeset .admonition.#{$name} {
      border-color: $tint;
      &:focus-within { box-shadow: 0 0 0 4px rgba($tint, .1) }
    }
    .md-typeset .#{$name} > .admonition-title {
      background-color: color.adjust($tint, $alpha: -0.9);
      &::before { background-color: $tint; mask-image: ...icon }
      &::after  { color: $tint }
    }

FIVE SURFACES PER FAMILY, all painted from one hardcoded hex: the box border,
the title bar wash at 10% alpha, the ICON (a mask whose colour comes from
`background-color`), the details marker on a collapsible, and THE FOCUS RING.
None of them is a variable, which is the whole reason no theme change has ever
reached a callout.

🔴 READING THE SOURCE IS WHY THE SELECTORS WORKED FIRST TIME. The previous
attempt to beat a Material rule in this engine -- the dark-mode blue link --
shipped against a selector quoted from memory, was wrong in both halves, and
survived a full day because the fix looked structural. A selector stated from
memory is a guess wearing a bracket.

=============================================================================
🔴 THE FOCUS RING: HARDCODED, AND NEVER A FOCUS INDICATOR AT ANY COLOUR
=============================================================================

Found 2026-08-05 while reading this file for an unrelated question. Material
paints the ring TWICE -- base and per flavour -- so tabbing to a `success` box
flashed Material's green rather than the theme's, and `good` (which has no
flavour rule of Material's) flashed BLUE inside a green box.

⭐ THAT HALF IS ORDINARY WIRING. Every family emits its own ring from the same
token that paints its border: one cell, five surfaces. A base rule painted from
`accent` catches any family not in the table, so an undeclared word flashes the
site's own colour instead of Material's indigo.

⚠️ SPECIFICITY, NAMED HONESTLY. Per-family focus is (0,4,0) and beats Material's
(0,3,0) OUTRIGHT. The base rule is (0,3,0) -- a TIE, taken on source order,
exactly like chrome.css's ARMOUR. Two different mechanisms in one sheet and they
are labelled differently on purpose.

🔴 AND THE SECOND HALF IS THE REAL FINDING: THE 10% ALPHA CANNOT WORK.

A 10% mix composites to 90% of the ground it sits on, so it cannot separate from
that ground. That is arithmetic, not a property of any palette. Measured on the
real eos rows against `bg` -- the ring sits OUTSIDE the box, so the page ground is
what it composites over, not the callout:

    alpha   eos dark          eos light
     10%    1.12  FAIL        1.13  FAIL      <- Material's value
     40%    1.82  FAIL        1.69  FAIL
     70%    3.09  pass        2.68  FAIL
    100%    5.06  PASS        4.63  PASS

WCAG 1.4.11 asks 3.0 of a non-text indicator. Nothing below full strength clears
it on both schemes, because the worst case is `text-faint` -- a grey, close to the
ground BY DESIGN, which no opacity can pull away from it.

⚑ SO PORTING THE 10% FAITHFULLY WOULD HAVE WIRED UP A BROKEN VALUE. The ring
takes the token at FULL STRENGTH, justified by the numbers this repo already holds
the BORDER to: accent 7.05/5.84, good 7.27/5.42, bad 5.82/5.05, text-faint
5.06/4.63. One bar, one set of numbers, no new column. ⭐ *An alpha is not a
colour choice, it is a CEILING on how different two things can be* -- and "match
the framework" does not get to be the tie-breaker on a floor this repo has already
written down.

🚫 THE 10% WASH STAYS ON THE TITLE BAR, which is the surface it is right for: a
tint behind bold text, not an indicator that has to be seen from across a room.
Same construction, different job. Do not "fix" that one to match this one.

⚠️ THE RING WIDTH IS A LITERAL AND IS AN HONEST GAP. `_RING_W` is 0.2rem because
no token in any vector expresses a ring width -- `border-w` is a hairline at
1-1.5px and using it would make the ring vanish. Named rather than smuggled into
a token that means something else, which is the bridge-row mistake PR #82 had to
revert.

=============================================================================
THE ICONS ARE MATERIAL'S, AND A DECLARED FAMILY HAS TO BORROW ONE
=============================================================================

Material emits `--md-admonition-icon--<name>` for each of its twelve, and its
BASE rule is unconditional:

    .md-typeset .admonition-title::before {
      background-color: $clr-blue-a200;
      mask-image: var(--md-admonition-icon--note);      <- THE PENCIL
    }

⚠️ SO A FAMILY MATERIAL HAS NEVER HEARD OF DOES NOT LOSE ITS ICON -- IT WEARS
THE PENCIL. That is the harder failure to see: a missing glyph is obvious, a
wrong glyph on a correctly-coloured box reads as a near-miss in the stylesheet
rather than as an unfinished row in a table. `_MATERIAL` below is what lets this
module notice and say so.

⚠️ THE GLYPHS ARE REAL SVG FILES, WHICH IS WHY THE TABLE HOLDS A NAME AND NOT
AN IMAGE. Material's `$admonitions` map pairs each family with an icon NAME
(`note`: pencil-circle, `success`: check), and `svg-load()` inlines that file's
markup into a custom property at ITS build time. So by the time a page renders,
`--md-admonition-icon--success` is already a complete data URL -- 129 bytes of
`<svg>` for the check -- and borrowing it costs a pointer. Authoring a new glyph
would mean putting image data in a colour table, which theme/blocks.tsv refuses.

⚠️ AND AN UNKNOWN ICON NAME IS REFUSED RATHER THAN PASSED THROUGH. Emitting
`var(--md-admonition-icon--nonsense)` is worse than emitting nothing: no
fallback means invalid at computed-value time, which sets `mask-image: none`,
which removes the mask entirely and leaves the ::before painting its full
background-color as a solid 20x20px SQUARE.

🔴 AND THE SAME SQUARE ARRIVES FROM AN OLD BROWSER, WHICH THE GUARD ABOVE CANNOT
SEE (found 2026-08-05 by running the generator). Unprefixed `mask-image` needs
Safari 16.4; below that the declaration is dropped as unknown, the mask is gone,
and a CORRECT icon name paints the square. Material's own compiled stylesheet
emits both spellings -- read off the published `main.ec1eaa64.min.css`, not
recalled -- so `_icon` emits both too. ⚑ A guard against one CAUSE of a symptom
is not a guard against the symptom.

=============================================================================
SPECIFICITY IS A TIE, WON ON SOURCE ORDER, AND THAT IS THE HONEST NAME
=============================================================================

Material's flavour rules compute to (0,3,0):

    .md-typeset .admonition.note                (0,3,0)
    .md-typeset .note > .admonition-title       (0,3,0)

The generated rules use the same selectors, so they are also (0,3,0), and every
stylesheet this engine ships is linked AFTER `main.css`. Equal specificity plus
later in the cascade means we win.

⚠️ THAT IS A TIE, NOT A STRUCTURAL FIX. There is nothing to delete here --
Material's rule is in its own stylesheet and stays there. chrome.css's ARMOUR
block carries the same warning for the same reason: the last time somebody in
this repo called a cascade tie "structural", the mislabel is what let a wrong
diagnosis ship for a day.

⚠️ THE `details` SELECTORS ARE DEFENSIVE AND I COULD NOT VERIFY THEM.
`_admonition.scss` says its styles "also apply to details tags, which are
rendered as collapsible admonitions with summary elements as titles" -- but the
rule that makes that true lives in a file this pass did not read. So every rule
below is emitted for BOTH spellings: `.admonition.<name>` and `details.<name>`,
`.admonition-title` and `summary`. A selector that matches nothing costs a few
bytes; a missing one costs a family that quietly stays blue.

=============================================================================
⚠️ EVERY COLOUR CARRIES A FALLBACK, AND HERE THAT IS NOT DEFENSIVENESS
=============================================================================

markers.py deliberately emits `var(--dr-x)` with no fallback, and says so: a
marker naming a token the active theme does not emit paints nothing, and an
unstyled marker is still readable text.

A CALLOUT IS NOT. On a nine-token local theme (`utility`, `database`, `base`)
nine of the twelve families name a canonical token that is never emitted:

    border-color: var(--dr-accent-2)     -> invalid at computed-value time
                                         -> unset -> currentColor
    background-color on the ICON         -> unset -> transparent
                                         -> THE ICON DISAPPEARS ENTIRELY

The icon is a MASK whose visible colour comes from `background-color`, so no
colour means no icon at all. That is why this module resolves its own colour
instead of reusing markers' resolver: the two files have the same QUESTION and
different CONSEQUENCES, and a shared helper that encoded one policy was what
broke the build.

⚠️ AND THE FALLBACK HAS TO BE INSIDE THE `var()`. A second `border-color`
declaration ahead of it does NOT help: a property that is invalid at
computed-value time is set to unset, and earlier declarations in the same rule
are discarded rather than used. `var(--dr-x, currentColor)` is the only mechanism.

=============================================================================
THE 10% WASH
=============================================================================

Material computes the title bar as the tint at 10% alpha, at BUILD time, from a
Sass colour. We cannot do that to a custom property -- the value is not known
until the browser resolves it -- so the wash is `color-mix(in oklch, TOKEN 10%,
transparent)`. Same result, computed one layer later.

`in oklch` matches what base.css already uses for marker chips, so the mixing
space is consistent across the two places this engine tints a token.
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
#: 0.64rem, which on this site is far below body text; eos's `fs-sm` is 0.82rem
#: against a 0.9rem body. Callouts get bigger and sit just under the prose
#: instead of looking like a footnote. That is the correct relationship rather
#: than the one that happened to exist, and it is stated here so it is not
#: mistaken for a regression.
_BOX = (
    ("border-width", "border-w", "1.5px"),
    ("border-radius", "radius-lg", "4px"),
    ("font-size", "fs-sm", "0.64rem"),
)

#: 🔴 THE TRANSITION, WHICH THIS FILE PREVIOUSLY CLAIMED WAS ALREADY HANDLED.
#:
#: The comment above the box block used to read: "A shadow and a transition, both
#: of which Material states as its own variables -- so those are mapped in
#: chrome.css and NOT restated here." HALF RIGHT, which is worse than wrong:
#: `box-shadow: var(--md-shadow-z1)` genuinely is a variable and genuinely is
#: mapped, and `transition: box-shadow 125ms` is a bare literal that chrome.css
#: never touched. ⚑ A sentence that is true about one of two things it names
#: reads as verified, so nobody checks the other half.
#:
#: Fallbacks are Material's own literals. A bare `var()` inside `transition` is
#: invalid at computed-value time, which drops the whole property on the three
#: local-theme sites.
_TRANSITION = (
    "  transition: box-shadow var(--dr-motion-fast, 125ms)"
    " var(--dr-ease, linear);"
)

#: The focus ring width.
#:
#: ⚠️ AN HONEST GAP, NOT AN OVERSIGHT. No token in any vector expresses a ring
#: width. `border-w` is the obvious candidate and it is WRONG: it is a hairline
#: at 1-1.5px, so using it would make the ring effectively disappear. Naming a
#: token that means something else to avoid a literal is precisely the bridge-row
#: mistake PR #82 had to revert. 0.2rem is Material's own 4px, kept.
_RING_W = "0.2rem"

#: What a family falls back to when its token is not emitted by the active
#: theme. `currentColor` rather than `accent`: accent would paint all nine
#: unemitted families identically and claim a family meaning that is not there,
#: where currentColor says plainly "this family has no colour here" and still
#: draws the icon.
_FALLBACK = "currentColor"

#: The twelve families Material ships, in its own order.
#:
#: ⭐ ONE CONSTANT, TWO QUESTIONS, and that is deliberate rather than thrifty.
#: It is the set of legal `icon` values -- Material emits
#: `--md-admonition-icon--<name>` for exactly these -- AND it is how this module
#: tells an INHERITED row from a DECLARED one. A second list for the second
#: question would be a second place stating one fact, which is the defect this
#: repo has now killed in tokenaudit's sheet list, three JSON manifests and the
#: marker validator.
_MATERIAL = (
    "note", "abstract", "info", "tip", "success", "question",
    "warning", "failure", "danger", "bug", "example", "quote",
)

#: `mask-image`, both spellings, prefix first.
#:
#: 🔴 THE PREFIX IS NOT COURTESY. Unprefixed `mask-image` needs Safari 16.4
#: (March 2023); below that the declaration is dropped, the mask is gone, and the
#: ::before paints its full background-color as a solid 20x20px square -- the
#: exact failure `_icon` refuses a bad NAME to prevent, arriving from a correct
#: name on an old browser. Material's compiled stylesheet emits both spellings
#: for its own masked icons, which is where this was read from.
#:
#: Prefix FIRST: a browser that understands both takes the later unprefixed
#: declaration, and one that understands only the prefix ignores the line it
#: cannot parse. Reversed, the old browser would win.
_MASK = ("-webkit-mask-image", "mask-image")


def _rows() -> list[dict]:
    return load_tsv(state.ENGINE_ROOT / "theme" / "blocks.tsv")


def _colour(value: str, where: str, tokens: set[str], report: bool = True) -> str:
    """Resolve a `color` cell to something CSS can use, WITH a fallback.

    Deliberately not markers._colour, which is the same question with a
    different answer -- see the fallback section in the module docstring. The
    token LIST is still shared, because "which names exist" has exactly one
    correct answer and a second copy of it is what went stale in tokenaudit,
    contrast.tsv and the marker validator.

    `report` defaults False at the build_css call site because assets._plan runs
    from BOTH on_config and on_files, so anything reported there is reported
    twice. `report()` below is the single honest complaint.
    """
    value = (value or "").strip()
    if not value:
        return _FALLBACK
    # Anything that is not a bare word -- #hex, oklch(...), rgb(...) -- is passed
    # through as written. Same rule as markers.py, same regex, imported rather
    # than retyped.
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

    🚫 DO NOT REUSE THIS FOR THE FOCUS RING. It was used there and it was
    measured at 1.12:1 -- see the focus-ring section in the module docstring. A
    10% mix is 90% its own ground by construction, which is correct for a tint
    behind bold text and useless for an indicator.
    """
    return "color-mix(in oklch, " + value + " 10%, transparent)"


def _icon(name: str, icon: str, report: bool = True) -> str:
    """The mask declarations for one family, or "" to leave Material's.

    Returns COMPLETE CSS lines -- both spellings of `mask-image`, newline
    separated -- so the caller extends a declaration list rather than
    concatenating a conditional into a string. See build_css.

    THREE CASES, and only one of them emits anything:

      inherited row, no icon    Material keys its own icon off the class name.
                                Nothing to do, nothing to say.
      DECLARED row, no icon     ⚠️ REPORTED. Material's base rule sets the note
                                pencil unconditionally, so this family wears the
                                wrong glyph rather than none -- which is why it
                                needs saying out loud.
      icon names a non-family   ⚠️ REFUSED and reported. An undefined var with no
                                fallback is invalid at computed-value time, which
                                removes the mask and leaves the ::before painting
                                a solid 20x20px square. Keeping the pencil is
                                wrong and legible; the square is wrong and loud.
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

    # Both spellings. See `_MASK` on why the prefix is load-bearing and why it
    # comes first.
    return "\n".join(
        "  " + prop + ": var(--md-admonition-icon--" + icon + ");"
        for prop in _MASK
    )


def _ring(value: str) -> str:
    """The focus ring for one family, at FULL STRENGTH.

    ⚠️ The strength is the decision and it is measured, not preferred. See the
    focus-ring section in the module docstring: Material's 10% alpha measures
    1.12 dark / 1.13 light against a 3.0 floor, and nothing below 100% clears
    both schemes because `text-faint` is a grey sitting near its own ground by
    design.
    """
    return "  box-shadow: 0 0 0 " + _RING_W + " " + value + ";"


def _selectors(name: str) -> tuple[str, str, str, str, str]:
    """(box, focus, title, icon, marker) selector lists for one family.

    Both spellings of every selector, always. See the docstring on why the
    `details` half could not be verified from the file that documents it.

    ⭐ `focus` is (0,4,0) -- one class more than Material's flavour rule -- so it
    wins OUTRIGHT rather than on source order. The base ring in build_css is the
    one that ties.
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
        "   win outright. See that module for the whole argument.",
        "   Every colour carries a currentColor fallback: the icon is a mask",
        "   painted by background-color, so an unresolved token would not be",
        "   a wrong colour, it would be no icon. */",
        "",
    ]

    # THE BOX, every family at once. Material hardcodes all of these.
    box_decls = [
        "  " + prop + ": var(--dr-" + token + ", " + fallback + ");"
        for prop, token, fallback in _BOX
    ]
    box_decls.append(_TRANSITION)
    # `box-shadow` itself is NOT restated here: Material reads --md-shadow-z1,
    # which chrome.css maps to elev-1. One surface, one address. The TRANSITION
    # on that shadow is a literal and is handled above -- see `_TRANSITION`.
    out.append(
        ".md-typeset .admonition,\n.md-typeset details {\n"
        + "\n".join(box_decls)
        + "\n}"
    )
    out.append("")

    # ⭐ THE BASE RING, for a family that has no row in the table. Material's
    # base rule is hardcoded blue, so without this an undeclared word gets a
    # correctly-coloured nothing and an indigo flash. `accent` is the honest
    # choice: it says "this site" rather than claiming a family meaning.
    #
    # ⚠️ (0,3,0) -- level with Material, taken on SOURCE ORDER. The per-family
    # rules below are (0,4,0) and do not depend on load order at all.
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
        # carries one declaration or three depending on the row, and building
        # that by joining a conditional into a string is where a missing
        # semicolon merges two properties into one invalid declaration. Whole
        # lines joined by newline cannot do that -- which is why adding the
        # `-webkit-` spelling later cost one line and no risk.
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

    Separate from build_css for the double-call reason above. Called by
    hooks/01d via the token audit, which is the one place that already runs
    exactly once per build and already reports on the theme.

    ⭐ INHERITED AND DECLARED ARE COUNTED SEPARATELY, because they carry
    different risk. An inherited family is Material's vocabulary and gets its
    icon for free; a declared one is ours and is one blank cell away from
    wearing the note pencil. A single total would hide the number that matters.
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
