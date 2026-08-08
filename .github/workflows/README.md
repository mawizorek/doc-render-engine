# Workflows — why they are the way they are

**This file holds the RATIONALE. The `.yml` files hold the MECHANISM.**

A workflow file that is 70% prose cannot be read whole by a tool with a size
cap, which means the one thing that must be editable safely becomes the thing
nobody can edit safely. `publish.yml` reached 27KB against ~40 lines of actual
steps. The steps did not need explaining at that length; the TRAPS did.

So the split, and it is the same rule this repo already applies elsewhere
(procedure lives in a tool, the agent points at it; a decision log lives beside
the descriptor, not inside it):

| Goes in the `.yml` | Goes here |
|---|---|
| the steps | why a step exists at all |
| a one-line `# see README § X` pointer | the incident that created the rule |
| a `# ⚠️` marker on a genuinely dangerous line | superseded reasoning, kept not deleted |
| values, conditions, expressions | what breaks if you change them |

**Nothing below is new.** It is verbatim reasoning relocated out of
`publish.yml`, section by section, so the file could be read and edited.

---

## publish.yml

### § Publish vs build

Pick a site, choose Preview or Publish, run it. That is the whole interface, and
it is deliberately a different thing from `build.yml`:

- **`build.yml`** fires on every engine change and rebuilds EVERYTHING. It is the
  engine's own regression check: *did my change break a site.*
- **`publish.yml`** is ONE site, on purpose, when its content is ready — the
  closest thing this family has to *make THIS public, now.*

### § The `site` dropdown is a hand-maintained list, and it is the one exception

`bin/publish.sh` reads `instances/` live and deliberately keeps no list of sites.
The `choice` input here cannot: GitHub requires literal options. **This dropdown
is the only derived-from-nothing copy of the site list in the family, and it is a
platform limit rather than a decision.**

⚠️ **Adding an instance is TWO edits.** `hml` shipped buildable-but-unpublishable
for two days because only the first was made.

### § The `theme` input is a string, not a dropdown

The legal set is the live union of `maw-themes/themes.json`, the canonical colour
table, and `theme/themes.tsv`, resolved inside the build. A dropdown here would
be a fourth copy of a union this file cannot see — wrong the first time a palette
is added upstream, and wrong in the direction that REFUSES a legal name.

The engine discards an unknown theme loudly, keeps the site's declared one, and
lists the legal names. A typo costs one preview run.

### § The `note` input is optional and has a durable home

Actions logs age out of retention; a commit in the content repo does not. If the
reason for a publish is ever going to be read six months from now, it is read in
the deploy commit message.

⚠️ **The theme rides along in that commit for a sharper reason than the note does**
(2026-08-07): a themed publish leaves a live site that does not match its own
`site.yml`, and that commit is the ONLY durable record of why. Without it, the
next person to open the site and the file together finds a contradiction with no
explanation. It records what was ASKED FOR — on `random`, the engine's notice
names the roll.

### § Checkout pins `main`, not the triggering SHA

Without it, re-running an old run publishes an old engine over a newer build
**and looks completely healthy.**

### § The content repo is NOT restated in this file

It is read from the instance's own `site.yml` — the file that already had to be
correct for anything to build. The old version carried a `case` statement naming
every repo a second time, so a new site could be added to the dropdown and still
fail on a missing branch of a switch nobody remembered existed.

### § The content checkout is authenticated

Same shape as `build.yml` so the two cannot drift. `uritp-docs` went private
2026-08-04 so the repo page 404s to anyone who swaps `github.io` for
`github.com`, while Pages keeps serving `gh-pages` publicly. `GITHUB_TOKEN` is
scoped to THIS repository, so an unauthenticated checkout of a private content
repo dies with `exit code 128` — which reads as a broken build rather than a
missing credential.

**The condition mirrors the deploy step's own, deliberately**, rather than
inventing a second rule about privacy. Every site this workflow can actually
publish is written to with the PAT, so the PAT's read access is proven rather
than assumed. `template` is the one exception in both places: it deploys from
`publish-default.yml` and never from here, so nothing has demonstrated the PAT
can see `template-docs`, and it stays on `GITHUB_TOKEN` — all a public repo
needs.

### § `fetch-depth: 0` is a preference now, not a requirement

🪦 **Superseded 2026-08-04, recorded rather than deleted:**

> *"docrender/revlog.py builds the automatic revision log by reading `git log` out
> of this checkout, and a shallow clone answers that query without complaining —
> it returns the handful of commits it happens to have, which renders as a
> complete-looking history covering an afternoon."*

`revlog.py` now renders the TSV the content repo commits for itself and makes NO
git call, so nothing breaks at depth 1. **The shallow-clone trap did not go away,
it MOVED** to the content repo's own revision-log workflow, which pins
`fetch-depth: 0` for exactly the reason quoted above.

Kept anyway: a full clone of a markdown repo costs seconds. Anyone removing it
should know it is now a preference.

### § The canonical design system is read live, and the fallback is loud

`continue-on-error` IS the fallback mechanism: no directory means `vectors.py`
renders `theme/canonical/` and says so in the build report. The step shows a red
X while the job stays green.

**Preview mode is where this pays.** A fallback caught during a preview costs
nothing; the same fallback on `publish` has already put an old palette on the
live site by the time anybody reads the summary.

⚠️ **It is also what makes the `theme` input worth anything.** The legal theme
names are read from this checkout. If it fails, the union shrinks to the vendored
copy plus the four local skins, so a canonical theme that exists upstream can be
REJECTED as unknown — with the fallback warning printed above it, which is the
line that explains why.

### § Why the env exports are inline in the render step

`$GITHUB_ENV` only reaches LATER steps. Setting them and running `mkdocs` in the
same step is required, or the build stamp reads `unstamped`.

`DOCRENDER_THEME` and `DOCRENDER_CANONICAL` are both **always set, and the VALUE
is what varies.** `instance._theme_override` returns immediately on an empty
string, so setting it unconditionally is safe by contract.

### § The reporting steps are separate on purpose

A step that does not appear did not run. Printing the note and the theme override
as their own steps makes them visible in the step LIST rather than inside a log
nobody expands — and a publish with no stated reason SAYS so, because silence
would read as a missing step.

⚠️ Those steps only ECHO what was asked for. They cannot validate a theme name,
and on `random` they cannot know the roll. The ENGINE is the authority on both
and reports from the render step.

### § `timeout-minutes: 10`

Matches `build.yml` deliberately. A hung render holds a runner for SIX HOURS on
the default ceiling, and the `theatre` render is known to hang rather than fail
(observed 2026-08-05). Ten minutes is ~20x the worst case; if it fires, it is the
messenger.

---

## build.yml · poll.yml · publish-default.yml

Not yet split. `build.yml` is 18KB and `publish.yml` is the file that forced the
issue. When either is next edited, move its rationale here under its own heading
rather than growing it in place.
