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

---

## D2 · THE PILL IS FOR CLICKING, THE STRIP IS FOR READING (2026-10-02)

> Michael: *"I'd like to be able to leave my mouse in one spot and click 'next'
> repeatedly as I go through the pages."* · *"the footer position adjusts based on the
> length of the article."* · *"I don't need to see 'Next in program' or specific part
> names constantly. Perhaps those details could appear if I hover."* · *"It is still
> important to have that information available somewhere on the page."* · then:
> *"Build it, but slim down the text and information in the footer."*

### What was wrong

D1 put the only control at the FOOT of the article, so its screen position was a
function of article length. Reading a binder meant hunting for the button on every
page. D1 solved WHICH strip shows; nothing addressed WHERE the control sits.

### ✅ The ruling (Mira seated, Dexter built; Frank: FOLD-IN, same module, zero new keys)

- **A pill per strip: `‹ Last` · `Next ›`, `position: fixed`** at `top 3.4rem /
  right .6rem`, directly under the `chrome: app` toolbar pill and under Material's
  2.4rem header on full-chrome pages. ⭐ Fixed, not merely "at the top": anything
  above an in-flow control (back link, title, lede) varies per page too.
- **Next never moves.** Fixed-width buttons, right-anchored pill, Next rightmost;
  Start and Finish ✓ take Next's slot; a missing Last is greyed, never removed.
  Verified headless at 1100px: Next/Start/Finish at the same rect (997,73, w86) on
  the hub, a middle step and the last step.
- **Detail on hover** (`title` + `aria-label`): *"Next: Lighting Sheet (SM Binder,
  step 3 of 3)"*.
- **The foot strip stays, as one row:** `← prev title` | `Program 2/3` |
  `next title →`. Direction words, filled cards and the step chip removed.
- **Selection is free.** The pill lives inside its `<nav>`, so D1's `is-via` hiding
  hides it too. No script: first strip's pill only. A member pill outranks a start
  pill via `:has`.
- **Under 600px the pill docks bottom-right** (the thumb zone; top-right sat on the
  page title). Never prints.

### 🔴 This REVERSES D1's "one navigation surface per page," and says so

D1's rule was aimed at Material's footer duplicating the strip: two surfaces doing
the SAME job. This is two surfaces doing DIFFERENT jobs, control vs reference.
⚑ **The defect D1 fixed was duplication, not plurality.** Material's footer is still
suppressed.

### ⚠️ Known edges

- On mid-width screens with full chrome the pill can overlap the top of the right
  TOC sidebar or the first line of wide content. It has its own ground and shadow.
- Hover titles keep the TARGET's name under a face; the face swap rewrites hrefs and
  visible text, not titles. Cosmetic.
- Keyboard ←/→ deliberately NOT bound: it would fight text inputs and tabs. Tab
  order reaches the pill at the foot of the content, where it sits in the DOM.

---

## D3 · THE PILL WAS SLOP; THE CONTROL BELONGS TO THE HEADER (2026-10-02, same day)

> Michael, on the first live render: *"the pills look like ai rendered slop widget.
> fucking gross."* Screenshot: the fixed pill sitting on the TOC heading.

### What was wrong

D2 drew a NEW object (rounded pill, shadow, filled accent button, text labels) and
floated it over the page. It was stable, which was the requirement, and it read as
a widget bolted onto someone else's interface, which was the failure. The "known
edge" D2 wrote down (overlapping the TOC on mid-width full-chrome pages) was the
first thing he saw. ⚑ **A known edge on the most common layout is not an edge.**

### ✅ The ruling

- **Two Material header icons**, chevron-left / chevron-right (Finish = check),
  built as `md-header__button md-icon`: the same object as the light/dark switch
  and the print button, inheriting their size, colour and spacing.
- **The foot script docks the active strip's pair as the LAST child of
  `.md-header__inner`.** The header is the one surface that never moves, and
  last child makes Next the rightmost control. Verified headless at 1100px on full
  chrome (Next at 1055,4 on hub / step 1 / step 2 / last step) and `chrome: app`
  (1041,16 on all four).
- **`chrome.py` exempts `.dr-flow__pill`** from the app-chrome hide rule, so the
  icons join the floating app pill instead of vanishing.
- **Undocked = invisible.** No script or no header leaves the foot strip as the only
  control, which is the D1 page.
- The fixed position, the bottom-right mobile dock and the text labels are gone.

### ⚠️ Known edges

- A thin divider separates the pair from the theme/print icons. If it reads as
  furniture, it is one rule.
- Hover titles under a face still carry the target's name (unchanged from D2).
