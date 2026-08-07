# BUILD 3 — a theme that is not the whole site, and the report page that wants one

> ## ✅ RULED AND SHIPPED, IN PART — 2026-08-07
>
> **Michael: *"UTILITY is the folder."*** That is §1, the blocking ruling, and it
> went the way that **kills §4 entirely**. No scoped theme, no second stylesheet,
> no `print.css` re-scope, no death of the `:root` invariant, and Option B versus
> Option C never has to be settled.
>
> **What shipped instead, same day:** `docrender/report.py` (Piece C, the renderer
> split) and a `!!! report` block on an authored page in `01-utility/`.
>
> ⭐ **THE HEDGE IN §1 IS WHAT MADE THAT CHEAP, and it is the transferable result
> of this document.** §1 named both readings, said which one it had taken, and
> said exactly which section died under the other. **One word of ruling then
> deleted the expensive half with no discussion at all.** A spec that had quietly
> assumed the theme reading would have shipped a scoped-selector emitter, and a
> silent dark-mode print regression with it, to answer a question nobody asked.
>
> | Ruling | Answer |
> | --- | --- |
> | **1. Which UTILITY?** | **The FOLDER.** §4 is dead. |
> | **2. General mechanism or one scope?** | **Moot.** No scope exists to build. |
> | **3. Who may see it?** | **`status: unlisted`**, generated on every build. The preview-only half of the recommendation was dropped: the live site's report is the one worth reading. |
> | **4. Wait for BUILD 2 Piece C?** | **Yes, and it went first**, exactly as recommended. |
>
> ⚠️ **§5 IS SUPERSEDED IN ONE RESPECT AND IS MARKED RATHER THAN REWRITTEN.** The
> page is **AUTHORED** with a one-line directive, not `File.generated`. An
> authored page carries its own `status:`, takes its normal place behind the
> router, and can put prose around the block explaining how to read it — three
> things a generated file cannot do, and all three worth more than never touching
> the content repo. **§2's argument is still correct**; it simply stopped being
> the reason to prefer one shape over the other.
>
> 🔴 **AND THE ONE THING NEITHER §2 NOR §5 SAW:** the report is not FINISHED when
> the page renders. Every other `!!!` directive draws something already known;
> this one reads an accumulator that is still filling. Rendering at
> `on_page_markdown` emits a report missing every finding from every page not yet
> walked plus all of hook 08 — **and it looks correct.** The shipped design swaps
> the directive for an inert HTML comment and substitutes into the built file at
> `on_post_build`, one stage after 08. Full reasoning in `docrender/report.py`.

⚠️ **ORIGINALLY SCOPED, NOT GREENLIT.** 2026-08-07. Everything below this line is
the spec as written before the ruling, kept because §4's analysis is the record of
why a scoped theme is expensive — and the next person who wants one should read it
rather than rediscover it.

---

🔴 **READ THIS FIRST, BECAUSE THE WHOLE SPEC HANGS OFF ONE READING OF ONE SENTENCE.**
I have taken *"renders in UTILITY"* to mean **the `utility` THEME** — the skin
`theme/themes.tsv` describes as *"dense and low-chrome, for pages that are worked
from rather than read"* — and therefore to mean: **a build/publish report that
lives ON the site as a page, wearing a different theme from the site around it.**
That reading is what unifies the two halves of the sentence, and it is why a
scoped theme is worth specifying at all rather than being filed as a curiosity.

The other available reading is `01-utility/`, the content FOLDER on `uritp` that
already holds `automatic-revision-log.md`. Under that reading the report is just
a page in a known folder and **the scoped theme is not required at all** — §4
becomes optional and this document is half its size. ⚠️ **If that was the intent,
say so before anybody builds §4**, because §4 is the expensive half and it is the
half that only exists to serve the other reading.

✅ **AND IT WAS. See the banner. This paragraph did its job.**

---

## 1. What is actually being asked for

Two things that have been circling each other for three days, and they turn out
to be one thing:

| | The ask | Where it has been sitting |
| --- | --- | --- |
| **A** | The build report has a reader | `next-build-spec.md` BUILD 2, scoped 2026-08-06 |
| **B** | A theme that applies to part of a site | refused today, because the mechanism does not exist |

**B is only worth building because of A.** A report page is the first honest
reason this engine has ever had for two themes in one site: it is not a document,
it is an instrument, and it should not look like the venue paperwork around it.
Every previous request for a scoped theme was decoration. This one has a job.

⭐ **And A is only fully solved by B.** BUILD 2 ships the report into the Actions
run page, which is behind a login, three clicks deep, and gone when log retention
expires. A report that renders on the site is the version somebody actually
reads — which was BUILD 2's entire stated problem.

🔴 **THE SECOND HALF OF THAT IS WRONG AND THE RULING PROVED IT.** A is solved by
putting the report on the site. It is not solved *by B*: the page renders in the
site's own theme, and nothing about being an instrument rather than a document
turned out to need a different skin to say so. **A justification that survives
only while both halves are wanted is not a justification, it is a bundle.**

---

## 2. 🔴 THIS OVERTURNS A RULING FROM BUILD 2, AND THE OBJECTION WAS HALF RIGHT

BUILD 2's ruling 1 considered exactly this and rejected it:

> *"A published `/build-report/` page on the site. 🚫 Recommend against: it puts
> internal validation output on a public docs site, and the content-repo purity
> rule says the content tree holds documents, not machinery."*

**The purity half is WRONG, and I can show it rather than argue it.** The rule is
that the CONTENT TREE holds no machinery — it is a rule about what lives in the
content repo, so that its Download ZIP button hands over documents and nothing
else. A generated report page never enters the content repo. `assets.py` already
publishes five stylesheets and a script that exist in no `docs_dir` anywhere,
via `File.generated`, and `docindex.py` already publishes `/doc-index.json` the
same way. **A generated page is the same mechanism with a different MIME type.**
The content repo is untouched, its ZIP is unchanged, and the purity rule is not
engaged at all. That objection was aimed at committing a report INTO the docs
tree, which nobody proposed.

⚠️ **THE SHIPPED PAGE IS AUTHORED AND DOES ENTER THE CONTENT REPO — 3 KB of
frontmatter and prose, with the report itself still generated.** The argument
above is still sound; it just stopped being decisive once the page needed a
`status:`, a place behind the router, and a paragraph explaining how to read it.
**A rule about machinery is not a rule against a page that EXPLAINS machinery.**

⚠️ **The other half of the objection SURVIVES and is the real design problem.**
*Internal validation output on a public docs site* is a genuine cost: `uritp` is
a private repo with a public site, and a page reading *"dead_links: 4 —
production-dropbox.md declares data slot 'folders'"* is an invitation and an
embarrassment in equal measure. **That is the thing this build has to solve, and
§5 is where it gets solved.** Recording the split because a rejected option that
is later accepted must say WHICH of its reasons died.

---

## 3. What exists today, measured at HEAD

Read this session rather than recalled:

- `theme.build_css()` takes **no arguments**. It reads `state.INSTANCE` and
  emits one string.
- `assets._plan()` calls it once and appends the result to `config.extra_css`,
  which MkDocs links from **every page**. There is no per-page CSS mechanism.
- The emitted CSS uses exactly three selectors: `:root`, and
  `[data-md-color-scheme="slate"]` / `[data-md-color-scheme="default"]`, which
  Material writes on the **document**, not on a page element.
- The three scheme-independent vectors (typography, forms, spacing) are emitted
  **once, in `:root`,** from the primary scheme only.
- Inside each scheme block, **order is load-bearing and its failure mode is
  silence**: local `base` rows, then the canonical row, then the aliases. The
  bridge is last in `:root`. `theme.py`'s own docstring: *"put either anywhere
  else and the local value quietly survives while every file involved still
  looks correct."*

So "one build, one theme" is not a policy anybody chose. It is four separate
properties of the emitter, and a scoped theme has to change all four.

---

## 4. 🪦 THE SCOPED THEME — DEAD 2026-08-07, KEPT AS THE PRICE LIST

🚫 **NOT BUILT AND NOT TO BE BUILT WITHOUT A NEW ASK.** Ruling 1 removed the only
consumer. This section stays because it is the measured cost of a scoped theme in
this engine, and the next person who wants one should read it rather than
rediscover §4c the hard way.

### 🚫 Option A: a second stylesheet, linked only on scoped pages

Rejected on mechanism. `extra_css` is CONFIG-level, so MkDocs links it
everywhere; a per-page link needs `on_post_page` HTML surgery. That is a real
precedent in this repo (`navstate.py` edits rendered HTML deliberately, and
argued for it over forking a Material partial) — **but the cost here is
different.** A page that links a second full token sheet gets both sheets, and
which one wins is decided by source order across two files rather than by
anything either file states. That is the `print.css` trap (§4c) with no fixed
ordering to defend it.

### ✅ Option B: one stylesheet, N scoped blocks, one attribute on the body

Emit an extra pair of scheme blocks per declared scope, selected by a data
attribute the engine writes onto the page:

```
body[data-dr-theme="utility"][data-md-color-scheme="slate"]  { … }
body[data-dr-theme="utility"][data-md-color-scheme="default"] { … }
```

Material already writes `data-md-color-scheme` on `<body>`, so both attributes
land on one element and combine naturally. One stylesheet, one fingerprint, no
cross-file ordering, and a page with no attribute is byte-for-byte unaffected.

**What it costs, stated honestly:**

1. **The `:root` vectors stop being `:root`.** Typography, forms and spacing are
   currently emitted once, globally. A scope that changes typography needs them
   re-emitted under the scoped selector — so `_shared()` grows a selector
   argument and the "emitted ONCE" invariant in its docstring dies. That is the
   deep change in this build, not the colour blocks.
2. **Every scope multiplies by two schemes**, and the alias + bridge ordering
   must hold inside each block independently. Silence is the failure mode, so
   the emitter needs a test that walks each block and asserts the aliases are
   last — not an eyeball.
3. **Stylesheet size grows roughly linearly per scope.** Two scopes is fine. This
   is not a feature that should ever accept ten.

### 🔴 4c. AND HERE IS THE ONE THAT WOULD HAVE SHIPPED BROKEN

**A two-attribute scoped block OUTRANKS `print.css`, and dark-mode printing dies
silently on every scoped page.**

`print.css` re-points custom properties on `[data-md-color-scheme="slate"]` so a
reader in dark mode gets black ink on white paper. `assets.py` puts it AFTER the
generated sheets for exactly this reason, and its comment says why: the two write
the same selector **at the same specificity**, so the winner is decided purely by
source order. A scoped block with two attribute selectors is a HIGHER
specificity, so source order stops mattering and the scoped theme wins — and the
symptom is *"a dark-mode print comes out as pale grey ink on a background the
browser drops. No error, no report, just a near-blank sheet."*

⚑ **This is the `data-md-color-primary` incident, one file over.** That one also
was a two-attribute Material selector outranking a one-attribute scope, also only
in dark mode, also invisible for weeks. **Any build that adds a scoped selector
must re-scope `print.css` to match, in the same commit.** Written down here
because it is not discoverable from either file alone: `print.css` says it relies
on source order, and the scoped emitter would have no reason to read it.

⭐ **THIS PARAGRAPH IS THE REASON §4 WAS WORTH WRITING EVEN THOUGH IT DIED.** The
regression it names is invisible, only in dark mode, only on paper, and would have
been found weeks later by somebody printing a call sheet.

### 🚫 Option C: hardcode a single `report` scope, no general mechanism

Cheapest, and worth naming as the fallback. If the report page is the only thing
that ever needs a second theme, a general per-folder feature is a framework built
for one caller. ⚠️ **Take this if ruling 2 says the report is the only consumer.**
The honest test: name a SECOND page that should wear a different theme. If none
exists, build C.

✅ **The test was never run, because ruling 1 removed the FIRST consumer.**

---

## 5. The report page itself

⚠️ **SHIPPED WITH ONE CHANGE — see the banner. The page is AUTHORED**
(`01-utility/build-report.md`, carrying a `!!! report` block) rather than
generated. Everything else below held.

~~**Generated, never authored.** Emitted by a hook via `File.generated`, same as
`doc-index.json`. It never exists in the content repo.~~

**It renders the SAME report object BUILD 2 renders**, from `state.REPORT`. ⭐
**ONE RENDERER, N DESTINATIONS — this is BUILD 2's central constraint and it now
has a third destination.** stdout, `GITHUB_STEP_SUMMARY`, and this page must be
the same string from the same function or they disagree within a month. That is
the strongest argument for doing BUILD 2 Piece C (the `report.py` split) FIRST:
this page is a caller of it.

✅ **Piece C shipped first. `report.sections()` is the one walk; `as_text()` and
`as_html()` are two callers of it and neither iterates the label dict itself.**

**Visibility — the surviving half of §2's objection.** Options, in the order I
would take them:

1. **`status: unlisted` equivalent.** Built, has no sidebar row, findable only by
   URL. Cheapest, and honest: it is not a secret, it is not advertised.
2. **Behind the router.** The mechanism exists and is exactly "withhold the shape
   of a section from anyone without a code." ⚠️ Costs a code to read your own
   build report, on a phone, which is the moment you least want one.
3. **Preview builds only** (`DOCRENDER_DRY_RUN`). Strong: a preview is where you
   look before publishing, and the page never reaches the live site at all.
   ⚠️ And it means the live site's report is never readable, which is where the
   two 2026-08-06 defects were sitting.

**Recommend 1 + 3 together:** always generated, unlisted on a publish, and named
in the run summary on a preview. Ruling 3.

✅ **1 taken. 3 dropped**, on its own stated objection: the live site's report is
the one that matters, and a page that only exists in previews is a page nobody
ever lands on. ⭐ **And 2 came free** — `01-utility/` is already a routed folder,
so the page sits behind the curtain whether or not it is listed.

---

## ⏳ Rulings needed (four) — ✅ ALL FOUR ANSWERED, see the banner

**1. Which "UTILITY"?** The theme, or `01-utility/` the folder? The whole of §4
exists only under the first reading. **This is the blocking one.**

**2. General mechanism, or one hardcoded scope?** Option B or Option C. The test
is whether a second consumer exists. **Recommend C until somebody names one** — a
general scoped-theme feature is a large change to the theme spine, and the spine's
whole promise is *"a theme is one pointer and zero CSS edits."*

**3. Who may see the report page?** §5. **Recommend unlisted + generated always.**

**4. Does this wait for BUILD 2?** **Recommend YES, and specifically for Piece C.**
This page is a second caller of a renderer that currently lives inside
`sizecheck.py` as job 3. Building the page first means writing its renderer
twice, which is the defect both specs already exist to prevent.

---

## Sequence, if it is greenlit

1. ✅ BUILD 2 Piece C — `report.py`, a pure move.
2. ⏳ BUILD 2 Piece A — annotations. Independent, ships value immediately. **Still
   open, and now cheaper: it is a third caller of `report.sections()`.**
3. ✅ This page, generated, unlisted, in the site's OWN theme. **Useful already**,
   and it proves the generation path before any theme work starts.
4. 🪦 The scope (Option C, or B if ruling 2 says so) — **and `print.css` re-scoped
   in the same commit**, per §4c. **Dead: ruling 1.**

🚫 **Do not start at 4.** It is the interesting part and the only part that can
break a page nobody is looking at.

⭐ **Nobody did, and step 3 needed nothing from step 4 — which is the ruling,
restated as a result.**

---

## Files and sizes (read back at HEAD 2026-08-07, not estimated)

| File | Now | Change |
| --- | --- | --- |
| ~~`docrender/theme.py`~~ | 12,474 B | 🪦 **Untouched. §4 is dead.** |
| ~~`docrender/assets.py`~~ | 12,731 B | 🪦 **Untouched.** No generated page. |
| ~~`assets/print.css`~~ | — | 🪦 **Untouched, and that is the win** — no scoped selector, so §4c never fires. |
| ✅ **NEW** `docrender/report.py` | 15,715 B | Piece C plus the page. Under the 18KB warn line. |
| ✅ `docrender/sizecheck.py` | 15,233 → 12,481 B | Two scans and a print. Back under its own warn line with room. |
| ✅ **NEW** `hooks/08b_report.py` | 1,820 B | Shim. Must sit after 08. |
| ✅ `mkdocs.yml` | 9,099 → 10,137 B | One registration, one chain note. |
| ✅ `docrender/state.py` | 13,903 → 14,855 B | The two-edits warning repointed at report.py. |
| `docrender/instance.py` | **21,673 B** | 🔴 **PAST the 18KB warn line.** It absorbed `DOCRENDER_THEME` today. **Nothing else goes in this file.** Untouched by this build. |
| `next-build-spec.md` | **22,660 B** | 🔴 **PAST the 22KB ceiling**, which is why this spec is its own file. Still needs splitting per build. |
| 🚩 `README.md` | **25,119 B** | 🔴 **OVER THE HARD LIMIT AND THEREFORE NOT EDITED.** `!!! report` is undocumented there. Not written from a truncated read — see the flag below. |

⚠️ **Do not quote this table.** Two of these numbers moved today, and the last
time a size table in this repo was trusted it was 48 hours stale and had changed
an instruction rather than just a figure. Measure at the moment you act.

---

## 🚩 Flagged, not fixed

**`README.md` does not document `!!! report`, and it was not edited on purpose.**
At 25,119 B it is over the 22KB hard limit, so it cannot be read back whole — and
this repo's standing rule is that a file which cannot be read whole cannot be
safely rewritten. Reconstructing the unread remainder from inference is the exact
failure that rule exists to prevent. **The README needs splitting before it can
accept another section**, and that is a separate build.

The directive is fully documented in `docrender/report.py`'s module docstring
meanwhile, which is where a reader of the code will look. It is the reader of the
README who is currently unserved.
