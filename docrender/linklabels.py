"""Literal, build-time labels for empty page references. No content writes."""

from . import state


def page_label(label: str, target: dict, token: str, source: str) -> str:
    """Only [] opts in; a nonempty author label is never reinterpreted.

    Resolve from the existing published page map (or peer index), not raw
    frontmatter: hidden pages must not leak through this feature. Peer freshness
    is governed by the existing fetch/cache path in links.py.
    """
    if label:
        return label
    value = target.get("title")
    title = " ".join(str(value).split()) if value is not None else ""
    if not title:
        title = "@" + token
        state.note(
            "notes",
            source + ": '@" + token
            + "' has no title in the page index; using its ID as the link label.",
        )
    # A title is text, not authored Markdown or HTML. Numeric entities survive
    # Markdown parsing as literal characters without enabling markup, nested
    # links, table separators, house markers, or an entity supplied by a title.
    return "".join(
        "&#" + str(ord(char)) + ";" if char in "\\`*_{}[]<>&!|~" else char
        for char in title
    )
