# `assets.py` — incident history and the arguments behind hook 05

Companion to [`assets.py`](assets.py). **This file is the SINGLE CLAIMANT for the history in it.** The module states conclusions and points here; it does not restate the accounts. Same contract as [`buildstamp-dl.md`](buildstamp-dl.md), [`forms-dl.md`](forms-dl.md) and [`views-dl.md`](views-dl.md).

<p><br/></p>

⚠️ **Why this file exists.** `assets.py` reached **32,684 B** against a ~22.5 KB read ceiling and a 30 KB write cap — unreadable whole, unwritable at all. The extraction was owed since **PR #190 (2026-08-29)**, named four more times, and on 2026-08-30 it stopped being tidiness: it was the last thing standing between Michael and a **ruled** BUILD 9 feature, because a new stylesheet needs one tuple line in a file nothing could edit. **The mechanism was always ~90 lines. The rest was this.**

<p><br/></p>

🔴 **WHAT DELIBERATELY STAYED BEHIND, because it is the whole judgment of the split.** Every **load-order LAW** is still inline in `assets.py`, beside the tuple it governs — `chrome.css` after `base.css`, `nav.css` after `base.css`, `data-list.css` after `data.css`, `navtree.js` before `router.js`, and the print group's position. ⚑ **A guardrail belongs where the hand is about to act. A guardrail in a sidecar is a guardrail that does not fire** — which is this repo's single most-repeated defect, recorded five separate times as *"a rule that is correct in isolation and unreachable in place."* `buildstamp-dl.md` and `forms-dl.md` moved **arguments**; this file draws the line at **instructions**.

---

## D1 — WHY THE ASSETS LIVE OUTSIDE THE CONTENT TREE AT ALL

MkDocs publishes files it finds inside `docs_dir` and resolves `extra_css` relative to `docs_dir`. **Read literally, that means stylesheets and scripts must live inside the doc tree.** v1 did exactly that, and it is **the single largest reason its content folder was full of machinery.**

<p><br/></p>

The way out is the `on_files` event: append `File` objects whose source is somewhere else entirely — the engine's own `assets/` and the instance's folder. MkDocs treats them as ordinary site files from that point on.

<p><br/></p>

🚫 **So this hook is what makes the content-purity rule physically possible.** Read that before anyone "fixes" it by moving the CSS back where it looks like it belongs.

---

## D2 🔴 THE OUTAGE: `on_config` CANNOT SEE THE PAGES, AND IT BROKE THE ROUTER COMPLETELY

MkDocs runs **EVERY** hook's `on_config` before **ANY** hook's `on_files`. So at `on_config` time `state.BY_SRC` is empty — nothing has read a frontmatter block yet — and the old `_uses_router()` check therefore **answered False on every single build.**

<p><br/></p>

**Consequence:** `router.js` and `router.css` were PUBLISHED (that happens in `on_files`, by which point `BY_SRC` is populated) but **never LINKED from any page.** The form rendered, looked completely correct, had no JavaScript attached, and so submitting it did what an unhandled form does: reloaded the page. Which is precisely the symptom Michael reported — *"the page reloads so my guess is the unlock just doesn't hold."* **The unlock was never running.**

<p><br/></p>

✅ **The fix is to decide from something that EXISTS at `on_config` time.** Two sources, both cheap: the instance's `routes.yml`, and a scan of the content tree for the frontmatter keys. The scan is one pass over small text files, done once and cached, **which is a fair price for a check that cannot silently answer wrong.**

<p><br/></p>

⭐ **FEATURE ASSETS ARE STILL PUBLISHED ONLY WHERE THE FEATURE IS USED.** The principle was right; the implementation **asked a question too early.**

---

## D3 — THE FOUR REASONS A GROUP IS UNCONDITIONAL, AND THEY ARE NOT THE SAME REASON

Worth keeping separate, because each one answers a different objection and collapsing them would invite a gate where none is safe.

<p><br/></p>

**1. The GENERATED sheets** (`tokens.css`, `marks.css`, `blocks.css`) are built from `theme/*.tsv`, read straight off disk, and **do not care which event is running.** Nothing about them can answer wrong early, so they are never gated. **The D2 trap only bites a decision that needs the page map.**

<p><br/></p>

**2. The DATA-TABLE assets** (2026-08-04) are feature assets and **look gateable.** They are not: *"does this site embed a table"* cannot be answered cheaply or safely at `on_config`, because a `!!! data` block lives in the **BODY** of a page, not in the first 2000 bytes a frontmatter scan reads — **so the router's trick does not transfer.** The choice is between a whole-body scan of every page and ~24 KB that matches nothing and binds no listener. ⚑ **A check that can answer wrong is more expensive than the bytes**, which is the whole lesson of D2.

<p><br/></p>

**3. The PRINT layer** (2026-08-06) is unconditional for the simplest reason of the four: **there is no question to ask.** Every page can be printed, so a usage check would have no input and no answer. It is rules behind an `@media print` gate that cost a screen reader nothing.

<p><br/></p>

**4. The FLOW layer** (2026-08-19) is unconditional for reason 2, **not** reason 3. `chain:` and `forms:` **are** frontmatter keys, so unlike `!!! data` the router's scan trick genuinely **would** transfer — which makes this **the first asset group that was gateable and was left ungated on purpose.** Two honest reasons: a second cached scan is more code and one more thing that can answer wrong, and `flow.css` is `.dr-flow*` rules that match nothing at all on a site with no chains.

<p><br/></p>

⭐ **AND THE COST OF A WRONG ANSWER IS WORSE HERE THAN ANYWHERE ELSE IN THE FILE.** With `hide: footer` on program pages the flow strip is the **ONLY** navigation on the page, so a gate that answered False by mistake would ship an unstyled strip as a site's sole means of moving — **the exact failure Michael reported in words on 2026-08-19** (*"all this other foot matter"*), arrived at by a clever optimisation instead of a missing file.

<p><br/></p>

**5. The QR and ALIGN layers** are unconditional for reason 2 exactly: `!!! qr` is a BODY directive and `{.align-*}` is an inline class, so the frontmatter scan cannot see either. **Not a judgement call — there is no cheap question to ask.**

---

## D4 — THE CONTENT FINGERPRINT, AND THE BUG THAT BOUGHT IT

```
assets/base.a41f7c92.css
```

First eight hex of the file's own SHA-256, so the URL **changes when the bytes change** and stays identical when they do not.

<p><br/></p>

⭐ **Not a micro-optimisation.** A stable asset URL on GitHub Pages meant a browser kept the old stylesheet after a correct deploy, **and every symptom pointed at the build.** A fingerprint makes *"I published and do not see my change"* impossible for assets.

---

## D5 — `hand_written_css()` IS A DERIVED LIST BECAUSE FOUR MANIFESTS DIED FIRST

`docrender/tokenaudit.py` used to keep **its own hardcoded tuple** of stylesheet names, and its own docstring records that the tuple went stale **WITHIN TWO HOURS** when `nav.css` was split out of `base.css` — so the audit **under-reported silently**, which is the worst possible failure for a page whose whole job is to be trusted. That docstring's remedy was to cross-check it against `assets.py` whenever either changed: **a manifest with a reminder attached.**

<p><br/></p>

🔴 **This repo has killed three manifests for that defect** (`roster.json`, `registry.json`, `app-index.md`) **and then kept a fourth inside a function.** One list now, derived, in the file that has to be right or nothing ships at all.

<p><br/></p>

⭐ **AND THE WARNING IN `hand_written_css()` HAS FIRED THREE TIMES FOR REAL.** It said *"adding a fourth group and forgetting it here is precisely how the old hardcoded tuple went stale"* — **written before any fourth group existed.** `_FLOW_ASSETS` became the fourth on 2026-08-19, `_QR_ASSETS` the fifth on 08-21, `_ALIGN_ASSETS` the sixth on 08-29; **every time the line was read first and the group joined the walk in the SAME COMMIT.** ⚑ *A warning obeyed three times is worth more than any number of anecdotes about why it exists.*

<p><br/></p>

🪦 **THE GROUP COUNT IS NO LONGER WRITTEN IN THAT DOCSTRING.** It said *"there are FIVE of them as of 2026-08-21"* and had **already been edited twice**; `len()` of the concatenation is derivable and a number in prose is not. ⭐ **Removing it ends the vector rather than resetting the timer** — the same move that killed the fleet count in `brain-config`, and **the sixth group is what proved it needed making.**

<p><br/></p>

⭐ **AND THE `.css` FILTER IS WHAT MAKES A SPLIT FREE.** Files join these tuples in mixed pairs — navtree contributed one sheet and one script — and the sheet is picked up while the script is correctly ignored, **with no edit.** That is the whole reason it is a function and not another tuple.

---

## D6 🔴 THE 08-21 OMISSION: A SHEET ON DISK, ABSENT FROM THE TUPLE, DEAD FOR TWO DAYS

`_PRINT_ASSETS`'s header carried the sentence **"a file in `assets/` absent from these tuples is never published and does nothing,"** written about a deliberate tombstone.

<p><br/></p>

🔴 **THEN IT CAME TRUE BY ACCIDENT AND COST EVERY PRINTED PAGE.** `print-chrome.css` — 9,672 B, the chrome-off list and the corner stamp — was on disk and **ABSENT FROM THE TUPLE.** So it was never published and did nothing, and **the nav drawer, the table of contents and the site header printed on every sheet of every site since the six-way split**: the exact defect `print.css`'s opening paragraph was written to fix, **reintroduced by an omission rather than by a rule.**

<p><br/></p>

⭐ **THE TELL WAS SITTING IN TWO FILES THAT DISAGREED IN PROSE.** `print.css`'s header said *"THE PRINT GROUP IS SIX FILES AS OF 2026-08-19"* and listed `print-chrome.css` among them; the tuple held five and said so. **Neither number was derived from anything, so both were free to be wrong, and only one of them was.**

<p><br/></p>

🔴 **AND THE TOMBSTONE NOTE IS WHAT MADE IT INVISIBLE.** One file in `assets/` is unregistered **ON PURPOSE** (`print-scheme.css`) and one was unregistered **BY ACCIDENT**, and from the tuple **they are indistinguishable.** ⚑ *A deliberate absence and a mistake look identical in a list of what IS present.*

<p><br/></p>

⚠️ **`hand_written_css()` COMPOUNDED IT RATHER THAN CATCHING IT.** The token audit derives its scan list from these tuples, so an unregistered sheet is invisible to the audit as well — **no rule in `print-chrome.css` had ever been checked.** The derived list was doing its job perfectly and could not see the hole, because **it guards against a forgotten GROUP and this was a forgotten FILE.**

<p><br/></p>

🔴 **THE GAP IS STILL OPEN.** Nothing compares `assets/*.css` **on disk** against the tuples. A build reporting *"on disk, unregistered: print-scheme.css"* would have made this obvious on day one — **and the tombstone would be one expected line rather than cover for a real one.** ✅ Until it exists, **every sheet added is registered in the SAME PR as the sheet itself** (three times on 2026-08-29: `print-identity.css`, `print-ink.css`, `align.css`). **The 08-21 incident is the whole argument against a two-step.**

---

## D7 — THE PRINT GROUP: EIGHT FILES, EIGHT JOBS, ONE QUESTION EACH

| Sheet | Answers |
|---|---|
| `print.css` | **HOW WIDE IT RUNS** — `@page`, the column unrailing, `print-color-adjust`, code wrapping, the transparent ground |
| `print-chrome.css` | **WHAT APPEARS AT ALL** — the chrome-off list and the corner stamp's own box |
| `print-flow.css` | **WHERE IT BREAKS** — `break-*`, orphans/widows, `h1`–`h6`, tab labels, forced-open `<details>`, `thead` repetition, `{.new-page}` |
| `print-type.css` | **HOW BIG THE TYPE IS** — the dial, the ramp, weight, tracking, link decoration, the data table's size anchor |
| `print-space.css` | **HOW MUCH AIR IS BETWEEN THINGS** — block margins, list margins, justification, the tabbed set |
| `print-callout.css` | **WHAT THE BOX IS** — the rule and indent, the icon, the font-size anchor |
| `print-identity.css` | **WHOSE DOCUMENT IT IS** — the letterhead row: the declared logo mark, the two text weights |
| `print-ink.css` | **WHAT COLOUR IT IS** — body ink black on paper; `h1`–`h3` keep the theme's ink |

🔴 **`print-ink.css` IS THE ONE MEMBER THAT CONTRADICTS `print.css`'s FOUNDING RULE** — *"THIS FILE IS STRUCTURE, NOT COLOUR"* — which is why it carries a **ruling** in its header rather than an argument. Michael exempted ONE property on ONE medium (2026-08-29). 🚫 **Not a precedent for a second colour opinion in this group;** the next one needs its own ruling.

<p><br/></p>

⚠️ **THE JOB TABLE WAS ITSELF CORRECTED.** It once credited `print.css` with *"chrome off"* **after** that list had moved to `print-chrome.css`, and with a *"link policy"* it does not contain — `print.css` has **no link rule at all**, deliberately, because `base.css` declares link decoration unscoped to any medium and it reaches paper on its own. ⚑ *A summary of somebody else's file is a second claimant.*

<p><br/></p>

⭐ **EVERY ONE OF THESE SPLITS WAS FORCED BY THE SAME 22 KB CEILING**, and each seam was already written in the header of the file that split. ⚑ **A FILE AT ITS SIZE LIMIT IS USUALLY A FILE WITH A SEAM IN IT; trimming prose is what you do instead of finding the seam.** ⭐ `print-identity.css` and `print-ink.css` are the two members **not** forced by a split — both are new subjects — but every existing neighbour was inside ~330 B of the ceiling, **so the ceiling still decided WHERE they went.**

---

## D8 — THE FREE POSITIONS, SAID OUT LOUD SO NOBODY DEFENDS ONE LATER

Four groups have a position that is **genuinely not load-bearing**, and each says so on its own tuple. Recording it here because *"nobody knows whether this matters"* is how a harmless line becomes untouchable.

<p><br/></p>

- **`_FEATURE_ASSETS`, the CSS half.** `navtree.css` is `.dr-` classes overriding nothing of Material's, and the one Material class it touches deliberately **INHERITS** `nav.css`'s top-level caps rather than fighting it. It sits beside its own JS because that reads as one feature. 🔴 **The JS half is NOT free — see the ordering law in the module.**
- **`_FLOW_ASSETS`.** Every selector is a `.dr-flow*` / `.dr-form*` / `.dr-view*` class no other sheet mentions. It **consumes** `--dr-*` tokens rather than defining them, and custom-property resolution does not depend on parse order. ⚠️ It sits after the print group because it carries its own `@media print` block and reading it next to the other print rules is easier than hunting it — **legibility, not a law.**
- **`_QR_ASSETS`.** Every selector is a `.dr-qr*` class. 🚫 It declares **no** `--dr-*` token: a QR is black on white because scanners need luminance contrast, not because a palette says so, **which makes it the one sheet here that is deliberately un-themeable.** ⚠️ And its rules are **functional rather than cosmetic** — the mm size floor, the media gates and `print-color-adjust` all decide whether a camera can READ the code.
- **`_ALIGN_ASSETS`.** `.align-*` is matched by no other sheet, and the one selector it borrows (`.dr-qr__svg`) takes a `margin-inline` that `qr.css` never declares — **so there is no selector-and-property PAIR in either medium.**

<p><br/></p>

⭐ **WHY `_QR_ASSETS` AND `_ALIGN_ASSETS` ARE THEIR OWN GROUPS RATHER THAN PRINT MEMBERS.** Both carry **screen AND print rules as one feature.** `_PRINT_ASSETS` is entirely `@media print` and loads where it does for a cascade reason; a sheet with a screen half would make that group's own header a lie. ⚑ **A GROUP IS A CLAIM ABOUT WHEN A SHEET LOADS AND WHY. Adding a member that breaks the claim is worse than adding a group.** ⭐ And for align there is a second reason: a class that did nothing on screen would be **unverifiable before printing**, which is the scar `qr.py` already carries about print-only elements.

<p><br/></p>

⚠️ **`_ALIGN_ASSETS` is also the first sheet here whose feature has TWO authoring spellings**, which is a markup constraint rather than a choice: `attr_list` cannot decorate a `!!!` directive, so a QR takes `align=` and everything else takes the class. **Both files say so, so neither reads as arbitrary.**

---

## D9 🔴 THE PRINT GROUP'S INTERNAL ORDER IS FREE, WITH TWO PROVEN EXCEPTIONS

No two of the eight share a **selector-and-property PAIR** — `.md-typeset h1` is written in `print-type.css`, `print-space.css` **and** `print-ink.css`, but they set size/weight/tracking, margins, and **colour** respectively, and **a cascade fight needs both halves to match.** What is load-bearing is the **GROUP's** position, not the order inside it.

<p><br/></p>

🔴 **EXCEPTION 1, added the day it bit.** `print-space.css` §9 justifies `.md-typeset p`, which **MATCHES the corner buildstamp** and beat `print.css`'s `text-align: right` on **SPECIFICITY rather than order.** Fixed by narrowing §9. ⚑ **The order is still free; what is not free is assuming two of our own files cannot collide.** ⚠️ And that narrowing has still never been exercised on paper — the corner stamp it collides with was unpublished until PR #190. **Re-preview it.**

<p><br/></p>

🔴 **EXCEPTION 2, a landmine dodged rather than a bug fixed.** `print-identity.css` deliberately **does not touch** `.buildstamp--corner`. A `display: flex` there would have been a genuine pair against `print-chrome.css`'s `display: block` **on the same selector.** The layout was moved onto a net-new inner element (`.buildstamp__row`) specifically to avoid creating the group's first real collision.

<p><br/></p>

⚠️ **IF THAT EVER STOPS BEING TRUE, THIS SECTION IS THE THING THAT ROTS.** Three likely ways, named in advance: `print-type.css` growing a `margin` on a heading it already sizes (`print-space.css`'s header calls this the likeliest); `print-callout.css` and `print-flow.css` both reaching for `<details>` — **flow owns whether it is OPEN, callout owns what it LOOKS LIKE**; or `print-type.css` growing a `color` on a heading, **which is now `print-ink.css`'s property.**

---

## D10 — WHY A MISSING FILE IS SILENT, AND WHY THAT HID D6

`_read` returning `None` makes a missing file silent in `_plan`. ✅ **That is correct behaviour for a sheet somebody deleted on purpose.** 🔴 **And it is also why an UNREGISTERED sheet was undetectable: the loop can only skip what it was asked for.** See D6.

---

## D11 — EXPECTED NOISE IN THE TOKEN AUDIT, SO IT IS NOT RE-DISCOVERED AS A FINDING

The print sheets show up **loudly**, which is correct. `line-height`, `margin`, `padding` and `font-size` are all in `tokenaudit._METRIC_PROPS`, so every value `print-type.css`, `print-space.css` and `print-callout.css` set is a new row in the metrics section. `flow.css` does the same and more.

<p><br/></p>

🔴 **THREE FAMILIES OF ROW LOOK LIKE FINDINGS AND ARE NOT:**

1. `qr.css`'s `width: 30mm` and `print-identity.css`'s `40.5mm` / `8.46mm` / `4mm` carry **no token**, because **a physical mark on a physical sheet is not a design vector.**
2. `print-ink.css`'s `#000` is a hardcoded colour **BY RULING** (2026-08-29).
3. `align.css`'s `margin-inline: auto` is a **keyword**, not a metric.

<p><br/></p>

Each sheet's header carries its own argument. ✅ **The audit flagging them is the audit working.**

---

## D12 — THE SPLIT ITSELF (2026-08-30)

✅ **Mechanism kept, history moved, nothing deleted.** `assets.py` went **32,684 B → ~10 KB** and every function is byte-identical: the tuples, `hand_written_css()`, `_uses_router`, `_fingerprint`, `_stamped`, `_read`, `_plan`, `on_config`, `on_files`. **No behaviour change, and the split is verifiable as a pure move** — which is the only kind of extraction worth doing on a file that publishes every asset on every site.

<p><br/></p>

🔴 **THE ONE JUDGMENT CALL, STATED AS A RULE RATHER THAN LEFT AS TASTE.** History moved; **instructions did not.** Every load-order LAW is still inline beside its tuple, because ⚑ **a guardrail belongs where the hand is about to act.** This repo has recorded *"a rule that is correct in isolation and unreachable in place"* **five separate times** — `sizecheck` never walking `assets/`, the no-hash lock in a renderer the page stopped calling, `tr:not(:has(td.dr-detail))` against an emitter that always emits, the eyebrow welded to a TYPE, `:first-child` assuming an identifier. **Moving `navtree.js MUST COME BEFORE router.js` into a sidecar would have been the sixth**, and the failure mode is a dead sidebar on a working unlock, which is the quiet shape.

<p><br/></p>

⚠️ **What this split does NOT fix, so it is not read as closed:** the disk-vs-tuple check (D6) is **still missing.** The extraction makes the tuples editable again; it does not make an omission detectable. **That check remains the one guard this file has been asking for since 08-21.**
