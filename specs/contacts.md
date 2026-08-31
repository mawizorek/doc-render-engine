# BUILD 11 — the contacts index: one address book, reached by `@contact:<id>`

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-31.

> Michael, 2026-08-31: *"a new frontmatter field on ROLE type page that is 'mailto:' which can be used then in other pages... I will ultimately probably want to be able to do more one-off emails or even a small index of just emails... so instead of entire pages for one email, just a tsv or md of emails with associated id's that i'd like to reference them by throughout the renderer."*

Asked whether he wanted the role field or the index: *"i probably want both?"* Walked through it, and the answer landed as **both KINDS of address, ONE store.** On whether every role must carry a row: **"just a convention."** Ruling 4 below is therefore closed rather than open.

🔴 **THE REASONING FOR EVERY DECISION IS IN THIS FILE TODAY AND STAYS HERE UNTIL IT SHIPS.** No `contacts-dl.md` sidecar yet; the moment this build gains a correction history, history moves out and this file stays the SPEC, per the pattern `views-dl.md` and `forms-dl.md` set.

---

## §0 The refusal this build has to get past, and why it is legally re-testable

`objects/role.yml` forbids the first half of the ask, in writing:

> 🚫 SO DO NOT ADD A FACTS-ABOUT-THE-SUBJECT FIELD HERE. No `phone:`, no `office:`, no `email:`, no `term:`. Every one of those is read only on this page, which means space.yml has already refused it. Write it in the BODY.

That is the 2026-08-03 purge, and its test is *"whether a value is needed AWAY from the page it appears on."*

⭐ **MICHAEL'S MECHANISM PASSES THAT TEST.** An address reached by `@contact:` is read on every page EXCEPT its own — which is the single reason `gloss` was admitted to `role.yml` at all. So this is not a dead ask hitting a live refusal; it is the case PR #91 wrote the rule for: *a refusal aimed at a MECHANISM should be re-tested against a different mechanism rather than treated as a refusal of the goal.*

🔴 **AND IT STILL LOSES — TO THE SECOND HALF OF HIS OWN MESSAGE, NOT TO THE OLD REFUSAL.** `email:` on a role page PLUS an index is **two places stating who to email for Production Management**, with nothing reconciling them. That is the defect that retired `roster.json`, `registry.json` and `app-index.md`. ⚑ *Two strings about one subject are safe exactly when they answer different questions* — role.yml's own line, and here they answer the identical one.

✅ So `email:` on `role.yml` is refused a SECOND time, on a NEW argument, and role.yml's block gains a pointer at this file rather than another sentence. **Recording the re-test rather than just the refusal, because the next person to ask will hit the 08-03 wording and needs to know it was actually re-examined.**

---

## §1 The pointer direction, which is the whole design

⭐ **THE INDEX ROW NAMES THE ROLE. THE ROLE PAGE HOLDS NOTHING.**

Turn it the other way and the feature breaks on arithmetic rather than on taste: a role page cannot hold a vendor's address, a rental house's, or the box office's, so **the index has to exist either way** — and putting addresses on role pages too means maintaining two surfaces that have to agree. ⚑ *Put the pointer on the side that has to be complete anyway.* One address, one row, one place.

**What that buys, free:** because a row may name a role page `id`, the resolver can read that role's `gloss` off `state.PAGES` and render *both* the address and who this is. 🔴 **`PAGES`, never `BY_SRC`** — links.py's docstring says why in bold: PAGES is built AFTER visibility prunes, so a contact can never gloss from a page nobody can open. BUILD 9 put `gloss` on that map on 2026-08-30 for exactly this class of consumer, and its own admission test was *"does a page OTHER THAN THIS ONE need the value."* A contact row is that page.

---

## §2 The prefix is `@contact:`, NOT `@mailto:`

Michael proposed `@mailto:role-pm`. Three reasons it should not ship under that name:

1. 🔴 **Every existing prefix names the TARGET, not the mechanism.** `@role:` `@img:` `@data:` `@term:` `@rel:` `@calc:` `@peer:`. `@mailto:` names the *protocol*, which is the one thing the author should not have to care about — and it forecloses a row ever carrying a phone number or a Teams handle.
2. ⚠️ **It shadows a live URI scheme.** `[x](mailto:a@b.edu)` and `[x](@mailto:a)` differ by one character and mean different things. A reader diffing content would have to squint at the `@`.
3. 🚫 **Not `@email:` either.** A row will want a display name and a paper override; `email` locks the namespace to one field and the rename costs every page that typed it. `id` is permanent by promise (links.py: *"Set `id:` once and never change it; that promise is the whole mechanism"*), and so is a prefix.

⚠️ **`contact` must not collide with a marker row.** `markerlinks.py` claims one namespace per `prefix` cell in `theme/markers.tsv`, so the reserved set grows with a data edit. `prefixes.claim()` raises on a second owner and markerlinks checks-and-reports before calling, so a `contact` marker row is LOUD rather than silent. Verified at HEAD: no such row is claimed by name anywhere in `prefixes.py`.

---

## §3 What it costs in `links.py` and `prefixes.py`: **nothing**

✅ **Read at HEAD rather than assumed.** `links.replace()` already routes any claimed prefix through `prefixes.resolver()` and picks the call shape from `takes_anchor()` / `takes_opts()`. **A new namespace is a `claim()` call in a new module and zero edits to either file.**

⭐ **That matters more than it sounds.** `links.py` is **22,090 B** and `markerlinks.py` is **27,637 B** — one at the ~22KB read ceiling and one 5.6KB past it. A design that needed either one edited would be blocked on a refactor before it started. The derived registry, argued in `prefixes.py` in 2026-08 for a different reason, is what makes this build cheap.

### The claim

```python
prefixes.claim("contact", __name__, _resolve_contact, opts=True)
```

`opts=True` and therefore `anchors` too, per the ladder — **but the anchor is DECLINED in the handler and reported**, exactly as `@data:` and `@img:` do it, because an address is a whole target with nowhere for a fragment to point. 🔴 The ladder is cumulative, so there is no way to take the fifth argument and refuse the fourth; the refusal is a report line, not a signature.

⚠️ **`opts=True` MAKES THE HANDLER RESPONSIBLE FOR THE AUTHOR'S BRACE BLOCK.** links.py stops re-emitting it. A handler that opts in and ignores it silently eats `{.no-print}`, and this file cannot tell that case from a handler that merged it. **Merge it or do not claim it.**

---

## §4 The row, and the header grammar

Hand-maintained, so **a person declares the spec** — J22's rule, whose three subjects are person / FileMaker field name / the script that writes the header.

| column | required | what it is |
|---|---|---|
| `id` | ✅ | the only string another page ever types. Permanent. |
| `email` | ✅ | the address. One per row. |
| `role` | — | a role page `id`. Supplies the gloss. |
| `gloss` | — | one sentence, for a contact with no role page. |
| `print_gloss` | — | paper override. |

🔴 **`role` AND `gloss` ARE MUTUALLY EXCLUSIVE, AND BOTH-PRESENT IS REPORTED.** Two claimants on one hover string is the defect this whole file keeps citing; declaring the conflict beats picking a winner silently.

⚠️ **`print_gloss`: ABSENT AND EMPTY ARE DIFFERENT STATES.** Absent = print the gloss. `""` = print nothing. Test `is None`, never falsiness — `collapsed:` had to be retrofitted for precisely this on 2026-08-30 (PR #201), where `false` and an omitted key produced identical output and one whole state was unreachable.

⚠️ **NO `::type` ANNOTATIONS ON THIS HEADER.** That grammar belongs to `sheet.py` and rendered `!!! data` tables. This TSV is a REGISTRY read by a resolver, not a sheet drawn on a page. 🚩 Whether it should ALSO be renderable as a directory page is a real question and it is **out of scope** — a second consumer of one file is a decision, not a freebie.

🔴 **A HUMAN'S NAME IN ANY OF THESE CELLS IS A CLICKUP FACT WEARING A TSV COSTUME.** URITP PEOPLE owns role assignment, with a term attached, so a name here is a snapshot nothing can see rot. role.yml already says this about `print_gloss` and it applies with more force to a file that is one commit from being a staff directory. **Prefer the role, not the person.**

---

## §5 🔴 Where the file lives, and what reaches the public web

### Option A — the registry in `site.yml`, like `links:`

**Refused, and the reason is visibility asymmetry rather than tidiness.** `urllinks.py` reads `links:` straight off `state.INSTANCE`, so this would need zero discovery code and could never be copied to `gh-pages`. But `instances/<slug>/site.yml` is in **`mawizorek/doc-render-engine`, which is PUBLIC**, while the content repos are private — Dexter, 2026-08-30: *"content repo is `mawizorek/uritp-safety` (private, 🔒 opposite visibility to the engine)."* 🚫 **An address book committed to the engine is published in the repo, which is the exact door J27 measured and closed one over.**

### Option B — a TSV in the content tree ✅ RECOMMENDED

Addresses are **content**, per J30's ratified invariant: a content repo supplies markdown, TSVs and frontmatter, and this is the third of those. It also keeps six sites from sharing one address book across two different audiences.

⚠️ **AND IT NEEDS ONE THING VERIFIED BEFORE IT IS SAFE, WHICH J27 ALREADY PAID FOR ONCE.** `course-index.tsv` sits in `gh-pages` today — deliberately, because a download link needs it, and J27 flagged it as *"the one raw data file a stranger with the URL can still pull."* **An address book has no download link and must not ship.** Nothing in the engine has ever consumed a content TSV and then dropped it from the output.

🔴 **I told Michael in chat that keeping it unpublished was free. That was reasoning from the precedent instead of from what the file is FOR, and the mechanism is unverified.** Two candidate mechanisms, and the first one has to be proven, not assumed:

- **MkDocs' own exclusion of `_`-prefixed and dot-prefixed files** under `docs_dir`. If that holds, `_contacts.tsv` never enters the file set and never copies. **Read MkDocs' source at the pinned version — do not read its docs.** That substitution is the one the 08-30 checkbox miss was written about.
- **Remove the `File` from the collection at `on_files`** after reading it. `assets.py` already reaches the content tree with `Path(str(config.docs_dir))`, so the read half has precedent at HEAD.

✅ **Acceptance test, and it is the only one that decides whether this build is publishable:** after a real deploy, fetch the path directly on the published site and get a 404. Not inferred from the file set. **Fetched.**

### 🚫 And the harvesting question, answered honestly rather than papered over

A `mailto:` on a public page **is** the address, in the href, in the DOM, in view-source. There is no version of this feature that publishes a working email link and withholds the address, and role.yml already ruled on the shape of that lie: *"print-only is a VISUAL claim and never a privacy one."*

🚫 **So no obfuscation, no entity-encoding, no JS assembly.** Each one breaks the link for a real reader, defeats an actual scraper for about a week, and dresses the feature as protection it does not provide — the same dishonesty the padlock refusal turned down on the router gate. ⭐ **The real control is WHICH addresses get a row**, and that is the author's call per row. Departmental inboxes are what this is for.

---

## §6 🔴 The finding worth reading even if the build never happens

The token charset is `[A-Za-z0-9_.:-]` and **has no `@` in it.** So `[me](@contact:michael.wizorek@rochester.edu)` cannot match `_LINK` at all. Ids are structurally the only addressable form — no check, no code, no way around it.

⚠️ **AND THAT IS ALSO A HOLE, WHICH IS THE CORRECTION TO MY OWN CHAT CLAIM THIRTY MINUTES BEFORE THIS FILE.** I called it a free win. A non-match is not a refusal: the text stays literal markdown, so it renders as an ordinary link to a garbage relative URL, with **no dead marker and no `dead_links` line**. The most tempting authoring mistake available — pasting a real address — is the one failure mode this namespace reports nothing about. ⚑ *A structural guarantee protects the RESOLVER, not the author. The two get confused because both feel like safety.*

🔴 **A SECOND, SMALLER HOLE IN THE SAME PLACE.** links.py step 0 refuses a token carrying a file extension and **branches its advice two ways** — data slot or image name. `@contact:staff.md` would be sent to `@data:<slot>`, which is the wrong subsystem, and that refusal list is the same one that already had a hole for images until 2026-08-07: *the same bug wearing the same clothes.* 🚩 **Flagged, not fixed:** a third branch is four lines in a file at 22,090 B, and it is not this build's to spend.

⏳ **Ruling 3 is what to do about the first hole**, and both candidates are cheap:
- a `contacts.py` pre-scan for `](@contact:` followed by an `@` before the closing paren, reported to `dead_links`; or
- widen `_LINK`'s charset to admit `@` so the token matches and the handler can refuse it out loud. 🚫 **Recommend AGAINST the second**: widening a live regex to improve one error message is how `[x](@circuits-and-dimmers.tsv)` became a page-id lookup, and every branch of `replace()` would have to be re-argued.

---

## §7 Paper

An address rendered as a coloured underline on a printed sheet is nothing at all — the reader cannot dial a hyperlink. ✅ **`@role:` already solved this exact shape** (hover on screen, gloss printed inline in parentheses), so `@contact:` inherits the pattern rather than inventing one:

```
SCREEN   Email [Production Management](@contact:pm) with questions.
         -> terminology-styled link, mails on click, gloss on hover

PAPER    Email Production Management (pm@example.edu) with questions.
```

⚠️ **`print_gloss: ""` is how an author prints the name and withholds the address** — and per §5 that is a LAYOUT choice, not a privacy one. The href is still in the DOM.

⭐ **NO NEW STYLESHEET.** `@contact:` rides the terminology + gloss rules already registered; `assets.py` is **20,590 B** and a net-new sheet is exactly the addition its own budget refuses. 🔴 **`specs/view-embed.md` §3 quotes `assets.py` at 32,684 B and blocks `embed.css` on it. That number is stale by 12KB at HEAD — the file was split.** Measure at the moment you act; never quote a spec's file table. This one included.

---

## §8 Files and sizes (measured at HEAD `9ec845e`, 2026-08-31)

| File | Now | Change |
|---|---|---|
| **NEW** `docrender/contacts.py` | — | ~6–8 KB. The claim, the TSV read, the resolver, the print attribute. |
| **NEW** `hooks/03f_contacts.py` | — | ~1.5 KB shim. ⚠️ A suffixed stage takes a **letter, never a digit** — J29, and the reason is that `_` sorts after a digit and before a letter, so the filesystem and `mkdocs.yml` would disagree about order in the one directory whose premise is that the filename carries the order. |
| `docrender/links.py` | 22,090 B | **untouched.** §3. |
| `docrender/prefixes.py` | 10,004 B | **untouched.** The claim is made by the claimant. |
| `docrender/markerlinks.py` | 27,637 B | **untouched, and it must be** — 5.6KB past the read ceiling. |
| `objects/role.yml` | — | one pointer line in the existing 🚫 block. §0. |
| `mkdocs.yml` | 29,259 B | **one hook registration**, and it is the only hard cost. Past the read ceiling and the write tool replaces whole files — so use the byte-count method PR #225 proved: transcribe, count, match the repo exactly, then write. ⚑ *A whole-file rewrite is unsafe only while the read is unproven.* |
| `assets/*.css` | — | **untouched** under §7. |

---

## §9 Rulings

1. ⏳ **Where does the TSV live and how is it withheld from `gh-pages`?** §5 recommends Option B with `_contacts.tsv`, and the exclusion mechanism must be READ at the pinned MkDocs version, then proven by fetching a 404 off a real deploy.
2. ⏳ **Does a row's `role` cell have to point at a page that exists?** A missing role page means no gloss, which degrades correctly to an address with no explanation. **Recommend reporting it and rendering anyway** — same posture as a dead peer serving a stale cache rather than taking the build down.
3. ⏳ **Report a pasted raw address, or leave it silent?** §6. Recommend the pre-scan, not the regex widening.
4. ✅ **CLOSED — every role does NOT need a row. Convention, not a check.** Michael, 2026-08-31: *"jsut a convetion."* A `@contact:` naming no row already renders the `docrender-dead` span (red, struck, unclickable, tooltip naming what was missing) and files a `dead_links` line, because links.py does that for any handler returning `None`. **So the failure is loud without a single new bucket** — and `report.py` gains nothing, matching BUILD 2's standing rule that a digest makes the report louder and never the checks smarter.

---

## §10 What is left before anybody writes code

1. **Ruling 1.** It is the one that can make this build unpublishable, and it is a read plus one fetch.
2. 🅿️ **`next-build-spec.md` row 11 is OWED and CANNOT BE WRITTEN.** That file is **32,840 B, over the write cap** — the identical debt `specs/view-embed.md` §5 recorded for row 7 on 2026-08-30. 🔴 **Index debt is now FIVE rows (7, 8, 9, 10, 11), compounding one per spec, and its own header instructs that the hand-kept build count be DELETED rather than refreshed the next time it is wrong.** It is wrong again. **The fix is to move BUILDS 1 and 2 out to `specs/` and leave an index**, which that header has been asking for since BUILD 3 and which is a real edit somebody has to make.
3. 🅿️ **The `assets.py` split**, still named in `view-embed.md` §5 against a number that has since changed. Not a blocker here; §7 needs no sheet.
