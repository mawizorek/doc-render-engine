# BUILD 11 · THE PRINT COMPOSER — pick pages, order them, print one document

✅ **Phase 1 BUILT 2026-09-28** (browser-side, casual). ✅ **Phase 2 binders BUILT 2026-09-28** (§6), plus the footer note (§7). ⏳ Every-sheet footer NOT built (§8). Workshop: Maestro Mira (scope) + Dev Dexter (engine), one pass. Decision history: the **doc-render-engine (repo) Decision Log** subpage in ClickUp.

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
