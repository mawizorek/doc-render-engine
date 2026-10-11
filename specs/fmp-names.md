# `@fmp:` — a FileMaker name written once, rendered everywhere

✅ **BUILT 2026-10-11** in [`docrender/fmpnames.py`](../docrender/fmpnames.py) via [`hooks/02b_fmpnames.py`](../hooks/02b_fmpnames.py) (#300, tests in `tests/test_fmpnames.py`). ⏳ **Not yet run on a real `uritp-docs` publish.** R1–R5 accepted as recommended 2026-10-11 (DL J33). Indexed from `next-build-spec.md`. Born on the URITP Budget notes build (`uritp-docs` `uritp-budget/`), session task in ClickUp: *Dexter + Fiona ↔ Frank · FileMaker XML → compact app-state render*.

> Michael, 2026-10-11 (paraphrased): an update to schema or field names must not scatter through too many notes.

---

## The problem, measured

FileMaker notes spell object names in prose: `[fkCal](@rel:table-events)`, `` `BudgetCode_YearConfig` ``. The **target** of a link is a stable page id; the **label** is a spelling. A rename leaves every label wrong and nothing reports it.

- `@alias:` already exists (`theme/markers.tsv`) and points a RETIRED name at the live page. It fixes paperwork quoting an old name. It does not fix the prose.
- `{.field}` has no prefix, so `@field:` links in `production-mawster` resolve to nothing today (`@field:table-global-use-variables#g_pkCurrentProduction` in `50-LAYOUTS/LAYOUTS.tsv`).
- A FileMaker rename pass is a real, recurring event: `URITP Budget` has one pending across 31 tables (`uritp-budget/NAMES.tsv`).

## The shape

A per-app **names catalog** owns every spelling. Prose cites a key; the engine writes the name.

```
uritp-budget/NAMES.tsv
key            kind   current                  proposed               status   page
t.yearconfig   table  BudgetCode_YearConfig    BudgetCodeYearConfigs  rename
t.alloc        table  Budget_Allocation        BudgetAllocations      rename   table-budget-alloc
```

```
Every money row points at [](@fmp:t.yearconfig).
```

renders as `BudgetCode_YearConfig`, in the `schema` marker class, linked to `page` when the row has one, and recorded as an edge in `/doc-refs.json`.

### Resolution

1. **Nearest-ancestor catalog.** Walk up from the page's folder to the first `NAMES.tsv`. One file per app, no instance config, no cross-app bleed.
2. **Empty label → `current`.** A written label is kept verbatim (the author meant those words) and reported if it doesn't match `current` or `proposed`.
3. **`kind` picks the marker class** from existing rows: `table`/`field`/`calc`/`rel`/`script`/`vl`/`layout`. No new class.
4. **`status`:** `retire` renders struck (`was` shape) and reports; `new` renders `tbc`; `open` renders plain and reports once per page.
5. **Anchor passes through:** `@fmp:t.alloc#grain` → `page#grain`.
6. **Dead key** → the standard broken-reference span + `dead_links` line. Never a fallback to plain text.

### Piece B — the drift check (same module, report only)

On every page under a catalog, scan prose and code spans for any `current` or retired spelling written **outside** an `@fmp:` reference. One `names` report line per hit: *"`Budget_Codes_Defintions` is spelled out in 50-LAYOUTS/h-budget-hub.md; cite `@fmp:t.codes`."*

That turns "search the folder for the old name" into a list the build hands you. It also makes migration incremental: existing pages keep working and get a to-do list.

## Rulings (all accepted as recommended, 2026-10-11, DL J33)

| # | Question | Ruled |
|---|---|---|
| R1 | Prefix word | **`@fmp:`**. `@name:` is generic enough to collide with a future non-FileMaker use. |
| R2 | Catalog location | **Nearest ancestor `NAMES.tsv`**, filename fixed. |
| R3 | Fields in the catalog | **Only when cited.** STATE.md already lists all of them; mirroring 384 rows is the second-claimant defect. |
| R4 | Key grammar | **`<kind letter>.<slug>`**, fields as `f.<table-slug>.<field-slug>`. Keys never change; renames edit `current`. |
| R5 | Which name renders during a pending rename | **`current`** until the DDR proves the rename, then swap `proposed` into `current`. The DELTA is the trigger, not the author. |

## Build notes

- New module `docrender/fmpnames.py`, claims `@fmp:` at import with `anchors=True, opts=True` (prefixes.py ladder).
- Reads catalogs in `on_files`, never at import (prefixes.py timing rule).
- `markers.py` is at the size ceiling: import `table()` and `LINK_CLASS` only, same seam `markerlinks.py` uses.
- Nothing here can fail a build.

### ⚠️ As built, where it differs from the text above (the code wins)

1. **Hook slot is `02b`, before `03_links`, not after `03c_markerlinks`.** The drift scan has to see raw markdown, before link rewriting turns `@fmp:` refs into HTML and hides what was hand-spelled. Resolution still goes through the shared prefix ladder, so order does not change what renders.
2. **Drift lines land in the existing `notes` bucket, prefixed `names:`**, not a new `names` bucket. A new bucket costs edits in both `state.reset` and `report._LABELS`; one prefix costs neither. Promote it when the line count justifies its own heading.
3. **`kind` is inferred from the key letter** (`t f c r s l v g`) when the column is blank; a written `kind` that disagrees with the letter is reported.
4. **`new` renders soft and shows `proposed`** (the name being introduced), rather than the bare `tbc` shape.
5. ⚠️ **Known gap, unguarded:** a key whose last segment is a data/image suffix (e.g. `f.x.md`) is refused by `links.py`'s token rule before this module sees it. Don't key that way.

## 🅿️ Futures

- Fill `current` from `fmp-state/<app>/fingerprints.json` by FileMaker object id, so a rename in the file renames the notes with zero edits.
- A `kind` column hover: field type and calc formula pulled from STATE.
