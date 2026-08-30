# BUILD 10 · THE PROGRAM PACKET — one document, printed once, with the program page as its cover

✅ **BUILT 2026-08-30**, same day it was scoped. Greenlit by Michael: *"i want to have a button export an entire program asap. this looks good. let's do it."* Five rulings closed, **two open and named in §11**. Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

<p><br/></p>

📚 **The ARGUMENTS live in [`print-packet-dl.md`](print-packet-dl.md)** — A1–A13, the single claimant for all of them. This file holds the decisions and what shipped.

<p><br/></p>

🔴 **AND TWO CLAIMS IN THE FIRST VERSION OF THIS FILE WERE FALSE ON ARRIVAL — see §10.** Both were copied out of `next-build-spec.md`'s file table, which is the one thing that file tells you in bold not to do.

---

## What shipped

| File | | What |
|---|---|---|
| `docrender/packet.py` | **NEW** 18,489 B | what a packet IS: the `export:` vocabulary, `article()`, id + href namespacing, the cover, the button. **Every function pure and unit-tested.** |
| `docrender/packetbuild.py` | **NEW** 11,823 B | WHEN: mint at `on_files`, plan at `on_nav`, place at `on_page_markdown` / `on_page_content`, assemble at `on_post_build`. |
| `assets/packet.css` | **NEW** 4,504 B | button, cover, section boundary |
| `assets/print-packet.css` | **NEW** 5,117 B | one policy per sheet; the button does not print |
| `docrender/assets.py` | edited | eighth group, `_PACKET_ASSETS`, walked everywhere |
| `hooks/05b_program.py` | edited | four more events, **no `mkdocs.yml` edit** |
| `objects/program.yml` | edited | `export` declared, plus why the declaration is not the check |

---

## ✅ §1 — THE SHAPE, AS BUILT

A program declares `export: [packet]`. The engine mints **one generated page per program**, at `<program-src>-packet.md`. The program's own title is sheet one with a contents list; each `chain:` member follows as a `<section>` that starts a fresh sheet. The button links to it. **One dialog, one file, one PDF.**

<p><br/></p>

⚠️ **A SIBLING FILE, NOT `<program-path>/packet/`, WHICH CORRECTS §1 OF THE SCOPED VERSION.** A program page is a FILE, so a child path needs a directory that does not exist. `docrender/packet.py:packet_src` carries the reason.

<p><br/></p>

🔴 **THE MECHANISM HE ASKED FOR CANNOT EXIST** and that is the spine of the build: `window.print()` prints the current document only, a print job is user-mediated, and the PDF never enters JavaScript. **He described a reader doing it by hand; the engine holds every page at once.** → **A1**

---

## ✅ §2 — THE PRINT IS AN ORDINARY PRINT

> *"the print should run just like a manual print command on the page."*

✅ The packet is a real MkDocs page, so `Ctrl+P` on it IS that. All eight print sheets apply, the chrome-off list applies, the corner stamp applies. 🚫 **No second print path exists and none may be built** — which closes the WeasyPrint question independently.

<p><br/></p>

🔴 **"ALL THE THEMING STRIPPED" IS THE ONE PART OF THE ASK THAT WAS REFUSED.** `print.css` applies `print-color-adjust: exact` narrowly, to elements *"whose MEANING is carried by a colour"*. It strips chrome and ground and **keeps semantic colour**, because a `!!! danger` border printing grey on a photocopied safety sheet is a regression. → **A3**

<p><br/></p>

🚫 **NO AUTO-`window.print()`.** Legal, identical to a manual print, and it defeats §5: a nine-section packet from a ten-id chain is a **valid document**, so the reader's glance at the cover is the last line of defence.

---

## ✅ §3 — ANCHOR COLLISION: WHAT THE CODE ACTUALLY DOES

Every id gets its section prefix (`overview` → `s3-overview`). Every href is classified:

| Link | Becomes |
|---|---|
| `#frag` | `#sN-frag` |
| a path **IN** the packet | `#sM[-frag]` — the internal jump |
| a path **OUTSIDE** the packet | the **absolute** site URL |
| absolute / `mailto:` / `tel:` | untouched |
| no `site_url` declared | **untouched AND reported** — never guessed |

<p><br/></p>

✅ **PROVEN BY EXECUTION, NOT BY READING.** Two suites, 58 assertions, run against the real module with stubs only at the I/O boundary: five colliding `#overview` anchors namespaced apart, a cross-member link converted to `#s2-extinguishers`, an outside link absolutised **including the publish sub-path**, and a second assembly pass reporting the consumed marker instead of blanking the file.

<p><br/></p>

🔴 **TWO REAL DEFECTS WERE FOUND BY RUNNING IT.** (1) The strip and namespace regexes were double-quote-only, so a hand-written `<div id='x'>` in a markdown body would have slipped through **unnamespaced and unreported** — now quote-agnostic. (2) My own first test expectation dropped the publish sub-path from an absolute link; **the code was right and the test was wrong**, which is the BUILD 6 `base_url` hazard in miniature.

---

## ⚠️ §4 — STILL UNVERIFIED, AND IT IS THE PART HE IS EXCITED ABOUT

**Nobody has proven Chrome print-to-PDF emits real link annotations for `#fragment` jumps.** The markup is correct either way — only the CLAIM changes: a clickable index, or a printed contents list. **Ruling 1 stays open and is a ten-minute experiment on the first real packet.** → **A4**

---

## 🚫 §5 — WHAT A PACKET CANNOT HAVE, AND WHAT IS REPORTED INSTEAD

No page numbers (Blink has never implemented `@page` margin boxes), no PDF bookmark pane. **The cover's contents list is the outline.** → **A5**

<p><br/></p>

✅ **COVERAGE IS REPORTED PER PROGRAM**: members resolved against members declared, every refusal by name. A dropped chain member costs a DOCUMENT, not a button. → **A6**

---

## ✅ §6 — THE LEAK REFUSAL IS LIVE

A chain member whose `status:` is not `public` is **refused and named**. `nav: hidden` and `unlisted` are curtains for somebody browsing; a packet is a PDF that leaves the site. → **A7**

---

## ✅ §7 — WHAT IS REMOVED FROM EACH SECTION

`.dr-flow*` — **the packet IS the flow**, and nine strips would each orient somebody already past them. `buildstamp*` — **not** because paper does not want provenance, but because the print stamp is a FIXED element that repeats per sheet from ONE instance, so nine copies is nine overlapping stamps. The packet's own stamp does the job §8 asks for. Class block read off `buildstamp.py`, never guessed. → **A8**

---

## 🚫 §8 — `{.new-page}` IS REFUSED IN A PACKET

Invalidation **number nine**, and the first where every authored break is invalidated **by definition**. Section boundaries are the only breaks a packet honours. → **A9**

---

## ✅ §9 — THE BUTTON: DECLARED, PLACED OR AUTOMATIC

✅ **Ruling 4 CLOSED — frontmatter-declared**, per Michael. ⚠️ The floated value `available` was **not** built: there are exactly two states, so a status word is a boolean in a costume, it invites `pending`/`soon` that nothing validates, and it reads as a second `status:` axis. **Built as `export: [packet]`, closed set, unknown kinds reported** — and `export: true` is accepted too. → **A10**

<p><br/></p>

✅ **Ruling 6 CLOSED — both.** `export:` declares, `!!! export` places, no directive renders it automatically inside the flow strip's block. **Exactly the `forms:` split he praised on 08-19.** → **A11**

<p><br/></p>

🚫 **The button does not print** — *"A BUTTON ON PAPER IS A LIE"*, and the chrome-off rule shipped in the same commit. ⚠️ **Not a fourth footer**, rejected by name on 08-19.

---

## 🔴 §10 — TWO STALE CLAIMS I INHERITED, AND THE CORRECTION IS THE LESSON

The scoped version of this file said, twice, that there were **five print sheets** and that **`print-identity.css` does not exist, so the letterhead never landed.**

<p><br/></p>

✅ **BOTH FALSE AT HEAD.** `assets.py` registers **EIGHT** print sheets and `assets/print-identity.css` is **13,155 B on disk**. BUILD 5's letterhead shipped; `print-ink.css` and `print-identity.css` both exist.

<p><br/></p>

🔴 **I COPIED THEM OUT OF `next-build-spec.md`, WHICH SAYS IN BOLD: *"Read `assets.py` for what exists; never that spec's file table."*** The warning was correct, addressed to exactly the person who would trip it, reachable, and read only after the fact. ⚑ *That is J27's shape verbatim — a comment cannot fire. And the cost here was specific rather than cosmetic: §8's per-sheet provenance was written as blocked on a prerequisite that had already landed, so a cold session would have deferred work that was ready.*

<p><br/></p>

⚠️ **`docrender/assets.py` IS NOW 18,650 B, past the 18 KB warn line, and my comments did that.** It was extracted from 32,684 B this morning. Under the 22.5 KB read ceiling and safe, but named rather than left to be discovered.

---

## ⏳ §11 — RULINGS

**1. 🔴 OPEN — do link annotations survive Chrome print-to-PDF?** §4. Ten minutes on the first real packet. **It changes no markup, only the claim.**

**2. 🔴 OPEN — is the packet Chrome-only, stated in the report?** Depends entirely on ruling 1.

**3. ✅ CLOSED — refuse-and-report**, as recommended. Built in `packetbuild.on_nav`.

**4. ✅ CLOSED — declared, as `export: [packet]`.** See §9.

**5. ✅ CLOSED — moot until BUILD 8 Feature A ships.** The packet holds no reader state and reads no per-page `print:` block, so **PACKET > PAGE** is satisfied by construction rather than by a rule.

**6. ✅ CLOSED — both.** See §9.

**7. 🚩 NOT BUILT — the browser print-footer page number.** A provenance decision, his call, and no default was invented.

---

## ⚠️ §12 — DEVIATIONS FROM THE SCOPE, EACH WITH ITS REASON

1. **Sibling path, not a child path** (§1). A program page is a file.
2. **Two modules, not one.** `packet.py` hit 18,004 B against the read ceiling; cut on the concern (`visibility-split.md` §1), pure functions one side, MkDocs and disk the other.
3. **Wired into `hooks/05b_program.py`, not a new stage.** A new stage means editing `mkdocs.yml`, which is **28,158 B — past the read ceiling, so it cannot be read whole and therefore cannot be safely rewritten.** The packet is a program concern and 05b is the program stage.
4. **The inventory line goes to `notes`, not a new `packet` bucket** (§6 asked for one). A new bucket is two edits in two large files and a bucket declared in only one of them is **silently dropped**. Every packet DEFECT already lands in `missing_required` / `dead_links`, which are annotated. 🚩 Owed if the heading is wanted.
5. **No QR on the cover.** BUILD 6 territory; `qr.py` exists and the cover is the right home, but it is a separate feature and this PR did not touch it. 🚩 Owed.
6. **`print-packet.css` is in the PACKET group, not `_PRINT_ASSETS`.** That group's claim is "must beat the generated sheets at equal specificity" and these rules share no selector with anything. **A member that breaks its group's claim is worse than a new group.**

---

## ⚠️ §13 — WHAT IS NOT VERIFIED, STATED PLAINLY

**No MkDocs build has run.** Every pure function is executed and green; **every MkDocs interaction is reasoned, not run** — `File.generated` on a markdown path, the nav prune, `abs_dest_path` on a generated File, and hook-event ordering inside the 05b shim. The first publish is the test, and the build report is where it will say so.

<p><br/></p>

🔴 **THE MOST LIKELY FIRST FAILURE, NAMED SO NOBODY HUNTS IT BLIND:** the generated packet page appearing in the sidebar anyway, if MkDocs builds nav items this hook's `_prune` does not reach. It is cosmetic and one line to fix. **The second: `abs_dest_path` empty on a generated File**, which `on_post_build` already handles as "not on disk" and reports rather than crashing.

---

## Next

1. **Publish `uritp-safety` and read the report.** It names every packet, its member count against its declared count, and every refusal.
2. **Ruling 1** — print the packet, click a cover entry.
3. **Move BUILDS 1 and 2 out of `next-build-spec.md`** so it becomes a ~4 KB index that can be written. **Five rows are now owed there: BUILDS 7, 8, 9, 10 and this one's BUILT status.**
