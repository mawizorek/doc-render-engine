"""Page-link labels, icon shortcuts and destination-owned hover text.

Authoring:
    [](@page-id)                    current title
    [->](@page-id){color=accent}     right arrow, theme color
    [<-] / [^^] / [vv] / [*] / [!] left / up / down / star / information
Append (@page-id) to each shortcut. Literal arrow/star/info glyphs work too.
Other nonempty labels remain authored text. Escape a shortcut with a backslash
to keep it literal. No content file is rewritten by this module.

Destination frontmatter:
    gloss: "A short explanation."   optional, including on ordinary pages
    gloss_from_summary: true       use summary only when gloss is absent/null
An explicit empty gloss suppresses summary reuse. Neither field means no hover
on a text link; an icon still shows its target title. Resolution is per build.
Peer links use the peer's published index and its existing cache freshness rules.

Ordinary links do not gain printed glosses. Marker links retain their existing
print_gloss/no-print behavior, consuming the same resolved page-map gloss.
"""

import html
import re

import markdown
from markdown.extensions.attr_list import get_attrs

from . import state


ICONS = {"->": "→", "<-": "←", "^^": "↑", "vv": "↓", "*": "★", "!": "ⓘ"}
# Foreground roles only. No hex, arbitrary CSS, or background-wash colors.
COLORS = frozenset(("accent", "accent-2", "accent-deep", "text", "text-soft",
                    "good", "warn", "bad"))
_ATTR_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


def entity_gloss(meta: dict, source: str):
    """Resolve once while building the published page map; no reverse lookup."""
    flag = meta.get("gloss_from_summary", False)
    if not isinstance(flag, bool):
        state.note("notes", source + ": gloss_from_summary must be true or false; ignored.")
        flag = False
    if meta.get("gloss") is not None:
        return meta["gloss"]
    if flag:
        summary = meta.get("summary")
        if summary is None or not str(summary).strip():
            state.note("notes", source + ": gloss_from_summary is true but summary is empty.")
            return ""
        return summary
    return None


def _text(value) -> str:
    return " ".join(str(value).split()) if value is not None else ""


def _title(target: dict, token: str, source: str) -> str:
    title = _text(target.get("title"))
    if not title:
        title = "@" + token
        state.note(
            "notes",
            source + ": '@" + token
            + "' has no title in the page index; using its ID as the link label.",
        )
    return title


def page_label(label: str, target: dict, token: str, source: str) -> str:
    """Only [] opts in; a nonempty author label is never reinterpreted.

    Resolve from the existing published page map (or peer index), not raw
    frontmatter: hidden pages must not leak through this feature. Peer freshness
    is governed by the existing fetch/cache path in links.py.
    """
    if label:
        return label
    title = _title(target, token, source)
    # A title is text, not authored Markdown or HTML. Numeric entities survive
    # Markdown parsing as literal characters without enabling markup, nested
    # links, table separators, house markers, or an entity supplied by a title.
    return "".join(
        "&#" + str(ord(char)) + ";" if char in "\\`*_{}[]<>&!|~" else char
        for char in title
    )


def _attr(value) -> str:
    """HTML-escape once, also protecting later house hooks and Markdown tables."""
    text = html.escape(_text(value), quote=True)
    for char in "[]{}|`":
        text = text.replace(char, "&#" + str(ord(char)) + ";")
    return text


def page_link(label, target, token, source, href, opts="", peer=False):
    """Finish an already-resolved page link; never performs a second lookup."""
    shortcut = label.strip()
    icon = ICONS.get(shortcut)
    if shortcut in ICONS.values():
        icon = shortcut
    gloss = _text(target.get("gloss"))
    # Preserve old Markdown output when no new decoration is requested.
    if not icon and not gloss and not re.search(r"\bcolor\s*=", opts):
        return ("[" + page_label(label, target, token, source) + "](" + href + ")"
                + ("{ .docrender-xref }" if peer else "") + opts)

    classes = ["docrender-xref"] if peer else []
    attrs = {}
    color = None
    for key, value in get_attrs(opts.strip()[1:-1]) if opts else []:
        if key == ".":
            classes.append(value)
        elif key == "class":
            classes.extend(value.split())
        elif key == "color":
            if icon and value in COLORS:
                color = value
            else:
                state.note("notes", source + ": color=" + value
                           + " ignored; icon colors: " + ", ".join(sorted(COLORS)) + ".")
        elif (_ATTR_NAME.fullmatch(key)
              and (key in ("id", "title", "target", "rel")
                   or key.startswith("aria-") or key.startswith("data-"))):
            attrs[key] = value
        else:
            state.note("notes", source + ": unsupported page-link attribute " + key + " ignored.")

    if icon:
        title = _title(target, token, source)
        classes.append("dr-link-icon")
        attrs["aria-label"] = title
        if gloss:
            attrs["aria-description"] = gloss
        popup = title + (": " + gloss if gloss else "")
        body = '<span aria-hidden="true">' + icon + "</span>"
    else:
        popup = gloss
        attrs["aria-description"] = gloss
        # Preserve inline emphasis/code in explicit labels. No block wrapper.
        body = markdown.markdown(page_label(label, target, token, source))
        if body.startswith("<p>") and body.endswith("</p>"):
            body = body[3:-4]
    if popup:
        classes.append("dr-gloss")
        attrs["data-gloss"] = popup
    if attrs.get("target") == "_blank":
        attrs["rel"] = " ".join(dict.fromkeys(
            (attrs.get("rel", "") + " noopener noreferrer").split()))
    if classes:
        attrs["class"] = " ".join(dict.fromkeys(classes))
    # The only generated style value is a validated role, never author CSS.
    if color:
        attrs["style"] = "--dr-link-icon-color:var(--dr-" + color + ")"
    return ('<a href="' + _attr(href) + '"'
            + "".join(" " + key + '="' + _attr(value) + '"' for key, value in attrs.items())
            + ">" + body + "</a>")
