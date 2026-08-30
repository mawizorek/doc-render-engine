"""Small shared helpers. No MkDocs imports here, on purpose.

Keeping this file framework-free means the frontmatter contract can be parsed
and checked by anything -- a linter, a ClickUp importer, a print pipeline --
without dragging a static site generator along. Same argument as the pure
content repo, one level down.

That promise is why `relative_url` below is hand-written instead of importing
`mkdocs.utils.get_relative_url`, which does the same job. The algorithm is
deliberately the same as MkDocs', because agreeing with the framework is the
point; the independence is about the import, not the behaviour.

🔴 THIS FILE WAS CLOBBERED ONCE (2026-08-03) AND THE LESSON IS IN THE HEADER
SO IT DOES NOT HAPPEN TWICE. `relative_url` was added here, then deleted by a
later commit that REWROTE THE WHOLE FILE to add `duplicate_keys` -- authored
from a stale read that predated it. Every build then died on
`ImportError: cannot import name 'relative_url'`, because two hooks import it.

This is a shared-helper module: additions belong here, so it is exactly the
file most likely to have changed since you last read it. **Re-read it
immediately before writing, and prefer a surgical edit to a full replacement.**
A wholesale rewrite of a shared file cannot add without also deciding, silently,
to delete everything it does not happen to contain.
"""

from __future__ import annotations

import posixpath
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

#: A trailing `key=value` pair on a `!!!` directive line. Lifted verbatim from
#: `qr.py`'s `_OPT`, which has been parsing this shape in production since
#: 2026-08-21 -- the pattern is the proven half and is not being redesigned here.
_DIRECTIVE_OPT = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=(\S+)")

#: The LAYOUT vocabulary, shared by every block directive that can be aligned.
#: 🚫 NO `left`: it is what a block already does, and a control that produces the
#: current rendering is indistinguishable from one that failed to resolve.
#: `assets/align.css` states that rule at length and this is the enforcement.
ALIGNS = ("right", "center")


def _url_parts(url: str) -> list[str]:
    """Split a site-relative URL into normalized path segments.

    Handles every shape MkDocs hands us for the ROOT index page -- `.`, `./`,
    `''` -- as the empty list, which is the whole reason this function exists.
    """
    norm = posixpath.normpath("/" + str(url).strip("/"))
    return [part for part in norm.split("/") if part and part != "."]


def relative_url(target: str, from_page: str) -> str:
    """Resolve a site-root-relative page URL against the page linking to it.

    🔴 THIS REPLACES `"../" * page.file.url.count("/")`, WHICH WAS WRONG ON
    EXACTLY ONE PAGE PER SITE -- the landing page, i.e. the most-linked-from
    page there is.

    MkDocs reports the root index page's url as `./`, which counts ONE slash
    while sitting at depth ZERO. Every `@id` link on a landing page therefore
    got one extra `../` and resolved one directory ABOVE the site root:
    `mawizorek.github.io/01-utility/...` instead of
    `mawizorek.github.io/uritp-docs/01-utility/...`. A hard 404, live, on the
    first page anybody sees.

    Every DEEPER page was correct, which is the nasty part: `production/x/`
    counts to 2 and genuinely needs 2, so the bug was invisible from any page
    except the one where it mattered. Counting separators is not measuring
    depth; it only looked like it because most inputs are well behaved.

    Lives in util rather than in one hook because two call sites had already
    copied the broken math (`links.py`, `router.py`) before anybody noticed,
    and the router's copy was the worse one -- it seals the destination inside
    an encrypted payload, so a wrong URL is not visible until a reader types a
    correct code and lands nowhere.

    ⚠️ AND FOR TWO DAYS THAT PARAGRAPH WAS AHEAD OF THE CODE. Naming two call
    sites reads as having converted two; only `links.py` was. `router.py` kept
    its own copy until 2026-08-03, so the copy described here as the more
    dangerous one is precisely the one that stayed broken -- protected from
    discovery by the same encryption that made it dangerous. When a docstring
    explains why a helper was extracted, say which callers actually call it.

    A trailing component containing a dot is treated as a filename and dropped
    from the source path, so this stays correct under `directory_urls: false`.
    """
    head, _, tail = str(from_page).rpartition("/")
    if "." in tail:
        from_page = head

    base = _url_parts(from_page)
    dest = _url_parts(target)

    common = 0
    for here, there in zip(base, dest):
        if here != there:
            break
        common += 1

    parts = [".."] * (len(base) - common) + dest[common:]
    rel = "/".join(parts) or "."
    return rel + "/" if str(target).endswith("/") else rel


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

    Rebuilding from slices keeps protected regions byte-identical instead of
    round-tripping them through a replacement.
    """
    out = []
    cursor = 0
    for guard in _PROTECTED.finditer(markdown):
        out.append(pattern.sub(repl, markdown[cursor:guard.start()]))
        out.append(guard.group(0))
        cursor = guard.end()
    out.append(pattern.sub(repl, markdown[cursor:]))
    return "".join(out)


def directive_options(tail: str, legal=()) -> tuple[dict, list[str]]:
    """Parse the trailing `key=value` options on a `!!!` directive line.

    Returns `(options, problems)`. `align` is validated against `ALIGNS` and
    lands as a STRING; every other legal key coerces to a bool the way `qr.py`
    has always done. Anything unrecognised is DROPPED and described in
    `problems` -- one human sentence per fault, ready to hand to `state.note`.

    🔴 IT REPORTS RATHER THAN LOGGING, AND THAT IS THE WHOLE INTERFACE DECISION.
    Importing `state` here would put a docrender module inside the one file whose
    header promises it stays framework-free and independently usable. So the
    caller owns the bucket, and this stays a pure function a linter can run.

    ⚠️ AN UNKNOWN KEY IS NEVER SILENTLY IGNORED. A mistyped `algin=center` that
    vanished would leave an author staring at an unmoved block with no signal --
    and this function exists BECAUSE the silent version of that failure shipped:
    `!!! form "x" align=center` did not match `forms._FORM` at all, so the whole
    directive was left as literal text with nothing in the report, because
    nothing had matched to report on.

    ⚠️ `false` IS RECORDED, NOT DROPPED, so a caller can tell "absent" from
    "present and false" -- the distinction `qr._shape` turns on and `forms._entry`
    turns on twice. Storing only the true keys would collapse two different facts.

    🚩 `qr.py` STILL HAS ITS OWN COPY OF THIS LOGIC and should call this instead.
    It is not converted in the same pass because that file is 29,915 B, at the
    `create_or_update_file` write cap, so it cannot be rewritten safely --
    recorded here rather than left as an invisible second claimant. When `qr.py`
    is split, delete its `_OPT`, `_ALIGN_KEY` and `_ALIGNS` and pass
    `legal=("display", "print")`.
    """
    text = (tail or "").strip()
    if not text:
        return {}, []

    found: dict = {}
    problems: list[str] = []
    for key, value in _DIRECTIVE_OPT.findall(text):
        if key == "align":
            choice = value.lower()
            if choice not in ALIGNS:
                problems.append(
                    "`align=" + value + "` is not an alignment this engine "
                    "knows. Legal: " + ", ".join(ALIGNS) + ". Ignored, so the "
                    "block sits where it would have anyway. There is "
                    "deliberately no `left` -- that is already the default."
                )
                continue
            found[key] = choice
            continue
        if key not in legal:
            problems.append(
                "unknown option `" + key + "=" + value + "`. Legal here: "
                + ", ".join(tuple(legal) + ("align",)) + ". Ignored."
            )
            continue
        found[key] = value.lower() in ("true", "yes", "1")

    leftover = _DIRECTIVE_OPT.sub("", text).strip()
    if leftover:
        problems.append(
            "trailing text that is not a `key=value` option: '" + leftover
            + "'. Ignored."
        )
    return found, problems


def duplicate_keys(text: str) -> list[str]:
    """Top-level frontmatter keys that appear more than once.

    YAML resolves a duplicate silently by keeping the LAST value, which is a
    genuinely nasty failure in frontmatter: writing

        status: public
        status: routed

    leaves the page on `status: routed`, which is not a real state, so it is
    not built -- and nothing anywhere says why. It reads as "my page vanished",
    and the report's own complaint (`status is 'routed'`) sends the author
    hunting for a typo they cannot see.

    THE SAME TRAP CATCHES ANY REPEATED KEY, which is why routers take a LIST
    rather than a repeated line: `router:` twice keeps the second table and
    silently discards the first. See docrender/router.py.

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
