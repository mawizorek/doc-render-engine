# BUILD 7 — the `views:` registry: embed ANY ClickUp view by NAME

✅ **SHIPPED 2026-08-30.** Scoped 08-28, rewritten 08-29, built + corrected twice + `collapsed:` added 08-30.

🔴 **THE REASONING LIVES IN [`docrender/views-dl.md`](../docrender/views-dl.md), NOT HERE.** D1–D7 hold every decision and every correction with the quote that forced it. **This file is the SPEC: what it does, what it costs, what is left.** Two claimants on one argument is the defect this repo has retired three manifests over, so when they disagree the sidecar wins and this file gets corrected.

---

## §1 What it does

A page names a shared ClickUp view in frontmatter; the engine builds the iframe.

### ClickUp side, once per view (by hand — no agent can do it)

Right-click the view in the **Views Bar** → **Sharing & Permissions** → toggle **Share link with anyone** → copy **Embed code**. Leave the search-engine toggle off unless indexing is wanted.

⚠️ **Applied filters travel with the share**, so scoping what a reader sees happens IN the view. **That is how the author controls the rendering, and it is the whole reason the tool is worth having.**

🔴 **The share token is server-minted when the toggle flips** — not derivable from a view id, and nothing in the tool surface reads or writes Sharing & Permissions. A perfectly-shaped guess produces a dead `src`.

### Engine side — the whole of it

```
views:
  recently-created:
    src: https://sharing.clickup.com/36074068/l/h/12cwjm-61513/486ae60bf886d69
    text: Recently created notes
    collapsed: true      # optional; REQUIRES text: — see below
    height: 700px        # optional, defaults to 700px

!!! view "recently-created"
```

✅ **That is everything. No site config, no registration, no other file, on any site including a brand-new one.** A bare string is shorthand for `src:`, as `forms:` already permits.

🔴 **ONLY THE `src=` URL, NEVER THE WHOLE `<iframe>`.** The first real paste did exactly that, so the allow-list failure message names the case and says to paste the URL.

**What renders:** the frame, and a link to the same view beneath it. 🚫 **Nothing else — the engine emits structure, never page copy.** views-dl.md D6.

### `collapsed:` — new 2026-08-30

> Michael: *"can we embedd these like formas optionally to make them collapsable too?"*

The same script-free mechanism `forms.py` proves: a closed `<details>`, and per the HTML spec **a fragment targeting content inside it expands it** — so `#dr-view-<slot>` opens it with no JavaScript, no query parameter, no state. ⭐ An author can link to that id; nothing in the engine does today.

⭐ **Worth more on a view than on a form.** A collapsed form solves *sequencing* (do not ask somebody to certify unread material). A collapsed view solves **weight**: a 700px frame is the tallest thing on any page it sits on and pushes real prose below the fold. 🔴 It is also the only element here that costs a third-party request, **so a closed disclosure is the one honest way to make a live embed free until it is wanted.**

🔴 **THE LABEL IS THE AUTHOR'S `text:`. THERE IS NO DEFAULT.** `forms.py` can default to *"Complete this program"* because a completion form has exactly one purpose; a view has none, so naming it would be the engine writing page copy — the mistake deleted one day earlier. ✅ **`collapsed: true` with no `text:` renders OPEN and reports why**: the frame still appears, nothing is lost, and the note names the one line to add.

---

## §2 Properties of the mechanism (read once, then decide freely)

| Property | What it means for a page |
|---|---|
| 🔴 **Public shares require third-party cookies** | Blocked by default in a growing number of browsers, and the affected reader is exactly the one not logged into the workspace. **Unverifiable at build time. Acceptance test: load the page with them OFF.** |
| ⚠️ **The frame carries ClickUp's chrome** — *Sign up free* / *Login*, an *Embed ClickUp* logo | Cross-origin, so it cannot be removed (both are open feature requests). 🚫 **The engine does not explain it.** If a page needs that said, the author writes the line. |
| ⚠️ **An iframe prints blank** | The fallback link renders **always**. 🔴 A worse loss than for a form: a printed form-link is a full substitute, but for a table the frame IS the content, so paper gets a URL where rows belong. A build-time print copy was refused — two sources behind one element disagree the first time a filter changes. ✅ A collapsed embed needs no print rule: `print-flow.css` already forces every `<details>` open. |
| 🔴 **A public share is public until revoked** | Indexable if that toggle is on; auditable by Owners/Admins on Enterprise under Security & Permissions. **Recommend logging each share in the Access Tracking Decision Log** so it can be revoked deliberately rather than discovered. **What is safe to publish is the author's call, per view.** |
| ⚠️ **A revoked share → empty frame, NO build finding** | External runtime behaviour is invisible at build time. The fallback link is the only thing distinguishing "loading" from "gone." |

**Everything the engine CAN see renders a visible `docrender-dead` marker AND a `dead_links` line:** undeclared slot (naming what *is* declared), and a `src` off the allow-list. ⭐ The second is where a marker matters most — the slot exists, so an author has every reason to think the embed is merely slow. A bad `height:` and a leftover `caption:` land in `notes`.

---

## §3 Files — read back from the write responses, never estimated

| File | Now |
|---|---|
| `docrender/views.py` | **11,471 B** ⭐ **DOWN from 19,103 while gaining a feature** — history moved to the sidecar |
| `docrender/views-dl.md` | **14,018 B** (new) |
| `assets/flow.css` | **23,163 B** 🔴 see the debt |
| `docrender/forms.py` | **untouched.** Michael is editing it himself — measure it, never quote a row |
| `mkdocs.yml` · `instance.py` · `instances/*/site.yml` | **untouched, and permanently so** |

⭐ **THE SIDECAR SPLIT WAS THIS FILE'S OWN INSTRUCTION, EXECUTED.** The previous version wrote *"the next addition should move history to a `views-dl.md` sibling"* — and that is the pattern Michael set with `forms-dl.md`. **A module that shrinks while gaining a feature is what the split is for.**

### 🔴 The standing debt

**`assets/flow.css` is 23,163 B, past the ~22KB read ceiling.** Merging the duplicated form/view blocks bought back 25 B; **it was already ~21.6KB before BUILD 7 existed.** `.dr-view` belongs in its own `embed.css`, which requires registering a sheet in `docrender/assets.py` — **32,684 B, past the read ceiling AND the write cap.** ⚠️ **The real fix is splitting `assets.py`**, which is its own build. Flagged in flow.css's header so the next editor meets it.

---

## §4 Rulings

1. ~~`caption:` defaults ON.~~ 🚫 **STRUCK — the key is deleted.** Kept struck rather than removed because this ruling IS the record of the mistake: it reasoned an engine-authored sentence into a default and read as sound at the time. views-dl.md D6.
2. **`views:` is universal, not type-gated.** `forms:` is gated because a completion form is a program-shaped idea; an embedded view is not shaped like anything.
3. **No print treatment beyond the fallback link.** §2.
4. **`collapsed:` is opt-in and needs `text:`.** Declared beats inferred, and the engine writes no labels.

---

## §5 ⏳ What is left

1. **Put a `views:` block on any page.** Nothing to set up.
2. **The acceptance test, still not run, and it is the one that decides whether the feature is real:** load a page with **third-party cookies BLOCKED**, then print-preview it.
3. 🅿️ **`next-build-spec.md` row 7 is OWED** — 32,840 B, over the write cap. Its own header says to DELETE the hand-kept build count rather than refresh it the next time it is wrong, and adding row 7 makes it wrong.
4. 🅿️ **The `assets.py` split**, which unblocks `embed.css` and the flow.css debt.

---

## §6 Recorded, not prescriptive: the program-index example

Michael's first use case was *"a table view of all the available completion forms with their autofilled links with their program id... one source of truth filtered and displayed for public."* **The tool serves that directly and the choice is his.** Two FACTS about the live data, found 08-29:

- 🔴 **`Program_ID=ITPSAFE-1219` is on two different programs** in Programs (canonical) — *Key & Swipe Access* and *MEWP Training, for Instructors*. Submissions from those two cannot be told apart. **A compliance defect in the record, independent of any rendering decision.**
- ⚠️ **`Program URL` disagrees with the site in three ways**: two URL shapes for one site, one 🌐 PUBLIC row with an empty URL, and one page (`30-programs/10-general/rehearsal.md`) carrying a completion form with no row at all.

⚠️ **Honest limit:** read with closed tasks and subtasks excluded by default — six open non-subtask rows is what the query returned, **not a proven total.**

🚫 **No fix attempted and none proposed.** Which program gets renumbered is Michael's call.
