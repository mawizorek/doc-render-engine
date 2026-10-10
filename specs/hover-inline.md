# Inline hover text — `[Text]{hover="…"}`

**State:** ✅ BUILT 2026-10-10 · part 1 (text spans, TSV cells, gloss.css) #287 · part 2 (external links, refusals, R7 report) #288 · R1–R7 accepted 2026-10-09 (`hover_inline_accept`) · ⚠️ phone tap and paper print of a `print` link still need Michael's eyes · 🚫 no build number, deliberately (index numbering debt).
**Builds on:** the gloss popup in [`assets/gloss.css`](../assets/gloss.css) and [`docrender/linklabels.py`](../docrender/linklabels.py). **Sibling, not a reopening, of** [`hover-text.md`](hover-text.md). **Decision history:** doc-render-engine (repo) — Decision Log, ClickUp.

> Michael, 2026-10-09: *"do i have custom hover text definable anywhere? like [text](@) syntax but with like [Text]{.hover="This is a tooltip."} for custom hover text definable inline?"* Then: `hover_inline_spec`. Then: all seven recommendations accepted.

<p><br/></p>

## 🔎 §1 — What exists today, read at HEAD (0068eb3)

| Want | Today | Verdict |
|---|---|---|
| Hover on a link to a page | `gloss:` (or `gloss_from_summary: true`) in the **destination's** frontmatter → every `[x](@id)` gets the styled popup (`linklabels.page_link` → `a.dr-gloss[data-gloss]`) | ✅ built |
| Hover typed AT a link | `[x](@id){title="…"}` — `page_link` passes `title` through | ⚠️ works, but it is the browser tooltip `gloss.css` itself refuses (no touch, no keyboard, inconsistent screen readers) |
| Hover on plain words | **nothing.** Python-Markdown has no bracketed span; `[Text]{…}` renders literally. `{.hover="…"}` is not even attr_list grammar (`.` is a class) | 🚫 missing — this spec |

⚠️ **Index drift spotted while reading:** `hover-text.md`'s row says *NOT YET BUILT*, but `gloss.css` ships the role popup and `linklabels.py` emits it. Re-verify and correct that row separately; not this spec's job.

<p><br/></p>

## ⚖️ §2 — Why this does NOT reopen hover-text's per-instance refusal

[dl A3](hover-text-dl.md) refuses a per-instance **gloss** because it is a second COPY of a fact the destination page owns, free to drift. ⭐ **Plain text has no destination.** A hover on the word *"quarter-hour"* is the only place that sentence exists, so there is nothing to drift FROM. Same test, opposite answer, because the subject changed.

🔴 **So the boundary is the whole design:** inline hover on **text** (and external URLs, R2); **never** on `@`-links, which keep `gloss:` as the single claimant.

<p><br/></p>

## ✍️ §3 — Authoring

```
Call is [the quarter-hour]{hover="15 minutes before places, not before curtain."} for all crew.

Read the [house rules](https://example.org/rules){hover="Opens the venue PDF."} first.

[Places]{hover="Everyone in position for the top of show." print}   printed as an italic parenthesis (R3)

\[literal]{hover="kept as typed"}            escaped, not converted
```

- **Text:** inline markdown allowed inside (`*em*`, `**bold**`, code, a `.marker`). No links inside the span.
- **Hover string:** plain text only, `"…"` or `'…'`, escaped `\"` allowed. Never markdown, never HTML (escaped with `quote=True`).
- **Links:** absolute `https://`, `http://` and `mailto:` only. Page, peer and `@` links are refused with a report line; so are images.
- 🚫 **Headings excluded** (the hover-text ruling: a heading is also a nav label, TOC entry and anchor).
- 🚫 **Code fences and backticks skipped** via `util.sub_outside_code`, so this page can document the syntax.

<p><br/></p>

## ⚙️ §4 — Mechanism (as built)

- **`docrender/hoverspan.py`, `on_page_markdown`**, composed into hook `03b_markers.py` ahead of markers (no `mkdocs.yml` registration). Regex outside code: `\[(text)\]\{\s*hover=("…"|'…')\s*(print)?\s*\}` **not followed by `(`**, so text spans never touch link syntax.
- **Text spans emit raw inline HTML:** `<span class="dr-gloss dr-hover" data-gloss="…" aria-description="…" tabindex="0">Text</span>` (+ `data-role-print="…"` when `print` is set). The hover string is entity-escaped for `[]{}|`, backtick, `:` and `@` so later stages can't re-read it as markup.
- ⭐ **Raw HTML is why TSV cells work.** `cells.render` calls `hoverspan` first; `cells.plain()` strips hover spans to their text, so `[12]{hover="…"}` still sorts and sums as 12.
- **`gloss.css`:** `a.dr-gloss` widened to `.dr-gloss` for the box, hover, `:focus-visible` and `:focus` (tap, R6); dotted underline + `cursor: help` on `span.dr-hover` only (R5). The existing `[data-role-print]` print rule covers R3 unchanged.
- **Links (R2), also in `hoverspan.py`, not `links.py`:** `[x](https://…){hover="…" print?}` becomes a finished `<a class="dr-gloss" data-gloss …>`. Page links are already relative by the time hover runs, so the absolute-URL rule cannot match them; peer links carry the engine's own brace first. Page, peer and `@` links: reported and left as plain links. Images: reported separately.
- **`title=` on page links (R7):** still passed through by `linklabels.page_link`, with a report line pointing at `gloss:`. `hover=` on a page link is skipped silently there, because `hoverspan` already reported it.
- **Report:** count per page; malformed braces (`hover` with no closing quote, `.hover=` typo) reported by name, never silently printed as literal braces.

<p><br/></p>

## ⚖️ §5 — Rulings (all seven accepted, Michael, 2026-10-09)

| # | Question | ✅ Ruled | Why |
|---|---|---|---|
| R1 | Syntax | **`[Text]{hover="…"}`** | Reads like attr_list, distinct from `title=`, and `.hover=` (Michael's sketch) is a class, not a value |
| R2 | Where it is legal | **Plain text + external URL links. Refused (reported) on `@`-links** | §2: `@`-links already have a single claimant, `gloss:` |
| R3 | Paper | **Not printed by default; `print` flag prints it as the italic parenthesis** (`[x]{hover="…" print}`) | Hover text is usually screen help; the parenthesis rule already exists in `gloss.css` (`data-role-print`) |
| R4 | Markup in the hover string | **Plain text only** | A popup holding links or formatting is a second page, not a tooltip |
| R5 | Affordance | **Dotted underline + `cursor: help` on text spans** | Otherwise nobody knows the hover is there. Links keep their own underline (gloss.css header: no help cursor on links) |
| R6 | Touch | **Tap shows it** (focus via `tabindex`); tap elsewhere hides | No JavaScript; `:focus` covers it |
| R7 | Kill the `title=` passthrough on page links? | **Keep it, report it** as a soft nudge toward `gloss:` | Removing a working attribute breaks pages silently; a report line doesn't |

<p><br/></p>

## 💣 §6 — Risks

- ✅ **Most-used regex territory.** Resolved: the not-followed-by-`(` guard keeps text spans out of `links._LINK` and `markerlinks`; the link half matches absolute URLs only, so it never sees page links.
- ⚠️ **`}` inside a hover string on an external link in a TSV cell** can leave a tail in that cell's sort value. Rare; reword the hover if it bites.
- ⚠️ **Popup inside a horizontally scrolling table** can be clipped. Same open item as hover-text §17.
- ⚠️ **Popup near the right edge** runs off-screen (`left: 0` anchor). Acceptable v1; `max-width: min(32ch, 80vw)` bounds it.
- ⚠️ **Search:** the hover string sits in an attribute, so site search will not find it. Correct: it is help, not content.
- ⚠️ **`print-flow.css` `display: revert !important`:** any print rule here carries `!important` (gloss.css already does).

<p><br/></p>

## ✅ §7 — Build order

1. ✅ Rulings R1–R7.
2. ✅ `hoverspan.py` (text spans) + `gloss.css` selector widening + affordance. Test page `REPO_PAGES/test-hover-inline.md` in `uritp-docs` (#287, uritp #209).
3. ✅ `cells.py` hook-up (#287).
4. ✅ External-link half in `hoverspan.py` (R2), `@`-link and image refusals, `title=` report (R7) (#288, uritp #211).
5. ✅ Chrome hover, print preview, tables (Michael's screenshots, part 1). ⏳ Phone tap; hover + print on the part-2 links.

<p><br/></p>

## 🚫 §8 — Not in scope

Per-instance hover on `@`-links · rich popups (links, images) · hover on headings · a glossary page built from hover strings.
