"""BLOCK FAMILY COLOURS -- generated CSS for the `!!!` and `???` callouts.

Not a hook. `build_css()` is called by docrender/assets.py and published as
`blocks.css`, exactly like markers.py's marker-class sheet.

Defined in theme/blocks.tsv. Adding or recolouring a family is a row there.

=============================================================================
🔴 THIS FILE TOOK EVERY SITE DOWN ON THE DAY IT SHIPPED (2026-08-05)
=============================================================================

    ImportError: cannot import name '_token_sets' from 'docrender.markers'

Raised at CONFIG LOAD -- `hooks/01d_audit.py` imports tokenaudit, which imports
assets, which imports this module -- so it fired before a single page rendered
and killed uritp, template, theatre and hml simultaneously.

`_token_sets` was a function I wrote in PR #84 and then CLOSED MYSELF when a
parallel session shipped the same fix first as #83. Their version is named
`_known_tokens` and returns one union SET; mine returned a `(local, canonical)`
TUPLE. This file was then written against my own closed branch's API, from
memory, three hours later.

⚑ CLOSING A PR AS SUPERSEDED DOES NOT RETRACT THE ASSUMPTIONS OF WORK BUILT ON
TOP OF IT. A superseded PR leaves its API in your head, which is the one place a
diff cannot reach.

⭐ AND THE IMPORT IS A MODULE IMPORT NOW, DELIBERATELY. `from .markers import
_colour` puts a borrowed PRIVATE name into this namespace, where every call site
reads as though the function were local -- nothing at the point of use says "this
belongs to another module and can move under you." `markers._colour(...)` says it
on every line.

⚠️ AND THE REAL SEAM IS STILL OPEN: colour-token resolution is an ENGINE-WIDE
concern living in the marker module as two private functions, and two modules now
reach for it. It belongs in its own module. Not moved during an outage.

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

🔴 READING THE SOURCE IS WHY THE SELECTORS WORKED FIRST TIME -- and the import
above is what happens when the same file does the opposite one function later.
The CSS was read from disk; the Python API was recalled from a branch that no
longer exists.

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

from . import markers, state
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


def _rows() -> list[dict]:
    return load_tsv(state.ENGINE_ROOT / "theme" / "blocks.tsv")


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

    ⚠️ EVERY CALL INTO markers IS QUALIFIED. See the red section in the module
    docstring: importing those private names directly is what let this file be
    written against a signature that had never merged.
    """
    tokens = markers._known_tokens()
    rows = [r for r in _rows() if (r.get("block") or "").strip()]

    out = [
        "/* GENERATED by docrender/blocks.py -- do not edit.",
        "   One rule set per family, from theme/blocks.tsv.",
        "   Beats Material's flavour rules on source order at equal",
        "   specificity (0,3,0). See that module for the whole argument. */",
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
        value = markers._colour(
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
    tokens = markers._known_tokens()
    named = []
    for row in _rows():
        name = (row.get("block") or "").strip()
        if not name:
            continue
        markers._colour(
            (row.get("color") or "").strip(), "block '" + name + "'", tokens
        )
        named.append(name)
    if named:
        state.note(
            "notes",
            "blocks: " + str(len(named)) + " callout families governed by "
            + "theme/blocks.tsv (" + ", ".join(sorted(named)) + ").",
        )
