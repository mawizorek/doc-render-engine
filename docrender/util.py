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

    TSV rather than YAML for the theme tables, inherited from v1 and kept: a
    palette is a grid, it reads like a grid in any editor, and a grid resists
    growing the free-text area that turns a data file into a document.
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
