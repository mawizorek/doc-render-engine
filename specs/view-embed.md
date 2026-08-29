# BUILD 7 — a `views:` registry: a live ClickUp view, embedded by NAME

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-28. Indexed from [`next-build-spec.md`](../next-build-spec.md) as **BUILD 7**.

> Michael, 2026-08-28: *"could i embed a clickup TABLE VIEW into one of my doc renderer pages??? like embedding a clickup form on the safety site but doing a custom clickup table view to embed instead."* Asked whether it should be **live** or a build-time table: **"live."**

**One-line summary:** a page names a shared ClickUp view in frontmatter, the engine builds the iframe. Mechanically this is `docrender/forms.py` with a second allow-listed host — **which is exactly why the code is the cheap half and this spec is mostly about the four things that are not code.**

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
| `docrender/datatable.py` | 16,566 B | **untouched.** `!!! data` is the build-time alternative, not part of this build. |
| `docrender/program.py` | 18,350 B | **untouched** unless `collapsed:` is wanted for views (recommend not — §0). |
| `theme/` CSS | not measured | one `.dr-view__caption` rule, if ruling 6 lands. |

⚠️ **`mkdocs.yml` IS RECORDED IN `next-build-spec.md` AT 13,632 B "AT HEAD 2026-08-21" AND IS 28,158 B TODAY — a 106% drift in seven days.** That file already carries the scar *"a size written into prose is wrong within two days, every time, in this repo,"* and it has now been proven by its own most recently corrected number. **Measure at the moment you act; never quote a table.**

---

## §7 ⏳ Rulings needed (six)

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
