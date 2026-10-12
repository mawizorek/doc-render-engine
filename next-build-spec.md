# doc-render-engine — the build index

**This file is an INDEX and nothing else.** Every build's plan lives in its own file under [`specs/`](specs/). Decision history for all of them: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

🚫 **NO COUNT IS WRITTEN HERE, AND THAT IS THIS FILE'S OWN INSTRUCTION BEING OBEYED.** The previous version opened *"SIX INDEPENDENT BUILDS ARE INDEXED HERE"* above a hand-kept table, went stale the first time a spec was added without touching the sentence, and said in bold: *"if it is wrong again, delete it rather than refresh it."* It was wrong again — by five rows. **A sentence and a list are two places stating one fact, and the list is the one that gets edited.** Count the rows.

## 🔴 ROWS ARE KEYED BY FILE, NOT BY BUILD NUMBER, BECAUSE THREE NUMBERS ARE CLAIMED TWICE

`claims` is a **reported fact about what each file calls itself** — it is not this table's key and nothing resolves through it. The filename is the identity, because a filename is unique by construction and a number in a heading is not.

| File in [`specs/`](specs/) | claims | Scoped | State |
|---|---|---|---|
| [`authoring-lint.md`](specs/authoring-lint.md) | 🚫 **none, deliberately** | 2026-10-09 | ✅ DECISION-COMPLETE, NOT YET BUILT · rulings 1–4 accepted 2026-10-09 (DL J32) · symptom scan on rendered HTML + 3 source checks → `authoring` (finding) + `authoring_notes` (inventory) buckets · born from the `uritp-docs` #205/#206 sweep |
| [`binder-type.md`](specs/binder-type.md) | 🚫 **none, deliberately** | 2026-10-11 | ⚠️ SCOPED, NOT GREENLIT · `type: binder` = a collection, split from `program` (a path) · reuses `chain:`, `binder:` flag retires · programs expand one level, sections as chain mappings, never touches prev/next · supersedes `print-compose.md` §6 P1/P2 once built · ⏳ owed: cross-site host (B11) + per-page classification (§6) |
| [`build-report.md`](specs/build-report.md) | BUILD 2 | 2026-08-06 | 🔴 **PARTLY SHIPPED** — Pieces A and C are live; B unverified |
| [`cards.md`](specs/cards.md) | 🚫 **none, deliberately** | 2026-09-28 | ✅ BUILT 2026-09-28 · live on the `uritp-docs` `app/` hubs |
| [`chrome.md`](specs/chrome.md) | BUILD 5 ⚠️ | 2026-08-18 | ⚠️ SCOPED, NOT GREENLIT |
| [`clickup-mirror.md`](specs/clickup-mirror.md) + [`-dl`](specs/clickup-mirror-dl.md) | 🚫 **none, deliberately** | 2026-10-11 | ⚠️ SCOPED, NOT GREENLIT · two directions: mirror from `/doc-index.json` every build (disposable, regenerated) + write-back as a **PR only, never `main`** · `id` refused unconditionally; blob-SHA drift refusal instead of last-write-wins · ✅ **R1–R5 RESOLVED 2026-10-11** · 🔴 **G7 added 2026-10-11: ClickUp `PageStatus`/`PageType` are NOT the engine's `status`/`type`** (2 of 5 and 1 of 18 values overlap), so `R4`'s allowlisted `status` would have written `status: draft` into files — mapping TSV per axis, write-back refuses an unmapped value, render degrades green · destination list named: `>REPO_PAGES` (36 rows, 18 fields, **not greenfield**) · 🔴 pilot = `template-docs`, 8 pass criteria, nothing runs on `uritp-docs` until all pass · third caller of `clickuppull.py` (`view-snapshot.md` §5) · DL `Q2`/`J5`/`J6` |
| [`cols.md`](specs/cols.md) | BUILD 7 ⚠️ | 2026-08-31 | ⚠️ SCOPED, NOT GREENLIT |
| [`contacts.md`](specs/contacts.md) | BUILD 11 | 2026-08-31 | ⚠️ SCOPED, NOT GREENLIT |
| [`dialect-clean.md`](specs/dialect-clean.md) | BUILD 1 | 2026-08-04 | ⚠️ SCOPED, NOT GREENLIT |
| [`draft-watermark.md`](specs/draft-watermark.md) | BUILD 4 ⚠️ | 2026-08-16 | ⚠️ SCOPED, NOT GREENLIT |
| [`flow-context.md`](specs/flow-context.md) + [`program-dl`](docrender/program-dl.md) | 🚫 **none, deliberately** | 2026-09-28 | ✅ BUILT 2026-09-28 · faces (`chain: "@id"`), one strip per page by `?via=`, footer auto-hide · `promote.py` deleted, `flow.css` split to embeds only |
| [`fmp-names.md`](specs/fmp-names.md) | 🚫 **none, deliberately** | 2026-10-11 | ✅ BUILT 2026-10-11 in [`docrender/fmpnames.py`](docrender/fmpnames.py) (#300) · hook `02b`, before `03_links` · drift lines to `notes` as `names:` · R1–R5 (DL J33) · ⏳ first real run = next `uritp-docs` publish (`uritp-budget/`) |
| [`hover-inline.md`](specs/hover-inline.md) | 🚫 **none, deliberately** | 2026-10-09 | ✅ BUILT 2026-10-10 in [`docrender/hoverspan.py`](docrender/hoverspan.py) · part 1 text spans + TSV cells (#287), part 2 external links + `@`/image refusals + R7 `title=` report (#288) · test page `uritp-docs` `REPO_PAGES/test-hover-inline.md` (unlisted) · ⏳ phone tap + part-2 print unverified |
| [`hover-text.md`](specs/hover-text.md) + [`-dl`](specs/hover-text-dl.md) | BUILD 9 | 2026-08-30 | ✅ DECISION-COMPLETE, NOT YET BUILT · ⚠️ **likely stale:** `assets/gloss.css` + `linklabels.py` ship the popup at HEAD (noted 2026-10-09, unverified) |
| [`layout-frame.md`](specs/layout-frame.md) | 🚫 **none, deliberately** | 2026-10-11 | ✅ DECISION-COMPLETE, NOT YET BUILT · R1–R4 accepted 2026-10-11 (DL J33) · `!!! layout` draws a FileMaker layout from its objects TSV (`area` + `parent` columns) · new `layout` page type · composes with `fmp-names.md` |
| [`print-control.md`](specs/print-control.md) + [`-dl`](specs/print-control-dl.md) | BUILD 8 | 2026-08-30 | ⭐ B (reader print menu) BUILT 2026-09-28 · A (per-page defaults) not built |
| [`print-identity.md`](specs/print-identity.md) | BUILD 5 ⚠️ | 2026-08-19 | ⭐ PARTLY SHIPPED |
| [`print-packet.md`](specs/print-packet.md) + [`-dl`](specs/print-packet-dl.md) | BUILD 10 | 2026-08-30 | ✅ BUILT |
| [`qr-codes.md`](specs/qr-codes.md) | BUILD 6 | 2026-08-21 | ⚠️ SCOPED, NOT GREENLIT |
| [`repo-onboarding.md`](specs/repo-onboarding.md) | 🚫 **none, deliberately** | — | ⚠️ not read this pass |
| [`scoped-theme.md`](specs/scoped-theme.md) | BUILD 3 | 2026-08-07 | ✅ report page SHIPPED 08-07 · ⭐ **page-level `theme:` BUILT 2026-09-28** in [`docrender/pagetheme.py`](docrender/pagetheme.py), by a DIFFERENT mechanism than the spec's §4 (read the module docstring, not §4, for how it works; §4 stays the price list for a shared-sheet version) · folder inheritance NOT built |
| [`sign-editor.md`](specs/sign-editor.md) | 🚫 **none, deliberately** | 2026-10-09 | ✅ DECISION-COMPLETE, NOT YET BUILT · R1–R8 accepted 2026-10-09 · §7.1 prototype BUILT (ClickUp artifact "Sign Lab") · ⏳ Michael's layout + paper test owed before engine code |
| [`sign-layout.md`](specs/sign-layout.md) | 🚫 **none, deliberately** | 2026-10-08 | ✅ BUILT 2026-10-08 in [`docrender/sign.py`](docrender/sign.py) · 2025 UR palette · 🔴 first page deleted by Michael 10-08 (layout too rigid); the type stays as `sign-editor.md`'s parent layer · ⏳ NOT paper-verified |
| [`tally.md`](specs/tally.md) | 🚫 **none, deliberately** | 2026-09-28 | ✅ BUILT 2026-09-28 · one live example (`uritp-docs` `app/app-box-office.md`) |
| [`view-embed.md`](specs/view-embed.md) | BUILD 7 ⚠️ | 2026-08-28 | ✅ SHIPPED 2026-08-30 |
| [`view-snapshot.md`](specs/view-snapshot.md) | 🚫 **none, deliberately** | 2026-10-06 | ⚠️ SCOPED, NOT GREENLIT · two spikes + four Michael rulings before code · ships `clickuppull.py`, which the report-renderer build reuses |
| [`visibility-split.md`](specs/visibility-split.md) | BUILD 4 ⚠️ | 2026-08-07 | ⚠️ not read this pass |

⚠️ **A `-dl` FILE IS A SIDECAR, NOT A BUILD.** It holds the arguments its spec points at, and it is listed beside its parent rather than on a row of its own.

### 🔴 The collisions, and the one that arrived after the warning was already written

**4** is `visibility-split.md` (08-07) and `draft-watermark.md` (08-16). **5** is `chrome.md` (08-18) and `print-identity.md` (08-19). **7** is `view-embed.md` (shipped 08-30) and `cols.md` (08-31).

⭐ **`repo-onboarding.md` DIAGNOSED THE FIRST TWO AND REFUSED TO TAKE A NUMBER AT ALL**, calling it *"a finding rather than a style choice"* and noting that taking one *"would be the third collision, not the first."* 🔴 **The third collision then happened anyway, in `cols.md`, one file over from the warning.** ⚑ *A comment cannot fire. Only a check can* — this repo's own line, and the index is where the check would have to live.

🚫 **NOTHING IS RENUMBERED HERE.** Every heading belongs to the file that wrote it, and rewriting somebody's H1 to tidy a table is a stance shift, not a cleanup. **The recommendation is that a spec should not carry a number at all** — the filename already identifies it, `roster.json` was retired for being a table simulated by prose, and this repo's standing rule is *names, never numbers.* That is Michael's call to make once, and until he makes it the `claims` column tells the truth about a mess instead of hiding it.

## What this index deliberately does NOT contain

🚫 **No per-build summary, no findings, no file tables.** The previous version reproduced a one-line summary and two or three findings per build, which is **a second claimant on every argument its specs already own** — the defect that retired `roster.json`, `registry.json` and `app-index.md`. It is also what pushed this file to **32,840 B, over the write cap**, so the index that holds the plans became the one file nobody could edit. Rows 7 through 11 went unwritten for that reason across five separate sessions, each one logging the debt and moving on.

🔴 **AND THE COPIES WENT STALE, WHICH IS THE ARGUMENT RATHER THAN THE TIDINESS.** The deleted BUILD 5 block stated that `assets.py` registers **five** print sheets and that `print-identity.css` *"does not exist, so the letterhead never landed."* At HEAD there are **nine `print-*.css` files on disk** and `print-identity.css` is **16,106 B**. `print-packet.md` had already corrected it to eight and 13,155 B, and **that correction is stale too.** ⚑ *Three claimants, three different numbers, none of them right.* **Read `docrender/assets.py` for the registered set and the directory for what is on disk. Never read a spec's file table, this file included.**

⚠️ **A STATE CELL IS THE SAME HAZARD AT SMALLER SCALE, PROVED ON THIS FILE 2026-10-11.** The `clickup-mirror.md` row read *"R1–R5 owed"* while the spec it points at had carried those rulings as RESOLVED since it was scoped, the same day. A state cell is a second claimant on a fact the spec owns. 🚫 It stays anyway, because an index with no state is a list of filenames — but **read the spec, not the cell, before acting on one.**

## ✅ What the index DOES own, because it belongs to no single spec

⚠️ **`build-report.md` (BUILD 2) → `scoped-theme.md` (BUILD 3): the only hard dependency.** BUILD 3's report page is a second caller of the renderer Piece C extracts into `report.py`. Building 3 first meant writing that renderer twice. ✅ **Piece C shipped first, exactly as recommended**, so this dependency is satisfied rather than pending.

⚠️ **Three soft couplings, none blocking, all real.**
1. `draft-watermark.md` §4 names `assets/print.css` as the home of the print DRAFT stamp and **the print split moved that target.** Whichever lands first fixes the other's pointer in the same PR.
2. `qr-codes.md` §5 ruling 6 adds a report bucket that lands in `sizecheck.py` or in `report.py` depending on where the report lives — ✅ **now decided by Piece C having shipped: it is `report.py`.**
3. The print leading change, the letterhead and the QR block are **three claimants on the vertical space of printed sheet one.** Whichever lands last re-previews the others.

⚠️ **`view-snapshot.md` → `clickup-mirror.md`: a shared module, not a dependency.** Both read ClickUp through `clickuppull.py`, which `view-snapshot.md` §5 ships. Whichever lands first writes it; the second one is a caller and adds no client of its own. 🚫 A second ClickUp client is a named road not taken in both files.

## 🅿 Standing debt

1. 🔴 **The numbering.** Named above. One ruling, then either every spec drops its number or a check enforces uniqueness. **Nothing else in this file can be trusted to stay true while two specs can share a name.**
2. **`_LABELS` matches in both `report.py` and `sizecheck.py`** at HEAD, which `build-report.md` forbade in bold. ⚠️ **That is a grep, not a finding** — read both before concluding.
3. **The `assets.py` split**, still named in `view-embed.md` §3 against a size that has since changed by 12 KB.
4. ⚠️ **The 22KB read ceiling has no check, and it bit twice in one session (2026-10-11).** `instances/uritp-safety/site.yml` reached 22,177 B and `specs/clickup-mirror.md` reached 24,765 B, both caught only because the write tool reports a size. A file past the ceiling cannot be read whole, and a file that cannot be read whole cannot be safely rewritten — which is how `util.py` lost `relative_url` and every build died on ImportError. `sizecheck.py` is the obvious home.
