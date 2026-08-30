"""A TSV cell is PROSE, and it renders exactly like a line of markdown body text.

Decision history: doc-render-engine Decision Log, J17 and the block above it. The
argument lives there; this file states the contract.

    Grid height	[18'-0"]{.est}		measured off the old plot
    Console	[QL5](@term:yamaha-ql5)	1	**do not** repatch
    Keys	[Theatre Administrator](@role:theatre-administrator)		sign out at the desk

Everything a page body can say inline, a cell can say: confidence markers, `@` page
and peer references, `@term:`, `@role:` and `@data:` references, `**bold**`,
`*emphasis*` and `code`. What renders in prose renders in a cell, and it renders
IDENTICALLY, because this module hands the cell to the same two hooks the page body
goes through.


WHY THIS EXISTS AT ALL -- IT WAS ALREADY HAPPENING, BADLY
=========================================================

Markers in cells half-worked before this module, by accident, and the accident is worth
understanding because it is the reason a shared renderer beats leaving it alone.

`01b_data` emits the table as raw HTML. `03_links` and `03b_markers` run LATER and scan
the whole page, HTML included. So a cell reading `[3]{.est}` did become a styled span --
but datatable had already escaped the cell, and markers escaped the matched text again,
so any cell containing a quote came out as visible entity gibberish:

    [18'-0"]{.est}   ->   18&#x27;-0&quot;

which is precisely the feet-and-inches value markers exist for. And `@` references were
worse: `03_links` resolved them correctly into markdown, then nothing converted that
markdown, because the `dr-data` div carries no `markdown="1"` -- so the reader saw literal
`[ETC](../etc/)` in the cell. dr-spec DOES carry `markdown="1"`; the engine already
knew about this trap one module over.

**So the choice was never "add a feature" -- it was between a half-working accident and
one deliberate path.** This is the deliberate path: cells are rendered at 01b, escaped
EXACTLY ONCE, and the later hooks find finished HTML with nothing left to match.


IT DELEGATES, IT DOES NOT REIMPLEMENT
=====================================

`links.on_page_markdown` and `markers.on_page_markdown` are called directly on the cell
text. Both take `(markdown, page, config, files)` and neither reads `config` or `files`,
so they are reusable as-is on any fragment. That matters more than tidiness:

  * a marker resolves through the same class table, so a cell and a sentence cannot
    disagree about what `{.est}` looks like;
  * `@term:` and `@data:` resolve through the same reserved-prefix registry;
  * every marker used in a cell lands in the build report already, because
    `markers.py` records as it renders. "Which terms still have no page" and "what is
    unconfirmed sitewide" stay answerable without this module knowing they exist.

A second copy of any of that is the defect this whole engine keeps writing down.


WHAT IT DOES OWN: INLINE MARKDOWN, AND ONLY THE INLINE PART
===========================================================

After the two hooks run, the cell holds real HTML (marker spans), markdown link syntax,
and literal text. Nothing downstream will convert that markdown, so this module finishes
the job -- links, code, strong, emphasis -- and escapes every literal run around them.

NOT BLOCK MARKDOWN. No headings, lists, tables or fences in a cell. A table cell is
one line by construction, `white-space: nowrap` is load-bearing in the stylesheet, and a
`<ul>` inside a `<td>` in a horizontally-scrolling grid is not a thing anybody wants.
Unsupported block syntax renders as its own literal characters, which is legible and
wrong in an obvious way rather than silently.

RAW HTML IN A CELL IS TRUSTED, exactly as it is in a markdown page body. This module
escapes the literal text it finds between constructs; it does not sanitise. A cell
containing `<b>x</b>` renders bold, and a cell containing a stray `<` will eat the rest
of itself. Same bargain the rest of the content tree makes, stated so nobody discovers it
from a broken table.


AND THAT BARGAIN IS EXACTLY WHY THE ATTRIBUTE PASS-THROUGH IS AN ALLOWLIST
==========================================================================

Added 2026-08-30 for BUILD 9. `_classes()` read ONLY `.class` tokens out of an
attr_list block, so every NON-CLASS attribute an upstream hook emitted was silently
dropped INSIDE A CELL and nowhere else. The role gloss is carried in exactly such an
attribute, so `[the TD](@role:technical-director)` rendered a correct-looking link
with no hover text -- in tables, the surface most likely to name a role.

THE SHAPE IS WORTH MORE THAN THE FIX: `_classes` was never wrong, it was NARROWER
THAN ITS POSITION. It was named for the one kind of value that existed when it was
written, and it stands where any attribute now has to pass. Its name and its docstring
both describe the narrow job so convincingly that nothing invites you to check it. Same
family as the eyebrow welded to a TYPE, `:first-child` assuming an identifier, and
`tr:not(:has(td.dr-detail))` written against an emitter that always emits.
The tell, cheap and available in advance: WHEN A NEW KIND OF VALUE STARTS FLOWING
THROUGH AN OLD PIPE, READ THE PIPE RATHER THAN THE VALUE.

A WILDCARD PASS-THROUGH WAS REFUSED, and the reason is the paragraph above this
one. Trusting HTML a person TYPED into a cell is the bargain the content tree already
makes. Forwarding arbitrary key-value pairs out of a TSV -- the least-reviewed content
in the tree, on sites that publish publicly -- is a different bargain, and this module
is not the place to make it. `_ATTR_ALLOW` is the whole list, and adding to it should
feel like a decision.


THE NUMBERS SURVIVE, WHICH WAS THE HARD CONSTRAINT
==================================================

Michael's line: *"we absolutely cannot lose the number functionality that we get in
sorting or summing digits."* So `plain()` strips every construct back to bare text, and
that -- never the marked-up cell -- is what `sort:` orders on. `[18'-0"]{.est}` sorts as
`18'-0"`, and a marked number sorts among unmarked ones.

AND THE ATTRIBUTE PASS-THROUGH DOES NOT TOUCH THAT, verified rather than assumed:
`plain()` deletes the whole brace block before anything reads it, so a gloss attribute
is stripped for sorting exactly as a class always was, and `number()` still refuses
`[the TD](@role:x)` as non-numeric because it keeps only the LABEL.

AND THE HONEST LIMIT, because it cannot be fixed here: a spreadsheet cannot do this.
Any non-digit in a cell makes it TEXT to Excel and Numbers, so a marked value stops being
a number to everything that is not this renderer. That is the whole reason a separate
confidence COLUMN was the better answer (J17) and remains the end state. This ships
because the column needs a FileMaker field to feed it and that mapping is later work --
not because in-cell marking won the argument.
"""

from __future__ import annotations

import html
import re

from . import links, markers

#: `[text](url)` with an optional attr_list block, which is what links.py emits for a
#: cross-site or @term: reference. The attrs are carried through as real classes.
_LINK = re.compile(
    r"\[(?P<text>[^\]\n]*)\]\((?P<url>[^)\s]*)\)"
    r"(?:\{[ \t]*(?P<attrs>[^}\n]*)\})?"
)
_CODE = re.compile(r"`(?P<code>[^`\n]+)`")
_STRONG = re.compile(r"\*\*(?P<text>[^*\n]+)\*\*")
_EM = re.compile(r"(?<![*\w])\*(?P<text>[^*\n]+)\*(?![*\w])")

#: An HTML tag already in the text: either emitted by the marker hook, or typed by the
#: author. Protected from escaping, not validated.
_TAG = re.compile(r"</?[A-Za-z][^>]*>")

#: A construct parked while the literal text around it is escaped. NUL cannot occur in
#: the source -- a TSV is read as text and split on tabs, so a NUL would already have
#: broken the read.
_SLOT = "\x00{}\x00"
_SLOT_BACK = re.compile(r"\x00(\d+)\x00")

_CLASS = re.compile(r"\.([A-Za-z][\w-]*)")

#: `key="value"` inside an attr_list block. Double quotes only, because that is the
#: one spelling any hook in this engine emits -- a looser pattern would invite a
#: second spelling and then have to pick between them.
_ATTR = re.compile(r'([A-Za-z][\w-]*)="([^"]*)"')

#: THE COMPLETE LIST OF NON-CLASS ATTRIBUTES A CELL MAY CARRY. See the docstring
#: for why this is an allowlist and not a pass-through. Every entry is emitted by a
#: hook in this engine, never typed by an author:
#:
#:   data-gloss       the role's hover text, from the target page's frontmatter
#:   data-role-print  what that role prints on paper
#:
#: ADDING A NAME HERE IS A DECISION, not a formality. The question to answer first
#: is whether the value can ever originate in the TSV rather than in a hook -- if it
#: can, it does not belong in this list.
_ATTR_ALLOW = ("data-gloss", "data-role-print")


def _classes(attrs: str) -> str:
    """`{ .dr-term .dr-mark--cls-terminology }` -> a class attribute.

    CLASSES ONLY, AND THAT IS NOW A STATED SCOPE RATHER THAN AN ASSUMPTION. This
    function silently dropped everything else for as long as everything else did not
    exist. `_allowed_attrs` is the other half; a caller needs both.
    """
    found = _CLASS.findall(attrs or "")
    if not found:
        return ""
    return ' class="' + html.escape(" ".join(found), quote=True) + '"'


def _allowed_attrs(attrs: str) -> str:
    """The allowlisted key="value" pairs from an attr_list block, re-escaped.

    Escaped with `quote=True` exactly as `_classes` does, so a value carrying a
    quote cannot close the attribute it is sitting in.

    NOT A VALIDATOR. An unknown key is dropped in silence, which is correct: an
    attr_list block on a cell link is written by a hook, so an unrecognised key means
    a hook changed and this list did not, and the visible symptom is the feature not
    working rather than a broken table.
    """
    out = []
    for key, value in _ATTR.findall(attrs or ""):
        if key in _ATTR_ALLOW:
            out.append(" " + key + '="' + html.escape(value, quote=True) + '"')
    return "".join(out)


def _inline(text: str) -> str:
    """Convert inline markdown, escape everything else, exactly once.

    Constructs are parked as sentinels FIRST, then the remaining literal text is escaped
    in one pass, then the sentinels are restored. That ordering is the whole reason this
    does not double-escape: nothing that has already been rendered is ever handed to
    `html.escape` again.
    """
    parked: list[str] = []

    def park(fragment: str) -> str:
        parked.append(fragment)
        return _SLOT.format(len(parked) - 1)

    # Order matters. Tags and code first, so a `<span>` or a backticked `**x**` is never
    # reinterpreted. Links before emphasis, so a link label may contain asterisks.
    text = _TAG.sub(lambda m: park(m.group(0)), text)
    text = _CODE.sub(
        lambda m: park("<code>" + html.escape(m.group("code")) + "</code>"), text
    )

    def link(match):
        label = _inline(match.group("text"))
        url = html.escape(match.group("url"), quote=True)
        attrs = match.group("attrs")
        return park('<a href="' + url + '"' + _classes(attrs)
                    + _allowed_attrs(attrs) + ">" + label + "</a>")

    text = _LINK.sub(link, text)
    text = _STRONG.sub(
        lambda m: park("<strong>" + _inline(m.group("text")) + "</strong>"), text
    )
    text = _EM.sub(lambda m: park("<em>" + _inline(m.group("text")) + "</em>"), text)

    text = html.escape(text)
    return _SLOT_BACK.sub(lambda m: parked[int(m.group(1))], text)


def render(cell: str, page, config=None, files=None) -> str:
    """One TSV cell as finished HTML.

    Runs at stage 01b, BEFORE links (03) and markers (03b) see the page. That is why
    the output must be finished rather than half-converted: those hooks will scan this
    HTML afterwards, and anything left unresolved gets resolved a second time -- which is
    exactly the double-escape this module was built to end.
    """
    text = str(cell)
    if not text.strip():
        return ""
    if "@" in text or "](" in text:
        text = links.on_page_markdown(text, page, config, files)
    if "{" in text:
        text = markers.on_page_markdown(text, page, config, files)
    return _inline(text)


def plain(cell: str) -> str:
    """The cell with every construct stripped back to its bare text.

    This is what `sort:` compares and what a future `total:` would add up. A marked value
    has to sort as its value or the marking has broken the sheet -- see the module
    docstring on the one constraint that was not negotiable.

    THE BRACE STRIP IS WHAT KEEPS THAT TRUE FOR ATTRIBUTES TOO, and it needed no
    change for BUILD 9: the whole block goes, so a gloss attribute never reaches a
    comparison, exactly as a class never did.
    """
    text = str(cell)
    # Marker and attr blocks go entirely; a link or emphasis keeps its LABEL.
    text = re.sub(r"\{[^}\n]*\}", "", text)
    text = _LINK.sub(lambda m: m.group("text"), text)
    text = _TAG.sub("", text)
    text = text.replace("**", "").replace("*", "").replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


_NUMBER = re.compile(r"^[-+]?\d+(?:\.\d+)?$")


def number(cell: str):
    """The cell as a float, or None if it is not purely a number.

    Deliberately strict: `12`, `-4`, `3.5` yes; `18'-0"`, `12 units`, `1-4` no. A loose
    parse that pulled the first digits out of `18'-0"` would sort feet-and-inches as 18
    and dimensions as their first number, silently, which is worse than sorting them as
    text -- text at least looks like what it is.
    """
    value = plain(cell)
    if not _NUMBER.match(value):
        return None
    try:
        return float(value)
    except ValueError:
        return None
