# BUILD 7 — a `views:` registry: a live ClickUp view, embedded by NAME

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-28. Indexed from [`next-build-spec.md`](../next-build-spec.md) as **BUILD 7**.

> Michael, 2026-08-28: *"could i embed a clickup TABLE VIEW into one of my doc renderer pages??? like embedding a clickup form on the safety site but doing a custom clickup table view to embed instead."* Asked whether it should be **live** or a build-time table: **"live."**

**One-line summary:** a page names a shared ClickUp view in frontmatter, the engine builds the iframe. Mechanically this is `docrender/forms.py` with a second allow-listed host — **which is exactly why the code is the cheap half and this spec is mostly about the four things that are not code.**

🔴 **READ §10 FIRST IF YOU ARE ABOUT TO BUILD THIS.** The use case arrived a day after the spec and it is a PROGRAM INDEX, which is the one shape where three of the constraints below stop being tolerable. §10 does not cancel the build; it narrows what the build is FOR.

---

## §0 What already exists. Do not rebuild any of it.

`docrender/forms.py` (11,740 B at HEAD) already solved this problem for forms on 2026-08-19, and every hard-won piece of it transfers unchanged:

| Piece | Already in `forms.py` | Transfers? |
|---|---|---|
| frontmatter registry + `!!! form "slot"` directive | yes | **yes**, same shape |
| host **allow-list** rather than a scheme check | `_FORM_HOST` | **yes**, different constant |
| `clickup-dynamic-height` + the `forms-embed/v1.js` CDN asset | yes | ⏳ **UNVERIFIED for views** — ruling 2 |
| `min-height` floor so a script failure degrades to a scrollable frame, not a hole | `_FORM_MIN_HEIGHT = 40rem` | **yes** |
| always-rendered fallback link (print + "it did not load") | `dr-form__fallback` | **yes**, and it matters MORE here — §5 |
| `collapsed:` → closed `<details>`, opened by fragment navigation, zero JS | yes | **probably not wanted** — a table is content, not an action |
| `sub_outside_code` on the substitution | yes | **yes, non-optional** |
| script appended **once per page**, not once per embed | yes | **yes**, and now it is once per page across BOTH registries |

🚫 **THE CONTENT REPO STILL NEVER HOLDS THE IFRAME.** The rule `forms.py` opens with is untouched: the page NAMES a view, the engine builds the element. `views:` is the third registry to follow `links:`, `data:` and `forms:`, not a new idea.

---

## §1 🔴 RULING 1 — THE HOST, AND IT BLOCKS THE BUILD

`_FORM_HOST = "https://forms.clickup.com/"` is a deliberate allow-list, and its reason is stated in the file: *"this element executes a third-party script in the reader's browser on a page that carries a compliance instruction, so 'any https URL' is not a good enough answer."*

**A shared view does not live on `forms.clickup.com`.** So the build needs a second constant, and:

🔴 **THE VALUE CANNOT BE DERIVED, INFERRED, OR REMEMBERED. IT MUST BE COPIED OUT OF THE SHARE MODAL.** Not a guess with a fallback, not a regex over `*.clickup.com`, and not a value carried in from another session. **Michael pastes the `Embed code` from the view's Sharing & Permissions panel; the `src=` host in that string becomes the constant.** Everything below assumes it exists and nothing below can supply it.

⚠️ **Why a wildcard is the wrong shortcut, since it will be proposed:** `*.clickup.com` also matches `app.clickup.com`, which is the LOGGED-IN application. An allow-list that admits it invites a page that embeds a workspace URL, renders a login wall to the public, and looks like a broken table rather than a misconfiguration. **Two named hosts, no pattern.**

---

## §2 The design: FOLD into `forms.py`. Do not write `views.py`.

`forms.py`'s own docstring makes the cohesion argument that decides this: *"A strip is NAVIGATION... A form is an EMBED — it validates a URL and emits an element."*

**A shared view is also an embed that validates a URL and emits an element.** Same concern, same CDN dependency, same height problem, same fallback shape, same one-script-per-page rule. A `views.py` would be a **second implementation of one idea** — and this repo has retired three manifests over exactly that.

**The shape:**

```
forms:            # unchanged
  completion:
    src: https://forms.clickup.com/...?Program_ID=ITPSAFE-1225

views:            # new, same grammar
  training-log:
    src: <the host from ruling 1>/...
    text: Live training completion log
    caption: true

    !!! view "training-log"
```

One internal `_embed(url, label, host, ...)` builds the frame for both. One `slot_anchor()`. One script append. The registries differ in three values: the allow-listed host, the default label, and whether `Program_ID=` is checked (it is a **form** concern — a view has no submission to attribute).

🚫 **DO NOT RENAME THE FILE TO `embeds.py`.** The rename is cosmetically correct and costs an edit to **`mkdocs.yml`, 28,158 B at HEAD — past the read ceiling.** A hook path edit in a file that cannot be read whole, to fix a filename nobody is confused by, is the worse trade. ⭐ **And the fold means NO new hook registration at all, which is half its value.** Note the wrongness in the docstring and move on.

⚠️ **Size forecast, and Sally is seated at the plan rather than at the commit:** `forms.py` 11,740 B + ~3–4 KB of mechanism ≈ **15–16 KB**, under the 18KB warn line. **The risk is prose, not code.** This spec's reasoning belongs in the **doc-render-engine (repo) — Decision Log** in ClickUp, where `forms.py` already points for its own *why*. Do not paste §1–§5 into the module docstring.

---

## §3 The three ClickUp-side gates that are NOT code

All three are true of ClickUp itself, verified against the Help Center on 2026-08-28. **Any one of them can make a shipped, correct build useless.**

**a) 🔴 A non-Form view shares publicly only from the EVERYTHING level, on Business and above.** Forms publish from a List on every plan — which is why the safety site's completion form was easy. Per *Share locations and items with a public link*: Form views share from a Space, Folder, Subfolder or List; **all other views "can be publicly shared from the Everything level."** ⚠️ **This is a CONTENT-MODEL constraint, not a code one:** the tidy List-scoped table Michael is picturing may have no share toggle at all, and the shareable equivalent is an Everything-level view with filters doing the scoping. **Verify on the actual view before any code is written** — the Share modal either offers *Share link with anyone* or it does not.

**b) 🔴 Public shares require THIRD-PARTY COOKIES.** Stated in the same article. Browsers block them by default in more configurations every quarter, and the reader most likely to be blocked is **exactly the one who is not logged into the workspace** — which is every reader a public docs site has. **Unverifiable at build time**, the same reduction `forms.py` and `urllinks.py` both state at the top of their own files. The `min-height` floor and the fallback link are the whole mitigation.

**c) ⚠️ The embed carries ClickUp's own chrome and it CANNOT be removed.** An embedded view renders **"Sign up free" and "Login" buttons** plus an **"Embed ClickUp" label and logo**; both are open, unresolved feature requests on ClickUp's feedback board. On a compliance page that reads as an advertisement inside a policy document. **Recommend: accept it and CAPTION the frame** ("Live from ClickUp — updates automatically") so the chrome reads as provenance rather than as clutter. Hiding it is not on the table: it is inside a cross-origin iframe.

---

## §4 🔴 A PUBLIC SHARE IS PUBLIC, AND THE ENGINE CANNOT SEE WHAT IS IN THE TABLE

The form embed collects data from readers. **This embed publishes data to them**, and that inverts the risk.

An `Embed code` exists only once the view is toggled *Share link with anyone*. From that moment the rows are readable by anyone with the link, indexable if the search-engine toggle is on, and **the link keeps working until somebody revokes it** — Owners and Admins on Enterprise can see every publicly shared item in Security & Permissions, which is the audit surface if this ships.

🚫 **A view carrying named people — training completion, roster status, contact columns — is not a candidate.** Same class as the standing rule that a PII/FERPA judgment is never carried between repos: the safety site's repo visibility says nothing about what a ClickUp share link exposes. **The two are independent, and the share link is the more public of the two.**

**Recommend, and this is a real gate rather than a caution:** a view is embeddable only if **every visible column is already public-safe with names attached**, decided per view before the toggle is flipped, and the share is recorded in the **Access Tracking (person × target × level)** Decision Log so it can be revoked deliberately rather than discovered. ⏳ **Ruling 3.**

---

## §5 Print — the fallback link is doing more work here than it does for a form

`forms.py` already renders its fallback link on every build, not only for print, because *"an iframe prints as a blank rectangle and this engine has a print identity spec."*

**For a form, a printed link is a fully adequate substitute** — the reader was going to click something anyway. **For a table it is not: the table IS the content**, so a printed program packet carries a link where information belongs. That is a genuine loss and it should be written down rather than smoothed over.

⏳ **Ruling 4 — and my recommendation is the boring one:** do **NOT** make print render a build-time `!!! data` table as a substitute. Two sources for one table is the mirror defect this repo keeps retiring, and they would disagree the first time the ClickUp view's filters changed. **Ship the link, name the limitation in the caption, and if print fidelity turns out to be the real requirement then the honest answer was `!!! data` all along and the live embed was the wrong build.**

---

## §6 Files and sizes — measured at HEAD 2026-08-28, read back, not estimated

| File | Now | Change |
|---|---|---|
| `docrender/forms.py` | **11,740 B** | **+3–4 KB.** Second registry, one shared `_embed()`, second host constant. Lands ~15–16 KB, under the warn line. |
| `mkdocs.yml` | **28,158 B** | **untouched — deliberately.** See §2. |
| `objects/program.yml` | not measured this pass | +vocabulary for `views:`, if the key is type-gated the way `data:` slots are. ⏳ ruling 5. |
| `docrender/datatable.py` | 16,566 B | **untouched.** `!!! data` is the build-time alternative, not part of this build. ⚠️ **§10 promotes it to a candidate for the index case.** |
| `docrender/program.py` | 18,350 B | **untouched** unless `collapsed:` is wanted for views (recommend not — §0). |
| `theme/` CSS | not measured | one `.dr-view__caption` rule, if ruling 6 lands. |

⚠️ **`mkdocs.yml` IS RECORDED IN `next-build-spec.md` AT 13,632 B "AT HEAD 2026-08-21" AND IS 28,158 B TODAY — a 106% drift in seven days.** That file already carries the scar *"a size written into prose is wrong within two days, every time, in this repo,"* and it has now been proven by its own most recently corrected number. **Measure at the moment you act; never quote a table.**

---

## §7 ⏳ Rulings needed (six, plus three in §10)

1. 🔴 **THE HOST — BLOCKING.** Paste the `Embed code` from a shared view's Sharing & Permissions panel. Nothing in this build can start without it. §1.
2. **Does `forms-embed/v1.js` size a VIEW frame, or is that helper form-only?** If it is form-only, the frame has no dynamic height and `min-height` stops being a floor and becomes the height. **Recommend a fixed, declared `height:` key for views** rather than pretending the helper works. Verifiable in ten seconds from the pasted embed code — it either carries `clickup-dynamic-height` or it does not.
3. **The public-safe-columns gate in §4 — is it a rule or a caution?** **Recommend: a rule**, plus an Access Tracking row per shared view.
4. **Print.** **Recommend: fallback link only.** No second table. §5.
5. **Is `views:` type-gated like `data:` slots, or universally available like `links:`?** `forms:` chose DECLARED-not-inferred and put its vocabulary in `objects/program.yml`. **Recommend: universal**, because unlike a completion form a live table is not a program-shaped idea.
6. **Caption on or off by default?** **Recommend a `caption:` key, defaulting ON**, because the unremovable ClickUp chrome (§3c) needs explaining and a caption is the cheapest place to also carry "this is live."

---

## §8 Sequence

1. **Michael pastes one real embed code.** Ruling 1 and ruling 2 both resolve off that single string.
2. **Verify a non-Form view can actually be shared** on this workspace's plan, at the level the content wants (§3a). **If it cannot, the build stops here and `!!! data` is the answer.**
3. **One page, one view, hand-checked in a browser with third-party cookies BLOCKED** (§3b). This is the acceptance test, and it is the one that decides whether the feature is real.
4. Then the fold into `forms.py`, the caption, the report messages.

🚫 **Do not start at step 4.** Steps 1–3 are all ClickUp-side and any one of them can cancel the code.

---

## §9 Honest limits, stated up front

- Nothing here can prove a shared view is live, still shared, or renders correctly. Same reduction as `forms.py` and `urllinks.py`: **the host and the scheme are checked and that is all.**
- **A revoked share degrades to an empty frame with no build finding**, because an external page's runtime behaviour is invisible at build time. The fallback link is the only thing that tells a reader the difference between "loading" and "gone."
- **The chrome, the cookie dependency and the Everything-level constraint are all ClickUp's, not ours.** No amount of engine quality fixes any of them, and a build report that implied otherwise would be lying.

---

# §10 THE USE CASE — a public index of completion forms (2026-08-29)

> Michael, 2026-08-29: *"i'm going to make a table view of all the available completion forms with their autofilled links with their program id - then embed that as an index of available programs - instead of hand maintaining a tsv alongside the existing details. one source of truth filtered and displayed for public."*

**The goal is right and the target is the wrong surface.** Killing a hand-maintained index is exactly correct — *every hand-maintained index in this fleet is on a growth curve toward unwriteable*, and that is a standing scar, not an opinion. Three findings, then a recommendation.

## §10a 🔴 IT IS NOT A BINARY, AND THE THIRD OPTION IS THE ONE HE ACTUALLY ASKED FOR

The choice was framed as **live embed vs hand-maintained TSV**. There is a third shape and it is already in this engine:

| | Hand-kept TSV | Live embed | **DERIVED index** |
|---|---|---|---|
| hand maintenance | 🔴 yes — the actual complaint | none | **none** |
| survives blocked third-party cookies | yes | 🔴 **no** | **yes** |
| prints | yes | 🔴 **no** — blank rectangle | **yes** |
| can list a program that has no page | ⚠️ yes | ⚠️ **yes** | **impossible** |
| carries ClickUp login chrome | no | ⚠️ yes | **no** |
| updates without a publish | no | ✅ **yes** | no |

**Every program page already declares its own form src, with the `Program_ID` on it, in `forms:` frontmatter.** The engine reads all of it into `state.BY_SRC` on every build. So an index of *"available programs and their completion forms"* is **derivable from the pages themselves at zero maintenance cost** — and `30-programs/index.md` already carries **`contents: auto`**, so the auto-index mechanism is not even new (`docrender/objects.py` documents the key).

⭐ **The decisive property is not freshness, it is that a derived index CANNOT LIE ABOUT WHAT EXISTS.** It is built from the pages, so a program with no page cannot appear and a page with a form cannot be missing.

## §10b 🔴 THE SETS ALREADY DISAGREE, AND I READ IT RATHER THAN PREDICTING IT

The **Programs (canonical)** list holds **six open rows** today. Four defects, all live, all of which an embedded public index would publish:

1. 🔴 **ONE `Program_ID` ON TWO DIFFERENT PROGRAMS.** *Key & Swipe Access* and *MEWP Training, for Instructors* both carry `Program_ID=ITPSAFE-1219`. **Submissions from those two programs can never be told apart** — that is a compliance defect in the RECORD, not a display problem, and it is the most important thing on this page. Neither row is PUBLIC, so the embed would hide it rather than fix it.
2. 🔴 **TWO URL SHAPES FOR ONE SITE.** *MEWP Training, for Students* points at `/uritp-safety/programs/mewp-students/`; *General Safety for All* points at `/uritp-safety/30-programs/general-safety-for-all/`. **Both cannot be right**, and the source file behind the second is `30-programs/10-general/for-all.md` — a third shape. `Program URL` is a hand-typed URL field that **nothing validates**.
3. ⚠️ **A PUBLIC ROW WITH AN EMPTY LINK.** *General Safety for Scene Shop* is flagged 🌐 PUBLIC with no `Program URL`, though its page exists and carries `ITPSAFE-1242`. In an embedded index that is a visible row pointing nowhere.
4. ⚠️ **A PAGE WITH A FORM AND NO ROW.** `30-programs/10-general/rehearsal.md` carries the completion form link in its own frontmatter and has **no row in the list at all** — so it would be absent from the index while being present on the site. ⚠️ Related: *Incident Reporting* is PUBLIC, its form carries **no `Program_ID`**, and its page lives under `20-policies/` — against `30-programs/index.md`'s own opening line, *"a completion form accompanies a program and not a policy."*

🔴 **THE GENERALIZATION, AND IT IS THE WHOLE FINDING: MOVING A HAND-MAINTAINED INDEX INTO A CUSTOM FIELD DOES NOT DELETE THE HAND MAINTENANCE, IT RELOCATES IT SOMEWHERE THE BUILD REPORT CANNOT SEE IT.** The TSV had exactly one virtue — it sat in the content repo, so the engine could validate it and `dead_links` would complain. A `Program URL` typed into ClickUp is checked by nobody, and defects 2 through 4 are what that looks like after a few weeks. **A source of truth is not a source of truth because it is singular; it is one because something falsifies it.**

## §10c ClickUp IS canonical — for the RECORD, not for the SITE'S TABLE OF CONTENTS

The counter-argument, stated fairly because it is strong: the list owns fields the pages genuinely do not have — `🌐 PUBLIC`, `on Form Dropdown`, `Roles Affected`, `Role RESPONSIBLE`, `Completed Programs Submissions`. **That is real program metadata with no home in a markdown file, and it means ClickUp authoring is not a duplicate.**

So the split that holds, in this repo's existing canonical / generated / projection vocabulary:

- **ClickUp is CANONICAL for the program RECORD** — who owns it, which roles it touches, whether it is public, what has been submitted against it.
- **The SITE is CANONICAL for what is ON the site.** A page exists or it does not; nothing in ClickUp can be more authoritative about that.
- **`🌐 PUBLIC` is a publishing DECISION, and a decision should travel into the page** (it maps onto the `status:` field `visibility.py` already gates every build on) **rather than into a live frame the site cannot verify.**
- **`Program URL` should be DERIVED or DELETED.** It is the field that rotted, and the engine already knows every page's real URL.

## §10d ⏳ Rulings needed (three more)

7. 🔴 **Which surface is the program index: DERIVED from pages, or a live embed?** **Recommend DERIVED**, and it is not a close call — an index is NAVIGATION, and navigation that depends on third-party cookies degrades to a fallback link where the table of contents belongs. **A live embed is right for a table whose rows change independently of the site's pages and that nobody prints. A program index is the opposite of all three.**
8. **Then what IS the live embed for?** ⭐ **Recommend keeping BUILD 7 and pointing it at the submission side** — *"who has completed this program,"* a genuinely live table that no page can derive, sitting on an internal-audience page. ⚠️ But that is precisely the named-people case §4 forbids in public, so it lands **only** behind an unlisted page or not at all. **This is the honest tension in the whole build and it should not be resolved by pretending §4 is softer than it says.**
9. **The four defects in §10b — fix before or after?** **Recommend BEFORE, and treat defect 1 as urgent independently of this build.** 🚫 **Not touched in this pass by design:** a duplicated `Program_ID` is a compliance fact about two real programs, and picking which one gets renumbered is Michael's call, not a cleanup. Whichever index ships will publish these defects — the derived one at least cannot invent a fifth.

⚠️ **Honest limit on §10b:** read from the list on 2026-08-29 with closed tasks and subtasks excluded by default. **Six rows is what an open, non-subtask query returned, not a proven total** — if programs live as subtasks or closed rows, the set is larger and the disagreement with the site is worse, not better.
