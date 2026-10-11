# ClickUp mirror + strict write-back: the frontmatter you can see in a table view

⚠️ **SCOPED 2026-10-11, NOT GREENLIT.** No build number, deliberately — see the numbering debt in [`../next-build-spec.md`](../next-build-spec.md). Decision history: **Authoring Contract (doc standard) — Decision Log**, `Q2` and `J5`.

🔴 **READ THIS FIRST: the one thing that makes a write-back safe is that it never writes to a branch anybody is serving.** Every write-back run opens a **pull request**. A run that goes wrong is an open PR with a diff in it; a run that goes wrong against `main` is indistinguishable from a run that went right. That is the entire safety argument, and every gate below is downstream of it.

---

## §1 The ask

> Michael, 2026-10-11: *"it's just not convenient to have the metadata in the files but that is the reliable way to have that data and it is convenient to have it on the actual coded page but not if it's not going to mirror well or be reliable to write back and forth"*

and the amendment that turned this from a read-only mirror into a build:

> *"I want a strict hook that can take the CU versions and write them carefully back into the REPO files in case i DO make edits here in CU"*

**Ruled first, `J5`: content must be in the FILE; presentation MAY live in ClickUp.** The reason is §1 of this repo's README — a content repo's green **Download ZIP** button has to hand somebody the documents. A title and a lede that exist only in a ClickUp field break that promise. A theme does not; it is a skin.

## §2 Two directions, and they are not one feature

**MIRROR, repo → ClickUp, every build.** Regenerated from scratch, never merged. A regenerated mirror cannot drift, because nothing is remembered between builds.

**WRITE-BACK, ClickUp → repo, manual, PR only.** This is the only direction that can damage anything, so it is the only direction with gates.

⭐ **Splitting them is the design.** A single "sync" feature would have to reconcile, and reconciliation is where every version of this idea has died: last-write-wins picks a winner without telling anybody. Here one direction is disposable and the other is reviewable, and neither one reconciles.

## §3 Where each key lives

**`id` — repo, mirrored, never written.** The filename IS the id (`authoring/frontmatter.md`). Every inbound link resolves on it, including `@peer:id` from sibling sites. 🚫 Refused by the write-back unconditionally, not by allowlist omission but by an explicit check, because the one key that must never move is the one an allowlist edit could quietly admit.

**`status`, `title`, `summary`, `header_info` — repo is home, ClickUp may edit, write-back carries it.** These are content. They land in the file or the ZIP guarantee is a lie.

**`theme` — repo holds the default, ClickUp holds per-page overrides, NEVER written to the file.** Michael's own line, and it is the cleanest idea in the whole design: ClickUp as a build-time **input** rather than a writer. Nothing is stored twice, so nothing can disagree. Ruled per-repo-with-per-page-override on `J4`.

**Everything else — repo only, mirrored read-only.** `gloss`, `keywords`, `router`, `related`, `xref`, `data`, `order`, `indexed`, `revised`, `source`. Each is a judgment about one page, made by whoever is looking at that page.

**`repo` — a mirror COLUMN, not a frontmatter key.** Michael wants it to sort by. It is derivable from which repo the file came from, so putting it in the file would be a value with two homes and no author. 🚫 Does not go in the contract.

## §4 The mirror

Source is `/doc-index.json`, already published every build by `docindex.py` (stage 09). ⚠️ **Whether it carries every key this mirror wants is UNVERIFIED** — gate G0. If it does not, widen `docindex.py` first; do not add a second extraction.

One ClickUp task per page. **Matched on `id`**, never on title and never on path — titles repeat and paths move, which is the whole reason `id` exists.

🔴 **Mirror columns are overwritten every build, and the list description has to say so.** Anything typed into one is gone at the next build. That is not a bug to fix later; it is what makes the mirror trustworthy, and a user who has not been told is a user who will lose work exactly once.

## §5 The write-back, where "strict" gets mechanical

1. **PR only.** Never `main`, never `gh-pages`. One run, one PR, one reviewable diff.
2. **Closed allowlist**, named in §3. An unknown key **fails the whole run**, it does not skip the row — a partial write nobody was told about is the failure this spec exists to prevent.
3. **Drift refusal instead of merging.** The mirror records each file's blob SHA when it pulls. If HEAD's SHA differs at write-back time, that file is **refused and reported**. No three-way merge, no guess, no last-write-wins. The repo always wins a race it did not know it was in.
4. **Surgical edits.** Rewrite the one `key: value` line inside the frontmatter block. 🚫 Never re-serialise the YAML — a round-trip through a YAML dumper reorders keys and strips every comment, and in this repo the comments are the documentation. Never touch the body. A key that is absent is inserted in the contract's declared order.
5. **Blank never deletes.** An empty ClickUp field means *no opinion*, never *remove the key*. Deleting a key is a file edit.
6. **Manual trigger only.** Same posture as `publish.yml`. 🚫 No cron, no on-change automation: this is the Derived Field Pattern's `Q2` (*what re-drives it*) across a runtime boundary, and that question has failed on four separate instances on that page, every time by a re-driver scoped to fewer events than the value had sources.
7. **`status` gets no special case, because the PR already is one.** It is the engine's only hard gate and a bad value publishes work nobody cleared — but nothing reaches a built site until somebody merges, so the review IS the gate. ⚠️ Worth stating because it is the one key where "the PR catches it" is load-bearing rather than belt-and-braces.

## §6 Gates before merge, each one empirical

**G0.** Does `/doc-index.json` carry every key in §3? Widen `docindex.py` before anything else if not.

**G1 — THE COLON, and this one has already drawn blood.** A summary typed in ClickUp containing `: ` must survive ClickUp → file → render. The YAML colon trap killed four course pages in `uritp-docs`, documented on `template-docs/authoring/data-tables.md`. Quote on write or refuse the value; **never emit a bare colon.**

**G2.** Accents, apostrophes, straight and curly quotes, and emoji round-trip byte-identical.

**G3.** A multi-line ClickUp text field. Fold to one line or emit a block scalar — ruled before code, never discovered at runtime. Broken YAML on a content repo is a page that stops building.

**G4.** A file renamed between mirror and write-back: drift refusal fires, the file is absent from the PR, the report names it.

**G5.** A page deleted in the repo whose task still exists: reported, never resurrected.

**G6.** Two tasks claiming one `id`: refuse both and report, matching `objects.py`'s existing `duplicate_id` posture (*"links to it are a coin flip"*).

## §7 What this costs, stated as a trade

🔴 **The write-back is not a convenience, it is what keeps the ZIP guarantee true.** The moment a title is edited in ClickUp and the PR is never run, the file is stale and that green button hands somebody an old document. A read-only mirror has no such exposure. **Choosing to allow ClickUp edits is choosing to owe the write-back**, and an unrun write-back is a slow leak in §1 of the README rather than a missing nicety.

⚠️ **`theme`-in-ClickUp-only makes the published look depend on ClickUp being readable at build time.** Fallback is graceful and must be: unreachable means the repo default renders, with a report line. 🚫 It must never fail the build — same posture as everything else in this engine.

⚠️ **Between a ClickUp edit and a merged PR, one value has two homes.** That window is unavoidable and it is *visible*, which is the only reason it is acceptable: an open PR is a thing you can see, unlike a sync that has not fired.

## §8 Code shape

`docrender/clickuppull.py` is **already specced** by [`view-snapshot.md`](view-snapshot.md) §5 and this is its third caller, on the `api` backend. 🚫 Do not write a second ClickUp client; that is `view-snapshot.md` §9's named road not taken.

New `docrender/mirror.py` with a `docrender/mirror-dl.md` sidecar from day one — mechanism in the module, the why in the sidecar.

🔴 **The write-back is NOT a renderer hook.** It runs in a workflow, not in a build. A hook that writes frontmatter makes the build edit its own inputs, and it breaks preview: `mode: preview` would either skip the write (so a preview no longer shows what publish does) or fire it (so a dry run mutates the repo). New `.github/workflows/mirror-writeback.yml`, `workflow_dispatch` only, opens the PR.

`report.py` gains a `mirror` bucket: every page mirrored, every file refused for drift, every key written.

## §9 Rulings owed before code

**R1.** Does the file carry a `cu:` pointer to its ClickUp task (Michael's draft shows `cu: MAW-2486`), or does the mirror hold the mapping? A `cu:` key is self-describing and survives a repo move; it is also a key that means nothing to a reader of the page, which is the test `frontmatter.md` applies to every field. **Recommend: no `cu:` key. Match on `id`,** which is already permanent and already the link contract.

**R2.** `header_info` is a NET-NEW key. It needs declaring in `objects/_base.yml`, legal values fixing, and an author-facing entry in `frontmatter.md`. What does it control, exactly — the rendered title block, the lede, or both?

**R3.** Confirm `repo` is a mirror column only, per §3.

**R4.** Confirm `status` belongs on the write-back allowlist at all. §5.7 argues the PR covers it; the conservative alternative is leaving it repo-only.

**R5.** Confirm the `theme`-unreachable fallback is *repo default renders plus a report line*, never a failed build.

## §10 Out of v1

Body content from ClickUp · the `!!! summary` callout whose content lives in the database (a rendering build, not a mirror one) · the heading-level change that gives `#` back to page content (chrome, and a separate decision) · creating pages from ClickUp · deleting files from ClickUp · any cron · any cache of previous mirror state.

## §11 Roads not taken

**Two-way sync.** No reconciliation point, and it fails silently. The whole reason this is two features.

**Direct commits to `main`.** A bad run looks exactly like a good one.

**Writing on publish.** Makes the build edit its own inputs and breaks preview mode, per §8.

**A second ClickUp API client.** `view-snapshot.md` §9.

**Committing the mirror as JSON in the repo.** A second claimant on `/doc-index.json`, which is the defect that retired `roster.json`, `registry.json` and `app-index.md`.
