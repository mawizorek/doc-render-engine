# BUILD 4 — splitting `visibility.py`

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-07. No code.

⚠️ **NOT YET INDEXED from `next-build-spec.md`, and the header used to claim it
was.** Corrected by the second reader: the commit that created this file added
exactly one file. The row is deferred to whoever edits that file next — it is
**22,660 B, already past its own 22 KB ceiling**, and §10d is the argument that
widening it is its own build rather than a passenger on this one. 🔴 **A claim
that is not true yet is the defect this repo hunts; an unwritten table row is
only a task.**

> Michael, 2026-08-07, after the first build report rendered on the site:
> *"Split visibility.py first, spec the seams before cutting."*

---

## 0. The read, first, because everything below depends on it

`docrender/visibility.py` is **29,648 B** at `9a74c7d`. It came back **whole** on
the git blob path this session, and every claim in this document is read out of
that source rather than recalled.

🔴 **AND THAT FACT CORRECTS SOMETHING I SAID EARLIER TONIGHT.** Refusing to edit
`README.md`, I wrote that at 25,119 B it *"cannot be read back whole."* That
inferred a **read cliff from a policy line**, and it is wrong: a larger file just
came back intact. ⚑ **The 22KB budget is a MARGIN, not an observed limit**, and
the two are worth keeping apart — the margin is still correct, because the read
ceiling is a property of the READ PATH (blob API, raw URL, an editor, whatever
comes next) and not of the file, so a number that holds on one path proves
nothing about another. The refusal was right. The reason given for it was not.

---

## 1. 🔴 Size is the TRIGGER. Cohesion is the REASON. Do not confuse them.

The build report flagged this file, which is why it is being cut. But **a cut
made to satisfy a byte count is an arbitrary cut**, and arbitrary cuts are
exactly what the Source-Size Budget Enforcer tells us to refuse.

The reason worth acting on is in the filename. **The publication gate — the thing
this module is NAMED for — is roughly a fifth of it.** Over half is the router
nav-seal, which is a routing feature that happens to run during `on_nav`. The
file holds **three concerns across two MkDocs events and three hook stages**, and
it got there honestly, one correct decision at a time.

The cut that is worth making follows the concerns. It also fixes the bytes. If
those two ever disagree, follow the concerns.

⭐ **THEY DISAGREE IN EXACTLY ONE PLACE AND THIS SECTION ALREADY SETTLED IT.**
See §11: two helpers sit on the wrong side of the seam, and moving them where
they belong makes the biggest new file BIGGER. This paragraph is the ruling, made
before the case arrived, which is the only time a rule like it is worth anything.

---

## 2. What is actually in the file

Every top-level definition, in source order, with the concern it serves.

| Definition | Concern | Stage |
| --- | --- | --- |
| module docstring | all three | — |
| `on_files` | **gate** | 02 |
| `_prune` | **tree** | 00b |
| *(routed-folders comment block)* | **seal** | — |
| `_routed` | **seal** | 00bc |
| `_nav_routed` | **seal** | 00bc |
| `_find_index` | **tree** | 00b |
| `_mark_indexes` | **tree** | 00b |
| `_index_of` | **tree** | 00b + exported to navstate |
| ~~`_title`~~ | ~~tree~~ → **seal** | ⚠️ corrected, §11 |
| ~~`_node_url`~~ | ~~tree~~ → **seal** | ⚠️ corrected, §11 |
| `_next_visible_url` | **seal** | 00bc |
| `_unchain` | **tree** | shared + exported to navstate |
| `_collect` | **seal** | 00bc |
| `_seal` | **seal** | 00bc |
| `_seal_routers` | **seal** | 00bc |
| `prune_nav` | **tree** | 00b |
| `seal_nav` | **seal** | 00bc |
| `on_page_markdown` | **gate** | 02 |

**Who imports it — verified, not assumed.** Exactly four hook shims:

| Shim | Imports | After the split |
| --- | --- | --- |
| `02_visibility.py` | `on_files`, `on_page_markdown` | ✅ **untouched** |
| `00b_unlisted.py` | `prune_nav` | repoint to `navtree` |
| `00bc_seal.py` | `seal_nav` | repoint to `navseal` |
| `00bb_navstate.py` | `_index_of`, `_unchain` | repoint to `navtree` |

Nothing in `docrender/` imports it. Every other mention across the repo is prose.

✅ **BOTH TABLES RE-VERIFIED AGAINST SOURCE BY A SECOND READER**, 2026-08-07, and
the importer list came back identical. The concern column did not — see §11.

---

## 3. The proposed cut — three modules, one per concern

| Module | Holds | Stage |
| --- | --- | --- |
| `visibility.py` *(stays)* | the publication gate: `on_files`, `on_page_markdown` | 02 |
| **NEW** `navtree.py` | the prune, and the shared tree vocabulary | 00b |
| **NEW** `navseal.py` | the router nav-seal, whole | 00bc |

⭐ **AND IT LANDS ON A STRUCTURE THAT ALREADY EXISTS: ONE MODULE PER `on_nav`
STAGE.** That is not a pattern being imposed, it is one the chain has been
asking for since the 08-05 split:

```
00b   prune   navtree.py    <- new
00bb  shape   navstate.py   <- exists
00bc  seal    navseal.py    <- new
00c   chain   nav.py        <- exists
```

Four stages, four modules, and the two that already existed were already named
this way. **The odd one out today is the file holding two of the four.**

⚠️ **`navtree` AND NOT `navprune`, DELIBERATELY.** The stage name maps better,
and the name would lie: this module also holds `_unchain` and `_index_of`, which
the seal and navstate both use and which are not the prune. Same rule `links.py`
applied when it refused to append seven image suffixes to a tuple called
`_DATA_SUFFIXES` — *"a name is a promise."* Name it for what it holds.

⚠️ **That sentence originally listed `_title` and `_node_url` here too. It no
longer can — see §11 — and the name survives the correction on the two genuinely
shared helpers that remain.** Recorded rather than silently reworded, because an
argument that loses half its evidence is worth re-reading.

---

## 4. ⭐ THE SPLIT DISSOLVES THE IMPORT CYCLE THAT FORCED THE THICK SHIM

This is the finding, and it was not why anybody asked for the split.

**Today:** `visibility` imports `navstate` (for `declared()`). `navstate` needs
`_index_of` and `_unchain`, which live in `visibility`. That is a cycle, so it is
not allowed — and `hooks/00bb_navstate.py` does the wiring by hand instead,
passing both functions in as arguments. Its docstring says so plainly: *"this
shim is thicker than the others and that is the job."*

**After:** only `navseal` needs `navstate`. `navtree` imports nothing but
`state`. So the graph is acyclic in a way it has never been:

```
state     <- everybody
navtree   <- navseal, and legally navstate
navstate  <- navseal
```

**`navstate` importing `navtree` directly becomes legal.** The constraint that
forced the hand-wiring is a consequence of the bundling, not of the design.

✅ **§11 STRENGTHENS THIS RATHER THAN THREATENING IT.** Moving `_title` and
`_node_url` out of `navtree` removes two more functions from the module that must
stay dependency-free, so `navtree imports nothing but state` gets easier to keep
true, not harder. Worth checking, because a correction that quietly broke §4
would be a bad trade.

🚫 **AND DO NOT CASH IT IN THIS BUILD.** Collapsing that shim means changing
`navstate.shape()`'s signature, and **`navstate.py` is 25,631 B — the
second-largest module in the engine and over the same ceiling this build exists
to clear.** Performing surgery on an over-budget file as a *side effect* of
splitting a different one is how a tidy-up becomes an outage.

**Repoint the shim's import. Change nothing else about it.** Record that the
collapse is now available; let whoever splits `navstate` decide whether to take
it.

---

## 5. 🔴 THE RISK THAT MATTERS: AN IMPORTERROR HERE KILLS EVERY SITE AT CONFIG LOAD

Four hook shims import this module. **An ImportError in a hook is raised while
MkDocs validates its config, before one page is read** — so `strict: false`, the
warn-never-die posture, and every `try/except` in the pipeline are all downstream
of it and none of them can help. All four sites, at once, with no page to report
the failure on.

⚑ **This has already happened here, on 2026-08-05**, when `blocks.py` imported
`_token_sets` from a `markers.py` that no longer had it. `mkdocs.yml` carries the
lesson in its own comments: a listed file that cannot import *"takes every later
hook down with it."*

**This build's version of that failure is subtler than that one.** The 08-05
outage was a caller written against a closed branch's API. Here it is a name that
changes module while a shim still points at the old one — which is a one-line
mistake that no amount of care about the *content* of the move will catch.

**Consequence for the plan:** the verification in §8 is not optional polish. It
is the build.

---

## 6. `navseal.py` will still be over the warn line, and that is the right answer

Estimated **~19–20 KB**, and **§11 adds roughly another 1 KB to it**: under the
22KB hard limit, past the 18KB warn line, and with less headroom than this
section originally claimed.

The obvious further cut is to separate **describing a node for the manifest**
(`_collect`, `_title`, `_node_url`, `_next_visible_url`) from **deciding to seal**
(`_seal`, `_seal_routers`, `seal_nav`). It is refused, and not on taste:

🔴 **`_collect` AND `_seal` ARE MUTUALLY RECURSIVE.** `_collect` calls `_seal`
when it meets a nested routed folder; `_seal` calls `_collect` to harvest a
section's children. Putting them in two modules puts a cycle between them —
**which is precisely the thing §4 just spent the whole split removing.** Trading
a real cycle for a byte count would be a bad deal made twice in one build.

✅ **RE-VERIFIED INDEPENDENTLY, 2026-08-07**, because this is the claim the whole
section rests on and "two functions call each other" is easy to assert and cheap
to check. Both call sites are in the source: `_collect` → `_seal(node, index)` in
its nested-routed branch, `_seal` → `_collect(kid, items, 1)` in its harvest
loop. The recursion is real.

So: accept it, and say so in the report rather than letting it look like an
oversight. The Source-Size Budget Enforcer's own instruction is to flag the
pathological case, not to fragment one coherent unit into arbitrary A/B pieces —
and the seal is one feature (DL J14, plus `nav: routed`), not a bag of leftovers.

⚠️ **The next honest reduction in that file is PROSE, not code.** `_seal` is
~7.5 KB and most of it is comment and report text. That is a separate decision
about how much argument a function should carry, and this build must not make it
quietly while doing something else. **§11 makes this more urgent, not less.**

---

## 7. What must NOT change

- 🚫 **`mkdocs.yml` — UNTOUCHED.** Same four `on_nav` stages, same numbers, same
  count, no new hook file. ⭐ **This is the first split in this repo that adds no
  stage**, and it is worth stating out loud: every previous one (`00bc`, `01e`,
  `01f`, `08b`) was two edits and an ordering argument. This one is neither.
- 🚫 **`navstate.py` — UNTOUCHED.** See §4.
- 🚫 **`hooks/02_visibility.py` — UNTOUCHED.** Both symbols it imports stay put.
- 🚫 **NO RENAMES.** `_index_of` and `_unchain` stay private and stay imported
  across a module boundary by a shim. That is a real smell — the same one
  `blocks.py` was left carrying after the outage — and it is **known debt, not an
  oversight.** A pure move is reviewable by reading a diff; a move plus a rename
  is not. Precedent: BUILD 2 Piece C shipped as a pure move eight hours ago.
- 🚫 **NO BEHAVIOUR CHANGE OF ANY KIND**, which is what makes §8 possible.

⚠️ **§11 IS A MOVE, NOT A RENAME OR A BEHAVIOUR CHANGE**, so it does not breach
any line above and does not weaken §8. Two functions land in a different file;
not one caller, signature or byte of logic differs.

---

## 8. ⭐ Verification: a pure move must produce a BYTE-IDENTICAL site

The strongest available test, and it is free.

1. Build one instance at HEAD. Keep `site/`.
2. Build the same instance on the branch.
3. **Diff. Any difference at all is a defect.** Not "looks right" — identical.

⚠️ Exclude the build stamp, which carries a timestamp by design. Nothing else has
licence to differ.

Then the import checks, which are what §5 demands:

- Import each of the three modules on its own.
- **Import all four hook shims**, because that is what MkDocs does, and it is the
  step that would have caught the 08-05 outage.
- Assert the five exported names resolve: `on_files`, `on_page_markdown`,
  `prune_nav`, `seal_nav`, and the `_index_of`/`_unchain` pair.
- Assert `navtree` imports nothing but `state`.

🔴 **IMPORT THE REAL MODULES. DO NOT REIMPLEMENT THEM IN A TEST.** The 08-05
post-mortem is one sentence long and it is the whole rule here: *"a test that
reimplements its subject tests the reimplementation."* That test passed while the
import it was supposed to prove had never once executed.

And **read the byte sizes back** rather than quoting §9.

---

## 9. Files and sizes — ⚠️ ESTIMATED, NOT MEASURED

Derived by summing the source read in §2. **Every one of these is a guess about a
file that does not exist yet**, and §11 moves roughly 1 KB from `navtree` to
`navseal` after these were written.

| File | Now | After (est.) |
| --- | --- | --- |
| `docrender/visibility.py` | 29,648 B | **~6 KB** |
| **NEW** `docrender/navtree.py` | — | **~6–7 KB** |
| **NEW** `docrender/navseal.py` | — | **~20–21 KB** ⚠️ over the warn line, §6 |
| `hooks/00b_unlisted.py` | 1,333 B | +0, one import line |
| `hooks/00bb_navstate.py` | 1,531 B | +0, one import line, plus §10 |
| `hooks/00bc_seal.py` | 1,460 B | +0, one import line, plus §10 |
| `hooks/02_visibility.py` | 1,333 B* | **untouched** |
| `README.md` | 25,119 B | one module-map entry becomes three |
| `hooks/README.md` | 5,032 B | one paragraph names two modules |
| `mkdocs.yml` | 10,137 B | **untouched** |

\* not re-measured this session.

🔴 **DO NOT QUOTE THIS TABLE.** This repo's own history on the point: a size table
in `next-build-spec.md` was wrong within 48 hours and **had changed an
instruction rather than just a figure**; seven size claims on 2026-08-01 were
wrong on arrival, one of them inside the sentence documenting the pattern.
**Measure at the moment you act.**

⚠️ **AND THIS TABLE HAS NOW BEEN EDITED ONCE BEFORE ANY CODE EXISTS**, which is
the warning above proving itself inside its own document.

---

## 10. 🚩 Found while reading. Flagged, not fixed.

**a. `hooks/00bb_navstate.py` carries live doc rot.** Its docstring says *"00b
prunes unlisted pages **and seals routed subtrees**"* — the seal moved to 00bc on
2026-08-05. `00bc_seal.py` says the opposite, correctly, three files away.
**Fix it in this build**, because the split has to edit that line anyway, and the
commit that moves a thing is the only one that still remembers where it was.

**b. `hooks/00bc_seal.py` will be falsified BY this build.** *"Thin on purpose:
`visibility` owns the prune and the seal both, so there is nothing to wire across
modules here."* After the split they are two modules. **The conclusion survives —
the shim stays thin, one symbol from one module — but its stated reason does
not.** Rewrite the reason, keep the claim.

**c. The five-stage `on_nav` chain is written out in full in at least three
places**: `visibility.seal_nav`, `hooks/00b_unlisted.py`, and `mkdocs.yml`, with
`00bb` carrying a stale partial and `00bc` pointing at it. 🚫 **The split must not
add a fourth full copy.** Each new module's docstring POINTS at the chain. A
fourth copy of a five-line ordering law in a repo that has retired three
manifests for exactly that shape would be an unforced error.

**d. 🔴 THE SIZE BUDGET DOES NOT WALK THIS REPO'S OWN MARKDOWN, AND THAT IS WHY
NOBODY NOTICED THE README.** `sizecheck._ENGINE_SOURCE` is `docrender/*.py` plus
`assets/*.css|.js`; the markdown half of `_scan_sizes` walks `DOCRENDER_CONTENT`,
which is the CONTENT repo. So the engine repo's own `README.md` (**25,119 B**),
`next-build-spec.md` (**22,660 B**), `hooks/README.md` and everything in
`specs/` are **unbudgeted and unreported.** Two of them are over the ceiling right
now, and `next-build-spec.md` has to warn about **itself, in prose**, in its own
header — which is a hand-maintained check standing in for a mechanism.

⚑ **This is the assets/ hole of 2026-08-04, one directory over, and it was found
the same way: by somebody citing a warning that could never have fired.** That
entry's conclusion applies here unchanged — *"an unenforced rule is a rule that
survives only as long as everybody remembers it, which is not a mechanism."*

🚫 **Not fixed here, and deliberately not**: widening the scan is a change to
`sizecheck.py` that would report several files at once and belongs in its own
build, not riding inside a refactor of a different module. But it is the reason
the README got to 25 KB unremarked, and it will do it again.

**e. And it is why this spec is not indexed.** The header claim was corrected
rather than the row added: `next-build-spec.md` is past its own ceiling, the
budget cannot see it, and inflating it further inside a refactor spec is the
exact side-effect surgery §4 refuses. The row goes in when that file is next
opened deliberately.

---

## 11. ⚠️ AMENDMENT — two helpers are on the wrong side of the seam

Added by a second reader, 2026-08-07, before any code existed.

**`_title` and `_node_url` are filed in §2 as shared tree vocabulary. They are
not shared.** Every caller of either is in the seal half:

| Helper | Called by | Concern of every caller |
| --- | --- | --- |
| `_title` | `_collect`, `_seal` | seal |
| `_node_url` | `_next_visible_url` (twice) | seal |

Nothing in the prune, in `prune_nav`, or in the pair exported to `navstate`
touches either one.

⭐ **AND THE RULE THAT DECIDES IT IS ALREADY WRITTEN DOWN, IN `state.py`, ABOUT
ITSELF:** *"EVERY VALUE HERE NEEDS A WRITER AND A READER IN DIFFERENT HOOKS. That
is the admission price… If a value is only ever touched by one module, it belongs
in that module."* That rule got `REVLOG` deleted on 2026-08-04 after its reader
went away and it sat in the shared namespace *"by preference."* **Two functions
about to be placed in a shared module, used by exactly one consumer, is the same
situation caught one step earlier — before the shared copy exists rather than
four weeks after.**

🔴 **THE COST RUNS THE WRONG WAY, AND THAT IS WHY IT IS WORTH A SECTION.** Moving
them **shrinks `navtree` and grows `navseal`** — the file that is already past the
warn line and the one thing about this plan anybody would want to make smaller.
Roughly 1 KB, in the wrong direction, to satisfy a placement rule.

⭐ **§1 SETTLED THIS BEFORE THE CASE AROSE:** *"The cut that is worth making
follows the concerns. It also fixes the bytes. If those two ever disagree, follow
the concerns."* This is the disagreement, and it arrived within one reading of the
rule being written. **Keeping two seal-only helpers in `navtree` to protect a byte
count would be precisely the arbitrary cut §1 exists to refuse** — and it would
leave `navtree` exporting vocabulary its own stage never speaks.

✅ **It costs §4 nothing** (two fewer functions in the module that must stay
dependency-free) and **breaches nothing in §7** (a move, not a rename, not a
behaviour change), so §8's byte-identical test is unaffected.

⚠️ **What it does cost is headroom**, and the honest consequence is that §6's
closing note stops being a nice-to-have: **the prose reduction in `_seal` is now
the next real decision in that file**, not a someday. Named here rather than
solved, because how much argument a function should carry is Michael's call and
not a thing to settle as a passenger on a refactor.

---

## ⏳ Rulings needed (five)

**1. Three modules, or two?** The two-way alternative is gate + everything-nav,
which leaves one ~23 KB module still over the hard limit. **Recommend three.**
The only argument for two is fewer files, and the file count is not the problem.

**2. The names.** `navtree.py` and `navseal.py`. **Recommend as proposed** — see
§3 for why not `navprune`.

**3. Accept `navseal.py` past the warn line?** **Recommend yes**, on the mutual
recursion in §6, and report it in the same commit rather than letting the next
reader find it as a surprise. ⚠️ §11 makes this ~1 KB worse; the recommendation
does not change.

**4. Pure move, or fix the private cross-module names in the same pass?**
**Recommend pure move.** §8's byte-identical test only works if nothing else
changed, and that test is worth more than the rename.

**5. NEW — §11: follow the concerns, or protect the byte count?** **Recommend
following the concerns**, per §1, which ruled on it in advance. The alternative is
defensible only if `navseal` turning out over 22 KB when measured makes the hard
limit the binding constraint — in which case the answer is the prose reduction in
§6, not a helper parked in the wrong module.

---

## Sequence, if it is greenlit

1. **Capture the before-build.** `site/` at HEAD, on one instance. Without it §8
   does not exist, and it cannot be captured after the fact.
2. **`navtree.py`** — move the prune and the genuinely shared helpers. Nothing
   imports it yet.
3. **`navseal.py`** — move the seal, including `_title` and `_node_url` per §11.
   It imports `navtree` and `navstate`.
4. **Trim `visibility.py`** to the gate, and rewrite its docstring to the gate's
   contract only.
5. **Repoint the three shims**, and fix §10a and §10b while there.
6. **Verify** — §8, all of it, before the PR exists.
7. **The two READMEs.**

🚫 **Do not start at 5.** A shim repointed before its target exists is the §5
outage, arrived at deliberately.

⚠️ **And claim the branch first.** Seven parallel-session collisions in this repo
have ended the same way: complete, correct, unmerged work that nobody could see.
**This document was the seventh** — written, committed, and sitting on an
unopened branch when a second session tried to claim the same name. The 422 is
what surfaced it, which is luck rather than a mechanism.
