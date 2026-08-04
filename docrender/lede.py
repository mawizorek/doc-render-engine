"""The lede, and the keywords line. What a page says before it starts arguing.

WHY THE LEDE IS A FIELD AND NOT A POSITION (decided 2026-08-03, Michael).

It used to be defined three times, in three languages, and none of the three
knew the others existed:

    stylesheet   `.md-typeset h1 + p` -- the paragraph ELEMENT after the H1
    engine       the first non-blank run of lines after the `# ` line
    search       everything between the H1 and the next heading

Those three agree perfectly on a page that opens with exactly one paragraph,
and diverge on every page that does not. Nothing checked it, so the divergence
was silent and looked like a styling bug: on a page whose H1 is followed
straight by `## Section`, the old code read the HEADING as the lede and planted
the generated spec table underneath it.

Now it is `summary:`, required on `_base`, rendered here into the slot after the
H1. One definition. The stylesheet targets what this emits instead of guessing
at document shape, and search indexes it because it is genuinely on the page.

⚠️ NO POSITIONAL FALLBACK, and that was the explicit call. "Field wins, a body
paragraph stays legal" was on the table and was REJECTED: a sanctioned fallback
is a fourth definition of the lede, which is the defect this module exists to
remove. A page keeping its lede in the body gets REPORTED, never quietly
absorbed.

THE MIGRATION IS LOUD ON PURPOSE. Every page written before this carries its
lede positionally, so the first build after it ships reports the whole tree.
That is a worklist, not a regression -- nothing fails, nothing stops
publishing, and a page with no `summary:` renders exactly as it did the day
before.

THE KEYWORDS LINE is the same argument pointed at search. `keywords: [genie,
personnel lift]` renders as a visible line at the foot, so the words are indexed
because they are ON THE PAGE rather than injected into an index by a mechanism
nobody can see. A HIDDEN meta block was the rejected option: it cannot be
audited, so it rots silently, and the first symptom is a search that quietly
stopped matching.

⚠️ RENAMED FROM `also_known_as` 2026-08-04, Michael. The old key is reported via
objects.py _LEGACY_KEYS. **The visible label moved with the field on purpose:**
the old name could only honestly hold aliases, and the new one also holds search
terms that are not names, so "Also called: electrics" was about to be false.

⚠️ THE CSS CLASS IS STILL `dr-aka` AND THAT IS DELIBERATE, not a half-finished
rename. Moving it means editing a stylesheet measured near the read-clip line,
and a file that cannot be read whole cannot be safely rewritten -- which is a
worse trade than one internal name that disagrees with its field. Named here so
the next reader does not mistake it for an oversight.
"""

from __future__ import annotations

import re

_H1 = "# "

#: A list item opening a block. Up to three spaces of indent, which is all
#: Python-Markdown allows before it stops being a list at all.
_LIST_ITEM = re.compile(r"^ {0,3}(?:[-*+][ \t]|\d+[.)][ \t])")

#: A Material callout or collapsible: `!!! danger`, `??? note`.
_CALLOUT = re.compile(r"^ {0,3}(?:!!!|\?\?\?)")


def _find_h1(lines: list[str]) -> int | None:
    return next((i for i, ln in enumerate(lines) if ln.startswith(_H1)), None)


def _clip(text: str, limit: int = 60) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "..."


def classify(body: str) -> tuple[str, str]:
    """What the first block after the H1 IS, and what it says.

    Returns one of `no_h1` `empty` `paragraph` `heading` `callout` `list`
    `table` `html`, plus that block's text where there is any.

    It classifies rather than answering yes/no because 'no lede found' is the
    same sentence for a page that opens with a table and a page with no body,
    and those are different jobs for whoever has to fix it.
    """
    lines = body.splitlines()
    h1 = _find_h1(lines)
    if h1 is None:
        return "no_h1", ""

    i = h1 + 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return "empty", ""

    first = lines[i]
    stripped = first.lstrip()
    if stripped.startswith("#"):
        return "heading", stripped
    if _CALLOUT.match(first):
        return "callout", stripped
    if _LIST_ITEM.match(first):
        return "list", stripped
    if stripped.startswith("|"):
        return "table", stripped
    if stripped.startswith("<"):
        return "html", stripped

    run = []
    while i < len(lines) and lines[i].strip():
        run.append(lines[i].strip())
        i += 1
    return "paragraph", " ".join(run)


def check(src: str, meta: dict, body: str, note) -> None:
    """Report a page whose lede is not where the field says it is.

    Runs in hook 01, on EVERY page including hidden ones, for the same reason
    the rest of that hook does: a page is broken or not regardless of whether
    it happens to be published today.

    A missing `summary:` is already reported by the required-field check. What
    is added here is WHERE THE TEXT IS -- the difference between a lede that
    needs moving and a lede that has to be written.
    """
    summary = str(meta.get("summary") or "").strip()
    kind, text = classify(body)

    if kind == "no_h1":
        note(
            "body_lede",
            src + ": no `# ` heading. There is nowhere to render the lede, so "
            + "`summary:` is dropped even if it is set, and the page has no "
            + "title in its own body.",
        )
        return

    if summary and kind == "paragraph":
        note(
            "body_lede",
            src + ": has BOTH `summary:` and a paragraph under the H1. The "
            + "field is the lede; that paragraph now renders as ordinary body "
            + 'text directly beneath it, usually saying the same thing twice '
            + '-- "' + _clip(text) + '"',
        )
        return

    if kind == "paragraph":
        note(
            "body_lede",
            src + ": lede is still in the BODY. Move it into `summary:` and "
            + 'delete the paragraph -- "' + _clip(text) + '"',
        )
        return

    if not summary:
        note(
            "body_lede",
            src + ": no `summary:`, and no paragraph under the H1 to migrate "
            + "(found " + kind + "). This lede has to be WRITTEN, not moved. "
            + "Until it is, the page's search result shows no text at all.",
        )


def render(markdown: str, summary) -> str:
    """Put the summary in the slot immediately after the H1.

    Emitted as a real element with a class rather than as a bare paragraph, so
    the stylesheet can target what the engine MADE instead of inferring the
    lede from document shape a third time.
    """
    text = " ".join(str(summary).split())
    if not text:
        return markdown

    lines = markdown.splitlines()
    h1 = _find_h1(lines)
    if h1 is None:
        # Nothing to anchor to. `check` reports it; nothing is invented here.
        # Guessing a position for generated content is exactly how a spec
        # table ended up inside somebody's first section.
        return markdown

    block = '<p class="dr-lede" markdown="1">' + text + "</p>"
    return "\n".join(lines[: h1 + 1] + ["", block] + lines[h1 + 1 :])


def keywords(value) -> str:
    """The keywords line. VISIBLE, which is the whole point of it.

    Accepts a list or a comma-separated string, because both are what people
    actually type and refusing one of them buys nothing.

    ⚠️ The emitted class is `dr-aka`, not `dr-keywords`. See the module
    docstring: the stylesheet that would have to change sits near the read-clip
    line, and that is a worse risk than one stale internal name.
    """
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, str):
        names = value.split(",")
    else:
        names = [str(v) for v in value]
    names = [" ".join(n.split()) for n in names]
    names = [n for n in names if n]
    if not names:
        return ""
    return '<p class="dr-aka">Keywords: ' + ", ".join(names) + "</p>"


def insert_after(markdown: str, block: str) -> str:
    """Place generated content after the H1 and the lede.

    Moved here from objects.py unchanged: it is a function about the lede, and
    it was the biggest thing in that file that was not about types.

    Anything it cannot parse confidently goes at the TOP rather than being
    placed on a guess, because a wrong guess splits a sentence in half.
    """
    lines = markdown.splitlines()
    h1 = _find_h1(lines)
    if h1 is None:
        return block + "\n" + markdown
    i = h1 + 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    while i < len(lines) and lines[i].strip():
        i += 1
    return "\n".join(lines[:i] + ["", block] + lines[i:])
