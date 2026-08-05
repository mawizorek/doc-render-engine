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

    .md-typeset .admonition.#{$name}          { border-color: $tint }
    .md-typeset .#{$name} > .admonition-title {
      background-color: color.adjust($tint, $alpha: -0.9);
      &::before { background-color: $tint; mask-image: ...icon }
      &::after  { color: $tint }
    }

FOUR SURFACES PER FAMILY, all painted from one hardcoded hex: the box border,
the title bar wash at 10% alpha, the ICON (a mask whose colour comes from
`background-color`), and the details marker on a collapsible. None of them is a
variable, which is the whole reason no theme change has ever reached a callout.

🔴 READING THE SOURCE IS WHY THE SELECTORS WORKED FIRST TIME. The previous
attempt to beat a Material rule in this engine -- the dark-mode blue link --
shipped against a selector quoted from memory, was wrong in both halves, and
survived a full day because the fix looked structural. A selector stated from
memory is a guess wearing a bracket.

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

#: What a family falls back to when its token is not emitted by the active
#: theme. `currentColor` rather than `accent`: accent would paint all nine
#: unemitted families identically and claim a family meaning that is not there,
#: where currentColor says plainly "this family has no colour here" and still
#: draws the icon.
_FALLBACK = "currentColor"


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


def _selectors(name: str) -> tuple[str, str, str, str]:
    """(box, title, icon, marker) selector lists for one family.

    Both spellings of every selector, always. See the docstring on why the
    `details` half could not be verified from the file that documents it.
    """
    box = (
        ".md-typeset .admonition." + name + ",\n"
        ".md-typeset details." + name
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
    return box, title, icon, marker


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
        "   specificity (0,3,0). See that module for the whole argument.",
        "   Every colour carries a currentColor fallback: the icon is a mask",
        "   painted by background-color, so an unresolved token would not be",
        "   a wrong colour, it would be no icon. */",
        "",
    ]

    # THE BOX, every family at once. Material hardcodes all three of these.
    box_decls = [
        "  " + prop + ": var(--dr-" + token + ", " + fallback + ");"
        for prop, token, fallback in _BOX
    ]
    # A shadow and a transition, both of which Material states as its own
    # variables -- so those are mapped in chrome.css and NOT restated here. One
    # surface, one address.
    out.append(
        ".md-typeset .admonition,\n.md-typeset details {\n"
        + "\n".join(box_decls)
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
        box, title, icon, marker = _selectors(name)
        wash = "color-mix(in oklch, " + value + " 10%, transparent)"
        out += [
            box + " {\n  border-color: " + value + ";\n}",
            title + " {\n  background-color: " + wash + ";\n}",
            icon + " {\n  background-color: " + value + ";\n}",
            marker + " {\n  color: " + value + ";\n}",
            "",
        ]

    return "\n".join(out) + "\n"


def report() -> None:
    """Say which families are governed, once, from a caller that runs once.

    Separate from build_css for the double-call reason above. Called by
    hooks/01d via the token audit, which is the one place that already runs
    exactly once per build and already reports on the theme.
    """
    tokens = _known_tokens()
    named = []
    for row in _rows():
        name = (row.get("block") or "").strip()
        if not name:
            continue
        _colour((row.get("color") or "").strip(), "block '" + name + "'", tokens)
        named.append(name)
    if named:
        state.note(
            "notes",
            "blocks: " + str(len(named)) + " callout families governed by "
            + "theme/blocks.tsv (" + ", ".join(sorted(named)) + ").",
        )
