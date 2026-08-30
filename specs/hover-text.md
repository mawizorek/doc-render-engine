# BUILD 9 · HOVER TEXT AND THE ROLE PAGE

✅ **DECISION-COMPLETE, NOT YET BUILT.** Scoped 2026-08-30, **ruled four times the same day** (§0). **Every ruling is closed.** Indexed from [`next-build-spec.md`](../next-build-spec.md) — 🚩 see [`print-control.md`](print-control.md) §7 on why that row is missing.

<p><br/></p>

📚 **The ARGUMENTS live in [`hover-text-dl.md`](hover-text-dl.md)** — sections A1–A10, the single claimant for all of them. This file holds the decisions and the mechanism. Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

<p><br/></p>

🔴 **ONE BLOCKING DEPENDENCY LEFT, mechanical, not a decision:** a TSV cell silently drops the gloss today (§15). ✅ The `assets.py` blocker is **CLEARED** (§16). **Nothing is waiting on Michael.**

---

## ✅ §0 — THE RULINGS, ALL CLOSED

**13:0x** — the token is **`.role`**, the form is the **LINK** form, the gloss lives on a new page **TYPE**, it arrives via that page's **frontmatter**, and the page is also a destination worth visiting. 7 to 10, hand-minted. Safety site in scope.

<p><br/></p>

**14:30** — (1) the gloss **never renders on the role page itself**, external hovers only · (2) an **optional second field** overrides what PRINTS, default is the gloss · (3) **per-instance suppression** at the point of use.

<p><br/></p>

**14:54** — *"DEFINITELY b, duh … prose only is fine, but tsv tables and other should still count"*

<p><br/></p>

**15:00** — *"just pick an existing marker style, like layout or link … but know that I'll want to swap it easily or edit it later. don't suggest adding new color vector though."* Plus: **do the `assets.py` split.**

<p><br/></p>

| Ruling | Answer | Lands in |
|---|---|---|
| popup or `title=` | **the styled popup** | §16 |
| headings | **excluded from v1** | §17 |
| TSV tables and everything else | **in scope** | §15, §17 |
| **which existing style** | **`terminology`** — `layout` refused on REPORTING grounds | **§18** |
| does a role page name its holder | **no field at all** (ruling 2 removed the need) | §12 |
| own marker class | **no**, a `terminology` row | [dl A7](hover-text-dl.md#a7--why-no-new-marker-class-the-j31-clone-argument-in-full) |
| a `@person:` prefix | **no** — `@role:`, and the TYPE is the tightening `markerlinks` asked for | §7 |

### ⭐ THE SECOND HALF OF HIS 14:54 SENTENCE WAS THE MOST EXPENSIVE FOUR WORDS IN THE BUILD

*"tsv tables and other should still count"* reads like a scope confirmation. **It is a blocking defect report** — see §15. Had the surfaces question been answered as *"prose only, tables later,"* this would have shipped, worked in prose, and been silently dead in every table on the safety site.

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

**`extends: _base` inherits `id`, `title`, `status` and `summary`**, so a role page is a real page with a lede, a URL, a revision date and an owner tag. 🚫 **No `renders:` directive** — that is ruling 1 expressed as an absence (§13).

### One row in `theme/markers.tsv`

```
role	terminology	Role			role	A defined production role. The page behind it says what the role covers and who to ask.
```

🔴 **No new marker class**, and the class it takes is ruled in §18. [dl A7](hover-text-dl.md#a7--why-no-new-marker-class-the-j31-clone-argument-in-full).

### 🔴 The id

`@role:theatre-administrator`, **not** `@role:role-theatre-administrator`. The prefix already namespaces it. [dl A8](hover-text-dl.md#a8--the-id-and-why-role-theatre-administrator-has-the-word-twice).

---

## 🔴 §8 — THE CORE CODE CHANGE: THERE IS NO id → FRONTMATTER PATH TODAY

`markerlinks._make.resolve` resolves against `state.PAGES`, which `links.on_files` builds:

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

✅ **THE FIX IS AT THAT ONE CALL SITE, WHERE `meta` IS ALREADY IN HAND:** add `"gloss"` and `"print_gloss"`. `type` and `status` were added the same way and for the same reason — **a fact the published map needs about a page it already knows.** No second index, no reverse lookup, nothing cached that could go stale.

<p><br/></p>

⚠️ **`markerlinks` reads it off `hit`, NEVER off `BY_SRC`.** `PAGES` is built AFTER visibility prunes, which is the property that makes a link unable to resolve to an unbuilt page.

<p><br/></p>

⚠️ **The link form drops the tooltip today** — `resolve` reads `class` and `shape` and nothing else. Fixing it inverts the asymmetry the right way, since the link form is the one that writes an edge into `/doc-refs.json`. Also correct `markerlinks.py`'s docstring, which asserts the opposite in passing.

<p><br/></p>

⭐ **The type check comes free.** `hit["type"]` is already there, so `@role:` landing on a non-role page can be **reported**. 🚩 Report, never refuse.

---

## 🔴 §9 — PRINT INSERTION: THE FIRST ADDITIVE PRINT RULE IN THIS ENGINE

**Every print rule here today SUBTRACTS.** ⚑ **The engine may place a string on paper that it did not compose. It may never compose one.** That is the whole difference between this and the caption PR #202 deleted, and it generalises past both. [dl A6](hover-text-dl.md#a6--the-struck-paper-section-and-the-test-that-still-governs).

### The two fields, and the precedence

| Field | Screen (hover) | Paper |
|---|---|---|
| **`gloss`** (required) | ✅ the hover text | ✅ printed, **unless overridden** |
| **`print_gloss`** (optional) | — never on screen | ✅ **wins when present** |

⭐ **ABSENT IS A REAL STATE AND MUST STAY DISTINGUISHABLE FROM EMPTY.** Absent means *print the gloss*; `print_gloss: ""` means *print nothing*. 🔴 The distinction PR #201 had to retrofit onto `collapsed:`, where `false` and an omitted key produced identical output and a whole state was unreachable. **Test `is None`, never falsiness.**

### Mechanism

```css
@media print {
  .dr-mark--link[data-role-print]::after {
    content: " (" attr(data-role-print) ")" !important;
  }
}
```

⭐ **ONE ATTRIBUTE, RESOLVED IN PYTHON.** `markerlinks` picks `print_gloss` if present else `gloss` and writes the winner. **The CSS never sees two candidates**, so precedence cannot be expressed twice. ✅ `attr()` in `content` is the one universally supported use of `attr()`, and it keeps the string in the HTML: greppable, auditable, impossible for a stylesheet to have invented.

<p><br/></p>

🔴 **ITS ONE HONEST COST: the attribute is in the DOM on every page on every build, on screen.** *"Print-only" is a VISUAL claim and never a privacy one.* §12.

<p><br/></p>

⚠️ **`print-flow.css` uses `display: revert !important` and has already beaten a plain declaration twice in this feature family**, so every declaration here carries `!important` and is verified in **Chrome** print preview, never WeasyPrint (which discards `revert`). A `::after` on an inline run can break across a line, so the parenthesis wants the `white-space` treatment `.dr-mark` already carries.

---

## ⭐ §10 — THE FRONTMATTER TEST, AND RULING 1 MAKES IT AN EXCLUSIVE PASS

`space.yml`'s standing test, which killed six room fields and four venue fields: **"whether a value is needed AWAY from the page it appears on."** [dl A10](hover-text-dl.md#a10--the-frontmatter-test-quoted-in-full-because-it-decides-every-future-field).

<p><br/></p>

| Field | Read away from its own page? | Verdict |
|---|---|---|
| **`gloss`** | ✅ on every referencing page **— and NOWHERE ELSE** | **earns frontmatter** |
| **`print_gloss`** | ✅ on every referencing page's paper | **earns it** |
| a phone number, an office, a term of appointment | ❌ only on the role page itself | **body prose** |

⭐ **RULING 1 TURNS A PASS INTO AN EXCLUSIVE PASS**, which is the strongest form of the argument available and 🚫 the reason `phone:` will never be legal here.

---

## 🔴 §11 — `gloss` IN `requires`, AND `print_gloss`'s CONSUMER SHIPS WITH IT

`objects._resolve` merges `optional` and **nothing ever reads it**. Three fields have already been found declared-and-unread. [dl A9](hover-text-dl.md#a9--the-optional-trap-and-the-three-fields-it-has-already-eaten).

<p><br/></p>

✅ **`gloss` goes in `requires:`.** **`print_gloss` is legitimately optional**, so its consumer must ship in the same PR as its declaration — or it is the documented fourth instance, added by the session that read the warning.

---

## ⭐ §13 — THE GLOSS NEVER RENDERS ON ITS OWN PAGE (RULING 1)

✅ **Expressed as an absence: `role.yml` declares no `renders:` directive.** `objects.on_page_markdown` only draws what a type declares. **Nothing to suppress, no flag, no default to get wrong.** 🚩 Write it into `role.yml` as a RULING with the reason, or the next session adds a `spec_table` for tidiness and thinks it is filling a gap.

<p><br/></p>

⭐ **THE REASON IS SHARPER THAN THE INSTRUCTION.** `_base` already requires `summary:`, the lede. **A gloss rendered on the role page would be a SECOND sentence answering the SAME question, six lines apart, from two fields nothing reconciles.** The two-claimants defect at the smallest possible scale.

<p><br/></p>

⭐ **The two fields have two AUDIENCES and that is the design:** `summary` is for somebody **on** the page; `gloss` is for somebody **who never arrives**. *Two strings about one subject are safe exactly when they answer different questions, and unsafe the moment they answer the same one.*

---

## 🔴 §14 — PER-INSTANCE `never print` (RULING 3), AND THE SYNTAX DOES NOT EXIST YET

✅ **This does NOT reopen the per-instance refusal.** [dl A3](hover-text-dl.md#a3--the-three-gloss-scopes-and-why-per-instance-content-is-refused) refuses a per-instance **gloss** because a per-instance string is a second COPY. ⚑ **A `never print` flag carries no copy of the fact, so it has nothing to drift FROM. A second claimant is a second COPY; a switch is not a claimant.** Four existing precedents: `indexed: false`, `contents: false`, `reload: false`, `print=true`.

<p><br/></p>

🔴 **BLOCKING: there is no legal place for an option on an inline link.** `links._LINK` stops at the closing paren, and `markerlinks.resolve` already returns a brace of its own — so `[x](@role:y){.no-print}` yields **two adjacent attr_list blocks and the author's option is the one that loses**, silently, **with no report line because nothing matched to report on.** Same shape as the `align=center` failure earlier today.

<p><br/></p>

| | How | Cost |
|---|---|---|
| **A** widen `_LINK` to capture and merge a trailing brace | ✅ general: any marker link could take any class | 🔴 **touches every `@`-link on every site.** All five branches of `replace()` must re-emit it or they silently eat author classes |
| **B** a second `markers.tsv` row with its own prefix (`@role-np:`) | ✅ **zero code, zero risk, data-only, reversible** | ⚠️ two prefixes for one idea |
| **C** `print: false` on the ROLE page | ✅ cheapest | 🚫 **answers a different question** — per-entity, not per-instance |

✅ **RECOMMEND B FOR v1**, 🚫 **refuse A as part of this build**: *a five-branch change to the most-used regex in the engine, shipped for a flag, is how a feature takes down a site it had nothing to do with.* ⭐ **And §15 raises B's value: option B needs no attribute at all in a cell**, so it is the only one of the three that works in a table without §15's fix.

---

## 🔴 §15 — A TSV CELL SILENTLY DROPS THE GLOSS. THE LAST REAL BLOCKER.

> *"tsv tables and other should still count"*

**They do not, and the reason is four lines of `cells.py`.** A cell is rendered at stage **01b** by `cells.render`, which delegates to `links` and `markers` and then finishes the inline markdown itself. Its link handler keeps only CLASSES:

```python
_CLASS = re.compile(r"\.([A-Za-z][\w-]*)")

def _classes(attrs: str) -> str:
    """`{ .dr-term .dr-mark--cls-terminology }` -> a class attribute."""
    found = _CLASS.findall(attrs or "")
    if not found:
        return ""
    return ' class="' + html.escape(" ".join(found), quote=True) + '"'
```

🔴 **SO EVERY NON-CLASS ATTRIBUTE IS DROPPED INSIDE A CELL.** `data-role-print` (§9) and the popup's own text (§16) both vanish. **The link still renders, still resolves, still lands in the build report** — only the gloss disappears, and only in tables. ⚠️ **On the safety site the tables are the surface most likely to name a role**, and a table full of correct-looking links with no hover is indistinguishable from a feature nobody enabled.

<p><br/></p>

⚑ **AND THE SHAPE IS THIS REPO'S OLDEST ONE, ONE LAYER FURTHER OUT THAN USUAL: a helper NAMED for the one attribute it was written to carry, standing in a position where any attribute now has to pass.** `_classes` is not wrong and was never wrong — **it is NARROWER THAN ITS POSITION**, and its docstring and its name both describe the narrow job so convincingly that nothing invites you to check. Same family as the eyebrow welded to a TYPE, `:first-child` assuming an identifier, and `tr:not(:has(td.dr-detail))` against an emitter that always emits. ⭐ *The tell, available in advance and cheap: when a NEW kind of value starts flowing through an old pipe, read the pipe rather than the value.*

<p><br/></p>

✅ **THE FIX, IN `cells.py` (9,660 B, room):** an **allowlisted** attribute pass-through beside `_classes` — `data-role-print` and the gloss attribute, named explicitly.

<p><br/></p>

🚫 **REFUSED: a wildcard pass-through of every attribute.** `cells.py`'s own docstring states the posture it would break: *"RAW HTML IN A CELL IS TRUSTED … This module escapes the literal text it finds between constructs; it does not sanitise."* Trusting **typed HTML tags** is the bargain the content tree already makes; **silently forwarding arbitrary key-value pairs out of a TSV** is a different one, and the TSVs on a public site are the least-reviewed content in the tree. **Allowlist, escaped with `quote=True`, exactly as `_classes` already does.**

<p><br/></p>

✅ **Sorting is unaffected and verified: `plain()` strips `{…}` blocks entirely and keeps a link's LABEL**, so a glossed role in a cell still sorts as its own text and `number()` still refuses it as non-numeric. **The one constraint Michael called non-negotiable** (*"we absolutely cannot lose the number functionality"*) **is untouched by this build.**

---

## ✅ §16 — THE POPUP (RULING: "DEFINITELY B")

The mechanism is already built and proven in `buildstamp.py`: hidden with **`opacity`**, not `display`, plus `pointer-events: none`, absolutely positioned, and a `tabindex="0"` host revealed on `:focus-visible`. **The accessibility argument is quoted in full in [dl A2](hover-text-dl.md#a2--the-title-contradiction-one-engine-one-attribute-three-verdicts).**

### 🚫 THE `markers.py` SPAN REWRITE IS OUT OF SCOPE FOR v1, AND THE REASON IS MEASURED

- `markers.py` is **21,561 B** against a 22,528 ceiling — **967 B.**
- A popup is not an attribute swap. It is a **nested-element rewrite** of the span renderer's output, plus escaping, plus the `tabindex` host.
- 🔴 **That module's history includes taking every site down at config-load time** (2026-08-05, the `_token_sets` ImportError), and it is imported by `blocks.py`, `markerlinks.py` and `cells.py`.

✅ **THE LINK FORM IS NET-NEW CODE IN `markerlinks.py` (13,047 B, room) AND GETS THE POPUP WITH NO CEILING PROBLEM.** That is the form Michael ruled and the only form that can carry an entity gloss.

<p><br/></p>

🚩 **THE COST, NAMED IN BOTH FILES RATHER THAN LEFT FOR A COLD SESSION:** the span form keeps `title=` and the link form gets a popup, so **one engine will have two hover mechanisms** until the span rewrite ships. ⚑ *That is a KNOWN divergence with a written owner, which is a different object from the unknown divergence [dl A2] describes — where two files disagreed and neither mentioned the other.* Write the pointer in both directions, in the same PR.

### ✅ THE CSS NOW HAS A LEGAL HOME — BLOCKER CLEARED 2026-08-30

**Re-measured this pass:**

| Sheet | Now | Verdict |
|---|---|---|
| `docrender/assets.py` | ✅ **13,943 B** | **SPLIT, PR #216.** Was 32,684 B and past the write cap. History moved to `assets-dl.md`; every function byte-identical; read back whole |
| `assets/base.css` | **21,190 B** | 🚫 ~1.3KB headroom. Not the popup's home |
| `assets/flow.css` | **23,163 B** | 🔴 already past the ceiling |
| `assets/type.css` | 5,937 B | ⚠️ wrong owner — it is the type ramp |
| **NEW** `assets/gloss.css` | — | ✅ **correct home, and now registerable** |

🚫 **`gloss.css` WAS DELIBERATELY NOT PRE-REGISTERED IN THE SPLIT PR.** It would have been one line and it is the wrong line: the sheet does not exist, and `assets.py`'s own standing rule is that **a sheet is registered in the same PR as the sheet itself** — the 08-21 `print-chrome.css` omission is the whole argument against a two-step. See [`assets-dl.md`](../docrender/assets-dl.md) D6.

<p><br/></p>

⚠️ **PRINT PARITY IS PART OF THE POPUP, NOT A FOLLOW-UP.** The popup must be **hidden on paper** — §9 already prints the gloss inline, so a visible popup would print the same fact twice. 🔴 And `print-flow.css`'s `display: revert !important` has beaten a plain `display: none` **twice in this feature family this week**, so the rule carries `!important` and both selector spellings, gated on a popup actually being **emitted**.

---

## ✅ §17 — THE SURFACES: "AND OTHER SHOULD STILL COUNT", ANSWERED STRUCTURALLY

⭐ **The right answer is not a list, because `markerlinks` does not emit HTML — it emits MARKDOWN back into the stream.** So it works **wherever inline markdown works**, and that is a property rather than a feature set. Free, with no per-surface code:

<p><br/></p>

✅ prose · **TSV table cells** (once §15 lands) · markdown table cells · list items · callout bodies · blockquotes · the `summary:` lede · a `related:` entry · inside `**bold**` or `*emphasis*`

<p><br/></p>

| Surface | Why not |
|---|---|
| **code fences and backticks** | 🚫 `util.sub_outside_code` skips them **by design** — a page documenting `[x](@role:y)` has not referenced a role, and reading its example as real would corrupt the reference graph |
| **headings** | ✅ **his ruling.** A heading is also a nav label, a TOC entry and an anchor target: four surfaces, one string |
| **figure captions** | ⚠️ `figure.py`'s regex allows only `caption="…"` in the brace, so there is **no authoring path**. Logged 2026-08-29 as a pre-existing gap; **not caused by this build and not fixed by it** |

⚠️ **ONE HONEST NOTE ON TABLES:** `data.css` gives a cell `white-space: nowrap`, and 🔴 a marker note clipping at a cell edge has already been logged twice in this repo (J25 defect 4, J26). **A popup is absolutely positioned so it escapes the cell box — but it can escape a horizontally-scrolling grid too**, and that is the one thing in §16 that cannot be reasoned about from source. Verify in a real table.

---

## ✅ §18 — THE STYLE: `.role` TAKES THE `terminology` CLASS

> *"just pick an existing marker style, like layout or link … but know that I'll want to swap it easently or edit it later. don't suggest adding new color vector though."*

✅ **`terminology`** — `shape: plain`, `color: accent-2`. Coloured text, no chrome, no new token, no CSS. **Its own label in `marker-classes.tsv` already reads *"a defined term, with or without a page behind it,"* which is what a role is**, so the class needs no amendment to accept it.

### 🔴 `layout` REFUSED ON REPORTING GROUNDS, NOT ON LOOKS — and that is the half worth recording

On looks it would have been fine. **`layout` is the FileMaker LAYOUT MODE family** (owner: FMP Fiona): a button, a field, a portal, *"something you place on a screen."*

<p><br/></p>

⚑ **THE ENTIRE RETURN OF THE CLASS SYSTEM IS THAT EACH CLASS ANSWERS ONE QUESTION.** `marker-classes.tsv` says so outright: two families exist rather than one `fmp` because *"one family answers 'show me the FileMaker things,' which nobody needs. Two answer 'every relationship' and 'every control' separately, and the report is only worth reading while each class answers ONE question."* **Putting roles in `layout` makes *every control on this FileMaker layout* return theatre staff.** 🔴 A **colour** collision is explicitly permitted in this engine by Michael's own 08-09 ruling; a **REPORT** collision is the exact thing classes were invented to prevent. *Those are not the same kind of collision and the file only forgave one of them.*

<p><br/></p>

⚠️ **Second, independent reason: `layout` is `box`.** The `schema` family is `plain` precisely because *"a boxed chip in every cell of a .tsv is a wall"* — and §15/§17 just put roles **into table cells**. `terminology` being `plain` is not a coincidence; it is the same decision already made for the same reason.

### ⚠️ `link` IS NOT A CLASS. IT IS A FORM, AND HE ALREADY HAS IT.

`.dr-mark--link` is what `markerlinks` adds to **every** marker link for the underline, **regardless of family** — `markers.py` calls that underline *"the only difference a reader sees"* between the two forms.

<p><br/></p>

✅ **So there was nothing to pick there: every `@role:` reference gets the link styling by construction.** Named rather than quietly answered, because the sentence offered two options and one of them was a category error — *answering only the half that parsed is how a misunderstanding survives into a build.*

### ⭐ SWAPPABILITY NEEDS NOTHING BUILT. IT IS ALREADY THREE CELLS.

His *"I'll want to swap it easily or edit it later"* is **the existing design**, not a requirement to engineer. Three independent levers, every one **a single cell in `theme/markers.tsv`**, zero Python and zero CSS:

<p><br/></p>

| Lever | Cell | Effect |
|---|---|---|
| **whole family** | `class` | `terminology` → any other row in `marker-classes.tsv`. Inherits that family's shape AND colour |
| **shape only** | `shape` | overrides the family per row: `box` · `plain` · `strike` · `soft`. **Four, because a reader can distinguish four at a glance and cannot distinguish nine** |
| **colour only** | `color` | overrides the family per row. ⚠️ **Prefer inheriting, then a TOKEN, and only then a hex** — a token follows the theme into light mode and onto every other site; a hex is frozen where you typed it and will be wrong on the scheme you were not looking at |

✅ **And his constraint is already honoured: none of the three adds a colour vector.** Every value above is a token that exists.

### 🔴 THE ONE TRAP HE WILL ACTUALLY HIT, WHICH IS WHY THIS SECTION IS NOT A ONE-LINE CONFIRMATION

**`accent-1` DOES NOT EXIST.** The canonical palette is **`accent`**, **`accent-deep`**, **`accent-2`**, **`accent-soft`** — there is no `-1` anywhere in it.

<p><br/></p>

⚠️ **It validates as a legal token NAME, resolves to NOTHING, is reported once per build, and paints in the body colour** — so the marker silently stops looking marked, on a page that looks otherwise fine. `markers.tsv` already calls it *"the natural thing to type once `accent-2` exists."* ⚑ **A man who has just said he will edit the colour cell later is the exact person that trap is set for**, which is the whole reason it belongs in this spec and not only in the TSV header.

<p><br/></p>

🔴 **Same family, one row over: `accent-soft` is a tinted GROUND, not a text colour** — it measures **1.4:1** on the eos dark canvas. It was in the `terminology` cell for two days, the validator refused it, everyone read the report line as *"not vendored yet,"* and **the graceful fallback to body colour is the only reason nobody noticed the cell was also wrong.** ⚑ *A broken reference that degrades gracefully can hide a second, worse mistake underneath it.*

### ⚠️ The one cost of sharing a class, restated so a swap is an informed choice

**The build report groups by CLASS**, so *"every role on this site"* is a filter on the marker NAME rather than its own group. The report line is `class · name · page · label → target`, so the name is present and the question stays answerable. **That is the only argument for a class of its own**, and it costs a colour decision plus a chip contrast measurement — measured against the chip's **own wash**, never against the page. [dl A7](hover-text-dl.md#a7--why-no-new-marker-class-the-j31-clone-argument-in-full).

---

## 🚩 §12 — PII: OPT-IN, NOT RESOLVED

🔴 `mawizorek/uritp-docs` is **PRIVATE**; the safety site publishes **PUBLICLY**. Visibility is per-repo and **never carried between them.**

<p><br/></p>

✅ **Ruling 2 removed the structural version of this problem.** No `holder:` field, and the printed default is the role definition. **A human's name enters the repo only when Michael types it into `print_gloss` on one page** — a deliberate act on a single file, not a schema that invites one.

<p><br/></p>

⚠️ **What remains:** the moment he does, the name is in the DOM of every page referencing that role (§9), on a public site, in search, in `/doc-index.json`. And **the assignment is a ClickUp fact** — URITP PEOPLE owns it, with a term attached — so a name in `print_gloss` is a snapshot `dead_links` cannot see rot.

<p><br/></p>

🚩 **Free mitigation:** `revised:` is already inherited and already renders as the last line. **A stale name with a visible date is a different object from a stale name with none.**

---

## ✅ Build order

1. ✅ ~~Split `assets.py`~~ **DONE, PR #216.** 32,684 → 13,943 B, zero behaviour change, read back whole.
2. **`links.py`** — two dict keys (§8). The unlock, and independently harmless.
3. **`cells.py`** — the allowlisted attribute pass-through (§15). 🔴 **Before any table is authored**, or the first table teaches him the feature is broken.
4. **`objects/role.yml`** + the `markers.tsv` row (§7, §18), with the §13 ruling written in.
5. **`markerlinks.py`** — read the gloss off `hit`, resolve the print precedence, emit the popup, fix the docstring, add the divergence pointer (§16).
6. **NEW `assets/gloss.css`** — popup, focus-visible, print suppression. ✅ **Registered in `assets.py` in the SAME PR** (§16).
7. **One `mkdocs serve`** — §14's two-brace behaviour, and the popup inside a scrolling table (§17).
8. **Chrome print preview** — §9's parenthesis and §16's suppression. ⚠️ WeasyPrint cannot verify either.

---

## Files and sizes

**Re-measured from HEAD, 2026-08-30 15:0x. ⚠️ Re-measured rather than carried, because a previous revision of this very table quoted `base.css` at 20,335 B when it was 21,190 — it had moved.**

| File | Now | Change |
|---|---|---|
| `docrender/assets.py` | ✅ **13,943 B** | **split, PR #216.** `gloss.css` is now registerable |
| `docrender/links.py` | 16,596 B | **+2 dict keys**. §8 |
| `docrender/markerlinks.py` | 13,047 B | the gloss, the precedence, the popup, the docstring. Room |
| `docrender/cells.py` | **9,660 B** | 🔴 the allowlist. §15. Plenty of room |
| **NEW** `objects/role.yml` | — | ~12 lines incl. the §13 ruling |
| `theme/markers.tsv` | — | one row, class `terminology` (§18). Two rows under §14 option B |
| **NEW** `assets/gloss.css` | — | ✅ unblocked |
| `assets/base.css` | **21,190 B** | 🚫 ~1.3KB. Not the popup's home |
| `docrender/markers.py` | **21,561 B** | 🚫 967 B. **Span rewrite deferred, §16** |
| `docrender/objects.py` | **22,423 B** | 🔴 **105 B. Nothing may be added here** |
| `docrender/assets-dl.md` | 21,151 B | the assets history. Single claimant |
| `specs/hover-text-dl.md` | 15,490 B | the arguments. Single claimant |
