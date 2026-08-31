# BUILD 2 — the build report has no reader

🔴 **PARTLY SHIPPED. ~~SCOPED, NOT GREENLIT.~~** Scoped 2026-08-06. **Moved out of `next-build-spec.md` on 2026-08-31**, on that file's own instruction. Indexed from [`next-build-spec.md`](../next-build-spec.md). Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

⚠️ **THE STATE LINE IS STRUCK RATHER THAN OVERWRITTEN, BECAUSE THE INDEX CARRIED IT AS UNBUILT FOR WEEKS AFTER IT WAS FALSE.** A superseded state and a violated one look identical once the old wording is deleted.

## ✅ What actually shipped, measured at HEAD `076ce81` on 2026-08-31

| Piece | State | Evidence |
|---|---|---|
| **C** — split the report into `docrender/report.py` | ✅ **SHIPPED** | the module exists at **16,490 B** and holds `_LABELS`; `hooks/08b_report.py` (1,820 B) is on disk between `08_sizecheck` and `09_index` |
| **A** — warning annotations | ✅ **SHIPPED**, and it is the piece this spec called *"most of the value"* | `::warning` is emitted from `report.py` |
| **B** — the same report in `GITHUB_STEP_SUMMARY` | ⚠️ **NOT VERIFIED EITHER WAY** | not read this pass. It is the piece blocked on ruling 2, so absence would be correct rather than a defect |

⭐ **AND `scoped-theme.md` (BUILD 3) ALREADY RECORDED THIS FROM THE OTHER SIDE**, in its own closed-rulings table: *"Wait for BUILD 2 Piece C? **Yes, and it went first**, exactly as recommended."* 🔴 **So the fact was written down in a sibling spec and the index still said NOT GREENLIT.** ⚑ *A state living in two files is only as true as the copy nobody updates — which is the defect this whole spec is about, committed against the spec itself.*

## 🔴 One thing to READ before anybody builds on this, named rather than asserted

`_LABELS` matches in **both** `docrender/report.py` and `docrender/sizecheck.py` at HEAD. This spec's own instruction, in bold, was: *"`_LABELS` MOVES WITH IT AND IS NOT COPIED… Two copies of that dict is the defect this repo has retired three manifests over."*

⚠️ **THAT IS A GREP, NOT A FINDING, AND THE DIFFERENCE IS THE WHOLE POINT.** The string could be a live second dict, or a comment, or a one-line reference pointing at the real one. **Read both files before concluding anything** — a guess wearing the clothes of a measurement is camouflaged by the real measurements beside it, and this file is now full of them. The check is two reads and it decides whether a bucket can go silently missing.

⚠️ **EVERY NUMBER IN THE "Files and sizes" TABLE AT THE BOTTOM IS FROM 2026-08-06 AND IS STALE.** `sizecheck.py` is **17,550 B** at HEAD, not 14,859 — it went **UP** by 2.7 KB across a change that was supposed to remove 4–5 KB from it, so the *"net effect on the budget is NEGATIVE"* claim did not survive contact. `mkdocs.yml` is **29,259 B**, not 7,685. **Measure at HEAD. Never quote that table.**

---

⚠️ **THE BODY BELOW IS THE 2026-08-06 TEXT VERBATIM.** Nothing in it was re-measured or re-argued on the way across; the corrections all sit above, where a reader meets them first.

---

⚠️ **AND IT NOW HAS TWO DOWNSTREAM CONSUMERS.** BUILD 3's report PAGE is a second caller of the renderer Piece C extracts (2026-08-07). **BUILD 6's QR inventory bucket is a third** (2026-08-21) — and it lands in `sizecheck.py` if it ships first, or in `report.py` if this build does. Neither changes any decision below; together they raise Piece C's priority from tidiness to a dependency.

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

- **Non-inventory buckets only.** `markers`, `routers`, `nav_default` and `aliases` fire on every build by design; annotating them trains everyone to ignore annotations, which rebuilds the exact failure being fixed. ⚠️ **BUILD 6's `qr` bucket is inventory and is therefore NOT annotated** — same rule, and its spec cites this line for the reason.
- **One annotation per BUCKET, never per entry.** The `markers` bucket alone carries roughly twenty entries on the courses sheet.
- ⚠️ **GitHub caps annotations at 10 per step.** Bucket-level keeps us at or under eleven by construction. Per-entry does not, **and the overflow is dropped silently** — a truncation nobody is told about, which is this repo's least favourite shape.
- 🚫 **Does not change the exit code.** The leak scan stays the only hard failure. Ruling 3 asks whether that should ever change.

### PIECE B — the same report, rendered into the step summary

Append the report to `GITHUB_STEP_SUMMARY` beside docindex's publish preview.

⭐ **ONE RENDERER, TWO DESTINATIONS — this is the whole design constraint.** A markdown renderer for the summary *plus* the existing `print()` loop is two implementations of one output, and they will disagree inside a month. **Markdown reads perfectly well as plain text** (`###` headings, `-` bullets), so render once and send the same string to stdout and to the summary file. The current plain-text loop is deleted, not kept alongside. *(2026-08-07: BUILD 3 makes it THREE destinations. The constraint is unchanged and the argument is stronger.)*

⚠️ **APPEND ORDER IS HOOK ORDER, AND IT IS INVISIBLE.** Both writers open the file in append mode. sizecheck is hook 08 and docindex is 09, so the naive implementation puts findings ABOVE the publish preview. **Recommend findings BELOW the preview** — the preview answers *what am I about to ship*, which is the headline, and Piece A carries urgency independently of where the section sits. That requires the digest to run after hook 09. **Ruling 2.**

⚠️ **`dry_run` is the case that matters most.** docindex's docstring: *"In `dry_run` mode nothing deploys and this report is the entire output."* A preview showing what changes but not what broke is half a preview. ⚠️ **BUILD 6 leans on this hard**: a QR payload read off a preview build is the one artifact that cannot be re-published once printed.

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
| `docrender/state.py` | 13,271 B | **untouched.** `REPORT` and `note()` do not move. ⚠️ **15,918 B at HEAD 2026-08-21** — the row above is the scar this file keeps documenting. |
| `docrender/docindex.py` | 13,199 B | **untouched** under ruling 2. |
| `mkdocs.yml` | 7,685 B | one hook registration. ⚠️ **13,632 B at HEAD 2026-08-21.** |

⚠️ **Net effect on the budget is NEGATIVE**, which is worth stating because a new module usually is not.

---

## Sequence

1. **Piece C first — the split.** A pure move, no behaviour change, independently reviewable. Doing it after A and B means writing new code into a file already at the warn line.
2. **Piece A — annotations.** Smallest diff, largest effect, no format decisions to make.
3. **Piece B — the summary section.** Needs ruling 2 first.

🚫 **Do not start with B.** It is the piece that looks like the feature, and it is the one blocked on a ruling. A ships value the same day and is reversible in one line.
