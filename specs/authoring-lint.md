# Authoring lint: catch prose that won't render the way it was written

⚠️ **SCOPED, NOT GREENLIT.** 2026-10-09. Indexed from [`next-build-spec.md`](../next-build-spec.md). No build number, per that file's standing recommendation.

> Michael, 2026-10-09, after a checkbox list inside a callout printed as literal `- [ ]`: *"check for other prose to css faults in the docs."* Then, once the sweep and the fixes landed: *"how do we keep this from piling up again?"*

---

## Why this exists: one sweep, real numbers

On 2026-10-09, every `.md` file in `uritp-docs` went through an LLM read against a fault rubric. Fixes shipped in `uritp-docs` **#205** (the PSM callouts) and **#206** (28 pages).

- **Real faults, confirmed by reading the source:** about 60, across 41 files.
- **False positives thrown out:** 43 in the first pass, plus about 10 more found while fixing. Those included cards blurbs, `[](@id)` empty labels, tab indents, lone `~`, and nested lists that were already correct.
- **Wrong fixes made by the fixer and reverted inside #206:** two.
  - Emergency Handbook quotes were moved from 3 to 4 spaces, which **breaks** them.
  - A "fix" for `4.` list start numbers turned out to be unnecessary, because Python-Markdown honours them.

🔴 **That last part is the whole argument for this spec.** A reader that *models* the parser got the parser wrong twice in one evening, in both directions. CALLOUTS.md already wrote the law down: ***a test that reimplements its subject tests the reimplementation.*** So this lint must not be a second Markdown parser written as regexes over source. **It checks what the real parser actually emitted.**

The faults that were real, by how often they appeared:

| Class | Seen | What the reader sees |
|---|---|---|
| List with no blank line above it | ~17 | `- [ ]` / `- item` printed as text, run into the line above |
| Callout opener malformed (no type, unclosed or curly title quote, body under 4 spaces) | 7 | `??? "example" ...` printed as a paragraph, and the body falls out |
| Indented list with nothing to nest under | ~3 | a grey code box full of dashes |
| `<word ...>` in prose | 3 | the text **vanishes**: the browser receives it as an unknown tag |
| Broken link punctuation (`]  (`, `((url`, missing `[`) | 5 | literal brackets |
| Sub-items indented 2–3 spaces | 3 | children flatten into the parent list (on a choking first-aid page) |
| Lettered `a.` sub-steps in a list item | 2 pages | one run-on paragraph |
| Unresolved git merge markers | 1 page | `<<<<<<< Updated upstream` on a live page |
| Empty page | 2 | a blank page in the nav |

---

## The design: symptoms first, source second

### Layer 1: SYMPTOM scan on rendered HTML. This is the ground truth.

`on_page_content` gets the HTML Python-Markdown actually produced. Every real fault above leaves a **fingerprint in the output** that a correct page never has. Detecting the fingerprint needs no model of the parser at all.

Scan text nodes **outside `<pre>`, `<code>` and the report's own block**:

| Id | Fingerprint in output | Catches |
|---|---|---|
| `glued-list` | a `<p>` or `<li>` text with a newline followed by `- `, `* `, `+ `, `\d+. ` or `[ ]` | lists glued to a paragraph, lettered-step run-ons are NOT this (see `run-on`) |
| `dead-callout` | a `<p>` whose text starts `!!! ` or `??? ` | malformed openers, every variant at once |
| `dead-quote` | a `<p>` text with a newline followed by `&gt; ` | quotes indented 4+ inside a list item (the 2026-10-09 mistake) |
| `link-debris` | `](` or `]  (` or `((http` in text | broken link punctuation |
| `attr-debris` | `{.` or `{:` in text | an attr_list or marker with no element to attach to (`{.gap} at line start`, `[x]{.}`) |
| `ghost-tag` | an element whose tag name is **not a real HTML element** and not one this engine emits | `<true>`, `<defintinely ...>`, `<Base Production>`: swallowed text |
| `code-list` | an indented-code `<pre><code>` (no fence class) whose first line starts `- ` or `* ` | a list that became a code box |
| `conflict` | a line that is exactly `=======`, or starts `<<<<<<< ` / `>>>>>>> ` | merge markers |
| `run-on` | `<p>` or `<li>` text containing a newline followed by `[a-z]\. ` or `[ivx]+\. ` | lettered sub-steps folded into one paragraph |

⭐ **Why this beats a source lint:** `dead-quote` fires on the 4-space version and stays silent on the 3-space version *because that is what the parser did*. Both of tonight's wrong fixes would have been caught by the next build, rather than by luck.

⚠️ **`ghost-tag` needs an allow-list, and it is the one check with a real failure mode.** The allow-list is the HTML living-standard element list, plus SVG/MathML, plus custom elements containing a hyphen. A legitimate `<kbd>` must never fire. A hyphenated name is always a custom element by spec, so it is always allowed.

### Layer 2: SOURCE checks. Only where HTML cannot see the fault.

Three faults leave no fingerprint, because the parser "succeeds" at the wrong thing:

| Id | Source rule | Why HTML can't see it |
|---|---|---|
| `flat-nest` | a `- ` / `N. ` line indented 1–3 spaces directly under a list item | it renders as a valid sibling item, so the output is well-formed and wrong |
| `empty-page` | nothing after the frontmatter except whitespace or comments | an empty page is valid HTML |
| `conflict` (again) | merge markers in source | they can sit inside a fence or comment and never render |

🔴 **Read `page.file.abs_src_path` from disk, never the in-flight `markdown`.** Every earlier hook rewrites the markdown (markers, figures, links), so line numbers drift and some syntax is already gone. The source file on disk is the only thing the author actually wrote, and it makes the hook's **position in `mkdocs.yml` free**.

---

## Where it reports

A new bucket `authoring` in the build report: **a finding, not inventory**. Every entry is a page rendering differently from how it was written.

Entry shape: `<src path>:<line or ~> · <check id> · <the offending text, ≤80 chars>`. Layer 1 has no source line, so it reports the nearest heading instead: `cards.md § Shape`.

⚠️ **TWO EDITS, SAME COMMIT, PER `report.py`'s OWN WARNING.** Declare the bucket in `state.reset()` and label it in `report._LABELS`. A bucket declared in one and not the other is collected all build and printed nowhere. Place it **after `dead_links`**, because a glued list often explains a dead link below it (cause before symptom).

🚫 **Never fails the build.** Warn-never-die, same as every other content finding. `strict: false` stays.

---

## Files

| File | Change |
|---|---|
| **NEW** `docrender/lint.py` | both layers, the allow-list, the opt-out reader |
| **NEW** `hooks/0Xx_lint.py` | shim. Its slot is free (see Layer 2), but it must import **both** `on_page_content` and `on_page_markdown` — the `hooks/07` cautionary tale |
| `docrender/state.py` | declare `authoring` |
| `docrender/report.py` | label `authoring` |
| `mkdocs.yml` | one registration line |
| `template-docs` `authoring/writing.md` | **one rule in the authoring guide:** *a list needs a blank line above it.* That one bug was over a third of the real faults. Same session, per CALLOUTS.md's "the last row does not derive from the first" |

🚫 No file sizes quoted, per this repo's standing lesson. Measure at HEAD when you act.

---

## Verification: run the real parser, or it doesn't ship

Fixtures live in `tests/lint/`, rendered through **Python-Markdown with this repo's actual `markdown_extensions` list**, never a hand-picked subset. Every check gets one **breaks** fixture that must fire and one **fine** fixture that must stay silent. The fine fixtures are mostly tonight's false positives:

- 3-space `   > quote` under `1.` (fine) vs 4-space (fires `dead-quote`)
- `4. Fittings` alone (fine: renders `<ol start="4">`)
- `- item:` then 4-space `    - child` with no blank line (fine: a proper nest)
- tab-indented callout body (fine)
- `!!! cards` blurb indented 6 (fine: `cards.py` re-indents it)
- `[](@id)` empty label (fine: `linklabels.py` fills it)
- a lone `~70%` (fine: subscript needs a closing `~` and no spaces)
- a fenced block quoting `- [ ]` and `!!! tip` (fine: inside `<pre>`)

🔴 **The fixture suite is the spec's real deliverable.** A check that has never seen its own false positive will produce one.

---

## ⏳ Rulings needed

1. **Opt-out for specimen pages.** `01-utility/callouts.md`, `markers.md` and the authoring pages show broken syntax on purpose. **Recommend:** frontmatter `lint: off` (whole page) or `lint: [ghost-tag]` (named checks). Reported as inventory, so an opt-out is visible and never silent.
2. **First build is loud.** Six sites, never linted, will print a backlog on the first run (uritp-docs is mostly clean after #206). **Recommend:** ship it loud. A finding that is real is not noise, and a grace period is a switch nobody turns off.
3. **Does `run-on` belong?** Lettered steps folding into a paragraph is ugly, not broken, and the fix (hard breaks) is a style choice inside verbatim imports. **Recommend:** keep it, but as **inventory**, so it is listed without making a build unclean.
4. **Peer sites.** `maw-prose`, `template-docs`, `theatre-docs`, `hml-docs` build through the same engine. **Recommend:** they get it for free, because the hook is engine-side. Nothing to opt into.

## 🅿️ Futures (not in v1)

- A one-line **fix suggestion** per entry (`add a blank line above line 26`). Easy to add once the checks are proven, but unproven suggestions are how tonight's wrong fixes happened.
- A `--lint-only` CLI over a content repo with no full build.
- Feeding `authoring` counts into the Actions step summary (BUILD 2 Piece A's third caller).
