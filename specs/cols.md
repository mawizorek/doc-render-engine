# BUILD 7 — `!!! cols`, a real directive for side-by-side blocks

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-31. Indexed from `next-build-spec.md`.

> Michael, 2026-08-31, after two run-crew date tables shipped side by side via a hand-written wrapper: *"I'm definitely going to need a better way to implement and write these, because that's too many to remember, but we'll simplify it if this looks good."* Then: *"Draft the `!!! cols` directive as a build spec."*

---

## What already shipped, and why this build exists

The side-by-side layout is **already live** and this build changes nothing about how it looks. What shipped on 2026-08-31 was:

- `.dr-cols` in `assets/align.css` — a `flex-wrap` rule, position-free, no new asset registration (commit `d312943`).
- An **author-written wrapper** on the page: `<div class="dr-cols" markdown="1">` around two `!!! data` blocks, resolved by `md_in_html` exactly as `figure.py` relies on it (uritp-docs `prod-xp.md`, PR #166).

That wrapper is the thing to retire. It is raw HTML in a markdown file, it depends on the author remembering `markdown="1"` (omit it and the inner `!!! data` blocks ship as literal text), and it is precisely the class of hand-authored structure the engine everywhere else replaces with a directive. **This build promotes the working CSS to a first-class `!!! cols` block, on the exact `!!! qr` / `!!! form` precedent.**

🔴 **THE CSS DOES NOT CHANGE. This is an AUTHORING build, not a layout one.** `.dr-cols` is proven; the deliverable is a nicer way to emit the same `<div class="dr-cols">`.

---

## The shape

```
!!! cols
    !!! data "runcrew-p1"
    !!! data "runcrew-p2"
```

renders as

```html
<div class="dr-cols">
  <div class="dr-data" id="data-runcrew-p1">…</div>
  <div class="dr-data" id="data-runcrew-p2">…</div>
</div>
```

— byte-identical to what the hand wrapper produces today, so the live page is unchanged the moment the author line is swapped.

⭐ **Children are ANY block, not just `!!! data`.** Two QR codes, two forms, a table beside a callout — the wrapper does not care and neither should the directive. It groups; it does not inspect.

---

## 🔴 The one hard problem: this directive WRAPS other directives, and nothing else here does

`!!! qr`, `!!! form`, `!!! data` each match a single line and replace it. `!!! cols` has to contain **indented child blocks that are themselves directives**, and those children are consumed by different hooks at different stages:

- `!!! data` → `01b_data`
- `!!! form` → `05b_program`
- `!!! qr` → `03e_qr`

So `!!! cols` cannot render its children itself — it does not own them and must not learn to. **It has to emit the wrapper `<div>` and leave the children in place for their own hooks to find, on their own passes.** This is the whole design question, and there are two ways to do it.

### Approach A — markdown rewrite, earliest stage (RECOMMENDED)

A hook at the FRONT of the pipeline (before `01b`) rewrites

```
!!! cols
    <indented block>
    <indented block>
```

into the literal HTML wrapper with the children **dedented back to column zero inside it**:

```html
<div class="dr-cols" markdown="1">

!!! data "runcrew-p1"

!!! data "runcrew-p2"

</div>
```

Then every downstream hook runs exactly as it does today — `01b_data` finds its `!!! data` lines, `03e_qr` finds its `!!! qr`, all unaware they now sit inside a div. **This is literally what the author types by hand today, generated instead of remembered.** The engine already trusts this exact structure in production.

⚠️ **The catch is the dedent.** The children are indented under `!!! cols` (that is how the block groups them), and `md_in_html` needs them at column zero inside the `<div markdown="1">` or they render as an indented code block. So the rewrite strips the block's indent from each child line. That is a line-oriented transform on an indented run — the same shape `datatable._collect_blocks` already does, and it should be read for the fenced-code guard (`sub_outside_code`) so a page DOCUMENTING `!!! cols` does not rewrite its own example.

### Approach B — emit paired HTML sentinels, reassemble late

Emit `<div class="dr-cols">` where the block opens and `</div>` where it closes, leaving children untouched in place, and let them render normally between the tags. 🚫 **Recommend against.** An open tag and a close tag emitted as two separate string substitutions, with other hooks editing the lines between them, is exactly the fragile shape `figure.py` refuses when it re-emits the image byte-identical rather than wrapping it in separately-emitted tags. One stage that produces a complete wrapper beats two that produce half each.

---

## ⏳ Rulings needed

**1. Options: `gap`, `align`, column count?** The live rule hardcodes `gap: 1.5rem` and `flex: 1 1 20rem`. The minimal directive takes NO options and inherits those. **Recommend: ship optionless first.** A `gap=` or `min=` option is a clean follow-up once the directive exists, and every option added now is one guessed before anyone has felt the default wrong. `align=` is already a solved pattern (`util.directive_options`) if it earns its way in.

**2. The `flex-basis` breakpoint — is `20rem` right?** Below ~20rem per column the blocks wrap to stacked. That number was a guess under time pressure and has not been tuned against real content on a phone. **Recommend: verify on the live `prod-xp` page across widths and set it once here, in the same PR.** Two 3-row date tables are the reference case.

**3. Does an empty or single-child `!!! cols` warn?** A one-block `cols` is a dead wrapper — the same dead-control shape `align.css` refuses with `.align-left`. **Recommend: a single child renders normally and is REPORTED, not failed** (the engine's standing posture: warn, render, publish). Zero children is an authoring mistake and is reported too.

**4. Nesting.** `!!! cols` inside `!!! cols`. **Recommend: out of scope, and reported if attempted.** The reference case is two tables in a row; nested grids are a real feature with real pagination questions and belong in their own build.

---

## Files (measure at HEAD, never quote)

| File | Change |
|---|---|
| **NEW** `hooks/01a_cols.py` | the rewrite hook. Runs BEFORE `01b_data`. Registered in `mkdocs.yml` — two edits, the file and the line. |
| **NEW** `docrender/cols.py` | `_collect_blocks`-style parser + the dedent + the wrapper emit. Its own module, never appended to `datatable.py`. |
| `assets/align.css` | 🔴 **UNTOUCHED.** `.dr-cols` already exists and is correct. This is the proof the build is authoring-only. |
| `mkdocs.yml` | one hook registration, and 🔴 its run-order comment updated — `01a` must precede `01b`, and that dependency is exactly the kind this file documents. |
| `template-docs authoring/writing.md` | a row teaching `!!! cols`, so authors read it instead of copying the raw `<div>` from a page. |

⚠️ **REGISTRATION IS THE FIRST-CLASS RISK, per `assets.py`'s own scars.** A hook in `hooks/` absent from `mkdocs.yml` does nothing; a stage misordered after `01b` means `!!! data` runs before the wrapper exists and the children never get grouped. The run-order comment block in `mkdocs.yml` is where that gets written, not discovered.

---

## Sequence

1. `docrender/cols.py` — the parser + dedent + emit, unit-testable against a fixture string with no build.
2. `hooks/01a_cols.py` + the `mkdocs.yml` registration and run-order note.
3. Swap `prod-xp.md`'s hand `<div class="dr-cols">` for `!!! cols` — the migration and the proof in one, and the live page must render byte-identical after.
4. `writing.md` authoring row.

🔴 **Definition of done: the author writes `!!! cols` with indented children and never types raw HTML or remembers `markdown="1"` again — and the rendered bytes match today's hand-wrapped page exactly.** If the output differs, the rewrite is wrong; the CSS is not in question.

---

## Decision history

doc-render-engine (repo) — Decision Log subpage in ClickUp. This build is the promotion of the 2026-08-31 `.dr-cols` hand-wrapper (uritp-docs PR #166, engine commit `d312943`) to a directive.