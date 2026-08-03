"""Stage 03b -- inline confidence markers.

    The second altered curtain is not named: [To be confirmed]{.tbc}
    Grid height [18'-0"]{.est} above deck
    Side tabs: 21, [18]{.was} on the legacy sheet
    Cyc width [40'-0"]{.conf}

ONE CATEGORY, NARROWLY: every marker says how much to TRUST the thing next to
it. Not highlighting, not decoration. That constraint is what keeps the set
small enough that a reader can actually learn it.

WHY THIS IS A HOOK AND NOT A MARKDOWN EXTENSION.
`attr_list` attaches attributes to elements that already exist -- a link, an
image, a heading. `[text]{.tbc}` is a bare bracketed span, which is Pandoc
syntax and is not an element Python-Markdown produces, so the attribute has
nothing to attach to and the whole thing renders as literal text with the
braces showing. That is exactly what shipped on the live curtain inventory.

SHAPE AND COLOUR ARE SEPARATE AXES. Shape is a closed set of four (box, plain,
strike, soft) because a reader can tell four shapes apart at a glance and
cannot tell nine apart. Colour is open: any token from colors.tsv, or a
literal hex/oklch value. Every combination works, so a green confirmation and
an amber caution are one mechanism in two colours rather than two features.

The colour is emitted as an inline custom property on the span, which is what
makes an arbitrary value possible without generating a stylesheet rule per
marker. A token resolves to `var(--dr-<token>)`, so it follows the active
theme into light mode; a literal is passed through as written and does not.

THE PART THAT EARNS ITS PLACE IS THE COUNTING. Every use lands in the build
report, grouped by marker and named by page. A marker you cannot enumerate is
just a colour; a marker you can is a worklist.

Defined in `theme/markers.tsv`. Adding one is a row, not a commit to this file.
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


def _table() -> dict[str, dict]:
    rows = load_tsv(state.ENGINE_ROOT / "theme" / "markers.tsv")
    return {r["marker"]: r for r in rows if r.get("marker")}


def _known_tokens() -> set[str]:
    return {
        r["token"] for r in load_tsv(state.ENGINE_ROOT / "theme" / "colors.tsv")
        if r.get("token")
    }


def _colour(value: str, marker: str, tokens: set[str]) -> str:
    """Resolve a marker colour to something CSS can use."""
    value = (value or "").strip()
    if not value:
        return "currentColor"
    if _TOKEN.match(value):
        if value not in tokens:
            # Named something that is not in the palette. Falling back silently
            # would render an invisible marker -- var() with no fallback
            # resolves to nothing -- so it is reported and given a real colour.
            state.note(
                "notes",
                "marker '" + marker + "' asks for colour token '" + value
                + "', which is not in theme/colors.tsv. Using the body colour. "
                + "Known tokens: " + ", ".join(sorted(tokens)),
            )
            return "currentColor"
        return "var(--dr-" + value + ")"
    return value


def on_page_markdown(markdown, page, config, files):
    if "{" not in markdown:
        return markdown

    table = _table()
    if not table:
        return markdown

    tokens = _known_tokens()
    src = page.file.src_uri

    def replace(match):
        name = match.group("marker")
        row = table.get(name)
        if not row:
            # Not one of ours. Almost certainly an attr_list attribute on a
            # real element (`{ .md-button }`), so hand it back untouched rather
            # than eating syntax that belongs to somebody else.
            return match.group(0)

        text = (match.group("text") or "").strip() or row.get("label") or name
        shape = (row.get("shape") or "box").strip()
        if shape not in _SHAPES:
            state.note(
                "notes",
                "marker '" + name + "' has shape '" + shape + "', which is not "
                + "one of " + ", ".join(sorted(_SHAPES)) + ". Using 'box'.",
            )
            shape = "box"

        colour = _colour(row.get("color", ""), name, tokens)
        tooltip = row.get("tooltip") or ""

        state.note("markers", src + " · " + name + " · " + text)

        return (
            '<span class="dr-mark dr-mark--' + html.escape(shape)
            + '" data-mark="' + html.escape(name) + '"'
            + ' style="--dr-mark-color: ' + html.escape(colour, quote=True) + '"'
            + ' title="' + html.escape(tooltip, quote=True) + '">'
            + html.escape(text) + "</span>"
        )

    return sub_outside_code(_MARK, replace, markdown)
