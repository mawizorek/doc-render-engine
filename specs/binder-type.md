# binder type: a collection, split from program

🚫 **Claims no build number, deliberately** (see `next-build-spec.md`). ✅ **BUILT 2026-10-11** (§11 lists what shipped and what did not). Every owed ruling landed 2026-10-11 (Michael, §10). Workshop 2026-10-11 (Frank, Beckett, Rhys, Cleo, Finn, Skye, Enzo, Dexter, Anna), transcript on the ClickUp Agent Activity Board task *"Maestro Mira (Opus 5) · Workshop — binder vs program: the split, and bundles of programs · Oct 11"*. Supersedes `print-compose.md` §6 P1 and P2.

> Michael, 2026-10-11: *"what if i want to assemble a bundle of programs. like the scene shop technical director should have a binder of programs or one off policies or pages that are relevant to them. wonder if we can develop the split?"*

## §1 What each type is

**Program** = the thing somebody COMPLETES, in an order, and proves (`objects/program.yml`, unchanged). Its proof is a completion form.

**Binder** = the thing somebody KEEPS and consults out of order, for a role or an event. No sign-off.

**Index** = a folder's hub. Unchanged.

**The test:** does somebody sign at the end? Program. Does somebody grab it mid-call to look something up? Binder. ⭐ A page with a completion form is a program by definition, whatever it is called.

Why a type and not a flag (Frank): the test for a new type is BEHAVIOUR, not name. A training and a program behave identically, which is why `type: flow` was refused. A binder and a program do not: one owns a reading order and draws a strip on every member, the other must never touch either. A flag that switches off half a type is worse than a type. `binder.py`'s own docstring pre-authorised this: *"If a binder ever needs to be print-only, that is a new type, not a flag on this one."*

## §2 Author surface

⚠️ **Illustrative.** The Scene Shop TD binder was an example, not an owed page (Michael, 2026-10-11).

    ---
    id: binder-scene-shop-td
    title: Scene Shop TD
    type: binder
    status: public
    summary: What the scene shop technical director keeps at hand.
    export: [packet]
    chain:
      - section: "Safety"
        subtitle: "Programs you have completed"
      - program-general-safety          # expands: tab sheet, then its members
      - program-general-safety-lx
      - section: "Shop"
      - policy-shop-hours               # one-off page, stays one page
      - policy-power-tools
    ---

    ## Contents

    !!! chain

No new key. `chain:` is the one list; `nav.declared()` resolves reading orders and `collection.expanded()` resolves binders.

## §3 Rulings

**B1 · `type: binder` reuses `chain:`.** No `members:`, `includes:` or `binder:` list (Frank). ⚠️ As built: NOT added to `nav._CHAIN_TYPES`; binders have their own resolver (§11).

**B2 · The `binder:` flag RETIRES into the type, `true` AND `false`.** One deprecation cycle: a `type: program` page with `binder: true` is still offered as a composer preset and reported as deprecated; then the code path is deleted. `binder: false` is reported as a dead key. 🚫 If flag and type both survive, that is a second vocabulary for one idea (Frank, Anna).

**B3 · Expansion: PROGRAMS ONLY, ONE LEVEL.** A program id expands to [that program's own page, then its chain]. A face (`chain: "@x"`) expands as its target. A page id stays one page. 🔴 **An index id stays one page**, because expanding hubs would pull a whole folder in from one listed id (Beckett). A binder id is REFUSED and reported: one hop, the alias-of-alias law.

**B4 · Repeats: first appearance wins.** A page reached twice (a program and one of its own members, or two programs sharing a policy) appears once, at its first position; every later appearance is a `notes` line naming both positions, so a binder that reads in the wrong order says so (Beckett).

**B5 · A binder never touches navigation.** Members keep their programs' prev/next and strips. Context (Dexter, corrected 2026-10-11): `flow-context.md` rule 3 already hides footers on flow pages and `?via=` picks the active strip, so the live cost of binder-as-program was extra strips rather than stolen buttons.

**B6 · Section entries.** A chain item may be a mapping `{section: <title>, subtitle: <optional>}` instead of an id. Mirrors the ClickUp binder schema: Section Separator documents carry Title + Subtitle per binder, ordered by Sort Index (the `>COVER PAGES | SEPARATORS | INDEX` list, 2026-09-20). Legal on `binder` only; on any other type it is reported and ignored. ⚠️ Sub-sections (ClickUp has *"Staffing: Prostaff Job Descriptions"*) are just titles in v1; no `level:` key.

**B7 · Tab sheets.** An expanded program's own page is its section's tab sheet, reusing `packet.py`'s existing "program page is sheet one" behaviour. No new cover logic (Cleo).

**B8 · `export: [packet]` is legal on `binder`.** Same closed kind set (`packet.py` `_KINDS`). The packet prints the binder page, then the expanded list.

**B9 · The composer menu is generated, never declared.** Two preset groups: **Binders** (`type: binder`, plus the legacy flag for one cycle) and **Programs** (`type: program` with `export: [packet]`); every public page stays in the list below them. No `print-menu:` key.

**B10 · Leak and emptiness rules are inherited unchanged.** Public members only, refused and named. Zero resolved members means not offered and reported.

**B11 · Cross-site: RULED, same-site only in v1.** Chains resolve per site; a binder bundles only pages built on its own site. No host decision is owed, because the TD binder was an example (Michael, 2026-10-11).

**B12 · "Copy as binder" emits `type: binder`.** Shipped in the same PR as B1 (Enzo).

## §4 OUT of v1, by name

1. Role or audience tags that generate binders (`audience: td`). The reverse direction under another word.
2. Binder in binder.
3. Expanding index pages.
4. Per-role sites or sidebars.
5. Auto-building any binder's list. Michael authors it.
6. Cross-site bundling (B11).
7. A face (`chain: "@id"`) of or as a binder.

## §5 Touch list, as built

1. `docrender/nav.py`: `declared()` and `aliases()` skip binders; a `section:` mapping on a non-binder is reported and dropped; `BINDER` + `is_binder()` exported.
2. `docrender/collection.py` (NEW): `binders()` and `expanded()` (B3, B4, B6).
3. `docrender/binder.py`: presets by `kind`; the B2 flag report; sections carried in `binders.json`.
4. `docrender/packet.py`: `wanted()` accepts `binder` and reads `expanded()`.
5. `docrender/chainlist.py`: `!!! chain` on a binder draws `####` sections, chapters, nested members.
6. `objects/binder.yml` (NEW).
7. `assets/printcompose.js`: Binders / Programs groups (B9), section entries skipped, generator emits `type: binder` (B12).
8. `tests/test_binder.py` (NEW): 8 tests.
9. `docrender/program.py`: NO CHANGE needed (see §11).

## §6 Classification (RULED 2026-10-11)

> Michael: *"propsoe clasifaitons hold"*

By §1's test. Content changes ride the migration PRs, now that the engine has landed.

- `uritp-docs` **binder-events**: binder.
- `uritp-docs` **binder-front-of-house-procedures**: binder. FOH training is `uritp-safety` program-foh-safety (ITPSAFE-1337), on the other site, so it is NOT a chapter here (B11).
- `uritp-docs` **binder-show-program-playbill**: binder. ⚠️ "show program" collides with the type name.
- `uritp-docs` **binder-inventories**: binder.
- `uritp-docs` **program-psm-calling-station**: binder (reference at the station). Slug keeps `program-`; slugs are immutable ids.
- `uritp-docs` **program-asl-interpretted-performance**: stays `type: program` until Michael adds a form or says otherwise.
- `uritp-safety` **binder-emergency-handbook-spac**: PROGRAM (completion form ITPSAFE-1336). Drops the flag; slug stays.
- `uritp-safety` **program-foh-safety**: program (form ITPSAFE-1337, packet). Drops the flag.
- `uritp-safety` **binder-put-in-rehearsal**: binder.

## §7 Migration worklist (from code search, not a census)

- `binder: true` on `type: program`: the files in §6 carrying it. Binders switch type; programs drop the key.
- `binder: true` on `type: page`: **REMOVE (Michael, 2026-10-11).** `uritp-docs` event-tech-setup, event-tech-pre-flow, event-tech-sessions, event-dress-rehearsal, event-rehearsal-last-todd; `uritp-safety` program-emergency-response.
- `binder: false`: `uritp-docs` program-asl-interpretted-performance, program-psm-calling-station. Remove.
- ⚠️ A search for the WORD binder in `uritp-safety` also hit `app/index.md`, `index.md`, program-spac-access, program-rehearsal-proper-attire, program-general-safety-lx, program-general-safety-rehearsals, policy-documentation-pipeline. Not read; key vs prose unverified. The migration PR reads each before touching it.
- ⭐ The build report now lists every remaining `binder:` key under `missing_required`, so the worklist is falsifiable after the first publish.

## §8 Not verified

- `binder-show-program-playbill` chains `report-people-production`; its `views:` key is `report-people-production-staff`. Dead id or different namespaces; no build report read.
- No MkDocs build was run. `tests/test_binder.py` passes against the real module code with stub `state`/`util`; `node --check` passes on `printcompose.js`. First real run = next publish.
- The composer itself has had no browser run since 2026-09-28 (`print-compose.md` §5).

## §9 Acceptance (Anna)

1. Every live `binder:` key accounted for by name in the build report. ✅ Built (B2 report); needs a publish to read.
2. ✅ Michael's classification ruling recorded (§6).
3. ✅ Test: a binder reuses a program's policy; the policy keeps the PROGRAM's navigation, and the binder's contents show it once.
4. ✅ Test: a binder naming a program, an index, a binder and a dead id: expands, stays single, refused, reported. ⚠️ A face member is not in the test.
5. ✅ B12 generator fix in the same PR as B1.

## §10 Rulings log

- 2026-10-11 · B11: the TD binder was *"an example"*; no host owed; v1 same-site only.
- 2026-10-11 · §7: `binder: true` on pages *"can be removed"*.
- 2026-10-11 · §6: *"proposed classifications hold"*.

## §11 As built (2026-10-11) and the deviations

1. 🔴 **Binders are kept OUT of `nav.declared()` instead of skipped by each consumer.** §5's original plan added `binder` to `_CHAIN_TYPES` and taught `_apply` and `program.py` to skip it. Skipping at the source does the same job with no consumer edits, so `program.py` is untouched and a future consumer cannot forget the rule.
2. **`collection.py` is new** because `nav.py` would have reached ~27 KB, past the read ceiling. It ships at ~21.9 KB.
3. **Section SEPARATOR SHEETS are not built.** A section draws as a `####` contents heading on the binder page and is carried in `binders.json`, but neither the packet nor the composer prints a separator sheet yet: a sheet needs a URL or a client-side render. Named follow-up.
4. **A face member of a binder** (a binder listing a program's `@` face) expands as the face's target because `declared()` returns the target's ids; untested.
5. **`binder.py` refuses non-public members only for binder presets**; program presets are already refused-and-named by `packet.py`, so a second line would double the report.
