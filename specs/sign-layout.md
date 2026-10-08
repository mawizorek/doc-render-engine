# Sign layout — `type: sign`

**State:** ✅ BUILT 2026-10-08 · `docrender/sign.py` + `objects/sign.yml` + `theme/canonical/frames.tsv`, first page `uritp-docs` `sign-backstage-access` · 🚫 no build number, deliberately (see the index's numbering debt). ⏳ **NOT paper-verified: §7 step 1 (Chrome + Safari on Letter) is still owed.**
**Decision history:** doc-render-engine (repo) — Decision Log, ClickUp.

> Michael, 2026-10-08, handing over `CAST AND CREW ONLY.pdf`: *"what we're aiming to replace...."* Then: spec it first. Then: **all seven recommendations accepted** (`sign_accept_all`). Then: *"update to the new color pallete and ship the spec."* Built ahead of the paper test on that instruction.

The goal is to retire hand-laid sign files (InDesign-style PDFs) in favour of **rendered pages that print as the sign.** First customer: `uritp-docs` `REPO_PAGES/sign-backstage-access.md`. Second, already live and different in shape: `REPO_PAGES/sign-content-disclosure.md` (body paragraphs, an italic show title).

### 🛠️ As built (read `docrender/sign.py` docstring for the authority)

- The sheet is a card at `aspect-ratio: 8.5 / 11`, with every length in `--u = 100cqi / 612` (one source pt, scaled to the card's width; fallback `1pt` where container queries are absent). 🔴 **This is the §6 `@page` answer:** the sheet scales to whatever printable box the browser gives it instead of assuming the full 8.5 × 11 in, so it cannot spill onto a second page.
- In print only `.dr-sign` is shown and the `@page` margin boxes are cleared (R5). The screen header and the print menu stay.
- Frame colours read from `frames.tsv` by `frame:` slug, live vs vendored per `source.tsv`. Source Serif 4 linked on sign pages only (R4).
- Composed in the existing `06_pagefoot` shim (no `mkdocs.yml` registration, no `assets.py` sheet).

<p><br/></p>

## 📏 §1 — The target, MEASURED from the source PDF (not eyeballed)

Read with `pdfplumber` off the file Michael attached. US Letter, **612 × 792 pt**, one page.

**The frame is four nested rectangles**, not strokes:

| Band | CMYK (as authored) | naive sRGB | Outer box (x, y, w × h pt) | Band width |
|---|---|---|---|---|
| Red | 0.4 / 99.2 / 97.3 / 14 | `#DA0206` | 17, 21, 579 × 749 | ~13 pt sides · ~11 pt top |
| Navy | 100 / 57 / 0 / 38 | `#00449E` | 30, 32, 553 × 727 | ~13 pt · ~11 pt |
| Yellow | 0 / 10.2 / 100 / 0 | `#FFE500` | 43, 43, 527 × 705 | ~8 pt |
| White field | 0 / 0 / 0 / 0 | `#FFFFFF` | 51, 51, 510 × 690 | — |

**Layout** (top edge of each element, pt from the top of the sheet): logo 86 (431 pt wide, centred) · kicker lines 274 and 326 · message lines 432 and 518.

**Type**, by font name embedded in the PDF:

| Text | Face | Size |
|---|---|---|
| PLEASE NOTE · ACCESS RESTRICTED | **Source Serif 4 Semibold** | **36 pt**, both lines the SAME size |
| CAST AND / CREW ONLY | **Source Serif 4 Regular** | **72 pt**, wraps to two lines |

⭐ Source Serif 4 is an open Google Font, so the source's own face is available to the engine with no licence question. 🚫 **No serif exists anywhere in `maw-themes` `vectors/typography.tsv` today** (every row is sans), so this is a new family either way.

**Three things in the source that are NOT the design:**

- 🔴 **A hidden layer.** 244 characters of Adobe Caslon Pro 18 pt sit *under* the sign: the content-disclosure list (loud sounds, gunshots, smoke, strobe, nudity…). The source file stacks two signs. That text belongs to `sign-content-disclosure`, never to this page.
- The source reads **"RESTRICED"** (typo) and orders it **"Access Restricted"**; the live page says "Restricted Access". Author's call, not the engine's.
- The logo is the existing `91-media-logos/logo-horizontal.jpg`, centred at the top. Already reachable as `@img:logo-horizontal`.

<p><br/></p>

## ✍️ §2 — The authoring shape this spec is aiming at

```
---
id: sign-backstage-access
title: Sign - Backstage Access
type: sign
frame: uritp
---

![URITP](@img:logo-horizontal)

## Please Note
## Access Restricted

# Cast and Crew Only
```

⭐ **Everything the page fights for today, the type owns.** No `{.align-center}` on every line, no `hide:` list, no capitals typed by hand, no print-panel clicks. A sign author writes the words.

- `h2` = **kicker** (36 pt semibold, caps). Any number of them, all one size, which is the hierarchy the source actually uses.
- `h1` = **the message** (72 pt regular, caps).
- `p` = body copy for a disclosure-style sign (~18 pt), sentence case kept.
- Capitals by `text-transform`, **headings only**. The source text stays sentence case, so it reads and searches normally.

<p><br/></p>

## ⚙️ §3 — What `type: sign` draws

1. **One sheet.** Letter portrait. The frame fills the printable area; content sits inside it at the §1 positions with the logo pinned to the top.
2. **The frame**, as nested BORDERS, never backgrounds. ⚠️ Browsers drop background colour on print by default; borders print. Plus `print-color-adjust: exact` on the frame, the precedent `qr.css` and the `!!! danger` border already use.
3. **Print furniture off**: letterhead, revised / posted-by, page numbers. A sign is not a document. 🔴 **The SCREEN header and the print menu stay** — the lesson of PR #277, where hiding the header from frontmatter took the print menu with it.
4. **On screen, a sheet-shaped card**: the framed page at `aspect-ratio: 8.5 / 11`, forced light inside the card even in dark mode, because it is paper. What you see is the sign you print.

<p><br/></p>

## 🧩 §4 — Mechanism, and why each piece sits where it does

- ✅ **A real type: `objects/sign.yml`.** `page.yml`'s own rule: *"A type earns its existence by having fields or a way of drawing."* A sign has a way of drawing and one field (`frame:`). Not a `chrome:` value: `chrome:` is about the site's skin around a page, and a sign changes the page itself.
- ✅ **CSS injected page-scoped**, on the `chrome.py` precedent (a `<style>` only the asking page pays for). 🔴 **Not a registered sheet:** `docrender/assets.py` is past the read ceiling and its split is standing debt in the index. A new registered asset would block on that split.
- ✅ **The font: page-scoped** (R4). `docrender/fonts.py` (stage 04c) fetches the families an INSTANCE's typography row names; Source Serif 4 is fetched beside the injected CSS on sign pages only, and no typography row changes.
- ✅ **The frame palette: `maw-themes` `vectors/frames.tsv`** (R3) — `slug · band colours · band widths`, so `frame: uritp` is a NAME. 🚫 **Not new columns in `colors.tsv`**: those are theme-wide properties across ~60 rows, and a frame is not a property of a theme.

<p><br/></p>

## ⚖️ §5 — Rulings (all seven recommendations accepted, Michael, 2026-10-08)

| # | Question | ✅ Ruled |
|---|---|---|
| R1 | `type: sign` vs `chrome: sign` vs a class | **`type: sign`** (§4) |
| R2 | Frame colours: brand guide vs the sampled ones | **Brand guide first, sampled as the fallback** — resolved below |
| R3 | Frame home | **`maw-themes` `vectors/frames.tsv`** |
| R4 | Source Serif 4 | **Page-scoped, sign pages only** |
| R5 | Print furniture on signs | **Forced off.** Default-off-with-override would need print-control.md Part A (not built) |
| R6 | Paper sizes | **Letter only** |
| R7 | Screen view | **Framed sheet card** (§3.4) |

### 🔴 R2, resolved — and the source PDF turned out to be on the OLD palette

Checked 2026-10-08 against the University of Rochester Brand Center ([color system](https://brand.rochester.edu/visual-identity/color-system/)) and the archived 2010 graphic standards.

- **The source PDF's navy (CMYK 100/57/0/38) and yellow (0/10/100/0) are EXACTLY the legacy 2010 palette:** PMS 541 (`#00467F`) and PMS 109 (`#FFDD00`). The sign was made to a standard UR has since replaced.
- **The current brand (refreshed Oct 2025):** **URochester Navy `#001E5F`** (PMS 2748 C) and **Dandelion Yellow `#FFD82B`** (PMS Yellow C). Under R2 these WIN.
- 🔴 **The red is NOT a UR brand colour** — neither palette carries it. It is the URITP logo's "theatre" red. So the fallback applies: **sampled `#DA0206`**, owned by URITP, not UR.
- ⚠️ Consequence, stated so it is not a surprise on paper: the rendered sign's navy is **darker** than the old printed one. That is the brand moving, not the engine drifting.

```
frames.tsv row (shipped, maw-themes #17):  uritp · #DA0206 13pt · #001E5F 13pt · #FFD82B 8pt
```

<p><br/></p>

## 💣 §6 — Risks and edge cases, stated before anything is built

- 🔴 **`@page` margins are browser-dependent** (`printctl.js` header says so plainly). If a browser ignores `@page`, a frame sized to the sheet spills onto a SECOND sheet, and a two-page sign is a failed sign. The frame must be sized against the content box with an honest fallback, and **only a paper test settles it.** ✅ Built answer: the container-unit scaling above. ⏳ Still only paper settles it.
- ⚠️ **The browser's own "Headers and footers"** will print a URL and date over the frame unless unticked. The print panel already tells readers; a sign page should say it louder.
- ⚠️ **`print-flow.css`'s `display: revert !important`** has beaten plain display rules in this family twice. Any hide rule here carries `!important` from the start.
- ⚠️ **Overflow cannot be detected at build time.** At 72 pt on a ~7 in measure a line holds roughly 12-13 capitals, which "CAST AND / CREW ONLY" fits and a longer message will not. Honest limit: the print panel's text-size dial already scales a sign down. 🚫 No auto-fit script in v1.
- ⚠️ **The content-disclosure sign** has an italic `h2` show title and two paragraphs. It must fit the same frame. It is the second test page, not an afterthought.
- ⚠️ **The `{.align-center}` work from today** (align.css) becomes unnecessary on sign pages. It stays correct everywhere else; nothing is removed.

<p><br/></p>

## ✅ §7 — Pre-build proof, cheapest first

1. ⏳ **A hand-built HTML sheet, before any engine code.** ✅ BUILT 2026-10-08 as a standalone file (logo extracted from the source PDF, R2 colours, Source Serif 4 from Google Fonts, `@page { margin: 0 }`, fixed 8.5 × 11 in sheet). Verified in WeasyPrint: ONE sheet, every text line at the source's exact pt position (274 / 326 / 432 / 518). 🔴 **WeasyPrint honours `@page`, which is exactly the thing browsers may not — so that result proves the geometry, NOT the risk.** Owed: Michael prints it from Chrome AND Safari on Letter. Pass = one sheet, frame intact, colours present, no browser furniture; record which margin setting passed.
2. ✅ R2 colours confirmed against the brand guide (§5).
3. ✅ BUILT 2026-10-08: `sign.yml` + `frames.tsv` + the injected style + the font, and `sign-backstage-access` converted as the first page. Paper test (step 1) now runs against the LIVE page rather than the hand-built sheet.

<p><br/></p>

## 🚫 §8 — Not in scope

Per-page print defaults in general (print-control.md Part A) · QR codes on signs · multi-sign packets · A4 · auto-fit text.
