"""Stage 03b -- inline markers, in CLASSES.

    The second altered curtain is not named: [To be confirmed]{.tbc}
    Grid height [18'-0"]{.est} above deck
    A [source 4]{.term} is an ERS fixture

Decision history: doc-render-engine (repo) -- Decision Log in ClickUp, Q6/J7.
The argument lives THERE; this file states the contract.


TWO AXES OF MEANING, NOT ONE
============================

Every marker used to say the same KIND of thing -- how much to trust the value
beside it -- and this docstring used to defend that narrowness as the feature.
It was half right. The narrowness protected the BUILD REPORT: you can ask "what
is unconfirmed across this whole site" only while every row answers the same
question.

What was missing was a way to say which kind a row IS. So terminology was very
nearly built as a SECOND, parallel family -- two mechanisms for one concept --
because the table had no column for it. Michael's ruling settled it: *"it. is. a.
marker. put it in markers. you've just found different 'classes' of markers...
so they should cascade and be familied."*

So `class` is a column, families live in theme/marker-classes.tsv, and the report
groups by class. The confidence question survives untouched no matter how many
glossary terms a site marks.


THE CASCADE
===========

A class carries the default SHAPE and COLOUR; a row overrides either. `est` and
`was` still draw soft and struck -- now as OVERRIDES rather than as the only
mechanism -- and a new terminology row is a slug and a tooltip, nothing else.

SHAPE IS STILL A CLOSED SET OF FOUR (box, plain, strike, soft), because a reader
can tell four apart at a glance and cannot tell nine apart. Terminology needed
colour and weight WITHOUT an underline, which is `plain`, which already existed:
the class axis cost the shape axis nothing. A span is not an anchor and takes no
underline; when the link form lands, the underline is the whole affordance and
nobody has to write a rule to create it.


WHY THIS IS A HOOK AND NOT A MARKDOWN EXTENSION
===============================================

`attr_list` attaches attributes to elements that ALREADY EXIST -- a link, an
image, a heading. `[text]{.tbc}` is a bare bracketed span, which is Pandoc syntax
and is not an element Python-Markdown produces, so the attribute has nothing to
attach to and the whole thing renders as literal text with the braces showing.
That is exactly what shipped on the live curtain inventory.


COLOUR IS RESOLVED ONCE PER BUILD, AND THAT IS A FIX
====================================================

`_colour()` used to run inside the per-MATCH replacement, so an unknown colour
token reported once per OCCURRENCE. Six confidence markers on a page hid that
completely. A terminology class used three hundred times on a site would have
buried the report under three hundred copies of one complaint -- and the report is
the only reason any of this is better than a highlighter.

The table is therefore merged and resolved in `on_files`, once, before any page
renders. Deliberately in an event and not at import: `mkdocs serve` rebuilds
in-process, so a table cached at import would outlive an edit to either TSV.

A class's colour is emitted as a REAL CSS RULE by `build_css()`. The inline custom
property survives for a ROW override only -- there are a handful of classes, so a
rule per class is cheap where a rule per marker was not, which is what the inline
property existed to avoid.

⚠️ THE COLOUR THIS SHIPS WITH IS NOT IN theme/colors.tsv YET, ON PURPOSE.
`terminology` asks for `accent-soft`: real in the canonical maw-themes palette,
absent from the nine-token stand-in this engine still reads. It reports as unknown
ONCE and falls back to the body colour until the palette refit lands. Decided
sequencing (maw-themes DL J11), not a defect.

Defined in theme/markers.tsv + theme/marker-classes.tsv. Adding one is a row.
"""

from __future__ import annotations

import html
import re

from . import state
from .util import load_tsv, sub_outside_code

# [text]{.marker} with optional whitespace, or bare {.marker}.
_MARK = re.compile(
    r"(?:\[(?P<text>[^\]\n]*)\])?\{[ \t]*\.(?P<marker>[a-z][a-z0-9-]*)[ \t]*\}"
)

# A colour that is a bare word is a TOKEN and resolves against the theme. Any
# thing else -- #hex, oklch(...), rgb(...) -- is passed through as written.
_TOKEN = re.compile(r"^[a-z][a-z0-9-]*$")

_SHAPES = {"box", "plain", "strike", "soft"}
_FALLBACK_SHAPE = "box"

#: Marker name -> resolved row. Built by on_files, read by on_page_markdown.
_TABLE: dict[str, dict] = {}


def _rows(name: str) -> list[dict]:
    return load_tsv(state.ENGINE_ROOT / "theme" / name)


def _classes() -> dict[str, dict]:
    return {r["class"]: r for r in _rows("marker-classes.tsv") if r.get("class")}


def _known_tokens() -> set[str]:
    return {r["token"] for r in _rows("colors.tsv") if r.get("token")}


def _colour(value: str, where: str, tokens: set[str], report: bool = True) -> str:
    """Resolve a colour to something CSS can use.

    `report` exists because build_css() runs from assets._plan, which is called by
    BOTH on_config and on_files and would therefore complain twice about one bad
    cell. The single honest complaint comes from _build_table, which runs once.
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
            where + " asks for colour token '" + value + "', which is not in "
            + "theme/colors.tsv. Using the body colour. Known tokens: "
            + ", ".join(sorted(tokens)),
        )
    return "currentColor"


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
        _colour(classes[name].get("color", ""), "marker class '" + name + "'", tokens)

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
    Shape stays in base.css -- only colour is generated.
    """
    classes = _classes()
    tokens = _known_tokens()

    lines = [
        "/* GENERATED by docrender/markers.py -- do not edit.",
        "   One rule per marker CLASS, from theme/marker-classes.tsv.",
        "   Shape lives in assets/base.css; colour is data. */",
    ]
    for name in sorted(classes):
        value = _colour(
            classes[name].get("color", ""),
            "marker class '" + name + "'",
            tokens,
            report=False,
        )
        lines.append(
            ".md-typeset .dr-mark--cls-" + name
            + " { --dr-mark-color: " + value + "; }"
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
            # element (`{ .md-button }`), so hand it back untouched rather than
            # eating syntax that belongs to somebody else.
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

        # CLASS LEADS the entry, so the sorted inventory reads as families.
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
    REGISTRATION order and 03b is registered before 08. That is the same ordering
    dependency mkdocs.yml already documents for the nav chain -- if this ever
    stops working, check that list before you check this function.
    """
    entries = state.REPORT.get("markers")
    if entries:
        entries.sort()
