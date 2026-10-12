# binder type: a collection, split from program

🚫 **Claims no build number, deliberately** (see `next-build-spec.md`). ⚠️ **SCOPED, NOT GREENLIT.** Workshop 2026-10-11 (Frank, Beckett, Rhys, Cleo, Finn, Skye, Enzo, Dexter, Anna), transcript on the ClickUp Agent Activity Board task *"Maestro Mira (Opus 5) · Workshop — binder vs program: the split, and bundles of programs · Oct 11"*. Supersedes `print-compose.md` §6 P1 and P2 once built.

> Michael, 2026-10-11: *"what if i want to assemble a bundle of programs. like the scene shop technical director should have a binder of programs or one off policies or pages that are relevant to them. wonder if we can develop the split?"*

## §1 What each type is

**Program** = the thing somebody COMPLETES, in an order, and proves (`objects/program.yml`, unchanged). Its proof is a completion form.

**Binder** = the thing somebody KEEPS and consults out of order, for a role or an event. No sign-off.

**Index** = a folder's hub. Unchanged.

**The test:** does somebody sign at the end? Program. Does somebody grab it mid-call to look something up? Binder. ⭐ A page with a completion form is a program by definition, whatever it is called.

Why a type and not a flag (Frank): the test for a new type is BEHAVIOUR, not name. A training and a program behave identically, which is why `type: flow` was refused. A binder and a program do not: one owns a reading order and draws a strip on every member, the other must never touch either. A flag that switches off half a type is worse than a type. `binder.py`'s own docstring pre-authorised this: *"If a binder ever needs to be print-only, that is a new type, not a flag on this one."*

## §2 Author surface

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

No new key. `chain:` is the one list and `nav.declared()` the one resolver, now with a fifth consumer.

## §3 Rulings

**B1 · `type: binder` reuses `chain:`.** Added to `nav._CHAIN_TYPES`. No `members:`, `includes:` or `binder:` list (Frank).

**B2 · The `binder:` flag RETIRES into the type, `true` AND `false`.** One deprecation cycle: a `type: program` page with `binder: true` is still offered as a composer preset and reported as deprecated; then the code path is deleted. `binder: false` is reported as a dead key. 🚫 If flag and type both survive, that is a second vocabulary for one idea (Frank, Anna).

**B3 · Expansion: PROGRAMS ONLY, ONE LEVEL.** A program id expands to [that program's own page, then its chain]. A face (`chain: "@x"`) expands as its target. A page id stays one page. 🔴 **An index id stays one page**, because expanding hubs would pull a whole folder in from one listed id (Beckett). A binder id is REFUSED and reported: one hop, the alias-of-alias law.

**B4 · Repeats: first appearance wins.** A page reached twice (a program and one of its own members, or two programs sharing a policy) appears once, at its first position; every later appearance is a `notes` line naming both positions, so a binder that reads in the wrong order says so (Beckett).

**B5 · A binder never touches navigation.** `nav._apply` skips binder srcs the way it already skips faces; `program.py` draws no binder strip. Members keep their programs' prev/next and strips. Context (Dexter, corrected 2026-10-11): `flow-context.md` rule 3 already hides footers on flow pages and `?via=` picks the active strip, so the live cost of binder-as-program is extra strips rather than stolen buttons. The trap is latent, not fired (Anna checked the FOH, ASL and PSM chains: no shared ids).

**B6 · Section entries.** A chain item may be a mapping `{section: <title>, subtitle: <optional>}` instead of an id. Mirrors the ClickUp binder schema: Section Separator documents carry Title + Subtitle per binder, ordered by Sort Index (the `>COVER PAGES | SEPARATORS | INDEX` list, 2026-09-20). Renders as a heading in the contents list and as a separator sheet in the packet and composer. Legal on `binder` only; on any other type it is reported and ignored. ⚠️ Sub-sections (ClickUp has *"Staffing: Prostaff Job Descriptions"*) are just titles in v1; no `level:` key. ⚠️ This widens what a chain item may be, which Frank flagged; accepted because a separator page per heading is file sprawl against the REPO_PAGES flattening.

**B7 · Tab sheets.** An expanded program's own page is its section's tab sheet, reusing `packet.py`'s existing "program page is sheet one" behaviour. No new cover logic (Cleo).

**B8 · `export: [packet]` is legal on `binder`.** Same closed kind set (`packet.py` `_KINDS`). The packet prints the binder page, then the expanded list with section sheets in place.

**B9 · The composer menu is generated, never declared.** Three groups: **Binders** (`type: binder`), **Programs** (`type: program` with `export: [packet]`), **All public pages**. No `print-menu:` key. A preset whose members are not on this site is shown disabled with the reason, never silently dropped.

**B10 · Leak and emptiness rules are inherited unchanged.** Public members only, refused and named. Zero resolved members means not offered and reported.

**B11 · Cross-site: OPEN.** Chains resolve per site. `uritp-docs` and `uritp-safety` build separately, so a binder can bundle only pages built on its own site. `xref`/`@peer:id` bundling is OUT of v1. ⏳ **Michael's ruling owed:** which site hosts the Scene Shop TD binder.

**B12 · "Copy as binder" emits `type: binder`.** `assets/printcompose.js` currently emits `type: program` + `binder: true`; it is a GENERATOR of the old shape and ships in the same PR (Enzo).

## §4 OUT of v1, by name

1. Role or audience tags that generate binders (`audience: td`). The reverse direction under another word.
2. Binder in binder.
3. Expanding index pages.
4. Per-role sites or sidebars.
5. Auto-building any binder's list. Michael authors it.

## §5 Touch list (Finn)

1. `docrender/nav.py`: `binder` in `_CHAIN_TYPES`; `_apply` skips binders; new `expanded(src)` (B3, B4); section mappings pass through `declared()` and are skipped by `_apply`.
2. `docrender/program.py`: no strip for binders.
3. `docrender/binder.py`: read the type; deprecated-flag path for one cycle (B2); sections into `binders.json`.
4. `docrender/packet.py`: `wanted()` accepts `binder` and reads `expanded()`.
5. `docrender/chainlist.py`: nested contents for program members, headings for sections (Cleo).
6. `objects/binder.yml`: NEW, or the type fails validation the day it lands (Enzo).
7. `assets/printcompose.js`: B9 groups, B12 generator. ⚠️ ~22 KB against the read ceiling (`print-compose.md` C2); a split may be owed first.
8. `nav._stragglers`: skip binders, which cross folders by design (Enzo).
9. `specs/authoring-lint.md`: add the type before that build, not after.

## §6 Proposed classification (NOT RULED)

By §1's test. Each is Michael's call; the build flips nothing without it (Rhys).

- `uritp-docs` **binder-events**: binder (one guide per event, consulted when it comes up).
- `uritp-docs` **binder-front-of-house-procedures**: binder. Box office policies are reference; FOH training already exists as `uritp-safety` program-foh-safety (ITPSAFE-1337), which is a chapter candidate only if B11 resolves.
- `uritp-docs` **binder-show-program-playbill**: binder (a working tool). ⚠️ "show program" collides with the type name.
- `uritp-docs` **binder-inventories**: binder.
- `uritp-docs` **program-psm-calling-station**: binder (reference at the station).
- `uritp-docs` **program-asl-interpretted-performance**: program if a completion form is added, else binder.
- `uritp-safety` **binder-emergency-handbook-spac**: PROGRAM (completion form ITPSAFE-1336). Drops the flag; slug stays.
- `uritp-safety` **program-foh-safety**: program (form ITPSAFE-1337, packet). Drops the flag.
- `uritp-safety` **binder-put-in-rehearsal**: binder.

## §7 Migration worklist (from code search, not a census)

- `binder: true` on `type: program`: the eight files in §6 carrying it.
- `binder: true` on `type: page`, already ignored by the engine today: `uritp-docs` event-tech-setup, event-tech-pre-flow, event-tech-sessions, event-dress-rehearsal, event-rehearsal-last-todd; `uritp-safety` program-emergency-response. Meaning unknown; Michael to say.
- `binder: false`: `uritp-docs` program-asl-interpretted-performance, program-psm-calling-station.
- ⚠️ A search for the WORD binder in `uritp-safety` also hit `app/index.md`, `index.md`, program-spac-access, program-rehearsal-proper-attire, program-general-safety-lx, program-general-safety-rehearsals, policy-documentation-pipeline. Not read; key vs prose unverified.

## §8 Not verified

- `binder-show-program-playbill` chains `report-people-production`; its `views:` key is `report-people-production-staff`. Dead id or different namespaces; no build report read.
- `binder-inventories`, `binder-events` vs `uritp-safety` first-aid overlap: not checked.
- The composer itself has had no browser run since 2026-09-28 (`print-compose.md` §5).

## §9 Acceptance (Anna)

1. Every live `binder:` key accounted for by name in the build report.
2. Michael's per-page ruling on §6 recorded before any content file changes type.
3. Test build: a binder reuses a General Safety policy; that policy keeps the PROGRAM's strip and navigation, and the binder's contents show it once.
4. A binder naming a program, a face, an index, a binder and a dead id: expands, expands, stays single, refused, reported.
5. B12 generator fix in the same PR as B1.
