"""Hook 04 -- look, assembled from data rather than written as code.

An instance picks a theme by NAME in its site.yml; this turns the chosen rows
into CSS custom properties and hands them to assets.py as a generated sheet.
Switching a whole site's look is ONE LINE in one instance file. That is not a
convenience, it is the test of whether the theme layer is real: if changing a
site's appearance required touching code, the separation between engine and
site would be decorative.

STAR 2026-08-04 -- THE PALETTE IS NOW CANONICAL, WHICH IS THE WHOLE REASON THIS
FILE CHANGED.

There were two files called `colors.tsv`. One is the real design system in
`mawizorek/maw-themes` -- 19 themes, 33 tokens, hand-authored, also consumed by
the ClickUp HTML apps and mapped onto FileMaker layout roles. The other is
`theme/colors.tsv` here: three themes and nine tokens, written in an afternoon
to unblock a demo. They shared a FILENAME and nothing else, and that collision
is exactly why an edit to the real `eos` theme never showed up on the live site.

`theme/canonical/colors.tsv` is a vendored, byte-verified copy of the real one.
A theme WITH a canonical row is painted from it. A theme WITHOUT one keeps the
local table and renders exactly as it did, so shipping this cannot re-shape a
site nobody touched.

WHY VENDORED AND NOT FETCHED. A build that reaches the network can produce
different bytes on two runs from one commit, and this engine publishes from CI
where that failure is invisible. The copy is proved by its git blob SHA, checked
on every build against `canonical/source.tsv`, so tampering is caught and the
build stays hermetic. WARNING: the check cannot see UPSTREAM drift. It proves
the file is what we vendored, not that what we vendored is still current. That
needs a scheduled job with network and does not exist yet -- said plainly,
because a green check answering a narrower question than the reader assumes is
worse than no check at all.

NINE OF THE TEN TOKEN NAMES WERE ONLY A RENAME. surface->bg, ink->text,
rule->border, danger->bad, ok->good, and so on. Those are emitted as ALIASES
(`--dr-ink: var(--dr-text)`), so every `var(--dr-ink)` already written in a
stylesheet keeps working and nothing had to be found and replaced across the
asset layer. The map is DATA, in `canonical/aliases.tsv`, because a rename table
in a paragraph cannot be diffed.

RED `dead` IS THE ONE TOKEN CANONICAL DOES NOT HAVE. A reference to a page
nobody has written yet is not an error, and sharing `danger` made it read as
one. It is raised upstream as maw-themes D11 and awaits authored values, so the
local `base` rows are still emitted UNDERNEATH the canonical block purely to
keep it alive. That is the only reason the old table is still loaded at all.

MODE, AND THE PART THAT LOOKS LIKE A BUG. A canonical row is ONE theme in TWO
modes: the base columns are its native ramp, the `alt-` band is the opposite
one. WARNING: the band covers GROUND AND TEXT ONLY -- accent, accent-deep,
accent-2 and the four semantics are SHARED across modes. That is a deliberate
2026-07-17 design which measurably produces illegible pairs, already ruled for
re-authoring per mode (maw-themes D5) and NOT YET AUTHORED. So a light-mode
reader gets the dark accent, on purpose, until those values exist. `mode: mid`
(default-theme) has no opposite and an empty alt band; both schemes get the
native ramp, which is the documented graceful case rather than a hole.

What is deliberately NOT shared: the sites must not look identical. TOKEN NAMES
are shared and VALUES are per theme, so the day somebody edits a colour to fix
one site is not the day another breaks quietly.

OVERRIDE ORDER IS LOAD-BEARING, in this exact sequence: local `base` rows, then
the canonical block, then the aliases. Later declarations win at equal
specificity, so the aliases MUST come last -- put them anywhere else and
`--dr-ink` keeps the stand-in's value while every file involved still looks
correct. A silent no-op is the failure mode this ordering exists to prevent.

Typography, forms and spacing are a SEPARATE vector and are not part of this
join; they still come from `theme/typography.tsv`. Colour was the axis with two
disagreeing tables. Type was not, and widening the change would have made the
first real test unreadable.

contrast.tsv is not decoration. It is the measured accessibility floor, and a
palette that drops below it gets reported.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from . import state
from .util import load_tsv

# Material writes the active scheme onto the document; `slate` is its dark
# scheme and `default` its light one. Emitting both on every build is what lets
# a reader use the toggle without the site fetching anything.
_SCHEMES = (
    ("dark", '[data-md-color-scheme="slate"]'),
    ("light", '[data-md-color-scheme="default"]'),
)

# Columns in a canonical row that are not tokens.
_META = ("slug", "name", "mode")


def _theme_dir() -> Path:
    return Path(state.ENGINE_ROOT) / "theme"


def _rows(name: str) -> list[dict]:
    return load_tsv(_theme_dir() / name)


# --------------------------------------------------------------------------
# The canonical table
# --------------------------------------------------------------------------


def _canonical_rows() -> list[dict]:
    return load_tsv(_theme_dir() / "canonical" / "colors.tsv")


def _canonical_row(slug: str) -> dict | None:
    for row in _canonical_rows():
        if (row.get("slug") or "").strip() == slug:
            return row
    return None


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


def _canonical_decls(row: dict, scheme: str) -> list[tuple[str, str]]:
    """Token declarations for one canonical row in one colour scheme.

    The row's `mode` names its NATIVE ramp. When the requested scheme is the
    other one, an `alt-<token>` column wins if the row carries a value there.
    Falling back to the base column is not a defect: the alt band deliberately
    covers ground and text only, so accent and the semantics stay SHARED across
    modes until maw-themes D5 is authored.
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


# --------------------------------------------------------------------------
# The local table -- still the only source for themes canonical has never heard
# of, and the only source for `dead` anywhere.
# --------------------------------------------------------------------------


def _local_decls(themes: tuple[str, ...], scheme: str) -> list[tuple[str, str]]:
    decls = []
    for row in _rows("colors.tsv"):
        if (row.get("theme") or "") not in themes:
            continue
        token = (row.get("token") or "").strip()
        value = (row.get(scheme) or "").strip()
        if token and value:
            decls.append(("--dr-" + token, value))
    return decls


# --------------------------------------------------------------------------


def _known() -> set[str]:
    """Every theme name an instance may legally ask for.

    The union is the point: reading the canonical slugs here is what makes all
    19 canonical themes selectable without anybody re-typing them into
    themes.tsv, which would be a second list to keep in step.
    """
    named = {(r.get("theme") or "").strip() for r in _rows("themes.tsv")}
    slugs = {(r.get("slug") or "").strip() for r in _canonical_rows()}
    return {n for n in named | slugs if n}


def _wanted() -> str:
    wanted = str(state.INSTANCE.get("theme", "base"))
    known = _known()
    if wanted not in known:
        listed = ", ".join(sorted(known)) or "none"
        state.note(
            "notes",
            "theme '" + wanted + "' is not in theme/themes.tsv or the "
            "canonical table; falling back to 'base'. Known: " + listed,
        )
        return "base"
    return wanted


def build_css() -> str:
    """Return the generated custom-property sheet for the active instance."""
    _verify_source()

    wanted = _wanted()
    slug = str(state.INSTANCE.get("slug", "?"))
    canonical = _canonical_row(wanted)

    lines = [
        "/* GENERATED by docrender/theme.py -- do not edit.",
        "   Theme: " + wanted
        + (" (CANONICAL)" if canonical else " (local table)") + ".",
        "   Values come from theme/*.tsv and instances/" + slug + "/theme.css.",
        "*/",
    ]

    for scheme, selector in _SCHEMES:
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

    typography = []
    for row in _rows("typography.tsv"):
        if (row.get("theme") or "") not in ("base", wanted):
            continue
        token = (row.get("token") or "").strip()
        value = (row.get("value") or "").strip()
        if token and value:
            typography.append("  --dr-" + token + ": " + value + ";")
    if typography:
        lines.append(":root {")
        lines.extend(typography)
        lines.append("}")

    if canonical:
        state.note(
            "notes",
            "theme '" + wanted + "' painted from the CANONICAL vector "
            "(theme/canonical/colors.tsv, mode '"
            + str(canonical.get("mode", "?")) + "'). "
            + str(len(_aliases())) + " local token names aliased onto canonical "
            "roles. `dead` still comes from the local base rows -- it has no "
            "canonical equivalent (maw-themes D11).",
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
