# doc-render-engine — the build index

**This file is an INDEX and nothing else.** Every build's plan lives in its own file under [`specs/`](specs/). Decision history for all of them: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

🚫 **NO COUNT IS WRITTEN HERE, AND THAT IS THIS FILE'S OWN INSTRUCTION BEING OBEYED.** The previous version opened *"SIX INDEPENDENT BUILDS ARE INDEXED HERE"* above a hand-kept table, went stale the first time a spec was added without touching the sentence, and said in bold: *"if it is wrong again, delete it rather than refresh it."* It was wrong again — by five rows. **A sentence and a list are two places stating one fact, and the list is the one that gets edited.** Count the rows.

## 🔴 ROWS ARE KEYED BY FILE, NOT BY BUILD NUMBER, BECAUSE THREE NUMBERS ARE CLAIMED TWICE

`claims` is a **reported fact about what each file calls itself** — it is not this table's key and nothing resolves through it. The filename is the identity, because a filename is unique by construction and a number in a heading is not.

| File in [`specs/`](specs/) | claims | Scoped | State |
|---|---|---|---|
| [`build-report.md`](specs/build-report.md) | BUILD 2 | 2026-08-06 | 🔴 **PARTLY SHIPPED** — Pieces A and C are live; B unverified |
| [`chrome.md`](specs/chrome.md) | BUILD 5 ⚠️ | 2026-08-18 | ⚠️ SCOPED, NOT GREENLIT |
| [`cols.md`](specs/cols.md) | BUILD 7 ⚠️ | 2026-08-31 | ⚠️ SCOPED, NOT GREENLIT |
| [`contacts.md`](specs/contacts.md) | BUILD 11 | 2026-08-31 | ⚠️ SCOPED, NOT GREENLIT |
| [`dialect-clean.md`](specs/dialect-clean.md) | BUILD 1 | 2026-08-04 | ⚠️ SCOPED, NOT GREENLIT |
| [`draft-watermark.md`](specs/draft-watermark.md) | BUILD 4 ⚠️ | 2026-08-16 | ⚠️ SCOPED, NOT GREENLIT |
| [`hover-text.md`](specs/hover-text.md) + [`-dl`](specs/hover-text-dl.md) | BUILD 9 | 2026-08-30 | ✅ DECISION-COMPLETE, NOT YET BUILT |
| [`print-control.md`](specs/print-control.md) | BUILD 8 | 2026-08-30 | ⚠️ SCOPED, NOT GREENLIT |
| [`print-identity.md`](specs/print-identity.md) | BUILD 5 ⚠️ | 2026-08-19 | ⭐ PARTLY SHIPPED |
| [`print-packet.md`](specs/print-packet.md) + [`-dl`](specs/print-packet-dl.md) | BUILD 10 | 2026-08-30 | ✅ BUILT |
| [`qr-codes.md`](specs/qr-codes.md) | BUILD 6 | 2026-08-21 | ⚠️ SCOPED, NOT GREENLIT |
| [`repo-onboarding.md`](specs/repo-onboarding.md) | 🚫 **none, deliberately** | — | ⚠️ not read this pass |
| [`scoped-theme.md`](specs/scoped-theme.md) | BUILD 3 | 2026-08-07 | ⚠️ its own rulings table reads CLOSED — state needs confirming |
| [`view-embed.md`](specs/view-embed.md) | BUILD 7 ⚠️ | 2026-08-28 | ✅ SHIPPED 2026-08-30 |
| [`visibility-split.md`](specs/visibility-split.md) | BUILD 4 ⚠️ | 2026-08-07 | ⚠️ not read this pass |

⚠️ **A `-dl` FILE IS A SIDECAR, NOT A BUILD.** It holds the arguments its spec points at, and it is listed beside its parent rather than on a row of its own.

### 🔴 The collisions, and the one that arrived after the warning was already written

**4** is `visibility-split.md` (08-07) and `draft-watermark.md` (08-16). **5** is `chrome.md` (08-18) and `print-identity.md` (08-19). **7** is `view-embed.md` (shipped 08-30) and `cols.md` (08-31).

⭐ **`repo-onboarding.md` DIAGNOSED THE FIRST TWO AND REFUSED TO TAKE A NUMBER AT ALL**, calling it *"a finding rather than a style choice"* and noting that taking one *"would be the third collision, not the first."* 🔴 **The third collision then happened anyway, in `cols.md`, one file over from the warning.** ⚑ *A comment cannot fire. Only a check can* — this repo's own line, and the index is where the check would have to live.

🚫 **NOTHING IS RENUMBERED HERE.** Every heading belongs to the file that wrote it, and rewriting somebody's H1 to tidy a table is a stance shift, not a cleanup. **The recommendation is that a spec should not carry a number at all** — the filename already identifies it, `roster.json` was retired for being a table simulated by prose, and this repo's standing rule is *names, never numbers.* That is Michael's call to make once, and until he makes it the `claims` column tells the truth about a mess instead of hiding it.

## What this index deliberately does NOT contain

🚫 **No per-build summary, no findings, no file tables.** The previous version reproduced a one-line summary and two or three findings per build, which is **a second claimant on every argument its specs already own** — the defect that retired `roster.json`, `registry.json` and `app-index.md`. It is also what pushed this file to **32,840 B, over the write cap**, so the index that holds the plans became the one file nobody could edit. Rows 7 through 11 went unwritten for that reason across five separate sessions, each one logging the debt and moving on.

🔴 **AND THE COPIES WENT STALE, WHICH IS THE ARGUMENT RATHER THAN THE TIDINESS.** The deleted BUILD 5 block stated that `assets.py` registers **five** print sheets and that `print-identity.css` *"does not exist, so the letterhead never landed."* At HEAD there are **nine `print-*.css` files on disk** and `print-identity.css` is **16,106 B**. `print-packet.md` had already corrected it to eight and 13,155 B, and **that correction is stale too.** ⚑ *Three claimants, three different numbers, none of them right.* **Read `docrender/assets.py` for the registered set and the directory for what is on disk. Never read a spec's file table, this file included.**

## ✅ What the index DOES own, because it belongs to no single spec

⚠️ **`build-report.md` (BUILD 2) → `scoped-theme.md` (BUILD 3): the only hard dependency.** BUILD 3's report page is a second caller of the renderer Piece C extracts into `report.py`. Building 3 first meant writing that renderer twice. ✅ **Piece C shipped first, exactly as recommended**, so this dependency is satisfied rather than pending.

⚠️ **Three soft couplings, none blocking, all real.**
1. `draft-watermark.md` §4 names `assets/print.css` as the home of the print DRAFT stamp and **the print split moved that target.** Whichever lands first fixes the other's pointer in the same PR.
2. `qr-codes.md` §5 ruling 6 adds a report bucket that lands in `sizecheck.py` or in `report.py` depending on where the report lives — ✅ **now decided by Piece C having shipped: it is `report.py`.**
3. The print leading change, the letterhead and the QR block are **three claimants on the vertical space of printed sheet one.** Whichever lands last re-previews the others.

## 🅿️ Standing debt

1. 🔴 **The numbering.** Named above. One ruling, then either every spec drops its number or a check enforces uniqueness. **Nothing else in this file can be trusted to stay true while two specs can share a name.**
2. **`_LABELS` matches in both `report.py` and `sizecheck.py`** at HEAD, which `build-report.md` forbade in bold. ⚠️ **That is a grep, not a finding** — read both before concluding.
3. **The `assets.py` split**, still named in `view-embed.md` §3 against a size that has since changed by 12 KB.
