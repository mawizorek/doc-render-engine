"""The page head -- the lede, the aka line, and the checks on both.

WHY THIS IS A MODULE AND NOT TEN MORE LINES IN objects.py. That file was 17.0KB
when this was written, against an 18KB warn line and a 22KB hard cap that
exists because a file an agent cannot read back whole is a file an agent edits
from a partial read. Adding this there would have crossed the warn line in a
single commit and left whoever came next to do the split under pressure.

THE DECISION THIS IMPLEMENTS (Decision Log Q1, Michael, 2026-08-03). The lede
-- the paragraph under the H1, which is also the text a search result shows --
used to be defined in three places that never spoke to each other:

    stylesheet   `.md-typeset h1 + p`, the paragraph ELEMENT after the H1
    engine       the first non-blank run of lines after the `# ` line
    search       everything between the H1 and the next heading

They agree perfectly on the happy path and diverge the instant the first block
after the H1 is not exactly one paragraph -- and nothing reported it. A page
whose H1 ran straight into `## Section` had its generated spec table planted
underneath that heading. Silently, and it looked like a styling bug.

So the lede becomes a FIELD: `summary:`, required by _base.yml, validated like
every other field, rendered here.

⚠️ THERE IS DELIBERATELY NO FALLBACK, and that rejection is the ruling, not an
oversight. A positional first paragraph is not a second, lesser way to declare
a lede; it is the OLD way, and a page still carrying one is reported. The
defect was three definitions disagreeing. Sanctioning a fallback would have
made a fourth and called it a feature.

MIGRATION POSTURE, because the first run of this against a real tree reports
every page in it. That is a worklist, not an outage. Nothing here can fail a
build, and an unmigrated page renders exactly as it did yesterday, because the
stylesheet still styles whatever paragraph follows the H1. **The stylesheet
swap to `.dr-lede` is the LAST step of the migration and is deliberately not in
this commit** -- doing it first would drop every unmigrated lede to plain body
text across the whole site at once.
"""

from __future__ import annotations

from . import state

#: Line starts that are not the beginning of a paragraph. A page whose first
#: line after the H1 begins with one of these went straight into structure --
#: a heading, callout, tab, table, list, quote, fence or raw HTML -- and has no
#: positional lede to find. Kept as a prefix tuple rather than a parser on
#: purpose: this decides what to REPORT, and a check that needs a full markdown
#: parse to say something honest is a check that will be wrong quietly.
_NOT_A_PARAGRAPH = (
    "#", "!!!", "???", "===", "|", "-", "*", "+", ">", "<", "```", "~~~", "{",
)

#: How much of a body lede to quote back in the report. Long enough to identify
#: the line in the file, short enough that thirty of them stay readable.
_QUOTE = 100


def _one_line(value) -> str:
    """Collapse any whitespace to single spaces.

    A YAML block scalar is the natural way to write two sentences in
    frontmatter, and it arrives here carrying newlines. Emitted raw, those
    newlines would end the paragraph early and strand the attr_list line, which
    would then render as literal `{: .dr-lede }` text on the page.
    """
    return " ".join(str(value).split())


def _h1_index(lines: list[str]) -> int | None:
    for i, line in enumerate(lines):
        if line.startswith("# "):
            return i
    return None


def body_lede(markdown: str) -> str:
    """The paragraph a page carries under its H1, or '' if it has none."""
    lines = markdown.splitlines()
    start = _h1_index(lines)
    if start is None:
        return ""
    i = start + 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return ""
    text = lines[i].strip()
    return "" if text.startswith(_NOT_A_PARAGRAPH) else text


def lede_block(meta: dict) -> str:
    """The generated lede paragraph, carrying the class the stylesheet will
    eventually key on.

    A real paragraph with an attr_list class, NOT a div, and that is
    load-bearing for the whole migration: `<p class="dr-lede">` is still
    matched by the existing `.md-typeset h1 + p` rule, so a migrated page and
    an unmigrated one look identical to a reader until the stylesheet swaps
    over at the end. A div would have made every migrated page visibly
    different the moment it was touched, and the migration would have had to
    land in one commit or look broken in between.
    """
    summary = meta.get("summary")
    if not summary:
        return ""
    return _one_line(summary) + "\n{: .dr-lede }"


def aka_block(meta: dict) -> str:
    """The 'Also called' line for the foot of the page.

    VISIBLE, on purpose (Decision Log Q2). The rejected option was a hidden
    element carrying the same words: it cannot be audited by anyone reading the
    page, so it rots silently and the first symptom is a search that quietly
    stopped matching something. These terms are indexed for the boring reason
    that they are genuinely on the page, which means there is no second search
    mechanism here to maintain or to get out of step.

    Accepts a list or a comma-separated string, because both are the obvious
    thing to type and neither is wrong.
    """
    aka = meta.get("also_known_as")
    if not aka:
        return ""
    if isinstance(aka, (list, tuple)):
        terms = [_one_line(a) for a in aka if str(a).strip()]
    else:
        terms = [t.strip() for t in _one_line(aka).split(",") if t.strip()]
    if not terms:
        return ""
    return "Also called: " + ", ".join(terms) + "\n{: .dr-aka }"


def insert_after_h1(markdown: str, block: str) -> str:
    """Put a block immediately under the H1, ahead of everything else.

    Contrast objects._insert_after_lede, which places a block AFTER the lede.
    Both exist and they compose: insert the lede here first, and the spec table
    then finds a lede to sit under without needing to know one was generated.
    """
    lines = markdown.splitlines()
    start = _h1_index(lines)
    if start is None:
        return block + "\n\n" + markdown
    return "\n".join(lines[:start + 1] + ["", block] + lines[start + 1:])


def check(src: str, meta: dict, markdown: str) -> None:
    """Report what is wrong with this page's head. Never raises, never blocks.

    THE THREE LEDE FINDINGS ARE SEPARATE BECAUSE THEY WANT DIFFERENT FIXES: a
    page with no lede anywhere needs one WRITTEN, a page with its lede in the
    body needs it MOVED, and a page with both needs one DELETED. Collapsing
    them into a single 'lede problem' would hand the author a worklist they
    still have to triage by opening every file.

    The title/H1 check rides along because it is the same question -- does the
    top of this page agree with itself -- and because it caught three separate
    pages in one evening while being invisible from inside any of them.
    """
    summary = meta.get("summary")
    body = body_lede(markdown)
    lines = markdown.splitlines()
    start = _h1_index(lines)

    if summary and body:
        state.note(
            "page_head",
            src + ": lede in BOTH places. `summary:` is what renders; the "
            + "paragraph under the H1 now reads as ordinary prose directly "
            + "beneath it -- " + body[:_QUOTE],
        )
    elif body:
        state.note(
            "page_head",
            src + ": lede is still in the body. Move it into `summary:` and "
            + "delete the paragraph -- " + body[:_QUOTE],
        )
    elif not summary:
        state.note(
            "page_head",
            src + ": no lede anywhere, so the search result for this page "
            + "shows a heading and no teaser text at all.",
        )

    if start is None:
        state.note(
            "page_head",
            src + ": no `# ` heading. Nothing here has a top to check.",
        )
        return

    title = str(meta.get("title") or "").strip()
    h1 = lines[start][2:].strip()
    if title and h1 and h1 != title:
        state.note(
            "page_head",
            src + ': title and H1 disagree -- frontmatter says "' + title
            + '", the page says "' + h1 + '". The sidebar, the browser tab '
            + "and doc-index.json all carry the frontmatter one, so every "
            + "other site in the family links to this page under a name it "
            + "never shows a reader.",
        )
