"""Inline hover text on plain words: `[Text]{hover="..."}`.

    Call is [the quarter-hour]{hover="15 minutes before places."} for all crew.
    [Places]{hover="Everyone in position for the top of show." print}
    \\[literal]{hover="kept as typed"}          escaped: left alone

Spec and rulings R1-R7: specs/hover-inline.md. Popup: assets/gloss.css (the same
box a glossed page link gets, so the two cannot look different).

WHY TEXT ONLY. A page link's hover belongs to the DESTINATION (`gloss:`), so an
inline one there would be a second copy free to drift (hover-text dl A3). Plain
words have no destination, so the only copy is this one. `@`-links keep `gloss:`;
the external-link half (R2) is part 2 and is reported, not built, here.

WHY RAW HTML. The span is emitted as finished inline HTML, which is why a TSV cell
carries it: cells.py trusts typed tags and narrows only attr_list ATTRIBUTES on
links (`_classes` / `_ATTR_ALLOW`, the trap that ate the role gloss in tables).
A pre-built span never goes through that pipe. cells.render calls this FIRST,
before its own escaping, or the quotes would already be entities.

THE TEXT STAYS MARKDOWN. Python-Markdown keeps processing inline syntax between
inline tags, so `[**do not** repatch]{hover="..."}` still bolds. The text group
forbids `]`, exactly like markers.py, so a span cannot hold a link or a marker.

THE HOVER STRING IS ESCAPED TWICE OVER, on purpose: `html.escape(quote=True)`,
then `[]{}|`, backtick, `:` and `@` as numeric entities (linklabels._attr's rule
plus two). Later hooks scan the whole page: markers (03b) would turn a `{.est}`
inside a hover string into a chip INSIDE an attribute, and urllinks (03d) would
autolink a `https://` there. Either one breaks the tag.

NOT IN HEADINGS (the hover-text ruling: a heading is also a nav label, TOC entry
and anchor). A heading match is reported and left literal. Code is skipped by
util.sub_outside_code, so a page can document the syntax.
"""

from __future__ import annotations

import html
import re

from . import state
from .util import sub_outside_code

_STR = r'"(?P<dq>(?:[^"\\\n]|\\.)*)"|\'(?P<sq>(?:[^\'\\\n]|\\.)*)\''

#: `[text]{hover="..." print?}`, not preceded by a backslash. `]{` can never be
#: link syntax (`](`), so this cannot touch what links / markerlinks own.
_HOVER = re.compile(
    r"(?<!\\)\[(?P<text>[^\]\n]+)\]\{[ \t]*hover[ \t]*=[ \t]*(?:" + _STR + r")"
    r"(?P<flags>(?:[ \t]+print)?)[ \t]*\}"
)

#: Near-misses worth a report line rather than a silent literal brace.
_NEAR = re.compile(r"(?<!\\)\[[^\]\n]+\]\{[ \t]*\.?hover\b[^}\n]*\}")
_ON_LINK = re.compile(r"\]\([^)\n]*\)\{[ \t]*hover[ \t]*=")


def _attr(value: str) -> str:
    text = html.escape(" ".join(value.split()), quote=True)
    for char in "[]{}|`:@":
        text = text.replace(char, "&#" + str(ord(char)) + ";")
    return text


def _unq(raw: str) -> str:
    return re.sub(r"\\(.)", r"\1", raw)


def span(text: str, hover: str, printed: bool) -> str:
    g = _attr(hover)
    out = ('<span class="dr-gloss dr-hover" tabindex="0" data-gloss="' + g
           + '" aria-description="' + g + '"')
    if printed:
        out += ' data-role-print="' + g + '"'
    return out + ">" + text + "</span>"


def _in_heading(m) -> bool:
    s = m.string
    start = s.rfind("\n", 0, m.start()) + 1
    return re.match(r"[ ]{0,3}#{1,6}(?:[ \t]|$)", s[start:]) is not None


def convert(markdown: str, src: str = "?", headings_ok: bool = False) -> str:
    """Rewrite every hover span outside code. Pure: page-free so cells can call it."""
    if "hover" not in markdown:
        return markdown

    def repl(m):
        if not headings_ok and _in_heading(m):
            state.note("notes", src + ": hover text is not allowed in headings; "
                       + "'[" + m.group("text") + "]{hover=...}' left as typed.")
            return m.group(0)
        raw = m.group("dq") if m.group("dq") is not None else m.group("sq")
        hover = _unq(raw)
        if not hover.strip():
            state.note("notes", src + ": empty hover on '" + m.group("text") + "'; rendered as plain text.")
            return m.group("text")
        return span(m.group("text"), hover, bool(m.group("flags").strip()))

    out = sub_outside_code(_HOVER, repl, markdown)

    # Whatever still looks like a hover after conversion is malformed.
    def near(m):
        if not headings_ok and _in_heading(m):
            return m.group(0)  # already reported as a heading above
        state.note("notes", src + ": malformed hover '" + m.group(0)[:80]
                   + "' left as typed. Spelling: [Text]{hover=\"...\"}: no dot before hover, "
                   + "one quoted string, and inner quotes as \\\" or inside 'single quotes'.")
        return m.group(0)
    sub_outside_code(_NEAR, near, out)

    def onlink(m):
        state.note("notes", src + ": hover= on a link is not built yet (hover-inline part 2). "
                   + "For a page link, put gloss: on the destination page.")
        return m.group(0)
    sub_outside_code(_ON_LINK, onlink, out)
    return out


def on_page_markdown(markdown, page, config, files):
    src = getattr(getattr(page, "file", None), "src_uri", "?")
    return convert(markdown, src)
