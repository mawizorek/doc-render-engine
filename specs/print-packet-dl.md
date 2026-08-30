# BUILD 10 sidecar — the arguments behind the packet rulings

Companion to [`print-packet.md`](print-packet.md). **This file is the SINGLE CLAIMANT for every argument in it** — the spec states conclusions and points here; it does not restate the reasoning. Same contract as [`hover-text-dl.md`](hover-text-dl.md), [`../docrender/forms-dl.md`](../docrender/forms-dl.md), [`../docrender/views-dl.md`](../docrender/views-dl.md) and [`../docrender/buildstamp-dl.md`](../docrender/buildstamp-dl.md).

<p><br/></p>

⚠️ **Why this file exists, and it is the least flattering possible reason.** `print-packet.md` shipped at **24,169 B** at 15:17 ET on 2026-08-30, already ~1.7 KB past the ~22.5 KB read ceiling it cites at other files, with a note in its own §12 saying *"the NEXT substantive edit cuts a sidecar... do not close another ruling in place."* **Three rulings were then closed in place seven minutes later and the file landed at 30,283 B — over the 30 KB write cap, which means one more edit through `create_or_update_file` is the corruption case LOCKED 2026-07-02.** ⚑ *A file that documents a ceiling and then crosses it in the next commit is the exact rot shape this repo has retired three manifests over, and it took eight minutes rather than eight weeks. The split happened before the PR merged, so nothing shipped unwritable — but the instruction was written, ignored by its own author, and only obeyed after the size was read back.* **Read the size back. Every time. It is the only thing that has ever caught this.**

---

## A1 — Why navigate-print-stack cannot exist, and why the reason matters more than the fact

Three separate walls, none of them a gap somebody could close:

- **`window.print()` prints the current document and nothing else.** There is no API that prints a document you are not on, and no API that concatenates two print jobs.
- **A print job is USER-MEDIATED.** Nine policies is nine dialogs and nine files with nine filenames. A reader who wanted nine files already had nine pages.
- **There is no PDF in the page to merge.** The browser hands the PDF to the operating system, not to JavaScript. **A merge step has nothing to merge.**

<p><br/></p>

🚫 **AND THE IFRAME TRICK, WHICH IS THE ONE SOMEBODY WILL PROPOSE, DOES NOT HELP:** printing an iframe prints *that document alone*. It is the same wall wearing a frame.

<p><br/></p>

⚑ **THE GENERALISATION, AND IT IS THE SPINE OF THE WHOLE BUILD: HE ASKED FOR A LOOP BECAUSE HE WAS PICTURING A READER DOING IT BY HAND. THE ENGINE IS NOT A READER — IT ALREADY HOLDS EVERY PAGE IN MEMORY AT ONCE.** `chain:` is resolved at `on_nav`, every page in it is built in the same process, and the flow strip proves the graph is already walkable in both directions. **So the aggregation belongs where the aggregation is free, and that is nine hours before anybody opens a print dialog.**

<p><br/></p>

⭐ **The generated-page precedent is load-bearing rather than hypothetical.** BUILD 2 ruling 1 was partly overturned on exactly this ground: *"a GENERATED page never enters the content repo, which is what the [purity] rule is about, and `assets.py` already publishes six such files via `File.generated`."* **A packet is the seventh, and it is the first one a reader is meant to open.**

---

## ⭐ A2 — The word was already in the codebase three times, with nothing behind it

The packet is not a net-new idea and should never have been specced as one. `packet` appears at HEAD in three places, every one of them **assuming** the artifact exists:

| Where | What it says |
|---|---|
| `assets/flow.css` | *"print-flow.css already forces every `<details>` open, so a printed packet lists every program a page belongs to"* |
| `docrender/lede.py` | the `Posted by` label is engine-supplied *"to keep the phrasing identical across every sheet in a printed packet"* |
| `instances/uritp-safety/site.yml` | the same rule from the site side: no per-site label, *"what keeps every sheet in a printed packet phrased identically"* |

<p><br/></p>

⚑ **TWO DESIGN DECISIONS WERE ALREADY MADE IN SERVICE OF A PACKET NOTHING BUILDS.** The global `Posted by` label and the forced-open `<details>` are both correct, both argued, and both paying rent on an artifact that does not exist — so **the cost of this build was partly pre-paid and the vocabulary is already consistent.**

<p><br/></p>

⭐ *Worth recording because it is the GOOD version of a shape this repo usually catches as rot: a word used consistently across three files by people who each assumed somebody else had built the thing. The bad version is three files disagreeing. This one had one meaning and no implementation.*

<p><br/></p>

⚠️ **It also means the packet is not free to get wrong.** Those two rules become testable for the first time, and if a packet renders per-sheet labels that disagree, the defect belongs to BUILD 10 and not to them.

---

## A3 — Why the print must be an ordinary print, and why "all the theming stripped" is the wrong target

> Michael, 2026-08-30: *"the print should run just like a manual print command on the page to make sure you get all the theming stripped and header and such that we've defined."*

✅ **The confirmation half is what makes the build cheap rather than a concession.** The packet is an ordinary page, so `Ctrl+P` on it is the entire mechanism: all five sheets registered in `_PRINT_ASSETS` apply unconditionally, the chrome-off list applies, the corner stamp applies. ⚑ *This is A5's WeasyPrint refusal arriving from the other direction — the packet is printed by the exact code path every other page is printed by, or the printed artifact stops being the page anybody previewed.*

<p><br/></p>

🔴 **The correction half: `print.css` applies `print-color-adjust: exact` NARROWLY and DELIBERATELY**, to *"elements whose MEANING is carried by a colour"* — a `!!! danger` border, a marker chip, the letterhead. The print layer strips **chrome and ground** and **keeps semantic colour**.

<p><br/></p>

⭐ **AND THE PACKET DEPENDS ON THAT, WHICH IS WHY THE WORD IS WORTH CORRECTING RATHER THAN LETTING PASS.** A packet is distributed and photocopied (A6), and a hazard box printing as a grey box is a `!!! danger` that no longer reads as danger — the thing BUILD 8 §1 already refuses as a reader control (*"Hawthorne's floor, not a preference"*). ⚠️ **A full strip is not a target, it is a regression**, and a future reader holding only the ask would implement it.

### 🚫 Why the packet page must not auto-fire `window.print()`

It is technically legal and identical to a manual print. **It also defeats the coverage check, which is the one thing a human can do that no build can.**

<p><br/></p>

🔴 A short packet is a **valid document** — nine sections from a ten-id chain looks exactly like a correct nine (A6) — so the reader's glance at the cover contents list is the last line of defence, and a dialog that opens before the cover renders spends it. ⚑ *An automatic action is only safe when the thing it skips is worthless. Here the thing it skips is the verification.*

---

## 🔴 A4 — Why the PDF-link question is a ruling and not an assumption

The payoff rests on one untested property: **that Chrome's print-to-PDF emits real link annotations for `<a href>`, including in-document `#fragment` jumps.** I believe it does. It is not proven.

<p><br/></p>

🔴 **IT IS A BROWSER-SPLIT RISK ON A SITE THAT HAS ALREADY BEEN BITTEN BY ONE.** J28 spent four attempts on a table that rendered correctly in Chrome and wrongly in Orion, and the cause was *"WebKit resolving container queries differently from Blink"* — **a third hypothesis nobody had listed.** Link-annotation emission is exactly that class: invisible on screen, browser-specific, observable only in the artifact. Safari and the macOS system print path are the specific doubt.

<p><br/></p>

⚑ *The reason it is a ruling: this log's standing scar is "a guess wearing the clothes of a measurement is camouflaged by the real measurements around it." The link-classification table is reasoned from the source. This is not, and it sits next to it.*

<p><br/></p>

🔴 **And it is load-bearing twice over, because the cover's contents list IS the outline** (A5) — so if annotations do not survive, the packet loses **both** navigation mechanisms at once. That is why it is Ruling 1 rather than a footnote.

---

## 🔴 A5 — What a packet cannot have, and why the fix is not a PDF library

Two things a distributed packet obviously wants, neither available from CSS in Chrome:

<p><br/></p>

| Wanted | Mechanism | Verdict |
|---|---|---|
| **"Page 3 of 27"** | `@page { @bottom-center { content: counter(page) } }` | 🚫 **Blink has never implemented `@page` margin boxes.** The declaration parses and does nothing. |
| **a PDF bookmark outline** | headings → outline entries | 🚫 not emitted by print-to-PDF; nothing in CSS asks for it |

<p><br/></p>

⚠️ **The browser's own print-dialog header/footer is the only page-number path that exists.** It also stamps a URL and a date in a font nobody chose, and `print.css` already strips repo references from our chrome twice over — **so switching it on is a provenance decision, not a convenience toggle.**

<p><br/></p>

✅ **THE COVER'S CONTENTS LIST IS THE HONEST WORKAROUND, NOT A CONSOLATION.** A clickable list on sheet one does a bookmark pane's job, survives photocopying, and is the artifact he described.

### 🚫 The WeasyPrint refusal

It would give real margin boxes, a real outline and guaranteed annotations. It would also add cairo, pango and gdk-pixbuf to a `requirements.txt` whose header argues that *"an unpinned transitive dependency is an unpinned build"* and which refuses **Pillow** on the grounds that `segno` writing PNG natively is *"the only reason a new dependency is defensible."*

<p><br/></p>

⚑ **A build-time PDF renderer is a SECOND RENDERER: two engines, two layouts, and the printed artifact stops being the page anybody previewed.** ✅ A3's ruling closes it independently — *"just like a manual print command on the page"* is incompatible with a second renderer by definition. **The packet is HTML that Chrome prints, or it is a different product.**

---

## 🔴 A6 — Why coverage reporting is not optional

`objects/program.yml` already carries the trap: a page with `hide: footer` and no flow has **zero** navigation, *"and nothing reports it."* A packet adds a second consumer of the same list with a worse failure mode.

<p><br/></p>

🔴 **A NINE-SECTION PACKET BUILT FROM A TEN-ID CHAIN IS INDISTINGUISHABLE FROM A CORRECT NINE.** The cover lists what it found. Nobody counts. **Somebody signs a completion form for material that was never in the document.**

<p><br/></p>

⚠️ **It is a DEFECT bucket, not inventory.** BUILD 2 Piece A's rule: inventory buckets fire on every build and *"annotating them trains everyone to ignore annotations."* A chain that dropped a page is not inventory.

<p><br/></p>

🔴 **THE INHERITED SCAR THAT WILL BITE: THE FIRST-DECLARATION RULE.** `program.yml` records that `20-policies/index.md` declaring a chain over the same nine policies made **every program resolve to ZERO steps**, because it sorted first alphabetically. **A packet built during that state is a cover page with nothing behind it — and it would look like a working build, because zero sections is a valid document.** The straggler report was already re-scoped once for this exact reason (written folder-scoped, on the one type whose whole point is crossing folders).

---

## 🔴 A7 — Why an aggregator is a leak surface

`docrender/visibility.py` builds a page only `if status in ("unlisted", "public")`, and `nav: hidden` is *"a curtain"* — the pages are still built, still resolve by `@id`, still in search.

<p><br/></p>

🔴 **A BUILDER THAT WALKS `chain:` AND CONCATENATES WHAT IT FINDS WILL PULL A CURTAINED PAGE INTO A DISTRIBUTABLE PDF.** Every prior instance of this shape was a page a reader had to go looking for. **A packet brings it to them, stapled to a cover, in a file that leaves the site.**

<p><br/></p>

⚠️ **`uritp-safety` is the site this ships on and its content repo is 🔒 PRIVATE while this engine is PUBLIC**, so the visibility judgment cannot be carried from the repo it renders. Same rule as the repo-referent gate, one layer down.

---

## ⚑ A8 — Why a packet is a BINDING, not a document

The naive answer is that a packet is one document and therefore carries one identity. **That is wrong for the reason safety documents are always wrong about this: a packet gets split.**

<p><br/></p>

People photocopy the four sheets they need and hand them to a crew. **Every mark that identifies a POLICY stays per-policy; only marks that identify the PACKET collapse to the cover.** A sheet pulled out of a packet must still say what it is — Hazard Hawthorne owns that floor on the same grounds as legibility: **a policy sheet that cannot identify itself is a safety defect, not a layout preference.**

<p><br/></p>

⚠️ **BUILD 5 §5's unverified claim becomes blocking here:** the build stamp may not print at all, because `print.css` hides `.md-footer-meta` and `display: none` on an ancestor cannot be opted back out of by a descendant. **The per-sheet provenance row assumes that mark exists.** One preview settles it, and BUILD 5 has owed that preview since 08-19.

---

## 🚫 A9 — `{.new-page}` invalidation number nine, and why it becomes a refusal

`print-type.css` §8 keeps a running count of hand-placed page breaks invalidated by a change to the print layer. **It stands at eight.** BUILD 8 §5c predicted the ninth would come from a reader-facing dial *"with no build and no report."*

<p><br/></p>

🔴 **IT ARRIVES HERE INSTEAD, AND IT IS WORSE IN ONE SPECIFIC WAY: EVERY AUTHORED BREAK IS INVALIDATED BY DEFINITION, NOT BY ACCIDENT.** A policy authored to break after its second heading sits at an arbitrary offset inside a 27-sheet document. **The break did not get worse — it stopped referring to anything.**

<p><br/></p>

⚑ *A page-level break instruction is meaningless in a document the page does not know it is in, and a rule that is only true when a page is read alone is not a rule.* Section boundaries are the only breaks the packet honours, and it owns those.

---

## A10 — Why `export: available` is the wrong shape, and what to build instead

✅ **The frontmatter-declared half is right and overruled the spec's own recommendation correctly.** A program that should not be handed out as a packet is a real case, and silence is the safe default for a distributable artifact (A7).

<p><br/></p>

⚠️ **The VALUE is the problem, and the objection is mechanical rather than aesthetic.** There are exactly two states — there is a packet or there is not — so `available` is **a boolean wearing a status costume**, and it invites `pending`, `soon`, `unavailable`, none of which anything would validate.

<p><br/></p>

🔴 **THE FAILURE IS THE DEAD-CONTROL SHAPE THIS REPO KEEPS FINDING.** Nothing in the `objects/` family validates a VALUE, only a key's presence. So `export: availabe` either passes as truthy and works by accident, or is compared against a literal, silently produces no button, and **nothing reports it.** The `qr.py` scar is the same family in reverse: *"a `print=true`-only code IS INVISIBLE ON SCREEN, so 'it failed to resolve' and 'it resolved and is correctly hidden' are the same blank space to its author."*

<p><br/></p>

🔴 **AND `export` COLLIDES WITH A WORD THE ENGINE ALREADY OWNS.** `status: draft | unlisted | public` governs whether a page is built. `export: available` sits inches away in the same frontmatter block and reads as a second status axis — **two vocabularies for one idea, which is what retired three manifests here.**

<p><br/></p>

✅ **Recommendation, keeping his word and killing the ambiguity: `export: [packet]`** — a LIST of named export kinds validated against a closed set (`markers._SHAPES` is the precedent: *"the closed set of four"*), with an unknown kind **reported, not ignored**. It survives the second export kind he will inevitably want, it cannot be mistaken for a status, and a typo becomes a finding instead of a silent no-op. 🚩 **His call — `export: true` is also correct.** What must not ship is a free-text status word.

---

## ⭐ A11 — Why placement is BOTH, and why that is a fold-in rather than a decision

> Michael: *"maybe i place it or it does so automatically?"*

**`forms:` is the exact precedent, and he is the one who praised it:** the frontmatter DECLARES (*"love that i can define in frontmatter, well outside of the actual body content"*) and a body directive DRAWS (`!!! form "completion"`).

<p><br/></p>

✅ So `export:` declares the packet exists; a body directive places the button exactly where he wants it; with no directive it renders automatically inside the flow strip's block.

<p><br/></p>

⚠️ **The automatic position is CONSTRAINED, not chosen.** `hide: footer` makes the strip the only navigation on a program page, and a second footer was rejected by name on 08-19 — *"all this other foot matter... is that what I'm supposed to click next? It's not actually appearing in the main footer; it's in this other separate footer you created."* **Two footers, and the wrong one looked authoritative.** A packet button in new foot matter of its own repeats that failure exactly.

<p><br/></p>

🚫 **The button does not print.** `assets/flow.css` already says it, verbatim and in the right file: *"A BUTTON ON PAPER IS A LIE."* The packet link and the packet page's own print affordance both join the chrome-off list **in the commit that creates them**, or sheet one carries a picture of the button that made it.

<p><br/></p>

⚑ *A registry plus an optional directive is a fold-in of a shipped mechanism, not a new one — same split as `data:` slots and the `links:` registry, and the third time this pattern has been the right answer. Fold-in Frank does not need seating for a pattern that has already won twice.*

---

## ⚠️ A12 — The BUILD 8 seam, and why the packet is the cheap half

BUILD 8 splits print work into **A** (per-page frontmatter defaults, cheap) and **B** (a reader-facing widget, *"a new state category"*). Its Ruling 1 recommends A alone.

<p><br/></p>

✅ **THE PACKET IS ON A'S SIDE AND DOES NOT TOUCH B.** `datatable.py`'s law — *"THE RENDERER NEVER LEARNS WHAT DEVICE IT IS ON, AND CANNOT"* — is satisfied rather than strained: one file, built from declared data, identical for every reader, **zero** reader state. ⚑ *It is the print feature BUILD 8's expensive half was never needed for, and it delivers more than the widget would have.*

<p><br/></p>

⚠️ **One real coupling.** If BUILD 8 Feature A ships, a `print:` block on a policy page is a per-page declaration landing inside a document that is not that page. **Precedence must be PACKET > PAGE**, on BUILD 8 §3's own principle that *"an override expressed as a value beats an override expressed as a selector."* A per-page `base: 11pt` inside a 27-sheet packet is one policy in a different size, which reads as a defect.

---

## 🚩 A13 — The index correction, which is a correction to `print-control.md` §7 and not an echo of it

That section says `next-build-spec.md` *"is 32,840 B"* and treats it as unreadable. **It read back WHOLE at HEAD on 2026-08-30.** So the blocker is not the read path — it is the **write** cap alone: *large files (>~30KB) never go through `create_or_update_file`*, LOCKED 2026-07-02 after it corrupted a file four times in one session.

<p><br/></p>

⚑ **A FILE CAN BE PERFECTLY READABLE AND STILL BE UNWRITABLE, AND CONFLATING THE TWO COSTS THE WRONG FIX:** *"split it so it can be read"* and *"split it so it can be WRITTEN"* point at different seams.

<p><br/></p>

🚩 **FOUR ROWS ARE OWED: BUILDS 7, 8, 9 AND 10.** `print-control.md` §7 said three, eight hours earlier. **The debt compounds at one row per spec**, and the index's own instruction — *"if it is wrong again, delete it rather than refresh it"* — has been earned twice over.

<p><br/></p>

✅ **The fix is a pure move: lift BUILDS 1 and 2 into `specs/`**, dropping that file to a ~4 KB index and making it writable again. Its own header already asks for this in its own words. **It should happen before a fifth spec is written.**
