---
id: publish-workflow-dl
title: publish.yml — reasoning
type: reference
status: draft
summary: Why publish.yml is the way it is. Struck reasoning kept, not deleted.
---

# publish.yml — reasoning

**This file holds the WHY. `publish.yml` holds the mechanism.**

The workflow reached ~39KB against about 40 lines of actual steps. A file that
cannot be read whole is a file that cannot be edited safely, and the steps were
never what needed explaining — the traps were. Struck reasoning stays struck
rather than deleted, because a silently-rewritten comment teaches nobody why it
rotted.

⚠️ **Formatting fixed 2026-08-08:** every line in this file was still carrying its
`#` comment prefix from the cut, which in markdown renders each one as a heading.
Content unchanged; prefixes removed.

---

## It has a terminal front door (2026-08-07)

`bin/publish.sh`, sourced into a shell, giving `publish uritp theme:eos`. It
dispatches THIS workflow with these inputs and invents no vocabulary of its own.
See the site-list section for the one thing it has to do that the web form does
not.

## 🪦 STRUCK 2026-08-05 — this file's central claim, false at HEAD

It was quoted to Michael as fact.

> ~~"publish.yml is the editorial act … it is a decision rather than a side effect.
> WHY IT IS NOT AUTOMATIC ON CONTENT PUSH: publishing is an editorial decision, an
> unfinished page can sit in `main` for a week without a reader ever seeing it, and
> going live is something somebody chooses."~~

Read `build.yml`. It fires `on: push [main]` and its deploy step runs for every row
with `publisher: matrix` — uritp, theatre and hml. **Every engine push republishes
all three.** Publishing is already a side effect of an engine commit and has been
for as long as that trigger has existed.

The ARGUMENT for a manual publish is still good. It is simply not a description of
this pipeline. Anybody who wants publishing to actually BE an editorial act has to
change `build.yml`'s trigger — not read a comment and feel reassured.

**What this workflow is still for, unambiguously:** publishing ONE site NOW,
without waiting for or making an engine commit, with a preview mode and a stated
reason. That justifies it on its own.

And the old second half of that argument was already dead (2026-08-04). It read
~~"a content repo holds no workflow — that is the purity rule — so it CANNOT publish
itself."~~ `uritp-docs` now holds exactly one workflow, by Michael's explicit
exception, regenerating its revision-log TSV on every doc commit. So auto-publish
became POSSIBLE the day that stopped being a fact. **"Impossible" and "chosen
against" are different arguments — and neither is true now.**

**Preview mode** renders the site, diffs it against what is actually being served,
prints new / disappearing / renamed pages to the run summary, and deploys NOTHING.
Run it before every publish.

## The `note` input — a publish can carry a why (2026-08-05)

Optional free text. Michael asked whether a publish could carry a comment and
whether that was even a field. It was not, and a bare input would have been a thin
answer: GitHub keeps dispatch inputs in the event payload and displays them nowhere
a person actually looks. **The note is surfaced in THREE places, and the surfaces
are the feature:**

| Surface | Why |
|---|---|
| `run-name` | the note becomes the RUN TITLE in the Actions list — the only surface anybody scans. Nine runs all called "Publish a site" is not a log |
| `commit_message` | rides into the gh-pages deploy commit, so it outlives Actions log retention in the CONTENT repo's own history. **This is the copy that lasts** |
| step summary | stated on the run itself, beside the engine SHA |

**It must stay optional.** `required: true` turns every publish into a form, and the
entire value of the terminal path is that a publish is one word. An empty note
reproduces the old behaviour byte for byte.

## The `theme` input — a publish may choose the look, for one build (2026-08-07)

Michael: *"what would it take for our publish command to accept an additional
variable that lets me set the theme at the last minute… I want to be able to push
publishes with random themes just to debug better."*

Optional free text, same contract as `note`. It reaches the engine as
`DOCRENDER_THEME` and is applied in `docrender/instance.py:_theme_override` — hook
00, the only stage that runs exactly ONCE per build.

| Value | Behaviour |
|---|---|
| *(empty)* | byte for byte the build it would have been. **The default must stay passive:** an input nobody filled in can never be why a site suddenly looks different |
| a theme name | renders for this run only. `site.yml` is NOT edited, NOTHING is written to disk, so the override cannot outlive the run and there is no cleanup to forget |
| `random` | the engine rolls one from every legal name and says which |

🔴 **A bad name is DISCARDED, not substituted**, and that differs on purpose from a
bad theme in `site.yml` (which falls back to `base`). A committed typo should still
render a readable site; an override was typed thirty seconds ago by somebody
watching this run, so answering with a THIRD theme — neither what was typed nor
what the site declares — would send them hunting a palette bug. The declared theme
renders and the report names the legal set.

⚠️ **Why it is `string` and not `choice`**, which is the obvious ask. The legal set
is the UNION of maw-themes' `themes.json`, the canonical colour table and this
engine's local `themes.tsv` — three files, one in another repo, resolved live at
build time. A hardcoded dropdown would be a fourth copy of that union, wrong the
first time anybody adds a palette upstream, and wrong in the direction that REFUSES
a legal name. `bin/publish.sh` declines to pre-validate for the same reason.

⚠️ **The run title cannot name a random roll.** `run-name` is evaluated before the
job starts, so on `random` it prints the word `random`, not the theme drawn — the
roll happens inside the engine minutes later. The engine emits a `::notice::` naming
the chosen theme, rendered at the TOP of the run page. Fire five random publishes
and the five answers are in five notices; the titles alone would be five identical
rows.

## The site list is hand-maintained, and it cannot be otherwise

`workflow_dispatch` inputs are read out of the workflow file on the default branch
**before any job starts**, so a `type: choice` list cannot be computed. There is no
step that runs early enough to fill it in. Every other list of sites in this repo
is derived from `instances/*/site.yml`; this one is the exception, and it is a
platform limit rather than a decision.

**So it WILL be forgotten. It already was:** `hml` was added as an instance and
wired into `build.yml` on 2026-08-03 and the dropdown was not touched, leaving a
site that builds and cannot be published — visible only to whoever next opened the
dropdown looking for it.

Adding a site is **THREE edits:**

1. `instances/<slug>/site.yml` — the site itself
2. `build.yml` matrix row — the all-sites regression build
3. the `options` list in `publish.yml` — the publish button

⭐ **`bin/publish.sh` is NOT a fourth edit**, and that is the whole reason it reads
`instances/` live rather than carrying its own list. A new site is publishable from
the terminal the moment step 1 lands.

**A `choice` input is case-sensitive and the slugs are lowercase.** `gh workflow run
… -f site=URITP` is rejected before any job starts, with an error about an invalid
value rather than about case. Any wrapper must lower-case the argument;
`bin/publish.sh` does, in `_dr_resolve`.

🔴 ~~"the terminal helper in uritp-docs/guides does"~~ **pointed at a script that did
not exist, for two days** (struck 2026-08-07). `uritp-docs` is a CONTENT repo and may
hold no machinery, so the helper was not merely missing but described as living
somewhere the architecture forbids. Michael then typed the command it promised.
⚑ **The pair of claims (here, and in `instance.py` about `aliases:`) is a worked
example of documentation CREATING a feature: two files agreed, neither owned it,
and agreement between quotes is not evidence that a thing exists.**

## Re-run is not the same as run (fixed 2026-08-03)

GitHub's "Re-run jobs" replays a run **at its original commit.** For a workflow that
builds a site out of THIS repository, re-running an earlier publish rebuilds with an
OLD ENGINE — and because deploys are last-writer-wins, it silently overwrites a
newer, correct build.

It happened for real: three consecutive publishes all shipped engine `74ee551` while
HEAD was `cf35bda`, each stamping over a good build. **The symptom is the worst kind
available — a green run, a fresh timestamp, and none of your changes on the page.**

Three defences: the engine checkout is pinned to `main` EXPLICITLY rather than to the
triggering SHA; the run summary prints the engine commit actually used; and — the
real one, 2026-08-05 — `run-name` puts the site, mode and note in the run TITLE, so a
re-run inherits the title of the run it replays and announces itself as a duplicate.

⚠️ **A re-run carrying a `theme` inherits that too** (2026-08-07). A one-off costume
comes back on. The title says so.

## The same staleness had a third source until 2026-08-06

The defences above are about a stale ENGINE. Neither could see a stale **THEME**: the
canonical vectors were vendored into the engine and re-copied by hand, so a publish
run minutes after a colour edit upstream would render, go green, and paint the old
palette.

The workflow now checks the design system out beside the engine and the content.
**It matters more here than anywhere else** — this is the button somebody presses
right after editing a colour, specifically to look at the result, so a silent
fallback on this path actively disproves a change that did happen.

`continue-on-error` IS the fallback mechanism: no directory means `vectors.py`
renders `theme/canonical/` and says so in the build report. Red X on the step, green
job.

⚠️ **It is also what makes the `theme` input worth anything.** The legal names are
read from that checkout. If it fails, the union shrinks to the vendored copy plus the
four local skins, so a canonical theme that exists upstream can be REJECTED as
unknown — with the fallback warning printed above it, which is the line that
explains why.

---

# Still-stranded reasoning, relocated 2026-08-08

Five blocks were still living in the `.yml` after the first cut. Same rule, same
destination.

## § publish vs build

- **`build.yml`** fires on every engine change and rebuilds EVERYTHING — the engine's
  own regression check: *did my change break a site.*
- **`publish.yml`** is ONE site, on purpose, when its content is ready.

## § The content repo is NOT restated in the workflow

It is read from the instance's own `site.yml` — the file that already had to be
correct for anything to build. The old version carried a `case` statement naming
every repo a second time, so a new site could be added to the dropdown and still
fail on a missing branch of a switch nobody remembered existed.

## § The content checkout is authenticated (2026-08-04)

Same shape as `build.yml` so the two cannot drift. `uritp-docs` went private so the
repo page 404s to anyone who swaps `github.io` for `github.com`, while Pages keeps
serving `gh-pages` publicly. `GITHUB_TOKEN` is scoped to THIS repository, so an
unauthenticated checkout of a private content repo dies with `exit code 128` — which
reads as a broken build rather than a missing credential.

**The condition mirrors the deploy step's own, deliberately**, rather than inventing a
second rule about privacy. Every site this workflow can publish is written to with
the PAT, so the PAT's read access is proven rather than assumed. `template` is the one
exception in both places: it deploys from `publish-default.yml` and never from here,
so nothing has demonstrated the PAT can see `template-docs`, and it stays on
`GITHUB_TOKEN` — all a public repo needs.

## § `fetch-depth: 0` is a preference now, not a requirement (2026-08-04)

🪦 **Superseded, recorded rather than deleted:**

> ~~"docrender/revlog.py builds the automatic revision log by reading `git log` out of
> this checkout, and a shallow clone answers that query without complaining — it
> returns the handful of commits it happens to have, which renders as a
> complete-looking history covering an afternoon."~~

`revlog.py` now renders the TSV the content repo commits for itself and makes NO git
call, so nothing breaks at depth 1. **The shallow-clone trap did not go away, it
MOVED** to the content repo's own revision-log workflow, which pins `fetch-depth: 0`
for exactly the reason quoted above. Kept anyway: a full clone of a markdown repo
costs seconds. Anyone removing it should know it is now a preference.

## § Two mechanical facts that must stay in the file

- **Env exports are inline in the render step** because `$GITHUB_ENV` only reaches
  LATER steps. Setting them elsewhere leaves the build stamp reading `unstamped`.
  `DOCRENDER_THEME` and `DOCRENDER_CANONICAL` are both ALWAYS set; the VALUE varies.
- **The note and theme are reported as separate steps** because a step that does not
  appear did not run. It makes them visible in the step LIST rather than inside a log
  nobody expands — and a publish with no stated reason SAYS so, because silence would
  read as a missing step. Those steps only ECHO; the engine is the authority.

## § `timeout-minutes: 10`

Matches `build.yml` deliberately. A hung render holds a runner for SIX HOURS on the
default ceiling, and the `theatre` render is known to hang rather than fail (observed
2026-08-05). ~20x the worst case; if it fires, it is the messenger.

---

## build.yml · poll.yml · publish-default.yml

Not yet split. `build.yml` is 18KB. When it is next edited, move its reasoning into a
sibling `build-dl.md` rather than growing it in place.
