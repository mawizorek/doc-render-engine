"""Stage 01b -- render a TSV sitting next to a page as a table.

Decision history: doc-render-engine (repo) Decision Log in ClickUp, blocks J4/J5/J7/J17
and J20/J21. **The argument lives THERE; this file states the contract.** That split is
not a style preference -- this docstring has three times grown until the module failed
the size gate it enforces on everybody else.

FOUR MODULES, ONE FEATURE:

    sheet.py    reading and shaping a TSV. Rows, header, sections, options, order, kind.
    cells.py    one cell as prose. Markers, @refs, inline markdown, escaping.
    table.py    shaped rows -> markup. Column classes, roles, labels, money, the shell.
    this file   the frontmatter contract and the `!!! data` block.


WHY DATA FILES ARE ALLOWED IN THE CONTENT TREE
==============================================

"Markdown and nothing else" is a rule about MACHINERY -- no stylesheet, no config, no nav
manifest, no build script -- so the Download ZIP hands somebody the documents and nothing
they must be told to ignore. A table of dimmer circuits is not machinery, it IS the
documentation. TSVs stay TSV on disk: spreadsheet-editable, git-diffable, greppable.


THE CONTRACT
============

    ---
    type: reference
    data:
      inventory_table:
        file: audio-inventory.tsv
        caption: Audio inventory          # optional
    ---

    !!! data "inventory_table"            EMBED. Block level. Draws it here.
        sort: Count                       options, indented
        pin: ID
        hide: internal_notes
        caption: ...                      overrides the frontmatter one

    ...or [the inventory](@data:inventory_table)   MENTION. Inline. Links to it.

⭐ The body never names a FILE, only a SLOT. Swap the filenames in the frontmatter and the
body is byte-identical between Audio, LX and Video -- the whole reason this exists.

⚠️ Slot names belong to the TYPE (`objects/<type>.yml` → `data_slots`); an undeclared key
is reported. ⚠️ ONE FRONTMATTER FORM: a slot is always a map with `file:`. The old list
form is reported by name, because an ignored key looks exactly like the feature never
having worked. ⚠️ The embed carries NO label; the mention carries one because a sentence
needs words. `data` is a reserved admonition type.


WHAT THE SHEET ITSELF CAN SAY
=============================

    thtr::id.key    slug    title::.key    credits::num    unit_cost::money

A header cell may DECLARE its column's type and role -- `sheet.split_header`, which also
carries why derivation alone is not enough. It runs BEFORE `apply_options` here, so an
option saying `sort: credits` still matches a column headed `credits::num`.

A cell may say anything a line of body text can say inline: markers, `@` references,
bold, code. `cells.py` owns that, and owns the escaping order that makes it safe.

⭐ MARKUP CANNOT REORDER A SHEET (`sheet.sort_within_sections`). ⚠️ But a SPREADSHEET
cannot read a marked cell as a number, and nothing here can fix that (J17).

⭐ **THE RENDERER NEVER LEARNS WHAT DEVICE IT IS ON, AND CANNOT.** MkDocs builds one file
and Pages serves those same bytes to every reader -- there is no request, no viewport, no
user agent at build time. So `table.py` marks ROLES and `assets/data.css` restructures at
read time with a CONTAINER query. One artifact, so a phone and a laptop cannot disagree
about what the data says; and a container query rather than a viewport one because a table
is a component, so it answers to the space it is given and not to the size of the glass.


FAILURE POSTURE
===============

Warn, render without the broken part, publish, report. Never raise, never fail a build
over a cosmetic typo. `sheet.apply_options` carries the argument for why an ignored option
is reported rather than silent, and it is the most important paragraph in this feature.

NOT PROVIDED: filters, totals, renames, computed columns. Those edit the data and the
sheet is the source of truth. `hide` is allowed because dropping a column from a VIEW does
not change what the sheet says. ⚠️ The one exception, deliberately narrow and argued in
`table.py`, is that a `money` cell is padded to two decimals.

⚠️ `pin:` EMITS MARKUP THE STYLESHEET DOES NOT YET HONOUR. The sticky rule is held until
the older frozen-column claim is verified on the deployed site. Shipping CSS onto an
unverified mechanism is the same silent failure one layer up.


THE TRAP THAT LIVES IN THIS FILE
================================

🐛 The download link was a 404 on every non-index page until 2026-08-04 while the comment
beside it asserted a bare filename was correct: under `use_directory_urls` a page at
`lighting/x.md` serves from `lighting/x/` while its TSV stays a sibling. It goes through
`util.relative_url` now -- the helper that fixed the same class of bug in links.py,
router.py and revlog.py. Do not go back to a bare filename, and do not count separators.

*(The two `sticky` traps moved to `table.py` with the code that carries them. A trap
described in one file and implemented in another is the two-homes defect with extra
steps.)*
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

#: src_uri -> {slot: {"href": ..., "anchor": bool}}. Written at stage 01b, read by links.py
#: at stage 03 to resolve an inline @data: mention. The per-page event order guarantees 01b
#: has already run for THIS page.
#:
#: `href` is resolved RELATIVE TO THE PAGE, not a bare filename -- links.py hands it
#: straight to a reader, so a wrong value here is a 404 in two places rather than one.
PLACED: dict[str, dict[str, dict]] = {}


def _slots_for_type(type_name: str) -> list[str]:
    """The `data_slots` a type may carry, flattened along its `extends` chain.

    ⚠️ Walks state.TYPES itself rather than reading meta["_spec"], because objects._resolve
    merges only requires/optional/renders. Folding `data_slots` into that merge is the
    right end state and is a named follow-up; until then this is the one place the chain is
    walked twice, and it is called out here so it does not become the quiet second copy
    this feature spends its docstrings arguing against.
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

    here = Path(page.file.abs_src_path).parent
    folder = posixpath.dirname(src)
    replacements: list[tuple[int, int, str]] = []

    def href_for(filename: str) -> str:
        """The TSV's URL as seen FROM THIS PAGE. Never the bare filename."""
        site_path = posixpath.join(folder, filename) if folder else filename
        return relative_url(site_path, page.file.url)

    # ⚠️ PLACED IS POPULATED BEFORE ANY CELL IS RENDERED, and the order is the point. A
    # cell may itself contain `[x](@data:other_slot)`, and cells.render resolves that
    # through links.py, which reads this map. Filling it afterwards would make a same-page
    # reference resolve as broken on the first table and fine on the second -- an ordering
    # bug that reads as a typo.
    embedded = {b[2] for b in blocks}
    placed: dict[str, dict] = {
        slot: {"href": href_for(entry["file"]), "anchor": slot in embedded}
        for slot, entry in declared.items()
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

        path = here / entry["file"]
        if not path.is_file():
            state.note(
                "missing_required",
                src + ": data slot '" + slot + "' declares file '" + entry["file"]
                + "' which does not exist beside it.",
            )
            replacements.append((
                start, end,
                '<p class="docrender-dead">Missing data file: '
                + html.escape(entry["file"]) + "</p>",
            ))
            placed[slot]["anchor"] = False
            continue

        rows = sheet.trim_columns(sheet.read_rows(path))
        if not rows:
            state.note(
                "notes",
                src + ": data file " + entry["file"] + " is empty or unreadable.",
            )
            replacements.append((start, end, ""))
            placed[slot]["anchor"] = False
            continue

        # BEFORE apply_options, so `sort: credits` still matches `credits::num`.
        rows, specs = sheet.split_header(rows, slot, src, state.note)
        rows, pinned, override = sheet.apply_options(
            rows, options, slot, src, state.note
        )
        caption = override if override is not None else entry["caption"]
        replacements.append((
            start, end,
            table.draw(rows, specs, href_for(entry["file"]), entry["file"], slot,
                       caption, pinned, page),
        ))

    for slot in declared:
        if slot in embedded:
            continue
        # Declared and never drawn. It is NOT quietly appended at the page foot: a table
        # silently landing at the bottom of a long page is the failure nobody notices for a
        # month, and that fallback is the second legal path this rewrite removed.
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
