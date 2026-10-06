# `views:` snapshot: the rows of a shared view, as text you can take with you

⚠️ **SCOPED 2026-10-06, NOT GREENLIT.** No build number, on purpose: see the numbering debt in [`../next-build-spec.md`](../next-build-spec.md). Workshopped and audited (Audit Anna ↔ Maestro Mira, three passes, PASS) on the Agent Activity Board session task *"Dexter + Anna ↔ Mira · views: snapshot"*. Per-voice reasoning lives there, not here.

🔴 **READ THIS FIRST: unless Spike A or B (§6) succeeds, A SNAPSHOT OUTLIVES ITS SHARE.** Revoking a public share kills the iframe. It does not kill rows already rendered into a static page or a CSV. The floor in §4 makes that visible every build; it does not make it untrue.

---

## §1 The ask, and what it is really for

> Michael, 2026-10-06: *"there's no way for someone to 'export' the table view themselves to get the list of names as text for themselves. or exporting house report data... can we build this into the editor or have clickup views print better?"*

**True purpose (Anna, confirmed pass 3):** the people who need this data (whoever compiles the playbill, the PM filing house numbers) are not workspace members, so the embed shows them rows and gives them no way to take the rows with them. **The deliverable is portable text. Print is a side effect.**

Why ClickUp cannot fix it: view export (CSV/Excel) is a logged-in member feature. Public share and embed viewers get none. An iframe prints blank (views-dl D9).

First pages: `uritp-docs` → `production/binder-show-program-playbill.md` (four people views) and `app/app-foh-report.md` (*House Reports by Production*).

## §2 The authoring contract

```yaml
views:
  foh-summary:
    src: https://sharing.clickup.com/36074068/l/h/6-901325963601-1/9822dab00b3de9e
    text: House Reports by Production
    snapshot: true
    view: 6-901325963601-1   # optional; only when the id parsed from src is wrong
```

✅ **That is the whole surface.** `snapshot: true` plus an optional `view:` override. Nothing else in v1.

⭐ **THE VIEW IS THE SPEC** (Cleo). Columns, column order, sort and filters come from the ClickUp view. Want a names-only list for a playbill? Make a one-column view and share it. Want the house report without money? Make a second share view without those columns. No `columns:`, no `names_only:`, no engine-side picker: D6 (*the engine emits STRUCTURE, the author decides CONTENT*) pointed at ClickUp, where the author already decides it.

## §3 What renders

| Surface | Output |
|---|---|
| Screen | The iframe, as today. The snapshot table's screen visibility is **parked on Michael** (§7). |
| Paper | The snapshot table prints where today only the fallback URL does. The iframe stays hidden on paper (D9 untouched). No new print CSS expected; needing any is a smell. |
| File | One CSV per slot, **UTF-8 with BOM**, emitted into the built site under `/_snapshots/`, **never committed to any repo**. |
| Stamp | A bare `<time datetime>` element carrying the pull time. No surrounding words. |
| Link label | The CSV's filename, slugged from the slot (`foh-summary.csv`). A filename is structure, not copy. |
| Caption | The slot's own `text:`, exactly as the fallback link uses it. No default (D7). |

Rendering rules: the view's columns in the view's order; task name rendered once; a grouped view carries the group as a **leading column** (sub-summary / break rows are out of v1); a wide table scrolls inside its own box at 390px, never page-wide. Snapshot CSS is emitted inline by `snapshot.py` (`forms._RESET_CSS` / views-dl D9 precedent) because `assets/flow.css` is past the read ceiling.

🔴 **A snapshot is a MIRROR, never a source of truth** (Dara). It reproduces whatever the view shows. A wrong view produces a confidently wrong printable list.

## §4 Revocation and exposure (the risk that hurts a real person)

🔴 **Invariant (Rhys): a snapshot failure can never make a page worse than it is without snapshots.** Every failure degrades the slot to today's iframe + fallback link.

**Ladder, top rung that works wins:**
1. **Share transport** (Spike A). Rows read through the public share itself. Revocation kills the snapshot **by construction**, and no ClickUp token is needed in CI.
2. **API transport + liveness check** (Spike B). A share that answers as revoked refuses the snapshot with a dead marker.
3. **Floor, two mechanisms, not a procedure:** (a) the header of this file says a snapshot outlives its share; (b) **every build report lists every live snapshot** (page, slot, view, row count, transport) in a `snapshots` bucket. Revoking means removing `snapshot:` and rebuilding, and the register makes a forgotten snapshot impossible to miss.

One Access Tracking Decision Log row per snapshot, same as view-embed §2 recommends per share.

**Crawlers, honestly:** GitHub Pages cannot send `X-Robots-Tag`, and `noindex` meta does not apply to a CSV. `/_snapshots/` gets a `robots.txt` Disallow, which stops polite crawlers and nobody holding the link. ⚠️ The CSV holds exactly what the public share already shows: **it adds durability, not new exposure.** The FOH money columns are the real problem, and the fix is the author's money-free view (§2).

## §5 Code shape

- **`docrender/clickuppull.py`** (new, shared). One interface: `pull_view(src, view_override) → Rows(columns, rows, pulled_at, transport)`, with `share` and `api` backends behind it. **This slice ships it first; the report-renderer build (session task *"ClickUp-record report renderer"*, Oct 6) is its second caller** and uses only `api`, because it needs relationships a share cannot give. Snapshot rendering needs never leak into it. API backend: `GET /v2/view/{id}` for columns, `GET /v2/view/{id}/task` paged; the view's own filters, sort and grouping apply server-side, which is why views-dl's *"two sources behind one element"* objection no longer holds. What remains is the time gap, already ruled (Michael 2026-08-11: *"real time with a tap i have to do is real time enough for me"*).
- **`docrender/snapshot.py` + `docrender/snapshot-dl.md`** (new). Mechanism in the module, the why in the sidecar from day one.
- **`docrender/views.py`** gets one delegation call, the way `forms.py` delegates to it (views-dl D2). Zero edits to `mkdocs.yml`, `instance.py`, or any file past the ceiling.
- **`report.py`** gains the `snapshots` bucket.
- Pull once per view per build, paged; never once per render.

## §6 Gates (each fails the SLOT, never the build)

**Before any code:** Spike A (can a build read rows through the share URL's token alone?) and Spike B (does a revoked share answer distinguishably?). No repo writes; findings to the session task.

1. View id parsed from `src` ≠ Get View's id → dead marker naming the slot and `view:`.
2. A visible column missing from returned tasks → report line naming it.
3. A formula column returns no value → report line; cell renders empty, **never 0**.
4. Column order checked against the live FOH view by eye, once. Mismatch → correct this spec, not a code workaround.
5. An accented name round-trips through an Excel double-click. Fail → merge blocked.
6. Grouped view renders the group column; an ungrouped view gets none.
7. API 401 / 429 / 500 or share failure → dead marker + report line + iframe still renders + **zero rows from any cache**.

By hand, after build: Chrome print preview (WeasyPrint lies about `display: revert`, views-dl D9) and a 390px check on the FOH page.

## §7 Parked on Michael (rulings, not gaps)

1. Is the published uritp site public? Gates the FOH snapshot.
2. Which account owns the CI token if Spike A fails? A personal token reads everything Michael can, including student records. Least privilege recommended.
3. FOH: a money-free share view for the snapshot, or keep income?
4. Screen: snapshot table visible on screen (inside a `<details>` labelled by `text:`), or print + CSV only?

## §8 Out of v1

Clipboard button (JS; selecting text works) · sub-summary / break rows (the report renderer's job, Fiona C2) · relationship hops · per-column formatting · a names-only mode (make a view) · any cache of old rows · `snapshot:` options beyond `view:`.

## §9 Roads not taken

A new `!!! table` directive (second claimant on how a view appears; Frank) · its own API client in this slice (second pull in one engine on the same day; Frank) · an engine column picker (Cleo) · cached rows on failure (Beckett) · committing CSVs to the content repo (Dexter, `maw-prose` eb63e88).
