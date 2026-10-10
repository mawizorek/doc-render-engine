"""Inline hover text on plain words: `[Text]{hover="..."}`.

    Call is [the quarter-hour]{hover="15 minutes before places."} for all crew.
    [Places]{hover="Everyone in position for the top of show." print}
    \\[literal]{hover="kept as typed"}          escaped: left alone

Spec and rulings R1-R7: specs/hover-inline.md. Popup: assets/gloss.css (the same
box a glossed page link gets, so the two cannot look different).

TEXT AND EXTERNAL LINKS ONLY (R2). A page link's hover belongs to the DESTINATION
(`gloss:`), so an inline one there would be a second copy free to drift
(hover-text dl A3). Plain words and outside sites have no destination page, so the
only copy is this one.

    Read the [house rules](https://example.org/rules){hover="Opens the venue PDF."} first.

The link form matches ABSOLUTE `http(s)://` and `mailto:` targets only. That is
the whole @-link refusal, and it is structural rather than a check: links.py runs
at 03, BEFORE this, and has already turned `[x](@id)` into a RELATIVE href, so a
page link can never match here. It stays plain markdown, and the leftover
`{hover=...}` is reported with a pointer to `gloss:`. Peer links resolve to
absolute URLs but always carry links.py's own brace first, so they cannot match
either. Images (`![...]`) are excluded.

Emitted as a finished `<a>`, not an attr_list brace: attr_list cannot carry a
quote inside a value, and nothing in this engine decorates a plain external link
later (checked 2026-10-10: no `target`/`rel` pass exists outside linklabels), so
nothing is lost by finishing it here.

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
inside a hover string into a chip INSIDE an attribute, which breaks the tag. `:`
and `@` are defence in depth, not a known bug: no later stage autolinks today
(03d has no page pass, checked 2026-10-10), and encoding them means no future
`@`- or URL-shaped pattern can ever match inside a hover string.

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

#: `[text](https://...){hover="..." print?}`. Absolute targets only; see docstring.
_HOVER_LINK = re.compile(
    r"(?<![\\!])\[(?P<text>[^\]\n]+)\]\((?P<url>(?:https?://|mailto:)[^)\s]+)\)"
    r"\{[ \t]*hover[ \t]*=[ \t]*(?:" + _STR + r")(?P<flags>(?:[ \t]+print)?)[ \t]*\}"
)

#: Near-misses worth a report line rather than a silent literal brace.
_NEAR = re.compile(r"(?<!\\)\[[^\]\n]+\]\{[ \t]*\.?hover\b[^}\n]*\}")
#: A hover left on a link this module did not take: a page link (relative after
#: links.py), a peer link (links.py's `{ .docrender-xref }` sits in between), an
#: `@url:` that resolved with a brace. Escaped links are the author's business.
_ON_LINK = re.compile(
    r"(?<![\\!])\[[^\]\n]*\]\([^)\n]*\)(?:\{[^}\n]*\})?\{[ \t]*hover[ \t]*="
)
_ON_IMAGE = re.compile(r"!\[[^\]\n]*\]\([^)\n]*\)(?:\{[^}\n]*\})?\{[ \t]*hover[ \t]*=")


def _attr(value: str) -> str:
    text = html.escape(" ".join(value.split()), quote=True)
    for char in "[]{}|`:@":
        text = text.replace(char, "&#" + str(ord(char)) + ";")
    return text


def _unq(raw: str) -> str:
    return re.sub(r"\\(.)", r"\1", raw)


def _gloss_attrs(hover: str, printed: bool) -> str:
    g = _attr(hover)
    out = ' data-gloss="' + g + '" aria-description="' + g + '"'
    return out + (' data-role-print="' + g + '"' if printed else "")


def span(text: str, hover: str, printed: bool) -> str:
    return ('<span class="dr-gloss dr-hover" tabindex="0"' + _gloss_attrs(hover, printed)
            + ">" + text + "</span>")


def anchor(text: str, url: str, hover: str, printed: bool) -> str:
    # A link is focusable already: no tabindex (gloss.css header), no help cursor.
    return ('<a href="' + _attr(url) + '" class="dr-gloss"' + _gloss_attrs(hover, printed)
            + ">" + text + "</a>")


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

    def repl_link(m):
        raw = m.group("dq") if m.group("dq") is not None else m.group("sq")
        hover = _unq(raw)
        if not hover.strip():
            state.note("notes", src + ": empty hover on link '" + m.group("text") + "'; rendered as a plain link.")
            return "[" + m.group("text") + "](" + m.group("url") + ")"
        return anchor(m.group("text"), m.group("url"), hover, bool(m.group("flags").strip()))

    out = sub_outside_code(_HOVER_LINK, repl_link, markdown)
    out = sub_outside_code(_HOVER, repl, out)

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
        state.note("notes", src + ": hover= ignored on a page or peer link (hover-inline R2). "
                   + "Put gloss: on the destination page instead; hover= works on plain text "
                   + "and on https:// / mailto: links.")
        return m.group(0)
    sub_outside_code(_ON_LINK, onlink, out)

    def onimage(m):
        state.note("notes", src + ": hover= is not supported on images; use the figure "
                   + "caption, or put hover on the words beside it.")
        return m.group(0)
    sub_outside_code(_ON_IMAGE, onimage, out)
    return out


def on_page_markdown(markdown, page, config, files):
    src = getattr(getattr(page, "file", None), "src_uri", "?")
    return convert(markdown, src)
