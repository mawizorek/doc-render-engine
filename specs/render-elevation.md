# Renderer Elevation — close the visual quality gap with ClickUp and GitHub standard rendering

⚠️ **SCOPED, NOT GREENLIT.** 2026-10-18. Scoped by Dev Dexter.

> Michael, 2026-10-18: *"this clickup and github standard render is just like BETTER than the site renderer that we have in a lot of professionalized ways... let's define how we elevate our renderer to feel less like a plastic toy and maybe lean into the database and article aesthetic."*

One sentence: **Material for MkDocs is too visible, and it makes every site in the family read as a documentation template instead of a professional reference surface.**

Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

---

## §0 The diagnosis

The engine's architecture is sound: four-vector theming, design tokens, TSV data tables, per-site instances, print composition. The architecture DISAPPEARS when a reader opens the page, because what they see is MkDocs Material wearing a coat of paint. The sidebar tree, the header bar, the hamburger menu, the search behavior, the content column proportions, the heading rhythm — all are instantly recognizable as a Material site to anyone who has seen one.

GitHub and ClickUp built their renderers from scratch, so their rendering IS their identity. Ours is a skin on somebody else's furniture, and that is the "plastic toy" Michael named.

### What ClickUp and GitHub do that we do not

| quality | GitHub | ClickUp | doc-render-engine |
|---|---|---|---|
| **typography** | custom font stack (Mona Sans / Hubot Sans), distinct heading scale, generous line-height | custom stack, clean hierarchy | `system-ui` fallback everywhere; the font columns in the typography vector have NEVER rendered on any site (finding documented in `type.css`) |
| **content density** | wider content column, clear vertical rhythm, article-grade whitespace | knowledge-base density, good breathing room | Material's default `0.8rem` base, Material's heading scale, Material's paragraph spacing |
| **chrome** | minimal header, no left sidebar on rendered docs, content is the whole viewport | polished sidebar with icons, modern header, feels purpose-built | MkDocs sidebar tree, standard Material header, hamburger toggle — all recognizable as template |
| **code blocks** | distinct styling that feels like GitHub | clean, bordered, owned | Material's default code block shape with our background token |
| **tables** | clean hairlines, subtle alternation, data-forward | modern, bounded | **our TSV data tables are the strongest piece we have** — `data.css` and `data-list.css` already feel custom and database-forward |
| **dark mode** | designed as a first-class surface, not derived | designed, not derived | whatever maw-themes emits through Material's scheme toggle |
| **callouts / admonitions** | clean, minimal, icon-forward | polished, custom shapes | Material's admonition shape with our colour tokens via `blocks.tsv` |

---

## §1 Elevation vectors

Five vectors, ordered by leverage. Each is independently shippable.

### V1 — Typography (highest leverage)

**The single highest-impact fix.** `type.css` documents the finding in full: the three font columns in the canonical typography vector (`font-body`, `font-display`, `font-mono`) have never rendered on any site. Every heading declares `font-family: var(--dr-font-display)`, the token resolves to "Archivo" or "Chakra Petch," no stylesheet is fetched, and it falls through to `system-ui`.

**The parked ruling** (documented since 2026-08-05): two options, both real decisions.

1. **Google Fonts** — adds a third-party request to every page of a reference site read in venues on variable connections.
2. **Self-hosting** — commits font binaries to a repo that currently holds only text.

**What ships:** whichever ruling lands, the wiring is ONE line — `theme.font` in `mkdocs.yml`, or a `<link>` in `assets.py`. Everything downstream (`--dr-font-display`, `--dr-font-body`, the heading rules in `type.css`) is already built and waiting.

⭐ **The data tables already prove the point.** They render with tight, intentional type at a density that reads as database. The rest of the page renders in `system-ui` at Material's default scale. The contrast between the two surfaces IS the plastic-toy problem, visible on a single page.

### V2 — Content rhythm and density

**The problem:** `fs-body` is deliberately NOT wired (the trap is documented in `type.css` — one line makes every word 12.5% bigger because every size inside `.md-typeset` is em-relative). So our text density, heading scale, paragraph spacing, and measure are all Material's opinion about documentation.

**What "article and database aesthetic" means, measurably:**

- heading scale that creates more visual distance between H1/H2/H3
- line-height at 1.6+ (GitHub) instead of Material's tighter default
- paragraph spacing that creates rhythm instead of uniform gaps
- content column width: Material constrains to ~756px; GitHub gives more
- the lede (`.dr-lede`) already has the right idea but is fighting the surrounding rhythm

**The trap to avoid:** `fs-body` is a single-line change with a full-site blast radius. Any density change must be measured against the data tables, the spec tables, the callout boxes, the markers, and print. Upstream `bridge.tsv` already cost two reverts for exactly this shape.

🅿️ **UI/UX agent input wanted here.** "Does this heading scale feel like an article vs. a docs template" is a design judgment, not a measurement.

### V3 — Chrome polish

`specs/chrome.md` already scopes `bare` and `branch` modes for REMOVING chrome per-page. This vector is about making the chrome that STAYS feel less like a template.

**Surfaces:**

- **header:** already ours (hairline border, token-driven background). Still READS as a Material header because of shape and element arrangement.
- **sidebar tree:** the single loudest Material tell. The nested-tree-with-expanding-nodes-and-a-hamburger-toggle is recognizable from ten feet away. GitHub does not have one on rendered docs. ClickUp's is custom.
- **search bar:** Material's built-in modal. Functional, generic.
- **scheme toggle:** Material's default sun/moon switch.
- **mobile drawer:** standard Material slide-out.

**The honest limit:** the sidebar and header are Material partials. Changing their shape means either a `custom_dir` (a copy of somebody else's truth maintained forever — the defect this repo has killed three times), client-side DOM manipulation (visible flap on load), or post-render rewriting (`on_post_page`, the `navstate.py` precedent). The engine has chosen the third option before and documented why.

🅿️ **UI/UX agent input wanted here.** Which chrome surfaces contribute most to the template read, and what treatments bring them toward the article/database aesthetic without a full-custom sidebar build.

### V4 — Component restyling

**Code blocks:** Material's default shape with our `--dr-code-bg-color` token. No border treatment, no header bar, no language badge, no copy-button styling. GitHub's code blocks have a distinct border, subtle background, and clear containment that says "this is GitHub."

**Blockquotes:** Material default. No token involvement at all.

**Callout / admonition boxes:** colour-governed via `blocks.tsv` and `blocks.py` (13 families, icon system, border tokens). The COLOUR is ours. The BOX SHAPE — padding, radius, title bar proportion, icon size — is Material's admonition CSS. That shape is the template tell.

**Inline code:** Material default with `--dr-code-bg-color`. No border, no contrast differentiation from surrounding text beyond background.

⭐ **The data tables (`data.css`, `data-list.css`) are the internal benchmark.** They prove the engine CAN produce components that feel custom and database-forward. Every other component should be measured against them.

🅿️ **UI/UX agent input wanted here.** The treatment vocabulary (border weight, radius, padding, background contrast) that would make these components feel like they belong to the same design system as the data tables.

### V5 — Dark mode as a designed surface

**The problem:** dark mode is whatever the scheme toggle resolves through `maw-themes`. Material handles the switching mechanics. The quality gap between light and dark is visible on any site — dark mode is "light mode in dark colours" rather than a surface designed for its own context.

**What GitHub does differently:** distinct background values (not just inverted), adjusted contrast ratios for dark, different border treatments, code block backgrounds that separate more clearly from canvas.

**What this vector touches:** `maw-themes` colour authoring (the upstream), not the engine. The engine's token system already supports per-scheme values. The gap is in the VALUES, not the MECHANISM.

---

## §2 What is NOT in this brief

- **Navigation architecture.** Michael called the nav "a travesty" and he is right. But replacing the sidebar tree is a different scope from polishing the rendering. The chrome spec (`specs/chrome.md`) handles per-page reduction; a full nav redesign is its own project.
- **Print.** Already extensively spec'd and built. `print-*.css` is 11 files. The print surface is the most custom thing the engine produces.
- **The data table system.** It is the strongest piece we have. It is the benchmark, not the patient.
- **The theme system itself.** Four-vector theming, `maw-themes`, the token pipeline — all sound. The gap is in what the tokens LAND ON, not how they get there.

---

## §3 Sequencing

1. **V1 first.** Typography is the single highest-leverage change. It needs one ruling (Google Fonts vs. self-host) and one line of wiring. Everything downstream is already built.
2. **V4 second.** Component restyling is CSS-only, independently testable per component, and does not touch the engine's Python.
3. **V2 third.** Content rhythm changes have the widest blast radius and need the most measurement. Ship after V1 so the type stack is settled.
4. **V3 fourth.** Chrome polish has the deepest Material entanglement and the most architectural constraints.
5. **V5 last.** Dark mode quality depends on every other vector being settled.

🔴 **V1 must ship before V2 is even scoped in detail.** The heading scale, paragraph spacing, and content density all change meaning when a real font loads instead of `system-ui`. Measuring rhythm against a fallback font is measuring the wrong thing.

---

## §4 The UI/UX agent's role

This brief is scoped by Dev Dexter (engineering) and waits for the UI/UX agent being spec'd in the Throughline project. Their input is wanted on:

- **V2:** heading scale, line-height, paragraph spacing, content column width — the article feel
- **V3:** which chrome surfaces to prioritize and what treatments to apply
- **V4:** the component treatment vocabulary (border, radius, padding, background) that unifies the non-table components with the data table aesthetic

Dexter holds the mechanism (what Material will and will not let us do, what the token system can reach, what `on_post_page` can rewrite). The UI/UX agent holds the design judgment. Neither substitutes for the other.

---

## §5 The benchmark test

The brief is DONE when a reader opens one of our sites and does not think "MkDocs Material." They should think "database" or "article" or "reference surface" — something that belongs to the content rather than to the tool that built it.

That is a subjective test, and the UI/UX agent's role is to make it as measurable as possible before build begins.
