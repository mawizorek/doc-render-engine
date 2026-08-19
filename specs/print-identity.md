# BUILD 5 — the print layer SPLIT, PRINT TYPOGRAPHY, and a printed IDENTITY

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-19. Requested by Michael out of the URITP Safety fire-policy print session: *"i want to adjust the print styling yes. lets split that file out if we need - but i was about to ask for a small logo potentially rendered on the top of the page or something that we define too so lets spec the printing mechanism to be a little more professional looking."*

⭐ **AMENDED SAME DAY, AND THE AMENDMENT IS THE HEADLINE** — Michael, 2026-08-19: *"and general LINE SPACING - that's the big one. we should make the print feel a little more like printed markdown text scale and less like rendered webpage at that point."* That sentence changes what this build IS; see §2. Indexed from [`next-build-spec.md`](../next-build-spec.md).

Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

---

## One line

Split `assets/print.css` at a real seam, then **re-typeset the paper** — leading first, box chrome second — so a printed page reads as a printed document rather than a photograph of a web page. A declared **printed identity** (logo + title line) rides on top of that.

---

## ⭐ §0 — THE REFRAME, AND IT REORDERS THE WHOLE BUILD

The original scope treated density as one lever among several and put the letterhead first, because the letterhead is what was asked for. **The line-spacing note inverts that, and it is correct.**

<p><br/></p>

🔴 **A LETTERHEAD ON BADLY TYPESET PAPER LOOKS WORSE THAN NO LETTERHEAD.** Adding a logo to a page whose leading is set for a scrolling screen produces something that looks like a web page with a logo on it — which is a more specific kind of unprofessional than a plain print, because now it is *trying*. **Typography is the substrate; identity is the garnish.** The letterhead moves to last in the sequence and nothing is lost by that, because §0's blocking ruling has to be answered before it can be built anyway.

<p><br/></p>

⭐ **AND THE FRAMING IS A REAL TYPOGRAPHIC ARGUMENT, NOT A PREFERENCE.** Generous leading exists on screen for reasons that are all about the screen: ~96dpi rendering with soft stem edges, a backlit emissive ground, and an unbounded scroll where vertical space is free. **Paper is ~300+dpi, reflective, and bounded** — the stems are crisp, the contrast is subtractive, and every millimetre of leading is paid for in sheets. So the print layer being TIGHTER than the screen layer is not a compromised version of the screen design. **It is the same content typeset for a different medium, which is what a print stylesheet is for.** This is the first time this engine has had a reason to say that out loud, and it belongs in the header of whatever file lands.

---

## 🔴 §1 — THE BLOCKING LIMIT (identity), UNCHANGED AND STILL UNANSWERED

**Michael asked for a logo "rendered on the top of the page." If "the page" means EVERY SHEET, a browser cannot do it, and no amount of CSS in this repo changes that.**

<p><br/></p>

A true running header is CSS Paged Media `@page` margin boxes:

```
@page { @top-center { content: element(letterhead); } }
```

**No major browser implements `@page` margin boxes.** Chrome and Firefox support `@page` for `size` and `margin` only — which is exactly the subset `print.css` already uses, and that is not a coincidence. Margin boxes are implemented by dedicated paginators (Prince, WeasyPrint, Paged.js), none of which is in this pipeline, and adding one is a new dependency and a new build stage rather than a stylesheet edit.

<p><br/></p>

⚠️ **AND THE FALLBACK EVERYONE REACHES FOR IS BROWSER-DEPENDENT.** `position: fixed` on a header element repeats per sheet in Firefox and prints **once, on sheet one,** in Chrome. So the same rule produces a letterhead on every page for one reader and a letterhead on page one for another, with nothing reporting the difference. **That is worse than a documented limit** — it is the silent-divergence shape this repo has logged against `em` container queries (Orion vs Blink, PR #82) and against the `bad`/`danger` token mismatch. The only other trick is wrapping all content in a `<table>` so `thead` repeats via `display: table-header-group`, which the print sheet already exploits for real tables. Wrapping a document in a table to get a header is a layout lie and it breaks `break-inside` on everything nested in it. 🚫 Refused here in advance.

<p><br/></p>

⭐ **SO THE HONEST BUILD IS A FIRST-PAGE LETTERHEAD, and it should be presented as the feature rather than as a compromise.** Every document this engine renders is ONE document; a letterhead on sheet one plus the existing build stamp at the end is how a real printed policy is laid out. **Ruling 1 asks Michael to confirm that reading**, because if he genuinely needs a mark on every sheet, that half of this build is a paginator evaluation and not a CSS change. ⚠️ **Still open as of the amendment — asked, not answered.** It no longer blocks the build as a whole, because §0 moved identity to last.

---

## §2 — THE SPLIT

`assets/print.css` is **22,844 B** (measured 2026-08-19, after PR #132). The repo's own ceiling is ~22 KB — the point at which a file stops coming back whole from one read and therefore stops being safely editable. `type.css`, `nav.css`, `data.css` and `chrome.css` all left `base.css` for exactly this reason and each says so in its header.

<p><br/></p>

⚠️ **IT IS COMMENT-DOMINATED, NOT RULE-DOMINATED, AND THAT CHANGES THE SPLIT.** The rules in that file are short; the reasoning is long, and the reasoning is the reason anybody can safely touch it. **A split that shortens the file by deleting argument is a regression disguised as hygiene.** Every note travels with the rule it explains.

<p><br/></p>

**The seam — and it is the one the file already argues for in its own header.** That header divides its subject into *"what appears on paper at all, how wide it runs, and where the page is allowed to break."* The amendment adds a third job, so it is now three files rather than two:

<p><br/></p>

| File | Owns | Why it is one job |
|---|---|---|
| **`assets/print.css`** (stays) | `@page`, chrome-off, the column unrailing, the slate→light neutral overrides, `print-color-adjust`, link policy | **What the sheet IS.** Every rule answers *what reaches the paper and how wide*. |
| **`assets/print-flow.css`** (NEW) | `break-after`/`break-inside`/`orphans`/`widows`, the h1–h6 rule, tab-label protection, the forced-open `<details>`, `thead` repetition, `{.new-page}` | **WHERE IT BREAKS.** Every rule answers *what may be split*. |
| **`assets/print-type.css`** (NEW, §3) | leading, block spacing, list spacing, callout density, the type ramp | **HOW IT IS SET.** ⭐ A separate file because §0 makes this the biggest surface in the build, not a handful of overrides bolted onto either neighbour. |
| **`assets/print-identity.css`** (NEW, §4) | the letterhead block | A new surface, and it should not be born inside a file already over the line. |

<p><br/></p>

⭐ **THE FORCED-OPEN `<details>` RULE GOES WITH FLOW, WHICH IS NOT OBVIOUS.** It looks like a *what appears at all* rule — it makes withheld content appear. It belongs with flow because **it is the rule that creates the pagination problem the rest of that file solves**: force seven collapsed panels open and you have just invented seven new break hazards. Keeping the cause beside its consequences is worth more than filing it by its verb.

<p><br/></p>

⚠️ **FOUR PRINT SHEETS IS A REAL COST AND RULING 2 SHOULD WEIGH IT.** `print-type.css` is the one whose existence §0 justifies on its own. Folding identity into type, or flow into the base sheet, are both defensible; what is not defensible is one 30 KB file nobody can read whole.

<p><br/></p>

### 🔴 §2a — THE SPLIT'S REAL HAZARD IS SOURCE ORDER, AND TWO EXISTING SPECS ALREADY WARN ABOUT IT

`print.css`'s own header states that its position is load-bearing **twice over**: it must publish AFTER the generated `tokens.css` (because its slate overrides re-point the same custom properties at the same specificity, and losing that tie prints pale ink on white paper, silently) and BEFORE an instance's `site.css` (because an instance keeps the final word).

<p><br/></p>

⚠️ **EVERY NEW SHEET INHERITS THAT SANDWICH.** Order is declared in `docrender/assets.py` (`_DATA_ASSETS`; **15,226 B** — verify the list's exact name and shape at build, do not trust this sentence). Four sheets in the slot where one used to sit means four chances to insert one in the wrong place, and **the failure mode is a blank-looking page rather than an error.**

<p><br/></p>

🔴 **AND `specs/scoped-theme.md` §4c ALREADY FOUND THE ADJACENT BUG:** *a scoped selector silently kills `print.css` on the pages it scopes, because that sheet wins on source order at equal specificity and a two-attribute scope outranks it.* **That finding was written about ONE print sheet. After this split it applies to four, and a scope could kill one and spare the others** — producing a page that paginates correctly and prints grey, or one typeset for paper that prints in web leading. **Whichever of BUILD 3 and BUILD 5 lands second must re-read the other's note.**

---

## ⭐ §3 — PRINT TYPOGRAPHY: LEADING IS THE BIG ONE, AND THE ARITHMETIC SAYS SO

> Michael: *"general LINE SPACING - that's the big one."*

### §3a — why leading beats every other lever, without needing a measured number

**Leading is the only property in this build that multiplies across the whole document.** Box padding is paid once per box, so its total cost is bounded by how many boxes a page happens to have. **Leading is paid once per LINE**, and a reference document is almost entirely lines. Reduce the leading by *n*% and the document loses very nearly *n*% of its height, on every page, in every section, forever.

<p><br/></p>

⭐ **THAT ARGUMENT HOLDS WITHOUT KNOWING THE CURRENT VALUE, WHICH IS WHY IT CAN BE WRITTEN HERE.** The ratio is what matters, not the starting point — so the lever order below is decidable now, and only the final number needs a measurement. That distinction is what this spec has been careful about throughout.

<p><br/></p>

✅ **VERIFIED AT HEAD, and it is the same finding shape as the callout padding:** grepping `line-height` across the repo returns **four hits, and not one of them is body prose** — `data.css` (1.35 on table cells, 1.4 on a wrapped cell), `data-list.css` (1.35), `navtree.css` (1.5). **So prose, list and callout leading are Material's, unmodified, on screen and therefore on paper.** Nothing in this engine has ever had an opinion about the leading of a sentence.

<p><br/></p>

⭐ **AND THE HOUSE ALREADY HAS A DENSE-CONTENT PRECEDENT: 1.35.** That is the value `data.css` and `data-list.css` both chose for content whose job is to be scanned rather than read. It is **not** the print answer — a data cell is one line and a policy paragraph is six — but it is the nearest existing decision and the print value should be argued *against* it rather than invented from nothing.

### 🔴 §3b — THE ONE HARD CSS RULE: UNITLESS, NEVER `em`

**`line-height` must be declared as a UNITLESS number.** This is not style preference, it is inheritance mechanics, and getting it wrong produces a specific ugly failure:

<p><br/></p>

- **Unitless** (`line-height: 1.4`) inherits as a **ratio** and is recomputed against each descendant's own `font-size`. A code block, a table cell and an `h2` each get leading proportional to themselves.
- **`em` or `rem`** (`line-height: 1.4em`) inherits as a **computed LENGTH**. Every descendant gets that same absolute leading regardless of its own size — so a heading gets cramped lines and small print gets airy ones, on the same page.

<p><br/></p>

⚠️ **AND THIS IS THE `em` TRAP FROM PR #82 AND #80 WEARING A THIRD COSTUME.** That family already cost this repo two reverts: a bridge row mapping a two-axis padding onto a one-axis primitive, and a container query whose `45em` resolved against the wrong font size. **Same lesson, third property: a relative unit is only relative to something, and the something is rarely what you meant.** `.md-typeset` is the element whose whole documented hazard is that everything inside it is em-relative (`type.css`), so this is exactly the wrong place to introduce a length-valued line-height.

### §3c — "LINE SPACING" IS AT LEAST THREE PROPERTIES, AND THEY MUST NOT BE COLLAPSED

The complaint reads as one knob. It is three, they fail differently, and a single global `line-height` fixes only the first:

<p><br/></p>

| # | Property | Governs | Symptom when too loose |
|---|---|---|---|
| **1** | `line-height` | space **within** a paragraph | the page reads airy, screen-like |
| **2** | `p` / heading `margin` | space **between** blocks | sections drift apart; headings float |
| **3** | `li` margin + list `padding` | space **between** bullets | a 4-item list eats a third of a sheet |

<p><br/></p>

🔴 **NUMBER 3 IS THE ONE MOST LIKELY TO BE MISDIAGNOSED, AND THE FIRE POLICY IS FULL OF LISTS.** Material spaces list items with margin, not leading, so tightening `line-height` alone leaves a bulleted list exactly as tall as it was and the fix looks like it failed. ⚠️ **It also interacts with the numbering fix already handed to Michael:** nesting a callout inside list item 5 makes that list LOOSE, which adds paragraph spacing to all eight items. So the list-spacing rule here is what pays that fix back — **and it means the two must be judged on the same sheet, not separately.**

### §3d — the type ramp, which is the other half of "less like a rendered webpage"

> Michael: *"more like printed markdown text scale."*

**Heading sizes are set for screen hierarchy, where an `h1` competes with chrome, a sidebar and a scroll position.** On paper the page boundary and the letterhead do that work, so a compressed ramp reads as a document rather than as a landing page. This is a smaller lever than leading and a more visible one.

<p><br/></p>

⚠️ **AND IT COLLIDES WITH A KNOWN, DOCUMENTED DEFECT worth reading before touching type here.** `type.css` records that the typography vector's font FACES have never rendered on any site: `theme.font` is unset, so Material's loader fetches Roboto while `base.css` renames the variables to `Inter`/`IBM Plex Mono`, which resolve against nothing and fall through to `system-ui`. **So part of the "rendered webpage" feel is that every heading is large system-ui sans.** 🚫 Not this build's job to fix — it is Michael's ruling between a third-party font request and committing binaries — but **a print type ramp is being designed on top of a face nobody chose, and that should be known rather than discovered.**

### §3e — box chrome, the second lever (was §2 in the original scope)

**Verified at HEAD: nothing in this engine sizes or pads a callout.** `admonition` appears in `assets/` only in `chrome.css` (a shadow token and `--md-admonition-bg-color`) and in `print.css` (`print-color-adjust`). So callout metrics are Material's, unmodified, and **`print.css` governs breaks, width, colour and never density.**

<p><br/></p>

⭐ **THE COST IS ARITHMETIC, NOT TASTE.** On the fire policy, four `???+` boxes each carrying ONE sentence consume roughly half of sheet one. A `???+` is a `<details>` — cheap on screen precisely because it collapses — and `print.css` force-opens all of them. **The shape chosen to make a screen read compact is the most expensive shape available on paper**: padding, border, title bar and inter-box margin paid four times for four sentences.

<p><br/></p>

**Revised lever order, leading first:**

1. **Leading** (`line-height`, unitless). Highest ratio of space recovered to risk taken, and it is what was asked for.
2. **Block and list spacing** (§3c items 2 and 3). Without this, lists do not move and the leading change looks half-broken.
3. **Callout padding and inter-box margin.**
4. **The type ramp** (§3d).
5. **A print base font size**, LAST and possibly never — if 1–4 land, this may be unnecessary.

<p><br/></p>

⭐ **§3's LAST LEVER IS THE ONE PLACE `fs-body` IS SAFE, WHICH IS WORTH SPELLING OUT.** `type.css` refuses `.md-typeset { font-size: var(--dr-fs-body) }` outright: every size inside `.md-typeset` is em-relative, so one line makes **every word on the site** 12.5% bigger — the same blast radius that forced the PR #82 revert Michael reported as *"the font in the TABLE is massive."* **That objection is about SITE-WIDE blast radius. A declaration inside `@media print` has a blast radius of exactly one medium**, it is reversible in one line, and it is invisible to every reader who never prints. The refusal in `type.css` stands unamended and this does not contradict it — same mechanism, different scope, and the scope was the whole objection.

### ⚠️ §3f — THERE IS A FLOOR, AND THIS IS A SAFETY DOCUMENT

**Tighter is not monotonically better and the stopping point is not aesthetic.** Two concrete costs, neither hypothetical for these documents:

<p><br/></p>

- **A printed safety policy gets photocopied**, and tight leading degrades badly through a generation of copying — ink spread closes the gaps that separate lines.
- **It gets read in a shop, a corridor, or a dim backstage**, standing up, quickly, by somebody looking for one rule. Scanning is more leading-dependent than reading is.

<p><br/></p>

⚠️ **`unverified`: WCAG 2.1 SC 1.4.12 (Text Spacing) names a 1.5× line-height expectation, and its applicability to a FIXED print medium is genuinely unclear** — the criterion is about content supporting user-applied spacing, which paper cannot do either way. **Cited body/designation/clause but NOT confirmed against the published text this session, so it is marked unverified per house rule and must not be quoted as settled.** 🔴 **Hazard Hawthorne should have the final read on legibility floors for safety-critical print** — that is his lane, not the engine's, and a craft head is easiest to omit exactly when the generalists are doing well.

### 🔴 §3g — RE-TYPESETTING INVALIDATES EVERY MANUAL BREAK, IMMEDIATELY

`print.css` already warns, in the note shipped in PR #132 an hour before this amendment, that `{.new-page}` *"is correct on the day it is typed and nobody is told when it stops being correct."*

<p><br/></p>

⭐ **THIS BUILD IS THE THING THAT MAKES THAT WARNING COME TRUE.** Tighter leading means more lines per sheet, so every hand-placed break shifts and a break that sat perfectly at web leading can leave a half-empty sheet. **Consequence, and it is actionable today: do not author `{.new-page}` markers across the doc tree until the leading lands.** Anything placed now gets re-judged later, and the whole point of the automatic rules is to keep that work from being necessary.

<p><br/></p>

⚠️ **AND IT RE-EXERCISES THE BREAK POLICY MERGED IN PR #132.** More lines per sheet changes where every break falls, so the `orphans: 3`, heading and tab-label protections all get a different workout. Not a conflict — but **the two changes must be previewed on the same sheet, because a pagination oddity after this ships could belong to either.**

---

## §4 — THE PRINTED IDENTITY

A small logo plus a title line at the top of sheet one, and a site declares it. ⭐ **Sequenced LAST per §0**, and it is still gated on ruling 1.

<p><br/></p>

### 🔴 §4a — WHERE THE IMAGE FILE LIVES IS THE DECISION, NOT THE CSS

The CSS is trivial. The placement question is governed and gets answered by **audience, not by convenience** — the repo-referent rule.

<p><br/></p>

| Option | Verdict |
|---|---|
| **In the CONTENT repo**, referenced by a `site.yml` key | ✅ **Recommended.** A logo is that organisation's identity, not engine machinery. URITP's mark is not the engine's business, and six sites will not share one image. |
| **In the ENGINE repo** (`assets/`) | 🚫 Refused. It makes the engine hold one instance's brand, and the second site to want a different logo forces the refactor anyway. |
| **Inline base64 in `site.yml`** | 🚫 Refused. Binary in a config file, unreviewable in a diff, and it inflates a file every build parses. |

<p><br/></p>

⚠️ **`images.py` ALREADY SOLVES THE PATH PROBLEM AND MUST NOT BE RE-SOLVED.** It owns `@img:<name>` and resolves through `util.relative_url` — and its own docstring carries the five-level `../../../../../shared/uritp-logo.png` example as the arithmetic **this house shipped wrong three separate times** (`links.py`, `router.py`, `datatable.py`). 🔴 **A letterhead injected into a template renders at every depth in the tree, so it is maximally exposed to exactly that bug.** Read `images.py` first and reuse its resolver.

<p><br/></p>

### §4b — the declaration

A `print:` block in each instance's `site.yml`, absent by default:

```
print:
  logo: shared/uritp-logo.png     # resolved through the images layer, never a raw path
  title: URITP Safety             # optional; falls back to site name
```

⭐ **ABSENT MEANS NO LETTERHEAD, AND THAT POLARITY IS DELIBERATE** — the same rule `_uses_router` already sets, where a missing `routes.yml` means the router assets are never even published. Five of six sites should print exactly as they do today until somebody chooses otherwise.

<p><br/></p>

⚠️ **THE TYPOGRAPHY HALF HAS THE OPPOSITE POLARITY, AND THAT ASYMMETRY IS THE ONE THING IN THIS SPEC MOST LIKELY TO SURPRISE SOMEBODY.** §3 changes paper output on **all six sites the moment it merges**, with no opt-in, because it is a fix to a default nobody chose rather than a feature somebody asked for. That is defensible — the current leading was never a decision — but it should be a stated choice. ⏳ **Ruling 5.**

<p><br/></p>

### ⚠️ §4c — IT COLLIDES WITH THE BUILD STAMP, WHICH IS ALREADY THE PROVENANCE LINE

`print.css` keeps `.buildstamp` on paper as a deliberate, argued exception: *"a printed page leaves the system entirely — it gets handed to a guest artist, filed, carried into a room months later — and the one question nobody can answer about a piece of paper is how old it is."*

<p><br/></p>

🔴 **A letterhead that repeats the site name and date is a SECOND claimant on provenance**, and this repo has retired three manifests over exactly that shape. **Recommend: the letterhead carries IDENTITY (logo + title) and the build stamp keeps DATE, unchanged, at the foot.** Two facts, two ends of the sheet, neither stating the other's.

<p><br/></p>

### §4d — mechanism, and the honest unknown

The element has to be injected, which means a hook or a template partial. ⚠️ **`specs/chrome.md` already establishes that `base.html` renders the header as a bare block with no `page.meta.hide` check anywhere near it**, so somebody has already read this template tree — **read that spec before choosing an injection point rather than re-deriving it.** J29 set the precedent that editing HTML on the way out beats forking a Material partial into a `custom_dir`, because a fork is a copy of somebody else's truth that we then maintain forever.

<p><br/></p>

🚫 **AND IT MUST NOT BE VISIBLE ON SCREEN.** `display: none` outside `@media print` is the whole trick, and it is also why the element can be injected unconditionally without touching the screen page.

---

## 🔴 §5 — THIS BUILD MOVES BUILD 4's TARGET FILE

**[`specs/draft-watermark.md`](draft-watermark.md) §4 names `assets/print.css` as the home of the print DRAFT stamp** and instructs the builder to add it *"there"* beside the edit-on-git strip and the white-background rule.

<p><br/></p>

⚠️ **After this split, that instruction is wrong.** A DRAFT watermark is not *what the sheet is*, not *where it breaks*, and not *how it is set* — it is an overlay, and it belongs beside the letterhead in `print-identity.css`.

<p><br/></p>

**Whichever build lands first updates the other's spec in the same PR.** ⭐ J29: *the commit that moves a thing is the only commit that still remembers where it was.*

---

## ⏳ Rulings needed

1. **🔴 Identity: sheet one, or every sheet?** (§1) **Recommend sheet one.** Every other answer costs a paginator. ⚠️ Asked 2026-08-19, not yet answered — no longer blocks the build, only §4.
2. **How many print sheets — two, three or four?** (§2) **Recommend four**, with `print-type.css` as the non-negotiable one.
3. **How far does the leading go, and what is the floor?** (§3a, §3f) A measurement against a rendered sheet at Letter and A4, argued against the house's existing 1.35 dense-content precedent. **Hawthorne reads the legibility floor** for safety print.
4. **Does the type ramp compress too** (§3d), knowing the face is `system-ui` by accident? **Recommend deferring the ramp** until the font question is ruled, and shipping leading + spacing first.
5. **🔴 Is the typography change opt-in or global?** (§4b) It lands on all six sites at once. **Recommend global** — it corrects a default nobody chose — but it needs to be said out loud, not discovered on somebody's printer.
6. **Should `???+` on a print-heavy page be advice rather than CSS?** (§3e) The fire policy's four one-sentence boxes are a **content** shape, and no stylesheet makes four boxes as cheap as a four-item definition list. About how Michael writes, not about the engine.
7. **`print:` block shape** (§4b), and whether `title` is wanted given §4c's provenance seam.

---

## Files and sizes (measured at HEAD 2026-08-19 — RE-MEASURE AT BUILD)

| File | Now | Change |
|---|---|---|
| `assets/print.css` | **22,844 B** | **−10 to −13 KB.** Loses break policy AND gains no typography — it keeps only *what the sheet is*. |
| **NEW** `assets/print-flow.css` | — | ~9–11 KB. Break policy verbatim, comments intact. |
| **NEW** `assets/print-type.css` | — | ~4–6 KB. Leading, block/list spacing, callout density, optional ramp. |
| **NEW** `assets/print-identity.css` | — | ~2–3 KB. |
| `docrender/assets.py` | 15,226 B | +small. Three registrations, **in the correct order** (§2a). |
| `docrender/instance.py` | 23,047 B | ⚠️ **ALREADY OVER THE CEILING at 23,047 B**, before the `print:` block adds anything. |
| `docrender/tokenaudit.py` | 24,295 B | ⚠️ **untouched, but it AUDITS this work:** `line-height` is already in its `_METRIC_PROPS`, so every value §3 adds shows up in the token audit. Expect new rows and read them. |
| `docrender/images.py` | 9,451 B | untouched if its resolver is reused (§4a). |
| a template partial / hook | — | letterhead injection. See `specs/chrome.md` first. |
| `instances/*/site.yml` | varies | opt-in `print:` block, **only where wanted**. |
| `specs/draft-watermark.md` | 11,302 B | §4 pointer correction, by whichever build ships first. |

<p><br/></p>

🔴 **THIS TABLE WILL BE WRONG WITHIN TWO DAYS. It is the house scar.** `next-build-spec.md` BUILD 1 recorded `mkdocs.yml` at 7,685 B; it is **13,632 B** today, a 77% drift, and that same table documents `markers.py` rotting from 16,241 to 18,534 in 48 hours — which moved an *instruction*, not just a figure. **Measure at the moment you act.**

---

## Sequence

⭐ **REORDERED BY THE AMENDMENT.** Typography now leads and identity is last; §0 is the argument.

<p><br/></p>

1. **The split, as a PURE MOVE.** No behaviour change, independently reviewable, and it is what makes everything after it safe to write. Same argument as BUILD 2 Piece C: doing it last means writing new code into a file already past the line. **Not blocked on any ruling.**
2. **Verify nothing broke.** One print preview, both schemes, Letter and A4. The `slate` override is the rule that fails silently if the order slipped.
3. **Leading + block/list spacing** (§3a–§3c). The headline. Measured on a rendered sheet, unitless, all three properties or the lists will not move.
4. **Callout density** (§3e).
5. **The type ramp** (§3d) — only if ruling 4 says now rather than after the font question.
6. **The letterhead** (§4). Last: it needs a new config key, a new injection point, and ruling 1.

---

## What this build is NOT

- 🚫 **Not a paginator.** No Prince, WeasyPrint or Paged.js. If ruling 1 comes back *every sheet*, that is a separate evaluation with a separate cost, not a stretch goal inside this one.
- 🚫 **Not a colour opinion.** `print.css`'s founding rule holds: this layer is structure, and the semantic-token defect on light grounds stays upstream in `canonical/colors.tsv` where it can be fixed once.
- 🚫 **Not `fs-body` site-wide, and not a screen typography change of any kind.** Everything in §3 lives inside `@media print`. `type.css`'s refusal stands unamended.
- 🚫 **Not a `line-height` in `em` or `rem`.** §3b. Unitless or not at all.
- 🚫 **Not the font-face fix.** §3d names it as a known defect and a Michael ruling, not as work in scope.
- 🚫 **Not a fork of a Material partial into `custom_dir`.** J29 precedent.
- 🚫 **Not a second provenance line.** §4c.
- 🚫 **Not a content fix.** The fire policy's own defects (a stray `!` that swallows policy 5, an interrupting callout that renumbers items 6/7/8 as 1/2/3, the `R: Relocate` label contradicting its own `Rescue` body) are real and are **not** a print problem. They belong to Michael in `uritp-safety`, which agents read and never write.
