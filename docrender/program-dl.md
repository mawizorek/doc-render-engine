# `program.py` — rationale

Sibling to `docrender/program.py`, on the `forms-dl.md` pattern: **the mechanism and
its warnings live in the module; the arguments and incidents live here.** Started
2026-09-28. Older strip rulings (J19–J23, cited in the module) sit in the ClickUp
doc-render-engine Decision Log and are not restated.

---

## D1 · ONE STRIP, CHOSEN BY HOW YOU ARRIVED (2026-09-28)

> Michael: *"some pages render it twice, in the footer and in icon buttons just above
> it."* · *"i need a way to have the app version of the binder and the non-app version
> without having to maintain both chains."* · *"having emergency contacts part of
> multiple binders doesn't hold up well currently."*

### What was actually wrong (verified on gh-pages, not guessed)

1. **Two prev/next surfaces.** `nav.py` rewires Material's `previous_page`/`next_page`
   to the chain, so `navigation.footer` drew a second prev/next under the strip. The
   only suppressor was a hand-typed `hide: footer` (J19). Every page that forgot it
   (the `REPO_PAGES` handbook pages) showed both.
2. **Two chains for one binder.** The app handbook and the binder each declared the
   same 23 ids, so every member page drew two identical strips.
3. **Emergency Contacts drew FOUR strips** (binder, app copy, eh-handbook's lone
   Finish, General Safety step 4 of 7), and which one got Material's single slot was
   whatever path sorted first.
4. **Flow context rode on `:target`** (`promote.py`), which dies on the first in-page
   anchor click and does nothing for a sidebar arrival.
5. **`chrome: app` hid `.dr-flows`**, so an app binder could not have buttons at all.

### ✅ The ruling (Workshop 2026-09-28, Frank: FOLD-IN, zero new keys; Mira: ADJUST)

- **Faces.** `chain: "@target"` (string form) makes a page walk another program's list
  without owning its buttons. One list, two faces. `chrome: app` is the app face; the
  body keeps `!!! chain "target"` for its contents. Alias-of-alias and dead targets are
  reported, never resolved. (`nav.py`.)
- **The server renders every strip; the browser picks one.** Links carry
  `?via=<flow id>`. A ~1KB ES5 script reads `?via=`, else the page's own start flow,
  else sessionStorage `dr.via`, and marks the match `is-via`; CSS hides the rest.
  Start strips always show. Under a face, the program/Finish links point at the face
  hub and `via=` is rewritten, so the app stays an app the whole way through.
- **No match** (sidebar, search, bookmark): the first strip by `order:` shows, plus an
  "Also part of" line whose links re-open **this page** under another program.
- **Footer auto-hide.** Any page that renders a strip gets `footer` appended to
  `page.meta['hide']`. J19's hand-typed rule is now automatic.
- **Buttons.** Two equal cards, direction word over title. Next filled, Previous
  outline, Finish in `--dr-good`, Start full width. ≥2.9rem; under 600px they stack
  with Next on top.
- **CSS ships inline** (`<style class="dr-flowctx">`) because `flow.css` was past its
  ceiling and `assets.py` past its write cap. `flow.css` now holds embeds only.
- **`promote.py` deleted.** `chrome.py` no longer hides `.dr-flows` under `dr-app`.

### 🔴 This REVERSES the no-JS ruling, and says so

`promote.py` was written script-free on purpose. That ruling bought a footer that could
not survive an anchor click and could not know about faces. ⚑ **A principle that
produces a broken control is a cost, not a virtue.** The fallback is honest: with no
script every strip shows, which is the old page minus the cap. Nothing becomes
unreachable.

### 🚫 Out of v1

Switching programs in place (chips), printing only the active strip (print-chrome.css
hides strips on paper anyway), progress/completion state.

### ⚠️ Known edges

- sessionStorage is per tab. A new tab with no `?via=` falls back to `order:`.
- Rewritten hrefs become absolute (the script assigns `a.href`). Cosmetic.
- A page two binders both list still draws both strips server-side; only one shows.
  That is the design, not a leftover.
