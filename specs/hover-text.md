# BUILD 9 — HOVER TEXT: a gloss on a name, and the three verdicts this engine already holds

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-30. Indexed from [`next-build-spec.md`](../next-build-spec.md) — 🚩 see [`print-control.md`](print-control.md) §7 on why that row is missing. Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

> Michael, 2026-08-30: *"can i do hover text???? like it'd be cool to be able to have 'Nigel Maister' and then hover for it to say 'Artistic Director' or 'Go to contact' when hovered... inside a table or prose or header..."*

---

## ⭐ One line, and it is not the answer he expected

**Hover text already exists in this engine, is live in production, and was separately REFUSED BY RULING — in three different files, with three different verdicts.** So the build is not *"can we do hover text."* It is *"the engine holds three contradictory answers and needs one,"* plus a genuine gap: **every existing mechanism attaches the text to a VOCABULARY, and he is asking for it per NAME.**

| Where | Mechanism | Status |
|---|---|---|
| `markers.py` | `title="…"` from a `tooltip` column, `cursor: help` | ✅ **LIVE, in production** |
| `figure.py` | `title=` | 🚫 **REFUSED BY RULING, 2026-08-06** |
| `buildstamp.py` | a CSS popup, `opacity` not `display` | ✅ live, and it **DELETED** its `title` |

---

## ✅ §1 — IT IS ALREADY SHIPPING, AND HERE IS THE PROOF FROM A LIVE PAGE

`theme/markers.tsv` carries a `tooltip` column. `markers.py`'s span renderer emits it unconditionally:

```python
+ ' title="' + html.escape(row["tooltip"], quote=True) + '">'
```

Read off `gh-pages` on the built Emergency Contacts page, unedited:

```html
<span class="dr-mark dr-mark--box dr-mark--cls-layout" data-mark="layout"
      title="A layout. Prefer the link form where the layout has a page, so the
             report records which layouts a workflow actually touches.">
```

And `assets/base.css` gives `.dr-mark` **`cursor: help`** — `markers.py` names both that and `white-space: nowrap` as the two declarations that made the LINK form refuse `.dr-mark`. **So the hover affordance is deliberate, styled, and a reader is already meeting it inside a table.**

⭐ **So the honest first answer is: yes, and you have been shipping it for weeks.** What he is asking for is a different SHAPE of the same idea, and the difference is §3.

---

## 🚫 §2 — AND `title=` WAS REFUSED BY RULING, WITH THREE REASONS THAT ARE STILL TRUE

`figure.py`, verbatim: **"`title` IS NOT SUPPORTED, BY RULING RATHER THAN BY OMISSION. The HTML `title` attribute does not appear on touch devices at all, is announced inconsistently by screen readers, and cannot be reached by keyboard. Accepting the key would mean shipping something that does not do what the author writing it believes it does — the failure this engine writes down more often than any other."** Michael released it explicitly on 2026-08-06.

🔴 **AND `buildstamp.py` REACHED THE SAME CONCLUSION INDEPENDENTLY AND BUILT THE ALTERNATIVE.** It deleted `title` from both its nodes — on the corner copy because *"paper has no hover, so nobody could ever read it,"* and on the foot copy because it *"would draw a browser tooltip over ours."* What replaced it is the mechanism this build should probably adopt wholesale:

> **"THE POPUP IS HIDDEN WITH `opacity`, NOT `display: none`, AND THAT IS AN ACCESSIBILITY DECISION.** `display: none` and `visibility: hidden` remove an element from the accessibility tree, so a screen reader would lose the identifier entirely — a hover-only fact is invisible to anybody not hovering. At zero opacity with `pointer-events: none` the text stays in the tree and is read normally, and it is absolutely positioned so it costs no layout."

Plus: **a `<span>` with `tabindex="0"`, revealed on `:focus-visible`** — so a keyboard reaches it without the element claiming to be a control.

⚑ **THE CONTRADICTION IS THE FINDING. One engine, one attribute, two opposite rulings, and neither file knows about the other.** `markers.py` ships the exact attribute `figure.py` refused, on the element a reader meets most often, and no file mentions the disagreement. **A rule refused in one module and shipped in another is not a rule; it is a coin toss with a paper trail.** Resolving that is this build's real deliverable and it is worth more than the feature.

---

## 🔴 §3 — THE ACTUAL GAP: TOOLTIPS ARE PER-VOCABULARY, HE IS ASKING PER-INSTANCE

`tooltip` is a **column in `markers.tsv`** — one string per marker TYPE, shared by every occurrence. So `[Nigel Maister]{.person}` and `[Katie Farrell]{.person}` would carry the **identical** hover text, because the text belongs to the word `person`, not to either human.

**That is not a defect in markers.tsv.** Its whole design is that a marker is a member of a family and the report is answerable because *"every row answers the same question."* A per-person string in a vocabulary table would be a row per human, which is a contacts database wearing a stylesheet.

⚑ **SO THE FEATURE IS GENUINELY MISSING, AND NAMING WHICH ONE IT IS MATTERS:**

| | Carries | Lives in | Exists? |
|---|---|---|---|
| a **CLASS gloss** | one string per marker type | `markers.tsv` | ✅ shipped |
| an **INSTANCE gloss** | a different string per occurrence | nowhere | ❌ **the build** |
| an **ENTITY gloss** | one string per named thing, reused everywhere it appears | `links:` / a page | ⭐ **probably the right answer** |

🔴 **AND THE THIRD ROW IS THE ONE TO BUILD, NOT THE SECOND.** "Nigel Maister → Artistic Director" is a fact about **Nigel**, not about this sentence. Written per-instance it is a fact restated on every page that mentions him — **the two-claimants defect this repo has retired three manifests over** — and the day his title changes, every page is wrong and nothing can find them. Written per-ENTITY it is one declaration, reused, and drift is impossible by construction.

⭐ **Which means the mechanism already exists and is called `links:`.** `urllinks.py` reads it straight off `state.INSTANCE`, `qr.py` reuses its resolution ladder, and an entry already carries a URL and a label. **A `role:` or `gloss:` third field on a `links:` entry is the smallest possible version of this whole build.**

---

## 🔴 §4 — THE ASYMMETRY NOBODY HAS REPORTED: THE LINK FORM DROPS THE TOOLTIP

Found by reading the emitter rather than the stylesheet. `markerlinks._make.resolve` builds its output from the resolved row and reads exactly two fields:

```python
row = markers.table().get(name) or {}
klass = (row.get("class") or "").strip()
shape = (row.get("shape") or "").strip()
...
return "[" + label + "](" + target + anchor + "){ ." + " .".join(css) + " }"
```

**`tooltip` is on that row. It is never read.** So:

| Form | Goes somewhere | Hover text |
|---|---|---|
| `[Nigel Maister]{.person}` | ❌ | ✅ **yes** |
| `[Nigel Maister](@person:nigel)` | ✅ | ❌ **NO** |

🔴 **AND THE ONE THAT LOST IT IS THE ONE HE NEEDS.** His second example is *"Go to contact"* — that is a LINK, so it is the link form, so it is the form with no tooltip. **The two halves of his ask are currently mutually exclusive and nothing says so.**

⚠️ **`markerlinks.py`'s own docstring asserts the opposite in passing:** *"Everything else about a marker — colour, label, shape, tooltip — is re-read per build and stays hot."* True of the TABLE and false of the OUTPUT. ⚑ *A sentence listing four things where three are correct reads as verified, so nobody checks the fourth.* This engine has logged that exact shape before, in `blocks.py`, about a transition.

✅ **This is a two-line fix and it is the cheapest real win in either spec.** 🚩 It is also a live inconsistency shipping today, which arguably makes it a bug rather than part of a build.

---

## ⚠️ §5 — "GO TO CONTACT" IS NOT HOVER TEXT, AND CONFLATING THEM BUILDS A DEAD CONTROL

His two examples look like one feature and are not:

- *"Artistic Director"* — a **GLOSS**. Supplementary. Losing it costs a reader nothing.
- *"Go to contact"* — a **DESTINATION**. That is what a link is. A browser already reveals it on hover, in the status bar, for free.

🔴 **A DESTINATION THAT IS ONLY DISCOVERABLE BY HOVERING IS A DEAD CONTROL ON EVERY TOUCH DEVICE** — the rule this repo cites more than any other (`edit_links: false`, the retired PR number, the printed link policy, `!!! qr`'s all-false refusal, and `align.css`'s refusal of `.align-left`). **If a name is clickable, it must LOOK clickable without hovering.** The link form already does exactly that: `markerlinks` gives it an underline, and `markers.py` calls that underline *"the only difference a reader sees"* and says a reader *"learns that in one page without being told."*

✅ **So the answer to the second half is: it already works, and it should not be a tooltip.** A glossed link shows its role on hover and its destination by being underlined.

---

## 🔴 §6 — PAPER, WHERE HOVER DOES NOT EXIST

⚠️ **Every mechanism here is screen-only by nature, and the print layer has already ruled on the printed case twice.** `buildstamp.py` dropped its `title` because *"paper has no hover."* `print-callout.css` and `print-chrome.css` strip the caret, the chevron and the flow buttons on the same test: *"could a reader ACT on it with a pen?"*

🔴 **So a glossed name prints as a bare name, and the gloss is LOST.** That is correct for *"Artistic Director"* and is worth stating rather than discovering. 🚩 **And it is a real question for one case:** a printed safety sheet naming a person whose ROLE is the reason to contact them. If that matters, the answer is the same one the QR took — put it in the content, not in an affordance. **Not solved here, and named so the printed sheet is never assumed to carry it.**

---

## ⏳ Rulings needed

1. **🔴 Which mechanism wins — `title=` or the CSS popup?** ✅ **Recommend the popup, and retire `title=` from `markers.py` in the same pass.** It is the mechanism this engine already chose once, with the accessibility argument written down, on the element that had the same job. Keeping both means the contradiction in §2 survives the build that was supposed to end it. ⚠️ **Cost, stated: it is a real rewrite of the span renderer's output**, and `markers.py` is **21,561 B** with a history of taking every site down.
2. **🔴 Per-ENTITY or per-instance?** ✅ **Recommend per-entity, on a `links:` entry.** §3 is the argument. Per-instance is easier to build and is the version that rots.
3. **Does the link form get the tooltip?** ✅ **Recommend yes, and treat it as a BUG FIX shipped ahead of this build** rather than part of it. Two lines, and it removes the mutual exclusivity in §4.
4. **Is there a `@person:` prefix, or is a person just a page?** ⚠️ `markerlinks` resolves a prefix against ANY page id and says so: *"`@rel:safety-policy` will happily point at a safety page. The place to tighten that is objects/, not here."* A person is arguably a page TYPE, and the URITP tree already has `actual-people/`. **Recommend deciding that in `objects/` before adding a prefix**, or the prefix becomes the schema decision by default.
5. **Does the gloss appear on a HEADING?** He asked for *"inside a table or prose or header."* ⚠️ A heading is also a nav label, a TOC entry and an anchor target — four surfaces, one string. **Recommend prose and table cells only in v1**, and name headings as deliberately excluded rather than forgotten.

---

## Files and sizes (measured at HEAD 2026-08-30)

| File | Now | Change |
|---|---|---|
| `docrender/markerlinks.py` | 13,047 B | **+2 lines** for §4. The cheap win. |
| `docrender/markers.py` | **21,561 B** | 🔴 ~1KB of headroom, and it is the module whose history includes an outage. Ruling 1 lands here or nowhere. |
| `theme/markers.tsv` | — | unchanged under ruling 2 |
| `docrender/urllinks.py` | 14,403 B | +small, a third field on a `links:` entry |
| `assets/base.css` | 20,335 B | 🔴 `cursor: help` and the popup rules both live here; ~2KB of headroom |
| **NEW** `assets/gloss.css` | — | if ruling 1 picks the popup, it needs a home that is not base.css |

⚠️ **Every number above will be wrong within days — measure at the moment you act.** That is this repo's most-repeated scar and `next-build-spec.md` carries three instances of it in one table.
