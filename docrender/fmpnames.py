"""The `@fmp:` namespace -- a FileMaker object name written ONCE, rendered everywhere.

Spec: specs/fmp-names.md (decision-complete 2026-10-11, DL J33). WHY lives there;
this docstring holds what somebody EDITING this file has to know.

    [](@fmp:t.yearconfig)         renders the row's current name
    [the money table](@fmp:t.yearconfig)   keeps your words, checks them
    [](@fmp:t.alloc#grain)        anchor passes through when the row has a page

THE CATALOG
===========

One `NAMES.tsv` per app folder. A page uses the NEAREST one above it (R2), so two
apps on one site can each say `t.codes` and mean their own table. Columns read:

    key        REQUIRED. `<kind letter>.<slug>`, never changes (R4)
    current    the name the file has TODAY
    proposed   the name it is going to have
    status     keep | rename | retire | new | open
    kind       OPTIONAL. Inferred from the key's letter when absent
    page       OPTIONAL. A page id; the name becomes a link to it

Every other column (`grain`, notes) is the author's and is never read here.

WHICH NAME RENDERS (R5): `current`, always, until a DDR drop proves the rename and a
human moves `proposed` into `current`. The one exception is a `new` row, which has
no current name by definition, so it shows `proposed`.

TWO HALVES, TWO EVENTS, AND THE ORDER IS THE POINT
==================================================

  RESOLVE  the `@fmp:` claim, called BY links.py at stage 03. Claimed at import.
  DRIFT    `on_page_markdown`, which has to see the page BEFORE stage 03 rewrites
           every reference into a name -- after 03 the drift scan would report this
           module's own output. That is why the shim is registered at 02b, ahead of
           03_links, and not beside 03c where the other namespace owners sit.

DRIFT FINDINGS GO TO `notes`, PREFIXED `names:`, NOT TO A NEW BUCKET. The spec said
"a `names` report line"; a new bucket is two edits in two files (state.reset and
report._LABELS) and a bucket missing from _LABELS prints nothing at all. v1 rides
`notes`. If the volume earns its own section, that is the two edits, in one commit.

NOTHING HERE CAN FAIL A BUILD. A bad catalog row is reported and skipped; a dead key
declines, and links.py renders the standard broken-reference span.
"""

from __future__ import annotations

import html
import posixpath
import re

from . import markers, prefixes, state
from .util import load_tsv, relative_url

CATALOG = "NAMES.tsv"

#: R4. Letter, dot, slug; fields carry a second dotted segment. Lowercase only, so a
#: key can never differ from another by case alone.
_KEY = re.compile(r"^[a-z]\.[a-z0-9_]+(?:\.[a-z0-9_]+)?$")

#: The key's first letter, when the row has no `kind` cell.
_KINDS = {
    "t": "table", "f": "field", "c": "calc", "r": "rel",
    "s": "script", "l": "layout", "v": "vl", "g": "global",
}

#: Kinds that live on a LAYOUT rather than in the schema. Everything else paints in
#: the schema family. Read off theme/markers.tsv's own split, not invented here.
_LAYOUT_KINDS = {"layout", "button", "portal"}

_STATUSES = {"keep", "rename", "retire", "new", "open"}

#: folder ("" = site root) -> {key: row}. Built in on_files.
_CATALOGS: dict[str, dict[str, dict]] = {}

#: folder -> {spelling: key}, every non-empty `current`. What the drift scan hunts.
_SPELLINGS: dict[str, dict[str, str]] = {}

#: (src_uri, key) pairs already reported as `open`, so one page says it once.
_OPEN_SEEN: set = set()

#: An `@fmp:` reference with its label, so the drift scan can blank it out first.
_REF = re.compile(r"\[[^\]\n]*\]\(@fmp:[^)\s]*\)")


def _folder(src_uri: str) -> str:
    head = posixpath.dirname(str(src_uri))
    return "" if head in (".", "/") else head


def _catalog_for(src_uri: str):
    """(folder, rows) for the nearest catalog at or above this page, or ("", None)."""
    folder = _folder(src_uri)
    while True:
        if folder in _CATALOGS:
            return folder, _CATALOGS[folder]
        if not folder:
            return "", None
        folder = _folder(folder)


def _kind(row: dict) -> str:
    own = (row.get("kind") or "").strip().lower()
    return own or _KINDS.get(row["key"][:1], "")


def _family(kind: str) -> str:
    return "layout" if kind in _LAYOUT_KINDS else "schema"


def _shape(family: str) -> str:
    """The family's shape, read off the resolved marker table. Plain if unknown."""
    for row in markers.table().values():
        if row.get("class") == family:
            return row.get("shape") or "plain"
    return "plain"


def _load(src: str, path: str) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for raw in load_tsv(path):
        key = (raw.get("key") or "").strip()
        if not key:
            continue
        where = src + ": key `" + key + "`"
        if not _KEY.match(key):
            state.note(
                "notes",
                where + " is not `<letter>.<slug>` (lowercase, e.g. `t.yearconfig`, "
                + "`f.codes.default_code`). Skipped, so every `@fmp:" + key + "` is a "
                + "broken reference until it is fixed.",
            )
            continue
        if key in rows:
            state.note(
                "notes",
                where + " appears twice. The first row wins; a key is an identity "
                + "and cannot mean two objects.",
            )
            continue
        status = (raw.get("status") or "").strip().lower()
        if status and status not in _STATUSES:
            state.note(
                "notes",
                where + " has status `" + status + "`. Known: "
                + ", ".join(sorted(_STATUSES)) + ". Rendered as if `keep`.",
            )
            status = "keep"
        row = dict(raw)
        row["key"] = key
        row["status"] = status or "keep"
        if not _kind(row):
            state.note(
                "notes",
                where + " has no `kind` and its letter `" + key[:1] + "` maps to "
                + "none. Painted as schema. Known letters: "
                + ", ".join(k + "=" + v for k, v in sorted(_KINDS.items())) + ".",
            )
        if not (row.get("current") or row.get("proposed")):
            state.note(
                "notes",
                where + " has neither `current` nor `proposed`, so there is no name "
                + "to render. References to it show the key itself.",
            )
        rows[key] = row
    return rows


def on_files(files, config):
    """Find every catalog in the file set and load it. Once per build.

    Built from `files`, never by walking docs_dir: MkDocs' own collection honours
    exclude_docs, and datatable.py records why that matters.
    """
    _CATALOGS.clear()
    _SPELLINGS.clear()
    _OPEN_SEEN.clear()
    for f in files:
        src = str(f.src_uri)
        if posixpath.basename(src) != CATALOG:
            continue
        rows = _load(src, f.abs_src_path)
        folder = _folder(src)
        _CATALOGS[folder] = rows
        _SPELLINGS[folder] = {
            r["current"]: k for k, r in rows.items() if (r.get("current") or "").strip()
        }
        state.note(
            "notes",
            "names: " + src + " loaded, " + str(len(rows)) + " keys.",
        )
    return files


def _resolve(rest, page, label, anchor="", opts=""):
    """Resolve `@fmp:<key>`. Returns markdown/HTML, or None to decline."""
    src = page.file.src_uri
    folder, rows = _catalog_for(src)
    if rows is None:
        state.note(
            "dead_links",
            src + ": `@fmp:" + rest + "` but no " + CATALOG + " exists at or above "
            + "this page's folder.",
        )
        return None
    row = rows.get(rest)
    if row is None:
        return None

    status = row["status"]
    name = (row.get("current") or "").strip()
    if status == "new" or not name:
        name = (row.get("proposed") or "").strip() or rest
    where = src + ": '@fmp:" + rest + "'"

    if label and label not in (name, (row.get("proposed") or "").strip()):
        state.note(
            "notes",
            "names: " + where + " is labelled '" + label + "', which is neither the "
            + "current nor the proposed name. Kept as written. Leave the label empty "
            + "to have the catalog supply it.",
        )
    if status == "open" and (src, rest) not in _OPEN_SEEN:
        _OPEN_SEEN.add((src, rest))
        state.note("notes", "names: " + where + " cites a row whose fate is still `open`.")
    if status == "retire":
        state.note("notes", "names: " + where + " cites a row marked `retire`.")

    shown = label or name
    family = _family(_kind(row))
    shape = "strike" if status == "retire" else ("soft" if status == "new" else _shape(family))

    state.note(
        "markers",
        family + " \u00b7 fmp \u00b7 " + src + " \u00b7 " + shown + " \u2192 " + folder
        + "/" + CATALOG + "#" + rest,
    )

    target_id = (row.get("page") or "").strip()
    hit = state.PAGES.get(target_id) if target_id else None
    if target_id and not hit:
        state.note(
            "dead_links",
            where + " names page `" + target_id + "`, which was not built. "
            + "Rendered as a name without a link.",
        )

    authored = [c for c in re.findall(r"\.([A-Za-z][\w-]*)", opts or "")]

    if hit:
        href = relative_url(str(hit.get("url", "")), page.file.url) + (anchor or "")
        css = [markers.LINK_CLASS, "dr-mark--cls-" + family]
        if shape == "box":
            css.append("dr-mark--box")
        css += [c for c in authored if c not in css]
        return "[" + shown + "](" + href + "){ ." + " .".join(css) + " }"

    if anchor:
        state.note(
            "notes",
            "names: " + where + anchor + " carries an anchor but the row has no "
            + "built `page`, so there is nowhere for it to point. Dropped.",
        )
    css = ["dr-mark", "dr-mark--" + shape, "dr-mark--cls-" + family]
    css += [c for c in authored if c not in css]
    return (
        '<span class="' + " ".join(css) + '" data-mark="fmp" data-key="'
        + html.escape(rest, quote=True) + '">' + html.escape(shown) + "</span>"
    )


# CLAIMED AT IMPORT -- the prefixes.py contract. hooks/02b_fmpnames.py is what
# imports this module; drop it from mkdocs.yml and every `@fmp:` renders broken.
prefixes.claim("fmp", __name__, _resolve, anchors=True, opts=True)


def drift(markdown: str, src: str) -> list[tuple[str, str, int]]:
    """(spelling, key, count) for every catalog name typed by hand on this page.

    Pure, so it can be tested without MkDocs. Fenced blocks are skipped (they hold
    scripts and wireframes, where a literal name is the point); inline code spans
    and prose are scanned, because that is where the spellings that rot live.
    """
    folder, rows = _catalog_for(src)
    if rows is None:
        return []
    spellings = _SPELLINGS.get(folder) or {}
    if not spellings:
        return []
    text = _REF.sub(" ", markdown)
    text = re.sub(r"(?ms)^[ \t]*(`{3,}|~{3,}).*?^[ \t]*\1[ \t]*$", " ", text)
    found = []
    for spelling in sorted(spellings, key=len, reverse=True):
        pat = re.compile(r"(?<![\w])" + re.escape(spelling) + r"(?![\w])")
        n = len(pat.findall(text))
        if n:
            found.append((spelling, spellings[spelling], n))
            text = pat.sub(" ", text)
    return found


def on_page_markdown(markdown, page, config, files):
    src = page.file.src_uri
    if posixpath.basename(src) == CATALOG:
        return markdown
    for spelling, key, n in drift(markdown, src):
        state.note(
            "notes",
            "names: " + src + " spells `" + spelling + "` by hand (" + str(n)
            + "x). Cite `[](@fmp:" + key + ")` so a rename is one cell.",
        )
    return markdown
