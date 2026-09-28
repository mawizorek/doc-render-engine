# BUILD 8 — print control · sidecar: the 2026-09-28 Workshop pass and what shipped

Parent spec: [`print-control.md`](print-control.md). That file is unedited in this pass (its §1–§8 are the argument; this is the ruling and the build). Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

> Michael, 2026-09-28: *"sometimes I print to a binder and want a fatter left margin. sometimes I print as a sign or form and want all margins even. can we make the published site have a print menu that lets the user fine tune these print parameters?"* Then: *"mira and dex workshop it once. I want it specced and then built soon and available in the next 30 minutes."*

## One pass, Maestro Mira + Dev Dexter

**Mira (scope).** `print-control.md` recommended Feature A (per-page defaults) first and B (the widget) later. **Michael's ask inverts that, and he is allowed to**: he wants the reader-facing menu, today, for margins and size. A is not built here and is not blocked by this. §8 already turned the margin refusal into *"a clamped range"* once a real use case arrived; binder and sign/form ARE that use case. So B ships, scoped to §1's safe column plus §8's clamped margins, and nothing else.

**Dex (engine).** Three constraints decide the implementation, all read at HEAD:

1. **The 640px list-mode threshold.** Left + right is capped at **40mm total**. A4: 170mm = 642.5px (table). Letter: 175.9mm = 664.8px (table). One rule, both papers, no paper detection — the page cannot know what the dialog will pick. §8 computed a Letter-only ceiling of 34.6mm left at 12mm right (46.6mm total); A4 is the tighter paper, so 40 is the number that holds on both.
2. **`@page` cannot read a custom property.** §6 asked every control to write one custom property. The type dial does (`--dr-print-base`, overridden at (0,1,1) against print-type.css §0's (0,1,0)). Margins cannot, so the script writes a literal `@page` rule into ONE `<style>` appended last in `<head>`, winning over print.css's `12mm` on source order.
3. **Running furniture is off everywhere** (`runfoot.enabled()` is False on every site), so the block axis is free today. 🚩 If a site opts in to `print: running: true`, a top/bottom margin under 16mm clips its boxes. Floor is 5mm regardless.

## Rulings taken (Michael's ask + this pass)

| # | Ruling | Note |
|---|---|---|
| 1 | **B ships before A.** | Michael's ask. Supersedes the parent's ruling 1 recommendation ("A first, alone") for B only. |
| 2 | **Presets:** Standard 12mm · **Binder** 12/12/12/**25** (L) · **Sign / form** 20mm even · Custom (per side, 0.5mm steps). | Every preset fits the 40mm budget. |
| 3 | **Custom is clamped and SAYS so.** | Keeps the side the reader typed, gives way on the other, prints a one-line note. §8: *"never a free number."* |
| 4 | **Text size:** Site default (no override) · 7.5 → 11pt. | Under 9pt shows a photocopy warning rather than refusing. §7's floor is a warning here, not a wall — Michael just moved the default to 8.5pt himself. |
| 5 | **`sessionStorage`, not nothing.** | Deviates from §6. Printing ten pages to a binder means re-picking per page otherwise. Dies with the tab, so it cannot outlive its reason — §6's actual objection was localStorage. |
| 6 | **Untouched = byte-identical.** | Standard + Site default emits no `<style>` at all. |
| 7 | **The menu never prints.** | `@media print { .dr-printctl { display:none !important } }` in the same sheet as the control (§5b). |
| 8 | **Not offered:** callout density, ink, QR, letterhead, stamp. | §1 / §4 refusals stand. |

## Files

| File | What |
|---|---|
| **NEW** `assets/printctl.js` | the panel, the clamp, the one `<style>` |
| **NEW** `assets/printctl.css` | the pill + panel chrome, tokens with Material fallbacks, the print-hide rule |
| `docrender/assets.py` | `_PRINTCTL_ASSETS` registered, walked in `hand_written_css`, planned in `_plan` — same PR as the files (D6) |

⚠️ **`assets.py` is now 22,505 B against the 22,528 B read limit — 23 B of headroom.** The next edit there must split it (the D-sidecar already holds the history; the group docstrings are the candidate).

## Verified, and not

✅ `node --check` clean. ✅ Exercised against a stub DOM: default emits nothing; Binder → `@page{margin:12mm 12mm 12mm 25mm}`; +8pt → adds the dial override; Custom left 33 → right clamps to 7 with the note; Reset removes the style; Print calls `window.print()`; state round-trips through sessionStorage.

🔴 **NOT verified in a real browser or on paper.** No headless Chrome was available. The acceptance test is Michael's: republish, open the pill bottom-right, pick Binder, print to PDF, and check (a) the gutter, (b) a page with a TSV table still prints as a table, (c) the pill is absent from the PDF.

⚠️ §8 of `print-type.css` (hand-placed page breaks invalidated by every print change) now has an unbounded number of instances at read time, exactly as the parent's §5c predicted. Don't author `{.new-page}`.

---

## v2 · 2026-09-28 afternoon: two field reports, two fixes

**PR #244: margins did not land, size did.** Same `<style>` element, so the printing browser ignored `@page`. Left/right moved to a margin on `.md-content__inner`, written as an offset from print.css's 12mm (`calc(Xin - 12mm)`). Top/bottom stay on `@page` (a content margin only reaches the first and last sheet), so they remain browser-dependent.

**v2: inches, drawn controls, header icon.** Michael: *"make it work in inches now, not mm and actually design the arrows and popups rather than using os defaults ... it also floats over footer content. maybe it belongs next to the light/dark toggle in the header as just the printer icon?"*

| # | Ruling | Supersedes |
|---|---|---|
| 9 | **Inches, ⅛ in steps, shown as fractions** (1 ⅜ in). Clamp ¼ to 1 ¼ in per side. | ruling 2/3 units |
| 10 | **Inline budget 1.5 in** (38.1mm): A4 649.7px, Letter 672px, both tables. | the 40mm figure |
| 11 | **Presets:** Standard = site default (no override) · Binder 1 in left, ½ in elsewhere · Sign/form ¾ in even · Custom. | ruling 2 |
| 12 | **No OS controls.** Preset cards, steppers and the size control are all `<button>`s with roles, styled from tokens. | — |
| 13 | **A printer icon in the header, right after Material's palette toggle** (falls back to before search, then fixed top-right). Panel opens under it with a caret; closes on Esc, outside click, or ×. A dot on the icon means a non-default setting is live. | the floating pill |
| 14 | Size stepper: 7.5 to 11 pt, plus a Default link. From Site default, − lands on 8 and + on 9 (the dial is 8.5pt today). | ruling 4 control shape |

Storage key bumped to `dr-printctl-v2` so a stale mm session cannot load into an inch UI. Stub-DOM tested; 🔴 still not browser-verified.
