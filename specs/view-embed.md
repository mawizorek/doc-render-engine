# BUILD 7 — the `views:` registry: embed ANY ClickUp view by NAME

✅ **SHIPPED 2026-08-30.** Scoped 08-28, rewritten 08-29, built and corrected twice on 08-30. Indexed from [`next-build-spec.md`](../next-build-spec.md) as **BUILD 7**.

> Michael, 2026-08-28: *"could i embed a clickup TABLE VIEW into one of my doc renderer pages???"* → **live**, not build-time.
>
> 08-29, on scope: *"i want to know how to embed any clickup view in one of my pages. let me decide what actually gets rendered. i gave you an example for a tool i wanted. focus on the tool."*
>
> 08-30, on the per-site host config: *"in every sits congit?????????????????? so i can do this anywehre i want later?"*
>
> 08-30, on the rendered caption: *"WHAT THE FUCK IS THIS SLOP. DELETE IT IMMEDIATELY."*

🔴 **THIS IS A TOOL SPEC. IT DOES NOT DECIDE WHAT GOES ON A PAGE.** ⚠️ **Three corrections in three days all had ONE root, and it is worth naming before the details: I kept deciding things that were his.** Which surface deserved an embed (§0), what every site must configure (§3a), and what sentence appears under his table (§3d). Each was reasoned from a real constraint, and reasoning is exactly what made them hard to see. **The tool emits structure. He decides content.**

---

## §1 HOW IT WORKS — the two halves, end to end

### Half 1: ClickUp side (once per view, by hand)

1. Right-click the view in the **Views Bar** → **Sharing & Permissions**.
2. Toggle **Share link with anyone** on.
3. Copy **Embed code** — a complete `<iframe>` string.
4. Optional in the same panel: **Share link with search engines** (leave OFF unless indexing is wanted), **Expire link** (Enterprise).

⚠️ **Applied filters travel with the share.** A publicly shared view carries its filters, so scoping what a reader sees is done IN the view, not in the page. **That is the mechanism by which the author controls the rendering, and it is the whole reason this tool is worth building.**

🔴 **NO AGENT CAN PRODUCE THE EMBED CODE, AND IT IS A HARD LIMIT** (verified 08-29). Nothing in the tool surface reads or writes a view's Sharing & Permissions; `create_view` has no sharing parameter. **The share token is server-minted when the toggle flips**, so it is not derivable from a view id — a perfectly-shaped guess still produces a dead `src`.

### Half 2: the engine side — the whole of it

🔴 **ONLY THE `src=` URL GOES IN THE FRONTMATTER, NOT THE `<iframe>`.** The first real paste (Michael, 08-30) put the whole element into `src:`, which is the predictable mistake and is exactly why the registry exists: the page NAMES a view, the engine builds the element. **The build reports this case by name** and says to paste only the URL.

```
views:
  recently-created:
    src: https://sharing.clickup.com/36074068/l/h/12cwjm-61513/486ae60bf886d69
    text: Recently created notes
    height: 700px           # optional, defaults to 700px

!!! view "recently-created"
```

✅ **That is everything. No site config, no registration, no other file.** A bare string is allowed as shorthand for `src:`, as `forms:` already permits.

**What renders:** the iframe, and a link to the same view beneath it. Nothing else.

---

## §2 ⚠️ WHAT SHIPPED IS A DELEGATION, NOT THE FOLD THIS SPEC ARGUED FOR

v2 §2 said: fold the registry into `forms.py`, because both are "validate a URL and emit an element" and a second module would be a second implementation of one idea. **The cohesion argument still stands. The fold does not.**

🔴 **IT DIED ON A MEASUREMENT, AND THE MEASUREMENT WAS IN THIS FILE'S OWN SCAR.** `forms.py` was **11,740 B** when the fold was scoped and **17,360 B** at build time — Michael's PR #197 added the dead-reference marker on 08-30. Folding a second registry in lands ~21KB, past the 18KB warn line. This spec had already written *"a size written into prose is wrong within two days, every time, in this repo"* and then had its own plan invalidated by exactly that, in one day.

**So the seam moved and both halves survived:**

- `docrender/views.py` is its own module holding the whole `views:` registry.
- **`forms.py` keeps the ONLY hook** and calls `views.on_page_markdown` last.
- **The shared vocabulary is imported, never re-declared.** `_esc` and the `docrender-dead` span come from `forms.py`; `_dead` gained a `label` parameter so both render an identical marker reading "Form" or "View".

⭐ **ONE HOOK IS THE POINT, NOT TIDINESS.** A second hook means editing `mkdocs.yml` — **28,158 B**, unreadable whole, therefore unsafe to rewrite. The delegation buys a whole new directive for **zero edits to any file past the ceiling.**

⚠️ **The two imports look like a cycle and must not be "tidied."** `forms.py` imports `views` INSIDE its hook function; `views.py` imports from `forms` at module top. By the time anything calls the hook, `forms` is loaded.

---

## §3 What was settled, and what had to be undone

### §3a 🔴 THE HOST — an engine default, not per-site config

The host is **`sharing.clickup.com`**, read out of Michael's real embed code. v1 required **every site** to declare it in `instances/<slug>/site.yml` with **no default**, on the rule that *"this engine never guesses a third-party hostname."*

🔴 **THE RULE WAS RIGHT AND I APPLIED IT TO THE WRONG NOUN.** "Never guess" protects against inventing an unverified value. This one was verified. **Once a value is verified it is a FACT, and a fact does not need six copies to become true.**

⚠️ **AND THE SIBLING FILE HAD ALREADY SETTLED IT.** `forms.py` hardcodes `_FORM_HOST = "https://forms.clickup.com/"` and always has. ⭐ The cheap tell I missed: **a per-site key whose correct value is identical on every site is not configuration, it is a constant with extra steps.** The real cost was a **silent failure on every future site** — a seventh site would get a refusal with no reason to suspect a key nobody told its author about.

✅ **NOW:** `_DEFAULT_HOST` carries it; `view_hosts:` survives as an **ADDITIVE** extension for the case the default cannot cover. **Additive is load-bearing:** declaring a host must not silently disallow the default. 🚫 Still an allow-list not a scheme check, still **never** a `*.clickup.com` wildcard (it matches `app.clickup.com`, the logged-in app, which would serve a login wall to the public). ⚠️ A stale default fails **loudly**, naming the found URL and the allowed hosts.

### §3b ⭐ NO `clickup-dynamic-height` AND NO CDN SCRIPT

ClickUp ships `clickup-embed` alone with a **literal `700px`**. So the invisible-frame hazard `forms.py` documents at length is **form-only**: the view height is declared, not scripted. `views.py` never appends the helper asset, and mirrors the height into `min-height` so a stylesheet cannot collapse it. A non-CSS-length `height:` is reported and replaced — a unitless `700` renders an invisible frame.

### §3c 🔴 THE "EVERYTHING LEVEL" CLAIM IS DEAD

The pasted view is `URITP PRODUCTIONS > Notes > Production Notes > Recently Created` — **a LIST-scoped, non-Form view with a working public share.** v3 recorded that one Help Center article contradicts itself on this, that I had stated the narrower row as a 🔴 fact twice, and that the Share modal outranks both rows. **The modal answered: the broader row is right.** ⭐ The durable part: **a document contradicting itself is not evidence, it is a prompt to go look** — the inverse of this repo's rule that agreeing sources are one source. Disagreeing sources are zero.

### §3d 🚫 THE CAPTION IS DELETED. THE ENGINE WRITES NO PROSE ONTO A PAGE.

v1 emitted a line under every frame reading *"Live from ClickUp — updates automatically."* Michael saw it rendered and wanted it gone on sight. **It is gone: no key, no constant, no CSS, no default.**

🔴 **THE DEFECT WAS NOT THE WORDING, IT WAS THE CATEGORY.** Everything else this registry emits is STRUCTURE — a frame, a link, a failure marker. The caption was the engine deciding an **editorial sentence** belonged in his content, in his voice, on his page, unasked. ⚠️ It was reasoned from a real constraint (ClickUp's unremovable *Sign up free* chrome) and §6 ruling 1 even took it as a recommended default — **which is the whole trap: a good argument for why a reader might want an explanation is not an argument for the ENGINE writing it.** If a page wants that sentence, the author types it above the directive.

🔴 **AND IT SHIPPED AN EM DASH INTO RENDERED OUTPUT**, against a standing absolute house rule. ⭐ That is the tell that should have caught it at authoring time: **the rule exists for prose, so a module emitting text that can VIOLATE a prose rule is a module writing prose** — which this one has no business doing.

✅ **THE FALLBACK LINK IS NOT THE SAME THING AND STAYS.** It is a control with a function: the answer to "the table did not load," and the only content on paper. Its label is the author's `text:`. **Function stays, narration goes.**

⚠️ **A leftover `caption:` key is REPORTED, not silently eaten** — pages written against v1 still carry it, and a key that quietly does nothing is this repo's least favourite shape (PR #197, one day earlier, same feature).

---

## §4 Properties of the mechanism (read once, then decide freely)

| Property | What it means for a page |
|---|---|
| 🔴 **Public shares require third-party cookies** | Blocked by default in a growing number of browsers, and the affected reader is exactly the one not logged into the workspace. Unverifiable at build time. **Acceptance test: load the page with third-party cookies OFF.** |
| ⚠️ **The frame carries ClickUp's own chrome** — *Sign up free* / *Login*, an *Embed ClickUp* logo | Inside a cross-origin iframe, so it cannot be removed (both are open feature requests). 🚫 **The engine does not explain it** — see §3d. If it needs explaining on a given page, the author writes that line. |
| ⚠️ **An iframe prints as a blank rectangle** | The fallback link renders **always**. 🔴 A worse loss than for a form, stated rather than solved: a printed form-link is a full substitute, but for a table the frame IS the content, so paper gets a URL where rows belong. A build-time copy for print was refused — two sources behind one element disagree the first time a filter changes. |
| 🔴 **A public share is public until revoked** | Works for anyone holding the link, indexable if that toggle is on, auditable by Owners/Admins on Enterprise under Security & Permissions. **Recommend logging each share in the Access Tracking Decision Log** so it can be revoked deliberately rather than discovered. What is safe to publish is the author's call, per view. |
| ⚠️ **A revoked share degrades to an empty frame with NO build finding** | External runtime behaviour is invisible at build time. The fallback link is the only thing distinguishing "loading" from "gone." |

**Every failure the engine CAN see renders a visible `docrender-dead` marker on the page AND a `dead_links` report line**, inheriting PR #197's rule whole: undeclared slot (naming what *is* declared), and a `src` off the allow-list. ⭐ That second one is the case where a marker matters most — the slot exists, so an author has every reason to think the embed is merely slow.

---

## §5 Files and sizes — read back from the write responses, not estimated

| File | Now |
|---|---|
| `docrender/views.py` | **19,103 B** (15,432 at first ship → 17,885 host default → 19,103 caption deletion) |
| `docrender/forms.py` | **untouched by the caption fix.** Michael has since edited it himself; measure it, never quote this row |
| `assets/flow.css` | **23,188 B** 🔴 see debt 2 |
| `mkdocs.yml` | **untouched** — the whole point of the delegation |
| `docrender/instance.py` | **untouched** |
| `instances/*/site.yml` | **untouched, and permanently so** — §3a |

⚠️ **`views.py` GREW WHILE DELETING A FEATURE**, +1,218 B, because the removal is documented. That is the right trade at this size and it will not be at the next one — the file is past the 18KB warn line and the next addition should move history to a `views-dl.md` sibling, which is the pattern `forms-dl.md` already establishes in this repo.

### 🔴 THE STANDING DEBT

**`assets/flow.css` is 23,188 B, past the ~22KB read ceiling.** Deleting the caption rule bought back ~300 B and did not fix it: **it was already ~21.6KB before BUILD 7 existed.** `.dr-view` belongs in its own `embed.css`, which requires registering a sheet in `docrender/assets.py` — **32,684 B, past the read ceiling AND the write cap.** ⚠️ **The real fix is splitting `assets.py`**, which is its own build. Flagged in flow.css's own header so the next editor meets it.

---

## §6 Rulings

1. ~~`caption:` defaults ON.~~ 🚫 **STRUCK 2026-08-30 — the whole key is deleted.** §3d. Kept struck rather than removed because this ruling is the record of the mistake: it reasoned an engine-authored sentence into a default, and it read as sound at the time.
2. **`views:` is universal, not type-gated.** `forms:` is gated because a completion form is a program-shaped idea; an embedded view is not shaped like anything.
3. **No print treatment beyond the fallback link.** See §4.

---

## §7 ⏳ What is left

1. **Put a `views:` block on any page and paste ONLY the `src=` URL.** Nothing else to set up, on any site.
2. **Acceptance test, and it is the one that decides whether the feature is real:** load that page with **third-party cookies BLOCKED**, then print-preview it.
3. 🅿️ **`next-build-spec.md` row 7 is still OWED** — 32,840 B, over the write cap. Its own header also instructs that the hand-kept build count be DELETED rather than refreshed the next time it is wrong, and adding row 7 makes it wrong.
4. 🅿️ **The `assets.py` split**, which unblocks `embed.css` and the flow.css debt.

---

## §8 Recorded, not prescriptive: the program-index example

Michael's first use case was *"a table view of all the available completion forms with their autofilled links with their program id... one source of truth filtered and displayed for public."* **The tool serves that directly and the choice is his.** Two FACTS about the live data, found 08-29:

- 🔴 **`Program_ID=ITPSAFE-1219` is on two different programs** in Programs (canonical) — *Key & Swipe Access* and *MEWP Training, for Instructors*. Submissions from those two cannot be told apart. **A compliance defect in the record, independent of any rendering decision.**
- ⚠️ **`Program URL` disagrees with the site in three ways**: two different URL shapes for one site, one 🌐 PUBLIC row with an empty URL, and one page (`30-programs/10-general/rehearsal.md`) carrying a completion form with no row at all.

⚠️ **Honest limit:** read with closed tasks and subtasks excluded by default — six open non-subtask rows is what the query returned, **not a proven total.**

🚫 **No fix attempted and none proposed.** Which program gets renumbered is Michael's call.
