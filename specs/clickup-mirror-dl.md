# `clickup-mirror` — the arguments

**A SIDECAR, NOT A BUILD.** It holds the reasoning [`clickup-mirror.md`](clickup-mirror.md) points at, so that spec stays a readable set of rules and gates. Same shape as [`hover-text-dl.md`](hover-text-dl.md), [`print-control-dl.md`](print-control-dl.md) and [`print-packet-dl.md`](print-packet-dl.md). 🚫 It takes no row in [`../next-build-spec.md`](../next-build-spec.md) and claims no build number.

Written 2026-10-11, the same night the parent spec was scoped, because two of its
sections had already outgrown it.

---

## §A The rival design: `page-registry.md`, withdrawn unmerged

A second spec for the same relationship was written on 2026-10-11, hours after
`clickup-mirror.md` was scoped and **without the author reading
`next-build-spec.md` first.** It is recorded here rather than deleted for the
reason this repo always gives: a coherent road nobody can see gets re-walked.

### What it proposed

`>REPO_PAGES` as the **database**, not the mirror. The repo keeps prose plus two
identity lines (`id:` and `cu: MAW-####`). **Registration as a one-way door:** an
unregistered page's frontmatter IS the intake form and the sync creates the
ClickUp row from it; once a row exists, ClickUp owns every standard field and the
build **generates** them into the file from a snapshot committed into the content
repo. One field, one author, at every point in time. No reconciliation, because
authority hands over once and never comes back.

It also carried three things that survive and are now folded into the parent:
**G7**, the naming of the destination list (§4), and the `template-docs` pilot
(§12).

### The three collisions that killed it

1. 🔴 **The committed snapshot is the road `§11` already refused.** *"Committing
   the mirror as JSON in the repo. A second claimant on `/doc-index.json`"* — the
   defect that retired `roster.json`, `registry.json` and `app-index.md`. The
   rival spec argued the snapshot belongs beside content history so one `git log`
   answers both, which is a real benefit and does not outweigh a second claimant
   on a file the engine already publishes every build.
2. 🔴 **The second identity line is refused by `R1`.** See §A.1 below.
3. 🔴 **ClickUp-as-author inverts `J5`.** *Content must be in the FILE.* A field
   generated into the file at build time technically lands there, so the ZIP
   stays populated — but the authority is elsewhere, and a repo whose titles are
   only correct because a sync ran is not a repo you can hand somebody.

### §A.1 Why `R1` survived the strongest case against it

The rival design's argument for `cu:` was not the convenience one `R1` refused.
It was: **a PageID is authored and therefore fallible** — it can be retyped,
corrected, or collided — while `MAW-####` is issued by ClickUp and cannot
collide, so the task id is the trustworthy *fallback*. Resolution order would be
PageID first, task id on a miss with a stale-slug warning, failure on a double
miss. Verified live: Emergency Contacts is `MAW-2117`, and the ids are
**workspace**-sequential (1990–2117 across this list), so they are unordered
within the list and carry no sort meaning.

⭐ **It loses on DURABILITY rather than on uniqueness, and that distinction is
the keeper.** The issued id is stable only as long as the task is. Delete and
recreate a task — a thing ClickUp does without ceremony, and a thing a cleanup
pass does on purpose — and the value committed in the file is now a confident
pointer at nothing, unreportably, because nothing in the engine knows the id went
stale. The repo outlives the task.

**So: a fallible key the repo controls beats an infallible key it does not.** A
wrong `PageID` is visible in the file and fixable by the person reading it. A
wrong `cu:` is invisible everywhere.

⚠️ And the premise was never tested on the one case that matters: whether a
`MAW-####` survives a **cross-space move** is still unverified. An argument for a
fallback resting on an unverified durability claim is an argument to verify first.

### The lesson, which was cheaper than the spec

⚑ **Read the index before scoping anything.** `next-build-spec.md` exists for
exactly this, lists 27 specs with their state, and names the two-claimants defect
four separate times in its own prose. The rival spec was argued across two
sessions and withdrawn in one read.

---

## §B G7 in full: two taxonomies wearing one name

Read off the live field definitions on `>REPO_PAGES` on 2026-10-11, not inferred
from documentation:

```
ClickUp PageStatus     draft  private  public  closed  unlisted
engine status:         hidden  unlisted  gated  public

ClickUp PageType       policy program privilege handbook guide role
                       course form index media "Checklist | Table"
engine type:           page index venue space standard procedure reference
```

`status` overlaps on **two values of five**. `type` overlaps on **one word out of
eighteen**, and that word is `index`.

### Why they diverged, which is not an accident to correct

ClickUp's are **EDITORIAL** categories: what kind of document is this, inside the
program that produced it. A policy, a program, a privilege, a handbook. Those
answer *what is this for and who adopted it*.

The engine's are **RENDER CONTRACTS**: what does this page draw, and what does it
require. `space` requires `parent`; `index` draws a contents list; the rest draw
nothing. Those answer *what must be true of this file for it to build*.

⭐ **Both are correct and neither is a subset of the other.** `policy`,
`handbook` and `guide` are all `page` to the renderer, and that is not a loss of
information — it is the renderer correctly not caring. Forcing one vocabulary on
both sides would either flatten the editorial distinctions Michael actually sorts
by, or invent render contracts that draw nothing.

### The failure it would have caused, step by step

1. `R4` puts `status` on the write-back allowlist, deliberately, because
   *"promoting a batch of pages from `hidden` to `public` from a table view is
   the single most likely reason to touch frontmatter from ClickUp at all."*
2. The field an implementer reaches for to do that is `PageStatus`. It already
   exists on the destination list and it is already populated.
3. Its first option is `draft`. The engine has no such value.
4. `status:` is the engine's **only hard gate with no default and no fallback**.
   `objects/_base.yml`: *"Mandatory with no default, so a page that forgets it
   does not build. Nothing goes public by accident."*
5. So the write-back emits `status: draft` and those pages **stop building**.
6. ⚡ And the damage does not stop at those pages: every `@id` pointing at one
   renders a struck broken-reference marker on a page **nobody edited**, and the
   same happens on sibling sites resolving `@peer:id` against a
   `/doc-index.json` the pages have now vanished from.
7. The PR gate `R4` relies on does not catch it. A one-line diff reading
   `status: draft` looks exactly like a correct edit. **The gate protects against
   a bad VALUE reaching the public; it does not protect against a valid-looking
   value that is not in the engine's vocabulary at all.**

🔴 The mismatch is already in the data, so this is measurement and not
prediction: `policy-emergency-contacts` carries PageType **policy** and file
`type: page`. Nothing is wrong with that row. It is simply two fields answering
two questions, which is exactly what a naive generator would read as a conflict
to resolve.

### Why a mapping TSV rather than code

The FMP law's *"Git repo as an external data store"* convention grants a short
list of free transfers, and **mapping-table-as-data** is one of them, alongside a
`schema.json` sidecar with refuse-on-drift, deterministic sort by key and a
frozen column order. A mapping in code means a new ClickUp dropdown option
requires an engine commit, which is the shape that put `theme` colours in three
places and `router` keys in a laptop's `~/.zshrc`. A mapping in data means adding
`handbook` is a row.

⚠️ **Refuse on drift, do not widen silently.** A ClickUp option with no row in
the table stops the run and names itself. The alternative — passing an unmapped
value through — is step 5 above.

### Why the two sides of the boundary behave differently

| Side | Unmapped value | Why |
| --- | --- | --- |
| write-back (ClickUp → file) | **refuse the value, report the row** | A file is durable. A bad write is a commit somebody has to find. |
| render (file → site) | `status` → **unlisted**, `type` → `page`, build green | A build must not fail on metadata. Michael: *"you are constantly breaking builds just because we find something."* |

⭐ **That asymmetry is deliberate and worth stating:** strictness belongs where a
mistake persists, leniency belongs where it is re-run every build. The write-back
is a permanent edit and gets the refusal; the render is disposable and gets the
degradation. `type` falling back to `page` is not new behaviour either —
`objects.py` already does exactly that for an undeclared type.

🚩 **Still open:** whether `>REPO_PAGES` should grow a second column holding the
engine's render contract, so a row carries both the editorial category and the
type, and the mapping becomes a lookup rather than a translation. Cleaner at read
time, one more column maintained by hand, and it would make the two taxonomies
visibly separate rather than apparently redundant. Not decided.

---

## §C The destination list is not greenfield

`>REPO_PAGES` (list `901329123131`) held **36 rows and 18 custom fields** when
this was written, with values typed in by hand over weeks: `PageID`,
`PageStatus`, `PageType`, `Repo`, `FileType`, `✍️ Edit Link`,
`🌐 Published Link`, `GitHub Folder Name`, `Agent Assignee`, and two list
relationships.

By `Repo`: `uritp-safety` 24, `uritp-docs` 6, **unset 6**.

⚡ **So "one ClickUp task per page, matched on `id`" describes a MERGE on every
real tree, and the parent spec's "mirror columns are overwritten every build"
warning stops being theoretical.** The first run on `uritp-safety` would
overwrite 24 rows of hand-typed values with generated ones. That is the correct
behaviour for a mirror and it is also a surprise worth having in writing before
it happens once.

Three consequences, all in the parent §4:

1. **6 rows have no `Repo`**, so they match no source tree and cannot be
   reconciled with anything. Refuse by name. 🚩 Unchanged across the fourteen
   hours of this design, so this is a standing data gap rather than a race.
2. **An orphan row** — a hand-typed `PageID` matching no file in its repo — is
   `G5` arriving from the other direction and gets the same posture: report,
   never resurrect, never delete.
3. **Pilot on `template-docs`**, where the count is zero and the run is a pure
   create. 36 rows against 607 files in `uritp-docs` means the first run there
   creates hundreds of tasks, and a ClickUp task is harder to unwind than a
   branch.
