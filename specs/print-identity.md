# BUILD 5 — the print layer SPLIT, print density, and a printed IDENTITY

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-19. Requested by Michael out of the URITP Safety fire-policy print session: *"i want to adjust the print styling yes. lets split that file out if we need - but i was about to ask for a small logo potentially rendered on the top of the page or something that we define too so lets spec the printing mechanism to be a little more professional looking."* Indexed from [`next-build-spec.md`](../next-build-spec.md).

Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

---

## One line

Split `assets/print.css` at a real seam, give the paper layer **density control** it has never had, and let a site declare a **printed identity** — a small logo plus a title line — that appears on a printed page and nowhere else.

---

## 🔴 §0 — THE BLOCKING LIMIT, AND IT KILLS THE OBVIOUS DESIGN

**Michael asked for a logo "rendered on the top of the page." If "the page" means EVERY SHEET, a browser cannot do it, and no amount of CSS in this repo changes that.**

<p><br/></p>

A true running header is CSS Paged Media `@page` margin boxes:

```
@page { @top-center { content: element(letterhead); } }
```

**No major browser implements `@page` margin boxes.** Chrome and Firefox support `@page` for `size` and `margin` only — which is exactly the subset `print.css` already uses, and that is not a coincidence. Margin boxes are implemented by dedicated paginators (Prince, WeasyPrint, Paged.js), none of which is in this pipeline, and adding one is a new dependency and a new build stage rather than a stylesheet edit.

<p><br/></p>

⚠️ **AND THE FALLBACK EVERYONE REACHES FOR IS BROWSER-DEPENDENT.** `position: fixed` on a header element repeats per sheet in Firefox and prints **once, on sheet one,** in Chrome. So the same rule produces a letterhead on every page for one reader and a letterhead on page one for another, with nothing reporting the difference. **That is worse than a documented limit** — it is the silent-divergence shape this repo has logged against `em` container queries (Orion vs Blink, PR #82) and against the `bad`/`danger` token mismatch. The only other trick is wrapping all content in a `<table>` so `thead` repeats via `display: table-header-group`, which the print sheet already exploits for real tables. Wrapping a document in a table to get a header is a layout lie and it breaks `break-inside` on everything nested in it. 🚫 Refused here in advance.

<p><br/></p>

⭐ **SO THE HONEST BUILD IS A FIRST-PAGE LETTERHEAD, and it should be presented as the feature rather than as a compromise.** Every document this engine renders is ONE document; a letterhead on sheet one plus the existing build stamp at the end is how a real printed policy is laid out. **Ruling 1 asks Michael to confirm that reading before anything is written**, because if he genuinely needs a mark on every sheet, this build is a paginator evaluation and not a CSS change, and that is a different conversation with a different cost.

---

## §1 — THE SPLIT

`assets/print.css` is **22,844 B** (measured 2026-08-19, after PR #132). The repo's own ceiling is ~22 KB — the point at which a file stops coming back whole from one read and therefore stops being safely editable. `type.css`, `nav.css`, `data.css` and `chrome.css` all left `base.css` for exactly this reason and each says so in its header.

<p><br/></p>

⚠️ **IT IS COMMENT-DOMINATED, NOT RULE-DOMINATED, AND THAT CHANGES THE SPLIT.** The rules in that file are short; the reasoning is long, and the reasoning is the reason anybody can safely touch it. **A split that shortens the file by deleting argument is a regression disguised as hygiene.** Every note travels with the rule it explains.

<p><br/></p>

**The seam — and it is the one the file already argues for in its own header.** That header divides its subject into *"what appears on paper at all, how wide it runs, and where the page is allowed to break."* That is two jobs, not one:

<p><br/></p>

| File | Owns | Why it is one job |
|---|---|---|
| **`assets/print.css`** (stays) | `@page`, chrome-off, the column unrailing, the slate→light neutral overrides, `print-color-adjust`, link policy | **What the sheet IS.** Every rule here answers *what reaches the paper and how wide*. |
| **`assets/print-flow.css`** (NEW) | `break-after`/`break-inside`/`orphans`/`widows`, the h1–h6 rule, tab-label protection, the forced-open `<details>`, `thead` repetition, `{.new-page}` | **WHERE IT BREAKS.** Every rule here answers *what is allowed to be split*. |
| **`assets/print-identity.css`** (NEW, §3) | the letterhead block | A new surface, and it should not be born inside a file already over the line. |

<p><br/></p>

⭐ **THE FORCED-OPEN `<details>` RULE GOES WITH FLOW, WHICH IS NOT OBVIOUS.** It looks like a *what appears at all* rule — it makes withheld content appear. It belongs with flow because **it is the rule that creates the pagination problem the rest of that file solves**: force seven collapsed panels open and you have just invented seven new break hazards. Keeping the cause beside its consequences is worth more than filing it by its verb.

<p><br/></p>

## 🔴 §1a — THE SPLIT'S REAL HAZARD IS SOURCE ORDER, AND TWO EXISTING SPECS ALREADY WARN ABOUT IT

`print.css`'s own header states that its position is load-bearing **twice over**: it must publish AFTER the generated `tokens.css` (because its slate overrides re-point the same custom properties at the same specificity, and losing that tie prints pale ink on white paper, silently) and BEFORE an instance's `site.css` (because an instance keeps the final word).

<p><br/></p>

⚠️ **EVERY NEW SHEET INHERITS THAT SANDWICH.** Order is declared in `docrender/assets.py` (`_DATA_ASSETS`; **15,226 B** — verify the list's exact name and shape at build, do not trust this sentence). Three sheets in the slot where one used to sit means three chances to insert one in the wrong place, and **the failure mode is a blank-looking page rather than an error.**

<p><br/></p>

🔴 **AND `specs/scoped-theme.md` §4c ALREADY FOUND THE ADJACENT BUG:** *a scoped selector silently kills `print.css` on the pages it scopes, because that sheet wins on source order at equal specificity and a two-attribute scope outranks it.* **That finding was written about ONE print sheet. After this split it applies to three, and a scope could kill one and spare the others** — producing a page that paginates correctly and prints grey, or vice versa. **Whichever of BUILD 3 and BUILD 5 lands second must re-read the other's note.** Named here so neither discovers it.

---

## §2 — DENSITY: THE COMPLAINT IS CHROME, NOT FONT SIZE

> Michael: *"the callouts print in a font larger and take up so much space for such little actual content on print."*

**Verified at HEAD: nothing in this engine sizes or pads a callout.** `admonition` appears in `assets/` only in `chrome.css` (a shadow token and `--md-admonition-bg-color`) and in `print.css` (`print-color-adjust`). So callout metrics are Material's, unmodified, and **`print.css` governs breaks, width, colour and never density** — screen sizing reaches paper untouched.

<p><br/></p>

⭐ **THE DOMINANT COST IS BOX CHROME AND IT IS ARITHMETIC, NOT TASTE.** On the fire policy, four `???+` boxes each carrying ONE sentence consume roughly half of sheet one. A `???+` is a `<details>` — cheap on screen precisely because it collapses — and `print.css` force-opens all of them. **The shape chosen to make a screen read compact is the most expensive shape available on paper.** Padding, border, title bar and inter-box margin are being paid four times for four sentences.

<p><br/></p>

**Levers, cheapest and least destructive first:**

1. **Tighten callout padding and inter-box margin at print only.** Highest ratio of space recovered to risk taken. Does not touch type.
2. **Collapse the title-bar gap** — on paper the title and its one-sentence body do not need the separation a hover-able screen box uses.
3. **A print base size**, LAST, and only if 1 and 2 are not enough.

<p><br/></p>

⭐ **AND §2's THIRD LEVER IS THE ONE PLACE `fs-body` IS SAFE, WHICH IS WORTH SPELLING OUT.** `type.css` refuses `.md-typeset { font-size: var(--dr-fs-body) }` outright, and the argument is recorded there: every size inside `.md-typeset` is em-relative, so one line makes **every word on the site** 12.5% bigger — the same blast radius that forced the PR #82 bridge-row revert Michael reported as *"the font in the TABLE is massive."* **That objection is about SITE-WIDE blast radius. A declaration inside `@media print` has a blast radius of exactly one medium**, it is reversible in one line, and it is invisible to every reader who never prints. The refusal in `type.css` stands unamended and this does not contradict it — same mechanism, different scope, and the scope was the whole objection.

<p><br/></p>

⚠️ **NO NUMBER IS WRITTEN IN THIS SPEC ON PURPOSE.** Material's compiled admonition metrics have not been read this session. Quoting a rem value from recollection would be **a proxy read presented as a verification** — the exact failure logged in `instances/uritp-safety/site.yml` over the `database` theme claim, where an accurate reading of the wrong table was committed in the voice of something verified. Read Material's published stylesheet, then measure against a rendered sheet.

<p><br/></p>

🔴 **AND ONE MEASUREMENT IS FORBIDDEN TO MOVE.** `@page { margin: 12mm }` is not a margin preference, it is a calculation: the data table flips to list mode below a **640px** container, and 12mm keeps Letter at 726px and A4 at 703px. **The TOP margin is free to change** (a letterhead may want more room). **The LEFT and RIGHT margins are load-bearing** and widening them silently converts every data table on every site into a stack of key/value rows. If §3 needs vertical space, change `margin: 12mm` to a two-value form and touch only the block axis.

---

## §3 — THE PRINTED IDENTITY

A small logo plus a title line at the top of sheet one, and a site declares it.

<p><br/></p>

### 🔴 §3a — WHERE THE IMAGE FILE LIVES IS THE DECISION, NOT THE CSS

The CSS is trivial. The placement question is governed and gets answered by **audience, not by convenience** — the repo-referent rule.

<p><br/></p>

| Option | Verdict |
|---|---|
| **In the CONTENT repo**, referenced by a `site.yml` key | ✅ **Recommended.** A logo is that organisation's identity, not engine machinery. URITP's mark is not the engine's business, and six sites will not share one image. |
| **In the ENGINE repo** (`assets/`) | 🚫 Refused. It makes the engine hold one instance's brand, and the second site to want a different logo forces the refactor anyway. |
| **Inline base64 in `site.yml`** | 🚫 Refused. Binary in a config file, unreviewable in a diff, and it inflates a file every build parses. |

<p><br/></p>

⚠️ **`images.py` ALREADY SOLVES THE PATH PROBLEM AND MUST NOT BE RE-SOLVED.** It owns `@img:<name>` and resolves through `util.relative_url` — and its own docstring carries the five-level `../../../../../shared/uritp-logo.png` example as the arithmetic **this house shipped wrong three separate times** (`links.py`, `router.py`, `datatable.py`). 🔴 **A letterhead injected into a template renders at every depth in the tree, so it is maximally exposed to exactly that bug.** Read `images.py` first and reuse its resolver. Writing a fourth relative-path computation in this repo is the single most predictable failure available in this build.

<p><br/></p>

### §3b — the declaration

A `print:` block in each instance's `site.yml`, absent by default:

```
print:
  logo: shared/uritp-logo.png     # resolved through the images layer, never a raw path
  title: URITP Safety             # optional; falls back to site name
```

⭐ **ABSENT MEANS NO LETTERHEAD, AND THAT POLARITY IS DELIBERATE** — the same rule `_uses_router` already sets, where a missing `routes.yml` means the router assets are never even published. Five of six sites should print exactly as they do today until somebody chooses otherwise. **A feature that changes paper output on six sites the moment it merges is not opt-in, whatever the docs say.**

<p><br/></p>

### ⚠️ §3c — IT COLLIDES WITH THE BUILD STAMP, WHICH IS ALREADY THE PROVENANCE LINE

`print.css` keeps `.buildstamp` on paper as a deliberate, argued exception: *"a printed page leaves the system entirely — it gets handed to a guest artist, filed, carried into a room months later — and the one question nobody can answer about a piece of paper is how old it is."*

<p><br/></p>

🔴 **A letterhead that repeats the site name and date is a SECOND claimant on provenance**, and this repo has retired three manifests over exactly that shape. **Recommend: the letterhead carries IDENTITY (logo + title) and the build stamp keeps DATE, unchanged, at the foot.** They are two facts, they belong at two ends of the sheet, and neither should state the other's.

<p><br/></p>

### §3d — mechanism, and the honest unknown

The element has to be injected, which means a hook or a template partial. ⚠️ **`specs/chrome.md` already establishes that `base.html` renders the header as a bare block with no `page.meta.hide` check anywhere near it**, so somebody has already read this template tree — **read that spec before choosing an injection point rather than re-deriving it.** J29 set the precedent that editing HTML on the way out beats forking a Material partial into a `custom_dir`, because a fork is a copy of somebody else's truth that we then maintain forever.

<p><br/></p>

🚫 **AND IT MUST NOT BE VISIBLE ON SCREEN.** `display: none` outside `@media print` is the whole trick, and it is also the reason the element can be injected unconditionally without touching the screen page at all.

---

## 🔴 §4 — THIS BUILD MOVES BUILD 4's TARGET FILE

**[`specs/draft-watermark.md`](draft-watermark.md) §4 names `assets/print.css` as the home of the print DRAFT stamp** and instructs the builder to add it *"there"* beside the edit-on-git strip and the white-background rule.

<p><br/></p>

⚠️ **After this split, that instruction is wrong.** A DRAFT watermark is neither *what the sheet is* nor *where it breaks* — it is an overlay, and it most plausibly belongs beside the letterhead in `print-identity.css`, which is the sheet that owns marks laid over the paper.

<p><br/></p>

**Whichever build lands first updates the other's spec in the same PR.** ⭐ This is precisely the J29 lesson: *the commit that moves a thing is the only commit that still remembers where it was.* Neither build is blocked by the other, and the pointer rots the moment one ships alone.

---

## ⏳ Rulings needed

1. **🔴 §0 first — sheet one, or every sheet?** Blocking, and it decides whether this is a CSS build or a paginator evaluation. **Recommend sheet one.** Every other answer costs a new build dependency.
2. **Two new sheets or one?** §1 proposes `print-flow.css` + `print-identity.css`. **Recommend both** — identity is a new surface and should not be born inside a file already over the ceiling — but one combined `print-flow.css` is defensible if three print sheets in the `assets.py` order feels like more rope than it is worth.
3. **Density: how far?** Padding and margin only, or a print base size as well? **Recommend shipping levers 1–2 alone first and measuring**, because they are the reversible ones and the complaint may be fully answered by them.
4. **Should `???+` on a print-heavy page be advice rather than CSS?** The fire policy's four one-sentence boxes are a **content** shape, and no stylesheet makes four boxes as cheap as a four-item definition list. An authoring note may be worth more than a rule. Michael's call; it is about how he writes, not about the engine.
5. **`print:` block shape** (§3b) — and whether `title` is even wanted given §3c's provenance seam.
6. **Does the letterhead print on EVERY page of a multi-page data table?** Follows from ruling 1 and is worth asking separately, because a 40-row inventory is the one document where a per-sheet mark genuinely earns its keep.

---

## Files and sizes (measured at HEAD 2026-08-19 — RE-MEASURE AT BUILD)

| File | Now | Change |
|---|---|---|
| `assets/print.css` | **22,844 B** | **−8 to −11 KB.** Loses the break policy and gains the density rules. |
| **NEW** `assets/print-flow.css` | — | ~9–11 KB. Break policy verbatim, comments intact. |
| **NEW** `assets/print-identity.css` | — | ~2–3 KB. |
| `docrender/assets.py` | 15,226 B | +small. Two registrations, **in the correct order** (§1a). |
| `docrender/instance.py` | 23,047 B | ⚠️ **ALREADY OVER THE CEILING at 23,047 B.** If the `print:` block is parsed here, that is a read-whole problem before a single line is added. Check whether instance config can grow anywhere else. |
| `docrender/images.py` | 9,451 B | untouched if its resolver is reused (§3a). |
| a template partial / hook | — | letterhead injection. See `specs/chrome.md` first. |
| `instances/*/site.yml` | varies | opt-in `print:` block. **Only where wanted.** |
| `specs/draft-watermark.md` | 8,4xx B | §4 pointer correction, by whichever build ships first. |

<p><br/></p>

🔴 **THIS TABLE WILL BE WRONG WITHIN TWO DAYS. It is the house scar.** `next-build-spec.md` BUILD 1 recorded `mkdocs.yml` at 7,685 B; it is **13,632 B** today, a 77% drift, and that same table already documents `markers.py` rotting from 16,241 to 18,534 in 48 hours — which moved an *instruction*, not just a figure. **Measure at the moment you act.**

---

## Sequence

1. **Ruling 1.** Nothing starts until sheet-one-vs-every-sheet is settled.
2. **The split, as a PURE MOVE.** No behaviour change, independently reviewable, and it is the step that makes everything after it safe to write. Same argument as BUILD 2 Piece C: doing it last means writing new code into a file already past the line.
3. **Verify nothing broke.** One print preview, both schemes, Letter and A4. The `slate` override is the rule that fails silently if the order slipped.
4. **Density**, levers 1–2, measured on a rendered sheet.
5. **The letterhead.** Last, because it is the only piece that needs a new config key and a new injection point.

---

## What this build is NOT

- 🚫 **Not a paginator.** No Prince, WeasyPrint or Paged.js. If ruling 1 comes back *every sheet*, that is a separate evaluation with a separate cost, not a stretch goal inside this one.
- 🚫 **Not a colour opinion.** `print.css`'s founding rule holds: this layer is structure, and the semantic-token defect on light grounds stays upstream in `canonical/colors.tsv` where it can be fixed once.
- 🚫 **Not `fs-body` site-wide.** §2's third lever is print-scoped. `type.css`'s refusal stands unamended.
- 🚫 **Not a fork of a Material partial into `custom_dir`.** J29 precedent.
- 🚫 **Not a second provenance line.** §3c.
- 🚫 **Not a content fix.** The fire policy's own defects (a stray `!` that swallows policy 5, an interrupting callout that renumbers items 6/7/8 as 1/2/3, the `R: Relocate` label contradicting its own `Rescue` body) are real and are **not** a print problem. They belong to Michael in `uritp-safety`, which agents read and never write.
