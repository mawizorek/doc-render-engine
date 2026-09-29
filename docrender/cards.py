"""`!!! cards` -- a launcher grid Michael controls from one line.

    !!! cards cols=3 phone=2 size=l style=tiles color=blue
        - 🎟️ [House Reports](@app-foh-report) {color=red badge="Tonight"}
          Submit each performance's report.
        - @run-sheet-foh {wide}
        - Parked idea, no link yet

The contract, argued, is `specs/cards.md`. Warnings stay here.

⭐ IT COMPILES DOWN TO MATERIAL'S OWN `grid cards` MARKUP (Frank's condition,
2026-09-28). The emitted block is the same `<div class="grid cards" markdown>` +
loose `-   ` list authors hand-wrote before, plus classes. Hover, borders and dark
mode stay Material's; this file only adds columns, size, style, colour and tap.
Hand-written `grid cards` pages are untouched.

🔴 HOOK 03 ALREADY RAN. `[x](@id)` arrives here as a finished relative URL (or a
`docrender-dead` span), and an author brace after it arrives re-emitted verbatim,
which is why a card's `{color=... badge=... wide}` can be read at this stage. A
BARE `@id` card is the one reference links.py never sees, so this file resolves
it against `state.PAGES` (built pages only) and records the edge with `state.ref`
exactly as links.py would.

🔴 PER-CARD KNOBS RIDE ON AN EMPTY `<span class="dr-k ...">` AND CSS `:has()`.
Markdown gives a list item no attribute hook, and a second pass over rendered
HTML would be a second parser for one class name. The trade: the style needs
`:has()` (every current browser); an old one gets a plain Material card.

⚠️ A BRACE IS ONLY CONSUMED WHEN IT NAMES A CARD KNOB (color, badge, wide).
`{.align-center}` or any other attr_list is left alone for attr_list. A brace that
names a knob is ours: its good tokens apply and its bad ones are reported.

⚠️ FENCES ARE GUARDED, INLINE CODE IS NOT, and that differs from `sub_outside_code`
on purpose: that helper splits the text at every backtick span, which would cut a
card block in half whenever a blurb contains `code`. A page DOCUMENTING the
directive puts it in a fence, and a fence is protected.
"""

from __future__ import annotations

import html
import re

from . import state

_BLOCK = re.compile(
    r"(?m)^(?P<ind>[ \t]*)!!![ \t]+cards\b(?P<opts>[^\n]*)\n"
    r"(?P<body>(?:[ \t]*\n|(?P=ind)[ \t]+[^\n]*(?:\n|\Z))*)"
)
_FENCE = re.compile(r"(?ms)^[ \t]*(?P<f>`{3,}|~{3,}).*?(?:^[ \t]*(?P=f)[ \t]*$|\Z)")
_OPT = re.compile(r'([A-Za-z]+)=("[^"]*"|\'[^\']*\'|\S+)|(\S+)')
_KNOBS = re.compile(r"[ \t]*\{([^{}\n]*)\}[ \t]*$")
_ICON = re.compile(
    "^((?:[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\u2190-\u21FF"
    "\u2300-\u23FF\uFE0F\u200D\u20E3])+)[ \t]+"
)
_BARE = re.compile(r"^@([A-Za-z0-9_.-]+)$")
_MDLINK = re.compile(r"(?<!!)\[[^\]\n]*\]\([^)\s]+\)(?P<brace>\{[^}\n]*\})?")

#: Material's 600 shades. Named, not hex: a class can carry a name, and the
#: card's colour has to reach its `<li>` through `:has()`, which cannot read a value.
COLORS = {
    "red": "#e53935", "pink": "#d81b60", "purple": "#8e24aa", "indigo": "#3949ab",
    "blue": "#1e88e5", "cyan": "#00acc1", "teal": "#00897b", "green": "#43a047",
    "lime": "#7cb342", "yellow": "#fdd835", "amber": "#ffb300", "orange": "#fb8c00",
    "brown": "#6d4c41", "grey": "#757575",
}
_GRID = {
    "cols": ("1", "2", "3", "4", "5", "6"),
    "phone": ("1", "2"),
    "size": ("s", "m", "l"),
    "style": ("tiles", "rows"),
    "color": tuple(COLORS),
}
_SIZE_WORDS = {"small": "s", "medium": "m", "large": "l"}


def _esc(text) -> str:
    return html.escape(str(text), quote=True)


def _unq(value: str) -> str:
    if len(value) > 1 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def grid_options(tail: str):
    """Directive-line options -> (opts, problems). Unknown keys are reported."""
    opts, problems = {}, []
    for key, value, stray in _OPT.findall(tail or ""):
        if stray:
            problems.append("stray text `" + stray + "` (options are key=value). Ignored.")
            continue
        key, value = key.lower(), _unq(value).lower()
        value = _SIZE_WORDS.get(value, value) if key == "size" else value
        if key not in _GRID:
            problems.append("unknown option `" + key + "`. Legal: " + ", ".join(_GRID) + ". Ignored.")
        elif value not in _GRID[key]:
            problems.append("`" + key + "=" + value + "` is not one of "
                            + ", ".join(_GRID[key]) + ". Ignored.")
        else:
            opts[key] = value
    return opts, problems


def card_knobs(head: str):
    """Strip a trailing `{color=.. badge=".." wide}` -> (head, knobs, problems).

    A brace naming NONE of the three knobs is somebody's attr_list and is left
    exactly as written. One naming any of them is ours: good tokens apply, bad
    ones are reported, and the brace is consumed either way.
    """
    m = _KNOBS.search(head)
    if not m:
        return head, {}, []
    toks = _OPT.findall(m.group(1))
    if not any((k or f).lower() in ("color", "badge", "wide") for k, _v, f in toks):
        return head, {}, []
    knobs, bad = {}, []
    for key, value, flag in toks:
        key, value = (key or flag).lower(), _unq(value)
        if key == "wide":
            knobs["wide"] = (not value) or value.lower() in ("true", "yes", "1")
        elif key == "badge" and value:
            knobs["badge"] = value
        elif key == "color" and value.lower() in COLORS:
            knobs["color"] = value.lower()
        elif key == "color":
            bad.append("`color=" + value + "` (colours: " + ", ".join(COLORS) + ")")
        else:
            bad.append("`" + (flag or key + "=" + value) + "` (knobs: color, badge, wide)")
    return head[:m.start()], knobs, ["card knob " + b + " ignored." for b in bad]


def split_cards(body: str):
    """Indented body -> [(head, [continuation lines])], problems."""
    lines = body.split("\n")
    live = [ln for ln in lines if ln.strip()]
    if not live:
        return [], []
    cut = min(len(ln) - len(ln.lstrip()) for ln in live)
    cards, problems = [], []
    for raw in lines:
        line = raw[cut:] if raw.strip() else ""
        if line[:2] in ("- ", "* "):
            cards.append([line[2:].strip(), []])
        elif not line:
            if cards:
                cards[-1][1].append("")
        elif line[:1] in (" ", "\t") and cards:
            cards[-1][1].append(line)
        else:
            problems.append("line `" + line.strip()[:40] + "` is not a card (cards start `- `). Ignored.")
    return cards, problems


def _dedent(rest):
    while rest and not rest[-1].strip():
        rest.pop()
    while rest and not rest[0].strip():
        rest.pop(0)
    live = [ln for ln in rest if ln.strip()]
    cut = min((len(ln) - len(ln.lstrip()) for ln in live), default=0)
    return [ln[cut:] if ln.strip() else "" for ln in rest]


def _bare(pid, page, src_id):
    """A bare `@id` card -> (title markdown, summary) against built pages only."""
    hit = state.PAGES.get(pid)
    if not hit:
        state.ref(src_id, pid, "page", pid, False)
        return ('<span class="docrender-dead" title="no page yet with id: ' + _esc(pid)
                + '">@' + _esc(pid) + "</span>"), "", False
    state.ref(src_id, pid, "page", pid, True)
    from .util import relative_url
    url = relative_url(str(hit.get("url", "")), page.file.url)
    summary = ""
    for meta in state.BY_SRC.values():
        if (meta or {}).get("id") == pid:
            summary = str(meta.get("summary") or "")
            break
    title = str(hit.get("title") or pid).replace("[", "&#91;").replace("]", "&#93;")
    return "[" + title + "](" + url + ")", summary, True


def _card(head, rest, page, src, src_id):
    problems = []
    head, knobs, bad = card_knobs(head)
    problems += bad
    icon = ""
    m = _ICON.match(head)
    if m:
        icon, head = m.group(1), head[m.end():]
    rest = _dedent(rest)
    bare = _BARE.match(head.strip())
    if bare:
        head, summary, ok = _bare(bare.group(1), page, src_id)
        if not ok:
            problems.append("card `@" + bare.group(1) + "` names no built page. Drawn as dead.")
        if not rest and summary:
            rest = [summary]
    links = list(_MDLINK.finditer(head + "\n" + "\n".join(rest)))
    if len(links) == 1:
        hit = links[0]
        where = "head" if hit.start() < len(head) else "rest"
        text = head if where == "head" else "\n".join(rest)
        start = hit.start() if where == "head" else hit.start() - len(head) - 1
        end = start + (hit.end() - hit.start())
        chunk = text[start:end]
        chunk = (chunk.replace("{", "{.dr-t ", 1) if hit.group("brace") else chunk + "{.dr-t}")
        text = text[:start] + chunk + text[end:]
        if where == "head":
            head = text
        else:
            rest = text.split("\n")
    cls = ["dr-k"]
    if knobs.get("color"):
        cls.append("dr-c-" + knobs["color"])
    if knobs.get("wide"):
        cls.append("dr-wide")
    lead = '<span class="' + " ".join(cls) + '"></span>'
    if knobs.get("badge"):
        lead += '<span class="dr-badge">' + _esc(knobs["badge"]) + "</span>"
    if icon:
        lead += '<span class="dr-icon" aria-hidden="true">' + icon + "</span>"
    out = ["-   " + lead + head.strip(), ""]
    for ln in rest:
        out.append(("    " + ln) if ln else "")
    if rest:
        out.append("")
    return "\n".join(out), problems


def render(opts_tail, body, page, src, src_id):
    opts, problems = grid_options(opts_tail)
    cards, more = split_cards(body)
    problems += more
    if not cards:
        state.note("notes", src + ": `!!! cards` has no `- ` cards under it. Nothing drawn.")
        return ""
    style = opts.get("style", "tiles")
    cols = opts.get("cols", "1" if style == "rows" else "3")
    cls = ["grid", "cards", "dr-cards", "dr-cols-" + cols, "dr-phone-" + opts.get("phone", "1"),
           "dr-size-" + opts.get("size", "m"), "dr-" + style]
    if opts.get("color"):
        cls.append("dr-c-" + opts["color"])
    items = []
    for head, rest in cards:
        md, bad = _card(head, rest, page, src, src_id)
        items.append(md)
        problems += bad
    for p in problems:
        state.note("notes", src + ": `!!! cards` " + p)
    return ('<div class="' + " ".join(cls) + '" markdown>\n\n' + "\n".join(items)
            + "\n</div>")


def _css() -> str:
    tint = "color-mix(in srgb,{0} 9%,transparent)"
    colors = "".join(
        ".dr-cards.dr-c-{n},.dr-cards>ul>li:has(.dr-k.dr-c-{n}){{--dr-a:{h};--dr-tint:{t}}}"
        .format(n=n, h=h, t=tint.format(h)) for n, h in COLORS.items())
    cols = "".join(".dr-cols-{0}{{--dr-c:{0};--dr-t:{1}}}".format(n, min(n, 2)) for n in range(1, 7))
    g = ".md-typeset .grid.dr-cards"
    li = g + ">ul>li"
    return (
        "<style>" + cols + colors + ".dr-phone-2{--dr-p:2}"
        + g + "{--dr-n:var(--dr-p,1);--dr-w:var(--dr-p,1);"
        "grid-template-columns:repeat(var(--dr-n),minmax(0,1fr));gap:.6rem}"
        "@media screen and (min-width:600px){" + g + "{--dr-n:var(--dr-t);--dr-w:var(--dr-t)}}"
        "@media screen and (min-width:960px){" + g + "{--dr-n:var(--dr-c)}}"
        + li + "{position:relative;background:var(--dr-tint,transparent);"
        "border-top:.25rem solid var(--dr-a,var(--md-default-fg-color--lightest))}"
        + li + ":has(.dr-wide){grid-column:span var(--dr-w)}"
        + li + ">p:first-child{font-weight:700}"
        + li + ">p:first-child a{color:inherit}"
        + li + ":has(.dr-t):hover{border-top-color:var(--dr-a,var(--md-accent-fg-color))}"
        ".dr-cards a.dr-t::after{content:'';position:absolute;inset:0;z-index:1}"
        ".dr-cards a.dr-t:focus-visible{outline:none}"
        + li + ":has(a.dr-t:focus-visible){outline:.15rem solid var(--dr-a,var(--md-accent-fg-color));"
        "outline-offset:.1rem}"
        + li + ":has(.docrender-dead){opacity:.65;border-style:dashed}"
        ".dr-cards .dr-badge{float:right;margin:0 0 .2rem .5rem;padding:.05rem .5rem;border-radius:1rem;"
        "font-size:.72em;font-weight:700;color:#fff;background:var(--dr-a,var(--md-default-fg-color--light))}"
        ".dr-cards .dr-icon{display:block;line-height:1.1;margin-bottom:.35rem;font-size:2em}"
        + g + ".dr-size-s>ul>li{padding:.5rem .7rem}" + g + ".dr-size-s .dr-icon{font-size:1.4em}"
        + g + ".dr-size-m>ul>li{min-height:6rem}"
        + g + ".dr-size-l>ul>li{padding:1.1rem 1.2rem;min-height:9rem}"
        + g + ".dr-size-l>ul>li>p:first-child{font-size:1.15em}" + g + ".dr-size-l .dr-icon{font-size:2.8em}"
        + g + ".dr-rows>ul>li{min-height:0;padding-right:2rem;border-top-width:.05rem;"
        "border-left:.25rem solid var(--dr-a,var(--md-default-fg-color--lightest))}"
        + g + ".dr-rows .dr-icon{display:inline;font-size:1.3em;margin:0 .45rem 0 0;vertical-align:-.1em}"
        + g + ".dr-rows>ul>li:has(.dr-t)::after{content:'\\203A';position:absolute;right:.8rem;top:50%;"
        "transform:translateY(-50%);font-size:1.4em;opacity:.5}"
        + g + ".dr-rows>ul>li>p{margin:.15rem 0}"
        "@media print{" + g + "{grid-template-columns:repeat(2,minmax(0,1fr))}"
        + li + "{background:none;box-shadow:none;break-inside:avoid;min-height:0}"
        ".dr-cards a.dr-t::after{content:none}}"
        "</style>"
    )


CSS = _css()


def _outside_fences(pattern, repl, text):
    out, cursor = [], 0
    for guard in _FENCE.finditer(text):
        out.append(pattern.sub(repl, text[cursor:guard.start()]))
        out.append(guard.group(0))
        cursor = guard.end()
    out.append(pattern.sub(repl, text[cursor:]))
    return "".join(out)


def on_page_markdown(markdown, page, config, files):
    if "!!!" not in markdown or "cards" not in markdown:
        return markdown
    src = getattr(page.file, "src_uri", "")
    src_id = (state.BY_SRC.get(src) or {}).get("id") or ("path:" + src)
    drew = []

    def swap(m):
        out = render(m.group("opts"), m.group("body"), page, src, src_id)
        if out:
            drew.append(1)
        return "\n\n" + out + "\n\n"

    out = _outside_fences(_BLOCK, swap, markdown)
    if drew:
        out += "\n\n" + CSS + "\n"
    return out
