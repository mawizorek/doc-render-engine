# BUILD 5 — the print layer SPLIT, PRINT TYPOGRAPHY, and a printed IDENTITY

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-19, out of the URITP Safety fire-policy print session. Indexed from [`next-build-spec.md`](../next-build-spec.md). Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

**The asks, in the order they arrived, which is the reverse of the order they should be built:**

1. *'i want to adjust the print styling yes. lets split that file out if we need'*
2. *'a small logo potentially rendered on the top of the page or something that we define too... a little more professional looking'*
3. ⭐ *'and general LINE SPACING - that is the big one. we should make the print feel a little more like printed markdown text scale and less like rendered webpage at that point.'*

**Rulings, in order given:**

- ✅ **2026-08-19 — sheet one, not every sheet.** *'just just sheet one. and maybe its even just a tag in the footer of page one. like super database stamp style and not this is a webpage print.'*
- ✅ **2026-08-19, minutes later — the LOGO, at the HEADER.** *'page title can already come from the content of the page. lets stick to logo just header of the first page.'*

⭐ **THE SECOND RULING REVERSES PART OF THE FIRST, AND IT LANDED ON THE CHEAPER MECHANISM BY ACCIDENT.** The foot-tag idea was floated as *maybe* and is now withdrawn in favour of the original ask. See §4 — and §4b, where the header turns out to be the placement a browser can actually honour.

---

## One line

Split `assets/print.css` at a real seam, **re-typeset the paper** (leading first), and put a small declared **logo at the head of sheet one** — resolved by NAME through the existing images layer, never by path.

---

## ⭐ §0 — THE REFRAME: TYPOGRAPHY IS THE SUBSTRATE, IDENTITY IS THE GARNISH

The original scope put the mark first, because that is what was asked for. **Ask 3 inverts that, and it is correct.**

<p><br/></p>

🔴 **A LOGO ON BADLY TYPESET PAPER LOOKS WORSE THAN NO LOGO.** Adding identity to a page whose leading is set for a scrolling screen produces something that looks like a web page with a logo on it — a more specific kind of unprofessional than a plain print, because now it is *trying*. ⚠️ **The second ruling makes this sharper rather than softer:** a logo is more conspicuous than a foot tag, so it is more damaged by the leading underneath it. **Typography still ships first.**

<p><br/></p>

⭐ **AND THE FRAMING IS A REAL TYPOGRAPHIC ARGUMENT, NOT A PREFERENCE.** Generous leading exists on screen for reasons that are all about the screen: ~96dpi rendering with soft stem edges, a backlit emissive ground, and an unbounded scroll where vertical space is free. **Paper is ~300+dpi, reflective, and bounded** — crisp stems, subtractive contrast, and every millimetre of leading paid for in sheets. So a tighter print layer is not a degraded screen design. **It is the same content typeset for a different medium, which is what a print stylesheet is for.**

---

## ✅ §1 — SHEET ONE. CLOSED, AND IT CLOSED A WHOLE BRANCH OF THE BUILD

🚫 **NO PAGINATOR.** A running header on every sheet needs CSS Paged Media `@page` margin boxes (`@page { @top-center { content: element(x) } }`), which **no major browser implements** — Chrome and Firefox support `@page` for `size` and `margin` only, exactly the subset `print.css` already uses, and that is not a coincidence. Margin boxes belong to Prince, WeasyPrint and Paged.js, none of which is in this pipeline. **Out of scope, not deferred.**

<p><br/></p>

🚫 **AND NOT `position: fixed`.** It repeats per sheet in **Firefox** and prints once, on sheet one, in **Chrome**. ⚠️ **The ruling inverted which side is wrong** — under the old every-sheet reading Chrome was the broken one; now Chrome is exactly right and Firefox over-delivers. Same rule, same divergence, opposite verdicts, **which is why it stays refused either way**: a mark appearing once for one reader and six times for another, with nothing reporting it, is the silent-divergence shape logged against `em` container queries (Orion vs Blink, PR #82) and the `bad`/`danger` token mismatch. §4b needs none of it.

<p><br/></p>

🚫 **NOT the `<table>` trick** — wrapping all content so `thead` repeats via `display: table-header-group` is a layout lie and breaks `break-inside` on everything nested in it.

---

## §2 — THE SPLIT

`assets/print.css` is **22,844 B** (measured 2026-08-19, after PR #132), past the ~22 KB ceiling where a file stops coming back whole from one read and therefore stops being safely editable. `type.css`, `nav.css`, `data.css` and `chrome.css` all left `base.css` for exactly this reason.

<p><br/></p>

⚠️ **IT IS COMMENT-DOMINATED, NOT RULE-DOMINATED.** The rules are short; the reasoning is long, and the reasoning is why anybody can safely touch it. **A split that shortens the file by deleting argument is a regression disguised as hygiene.** Every note travels with the rule it explains.

<p><br/></p>

**The seam is the one the file already argues for in its own header** — *what appears on paper at all, how wide it runs, and where the page is allowed to break* — plus the third job ask 3 adds:

<p><br/></p>

| File | Owns | The one question it answers |
|---|---|---|
| **`assets/print.css`** (stays) | `@page`, chrome-off, column unrailing, slate to light neutrals, `print-color-adjust`, link policy | **What the sheet IS** |
| **`assets/print-flow.css`** (NEW) | `break-*`, `orphans`/`widows`, h1-h6, tab-label protection, forced-open `<details>`, `thead` repetition, `{.new-page}` | **Where it BREAKS** |
| **`assets/print-type.css`** (NEW, §3) | leading, block spacing, list spacing, callout density, optional ramp | **How it is SET** |
| **`assets/print-identity.css`** (NEW, §4) | the letterhead block | **Whose document it IS** |

<p><br/></p>

⚠️ **BACK TO FOUR SHEETS, AND THE REVERSAL IS MINE TO OWN.** The previous revision dropped `print-identity.css` on the argument that *a letterhead is a layout component; a foot tag is three or four typographic declarations.* **That argument was right, and it now cuts the other way** — the logo is a layout component again, so it earns its file back. ⏳ **Ruling 3** may still fold it into `print-type.css`; what is not defensible is one 30 KB sheet nobody can read whole.

<p><br/></p>

⭐ **THE FORCED-OPEN `<details>` RULE GOES WITH FLOW, WHICH IS NOT OBVIOUS.** It looks like a *what appears at all* rule — it makes withheld content appear. It belongs with flow because **it is the rule that creates the pagination problem the rest of that file solves**: force seven collapsed panels open and you have invented seven new break hazards. Cause beside consequence beats filing by verb.

<p><br/></p>

### 🔴 §2a — SOURCE ORDER IS THE SPLIT'S REAL HAZARD, AND TWO SPECS ALREADY WARN

`print.css` states twice that its position is load-bearing: it publishes AFTER generated `tokens.css` (its slate overrides re-point the same custom properties at the same specificity — lose that tie and a dark-mode reader prints pale ink on white paper, silently) and BEFORE an instance's `site.css`.

<p><br/></p>

⚠️ **EVERY NEW SHEET INHERITS THAT SANDWICH.** Order lives in `docrender/assets.py` (`_DATA_ASSETS`; **15,226 B** — verify the list's name and shape at build). Four sheets where one sat means four chances to insert one wrongly, and **the failure mode is a blank-looking page rather than an error.**

<p><br/></p>

🔴 **`specs/scoped-theme.md` §4c ALREADY FOUND THE ADJACENT BUG:** a scoped selector silently kills `print.css` on the pages it scopes, because that sheet wins on source order at equal specificity and a two-attribute scope outranks it. **Written about one sheet; after this split it applies to four, and a scope could kill one and spare the others** — a page that paginates correctly but prints in web leading, or one that keeps its letterhead and loses its margins. Whichever of BUILD 3 and BUILD 5 lands second re-reads the other's note.

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

### §3c — LINE SPACING IS THREE PROPERTIES AND THEY MUST NOT BE COLLAPSED

| # | Property | Governs | Symptom when loose |
|---|---|---|---|
| **1** | `line-height` | space **within** a paragraph | the page reads airy, screen-like |
| **2** | `p` / heading `margin` | space **between** blocks | sections drift; headings float |
| **3** | `li` margin + list `padding` | space **between** bullets | a 4-item list eats a third of a sheet |

<p><br/></p>

🔴 **NUMBER 3 IS MOST LIKELY TO BE MISDIAGNOSED, AND THE FIRE POLICY IS MOSTLY LISTS.** Material spaces list items with margin, not leading, so tightening `line-height` alone leaves a bulleted list exactly as tall and **the fix looks like it failed.** ⚠️ It also pays back the numbering fix handed to Michael on 2026-08-19: nesting a callout inside list item 5 makes that list LOOSE, adding paragraph spacing to all eight items. **Judge both on the same sheet, not separately.**

### §3d — the type ramp: the other half of 'less like a rendered webpage'

**Heading sizes are set for screen hierarchy**, where an `h1` competes with chrome, a sidebar and a scroll position. On paper the page boundary does that work, so a compressed ramp reads as a document rather than a landing page.

<p><br/></p>

🔴 **AND §4 GIVES THE RAMP A SECOND REASON TO EXIST:** once a logo sits above the `h1`, the `h1` no longer has to carry identity by itself. **A page that announces its owner in a mark does not need a 2rem heading to look important.** The letterhead and the ramp are two halves of one visual argument, which is new information the earlier revisions did not have.

<p><br/></p>

⚠️ **IT SITS ON A FACE NOBODY CHOSE.** `type.css` records that the typography vector's font FACES have never rendered on any site: `theme.font` is unset, so Material's loader fetches Roboto while `base.css` renames the variables to Inter / IBM Plex Mono, which resolve against nothing and fall through to `system-ui`. **So part of the webpage feel is that every heading is large system-ui sans.** 🚫 Not this build's fix — Michael's ruling between a third-party font request and committing binaries — but a print ramp designed on an accidental face should be known, not discovered. ⚠️ **And a real logo beside a system-ui heading will make that mismatch more visible, not less.**

### §3e — box chrome, the second lever

✅ **VERIFIED AT HEAD: nothing in this engine sizes or pads a callout.** `admonition` appears in `assets/` only in `chrome.css` (a shadow token, `--md-admonition-bg-color`) and `print.css` (`print-color-adjust`). Callout metrics are Material's, and **`print.css` governs breaks, width, colour and never density.**

<p><br/></p>

⭐ **THE COST IS ARITHMETIC, NOT TASTE.** On the fire policy, four `???+` boxes each carrying ONE sentence consume roughly half of sheet one. A `???+` is a `<details>` — cheap on screen precisely because it collapses — and `print.css` force-opens all of them. **The shape chosen to make a screen read compact is the most expensive shape available on paper**: padding, border, title bar and inter-box margin paid four times for four sentences. ⚠️ **And the letterhead now competes with them for sheet one**, which raises the priority of this lever rather than changing it.

<p><br/></p>

**Lever order:**

1. **Leading** (unitless). Highest ratio of space recovered to risk taken, and it is what was asked for.
2. **Block and list spacing** (§3c items 2-3). Without this, lists do not move and the leading change looks half-broken.
3. **Callout padding and inter-box margin.**
4. **The type ramp** (§3d).
5. **A print base font size**, LAST and possibly never.

<p><br/></p>

⭐ **LEVER 5 IS THE ONE PLACE `fs-body` IS SAFE.** `type.css` refuses `.md-typeset { font-size: var(--dr-fs-body) }` because every size inside `.md-typeset` is em-relative, so one line makes **every word on the site** 12.5% bigger — the blast radius that forced the PR #82 revert Michael reported as *the font in the TABLE is massive*. **That objection is about SITE-WIDE scope. Inside `@media print` the blast radius is one medium**, reversible in one line, invisible to anyone who never prints. The refusal stands unamended; the scope was the whole objection.

### ⚠️ §3f — THERE IS A FLOOR, AND THIS IS A SAFETY DOCUMENT

**Tighter is not monotonically better and the stopping point is not aesthetic.** A printed safety policy gets **photocopied**, and ink spread closes the gaps that separate tight lines. It gets read **standing up in a shop or a dim corridor** by somebody hunting one rule, and scanning is more leading-dependent than reading.

<p><br/></p>

⚠️ `unverified`: **WCAG 2.1 SC 1.4.12 (Text Spacing)** names a 1.5x line-height expectation, and its applicability to a FIXED print medium is genuinely unclear — the criterion is about content supporting user-applied spacing, which paper cannot do either way. Body, designation and clause cited; **not confirmed against published text this session, so it must not be quoted as settled.** 🔴 **Hazard Hawthorne owns the legibility floor for safety-critical print** — his lane, not the engine's, and a craft head is easiest to omit exactly when the generalists are doing well.

### 🔴 §3g — RE-TYPESETTING INVALIDATES EVERY MANUAL BREAK, IMMEDIATELY

`print.css` already warns, in the note shipped in PR #132 an hour before this section existed, that `{.new-page}` *is correct on the day it is typed and nobody is told when it stops being correct.*

<p><br/></p>

⭐ **THIS BUILD IS WHAT MAKES THAT WARNING COME TRUE.** Tighter leading means more lines per sheet, so every hand-placed break shifts and one that sat perfectly at web leading can leave a half-empty sheet. **Actionable today: do not author `{.new-page}` across the doc tree until the leading lands.** ⚠️ **The letterhead compounds it** — it consumes vertical space at the top of sheet one, so it moves every break on a one-sheet document too.

<p><br/></p>

⚠️ **AND IT RE-EXERCISES PR #132's BREAK POLICY.** More lines per sheet moves every break, so `orphans: 3`, the heading rule and the tab-label protection all get a different workout. **Preview both changes on the same sheet**, because a pagination oddity afterwards could belong to either.

---

## §4 — THE LETTERHEAD

> Michael: *'page title can already come from the content of the page. lets stick to logo just header of the first page.'*

### ✅ §4a — NO PAGE TITLE, AND IT CLOSES ON THE HOUSE'S OWN LAW

**Michael is right and the reason is stronger than convenience: the `h1` IS the page title, and it is already the first thing on the sheet.** A letterhead restating it would be **two places stating one fact** — the defect this repo has retired `roster.json`, `registry.json` and `app-index.md` over, and the exact argument `authoring/callouts.md` used when it refused to write a count in prose beside a list.

<p><br/></p>

⭐ **AND IT KILLS THE MECHANISM PROBLEM OUTRIGHT.** The previous revision flagged that `buildstamp.py` runs at `on_config` — once per BUILD, not per page — so `config.copyright` could never carry a page title without a new per-page hook. **That work is now unnecessary rather than deferred.**

<p><br/></p>

⚠️ **SO THERE ARE TWO MARKS ON A PRINTED SHEET, AND THAT IS THE DESIGN RATHER THAN AN OVERSIGHT.** Logo at the head answers *whose document is this*; build stamp at the foot answers *how old is it*. **Two different facts at two ends, neither restating the other** — which is the separation the withdrawn foot-tag reading had collapsed and this ruling restores.

### ⭐ §4b — THE HEADER IS THE PLACEMENT A BROWSER CAN ACTUALLY HONOUR

**Top of sheet one is free.** It is the first element in the content flow: no pagination knowledge required, no `@page` machinery, no browser divergence. **Bottom of sheet one is not free** — landing a mark at a page boundary is precisely what `@page` margin boxes do and browsers do not implement, which is why the withdrawn foot-tag reading was heading for *end of document* rather than *foot of sheet one*.

<p><br/></p>

⭐ **SO THE REVERSAL LANDED ON THE EASIER MECHANISM, AND MICHAEL DID NOT KNOW THAT WHEN HE MADE IT.** Worth recording because it is the second time today a ruling has made an implementation smaller rather than larger (J29's *the ruling made the implementation vanish*). The letterhead is one block, first in flow, `display: none` outside `@media print`.

### 🔴 §4c — THE LOGO IS DECLARED BY **NAME**, NOT BY PATH — AND MY EARLIER PROPOSAL WAS WRONG

The previous revisions proposed `logo: shared/uritp-logo.png`, which is a **PATH**.

<p><br/></p>

🔴 **THAT CONTRADICTS THE MODULE IT TOLD THE BUILDER TO REUSE.** `docrender/images.py`'s founding law, read at HEAD, is *an image is reached by NAME, never by path*, and its docstring uses **`../../../../../shared/uritp-logo.png` as its worked example of the arithmetic this house shipped wrong three separate times** (`links.py`, `router.py`, `datatable.py`). Proposing a path while citing that module as the fix is the same defect the spec was warning about, one layer up. **Corrected:**

```
print:
  logo: uritp-logo      # the STEM of the filename. No path, no extension.
```

<p><br/></p>

✅ **AND THE RESOLUTION IS ALREADY BUILT.** `images.on_files` indexes **every image in the content tree** by lowercased filename stem into `images.INDEX`, before any page renders. So:

- The logo can live **anywhere in the content tree** — `images.py` states it has *no opinion about WHERE an image lives*.
- ⭐ **Two files with one stem are REFUSED, loudly**, under `duplicate_id`, because *two pictures with one name are two different pictures*. A site cannot silently print the wrong logo.
- ⭐ **A `.png` can become a `.svg` without touching config** — the extension is not part of the id.

<p><br/></p>

⚠️ **REUSE `INDEX` PLUS `util.relative_url`, NOT `_resolve`.** `images._resolve(rest, page, label)` is claimed for the `@img:` namespace and returns **markdown**, which a template injection cannot use. The letterhead needs the URL, so it reads the indexed url and passes it through `util.relative_url(url, page.file.url)` — **the shared helper, never a `../` count.** 🔴 A letterhead renders at every depth in the tree, so it is maximally exposed to the bug that helper exists to prevent.

<p><br/></p>

⚠️ **AND THE FILE STILL LIVES IN THE CONTENT REPO**: a logo is that organisation's identity, not engine machinery, and six sites will not share one image. 🚫 Not `assets/`. 🚫 Not inline base64 in `site.yml` — binary in a config file, unreviewable in a diff.

<p><br/></p>

⭐ **ABSENT MEANS NO LETTERHEAD**, the polarity `_uses_router` already sets: a missing `routes.yml` means the router assets are never published. Five of six sites print exactly as they do today until somebody chooses otherwise.

<p><br/></p>

⚠️ **OPPOSITE POLARITIES, STATED RATHER THAN DISCOVERED:** the letterhead is opt-in; **§3's typography lands on all six sites the moment it merges.** Defensible — it corrects a default nobody chose — but it is **ruling 5**, not a surprise on somebody's printer.

### ⚠️ §4d — SIZE, ALIGNMENT AND THE RULE UNDERNEATH ARE WHERE 'PROFESSIONAL' IS WON OR LOST

All of it a measurement against a rendered sheet, **no number invented here:**

- **Small.** Michael said *a small logo* twice. A mark that competes with the `h1` fights the document.
- **A hairline rule under it** separates letterhead from content and is what makes a sheet read as a document. ⭐ **`pagefoot.py` already emits exactly this** — `<hr class="pagefoot__rule">` — and both it and `.pagefoot` sit in `print.css`'s chrome-off list, so paper has no rule today. **Same hairline, other end of the sheet.**
- **A max height in `mm`, not `px`.** ⚠️ This is the one place a physical unit is CORRECT rather than trapped: the sheet is a physical object and `px` at print resolution is a fiction. 🔴 **Not `em`** — §3b's whole finding.
- 🔴 **`print-color-adjust: exact` is MANDATORY on the logo.** Browsers drop backgrounds and can flatten images at print; a logo that prints as an empty box is worse than no logo. `print.css` already applies this narrowly to elements *whose MEANING is carried by a colour* — a brand mark qualifies, and it is one selector on that existing list.
- ⚠️ **An SVG is the right format and it is the one to TEST FIRST.** `images.SUFFIXES` includes `.svg`, and vector is obviously correct for a mark that must survive 300dpi — but SVG-in-print has real historical divergence between engines, and this repo does not assert render behaviour from a read. **Verify with an actual print preview before recommending the format.**

### §4e — injection: read `specs/chrome.md` first

The element has to be injected, which means a hook or a template partial. ⚠️ **`specs/chrome.md` already establishes that `base.html` renders the header as a bare block with no `page.meta.hide` check anywhere near it** — somebody has already read this template tree, so **read that spec rather than re-deriving it.** J29 set the precedent that editing HTML on the way out beats forking a Material partial into a `custom_dir`, because a fork is a copy of somebody else's truth that we then maintain forever.

<p><br/></p>

🔴 **AND `hide: [footer]` / `hide: [navigation]` ARE ALREADY IN USE IN CONTENT** — `uritp-safety/20-policies/fire.md` carries both. Whatever injection point is chosen must be checked against a page that hides things, because that is the page most likely to be printed.

---

## 🔴 §5 — THE BUILD STAMP IS PROBABLY NOT PRINTING TODAY. VERIFY FIRST.

Carried forward, **still unverified, and now load-bearing for §4a's two-marks design.**

<p><br/></p>

`buildstamp.py` emits its mark as **`config.copyright`**, which Material renders inside its footer meta region. `print.css`'s chrome-off list contains **`.md-footer-meta { display: none !important }`**, and then separately sets `.buildstamp { display: block }`.

<p><br/></p>

🔴 **`display: none` ON AN ANCESTOR REMOVES THE WHOLE SUBTREE FROM THE BOX TREE. A DESCENDANT CANNOT OPT BACK IN.** If the stamp is nested inside `.md-footer-meta`, the carefully argued exception has been dead since the day it was written — **the provenance line this engine insists on keeping is absent from every printed page.**

<p><br/></p>

⚠️ **STATED AS A STRONG SUSPICION, NOT A FINDING.** The nesting is knowledge of Material's footer structure, **not read off its compiled template this session**, and a proxy read presented as a verification is the failure logged in `instances/uritp-safety/site.yml` over the `database` theme claim. ⚠️ **The two fire-policy PDFs cannot settle it** — that page carries `hide: [footer]`, so no footer could print there regardless. **Print any page WITHOUT `hide: footer` and look.**

<p><br/></p>

⭐ **AND §4a RAISES THE STAKES: the two-marks design assumes the foot mark exists.** If it does not print, the letterhead ships onto a sheet with no date on it and the split-provenance argument quietly becomes a one-mark design nobody chose.

---

## 🔴 §6 — THIS BUILD MOVES BUILD 4's TARGET FILE

**[`specs/draft-watermark.md`](draft-watermark.md) §4 names `assets/print.css` as the home of the print DRAFT stamp**, beside the edit-on-git strip and the white-background rule. ⚠️ **After this split that instruction is wrong.** ⭐ **And this revision supplies the answer the last one could not:** with `print-identity.css` back, a DRAFT watermark has an obvious home — it is a mark laid over the paper, exactly like the letterhead.

<p><br/></p>

**Whichever build lands first updates the other's spec in the same PR.** ⭐ J29: *the commit that moves a thing is the only commit that still remembers where it was.*

---

## ⏳ Rulings needed

1. ✅ **CLOSED — sheet one.** Paginator and `position: fixed` out of scope.
2. ✅ **CLOSED — logo at the header; no page title in the mark** (§4a). Per-page hook unnecessary.
3. **Three print sheets or four?** (§2) `print-identity.css` earns its file back now that identity is a layout component. **Recommend four.**
4. **How far does the leading go, and what is the floor?** (§3a, §3f) A measurement at Letter and A4, argued against the house's 1.35 precedent. **Hawthorne reads the legibility floor.**
5. **🔴 Is the typography change opt-in or global?** (§4c) It lands on all six sites at merge, unlike the letterhead. **Recommend global** — it corrects a default nobody chose — but say it out loud.
6. **Does the type ramp compress too** (§3d), knowing the face is `system-ui` by accident and a real logo will expose that? **Recommend deferring** the ramp until the font question is ruled.
7. **Should `???+` on a print-heavy page be advice rather than CSS?** (§3e) Four one-sentence boxes are a **content** shape, and no stylesheet makes four boxes as cheap as a four-item definition list. About how Michael writes, not about the engine.
8. **Which logo file, and does one exist?** ⚠️ `images.py`'s docstring names `shared/uritp-logo.png` in an EXAMPLE; **that is illustrative prose, not evidence the file exists.** Confirm before building.

---

## Files and sizes (measured at HEAD 2026-08-19 — RE-MEASURE AT BUILD)

| File | Now | Change |
|---|---|---|
| `assets/print.css` | **22,844 B** | **-10 to -13 KB.** Keeps only *what the sheet is*. ⚠️ Its chrome-off list is where §5's suspected bug lives, and where the logo's `print-color-adjust` selector belongs. |
| **NEW** `assets/print-flow.css` | — | ~9-11 KB. Break policy verbatim, comments intact. |
| **NEW** `assets/print-type.css` | — | ~5-7 KB. Leading, block/list spacing, callout density, optional ramp. |
| **NEW** `assets/print-identity.css` | — | ~2-3 KB. Letterhead block plus hairline. |
| `docrender/assets.py` | 15,226 B | +small. Three registrations, **in the correct order** (§2a). |
| `docrender/images.py` | **9,451 B** | ⭐ **untouched — `INDEX` is read, not modified.** No new resolver, no fourth path computation. |
| `docrender/instance.py` | **23,047 B** | 🔴 **BACK IN PLAY, AND ALREADY OVER THE CEILING** before the `print:` block adds a line. Check whether instance config can grow anywhere else, or whether this file needs its own split first. |
| `docrender/buildstamp.py` | **2,892 B** | ⭐ **untouched** — ruling 2 removed the only reason to change it. |
| `docrender/pagefoot.py` | **2,613 B** | untouched. Named because it owns the `<hr>` §4d wants. |
| `docrender/tokenaudit.py` | 24,295 B | ⚠️ untouched, but it **AUDITS this work** — `line-height`, `padding`, `margin` and `max-width` are all in `_METRIC_PROPS`, so every value §3 and §4 add appears in the token audit. Expect new rows and read them. |
| a template partial / hook | — | letterhead injection. **Read `specs/chrome.md` first** (§4e). |
| `instances/*/site.yml` | varies | opt-in `print:` block, **only where wanted**. |
| `specs/draft-watermark.md` | 11,302 B | §4 pointer correction, by whichever build ships first. |

<p><br/></p>

🔴 **THIS TABLE WILL BE WRONG WITHIN TWO DAYS. It is the house scar.** `next-build-spec.md` BUILD 1 recorded `mkdocs.yml` at 7,685 B; it is **13,632 B** today, a 77% drift, and that same table documents `markers.py` rotting 16,241 to 18,534 in 48 hours, which moved an *instruction* rather than a figure. **Measure at the moment you act.**

---

## Sequence

1. 🔴 **§5 first — print one page without `hide: footer` and look for the build stamp.** One preview, no code. §4a's two-marks design depends on the answer.
2. **The split, as a PURE MOVE.** No behaviour change, independently reviewable, and it is what makes everything after it safe to write. Same argument as BUILD 2 Piece C. **Not blocked on any ruling.**
3. **Verify nothing broke.** One preview, both schemes, Letter and A4. The `slate` override is the rule that fails silently if the order slipped.
4. **Leading plus block/list spacing** (§3a-§3c). The headline. Unitless, all three properties, measured on a rendered sheet.
5. **Callout density** (§3e).
6. **The letterhead** (§4) — needs a logo file to exist (ruling 8) and a config key in a file already over the ceiling.
7. **The type ramp** (§3d) — only if ruling 6 says now rather than after the font question.

---

## What this build is NOT

- 🚫 **Not a paginator**, and no longer even an evaluation. Closed by §1.
- 🚫 **Not a logo on every sheet.** §1. One mark, sheet one, first in flow.
- 🚫 **Not a page title in the letterhead.** §4a. The `h1` already says it, and two places stating one fact is the defect three retired manifests were killed over.
- 🚫 **Not a logo declared by PATH.** §4c. The stem of the filename, resolved through the images index.
- 🚫 **Not a colour opinion.** `print.css`'s founding rule holds: this layer is structure, and the semantic-token defect on light grounds stays upstream in `canonical/colors.tsv`. ⚠️ `print-color-adjust` on the logo is a DELIVERY rule, not a colour choice.
- 🚫 **Not `fs-body` site-wide, and not a screen typography change of any kind.** Everything in §3 lives inside `@media print`.
- 🚫 **Not a `line-height` in `em` or `rem`.** §3b. Unitless or not at all.
- 🚫 **Not the font-face fix.** §3d names it as a known defect and a Michael ruling, not as work in scope.
- 🚫 **Not a content fix.** The fire policy's own defects (a stray `!` that swallows policy 5, an interrupting callout that renumbers items 6/7/8 as 1/2/3, the `R: Relocate` label contradicting its own `Rescue` body) are real and are **not** a print problem. They belong to Michael in `uritp-safety`, which agents read and never write.
