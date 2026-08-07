# doc-render-engine

The renderer for a family of documentation sites. One app, many instances.

**Status:** v1. Builds. Deployment needs the manual setup in §6.
**Instances:** `template` (live gold standard). Others are added deliberately.

---

## 1. The idea in one paragraph

A content repo holds markdown and nothing else, so its green **Download ZIP**
button hands you exactly the documents and no machinery. Everything that turns
those documents into a website lives here instead: hooks, object schema, theme
tables, and one small config file per site under `instances/`. The engine is
instantiated once per site, each instance points at a different content repo,
and every site gets the same behaviour without anybody copying code.

That button is not a footnote. It is the requirement the whole architecture was
reverse-engineered from.

---

## 2. Repo shape

```
mkdocs.yml              base config. Almost no identity in it, deliberately.
pyproject.toml          the engine is a real installable package.
requirements.txt        pinned build deps, and notes on what is NOT here.

docrender/              THE APP. Knows nothing about any particular site.
  state.py              one shared namespace per build.
  util.py               frontmatter + table parsing. No mkdocs import.
  instance.py           stage 00: become this site. Nav ordering. Also the
                        DOCRENDER_THEME override -- see §4a.
  visibility.py         stage 00b/00bc/02: the publication gate, and the
                        router nav-seal. TWO on_nav stages, split on purpose.
  navstate.py           stage 00bb/06b: what a FOLDER does in the sidebar.
  objects.py            stage 01: validate frontmatter, draw the type.
  links.py              stage 03: @id and @peer:id resolution.
  theme.py              stage 04: tokens from TSV to CSS properties.
  assets.py             stage 05: publish files from OUTSIDE the doc tree.
  pagefoot.py           stage 06: the edit link.
  buildstamp.py         stage 07: is this page the latest push?
  sizecheck.py          stage 08: size budget, LEAK SCAN, build report.
  docindex.py           stage 09: /doc-index.json, the cross-site contract.

hooks/NN_*.py           thin shims. They hold the ORDER; the package holds the
                        logic. The order is load-bearing, see hooks/README.md.
                        The five on_nav stages are a chain: 00, 00b, 00bb,
                        00bc, 00c. That file says what each misordering breaks.

objects/*.yml           WHAT A KIND OF PAGE IS. The schema layer.
theme/*.tsv             WHAT IT LOOKS LIKE. Data, not code.
assets/base.css         the shared style layer.

instances/<slug>/
  site.yml              WHICH SITE. Name, URL, content repo, palette, sections.
  theme.css             that site's own look. Loaded last, has the final word.
  xref-cache.json       last known good peer indexes. COMMITTED on purpose.

.github/workflows/
  build.yml             THE APP MATRIX. Every site, rendered and deployed.
                        Runs on push, on dispatch, and when poll.yml calls it.
  poll.yml              THE ROUTINE. One cron, calls build.yml, nothing else.
                        Disabling this workflow IS the off switch — see §6c.
  publish.yml           THE PUBLISH BUTTON. One site, on purpose, with a
                        preview mode and an optional one-build theme (§4a).
                        Never gated by anything.
  publish-default.yml   the template site, onto THIS repo's own Pages.
```

---

## 3. The frontmatter contract

The only interface between a content repo and this engine. A page declares
itself; the renderer obeys.

```markdown
---
id: main-stage          # IDENTITY. Permanent. Set once, never change.
title: Main Stage       # what humans see
type: space             # picks the rules in objects/space.yml
status: public          # hidden | unlisted | gated | public
parent: example-house   # an id, never a path
order: 10               # sidebar weight. Absent sorts alphabetically.
revised: 2026-08
---
```

`id`, `title` and `status` are required on every page. **A page with no status
does not build**, which is how nothing reaches the public web because someone
forgot a line.

🚫 **There is no `theme:` key, and there never has been.** `theme/themes.tsv`
claimed one until 2026-08-07; see §4a.

### `nav:` — what a FOLDER does in the sidebar *(2026-08-05)*

Declared on an `index.md` and **nowhere else**. A `nav:` on a leaf page is
ignored and reported. Each value has a bare-verb alias; they are identical.

| value | alias | the sidebar |
| --- | --- | --- |
| `collapsed` | `collapse` | a closed row you click to open |
| `expanded` | `expand` | opens by itself, and so does everything under it |
| `hidden` | `hide` | the folder keeps its own row and loses its children |
| *(absent)* | | **inherit** — see below. This is the normal case. |

**Absence is the normal case, so inheritance is the rule that matters.** A
folder with no `nav:` takes the value of the nearest ancestor index that has
one, and failing that the value on the **site root `index.md`**. There is no
per-folder default to remember.

**The site root declares the default for the whole site.** `nav: collapsed`
there is the sane setting and the one to write; `nav: expanded` is the one-line
flip that opens every folder which does not shut itself. Nothing in the engine
overrides it — the fallback constant in `navstate.py` only applies to a site
that has not answered, and that build says so in the report.

**`expanded` cascades; a descendant index overrides it.** Root `expanded` with
a subfolder `collapsed` means the tree opens down to that subfolder and stops —
which is the whole reason the key has three values rather than being a boolean.
🚫 `hidden` does **not** cascade, and does not need to: the subtree leaves the
sidebar in one cut, so there is nothing underneath for a value to reach.

🚫 **`nav: hidden` is refused on the site root** and reported. Inherited by
every top-level folder it empties the entire sidebar and leaves a row of
labels. Put it on the folders you meant.

**The branch you are IN is always open, whatever it says.** That is not a rule
the engine implements; it is Material's own behaviour, and `navstate.py` is
built to never remove it. Consequence worth knowing: `collapsed` on a folder you
are standing inside does nothing, and `hidden` is the value that empties a
sidebar you are looking at.

🚫 **`hidden` is a curtain, not a lock.** The pages are still built, still have
live URLs, still resolve by `@id`, and are still in search. `status:` is the
feature that controls what reaches the site; this one controls what a reader is
OFFERED. `courses/course-info/` on `uritp` is the reference case: 43 course
pages that belong in a table on the index, not in a drawer.

Every build prints the resolved site default in its own report section, along
with anything it refused. A site whose root declares nothing is named there too.

#### `nav:` inside a ROUTED folder *(the seam, added 2026-08-05)*

A `router:` on a folder index also seals that folder's subtree out of the
sidebar until a code is typed (§7). Both features remove children from a
sidebar, so what happens when they land on the same branch had to be decided.

**`nav: hidden` wins, and it wins by running FIRST.** Stage `00bb` cuts hidden
folders; stage `00bc` seals what is left. So a hidden folder inside a routed
parent is gone before the seal sees it, and **a correct code cannot bring it
back** — which is the point. *Never offered* is a stronger claim than *offered
to whoever has the code*, and the stronger claim should not be quietly weakened
by a feature on a page above it.

⚠️ **A routed folder whose OWN index says `nav: hidden` seals nothing**, and the
build report says so by name rather than leaving "router declared, no manifest"
as a silent surprise. The body curtain on that page still works normally.

**They are not alternatives.** `nav: hidden` takes a subtree away from
everybody; a router takes it away from everybody *without a code*. Reach for the
first when the pages belong somewhere else on the page (a table, a catalog), and
the second when the shape of the section is the thing being withheld.

---

## 4. Adding a site

1. Create the content repo, **under the same account as this one** (§6a says
   why that is not a style preference). Markdown only.
2. `cp -r instances/template instances/<slug>` and edit `site.yml`.
3. Add one row to the matrix in `.github/workflows/build.yml`.
4. **Add the new repo to the `DOCRENDER_TOKEN` PAT's repository list.** Easy to
   forget, and the failure is a 403 at the very last step of an otherwise green
   build. ⚠️ **If the content repo is PRIVATE the same omission fails much
   earlier and much less legibly** — `exit code 128` on the checkout, which
   reads as a broken build rather than a missing checkbox. See §6c.
5. Enable Pages on the content repo: **deploy from branch → `gh-pages`**.
6. Add it to the dropdown in `publish.yml`, or it builds and cannot be
   published by hand. (`hml` shipped that way on 2026-08-03.)
7. Write `nav: collapsed` on the new repo's root `index.md`. The build works
   without it and reports that nobody chose the sidebar default. See §3.

That this is seven steps rather than a fork is the point.

**Pin by tag, never by branch, once other sites are consuming this repo.** The
reason these are separate repos is that they fail separately; a floating
reference re-couples them and one bad engine commit breaks every site at once.
Run the lowest-stakes site as the canary on the moving tag and pin the rest.

### 4a. Publishing in a different theme, once *(2026-08-07)*

A site's theme is one line in its `site.yml`. **Publish a site** takes an
optional **theme** box that overrides that line for a single build.

| you type | what happens |
| --- | --- |
| *(nothing)* | byte for byte the build it would have been. The passive default, and it is load-bearing: a box nobody filled in must never be why a site looks different. |
| a theme name | that theme renders, this run only |
| `random` | the engine rolls one from every legal name and says which |

**Nothing is written to disk.** `site.yml` is not edited, so an override cannot
outlive the run that asked for it and there is no cleanup step to forget —
publishing again with an empty box puts the site back.

**A name that is not real is DISCARDED, not substituted.** The site's own theme
renders and the report lists the legal names. That differs on purpose from a bad
theme committed to `site.yml`, which falls back to `base`: a typo in a tracked
file should still render a readable site, but an override was typed thirty
seconds ago by somebody watching the run, and answering it with a THIRD theme
would send them hunting a palette bug.

**Read the notice at the top of the run, not the title.** GitHub evaluates
`run-name` before the job starts, so a random publish is titled `theme: random`
and cannot name the roll. The engine emits one `::notice::` naming the theme it
actually used — that is the line to read, and it is the only one that answers
`random`.

⚠️ **A re-run re-applies the theme**, because dispatch inputs are part of the
run being replayed. The title says so.

Under the hood it is `DOCRENDER_THEME`, applied in `instance.py` at hook 00 —
the only stage that runs exactly once per build, which a value allowed to be
random requires. `theme.build_css()` runs two or three times, and rolling there
would give the two colour schemes different themes AND break the generated
stylesheet's content fingerprint. The docstring has the whole argument.

🚫 **It is the WHOLE SITE, for ONE build. There is no per-page or per-folder
theme, and `theme/themes.tsv` claimed there was until 2026-08-07.** Nothing ever
read that key: `build_css()` takes no arguments, its output is linked as a
single site-wide `tokens.css`, and its selectors are `:root` plus the two
document-level scheme attributes. A scoped theme is a change to the theme spine
rather than a variable read — scoped, not greenlit, as `next-build-spec.md`
BUILD 3.

---

## 5. Rules this engine enforces on itself

- **No site name in the engine.** `sizecheck.py` scans for the active
  instance's proper nouns and **fails the build** if it finds one. It is the
  only hard failure in the pipeline, because a portable engine otherwise stops
  being portable silently.
- **22KB per source file**, 18KB warn. A file that cannot be read whole cannot
  be safely edited.
- **Warn, never die**, for everything else. v1 built with `--strict` and one
  typo froze the entire live site twice in forty minutes while Pages kept
  serving a stale commit. Broken things render as visible markers and appear in
  the report; the deploy continues.

---

## 6. Setup that a human has to do

None of this can be done from inside a workflow.

### a. The `DOCRENDER_TOKEN` secret, on THIS repo

A fine-grained PAT with **Contents: Read and write**. It goes on the engine,
not on a content repo, because **the secret belongs where the workflow runs** —
and every workflow in this family runs here. A content repo holds no workflow
at all; that is the purity rule.

⚠️ **A fine-grained PAT is scoped to ONE resource owner**, which is why every
repo in this family has to live under the same account. A split namespace is
not untidy, it is unbuildable: no single token can both read the engine and
write the site.

⚠️ **A repo TRANSFERRED into the account after the token was created is NOT
added to it automatically.** The token's repository list is a fixed set chosen
at creation. The build then goes green all the way through rendering and dies
with a 403 on the final push, which reads like a broken deploy rather than a
missing checkbox. Check the list at
[Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens?type=beta)
and add the repo.

### b. Pages on each content repo

**Settings → Pages → Deploy from a branch → `gh-pages` / `(root)`.**

Order matters: the first successful build CREATES that branch, so the setting
cannot be flipped until after the first run. Run the workflow, set Pages, run
it once more.

### c. Turning the routine on and off *(2026-08-04)*

**`poll.yml` is the routine: one cron, calls `build.yml`, nothing else.**
It is its own file for exactly one reason — GitHub can disable a **workflow**,
but not a single **trigger** of a workflow that also handles pushes.

**Actions → "Publish automatically (the routine)" → ⋯ → Disable workflow.**
Back on from the same menu. Works on a phone.

| state | what happens |
| --- | --- |
| enabled | every 20 minutes, every site renders and deploys |
| disabled | no routine at all — publish by hand with **Publish a site** |

⚠️ **The interval moved 5 → 20 minutes in PR #77** and this table said 5 until
2026-08-05. `poll.yml` states the live value in the cron AND in the job name,
which is the copy the Actions tab prints; this table is a third home for it and
is the one that rotted. If they ever disagree again, the workflow file wins.

**The state is legible, and that is why this beat a variable.** A disabled
workflow greys out in the sidebar and carries a banner saying it was disabled
manually, on the same screen you re-enable it from.

🪦 **It replaced an `AUTOPUBLISH` repository variable that lived for one
commit.** That variable gated a schedule which still fired, so `off` meant *a
routine that declines* — ~288 skipped rows a day burying the real ones — and
the live state could only be read by opening Settings. Michael: *"either
auto-publish on a routine, or don't publish at all… I don't think we should
have an 'on routine' and an 'off routine'."* ⚑ **When a toggle and the platform
disagree about where state lives, the platform wins.**

⚠️ **The `theme` input in §4a is not a counter-example to that rule.** It is not
a TOGGLE and it holds no state: it is an argument to one run, it is recorded in
that run's title and deploy commit, and it is forgotten the moment the run ends.
The `AUTOPUBLISH` failure was a variable that persisted a mode nobody could see.

🚫 **Disabling the routine does NOT touch:** `publish.yml` (off must never mean
*I cannot publish*), a push to this repo (still renders every site as the
regression check, still deploys), or `publish-default.yml` — which carries its
own separate nightly cron for the template site. ⚠️ **That is a second routine
this switch does not reach**, flagged rather than folded in, because the
template is the engine's own live gold standard and freezing it is a different
decision.

**Changing the interval** is one line in `poll.yml`. It deliberately does not
live in a variable; that would put the routine's shape in two places again.

---

## 7. Known limits, stated rather than discovered later

- **`status: gated` is NOT implemented.** A page declaring it is published as
  `unlisted` with a loud warning. Shipping a gate that looks like access
  control but is not is worse than shipping none, because people put things
  behind it. See `docrender/visibility.py`.
- **A theme is a property of the SITE, not of a page or a folder.** One build
  emits one stylesheet, linked from every page, scoped to `:root` and the two
  document-level scheme attributes. §4a's override changes which theme, never
  how many. ~~`theme/themes.tsv`: "a page or folder can override with `theme:`
  in frontmatter"~~ — **struck 2026-08-07, never true, nothing ever read that
  key.** Recorded rather than deleted because it was read as a feature and
  planned against, which is what a promised extension point costs.
- **One `nav: expanded` anywhere turns `navigation.prune` off for the whole
  site.** Not a bug and not negotiable: a pruned nav renders no children for
  any section the reader is not already inside, so expanding one would open an
  empty box. `navstate.py` drops the feature at build time rather than ship a
  control that silently does nothing, and the build report says so. The price
  is every page carrying the full nav tree — Material's own figure is ~33% of
  page weight. `nav: hidden` is the discount. A site that never writes
  `expanded` never pays either.
  - ⚠️ **It is not available per-subtree, and that is the first thing anybody
    asks.** `navigation.prune` is one boolean for the entire theme. There is no
    form of it that trims some branches and not others, so keeping it on while
    honouring one `expanded` folder is not a cheaper version of this — it is
    the dead control the drop exists to prevent.
  - ⭐ **And turning pruning off does not EXPAND anything.** It stops the DOM
    being trimmed. No folder opens that would not have opened anyway, and a
    root `nav: collapsed` with pruning off still renders a fully collapsed
    sidebar. Written down because the opposite was said out loud once in
    conversation, and a wrong intuition about a cost is how a working feature
    gets reverted by somebody reading this section six weeks from now.
- **The nav stages have to run in order, and one misordering is invisible.**
  `00b` prune → `00bb` `nav:` → `00bc` router seal → `00c` prev/next. Put the
  seal before `nav:` and a hidden folder inside a routed folder gets sealed with
  its children still in it, so a correct code reveals pages that were supposed
  to be out of the sidebar for everybody — **with no error, no warning, and a
  site that looks correct to anybody without the code.** Two things defend it:
  the filenames (see `hooks/README.md`) and a runtime check in
  `visibility.seal_nav` that reports if the `hooks:` list ever drifts. Live bug,
  2026-08-05, five hours, 43 pages.
- **Cross-site links resolve at BUILD time.** If a peer renames a page, links
  to it are wrong until the next build. ~~The nightly cron closes that to a
  day~~ — the poll closes it to the interval in §6c, *while the routine is
  enabled. With it disabled the window is however long you sandbox for, which
  is a trade you are making on purpose.*
- **A Pages site is public even from a private repo.** Privately published
  Pages requires GitHub Enterprise Cloud. ⭐ **As of 2026-08-04 that is the
  architecture rather than a caveat:** `uritp-docs` is PRIVATE and its site is
  PUBLIC, which is the whole point — swapping `github.io` for `github.com` on
  a served URL now 404s instead of handing over the source tree, while readers
  need no account. Publication states still control what reaches the SITE,
  never what is readable in the repo. ⚠️ **Files the renderer copies verbatim
  are still public**, and a TSV a download link points at is the live example.
- ~~**Content repos cannot trigger their own rebuild**, because they hold no
  workflow. That is the cost of purity and it is paid on purpose.~~
  **CORRECTED 2026-08-04:** `uritp-docs` holds one workflow by explicit
  exception (its revision-log TSV), so it *could* fire the `content-changed`
  dispatch. It deliberately does not — the exception was granted for one job
  and does not license a second. The poll covers it. Recorded rather than
  rewritten, because "impossible" and "chosen against" are different arguments
  and only one of them survives a new workflow.
- **A scheduled run is a hint, not a clock.** GitHub queues them under load,
  drifts 5–20 minutes, and drops them outright during heavy periods. It also
  **auto-disables a schedule after 60 days of repo inactivity** — by putting
  the workflow into the same state the off switch uses, so a routine that
  stopped for no reason you remember is the first thing to check.

---

*v1, 2026-08-03. Built from the v1 sandbox at `maw-agents/uritp-docs`, which
proved the mechanics and is the reason several decisions here are phrased as
reversals.*
