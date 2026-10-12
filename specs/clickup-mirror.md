# ClickUp mirror + strict write-back: the frontmatter you can see in a table view

⚠️ **SCOPED 2026-10-11. DECISION-COMPLETE, NOT YET BUILT.** No build number, deliberately — see the numbering debt in [`../next-build-spec.md`](../next-build-spec.md). Decision history: **Authoring Contract (doc standard) — Decision Log**, `Q2`, `J5` and `J6`.

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

**`status`, `title`, `summary`, `header_info` — repo is home, ClickUp may edit, write-back carries it.** These are content. They land in the file or the ZIP guarantee is a lie. 🔴 `status` and `type` both cross an ENUM BOUNDARY on the way — see **G7**, which is the gate `R4` opens and does not close.

**`theme` — repo holds the default, ClickUp holds per-page overrides, NEVER written to the file.** Michael's own line, and it is the cleanest idea in the whole design: ClickUp as a build-time **input** rather than a writer. Nothing is stored twice, so nothing can disagree. Ruled per-repo-with-per-page-override on `J4`.

**Everything else — repo only, mirrored read-only.** `gloss`, `keywords`, `router`, `related`, `xref`, `data`, `order`, `indexed`, `revised`, `source`. Each is a judgment about one page, made by whoever is looking at that page.

⚠️ **TWO OF THOSE TEN NEED A CORRECTION, FOUND 2026-10-11 AFTER THIS LIST WAS WRITTEN.**

* **`xref` is read by NOTHING.** It is declared in `objects/_base.yml` and no module consumes it — the fourth instance of this engine's recurring declared-but-unread defect, after `revised:`, `related:` and `router:`. All ten code references to the word are `.docrender-xref` (the class on a peer LINK), `xref-cache.json` (the peer index cache) and the `stale_xref` report bucket, none of them the frontmatter key. 🚫 So a mirror column for it must be **labelled dead**, or the mirror becomes the thing that makes a dead key look alive. Cross-site references are written inline as `[label](@peer:id)` and nowhere else.
* **`related` is no longer a flat list of ids.** As of #294 an entry may carry its own text (`- frontmatter: the header contract`), and the text describes the RELATION rather than either page. ⚠️ A mirror column that flattens it to ids is **lossy**, and a reader of that column would not know it. Mirror the rendered string or omit the column.

**`repo` — a mirror COLUMN, not a frontmatter key.** Michael wants it to sort by. It is derivable from which repo the file came from, so putting it in the file would be a value with two homes and no author. 🚫 Does not go in the contract. Ruled, `R3`.

## §4 The mirror

Source is `/doc-index.json`, already published every build by `docindex.py` (stage 09). ⚠️ **Whether it carries every key this mirror wants is UNVERIFIED** — gate G0. If it does not, widen `docindex.py` first; do not add a second extraction.

One ClickUp task per page. **Matched on `id`**, never on title and never on path — titles repeat and paths move, which is the whole reason `id` exists.

🔴 **THE DESTINATION LIST IS NAMED HERE BECAUSE IT WAS NOT, AND IT IS NOT GREENFIELD (added 2026-10-11).** It is **`>REPO_PAGES`** (list `901329123131`), in folder `ADD JOINS`, space `MAW Documents`. Measured the same day: **36 rows, 18 custom fields**, already holding `PageID`, `PageStatus`, `PageType`, `Repo`, `FileType`, `✍️ Edit Link`, `🌐 Published Link`, `GitHub Folder Name`, `Agent Assignee`, and two list relationships.

⚡ **So the first mirror run is a MERGE into rows a human has been maintaining by hand, not a create.** Breakdown by `Repo`: `uritp-safety` 24, `uritp-docs` 6, **unset 6**. Three consequences, none optional:

1. The 6 rows with no `Repo` cannot be matched to a source tree. **Refuse them by name**; do not guess.
2. A hand-typed `PageID` that matches no file in its repo is an ORPHAN row. Report it; `§6 G5` already covers the deleted-page case and this is the same shape arriving from the other side.
3. 36 rows against 607 markdown files in `uritp-docs` alone means the mirror's first real run creates hundreds of tasks. That is a bulk write to ClickUp, which is far harder to unwind than a branch. 🔴 **Pilot first: §12.**

🔴 **Mirror columns are overwritten every build, and the list description has to say so.** Anything typed into one is gone at the next build. That is not a bug to fix later; it is what makes the mirror trustworthy, and a user who has not been told is a user who will lose work exactly once. ⚠️ On this list that warning is overdue rather than pre-emptive: the hand-maintained values above are precisely what a first mirror run would overwrite.

## §5 The write-back, where "strict" gets mechanical

1. **PR only.** Never `main`, never `gh-pages`. One run, one PR, one reviewable diff.
2. **Closed allowlist**, named in §3. An unknown key **fails the whole run**, it does not skip the row — a partial write nobody was told about is the failure this spec exists to prevent.
3. **Drift refusal instead of merging.** The mirror records each file's blob SHA when it pulls. If HEAD's SHA differs at write-back time, that file is **refused and reported**. No three-way merge, no guess, no last-write-wins. The repo always wins a race it did not know it was in.
4. **Surgical edits.** Rewrite the one `key: value` line inside the frontmatter block. 🚫 Never re-serialise the YAML — a round-trip through a YAML dumper reorders keys and strips every comment, and in this repo the comments are the documentation. Never touch the body. A key that is absent is inserted in the contract's declared order.
5. **Blank never deletes.** An empty ClickUp field means *no opinion*, never *remove the key*. Deleting a key is a file edit.
6. **Manual trigger only.** Same posture as `publish.yml`. 🚫 No cron, no on-change automation: this is the Derived Field Pattern's `Q2` (*what re-drives it*) across a runtime boundary, and that question has failed on four separate instances on that page, every time by a re-driver scoped to fewer events than the value had sources.
7. **A run that changes `status` says so in the PR TITLE**, not only in the diff. Ruled `R4`; reasoning there.
8. **An enum value that does not map is REFUSED, never passed through.** G7.

## §6 Gates before merge, each one empirical

**G0.** Does `/doc-index.json` carry every key in §3? Widen `docindex.py` before anything else if not.

**G1 — THE COLON, and this one has already drawn blood.** A summary typed in ClickUp containing `: ` must survive ClickUp → file → render. The YAML colon trap killed four course pages in `uritp-docs`, documented on `template-docs/authoring/data-tables.md`. Quote on write or refuse the value; **never emit a bare colon.** ⚠️ Widened 2026-10-11: a leading backtick or `@` is reserved by YAML at the head of a plain scalar too, and three `related:` notes hit exactly that in the #36 migration. Quote on any of the three.

**G2.** Accents, apostrophes, straight and curly quotes, and emoji round-trip byte-identical.

**G3.** A multi-line ClickUp text field. Fold to one line or emit a block scalar — ruled before code, never discovered at runtime. Broken YAML on a content repo is a page that stops building.

**G4.** A file renamed between mirror and write-back: drift refusal fires, the file is absent from the PR, the report names it.

**G5.** A page deleted in the repo whose task still exists: reported, never resurrected.

**G6.** Two tasks claiming one `id`: refuse both and report, matching `objects.py`'s existing `duplicate_id` posture (*"links to it are a coin flip"*).

### 🔴 G7 — THE TWO VOCABULARIES ARE NOT THE SAME VOCABULARY (added 2026-10-11)

Read off the live field definitions on `>REPO_PAGES`, not inferred:

```
ClickUp PageStatus     draft  private  public  closed  unlisted
engine status:         hidden  unlisted  gated  public

ClickUp PageType       policy program privilege handbook guide role
                       course form index media "Checklist | Table"
engine type:           page index venue space standard procedure reference
```

**`status` overlaps on two values of five. `type` overlaps on exactly one word out of eighteen.** They are two different taxonomies wearing similar names: ClickUp's are EDITORIAL categories (what kind of document is this), the engine's are RENDER contracts (what does this page draw, what does it require).

⚡ **AND `R4` WALKS STRAIGHT INTO IT.** That ruling puts `status` on the write-back allowlist for a good reason — *"promoting a batch of pages from `hidden` to `public` from a table view is the single most likely reason to touch frontmatter from ClickUp at all"* — and the field anybody would reach for to do that is `PageStatus`, whose first option is `draft`. `status:` is the engine's only hard gate with no default and no fallback: a page that carries an unknown value **is not built**. So the single most likely first use of this feature writes `status: draft` into a batch of files, those pages vanish, and every `@id` pointing at them renders a dead reference on pages nobody edited.

🔴 Live proof the mismatch is already in the data rather than hypothetical: `policy-emergency-contacts` carries PageType **policy** and file `type: page`.

**The rule:**

1. **A mapping table per axis, as DATA, not as code.** ClickUp value → engine value, one TSV each. Deterministic sort by key, frozen column order, refuse on drift — the free transfers already granted by the FMP law's external-data-store convention.
2. **The write-back REFUSES an unmapped value** and reports the row. It does not pass it through and it does not guess `public`. §5 rule 8.
3. **On the render side an unmapped `status` makes the page `unlisted` and the build stays green**; an unmapped `type` falls back to `page` and is reported, which is already `objects.py`'s behaviour. Michael: *"i don't want to delay builds, but you are constantly breaking builds just because we find something."*
4. **`PageType` and `type:` may legitimately disagree forever.** Different questions, many-to-one mapping, and the registry keeps the richer value.

🚩 OPEN: whether `>REPO_PAGES` should instead grow a second column for the engine's render contract, so the row carries both. Cleaner, and one more column maintained by hand. Not decided.

## §7 What this costs, stated as a trade

🔴 **The write-back is not a convenience, it is what keeps the ZIP guarantee true.** The moment a title is edited in ClickUp and the PR is never run, the file is stale and that green button hands somebody an old document. A read-only mirror has no such exposure. **Choosing to allow ClickUp edits is choosing to owe the write-back**, and an unrun write-back is a slow leak in §1 of the README rather than a missing nicety.

⚠️ **`theme`-in-ClickUp-only makes the published look depend on ClickUp being readable at build time.** Fallback is graceful and must be: unreachable means the repo default renders, with a report line. 🚫 It must never fail the build — same posture as everything else in this engine. Ruled `R5`.

⚠️ **Between a ClickUp edit and a merged PR, one value has two homes.** That window is unavoidable and it is *visible*, which is the only reason it is acceptable: an open PR is a thing you can see, unlike a sync that has not fired.

## §8 Code shape

`docrender/clickuppull.py` is **already specced** by [`view-snapshot.md`](view-snapshot.md) §5 and this is its third caller, on the `api` backend. 🚫 Do not write a second ClickUp client; that is `view-snapshot.md` §9's named road not taken.

New `docrender/mirror.py` with a `docrender/mirror-dl.md` sidecar from day one — mechanism in the module, the why in the sidecar.

🔴 **The write-back is NOT a renderer hook.** It runs in a workflow, not in a build. A hook that writes frontmatter makes the build edit its own inputs, and it breaks preview: `mode: preview` would either skip the write (so a preview no longer shows what publish does) or fire it (so a dry run mutates the repo). New `.github/workflows/mirror-writeback.yml`, `workflow_dispatch` only, opens the PR.

`report.py` gains a `mirror` bucket: every page mirrored, every file refused for drift, every key written.

## §9 Rulings, RESOLVED 2026-10-11

⚠️ **Ruled by Brain on Michael's explicit delegation** (*"Resolve the questions."*, 2026-10-11 17:31 ET). Each one states its reasoning so he can reverse any of them in a line. Two go against the recommendation that was on the table.

### R1 — 🚫 NO `cu:` KEY. The write-back matches on `id`.

His draft showed `cu: MAW-2486` in the frontmatter. **Refused**, and the reason generalises past this key: `id` is already permanent, already the inbound-link contract, and already the mirror's match key, so a `cu:` key is a **second join key for one relationship** — and two keys for one relationship is a thing that can disagree with itself. The Budget Code Mapper already ruled this shape once: *one* durable join key, *"match, never duplicate on re-import."*

⭐ **The principle worth keeping: a derived pointer lives on the DISPOSABLE side, never in the durable source.** The mirror task carries the page's `id`; the page does not carry the task's. The mirror is regenerated every build and can be rebuilt from nothing, so a wrong pointer there costs one build. A wrong pointer committed into a content repo costs a migration.

⚠️ Secondary, and it would have bitten eventually: a ClickUp task can be deleted and recreated, which silently invalidates a `cu:` value in a tracked file — the exact *"renamed key"* failure `objects.py` keeps a `_LEGACY_KEYS` list to catch, except unreportable, because nothing in the engine would know the id had gone stale.

✅ **RE-TESTED AND UPHELD 2026-10-11, against a rival design that was built on the opposite answer** (§11). The counter-argument was that a PageID is authored and therefore fallible, while `MAW-####` is issued and cannot collide, so the task id is the trustworthy fallback. It loses on durability rather than on uniqueness: the issued id is stable only while the task is, and the repo outlives the task. A fallible key the repo controls beats an infallible key it does not.

### R2 — `header_info` is a VISIBILITY SWITCH over the title and the lede TOGETHER. Legal values `shown` (default) and `hidden`.

Michael answered this himself in the same draft and it is worth quoting, because it settles what the key is NOT: *"so the choice is actual whether to hide/show the title&summary versus what that content is."* So it controls **display, never content**, and it governs both as one unit — a page rendering a lede with no title above it is a layout nobody asked for.

🔴 **AND IT MUST NOT TOUCH SEARCH OR `/doc-index.json`.** This is the `indexed:` trap arriving on a new key: three things in this engine are called an index, and `indexed: false` already means *only* the parent page's contents list. `header_info: hidden` means **one thing — the title block does not render on this page.** The `summary` still feeds the search result, still publishes to `/doc-index.json`, and still resolves `gloss_from_summary`. A key whose name sounds like metadata and whose effect is layout needs that said out loud, in `frontmatter.md`, before it ships.

⚠️ Owed with it: a declaration in `objects/_base.yml`'s `optional:` list and an author-facing entry. 🚫 It must not ship as a key the engine honours and no type declares — that is the `data:` and `router:` defect, and it has now happened twice.

### R3 — ✅ `repo` is a mirror COLUMN. Confirmed.

It fails `frontmatter.md`'s own test in the most direct way available: **it is not a fact about the page at all**, it is a fact about where the page is stored. Every other key describes the document; this one describes the shelf. It is derivable from which repo the file came from, so writing it into the file creates a value with two homes and no author.

⚠️ The column exists on `>REPO_PAGES` today and **6 of 36 rows have it unset**, which is why §4 refuses those rows rather than inferring them.

### R4 — ✅ `status` GOES ON THE WRITE-BACK ALLOWLIST. 🔴 This reverses the earlier recommendation.

The argument against it was real: `status` is the engine's only hard gate, and a bad value publishes work nobody cleared. **It loses anyway**, for a reason that only becomes obvious once the use case is named: *promoting a batch of pages from `hidden` to `public` from a table view is the single most likely reason to touch frontmatter from ClickUp at all.* Leaving `status` off the list makes the write-back a feature nobody reaches for, which means it does not get run, which — per §7 — is precisely how the ZIP guarantee rots.

⭐ **The PR gate is genuinely sufficient here and it is worth being explicit about why.** Nothing reaches a built site until a human merges. A bad `status` in an open PR has published nothing. That is a stronger protection than an allowlist omission, because an omission can be edited away by anybody in one line while the merge step cannot.

⚠️ **One new gate, added with the ruling:** a run that changes any `status` **names it in the PR title**, not only in the diff. A status flip is the only change in the allowed set that alters what the public can see, and a diff is something you have to open. Cheap, and it makes the one dangerous case the loudest thing about the run.

🔴 **AND IT NEEDS G7 TO BE SAFE, WHICH WAS NOT NOTICED WHEN THIS WAS RULED.** The ruling is unchanged and still right. What it assumed is that the ClickUp side and the file side speak the same five words about status, and they do not. Read G7 before implementing this row.

### R5 — ✅ `theme` unreachable renders the repo default plus a report line. Never a failed build. Confirmed.

Anything else creates a new coupling where a ClickUp outage takes down a documentation site, which is strictly worse than a page wearing the wrong skin for an afternoon. Matches the engine's founding posture after `--strict` froze the live site twice in forty minutes.

⚠️ **The report line must name the page AND say why**, e.g. *"site theme used: ClickUp unreachable."* "Graceful" and "silent" are not the same thing, and a page quietly rendering a theme nobody chose is how the original three-way `theme` contradiction went unnoticed for two weeks.

## §10 Out of v1

Body content from ClickUp · the `!!! summary` callout whose content lives in the database (a rendering build, not a mirror one) · the heading-level change that gives `#` back to page content (chrome, and a separate decision) · creating pages from ClickUp · deleting files from ClickUp · any cron · any cache of previous mirror state.

## §11 Roads not taken

**Two-way sync.** No reconciliation point, and it fails silently. The whole reason this is two features.

**Direct commits to `main`.** A bad run looks exactly like a good one.

**Writing on publish.** Makes the build edit its own inputs and breaks preview mode, per §8.

**A second ClickUp API client.** `view-snapshot.md` §9.

**Committing the mirror as JSON in the repo.** A second claimant on `/doc-index.json`, which is the defect that retired `roster.json`, `registry.json` and `app-index.md`.

**A `cu:` frontmatter pointer.** `R1`.

🔴 **A `specs/page-registry.md` WITH CLICKUP AS THE AUTHOR — written 2026-10-11 and WITHDRAWN UNMERGED.** Recorded so it is not re-walked, because it was argued across two sessions and it is genuinely coherent: `>REPO_PAGES` as the database, two identity lines (`id` + `cu:`), registration as a one-way door where an unregistered page's frontmatter is the intake form, and a snapshot committed into the content repo that the build reads to generate frontmatter. It was withdrawn on three collisions with this file: the snapshot is the committed-mirror road refused above, the second identity line is refused by `R1`, and ClickUp-as-author inverts `J5`. ⭐ **Two of its findings survived and are folded in** — G7, and §4's naming of the destination list. ⚡ The lesson is cheaper than the spec was: *the index in `next-build-spec.md` is the first thing to read before scoping anything, and it was not read.*

## §12 PILOT: `template-docs` first, and it is not optional

> Michael, 2026-10-11: *"let's plan to test the sync with templates"*

Same pilot repo as the `related:` migration (#36), and the reasons are stronger here.

* ⭐ **Zero rows on `>REPO_PAGES` carry `Repo: template-docs` today.** So the first mirror run is a pure CREATE on a tree nobody reads, instead of a merge into 24 hand-maintained `uritp-safety` rows. The dangerous path gets exercised where it is cheap.
* **`template-docs` is already a `Repo` dropdown option**, so no field edit is needed to run it.
* **30 markdown files, zero PII, no readers.** It is the engine's own gold standard, served from the engine's own Pages.
* ⚠️ **4 of the 30 are the edge cases and they are the point of the pilot:** `README.md` (no frontmatter at all), `theatre/index.md` and `theatre/stage-management/index.md` (**zero-byte files**), and `theatre/stage-management/callboard-headers.md` (body only, no frontmatter). Each must be **refused by name**. A mirror that invents a row for a zero-byte file is the failure this pilot exists to catch.

### Pass criteria, in order

1. **Dry run writing nothing**, reporting what it WOULD create per file.
2. Tasks created equals markdown files carrying an `id:`; the four above appear in a refusal list.
3. **Re-run: zero created, zero changed, no PR.** Idempotency is the thing most likely to be wrong.
4. Change one `title` in ClickUp → write-back → the PR touches exactly one line of one file, and the H1 mismatch is reported (the engine does not reconcile those).
5. Edit that same file on `main` first, then write-back: **drift refusal fires**, the file is absent from the PR, the report names it (G4).
6. Set a row's `PageStatus` to `draft` → **the write-back refuses the value and reports it** (G7). The file is untouched and the page still builds.
7. A summary containing `: `, one containing a leading backtick, and one with an emoji all round-trip byte-identical (G1, G2).
8. ClickUp unreachable at build → site renders from file frontmatter, report says so, exit code 0.

🔴 **Nothing runs against `uritp-docs` until all eight pass.** 607 markdown files there against 6 registered rows means the first run is a bulk create of hundreds of ClickUp tasks, and tasks are harder to unwind than a branch.
