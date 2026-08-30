# BUILD 10 · THE PROGRAM PACKET — one document, printed once, with the program page as its cover

⚠️ **SCOPED, NOT GREENLIT** — **three rulings closed same-day** (§0, Rulings 4 and 6). 2026-08-30. Indexed from [`next-build-spec.md`](../next-build-spec.md) — 🚩 **see §10, that index still could not be edited and is now FOUR rows behind.** Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

<p><br/></p>

📚 **The ARGUMENTS live in [`print-packet-dl.md`](print-packet-dl.md)** — sections A1–A13, the single claimant for all of them. This file holds the decisions and the mechanism. Same contract as [`hover-text.md`](hover-text.md) / [`hover-text-dl.md`](hover-text-dl.md).

> Michael, 2026-08-30: *"can we render a button that essentially navigates to each policy in the program chain, and does a print of that page, and then stacks them all together to make a packet of all the policies in that program? and then naturally the program page becomes a cover page for that whole program with complete link clickable in pdf viewer."*

---

## One line

**The MECHANISM he described cannot exist. The THING he wants can, it is smaller than he thinks, and it is cheaper than BUILD 8.** A browser cannot navigate, print and stack — but it does not have to, because `chain:` already knows the reading order at BUILD time, and one document printed once is the same PDF with none of the machinery. → **A1**

---

## ✅ §1 — THE SHAPE

**One GENERATED page per program, at `<program-path>/packet/`.** The program page's own body is sheet one; each page named in `chain:` follows, each starting on a fresh sheet. **The "button" is a link to that page.** One dialog, one file, one PDF.

<p><br/></p>

✅ It is the seventh file published via `File.generated` and the first a reader is meant to open. → **A1**  
⭐ The word `packet` is already in the codebase three times with nothing behind it, so the vocabulary is consistent and the cost was partly pre-paid. → **A2**

---

## ✅ §2 — RULED 2026-08-30: THE PRINT IS AN ORDINARY PRINT

> *"the print should run just like a manual print command on the page to make sure you get all the theming stripped and header and such that we've defined."*

✅ **CONFIRMED.** `Ctrl+P` on the packet page is the whole mechanism. All five sheets in `_PRINT_ASSETS` apply, the chrome-off list applies, the corner stamp applies. 🚫 **THERE IS NO SECOND PRINT PATH AND NONE MAY BE BUILT.**

<p><br/></p>

🔴 **CORRECTION TO THE ASK: "all the theming stripped" is NOT what the print layer does, and the packet depends on that.** `print.css` applies `print-color-adjust: exact` narrowly, to *"elements whose MEANING is carried by a colour"* — so it strips **chrome and ground** and **keeps semantic colour**. A `!!! danger` border printing grey is a regression, not a target. → **A3**

<p><br/></p>

🚫 **THE PACKET PAGE MUST NOT AUTO-FIRE `window.print()` ON LOAD.** Legal, and it defeats §5: the cover contents list is the only place a human can catch a short packet. **The button NAVIGATES; the packet page carries a one-line print affordance that does not itself print.** → **A3**

---

## 🔴 §3 — ANCHOR COLLISION IS THE ACTUAL BUILD WORK

Nine pages in one id namespace is five `#overview` anchors, and every link resolves to the first. 🔴 **IT HALF-WORKS — right sheet for entry one, wrong sheet for two through nine, nothing reports it, and a PDF has no console.**

<p><br/></p>

✅ **Namespace every id by chain position** (`#overview` → `#s3-overview`), in two ordered passes per section:

1. **Rewrite ids** on every element carrying one, plus Material's heading-permalink anchors.
2. **Rewrite hrefs:**

| Link | Becomes | Why |
|---|---|---|
| `#frag` (same page) | `#sN-frag` | stayed inside its own section |
| relative path to a page **IN** the packet | `#sM-...` | ⭐ the internal jump — the "clickable" he asked for |
| relative path to a page **NOT** in the packet | the **absolute site URL** | 🔴 a relative href in a PDF is dead; there is no base document |
| absolute `http(s)` URL | untouched | already resolvable off paper |
| `@id:` / `@term:` / `@peer:` | resolved FIRST, then classified above | the registries run before this; never re-implement them |

<p><br/></p>

🔴 **Row three is the silent one.** A relative link surviving into a PDF opens nothing, or resolves against whatever directory the file was saved in. **A distributed safety packet whose citations do nothing is a compliance failure that looks like a working document** — the same sentence `objects/program.yml` writes about a form with no `?Program_ID=`.

<p><br/></p>

⚠️ **The base URL comes from the source BUILD 6 §1 flagged**, with the same blast radius: `publish-default.yml` overrides `base_url` per publishing path, and **a packet is in the reprint category.** Read the resolved value; never assume it.

---

## ⚠️ §4 — THE "CLICKABLE IN PDF VIEWER" HALF IS UNVERIFIED

**Nobody here has proven Chrome print-to-PDF emits real link annotations for `#fragment` jumps.** I believe it does; this file will not pretend otherwise. It is a browser-split risk on a site J28 already lost four attempts to, and **the cover's contents list IS the outline, so a failure costs BOTH navigation mechanisms at once.** → **A4**, **A5**

<p><br/></p>

✅ **Ruling 1, and it is a ten-minute experiment:** build one two-section packet by hand, print from Chrome, click a cover entry. **It decides whether the cover is an INDEX or a LIST.**

---

## 🚫 §5 — WHAT A PACKET CANNOT HAVE

| Wanted | Verdict |
|---|---|
| **"Page 3 of 27"** | 🚫 Blink has never implemented `@page` margin boxes — the declaration parses and does nothing |
| **a PDF bookmark outline** | 🚫 not emitted by print-to-PDF; nothing in CSS asks for it |
| **WeasyPrint to get both** | 🚫 **REFUSED, not deferred** — a second renderer, and §2's ruling closes it independently |

<p><br/></p>

⚠️ The browser's own print footer is the only page-number path and it stamps a URL and date in a font nobody chose — **a provenance decision, not a toggle** (Ruling 7). → **A5**

---

## 🔴 §6 — COVERAGE IS REPORTED OR THE FEATURE IS A LIE

🔴 **A nine-section packet built from a ten-id chain is indistinguishable from a correct nine.** The cover lists what it found, nobody counts, **and somebody signs a completion form for material that was never in the document.**

<p><br/></p>

✅ **Report per program: ids declared · sections emitted · every id that failed to resolve, BY NAME.** ⚠️ A **defect** bucket, never inventory — inventory buckets fire every build and train everyone to ignore annotations (BUILD 2 Piece A).

<p><br/></p>

🔴 **Inherited and it will bite: the first-declaration rule** already made every program resolve to **ZERO** steps once. A packet built in that state is a cover page with nothing behind it, and zero sections is a valid document. → **A6**

---

## 🔴 §7 — AN AGGREGATOR IS A LEAK SURFACE

`nav: hidden` is a curtain — the page is still built and still resolves by `@id`. 🔴 **A packet brings a curtained page to the reader stapled to a cover, in a file that leaves the site.**

<p><br/></p>

✅ **Resolve every chain id through `visibility.py`, never `state.PAGES` directly.** An id resolving to a page the reader-facing site excludes is a **reported finding** — never a silent omission, never a silent inclusion. ⚠️ `uritp-safety`'s content repo is 🔒 PRIVATE while this engine is PUBLIC, so the visibility judgment cannot be carried from the repo it renders. → **A7**

---

## ✅ §8 — PRINT IDENTITY: LETTERHEAD ONCE, PER-POLICY FOOT ALWAYS

| Mark | In a packet | Why |
|---|---|---|
| **letterhead** (BUILD 5) | **cover only** | it identifies the DOCUMENT; sheet one already has three claimants |
| **corner build stamp** | **every sheet, unchanged** | provenance, unconditional by design |
| **policy id + revision** | **every sheet of that policy** | 🔴 a sheet pulled out of a packet must still say what it is |

<p><br/></p>

⚑ **A PACKET IS NOT A DOCUMENT, IT IS A BINDING** — people photocopy four sheets and hand them to a crew. Hawthorne owns that floor. ⚠️ **BUILD 5 §5's unverified build-stamp claim is now BLOCKING**, because row two assumes that mark exists. → **A8**

---

## 🚫 §9 — `{.new-page}` IS REFUSED IN A PACKET

Invalidation **number nine**, and the first where every authored break is invalidated **by definition rather than by accident** — the break did not get worse, it stopped referring to anything. **Section boundaries are the only breaks the packet honours, and it owns those.** This promotes print-type.css §8's standing recommendation to a refusal. → **A9**

---

## ✅ §10 — THE COVER, THE QR, AND THE BUTTON

✅ On paper the embedded form is hidden and **the QR is the route** (ruled 2026-08-29: *"paper routes a reader to the live form instead of impersonating it"*), carrying its fallback link **and `?Program_ID=`** — the prefill param is the record.

<p><br/></p>

🚫 **`qr: false` is REFUSED on a packet cover.** On one sheet it removes the only route to the form; on a packet it removes the only route for the entire program.

<p><br/></p>

🚫 **The button does not print** — `assets/flow.css` already says it: *"A BUTTON ON PAPER IS A LIE."* It joins the chrome-off list in the commit that creates it, along with the packet page's print affordance. ⚠️ **And it is NOT a fourth footer** — rejected by name on 08-19. → **A11**

---

## ⭐ §11 — THE BUILD 8 SEAM

✅ **The packet is on Feature A's side and does not touch B.** It holds **zero** reader state, so `datatable.py`'s law is satisfied rather than strained. **It is the print feature BUILD 8's expensive half was never needed for.**

<p><br/></p>

⚠️ **Precedence must be PACKET > PAGE** if BUILD 8 Feature A ships. 🚩 **BUILD 5's letterhead is a hard prerequisite for §8 and has not landed** — `print-identity.css` does not exist at HEAD. Do not build it inside this PR. → **A12**

---

## ⏳ Rulings

**1. 🔴 OPEN — do link annotations survive Chrome print-to-PDF, including `#fragment` jumps?** §4. Ten minutes, and nothing else should start first.

**2. OPEN — is the packet CHROME-ONLY, stated in the report?** If §4 passes in Blink and fails in WebKit, that is a documented constraint on the artifact.

**3. OPEN — route through `visibility.py`, or refuse any chain id that is not `public`?** §7. **Recommend refuse-and-report:** a packet is a distribution channel, not a reader.

**4. ✅ CLOSED — DECLARED IN FRONTMATTER, NOT AUTOMATIC.** Michael: *"it should be front matter defined on any type: program to say like `export: available` to render a button."* The automatic-with-opt-out recommendation is **overruled**, correctly.

> ⚠️ **The KEY is agreed; the VALUE `available` is the wrong shape.** It is a boolean wearing a status costume, nothing validates a VALUE in the `objects/` family, and `export:` reads as a second `status:` axis. ✅ **Recommend `export: [packet]`** — a closed-set list, unknown kinds **reported**. 🚩 His call; `export: true` also works. **What must not ship is a free-text status word.** → **A10**

**5. OPEN — does the packet honour BUILD 8's per-page `print:` block?** §11. **Recommend no: PACKET > PAGE, stated in the report.**

**6. ✅ CLOSED — BOTH, AND THE HOUSE PATTERN ALREADY ANSWERED IT.** `export:` DECLARES; a body directive (`!!! export`) PLACES it; with no directive it renders automatically **inside the flow strip's block**. ⭐ Exactly the `forms:` split he praised on 08-19 — a fold-in, not a new mechanism. → **A11**

**7. OPEN — does the browser print-footer page number get switched on?** §5. Provenance, his call, not a default.

---

## ⚠️ §12 — FILES, AND THE INDEX ROW THAT STILL COULD NOT BE ADDED

🔴 **MEASURE EVERY ROW AT THE MOMENT YOU ACT. Do not quote this table** — this repo records a 77% drift on one such row, and a size written into prose is wrong within two days, every time.

<p><br/></p>

| File | At the read behind this spec | Change |
|---|---|---|
| **NEW** `docrender/packet.py` | — | walks `chain:`, namespaces ids, rewrites hrefs, emits via `File.generated` |
| **NEW** `assets/print-packet.css` | — | cover rules, section breaks, its own chrome-off rule |
| `docrender/program.py` | 17,659 B (blob `89f4a57`) | + the button and the `!!! export` directive. **Nothing else.** |
| `objects/program.yml` | 9,708 B | one `optional:` key — `export`, per Ruling 4 |
| `docrender/instance.py` | 23,047 B per BUILD 8 §7 | 🚫 **past the ceiling. Not the home for any of this.** |
| `assets/print-type.css` | 22,289 B per BUILD 8 §7 | 🚫 **~239 B of headroom. Do not open it.** |
| `next-build-spec.md` | **32,840 B** (blob `2c082a6`) | 🚩 **NOT EDITED.** |

<p><br/></p>

🚩 **FOUR ROWS OWED: BUILDS 7, 8, 9, 10.** `print-control.md` §7 said three, eight hours earlier — **the debt compounds at one row per spec.** 🔴 **And §7's framing was wrong:** that file is READABLE whole, the blocker is the **write** cap alone, and the two point at different seams. ✅ **Fix: lift BUILDS 1 and 2 into `specs/`, leaving a ~4 KB index.** → **A13**

<p><br/></p>

⚠️ **This file crossed its own ceiling in the commit after documenting it — 24,169 B → 30,283 B in seven minutes, over the write cap.** The split to `print-packet-dl.md` is that debt paid, before the PR merged. **The sidecar is the home for arguments now; do not grow this file back.** → sidecar header.

---

## Sequence

1. 🔴 **Ruling 1 — print one hand-built two-section packet and click the cover.** Everything downstream is shaped by the answer.
2. **Move BUILDS 1 and 2 out of `next-build-spec.md`**, then add rows 7–10. A pure move, and it unblocks every future spec.
3. **`packet.py`, sections only** — chain walk, section breaks, coverage reporting. **No cover, no links.** A stack of policies is already the useful half.
4. **Ids and hrefs** (§3) — the real work.
5. **The cover** — contents list, QR, letterhead if BUILD 5 has landed.
6. **The button and the `!!! export` directive** last — a few lines, and untestable without the rest.

<p><br/></p>

🚫 **Do not start with the button.** It is the part he described and the part that means nothing until step 5.
