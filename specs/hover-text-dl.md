# BUILD 9 sidecar — the arguments behind the hover-text rulings

Companion to [`hover-text.md`](hover-text.md). **This file is the SINGLE CLAIMANT for every argument in it** — the spec states conclusions and points here; it does not restate the reasoning. Same contract as [`../docrender/forms-dl.md`](../docrender/forms-dl.md), [`../docrender/views-dl.md`](../docrender/views-dl.md) and [`../docrender/buildstamp-dl.md`](../docrender/buildstamp-dl.md).

<p><br/></p>

⚠️ **Why it exists, stated so nobody folds it back in.** The spec reached 25,842 B on PR #213 and the PR body said the next growth would come here. It is here. 🔴 **And the failure this pattern exists to prevent has already happened once in this feature family:** on 2026-08-30 `views.py` pointed at a `views-dl.md D8` that had never been written — a phantom pointer. **A sidecar is only real once the thing pointing at it can be checked**, so every reference from the spec to this file names a section that exists below.

---

## A1 — HOVER TEXT WAS ALREADY SHIPPING, WITH PROOF FROM A LIVE PAGE

`theme/markers.tsv` carries a `tooltip` column and `markers.py`'s span renderer emits it unconditionally:

```python
+ ' title="' + html.escape(row["tooltip"], quote=True) + '">'
```

Read off `gh-pages`, unedited, on the built Emergency Contacts page:

```html
<span class="dr-mark dr-mark--box dr-mark--cls-layout" data-mark="layout"
      title="A layout. Prefer the link form where the layout has a page, so the
             report records which layouts a workflow actually touches.">
```

`assets/base.css` gives `.dr-mark` **`cursor: help`**. So the affordance was deliberate, styled, and a reader was already meeting it inside a table before anybody asked for it.

<p><br/></p>

⭐ **The honest first answer to *"can I do hover text"* was: yes, and you have been shipping it for weeks.** What was actually missing was a different SHAPE of the same idea (A3).

---

## A2 — THE `title=` CONTRADICTION: ONE ENGINE, ONE ATTRIBUTE, THREE VERDICTS

| Where | Mechanism | Status |
|---|---|---|
| `markers.py` | `title="…"` from the `tooltip` column, `cursor: help` | ✅ **LIVE, in production** |
| `figure.py` | `title=` | 🚫 **REFUSED BY RULING, 2026-08-06** |
| `buildstamp.py` | a CSS popup, `opacity` not `display` | ✅ live, and it **DELETED** its `title` |

`figure.py`, verbatim:

> **"`title` IS NOT SUPPORTED, BY RULING RATHER THAN BY OMISSION. The HTML `title` attribute does not appear on touch devices at all, is announced inconsistently by screen readers, and cannot be reached by keyboard. Accepting the key would mean shipping something that does not do what the author writing it believes it does — the failure this engine writes down more often than any other."**

Released explicitly by Michael on 2026-08-06.

<p><br/></p>

🔴 **`buildstamp.py` REACHED THE SAME CONCLUSION INDEPENDENTLY AND BUILT THE ALTERNATIVE.** It deleted `title` from both its nodes — on the corner copy because *"paper has no hover, so nobody could ever read it,"* and on the foot copy because it *"would draw a browser tooltip over ours."* What replaced it is the mechanism BUILD 9 should adopt wholesale:

> **"THE POPUP IS HIDDEN WITH `opacity`, NOT `display: none`, AND THAT IS AN ACCESSIBILITY DECISION.** `display: none` and `visibility: hidden` remove an element from the accessibility tree, so a screen reader would lose the identifier entirely — a hover-only fact is invisible to anybody not hovering. At zero opacity with `pointer-events: none` the text stays in the tree and is read normally, and it is absolutely positioned so it costs no layout."

Plus a `<span>` with `tabindex="0"`, revealed on `:focus-visible`, so a keyboard reaches it without the element claiming to be a control.

<p><br/></p>

⚑ **THE CONTRADICTION IS THE FINDING, NOT THE FEATURE.** `markers.py` ships the exact attribute `figure.py` refused, on the element a reader meets most often, and **neither file knows about the other.** **A rule refused in one module and shipped in another is not a rule; it is a coin toss with a paper trail.**

<p><br/></p>

⭐ **AND MICHAEL NEVER HAD TO BREAK HIS OWN RULE TO GET THIS FEATURE.** He opened by offering to (*"I want to break a rule I made previously for web interactions"*). He did not need to: the 08-06 refusal was aimed at `title=`'s three specific failures, and the popup has none of them. *A rule aimed at a MECHANISM should be re-tested against a different mechanism rather than treated as a refusal of the GOAL* — which is the line `blocks.tsv` already wrote when the icon column was accepted after an SVG-data-URL column had been refused.

---

## A3 — THE THREE GLOSS SCOPES, AND WHY PER-INSTANCE **CONTENT** IS REFUSED

`tooltip` is a **column in `markers.tsv`**: one string per marker TYPE, shared by every occurrence. Under the span form, every `{.role}` on every site would carry the **identical** hover text, because the text belongs to the word `role` and not to any role.

<p><br/></p>

**That is not a defect in `markers.tsv`.** Its design is that a marker is a member of a family and the report stays answerable because *"every row answers the same question."* A per-entity string in a vocabulary table would be a row per human, which is a contacts database wearing a stylesheet.

<p><br/></p>

| | Carries | Lives in | Status |
|---|---|---|---|
| a **CLASS gloss** | one string per marker type | `markers.tsv` `tooltip` | ✅ shipped |
| an **INSTANCE gloss** | a different string per occurrence | nowhere | 🚫 **refused, below** |
| an **ENTITY gloss** | one string per named thing, reused everywhere | the target page's frontmatter | ⭐ **RULED** |

🚫 **PER-INSTANCE CONTENT STAYS REFUSED.** "Theatre Administrator holds the keys" is a fact about the **ROLE**, not about the sentence. Written per-instance it is restated on every page that mentions it — **the two-claimants defect this repo has retired three manifests over** — and the day the role changes every page is wrong with nothing able to find them. ⭐ Per-entity, drift is impossible **by construction** rather than by discipline: there is one copy, so there is nothing to disagree with.

<p><br/></p>

⚠️ **THIS REFUSAL IS ABOUT CONTENT AND NOT ABOUT VISIBILITY**, and the distinction is load-bearing as of the 14:30 ruling. See `hover-text.md` §14: a per-instance *never print* flag carries no copy of the fact, so it has nothing to drift from. **A second claimant is a second COPY; a switch is not a claimant.**

---

## A4 — THE STRUCK `links:` RECOMMENDATION, KEPT BECAUSE IT WAS NEARLY RIGHT

~~⭐ Which means the mechanism already exists and is called `links:`. A `role:` or `gloss:` third field on a `links:` entry is the smallest possible version of this whole build.~~

<p><br/></p>

🪦 **STRUCK 2026-08-30 by Michael's ruling, and struck rather than deleted because the difference is instructive.** It correctly identified per-entity as the shape and then reached for the nearest existing map. **A `links:` entry is CONFIG: nothing renders it, nothing links to it, and a reader cannot open it.** The target page is the same one fact on a surface that already has a URL, a title, a type, an owner and a revision date.

<p><br/></p>

⚑ *When a fact needs a home and one candidate is a config key while the other is a page, the page wins unless the fact is machinery.* Same argument `keywords:` won on `_base` against a hidden meta block: *"nobody can see it, so nobody can audit it, so it rots silently and the first symptom is a search that stopped matching. Visible is the whole mechanism."*

---

## A5 — "GO TO CONTACT" IS NOT HOVER TEXT, AND CONFLATING THEM BUILDS A DEAD CONTROL

Michael's two opening examples looked like one feature and were not:

- *"Artistic Director"* is a **GLOSS**. Supplementary. Losing it costs a reader nothing.
- *"Go to contact"* is a **DESTINATION**. That is what a link is, and a browser already reveals it on hover for free.

<p><br/></p>

🔴 **A DESTINATION ONLY DISCOVERABLE BY HOVERING IS A DEAD CONTROL ON EVERY TOUCH DEVICE** — the rule this repo cites more than any other (`edit_links: false`, the retired PR number, the printed link policy, `!!! qr`'s all-false refusal, `align.css`'s refusal of `.align-left`). **If a name is clickable, it must LOOK clickable without hovering.**

<p><br/></p>

✅ **The link form already does exactly that.** `markerlinks` gives it an underline, which `markers.py` calls *"the only difference a reader sees"* and says a reader *"learns in one page without being told."* So the second half of the ask needed no build, and the ruling confirmed the read: he wanted a real link to a real page, which he already had.

---

## A6 — THE STRUCK PAPER SECTION, AND THE TEST THAT STILL GOVERNS

~~🔴 So a glossed name prints as a bare name, and the gloss is LOST. That is correct for "Artistic Director" and is worth stating rather than discovering.~~

<p><br/></p>

🪦 **STRUCK 2026-08-30.** Michael's print substitution answered it in the same conversation that raised it. Kept visible because **the reasoning still governs and §9 has to pass it rather than dodge it:** `buildstamp.py` dropped its `title` because *"paper has no hover"*; `print-callout.css` and `print-chrome.css` strip the caret, the chevron and the flow buttons on one test — ***"could a reader ACT on it with a pen?"***

<p><br/></p>

✅ **The printed gloss passes that test rather than weakening it**, by putting the fact in the ink instead of behind a gesture. A reader cannot hover paper; they can read a parenthesis.

---

## A7 — WHY NO NEW MARKER CLASS (the J31 clone argument, in full)

A `role` class would need `shape: plain` and `color: accent-2`: **byte-identical to `terminology` in every cell.**

<p><br/></p>

🔴 **THAT IS THE J31 CLONE DEFECT VERBATIM.** `uritp-safety` was `papyrus` with two cells changed, every other cell byte-identical — and one of the two changed cells shipped a link colour at **2.30:1**, failing AA, on the site whose readers are students acting on safety policy. The entry's own conclusion: **"A CLONE INHERITS THE BYTES, NOT THE FIXES.** Every cell matching is what made it look verified; the two cells that differ are the entire content of the row and neither was measured."

<p><br/></p>

✅ **And `marker-classes.tsv` had already ruled the general case** (Michael, 2026-08-09): *"i don't care if they're visually identical. the reporting tag is usually to be different. the front end would begin to look like skittles if everything had its own color at this point."* A collision is a defect **only where the colour is carrying the meaning**, and nobody reads a role chip and asks what hue it is. `terminology`'s own label already reads *"a defined term, with or without a page behind it,"* which is what a role is.

<p><br/></p>

⚠️ **The one real cost, so it is a trade rather than a slogan:** the build report groups by CLASS, so *"every role on this site"* is a filter on the marker NAME rather than its own group. The report line is `class · name · page · label → target`, so the name is present and the question is answerable. **That is the only argument for a class, and it costs a colour decision plus a chip contrast measurement** — measured against the chip's own wash, never against the page, per `marker-classes.tsv`.

---

## A8 — THE ID, AND WHY `role-theatre-administrator` HAS THE WORD TWICE

Michael's draft reference was `@role:role-theatre-administrator`. **The prefix already namespaces it**, so the page id is `theatre-administrator` and the reference is `@role:theatre-administrator`.

<p><br/></p>

`markers.tsv`'s own rule: *"WRITE THE PREFIX THE SAME AS THE MARKER unless there is a reason not to. `.rel` / `@rel:` is one idea with one name. `.relat` beside `@rel:` was the first draft and was rejected on the spot: two names for one thing is the defect that retired three manifests in brain-config."* A `role-` id prefix under a `@role:` namespace is that defect one layer down.

---

## A9 — THE `optional` TRAP, AND THE THREE FIELDS IT HAS ALREADY EATEN

`objects.py`, in its own docstring:

> **"`_resolve` merges `optional` into the spec and NOTHING EVER READS THAT LIST. It exists so a human can consult it, which means every key in it is a promise no code checks. The only way to know whether an optional field is live is to grep for a consumer, and that is a real structural gap rather than three separate oversights."**

`_base.yml` says it from the other side: *"objects.py checks `requires` and never reads `optional`, so these lists are the record a reader consults, not a gate."*

<p><br/></p>

🔴 **THE THREE ALREADY FOUND:**

1. **`revised:`** — declared optional, read by nothing until 2026-08-07. The date a reader saw was a line typed by hand at the foot of the page. *"The key was the decoration and the body line was the provenance."*
2. **`related:`** — declared since the type system shipped, read by nothing until 2026-08-19, **found because Michael asked whether it rendered.**
3. **`data:`** — the mirror direction: honoured by `datatable.py` since it shipped while declared by no type at all. *"Exactly the defect the type system exists to prevent, sitting inside the type system."*

<p><br/></p>

✅ **THE RULE FOR THIS BUILD, AND IT COVERS BOTH FIELDS.** A field goes in `requires:` (genuinely checked, reports the file and the field name) **or its consumer ships in the same PR as its declaration.** `print_gloss` is legitimately optional — absence is a real state meaning *print the gloss* — so it takes the second path, and shipping the declaration ahead of the print rule would make it the documented fourth instance, added by the session that read the warning.

---

## A10 — THE FRONTMATTER TEST, QUOTED IN FULL BECAUSE IT DECIDES EVERY FUTURE FIELD

`space.yml`, on the six room fields deleted 2026-08-03 (Michael: *"they're slop and not real metadata"*):

> **"They were facts about a ROOM. Nothing off the page ever read them: not the nav, not search, not doc-index.json, not a sibling site. The test this engine now applies is whether a value is needed AWAY from the page it appears on, and these were not — so they were prose wearing a header's clothes."**

> **"The evidence was stronger than the argument: across the whole of uritp-docs, all four space pages set ZERO of the six fields. A field set that is never populated is not waiting for content."**

> **"🚫 Do not re-add a facts-about-the-subject field here."**

`venue.yml` lost `address`, `city`, `operator` and `access_notes` to the same ruling.

<p><br/></p>

⚠️ **A ROLE PAGE IS THE SAME SHAPE AS A VENUE PAGE**, so that refusal points straight at BUILD 9 and had to be answered rather than sidestepped. ⭐ **`gloss` passes, and it is the first subject field to pass since the purge** — for a reason the purged fields never could: its entire purpose is to appear somewhere else. A phone number, an office or a term of appointment fails and belongs in the body.

<p><br/></p>

⭐ **AND THE 14:30 RULING MADE IT THE PUREST PASS AVAILABLE.** *"No to pasting frontmatter hover field render on the local page anywhere — just for external hovers."* The field is now read **only** away from its own page, never on it. **The test is not merely satisfied, it is satisfied exclusively** — which is the strongest form of the argument and the reason §13 of the spec exists.
