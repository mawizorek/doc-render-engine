# BUILD 9 · HOVER TEXT AND THE ROLE PAGE

⚠️ **SCOPED, NOT GREENLIT.** Scoped 2026-08-30, **ruled twice the same day** (§0). Indexed from [`next-build-spec.md`](../next-build-spec.md) — 🚩 see [`print-control.md`](print-control.md) §7 on why that row is missing.

<p><br/></p>

📚 **The ARGUMENTS live in [`hover-text-dl.md`](hover-text-dl.md)** — sections A1–A10, the single claimant for all of them. This file holds the decisions and the mechanism. It states conclusions and points; it does not restate reasoning. Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

---

## ✅ §0 — THE RULINGS

**13:0x** — the token is **`.role`**, the form is the **LINK** form, the gloss lives on a new page **TYPE**, it arrives via that page's **frontmatter**, and the page is also a destination worth visiting (*"we'll use that page as a potential actual like 'about this person' for the site anyways"*). 7 to 10, hand-minted. Safety site in scope.

<p><br/></p>

**14:30**, three parts:

> *"for now, no to pasting frontmatter hover field render on the local page anywhere — just for external hovers. also, possible to add an optional second field that is an override for at print so that the default is to print in a defined stylized way the hover text, or to use the override text if its there. BUT THEN on the external satellite page, when using .role, i should be able to say 'never print' for the role hover text at print maybe...."*

<p><br/></p>

| # | Ruling | Lands in |
|---|---|---|
| 1 | the gloss **never renders on the role page itself** | §13 |
| 2 | an **optional second field** overrides what PRINTS; default is the gloss | §9 |
| 3 | **per-instance suppression** at the point of use | §14 |

### ⭐ RULING 2 IS THE ONE THAT CHANGED THE BUILD, AND IT DISSOLVED THE BLOCKER

The opening ask was *"insert the person's name."* **Ruling 2 makes the printed default the GLOSS — the role definition — and a name reaches paper only if he types it into the override on one page, deliberately.**

<p><br/></p>

✅ **So there is no `holder:` field, and §12's PII question drops from STRUCTURAL to OPT-IN PER PAGE.** The previous revision of this spec parked ruling 1 as *"does a role page name its holder"* and called it blocking. **It is answered: no field, because the feature no longer needs one.** ⚑ *A question that was blocking a build stopped being blocking because the mechanism changed underneath it — which is the second time in this feature family that a refusal was answered by an intent rather than argued with, and it is worth checking for before re-raising any parked objection.*

---

## ⭐ §7 — THE ROLE PAGE TYPE: ONE YAML FILE, ONE TSV ROW

`objects/*.yml` populates `state.TYPES`; a page declares `type:` and `objects.py` holds it to the declaration. `venue.yml` is the precedent and is four lines.

### `objects/role.yml`

```yaml
type: role
label: Role
extends: _base
requires:
  - gloss
optional:
  - print_gloss
```

**`extends: _base` inherits `id`, `title`, `status` and `summary`**, so a role page is a real page with a lede, a URL, a revision date and an owner tag.

<p><br/></p>

🚫 **NO `renders:` DIRECTIVE, AND THAT IS RULING 1 EXPRESSED AS AN ABSENCE.** No `spec_table`, no `callout_if_missing`. See §13.

### One row in `theme/markers.tsv`

```
role	terminology	Role			role	A defined production role. The page behind it says what the role covers and who to ask.
```

🔴 **No new marker class.** A `role` class would be `plain` + `accent-2`, byte-identical to `terminology` in every cell — the J31 clone defect verbatim. Full argument: [dl A7](hover-text-dl.md#a7--why-no-new-marker-class-the-j31-clone-argument-in-full). ⚠️ Its one real cost (the report groups by class, so *"every role"* filters on the marker NAME) is costed there.

### 🔴 The id

`@role:theatre-administrator`, **not** `@role:role-theatre-administrator`. The prefix already namespaces it. [dl A8](hover-text-dl.md#a8--the-id-and-why-role-theatre-administrator-has-the-word-twice).

---

## 🔴 §8 — THE ONE REAL CODE CHANGE: THERE IS NO id → FRONTMATTER PATH TODAY

This is the whole build and it is small. `markerlinks._make.resolve` resolves against `state.PAGES`, which `links.on_files` builds:

```python
state.PAGES[page_id] = {
    "id": page_id,
    "type": meta.get("_type", "page"),
    "title": meta.get("title") or f.name,
    "url": f.url,
    "status": meta.get("status", "public"),
}
```

**Five keys, none of them the gloss.** The frontmatter is in `state.BY_SRC`, keyed by **`src_uri`**, not by page id. **So a resolver holding an id has no route to that page's frontmatter at all.**

<p><br/></p>

✅ **THE FIX IS AT THAT ONE CALL SITE, WHERE `meta` IS ALREADY IN HAND:** add `"gloss"` and `"print_gloss"`. `type` and `status` were added the same way and for the same reason — **a fact the published map needs about a page it already knows.** No second index, no reverse lookup, nothing cached that could go stale. `state.py`'s admission price is paid the way `REFS` pays it: the value is written in the branch that already computed it.

<p><br/></p>

⚠️ **`markerlinks` reads it off `hit`, NEVER off `BY_SRC`.** `PAGES` is built AFTER visibility prunes, which is the property that makes a link unable to resolve to an unbuilt page. Reading frontmatter directly reintroduces exactly that hole.

<p><br/></p>

⚠️ **AND THE LINK FORM DROPS THE TOOLTIP TODAY — BLOCKING.** `resolve` reads `class` and `shape` off the marker row and nothing else, so `[x]{.role}` has hover text and `[x](@role:y)` does not. **The form Michael ruled is the form with no hover text at all.** ⭐ Fixing it inverts the asymmetry the right way: the link form ends up carrying the RICHER gloss, and the link form is the one that writes an edge into `/doc-refs.json`. Also correct `markerlinks.py`'s docstring, which asserts the opposite in passing (*"colour, label, shape, tooltip — is re-read per build"*: true of the TABLE, false of the OUTPUT).

<p><br/></p>

⭐ **THE TYPE CHECK COMES FREE.** `hit["type"]` is already there, so `@role:` landing on a non-role page can be **reported** — the first real answer to `markerlinks`'s open *"`@rel:safety-policy` will happily point at a safety page"* note. 🚩 Report, never refuse: nothing in this family may fail a build.

---

## 🔴 §9 — PRINT INSERTION: THE FIRST ADDITIVE PRINT RULE IN THIS ENGINE

**Every print rule here today SUBTRACTS.** `flow.css` hides the iframe, `print-callout.css` strips the caret, `print-chrome.css` hides the flow strip and the site header, `views.py` hides the summary, the corner stamp dropped its PR number. The governing question has always been *what can a reader not act on with a pen.* **This rule ADDS text to his prose. That is a new category.**

<p><br/></p>

🔴 **AND THE ENGINE DELETED SOMETHING FOR LOOKING LIKE THIS THREE HOURS EARLIER.** PR #202 removed the view-embed caption on sight: *"the caption was the engine putting an editorial sentence in his content, in his voice, unasked."*

<p><br/></p>

✅ **THE TEST THAT LEGALISES THIS ONE, WRITTEN AS A RULE RATHER THAN LEFT A JUDGEMENT:** the caption was **engine prose**; this is **the author's own data**, typed by him, on a page he owns, reached through a reference he wrote. ⚑ **The engine may place a string on paper that it did not compose. It may never compose one.** That is the entire difference, and it generalises past both.

### The two fields, and the precedence

| Field | Screen (hover) | Paper |
|---|---|---|
| **`gloss`** (required) | ✅ the hover text | ✅ printed, **unless overridden** |
| **`print_gloss`** (optional) | — never rendered on screen | ✅ **wins when present** |

⭐ **ABSENT IS A REAL STATE AND MUST STAY DISTINGUISHABLE FROM EMPTY.** `print_gloss:` absent means *print the gloss*; `print_gloss: ""` means *print nothing*. 🔴 This is the distinction PR #201 had to retrofit onto `collapsed:` hours ago, where `false` and an omitted key produced identical output and a whole state was unreachable. **Build it in rather than discovering it: test `is None`, never falsiness.**

### Mechanism

`markerlinks` emits the resolved string as a data attribute; a print-only rule reveals it:

```css
@media print {
  .dr-mark--link[data-role-print]::after {
    content: " (" attr(data-role-print) ")" !important;
  }
}
```

⭐ **ONE ATTRIBUTE, RESOLVED IN PYTHON.** `markerlinks` picks `print_gloss` if present else `gloss` and writes the winner into `data-role-print`. **The CSS never sees two candidates**, so precedence cannot be expressed twice — the shape that killed three manifests. ✅ `attr()` inside `content` is the one universally supported use of `attr()`, and it keeps the string **in the HTML**: greppable, auditable, impossible for a stylesheet to have invented.

<p><br/></p>

🔴 **ITS ONE HONEST COST: `data-role-print` IS IN THE DOM ON EVERY PAGE ON EVERY BUILD, ON SCREEN.** *"Print-only" is a VISUAL claim and never a privacy one.* View-source shows it; a scraper gets it. This is why §12 still exists even though ruling 2 defanged it.

<p><br/></p>

⚠️ Two mechanical traps, named rather than discovered. **`print-flow.css` uses `display: revert !important` and has already beaten a plain declaration twice in this feature family** — so every declaration here carries `!important` and is verified in **Chrome** print preview, never WeasyPrint (which discards `revert`). And a `::after` on an inline run **can break across a line**, so the parenthesis wants the `white-space` treatment `.dr-mark` already carries.

---

## ⭐ §10 — THE FRONTMATTER TEST, AND RULING 1 MAKES IT THE PUREST PASS AVAILABLE

`space.yml`'s standing test, which killed six room fields and four venue fields on 2026-08-03: **"whether a value is needed AWAY from the page it appears on."** Full quotes: [dl A10](hover-text-dl.md#a10--the-frontmatter-test-quoted-in-full-because-it-decides-every-future-field).

<p><br/></p>

| Field | Read away from its own page? | Verdict |
|---|---|---|
| **`gloss`** | ✅ on every referencing page, as the hover **— and NOWHERE ELSE** | **earns frontmatter** |
| **`print_gloss`** | ✅ on every referencing page's paper | **earns it** |
| a phone number, an office, a term of appointment | ❌ only on the role page itself | **body prose** |

⭐ **RULING 1 TURNS A PASS INTO AN EXCLUSIVE PASS.** Before it, `gloss` was read away from its page **and** on it. Now it is read **only** away from it. **The test is not merely satisfied, it is satisfied exclusively** — the strongest form of the argument available, and 🚫 the reason `phone:` will never be legal here.

---

## 🔴 §11 — `gloss` IN `requires`, AND `print_gloss`'s CONSUMER SHIPS WITH IT

`objects._resolve` merges `optional` and **nothing ever reads it**. Three fields have already been found declared-and-unread: `revised:`, `related:` (found because Michael asked whether it rendered) and `data:` in the mirror direction. [dl A9](hover-text-dl.md#a9--the-optional-trap-and-the-three-fields-it-has-already-eaten).

<p><br/></p>

✅ **`gloss` goes in `requires:`**, which is genuinely checked and names the file and the field. **`print_gloss` is legitimately optional** — absence is a real state (§9) — **so its consumer must ship in the same PR as its declaration.** 🔴 Declaring it ahead of the print rule makes it the documented fourth instance, added by the session that read the warning.

---

## ⭐ §13 — THE GLOSS NEVER RENDERS ON ITS OWN PAGE (RULING 1)

> *"no to pasting frontmatter hover field render on the local page anywhere — just for external hovers."*

✅ **Expressed as an absence: `role.yml` declares no `renders:` directive at all.** `objects.on_page_markdown` only draws what a type declares, so a type declaring nothing draws nothing. **Nothing to suppress, no flag, no default to get wrong.** 🚩 And it must be written into `role.yml` as a RULING with the reason, or the next session adds a `spec_table` for tidiness and thinks it is filling a gap.

<p><br/></p>

⭐ **THE REASON IT IS RIGHT, WHICH IS SHARPER THAN THE INSTRUCTION.** `_base` already requires `summary:`, the lede — *"what this is and who needs it"*, rendered under the H1. **A gloss rendered on the role page would be a SECOND sentence answering the SAME question, six lines apart, from two fields nothing reconciles.** That is the two-claimants defect at the smallest possible scale, and 🔴 it is the one the `danger` callout, `roster.json` and `contrast.tsv` all died of.

<p><br/></p>

⭐ **So the two fields have two AUDIENCES and that is the whole design:** `summary` is written for somebody **on** the page; `gloss` is written for somebody **who never arrives**, reading a sentence on a different page about keys. *Two strings about one subject are safe exactly when they are answering different questions, and unsafe the moment they answer the same one.* ⚑ Which is why the on-page render was the right thing to refuse and the hover was the right thing to keep.

---

## 🔴 §14 — PER-INSTANCE `never print` (RULING 3), AND THE SYNTAX DOES NOT EXIST YET

> *"on the external satellite page, when using .role, i should be able to say 'never print' for the role hover text at print maybe...."*

### ✅ First: this does NOT reopen the per-instance refusal, and the distinction is load-bearing

[dl A3](hover-text-dl.md#a3--the-three-gloss-scopes-and-why-per-instance-content-is-refused) refuses a per-instance **gloss**, because a per-instance string is a second COPY of a fact and the day the role changes every page is wrong.

<p><br/></p>

⚑ **A `never print` flag carries no copy of the fact, so it has nothing to drift FROM. A second claimant is a second COPY; a switch is not a claimant.** Per-instance **content** stays refused; per-instance **visibility** is legitimate and always was — `indexed: false`, `contents: false`, `reload: false` and `print=true` are four existing per-instance visibility switches in this engine, none of which duplicate anything.

<p><br/></p>
🔴 **And there is a REASON to want it that argues for building it rather than merely permitting it:** a page that says *"go get your keys from the Theatre Administrator"* three times prints three identical parentheses. **The gloss is worth printing ONCE per sheet**, and only the author knows which mention is the one that matters.

### 🔴 BLOCKING: there is no legal place to put an option on an inline link

Read off the regexes, not assumed. `links._LINK` is:

```python
r"\[(?P<label>[^\]]*)\]\(@(?P<token>[A-Za-z0-9_.:-]+)(?P<anchor>#[A-Za-z0-9_-]+)?\)"
```

**It stops at the closing paren.** And `markerlinks.resolve` already returns a brace of its own:

```python
return "[" + label + "](" + target + anchor + "){ ." + " .".join(css) + " }"
```

🔴 **So `[x](@role:y){.no-print}` produces `[x](url){ .dr-mark--link … }{.no-print}` — two adjacent attr_list blocks.** attr_list consumes one. **The author's option is the one that loses**, and this is the same shape as the `align=center` failure three hours ago: an option written in good faith, silently doing nothing, **with no report line because nothing matched to report on.**

### Three mechanisms, costed

| | How | Cost |
|---|---|---|
| **A** widen `_LINK` to capture a trailing brace and merge it | ✅ general: any marker link could then take any class, a real gap today | 🔴 **touches every `@`-link on every site.** All FIVE branches of `replace()` must re-emit the captured brace or they silently eat author classes |
| **B** a second `markers.tsv` row with its own prefix (`@role-np:`) | ✅ **zero code, zero risk, data-only, reversible.** Same page, same gloss, same class | ⚠️ two prefixes for one idea, brushing `markers.tsv`'s own two-names warning |
| **C** a `print: false` on the ROLE page | ✅ cheapest of all | 🚫 **answers a different question** — per-entity, not per-instance. Does not give him what he asked for |

✅ **RECOMMEND B FOR v1** and 🚫 **refuse A as part of this build.** A is worth doing on its own merits and must not be smuggled in behind one boolean: *a five-branch change to the most-used regex in the engine, shipped for a flag, is how a feature takes down a site it had nothing to do with.*

<p><br/></p>

⚠️ **TWO THINGS I CANNOT VERIFY FROM HERE, STATED RATHER THAN REASONED PAST.** Whether attr_list eats one brace or both is **Python-Markdown's** behaviour, and it is **not installed and there is no network** — the same wall that stopped the markerlinks tooltip fix shipping on PR #197. And **hook 03b's `_MARK` pattern is unread**; `markerlinks`'s docstring says it *"matches a single-class attr_list block"* and would hand a miss back untouched, but a two-brace output is exactly the input nobody has tested it against. 🔴 **Two "tidy" mechanisms already failed a render test in this repo this week** (`var()` in `background-image`, `aspect-ratio`), both caught only by rasterising. **This wants one `mkdocs serve` before a line is written.** Option B needs neither check, which is a third argument for it.

---

## 🚩 §12 — PII: DOWNGRADED FROM BLOCKING TO OPT-IN, NOT RESOLVED

🔴 `mawizorek/uritp-docs` is **PRIVATE**; the safety site publishes **PUBLICLY**. Visibility is per-repo and **never carried between them** — they are the two most-confused repos in the fleet and their visibility is opposite.

<p><br/></p>

✅ **Ruling 2 removed the structural version of this problem.** There is no `holder:` field, and the printed default is the role definition. **A human's name enters the repo only when Michael types it into `print_gloss` on one page** — a deliberate act on a single file, not a schema that invites one.

<p><br/></p>

⚠️ **What remains, and it is real:** the moment he does that, **the name is in the DOM of every page referencing that role** (§9), on a public site, in search, in `/doc-index.json`. And **the assignment is a ClickUp fact** — URITP PEOPLE owns who holds a role, with a term attached — so a name in `print_gloss` is a snapshot `dead_links` cannot see rot.

<p><br/></p>

🚩 **Mitigation available and free:** `revised:` is already inherited from `_base` and already renders as the last line of the page. **A stale name with a visible date is a different object from a stale name with none.** Recommend it as a convention on role pages, not a required field — requiring it would put a second gate on the type for a problem only one optional field can create.

---

## ⏳ Rulings left — down from four to two

1. 🔴 **Popup or `title=`?** ✅ **Recommend the popup, and retire `title=` from `markers.py` in the same pass**, ending the three-verdict contradiction ([dl A2](hover-text-dl.md#a2--the-title-contradiction-one-engine-one-attribute-three-verdicts)). ⚠️ Cost: a real rewrite of the span renderer's output, and `markers.py` is **21,561 B** against a 22,528 ceiling with a history of taking every site down. **Measure at the moment you act; the rationale goes in a sidecar, never in the module.**
2. **Headings?** He asked for *"prose or header."* ⚠️ A heading is also a nav label, a TOC entry and an anchor target: four surfaces, one string. ✅ **Recommend prose and table cells in v1**, headings named as deliberately excluded rather than forgotten.

<p><br/></p>

🪦 **ANSWERED, no longer open:** *does a role page name its holder* (ruling 2 removed the field) · *own marker class or a `terminology` row* (the row — dl A7) · *is there a `@person:` prefix* (no: `@role:`, and the type IS the tightening `markerlinks` asked for).

---

## Files and sizes

**Measured from a directory listing at HEAD, 2026-08-30. ⚠️ Every number below will be wrong within days — `flow.css` moved 2,365 B in one morning and a PR shipped "three bytes under" against a file already 957 B over. Read it back at the moment you act.**

| File | Now | Change |
|---|---|---|
| `docrender/links.py` | 16,596 B | **+2 dict keys** in `on_files`. §8, and it is the whole unlock |
| `docrender/markerlinks.py` | 13,047 B | reads the gloss off `hit`, resolves the print precedence, emits the attributes, corrects its own docstring. Room |
| **NEW** `objects/role.yml` | — | ~12 lines incl. the §13 ruling |
| `theme/markers.tsv` | — | one row (two under §14 option B) |
| `docrender/markers.py` | **21,561 B** | 🔴 967 B of headroom. **Ruling 1 lands here or nowhere**, and only with a sidecar |
| `docrender/objects.py` | **22,423 B** | 🔴 **105 B of headroom. Nothing may be added here.** A role-page check belongs in `markerlinks` |
| `assets/print-*.css` | — | §9's block. 🚩 `print-type.css` had **239 B** headroom on 08-29 and its own note says the next edit must SPLIT it first |
| `specs/hover-text-dl.md` | 15,490 B | the arguments. Single claimant |
