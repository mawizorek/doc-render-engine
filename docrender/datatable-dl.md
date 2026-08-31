# `datatable.py` — rationale

> Sidecar for `docrender/datatable.py`. **The module states the CONTRACT; this file holds
> the ARGUMENTS and the incidents.** Same split Michael set with `publish-dl.md`, and the
> same trigger: the module docstring had grown until the module failed the size gate it
> enforces on everybody else.
>
> Older decision history lives in the **doc-render-engine (repo) Decision Log** in ClickUp,
> blocks J4 / J5 / J7 / J17 / J20 / J21. ⚠️ That log is the claimant for those blocks; this
> file does not restate them.

⚠️ **CUT 2026-08-31 AT 27,523 B AGAINST A 22,528 B CEILING** — the by-name resolver was
written into the docstring rather than beside it, which is the fourth time in one week a
feature's reasoning has pushed its own module past the read limit (`forms.py` four times,
`buildstamp.py` three, `assets.py` once at 32,684 B). ⚑ *The tell is a docstring section
whose subject is the file it sits in.*

---

## Why data files are allowed in the content tree

"Markdown and nothing else" is a rule about **machinery** — no stylesheet, no config, no
nav manifest, no build script — so the Download ZIP hands somebody the documents and
nothing they must be told to ignore.

A table of dimmer circuits is not machinery, it **is** the documentation. TSVs stay TSV on
disk: spreadsheet-editable, git-diffable, greppable.

---

## 🔴 D1 · FINDING THE FILE — sibling, relative, or by name (2026-08-31)

> Michael, having just made a `../../production/info-dates/...` path work: *"not a huge fan
> of it but it worked"*, then, choosing between a `site.yml` registry and a tree search:
> *"i just be sure to never name tsv that same. that's my pref for now."*

Three forms, tried in this order:

| declared | resolves | status |
|---|---|---|
| `audio-inventory.tsv` | beside the page | unchanged |
| `../../production/x/dates.tsv` | relative to the page | unchanged |
| `dates-big-love-run-crew.tsv` | anywhere in the tree | **new** |

### ✅ The first two are ONE test, and the order is the compatibility guarantee

`posixpath.normpath` collapses `..` itself, so a declared path naming a real file wins
before the index is consulted. His two live pages keep working with no edit, and a page can
still **pin** one specific file by path when two share a basename.

### ⚠️ A registry was the other candidate and HE refused it, on the honest objection

> *"so i still have to register the tsv somewhere else then?"*

Yes. A `site.yml` map trades counting separators for bookkeeping and **removes no step** —
it makes a brand-new TSV a two-file edit where today it is one line. ⭐ The offer had been
framed as strictly better and it was not; his one-sentence objection found the cost the
pitch had skipped. The search removes the step entirely.

### 🔴 The cost he accepted, which is why it must fail LOUD

Two TSVs with the same basename in different folders. `_locate` reports **every** path it
found and refuses — not the shallowest, not the first, not the nearest.

**A silent choice between two files is the one outcome that could publish the wrong dates
on a call sheet.** He accepted unique naming as the price of the feature, so the moment
that assumption breaks he has to be told rather than served a coin flip. Standing polarity;
`sheet.apply_options` carries the long-form version.

### ⭐ It needed no new hook event and no `mkdocs.yml` edit

`on_page_markdown` **already receives `files`.** The index is built from a parameter that
was there all along.

⚑ Same shape as `runfoot.py`'s finding hours earlier — *the blocker was on the shape I
assumed, not on the outcome I wanted.* It matters because `mkdocs.yml` is **28,158 B** and
past the write cap, so a new hook has been an unavailable write for weeks. Two features in
two days have now routed around that debt instead of waiting on it.

### ⚠️ Built from `files`, not by walking `docs_dir`

MkDocs' own collection is what the build actually knows about — it honours `exclude_docs`
and anything else that pruned a file, so a TSV MkDocs is **not shipping** cannot be
resolved into a download that would 404.

### ⚠️ The index is cached against the `files` OBJECT, not its `id()`

`mkdocs serve` rebuilds in-process, so a grow-only module dict would carry a deleted page's
TSV into the next build — the trap `qr.PENDING` documents and clears at `on_config`.
Holding the reference makes the identity test **true** rather than probable; `id()` can be
recycled.

### 🔴 A declared PATH that misses does NOT fall through to the search

It is reported and refused. A path is an authoring statement with one specific answer, and
quietly finding a same-named file somewhere else would **hide the typo** rather than report
it — turning a one-build fix into a wrong table nobody questions.

---

## 🔴 D2 · Resolution returns a SITE PATH, never a filename

This is the 2026-08-04 download trap one resolution step further out.

That bug: the download link was a 404 on every non-index page while the comment beside it
asserted a bare filename was correct — under `use_directory_urls` a page at `lighting/x.md`
serves from `lighting/x/` while its TSV stays a sibling. Fixed by routing through
`util.relative_url`, the helper that fixed the same class of bug in `links.py`, `router.py`
and `revlog.py`.

🔴 **A TSV found elsewhere in the tree downloads from ITS OWN folder, not the page's.** So
the href must be built from where the file **is**. Handing `href_for` a bare name would
have made every by-name download a 404 **while the table on the page rendered perfectly** —
the same looks-fine-reads-broken shape as the original bug.

⚠️ **Do not go back to a bare filename, and do not count separators.**

### ⚠️ And the first draft of this feature carried a real bug of exactly that family

`_locate` was written referencing `state.DOCS_DIR`, **which does not exist** — the docs
directory reaches this module as `config["docs_dir"]`, per-build, through the hook
signature. It would have raised on the first page carrying a `data:` slot.

⚑ *An attribute invented on a module you did not re-read is indistinguishable, in your own
diff, from one that is there.* Caught by reading the write back rather than by a render.
The fix threads `docs_dir` in as a parameter, which is also the honest shape: resolution
depends on the build's config and should say so rather than reaching for a global.

---

## D3 · `align:` is a LAYOUT option and is popped before `sheet.apply_options` sees it

Added 2026-08-29, on the `!!! qr align=` precedent one module over. Every **other** option
on the block reshapes the DATA — `sort`, `pin`, `hide` — and `sheet.apply_options`
validates them against its own `KNOWN_OPTIONS`, reporting anything it does not recognise.

⚠️ **Leaving `align` in that dict would report it as an unknown option on every table that
used it** — correctly, because it IS unknown to that validator. `sheet.py`'s contract is
*"everything BEFORE the HTML... it emits no HTML and imports nothing that does"*, and
alignment is presentation. Adding it to `KNOWN_OPTIONS` would break that contract for a key
the module has no use for.

⭐ So it is popped and handed straight to `table.draw`. Two vocabularies, one indented
option block, and the seam is written in all three files. ✅ Verified by executing the parser
against eight option sets, including `align: middle` (reported and dropped) and
`algin: center` (still caught by sheet.py as an unknown key).

🚫 **No `left`.** It is what a table already does, and an option that produces the current
rendering is a dead control indistinguishable from one that failed to resolve.
`assets/align.css` states that rule at length.

---

## D4 · Slot vocabulary: empty means anything goes

Slot names belong to the TYPE (`objects/<type>.yml` → `data_slots`); an undeclared key is
reported — **but only if that type declares any.**

An empty `data_slots` list means UNRESTRICTED, ruled by Michael 2026-08-06 (*"empty means
anything goes"*), so a page on `page`, `procedure`, `standard`, `venue` or `space` may use
any slot name it likes and nothing is reported.

🔴 **Live example, and the reason the guard reads `legal and slot not in legal`:**
`01-utility/automatic-revision-log.md` in uritp-docs is `type: page` and runs slot `revlog`,
which no type declares. Deleting those two words is a cleanup that looks like one character
and would put every page on five types into the build report in a single commit.

The full argument, and the warning about what adding a FIRST slot to a type costs, is in
`objects/_base.yml` under DATA SLOTS.

⚠️ `_slots_for_type` walks `state.TYPES` itself rather than reading `meta["_spec"]`,
because `objects._resolve` merges only requires/optional/renders. Folding `data_slots` into
that merge is the right end state and is a named follow-up; until then this is the one
place the chain is walked twice.

---

## D5 · One frontmatter form, and why the old one is reported by name

A slot is always a map with `file:`. The old list form is **reported**, because an ignored
key looks exactly like the feature never having worked.

⚠️ The embed carries **no** label; the mention carries one because a sentence needs words.
`data` is a reserved admonition type.

---

## D6 · The renderer never learns what device it is on, and cannot

MkDocs builds one file and Pages serves those same bytes to every reader — there is no
request, no viewport, no user agent at build time.

So `table.py` marks **roles** and `assets/data.css` restructures at read time with a
**container** query. One artifact, so a phone and a laptop cannot disagree about what the
data says; and a container query rather than a viewport one because a table is a component,
so it answers to the space it is given and not to the size of the glass.

---

## D7 · Failure posture, and what is deliberately not provided

Warn, render without the broken part, publish, report. **Never raise, never fail a build
over a cosmetic typo.** `sheet.apply_options` carries the argument for why an ignored option
is reported rather than silent, and it is the most important paragraph in this feature.

🚫 **NOT PROVIDED:** filters, totals, renames, computed columns. Those edit the data, and
the sheet is the source of truth. `hide` is allowed because dropping a column from a VIEW
does not change what the sheet says. ⚠️ The one exception, deliberately narrow and argued in
`table.py`, is that a `money` cell is padded to two decimals.

⚠️ `pin:` emits markup the stylesheet does not yet honour. The sticky rule is held until
the older frozen-column claim is verified on the deployed site. Shipping CSS onto an
unverified mechanism is the same silent failure one layer up.

⚠️ **`PLACED` is populated before any cell is rendered**, and the order is the point: a
cell may itself contain `[x](@data:other_slot)`, which `cells.render` resolves through
`links.py`, which reads that map. Filling it afterwards would make a same-page reference
resolve as broken on the first table and fine on the second — an ordering bug that reads as
a typo.

⚠️ A declared-but-unembedded slot is **not** quietly appended at the page foot. A table
silently landing at the bottom of a long page is the failure nobody notices for a month,
and that fallback was the second legal path this feature's rewrite removed.

---

## Honest limits

- ⚠️ **A spreadsheet cannot read a marked cell as a number**, and nothing here can fix that
  (Decision Log J17). Markup cannot reorder a sheet either — `sheet.sort_within_sections`.
- 🔴 **The by-name search is only as safe as unique basenames.** The engine reports a
  collision rather than guessing, but it cannot tell you a name is *about* to collide when
  somebody adds a file next week. The report is the whole guard.
- ⚠️ **None of this is verified against a live build.** The resolution order and the
  ambiguity report were read back from the written file, not rendered — `mkdocs` is not
  installed in this environment. First real build on `uritp-docs` is the test.
