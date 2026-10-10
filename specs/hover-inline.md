# Inline hover text — `[Text]{hover="…"}`

**State:** ⚠️ SCOPED, NOT GREENLIT · 2026-10-09 · 🚫 no build number, deliberately (index numbering debt). **Seven rulings below before code.**
**Builds on:** the gloss popup in [`assets/gloss.css`](../assets/gloss.css) and [`docrender/linklabels.py`](../docrender/linklabels.py). **Sibling, not a reopening, of** [`hover-text.md`](hover-text.md). **Decision history:** doc-render-engine (repo) — Decision Log, ClickUp.

> Michael, 2026-10-09: *"do i have custom hover text definable anywhere? like [text](@) syntax but with like [Text]{.hover="This is a tooltip."} for custom hover text definable inline?"* Then: `hover_inline_spec`.

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

\[literal]{hover="kept as typed"}            escaped, not converted
```

- **Text:** inline markdown allowed inside (`*em*`, `**bold**`, code, a `.marker`). No links inside the span.
- **Hover string:** plain text only, `"…"` or `'…'`, escaped `\"` allowed. Never markdown, never HTML (escaped with `quote=True`).
- 🚫 **Headings excluded** (the hover-text ruling: a heading is also a nav label, TOC entry and anchor).
- 🚫 **Code fences and backticks skipped** via `util.sub_outside_code`, so this page can document the syntax.

<p><br/></p>

## ⚙️ §4 — Mechanism

- **NEW `docrender/hoverspan.py`, `on_page_markdown`**, composed into an existing shim (no `mkdocs.yml` registration). One regex outside code: `\[(text)\]\{\s*hover=("…"|'…')\s*\}` **not followed by `(`**, so it can never touch link syntax.
- **Emits raw inline HTML:** `<span class="dr-gloss dr-hover" data-gloss="…" aria-description="…" tabindex="0">Text</span>`. Markdown inside the span still renders (Python-Markdown processes text between inline tags).
- ⭐ **Raw HTML is why TSV cells work for free.** `cells.py` trusts typed HTML tags and only narrows ATTRIBUTE lists on link braces (`_classes`, hover-text §15) — the exact trap that made the role gloss vanish in tables. A pre-built span never passes through `_classes`. `cells.render` must call `hoverspan` the same way it calls `links` / `markers`.
- **`gloss.css`:** widen `a.dr-gloss` → `.dr-gloss` for the box, hover and `:focus-visible` rules; add a dotted-underline affordance on `span.dr-hover` only (R5). The span needs `tabindex="0"` because it is not focusable (the buildstamp precedent the sheet's header cites).
- **Links (R2):** external URL links route through the same brace: `hover=` becomes `data-gloss` + `.dr-gloss` on the `<a>`. On an `@`-link it is **reported and ignored**.
- **Report:** count per page; malformed braces (`hover` with no closing quote, `.hover=` typo) reported by name, never silently printed as literal braces.

<p><br/></p>

## ⚖️ §5 — Rulings needed (recommendation first)

| # | Question | ⭐ Recommend | Why |
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

- 🔴 **Most-used regex territory.** `links._LINK` and `markerlinks` own `[…](…)`. The not-followed-by-`(` guard keeps this out of their way; the external-link half (R2) does need `links.py` to carry the brace, so it ships **second**, after text spans prove out.
- ⚠️ **Popup inside a horizontally scrolling table** can be clipped. Same open item as hover-text §17; verify in a real table.
- ⚠️ **Popup near the right edge** runs off-screen (`left: 0` anchor). Acceptable v1; `max-width: min(32ch, 80vw)` bounds it.
- ⚠️ **Search:** the hover string sits in an attribute, so site search will not find it. Correct: it is help, not content.
- ⚠️ **`print-flow.css` `display: revert !important`:** any print rule here carries `!important` (gloss.css already does).

<p><br/></p>

## ✅ §7 — Build order

1. Rulings R1–R7.
2. `hoverspan.py` (text spans) + `gloss.css` selector widening + affordance. One test page in `uritp-docs` with prose, a list, a callout and a TSV cell.
3. `cells.py` hook-up.
4. External-link half in `links.py` (R2), then the `@`-link report.
5. Chrome hover, keyboard Tab, phone tap, and print preview (R3 flag on and off).

<p><br/></p>

## 🚫 §8 — Not in scope

Per-instance hover on `@`-links · rich popups (links, images) · hover on headings · a glossary page built from hover strings.
