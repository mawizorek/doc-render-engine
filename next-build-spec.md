# doc-render-engine — next build spec

⚠️ **FOUR INDEPENDENT BUILDS ARE INDEXED HERE.** None depends on another except where noted. 1 and 2 live in this file because neither was big enough for its own document; **3 and 4 live in their own files, and that is the convention now** — see the size note below.

| | Build | Scoped | State | Where |
|---|---|---|---|---|
| **1** | `dialect.py` + `clean.py` — publish the vocabulary, perform the removal | 2026-08-04 | ⚠️ SCOPED, NOT GREENLIT | below |
| **2** | **The build report has no reader** — annotations, digest, `report.py` | 2026-08-06 | ⚠️ SCOPED, NOT GREENLIT | below |
| **3** | **A scoped theme, and the report page that needs it** | 2026-08-07 | ⚠️ SCOPED, NOT GREENLIT | [`specs/scoped-theme.md`](specs/scoped-theme.md) |
| **4** | **The `draft` status, and the watermark it drives** | 2026-08-16 | ⚠️ SCOPED, NOT GREENLIT | [`specs/draft-watermark.md`](specs/draft-watermark.md) |

🔴 **THIS FILE WAS 22,660 B BEFORE BUILD 3 WAS ADDED — PAST THE 22KB CEILING IT DOCUMENTS OTHER FILES AGAINST.** A file that cannot be read whole cannot be safely edited, and this one holds the plans. BUILDS 3 AND 4 went to `specs/` for that reason. **Builds 1 and 2 should follow them, leaving this as an index**; that is a real edit somebody has to make and it is not part of any current build.

⚠️ **BUILD 3 DEPENDS ON BUILD 2 — the only dependency in the table.** Its report page is a second caller of the renderer BUILD 2 Piece C extracts into `report.py`. Building 3 first means writing that renderer twice. **BUILD 4 depends on nothing.**

Decision history for all four: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

---

# BUILD 1 — `dialect.py` + `clean.py`

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

⚠️ **THIS TABLE'S OWN NUMBERS HAD ROTTED IN 48 HOURS, and the drift changed an instruction rather than just a figure.** `markers.py` was recorded here as 16,241 B and is **18,534** — so the note moved from *"near the ceiling"* to *past the warn line*. `mkdocs.yml` was 5,580 B and is **7,685**. The 08-04 note about `prism/next-build-spec.md` quoting `datatable.py` at 16,410 B stands and is now doubly stale: HEAD was 14,885 on 08-04 and is **16,566** today after PR #103. **A size written into prose is wrong within two days, every time, in this repo. Measure at the moment you act, never quote this table.**

---

## Sequence

1. **`dialect.py`** — independent, testable alone, unblocks Prism's vocab reader.
2. **`clean.py` + `strip()`** — independent of Prism entirely.
3. Wire the CLI entry point.
4. Consumers (Prism `prism.vocab.js`) read the manifest. **No consumer ever reimplements removal.**

**Steps 1 and 2 can ship in either order.** Neither depends on the other, and neither depends on anything in Prism or git-grab.

---

# BUILD 2 — the build report has no reader

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-06.

⚠️ **AND IT NOW HAS A DOWNSTREAM CONSUMER (2026-08-07).** BUILD 3's report PAGE is a second caller of the renderer Piece C extracts. That does not change any decision below; it raises Piece C's priority from tidiness to a dependency.

> Michael, 2026-08-06, after a session that fixed three defects in a row: *"spec the build-report digest."*

## The evidence, and it is not anecdotal

Three defects were found by hand in one session. **Two were already in the build report, printed on every publish, for days.**

| Defect | Bucket | What the report said | Fixed by |
|---|---|---|---|
| `production-dropbox.md` declared data slot `folders`, which `reference` does not allow | `missing_required` + `dead_links` | *"data slot 'folders' is not declared on type 'reference'. Declared: schedule, survey, inventory_table, revision_log, catalog."* | uritp-docs #59 |
| `courses/index.md` had `hide: slug, lab offered, …` — one missing comma, so two columns never hid | `dead_links` | *"hides column 'lab offered' which is not in the sheet. Nothing hidden. Header: …"* | uritp-docs #60 |
| `automatic-revision-log.md` uses slot `revlog`, which no type declares | **none** | **nothing, and nothing was possible** — see the limit below | not a defect (ruled) |

Both messages are excellent: each names the file, the offending value, and the correct alternatives. Both also rendered on the page as visible red markers. **Nobody read either one, and both pages looked plausible enough that nobody looked twice.**

### ⚠️ THE HONEST LIMIT, FIRST, SO NOBODY OVERSELLS THIS

**The third defect would still be invisible after this build ships.** `revlog` passes validation because `datatable._declared()` guards with `if legal and slot not in legal` and `page` declares no `data_slots` — ruled correct on 2026-08-06 (*"empty means anything goes"*, PR #103). It produces no finding, so there is no report line, so no digest can surface it.

**A digest makes the report louder. It does not make the checks smarter.** Two out of three is the honest claim, and any framing of this work implying otherwise is wrong.

---

## 🔴 The root cause is NOT where the report prints

The obvious diagnosis is *"it prints to stdout in a CI log nobody opens."* True, and not the cause.

**The cause is that a build with forty findings and a build with none produce the identical green checkmark.** `sizecheck.on_post_build` exits 0 either way. Nothing about the run's *appearance* depends on what the report says, so the report can only be found by somebody who already suspects something — which is exactly the person who does not need it.

The file already knows this in one place: the leak scan is *"still the ONE hard failure in the pipeline. Everything else warns."* **A warning that never blocks and never notifies is not a warning. It is a diary.**

So the build is: make the run LOOK different when the report is not clean. Everything else is presentation.

---

## What already exists. Do not rebuild any of it.

**1. The report itself is good and is not the problem.** `docrender/sizecheck.py` job 3: fifteen buckets in `_LABELS`, ordered cause-before-symptom, an `_INVENTORY` set that stops worklists counting as defects, and a *"No findings"* clean signal. **This spec adds no bucket, no check, and no message.**

**2. `GITHUB_STEP_SUMMARY` IS ALREADY BEING WRITTEN — and not by sizecheck.** `docindex.on_post_build` (hook 09) appends the publish preview and the reference-graph section to it. **This is the most important fact in this spec.** The surface exists, has a writer, and has a proven format. The digest is a second section on a page that already renders, not a new mechanism.

**3. Annotations are already emitted from sizecheck** — one `::error::`, for the leak scan. **The mechanism for making a run look different is already in the file that needs it.** It has only ever been used for the one failure that also exits 1.

⚠️ **4. AND AS OF 2026-08-07 THERE IS A SECOND ANNOTATION IN THE PIPELINE**, from `instance._theme_override`: one `::notice::` naming the theme a publish overrode to, or one `::warning::` when the name was refused. It fires only on an override, so it does not affect the 10-per-step cap arithmetic in Piece A — but Piece A must count it rather than discovering it.

---

## The three pieces, cheapest first

### PIECE A — warning annotations. Do this first; it is most of the value.

GitHub renders workflow-command annotations at the top of the run page and inline on a PR diff. One line per non-inventory bucket:

```
::warning title=docrender broken references::4 findings in dead_links -- see the build report
```

- **Non-inventory buckets only.** `markers`, `routers`, `nav_default` and `aliases` fire on every build by design; annotating them trains everyone to ignore annotations, which rebuilds the exact failure being fixed.
- **One annotation per BUCKET, never per entry.** The `markers` bucket alone carries roughly twenty entries on the courses sheet.
- ⚠️ **GitHub caps annotations at 10 per step.** Bucket-level keeps us at or under eleven by construction. Per-entry does not, **and the overflow is dropped silently** — a truncation nobody is told about, which is this repo's least favourite shape.
- 🚫 **Does not change the exit code.** The leak scan stays the only hard failure. Ruling 3 asks whether that should ever change.

### PIECE B — the same report, rendered into the step summary

Append the report to `GITHUB_STEP_SUMMARY` beside docindex's publish preview.

⭐ **ONE RENDERER, TWO DESTINATIONS — this is the whole design constraint.** A markdown renderer for the summary *plus* the existing `print()` loop is two implementations of one output, and they will disagree inside a month. **Markdown reads perfectly well as plain text** (`###` headings, `-` bullets), so render once and send the same string to stdout and to the summary file. The current plain-text loop is deleted, not kept alongside. *(2026-08-07: BUILD 3 makes it THREE destinations. The constraint is unchanged and the argument is stronger.)*

⚠️ **APPEND ORDER IS HOOK ORDER, AND IT IS INVISIBLE.** Both writers open the file in append mode. sizecheck is hook 08 and docindex is 09, so the naive implementation puts findings ABOVE the publish preview. **Recommend findings BELOW the preview** — the preview answers *what am I about to ship*, which is the headline, and Piece A carries urgency independently of where the section sits. That requires the digest to run after hook 09. **Ruling 2.**

⚠️ **`dry_run` is the case that matters most.** docindex's docstring: *"In `dry_run` mode nothing deploys and this report is the entire output."* A preview showing what changes but not what broke is half a preview.

### PIECE C — split the report into `docrender/report.py`

`sizecheck.py` is **14,859 B** and its own docstring opens with *"THREE JOBS, all of which want to run last."* Adding a markdown renderer makes it four jobs at roughly **19 KB** — past the 18KB warn line the file itself enforces on everybody else. That is not ironic, it is disqualifying.

The report was never a size-budget concern; it lives there because both run last. Move job 3 to `docrender/report.py` and leave the size budget and the leak scan behind.

🔴 **`_LABELS` MOVES WITH IT AND IS NOT COPIED.** It is the section order, the display names, and the only thing standing between a bucket and silent oblivion. Two copies of that dict is the defect this repo has retired three manifests over.

⚠️ **The two-edit rule survives the split and gets worse.** `state.reset()` and `_LABELS` already both carry the warning that adding a report section means two edits in two files. After this they are two edits in two files that sit *further apart*. Restate it in `report.py`'s header; do not assume the move makes it obvious.

---

## ⏳ Rulings needed (three)

**1. Is the Actions surface enough?** Everything above still requires opening a workflow run. The alternatives, with the objection to each:

- **A published `/build-report/` page on the site.** 🚫 Recommend against: it puts internal validation output on a public docs site, and the content-repo purity rule says the content tree holds documents, not machinery. ⚠️ **PARTIALLY OVERTURNED 2026-08-07 — see `specs/scoped-theme.md` §2.** The purity half is wrong: a GENERATED page never enters the content repo, which is what the rule is about, and `assets.py` already publishes six such files via `File.generated`. **The public-exposure half stands and is the real problem**, and BUILD 3 §5 is where it gets answered.
- **A ClickUp comment posted from the workflow.** 🚫 Recommend against *inside the engine*: it needs a token, and it makes the engine know about a system that is not the web — the leak scan exists to stop exactly that class of coupling. If it is wanted, it belongs in the **workflow**, reading the summary file the engine already wrote. The engine stays ignorant, which is the seam that keeps it portable.
- **Recommend: ship A and B, live with it a week, let the annotations prove whether the surface is the problem.** Today's evidence says nobody looks because nothing tells them to look, not because the log is hard to reach.

**2. Where does the digest sit relative to the publish preview, and how?** A new hook at 10, or a call from docindex? **Recommend its own hook at 10.** A call from docindex makes hook 09 responsible for a section it does not own, and this engine has spent several decision blocks separating exactly that.

**3. Should any non-leak finding ever fail a build?** Today no, deliberately — *"a cosmetic typo must not be able to fail a build."* But `missing_status` means a page **was not built**, which is not cosmetic. **Recommend no exit-code change in this build.** Ship the annotations and see whether visibility is sufficient. Failing on a category that has been silently accumulating for weeks would fail every site on the first run, and the first thing anybody would do is switch it off.

---

## Files and sizes (measured at HEAD 2026-08-06, read back not estimated)

| File | Now | Change |
|---|---|---|
| **NEW** `docrender/report.py` | — | ~6-7 KB. `_LABELS` + one markdown renderer + the annotation emitter. |
| `docrender/sizecheck.py` | 14,859 B | **−4 to −5 KB.** Loses job 3, `_LABELS`, `_INVENTORY` and the print loop; docstring drops to two jobs. |
| `docrender/state.py` | 13,271 B | **untouched.** `REPORT` and `note()` do not move. |
| `docrender/docindex.py` | 13,199 B | **untouched** under ruling 2. |
| `mkdocs.yml` | 7,685 B | one hook registration. |

⚠️ **Net effect on the budget is NEGATIVE**, which is worth stating because a new module usually is not.

---

## Sequence

1. **Piece C first — the split.** A pure move, no behaviour change, independently reviewable. Doing it after A and B means writing new code into a file already at the warn line.
2. **Piece A — annotations.** Smallest diff, largest effect, no format decisions to make.
3. **Piece B — the summary section.** Needs ruling 2 first.

🚫 **Do not start with B.** It is the piece that looks like the feature, and it is the one blocked on a ruling. A ships value the same day and is reversible in one line.

---

# BUILD 3 — a scoped theme, and the report page that needs it

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-07. **The spec is [`specs/scoped-theme.md`](specs/scoped-theme.md)** — it is not reproduced here, because a second copy of a plan is the defect both builds above already exist to prevent.

One-line summary: a build report that renders as a generated PAGE on the site, wearing the `utility` theme rather than the site's own — which requires a theme that can apply to part of a site, which this engine has never had.

🔴 **Its §1 is a blocking ruling on what "UTILITY" meant** (the theme, or the `01-utility/` folder), and the answer decides whether half the build exists at all. ⚠️ **Its §4c is the finding worth reading even if the build never happens:** a scoped selector silently kills `print.css` on the pages it scopes, because that sheet wins on source order at equal specificity and a two-attribute scope outranks it.

---

# BUILD 4 — the `draft` status, and the watermark it drives

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-16. **The spec is [`specs/draft-watermark.md`](specs/draft-watermark.md)** — not reproduced here, same reason as BUILD 3.

One-line summary: make `draft` a first-class page status, and let a **status → treatment map** (only `draft` populated) paint a fixed 45° **DRAFT** watermark over the scroll viewport on screen. Print adds DRAFT **manually** in the existing print flow — the same path that strips "edit on git" and forces a white background — rather than inheriting the screen rule.

🔴 **Its §0 is a blocking read that must happen first:** what does the engine do with `status: draft` TODAY? If an unrecognized status falls through to *publish*, the whole `safety/` tree (all `draft`) may be live right now, which turns this from a feature into a fix. ⚠️ **It touches `print.css`, which BUILD 3 §4c flags as fragile under scoping** — if both land, the draft print rule and the scoped-theme selector interact.
