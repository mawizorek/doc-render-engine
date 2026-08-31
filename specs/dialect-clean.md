# BUILD 1 — `dialect.py` + `clean.py`

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-04. **Moved out of `next-build-spec.md` on 2026-08-31**, unchanged except for this header — that file's own instruction, written when it was already past its ceiling: *"Builds 1 and 2 should follow them, leaving this as an index."* Indexed from [`next-build-spec.md`](../next-build-spec.md). Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

⚠️ **THE BODY BELOW IS THE 2026-08-06 TEXT VERBATIM, INCLUDING ITS OWN STALENESS WARNINGS.** Nothing was re-measured on the way across, deliberately: a move that also edits is two changes wearing one commit, and this file's *"Files and sizes"* table already carries three dated notes saying every number in it rots within 48 hours. 🔴 **Measure at HEAD when you act. Never quote that table.**

---

> Michael, 2026-08-04: *"a helper script that identifies our declared markers and makes them publicly available to other apps… It would be neat if this could apply to TSVs and Markdown files as well… published by a renderer action, identifying the markers we use and their flags, along with the logic for how to remove them. That way, you're left with just the prose."*

Two deliverables, and they must not be one thing:

| | What | Shape |
|---|---|---|
| **`dialect.py`** | publish the VOCABULARY | generated `dialect.json`, DATA, public |
| **`clean.py`** | perform the REMOVAL | one Python implementation, two entry points |

---

## 🔴 The correction this spec exists to make: STRIP is not PLAIN

`cells.plain()` already exists (`docrender/cells.py`, 9,660 B, in production) and takes a plain `str`, not a cell object — **it has no idea it is being handed a cell.** So "point it at markdown too" looks free.

**It is not free, and pointing it at a markdown document would quietly destroy the document.** `plain()` is a *plaintext-ifier*, not a *marker-stripper*. For a TSV cell those are the same operation, because a cell is one line of inline prose by construction. For a `.md` file they are emphatically different, and here are three concrete failures, read out of the source rather than guessed:

**1. It strips braces that are not ours.** `plain()` opens with `re.sub(r"\{[^}\n]*\}", "", text)` — **every** brace block. But `markers.on_page_markdown` is careful: `row = _TABLE.get(name)`, and if the name is not in `markers.tsv` it hands the text back untouched, with the comment *"Not one of ours… almost certainly an attr_list attribute on a real element (`{ .md-button }`)… rather than eating syntax that belongs to somebody else."* **The renderer and `plain()` already disagree about what a marker is.** On a cell nobody notices. On a markdown page, `{ .md-button }`, `{ #anchor }` and every other attr_list block vanishes.

**2. Stripping backticks destroys code FENCES.** `.replace` on the backtick exists to strip inline code spans, which is right for a cell. Run it over a document and a triple-backtick fence becomes an empty string — so a fenced block does not lose its formatting, **it stops being a block at all** and its contents merge into the body as prose. Silent, and catastrophic on any page carrying an example.

**3. No `sub_outside_code`.** The renderer routes every substitution through `util.sub_outside_code` so marker syntax inside a fence is left alone. `plain()` has no such guard — which means **the page that documents the marker syntax would have its examples stripped by the stripper.** The syntax reference destroys itself. This is the one that would be found last and hurt most.

### Therefore: two named operations, and neither is renamed to hide the difference

| Operation | Removes | Leaves | Correct for |
|---|---|---|---|
| **`strip()`** *(new)* | **only the declared vocabulary** — marker spans in `_TABLE`, `@`-references, `@term:` links | markdown intact: bold stays bold, fences stay fences, foreign attr_list untouched | **a `.md` document** |
| **`plain()`** *(exists, unchanged)* | every construct, including emphasis and code | bare text | **a TSV cell**, and `sort:` depends on it |

⭐ **`strip()` and the renderer must share `_TABLE`.** That is the whole reason this belongs in the engine: the stripper knows a marker is ours because the same merged table that paints it says so. A stripper with its own list is the fourth hand-typed copy of a vocabulary this repo has already been bitten by four times.

---

## 🔴 Publish the VOCABULARY as data. Do NOT publish the REMOVAL LOGIC as data.

Michael asked for the manifest to carry *"the logic for how to remove them."* **This is the one part of the ask I would not build, and the reason is specific rather than purist.**

Removal logic expressed as data is a set of regex patterns in a JSON file. **A published pattern is a second implementation wearing a data costume**, because the pattern is only meaningful inside a regex engine, and the engines differ in ways that bite exactly here:

- Python names a group one way and JavaScript names it another. The engine's `_LINK` and `_MARK` patterns both use named groups, so **neither one is portable as written.**
- `cells._EM` uses a lookbehind. Safari shipped lookbehind in **16.4**; anything older throws on the pattern itself, not on the input.
- Order is load-bearing and is not in the pattern. `plain()` strips braces *before* links so a marked reference degrades correctly. A consumer given four patterns and no order gets a different answer.

**So the manifest answers *what exists*; the module answers *what to do about it*.** A consumer that only needs to IDENTIFY markers (paint them, count them, warn about them — Prism's case) is fully served by data. A consumer that needs to REMOVE them gets a clean file, not a recipe.

### `dialect.json` — generated, never authored

Derived from what is already in memory at build time:

```
marker classes    <- theme/marker-classes.tsv   (class, shape, colour)
marker rows       <- theme/markers.tsv          (marker, class, label, shape, tooltip)
reserved prefixes <- prefixes.reserved()        DERIVED from prefixes.claim()
colour tokens     <- theme/colors.tsv
shapes            <- markers._SHAPES            the closed set of four
build stamp       <- buildstamp.py
```

⚠️ **`prefixes.reserved()` is the piece that cannot be a fetched TSV** — it only exists once Python has imported the hooks. That single fact is the argument for a manifest over "let consumers read the TSVs directly."

⚠️ **Read it inside an event, never at import.** `prefixes.py` documents the trap in its own header: claims happen at hook import, and a registry read at import time caches an empty answer for the whole build.

**Publishing is consistent with what Michael already ruled** on 2026-08-04 re: git-grab — *"they might see our markers in their IDE, but that's my proprietary stuff and that is totally fine."* The dialect is not a secret; it is a contract.

---

## `clean.py` — one implementation, two entry points

This is how *"I could feed it actual Markdown"* gets answered without a second implementation existing anywhere.

**Entry point 1 — the build hook.** Emits a stripped sibling next to every marked source file: `<name>.clean.tsv`, `<name>.clean.md`. They become **real files in the repo/site**, so they appear in listings, in `git-grab`'s file table and count, and in any zip, **with zero new capability in any consumer.**

**Entry point 2 — the CLI.** `python -m docrender.clean <file>` over any file on disk. Same module, same table, same answer. This is the *"feed it actual markdown"* half, and it costs a `__main__` block rather than a project.

🔴 **A distinct filename, never a stripped download under the existing link.** `01-utility/automatic-revision-log.md` promises in Michael's own words that the table and the download *"cannot disagree."* A silent strip on the way out breaks that promise; `.clean.` makes the transform visible.

### What `strip()` does to each construct

| Construct | Becomes | Note |
|---|---|---|
| a marked value with a label | the label | label survives, marker goes |
| a bare marker | the row's `label`, or nothing | the renderer already falls back to `label` then `name` |
| `[ETC](@term:etc)` | `ETC` | the reference is ours; the words are the content |
| `[x](@peer:page)` | `x` | same |
| `{ .md-button }` | **untouched** | not in `_TABLE`, not ours |
| bold, inline code | **untouched** | markdown is the content, not the markup we added |
| fenced code block | **untouched, and never scanned** | `sub_outside_code` |
| YAML frontmatter | ⏳ **ruling** | see below |
| a `!!! data` embed | ⏳ **ruling** | see below — this one loses real content |

---

## ⏳ Rulings needed (four)

**1. `!!! data` embeds — the only place stripping LOSES content.** Every other construct wraps text that survives. A data embed *is* a placeholder that the build resolves into real content by walking the page graph, so a `.clean.md` either drops it (silent content loss) or keeps the unresolved directive (an artifact that is not prose). **Recommend: emit the RESOLVED content as plain text if the strip runs after resolution, and if it cannot, leave a visible one-line placeholder naming the slot.** Precedent is set both ways in this engine: a dead `@term:` renders as the broken-reference span, never as an accessory, and Prism's spec requires MDLens to *decline visibly*. Silence is the one option with no precedent behind it.

**2. YAML frontmatter — keep, drop, or flatten?** It is metadata rather than prose, so *"just the prose"* argues for dropping it. But it carries the title, and a stripped file with no title is worse to read. **Recommend: keep it.** It is already valid text, it is not our marker vocabulary, and dropping it is a second unrelated decision hiding inside this one.

**3. Which files get a build-time sibling?** Every marked file, or only files that opt in with a frontmatter flag? **Recommend: only files that actually CONTAIN a declared marker** — the module can answer that cheaply, and emitting `.clean.md` beside a file with nothing to strip doubles the tree for nothing.

**4. Does `strip()` become the shared base of `plain()`?** `plain()` = `strip()` + emphasis/code removal is a true statement today. Refactoring `plain()` to call `strip()` is tidy, and it touches the function `sort:` depends on. **Recommend: NO, not in this build.** Ship `strip()` alongside, prove it, and unify later if it still looks right. The sorting behaviour is load-bearing and Michael's stated hard constraint was *"we absolutely cannot lose the number functionality."*

---

## Files and sizes (re-measured at HEAD 2026-08-06)

| File | Now | Change |
|---|---|---|
| **NEW** `docrender/dialect.py` | — | ~3-4 KB. Reads registries already in memory, writes one file. |
| **NEW** `docrender/clean.py` | — | ~6-8 KB. `strip()` + the hook + `__main__`. |
| `docrender/prefixes.py` | 4,385 B | +small. `reserved()` exists; the manifest needs the class/owner map too. |
| `docrender/markers.py` | 18,534 B | ⚠️ **PAST the 18KB warn line — expose `_TABLE` via a small accessor, add nothing else.** |
| `docrender/cells.py` | 9,660 B | **untouched** (see ruling 4). |
| `mkdocs.yml` | 7,685 B | two hook registrations. ⚠️ Its own comment records a hook that has been dead exactly this way. |

🔴 **Both new files go in their own modules. Do not append to `markers.py` or `datatable.py`** — the Prism spec already carries that instruction.

⚠️ **THIS TABLE'S OWN NUMBERS HAD ROTTED IN 48 HOURS, and the drift changed an instruction rather than just a figure.** `markers.py` was recorded here as 16,241 B and is **18,534** — so the note moved from *"near the ceiling"* to *past the warn line*. `mkdocs.yml` was 5,580 B and is **7,685**. 🔴 **AND IT ROTTED AGAIN: `mkdocs.yml` is 13,632 B at HEAD 2026-08-21, a 77% drift off the number in the row above.** The 08-04 note about `prism/next-build-spec.md` quoting `datatable.py` at 16,410 B stands and is now doubly stale: HEAD was 14,885 on 08-04 and is **16,566** today after PR #103. **A size written into prose is wrong within two days, every time, in this repo. Measure at the moment you act, never quote this table.**

---

## Sequence

1. **`dialect.py`** — independent, testable alone, unblocks Prism's vocab reader.
2. **`clean.py` + `strip()`** — independent of Prism entirely.
3. Wire the CLI entry point.
4. Consumers (Prism `prism.vocab.js`) read the manifest. **No consumer ever reimplements removal.**

**Steps 1 and 2 can ship in either order.** Neither depends on the other, and neither depends on anything in Prism or git-grab.
