# BUILD 5 — the print layer SPLIT, PRINT TYPOGRAPHY, and a printed STAMP

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-19, out of the URITP Safety fire-policy print session. Indexed from [`next-build-spec.md`](../next-build-spec.md). Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

**Three asks, in the order they arrived, which is the reverse of the order they should be built:**

1. *"i want to adjust the print styling yes. lets split that file out if we need"*
2. *"a small logo potentially rendered on the top of the page or something that we define too so lets spec the printing mechanism to be a little more professional looking"*
3. ⭐ *"and general LINE SPACING - that's the big one. we should make the print feel a little more like printed markdown text scale and less like rendered webpage at that point."*

✅ **RULED 2026-08-19, and the ruling SHRANK this document.** Michael, on where the identity mark goes: *"just just sheet one. and maybe its even just a tag in the footer of page one. like super 'database stamp' style and not 'this is a webpage' print."* Both halves of that changed the build — see §1 and §4.

---

## One line

Split `assets/print.css` at a real seam, **re-typeset the paper** (leading first), and put a small **database-stamp** mark in the foot rather than a letterhead at the top.

---

## ⭐ §0 — THE REFRAME: TYPOGRAPHY IS THE SUBSTRATE, IDENTITY IS THE GARNISH

The original scope put the mark first, because that is what was asked for. **Ask 3 inverts that, and it is correct.**

<p><br/></p>

🔴 **A MARK ON BADLY TYPESET PAPER LOOKS WORSE THAN NO MARK.** Adding identity to a page whose leading is set for a scrolling screen produces something that looks like a web page with a logo on it — a more specific kind of unprofessional than a plain print, because now it is *trying*.

<p><br/></p>

⭐ **AND THE FRAMING IS A REAL TYPOGRAPHIC ARGUMENT, NOT A PREFERENCE.** Generous leading exists on screen for reasons that are all about the screen: ~96dpi rendering with soft stem edges, a backlit emissive ground, and an unbounded scroll where vertical space is free. **Paper is ~300+dpi, reflective, and bounded** — crisp stems, subtractive contrast, and every millimetre of leading paid for in sheets. So a tighter print layer is not a degraded screen design. **It is the same content typeset for a different medium, which is what a print stylesheet is for.** First time this engine has had reason to say that out loud; it belongs in the header of whatever file lands.

---

## ✅ §1 — SHEET ONE. RULED, AND THE ANSWER DELETED HALF THIS SECTION

The blocking question was whether *"the top of the page"* meant every sheet or sheet one. **Michael: sheet one.** Recorded, and the consequence is that a whole branch of this build is now closed rather than merely unlikely:

<p><br/></p>

🚫 **NO PAGINATOR.** A true running header needs CSS Paged Media `@page` margin boxes (`@page { @top-center { content: element(x) } }`), which **no major browser implements** — Chrome and Firefox support `@page` for `size` and `margin` only, exactly the subset `print.css` already uses, and that is not a coincidence. Margin boxes belong to Prince, WeasyPrint and Paged.js, none of which is in this pipeline. **That evaluation is now formally out of scope**, not deferred.

<p><br/></p>

⚠️ **THE `position: fixed` DIVERGENCE STILL MATTERS, AND THE RULING INVERTED WHICH SIDE IS "WRONG."** A fixed element repeats per sheet in **Firefox** and prints once, on sheet one, in **Chrome**. Under the old letterhead-on-every-sheet reading, Chrome was the broken one. **Under this ruling Chrome is exactly right and Firefox over-delivers** — the same rule, the same divergence, opposite verdicts. 🔴 **Neither is a design.** A mark that appears once for one reader and six times for another, with nothing reporting it, is the silent-divergence shape this repo has logged against `em` container queries (Orion vs Blink, PR #82) and the `bad`/`danger` token mismatch. §4b is how it gets avoided.

<p><br/></p>

🚫 **AND NOT THE `<table>` TRICK.** Wrapping all content in a table so `thead` repeats via `display: table-header-group` — which this print sheet already exploits for real tables — is a layout lie and it breaks `break-inside` on everything nested inside it. Refused in advance.

---

## §2 — THE SPLIT

`assets/print.css` is **22,844 B** (measured 2026-08-19, after PR #132), past the ~22 KB ceiling where a file stops coming back whole from one read and therefore stops being safely editable. `type.css`, `nav.css`, `data.css` and `chrome.css` all left `base.css` for exactly this reason.

<p><br/></p>

⚠️ **IT IS COMMENT-DOMINATED, NOT RULE-DOMINATED.** The rules are short; the reasoning is long, and the reasoning is why anybody can safely touch it. **A split that shortens the file by deleting argument is a regression disguised as hygiene.** Every note travels with the rule it explains.

<p><br/></p>

**The seam is the one the file already argues for in its own header** — *"what appears on paper at all, how wide it runs, and where the page is allowed to break"* — plus the third job ask 3 adds:

<p><br/></p>

| File | Owns | The one question it answers |
|---|---|---|
| **`assets/print.css`** (stays) | `@page`, chrome-off, column unrailing, slate→light neutrals, `print-color-adjust`, link policy | **What the sheet IS** |
| **`assets/print-flow.css`** (NEW) | `break-*`, `orphans`/`widows`, h1–h6, tab-label protection, forced-open `<details>`, `thead` repetition, `{.new-page}` | **Where it BREAKS** |
| **`assets/print-type.css`** (NEW, §3) | leading, block spacing, list spacing, callout density, optional ramp — **and the stamp** (§4) | **How it is SET** |

<p><br/></p>

⭐ **THREE SHEETS, NOT FOUR — AND THAT IS THE RULING'S SECOND SAVING.** The earlier scope wanted `print-identity.css`. A letterhead is a layout component; **a foot stamp is three or four typographic declarations**, and a separate sheet for it would be a file whose comments outweigh its rules by ten to one. It rides in `print-type.css`. If it ever grows a logo block big enough to argue about, it earns its own file then.

<p><br/></p>

⭐ **THE FORCED-OPEN `<details>` RULE GOES WITH FLOW, WHICH IS NOT OBVIOUS.** It looks like a *what appears at all* rule — it makes withheld content appear. It belongs with flow because **it is the rule that creates the pagination problem the rest of that file solves**: force seven collapsed panels open and you have invented seven new break hazards. Cause beside consequence beats filing by verb.

<p><br/></p>

### 🔴 §2a — SOURCE ORDER IS THE SPLIT'S REAL HAZARD, AND TWO SPECS ALREADY WARN

`print.css` states twice that its position is load-bearing: it publishes AFTER generated `tokens.css` (its slate overrides re-point the same custom properties at the same specificity — lose that tie and a dark-mode reader prints pale ink on white paper, silently) and BEFORE an instance's `site.css`.

<p><br/></p>

⚠️ **EVERY NEW SHEET INHERITS THAT SANDWICH.** Order lives in `docrender/assets.py` (`_DATA_ASSETS`; **15,226 B** — verify the list's name and shape at build). Three sheets where one sat means three chances to insert one wrongly, and **the failure mode is a blank-looking page rather than an error.**

<p><br/></p>

🔴 **`specs/scoped-theme.md` §4c ALREADY FOUND THE ADJACENT BUG:** a scoped selector silently kills `print.css` on the pages it scopes, because that sheet wins on source order at equal specificity and a two-attribute scope outranks it. **Written about one sheet; after this split it applies to three, and a scope could kill one and spare the others** — a page that paginates correctly but prints in web leading. Whichever of BUILD 3 and BUILD 5 lands second re-reads the other's note.

---

## ⭐ §3 — PRINT TYPOGRAPHY: LEADING IS THE BIG ONE

### §3a — why leading beats every other lever, without needing a measured number

**Leading is the only property here that multiplies across the whole document.** Box padding is paid once per box, so its total is bounded by how many boxes a page happens to have. **Leading is paid once per LINE**, and a reference document is almost entirely lines. Reduce it by *n*% and the document loses very nearly *n*% of its height, on every page, in every section.

<p><br/></p>

⭐ **THAT HOLDS WITHOUT KNOWING THE CURRENT VALUE**, which is why the lever order below is decidable now and only the final number needs measuring.

<p><br/></p>

✅ **VERIFIED AT HEAD:** grepping `line-height` returns **four hits, and not one is body prose** — `data.css` (1.35 on cells, 1.4 on a wrapped cell), `data-list.css` (1.35), `navtree.css` (1.5). **Prose, list and callout leading are Material's, unmodified, on screen and therefore on paper.** Nothing in this engine has ever had an opinion about the leading of a sentence.

<p><br/></p>

⭐ **THE HOUSE ALREADY HAS A DENSE-CONTENT PRECEDENT: 1.35**, chosen twice for content whose job is to be scanned. Not the print answer — a data cell is one line, a policy paragraph is six — but the print value should be argued *against* it rather than invented from nothing.

### 🔴 §3b — THE ONE HARD CSS RULE: UNITLESS, NEVER `em`

- **Unitless** (`1.4`) inherits as a **ratio**, recomputed against each descendant's own `font-size`. A code block, a table cell and an `h2` each get leading proportional to themselves.
- **`em`/`rem`** inherits as a **computed LENGTH**. Every descendant gets the same absolute leading regardless of its size — cramped headings and airy small print on one page.

<p><br/></p>

⚠️ **THIS IS THE `em` TRAP FROM PR #82 AND #80 IN A THIRD COSTUME.** That family already cost two reverts: a bridge row mapping two-axis padding onto a one-axis primitive, and a container query whose `45em` resolved against the wrong font size. **A relative unit is only relative to something, and the something is rarely what you meant.** `.md-typeset` is the element whose whole documented hazard is em-relativity (`type.css`), so it is the worst possible place for a length-valued line-height.

### §3c — "LINE SPACING" IS THREE PROPERTIES AND THEY MUST NOT BE COLLAPSED

| # | Property | Governs | Symptom when loose |
|---|---|---|---|
| **1** | `line-height` | space **within** a paragraph | the page reads airy, screen-like |
| **2** | `p` / heading `margin` | space **between** blocks | sections drift; headings float |
| **3** | `li` margin + list `padding` | space **between** bullets | a 4-item list eats a third of a sheet |

<p><br/></p>

🔴 **NUMBER 3 IS MOST LIKELY TO BE MISDIAGNOSED, AND THE FIRE POLICY IS MOSTLY LISTS.** Material spaces list items with margin, not leading, so tightening `line-height` alone leaves a bulleted list exactly as tall and **the fix looks like it failed.** ⚠️ It also pays back the numbering fix handed to Michael on 2026-08-19: nesting a callout inside list item 5 makes that list LOOSE, adding paragraph spacing to all eight items. **Judge both on the same sheet, not separately.**

### §3d — the type ramp: the other half of "less like a rendered webpage"

**Heading sizes are set for screen hierarchy**, where an `h1` competes with chrome, a sidebar and a scroll position. On paper the page boundary does that work, so a compressed ramp reads as a document rather than a landing page. Smaller lever than leading, more visible.

<p><br/></p>

⚠️ **IT SITS ON A FACE NOBODY CHOSE.** `type.css` records that the typography vector's font FACES have never rendered on any site: `theme.font` is unset, so Material's loader fetches Roboto while `base.css` renames the variables to `Inter`/`IBM Plex Mono`, which resolve against nothing and fall through to `system-ui`. **So part of the "webpage feel" is that every heading is large system-ui sans.** 🚫 Not this build's fix — it is Michael's ruling between a third-party font request and committing binaries — but a print ramp designed on an accidental face should be known, not discovered.

### §3e — box chrome, the second lever

✅ **VERIFIED AT HEAD: nothing in this engine sizes or pads a callout.** `admonition` appears in `assets/` only in `chrome.css` (a shadow token, `--md-admonition-bg-color`) and `print.css` (`print-color-adjust`). Callout metrics are Material's, and **`print.css` governs breaks, width, colour and never density.**

<p><br/></p>

⭐ **THE COST IS ARITHMETIC, NOT TASTE.** On the fire policy, four `???+` boxes each carrying ONE sentence consume roughly half of sheet one. A `???+` is a `<details>` — cheap on screen precisely because it collapses — and `print.css` force-opens all of them. **The shape chosen to make a screen read compact is the most expensive shape available on paper**: padding, border, title bar and inter-box margin paid four times for four sentences.

<p><br/></p>

**Lever order:**

1. **Leading** (unitless). Highest ratio of space recovered to risk taken, and it is what was asked for.
2. **Block and list spacing** (§3c items 2–3). Without this, lists do not move and the leading change looks half-broken.
3. **Callout padding and inter-box margin.**
4. **The type ramp** (§3d).
5. **A print base font size**, LAST and possibly never.

<p><br/></p>

⭐ **LEVER 5 IS THE ONE PLACE `fs-body` IS SAFE.** `type.css` refuses `.md-typeset { font-size: var(--dr-fs-body) }` because every size inside `.md-typeset` is em-relative, so one line makes **every word on the site** 12.5% bigger — the blast radius that forced the PR #82 revert Michael reported as *"the font in the TABLE is massive."* **That objection is about SITE-WIDE scope. Inside `@media print` the blast radius is one medium**, reversible in one line, invisible to anyone who never prints. The refusal stands unamended; the scope was the whole objection.

### ⚠️ §3f — THERE IS A FLOOR, AND THIS IS A SAFETY DOCUMENT

**Tighter is not monotonically better and the stopping point is not aesthetic.** A printed safety policy gets **photocopied**, and ink spread closes the gaps that separate tight lines. It gets read **standing up in a shop or a dim corridor** by somebody hunting one rule, and scanning is more leading-dependent than reading.

<p><br/></p>

⚠️ `unverified`: **WCAG 2.1 SC 1.4.12 (Text Spacing)** names a 1.5× line-height expectation, and its applicability to a FIXED print medium is genuinely unclear — the criterion is about content supporting user-applied spacing, which paper cannot do either way. Body, designation and clause cited; **not confirmed against published text this session, so it must not be quoted as settled.** 🔴 **Hazard Hawthorne owns the legibility floor for safety-critical print** — his lane, not the engine's, and a craft head is easiest to omit exactly when the generalists are doing well.

### 🔴 §3g — RE-TYPESETTING INVALIDATES EVERY MANUAL BREAK, IMMEDIATELY

`print.css` already warns, in the note shipped in PR #132 an hour before this section existed, that `{.new-page}` *"is correct on the day it is typed and nobody is told when it stops being correct."*

<p><br/></p>

⭐ **THIS BUILD IS WHAT MAKES THAT WARNING COME TRUE.** Tighter leading means more lines per sheet, so every hand-placed break shifts and one that sat perfectly at web leading can leave a half-empty sheet. **Actionable today: do not author `{.new-page}` across the doc tree until the leading lands.**

<p><br/></p>

⚠️ **AND IT RE-EXERCISES PR #132's BREAK POLICY.** More lines per sheet moves every break, so `orphans: 3`, the heading rule and the tab-label protection all get a different workout. **Preview both changes on the same sheet**, because a pagination oddity afterwards could belong to either.

---

## §4 — THE STAMP

> Michael: *"maybe its even just a tag in the footer of page one. like super 'database stamp' style and not 'this is a webpage' print."*

⭐ **THIS IS A FOLD-IN, NOT A NEW COMPONENT, AND THE THING IT FOLDS INTO IS ALREADY THERE.** `buildstamp.py` (hook 07) already writes a foot mark and `print.css` already argues, at length, for keeping it on paper: *"a printed page leaves the system entirely — it gets handed to a guest artist, filed, carried into a room months later — and the one question nobody can answer about a piece of paper is how old it is."* Michael has now described the visual treatment that line always wanted. **The build is: restyle the stamp for paper and let it carry identity as well as date.**

<p><br/></p>

### 🔴 §4a — THE STAMP IS ALMOST CERTAINLY NOT PRINTING TODAY. VERIFY THIS FIRST.

`buildstamp.py` emits its mark as **`config.copyright`**, which Material renders inside its footer meta region. `print.css`'s chrome-off list contains **`.md-footer-meta { display: none !important }`**, and then separately sets `.buildstamp { display: block }`.

<p><br/></p>

🔴 **`display: none` ON AN ANCESTOR REMOVES THE WHOLE SUBTREE FROM THE BOX TREE. A DESCENDANT CANNOT OPT BACK IN.** If the stamp is nested inside `.md-footer-meta`, the carefully argued exception has been dead since the day it was written — **the provenance line this engine insists on keeping is absent from every printed page**, and the comment explaining why it survives is the only evidence it was ever meant to.

<p><br/></p>

⚠️ **STATED AS A STRONG SUSPICION, NOT A FINDING, AND THE REASON IS THE HOUSE RULE.** The nesting is from knowledge of Material's footer structure, **not read off its compiled template this session** — and a proxy read presented as a verification is exactly the failure logged in `instances/uritp-safety/site.yml` over the `database` theme claim. ⚠️ **The two fire-policy PDFs cannot settle it either way**: that page carries `hide: [footer]` in its own frontmatter, so no footer could print there regardless. **Print any page WITHOUT `hide: footer` and look.** If the stamp is missing, this is a live bug that predates the whole build.

<p><br/></p>

⭐ **AND IT IS THE PERFECT FIRST STEP ANYWAY.** §2's split has to touch the chrome-off list, the fix is a selector change rather than new machinery, and **a stamp that does not print cannot be restyled.**

<p><br/></p>

### §4b — "footer of page one" is harder than "top of page one", and the honest answer is END OF DOCUMENT

**Top of sheet one is free**: it is the first element in the flow, no pagination knowledge required. **Bottom of sheet one is not.** Landing a mark at a page boundary means knowing where that boundary falls, which is precisely what `@page` margin boxes do and browsers do not implement (§1).

<p><br/></p>

| Option | Verdict |
|---|---|
| **End of the content flow** — where the stamp already sits | ✅ **Recommended.** Zero new mechanism. On a ONE-SHEET document this IS the footer of page one, exactly as asked. On a longer document it lands at the end, which is where a document stamp belongs anyway. |
| `position: fixed; bottom: 0` | 🚫 Refused. Chrome gives sheet one only; **Firefox repeats it on every sheet.** §1's divergence, and no rule can tell them apart. |
| A paginator | 🚫 Out of scope by §1. |

<p><br/></p>

⚠️ **SO THE ONE HONEST CAVEAT TO GIVE MICHAEL: on a three-sheet policy the stamp is at the foot of sheet three, not sheet one.** That is the whole gap between what was asked and what a browser can do, and it is small — a document stamp at the end of the document is the conventional place for one.

<p><br/></p>

### §4c — "DATABASE STAMP" IS A STYLING DIRECTION AND IT IS A GOOD ONE

The register Michael named — a record-footer mark, not web furniture — resolves to a short list of decisions, and **every one of them is a subtraction:**

<p><br/></p>

- **Monospace.** `--dr-font-mono` already exists and is already a token. Mono is the single strongest signal of *this is a record, not prose*.
- **Small and quiet.** Faint ink, already the case (`#555`).
- **A rule above it, and one already exists** — `pagefoot.py` emits `<hr class="pagefoot__rule">` for the edit link. ⚠️ Both `.pagefoot` and its rule are in the chrome-off list, so on paper there is no rule today. The stamp wants that hairline back.
- **One line, field-separated.** `URITP Safety · Fire Prevention Policies · PR #157 · 19 Aug 2026` reads as a record; the same facts stacked read as a footer.
- 🚫 **No logo, and §1's ruling is what makes that defensible.** Michael's *"maybe its even just a tag"* is the cheaper half of his own ask, and it is better: an image needs a `site.yml` key, a resolver, and the `images.py` relative-path arithmetic **this repo shipped wrong three separate times** (`links.py`, `router.py`, `datatable.py`). A text stamp needs none of that. ⭐ **The cheapest version of a request is worth hunting for before the expensive one gets built.** If a mark is wanted later it is a new ruling with a known cost.

<p><br/></p>

### ⚠️ §4d — ONE STAMP, NOT TWO, AND THE PROVENANCE SEAM CHANGED SHAPE

The earlier scope split these deliberately: letterhead carries IDENTITY at the top, buildstamp keeps DATE at the foot, two facts at two ends. **The ruling collapses them into one place, so that separation is gone and the risk inverts:** instead of two marks at two ends, there is now one line that must carry both without becoming a paragraph.

<p><br/></p>

🔴 **A SECOND FOOT MARK WOULD BE A SECOND CLAIMANT ON PROVENANCE**, the shape this repo has retired three manifests over. **The stamp is extended, never duplicated.** Whatever the site name and page title need to say, they say inside `buildstamp.py`'s existing single element.

<p><br/></p>

⚠️ **AND `buildstamp.py` RUNS AT `on_config`, WHICH IS ONCE PER BUILD, NOT ONCE PER PAGE.** `config.copyright` is a global string. **A stamp naming the PAGE TITLE cannot be built there** — it needs a per-page hook, and that is a real mechanism change rather than a string edit. ⏳ **Ruling 3** asks whether the page title is wanted at all; the site name, PR and date are all global and free.

---

## 🔴 §5 — THIS BUILD MOVES BUILD 4's TARGET FILE

**[`specs/draft-watermark.md`](draft-watermark.md) §4 names `assets/print.css` as the home of the print DRAFT stamp**, beside the edit-on-git strip and the white-background rule.

<p><br/></p>

⚠️ **After this split that instruction is wrong**, and §2's drop to three sheets makes it wronger: there is no `print-identity.css` to inherit it. A DRAFT watermark is an overlay — not *what the sheet is*, not *where it breaks*, not *how it is set* — so it needs a home chosen deliberately rather than by elimination.

<p><br/></p>

**Whichever build lands first updates the other's spec in the same PR.** ⭐ J29: *the commit that moves a thing is the only commit that still remembers where it was.*

---

## ⏳ Rulings needed

1. ✅ **CLOSED 2026-08-19: sheet one, and a foot tag rather than a letterhead.** Paginator out of scope, `print-identity.css` out of scope, logo out of scope.
2. **How far does the leading go, and what is the floor?** (§3a, §3f) A measurement against a rendered sheet at Letter and A4, argued against the house's 1.35 dense-content precedent. **Hawthorne reads the legibility floor** for safety print.
3. **Does the stamp name the PAGE, or only the site?** (§4d) Site name + PR + date is free. Page title needs a per-page hook — real work for one line of text.
4. **Does the type ramp compress too** (§3d), knowing the face is `system-ui` by accident? **Recommend deferring** until the font question is ruled.
5. **🔴 Is the typography change opt-in or global?** It lands on all six sites at merge, unlike the stamp. **Recommend global** — it corrects a default nobody chose — but say it out loud rather than let somebody find it on a printer.
6. **Should `???+` on a print-heavy page be advice rather than CSS?** (§3e) Four one-sentence boxes are a **content** shape, and no stylesheet makes four boxes as cheap as a four-item definition list. About how Michael writes, not about the engine.

---

## Files and sizes (measured at HEAD 2026-08-19 — RE-MEASURE AT BUILD)

| File | Now | Change |
|---|---|---|
| `assets/print.css` | **22,844 B** | **−10 to −13 KB.** Keeps only *what the sheet is*. ⚠️ Its chrome-off list is where §4a's bug lives. |
| **NEW** `assets/print-flow.css` | — | ~9–11 KB. Break policy verbatim, comments intact. |
| **NEW** `assets/print-type.css` | — | ~5–7 KB. Leading, block/list spacing, callout density, the stamp, optional ramp. |
| `docrender/assets.py` | 15,226 B | +small. Two registrations, **in the correct order** (§2a). |
| `docrender/buildstamp.py` | **2,892 B** | +small, and only if ruling 3 wants more than the site name. ⚠️ `on_config` is once per BUILD. |
| `docrender/pagefoot.py` | **2,613 B** | untouched. Named because it owns the `<hr>` §4c wants back. |
| `docrender/tokenaudit.py` | 24,295 B | ⚠️ untouched, but it **AUDITS this work** — `line-height` is already in `_METRIC_PROPS`, so every value §3 adds appears in the token audit. Expect new rows and read them. |
| **NOT** `docrender/instance.py` | 23,047 B | ⭐ **The ruling spared it.** No `print:` config block, so the file that was already over the ceiling gains nothing. |
| **NOT** `docrender/images.py` | 9,451 B | ⭐ **The ruling spared it too.** No logo means no fourth relative-path computation. |
| `specs/draft-watermark.md` | 11,302 B | §4 pointer correction, by whichever build ships first. |

<p><br/></p>

🔴 **THIS TABLE WILL BE WRONG WITHIN TWO DAYS. It is the house scar.** `next-build-spec.md` BUILD 1 recorded `mkdocs.yml` at 7,685 B; it is **13,632 B** today, a 77% drift, and that same table documents `markers.py` rotting 16,241 → 18,534 in 48 hours, which moved an *instruction* rather than a figure. **Measure at the moment you act.**

---

## Sequence

1. 🔴 **§4a first — print one page without `hide: footer` and look for the stamp.** One preview, no code. It decides whether step 4 is a restyle or a repair, and a stamp that does not print cannot be styled.
2. **The split, as a PURE MOVE.** No behaviour change, independently reviewable, and it is what makes everything after it safe to write. Same argument as BUILD 2 Piece C. **Not blocked on any ruling.**
3. **Verify nothing broke.** One preview, both schemes, Letter and A4. The `slate` override is the rule that fails silently if the order slipped.
4. **Leading + block/list spacing** (§3a–§3c). The headline. Unitless, all three properties, measured on a rendered sheet.
5. **Callout density** (§3e).
6. **The stamp** (§4) — small, and it inherits whatever step 1 found.
7. **The type ramp** (§3d) — only if ruling 4 says now rather than after the font question.

---

## What this build is NOT

- 🚫 **Not a paginator**, and no longer even an evaluation. Closed by §1.
- 🚫 **Not a logo, not a `site.yml` `print:` block, not a letterhead.** All three closed by the ruling; all three would be new rulings with known costs.
- 🚫 **Not a colour opinion.** `print.css`'s founding rule holds: this layer is structure, and the semantic-token defect on light grounds stays upstream in `canonical/colors.tsv` where it can be fixed once.
- 🚫 **Not `fs-body` site-wide, and not a screen typography change of any kind.** Everything in §3 lives inside `@media print`.
- 🚫 **Not a `line-height` in `em` or `rem`.** §3b. Unitless or not at all.
- 🚫 **Not the font-face fix.** §3d names it as a known defect and a Michael ruling, not as work in scope.
- 🚫 **Not a second foot mark.** §4d. The stamp is extended, never duplicated.
- 🚫 **Not a content fix.** The fire policy's own defects (a stray `!` that swallows policy 5, an interrupting callout that renumbers items 6/7/8 as 1/2/3, the `R: Relocate` label contradicting its own `Rescue` body) are real and are **not** a print problem. They belong to Michael in `uritp-safety`, which agents read and never write.
