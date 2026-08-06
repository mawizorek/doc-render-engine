"""Hook 04 -- look, EMITTED. Resolution lives in docrender/vectors.py.

This file turns the resolved theme into CSS custom properties and hands them to
assets.py as a generated sheet. It decides nothing about WHICH theme; read
vectors.py for the join, the declared pair and where the vectors are READ FROM.
The full contract is maw-themes `docs/HOW-A-THEME-IS-CHOSEN.md`.

=============================================================================
WHAT GETS EMITTED, AND IN WHAT ORDER
=============================================================================

PER SCHEME (colour only -- the one vector that differs between toggle states):

  1. local `base` rows       carries `dead`, which canonical has no token for
  2. the canonical row       the palette the JOIN named for this slot
  3. the colour aliases      --dr-ink: var(--dr-text), and six more

ONCE, IN :root (the three scheme-independent vectors):

  4. local `base` typography  tokens canonical has no equivalent for
  5. canonical typography     6 entities, shared by pointer
  6. canonical forms          5 entities
  7. canonical spacing        6 entities
  8. the BRIDGE               --dr-data-pad: var(--dr-pad-cell), and three more

ORDER IS LOAD-BEARING IN BOTH BLOCKS AND ITS FAILURE MODE IS SILENCE. Later
declarations win at equal specificity, so the aliases and the bridge MUST come
last -- put either anywhere else and the local value quietly survives while every
file involved still looks correct.

STAR THE SAME PATTERN, THREE TIMES, AND IT IS THE SPINE OF THE WHOLE JOIN.
Colour aliases rename per scheme; local-underneath fills what canonical does not
model; the bridge points a SEMANTIC token at a canonical PRIMITIVE. Every one of
them keeps the consumer's own vocabulary and moves only where the value comes
from -- which is why no stylesheet had to be found-and-replaced, and therefore
why none of them could be missed.

=============================================================================
🔴 THIS FUNCTION RUNS TWO OR THREE TIMES PER BUILD. DO NOT REPORT FROM IT.
=============================================================================

`assets._plan()` calls `build_css()`, and `_plan` is called from BOTH `on_config`
and `on_files` -- so everything here happens at least twice, and a third time on
any page carrying a `!!! tokens` block, which reaches it through tokenaudit.

That is why `vectors.verify()` is NOT called here any more (moved 2026-08-06 to
instance.on_config, hook 00, which runs exactly once). It was harmless while the
provenance check only spoke about a damaged file; the live-read change made it
speak on every build, and the sentence that started repeating three times was the
fallback warning -- the single most important line the report can carry.

⚠️ THE NOTES STILL IN THIS FILE REPEAT, AND THAT IS AN OPEN DEFECT rather than a
choice: the bridge note, the two per-scheme theme lines and the contrast failures
all print two or three times. They are inventory rather than alarms, so it has
never been worth a fourth copy of the `report=False` flag markers.py and
blocks.py both carry. If you add a NEW report here, that flag is the price --
or better, put the report where the question is asked once.

WARNING: STILL NOT EVERYTHING GOVERNED. `elev-1/2/3`, the motion set and `lift`
have NO consumer anywhere in this engine's CSS. Section 4 of the token audit page
lists every literal that remains.

`contrast.tsv` is not decoration. It is the measured accessibility floor, and a
palette that drops below it gets reported.
"""

from __future__ import annotations

from . import state, vectors
from .util import load_tsv

# Material writes the active scheme onto the document; `slate` is its dark scheme
# and `default` its light one. Emitting both on every build is what lets a reader
# use the toggle without the site fetching anything.
_SCHEMES = (
    ("dark", '[data-md-color-scheme="slate"]'),
    ("light", '[data-md-color-scheme="default"]'),
)

#: The scheme that supplies the three scheme-independent vectors. Same value
#: vectors.PRIMARY uses to decide which slot takes a join's `alt-color`, and
#: imported rather than restated so the two cannot drift.
_PRIMARY = vectors.PRIMARY


def _pairs(file: str) -> list[tuple[str, str]]:
    """(consumer, canonical) rows from an alias-shaped table.

    A row pointing a name at itself is dropped: it is a no-op in CSS and a trap
    in a table, because it reads as a mapping somebody chose.

    ⚠️ READ FROM THE VENDORED FOLDER DIRECTLY, NOT THROUGH `vectors._canon`, and
    that is correct rather than an oversight. `aliases.tsv` and `bridge.tsv` are
    OURS -- they join this engine's vocabulary to the design system's and have no
    upstream file to fetch. They are absent from source.tsv, so the resolver
    would fall them back here anyway; going straight to the folder says so.
    """
    out = []
    for row in load_tsv(vectors.theme_dir() / "canonical" / file):
        local = (row.get("consumer") or "").strip()
        canon = (row.get("canonical") or "").strip()
        if local and canon and local != canon:
            out.append((local, canon))
    return out


def _color_decls(row: dict) -> list[tuple[str, str]]:
    """Every token on one canonical colour row.

    STAR THIS USED TO TAKE A `scheme` ARGUMENT AND CHOOSE BETWEEN A BASE VALUE
    AND AN `alt-` ONE. It does not any more: a row is one complete palette, the
    join says which row each toggle state uses, and there is nothing left to
    decide here. The whole base-versus-alt branch is gone.
    """
    return [
        ("--dr-" + token, (value or "").strip())
        for token, value in row.items()
        if token not in vectors.META and (value or "").strip()
    ]


def _local_color(themes: tuple[str, ...], scheme: str) -> list[tuple[str, str]]:
    """The local nine-token table -- the only source for themes canonical has
    never heard of, and the only source for `dead` anywhere."""
    decls = []
    for row in vectors.local("colors.tsv"):
        if (row.get("theme") or "") not in themes:
            continue
        token = (row.get("token") or "").strip()
        value = (row.get(scheme) or "").strip()
        if token and value:
            decls.append(("--dr-" + token, value))
    return decls


def _entity_decls(file: str, slug: str) -> tuple[list[str], set[str]]:
    """Every token on one shared-vector row, plus the names it defined.

    The name set is what lets the bridge skip a row whose primitive this theme
    never emitted.
    """
    row = vectors.entity(file, slug)
    if not row:
        return [], set()
    out, names = [], set()
    for token, value in row.items():
        clean = (value or "").strip()
        if token == "slug" or not clean:
            continue
        out.append("  --dr-" + token + ": " + clean + ";")
        names.add(token)
    return out, names


def _bridge(available: set[str]) -> list[str]:
    """Point each semantic token at its canonical primitive.

    WARNING: a row whose primitive is NOT in `available` is SKIPPED, not emitted
    as a dangling `var()`. A theme with no join emits no `pad-cell`, and
    `--dr-data-pad: var(--dr-pad-cell)` would then resolve to nothing and
    collapse every table cell's padding to zero -- a blank rather than an error.
    """
    out, skipped = [], []
    for local, canon in _pairs("bridge.tsv"):
        if canon in available:
            out.append("  --dr-" + local + ": var(--dr-" + canon + ");")
        else:
            skipped.append(local + " -> " + canon)
    if skipped:
        state.note(
            "notes",
            "bridge: " + ", ".join(skipped) + " not wired -- this theme emits "
            "no such canonical primitive, so the local value stands. Expected "
            "for a theme with no join; a bug for one with a join.",
        )
    return out


def _shared(primary: dict, other: dict) -> list[str]:
    """Typography, forms and spacing. Emitted ONCE, from the primary scheme."""
    out = []
    for row in vectors.local("typography.tsv"):
        if (row.get("theme") or "") != "base":
            continue
        token = (row.get("token") or "").strip()
        value = (row.get("value") or "").strip()
        if token and value:
            out.append("  --dr-" + token + ": " + value + ";")

    available: set[str] = set()
    for file, key in vectors.SHARED:
        slug = primary.get(key) or ""
        if slug:
            decls, names = _entity_decls(file, slug)
            out += decls
            available |= names

    out += _bridge(available)

    differing = [
        key + " '" + str(other.get(key)) + "'"
        for _file, key in vectors.SHARED
        if other.get(key) and other.get(key) != primary.get(key)
    ]
    if differing:
        state.note(
            "notes",
            "typography, forms and spacing come from the " + _PRIMARY
            + " theme '" + str(primary.get("name")) + "'. The other scheme "
            "points at " + ", ".join(differing) + " and those are NOT applied "
            "-- these three vectors are scheme-independent by design, so only "
            "one theme can supply them.",
        )
    return out


def build_css() -> str:
    """Return the generated custom-property sheet for the active instance.

    ⚠️ CALLED TWO OR THREE TIMES PER BUILD. See the red block in the module
    docstring before adding anything here that reports.
    """
    slug = str(state.INSTANCE.get("slug", "?"))
    picked = {scheme: vectors.resolve(scheme) for scheme, _sel in _SCHEMES}

    label = ", ".join(
        s + ": " + str(p["name"]) + " ("
        + ("alt: " if p["alt"] else "") + str(p["color"]) + ")"
        for s, p in picked.items()
    )
    lines = [
        "/* GENERATED by docrender/theme.py -- do not edit.",
        "   Theme: " + label + ".",
        "   Colour, type, forms and spacing come from the canonical design",
        "   system; see the build report for whether this build read it LIVE",
        "   or fell back to the vendored copy. Site overrides: instances/"
        + slug + "/theme.css.",
        "*/",
    ]

    for scheme, selector in _SCHEMES:
        got = picked[scheme]
        row = got["colorRow"]
        decls: list[tuple[str, str]] = []

        if row:
            # Local `base` FIRST, for one reason: it carries `dead`. The local
            # rows for the CHOSEN theme are skipped -- emitting a value that is
            # guaranteed to be overwritten reads, in a diff, like a decision.
            decls += _local_color(("base",), scheme)
            decls += _color_decls(row)
            # LAST. See the ordering note in the module docstring.
            decls += [
                ("--dr-" + local, "var(--dr-" + canon + ")")
                for local, canon in _pairs("aliases.tsv")
            ]
        else:
            decls += _local_color(("base", got["color"]), scheme)

        if decls:
            lines.append(selector + " {")
            lines.extend(
                "  " + name + ": " + value + ";" for name, value in decls
            )
            lines.append("}")

    other = "light" if _PRIMARY == "dark" else "dark"
    shared = _shared(picked[_PRIMARY], picked[other])
    if shared:
        lines.append(":root {")
        lines.extend(shared)
        lines.append("}")

    for scheme, got in picked.items():
        if not got["colorRow"]:
            continue
        state.note(
            "notes",
            scheme + " scheme: theme '" + str(got["name"]) + "' -> colour '"
            + str(got["color"]) + "'"
            + (" (its alt-color)" if got["alt"] else " (its primary colour)")
            + (", typography '" + got["typography"] + "', forms '"
               + got["forms"] + "', spacing '" + got["spacing"] + "'"
               if got["join"] else " -- colour entity only, no join")
            + ".",
        )

    for row in vectors.local("contrast.tsv"):
        try:
            ratio = float(row.get("ratio") or 0)
            floor = float(row.get("min") or 0)
        except ValueError:
            continue
        if ratio and floor and ratio < floor:
            state.note(
                "notes",
                "contrast: " + str(row.get("pair", "?")) + " measures "
                + str(ratio) + " against a floor of " + str(floor)
                + ". Readers with low vision lose this text.",
            )

    return "\n".join(lines) + "\n"
