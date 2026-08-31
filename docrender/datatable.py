"""Stage 01b -- render a TSV as a table. Beside the page, or by name from anywhere.

🔴 **EVERY ARGUMENT LIVES IN `docrender/datatable-dl.md`.** This docstring hit 27,523 B
against a 22,528 B read ceiling on 2026-08-31 while the by-name resolver's reasoning was
being written into it. **The contract and the warnings stay here; why a rule exists is one
file over.** ⚠️ If you are adding to this docstring, write the section in the sibling first.
Older history: the doc-render-engine Decision Log in ClickUp, blocks J4/J5/J7/J17/J20/J21.

FOUR MODULES, ONE FEATURE:

    sheet.py    reading and shaping a TSV. Rows, header, sections, options, order, kind.
    cells.py    one cell as prose. Markers, @refs, inline markdown, escaping.
    table.py    shaped rows -> markup. Column classes, roles, labels, money, the shell.
    this file   the frontmatter contract, the `!!! data` block, and WHERE THE FILE IS.


THE CONTRACT
============

    ---
    type: reference
    data:
      inventory_table:
        file: audio-inventory.tsv       beside the page, OR anywhere -- see FINDING
        caption: Audio inventory        # optional
    ---

    !!! data "inventory_table"            EMBED. Block level. Draws it here.
        sort: Count                       options, indented
        pin: ID
        hide: internal_notes
        caption: ...                      overrides the frontmatter one
        align: center                     LAYOUT -- `center` or `right`

    ...or [the inventory](@data:inventory_table)   MENTION. Inline. Links to it.

⭐ The body never names a FILE, only a SLOT. Swap the filenames in the frontmatter and the
body is byte-identical between Audio, LX and Video -- the whole reason this exists.


FINDING THE FILE (2026-08-31)
=============================
Three forms, tried in this order:

    file: audio-inventory.tsv                  1. beside the page      ← unchanged
    file: ../../production/x/dates.tsv         2. relative to the page ← unchanged
    file: dates-big-love-run-crew.tsv          3. anywhere in the tree ← new

✅ 1 AND 2 ARE ONE TEST. A declared path that names a real file wins before the index is
consulted, so every page written before today resolves exactly as it did -- and a page can
still PIN one file by path when two share a basename.

🔴 A DUPLICATE BASENAME IS REPORTED WITH EVERY PATH AND REFUSED. Not the shallowest, not
the first, not the nearest. Michael accepted unique naming as the price of this feature
(*"i just be sure to never name tsv that same"*), so the moment that assumption breaks he is
told rather than served a coin flip: on a call sheet the wrong file is the wrong dates.

🔴 A DECLARED **PATH** THAT MISSES DOES NOT FALL THROUGH TO THE SEARCH. It is reported and
refused -- quietly finding a same-named file elsewhere would hide the typo, not fix it.

⚠️ RESOLUTION RETURNS A **SITE PATH**, NEVER A FILENAME, and that is the 2026-08-04
download trap one step further out: a TSV found elsewhere downloads from ITS OWN folder, so
the href is built from where the file IS. A bare name would 404 every by-name download
while the table on the page rendered perfectly. **Do not go back to a bare filename, and do
not count separators** -- `util.relative_url` owns that arithmetic.


SLOTS, OPTIONS AND THE SHEET
============================
⚠️ Slot names belong to the TYPE (`objects/<type>.yml` → `data_slots`), and an undeclared
key is reported ONLY IF THAT TYPE DECLARES ANY -- an empty list means UNRESTRICTED (Michael,
2026-08-06, *"empty means anything goes"*). 🔴 `legal and` in `_declared` is what implements
that; deleting two words there puts five types' worth of pages into the report in one
commit. Argument: `objects/_base.yml` under DATA SLOTS, and D4 in the sidecar.

⚠️ ONE FRONTMATTER FORM: a slot is always a map with `file:`. The old list form is reported
by name, because an ignored key looks exactly like the feature never having worked.
🔴 `align:` IS LAYOUT AND IS **POPPED** BEFORE `sheet.apply_options` SEES IT -- that
validator reports unknown keys and correctly does not know this one. If `_align` is ever
changed to READ rather than REMOVE, every aligned table starts warning. 🚫 No `left`.

A header cell may declare its column's type and role (`thtr::id.key`, `credits::num`) --
`sheet.split_header`, which runs BEFORE `apply_options` so `sort: credits` still matches a
column headed `credits::num`. A cell may say anything inline prose can; `cells.py` owns that
and the escaping order that makes it safe.


FAILURE POSTURE
===============
Warn, render without the broken part, publish, report. Never raise, never fail a build over
a cosmetic typo.

🚫 NOT PROVIDED: filters, totals, renames, computed columns -- those edit the data, and the
sheet is the source of truth. `hide` is allowed because dropping a column from a VIEW does
not change what the sheet says.

⚠️ `pin:` emits markup the stylesheet does not yet honour, held until the older
frozen-column claim is verified on the deployed site.

⚠️ `PLACED` IS POPULATED BEFORE ANY CELL IS RENDERED and the order is the point -- a cell
may contain `[x](@data:other_slot)`, which resolves through the map below.
"""

from __future__ import annotations

import html
import posixpath
import re
from pathlib import Path

from . import prefixes, sheet, state, table
from .util import relative_url

_BLOCK = re.compile(r"^[ \t]*!!![ \t]+data[ \t]+\"(?P<slot>[^\"\n]+)\"[ \t]*$")
_OPTION = re.compile(r"^[ \t]+(?P<key>[A-Za-z_]+)[ \t]*:[ \t]*(?P<value>.*?)[ \t]*$")

#: The LAYOUT vocabulary. 🚫 No `left`: it is what a table already does, and an option that
#: produces the current rendering is a dead control indistinguishable from one that failed
#: to resolve. `assets/align.css` states that rule at length.
_ALIGNS = ("right", "center")

#: src_uri -> {slot: {"href": ..., "anchor": bool}}. Written at stage 01b, read by links.py
#: at stage 03 to resolve an inline @data: mention. The per-page event order guarantees 01b
#: has already run for THIS page.
#:
#: `href` is resolved RELATIVE TO THE PAGE, not a bare filename -- links.py hands it
#: straight to a reader, so a wrong value here is a 404 in two places rather than one.
PLACED: dict[str, dict[str, dict]] = {}

#: The by-name index: `basename.tsv` -> [site path, ...]. A LIST, never a single value,
#: because the duplicate case has to be reportable rather than silently resolved.
#:
#: ⚠️ `_INDEX_FOR` HOLDS THE `files` OBJECT, NOT ITS `id()`: `mkdocs serve` rebuilds
#: in-process, and holding the reference makes the identity test true rather than probable.
#: A grow-only module dict is the `qr.PENDING` trap. Sidecar D1.
_INDEX: dict[str, list[str]] = {}
_INDEX_FOR = None


def _index(files) -> dict[str, list[str]]:
    """Every `.tsv` in the docs tree, keyed by basename. Built once per build.

    ⚠️ BUILT FROM THE `files` PARAMETER RATHER THAN BY WALKING `docs_dir`. MkDocs' own
    collection is what the build actually knows about -- it honours `exclude_docs` and
    anything else that pruned a file, so a TSV MkDocs is not shipping cannot be resolved
    into a download that would 404.
    """
    global _INDEX, _INDEX_FOR
    if _INDEX_FOR is files:
        return _INDEX
    found: dict[str, list[str]] = {}
    for item in files:
        src = str(getattr(item, "src_uri", "") or "")
        if src.lower().endswith(".tsv"):
            found.setdefault(posixpath.basename(src), []).append(src)
    _INDEX, _INDEX_FOR = found, files
    return _INDEX


def _slots_for_type(type_name: str) -> list[str]:
    """The `data_slots` a type may carry, flattened along its `extends` chain.

    ⚠️ Walks state.TYPES itself rather than reading meta["_spec"], because objects._resolve
    merges only requires/optional/renders. Named follow-up; until then this is the one place
    the chain is walked twice, called out so it does not become a quiet second copy.

    ⚠️ AN EMPTY RETURN IS MEANINGFUL AND IS NOT AN ERROR. It means the type declared no
    vocabulary, which the caller reads as UNRESTRICTED rather than as "no tables allowed".
    """
    slots: list[str] = []
    decl = state.TYPES.get(type_name)
    seen: set = set()
    chain = []
    while decl and decl.get("type") not in seen:
        seen.add(decl.get("type"))
        chain.append(decl)
        parent = decl.get("extends")
        decl = state.TYPES.get(parent) if parent else None
    for decl in reversed(chain):
        for value in decl.get("data_slots") or []:
            if str(value) not in slots:
                slots.append(str(value))
    return slots


def _declared(meta: dict, src: str, note) -> dict[str, dict]:
    """Validate `data:` and return {slot: {"file":..., "caption":...}}."""
    raw = meta.get("data")
    if not raw:
        return {}

    if isinstance(raw, (list, tuple, str)):
        note(
            "duplicate_key",
            src + ": `data:` is a MAP of named slots now, not a list of filenames. The "
            + "list form is IGNORED, which looks exactly like the tables never having "
            + "worked. Rewrite as `data:` / `  <slot>:` / `    file: <name>.tsv`.",
        )
        return {}

    legal = _slots_for_type(str(meta.get("_type") or meta.get("type") or "page"))
    out: dict[str, dict] = {}

    for slot, value in raw.items():
        slot = str(slot)
        # 🔴 `legal and` IS LOAD-BEARING. DO NOT TIDY IT AWAY. An empty list is falsy, so a
        # type declaring no `data_slots` accepts ANY slot name -- Michael's 2026-08-06
        # ruling, "empty means anything goes." Deleting two words here is a
        # one-character-looking cleanup that would put every page on `page`, `procedure`,
        # `standard`, `venue` and `space` into the build report in a single commit,
        # including uritp-docs' automatic-revision-log, which runs slot `revlog`.
        # Argument: `objects/_base.yml` under DATA SLOTS, and sidecar D4.
        if legal and slot not in legal:
            note(
                "missing_required",
                src + ": data slot '" + slot + "' is not declared on type '"
                + str(meta.get("_type")) + "'. Declared: " + (", ".join(legal) or "none")
                + ". Add it to the type, or use the name the type already has -- a slot "
                + "spelled two ways across two pages is prose that stopped being "
                + "portable.",
            )
            continue
        if not isinstance(value, dict) or not value.get("file"):
            note(
                "missing_required",
                src + ": data slot '" + slot + "' needs a `file:` key. A slot is always "
                + "a map (`file:` required, `caption:` optional); bare "
                + "`slot: name.tsv` is not a second legal form.",
            )
            continue
        out[slot] = {
            "file": str(value.get("file")),
            "caption": str(value.get("caption") or ""),
        }
    return out


def _locate(declared_file: str, folder: str, docs_dir: Path, files, src, slot) -> str:
    """Where the TSV actually is, as a SITE path. `""` means it was not resolved.

    See FINDING THE FILE in the docstring for the three forms and the order, and sidecar
    D1/D2 for why each branch is shaped the way it is.

    🔴 `docs_dir` IS A PARAMETER AND NOT A MODULE GLOBAL, because the first draft of this
    function reached for a `state.DOCS_DIR` **that does not exist** and would have raised on
    the first page carrying a `data:` slot. The docs directory arrives per build through the
    hook signature; threading it is both the fix and the honest shape. Sidecar D2.
    """
    declared_file = declared_file.strip()
    if not declared_file:
        return ""

    # 1 + 2: relative to the page. `posixpath.normpath` collapses `..` the same way `Path`
    # does, so the site path and the on-disk read cannot drift apart.
    joined = posixpath.join(folder, declared_file) if folder else declared_file
    site_path = posixpath.normpath(joined).lstrip("/")
    if not site_path.startswith("..") and (docs_dir / site_path).is_file():
        return site_path

    # 3: by name, anywhere -- BARE FILENAMES ONLY. A declared path that missed is an
    # authoring mistake with one specific answer; searching would hide it.
    if "/" in declared_file:
        state.note(
            "missing_required",
            src + ": data slot '" + slot + "' declares path '" + declared_file
            + "' which does not resolve to a file. A path is taken literally; drop to "
            + "just the filename to search the tree by name instead.",
        )
        return ""

    hits = _index(files).get(declared_file) or []
    if len(hits) == 1:
        return hits[0]
    if not hits:
        state.note(
            "missing_required",
            src + ": data slot '" + slot + "' declares file '" + declared_file
            + "' which is not beside this page and is nowhere in the docs tree.",
        )
        return ""
    state.note(
        "missing_required",
        src + ": data slot '" + slot + "' names '" + declared_file + "', and "
        + str(len(hits)) + " files share that name: " + ", ".join(sorted(hits))
        + ". NOT rendered -- this engine will not choose between them. Rename one, or "
        + "declare the path you mean.",
    )
    return ""


def _align(options: dict, src: str, slot: str) -> str:
    """POP `align` out of the option dict and validate it. `""` means no alignment.

    🔴 THE POP IS THE POINT, NOT A CONVENIENCE -- see the docstring. ⚠️ An unrecognised
    value is reported and dropped, never guessed: a table silently sitting in the wrong
    place reads as a stylesheet bug and is an authoring one.
    """
    raw = (options.pop("align", "") or "").strip().lower()
    if not raw:
        return ""
    if raw not in _ALIGNS:
        state.note(
            "notes",
            src + ': !!! data "' + slot + '" carries `align: ' + raw + "`, which is not "
            + "an alignment this engine knows. Legal: " + ", ".join(_ALIGNS)
            + ". Ignored, so the table sits where it would have anyway. There is "
            + "deliberately no `left` -- that is already the default.",
        )
        return ""
    return raw


def _resolve_mention(slot: str, page, label: str):
    """Resolve an inline `[label](@data:slot)`. Returns markdown, or None to decline.

    An embedded slot resolves to its anchor on this page; a declared-but-unembedded slot
    resolves to the TSV download, which is the honest answer -- there is no table on the
    page to jump to. An unknown slot returns None and links.py renders the existing
    broken-reference marker, never a plausible-looking guess.
    """
    entry = (PLACED.get(page.file.src_uri) or {}).get(slot)
    if not entry:
        return None
    target = "#data-" + slot if entry.get("anchor") else entry["href"]
    return "[" + label + "](" + target + ")"


prefixes.claim("data", __name__, _resolve_mention)


def _collect_blocks(markdown: str):
    """Find every `!!! data` block and its indented options.

    Returns (lines, [(start, end, slot, options)]) with end EXCLUSIVE. Line-based rather
    than one regex because the options are an indented run of arbitrary length, and a regex
    spanning them is a regex nobody can read six months from now. Fenced code is skipped
    for the same reason util.sub_outside_code exists: a page DOCUMENTING this syntax has
    not placed a table.
    """
    lines = markdown.split("\n")
    found = []
    i = 0
    in_fence = False
    while i < len(lines):
        stripped = lines[i].lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            i += 1
            continue
        match = None if in_fence else _BLOCK.match(lines[i])
        if not match:
            i += 1
            continue
        start = i
        options: dict[str, str] = {}
        i += 1
        while i < len(lines):
            option = _OPTION.match(lines[i])
            if not option:
                break
            options[option.group("key").lower()] = option.group("value")
            i += 1
        found.append((start, i, match.group("slot").strip(), options))
    return lines, found


def on_page_markdown(markdown, page, config, files):
    src = page.file.src_uri
    meta = state.BY_SRC.get(src, {})
    declared = _declared(meta, src, state.note)

    lines, blocks = _collect_blocks(markdown)
    if not declared and not blocks:
        return markdown

    docs_dir = Path(config["docs_dir"])
    folder = posixpath.dirname(src)
    replacements: list[tuple[int, int, str]] = []

    # ⚠️ RESOLVED ONCE PER SLOT, NOT ONCE PER USE. A slot both mentioned inline and embedded
    # would otherwise report a missing file twice.
    located = {
        slot: _locate(entry["file"], folder, docs_dir, files, src, slot)
        for slot, entry in declared.items()
    }

    def href_for(site_path: str) -> str:
        """The TSV's URL as seen FROM THIS PAGE. Never a bare filename, and never the
        PAGE's folder for a file that lives somewhere else -- see the docstring."""
        return relative_url(site_path, page.file.url)

    # ⚠️ PLACED IS POPULATED BEFORE ANY CELL IS RENDERED. A cell may itself contain
    # `[x](@data:other_slot)`, and cells.render resolves that through links.py, which reads
    # this map. Filling it afterwards would make a same-page reference resolve as broken on
    # the first table and fine on the second -- an ordering bug that reads as a typo.
    embedded = {b[2] for b in blocks}
    placed: dict[str, dict] = {
        slot: {"href": href_for(site_path), "anchor": slot in embedded}
        for slot, site_path in located.items() if site_path
    }
    PLACED[src] = placed

    for start, end, slot, options in blocks:
        entry = declared.get(slot)
        if not entry:
            state.note(
                "dead_links",
                src + ': !!! data "' + slot + '" names a slot that is not in this '
                + "page's `data:` frontmatter. Declared here: "
                + (", ".join(sorted(declared)) or "nothing") + ".",
            )
            replacements.append((
                start, end,
                '<p class="docrender-dead">Undeclared data slot: '
                + html.escape(slot) + "</p>",
            ))
            continue

        # ⚠️ `_locate` HAS ALREADY REPORTED WHY. Three different failures land here -- not
        # beside the page, nowhere in the tree, or an ambiguous name -- and each has its own
        # report line naming the paths involved. The on-page marker stays generic because it
        # is read by somebody who then goes to the report.
        site_path = located.get(slot) or ""
        if not site_path:
            replacements.append((
                start, end,
                '<p class="docrender-dead">Unresolved data file: '
                + html.escape(entry["file"]) + "</p>",
            ))
            continue

        rows = sheet.trim_columns(sheet.read_rows(docs_dir / site_path))
        if not rows:
            state.note(
                "notes",
                src + ": data file " + site_path + " is empty or unreadable.",
            )
            replacements.append((start, end, ""))
            if slot in placed:
                placed[slot]["anchor"] = False
            continue

        # 🔴 LAYOUT FIRST, AND IT REMOVES THE KEY. See `_align`.
        align = _align(options, src, slot)

        # BEFORE apply_options, so `sort: credits` still matches `credits::num`.
        rows, specs = sheet.split_header(rows, slot, src, state.note)
        rows, pinned, override = sheet.apply_options(
            rows, options, slot, src, state.note
        )
        caption = override if override is not None else entry["caption"]
        replacements.append((
            start, end,
            table.draw(rows, specs, href_for(site_path),
                       posixpath.basename(site_path), slot,
                       caption, pinned, page, align),
        ))

    for slot in declared:
        if slot in embedded:
            continue
        # Declared and never drawn. NOT quietly appended at the page foot: a table silently
        # landing at the bottom of a long page is the failure nobody notices for a month.
        state.note(
            "missing_required",
            src + ": data slot '" + slot + "' is declared and never placed. Add "
            + '!!! data "' + slot + '" where the table belongs, or drop the slot. An '
            + "inline [mention](@data:" + slot + ") still resolves to the file download, "
            + "so this warns rather than breaking the page.",
        )

    for start, end, replacement in reversed(replacements):
        lines[start:end] = [replacement]
    return "\n".join(lines)
