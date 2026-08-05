"""Hook 04 -- look, assembled from data rather than written as code.

An instance picks its theme by NAME in site.yml; this turns the chosen rows into
CSS custom properties and hands them to assets.py as a generated sheet. Changing
a site's whole look is ONE LINE in one data file. That is not a convenience, it
is the test of whether the theme layer is real: if changing a site's appearance
required touching code, the separation between engine and site would be
decorative.

THE PALETTE IS CANONICAL (2026-08-04). There were two files called `colors.tsv`.
One is the real design system in `mawizorek/maw-themes` -- 19 themes, 33 tokens,
also consumed by the ClickUp HTML apps and mapped onto FileMaker layout roles.
The other is `theme/colors.tsv` here: three themes and nine tokens, written in an
afternoon to unblock a demo. They shared a FILENAME and nothing else, and that
collision is why an edit to the real `eos` theme never showed up on the live site.

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
STAR 2026-08-04 -- THE TOGGLE CAN NOW CYCLE TWO DIFFERENT THEMES
=============================================================================

    theme: eos                          # one theme, both schemes
    theme: {dark: mclaren, light: eos}   # the toggle cycles two themes

The scalar form is unchanged and is still the common case.

WHY THIS COST ALMOST NOTHING, which is worth recording because it looks like it
should have cost a lot. `_canonical_decls(row, scheme)` already resolves
base-versus-alt from the ROW'S OWN `mode` against the requested scheme. So asking
a DIFFERENT row per scheme needs no new colour logic -- only a different answer to
"which slug". The colour path below is untouched by this feature.

AND THE ARCHITECTURE WAS ALREADY RULED, upstream, before anyone asked for it here.
maw-themes S1: "mode is not a property of the data at all. It is a CHOICE the app
makes... the APP owns the toggle" -- the list of themes a toggle cycles belongs in
the app's own config, never in the table. This is that ruling implemented.

MODE, AND THE PART THAT LOOKS LIKE A BUG. A canonical row is ONE theme in TWO
modes: base columns are its native ramp, the `alt-` band is the opposite one. So
`dark: mclaren` takes McLaren's BASE columns (it is a dark-native row) while
`light: eos` takes eos's ALT band. WARNING: the alt band covers GROUND AND TEXT
ONLY -- `accent`, `accent-deep`, `accent-2` and the four semantics are SHARED
across modes unless a row carries an explicit `alt-` cell for them. That is a
deliberate 2026-07-17 design already ruled for re-authoring per mode (maw-themes
D5) and only partly done. `mode: mid` (default-theme) has no opposite and an empty
alt band; both schemes get the native ramp, which is the documented graceful case
rather than a hole.

WARNING: TYPOGRAPHY DOES NOT SPLIT, and that is deliberate rather than an
oversight. `typography.tsv` is scheme-independent by design -- its own header says
type must not change between light and dark, because that is how a site ends up
with two type systems that drift apart. So under a two-theme toggle ONE of them
has to supply the type, and it is the DARK one, because dark is the default scheme
in mkdocs.yml. If the other theme carries typography rows they are DROPPED, and
the build names them -- a font quietly changing because a colour was swapped is
exactly the class of surprise this engine keeps writing down.

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

# Columns in a canonical row that are not tokens.
_META = ("slug", "name", "mode")


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


def _known() -> set[str]:
    """Every theme name an instance may legally ask for.

    The union is the point: reading the canonical slugs here is what makes all 19
    canonical themes selectable without anybody re-typing them into themes.tsv,
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

    The row's `mode` names its NATIVE ramp. When the requested scheme is the
    other one, an `alt-<token>` column wins if the row carries a value there.
    Falling back to the base column is not a defect: the alt band deliberately
    covers ground and text only, so accent and the semantics stay SHARED across
    modes until maw-themes D5 is authored.

    STAR: this is also what makes a two-theme toggle free. It answers "which
    half of THIS row" from the row itself, so swapping the row per scheme needs
    nothing added here.
    """
    native = (row.get("mode") or "dark").strip()
    opposite = native in ("dark", "light") and scheme != native

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
            state.note(
                "notes",
                scheme + " scheme: theme '" + wanted + "' painted from the "
                "CANONICAL vector (mode '" + str(row.get("mode", "?")) + "', "
                + ("its own ramp" if (row.get("mode") or "").strip() == scheme
                   else "its alt- band") + "). `dead` still comes from the "
                "local base rows -- no canonical equivalent (maw-themes D11).",
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
