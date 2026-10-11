# `!!! layout` — draw a FileMaker layout from its objects catalog

✅ **DECISION-COMPLETE, NOT YET BUILT.** R1–R4 accepted as recommended 2026-10-11 (DL J33). Indexed from `next-build-spec.md`. Same origin as `fmp-names.md`.

> Michael, 2026-10-11: *"If this is how you want to communicate schemas to me, we have to build our renderer to create them rather than providing loose collections of artifacts."*

---

## The problem

`uritp-docs` `uritp-budget/50-LAYOUTS/h-budget-hub.md` carries a 100-column hand-drawn box diagram **and** an objects TSV that says the same thing. The TSV is the truth; the drawing is a second claimant that took two commits to get the border width right. And there is no `layout` page type, so that page is filed as `reference`.

## The shape

The page declares a grid once. Each object row names its area.

```
---
type: layout
data:
  objects:
    file: h-budget-hub.objects.tsv
---

!!! layout objects
    header: title fy version import
    body:   t1 t2 t3 t4
    body:   codes codes work work
    footer: foot
```

Each `header:` / `body:` / `footer:` line is one grid row in that part. Area names are free words; a name repeated across columns spans them (`grid-template-areas` semantics).

### New catalog columns (added to the objects TSV, nothing else changes)

| column | meaning |
|---|---|
| `area` | which grid area the object sits in. Several objects in one area stack in row order. |
| `parent` | the `#` of a containing object (portal cells under their portal, cells under a card). Rendered nested. |

### What draws

- **Layout-mode look, neutral by default:** dashed boxes, the family name as a corner tag, `source` as the box text (`[field]`, `<<merge>>`, `(button)` conventions), part bands labelled HEADER / BODY / FOOTER.
- **Behaviour on hover**, through the existing `hoverspan` mechanism, never `title=`.
- **Family checked against the Canonical Object Library.** A family not in `maw-themes` `vocabulary/_objects.json` draws with a `gap` marker and one report line. That's the "0 new families" claim, verified by the build instead of asserted by the author.
- **Below the frame, the catalog table**, unchanged, through the existing `!!! data` path.
- **Print:** frame on its own sheet, landscape.

### `objects/layout.yml`

New page type with `data_slots: [objects]`. Side effect, free: the `layout` marker's name now matches a type, so `markerlinks.py`'s type check switches on for `@layout:` links without a code change.

## Rulings (all accepted as recommended, 2026-10-11, DL J33)

| # | Question | Ruled |
|---|---|---|
| R1 | Neutral wireframe or painted in the layout's theme | **Neutral in v1.** Painting means resolving FMP theme vectors into page CSS, and that's `scoped-theme.md` territory. |
| R2 | Geometry | **Areas only, no pixel coordinates.** The DDR has no geometry (STATE says so); inventing coordinates would be a claim the file can't back. |
| R3 | Where the family vocabulary is read from | **`maw-themes` `_objects.json` vendored at build** (same as the theme vectors), not fetched live. |
| R4 | Retire the hand-drawn block | **Yes, the same PR that ships the directive**, on the one page that has it. |

## Build notes

- New module `docrender/layoutframe.py` plus `assets/layout-frame.css`, shipped once per page that draws a frame (the `cards.py` pattern). `chrome.py` and `assets.py` stay untouched.
- Reuses `datatable.py`'s TSV reader; does not edit it (over the safe-edit ceiling).
- Composes with `fmp-names.md`: a `source` cell may carry `@fmp:` keys and they resolve inside the box.

## 🅿️ Futures

- Pull real geometry if Michael ever drops a Save-as-XML with layout bounds (rejected today for credentials).
- Click a box → jump to its catalog row.
- Theme-painted mode once `scoped-theme.md` folder inheritance exists.
