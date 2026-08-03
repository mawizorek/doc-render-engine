"""Small shared helpers. No MkDocs imports here, on purpose.

Keeping this file framework-free means the frontmatter contract can be parsed
and checked by anything -- a linter, a ClickUp importer, a print pipeline --
without dragging a static site generator along. Same argument as the pure
content repo, one level down.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

_FRONTMATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?", re.S)
_TOP_KEY = re.compile(r"(?m)^([A-Za-z_][A-Za-z0-9_-]*)[ \t]*:")

# Fenced blocks (``` or ~~~, any indent, any info string) and inline code spans
# (one or more backticks). Ordered longest-first so a fence is never mistaken
# for an inline span that happens to start with three backticks.
_PROTECTED = re.compile(
    r"(?ms)^[ \t]*(?P<f>`{3,}|~{3,}).*?(?:^[ \t]*(?P=f)[ \t]*$|\Z)"
    r"|(?P<t>`+)(?:.|\n)*?(?P=t)"
)


def sub_outside_code(pattern: re.Pattern, repl, markdown: str) -> str:
    """Run a substitution everywhere EXCEPT inside code.

    CODE IS NOT CONTENT. Any transform that rewrites markdown text will, given
    a documentation site, eventually be pointed at a page that DOCUMENTS the
    syntax it rewrites -- and then it edits the example. That is not a corner
    case here, it is the authoring guide, and it happened for real on the first
    live build: the page teaching `[Main Stage](@main-stage)` shipped with the
    resolved URL inside its own code fence, teaching the opposite of the rule.

    Lives in util rather than in one hook because the bug is available to every
    hook that does this, and the second one to want it should not have to know
    the first one solved it.
    """
    out = []
    cursor = 0
    for guard in _PROTECTED.finditer(markdown):
        out.append(pattern.sub(repl, markdown[cursor:guard.start()]))
        out.append(guard.group(0))
        cursor = guard.end()
    out.append(pattern.sub(repl, markdown[cursor:]))
    return "".join(out)


def duplicate_keys(text: str) -> list[str]:
    """Top-level frontmatter keys that appear more than once.

    YAML resolves a duplicate silently by keeping the LAST value, which is a
    genuinely nasty failure in frontmatter: writing

        status: public
        status: routed

    leaves the page with `status: routed`, which is not a real state, so it is
    not built -- and nothing anywhere says why. It reads as "my page vanished."

    Detected with a regex rather than a strict YAML loader on purpose: this has
    to report ALL the offenders in one pass and keep parsing, where a strict
    loader raises on the first one and yields no metadata at all.
    """
    match = _FRONTMATTER.match(text)
    if not match:
        return []
    seen: dict[str, int] = {}
    for key in _TOP_KEY.findall(match.group(1)):
        seen[key] = seen.get(key, 0) + 1
    return sorted(k for k, n in seen.items() if n > 1)


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Return (metadata, body). Absent frontmatter is not an error here.

    Malformed YAML is not an exception either: it yields empty metadata, and
    the missing `status` that results is what gets reported. One bad page
    should produce a named complaint about that page, never a traceback that
    takes the whole site down with it.
    """
    match = _FRONTMATTER.match(text)
    if not match:
        return {}, text
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        meta = None
    if not isinstance(meta, dict):
        meta = {}
    return meta, text[match.end():]


def read_frontmatter(path: str | Path) -> dict:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return {}
    meta, _ = split_frontmatter(text)
    return meta


def read_frontmatter_checked(path: str | Path) -> tuple[dict, list[str]]:
    """Frontmatter plus any duplicated keys, in one read."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return {}, []
    meta, _ = split_frontmatter(text)
    return meta, duplicate_keys(text)


def load_yaml(path: str | Path) -> dict:
    p = Path(path)
    if not p.is_file():
        return {}
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def load_tsv(path: str | Path) -> list[dict]:
    """Read a tab-separated table with a header row.

    TSV rather than YAML for the theme and marker tables, inherited from v1 and
    kept: these are grids, they read like grids in any editor, and a grid
    resists growing the free-text area that turns a data file into a document.
    """
    p = Path(path)
    if not p.is_file():
        return []
    lines = [
        ln for ln in p.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.lstrip().startswith("#")
    ]
    if not lines:
        return []
    header = [h.strip() for h in lines[0].split("\t")]
    rows = []
    for line in lines[1:]:
        cells = line.split("\t")
        rows.append({
            header[i]: (cells[i].strip() if i < len(cells) else "")
            for i in range(len(header))
        })
    return rows


def slug_title(name: str) -> str:
    """'main-stage' -> 'Main Stage'. Last-resort fallback only."""
    return " ".join(w.capitalize() for w in re.split(r"[-_]+", name) if w)
