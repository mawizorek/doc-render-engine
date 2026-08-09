"""Stage 03b -- inline markers, in CLASSES, rendered as spans.

    [To be confirmed]{.tbc}                 a span, no underline
    Grid height [18'-0"]{.est} above deck
    A [source 4]{.term} is an ERS fixture

The LINK form -- `[ETC](@term:etc)`, `[fkCal](@rel:table-events)` -- lives in
docrender/markerlinks.py, which also carries the history of the two-form design.
This file owns the DATA and the PAINT.

Decision history: doc-render-engine (repo) Decision Log in ClickUp, Q6/J7 for the
class axis and J8 for the `@term:` prefix; maw-themes J11 for the colour token.


TWO AXES OF MEANING
===================

Every marker used to be a confidence claim, and that narrowness protected the
BUILD REPORT: "what is unconfirmed across this whole site" is answerable only
while every row answers the same question. What was missing was a way to say
which kind a row IS -- so terminology was nearly built as a second, parallel
family, because the table had no column for it.

`class` is now a column, families live in theme/marker-classes.tsv, and the
report groups by class. Confidence stays answerable however many terms a site
marks.

SHAPE IS A CLOSED SET OF FOUR (box, plain, strike, soft): four are
distinguishable at a glance, nine are not. Three families in a row have wanted a
fifth and needed none -- terminology wanted colour without an underline, which is
`plain`; highlight wanted a heavier tint, which is a NUMBER on `box` (`wash`, a
column on marker-classes.tsv); and the FMP pair split on `box` against `plain`.
⚑ A request for a new VARIANT is a request for a new PARAMETER far more often
than a new KIND, and the tell is whether you can state the difference without
using a number.


🔴 THIS FILE WAS SPLIT ON 2026-08-09, AND THE ARGUMENT AGAINST SPLITTING IT
===========================================================================

The docstring that used to sit here said this module claimed `@term:` itself
"not for tidiness, but so the two forms cannot disagree about which family they
are... A second module would be a second place to name the family."

That was correct, and it stopped being true rather than being overruled.

⚑ THE OBJECTION DISSOLVED WHEN THE FAMILY MOVED INTO THE DATA. `_TERM_CLASS =
"terminology"` was a constant in Python, so a second module genuinely would have
been a second place naming it. markers.tsv now carries a `prefix` column, so both
forms look the family up in the SAME ROW of the same table and NEITHER module
names one. There is no fact left for them to disagree about. ⭐ Generally: an
argument against splitting a file is usually an argument about a SHARED CONSTANT,
and it expires the moment that constant becomes data.

⚠️ WHAT FORCED IT was size -- 23,084 B against a ~22KB safe-edit ceiling, in the
one module whose history includes killing every site at once.

🔴 AND THE FIRST ATTEMPT AT THIS SPLIT CAME OUT AT 26,362 B. The code left and the
prose grew, so the change failed the exact test that justified it while looking
like it passed. ⚑ A refactor justified by a NUMBER has to have the number read
back, and that byte count was in the API response the whole time. Same family as
every unverified size claim this repo has written down.

🚨 THE SEAM IS THE TABLE, NEVER A FUNCTION. markerlinks imports `table()`,
`marker_rows()` and `LINK_CLASS` -- data and one name. It does NOT import
`_colour`, and must not: that helper encodes THIS module's policy, and sharing a
resolver that encodes one module's policy is what broke the build on 2026-08-05.


COLOUR IS RESOLVED ONCE PER BUILD, AND THAT IS A FIX
====================================================

`_colour()` used to run inside the per-MATCH replacement, so an unknown token
reported once per OCCURRENCE -- a terminology class used three hundred times
would have buried the report under three hundred copies of one complaint, and the
report is the only reason this beats a highlighter.

The table is merged in `on_files`, once. In an event and not at import, because
`mkdocs serve` rebuilds in-process and a table cached at import would outlive an
edit to either TSV.

⚠️ THE ONE THING READ AT IMPORT IS THE `prefix` COLUMN, by markerlinks, through
`marker_rows()`. A namespace must be claimed before any page renders, so that read
cannot wait for an event. The cost is stated where it is paid: a prefix ADDED
during a live `mkdocs serve` session needs a restart, and markerlinks reports it.
Everything else about a marker stays hot.


🔴 THE VALIDATION LIST WENT STALE WHEN THE PALETTE MOVED (fixed 2026-08-05)
==========================================================================

`_known_tokens()` read theme/colors.tsv and nothing else -- the nine-token
stand-in -- while the engine had been emitting the CANONICAL 22 since the
four-vector join. Exactly two names overlap, so every other canonical token was
REFUSED by a validator that had never heard of it. The visible cost was one cell
asking for `accent-soft`, reported unknown once per build, quietly painting in the
body colour -- long enough that the comment explaining it read as a plan.

☑ A PALETTE MOVED AND THE LIST OF WHAT IS ALLOWED DID NOT: a second place stating
a fact the first place already owns. The union now reads the canonical table's own
HEADER ROW, so a column added upstream is usable the day it is vendored.

⚠️ THE NEAR-MISS THAT SURVIVES IT IS `accent-1`, WHICH DOES NOT EXIST -- the four
are `accent`, `accent-deep`, `accent-2`, `accent-soft`. It is a legal token NAME,
so it passes the regex, fails the set, and lands in the report line everybody read
as "not vendored yet" for two days. Named in markers.tsv, where the cell is typed.

⚠️ AND WASH IS NOT A FREE DIAL: a chip's text sits on a wash of ITSELF, so raising
it lowers text-against-chip contrast. Measure the chip, not the page.

Defined in theme/markers.tsv + theme/marker-classes.tsv. Adding one is a row.
"""

from __future__ import annotations

import html
import re

from . import state, vectors
from .util import load_tsv, sub_outside_code

# [text]{.marker} with optional whitespace, or bare {.marker}.
#
# ⚠️ THE TEXT GROUP FORBIDS `]`, SO A MARKER SPAN CANNOT HOLD A LINK.
# `[Saved [SET](@table-print-sets)]{.button}` does not fail -- it matches the BARE
# form and renders a chip carrying the row's label, leaving the link beside it as
# ordinary markdown. The link form is the answer: put a prefix on the row and
# write `[SET](@rel:table-print-sets)`.
_MARK = re.compile(
    r"(?:\[(?P<text>[^\]\n]*)\])?\{[ \t]*\.(?P<marker>[a-z][a-z0-9-]*)[ \t]*\}"
)

# A colour that is a bare word is a TOKEN and resolves against the theme. Any
# thing else -- #hex, oklch(...), rgb(...) -- is passed through as written.
_TOKEN = re.compile(r"^[a-z][a-z0-9-]*$")

#: A wash is a PERCENTAGE and nothing else -- deliberately narrower than what
#: color-mix() accepts, because every alternative renders as something plausible
#: and wrong. A bare number is DROPPED by color-mix (no background at all), and a
#: length unit computes to a different tint than the author read in the cell.
_WASH = re.compile(r"^(?:100|[1-9]?[0-9])%$")

#: Stated here AND as the fallback inside the emitted var(). Not redundancy: the
#: var() fallback is what protects a page if this sheet fails to load at all.
_DEFAULT_WASH = "10%"

_SHAPES = {"box", "plain", "strike", "soft"}
_FALLBACK_SHAPE = "box"

#: Carried by the LINK form on top of its family class, so an anchor can take the
#: family colour without also taking `.dr-mark` -- whose `cursor: help` and
#: `white-space: nowrap` are both wrong on something clickable. Defined HERE
#: because this module owns paint and emits the rule; markerlinks imports the name.
#:
#: 🔴 RENAMED FROM `dr-term` ON 2026-08-09 -- one marker's name on a mechanism now
#: serving seven. Verified rather than assumed: a code search returned nothing,
#: WHICH IS NOT EVIDENCE, so assets/base.css was read in full and carries no
#: `.dr-term` rule. The generated rule below was always its only home.
LINK_CLASS = "dr-mark-link"

#: Marker name -> resolved row. Built by on_files, read by on_page_markdown AND by
#: markerlinks through `table()`.
_TABLE: dict[str, dict] = {}


def _rows(name: str) -> list[dict]:
    return load_tsv(state.ENGINE_ROOT / "theme" / name)


def marker_rows() -> list[dict]:
    """The RAW markers.tsv rows, unresolved.

    Public for one caller and one purpose: markerlinks reads the `prefix` column at
    IMPORT time, before any event has run and therefore before `_TABLE` exists.

    🚨 DO NOT REACH FOR THIS TO GET A MARKER'S COLOUR, SHAPE OR CLASS. Those are
    only correct after `_build_table()` has merged the row with its family: a raw
    row's `shape` cell is blank on almost every marker, because blank means INHERIT.
    Use `table()` for anything that has to be right.
    """
    return _rows("markers.tsv")


def table() -> dict:
    """The RESOLVED marker table. Empty until on_files has run.

    The entire seam between this module and markerlinks: data, not behaviour. A
    caller reading a name that is not here should degrade rather than fail -- an
    unstyled link is still a working link.
    """
    return _TABLE


def _classes() -> dict[str, dict]:
    return {r["class"]: r for r in _rows("marker-classes.tsv") if r.get("class")}


def _known_tokens() -> set[str]:
    """Every colour token a marker may legally name: the union of both tables.

      LOCAL      theme/colors.tsv, the nine-token stand-in. Still contributes
                 `dead`, which canonical genuinely lacks (maw-themes D11) and
                 which is the only reason that file is still loaded at all.
      CANONICAL  theme/canonical/colors.tsv, read from its HEADER ROW rather
                 than from a list kept here. No third place to update.

    ⚠️ THIS ANSWERS "MAY A MARKER NAME IT", NOT "IS IT EMITTED". A canonical token
    is emitted only by a theme that has a join; a nine-token local theme emits a
    handful. A marker naming a token the ACTIVE theme does not emit resolves to
    `var(--dr-x)` with no fallback, which paints nothing -- so the honest widening
    is to accept the name and let the theme decide.
    """
    local = {r["token"] for r in _rows("colors.tsv") if r.get("token")}

    canonical: set[str] = set()
    for row in vectors.rows("colors.tsv"):
        canonical = {k for k in row if k not in vectors.META and k}
        break

    return local | canonical


def _colour(value: str, where: str, tokens: set[str], report: bool = True) -> str:
    """Resolve a colour to something CSS can use.

    `report` exists because build_css() runs from assets._plan, which is called by
    BOTH on_config and on_files and would therefore complain twice about one bad
    cell. The single honest complaint comes from _build_table, which runs once.

    🚨 PRIVATE TO THIS MODULE AND IT STAYS THAT WAY. It encodes a POLICY -- an
    unresolvable token falls back to the body colour rather than painting nothing --
    which is right for a marker and wrong for other consumers. Exporting a resolver
    that encodes one module's policy is what took every site down on 2026-08-05.
    markerlinks shares the TABLE and never this.
    """
    value = (value or "").strip()
    if not value:
        return "currentColor"
    if not _TOKEN.match(value):
        return value
    if value in tokens:
        return "var(--dr-" + value + ")"
    if report:
        # Falling back silently would render an INVISIBLE marker -- var() with no
        # fallback resolves to nothing -- so it is reported and given a real colour.
        state.note(
            "notes",
            where + " asks for colour token '" + value + "', which is in neither "
            + "theme/colors.tsv nor theme/canonical/colors.tsv. Using the body "
            + "colour. Known tokens: " + ", ".join(sorted(tokens)),
        )
    return "currentColor"


def _wash(value: str, where: str, report: bool = True) -> str:
    """Validate a family's chip tint. Returns "" to mean "emit nothing".

    Empty is the NORMAL answer and is never reported: a family that does not
    mention wash is inheriting the default on purpose, and every family but one
    does.

    ⚠️ A REJECTED WASH FALLS BACK TO THE DEFAULT, which is the OPPOSITE of what
    _colour does with a bad token, deliberately. An unresolvable colour must not be
    quietly substituted -- the marker would be the wrong colour and nobody could
    tell by looking. A wash reverting to 10% is a chip that looks like every other
    chip: legible, and obviously not the emphasis that was asked for.
    """
    value = (value or "").strip()
    if not value:
        return ""
    if _WASH.match(value):
        return value
    if report:
        state.note(
            "notes",
            where + " asks for wash '" + value + "', which is not a percentage "
            + "between 0% and 100%. Using " + _DEFAULT_WASH + ". A bare number "
            + "is dropped by color-mix() and paints no chip at all, which is why "
            + "only one spelling is accepted here.",
        )
    return ""


def _build_table() -> dict[str, dict]:
    """Merge every marker row with its class defaults. Once per build."""
    classes = _classes()
    tokens = _known_tokens()
    table: dict[str, dict] = {}

    if not classes:
        state.note(
            "notes",
            "theme/marker-classes.tsv is missing or empty, so every marker falls "
            + "back to a boxed body-coloured chip. Markers still render; the "
            + "families do not.",
        )

    # Reported here rather than in build_css so one bad cell complains once.
    for name in sorted(classes):
        where = "marker class '" + name + "'"
        _colour(classes[name].get("color", ""), where, tokens)

        wash = _wash(classes[name].get("wash", ""), where)
        shape = (classes[name].get("shape") or "").strip()
        if wash and shape and shape != "box":
            # Not an error -- only `box` paints a ground, so the cell is inert.
            # Said out loud because the author is looking at a real value in a
            # real column and reasonably expects it to do something.
            state.note(
                "notes",
                where + " sets wash '" + wash + "' but its shape is '" + shape
                + "', which paints no background. Wash applies to `box` only, so "
                + "this cell has no effect. Nothing is broken; the value is inert.",
            )

    for row in _rows("markers.tsv"):
        name = row.get("marker")
        if not name:
            continue

        klass = (row.get("class") or "").strip()
        parent = classes.get(klass) or {}
        if not klass:
            state.note(
                "notes",
                "marker '" + name + "' declares no class. Every row belongs to a "
                + "family now -- that is what keeps the report answerable once not "
                + "every marker is a confidence claim.",
            )
        elif klass not in classes:
            state.note(
                "notes",
                "marker '" + name + "' is in class '" + klass + "', which is not in "
                + "theme/marker-classes.tsv. Known: "
                + (", ".join(sorted(classes)) or "none") + ".",
            )

        shape = (row.get("shape") or parent.get("shape") or _FALLBACK_SHAPE).strip()
        if shape not in _SHAPES:
            state.note(
                "notes",
                "marker '" + name + "' resolves to shape '" + shape + "', which is "
                + "not one of " + ", ".join(sorted(_SHAPES)) + ". Using '"
                + _FALLBACK_SHAPE + "'.",
            )
            shape = _FALLBACK_SHAPE

        own = (row.get("color") or "").strip()
        table[name] = {
            "class": klass,
            "label": row.get("label") or "",
            "shape": shape,
            "tooltip": row.get("tooltip") or "",
            # Carried on the resolved row so the link side reads ONE row for both
            # halves. This module never acts on it -- a span has no namespace.
            "prefix": (row.get("prefix") or "").strip(),
            # A row override becomes an inline property. An unset colour inherits
            # the generated class rule and needs nothing on the span at all.
            "colour": _colour(own, "marker '" + name + "'", tokens) if own else "",
        }
    return table


def build_css() -> str:
    """Class colours as real rules. Published as marks.css by assets.py.

    Specificity is deliberate: `.md-typeset .dr-mark--cls-x` is two classes and
    beats base.css's one-class `.dr-mark` currentColor default, so base.css does
    not need to know this sheet exists. A ROW override is inline and beats both.
    Shape stays in base.css; colour and the chip tint are generated.
    """
    classes = _classes()
    tokens = _known_tokens()

    lines = [
        "/* GENERATED by docrender/markers.py -- do not edit.",
        "   One rule per marker CLASS, from theme/marker-classes.tsv,",
        "   plus the chip-tint rule and the one static rule for link-form markers.",
        "   Shape lives in assets/base.css; colour and tint are data. */",
    ]
    for name in sorted(classes):
        decls = [
            "--dr-mark-color: "
            + _colour(
                classes[name].get("color", ""),
                "marker class '" + name + "'",
                tokens,
                report=False,
            )
        ]
        # Emitted ONLY when the family declares one, so a blank cell leaves the
        # var() fallback to supply the default. Writing 10% onto every class
        # would be a second live copy of a value base.css already states.
        wash = _wash(classes[name].get("wash", ""), "", report=False)
        if wash:
            decls.append("--dr-mark-wash: " + wash)
        lines.append(
            ".md-typeset .dr-mark--cls-" + name + " { " + "; ".join(decls) + "; }"
        )

    # THE CHIP TINT. base.css keeps border, radius and padding; only the background
    # moves here, because only the background is now data. Two classes beats
    # base.css's one, so base.css needs no edit.
    #
    # ⭐ AND A BOXED LINK NEEDED NO NEW CSS AT ALL, WHICH IS WHY THE SHAPE AXIS KEEPS
    # PAYING. An anchor from a `box` family carries `dr-mark--box` WITHOUT
    # `dr-mark`, so it picks up border, radius, padding and this background, and
    # picks up NEITHER `cursor: help` NOR `white-space: nowrap` -- the two
    # declarations that made the link form refuse `.dr-mark` in the first place.
    # The classes were already separate rules; nobody had used them apart.
    lines.append(
        ".md-typeset .dr-mark--box { background: color-mix(in oklch,"
        + " var(--dr-mark-color) var(--dr-mark-wash, " + _DEFAULT_WASH + "),"
        + " transparent); }"
    )

    # THE LINK FORM. An anchor carrying its family class inherits the custom
    # property set above; this rule consumes it, deliberately WITHOUT `.dr-mark`.
    #
    # ⚠️ THE UNDERLINE IS EXPLICIT, AND THAT IS NOT REDUNDANCY. The whole design
    # rests on underline being the one visible difference between the two forms,
    # and Material's link styling is a framework default nobody has verified
    # persists an underline in this build. If Material underlines too, this is a
    # no-op.
    #
    # ⚠️ ONE RULE FOR EVERY PREFIX, WHICH IS WHY IT NAMES NO FAMILY. It used to be
    # `a.dr-term` beside a hardcoded terminology class. Seven namespaces later that
    # would be seven near-identical rules, or one rule lying about who it serves.
    lines.append(
        ".md-typeset a." + LINK_CLASS + " { color: var(--dr-mark-color);"
        + " text-decoration: underline; text-decoration-thickness: 1px;"
        + " text-underline-offset: 0.15em; }"
    )

    return "\n".join(lines) + "\n"


def on_files(files, config):
    global _TABLE
    _TABLE = _build_table()
    return files


def on_page_markdown(markdown, page, config, files):
    if "{" not in markdown or not _TABLE:
        return markdown

    src = page.file.src_uri

    def replace(match):
        name = match.group("marker")
        row = _TABLE.get(name)
        if not row:
            # Not one of ours. Almost certainly an attr_list attribute on a real
            # element (`{ .md-button }`), or the multi-class block markerlinks just
            # emitted for a link-form marker, so hand it back untouched rather than
            # eating syntax that belongs to somebody else.
            #
            # ⚠️ LOAD-BEARING IN BOTH DIRECTIONS. It is why an invented marker
            # degrades to plain text instead of erroring -- and therefore why
            # `{.calc}` sat unrendered on a live site for days before 2026-08-09.
            # Being reported is not the same as being seen.
            return match.group(0)

        text = (match.group("text") or "").strip() or row["label"] or name
        klass = row["class"]

        css = ["dr-mark", "dr-mark--" + row["shape"]]
        if klass:
            css.append("dr-mark--cls-" + klass)

        style = ""
        if row["colour"]:
            style = (
                ' style="--dr-mark-color: '
                + html.escape(row["colour"], quote=True) + '"'
            )

        # CLASS LEADS the entry, so the sorted inventory reads as families. The
        # link form writes the same shape with a ` -> target` tail, so one sorted
        # list answers "every calc on this site" across both forms at once.
        state.note(
            "markers",
            (klass or "unclassed") + " \u00b7 " + name + " \u00b7 " + src
            + " \u00b7 " + text,
        )

        return (
            '<span class="' + " ".join(css) + '"'
            + ' data-mark="' + html.escape(name) + '"' + style
            + ' title="' + html.escape(row["tooltip"], quote=True) + '">'
            + html.escape(text) + "</span>"
        )

    return sub_outside_code(_MARK, replace, markdown)


def on_post_build(config):
    """Sort the inventory so it reads as families rather than as page order.

    Runs before hook 08 prints, because MkDocs dispatches an event to hooks in
    REGISTRATION order and 03b is registered before 08 -- the same ordering
    dependency mkdocs.yml already documents for the nav chain.

    ⚠️ IT SORTS ENTRIES THIS MODULE DID NOT WRITE. markerlinks appends to the same
    bucket, on purpose, and is registered at 03c -- also before 08. One sort, one
    list, both forms.
    """
    entries = state.REPORT.get("markers")
    if entries:
        entries.sort()
