# BUILD 9 · HOVER TEXT AND THE ROLE PAGE

⚠️ **SCOPED, NOT GREENLIT.** Scoped 2026-08-30, **RULED the same day** (§0). Indexed from [`next-build-spec.md`](../next-build-spec.md) — 🚩 see [`print-control.md`](print-control.md) §7 on why that row is missing. Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

> Michael, 2026-08-30, opening: *"can i do hover text???? like it'd be cool to be able to have 'Nigel Maister' and then hover for it to say 'Artistic Director' or 'Go to contact' when hovered... inside a table or prose or header..."*

---

## ✅ §0 — THE RULING, AND IT IS BETTER THAN WHAT THIS SPEC RECOMMENDED

> Michael, 2026-08-30: *"{.role} exactly ... but I'm going to only have 7-10 of these so i don't mind hand minting a contact page for them or something. it's important for the safety repo too maybe ... but then be able to say `Go get your keys from the [Theatre Administrator](@role:role-theatre-administrator)` and it would pull from a page somewhere (new page type: role probably) that has frontmatter for: hover text or something, and we'll use that page as a potential actual like 'about this person' for the site anyways..."*

Five things settled in one message: the token is **`.role`**, the form is the **LINK** form, the gloss lives on a **new page TYPE**, it arrives via that page's **frontmatter**, and the page is also a **destination worth visiting**.

<p><br/></p>

⭐ **THE LAST ONE IS WHY THIS WORKS, AND IT IS NOT A CONVENIENCE.** §3 below recommended a third field on a `links:` entry. That would have put a personnel fact in a config block: invisible, unlinkable, and auditable only by grep. **A page carrying its own gloss is the same fact on a surface a human can open**, which is the argument `keywords:` already won on `_base` (a hidden meta block *"rots silently and the first symptom is a search that stopped matching. Visible is the whole mechanism"*). The `links:` recommendation is **struck in §3**, not deleted.

<p><br/></p>

⚑ **And it retires ruling 4 by answering the prior question.** `markerlinks.py` says a prefix resolves against ANY page id and that *"the place to tighten that is objects/, not here."* A `role` TYPE is that tightening. `state.PAGES` already carries `type`, so **`@role:` becomes the first prefix in this engine that CAN check it resolved to the right KIND of page** rather than merely to a page. That capability is a side effect of his ruling, not a new ask.

---

## ✅ §1 — HOVER TEXT IS ALREADY SHIPPING, WITH PROOF FROM A LIVE PAGE

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

`assets/base.css` gives `.dr-mark` **`cursor: help`**. So the affordance is deliberate, styled, and a reader already meets it inside a table.

---

## 🚫 §2 — `title=` WAS REFUSED BY RULING, AND THE COMPLIANT MECHANISM IS ALSO ALREADY BUILT

`figure.py`, verbatim: **"`title` IS NOT SUPPORTED, BY RULING RATHER THAN BY OMISSION. The HTML `title` attribute does not appear on touch devices at all, is announced inconsistently by screen readers, and cannot be reached by keyboard. Accepting the key would mean shipping something that does not do what the author writing it believes it does — the failure this engine writes down more often than any other."** Released explicitly by Michael on 2026-08-06.

<p><br/></p>

🔴 **AND `buildstamp.py` REACHED THE SAME CONCLUSION INDEPENDENTLY AND BUILT THE ALTERNATIVE.** It deleted `title` from both nodes and replaced it with:

> **"THE POPUP IS HIDDEN WITH `opacity`, NOT `display: none`, AND THAT IS AN ACCESSIBILITY DECISION.** `display: none` and `visibility: hidden` remove an element from the accessibility tree, so a screen reader would lose the identifier entirely — a hover-only fact is invisible to anybody not hovering. At zero opacity with `pointer-events: none` the text stays in the tree and is read normally, and it is absolutely positioned so it costs no layout."

Plus a `<span>` with `tabindex="0"`, revealed on `:focus-visible`, so a keyboard reaches it without the element claiming to be a control.

<p><br/></p>

⚑ **THE CONTRADICTION IS STILL THE FINDING. One engine, one attribute, two opposite rulings, and neither file knows about the other.** `markers.py` ships the exact attribute `figure.py` refused, on the element a reader meets most often. **A rule refused in one module and shipped in another is not a rule; it is a coin toss with a paper trail.** ⭐ **Michael does not have to break his own rule to get this feature** — the 08-06 refusal was aimed at `title=`'s three failures, and the popup has none of them. Resolving the disagreement is worth more than the feature.

---

## 🔴 §3 — THE GAP: TOOLTIPS ARE PER-VOCABULARY, HE ASKED PER-ENTITY

`tooltip` is a **column in `markers.tsv`**: one string per marker TYPE, shared by every occurrence. So under the span form, every `{.role}` on every site would carry the **identical** hover text, because the text belongs to the word `role` and not to any role.

<p><br/></p>

**That is not a defect in `markers.tsv`.** Its design is that a marker is a member of a family and the report is answerable because *"every row answers the same question."* A per-entity string in a vocabulary table would be a row per human, which is a contacts database wearing a stylesheet.

<p><br/></p>

| | Carries | Lives in | Status |
|---|---|---|---|
| a **CLASS gloss** | one string per marker type | `markers.tsv` `tooltip` | ✅ shipped |
| an **INSTANCE gloss** | a different string per occurrence | nowhere | 🚫 refused, §3a |
| an **ENTITY gloss** | one string per named thing, reused everywhere | **the target page's frontmatter** | ⭐ **RULED, §7** |

### 🚫 §3a — per-instance stays refused, and the reason survived the ruling

"Theatre Administrator holds the keys" is a fact about the **ROLE**, not about the sentence. Written per-instance it is restated on every page that mentions it, which is **the two-claimants defect this repo has retired three manifests over**, and the day the role changes every page is wrong with nothing able to find them. ⭐ Per-entity, drift is impossible **by construction** rather than by discipline: there is one copy, so there is nothing to disagree with.

<p><br/></p>

~~⭐ Which means the mechanism already exists and is called `links:`. A `role:` or `gloss:` third field on a `links:` entry is the smallest possible version of this whole build.~~

<p><br/></p>

🪦 **STRUCK 2026-08-30 by §0, and struck rather than deleted because it was nearly right and the difference is instructive.** It correctly identified per-entity as the shape and then reached for the nearest existing map. **A `links:` entry is CONFIG: nothing renders it, nothing links to it, and a reader cannot open it.** The target page is the same one fact on a surface that already has a URL, a title, a type, an owner and a revision date. *When a fact needs a home and one candidate is a config key while the other is a page, the page wins unless the fact is machinery.*

---

## 🔴 §4 — BLOCKING: THE LINK FORM DROPS THE TOOLTIP TODAY

Found by reading the emitter rather than the stylesheet. `markerlinks._make.resolve` builds its output from the resolved row and reads exactly two fields:

```python
row = markers.table().get(name) or {}
klass = (row.get("class") or "").strip()
shape = (row.get("shape") or "").strip()
...
return "[" + label + "](" + target + anchor + "){ ." + " .".join(css) + " }"
```

**`tooltip` is on that row. It is never read.**

<p><br/></p>

| Form | Goes somewhere | Hover text |
|---|---|---|
| `[Theatre Administrator]{.role}` | ❌ | ✅ yes, the CLASS gloss |
| `[Theatre Administrator](@role:theatre-administrator)` | ✅ | ❌ **NO** |

🔴 **PROMOTED FROM "THE CHEAP WIN" TO BLOCKING BY §0.** It was a tidy inconsistency while the ask was ambiguous. Michael has now ruled the **link** form, so **the form he needs is the one with no hover text at all.** Nothing ships until this path can carry a gloss.

<p><br/></p>

⭐ **AND THE FIX INVERTS THE ASYMMETRY, WHICH IS THE RIGHT DIRECTION.** After §7 the link form carries the RICHER gloss (the entity) and the span form carries the weaker one (the class). That gives an author a reason to prefer the link form, **and the link form is the one that writes an edge into `state.REFS` and `/doc-refs.json`.** The feature and the reference graph pull the same way instead of against each other.

<p><br/></p>

⚠️ **`markerlinks.py`'s own docstring asserts the opposite in passing:** *"Everything else about a marker — colour, label, shape, tooltip — is re-read per build and stays hot."* True of the TABLE, false of the OUTPUT. ⚑ *A sentence listing four things where three are correct reads as verified, so nobody checks the fourth.* Correct it in the same pass.

---

## ⚠️ §5 — "GO TO CONTACT" IS NOT HOVER TEXT, AND CONFLATING THEM BUILDS A DEAD CONTROL

His two opening examples look like one feature and are not:

- *"Artistic Director"* is a **GLOSS**. Supplementary. Losing it costs a reader nothing.
- *"Go to contact"* is a **DESTINATION**. That is what a link is, and a browser already reveals it on hover for free.

🔴 **A DESTINATION ONLY DISCOVERABLE BY HOVERING IS A DEAD CONTROL ON EVERY TOUCH DEVICE**, the rule this repo cites more than any other. **If a name is clickable it must LOOK clickable without hovering.** The link form already does exactly that: `markerlinks` gives it an underline, which `markers.py` calls *"the only difference a reader sees"* and says a reader *"learns in one page without being told."*

<p><br/></p>

✅ **So the second half needs no build.** A glossed link shows its role on hover and its destination by being underlined. ⭐ §0 confirms this read: he asked for a real link to a real page, which is what he already had.

---

## ⭐ §6 — PAPER

~~🔴 So a glossed name prints as a bare name, and the gloss is LOST. That is correct for "Artistic Director" and is worth stating rather than discovering.~~

<p><br/></p>

🪦 **STRUCK 2026-08-30. Michael's print substitution is the answer to this and it arrived in the same conversation** ("since hovers don't work in print, maybe it could take the role and insert the person's name in a stylized parentheses right after it"). Kept visible because the *reasoning* still governs: `buildstamp.py` dropped its `title` because *"paper has no hover,"* and `print-callout.css` and `print-chrome.css` strip the caret, the chevron and the flow buttons on one test, *"could a reader ACT on it with a pen?"* **§9 does not weaken that test. It passes it** by putting the fact in the ink instead of behind a gesture.

---

## ⭐ §7 — THE ROLE PAGE TYPE: ONE YAML FILE AND ONE TSV ROW

The page-type mechanism already exists and is exactly what he named. `objects/*.yml` populates `state.TYPES`; a page declares `type:` and `objects.py` holds it to the declaration.

### `objects/role.yml`

```yaml
type: role
label: Role
extends: _base
requires:
  - gloss
```

**`extends: _base` inherits `id`, `title`, `status` and `summary`,** so a role page is a real page with a lede, a URL and a revision date. `venue.yml` is the precedent and is four lines.

### One row in `theme/markers.tsv`

```
role	terminology	Role			role	A defined production role. The page behind it says what the role covers and who to ask.
```

🔴 **NO NEW MARKER CLASS, AND THIS IS A REFUSAL RATHER THAN A SHORTCUT.** A `role` class would need `plain` and `accent-2`: **byte-identical to `terminology` in every cell.** `marker-classes.tsv` already rules that a collision *"is a defect only where the COLOUR IS CARRYING THE MEANING"* and that the answer is never a new hue. And an entity that is byte-identical to an existing one except for its name is **the J31 clone defect verbatim** (`uritp-safety` was `papyrus` with two cells changed, one of which shipped a failing contrast ratio). `terminology`'s own label already reads *"a defined term, with or without a page behind it,"* which is what a role is.

<p><br/></p>

⚠️ **The cost, stated: the report groups by CLASS, so "every role on this site" is a filter on the marker NAME rather than its own group.** The report line is `class · name · page · label → target`, so the name is present and the question is answerable. **That is the one argument for a class**, and it costs a colour decision plus a chip contrast measurement. Named in the rulings rather than decided here.

### 🔴 The id, and his own example has the word twice

His draft was `@role:role-theatre-administrator`. **The prefix already namespaces it**, so the page id should be `theatre-administrator` and the reference `@role:theatre-administrator`. `markers.tsv`'s own rule: *"WRITE THE PREFIX THE SAME AS THE MARKER... two names for one thing is the defect that retired three manifests in brain-config."* A `role-` id prefix under a `@role:` namespace is that defect one layer down.

### ⭐ Why 7 to 10 hand-minted pages is the right scale and changes the design

No generator, no index page required, no migration. **And it means the expensive half of this build does not exist:** there is no bulk authoring surface to design, so every remaining decision is about one YAML file and one code path.

---

## 🔴 §8 — THE ONE REAL CODE CHANGE: THERE IS NO id → FRONTMATTER PATH TODAY

This is the whole build, and it is small. `markerlinks._make.resolve` resolves against `state.PAGES`, which `links.on_files` builds:

```python
state.PAGES[page_id] = {
    "id": page_id,
    "type": meta.get("_type", "page"),
    "title": meta.get("title") or f.name,
    "url": f.url,
    "status": meta.get("status", "public"),
}
```

**Five keys, none of them the gloss.** The frontmatter is in `state.BY_SRC`, which is keyed by **`src_uri`**, not by page id. So a resolver holding an id has no route to that page's frontmatter at all.

<p><br/></p>

✅ **THE FIX IS AT THAT ONE CALL SITE, WHERE `meta` IS ALREADY IN HAND.** Add `"gloss": meta.get("gloss")` (and `holder`, under ruling 1) to the dict. `type` and `status` were added the same way and for the same reason: **a fact the published map needs about a page it already knows.** No second index, no reverse lookup, nothing cached that could go stale, and `state.py`'s admission price is paid the way `REFS` pays it (the value is written in the branch that already computed it).

<p><br/></p>

⚠️ **`markerlinks` then reads it off `hit`, never off `BY_SRC`.** `PAGES` is built AFTER visibility prunes, which is the property that makes a link unable to resolve to an unbuilt page. Reading frontmatter directly would reintroduce exactly that hole.

<p><br/></p>

⭐ **AND THE TYPE CHECK COMES FREE.** `hit["type"]` is already there, so `@role:` pointing at a non-role page can be **reported** rather than silently rendering a gloss-less link. First real answer to `markerlinks`'s open *"`@rel:safety-policy` will happily point at a safety page"* note. 🚩 Report, never refuse: nothing in this family may fail a build.

---

## 🔴 §9 — PRINT INSERTION IS THE FIRST ADDITIVE PRINT RULE IN THIS ENGINE

> Michael: *"maybe it could take the role and insert the person's name in a stylized parentheses right after it. It would add that content inline, which is similar to the other formatting we already do."*

**Every print rule in this engine today SUBTRACTS.** `flow.css` hides the iframe, `print-callout.css` strips the caret, `print-chrome.css` hides the flow strip and the site header, `views.py` hides the summary, the corner stamp dropped its PR number. The governing question has always been *what can a reader not act on with a pen.* **This rule ADDS text to his prose, and that is a new category.**

<p><br/></p>

🔴 **AND THE ENGINE DELETED SOMETHING FOR LOOKING LIKE THIS THREE HOURS AGO.** PR #202 removed the view-embed caption on sight: *"everything else the registry emits is structure (frame, link, failure marker) and the caption was the engine putting an editorial sentence in his content, in his voice, unasked."*

<p><br/></p>

✅ **THE TEST THAT LEGALISES THIS ONE, AND IT SHOULD BE WRITTEN DOWN AS THE RULE RATHER THAN REMEMBERED AS A JUDGEMENT:** the caption was **engine prose**; this is **the author's own data**, typed by him, on a page he owns, resolved through a reference he wrote. ⚑ **The engine may place a string on paper that it did not compose. It may never compose one.** That distinction is the entire difference between §9 and the thing deleted this morning, and it generalises past both.

### Mechanism

`markerlinks` emits `data-role-holder` on the anchor; a print-only rule reveals it:

```css
@media print {
  .dr-mark--link[data-role-holder]::after {
    content: " (" attr(data-role-holder) ")";
  }
}
```

⭐ **`attr()` in `content` is the one universally supported use of `attr()`**, and it keeps the string **in the HTML**: greppable, auditable, and impossible for the stylesheet to have invented.

<p><br/></p>

🔴 **AND THAT IS ALSO ITS ONE HONEST COST: `data-role-holder` IS IN THE DOM ON EVERY BUILD, ON EVERY PAGE, ON SCREEN.** *"Print-only" is a VISUAL claim and never a privacy one.* View-source shows it. Anybody scraping the site gets it. Stated here because §12 turns on it and because "it only shows in print" is the sentence somebody will reach for.

<p><br/></p>

⚠️ Two smaller things, named rather than discovered: `print-flow.css` uses `display: revert !important` on `<details>` children and has already beaten a plain `display: none` twice in this feature family, so **every declaration here carries `!important` and is verified in Chrome print preview**, not WeasyPrint (which discards `revert`). And a `::after` on an inline run **can break across a line**, so the parenthesis wants the same `white-space` treatment `.dr-mark` already has.

---

## ⭐ §10 — THE FRONTMATTER TEST IS ALREADY WRITTEN DOWN, AND IT DECIDES BOTH FIELDS

`space.yml`, on the six room fields deleted 2026-08-03 (Michael: *"they're slop and not real metadata"*):

> **"They were facts about a ROOM. Nothing off the page ever read them: not the nav, not search, not doc-index.json, not a sibling site. The test this engine now applies is whether a value is needed AWAY from the page it appears on, and these were not — so they were prose wearing a header's clothes."**

And: **"🚫 Do not re-add a facts-about-the-subject field here."** `venue.yml` lost `address`, `city`, `operator` and `access_notes` to the same ruling.

<p><br/></p>

⚠️ **A ROLE PAGE IS THE SAME SHAPE AS A VENUE PAGE, so that refusal is pointed straight at this build and has to be answered rather than sidestepped.** Applying the engine's own test:

<p><br/></p>

| Field | Read away from its own page? | Verdict |
|---|---|---|
| **`gloss`** | ✅ on **every page that references the role**, as the hover | **EARNS frontmatter** |
| **`holder`** | ✅ only if §9 ships, then on every referencing page's PAPER | earns it **under ruling 1** |
| a phone number, an office, a term of appointment | ❌ read only on the role page itself | **body prose.** `space.yml` applies |

⭐ **`gloss` is the first subject field to pass that test since the 08-03 purge**, and it passes for a reason the purged fields never could: the value's whole purpose is to appear somewhere else. 🚫 **So the role page gets exactly one or two declared fields and its content goes in the body.** The moment somebody adds `phone:` to `role.yml`, `space.yml` has already refused it.

---

## 🔴 §11 — `gloss` GOES IN `requires`, OR IT IS THE DOCUMENTED FOURTH INSTANCE

`objects.py`, in its own docstring:

> **"`_resolve` merges `optional` into the spec and NOTHING EVER READS THAT LIST. It exists so a human can consult it, which means every key in it is a promise no code checks... a real structural gap rather than three separate oversights."**

`_base.yml` says the same from the other side: *"objects.py checks `requires` and never reads `optional`, so these lists are the record a reader consults, not a gate."*

<p><br/></p>

🔴 **THREE FIELDS HAVE ALREADY BEEN FOUND DECLARED-AND-UNREAD:** `revised:` (2026-08-07), `related:` (2026-08-19, found because Michael asked whether it rendered), and `data:` in the mirror direction (honoured by the engine while declared by no type). **A `gloss:` in `optional` with no consumer is the fourth, and it would be shipped by the session that read the warning.**

<p><br/></p>

✅ **Two rules for this build:** `gloss` goes in **`requires:`**, which is genuinely checked and reports the file and the field. And **the consumer ships in the same PR as the declaration** (the two-edits discipline `state.REPORT` proved twice on report buckets). A role page with no gloss then reports itself at build instead of rendering a silently gloss-less link.

---

## 🚩 §12 — PII: THE SAFETY SITE IS PUBLIC AND ROLE PAGES WOULD BE A STAFF DIRECTORY

Michael: *"it's important for the safety repo too maybe."* ⚠️ **Then this needs deciding before a `holder:` is typed, not after.**

<p><br/></p>

🔴 `mawizorek/uritp-docs` is **PRIVATE** and the safety site publishes **PUBLICLY**. Visibility is per-repo and is **never carried between them** (the standing rule, and the pair most confused in the fleet). A set of role pages each naming its current holder is **a published staff directory**, reachable by URL, in `/doc-index.json`, in search, and per §9 **in the DOM of every page that references a role**.

<p><br/></p>

**Three shapes, and it is his call, not this spec's:**

1. **Role only.** The gloss says what the role covers and who to contact **by role**. No human named anywhere. Zero personnel data in any repo, nothing to go stale, `space.yml` unchallenged.
2. **Role plus holder, holder in the BODY.** The page reads as "about this person," which is what he asked for, and the name is visible content a reader can see is wrong. **No print insertion** (the field is not read away from its page, so §10 sends it to prose).
3. **Role plus `holder:` frontmatter.** Full feature including §9's printed parenthesis. The price is a named person in a public repo, on paper, and in the DOM of every referencing page.

<p><br/></p>

⚠️ **AND THE ASSIGNMENT IS A CLICKUP FACT.** URITP PEOPLE owns who holds a role, with a term attached. Option 3 is a **snapshot** of that in a markdown tree, and `dead_links` cannot see it rot. 🚩 If it ships, the honest mitigation is a `revised:` on every role page (already inherited from `_base`, already rendered as the last line) so a reader can see the age of the claim. **A stale name with a visible date is a different object from a stale name with none.**

---

## ⏳ Rulings needed

1. 🔴 **Does a role page name its holder, and if so where?** §12's three options. ✅ **Recommend option 2** unless the printed parenthesis is the point: it delivers the "about this person" page he asked for, keeps the name where a human can audit it, and needs no new consumer. **Option 3 is the only one that gets §9**, so this ruling and the print feature are one decision, not two.
2. 🔴 **Popup or `title=`?** ✅ **Recommend the popup, and retire `title=` from `markers.py` in the same pass**, ending §2's contradiction. ⚠️ Cost: it is a real rewrite of the span renderer's output, and `markers.py` is **21,561 B** against a 22,528 ceiling with a history of taking every site down. **Measure before writing, and the rationale goes in a sidecar** (`forms-dl.md` / `views-dl.md` / `buildstamp-dl.md` precedent) rather than in the module.
3. **Its own marker class, or a `terminology` row?** ✅ **Recommend the row.** §7 is the argument. The only thing a class buys is a report GROUP, and it costs a colour that would be identical to the one it forked from.
4. **Headings?** He asked for *"prose or header."* ⚠️ A heading is also a nav label, a TOC entry and an anchor target: four surfaces, one string. ✅ **Recommend prose and table cells in v1**, headings named as deliberately excluded rather than forgotten.

---

## Files and sizes

**Measured from a directory listing at HEAD `b47ee905`, 2026-08-30. Not carried from the previous revision of this spec.**

| File | Now | Change |
|---|---|---|
| `docrender/links.py` | 16,596 B | **+1 or 2 dict keys** in `on_files`. §8, and it is the whole unlock. |
| `docrender/markerlinks.py` | 13,047 B | reads the gloss off `hit`, emits the attribute pair, corrects its own docstring. Room. |
| **NEW** `objects/role.yml` | — | ~10 lines. §7. |
| `theme/markers.tsv` | — | one row. §7. |
| `docrender/markers.py` | **21,561 B** | 🔴 967 B of headroom against 22,528. **Ruling 2 lands here or nowhere**, and only with a sidecar. |
| `docrender/objects.py` | **22,423 B** | 🔴 **105 B of headroom.** Nothing may be added here. If a role-page check is wanted it belongs in `markerlinks`. |
| `assets/print-*.css` | — | §9's block. 🚩 Which sheet is open: `print-type.css` had **239 B** of headroom on 08-29 and its own note says the next edit must SPLIT it first. **Measure at the moment you act.** |

⚠️ **Every number above will be wrong within days, and this repo's most-repeated scar is a size asserted from memory.** `flow.css` moved 2,365 B in one morning and a PR shipped "three bytes under" against a file that was already 957 B over. **Read it back.**
