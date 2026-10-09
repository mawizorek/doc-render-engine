# Sign editor — an in-page layout sandbox for `type: sign`

**State:** ✅ DECISION-COMPLETE, NOT YET BUILT · R1–R8 accepted 2026-10-09 (`sign_editor_accept_proto`) · ⏳ **§7.1 prototype BUILT, awaiting Michael's layout + paper test** · 🚫 no build number, deliberately (index numbering debt).
**Builds on:** [`sign-layout.md`](sign-layout.md) (BUILT 2026-10-08, `docrender/sign.py`). **Decision history:** doc-render-engine (repo) — Decision Log, ClickUp.

> Michael, 2026-10-08, after the first rendered backstage sign: *"That looked like shit, so I deleted it."* Then: embed DesignCraft's text editor *"on top of a sign layout sandbox… define a border and the logo while still having control over text placement, size or content."* Then: *"can it be part of a page defined as type sign? … defining a parent page."* Then: `sign_editor_spec`. 2026-10-09: all eight rulings accepted.

<p><br/></p>

## 🔴 §0 — Why v1 failed, stated so v2 does not repeat it

`type: sign` v1 **owned the layout**: headings flowed down a column at fixed source-PDF sizes. The author could change the words and nothing else. That is the InDesign problem in reverse: a template you cannot nudge. **The fix is not better defaults. It is giving placement back to the author** while the engine keeps the parts that should never be hand-made (frame, logo, sheet geometry, print behaviour).

The `uritp-docs` page `sign-backstage-access` was deleted by Michael. The engine type, `frames.tsv` and the sheet card all stay: they become this editor's parent layer.

<p><br/></p>

## 🔎 §1 — DesignCraft, read at source (storytold/designcraft @ 14e677b)

[DesignCraft](https://github.com/storytold/designcraft) is an MIT / Apache-2.0, pure-Rust, clean-room InDesign. Checked before anything was proposed:

- 🚫 **Its text editor cannot be lifted out.** The UI is egui: every panel and the text cursor are PAINTED onto one canvas by Rust, so there is no DOM component to embed. Taking it means taking the whole WebAssembly app.
- 🚫 **The web build has no control channel** (README: *"The web build has no control channel"*). A page cannot drive it, feed it a template or read its result.
- ⚠️ **PNG export only;** PDF is roadmap (the README says roadmap; the marketing site says "print-ready PDF" — the README wins). A sign printed from a PNG is a raster sign.
- ✅ **Layers** (`crates/engine/src/cmd/layout.rs`, `crates/ui-egui/src/panels/layers.rs`): `layer.set` takes `name, visible, locked, printable, color` (Layer Options…), plus delete, merge, move-selection-here, hide/lock others, delete unused; per-object eye + lock. 🚫 **No layer reorder command and no drag in the panel.**
- ⭐ **What is worth taking is the MODEL:** the *parent page* (locked art every page inherits) and *named layers with lock / hide / print flags*. Taken as ideas, not code.

<p><br/></p>

## ✍️ §2 — The authoring shape

The page IS the layout. Everything the editor changes is written back as frontmatter, so the published page, the printed sheet and the repo are one fact.

```
---
id: sign-backstage-access
title: Sign - Backstage Access
type: sign
frame: uritp              # parent layer: the frame row in frames.tsv
sheet: letter             # R6
logo: {img: logo-horizontal, y: 35, w: 431}     # parent layer; pt on the sheet
layers:
  - {name: Text}
  - {name: Notes, printable: false}
blocks:
  - {id: kicker, layer: Text, text: "Please note\nRestricted access",
     x: 51, y: 223, w: 510, size: 36, weight: 600, align: center, case: upper, leading: 52}
  - {id: message, layer: Text, text: "Cast and crew only",
     x: 51, y: 381, w: 510, size: 72, weight: 400, align: center, case: upper, leading: 86}
status: public
summary: Backstage door sign, cast and crew only.
---
```

- **Units are sheet points** (Letter = 612 × 792), the same `--u` that v1 already scales to the printable box. So a block placed on screen lands on paper at the same place, at any browser margin.
- **Parent layer = `frame:` + `logo:`**, drawn by the engine, locked by default. Unlockable in the editor to move/resize the logo; never hand-drawn.
- **No `blocks:` → v1 behaviour** (headings flow). Nothing already published changes; `sign-content-disclosure` keeps working.
- `case: upper` is CSS, so the stored text stays sentence case (v1 rule, kept).
- ⚠️ The prototype's Copy layout emits the authoritative shape (adds `x` on `logo:`, `tracking`, `font`, `ink`, and layers top-of-stack first). Where it differs from the sketch above, **the prototype output wins** once Michael signs off a layout.

<p><br/></p>

## ⚙️ §3 — What the editor does (v1)

Opened by **Edit sign** on the page (R2). Screen only; never prints.

1. **Canvas:** the sheet card at real proportion, parent layer locked underneath, blocks absolutely positioned on top.
2. **Blocks:** click to select, drag to move, side handles to resize width, double-click to edit text in place (plain text only: paste is stripped). Arrow = 1 pt nudge, Shift+arrow = 10 pt. Add / duplicate / delete block.
3. **Snapping:** sheet centre line, field edges (inside the inner frame band), other blocks' edges and centres. Hold Alt to ignore snaps.
4. **Type controls** (selected block): size (pt), weight, align, case, leading, tracking, colour from the frame row + ink. Fonts limited by R5.
5. **Layers panel:** rename, **drag to reorder** (what DesignCraft lacks), lock, hide, printable, move selection to layer. Parent layer pinned at the bottom.
6. **Undo / redo** in memory; **draft autosave** to the browser per page `id`, so a refresh loses nothing.
7. **Copy layout** → the `layers:` + `blocks:` (+ `logo:` if moved) YAML on the clipboard (R3).
8. **Print from the editor** prints the CURRENT state, guides and handles hidden (R4).

<p><br/></p>

## 🧩 §4 — Mechanism

- **`docrender/sign.py` grows a blocks renderer:** frontmatter → absolutely positioned elements inside `.dr-sign__f3`, all lengths in `--u`. Read mode needs no JavaScript at all: a sign prints correctly with scripts off.
- **The editor is one script, `docrender/signedit.js`, inlined by `sign.py` on sign pages only** (R7). Same page-scoped precedent as the sign CSS; `assets.py` stays untouched (past its read ceiling).
- **The page carries its own state** as a JSON island (`<script type="application/json" id="dr-sign-state">`) built from frontmatter, so the editor never re-parses HTML.
- **No write-back.** A static site cannot commit. That is the honest limit and it is the whole of R3.

<p><br/></p>

## ⚖️ §5 — Rulings (all eight accepted, Michael, 2026-10-09)

| # | Question | ✅ Ruled | Why |
|---|---|---|---|
| R1 | Embed DesignCraft vs own editor | **Own editor, DesignCraft's model** | §1: not embeddable, no control channel, raster output |
| R2 | Who sees **Edit sign** | **Only with `?edit` in the URL** | Public site; a reader at the door should see a sign, not a toolbar. Not security, just clutter |
| R3 | Saving | **Copy layout → paste into frontmatter, or hand to Brain to commit** | No token on a public page (same blocker as `view-snapshot.md`). Direct GitHub write is a later build |
| R4 | Print from the editor | **Prints the live draft** | The test loop is print, look, nudge. Forcing a save first doubles every iteration |
| R5 | Fonts | **Source Serif 4 + the site's typography row** (Manrope / Archivo) | Bounded set = no Google Fonts 400 risk; everything already loaded on the page |
| R6 | Sheet sizes | **`letter` now; `sheets.tsv` (slug · w · h pt) so tags are a row, not code** | Tags were the second ask; the data shape should not need a rewrite for them |
| R7 | Editor JS home | **Inlined by `sign.py`, sign pages only** | `assets.py` split is standing debt; only sign pages pay the bytes (~15–20 KB est.) |
| R8 | Touch / phone editing | **Desktop-first; phone views and prints, edits best-effort** | Drag + handles on a 6" screen is a different design |

<p><br/></p>

## 💣 §6 — Risks and edge cases

- 🔴 **Overflow is now the author's to see, not the engine's to prevent:** a block whose text outruns its box shows a red edge in the editor and is reported at build if `blocks:` text is long for its `w` × `size` (estimate only, flagged as such).
- ⚠️ **Frontmatter grows.** A busy sign is ~20 lines of YAML. Acceptable; it is the price of the page being the layout. Flow-style `{}` rows keep it scannable.
- ⚠️ **Draft vs page drift:** a browser draft newer than the page shows a banner (*"unsaved draft from …"*) with Restore / Discard. Never silently applied.
- ⚠️ **Paper is still unproven** for v1's scaling; every paper test of this editor also tests that. Chrome + Safari, Letter, "Headers and footers" off, "Background graphics" on.
- ⚠️ **`sign-content-disclosure`** (body paragraphs, italic show title) must convert cleanly to blocks: it is the second test page.
- 🚫 **Not a general page builder.** Blocks exist on `type: sign` only.

<p><br/></p>

## ✅ §7 — Proof, cheapest first

1. ✅ **BUILT 2026-10-09: the Sign Lab prototype** (ClickUp artifact "Sign Lab", no engine): locked parent (frame at the source PDF's measured bands, 2025 UR palette, logo), draggable / resizable text blocks with snapping, layers panel (rename, drag reorder, hide, lock, non-printing), inspector, undo / redo, browser draft autosave, Copy layout, Letter print of the sheet only. Verified on screen in a headless browser (select, snapped drag, off-field warning, YAML export). ⏳ **Owed: Michael lays out the backstage sign himself and prints it. Pass = he would hang it.** ⚠️ Printing from inside ClickUp's artifact frame is itself untested; if it misbehaves, that is the frame, and the engine page will not have it.
2. ✅ Rulings R1–R8.
3. Engine: blocks renderer in `sign.py`, `signedit.js`, `sheets.tsv`; rebuild `sign-backstage-access` from the YAML Michael copied in step 1.

<p><br/></p>

## 🚫 §8 — Not in scope

Direct commit from the page · images other than the logo · IDML / DesignCraft file import · multi-page signs · rotation · QR blocks (see `qr-codes.md`) · A4.
