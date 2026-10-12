---
id: page-registry
title: Page metadata from the ClickUp registry
status: draft
summary: ClickUp `>REPO_PAGES` becomes the database for standard page metadata, the repo keeps the prose, and the build generates the frontmatter from a committed snapshot.
revised: 2026-10-11
---

# Page metadata from the ClickUp registry

**Nothing in this document is built.** Written 2026-10-11, after the design was
settled across two sessions and lived nowhere but a chat log and two decision
logs. ⚑ *A build gets a spec first* is a standing rule here, and this feature
had reached "fully designed" without one, which is how a design becomes
something only the person who argued it can implement.

Michael, opening it: *"in an ideal world, we had NO metadata in the repo -- and
the link here in clickup was essentially straight to a body text of the content.
the metadata frontmatter is all part of a discrete record, so i should be able
to edit that in a format independent of each specific page."*

=============================================================================
## 1. The shape, in one paragraph
=============================================================================

ClickUp list `>REPO_PAGES` (`901329123131`) is the database. A markdown file
keeps its prose, two identity lines, and the handful of keys that are genuinely
about that one page. Every standard field -- title, type, status, order, summary
-- is **generated into the file at build time** from a snapshot pulled out of
ClickUp and committed beside the content. The published page is built from the
file, as it always was, so nothing at render time depends on a network call.

🚫 **NOT FileMaker.** That was the opening guess and it is wrong: the records
already exist in ClickUp with 18 custom fields, and the FMP law
(`FileMaker Patterns + Conventions`, "Git repo as an external data store") locks
the direction as **ClickUp AUTHORS → FileMaker RENDERS → git ARCHIVES**. Adding
FileMaker here would insert a renderer between an author and an archive for no
gain.

=============================================================================
## 2. The two identity lines
=============================================================================

```yaml
---
id: policy-emergency-contacts     # PageID. The canonical key.
cu: MAW-2117                      # the native ClickUp custom task id. Fallback.
---
```

**PageID resolves first.** On a miss, the task id resolves and the build warns
that the slug is stale. On a double miss the page is unregistered (§3).

⭐ TWO LINES RATHER THAN ONE, AND THE SECOND ONE IS NOT REDUNDANCY. A PageID is
authored and can be retyped, corrected or collided; `MAW-####` is issued by
ClickUp and cannot. Michael: *"PAGE ID will be the id, but it's nice to have a
native real fallback."*

⚠️ VERIFIED, NOT ASSUMED: the `MAW` prefix was enabled mid-design and checked
live -- Emergency Contacts is `MAW-2117`, and the ids are **workspace**
sequential (1990–2117 across this list), so they are unordered within the list
and carry no sort meaning. 🚩 Durability across a cross-space move is still
unverified. Verify before relying on the fallback for anything but lookup.

=============================================================================
## 3. Registration is a ONE-WAY DOOR
=============================================================================

Michael: *"if I'm writing in the repo, I may dump things into the front matter
quickly and expect them to appear in ClickUp if they don't exist as repo docs
yet."*

So there are exactly two states, and the field ownership flips between them:

**UNREGISTERED** -- no row matches either id. The file's frontmatter **is the
intake form.** The sync creates the ClickUp row from it, verbatim. This is the
only direction in which the repo ever writes to ClickUp.

**REGISTERED** -- a row matches. ClickUp owns every standard field, and the
build generates them into the file. The repo never writes back.

⭐ ONE FIELD, ONE AUTHOR, AT EVERY POINT IN TIME. That is the whole invariant,
and it is what makes this safe without locking or merge logic. Registration is a
handover, not a sync.

🔴 AND IT REFINES THE FMP LAW RATHER THAN BREAKING IT. That law says *"nothing
pushes back to ClickUp at all."* Logged as **J17** on the FMP Apps Shared Build &
Behaviour decision log: the line was written for a pipeline where FileMaker is
the renderer and the repo is a dumb archive. Here the repo is where an author
actually types, and the carve-out is scoped to **creation of a row that does not
exist yet** -- never to updating one that does.

### Hand-editing a standard field on a registered page

It neither pushes nor gets silently overwritten. ClickUp's value publishes, and
the disagreement is **reported as inventory**. Nothing fails.

=============================================================================
## 4. 🔴 THE TWO VOCABULARIES DO NOT MATCH, AND THIS IS THE FINDING THAT
##    DECIDES THE SPEC
=============================================================================

Read off the live field definitions on 2026-10-11:

```
ClickUp PageStatus     draft  private  public  closed  unlisted
engine status:         hidden  unlisted  gated  public

ClickUp PageType       policy program privilege handbook guide role
                       course form index media "Checklist | Table"
engine type:           page index venue space standard procedure reference
```

**`status` overlaps on two values of five. `type` overlaps on exactly one word
out of eighteen.** These are two different taxonomies wearing similar names:
ClickUp's are EDITORIAL categories (what kind of document is this, in the
program), the engine's are RENDER contracts (what does this page draw, what does
it require).

⚡ AND A NAIVE GENERATOR WOULD HAVE BROKEN EVERY AFFECTED BUILD. `status:` is the
one field with no default and no fallback -- a page that forgets it **is not
built**. Writing `status: draft` into a file from a ClickUp row does not produce
a draft page; it produces a page that vanishes, plus a dead `@id` on every page
that linked to it. Live proof that the mismatch is already in the data:
`policy-emergency-contacts` carries PageType **policy** and file `type: page`.

### The rule

1. **A mapping table, as DATA, not as code.** One TSV per axis in the engine,
   ClickUp value → engine value. Per the FMP law's free transfers: mapping table
   as data, deterministic sort by key, frozen column order, refuse on drift.
2. **An unmapped `type` falls back to `page` and is reported.** That is already
   `objects.py`'s behaviour for an undeclared type, so this adds no new polarity.
3. **An unmapped `status` renders the page `unlisted` and the build stays
   green.** 🚫 It does not fail, and it does not guess `public`. The visibility
   carve-out Michael agreed to: *"i don't want to delay builds, but you are
   constantly breaking builds just because we find something."*
4. **`PageType` and `type:` may legitimately disagree forever.** They are
   different questions. The mapping is many-to-one and the registry keeps its own
   richer value.

🚩 OPEN: whether the engine should instead grow its OWN field on the row, so the
registry carries both the editorial category and the render contract. Cleaner,
and one more column to maintain by hand. Not decided here.

=============================================================================
## 5. What stays in the file, permanently
=============================================================================

Not everything normalizes. These are per-page by nature and the registry would
only be a worse place to type them:

- **`related:`, including per-entry local text.** Built 2026-10-11
  (doc-render-engine#294). The note describes the RELATION, not the destination,
  so it has no home on either page's row. Proof: `markers.md` calls Routers *"the
  other inline tool, for routing rather than confidence"* and `routers.md` calls
  Markers *"the other inline tool, for confidence rather than routing"* -- one
  edge, opposite directions. See `docrender/related.py`.
- **Local form links and embedded views.** Page content that happens to be
  written as a key.
- **`router_code:`, `data:` slots, `nav:`.** Each is a fact about this file.

=============================================================================
## 6. The snapshot
=============================================================================

**It lives in the repo that generated it, outside the published tree.** Michael's
ruling, and the better instinct: metadata history sits beside content history, so
one `git log` answers both.

```
<content-repo>/.registry/snapshot.json      # excluded from the build output
```

- **One snapshot per `Repo` dropdown value.** Eight values exist today
  (`uritp-docs`, `uritp-safety`, `maw-prose`, `ClickUp_apps`, `maw-themes`,
  `template-docs`, `hml-docs`, `scratch-documentation`).
- 🔴 **NO TIMESTAMP INSIDE THE COMMITTED FILE.** FMP law, rule 3. Run metadata
  goes in the commit message, where it cannot create a diff that says nothing.
- **Skip the write when the hash is unchanged**, so a sync with no changes
  produces no commit.
- **A `schema.json` sidecar, and refuse on drift.** A column added in ClickUp
  stops the sync rather than silently widening the file.
- 🚫 **NO PII, EVER.** Git history is permanent. The registry holds page
  metadata; it does not hold contact details. ⚡ Live counter-example to be fixed
  independently: `uritp-safety/REPO_PAGES/policy-emergency-contacts.md` carries
  three staff cell numbers in an HTML comment.

### Accepted costs, named

- The snapshot is excluded from build output, so it is a repo artifact a reader
  never sees.
- **A metadata-only change costs a PR.** Batched: one PR per sync run, not per
  field. The PR carve-out in the FMP law is per-REPO, not per-path, so docs repos
  get no exemption and this was checked rather than assumed.
- 🚩 **6 of 36 registry rows have `Repo` unset**, so they have no snapshot
  destination at all. Unchanged over 14 hours of this design. They must be
  assigned or the sync has to refuse them by name.

=============================================================================
## 7. Builds never break on metadata
=============================================================================

Every disagreement is **inventory in the build report**, reusing the mechanism
already accepted for the authoring lint: a named list, grouped, no exit code.

| Condition | Result |
| --- | --- |
| ClickUp and file disagree on a standard field | ClickUp wins, page publishes, listed |
| PageID missing, task id hits | resolves, warns slug is stale |
| both ids miss | treated as unregistered; sync creates the row |
| `status` unmappable | page renders **unlisted**, build green |
| `type` unmappable | falls back to `page`, reported |
| snapshot absent | build uses the frontmatter in the file, reports that it did |

⭐ THAT LAST ROW IS THE SAFETY PROPERTY WORTH PROTECTING: **the repo alone must
always be buildable.** A content repo that cannot render without a ClickUp pull
has traded the portability that is the entire point of the content/engine split.

=============================================================================
## 8. Refused alternatives, with the evidence
=============================================================================

🚫 **Last-edited-wins.** Michael proposed it; refused on measurement. Timestamps
exist per-FILE (git) and per-TASK (ClickUp), never per-FIELD. Per-line
`git blame` dates reset on any whole-file pass, and two shipped inside 36 hours
(PR #206 across 28 pages, the 22-file `REPO_PAGES → POLICIES` move). Both would
have read as *Michael edited every field on every page*, handing ClickUp the
whole file.

🚫 **A generated "end matter" block committed at the foot of each page.** The
separation of lanes was right and is kept (§2 top-of-file is the authoring lane).
Committing the block was refused: 607 pages means 607 mirror pairs, which is the
rot `registry.json` and `roster.json` were retired for. Then superseded entirely
-- the page foot already renders Related, Keywords and *Revised*, so title,
summary, related and revised are **already displayed**, and type, order, status
and PageID are machinery a reader has no use for. There is no footer to render.

🚫 **A dedicated metadata repo.** It would keep the data-only PR carve-out and
it cannot leak into a published site. It also divorces metadata history from
content history, which is the one thing §6 exists to preserve.

🚫 **Live fetch at render time.** Build-time snapshot instead. A site that cannot
build offline is not an archive.

=============================================================================
## 9. The pilot: `template-docs`
=============================================================================

Same pilot repo as the `related:` migration, and for better reasons here.

- ⭐ **Zero rows registered today.** The 36 rows are `uritp-safety` 24,
  `uritp-docs` 6, unset 6. So this pilot exercises **registration** -- the
  one-way door, the only path that writes to ClickUp -- rather than merging into
  rows that already exist. That is the risky half, tested where it is cheap.
- **30 markdown files, zero PII, no readers.** It is the engine's own gold
  standard, served from the engine's Pages.
- **`template-docs` is already a `Repo` dropdown value**, so the snapshot has a
  destination with no field edit.
- ⚠️ **4 files have no `id:` and are the edge cases, not the happy path:**
  `README.md` (no frontmatter at all), `theatre/index.md` and
  `theatre/stage-management/index.md` (**zero-byte**), and
  `theatre/stage-management/callboard-headers.md` (body only). The sync must
  **refuse each by name** and create nothing. A registration pass that invents a
  row for a zero-byte file is the failure mode this pilot exists to catch.

### Pass criteria, in order

1. **Dry run first, writing nothing.** Report what it WOULD create, per file.
2. Row count created equals markdown files carrying an `id:`, and the four
   id-less files appear in a refusal list.
3. Every created row carries PageID, Repo, FileType and the mapped PageType.
4. Re-run the sync: **zero rows created, zero fields changed, no commit.**
   Idempotency is the thing most likely to be wrong.
5. Change one title in ClickUp, sync, build: the file's `title:` follows and the
   H1 mismatch is reported (the engine does not reconcile those for you).
6. Hand-edit that `title:` in the repo, build: ClickUp still wins, page
   publishes, disagreement listed, exit code 0.
7. Set a row's PageStatus to `draft`: page renders **unlisted**, build green.
8. Delete the snapshot, build: site still renders from file frontmatter, and the
   report says the snapshot was missing.

🔴 **Not one of these runs against `uritp-docs` until all eight pass.** 36
registered rows against 607 markdown files in that tree means registration there
is a bulk row creation, and ClickUp rows are far harder to unwind than a branch.

=============================================================================
## 10. Not built, and what it waits on
=============================================================================

- **`docrender/clickuppull.py`** -- claimed by a sibling session with the
  interface `pull_view(src, view_override) → Rows(columns, rows, pulled_at,
  transport)`, spec'd in `specs/view-snapshot.md`, **nothing written**. The
  registry merge is its SECOND caller, so this spec does not get to invent its
  own transport.
- The two mapping TSVs (§4). They are the first deliverable, because the
  vocabularies cannot be reconciled in code.
- `Repo` on the 6 unset rows (§6).
- **J33 and J35** on the doc-render-engine decision log: the snapshot location,
  non-blocking builds, footer-not-bytes and the last-edited-wins refusal. Both
  blocked on the tables in J31, which refuse every body edit to that doc.
