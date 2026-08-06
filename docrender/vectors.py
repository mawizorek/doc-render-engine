"""The canonical design system: read it, resolve it, prove it.

This module answers "what is this site's look"; theme.py answers "what CSS does
that produce". Full contract, including the parts that are not this engine's to
decide: maw-themes `docs/HOW-A-THEME-IS-CHOSEN.md`.

=============================================================================
⭐ WHERE THE VECTORS COME FROM (2026-08-06): LIVE, WITH A FALLBACK
=============================================================================

Michael: *"the renderer should pull from canonical; there should be no
in-between"* -- and on the failure mode, *"only fallback to local if the
canonical in themes repo cannot be reached during build."*

So each file resolves per build:

    DOCRENDER_CANONICAL set, and the file is there  ->  LIVE, read from upstream
    anything else                                   ->  theme/canonical/, LOUDLY

The workflows check the design system out beside the engine and the content, and
that checkout is `continue-on-error` -- an unreachable design system degrades to
the last vendored copy instead of failing a publish.

🔴 IT DID NOT WORK THIS WAY UNTIL 2026-08-06, AND NOBODY EVER DECIDED THAT. The
initial extraction copied the files in to get moving, and every commit after it
improved the PROSE about the gap: source.tsv has carried "that needs a scheduled
job with network access, and it does not exist yet" from the day it was written.
The gap then fired on Michael's own hand-committed typography and spacing edits
-- fifty minutes live upstream and absent from every site, found only because
somebody read the refresh log for an unrelated reason. ⚑ A warning where a check
belongs, in the repo that spends its docstrings finding exactly that.

⭐ THE UPSTREAM PATHS ARE NOT RESTATED ANYWHERE. `canonical/source.tsv` has
recorded each file's repo and path since the first vendor, as provenance. That
table is now the lookup, so there is no second list of what lives where -- which
matters, because a second list is how the two would drift.

⭐ AND A FILE ABSENT FROM source.tsv STAYS LOCAL FOR FREE. `aliases.tsv` and
`bridge.tsv` sit in the same folder and are OURS: they join this engine's
vocabulary to the design system's and have no upstream. Nothing in the resolver
knows their names -- they are simply not in the provenance table.

⚠️ FALLBACK IS PER FILE AND IS REPORTED BY NAME. A renamed upstream file gives a
MIXED state -- live colours against a vendored join -- which is legal and worth
shouting about, because the symptom otherwise arrives as a dangling pointer with
no stated cause.

=============================================================================
A THEME IS A JOIN. A COLOUR SLUG IS NOT A THEME.
=============================================================================

A join in `themes.json` binds FIVE pointers: two colours, one typography, one
forms, one spacing. It is the only entry point.

🔴 `mclaren` IS A PALETTE, NOT A THEME -- the themes using it are `sharp-mclaren`
and `mclaren-mobile`. Naming a bare colour entity still resolves, for
compatibility, and gets colour ONLY: no canonical type, radii or density. It is
reported when it happens, because this went unnoticed for a day.

⚠️ `eos`, `papyrus` and `database` exist as BOTH a join slug and an entity slug.
JOIN WINS and the ambiguity is REPORTED -- silence there would mean a site's
whole look depends on which table was searched first. `eos` appearing to work was
exactly this coincidence: a join and a colour sharing a name and happening to
point at each other.

=============================================================================
⭐ THE PAIR IS DECLARED, NEVER DERIVED (2026-08-05)
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

🔴 AND THE COST IS REAL: A POINTER CAN DANGLE. An `alt-color` naming a row that
does not exist is REPORTED BY NAME here and never silently replaced with
something plausible. That is the entire mitigation and it is deliberate -- a loud
reader instead of a clever table.

⚠️ `mode` RESOLVES NOTHING NOW. It is descriptive. It survives as the one thing
that can still catch "you put a dark palette in the light slot," which is
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

PROVENANCE. Every file's git blob SHA is recomputed on each build and checked
against `canonical/source.tsv`. Reports rather than raises: a palette one edit
off canonical still renders a readable site.

🔴 AND THAT CHECK ANSWERS A DIFFERENT QUESTION SINCE 2026-08-06. It used to prove
only "this file is what we VENDORED" -- narrower than any reader assumed, which
source.tsv had to say out loud. Reading live, the same comparison proves the file
IS the current upstream one. A mismatch now means the vendored FALLBACK has gone
stale, which asks for a re-vendor rather than reporting a defect: the site is
already painting the right bytes.
"""

from __future__ import annotations

import hashlib
import json
import os
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


def _vendored(name: str) -> Path:
    return theme_dir() / "canonical" / name


def _provenance() -> list[dict]:
    """source.tsv, which is both the hash record AND the upstream path map.

    ⭐ ONE TABLE, TWO JOBS, and unlike most such things that is correct here:
    "where did this file come from" and "where do we fetch it from" are the same
    fact. A second table would be a copy of it, free to drift.
    """
    return load_tsv(_vendored("source.tsv"))


def _upstream_root() -> Path | None:
    """The checked-out design system, if the workflow fetched one."""
    raw = os.environ.get("DOCRENDER_CANONICAL", "").strip()
    if not raw:
        return None
    root = Path(raw)
    return root if root.is_dir() else None


def _upstream_path(name: str) -> Path | None:
    """Where `name` lives in the fetched design system, if it is there.

    ⚠️ RETURNS None FOR ANY FILE source.tsv DOES NOT LIST, which is how
    `aliases.tsv` and `bridge.tsv` stay local without being named in code.
    """
    root = _upstream_root()
    if root is None:
        return None
    for row in _provenance():
        if (row.get("file") or "").strip() != "canonical/" + name:
            continue
        rel = (row.get("path") or "").strip()
        if not rel:
            return None
        candidate = root / rel
        return candidate if candidate.is_file() else None
    return None


def _canon(name: str) -> Path:
    """The file to actually READ: upstream when reachable, vendored otherwise.

    ⚠️ NOT CACHED, on purpose. This is two `is_file()` calls, `load_tsv` re-reads
    from disk on every call anyway, and a module-level cache would outlive a
    build under `mkdocs serve` -- which rebuilds in-process.
    """
    return _upstream_path(name) or _vendored(name)


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


def _blob_sha(path: Path) -> str:
    """Git's own blob hash: sha1 over a short header plus the content.

    Directly comparable to a SHA read off the source repo without cloning it,
    which is the only reason this is git's algorithm rather than a plain digest.
    """
    raw = path.read_bytes()
    header = ("blob " + str(len(raw))).encode() + bytes(1)
    return hashlib.sha1(header + raw).hexdigest()


def verify() -> None:
    """Say where every vector came from, and prove it is what it claims to be.

    Reports, never raises. Taking a build down over a palette one edit off
    canonical is worse than a loud line in the report -- and the fallback exists
    precisely so an unreachable design system cannot stop a publish.

    THREE THINGS GET SAID, and they are three different questions:

      LIVE          read from the fetched design system. The healthy path.
      STALE COPY    live and correct, but the vendored fallback no longer
                    matches upstream. Not a defect -- the site is painting the
                    right bytes. It asks for a re-vendor so the fallback stays
                    worth having.
      FELL BACK     ⚠️ upstream unreachable. The site renders the last vendored
                    copy, which may be days old, and that is the one a human has
                    to see.
    """
    root = _upstream_root()
    live: list[str] = []
    fell_back: list[str] = []
    stale: list[str] = []
    damaged: list[str] = []

    for row in _provenance():
        rel = (row.get("file") or "").strip()
        want = (row.get("blob_sha") or "").strip()
        if not rel or not want:
            continue
        name = rel.split("/")[-1]

        upstream = _upstream_path(name)
        path = upstream or _vendored(name)

        if not path.is_file():
            state.note(
                "missing_required",
                "canonical: " + rel + " is recorded in source.tsv and is on "
                + "disk NOWHERE -- not upstream, not vendored. This site has no "
                + "value for that vector at all.",
            )
            continue

        got = _blob_sha(path)

        if upstream is not None:
            live.append(name)
            if got != want:
                # ⭐ NOT A DEFECT. Upstream has simply moved since the last
                # vendor, which is the NORMAL state of a live read. What it
                # costs is the fallback: if the design system were unreachable
                # right now, this site would paint the older bytes instead.
                stale.append(
                    name + " (recorded " + want[:7] + ", upstream " + got[:7] + ")"
                )
            continue

        fell_back.append(name)
        if got != want:
            # The old check, and it still means what it always meant: the
            # vendored file is not the one we recorded. Somebody edited it in
            # place, or the copy is damaged.
            damaged.append(
                name + " (recorded " + want[:7] + ", on disk " + got[:7] + ")"
            )

    if live and not fell_back:
        state.note(
            "notes",
            "canonical: LIVE -- all " + str(len(live)) + " vectors read from the "
            + "design system checked out at " + str(root) + ". This build paints "
            + "what is in maw-themes right now.",
        )
    elif fell_back and not live:
        state.note(
            "missing_required",
            "canonical: FELL BACK TO THE VENDORED COPY for all "
            + str(len(fell_back)) + " vectors"
            + ("" if root else " -- DOCRENDER_CANONICAL is not set, so the "
               + "workflow did not check the design system out at all")
            + ". The site renders theme/canonical/, which is a snapshot and may "
            + "be days behind. Any upstream edit since the last re-vendor is NOT "
            + "on this build.",
        )
    elif fell_back:
        # ⚠️ THE MIXED STATE, and it is the one worth shouting about. Live
        # colours against a vendored join can produce a pointer at a row that no
        # longer exists -- which is otherwise reported only as a dangling
        # pointer, with no stated cause.
        state.note(
            "missing_required",
            "canonical: MIXED SOURCES. Live: " + ", ".join(sorted(live))
            + ". Fell back to the vendored copy: " + ", ".join(sorted(fell_back))
            + ". A file listed in source.tsv was not found at its recorded path "
            + "upstream -- it has probably been renamed or moved there. Fix the "
            + "`path` column, because a live vector joined to a stale one can "
            + "point at a row that no longer exists.",
        )

    if stale:
        state.note(
            "notes",
            "canonical: the VENDORED FALLBACK is behind upstream for "
            + ", ".join(sorted(stale)) + ". Nothing is wrong with this build -- "
            + "it read the live files. Re-vendor and update source.tsv so the "
            + "fallback is still worth having on the day the fetch fails.",
        )

    if damaged:
        state.note(
            "missing_required",
            "canonical: the vendored copy does NOT match what was recorded for "
            + ", ".join(sorted(damaged)) + ", and this build is reading it "
            + "because upstream could not be reached. Either it was edited in "
            + "place (never do this) or the copy is damaged.",
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
        # 🔴 A DANGLING POINTER. Reported by name and never guessed at -- this
        # is the cost of a declared pair and the whole reason it is loud.
        state.note(
            "notes",
            "theme '" + name + "' points " + scheme + " at colour '" + color
            + "', which is not a row in the canonical colour table. Nothing is "
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
