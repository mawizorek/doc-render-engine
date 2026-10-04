# BUILD 11 · THE PRINT COMPOSER — pick pages, order them, print one document

✅ **Phase 1 BUILT 2026-09-28** (browser-side, casual). ✅ **Phase 2 binders BUILT 2026-09-28** (§6), plus the footer note (§7). ✅ **§9 COPY AS TEXT BUILT 2026-10-03.** ⏳ Every-sheet footer NOT built (§8). Workshop: Maestro Mira (scope) + Dev Dexter (engine), one pass. Decision history: the **doc-render-engine (repo) Decision Log** subpage in ClickUp.

> Michael, 2026-09-28: *"a new render menu page entirely for printing, that would let me select multiple articles from the repo, arrange them, and print them as one document... but like locally and just casually in the app first, a refresh of the page could potentially wipe the settings, and then we'll build this into being able to define default print 'groups' that are essentially the binders."*

## §1 Mira: what this is, and what it is not

It is **BUILD 10's packet, reader-assembled.** The packet is a fixed binding the build makes from a program's `chain:`. The composer lets the reader make any binding, ad hoc, from any public page. Phase 2 then turns a composed binding into a declared one, which is the packet mechanism with a second source list. **Two features, one shape.**

🚫 Not a second renderer, not a PDF merge, not a new print path. `print-packet-dl.md` A1 and A3 stand: the output is HTML the browser prints through the same sheets as every page.

## §2 Dex: why it can work in a browser at all

A1 says a browser cannot print several documents as one job. **Correct, and irrelevant here:** the composer never prints several documents. It fetches each chosen page's built HTML, stitches the article bodies into ONE `<article class="md-content__inner md-typeset">` inside the current page's `.md-content`, hides that page's own body, and the reader prints the current page. Every print sheet, the chrome-off list and the print menu's margins apply unchanged, because the selectors all match.

## §3 Rulings

| # | Ruling | Why |
|---|---|---|
| 1 | **The list is Material's `search/search_index.json`.** | `visibility.py` builds only `unlisted`/`public` and gives unlisted `search.exclude`. So the index is exactly what a reader can already find: the packet's A7 leak fence, for free. The sidebar is not usable: `navigation.prune` is on. |
| 2 | **Routed-folder pages appear in the list** (they are in search; sealing is presentation, `visibility.py`). **A fetched body still carrying a router curtain is skipped and named**, never printed as a form. | Same protective reading as A7. |
| 3 | **The packet's link law, in the browser:** ids → `sN-id`; `#frag` → `#sN-frag`; a link to a page in the stack → `#sM[-frag]`; other relative links and every `src`/`srcset` → absolute. | Five colliding `#overview` anchors is the default case, not the edge case. Images 404 otherwise. |
| 4 | **Stripped per section:** scripts, edit button, source-file footer, `.dr-flow*`, `.buildstamp--foot`, `.dr-packet*`, the print menu. **Kept:** each article's letterhead (`.buildstamp--corner`) and foot (`.dr-revised`, `.dr-owner`); the cover borrows the first letterhead (PR #248). | v1 stripped every `buildstamp*` on packet A8 reasoning, which assumed a fixed stamp. The corner stamp is in flow, so stripping it just deleted the letterhead. A pulled sheet must still say whose it is. |
| 5 | **Cover + contents page on by default, one article per sheet on by default.** Both are drawn switches. | Packet §5: the contents list IS the outline. The switch exists because short forms stacked for a sign run should flow. |
| 6 | **Preview before print, never auto-print.** Build & preview shows the stitched document with a bar (Edit stack / Exit / Print). | Packet §2: the glance at the cover is the last line of defence. |
| 7 | **`sessionStorage`**, key `dr-compose-v1`. Refresh keeps the stack; closing the tab loses it. | He said a wipe is acceptable; this is kinder at the same cost. |
| 8 | **Opened from the printer panel ("Compose from several pages…") or `#compose`.** A full-screen workspace, not a generated page. | A generated page means a Python hook and a nav prune; the overlay needs neither and ships today. Phase 2 can promote it to a real page if wanted. |
| 9 | **Every control drawn** (printctl v2 ruling 12). | His standing ask. |

## §4 Files

| File | What |
|---|---|
| **NEW** `assets/printcompose.js` | library, stack, stitch, link law, preview, binder export |
| **NEW** `assets/printcompose.css` | the workspace, the bar, print rules for the stitched document |
| `assets/printctl.js` / `.css` | the "Compose…" door in the panel |
| `docrender/assets.py` | both files join `_PRINTCTL_ASSETS` (same PR, D6). Block comment condensed, file now **smaller** than before (22,505 → ~22,317 B). |

## §5 Not verified

✅ `node --check` clean. 🔴 **No browser run.** Most likely first failures, named: (a) the site has no search index (the composer says so); (b) a page's body uses a class the curtain test mistakes for a router, so it is skipped with a name; (c) a data table that relies on `data.js` at load looks unstyled in the stitched copy. Acceptance: open the printer icon → Compose, add three pages, reorder, Build & preview, check cover links jump, print to PDF.

## §6 Phase 2: binders (built 2026-09-28)

> Michael: *"build binders by id - and keep it simple / one file per binder (it's just a program page type) / yes, I'd like to see them as preset options in the composer"*

    ---
    title: Crew Binder
    id: binder-crew
    type: program
    status: unlisted
    binder: true
    chain:
      - policy-fire
      - policy-ladders
    ---

| # | Ruling | Why |
|---|---|---|
| P1 | **A binder is a `type: program` page with `binder: true`. Its pages are its `chain:`.** | His words. No new type, no second list: `chain:` via `nav.declared()` is the one resolver (nav.py refused `steps:` on this ground). |
| P2 | ⚠️ **Being a program, a binder's members get its flow strip** and its prev/next wiring where unclaimed. | The price of "just a program page". A print-only binder would be a new type later, not a flag now. |
| P3 | **Public members only, refused and named in the build report.** | Packet leak rule. The composer only lists public pages, so a preset must not be the back door. |
| P4 | `docrender/binder.py` (hook 05b, `on_nav` + `on_post_build`) writes **`binders.json`**: `{binders: [{id, title, pages: [{loc, title}]}], ids: {url: id}}`. Written every build. | `loc` equals the search-index location, so the composer needs no mapping. `ids` lets "Copy as binder" return real `chain:` ids. |
| P5 | **Presets are chips above the filter.** A click replaces the stack + title; reorder freely after. A missing file = no chips. | Presets are a starting point, not a lock. |
| P6 | **"Copy as binder" copies a whole binder page frontmatter** (`status: unlisted` so it does not join the sidebar). A page with no `id:` is emitted as a comment telling you to add one. | By id, as ruled. |

## §7 Footer note (printctl, same PR)

Panel field "Footer note" + "Add a line" / "Replace Posted by". Inserted at `beforeprint`, removed at `afterprint`; one per article (per `.dr-compose-sec` in the composer). Replace hides that article's `.dr-owner` and puts the note in its slot wearing the same class. 🚫 **Not a per-sheet footer**: it lands at the end of each article, like the owner line. A true every-sheet footer is §8.

## §8 Every-sheet footer (NOT built)

`runfoot.py` (`@page` margin boxes) is intact but off: the boxes painted nothing in Michael's Chrome (print-identity.css, THE RETIRED RETIREMENT). The honest next candidate is a repeating `<tfoot>` spacer + `position: fixed` footer, which Chrome and Firefox repeat per sheet. Risk: it wraps the article in a table, which touches `break-before`, the 640px data-table threshold, and every `> child` selector. Prototype on one page behind a toggle before it goes near the composer.

## §9 COPY AS TEXT — the composer's second output (built 2026-10-03)

> Michael, 2026-10-03: *"i take notes i've generated, like default run sheets for audio, lighting, or stage management, and deliver them to those department heads as files for them to edit... i usually just pop into an email and provide the basic starting run sheet that they work from, which they can paste into their own Google Doc."* And: *"what if i could choose a toggle for the level of stripped html formatting?"*

### §9.1 🔴 IT IS A CLIPBOARD WRITE, NOT A FILE, AND THAT IS THE WHOLE COST SAVING

The ask arrived as *"an export option in the print menu, perhaps labeled 'page text'"* and the destination chain is what killed every word of that framing: **rendered page → email body → somebody else's Google Doc.** Nothing in that chain is a download.

| what it is NOT | why it matters |
|---|---|
| not a file | `print-packet.md` §5's refusal of a second renderer is untouched. The engine still emits no bytes. |
| not a distribution artifact | there is no URL, so there is nothing for the packet leak rule to govern. This is Michael exercising his OWN read access, which is categorically different from a PDF parked at a public link. |
| not in the print menu | print is paper. This is a clipboard, and it lives on the preview bar. |
| not a new `export:` kind | `packet.py`'s `export:` serves a program's `chain:`, which is a declared reading order. A run-sheet handoff is an ad-hoc pick, which is the COMPOSER's job. |

⭐ **AND IT IS A FOLD-IN RATHER THAN A FEATURE, twice over.** `stitch()` already returns the finished `.dr-compose-doc`, so there is nothing to assemble; and `copyBinder()` **already writes to the clipboard in `printcompose.js`**, so a copy action is not a new category in this codebase. The payload gets pasted TWICE and has to survive both hops.

### §9.2 🔴 THE GOVERNING RULE: THE DIAL MOVES FORMATTING AND NEVER CONTENT

`print-control.md` §1: *"a print option is safe only if it cannot change what the document says."* That table **refused callout density outright** as a reader control, on the grounds that it decides *"whether a hazard box still reads as a hazard box"* — Hawthorne's floor, not a preference. A "strip my markdown classes" control walks straight into it.

✅ **The dial is legal because one thing is NOT on it.**

| rung | emits | tables |
|---|---|---|
| **rich** (default) | semantic HTML: `h1-h6`, `p`, `strong`, `em`, `ul`/`ol`, `li`, `blockquote`, `code`, `pre`, `a`, `table` | real tables |
| **plain** | text only, headings upper-cased on their own line, list items as `- ` | 🔴 **LIST MODE** |
| **both** | ⭐ **the callout's WORD** — `DANGER:` · `WARNING:` · `NOTE:` | — |

🚫 **NO `class`, NO `style`, NO custom property survives either rung.** That is what Michael meant by *stripped*: **the structure travels, the skin does not.** A Doc that arrives wearing `uritp` black-and-gold is the thing he is trying to avoid.

🔴 **IN RICH MODE THE WORD HAS TO BE INJECTED, and that is the subtle half.** The red border is painted by the class, and the class is stripped — so a faithful strip would silently delete the hazard while looking like it preserved everything. `copytext.js` inserts `<p><strong>DANGER:</strong> …</p>` ahead of the box's own content and keeps the admonition title rather than dropping it. **A callout that loses its border and keeps its word is degraded; one that loses both is censored.**

### §9.3 ⭐ TABLES DEGRADE TO LIST MODE, REUSING A RULING RATHER THAN INVENTING A FORMAT

`data.css` flips to list mode inside `@container dr-table (max-width: 640px)` because **a table cannot survive a narrow measure.** An email body and a pasted Doc are narrower than any sheet this engine prints, so the condition is met by definition. One labelled line per cell, `Header: value`.

⚠️ **A row with no `thead` to label it emits the cell text alone** rather than an invented column name. 🔴 This makes `copytext.js` the **fifth** place the 640px number is load-bearing (`print.css`'s `@page`, `print-control.md` §1, §8's binder ceiling, `printctl.js`'s 1.5in inline budget are the first four). A plain-text pipe table pasted into a Doc is a wall of punctuation, which is the outcome this ruling exists to avoid.

### §9.4 ⭐ PLAIN-VERSUS-RICH WAS A FALSE FORK FOR THE DESTINATION

One clipboard write carries **two flavours at once** (`text/html` + `text/plain` in a single `ClipboardItem`), and the destination picks: a Doc takes the HTML, a plaintext composer takes the text. **So the dial decides which flavours we OFFER, never which one the recipient gets.** Ladder, matching `copyBinder()`'s exactly: `clipboard.write` → `clipboard.writeText` → `window.prompt`. ⚠️ **A clipboard write is invisible by construction**, so the status line is the only receipt a copy can give and "it worked" and "it silently failed" are the same blank bar without it.

### §9.5 Rulings

| # | Ruling | Why |
|---|---|---|
| C1 | **The copy lives on the PREVIEW BAR, beside Print. Never on the stack footer.** | Ruling 6's argument verbatim: the document must exist and be visible before it leaves. A stack-footer button would also copy something not yet built. |
| C2 | 🚫 **NO EDIT TO `printcompose.js`.** A new `assets/copytext.js` appends its own controls when `.dr-compose-bar` appears. | That file is 22,021 B against a ~22KB read ceiling. The observer is what buys the zero-byte change. |
| C3 | **An ALLOWLIST of tags, never a denylist. An unknown tag is UNWRAPPED to its children.** | `packet.py`'s own lesson about its retired strip tuple: *"a defence that must be updated by everyone who never reads it is not a defence."* Content is never lost, only its formatting. |
| C4 | **`sessionStorage`, key `dr-copytext-v1`.** Dies with the tab. | Ruling 7's shape. A persisted formatting preference is `print-control.md` §6's refused `localStorage` by another name. |
| C5 | **A drawn switch wearing the composer's own `.dr-compose__switch` chrome.** | Ruling 9 / printctl v2 ruling 12. Inventing a second control language for two controls sitting inside somebody else's bar would be a second claimant on one look. |
| C6 | **Every safety property is INHERITED, not re-argued.** | Ruling 1 means the library is public pages only; ruling 2 means a curtained body is already skipped and named. This module reads only what the composer already stitched, so it **cannot widen that fence.** |
| C7 | 🚫 **A markdown rung is NOT built.** | Michael's recipients work in Google Docs and email, neither of which renders markdown. A third rung is a real candidate the day a recipient uses a markdown tool, and not before. |

### §9.6 Files

| File | What |
|---|---|
| **NEW** `assets/copytext.js` | the converters, the clipboard ladder, the bar observer (15,193 B) |
| **NEW** `assets/copytext.css` | the wrapper, the status line, the print refusal (2,827 B) |
| `docrender/assets.py` | both join `_PRINTCTL_ASSETS`, same PR (D6). ⭐ **`hand_written_css()` needed NO edit** — an existing group, the `print-md-bridge.css` precedent. |

### §9.7 🔴 Not verified, and a numbering flag

✅ `node --check` clean. ✅ The module **loads and exports clean** with the DOM stubbed at the boundary only — which is more than §5 got, and is the shape `blocks.py`'s outage post-mortem prescribed (*"a test that reimplements its subject tests the reimplementation"*).

🔴 **THE CONVERTERS ARE NOT VERIFIED AGAINST A REAL DOM.** No jsdom was available. Named likely first failures, in order of my own suspicion: (a) **a stitched data table that already looks unstyled per §5(c) will convert from whatever it actually is, not from what the table was** — §5's third predicted failure is directly upstream of §9.3 and nobody has looked yet; (b) `family()` reads Material's class list, so a callout rendered by `blocks.py` under a class this engine added later wears `NOTE` rather than its own word; (c) nested list indentation is computed from recursion depth rather than from the DOM's list nesting, so a list inside a callout inside a list may over-indent.

⚠️ **AND THE BASE IS STILL UNVERIFIED.** §5 has said *"No browser run"* since 2026-09-28 across phase 1, phase 2 and §7. **This is a second unverified layer on the first and it says so rather than inheriting a green it was never given.** Acceptance: §5's three pages → Build & preview → Copy text with the switch off, paste into a Doc → switch on, paste into a plain email → confirm a `!!! danger` reads `DANGER:` in both.

🚩 **NO BUILD NUMBER IS CLAIMED BY §9, DELIBERATELY, and the reason is a live mess rather than modesty.** This file's H1 says **BUILD 11**; `printcompose.css` says **BUILD 11 phase 1**; `printcompose.js` says **BUILD 12**; `specs/contacts.md` also claims **BUILD 11** — and **not one of them has a row in `next-build-spec.md`.** That index's standing debt item 1 already says nothing in it can be trusted while two specs can share a name, and its recommendation is that a spec carry no number at all. 🚫 Nothing is renumbered here: the index's own rule is that a heading belongs to the file that wrote it, and rewriting one to tidy a table is a stance shift rather than a cleanup. **It is one ruling from Michael, and it is owed.**
