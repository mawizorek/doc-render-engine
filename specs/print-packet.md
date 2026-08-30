# BUILD 10 — THE PROGRAM PACKET: one document, printed once, with the program page as its cover

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-30. Indexed from [`next-build-spec.md`](../next-build-spec.md) — 🚩 **see §12, that index STILL could not be edited, and it is now FOUR rows behind.** Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

> Michael, 2026-08-30: *"in the doc render spec the safety docs and a page type: program — can we render a button that essentially navigates to each policy in the program chain, and does a print of that page, and then stacks them all together to make a packet of all the policies in that program? and then naturally the program page becomes a cover page for that whole program with complete link clickable in pdf viewer."*

---

## One line

**The MECHANISM he described cannot exist. The THING he wants can, it is smaller than he thinks, and it is cheaper than BUILD 8.** A browser cannot navigate, print and stack — but it does not have to, because `chain:` already knows the reading order at BUILD time, and one document printed once is the same PDF with none of the machinery.

<p><br/></p>

⭐ **The whole spec is that inversion.** Everything below is either the consequence of it or a trap inside it.

---

## 🔴 §1 — THE BLOCKING FINDING: NAVIGATE-PRINT-STACK IS NOT A THING A BROWSER CAN DO, AND THE REASON MATTERS MORE THAN THE FACT

Three separate walls, none of them a gap somebody could close:

- **`window.print()` prints the current document and nothing else.** There is no API that prints a document you are not on, and no API that concatenates two print jobs.
- **A print job is USER-MEDIATED.** Nine policies is nine dialogs and nine files with nine filenames. A reader who wanted nine files already had nine pages.
- **There is no PDF in the page to merge.** The browser hands the PDF to the operating system, not to JavaScript. **A merge step has nothing to merge.**

<p><br/></p>

🚫 **AND THE IFRAME TRICK, WHICH IS THE ONE SOMEBODY WILL PROPOSE, DOES NOT HELP:** printing an iframe prints *that document alone*. It is the same wall wearing a frame.

<p><br/></p>

⚑ **THE GENERALISATION, AND IT IS THE SPINE OF THIS BUILD: HE ASKED FOR A LOOP BECAUSE HE WAS PICTURING A READER DOING IT BY HAND. THE ENGINE IS NOT A READER — IT ALREADY HOLDS EVERY PAGE IN MEMORY AT ONCE.** `chain:` is resolved at `on_nav`, every page in it is built in the same process, and the flow strip proves the graph is already walkable in both directions. **So the aggregation belongs where the aggregation is free, and that is nine hours before anybody opens a print dialog.**

<p><br/></p>

✅ **THE SHAPE: one GENERATED page per program, at `<program-path>/packet/`.** The program page's own body becomes sheet one; each page named in `chain:` follows, each starting on a fresh sheet. The "button" is a link to that page. **One dialog, one file, one PDF.**

<p><br/></p>

⭐ **AND THE PRECEDENT IS ALREADY LOAD-BEARING RATHER THAN HYPOTHETICAL.** BUILD 2 ruling 1 was partly overturned on exactly this ground: *"a GENERATED page never enters the content repo, which is what the [purity] rule is about, and `assets.py` already publishes six such files via `File.generated`."* **A packet is the seventh, and it is the first one a reader is meant to open.**

---

## ⭐ §2 — THE WORD IS ALREADY IN THE CODEBASE THREE TIMES, WITH NOTHING BEHIND IT

This is not a net-new idea and it should not be specced as one. `packet` appears at HEAD in three places, every one of them **assuming** the artifact exists:

| Where | What it says |
|---|---|
| `assets/flow.css` | *"print-flow.css already forces every `<details>` open, so a printed packet lists every program a page belongs to"* |
| `docrender/lede.py` | the `Posted by` label is engine-supplied *"to keep the phrasing identical across every sheet in a printed packet"* |
| `instances/uritp-safety/site.yml` | the same rule, from the site side: no per-site label, *"what keeps every sheet in a printed packet phrased identically"* |

<p><br/></p>

⚑ **SO TWO DESIGN DECISIONS HAVE ALREADY BEEN MADE IN SERVICE OF A PACKET NOTHING BUILDS.** The global `Posted by` label and the forced-open `<details>` are both correct, both argued, and both paying rent on an artifact that does not exist — which means **the cost of this build was partly pre-paid and the vocabulary is already consistent.** ⭐ *Worth recording because it is the good version of the shape this repo usually catches as rot: a word used consistently across three files by people who each assumed somebody else had built the thing.*

<p><br/></p>

⚠️ **It also means the packet is not free to get wrong.** Those two rules are now testable for the first time, and if a packet renders per-sheet labels that disagree, the defect is in this build and not in theirs.

---

## 🔴 §3 — ANCHOR COLLISION IS THE ACTUAL BUILD WORK. THE STACKING IS THE EASY HALF

Nine pages concatenated into one document is nine sets of heading ids in one id namespace. `## Overview` on five policies is **five `#overview` anchors**, and every link to any of them resolves to the first.

<p><br/></p>

🔴 **AND IT HALF-WORKS, WHICH IS WHY IT IS THE FINDING.** The cover's table of contents will appear to function — every link jumps *somewhere*, on the right sheet for entry one and the wrong sheet for entries two through nine. **Nothing reports it, and a PDF has no console.**

<p><br/></p>

✅ **Namespace every id by its chain position, and rewrite every intra-packet link to match** (`#overview` → `#s3-overview`). Two ordered passes, per section, no exceptions:

1. **Rewrite ids** on every element carrying one, plus Material's own heading-permalink anchors.
2. **Rewrite hrefs** — and this is where the real classification lives:

| Link | Becomes | Why |
|---|---|---|
| `#frag` (same page) | `#sN-frag` | it stayed inside its own section |
| a relative path to a page **IN** the packet | `#sM-...` | ⭐ **the internal jump, and this is the "clickable" he asked for** |
| a relative path to a page **NOT** in the packet | the **absolute site URL** | 🔴 a relative href in a PDF is dead — there is no base document |
| an absolute `http(s)` URL | untouched | already resolvable off paper |
| `@id:` / `@term:` / `@peer:` | resolved FIRST, then classified above | the registries run before this; never re-implement them |

<p><br/></p>

🔴 **THE THIRD ROW IS THE SILENT ONE AND IT IS THE REASON THIS TABLE IS WRITTEN OUT.** A relative link that survives into a PDF is not a broken link a reader can see — it is a link that opens nothing, or worse, resolves against whatever directory the file was saved in. **A distributed safety packet whose citations do nothing is a compliance failure that looks like a working document,** which is the same sentence `objects/program.yml` already writes about a form with no `?Program_ID=`.

<p><br/></p>

⚠️ **The base URL for row three comes from the SAME source BUILD 6 §1 flagged**, and it carries the same blast radius: `publish-default.yml` overrides `base_url` per publishing path, and *"a poisoned `doc-index.json` is repaired by the next publish; a poisoned QR is repaired by reprinting."* **A packet is in the reprint category.** Read the resolved value, do not assume it.

---

## ⚠️ §4 — THE "CLICKABLE IN PDF VIEWER" HALF IS UNVERIFIED, AND IT IS THE PART HE IS EXCITED ABOUT

The payoff rests on one property nobody in this repo has tested: **that Chrome's print-to-PDF emits real link annotations for `<a href>`, including in-document `#fragment` jumps.** I believe it does. **I have not proven it, and this file will not pretend otherwise.**

<p><br/></p>

🔴 **IT IS ALSO A BROWSER-SPLIT RISK ON A SITE THAT HAS ALREADY BEEN BITTEN BY ONE.** J28 spent four attempts on a table that rendered correctly in Chrome and wrongly in Orion, and the cause was *"WebKit resolving container queries differently from Blink"* — a third hypothesis nobody had listed. **Link-annotation emission is exactly that class of property: invisible on screen, browser-specific, and only observable in the artifact.** Safari and the macOS system print path are the specific doubt.

<p><br/></p>

✅ **This is Ruling 1, and it is a ten-minute experiment, not a research project:** build one two-section packet by hand, print it from Chrome, open the PDF, click a cover entry. **The answer decides whether the cover is a clickable index or a printed contents list**, and those are different features with the same markup.

<p><br/></p>

⚑ *The reason it is a ruling rather than an assumption: this log's standing scar is "a guess wearing the clothes of a measurement is camouflaged by the real measurements around it." §3's link table is measured. This section is not, and it is adjacent to it.*

---

## 🔴 §5 — WHAT A PACKET CANNOT HAVE, STATED UP FRONT SO NOBODY SPENDS A DAY ON IT

Two things a distributed packet obviously wants, and Chrome gives neither from CSS:

<p><br/></p>

| Wanted | Mechanism | Verdict |
|---|---|---|
| **"Page 3 of 27"** | `@page { @bottom-center { content: counter(page) } }` | 🚫 **Blink has never implemented `@page` margin boxes.** The declaration parses and does nothing. |
| **a PDF bookmark outline** | headings → outline entries | 🚫 not emitted by print-to-PDF; nothing in CSS asks for it |

<p><br/></p>

⚠️ **The browser's own print-dialog header/footer can put a page number on the sheet, and it is the only path that exists.** It also stamps a URL and a date in a font nobody chose, and `print.css` already strips repo references from our own chrome twice over — **so "turn on the browser footer" is a decision about provenance, not a convenience toggle.** Named, not decided.

<p><br/></p>

✅ **THE COVER'S TABLE OF CONTENTS *IS* THE OUTLINE, AND THAT IS THE HONEST WORKAROUND RATHER THAN A CONSOLATION.** A clickable list on sheet one does the job a bookmark pane does, it survives photocopying, and it is the artifact he already described. 🔴 **Which loops it straight back to §4: if link annotations do not survive, the packet loses BOTH navigation mechanisms at once.** That is why §4 is Ruling 1 and not a footnote.

<p><br/></p>

🚫 **AND THE FIX IS NOT A PDF LIBRARY. THIS IS A REFUSAL, NOT A DEFERRAL.** WeasyPrint would give real margin boxes, a real outline and guaranteed annotations. It would also add cairo, pango and gdk-pixbuf to a `requirements.txt` whose own header argues that *"an unpinned transitive dependency is an unpinned build"* and which refuses **Pillow** on the grounds that `segno` writing PNG natively is *"the only reason a new dependency is defensible."* ⚑ **A build-time PDF renderer is a SECOND renderer: two engines, two layouts, and the printed artifact stops being the page anybody previewed.** The packet is HTML that Chrome prints, or it is a different product.

---

## ⚠️ §6 — THE CHAIN BECOMES LOAD-BEARING TWICE, SO COVERAGE IS REPORTED OR THE FEATURE IS A LIE

`objects/program.yml` already carries the trap: a page with `hide: footer` and no flow has **zero** navigation, *"and nothing reports it."* A packet adds a second consumer of the same list, with a worse failure mode.

<p><br/></p>

🔴 **A NINE-PAGE PACKET BUILT FROM A TEN-ID CHAIN IS INDISTINGUISHABLE FROM A CORRECT NINE-PAGE PACKET.** The cover lists what it found. Nobody counts. Somebody signs a completion form for material that was never in the document.

<p><br/></p>

✅ **Report, per program, in its own bucket: ids declared · sections emitted · every id that failed to resolve, BY NAME.** ⚠️ And it is a **defect** bucket, not inventory — BUILD 2 Piece A's rule is that inventory buckets fire on every build and *"annotating them trains everyone to ignore annotations."* A chain that dropped a page is not inventory.

<p><br/></p>

🔴 **ALSO INHERITED, AND IT WILL BITE: THE FIRST-DECLARATION RULE.** `program.yml` records that `20-policies/index.md` declaring a chain over the same nine policies made **every program resolve to ZERO steps**, because it sorted first alphabetically. **A packet built during that state is a cover page with nothing behind it** — and it would have looked like a working build, because zero sections is a valid document. The straggler report was already re-scoped once for this exact reason (folder-scoped on a type whose whole point is crossing folders).

---

## 🔴 §7 — A PACKET IS AN AGGREGATOR, AND AN AGGREGATOR IS A LEAK SURFACE

`docrender/visibility.py` builds a page only `if status in ("unlisted", "public")`, and `nav: hidden` is *"a curtain"* — the pages are still built, still resolve by `@id`, still in search.

<p><br/></p>

🔴 **SO A PACKET BUILDER THAT WALKS `chain:` AND CONCATENATES WHAT IT FINDS WILL HAPPILY PULL A CURTAINED PAGE INTO A DISTRIBUTABLE PDF.** Every prior instance of this shape in the repo was a page a reader had to go looking for. **A packet brings it to them, stapled to a cover page, in a file that leaves the site.**

<p><br/></p>

✅ **The packet resolves every id through `visibility.py`, never through `state.PAGES` directly**, and a chain id that resolves to a page the reader-facing site excludes is a **reported finding**, never a silent omission and never a silent inclusion. ⚠️ **`uritp-safety` is the site this ships on and its content repo is 🔒 PRIVATE** while this engine is PUBLIC — so the visibility judgment cannot be carried from the repo it renders. Same rule as the repo-referent gate, one layer down.

---

## ✅ §8 — PRINT IDENTITY IN A PACKET: LETTERHEAD ONCE, PER-POLICY FOOT ALWAYS

The naive answer is that a packet is one document and therefore carries one identity. **That is wrong for the reason safety documents are always wrong about this: a packet gets split.**

<p><br/></p>

| Mark | In a packet | Why |
|---|---|---|
| **letterhead** (BUILD 5) | **cover only** | it identifies the DOCUMENT; nine copies is noise, and sheet-one vertical space already has three claimants |
| **corner build stamp** | **every sheet, unchanged** | it is provenance and it is unconditional on every page of every site by design |
| **policy id + revision** | **every sheet of that policy** | 🔴 a sheet pulled out of a packet must still say what it is |

<p><br/></p>

⚑ **THE RULE UNDERNEATH IT: A PACKET IS NOT A DOCUMENT, IT IS A BINDING.** People photocopy the four sheets they need and hand them to a crew. **Every mark that identifies a POLICY stays per-policy; only marks that identify the PACKET collapse to the cover.** Hazard Hawthorne owns the floor here on the same grounds as legibility — a policy sheet that cannot identify itself is a safety defect, not a layout preference.

<p><br/></p>

⚠️ **BUILD 5 §5's unverified claim is now blocking rather than pending:** the build stamp may not print at all, because `print.css` hides `.md-footer-meta` and `display: none` on an ancestor cannot be opted back out of by a descendant. **The row above assumes that mark exists on every sheet.** One preview settles it, and BUILD 5 has owed that preview since 08-19.

---

## 🚫 §9 — `{.new-page}` IS INVALIDATED FOR THE NINTH TIME, AND THIS IS WHERE IT BECOMES A REFUSAL

`print-type.css` §8 keeps a running count of hand-placed page breaks invalidated by a change to the print layer. **It stands at eight.** BUILD 8 §5c predicted the ninth would come from a reader-facing dial *"with no build and no report."*

<p><br/></p>

🔴 **IT ARRIVES HERE INSTEAD, AND IT IS WORSE IN ONE SPECIFIC WAY: EVERY AUTHORED BREAK IS INVALIDATED BY DEFINITION, NOT BY ACCIDENT.** A policy authored to break after its second heading is now at an arbitrary offset inside a 27-sheet document. **The break did not get worse — it stopped referring to anything.**

<p><br/></p>

✅ **Recommend: the packet IGNORES `{.new-page}` outright and lets `print-flow.css` do the work**, and this build promotes §8's standing recommendation from *"do not author them"* to a refusal. ⚑ *A page-level break instruction is meaningless in a document the page does not know it is in, and a rule that is only true when a page is read alone is not a rule.* Section boundaries are the only breaks the packet honours, and it owns those.

---

## ⚠️ §10 — THE COVER IS BOTH ENTRANCE AND EXIT, AND THE FORM RULING ALREADY DECIDED HOW

`program.yml` argues the program page is *"BOTH the entrance and the exit"* and that `collapsed: true` exists so nobody certifies material they have not read. **A packet cover is the same page with the sequencing removed** — a reader holding paper has already been handed everything.

<p><br/></p>

✅ **On paper the embedded form is hidden and the QR is the route, by the 2026-08-29 ruling: *"paper routes a reader to the live form instead of impersonating it."*** So the cover carries the completion QR, with its fallback link, **and `?Program_ID=` on the payload** — the prefill param is the record, and a packet whose form collects unattributable submissions is BUILD 6's poisoned-QR case with a compliance failure attached.

<p><br/></p>

🚫 **`qr: false` IS REFUSED ON A PACKET COVER**, on BUILD 8 §4's reasoning and one step harder: on a single sheet it removes the only route to the form; **on a packet it removes the only route for the entire program.**

<p><br/></p>

🚫 **AND THE BUTTON MUST NOT PRINT — the precedent is already written, verbatim, in the file it belongs to.** `assets/flow.css`: *"A BUTTON ON PAPER IS A LIE."* The packet link joins the chrome-off list **in the commit that creates it**, or sheet one carries a picture of the button that made it. ⚠️ **And it is NOT a fourth footer.** Michael rejected exactly that shape on 08-19 — *"all this other foot matter... is that what I'm supposed to click next?"* — so the button sits with the flow strip or in the program body, never in new foot matter of its own.

---

## ⭐ §11 — THE SEAM WITH BUILD 8, AND IT IS THE ARGUMENT FOR DOING THIS ONE FIRST

BUILD 8 splits print work into **A** (per-page frontmatter defaults, cheap) and **B** (a reader-facing widget, *"a new state category"*). Its Ruling 1 recommends A alone.

<p><br/></p>

✅ **THE PACKET IS ON A'S SIDE OF THAT LINE AND DOES NOT TOUCH B.** `datatable.py`'s law — *"THE RENDERER NEVER LEARNS WHAT DEVICE IT IS ON, AND CANNOT"* — is satisfied rather than strained: the packet is one file built from declared data, identical for every reader, holding **zero** reader state. ⚑ *It is the print feature BUILD 8's expensive half was never needed for, and it delivers more than the widget would have.*

<p><br/></p>

⚠️ **One real coupling:** if BUILD 8 Feature A ships, a `print:` block on a policy page is a per-page declaration landing inside a document that is not that page. **Precedence must be PACKET > PAGE**, on BUILD 8 §3's own principle that *"an override expressed as a value beats an override expressed as a selector."* A per-page `base: 11pt` inside a 27-sheet packet is one policy in a different size, which reads as a defect.

<p><br/></p>

🚩 **BUILD 5's letterhead is a hard prerequisite for §8 and it has not landed** — `print-identity.css` does not exist at HEAD. **The packet can ship without a cover letterhead and would look unfinished.** Sequence accordingly; do not build the letterhead inside this PR.

---

## ⏳ Rulings needed

1. 🔴 **Do link annotations survive Chrome print-to-PDF, including `#fragment` jumps?** §4. **Ten-minute experiment, and it decides whether the cover is an INDEX or a LIST.** Nothing else should start first.
2. **Is the packet CHROME-ONLY, stated in the report?** If §4 passes in Blink and fails in WebKit, that is a documented constraint on the artifact — the same shape as J28's browser split, handled up front instead of after four attempts.
3. **Does the packet route through `visibility.py`, or does it refuse any chain id that is not `public`?** §7. **Recommend refuse-and-report:** `unlisted` is a curtain for readers, and a packet is a distribution channel, not a reader.
4. **Opt-in or automatic?** A `packet: true` key on the program, or every `type: program` gets one. **Recommend automatic with `packet: false` to opt out** — a program that cannot be printed as a packet is the exception, and a key nobody sets is a feature nobody finds. ⚠️ This is a new `objects/program.yml` `optional:` entry either way.
5. **Does the packet honour BUILD 8's per-page `print:` block?** §11. **Recommend no: PACKET > PAGE, and say so in the report.**
6. **Where does the button live?** §10 rules out new foot matter. **Recommend inside the flow strip's block**, which is already the only navigation on a program page by the `hide: footer` contract.
7. **Does the browser print-footer page number get switched on?** §5. Provenance question, Michael's call, not a default.

---

## ⚠️ §12 — FILES, AND THE INDEX ROW THAT STILL COULD NOT BE ADDED

🔴 **MEASURE EVERY ROW AT THE MOMENT YOU ACT. Do not quote this table** — `next-build-spec.md` records a 77% drift on one row in this repo and the standing rule is that a size written into prose is wrong within two days, every time.

<p><br/></p>

| File | At the read behind this spec | Change |
|---|---|---|
| **NEW** `docrender/packet.py` | — | walks `chain:`, namespaces ids, rewrites hrefs, emits via `File.generated` |
| **NEW** `assets/print-packet.css` | — | cover rules, section breaks, and its own chrome-off rule |
| `docrender/program.py` | 17,659 B (blob `89f4a57`) | + the button only. **Nothing else.** |
| `objects/program.yml` | 9,708 B | one `optional:` key (Ruling 4) |
| `docrender/instance.py` | 23,047 B per BUILD 8 §7 | 🚫 **past the ceiling. Not the home for any of this.** |
| `assets/print-type.css` | 22,289 B per BUILD 8 §7 | 🚫 **~239 B of headroom. Do not open it.** |
| `next-build-spec.md` | **32,840 B** (blob `2c082a6`) | 🚩 **NOT EDITED.** |

<p><br/></p>

🔴 **AND THE INDEX FINDING HAS SHARPENED, WHICH IS A CORRECTION TO `print-control.md` §7 RATHER THAN AN ECHO OF IT.** That section says the file *"is 32,840 B"* and treats it as unreadable. **It read back WHOLE at HEAD today.** So the blocker is not the read path at all — it is the **write** cap alone: *large files (>~30KB) never go through `create_or_update_file`*, LOCKED 2026-07-02 after it corrupted a file four times in one session. ⚑ *A file can be perfectly readable and still be unwritable, and conflating the two costs the wrong fix: "split it so it can be read" and "split it so it can be WRITTEN" point at different seams.*

<p><br/></p>

🚩 **FOUR ROWS ARE NOW OWED: BUILDS 7, 8, 9 AND 10.** print-control §7 said three, this morning. **The debt is compounding at one row per spec**, and the index's own instruction — *"if it is wrong again, delete it rather than refresh it"* — has now been earned twice over.

<p><br/></p>

✅ **The fix is unchanged and it is a pure move: lift BUILDS 1 and 2 into `specs/`**, which drops this file to a ~4KB index and makes it writable again. The header already asks for it in its own words. **That is the change that stops this recurring, and it should happen before a fifth spec is written.**

---

## Sequence

1. 🔴 **Ruling 1 — print one hand-built two-section packet and click the cover.** Everything downstream is shaped by the answer, and it costs ten minutes.
2. **Move BUILDS 1 and 2 out of `next-build-spec.md`**, then add rows 7 through 10. A pure move, independently reviewable, and it unblocks every future spec.
3. **`packet.py`, sections only** — chain walk, section breaks, coverage reporting. **No cover, no links.** A stack of policies is already the useful half.
4. **Ids and hrefs** (§3), which is where the real work is.
5. **The cover** — contents list, QR, letterhead if BUILD 5 has landed.
6. **The button** (§10) last, because it is one line and it is the only part that cannot be tested without the rest.

<p><br/></p>

🚫 **Do not start with the button.** It is the part he described and it is the part that means nothing until step 5.
