"""`!!! tally "name"` -- a live-math worksheet that hands its numbers to a form.

    tally:
      box-office:
        form: foh-report              # a slot in this page's `forms:` block
        Door Sales:                   # every other key is a SECTION
          Door Student: count @ 10    # a priced count: quantity in, dollars out
          Door Tickets Sold: count = Door Student + Door General
          Door: money = Door Student dollars + Door General dollars
          Concessions Total: money | include in receipts
        Receipts:
          Over Short: check money = Income Cash - Door

    !!! tally "box-office"

The whole contract, argued, lives in `specs/tally.md`. Warnings stay here.

⭐ A ROW NAME IS THREE THINGS AT ONCE: the label the reader sees, the name an
expression uses, and the ClickUp QUESTION LABEL prefill matches on. One string, so
they cannot drift apart. 🔴 THE ENGINE CANNOT SEE THE LIVE FORM, so a name that
matches no question prefills nothing, silently. Rename the question, not the row.

⭐ MATH COMPILES HERE, NOT IN THE BROWSER. Each expression is parsed at build time
into postfix tokens, so a typo'd name is a BUILD FINDING with the row named, never
a sheet that quietly shows $0.00. The browser only runs a ten-line stack machine.

🔴 A COMPUTED ROW MAY ONLY USE ROWS ABOVE IT. That is what makes evaluation a
single pass in page order, and it rules out cycles by construction.

🔴 NO BLANK LINE MAY APPEAR IN THE EMITTED HTML. A blank line ends a raw HTML block
and Markdown starts rewriting the rest of the sheet as paragraphs. `_html` joins
with single newlines; `[` and `]` are entity-escaped so `](` and `]{` can never form.

⚠️ PRICES LIVE IN THE PAGE, NOT HERE (Michael, 2026-09-28): a stopgap until the
FileMaker price schema exists. The engine knows no production and no price.

🔴 THE SEND BUTTON REPLACES THE IFRAME NODE, never `iframe.src =`, for the same
Back-button reason `forms._RESET_JS` gives. The replaced frame loses ClickUp's
height listener and sits at the forms floor, which is the known forms behaviour.
"""

from __future__ import annotations

import re

from . import forms, state
from .tally_assets import CSS, JS
from .util import directive_options, sub_outside_code

_TALLY = re.compile(r'(?m)^[ \t]*!!![ \t]+tally[ \t]+"([^"\n]+)"(?P<opts>[^\n]*)$')

_INPUTS = ("count", "money", "number", "text", "email", "notes", "date", "datetime")
_NUMERIC = ("count", "money", "number")
_FORMATS = ("money", "count", "number", "percent")
_RESERVED = ("form",)
_OPS = {"+": 1, "-": 1, "*": 2, "/": 2}
_SYMBOLS = {"×": "*", "÷": "/", "−": "-"}
_NUM = re.compile(r"\d+(?:\.\d+)?|\.\d+")
_PRICE = re.compile(r"^count[ \t]*@[ \t]*\$?(\d+(?:\.\d+)?)$")


def _esc(text) -> str:
    return forms._esc(text).replace("[", "&#91;").replace("]", "&#93;")


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-") or "row"


class TallyError(ValueError):
    """One human sentence, ready for `state.note`."""


def _split_hint(spec: str):
    spec, _, hint = str(spec).partition("|")
    return spec.strip(), hint.strip()


def compile_expr(expr: str, known: dict) -> tuple[list, set]:
    """`expr` -> (postfix tokens, input slugs it depends on).

    `known` maps a lower-cased name to `(token_list, deps)`; a priced count is
    registered twice, as `Name` (quantity) and `Name dollars` (quantity x price).
    Longest name wins, so `Door Student dollars` never reads as `Door Student`.
    """
    names = sorted(known, key=len, reverse=True)
    out, ops, deps = [], [], set()
    text, i, expect_value = expr.strip(), 0, True
    while i < len(text):
        ch = text[i]
        if ch.isspace():
            i += 1
            continue
        ch = _SYMBOLS.get(ch, ch)
        if expect_value:
            num = _NUM.match(text, i)
            if num:
                out.append(num.group(0))
                i, expect_value = num.end(), False
                continue
            if ch == "(":
                ops.append("(")
                i += 1
                continue
            if ch == "-":
                ops.append("neg")
                i += 1
                continue
            low = text[i:].lower()
            hit = next((n for n in names if low.startswith(n)
                        and not low[len(n):len(n) + 1].isalnum()), None)
            if not hit:
                word = re.match(r"[^+\-*/()×÷−]+", text[i:])
                raise TallyError(
                    "`" + (word.group(0).strip() if word else text[i:]) + "` is not a "
                    "row above this one. Names must match a row exactly, and a "
                    "computed row can only use rows defined before it."
                )
            toks, row_deps = known[hit]
            out.extend(toks)
            deps |= row_deps
            i, expect_value = i + len(hit), False
            continue
        if ch == ")":
            while ops and ops[-1] != "(":
                out.append(ops.pop())
            if not ops:
                raise TallyError("a `)` with no matching `(`.")
            ops.pop()
            while ops and ops[-1] == "neg":
                out.append(ops.pop())
            i += 1
            continue
        if ch in _OPS:
            while ops and ops[-1] != "(" and (ops[-1] == "neg" or _OPS[ops[-1]] >= _OPS[ch]):
                out.append(ops.pop())
            ops.append(ch)
            i, expect_value = i + 1, True
            continue
        raise TallyError("`" + text[i:].strip() + "` is not an operator. Use + - * / and ( ).")
    if expect_value:
        raise TallyError("the expression ends where a value was expected.")
    while ops:
        op = ops.pop()
        if op == "(":
            raise TallyError("a `(` that is never closed.")
        out.append(op)
    return out, deps


def parse(name: str, block) -> tuple[str, list, list]:
    """A tally block -> (form slot, sections, problems). Pure; no I/O."""
    problems: list[str] = []
    if not isinstance(block, dict):
        raise TallyError("`tally: " + name + "` must be a map of sections.")
    form = str(block.get("form") or "").strip()
    known: dict = {}
    seen: set = set()
    sections = []
    for title, rows in block.items():
        if title in _RESERVED:
            continue
        if not isinstance(rows, dict):
            problems.append("section `" + str(title) + "` is not a map of rows; skipped.")
            continue
        out_rows = []
        for label, spec in rows.items():
            label = str(label).strip()
            key = slug(label)
            if key in seen:
                problems.append("row `" + label + "` appears twice; the second was dropped.")
                continue
            try:
                row = _row(label, key, spec, known)
            except TallyError as err:
                problems.append("row `" + label + "`: " + str(err))
                continue
            seen.add(key)
            out_rows.append(row)
        sections.append((str(title), out_rows))
    return form, sections, problems


def _row(label, key, spec, known) -> dict:
    row = {"label": label, "key": key, "hint": ""}
    if isinstance(spec, list):
        row.update(kind="choice", options=[str(o) for o in spec])
        return row
    body, row["hint"] = _split_hint("" if spec is None else spec)
    head, eq, expr = body.partition("=")
    head = head.strip().lower()
    if eq:
        check = head.startswith("check")
        fmt = head[5:].strip() if check else head
        if fmt not in _FORMATS:
            raise TallyError("`" + head + "` is not a result format. Legal: "
                             + ", ".join(_FORMATS) + ", optionally after `check`.")
        toks, deps = compile_expr(expr, known)
        if not deps:
            raise TallyError("the expression uses no input row, so it can never change.")
        row.update(kind="calc", fmt=fmt, check=check, expr=toks, deps=deps)
        known[label.lower()] = (["$" + key], deps)
        return row
    price = _PRICE.match(head)
    if price:
        row.update(kind="count", price=price.group(1))
        known[label.lower()] = (["$" + key], {key})
        known[label.lower() + " dollars"] = (["$" + key, price.group(1), "*"], {key})
        return row
    if head not in _INPUTS:
        raise TallyError("`" + head + "` is not a row type. Legal: " + ", ".join(_INPUTS)
                         + ", `count @ price`, a list of choices, or `format = expression`.")
    row["kind"] = head
    if head in _NUMERIC:
        known[label.lower()] = (["$" + key], {key})
    return row


def _field(row, rid) -> str:
    k, kind = row["key"], row["kind"]
    common = ' id="' + rid + '" data-k="' + k + '" data-send="' + _esc(row["label"]) + '"'
    if kind == "choice":
        opts = "".join("<option>" + _esc(o) + "</option>" for o in row["options"])
        return '<select' + common + '><option value="">Pick one</option>' + opts + "</select>"
    if kind == "notes":
        return "<textarea" + common + "></textarea>"
    types = {"count": "number", "money": "number", "number": "number",
             "text": "text", "email": "email", "date": "date", "datetime": "datetime-local"}
    extra = {"count": ' min="0" step="1" inputmode="numeric"',
             "money": ' step="0.01" inputmode="decimal"',
             "number": ' step="any" inputmode="decimal"'}.get(kind, "")
    return ('<input type="' + types[kind] + '"' + common + extra
            + (' data-kind="' + kind + '"' if kind in ("date", "datetime") else "") + ">")


def _need(row) -> str:
    """🔴 A COMPARISON WAITS FOR BOTH SIDES. A check or percent row goes live only
    when EVERY row it names directly is live, so `House Count - Expected House`
    stays blank until the house is counted instead of shouting `-50 short` the
    moment one ticket is typed. Every other result goes live on ANY input."""
    if not (row["check"] or row["fmt"] == "percent"):
        return ""
    refs = []
    for tok in row["expr"]:
        if tok.startswith("$") and tok[1:] not in refs:
            refs.append(tok[1:])
    return ' data-need="' + " ".join(refs) + '"'


def _html(tname, form_url, sections, dead="") -> str:
    tid = "dr-tally-" + slug(tname)
    lines = ['<div class="dr-tally" id="' + tid + '" data-tally="' + _esc(slug(tname))
             + '" data-form="' + _esc(form_url) + '">', '<div class="dr-tally__grid">']
    for title, rows in sections:
        lines.append('<fieldset class="dr-tally__sec"><legend>' + _esc(title) + "</legend>")
        for row in rows:
            rid = tid + "-" + row["key"]
            hint = (" <small>" + _esc(row["hint"]) + "</small>") if row["hint"] else ""
            kind = row["kind"]
            if kind == "calc":
                cls = "dr-tally__row dr-tally__row--calc" + (" dr-tally__row--check" if row["check"] else "")
                lines.append(
                    '<div class="' + cls + '"><span>' + _esc(row["label"]) + hint + "</span>"
                    '<output data-k="' + row["key"] + '" data-fmt="' + row["fmt"] + '"'
                    + (' data-check="1"' if row["check"] else "")
                    + ' data-expr="' + _esc(" ".join(row["expr"])) + '" data-deps="'
                    + " ".join(sorted(row["deps"])) + '"' + _need(row) + "></output></div>")
            elif kind == "count" and "price" in row:
                lines.append(
                    '<div class="dr-tally__row dr-tally__row--priced"><label for="' + rid + '">'
                    + _esc(row["label"]) + " <small>$" + _esc(row["price"]) + "</small>" + hint
                    + "</label>" + _field(row, rid) + '<output data-fmt="money" data-expr="$'
                    + row["key"] + " " + row["price"] + ' *" data-deps="' + row["key"]
                    + '"></output></div>')
            else:
                wide = " dr-tally__row--wide" if kind == "notes" else ""
                lines.append('<div class="dr-tally__row' + wide + '"><label for="' + rid + '">'
                             + _esc(row["label"]) + hint + "</label>" + _field(row, rid) + "</div>")
        lines.append("</fieldset>")
    lines.append("</div>")
    if dead:
        lines.append('<p class="dr-tally__bar">' + dead + "</p>")
    else:
        lines.append(
            '<p class="dr-tally__bar"><button type="button" class="dr-tally__send">'
            "Send to report ↓</button><button type=\"button\" class=\"dr-tally__clear\">"
            'Clear</button><a class="dr-tally__open" href="' + _esc(form_url)
            + '" target="_blank" rel="noopener">open the form in a new tab</a></p>')
    lines.append('<p class="dr-tally__status" aria-live="polite"></p>')
    lines.append("</div>")
    return "\n".join(lines)


def render(src, tname, meta) -> str:
    """One directive -> HTML, reporting every fault. Never raises."""
    block = ((meta or {}).get("tally") or {})
    if not isinstance(block, dict) or tname not in block:
        known = sorted(block) if isinstance(block, dict) else []
        state.note("dead_links", src + ': `!!! tally "' + tname + '"` names no entry in '
                   "this page's `tally:` block. Declared here: " + (", ".join(known) or "nothing") + ".")
        return forms._dead("tally not declared on this page: " + tname, "Worksheet")
    try:
        slot, sections, problems = parse(tname, block[tname])
    except TallyError as err:
        state.note("dead_links", src + ": " + str(err))
        return forms._dead(str(err), "Worksheet")
    for problem in problems:
        state.note("notes", src + ": `tally: " + tname + "` " + problem)
    entry = forms._entry(src, slot) if slot else None
    url = entry[0] if entry else ""
    dead = ""
    if not url.startswith("https://forms.clickup.com/"):
        why = ("names no `form:` slot" if not slot else "`form: " + slot + "` is not a ClickUp form slot on this page")
        state.note("notes", src + ": `tally: " + tname + "` " + why + ". The sheet works; nothing can be sent.")
        dead, url = forms._dead("worksheet " + why, "Send"), ""
    return _html(tname, url, sections, dead)


def on_page_markdown(markdown, page, config, files):
    if "!!!" not in markdown or "tally" not in markdown:
        return markdown
    src = getattr(page.file, "src_uri", "")
    meta = state.BY_SRC.get(src) or getattr(page, "meta", {}) or {}
    drew = []

    def swap(match):
        tname = match.group(1).strip()
        opts, problems = directive_options(match.group("opts"), ())
        if opts:
            problems.append("options, and a worksheet takes none (it is always full width). Ignored.")
        for problem in problems:
            state.note("notes", src + ': `!!! tally "' + tname + '"` carries ' + problem)
        out = render(src, tname, meta)
        if "dr-tally" in out:
            drew.append(1)
        return "\n\n" + out + "\n\n"

    out = sub_outside_code(_TALLY, swap, markdown)
    if drew:
        out += "\n\n" + CSS + "\n\n" + JS + "\n"
    return out
