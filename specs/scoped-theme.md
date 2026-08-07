# BUILD 3 — a theme that is not the whole site, and the report page that wants one

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-07. No code. Indexed from `next-build-spec.md`.

> Michael, 2026-08-07, immediately after being told a per-folder `theme:` does nothing:
> *"SPEC that other part — i want it as part of a larger (a publish report that actually renders in UTILITY anyways…). but only BUILD the publish theme variable."*

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

## 4. The scoped theme — three options, and only one survives contact

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

### 🚫 Option C: hardcode a single `report` scope, no general mechanism

Cheapest, and worth naming as the fallback. If the report page is the only thing
that ever needs a second theme, a general per-folder feature is a framework built
for one caller. ⚠️ **Take this if ruling 2 says the report is the only consumer.**
The honest test: name a SECOND page that should wear a different theme. If none
exists, build C.

---

## 5. The report page itself

**Generated, never authored.** Emitted by a hook via `File.generated`, same as
`doc-index.json`. It never exists in the content repo.

**It renders the SAME report object BUILD 2 renders**, from `state.REPORT`. ⭐
**ONE RENDERER, N DESTINATIONS — this is BUILD 2's central constraint and it now
has a third destination.** stdout, `GITHUB_STEP_SUMMARY`, and this page must be
the same string from the same function or they disagree within a month. That is
the strongest argument for doing BUILD 2 Piece C (the `report.py` split) FIRST:
this page is a caller of it.

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

---

## ⏳ Rulings needed (four)

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

1. BUILD 2 Piece C — `report.py`, a pure move.
2. BUILD 2 Piece A — annotations. Independent, ships value immediately.
3. This page, generated, unlisted, in the site's OWN theme. **Useful already**,
   and it proves the generation path before any theme work starts.
4. The scope (Option C, or B if ruling 2 says so) — **and `print.css` re-scoped
   in the same commit**, per §4c.

🚫 **Do not start at 4.** It is the interesting part and the only part that can
break a page nobody is looking at.

---

## Files and sizes (read back at HEAD 2026-08-07, not estimated)

| File | Now | Change |
| --- | --- | --- |
| `docrender/theme.py` | 12,474 B | `build_css()` and `_shared()` take a selector; the `:root` invariant dies. |
| `docrender/assets.py` | 12,731 B | small — one more generated file. |
| `assets/print.css` | — | ⚠️ **re-scoped, same commit as any scoped selector.** §4c. |
| **NEW** `docrender/report.py` | — | BUILD 2 Piece C owns this; this build calls it. |
| `docrender/instance.py` | **21,673 B** | 🔴 **PAST the 18KB warn line.** It absorbed `DOCRENDER_THEME` today. **Nothing else goes in this file** — a scope declaration reader is its own module. |
| `next-build-spec.md` | **22,660 B** | 🔴 **PAST the 22KB ceiling before this build adds anything**, which is why this spec is its own file. It needs splitting into `specs/` per build. |

⚠️ **Do not quote this table.** Two of these numbers moved today, and the last
time a size table in this repo was trusted it was 48 hours stale and had changed
an instruction rather than just a figure. Measure at the moment you act.
