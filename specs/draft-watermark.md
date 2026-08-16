# BUILD 4 — the DRAFT status, and the watermark it drives

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-16. Requested by Michael out of the safety-docs publish: *"maybe we make 'draft' an actual page status… could the renderer literally do like an old school watermark at 45 degrees over the scroll window… that just says DRAFT in soft very opaque but clearly there."* Indexed from [`next-build-spec.md`](../next-build-spec.md).

Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

---

## One line

Make **`draft` a first-class page status**, and let that status — through a **status → treatment map** — paint a fixed 45° **DRAFT** watermark over the scroll viewport on screen. **Only `draft` is populated in the map;** the map exists so other statuses *can* get treatments later, but this build adds exactly one. Print is handled separately and manually (see §4).

---

## 🔴 §0 — THE BLOCKING QUESTION: what does the engine do with `status: draft` TODAY?

This decides whether the build starts from zero or from a live problem, and it must be answered by reading the code before anything is written, not assumed here.

<p><br/></p>

The recognized statuses today are **`public` / `gated` / `unlisted` / `hidden`** (handled in `docrender/visibility.py` + `state.py` — verify the exact set and home at build; do not trust this sentence). **`draft` is not known to be one of them.** So one of two things is currently true, and which one changes the stakes:

<p><br/></p>

- **(a) An unrecognized `status:` falls through to a default** — and if that default is *publish it*, then **every page currently marked `status: draft` is live right now.** The entire `safety/` tree is `draft` as of 2026-08-16. That would make this a correctness fix, not a nicety.
- **(b) An unrecognized `status:` is refused / reported** — in which case the safety pages may not be building, or are flagged in the build report nobody was reading (BUILD 2's entire premise).

<p><br/></p>

⚠️ **Find out which, first.** The answer is a one-file read (`visibility.py`), it is knowable before any design decision, and it changes whether §1 is "add a value" or "close a hole." This spec does not guess.

---

## §1 — `draft` as a real status

Add `draft` to the recognized status set. Its **visibility behaviour** (does a draft page build? appear in nav? in search? in the sitemap?) is a ruling, not an assumption — see the ruling block. The likely intent, from the ask: **a draft page BUILDS and is readable** (you are reviewing it), but wears the watermark so nobody mistakes it for adopted. That is closer to `public + a stamp` than to `hidden`.

<p><br/></p>

⚠️ **`draft` is orthogonal to `gated`.** A page can be both (a gated form still under review). The watermark is driven by `draft`; the password gate is driven by `gated`. Do not fold one into the other — they answer different questions (*is it finished* vs *who may read it*).

---

## §2 — the status → treatment MAP (the architecture Michael asked for)

> Michael: *"lets spec it as a clean map and not a one-off but i don't want to see any others yet."*

A single declared mapping from a status to a visual treatment, so adding a future treatment is a new **row**, never a new mechanism:

<p><br/></p>

```
status     screen treatment        print treatment
------     ----------------        ---------------
draft      watermark: "DRAFT"      watermark: "DRAFT"  (added manually in print flow, §4)
```

<p><br/></p>

**Only the `draft` row exists in this build.** `public`, `gated`, `unlisted`, `hidden` get **no** row (their behaviour is unchanged and lives where it already lives — this map is treatments, not a re-home of visibility logic). ⭐ **The map is the extension point; the emptiness is deliberate.** A reader must be able to see that `draft` is the only populated row and that adding, say, a `superseded` stamp later is one row plus one label.

<p><br/></p>

🔴 **Where the map lives is a real decision, not a detail.** Two honest options, decide at build:
- **A canonical TSV** (e.g. `theme/status-treatment.tsv`) — consistent with how every other vector in this engine is declared as data, and it is the answer that matches the house pattern. Preferred unless the read below says otherwise.
- **A small dict in `visibility.py`** — cheaper, but it is code stating a fact that the rest of the system states as data, and this repo has a documented allergy to that (three retired manifests). 
⚠️ If it becomes a TSV, it is a NEW canonical vector and the token/vector machinery has opinions — check whether that is proportionate for a one-row table, or whether a one-row TSV is over-engineering the very thing Michael said not to over-build. **Name the tradeoff; do not default silently.**

---

## §3 — the screen watermark

Michael's spec, verbatim intent: *"old school watermark at a 45 degree over the scroll window (ie it doesn't move, but the content moves under it) that just says DRAFT in soft very opaque but clearly there."*

<p><br/></p>

**The mechanics, and none of it is hard:**
- A **fixed** element over the content viewport — `position: fixed` so the content scrolls *under* it, exactly as asked.
- `transform: rotate(-45deg)`, centered.
- **Low opacity** — soft but unmistakable. The exact value is a MEASUREMENT against the eos/site grounds, not a guess (this repo does not eyeball contrast — see the whole Decision Log). It must be legible on both light and dark schemes, which likely means the value differs per scheme, same as every other token here.
- 🔴 **`pointer-events: none`** — non-negotiable. The watermark must never eat a click, a text selection, or a link. This is the one line that, omitted, makes the feature actively harmful.
- **Tiled vs single.** A single centered `DRAFT` is the classic look; a repeated/tiled `DRAFT` reads better down a long document (a single word scrolls out of view and a long page looks unmarked mid-scroll). **Recommend tiled**, but it is a look decision — Style Stu's call, not the engine's.
- Lives in its own asset (e.g. `assets/draft.css`), not bolted into `base.css` — the repo's own module-hygiene rule.

<p><br/></p>

⚠️ **The scroll-container question.** *"over the scroll window"* — fixed to the viewport is the simplest true reading and is almost certainly right. But Material renders content inside its own scroll structure; verify the watermark sits over the **content column** as intended and not under the header/sidebar chrome, and that it behaves when the sidebar is open on desktop vs collapsed on mobile. This is a render-time check, and this repo has a long scar about asserting layout from a read instead of a rendered page — do not declare it done without looking.

---

## §4 — print: DRAFT is added MANUALLY in the print flow (Michael's ruling)

> Michael: *"draft can be ADDED in the PRINT manually just like it strips 'edit on git' and guarantees white background?"*

**Yes, and this is the correct design** — a `position: fixed` screen watermark does not translate to paginated print reliably (it prints once, or mis-places, or vanishes), so print gets its own deliberate treatment rather than inheriting the screen one.

<p><br/></p>

🔴 **Hook into the EXISTING print pipeline, do not invent a parallel one.** `assets/print.css` exists and already does exactly this class of thing — Michael names two behaviours it owns: **stripping the "edit on git" affordance** and **forcing a white background.** The print DRAFT stamp is a third rule in that same pipeline.
⚠️ **BUILD STEP, not an assumption:** read `assets/print.css` (and whatever emits/paginates print — confirm whether the edit-on-git strip and white-bg live in `print.css` alone or partly in a hook/theme override) and add the DRAFT rule *there*, gated on the `draft` status the same way the screen treatment is. Confirm the mechanism before wiring; the two behaviours Michael cites are the map to follow.
⚠️ **`print.css` has a known scar** (see `specs/scoped-theme.md` §4c): a scoped selector can silently kill `print.css` on the pages it scopes, because that sheet wins on source order at equal specificity. If BUILD 3's scoped theme ever lands, the draft print rule and the scope interact — note it, do not collide with it.

---

## ⏳ Rulings needed

1. **§0 first — what does `status: draft` do today?** Blocking. Decides whether this is a feature or a fix. One-file read.
2. **Draft visibility:** does a `draft` page build + appear in nav + search + sitemap (watermarked), or is it held back like `unlisted`/`hidden`? Recommend **builds and is fully readable, watermarked** — the ask is *mark it as unfinished*, not *hide it*. But confirm, because it interacts with §0.
3. **Map home:** canonical TSV vs a dict in `visibility.py` (§2). Recommend TSV for house-consistency **unless** a one-row TSV trips the vector machinery disproportionately — measure, then choose.
4. **Tiled vs single watermark** (§3) — look decision, Stu. Recommend tiled.
5. **Exact opacity / per-scheme values** (§3) — a measurement against the grounds, not a guess; belongs with whoever owns the palette pass.

---

## Files likely touched (measure at HEAD before acting — do NOT trust these paths blind)

<p><br/></p>

| File | Likely change |
|---|---|
| `docrender/visibility.py` | add `draft` to the recognized status set; wire the treatment lookup. **Verify this is where status lives first.** |
| `theme/status-treatment.tsv` *(NEW, if ruling 3 = TSV)* | the one-row map |
| `assets/draft.css` *(NEW)* | the screen watermark rule |
| `assets/print.css` | the print DRAFT rule (third behaviour beside edit-on-git strip + white bg) |
| a hook / template partial | inject the watermark element + a `data-status` hook on the body/content, IF the status is not already exposed to the DOM — verify how `gated`/`unlisted` already reach CSS today and reuse that path, do not invent a second one |
| `mkdocs.yml` | asset registration if `draft.css` needs it |

<p><br/></p>

🔴 **This repo's iron rule: a size or path written into a spec is wrong within two days. Re-measure and re-confirm every file at the moment you build.** The Decision Log has this scar a dozen times over.

---

## Sequence

1. **§0 read** — answer what `draft` does today. Nothing else starts until this is known.
2. **`draft` as a recognized status** + the treatment-lookup seam (no visual yet). Independently verifiable: a draft page classifies correctly.
3. **Screen watermark** (`draft.css` + the DOM hook). The visible half.
4. **Print rule** in `print.css`. Smallest, and reuses the pattern edit-on-git already set.
5. **Measure** opacity/legibility on a rendered page, both schemes. Not done until looked at.

---

## What this build is NOT

- 🚫 **Not a second treatment for any other status.** The map is built for extension; only `draft` is filled. Michael: *"i don't want to see any others yet."*
- 🚫 **Not a re-home of the existing visibility logic.** `public`/`gated`/`unlisted`/`hidden` behaviour is untouched; this adds `draft` and a treatment lookup beside them.
- 🚫 **Not a screen watermark forced into print.** Print is deliberately its own manual rule (§4).
