# BUILD 8 — a PRINT CONTROL surface: per-page defaults, and a reader-facing menu

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-30. Indexed from [`next-build-spec.md`](../next-build-spec.md) — 🚩 **see §7, that index could not be edited in this pass.** Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

> Michael, 2026-08-30: *"what i think i'm coming up against soon is a real 'print' menu that I can control on this app. to begin it's accessible for me as a widget maybe, but then ultimately we backend it as defaults and codable options per page?"*

---

## One line

He named **two features in one sentence**, and they have almost nothing in common. This spec's whole job is to separate them, because building them as one thing is how the cheap half gets held hostage by the expensive half.

| | What | Where the state lives | Cost |
|---|---|---|---|
| **A** | **per-page print DEFAULTS**, declared in frontmatter | the CONTENT, at build time | small, and the idiom already exists |
| **B** | **a reader-facing print MENU** (the widget) | the BROWSER, at read time | large, and it is a new category for this engine |

⭐ **A is buildable this week and B is not, which inverts the order he proposed.** He said *"to begin it's a widget... then ultimately we backend it as defaults"* — but the backend half is the CHEAP half here, because the engine already has a `print:` frontmatter block, a `hide:` list and a one-value type dial. The widget is the part with no precedent.

---

## 🔴 §1 — THE BLOCKING FINDING: THE PAGE MARGIN IS A DATA CONTROL WEARING A LAYOUT COSTUME

**This is the reason a print menu cannot be a generic set of sliders, and it must be read before anything else in this document.**

`assets/print.css` sets `@page { margin: 12mm }` and its comment calls that *"a MEASUREMENT, NOT A MARGIN PREFERENCE... the least obvious rule in this file."* The data table flips to list mode inside `@container dr-table (max-width: 640px)`, and **a printed page is a container like any other**:

```
US Letter, browser-default 1in margins ->  6.50in ->  624px   LIST MODE
US Letter, print.css 12mm              ->  7.56in ->  725px   stays a TABLE
A4,        print.css 12mm              ->  7.33in ->  703px   stays a TABLE
```

🔴 **SO A "MARGINS" CONTROL IN A PRINT MENU SILENTLY CONVERTS EVERY DATA TABLE ON THE SHEET INTO A STACK OF KEY/VALUE ROWS.** Not broken, not reported, not the table the author wrote — and it would happen at READ time, where no build report exists to say so. print.css already spells out the direction of the danger: *"THE LEFT/RIGHT MARGINS ARE THE LOAD-BEARING HALF. The BLOCK axis is free to change."*

⚑ **THE GENERALISATION, AND IT IS THE SPINE OF THIS BUILD: A PRINT OPTION IS SAFE ONLY IF IT CANNOT CHANGE WHAT THE DOCUMENT SAYS.** Sorting that list once, up front, is most of the design work:

| Option | Changes | Verdict |
|---|---|---|
| body text size | how much fits per sheet | ✅ **safe** — one dial already exists |
| the letterhead on/off | identity only | ✅ safe |
| the corner stamp on/off | provenance only | ✅ safe |
| a QR on/off | ⚠️ a routing affordance | ⚠️ arguable, see §4 |
| leading / block spacing | how much fits per sheet | ✅ safe, and it is `em` so it follows the dial for free |
| **INLINE margins** | 🔴 **whether a table is a TABLE** | 🚫 **REFUSED as a reader control** |
| **callout density** | 🔴 whether a hazard box still reads as a hazard box | 🚫 **Hawthorne's floor, not a preference** |
| **ink colour** | 🔴 legibility on a photocopy | 🚫 ruled 2026-08-29, one property, one medium |

✅ **AND THE SAFE COLUMN IS ALREADY ONE VALUE.** `print-type.css` §0 declares `--dr-print-base: 10pt` and its own header says *"If the body reads small, `--dr-print-base` is the single value to move and everything follows it"* — because the ramp and every margin in `print-space.css` are `em`. **A print menu's entire useful surface is one custom property and three booleans.** That is the shape to build, and it is much smaller than "a print menu."

---

## ⚠️ §2 — WHAT THE BROWSER ALREADY GIVES HIM, AND WHY ONE CONTROL IS A TRAP

Every print dialog already offers paper size, margins, scale, background graphics and page range. **Two of those are the exact controls §1 just refused**, which means the danger already exists and this build does not create it — it can only choose whether to add a second, blessed path to it.

🔴 **AND THE SCALE CONTROL IS ALREADY VERIFIED USELESS FOR WHAT PEOPLE REACH FOR IT FOR.** `print.css`, from two PDFs of one page at 100% and 70%: *"the line breaks are byte-identical in both. Scale is a photographic reduction of a page that has ALREADY been laid out — it cannot reflow, so type and column shrink together and the right margin grows."*

⚑ **So the honest framing of this whole build: the browser's print dialog offers four controls, of which one (scale) does not do what a reader thinks and two (margins, background) can damage the document. A URITP print menu earns its existence by offering the ONE control the browser does not have — the type dial — and by not offering the ones it does.**

✅ **"Background graphics" is the one native toggle worth documenting rather than replacing.** `print.css` applies `print-color-adjust: exact` narrowly, to *"elements whose MEANING is carried by a colour"* — a `!!! danger` border, a marker chip, the letterhead. A reader who switches backgrounds off in the dialog loses none of those, by construction. **That is a property worth stating in the authoring page, not a control worth rebuilding.**

---

## ✅ §3 — FEATURE A: PER-PAGE DEFAULTS. THE IDIOM ALREADY EXISTS, THREE TIMES OVER

This half needs no new mechanism, and that is the argument for doing it first.

```yaml
---
hide: [navigation, toc, footer]        # already live, already per-page
print:
  logo: logo-horizontal                # already live (BUILD 5, shipped 08-29)
  base: 11pt                           # NEW -- the one dial, per page
  stamp: false                         # NEW -- suppress the corner mark
  qr: false                            # NEW -- see 4
---
```

⭐ **THREE PRECEDENTS, ALL LOAD-BEARING RATHER THAN DECORATIVE:**

1. **`print:` is a real instance-and-page key already.** `buildstamp.py` reads `state.INSTANCE["print"]["logo"]` at HEAD. A page-level sibling is the same shape one level down.
2. **`hide:` is per-page and reaches the print layer today.** `40-forms/incident-report.md` carries `hide: [navigation, toc, footer]`, and `print-chrome.css` hides all three anyway — so a per-page print key that a print sheet honours is not a new coupling.
3. **`--dr-print-base` is already a custom property on `.md-typeset`**, so a per-page override is an inline style on one element, not a stylesheet edit. 🔴 **AND IT MUST BE `pt`** — print-type.css §0 argues the unit at length, and §3b's `em`-vs-unitless finding cost this repo two reverts.

⚠️ **THE ONE REAL DECISION IN FEATURE A IS PRECEDENCE, AND IT IS NOT OBVIOUS.** There are now potentially three declarations of the same fact: `instances/<slug>/site.yml` (the site), a page's frontmatter (the page), and a reader's menu (the session). 🔴 **`specs/scoped-theme.md` §4c is the warning to read first:** a scoped selector silently kills a print sheet on the pages it scopes, because that sheet wins on source order at equal specificity. **A per-page print override is a scoped declaration by another name.**

✅ **Recommend: SITE < PAGE < SESSION, and every level is a custom property on the same element rather than a new selector.** A custom property re-declared on `.md-typeset` cannot lose a specificity fight to a print sheet, because the print sheets CONSUME `var(--dr-print-base)` and never re-declare it. ⚑ *An override expressed as a value beats an override expressed as a selector, every time, in a cascade nobody wants to reason about again.*

---

## 🔴 §4 — THE QR TOGGLE IS THE ONE "SAFE" OPTION THAT IS NOT SAFE

`!!! qr "x" print=true` already puts a scannable code on paper, and on 2026-08-29 that code plus the fallback link became **the entire printed route to the incident-report form**, by ruling — the embedded form is hidden on paper and *"paper routes a reader to the live form instead of impersonating it."*

⚠️ **SO A `qr: false` PRINT OPTION REMOVES THE ONLY WAY A PERSON HOLDING THAT SHEET CAN REACH THE FORM.** It is not a styling toggle on that page, it is the difference between a routable document and a dead one. 🔴 **Hazard Hawthorne owns this**, on the same grounds as the legibility floor: a safety document that cannot be acted on is a safety defect, not a layout preference.

✅ **Recommend: `qr:` is a PAGE-level key and NOT a reader-facing control.** An author suppressing a code on a page they wrote is making an editorial decision with a name attached; a reader unticking a box in a menu is removing an affordance they cannot see the consequence of.

---

## 🔴 §5 — FEATURE B: THE WIDGET. THREE THINGS IT COLLIDES WITH

### §5a — The engine has no reader. That is architecture, not an oversight.

`datatable.py` states it plainly: **"THE RENDERER NEVER LEARNS WHAT DEVICE IT IS ON, AND CANNOT. MkDocs builds one file and Pages serves those same bytes to every reader — there is no request, no viewport, no user agent at build time."** Every responsive behaviour in this engine is therefore a CSS container query, resolved in the browser.

⚠️ A print menu is the first feature that would hold **reader-owned state**. The only precedent is `router.js`, and it is a curtain rather than a preference — it reveals content, it does not restyle it. **So this build introduces a category, and the honest cost is that everything after it can point at it.**

### 🚫 §5b — THE WIDGET MUST NOT PRINT, AND THAT IS THE DEAD-CONTROL RULE AT ITS PUREST

print.css's test for its chrome-off list is *"could a reader ACT on it with a pen?"* A print menu fails it maximally: it is a control whose entire purpose is to affect the sheet it would be printed on. **It joins the chrome-off list in the same commit that creates it**, or the first printout carries a picture of the menu that made it.

⚠️ **AND IT INHERITS `qr.py`'S SCAR IN REVERSE.** That file records: *"a `print=true`-only code IS INVISIBLE ON SCREEN, so 'it failed to resolve' and 'it resolved and is correctly hidden' are the same blank space to its author."* A print menu is the opposite — **visible only on screen, and it controls something the author can only verify by printing.** Every setting it offers is unverifiable in the surface that offers it.

### ⚠️ §5c — EVERY READER-FACING OPTION INVALIDATES EVERY HAND-PLACED PAGE BREAK, AT READ TIME

`print-type.css` §8 keeps a running count of how many times `{.new-page}` has been invalidated by a change to the print layer. **It stands at eight.** Every one of those eight was a BUILD-time change, made by somebody who could re-preview.

🔴 **A reader-facing type dial invalidates them on every setting change, in the reader's browser, with no build and no report.** ⚑ *This is not a new defect, it is the existing scar acquiring an unbounded number of instances.* The mitigation is the one §8 already recommends and nobody has needed until now: **do not author `{.new-page}` at all**, and let `print-flow.css`'s automatic rules do the work. 🚩 If Feature B ships, that recommendation should become a refusal.

---

## ✅ §6 — THE SANCTIONED SHAPE, IF B IS BUILT

⭐ **`publish.yml`'s `theme` input is the precedent worth copying, and its property is the one that matters:** it overrides for ONE build and **writes nothing to disk**. `specs/print-identity.md` §3 calls that shape *"the right shape for an escape hatch — it permits looking without permitting drift."*

So:

- **🚫 NO `localStorage`.** A persisted print preference is a setting that outlives the reason for it, is invisible to everyone else, and makes "why does my printout differ from yours" unanswerable. Session-only, resets on reload.
- ✅ **Every control writes ONE custom property** on `.md-typeset` and nothing else. No sheet is toggled, no selector is added, no class is applied. That keeps the print group's "no two sheets share a selector-and-property pair" invariant untouched — the invariant three files now assert and one has already broken by accident.
- ✅ **The menu is a `<details>` with real inputs**, not a script-built panel — so it is keyboard-reachable and needs no framework, on the `forms.py` `collapsed:` precedent.
- 🔴 **It offers the SAFE column of §1 and nothing else.** If a control cannot be added without changing what the document says, it is not added.

---

## ⏳ Rulings needed

1. **🔴 Does the widget ship at all, or is Feature A enough?** ✅ **Recommend A first, alone, and live with it.** A is small, testable, and the thing he actually needs for *"defaults and codable options per page."* B is a new state category whose most valuable control (the type dial) is also available as a page default. **Ship A, print a few sheets, and see whether B is still wanted.**
2. **Which controls does the safe column contain?** §1's table is the recommendation. Margins, callout density and ink are refused as READER controls; §4 refuses `qr:` as one too.
3. **🔴 Is a printed sheet allowed to differ between two readers of the same page?** This is the question underneath the whole build and it has not been asked. `instances/uritp-safety/site.yml` carries Michael's own ruling that printed header/footer CONTENT must not differ per site — a reader-facing menu makes it differ per PERSON. **Recommend: the type dial yes, anything carrying content or provenance no.**
4. **Where does Feature A's `print:` page block get validated?** `objects/` owns page vocabulary and `docrender/instance.py` is **23,047 B and already past the ceiling**, with BUILD 5's `print:` block queued behind it. **Recommend a new small module rather than either.**
5. **Does `--dr-print-base` get a floor?** §7 of print-type.css defends ~10pt for photocopy and shop-floor legibility, and Hawthorne owns that floor. **Recommend a clamped range rather than a free number, with the clamp stated in the report.**

---

## ⚠️ §7 — FILES, AND THE ONE EDIT THIS PASS COULD NOT MAKE

| File | At HEAD | Change |
|---|---|---|
| **NEW** `assets/print-control.css` | — | the menu's own chrome, plus its chrome-off rule |
| **NEW** `docrender/printopts.py` | — | reads the `print:` page block, emits the custom properties |
| `assets/print-type.css` | **22,289 B** | 🔴 **239 B of headroom. Its own PR asked that the next edit SPLIT it first.** |
| `docrender/instance.py` | 23,047 B | 🔴 already past the ceiling. Not the home for this. |
| `next-build-spec.md` | **32,840 B** | 🚩 **NOT EDITED — see below.** |

🔴 **THE INDEX ROW FOR THIS BUILD WAS NOT ADDED, DELIBERATELY, AND THE REASON IS A STANDING RULE RATHER THAN CAUTION.** `next-build-spec.md` is 32,840 B and the GitHub MCP operating standard is explicit: **large files (>~30KB) never go through `create_or_update_file`** — LOCKED 2026-07-02 after it corrupted a file four times in one session. The only write path available here replaces the whole file.

⚠️ **AND THE INDEX IS ALREADY WRONG IN EXACTLY THE WAY IT PREDICTED.** Its header says *"SIX INDEPENDENT BUILDS ARE INDEXED HERE"* and its table has six rows, while **`specs/view-embed.md` exists on disk, calls itself BUILD 7, and appears in no row** — the identical defect it documented about BUILD 5 two weeks ago, and it left instructions: *"if it is wrong again, delete it rather than refresh it."*

🚩 **So three edits are owed to that file and all three need a safe write path:** delete the stale count, add rows for BUILDS 7, 8 and 9. **Recommend the same fix its own header already asks for — move BUILDS 1 and 2 into `specs/`, which drops the file to an index of ~4KB and makes it editable again.** That is the change that stops this recurring, and it is a pure move.
