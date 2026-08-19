# BUILD 5 — `chrome:` — page chrome as a folder-scoped declaration

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-18. Scoped by Dev Dexter.

> Michael, 2026-08-18: *"is it possible to take it a step further that when landing on a page with more front matter tags that we define or know about, you can hide like ALL excess site content besides just the formatted prose... no search bar. no header bar icon access back to the home page... no bottom page 'previous' and 'next' markers."*
>
> And, on scope: *"the whole goal is to make the page read like a single document — no hamburger menu necessary... unless you were saying we can limit it to select FOLDERS via an INDEX file as well and keep sub nav within a small branch... i do want that but you said it was too hard before."*

One sentence: **a page or folder declares how much of the site's chrome it wears**, so a document can read as a standalone document, or a subtree can read as its own small site, without either one becoming a separate MkDocs build.

Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

---

## §0 🔴 THE CORRECTION THIS SPEC OPENS WITH, BECAUSE IT IS MINE

**Scoping this in chat I wrote `type: course` and `type: guide` in two example frontmatter blocks. NEITHER TYPE EXISTS.** Michael caught it in three words: *"did you invent?"*

The real set, read out of `objects/` at HEAD `747bec3` rather than recalled:

```
_base  index  page  procedure  reference  space  standard  venue
```

⭐ **The mechanism is worth more than the apology, and it is already written down in Dexter's memory in a different costume: *a guess wearing the clothes of a measurement is camouflaged by the real measurements around it.*** Every other key in those two blocks was real — `id`, `title`, `status`, `nav`, `router` — all verified against `README.md` §3 minutes earlier. The invented values sat in the middle of correct ones and read as equally checked. **The examples in this file therefore use only types that exist, and the frontmatter contract in README §3 is the source, not memory.**

⚠️ **AND THE INVENTION POINTED AT A REAL GAP, WHICH IS WHY IT WAS PLAUSIBLE.** `courses/` on `uritp` is a live 43-page tree with no `course` type; those pages are typed from the existing set. **That is a legitimate question for another day and it is NOT part of this build.** Naming it here so nobody reads the correction as an argument for inventing the type.

---

## §1 The proposal: TWO values, and why it cannot be a boolean

`chrome:` in frontmatter. Two values, each with a bare alias, matching the `nav:` vocabulary's own rule that a family where only one value has a short form is a family you have to remember:

| value | alias | what the reader gets |
|---|---|---|
| `bare` | — | no sidebar, no prev/next, header reduced to an inert wordmark. A document. |
| `branch` | — | sidebar renders **only the current branch**; header keeps its utilities, loses the home link. A small site. |
| *(absent)* | | **inherit**, then the site default: full chrome. The normal case. |

🔴 **A BOOLEAN CANNOT EXPRESS THIS, AND THAT IS THE WHOLE ARGUMENT FOR THE SCOPE.** Michael's two sentences describe two different pages. *Reads like a single document, no hamburger* is one treatment. *Keep sub nav within a small branch* is the **opposite** treatment — it wants navigation, just less of it. A single `chrome: off` flag would force one of those two requests to be dropped, and §2's permutations are the evidence that both are wanted on the same site.

⚠️ **`bare` and `branch` are ALTERNATIVES, never a stack.** They are two answers to one question, so a page resolves to exactly one. This is unlike `nav:` + `status:`, which are orthogonal and compose.

---

## §2 The five permutations, and what each is FOR

These are the use cases the two values plus the existing keys have to cover. They are distinct in **audience**, **permission** and **navigation**, which is what justifies a vocabulary rather than a flag.

### P1 — the standalone handout *(a leaf page)*

```yaml
---
id: mewp-quickstart
title: MEWP Pre-Use Checklist
status: public
type: procedure
chrome: bare
---
```

**At that URL:** no left sidebar, no right TOC (ruling 2), no prev/next, header is an inert wordmark. Prose from the top of the viewport down. Nothing clickable but the links in the body. Reads like a handed-over PDF.

**Unchanged:** still built, still a live URL, still resolves by `@id`, still in search. `chrome:` is a **curtain on the FURNITURE**, in exactly the sense `nav: hidden` is a curtain on the sidebar — and in neither case is it `status:`.

**For:** a document that will be linked to directly, printed, or handed over. The reader did not browse in and is not going to browse on.

### P2 — a folder of self-contained documents *(the folder-scoped ask)*

```yaml
# safety/policies/index.md
---
id: safety-policies
title: Safety Policies
status: public
type: index
nav: hidden
chrome: bare
---
```

**At the index URL:** bare. **At every page beneath it:** bare, by inheritance — one declaration, fourteen policies.

**And `nav: hidden` does the complementary half:** the folder keeps its own row for readers elsewhere on the site, and its children leave the sidebar, so nobody browses *into* the pile. They arrive from a table on the index. `courses/course-info/` is the reference case for that pattern already.

⭐ **P2 is the permutation that answers the literal ask** — *limit it to select FOLDERS via an INDEX file* — and it needs **no new cascade logic** (§3).

### P3 — the scoped mini-site *(the "too hard" one, and it is not)*

```yaml
# courses/thtr-341/index.md
---
id: thtr-341
title: THTR 341 Stage Lighting
status: public
type: index
chrome: branch
---
```

**At any URL under it:** the sidebar renders this course's branch and nothing else — no sibling courses, no other departments. Header keeps its utilities and loses the home link. Prev/next stays *inside* the branch, because stage `00c` already rebuilds the chain from whatever survived the earlier stages. It feels like it has its own website; you leave by an authored link or the back button.

**For:** a subtree with its own audience, where the rest of the site is noise rather than context.

### P4 — the mini-site, fully open

```yaml
# guides/designers/index.md
---
id: designer-guides
title: Designer Guides
status: public
type: index
nav: expanded
chrome: branch
---
```

P3, with the whole subtree open on arrival. Right for a six-page guide where there is nothing to gain from making the reader click.

⚠️ **IT CARRIES A DOCUMENTED SITE-WIDE COST AND THE COST IS NOT NEW.** README §7: one `nav: expanded` anywhere drops `navigation.prune` for **every page on the site**, roughly 33% of page weight. `chrome:` neither causes nor fixes that. It is listed here because P4 is the permutation somebody will reach for casually, and `expanded` is never casual.

### P5 — the gated single document *(the permissions permutation)*

```yaml
# production/big-love/contracts/index.md
---
id: bl-contracts
title: Big Love — Contracts
status: public
type: reference
router: <code>
nav: routed
chrome: bare
---
```

**Before a code:** the folder is not in the sidebar at all. **After a correct code:** the folder appears, and every page inside reads bare — no drawer, no prev/next, nowhere to wander.

⭐ **P5 IS THE PERMUTATION THAT JUSTIFIES THE WHOLE SCOPE, because it proves the two keys are ORTHOGONAL.** `router:` decides **who gets in**. `chrome:` decides **what they can do once inside**. Neither substitutes for the other, and there is no combination of the existing keys that expresses *withheld, and then non-browsable*.

🚫 **And it must not be read as access control.** README §7 already says `status: gated` is unimplemented and that shipping a gate which merely looks like one is worse than shipping none. **A bare page is not a protected page.** `chrome: bare` removes the furniture a reader could click; it removes nothing a reader could type, guess, or find in search.

### The cascade override, which is the sixth arrangement and comes free

`chrome: bare` on `safety/policies/` with `chrome: branch` on `safety/policies/mewp/` = a folder of standalone documents with one sub-branch that keeps its own drawer. Same shape as root `expanded` with a `collapsed` subfolder, and it falls out of §3 rather than being built.

---

## §3 Mechanism — and the honest split between free and additive

### What is FREE TODAY, verified in Material's source at `squidfunk/mkdocs-material@master`

| ask | mechanism | state |
|---|---|---|
| kill prev/next | `hide: footer` | ✅ **works right now** |
| kill the sidebar | `hide: navigation` | ✅ works right now |
| kill the TOC | `hide: toc` | ✅ works right now |

`partials/footer.html` sets `hidden` on `md-footer__inner` when `"footer" in page.meta.hide`, gated behind `navigation.footer` — **which this engine enables**, so the gate is live. `base.html` does the same for `"navigation"` and `"toc"`, the latter gated on `toc.integrate` being ABSENT, which it is.

⭐ **So one third of the ask needs no build at all**, and any spec that did not say so would be selling work that already exists.

### 🔴 What is NOT free: the header is gated by NOTHING

`base.html` renders the header as a bare `{% block header %}{% include "partials/header.html" %}{% endblock %}`. **There is no `page.meta.hide` check anywhere near it, at any version.** Reading `partials/header.html`, `md-header` contains, in order: the `md-logo` home link · the drawer hamburger (`<label for="__drawer">`) · `md-header__title` (site name + page title) · the palette toggle · the search button · repo info (gated on `repo_url`, which this engine forbids outright).

**Everything Michael asked to remove and everything he asked to KEEP lives in one element.** That is the finding that shapes the build: *"no header bar icon access back to the home page (i'm fine with the color changer or the search bar...)"* is not a hide, it is a **reduction**.

### Delivery: the 06b precedent, not a `custom_dir`

One attribute on `<body>` in `on_post_page`, plus CSS. `navstate.py` already does exactly this and its docstring carries the argument: forking a Material partial into a `custom_dir` is *"a copy of somebody else's truth that we then maintain forever — the defect that killed roster.json, registry.json and app-index.md,"* and doing it client-side flaps the chrome on every page load.

⭐ **It inherits 06b's safety property: the pass only ever ADDS an attribute, to a tag it has fully matched, and hides via CSS.** Nothing is removed from the DOM, so the worst available failure is a page wearing more chrome than it asked for. **Fail-open, on the surface a reader navigates by.**

### The cascade: reuses `_walk`, and I am NARROWING my own earlier claim

In chat I said `chrome:` *"reuses that resolver verbatim."* **Half true, and the half that is wrong is the half that costs work.**

- ✅ **The cascade genuinely is verbatim.** `navstate._walk` already threads an `inherited` value down the tree, reads the declaration off each section's `index.md`, and lets a descendant override. `chrome:` is another value on that walk.
- 🔴 **The LEGALITY is not.** `nav:` is folder-index-only and *enforces* it — `_misplaced()` reports the key on any other page, because a folder's open state is a fact about the FOLDER. **Chrome is a fact about a PAGE's rendering**, so P1's leaf declaration is legitimate rather than a mistake. That is a second, different legality rule, and it is additive.

⚠️ **AND `objects/*.yml` VALIDATES NEITHER.** `objects/index.yml` states it plainly about `nav:`: *"THIS IS A RECORD, NOT AN ENFORCEMENT. objects.py checks `requires` and never reads `optional`."* So listing `chrome:` under `optional:` puts it in the spec a reader consults and in `doc-index.json`, and validates nothing. **Do not mistake the listing for a check** (ruling 3 decides which types get the listing).

---

## §4 Contradictions to REPORT, never guess

This engine has a settled habit for unsatisfiable frontmatter — `unlisted` + `nav: hidden` is reported with the one-word fix and the safe behaviour is taken. Same treatment here:

| declaration | why it cannot be satisfied | behaviour |
|---|---|---|
| `nav: hidden` + `chrome: branch` | hidden strips the folder's children from the sidebar; branch asks for a sidebar OF those children. **A drawer with nothing in it.** | render full-branch or fall back to `bare` — **ruling 4** |
| `chrome: bare` + `chrome: branch` on one page | two answers to one question | last wins is a guess. **Refuse and report**, the way a bad `nav:` value falls back to the default with a named reason |
| root `index.md` declaring `chrome:` | legal and load-bearing — it is the SITE default | ✅ allowed. This is the `nav:` root precedent, and unlike `nav: hidden` at the root there is nothing pathological about a whole site of bare documents |

---

## §5 ⏳ Rulings needed (four)

**1. 🔴 SEARCH CANNOT BE PAGE-LOCAL, AND HE ASKED FOR IT TO BE.** *"i'm fine with the color changer or the search bar if its only local to that page."* Material builds ONE index for the whole site; there is no page-scoped index and no feature flag that produces one. So the honest options are **keep site-wide search on a bare page** (and accept the result list is an exit from the document) or **drop it**. There is no third answer, and picking one quietly would be implementing a request that cannot be met.

⚠️ **AND A PRIOR QUESTION MUST BE ANSWERED ON A RENDERED PAGE FIRST.** `partials/header.html` gates the search button on `"material/search" in config.plugins`. This engine registers `plugins: - search`. **Whether that resolves to the same key is NOT determinable from the template**, and if it does not, the search button is *already* absent from every site and half of ruling 1 is moot. 🚫 **Do not assert either way from this file** — open a live page and look. This repo has paid repeatedly for a conclusion drawn from a read that could not have contradicted it.

**2. Does `bare` keep the TOC?** ⭐ **The TOC is the one piece of chrome that gets BETTER as a page gets longer**, and a bare 4,000-word policy is precisely where a right-hand contents list earns its place. It is also the one Michael did not mention. `hide: toc` already exists, so this is a question about the DEFAULT inside `bare`, not about capability. **Recommend: `bare` keeps the TOC**, and an author who wants it gone adds `hide: toc` — one existing key, no new value.

**3. Leaf pages, or folder indexes only?** P1 versus P2. This decides whether `chrome:` is a sibling of `status:` (per-page, listed on every type in `objects/`) or of `nav:` (per-folder, listed only on `index.yml` and reported everywhere else). **Recommend: both legal, per-page.** A page's own rendering is the page's business, and refusing P1 means a one-off handout needs a folder built around it.

**4. `nav: hidden` + `chrome: branch` — which side yields?** **Recommend: report it and render the full branch.** The precedent in `navstate._walk` for the `unlisted` + `hidden` clash is to take the OFFERING behaviour and report, on the grounds that a heading which expands to nothing is worse than a visible extra row.

---

## §6 Files and sizes

🔴 **NO SIZE TABLE IN THIS SPEC, ON PURPOSE, AND THIS IS THE FILE'S OWN LESSON APPLIED FORWARD.** `next-build-spec.md` carries the finding verbatim: *"A size written into prose is wrong within two days, every time, in this repo. Measure at the moment you act, never quote this table"* — and it earned that line by having its own numbers rot in 48 hours, changing an INSTRUCTION rather than just a figure.

**What to measure at build time, and the two that are already known to matter:**

- **NEW** `docrender/chrome.py` — the resolver, the `on_post_page` pass, the contradiction reports. Its own module. 🚫 **Do not append to `navstate.py`.**
- **NEW** `assets/chrome.css` — a file of this name **already exists** (created by the link-colour PR #89) and holds THE ARMOUR. Read it before assuming the name is free; this may be an edit, not a create.
- `docrender/navstate.py` — export the cascade, or grow a shared walker. ⚠️ README §5 measured it at 25,631 B on 2026-08-07, **already past the 22KB ceiling, and that figure is eleven days old.** Re-measure before touching it.
- `mkdocs.yml` — two hook registrations, and 🔴 **the ORDER is a real constraint, not a formality.** A chrome stage reading the nav tree must run after `00bc` (the seal) for the same reason `00bd` had to be split out of `00bb`: a folder sealed behind a router is still `expanded` to a stage that asks too early. **Read `hooks/README.md` before choosing the number.**
- `objects/*.yml` — the `optional:` listing, scope decided by ruling 3.

---

## §7 Sequence

1. **Answer ruling 1's PRIOR question by looking at a rendered page.** It is free, it takes one look, and it may delete a third of the surface.
2. **Ship `hide: footer` on one real page today.** Zero engine change, and it is the cheapest possible proof that the reduced-chrome page reads the way Michael wants before anything is built for it.
3. **`bare` first, `branch` second.** `bare` is CSS against a flag and needs no nav-tree reasoning at all. `branch` needs the stage-order question in §6 answered.
4. **The cascade last.** A single-page `bare` proves the treatment; the cascade only decides how many pages get it.

🚫 **Do not start with `branch`.** It is the piece that looks like the feature and it is the one carrying the ordering trap that cost `uritp` eleven days of full nav trees.

---

## §8 Known limits, stated now rather than discovered

- **`navigation.instant` IS ABSENT FROM `mkdocs.yml`, AND THIS DESIGN DEPENDS ON THAT.** A server-rendered body attribute survives an instant-loading XHR swap, so enabling instant navigation later would leak bare chrome onto the next page a reader clicks. ⚠️ **That is a tripwire on a feature nobody has asked for yet, which is exactly when it is cheapest to write down.**
- **Print is a separate surface and is NOT covered here.** `print.css` already strips the edit link and forces a white background, and `specs/scoped-theme.md` §4c flags that sheet as fragile under scoped selectors. A bare page and a printed page want nearly the same thing and must not be wired to each other by accident.
- **`chrome: branch` hides sidebar rows with CSS; it does not remove them from the DOM.** Deliberate — removal is what makes a post-processing pass dangerous. Consequence stated plainly: **a determined reader can see the full tree in view-source.** Same class of claim as `nav: hidden` being a curtain, and for the same reason it is fine: `status:` is the feature that controls what reaches the site.
- **No mobile drawer on a `bare` page, by request.** Michael, 2026-08-18: *"no hamburger menu necessary."* My objection that this leaves a phone with no navigation was **dissolved rather than answered** — a standalone document does not want navigation on any device. ⚠️ It does not apply to `branch` at all, which keeps the drawer with a smaller tree in it.
- **This is not `status: gated` and it is not a theme.** Chrome is furniture. `status:` controls publication, `router:` controls admission, a theme is site-wide for one build (README §7). `chrome:` touches none of those three.
