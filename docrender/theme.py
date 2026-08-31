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

ONCE MORE, IN `@media print` (2026-08-19):

  9. THE PAPER BLOCK          whichever resolved row declares `mode: light`,
                              emitted UNSCOPED **and** onto both scheme
                              selectors. See below.

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
🔴 THE PAPER BLOCK -- IT ASKS THE `mode` COLUMN, NOT THE SLOT NAME
=============================================================================
> Michael, 2026-08-19, on a print that came out cream on white: *"mercedes-light?
> i'm rendering in papyrus rn???"*

🪦 **THAT IS A BUG I SHIPPED AN HOUR EARLIER, AND THE FIRST VERSION OF THIS BLOCK
CAUSED IT.** It asked for `picked["light"]` -- and "light" is a SLOT NAME, not a
mode. `vectors.PRIMARY` is `dark`, so the primary slot takes a join's `color` and
the other slot takes its `alt-color`.

⚠️ AND EXACTLY ONE JOIN IN THE REGISTRY RUNS THE OTHER WAY:

    papyrus     color: papyrus (LIGHT)     alt-color: papyrus-dark
    everything   color: <dark>              alt-color: <light>
    else

So on `papyrus` the "light" slot holds **papyrus-dark**, whose `text` is
`#f0e6d2` -- cream. Paper asked for the light SLOT, got a dark ROW, and printed
cream ink on white with the background dropped. 🔴 **Both schemes then printed
identically and both were wrong, which is strictly worse than the asymmetry it
replaced: a wrong answer that agrees with itself looks like a working fix.**

⭐ AND THE REGISTRY HAD ALREADY WRITTEN BOTH HALVES DOWN. `themes.json` says of
papyrus: *"this is the one join whose PRIMARY is light and whose alt is dark --
proof the pair carries no assumption about which way round it goes."* Its rules
block says of the column that answers this: *`mode` "is descriptive, and it exists
so a consumer can warn when a dark palette lands in a light slot."*
**The one column that answers the question, and the first version never read it.**
⚑ *A constant named `_PAPER_SCHEME = "light"` reads as a fact about colour and is
actually a fact about SLOT ORDER. Naming a thing after what you want it to mean is
how a wrong read survives review.*

✅ SO THE ROW IS SELECTED BY ITS OWN `mode` CELL, and the slot it happened to
occupy is now irrelevant. `_paper_row()` walks the resolved schemes and takes the
first whose row declares `mode: light`. On papyrus that is the PRIMARY slot; on
eos, database and every other join it is the alt slot. **Neither the caller nor
this file needs to know which, which is the entire point.**

=============================================================================
🔴 AND ON 2026-08-31 IT GAINED AN UNSCOPED COPY, BECAUSE BOTH SELECTORS CAN MISS
=============================================================================
> Michael, printing a program page from a script and getting a near-black sheet
> with washed-out text, having just printed the SAME page by hand perfectly:
> *"everything else prints justtt fine - just your version."*

🔴 **THE PAPER BLOCK WAS EMITTED ONTO TWO ATTRIBUTE SELECTORS AND NOTHING ELSE, SO
A DOCUMENT CARRYING NEITHER ATTRIBUTE GOT NO PAPER PALETTE AT ALL.** Not a wrong
colour -- **no colour**, which is the exact failure this file's own next section
warns about for a different cause: *"`var(--dr-ink)` with no fallback collapses to
nothing."* The warning was written about `@media screen` and was true about this.

⚡ **AND THE TRIGGER IS A DEFAULT NOBODY THOUGHT OF AS ONE.** `mkdocs.yml` lists
`- scheme: slate` FIRST and calls it *"the default, and the toggle offers the other
one."* Material writes `data-md-color-scheme` from **localStorage**, so:

    a reader who has toggled  ->  attribute present  ->  paper block applies
    a FRESH profile           ->  attribute absent/slate before JS settles

Michael prints from his own browser, where he has chosen light and the attribute is
written. **A headless print starts from a brand-new profile every single time** --
`bin/print-packets.py` mints a fresh `--user-data-dir` per page ON PURPOSE -- so it
is the one reader for whom the toggle has never been touched.

⚑ **THE GENERALISATION, AND IT IS THE THIRD TIME THIS CLASS HAS BITTEN THIS
FEATURE IN TWO DAYS: A RULE SCOPED TO STATE IS UNREACHABLE FOR A READER WHO HAS NO
STATE.** `visibility.py`, `qr.py` and this file now all record a version of it. The
tell available in advance: **both** selectors were attribute selectors, so the
block had no answer for a document with no attributes, and nothing in the emit
reported that a `:root` case existed.

✅ THE FIX IS ONE MORE BLOCK AND IT CANNOT REGRESS THE OTHER TWO. `:root` is
(0,1,0) and an attribute selector is (0,1,0) -- a TIE, broken by source order, and
the unscoped copy is emitted FIRST. So a document WITH an attribute resolves
exactly as it did before (identical values, later block wins), and a document
WITHOUT one now resolves too. ⭐ *It also makes a printed sheet independent of the
reader's toggle, which is Michael's own 08-21 ruling -- printed content must not
differ per reader -- finally true in the mechanism rather than by luck.*

🚫 NOT FIXED IN THE PRINT SCRIPT, DELIBERATELY. Forcing a light scheme with a
Chrome flag would have made the scripted print differ from a manual one, and
**"identical to Ctrl+P on that page" is the entire premise the packet rests on.**
The defect was in the engine and it was wrong for hand-printing too: anybody
printing from a fresh browser, an incognito window or a shared machine got this
sheet. Fixing the flag would have hidden a live bug from every real reader.

=============================================================================
⭐ WHY NOT `@media screen` AROUND THE SLATE BLOCK, WHICH IS WHAT MATERIAL DOES
=============================================================================
Material wraps its ENTIRE slate scheme in `@media screen` (`palette/_scheme.scss`,
commented *"Only use dark mode on screens"*). Copying that here would print a page
with NO COLOUR AT ALL.

The difference is structural. Material declares its light values UNSCOPED, so
silencing slate on paper leaves the defaults standing. This file declares BOTH
schemes scoped -- and, until 2026-08-31, nothing unscoped. ⚑ **Silencing a scheme on
paper would leave every `--dr-*` token UNDEFINED for the readers in it**, and
`var(--dr-ink)` with no fallback collapses to nothing. Not a wrong colour: no
colour. 🔴 That is exactly what happened to a no-attribute document, by a different
route -- see the section above. **The paragraph was right and it was filed against
the wrong mechanism.**

🪦 AND IT RETIRED `assets/print-scheme.css`, WHICH WAS WORSE THAN BOTH. That sheet
forced sixteen hardcoded greys with `!important`: it ignored the vector entirely,
and it replaced the NEUTRALS while leaving the SEMANTICS dark -- a mix that exists
in no row of any table. The light row is a set somebody designed as a set.

✅ AND THIS NEEDS NO `!important`, WHICH IS THE REAL GUARANTEE. The old sheet needed
it because nobody could explain why a cross-sheet tie against `tokens.css` had
lost. This block is IN tokens.css, after the blocks it corrects, at equal
specificity -- later-in-file wins, deterministically, with no second file involved.

🚫 WHAT IT DELIBERATELY DOES NOT DO: compensate for the semantic-token defect
`print.css` documents. On 16 of 19 canonical pairs `good`/`warn`/`bad`/`info` are
BYTE-IDENTICAL between the dark and light rows, so those print unchanged and print
remains the surface where that shows worst. The fix belongs in the light rows of
`canonical/colors.tsv`.

⚠️ THE THREE SCHEME-INDEPENDENT VECTORS ARE UNTOUCHED BY ALL OF THIS. Typography,
forms and spacing are emitted once in `:root` and are not scheme-scoped, so the
face, the sizes, the tracking and the spacing on paper are already exactly what
the vector declares. Only COLOUR ever needed a medium. ⭐ *And that is the clue that
was sitting in this file the whole time: the three vectors that printed correctly
from a fresh profile were the three emitted UNSCOPED.*

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
blocks.py both carry. ⚠️ THE PAPER BLOCK'S "no light row" NOTE JOINS THEM AND WILL
ALSO REPEAT -- accepted knowingly, because it fires only on a two-dark theme and a
repeated warning is better than a fourth flag.

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

#: 🔴 THE PAPER BLOCK'S UNSCOPED SELECTOR. Emitted BEFORE the two attribute
#: selectors, which is what makes it a safety net rather than an override: `:root`
#: and `[data-md-color-scheme=...]` are both (0,1,0), so on a document that HAS the
#: attribute the later block wins with identical values, and on one that has NO
#: attribute this is the only thing that matches. See the 08-31 section in the
#: module docstring for the near-black sheet that proved the case exists.
_PAPER_UNSCOPED = ":root"

#: 🔴 THE `mode` CELL PAPER LOOKS FOR. Paper is always a light ground, so it wants
#: the row that DECLARES itself light -- never the slot that happens to be called
#: light. See the paper-block section in the module docstring for the papyrus bug
#: that made this a constant instead of a slot lookup.
_PAPER_MODE = "light"

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


def _scheme_decls(got: dict, scheme: str) -> list[tuple[str, str]]:
    """Every colour declaration for one resolved scheme, in emit order.

    ⭐ EXTRACTED 2026-08-19 SO THE PAPER BLOCK CANNOT DRIFT FROM THE SCREEN ONES.
    This was inline in `build_css`, and the paper block needs byte-identical
    construction -- local base, then the canonical row, then the aliases LAST.
    Copying those four steps would have been a second claimant on the emit order,
    which is the defect this repo has retired three manifests over.

    ⚠️ `scheme` IS ONLY USED TO PICK A COLUMN OUT OF THE LOCAL NINE-TOKEN TABLE,
    which has literal `dark` and `light` columns. It does NOT choose the canonical
    row -- `got` already carries that. Worth stating because conflating the two is
    precisely the papyrus bug: a slot name is not a mode.
    """
    row = got["colorRow"]
    if not row:
        # No join, or a theme canonical has never heard of. The local nine-token
        # table is the whole palette, and it has its own per-scheme columns.
        return _local_color(("base", got["color"]), scheme)

    # Local `base` FIRST, for one reason: it carries `dead`. The local rows for
    # the CHOSEN theme are skipped -- emitting a value that is guaranteed to be
    # overwritten reads, in a diff, like a decision.
    decls = _local_color(("base",), scheme)
    decls += _color_decls(row)
    # LAST. See the ordering note in the module docstring.
    decls += [
        ("--dr-" + local, "var(--dr-" + canon + ")")
        for local, canon in _pairs("aliases.tsv")
    ]
    return decls


def _paper_row(picked: dict) -> tuple[dict, str] | None:
    """The resolved scheme whose colour row DECLARES `mode: light`, or None.

    🔴 THIS FUNCTION IS THE WHOLE PAPYRUS FIX. The caller used to ask for the slot
    named "light", which is slot ORDER and not colour. `papyrus` pairs a light
    PRIMARY with a dark alt, so that lookup handed paper a cream palette. Read the
    `mode` cell and the slot stops mattering.

    Returns the (resolved, scheme_key) pair rather than just the row, because
    `_scheme_decls` needs the scheme key to index the local nine-token table's
    `dark`/`light` columns.

    ⚠️ DETERMINISTIC ORDER: `_SCHEMES` is walked, so a theme that somehow declares
    TWO light rows takes the primary one. That is not a real case today and the
    tie is broken openly rather than by dict ordering.

    🚫 RETURNS None RATHER THAN A FALLBACK when no row says light. A join may
    legally pair two darks (`themes.json`: *"two darks, two lights,
    normal-and-party"*), and for such a theme there is no light palette to print.
    Guessing one is what the caller used to do.
    """
    for scheme, _sel in _SCHEMES:
        got = picked.get(scheme) or {}
        row = got.get("colorRow")
        if row and (row.get("mode") or "").strip().lower() == _PAPER_MODE:
            return got, scheme
    return None


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
        decls = _scheme_decls(picked[scheme], scheme)
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

    # 🔴 THE PAPER BLOCK. Whichever row DECLARES itself light, painted UNSCOPED and
    # onto BOTH scheme selectors, so it cannot matter which slot a join put it in
    # NOR whether the document carries a scheme attribute at all. See the module
    # docstring for the papyrus bug and the 08-31 no-attribute sheet this shape
    # exists to prevent, and for why this is not `@media screen` around a scheme
    # block.
    found = _paper_row(picked)
    if found is None:
        state.note(
            "notes",
            "paper: no colour row in this theme declares `mode: light`, so the "
            "print sheet re-points NOTHING and paper renders Material's own "
            "light defaults. Expected for a theme pairing two dark palettes; "
            "add a light row to the join if a printed page matters here.",
        )
    else:
        got, paper_scheme = found
        paper = _scheme_decls(got, paper_scheme)
        if paper:
            lines.append("@media print {")
            # 🔴 UNSCOPED FIRST. It is the only block that matches a document with
            # no `data-md-color-scheme` attribute -- a fresh profile, an incognito
            # window, or a headless print. Equal specificity to the two below, so
            # emitting it first means a document that HAS the attribute resolves
            # exactly as it did before this line existed.
            for selector in (_PAPER_UNSCOPED,):
                lines.append("  " + selector + " {")
                lines.extend(
                    "    " + name + ": " + value + ";" for name, value in paper
                )
                lines.append("  }")
            for _scheme, selector in _SCHEMES:
                lines.append("  " + selector + " {")
                lines.extend(
                    "    " + name + ": " + value + ";" for name, value in paper
                )
                lines.append("  }")
            lines.append("}")
            state.note(
                "notes",
                "paper: the light palette is emitted UNSCOPED and on both scheme "
                "selectors, so a printed sheet is identical whether or not the "
                "reader has ever touched the theme toggle. A no-attribute "
                "document (fresh profile, incognito, headless print) used to get "
                "NO paper palette at all.",
            )

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
