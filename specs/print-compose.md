# BUILD 11 · THE PRINT COMPOSER — pick pages, order them, print one document

✅ **Phase 1 BUILT 2026-09-28** (browser-side, casual). ⏳ **Phase 2 (repo-declared binders) NOT built**, shaped in §6. Workshop: Maestro Mira (scope) + Dev Dexter (engine), one pass. Decision history: the **doc-render-engine (repo) Decision Log** subpage in ClickUp.

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
| 4 | **Stripped per section:** scripts, edit button, source-file footer, `.dr-flow*`, `buildstamp*`, `.dr-packet*`, the print menu. | Packet A8 reasoning. |
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

## §6 Phase 2 shape (not built)

"Copy as binder" already emits the shape:

    binder:
      title: "Crew binder"
      pages:
        - "policies/fire/"
        - "policies/ladders/"

Proposal: a `binders.yml` in the instance, each entry built by the packet machinery (`packet.py` / `packetbuild.py`) into a generated page, with the packet's coverage report and leak refusal. Open questions for Michael: locations (URLs, as copied) or `@id`s; one file or one per binder; do binders appear in the composer as presets.
