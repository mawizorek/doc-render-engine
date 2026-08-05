"""The canonical design system: read it, resolve it, prove it.

This module answers "what is this site's look"; theme.py answers "what CSS does
that produce". Full contract, including the parts that are not this engine's to
decide: maw-themes `docs/HOW-A-THEME-IS-CHOSEN.md`.

=============================================================================
A THEME IS A JOIN. A COLOUR SLUG IS NOT A THEME.
=============================================================================

A join in `canonical/themes.json` binds FIVE pointers: two colours, one
typography, one forms, one spacing. It is the only entry point.

RED `mclaren` IS A PALETTE, NOT A THEME -- the themes using it are
`sharp-mclaren` and `mclaren-mobile`. Naming a bare colour entity still resolves,
for compatibility, and gets colour ONLY: no canonical type, radii or density. It
is reported when it happens, because this went unnoticed for a day.

WARNING: `eos`, `papyrus` and `database` exist as BOTH a join slug and an entity
slug. JOIN WINS and the ambiguity is REPORTED -- silence there would mean a
site's whole look depends on which table was searched first. `eos` appearing to
work was exactly this coincidence: a join and a colour sharing a name and
happening to point at each other.

=============================================================================
STAR THE PAIR IS DECLARED, NEVER DERIVED (2026-08-05)
=============================================================================

    "color":     "mclaren",
    "alt-color": "mclaren-light",

Michael: *"there is no such thing as a 'theme family' or trying to guess the pair
systemically from the colors tsv. just point direct to its unique slug row
name."*

This replaced an `identity` column that grouped rows into pairs. That column was
symmetric, cost nothing and could not dangle -- and it was still wrong, because
it made the COLOUR TABLE hold a fact about a RELATIONSHIP. A canonical object
vector must not know what it is joined to. Cheap and structurally wrong is still
wrong.

What the reversal bought, immediately:

  * A PAIR NEED NOT BE DARK+LIGHT. Two darks, two lights, normal-and-party.
    Derivation could only ever find the opposite MODE.
  * A join may point at any row at all. There are no families to belong to.

RED AND THE COST IS REAL: A POINTER CAN DANGLE. An `alt-color` naming a row that
does not exist is REPORTED BY NAME here and never silently replaced with
something plausible. That is the entire mitigation and it is deliberate -- a loud
reader instead of a clever table.

WARNING: `mode` RESOLVES NOTHING NOW. It is descriptive. It survives as the one
thing that can still catch "you put a dark palette in the light slot," which is
reported as a mismatch rather than corrected -- correcting it would be inference,
and inference is what this change removes.

=============================================================================
THE THREE OTHER VECTORS ARE SHARED ENTITIES
=============================================================================

A colour row belongs to one theme. A typography row does not: `sharp-racing`
serves four joins, `tight` serves five. They are joined by POINTER, so editing
`tight` moves five themes at once, on purpose.

They also do NOT split by toggle state -- type is scheme-independent by design,
and a radius or a cell padding has no business changing when a reader flips a
switch. theme.py takes all three from the PRIMARY scheme and names what it
dropped.

PROVENANCE. Every vendored file's git blob SHA is recomputed on each build and
checked against `canonical/source.tsv`. Reports rather than raises: a palette one
edit off canonical still renders a readable site. WARNING it proves the file is
what we VENDORED, not that what we vendored is still CURRENT upstream.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import state
from .util import load_tsv

#: Columns in a canonical colour row that are NOT tokens. A metadata column left
#: out of this tuple is emitted as a custom property -- `--dr-mode: dark` --
#: which is junk, harmless, and invisible for a month.
META = ("slug", "mode")

#: The three scheme-independent vectors: (file, join key).
SHARED = (
    ("typography.tsv", "typography"),
    ("forms.tsv", "forms"),
    ("spacing.tsv", "spacing"),
)

#: The scheme an app treats as its default. The OTHER one is the alt slot, and
#: that is the only place `alt-color` is used.
PRIMARY = "dark"


def theme_dir() -> Path:
    return Path(state.ENGINE_ROOT) / "theme"


def _canon(name: str) -> Path:
    return theme_dir() / "canonical" / name


def rows(name: str) -> list[dict]:
    return load_tsv(_canon(name))


def local(name: str) -> list[dict]:
    return load_tsv(theme_dir() / name)


def joins() -> list[dict]:
    try:
        data = json.loads(_canon("themes.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    found = data.get("themes")
    return found if isinstance(found, list) else []


def join(slug: str) -> dict | None:
    for entry in joins():
        if str(entry.get("slug", "")).strip() == slug:
            return entry
    return None


def color_row(slug: str) -> dict | None:
    for row in rows("colors.tsv"):
        if (row.get("slug") or "").strip() == slug:
            return row
    return None


def entity(file: str, slug: str) -> dict | None:
    for row in rows(file):
        if (row.get("slug") or "").strip() == slug:
            return row
    return None


def known() -> set[str]:
    """Every name an instance may legally ask for: joins, colour entities, and
    the engine's own local themes. One union rather than three lists to keep in
    step."""
    out = {str(j.get("slug", "")).strip() for j in joins()}
    out |= {(r.get("slug") or "").strip() for r in rows("colors.tsv")}
    out |= {(r.get("theme") or "").strip() for r in local("themes.tsv")}
    return {n for n in out if n}


def verify() -> None:
    """Recompute each vendored file's git blob SHA and report a mismatch.

    Git's blob hash is sha1 over a short header plus the content, which makes it
    directly comparable to a SHA read off the source repo without cloning.
    Reports rather than raises -- taking a build down over a palette one edit off
    canonical is worse than a loud line in the report.
    """
    for row in load_tsv(_canon("source.tsv")):
        rel = (row.get("file") or "").strip()
        want = (row.get("blob_sha") or "").strip()
        if not rel or not want:
            continue
        path = theme_dir() / rel
        if not path.is_file():
            state.note(
                "notes",
                "canonical: " + rel + " is recorded in source.tsv but is not "
                "on disk. The theme join cannot verify what it is painting.",
            )
            continue
        raw = path.read_bytes()
        header = ("blob " + str(len(raw))).encode() + bytes(1)
        got = hashlib.sha1(header + raw).hexdigest()
        if got != want:
            state.note(
                "notes",
                "canonical: " + rel + " does NOT match the vendored source. "
                "Recorded " + want[:7] + ", on disk " + got[:7] + ". Either it "
                "was edited in place (never do this -- refresh it wholesale "
                "from " + str(row.get("repo", "?")) + " and update source.tsv) "
                "or the copy is damaged.",
            )


def _declared(scheme: str) -> tuple[str, bool]:
    """(theme name, is this scheme the ALT slot of that theme).

    Three shapes, and the second one is the whole ruling:

      theme: eos                  the primary scheme takes eos.color, the other
                                  takes eos.alt-color
      theme: {dark: A, light: B}  each named scheme takes THAT theme's `color`.
                                  A second declared theme REPLACES the alt, and
                                  contributes its PRIMARY -- naming it is a
                                  deliberate act and nothing may substitute.
      theme: {dark: A}            the unnamed scheme borrows A and falls back to
                                  A.alt-color, because a half-declared toggle
                                  almost certainly means one line was forgotten.
    """
    decl = state.INSTANCE.get("theme", "base")

    if not isinstance(decl, dict):
        return str(decl), scheme != PRIMARY

    pick = decl.get(scheme)
    if pick:
        return str(pick), False

    other = "light" if scheme == "dark" else "dark"
    borrowed = str(decl.get(other) or "base")
    state.note(
        "notes",
        "theme: no '" + scheme + "' entry, so it borrows '" + borrowed
        + "' from '" + other + "' and uses that theme's alt-color. Name both "
        "schemes explicitly if that is not what you meant.",
    )
    return borrowed, True


def resolve(scheme: str) -> dict:
    """Everything this scheme needs: the four vector slugs and the colour row.

    Returns `{name, join, color, colorRow, typography, forms, spacing, alt}`.
    `alt` records that this scheme took the join's `alt-color` rather than its
    `color`.
    """
    name, use_alt = _declared(scheme)

    if name not in known():
        state.note(
            "notes",
            "theme '" + name + "' (" + scheme + ") is not a join, a colour "
            "entity or a local theme; falling back to 'base'.",
        )
        name = "base"

    entry = join(name)
    if entry and color_row(name):
        state.note(
            "notes",
            "'" + name + "' is BOTH a join and a colour entity. Reading it as "
            "the JOIN. Rename one upstream -- a site's whole look should not "
            "depend on which table is searched first.",
        )

    if entry:
        color = str(entry.get("alt-color" if use_alt else "color", "")).strip()
        if use_alt and not color:
            color = str(entry.get("color", "")).strip()
            state.note(
                "notes",
                "theme '" + name + "' declares no alt-color, so " + scheme
                + " reuses its primary colour '" + color + "'. Both toggle "
                "states will look the same.",
            )
        picked = {key: str(entry.get(key, "")).strip() for _f, key in SHARED}
    else:
        # A bare colour entity: colour only, no join, no other vectors.
        color = name
        picked = {key: "" for _f, key in SHARED}
        state.note(
            "notes",
            "'" + name + "' (" + scheme + ") is a COLOUR ENTITY, not a theme, "
            "so this site gets a palette and nothing else -- no canonical "
            "typography, forms or spacing. Name a theme from themes.json.",
        )

    row = color_row(color)

    if color and row is None:
        # RED A DANGLING POINTER. Reported by name and never guessed at -- this
        # is the cost of a declared pair and the whole reason it is loud.
        state.note(
            "notes",
            "theme '" + name + "' points " + scheme + " at colour '" + color
            + "', which is not a row in canonical/colors.tsv. Nothing is "
            "substituted: this scheme has no palette. Fix the pointer.",
        )
    elif row is not None:
        native = (row.get("mode") or "").strip()
        if native in ("dark", "light") and native != scheme:
            state.note(
                "notes",
                "colour '" + color + "' declares mode '" + native + "' but is "
                "painting the " + scheme + " scheme. That is legal -- mode is "
                "descriptive, not a switch -- but it is usually a swapped "
                "pointer in themes.json.",
            )

    return {
        "name": name,
        "join": entry,
        "color": color,
        "colorRow": row,
        "typography": picked["typography"],
        "forms": picked["forms"],
        "spacing": picked["spacing"],
        "alt": use_alt,
    }
