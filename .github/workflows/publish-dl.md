
# ⭐ AND IT HAS A TERMINAL FRONT DOOR AS OF 2026-08-07: `bin/publish.sh` in this
# repo, sourced into a shell, giving `publish uritp theme:eos`. It dispatches
# THIS workflow with these inputs and invents no vocabulary of its own. See the
# note on the site list below for the one thing it has to do that the web form
# does not.
#
# =============================================================================
# STRUCK 2026-08-05. THE PARAGRAPH BELOW WAS THIS FILE'S CENTRAL CLAIM AND
# IT IS FALSE AT HEAD. IT WAS QUOTED TO MICHAEL AS FACT THIS SESSION.
# =============================================================================
# STRUCK: "publish.yml is the editorial act ... it is a decision rather than a
# side effect. WHY IT IS NOT AUTOMATIC ON CONTENT PUSH: publishing is an
# editorial decision, an unfinished page can sit in `main` for a week without a
# reader ever seeing it, and going live is something somebody chooses."
#
# Read build.yml. It fires `on: push [main]` and its deploy step runs for every
# row with `publisher: matrix`, which is uritp, theatre and hml. **Every engine
# push republishes all three.** Publishing is therefore already a side effect of
# an engine commit, and has been for as long as that trigger has existed.
#
# The ARGUMENT for a manual publish is still a good one. It is simply not a
# description of this pipeline. Anybody who wants publishing to actually BE an
# editorial act has to change build.yml's trigger -- not read this comment and
# feel reassured. Struck rather than deleted because the reasoning is worth
# keeping and because a silently-rewritten comment teaches nobody why it rotted.
#
# WHAT THIS WORKFLOW IS STILL FOR, unambiguously: publishing ONE site NOW,
# without waiting for or making an engine commit, with a preview mode and a
# stated reason. That justifies it on its own.
#
# AND THE OLD SECOND HALF OF THE STRUCK ARGUMENT WAS ALREADY DEAD (2026-08-04).
# It used to read "a content repo holds no workflow -- that is the purity rule --
# so it CANNOT publish itself." `uritp-docs` now holds exactly one workflow, by
# Michael's explicit exception, which regenerates its revision-log TSV on every
# doc commit. So auto-publish became POSSIBLE on the day that stopped being a
# fact. Recorded rather than quietly rewritten, because "impossible" and "chosen
# against" are different arguments -- and as of today neither one is true.
#
# PREVIEW MODE renders the site, diffs it against what is actually being
# served, prints new / disappearing / renamed pages to the run summary, and
# deploys NOTHING. Run it before every publish.
#
# =============================================================================
# THE `note` INPUT -- A PUBLISH CAN CARRY A WHY (added 2026-08-05)
# =============================================================================
# Optional free text. Michael asked whether a publish could carry a comment and
# whether that was even a field. It was not, and a bare input would have been a
# thin answer: GitHub keeps dispatch inputs in the event payload and displays
# them nowhere a person actually looks. So the note is surfaced in THREE places,
# and the surfaces are the feature:
#
#   run-name        the note becomes the RUN TITLE in the Actions list. That is
#                   the only surface anybody scans, and nine runs all called
#                   "Publish a site" is not a log.
#   commit_message  the note rides into the gh-pages deploy commit, so it
#                   outlives Actions log retention in the CONTENT repo's own
#                   history. This is the copy that lasts.
#   step summary    stated on the run itself, beside the engine SHA.
#
# IT MUST STAY OPTIONAL. `required: true` turns every publish into a form,
# and the entire value of the terminal path is that a publish is one word. An
# empty note reproduces the old behaviour byte for byte.
#
# =============================================================================
# THE `theme` INPUT -- A PUBLISH MAY CHOOSE THE LOOK, FOR ONE BUILD (2026-08-07)
# =============================================================================
# Michael: *"what would it take for our publish command to accept an additional
# variable that lets me set the theme at the last minute... I want to be able to
# push publishes with random themes just to debug better."*
#
# Optional free text, same contract as `note` and for the same reasons. It
# reaches the engine as `DOCRENDER_THEME` and is applied in
# `docrender/instance.py:_theme_override` -- hook 00, the only stage that runs
# exactly ONCE per build.
#
#   (empty)        this build is byte for byte the build it would have been.
#                  THE DEFAULT MUST STAY PASSIVE: an input nobody filled in can
#                  never be why a site suddenly looks different.
#   <a theme name> that name renders, for this run only. site.yml is NOT
#                  edited and NOTHING is written to disk, so the override
#                  cannot outlive the run and there is no cleanup to forget.
#   random         the engine rolls one from every legal name and says which.
#
# 🔴 A BAD NAME IS DISCARDED, NOT SUBSTITUTED, and that differs on purpose from
# how a bad theme in site.yml behaves (it falls back to `base`). A committed
# typo should still render a readable site; an override was typed thirty seconds
# ago by somebody watching this run, so answering it with a THIRD theme --
# neither what was typed nor what the site declares -- would send them hunting a
# palette bug. The declared theme renders and the report names the legal set.
#
# ⚠️ WHY IT IS `string` AND NOT `choice`, WHICH IS THE OBVIOUS ASK. The site
# list below is hand-maintained because dispatch inputs are read out of this
# file before any job starts (see the next section). A theme list is strictly
# worse: the legal set is the UNION of maw-themes' `themes.json`, the canonical
# colour table and this engine's local `themes.tsv` -- three files, one of them
# in another repo, resolved live at build time. A hardcoded dropdown would be a
# fourth copy of that union, wrong the first time anybody adds a palette
# upstream, and wrong in the direction that REFUSES a legal name. A typed name
# is checked against the real union by the engine, which is the only place that
# knows it. `bin/publish.sh` declines to pre-validate it for the same reason.
#
# ⚠️ AND THE RUN TITLE CANNOT NAME A RANDOM ROLL. `run-name` is evaluated by
# GitHub before the job starts, so on `random` it prints the word `random` and
# not the theme drawn -- the roll happens inside the engine, minutes later. The
# engine therefore emits a `::notice::` naming the chosen theme, which GitHub
# renders at the TOP of the run page. Fire five random publishes and the five
# answers are in five notices; the titles alone would be five identical rows.
#
# =============================================================================
# THE SITE LIST BELOW IS HAND-MAINTAINED, AND IT CANNOT BE OTHERWISE
# =============================================================================
# `workflow_dispatch` inputs are read out of THIS FILE on the default branch
# before any job starts, so a `type: choice` list cannot be computed. There is
# no step that runs early enough to fill it in. Every other list of sites in
# this repo is derived from `instances/*/site.yml`; this one is the exception,
# and it is a platform limit rather than a decision.
#
# So it WILL be forgotten. It already was: `hml` was added as an instance and
# wired into build.yml on 2026-08-03 and this dropdown was not touched, which
# left a site that builds and cannot be published -- visible only to whoever
# next opened the dropdown looking for it.
#
# Adding a site is therefore THREE edits, not two:
#   1. instances/<slug>/site.yml   (the site itself)
#   2. build.yml matrix row        (the all-sites regression build)
#   3. the options list here       (the publish button)
# The `Resolve the site` step below no longer duplicates the content repo --
# that comes from site.yml -- so the slug is the only thing stated twice.
#
# ⭐ `bin/publish.sh` IS NOT A FOURTH EDIT, AND THAT IS THE WHOLE REASON IT READS
# `instances/` LIVE rather than carrying its own list. A new site is publishable
# from the terminal the moment step 1 lands, with no change to the helper.
#
# A `choice` INPUT IS CASE-SENSITIVE AND THE SLUGS ARE LOWERCASE. `gh
# workflow run ... -f site=URITP` is rejected before any job starts, with an
# error about an invalid value rather than about case. Any wrapper script must
# lower-case the argument; `bin/publish.sh` does, in `_dr_resolve`.
#
# 🔴 THAT LINE POINTED AT A SCRIPT THAT DID NOT EXIST, FOR TWO DAYS (struck
# 2026-08-07). It read "the terminal helper in uritp-docs/guides does" -- and
# `uritp-docs` is a CONTENT repo, which may hold no machinery at all, so the
# helper was not merely missing but described as living somewhere the
# architecture forbids. Michael then typed the command it promised. ⚑ The pair
# of claims (here and in instance.py, about `aliases:`) is a worked example of
# documentation CREATING a feature: two files agreed, neither owned it, and
# agreement between quotes is not evidence that a thing exists.
#
# =============================================================================
# RE-RUN IS NOT THE SAME AS RUN (fixed 2026-08-03)
# =============================================================================
# GitHub's "Re-run jobs" button replays a run AT ITS ORIGINAL COMMIT. For a
# workflow that builds a site out of THIS repository, that means re-running an
# earlier publish rebuilds the site with an OLD ENGINE -- and because deploys
# are last-writer-wins, it silently overwrites a newer, correct build.
#
# It happened for real: three consecutive publishes all shipped engine 74ee551
# while HEAD was cf35bda, each one stamping over a good build. The symptom is
# the worst kind available -- a green run, a fresh timestamp, and none of your
# changes on the page.
#
# Two defences below. The engine checkout is pinned to `main` EXPLICITLY rather
# than to the triggering SHA, and the run summary prints the engine commit it
# actually used, so a stale build is visible instead of inferred.
#
# AND AS OF 2026-08-05 A THIRD, WHICH IS THE REAL ONE: `run-name` puts the
# site, the mode and the note in the run's TITLE. A re-run inherits the title of
# the run it replays, so a stale rebuild now announces itself as a duplicate in
# the list instead of looking like a fresh publish.
#
# ⚠️ AND A RE-RUN CARRYING A `theme` INHERITS THAT TOO (2026-08-07). Re-running
# a themed publish re-applies the theme, because the inputs are part of the run
# being replayed -- so a one-off costume comes back on. The title says so, which
# is the same defence as above.
#
# =============================================================================
# AND THE SAME CLASS OF STALENESS HAD A THIRD SOURCE UNTIL 2026-08-06
# =============================================================================
# The two defences above are about a stale ENGINE. Neither could see a stale
# THEME: the canonical vectors were vendored into the engine and re-copied by
# hand, so a publish run minutes after a colour edit upstream would render, go
# green, and paint the old palette.
#
# This workflow now checks the design system out beside the engine and the
# content. IT MATTERS MORE HERE THAN ANYWHERE ELSE -- this is the button
# somebody presses right after editing a colour, specifically to look at the
# result, so a silent fallback on this path actively disproves a change that
# did happen.
