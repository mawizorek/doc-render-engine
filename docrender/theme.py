"""Hook 04 -- look, assembled from data rather than written as code.

An instance picks its theme by NAME in site.yml; this turns the chosen rows into
CSS custom properties and hands them to assets.py as a generated sheet. Changing
a site's whole look is ONE LINE in one data file. That is not a convenience, it
is the test of whether the theme layer is real: if changing a site's appearance
required touching code, the separation between engine and site would be
decorative.

THE PALETTE IS CANONICAL (2026-08-04). There were two files called `colors.tsv`.
One is the real design system in `mawizorek/maw-themes` -- also consumed by the
ClickUp HTML apps and mapped onto FileMaker layout roles. The other is
`theme/colors.tsv` here: three themes and nine tokens, written in an afternoon to
unblock a demo. They shared a FILENAME and nothing else, and that collision is
why an edit to the real `eos` theme never showed up on the live site.

`theme/canonical/colors.tsv` is a vendored, byte-verified copy of the real one. A
theme WITH a canonical row is painted from it; a theme WITHOUT one keeps the
local table and renders exactly as it did, so shipping this cannot re-shape a
site nobody touched.

WHY VENDORED AND NOT FETCHED. A build that reaches the network can produce
different bytes on two runs from one commit, and this engine publishes from CI
where that failure is invisible. The copy is proved by its git blob SHA on every
build against `canonical/source.tsv`. WARNING: that check cannot see UPSTREAM
drift -- it proves the file is what we vendored, not that what we vendored is
still current. Said plainly, because a green check answering a narrower question
than the reader assumes is worse than no check.

NINE OF THE TEN TOKEN NAMES WERE ONLY A RENAME (`surface`->`bg`, `ink`->`text`,
`rule`->`border`, `danger`->`bad`, `ok`->`good`...). Those are emitted as ALIASES
(`--dr-ink: var(--dr-text)`), so every `var(--dr-ink)` already written keeps
working and nothing had to be found-and-replaced across the asset layer. The map
is DATA, in `canonical/aliases.tsv`, because a rename table in a paragraph cannot
be diffed.

RED: `dead` IS THE ONE TOKEN CANONICAL DOES NOT HAVE. A reference to a page
nobody has written yet is not an error, and sharing `danger` made it read as one.
Raised upstream as maw-themes D11; until it is authored the local `base` rows are
still emitted UNDERNEATH the canonical block purely to keep it alive. That is the
only reason the old table is still loaded at all.

=============================================================================
STAR THE TOGGLE CYCLES TWO THEMES, AND A ROW IS ONE COMPLETE PALETTE
=============================================================================

    theme: eos                               # one theme, both schemes
    theme: {dark: mclaren, light: eos-light}  # the toggle cycles two identities

The scalar form is unchanged and is still the common case.

WHY THIS COST ALMOST NOTHING. `_canonical_decls(row, scheme)` resolves
base-versus-alt from the ROW'S OWN `mode` against the requested scheme, so asking
a DIFFERENT row per scheme needed no new colour logic -- only a different answer
to "which slug". The resolution path below is untouched by the feature.

AND THE ARCHITECTURE WAS RULED UPSTREAM BEFORE ANYONE ASKED FOR IT HERE.
maw-themes S1: "mode is not a property of the data at all. It is a CHOICE the app
makes... the APP owns the toggle" -- the list of themes a toggle cycles belongs in
the app's own config, never in the table.

TWO ROW SHAPES ARE LIVE AT ONCE, ON PURPOSE (2026-08-04):

  COMPLETE   one row = one palette in one mode. The `alt-` band is EMPTY, and
             emptiness is the assertion. Its opposite is a SEPARATE ROW sharing
             its `identity`. This is the end state (maw-themes J10 + S1).

  LEGACY     one row = two modes. Base columns are its native ramp, the `alt-`
             band is the opposite one. WARNING: that band covers GROUND AND TEXT
             ONLY, so accent and the semantics are SHARED across modes -- the
             defect D5 exists to fix.

`identity` groups a pair: same identity, different mode. That is Cleo's answer
from maw-themes W2, which beat a `pair` pointer because a foreign key in a TSV can
dangle and a pair can be asymmetric, where grouping is symmetric by construction.
Unmigrated rows carry their own slug as identity, so the column is never
half-filled. Nothing in this engine READS it yet -- it is for the popup case
upstream ("give me Mercedes at the current mode"), and it is here so the shape is
complete before a consumer needs it.

Both shapes resolve through the same function, so the remaining rows migrate ONE
AT A TIME with no flag day. When the last one is split, the `opposite` branch in
`_canonical_decls` is four lines to delete.

RED THE TRAP THIS CREATES, AND IT IS GUARDED. Under the legacy shape
`light: eos` worked, because eos carried an alt- band. Once eos became a complete
DARK palette, that same line resolves the DARK ramp into the LIGHT scheme --
dark-on-light, no error, nothing to grep for. `_canonical_decls` now reports it,
names the sibling to use, and says why. A row with no alt cells is ASSERTING it is
one palette, so asking it for the opposite mode is a declaration error and not a
graceful fallback. `mode: mid` is exempt: it has no opposite by design (J12).

WARNING: TYPOGRAPHY DOES NOT SPLIT, deliberately. `typography.tsv` is
scheme-independent -- its own header says type must not change between light and
dark, because that is how a site ends up with two type systems that drift apart.
So under a two-theme toggle ONE of them supplies the type, and it is the DARK one,
because dark is the default scheme in mkdocs.yml. If the other theme carries
typography rows they are DROPPED and the build names them -- a font quietly
changing because a COLOUR was swapped is exactly the class of surprise this engine
keeps writing down.

What is deliberately NOT shared between sites: the look. TOKEN NAMES are shared
and VALUES are per theme, so the day somebody edits a colour to fix one site is
not the day another breaks quietly.

OVERRIDE ORDER IS LOAD-BEARING, in this exact sequence: local `base` rows, then
the canonical block, then the aliases. Later declarations win at equal
specificity, so the aliases MUST come last -- put them anywhere else and
`--dr-ink` keeps the stand-in's value while every file involved still looks
correct. A silent no-op is the failure mode this ordering exists to prevent.

`contrast.tsv` is not decoration. It is the measured accessibility floor, and a
palette that drops below it gets reported.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from . import state
from .util import load_tsv

# Material writes the active scheme onto the document; `slate` is its dark scheme
# and `default` its light one. Emitting both on every build is what lets a reader
# use the toggle without the site fetching anything.
_SCHEMES = (
    ("dark", '[data-md-color-scheme="slate"]'),
    ("light", '[data-md-color-scheme="default"]'),
)

#: The scheme that supplies typography, and the site default. See the docstring.
_PRIMARY = "dark"

#: Columns in a canonical row that are NOT tokens. `identity` is here because a
#: metadata column left out of this tuple is emitted as a custom property --
#: `--dr-identity: eos` -- which is junk, harmless, and invisible for a month.
_META = ("slug", "name", "identity", "mode")


def _theme_dir() -> Path:
    return Path(state.ENGINE_ROOT) / "theme"


def _rows(name: str) -> list[dict]:
    return load_tsv(_theme_dir() / name)


# --------------------------------------------------------------------------
# which theme, per scheme
# --------------------------------------------------------------------------


def _canonical_rows() -> list[dict]:
    return load_tsv(_theme_dir() / "canonical" / "colors.tsv")


def _canonical_row(slug: str) -> dict | None:
    for row in _canonical_rows():
        if (row.get("slug") or "").strip() == slug:
            return row
    return None


def _sibling(row: dict, scheme: str) -> str | None:
    """The row sharing this row's identity in the requested scheme.

    Only used to make an error message actionable. Resolution never depends on
    it, which is deliberate: a lookup that a build RELIES on becomes a thing
    that can dangle, and grouping was chosen over a pointer precisely to avoid
    that.
    """
    ident = (row.get("identity") or "").strip()
    if not ident:
        return None
    for other in _canonical_rows():
        if (other.get("identity") or "").strip() != ident:
            continue
        if (other.get("slug") or "").strip() == (row.get("slug") or "").strip():
            continue
        if (other.get("mode") or "").strip() == scheme:
            return (other.get("slug") or "").strip()
    return None


def _known() -> set[str]:
    """Every theme name an instance may legally ask for.

    The union is the point: reading the canonical slugs here is what makes every
    canonical theme selectable without anybody re-typing them into themes.tsv,
    which would be a second list to keep in step.
    """
    named = {(r.get("theme") or "").strip() for r in _rows("themes.tsv")}
    slugs = {(r.get("slug") or "").strip() for r in _canonical_rows()}
    return {n for n in named | slugs if n}


def _theme_for(scheme: str) -> str:
    """The theme slug this scheme paints from.

    Accepts either form of `theme:` in site.yml -- a bare slug for both schemes,
    or a map naming one per scheme. A map missing a scheme borrows the other
    rather than falling back to `base`, because a half-declared toggle almost
    certainly means one line was forgotten, and inheriting the sibling is far
    closer to the intent than dropping the site to the unskinned default.
    """
    decl = state.INSTANCE.get("theme", "base")

    if isinstance(decl, dict):
        pick = decl.get(scheme)
        if not pick:
            other = "light" if scheme == "dark" else "dark"
            pick = decl.get(other) or "base"
            state.note(
                "notes",
                "theme: no '" + scheme + "' entry; borrowing '" + str(pick)
                + "' from '" + other + "'. Name both schemes explicitly.",
            )
        wanted = str(pick)
    else:
        wanted = str(decl)

    known = _known()
    if wanted not in known:
        state.note(
            "notes",
            "theme '" + wanted + "' (" + scheme + ") is not in "
            "theme/themes.tsv or the canonical table; falling back to 'base'. "
            "Known: " + (", ".join(sorted(known)) or "none"),
        )
        return "base"
    return wanted


def _aliases() -> list[tuple[str, str]]:
    """(local name, canonical name) pairs that actually need an alias.

    A row pointing a name at itself is dropped: it is a no-op in CSS and a trap
    in a table, because it reads as a mapping somebody chose.
    """
    out = []
    for row in load_tsv(_theme_dir() / "canonical" / "aliases.tsv"):
        local = (row.get("consumer") or "").strip()
        canon = (row.get("canonical") or "").strip()
        if local and canon and local != canon:
            out.append((local, canon))
    return out


def _verify_source() -> None:
    """Recompute each vendored file's git blob SHA and report a mismatch.

    Git's blob hash is sha1 over a short header plus the content, which is what
    makes this directly comparable to a SHA read off the source repo without
    cloning anything.

    Reports rather than raises. A palette one edit off canonical still renders a
    readable site, and taking every build down over it is a worse outcome than a
    loud line in the report -- the warn-never-die rule the rest of this engine
    already follows.
    """
    for row in load_tsv(_theme_dir() / "canonical" / "source.tsv"):
        rel = (row.get("file") or "").strip()
        want = (row.get("blob_sha") or "").strip()
        if not rel or not want:
            continue
        path = _theme_dir() / rel
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


# --------------------------------------------------------------------------
# turning rows into declarations
# --------------------------------------------------------------------------


def _canonical_decls(row: dict, scheme: str) -> list[tuple[str, str]]:
    """Token declarations for one canonical row in one colour scheme.

    Handles both row shapes. The row's `mode` names its NATIVE ramp; when the
    requested scheme is the other one, an `alt-<token>` column wins if the row
    carries a value there.

    STAR This is what makes a two-theme toggle free: it answers "which half of
    THIS row" from the row itself, so swapping the row per scheme needs nothing
    added here.

    RED AND IT IS WHERE THE SPLIT'S ONE TRAP LIVES. A COMPLETE row has an empty
    alt band, so every token silently falls back to its native value and the
    palette renders in the wrong mode -- dark-on-light, no error, nothing to
    grep. Emptiness IS the row's assertion that it is one palette, so asking it
    for the opposite mode is a declaration error rather than a graceful
    fallback, and it is reported as one. `mid` is exempt: it has no opposite by
    design (maw-themes J12).
    """
    native = (row.get("mode") or "dark").strip()
    opposite = native in ("dark", "light") and scheme != native

    if opposite and not any(
        (value or "").strip()
        for token, value in row.items()
        if token.startswith("alt-")
    ):
        slug = (row.get("slug") or "?").strip()
        sibling = _sibling(row, scheme)
        state.note(
            "notes",
            "theme '" + slug + "' is a COMPLETE " + native + " palette (no "
            "alt- values) but was asked for the " + scheme + " scheme, so it "
            "is painting its " + native + " ramp there. "
            + ("Use '" + sibling + "' for " + scheme + " instead."
               if sibling else
               "No row shares its identity at " + scheme + " -- author one."),
        )

    decls = []
    for token in row:
        if token in _META or token.startswith("alt-"):
            continue
        value = ""
        if opposite:
            value = (row.get("alt-" + token) or "").strip()
        if not value:
            value = (row.get(token) or "").strip()
        if value:
            decls.append(("--dr-" + token, value))
    return decls


def _local_decls(themes: tuple[str, ...], scheme: str) -> list[tuple[str, str]]:
    """The local nine-token table -- still the only source for themes canonical
    has never heard of, and the only source for `dead` anywhere."""
    decls = []
    for row in _rows("colors.tsv"):
        if (row.get("theme") or "") not in themes:
            continue
        token = (row.get("token") or "").strip()
        value = (row.get(scheme) or "").strip()
        if token and value:
            decls.append(("--dr-" + token, value))
    return decls


def _typography(wanted: str, others: set[str]) -> list[str]:
    """Scheme-independent type. One theme supplies it. See the docstring."""
    out = []
    for row in _rows("typography.tsv"):
        if (row.get("theme") or "") not in ("base", wanted):
            continue
        token = (row.get("token") or "").strip()
        value = (row.get("value") or "").strip()
        if token and value:
            out.append("  --dr-" + token + ": " + value + ";")

    dropped = sorted(
        {
            (r.get("theme") or "").strip()
            for r in _rows("typography.tsv")
            if (r.get("theme") or "").strip() in others
        }
    )
    if dropped:
        state.note(
            "notes",
            "typography comes from '" + wanted + "' (the " + _PRIMARY
            + " theme). " + ", ".join(dropped) + " also declares typography "
            "rows and they are NOT applied -- type is scheme-independent by "
            "design, so only one theme can supply it.",
        )
    return out


# --------------------------------------------------------------------------


def build_css() -> str:
    """Return the generated custom-property sheet for the active instance."""
    _verify_source()

    slug = str(state.INSTANCE.get("slug", "?"))
    picked = {scheme: _theme_for(scheme) for scheme, _sel in _SCHEMES}
    split = len(set(picked.values())) > 1

    label = (
        ", ".join(s + ": " + t for s, t in picked.items()) if split
        else picked[_PRIMARY]
    )
    lines = [
        "/* GENERATED by docrender/theme.py -- do not edit.",
        "   Theme: " + label + ".",
        "   Values come from theme/*.tsv and instances/" + slug + "/theme.css.",
        "*/",
    ]

    for scheme, selector in _SCHEMES:
        wanted = picked[scheme]
        canonical = _canonical_row(wanted)
        decls: list[tuple[str, str]] = []

        if canonical:
            # Local `base` FIRST, and for one reason only: it carries `dead`,
            # which canonical has no equivalent for. Everything else it sets is
            # overridden by the aliases below. The local rows for the CHOSEN
            # theme are deliberately skipped -- emitting a value guaranteed to
            # be overwritten reads, in a diff, like a decision.
            decls += _local_decls(("base",), scheme)
            decls += _canonical_decls(canonical, scheme)
            # LAST. See the ordering note in the module docstring.
            decls += [
                ("--dr-" + local, "var(--dr-" + canon + ")")
                for local, canon in _aliases()
            ]
        else:
            decls += _local_decls(("base", wanted), scheme)

        if decls:
            lines.append(selector + " {")
            lines.extend(
                "  " + name + ": " + value + ";" for name, value in decls
            )
            lines.append("}")

    typography = _typography(
        picked[_PRIMARY],
        {t for s, t in picked.items() if s != _PRIMARY and t != picked[_PRIMARY]},
    )
    if typography:
        lines.append(":root {")
        lines.extend(typography)
        lines.append("}")

    for scheme, wanted in picked.items():
        row = _canonical_row(wanted)
        if row:
            complete = not any(
                (value or "").strip()
                for token, value in row.items()
                if token.startswith("alt-")
            )
            state.note(
                "notes",
                scheme + " scheme: theme '" + wanted + "' painted from the "
                "CANONICAL vector (mode '" + str(row.get("mode", "?")) + "', "
                + ("COMPLETE row" if complete else "legacy row with an alt- "
                   "band") + "). `dead` still comes from the local base rows "
                "-- no canonical equivalent (maw-themes D11).",
            )

    for row in _rows("contrast.tsv"):
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
