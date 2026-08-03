"""Stage 03b -- inline confidence markers.

    The second altered curtain is not named: [To be confirmed]{.tbc}
    Grid height [18'-0"]{.est} above deck
    Side tabs: 21, [18]{.was} on the legacy sheet

ONE CATEGORY, NARROWLY: every marker says how much to TRUST the thing next to
it. Not highlighting, not decoration. That constraint is what keeps the set
small enough that a reader can actually learn it.

WHY THIS IS A HOOK AND NOT A MARKDOWN EXTENSION.
`attr_list` attaches attributes to elements that already exist -- a link, an
image, a heading. `[text]{.tbc}` is a bare bracketed span, which is Pandoc
syntax and is not an element Python-Markdown produces, so the attribute has
nothing to attach to and the whole thing renders as literal text with the
braces showing. That is exactly what shipped on the live curtain inventory.

The fix could have been "stop using that syntax." It is a better syntax than
anything else available, it was already written into real pages, and the
substitution is fifteen lines. So the engine learns it instead.

THE PART THAT EARNS ITS PLACE IS THE COUNTING. Every use lands in the build
report, grouped by marker and named by page. A marker you cannot enumerate is
just a colour; a marker you can is a worklist -- "what is unconfirmed across
this entire site" becomes a question with an answer.

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


def _table() -> dict[str, dict]:
    rows = load_tsv(state.ENGINE_ROOT / "theme" / "markers.tsv")
    return {r["marker"]: r for r in rows if r.get("marker")}


def on_page_markdown(markdown, page, config, files):
    if "{" not in markdown:
        return markdown

    table = _table()
    if not table:
        return markdown

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
        style = row.get("style") or "flag"
        tooltip = row.get("tooltip") or ""

        state.note(
            "markers",
            src + " · " + name + " · " + text,
        )

        return (
            '<span class="dr-mark dr-mark--' + html.escape(style)
            + '" data-mark="' + html.escape(name) + '"'
            + ' title="' + html.escape(tooltip, quote=True) + '">'
            + html.escape(text) + "</span>"
        )

    return sub_outside_code(_MARK, replace, markdown)
