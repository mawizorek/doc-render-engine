# BUILD 7 — the `views:` registry: embed ANY ClickUp view by NAME

✅ **SHIPPED 2026-08-30.** Scoped 08-28, rewritten 08-29, built 08-30. Indexed from [`next-build-spec.md`](../next-build-spec.md) as **BUILD 7**.

> Michael, 2026-08-28: *"could i embed a clickup TABLE VIEW into one of my doc renderer pages???"* → **live**, not build-time.
>
> Michael, 2026-08-29, correcting the scope of this document: *"i want to know how to embed any clickup view in one of my pages. let me decide what actually gets rendered. i gave you an example for a tool i wanted. focus on the tool."*

🔴 **THIS IS A TOOL SPEC. IT DOES NOT DECIDE WHAT GOES ON A PAGE.** The v1 of this file argued about which surface deserved a live embed and shipped a ruling asking Michael to choose between derived and live. **That was scope creep dressed as diligence: he asked for a capability and got an architecture review of his content.** Constraints below are **properties of the mechanism**, never gates on his choice.

**What it does:** a page names a shared ClickUp view in frontmatter; the engine builds the iframe.

---

## §1 HOW IT WORKS — the two halves, end to end

### Half 1: ClickUp side (once per view, by hand)

1. Right-click the view in the **Views Bar** → **Sharing & Permissions**.
2. Toggle **Share link with anyone** on.
3. Copy **Embed code** — a complete `<iframe>` string.
4. Optional in the same panel: **Share link with search engines** (leave OFF unless indexing is wanted), **Expire link** (Enterprise).

⚠️ **Applied filters travel with the share.** A publicly shared view carries its filters, so scoping what a reader sees is done IN the view, not in the page. **That is the mechanism by which the author controls the rendering, and it is the whole reason this tool is worth building.**

🔴 **NO AGENT CAN PRODUCE THE EMBED CODE, AND IT IS A HARD LIMIT** (verified 08-29). Nothing in the tool surface reads or writes a view's Sharing & Permissions; `create_view` has no sharing parameter. **The share token is server-minted when the toggle flips**, so it is not derivable from a view id — a perfectly-shaped guess still produces a dead `src`.

### Half 2: the engine side

🔴 **ONLY THE `src=` URL GOES IN THE FRONTMATTER, NOT THE `<iframe>`.** The first real paste (Michael, 08-30) put the whole element into `src:`, which is the predictable mistake and is exactly why the registry exists: the page NAMES a view, the engine builds the element. **The build reports this case by name** and says to paste only the URL.

```
views:
  recently-created:
    src: https://sharing.clickup.com/36074068/l/h/12cwjm-61513/486ae60bf886d69
    text: Recently created notes
    caption: true
    height: 700px          # optional, defaults to 700px

!!! view "recently-created"
```

And once per SITE, in its instance config:

```
view_hosts:
  - https://sharing.clickup.com/
```

A bare string is allowed as shorthand for `src:`, as `forms:` already permits.

---

## §2 ⚠️ WHAT SHIPPED IS A DELEGATION, NOT THE FOLD THIS SPEC ARGUED FOR

v2 §2 said: fold the registry into `forms.py`, because both are "validate a URL and emit an element" and a second module would be a second implementation of one idea. **The cohesion argument still stands. The fold does not.**

🔴 **IT DIED ON A MEASUREMENT, AND THE MEASUREMENT WAS IN THIS FILE'S OWN SCAR.** `forms.py` was **11,740 B** when the fold was scoped and **17,360 B** at build time — Michael's PR #197 added the dead-reference marker on 08-30. Folding a second registry in lands ~21KB, past the 18KB warn line. This spec had already written *"a size written into prose is wrong within two days, every time, in this repo"* and then had its own plan invalidated by exactly that, in one day.

**So the seam moved and both halves survived:**

- `docrender/views.py` is its own module holding the whole `views:` registry.
- **`forms.py` keeps the ONLY hook** and calls `views.on_page_markdown` last.
- **The shared vocabulary is imported, never re-declared.** `_esc` and the `docrender-dead` span come from `forms.py`; `_dead` gained a `label` parameter so both render an identical marker reading "Form" or "View".

⭐ **ONE HOOK IS THE POINT, NOT TIDINESS.** A second hook means editing `mkdocs.yml` — **28,158 B**, unreadable whole, therefore unsafe to rewrite. The delegation buys a whole new directive for **zero edits to any file past the ceiling.** `instance.py` (23,047 B) is dodged the same way: `view_hosts:` is read off `state.INSTANCE`, never parsed per-key.

⚠️ **The two imports look like a cycle and must not be "tidied."** `forms.py` imports `views` INSIDE its hook function; `views.py` imports from `forms` at module top. By the time anything calls the hook, `forms` is loaded.

---

## §3 ✅ THE THREE UNKNOWNS, ALL SETTLED BY ONE REAL EMBED CODE

Michael's paste resolved every open question in this spec at once. The string:

```
<iframe class="clickup-embed" src="https://sharing.clickup.com/..." onwheel=""
        width="100%" height="700px" style="background: transparent; border: 1px solid #ccc;">
```

**a) The host is `sharing.clickup.com`.** It goes in `view_hosts:` per site — declared, never defaulted. 🚫 An absent or empty key refuses every embed and REPORTS it; **no fallback**, because a default would be this engine remembering a third-party hostname on the reader's behalf. 🚫 And never a `*.clickup.com` wildcard: that also matches `app.clickup.com`, the logged-in application, so a page could serve a login wall to the public and it would read as a broken table.

**b) ⭐ THERE IS NO `clickup-dynamic-height` AND NO CDN SCRIPT.** ClickUp ships `clickup-embed` alone with a **literal `700px`**. So the whole invisible-frame hazard `forms.py` documents at length is **form-only**: the view height is declared, not scripted. `views.py` therefore never appends the helper asset (fetching a sizing script for an already-sized frame is pure cost), and mirrors the height into `min-height` so a stylesheet cannot collapse it. A non-CSS-length `height:` is reported and replaced rather than passed through — a unitless `700` renders an invisible frame.

**c) 🔴 THE "EVERYTHING LEVEL" CLAIM IS DEAD.** The pasted view is `URITP PRODUCTIONS > Notes > Production Notes > Recently Created` — **a LIST-scoped, non-Form view with a working public share.** §4 of v3 recorded that one Help Center article contradicts itself on this, that I had stated the narrower row as a 🔴 fact twice, and that the Share modal outranks both rows. **The modal has now answered: the broader row is right.** ⭐ The generalization stands and is the durable part: **a document contradicting itself is not evidence, it is a prompt to go look** — the inverse of this repo's standing rule that agreeing sources are one source. Disagreeing sources are zero.

---

## §4 Properties of the mechanism (read once, then decide freely)

| Property | What it means for a page |
|---|---|
| 🔴 **Public shares require third-party cookies** | Blocked by default in a growing number of browsers, and the affected reader is exactly the one not logged into the workspace. Unverifiable at build time. **Acceptance test: load the page with third-party cookies OFF.** |
| ⚠️ **The frame carries ClickUp's own chrome** — *Sign up free* / *Login*, an *Embed ClickUp* logo | Inside a cross-origin iframe, so it cannot be removed (both are open feature requests). `caption:` is the answer and defaults ON: it names the frame as live third-party content, turning clutter into provenance. |
| ⚠️ **An iframe prints as a blank rectangle** | The fallback link renders **always**. 🔴 A worse loss than for a form, stated rather than solved: a printed form-link is a full substitute, but for a table the frame IS the content, so paper gets a URL where rows belong. A build-time copy for print was refused — two sources behind one element disagree the first time a filter changes. |
| 🔴 **A public share is public until revoked** | Works for anyone holding the link, indexable if that toggle is on, auditable by Owners/Admins on Enterprise under Security & Permissions. **Recommend logging each share in the Access Tracking Decision Log** so it can be revoked deliberately rather than discovered. What is safe to publish is the author's call, per view. |
| ⚠️ **A revoked share degrades to an empty frame with NO build finding** | External runtime behaviour is invisible at build time. The fallback link is the only thing distinguishing "loading" from "gone." |

**Every failure the engine CAN see renders a visible `docrender-dead` marker on the page AND a `dead_links` report line**, inheriting PR #197's rule whole: undeclared slot (naming what *is* declared), no `view_hosts:` configured, and a `src` off the allow-list. ⭐ That last one is the case where a marker matters most — the slot exists, so an author has every reason to think the embed is merely slow.

---

## §5 Files and sizes — read back from the write responses, not estimated

| File | Before | After |
|---|---|---|
| `docrender/views.py` | — | **15,432 B** (new) |
| `docrender/forms.py` | 17,360 B | **18,934 B** ⚠️ see debt 1 |
| `assets/flow.css` | ~21,635 B | **23,485 B** 🔴 see debt 2 |
| `mkdocs.yml` | 28,158 B | **untouched** — the whole point of the delegation |
| `docrender/instance.py` | 23,047 B | **untouched** |
| `instances/<slug>/` config | — | `+view_hosts:`, one line, **Michael's to add** — which site is his call |

### 🔴 TWO BUDGET DEBTS, RECORDED RATHER THAN BURIED

**Debt 1 — `forms.py` is 18,934 B, just past the 18KB warn line** (under the ~22KB ceiling). The first draft came back at **20,585 B** because I added ~3.2KB of prose to the one file whose own risk note says *"the risk is prose, not code"*. Trimmed in the same pass to a pointer, with the full argument living in `views.py`. **The remaining +1,574 B is real and the file has little room left.**

**Debt 2 — `assets/flow.css` is 23,485 B, PAST the ~22KB read ceiling, and it cannot be fixed here.** 🔴 **It was already ~21.6KB before this build**, so any addition at all broke it. `.dr-view` belongs in its own `embed.css`, which requires registering a sheet in `docrender/assets.py` — **32,684 B, past the read ceiling AND the write cap**, so it cannot be rewritten safely. ⚠️ **The real fix is splitting `assets.py`, and until then this sheet holds three concerns and has no room for a fourth.** Flagged in the file's own header so the next editor meets it.

⚠️ **I chose to report this rather than mangle pre-existing documentation to squeeze under a line.** A CSS file over the ceiling still renders correctly; the cost is editability, and hiding it by deleting somebody else's reasoning is the worse trade.

---

## §6 ✅ Rulings, all three taken as recommended

1. **`caption:` defaults ON.** The unremovable chrome needs explaining, and the caption also carries "this is live." `caption: false` opts out.
2. **`views:` is universal, not type-gated.** `forms:` is gated because a completion form is a program-shaped idea; an embedded view is not shaped like anything.
3. **No print treatment beyond the fallback link.** See §4.

---

## §7 ⏳ What is left, and it is not code

1. **Add `view_hosts: [https://sharing.clickup.com/]` to whichever site's instance config** gets the first embed. Until then the engine refuses and reports — by design.
2. **Put the `views:` block on a page** and paste ONLY the `src=` URL.
3. **Acceptance test, and it is the one that decides whether the feature is real:** load that page with **third-party cookies BLOCKED**, then print-preview it.
4. 🅿️ **`next-build-spec.md` row 7 is still OWED** — 32,840 B, over the write cap. Its own header also instructs that the hand-kept build count be DELETED rather than refreshed the next time it is wrong, and adding row 7 makes it wrong.

🚫 **Nothing here needs a decision about WHICH view goes on WHICH page. That was never this document's business.**

---

## §8 Recorded, not prescriptive: the program-index example

Michael's first use case was *"a table view of all the available completion forms with their autofilled links with their program id... one source of truth filtered and displayed for public."* **The tool serves that directly and the choice is his.** Two FACTS about the live data, found 08-29 and recorded because they are facts rather than arguments:

- 🔴 **`Program_ID=ITPSAFE-1219` is on two different programs** in Programs (canonical) — *Key & Swipe Access* and *MEWP Training, for Instructors*. Submissions from those two cannot be told apart. **A compliance defect in the record, independent of any rendering decision.**
- ⚠️ **`Program URL` disagrees with the site in three ways**: two different URL shapes for one site, one 🌐 PUBLIC row with an empty URL, and one page (`30-programs/10-general/rehearsal.md`) carrying a completion form with no row at all.

⚠️ **Honest limit:** read with closed tasks and subtasks excluded by default — six open non-subtask rows is what the query returned, **not a proven total.**

🚫 **No fix attempted and none proposed.** Which program gets renumbered is Michael's call.
