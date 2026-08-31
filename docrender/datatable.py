"""Stage 01b -- render a TSV as a table. Beside the page, or by name from anywhere.

Decision history: doc-render-engine (repo) Decision Log in ClickUp, blocks J4/J5/J7/J17
and J20/J21. **The argument lives THERE; this file states the contract.** That split is
not a style preference -- this docstring has three times grown until the module failed
the size gate it enforces on everybody else.

FOUR MODULES, ONE FEATURE:

    sheet.py    reading and shaping a TSV. Rows, header, sections, options, order, kind.
    cells.py    one cell as prose. Markers, @refs, inline markdown, escaping.
    table.py    shaped rows -> markup. Column classes, roles, labels, money, the shell.
    this file   the frontmatter contract, the `!!! data` block, and WHERE THE FILE IS.


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

⚠️ Slot names belong to the TYPE (`objects/<type>.yml` → `data_slots`); an undeclared key
is reported -- BUT ONLY IF THAT TYPE DECLARES ANY. An empty `data_slots` list means
UNRESTRICTED, ruled by Michael 2026-08-06 ("empty means anything goes"), so a page on
`page`, `procedure`, `standard`, `venue` or `space` may use any slot name it likes and
nothing is reported. Live example: `01-utility/automatic-revision-log.md` in uritp-docs
is `type: page` and runs slot `revlog`, which no type declares. The argument, the
consequence, and the warning about adding a FIRST slot to a type are all in
`objects/_base.yml`; the guard that implements it is in `_declared()` below.

⚠️ ONE FRONTMATTER FORM: a slot is always a map with `file:`. The old list form is
reported by name, because an ignored key looks exactly like the feature never having
worked. ⚠️ The embed carries NO label; the mention carries one because a sentence needs
words. `data` is a reserved admonition type.


🔴 FINDING THE FILE -- SIBLING, RELATIVE, OR BY NAME (2026-08-31)
===============================================================
> Michael, having just made a `../../production/info-dates/...` path work: *"not a huge
> fan of it but it worked"*, then, choosing between a `site.yml` registry and a tree
> search: *"i just be sure to never name tsv that same. that's my pref for now."*

Three forms, tried in this order, and the ORDER is the compatibility guarantee:

    file: audio-inventory.tsv                  1. beside the page      ← unchanged
    file: ../../production/x/dates.tsv         2. relative to the page ← unchanged
    file: dates-big-love-run-crew.tsv          3. anywhere in the tree ← new

✅ 1 AND 2 ARE ONE TEST AND ARE BYTE-IDENTICAL TO WHAT SHIPPED. `Path` resolves `..`
itself, so a declared path that names a real file wins before the index is ever consulted.
His two live pages keep working with no edit, and a page can still force a specific file
by path when two names collide.

⚠️ A REGISTRY WAS THE OTHER CANDIDATE AND WAS REFUSED BY HIM, on the honest objection:
*"so i still have to register the tsv somewhere else then?"* A `site.yml` map trades
counting separators for bookkeeping and **removes no step** -- it makes a new TSV a
two-file edit. The search removes the step entirely.

🔴 THE COST HE ACCEPTED, SO IT MUST FAIL LOUD: two TSVs with the same basename in
different folders. `_by_name` reports EVERY path it found and refuses -- it does not pick
the shallowest, the first, or the nearest. **A silent choice between two files is the one
outcome that could publish the wrong dates on a call sheet**, and this engine's standing
polarity is that an ambiguous reference reports rather than guesses (`sheet.apply_options`
carries the long-form argument).

⭐ IT NEEDED NO NEW HOOK EVENT AND NO `mkdocs.yml` EDIT, which is the whole reason it is
cheap: `on_page_markdown` **already receives `files`**. The index is built from a
parameter that was there all along. ⚑ Same shape as `runfoot.py`'s finding hours earlier
-- *the blocker was on the shape I assumed, not on the outcome I wanted* -- and it matters
because `mkdocs.yml` is 28,158 B and past the write cap, so a new hook has been an
unavailable write for weeks.

⚠️ THE INDEX IS CACHED AGAINST THE `files` OBJECT ITSELF, NOT ITS `id()`. `mkdocs serve`
rebuilds in-process, so a grow-only module dict would carry a deleted page's TSV into the
next build -- the trap `qr.PENDING` documents and clears at `on_config`. Holding the
reference makes the identity check true rather than probable; `id()` can be recycled.


🔴 `align:` IS A LAYOUT OPTION AND IS POPPED BEFORE `sheet.apply_options` EVER SEES IT
=====================================================================================
Added 2026-08-29, on the `!!! qr align=` precedent one module over. Every OTHER option on
the block reshapes the DATA -- `sort`, `pin`, `hide` -- and `sheet.apply_options` validates
them against its own `KNOWN_OPTIONS`, reporting anything it does not recognise.

⚠️ SO LEAVING `align` IN THAT DICT WOULD REPORT IT AS AN UNKNOWN OPTION ON EVERY TABLE
THAT USED IT, correctly, because it IS unknown to that validator -- `sheet.py`'s contract is
*"everything BEFORE the HTML... it emits no HTML and imports nothing that does"*, and
alignment is presentation. Adding it to `KNOWN_OPTIONS` would break that contract for a
key the module has no use for.

⭐ SO IT IS POPPED HERE AND HANDED STRAIGHT TO `table.draw`. Two vocabularies, one
indented option block, and the seam is written in all three files. ✅ Verified by executing
the parser against eight option sets, including `align: middle` (reported and dropped) and
`algin: center` (still caught by sheet.py as an unknown key).


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

🔴 AND THAT TRAP IS WHY RESOLUTION RETURNS A **SITE PATH** RATHER THAN A FILENAME. A TSV
found elsewhere in the tree downloads from ITS OWN folder, not the page's -- so the href
must be built from where the file IS. Handing `href_for` a bare name would have made every
by-name download a 404 while the table on the page rendered perfectly: the same
looks-fine-reads-broken shape as the 2026-08-04 bug, one resolution step further out.

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
#: ⚠️ `_INDEX_FOR` HOLDS THE `files` OBJECT, NOT ITS `id()`. See FINDING in the docstring:
#: `mkdocs serve` rebuilds in-process, and holding the reference makes the identity test
#: true rather than probable.
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
    merges only requires/optional/renders. Folding `data_slots` into that merge is the
    right end state and is a named follow-up; until then this is the one place the chain is
    walked twice, and it is called out here so it does not become the quiet second copy
    this feature spends its docstrings arguing against.

    ⚠️ AN EMPTY RETURN IS MEANINGFUL AND IS NOT AN ERROR. It means the type declared no
    vocabulary, which the caller reads as UNRESTRICTED rather than as "no tables allowed".
    See `_declared` below and `objects/_base.yml`.
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
        # 🔴 `legal and` IS LOAD-BEARING. DO NOT TIDY IT AWAY.
        #
        # An empty list is falsy, so a type declaring no `data_slots` skips this check
        # entirely and accepts ANY slot name. That is the ruling, not an oversight:
        # Michael, 2026-08-06 -- "empty means anything goes." A type opts IN to a closed
        # vocabulary by naming one; it does not start behind a wall.
        #
        # Deleting two words here is a one-character-looking cleanup that would put every
        # page on `page`, `procedure`, `standard`, `venue` and `space` into the build
        # report in a single commit -- including uritp-docs' automatic-revision-log,
        # which has run slot `revlog` since it shipped. The full argument, and the
        # warning about what adding a FIRST slot to a type costs, is in
        # `objects/_base.yml` under DATA SLOTS.
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


def _locate(declared_file: str, folder: str, files, src: str, slot: str):
    """Where the TSV actually is, as a SITE path. `""` means it was not resolved.

    Three forms, in order -- see FINDING in the module docstring:

      1/2. `beside.tsv` or `../../elsewhere/x.tsv`  -- ONE test, unchanged behaviour.
      3.   `x.tsv` found anywhere in the tree       -- new, and only reached when the
           declared path names nothing.

    🔴 THE DECLARED PATH WINS AND THAT IS THE COMPATIBILITY GUARANTEE. Every page written
    before 2026-08-31 resolves exactly as it did, and a page CAN still pin one specific
    file by path when two share a basename.

    🔴 A DUPLICATE BASENAME IS REPORTED WITH EVERY PATH AND REFUSED. Not the shallowest,
    not the first, not the nearest -- Michael accepted unique naming as the cost of this
    feature, so the moment that assumption breaks he has to be told rather than served a
    coin flip. On a call sheet the wrong file is the wrong dates.

    ⚠️ RETURNS A SITE PATH, NEVER A FILENAME. The caller builds both the read path and the
    download href from it, so the table and its download cannot disagree about which file
    they mean -- the failure the 2026-08-04 trap in this module's docstring records.
    """
    declared_file = declared_file.strip()
    if not declared_file:
        return ""

    # 1 + 2: relative to the page. `posixpath.normpath` collapses `..` the same way
    # `Path` does, so the site path and the on-disk read cannot drift apart.
    joined = posixpath.join(folder, declared_file) if folder else declared_file
    site_path = posixpath.normpath(joined).lstrip("/")
    if not site_path.startswith("..") and (Path(state.DOCS_DIR) / site_path).is_file():
        return site_path

    # 3: by name, anywhere. Only a BARE filename may search -- a declared path that
    # missed is an authoring mistake with a specific answer, and quietly finding a
    # same-named file somewhere else would hide the typo rather than report it.
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

    🔴 THE POP IS THE POINT, NOT A CONVENIENCE. `sheet.apply_options` reports any key it
    does not know, and it correctly does not know this one -- see the module docstring. If
    this function is ever changed to READ rather than REMOVE, every aligned table starts
    emitting an unknown-option warning.

    ⚠️ AN UNRECOGNISED VALUE IS REPORTED AND DROPPED, never guessed. A table silently
    sitting in the wrong place reads as a stylesheet bug and is an authoring one -- the
    same polarity `sheet.apply_options` argues for at length.
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

    # ⚠️ RESOLVED ONCE PER SLOT, NOT ONCE PER USE. A slot mentioned inline AND embedded
    # would otherwise report a missing file twice and index the tree twice.
    located = {
        slot: _locate(entry["file"], folder, files, src, slot)
        for slot, entry in declared.items()
    }

    def href_for(site_path: str) -> str:
        """The TSV's URL as seen FROM THIS PAGE. Never a bare filename -- see the
        module docstring's 2026-08-04 trap, and never the PAGE's folder for a file
        that lives somewhere else."""
        return relative_url(site_path, page.file.url)

    # ⚠️ PLACED IS POPULATED BEFORE ANY CELL IS RENDERED, and the order is the point. A
    # cell may itself contain `[x](@data:other_slot)`, and cells.render resolves that
    # through links.py, which reads this map. Filling it afterwards would make a same-page
    # reference resolve as broken on the first table and fine on the second -- an ordering
    # bug that reads as a typo.
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
        # beside the page, nowhere in the tree, or an ambiguous name -- and each has its
        # own report line naming the paths involved. The on-page marker stays generic
        # because it is read by somebody who then goes to the report.
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

        # 🔴 LAYOUT FIRST, AND IT REMOVES THE KEY. `sheet.apply_options` reports anything
        # it does not recognise, and it does not recognise this. See `_align`.
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
