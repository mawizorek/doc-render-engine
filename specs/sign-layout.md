# Sign layout — `type: sign`

**State:** ⚠️ SCOPED, NOT GREENLIT · 2026-10-08 · 🚫 no build number, deliberately (see the index's numbering debt).
**Decision history:** doc-render-engine (repo) — Decision Log, ClickUp.

> Michael, 2026-10-08, handing over `CAST AND CREW ONLY.pdf`: *"what we're aiming to replace...."* Then: spec it first.

The goal is to retire hand-laid sign files (InDesign-style PDFs) in favour of **rendered pages that print as the sign.** First customer: `uritp-docs` `REPO_PAGES/sign-backstage-access.md`. Second, already live and different in shape: `REPO_PAGES/sign-content-disclosure.md` (body paragraphs, an italic show title).

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

🔴 **The sRGB column is a NAIVE conversion** (no ICC profile). It is close, not authoritative. These are almost certainly the University of Rochester brand red / blue / dandelion; **confirm against the brand guide before any value becomes a token** (ruling R2).

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

1. **One sheet.** Letter portrait. The frame fills the printable area; content sits vertically centred inside it with the logo pinned to the top.
2. **The frame**, as nested BORDERS, never backgrounds. ⚠️ Browsers drop background colour on print by default; borders print. Plus `print-color-adjust: exact` on the frame, the precedent `qr.css` and the `!!! danger` border already use.
3. **Print furniture off**: letterhead, revised / posted-by, page numbers. A sign is not a document. 🔴 **The SCREEN header and the print menu stay** — the lesson of PR #277, where hiding the header from frontmatter took the print menu with it.
4. **On screen, a sheet-shaped card**: the framed page at `aspect-ratio: 8.5 / 11`, forced light inside the card even in dark mode, because it is paper. What you see is the sign you print.

<p><br/></p>

## 🧩 §4 — Mechanism, and why each piece sits where it does

- ✅ **A real type: `objects/sign.yml`.** `page.yml`'s own rule: *"A type earns its existence by having fields or a way of drawing."* A sign has a way of drawing and one field (`frame:`). Not a `chrome:` value: `chrome:` is about the site's skin around a page, and a sign changes the page itself.
- ✅ **CSS injected page-scoped**, on the `chrome.py` precedent (a `<style>` only the asking page pays for). 🔴 **Not a registered sheet:** `docrender/assets.py` is past the read ceiling and its split is standing debt in the index. A new registered asset would block on that split.
- ⚠️ **The font.** `docrender/fonts.py` (stage 04c) fetches the families an INSTANCE's typography row names. A sign needs Source Serif 4 on sign pages only. Either a small page-scoped fetch beside the injected CSS, or a typography row. Ruling R4.
- ⚠️ **The frame palette.** Recommend a tiny vocabulary file, `maw-themes` `vectors/frames.tsv` (`slug · band colours · band widths`), so `frame: uritp` is a NAME. 🚫 **Not new columns in `colors.tsv`**: those are theme-wide properties across ~60 rows, and a frame is not a property of a theme. Ruling R3.

<p><br/></p>

## ⚖️ §5 — Rulings needed before code

| # | Question | Recommendation |
|---|---|---|
| R1 | `type: sign` vs `chrome: sign` vs a class | **`type: sign`** (§4) |
| R2 | Frame colours: brand guide values vs the sampled ones above | **Brand guide**, sampled values as the fallback |
| R3 | Frame home: `frames.tsv` in maw-themes vs inline in `sign.yml` | **`frames.tsv`**: one row today, a name tomorrow |
| R4 | Source Serif 4, loaded only on sign pages? | **Yes, page-scoped** |
| R5 | Print furniture FORCED off on signs, or default-off with the print panel able to turn it back on | **Forced off.** Default-off-with-override needs print-control.md Part A (per-page defaults), which is not built |
| R6 | Letter only, or A4 as well | **Letter only.** Every sign in hand is Letter, and A4 doubles the frame geometry |
| R7 | Screen view: framed sheet card vs plain centred page | **Sheet card** (§3.4) |

<p><br/></p>

## 💣 §6 — Risks and edge cases, stated before anything is built

- 🔴 **`@page` margins are browser-dependent** (`printctl.js` header says so plainly). If a browser ignores `@page`, a frame sized to the sheet spills onto a SECOND sheet, and a two-page sign is a failed sign. The frame must be sized against the content box with an honest fallback, and **only a paper test settles it.**
- ⚠️ **The browser's own "Headers and footers"** will print a URL and date over the frame unless unticked. The print panel already tells readers; a sign page should say it louder.
- ⚠️ **`print-flow.css`'s `display: revert !important`** has beaten plain display rules in this family twice. Any hide rule here carries `!important` from the start.
- ⚠️ **Overflow cannot be detected at build time.** At 72 pt on a ~7 in measure a line holds roughly 12-13 capitals, which "CAST AND / CREW ONLY" fits and a longer message will not. Honest limit: the print panel's text-size dial already scales a sign down. 🚫 No auto-fit script in v1.
- ⚠️ **The content-disclosure sign** has an italic `h2` show title and two paragraphs. It must fit the same frame. It is the second test page, not an afterthought.
- ⚠️ **The `[…]{.align-center}` work from today** (align.css) becomes unnecessary on sign pages. It stays correct everywhere else; nothing is removed.

<p><br/></p>

## ✅ §7 — Pre-build proof, cheapest first

1. 🔴 **A hand-built HTML sheet, before any engine code.** Nested borders, Source Serif 4, the two type sizes. Print it from Chrome AND Safari on Letter. Pass = one sheet, frame intact, colours present, no browser furniture. This answers §6's first risk for the price of one file.
2. Confirm R2's colours against the brand guide.
3. Then `sign.yml` + the injected style + the font, and convert `sign-backstage-access` as the first page.

<p><br/></p>

## 🚫 §8 — Not in scope

Per-page print defaults in general (print-control.md Part A) · QR codes on signs · multi-sign packets · A4 · auto-fit text.
