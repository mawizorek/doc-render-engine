# BUILD 7 — the `views:` registry: embed ANY ClickUp view by NAME

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-28. Rewritten 2026-08-29. Indexed from [`next-build-spec.md`](../next-build-spec.md) as **BUILD 7**.

> Michael, 2026-08-28: *"could i embed a clickup TABLE VIEW into one of my doc renderer pages??? like embedding a clickup form on the safety site but doing a custom clickup table view to embed instead."* → **live**, not build-time.
>
> Michael, 2026-08-29, correcting the scope of this document: *"i want to know how to embed any clickup view in one of my pages. let me decide what actually gets rendered. i gave you an example for a tool i wanted. focus on the tool."*

🔴 **THIS IS A TOOL SPEC. IT DOES NOT DECIDE WHAT GOES ON A PAGE.** The v1 of this file argued about which surface deserved a live embed and shipped a ruling asking Michael to choose between derived and live. **That was scope creep dressed as diligence: he asked for a capability and got an architecture review of his content.** The capability is general — any view type, any list, any page — and the author decides what to render. Constraints below are stated as **properties of the mechanism**, never as gates on his choice.

**One-line summary:** a page names a shared ClickUp view in frontmatter; the engine builds the iframe. Mechanically this is `docrender/forms.py` with a second allow-listed host.

---

## §1 HOW IT WORKS — the two halves, end to end

### Half 1: ClickUp side (once per view, by hand, and no agent can do it)

1. Right-click the view in the **Views Bar** → **Sharing & Permissions**. *(Also reachable per-item; views are the Views Bar route.)*
2. Toggle **Share link with anyone** on.
3. Copy **Embed code** from the advanced settings. That is a complete `<iframe>` string.
4. Optional in the same panel: **Share link with search engines** (leave OFF unless indexing is wanted), **Expire link** (Enterprise), and for Docs/Whiteboards **Autosize embed height**.

⚠️ **Applied filters travel with the share.** A publicly shared view carries its filters, so scoping what a reader sees is done IN the view, not in the page. **That is the mechanism by which the author controls the rendering, and it is the whole reason this tool is worth building.**

### Half 2: the engine side (once, then free forever)

```
views:
  program-index:
    src: <the shared view URL, from the embed code's src=>
    text: Available programs and their completion forms
    caption: true
    height: 48rem          # optional; see §3

    !!! view "program-index"
```

Same grammar as `forms:`, `links:` and `data:`. **A bare string is allowed as shorthand for `src:`**, exactly as `forms:` already permits.

🚫 **THE CONTENT REPO STILL NEVER HOLDS THE IFRAME.** The page NAMES a view; the engine builds the element. This is the fourth registry to follow that split, not a new idea.

---

## §2 The design: FOLD into `forms.py`. Do not write `views.py`.

`forms.py`'s own docstring makes the argument that decides this: *"A form is an EMBED — it validates a URL and emits an element."* **A shared view is the same verb.** Same CDN question, same height problem, same fallback shape, same one-script-per-page rule. A `views.py` would be a second implementation of one idea, and this repo has retired three manifests over exactly that.

One internal `_embed(url, label, ...)` serves both registries. One `slot_anchor()`. One script append **per page across both**. The registries differ in three values: the allow-listed host, the default label, and whether `Program_ID=` is checked (a **form** concern — a view has no submission to attribute).

🚫 **Do not rename the file to `embeds.py`.** The rename is cosmetically right and costs an edit to `mkdocs.yml` — **28,158 B at HEAD, past the read ceiling.** ⭐ **The fold needs NO new hook registration at all, which is half its value.** Note the wrong filename in the docstring and move on.

**Everything in `forms.py` that transfers unchanged:** the frontmatter registry, the `!!!` directive shape, `sub_outside_code` on the substitution (**non-optional** — the page documenting the directive contains the directive), the `min-height` floor, the always-rendered fallback link, and the once-per-page script append.

**What does not transfer:** `collapsed:` (a `<details>` that a fragment link opens). It exists because a program page is both entrance and exit for a *form*. Available for views if wanted, not the default — a table is usually content rather than an action.

---

## §3 THE HOST — a declared instance key, so this does NOT block

`_FORM_HOST = "https://forms.clickup.com/"` is a deliberate allow-list, not a scheme check, because this element runs a third-party script in the reader's browser. **A shared view is not on that host, so the tool needs a second value — and v1 made that a blocking ruling waiting on a pasted string. Wrong call: it blocked the whole tool on one config value.**

⭐ **Instead: the view host is DECLARED, read off `state.INSTANCE`.** `urllinks.py` already reads `links:` straight off the instance config, so this needs **zero** edits to `instance.py` (23,047 B, past ceiling) — just a read of a new key:

```
view_hosts:
  - https://sharing.clickup.com/     # whatever the real embed code shows
```

- **Declared, never guessed.** 🔴 The value goes in from a REAL embed code, once. **No agent may invent, infer or remember this string** — same rule as every other unverifiable external fact in this engine.
- **A list, so a second ClickUp surface later is a config line, not a code change.**
- 🚫 **Never a `*.clickup.com` wildcard.** That also matches `app.clickup.com`, the logged-in application — which would let a page embed a workspace URL and render a login wall to the public, looking like a broken table rather than a misconfiguration.
- **Empty or missing `view_hosts:` → the embed is refused and REPORTED** (`dead_links`), never silently dropped. The engine ships working with nothing hardcoded.

### The height question, and it is the one real unknown

The form embed leans on `class="clickup-embed clickup-dynamic-height"` plus `app-cdn.clickup.com/assets/js/forms-embed/v1.js`. **Whether that helper sizes a VIEW frame is unverified** — and `forms.py` already documents what happens when it fails: `height="100%"` with no sized parent is ~0px, so the embed is not broken, it is **invisible**.

**So the tool does not depend on the answer:**

- The **`height:` key** in §1 is a declared, real height. Use it and the helper is irrelevant.
- The **`min-height` floor** (`40rem`, as forms) is the default. A script failure degrades to a scrollable frame, never a hole.
- **If the pasted embed code carries `clickup-dynamic-height`, pass it through; if it does not, omit it.** One glance at the string decides it, and no code path changes.

---

## §4 Properties of the mechanism (NOT gates — read once, then decide freely)

These are facts about ClickUp and about iframes. They constrain what the tool CAN do, not what should be on a page.

| Property | What it means for a page |
|---|---|
| 🔴 **Non-Form views share publicly from the EVERYTHING level, Business+**; Form views share from any level on any plan | If a view's Share modal has no *Share link with anyone*, the shareable equivalent is an Everything-level view with **filters** doing the scoping. This is where a build stalls in practice, and it is a two-second check in the modal. |
| 🔴 **Public shares require third-party cookies** | Blocked by default in a growing number of browsers, and the affected reader is exactly the one not logged into the workspace. Unverifiable at build time. Mitigation is the `min-height` floor + the fallback link. **Acceptance test: load the page with third-party cookies OFF.** |
| ⚠️ **The frame carries ClickUp's own chrome** — *Sign up free* / *Login* buttons, an *Embed ClickUp* label and logo | Inside a cross-origin iframe, so it cannot be removed (both are open feature requests). `caption:` is the cheap answer: label it as live ClickUp content so the chrome reads as provenance. |
| ⚠️ **An iframe prints as a blank rectangle** | The fallback link renders **always**, not only for print — `forms.py` already does this and the reason is the print identity spec. For a form a printed link substitutes fine; for a table the content is genuinely absent on paper. Stated, not solved. |
| 🔴 **A public share is public until revoked** | The link works for anyone who has it, is indexable if that toggle is on, and Owners/Admins on Enterprise can audit every shared item under Security & Permissions. **Recommend logging each share in the Access Tracking Decision Log so it can be revoked deliberately rather than discovered.** What is safe to publish is the author's call, per view. |
| ⚠️ **A revoked or deleted share degrades to an empty frame with NO build finding** | Runtime behaviour of an external page is invisible at build time. The fallback link is the only thing distinguishing "loading" from "gone." |

---

## §5 Files and sizes — measured at HEAD 2026-08-29, read back, not estimated

| File | Now | Change |
|---|---|---|
| `docrender/forms.py` | **11,740 B** | **+3–4 KB.** Second registry, shared `_embed()`, `view_hosts:` read, `height:`/`caption:` keys. Lands ~15–16 KB, under the 18KB warn line. |
| `mkdocs.yml` | **28,158 B** | **untouched — deliberately.** No hook registration. §2. |
| `docrender/instance.py` | **23,047 B** | **untouched.** `view_hosts:` is READ off `state.INSTANCE`, never parsed per-key. §3. |
| `instances/<slug>/` config | not measured | `+view_hosts:`, one line, once per site. |
| `theme/` CSS | not measured | one `.dr-view__caption` rule. |
| `docrender/datatable.py` | 16,566 B | **untouched.** `!!! data` remains the build-time table directive; unrelated to this build. |

⚠️ **`mkdocs.yml` is recorded in `next-build-spec.md` at 13,632 B "at HEAD 2026-08-21" and is 28,158 B — a 106% drift in eight days**, on a file whose own scar reads *"a size written into prose is wrong within two days, every time, in this repo."* **Measure when you act; never quote a table.**

---

## §6 ⏳ Rulings needed (three, and none of them block reading §1)

1. **`caption:` default ON or OFF?** **Recommend ON** — the unremovable chrome needs explaining and the caption is also where "this is live" belongs.
2. **Is `views:` type-gated like `data:` slots, or universal like `links:`?** **Recommend universal.** `forms:` is type-gated because a completion form is a program-shaped idea; an embedded view is not shaped like anything.
3. **Does a view embed get a `print:` treatment beyond the fallback link?** **Recommend no**, and say so in the caption. A second, build-time copy of the same table would be a mirror that disagrees with the live one the first time a filter changes.

---

## §7 Sequence

1. **Share one view and paste the embed code.** Its `src=` host → `view_hosts:`; its class list answers the `clickup-dynamic-height` question. **One string resolves both.**
2. Fold into `forms.py`: `views:` registry, `!!! view`, shared `_embed()`, caption, report messages.
3. **Acceptance test on one page, with third-party cookies BLOCKED**, and a print preview.
4. Then use it wherever it is wanted. **Where that is, is not this document's business.**

---

## §8 Recorded, not prescriptive: the program-index example

Michael's first use case was *"a table view of all the available completion forms with their autofilled links with their program id... one source of truth filtered and displayed for public."* **The tool serves that directly and the choice is his.** Two things were found while reading the live data on 2026-08-29 and they are recorded here because they are FACTS about the data, not arguments about the design:

- 🔴 **`Program_ID=ITPSAFE-1219` is on two different programs** in Programs (canonical) — *Key & Swipe Access* and *MEWP Training, for Instructors*. Submissions from those two cannot be told apart. **A compliance defect in the record, independent of any rendering decision, and worth fixing on its own.**
- ⚠️ **`Program URL` disagrees with the site in three ways today**: two different URL shapes for one site, one 🌐 PUBLIC row with an empty URL, and one page (`30-programs/10-general/rehearsal.md`) carrying a completion form with no row at all. Whatever renders that field will render these.

⚠️ **Honest limit on the above:** read with closed tasks and subtasks excluded by default — six open non-subtask rows is what the query returned, **not a proven total.**

🚫 **No fix was attempted and none is proposed here.** Which program gets renumbered, and whether `Program URL` stays hand-typed, are Michael's calls.
