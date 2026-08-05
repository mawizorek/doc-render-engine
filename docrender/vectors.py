"""The canonical design system: read it, resolve it, prove it.

Split out of theme.py 2026-08-04 at the seam PR #68 named. READING AND
RESOLVING the canonical data is a different job from turning it into CSS, and
theme.py was 1.7KB from the hard read limit. This module answers "what is this
site's look"; theme.py answers "what CSS does that produce".

=============================================================================
A THEME IS A JOIN OF FOUR VECTORS, AND THIS ENGINE ONLY EVER READ ONE
=============================================================================

From the join table's own header: *"A THEME binds the 4 independent vectors:
Color, Typography, Forms, and Spacing... theme = JOIN, a named combination of
exactly one token from each."*

Until now `theme:` in site.yml resolved against `colors.tsv` slugs, which are
COLOUR ENTITIES, not themes. `eos` appeared to work by coincidence: there is a
colour entity named `eos` AND a join named `eos`, and they point at each other.
`mclaren` is not a theme at all -- the joins are `sharp-mclaren` and
`mclaren-mobile`.

WARNING: THE THREE NEW VECTORS HAVE A DIFFERENT SHAPE FROM COLOUR, which is why
the colour approach did not simply extend. A colour row belongs to one theme. A
TYPOGRAPHY row does not: `sharp-racing` serves four joins, `tight` serves five.
They are SHARED ENTITIES joined by pointer. A theme does not OWN its type, it
POINTS at it -- so editing `tight` moves five themes at once, on purpose.

=============================================================================
MODE: THE APP OWNS IT, AND THE JOIN HANDLES THE GRACEFUL CASE
=============================================================================

Michael, 2026-08-04: *"app keeps mode. hands down. BUT if an app only declares a
single theme -- and the alternate toggle for that theme DOES exist it could be
written into the theme join... so app still sets the actual pointer ultimately
but the theme join gracefully handles alternative entry points."*

    theme: eos                                    # toggles eos <-> eos-light
    theme: {dark: sharp-mclaren, light: papyrus}   # two themes, app's choice

STAR AND IT COST NO NEW COLUMN, which matters because maw-themes S1 explicitly
refused one (*"No `toggle` in _themes.json"*). `identity` on the COLOUR row
already carries the pairing: a join names a colour entity, that row carries an
identity, and the sibling is the row with the same identity in the other mode.
DERIVED, never declared. Cleo's W2 argument paying a second time -- a declared
toggle is a pointer that can dangle; grouping cannot.

RED WHAT "APP KEEPS MODE" MEANS IN CODE, AND I GOT IT WRONG ONCE ALREADY.
It means the app decides WHICH THEME occupies each slot. It does NOT mean the
app picks a hex. Choosing the mode-appropriate ROW inside the theme the app
named is RESOLUTION, not substitution: when a site says `light: eos`, "the eos
theme at light" IS eos-light, and handing it the dark row is a worse answer by
every measure.

So derivation is UNCONDITIONAL -- it fires on a scalar and on an explicit map
alike. The first cut gated it on "the app did not state this scheme," which
looked like respect for the ruling and would have painted a dark ramp into light
mode the first time anybody wrote `light: eos`. Found by WRITING the config and
tracing it, not by reading the code.

WARNING: ONLY THE COLOUR SWAPS. Typography, forms and spacing are
scheme-independent -- type by documented design (two type systems that drift is
the failure it prevents), and a radius or a cell padding has no business
changing when a reader hits a toggle.

=============================================================================
NAME COLLISIONS ARE REAL AND THE ORDER IS A DECISION
=============================================================================

`eos`, `papyrus` and `database` exist as BOTH a join slug and a colour or
spacing slug. JOIN WINS; a bare colour entity is the fallback so the old
one-vector behaviour still resolves. An ambiguous name is REPORTED, because
silence would mean a site's entire look depends on which table happened to be
searched first.

PROVENANCE. Every vendored file's git blob SHA is recomputed on each build and
checked against `canonical/source.tsv`. Reports rather than raises: a palette
one edit off canonical still renders a readable site, and taking the build down
over it is worse than a loud line in the report. WARNING: it proves the file is
what we VENDORED, not that what we vendored is still CURRENT upstream. That
needs a scheduled job with network and does not exist yet.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import state
from .util import load_tsv

#: Columns in a canonical colour row that are NOT tokens. A metadata column left
#: out of this tuple is emitted as a custom property -- `--dr-identity: eos` --
#: which is junk, harmless, and invisible for a month.
META = ("slug", "name", "identity", "mode")

#: The three scheme-independent vectors: (file, join key).
SHARED = (
    ("typography.tsv", "typography"),
    ("forms.tsv", "forms"),
    ("spacing.tsv", "spacing"),
)


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


def sibling(row: dict, scheme: str) -> str | None:
    """The colour row sharing this row's identity in the requested scheme."""
    ident = (row.get("identity") or "").strip()
    if not ident:
        return None
    here = (row.get("slug") or "").strip()
    for other in rows("colors.tsv"):
        if (other.get("identity") or "").strip() != ident:
            continue
        if (other.get("slug") or "").strip() == here:
            continue
        if (other.get("mode") or "").strip() == scheme:
            return (other.get("slug") or "").strip()
    return None


def is_complete(row: dict) -> bool:
    """A row with no `alt-` values is asserting it is ONE complete palette."""
    return not any(
        (value or "").strip()
        for token, value in row.items()
        if token.startswith("alt-")
    )


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


def _declared(scheme: str) -> str:
    """The theme name this scheme asked for.

    A map missing a scheme borrows the other rather than dropping to `base`: a
    half-declared toggle almost certainly means one line was forgotten, and
    inheriting the sibling is far closer to the intent than the unskinned
    default.
    """
    decl = state.INSTANCE.get("theme", "base")
    if not isinstance(decl, dict):
        return str(decl)

    pick = decl.get(scheme)
    if pick:
        return str(pick)

    other = "light" if scheme == "dark" else "dark"
    borrowed = decl.get(other) or "base"
    state.note(
        "notes",
        "theme: no '" + scheme + "' entry; borrowing '" + str(borrowed)
        + "' from '" + other + "'. Name both schemes explicitly.",
    )
    return str(borrowed)


def resolve(scheme: str) -> dict:
    """Everything this scheme needs: the four vector slugs and their rows.

    Returns `{name, join, color, colorRow, typography, forms, spacing,
    derived}`. `color` differs from the named theme's colour when the
    opposite-mode sibling was derived; `derived` records that it happened.
    """
    name = _declared(scheme)

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
            "theme '" + name + "' is BOTH a join and a colour entity. Reading "
            "it as the JOIN. Rename one upstream -- a site's whole look should "
            "not depend on which table is searched first.",
        )

    if entry:
        color = str(entry.get("color", "")).strip()
        picked = {key: str(entry.get(key, "")).strip() for _f, key in SHARED}
    else:
        # A bare colour entity: the one-vector shape, still supported.
        color = name
        picked = {key: "" for _f, key in SHARED}

    row = color_row(color)
    derived = None

    # UNCONDITIONAL. See the docstring: picking the mode-appropriate row inside
    # the theme the app named is resolution, not substitution.
    if row:
        native = (row.get("mode") or "").strip()
        if native in ("dark", "light") and native != scheme:
            found = sibling(row, scheme)
            if found:
                derived = found
                color = found
                row = color_row(found)
            elif is_complete(row):
                state.note(
                    "notes",
                    "theme '" + color + "' is a COMPLETE " + native
                    + " palette and no row shares its identity at " + scheme
                    + ", so it is painting its " + native + " ramp there. "
                    "Author the sibling, or name a " + scheme + " theme.",
                )

    return {
        "name": name,
        "join": entry,
        "color": color,
        "colorRow": row,
        "typography": picked["typography"],
        "forms": picked["forms"],
        "spacing": picked["spacing"],
        "derived": derived,
    }
