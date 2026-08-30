# `views.py` — decision log

> Sidecar for `docrender/views.py`. **The module holds the MECHANISM; this file
> holds the WHY.** Same split Michael set with `forms-dl.md`, and the same reason:
> when a file's prose outgrows its mechanism, the rationale moves to a sibling,
> because a file that cannot be read whole cannot be edited safely.
>
> Spec: [`specs/view-embed.md`](../specs/view-embed.md) (BUILD 7).

---

## The ask

> Michael, 2026-08-28: *"could i embed a clickup TABLE VIEW into one of my doc
> renderer pages??? like embedding a clickup form on the safety site but doing a
> custom clickup table view to embed instead"* → **live**, not build-time.
>
> 2026-08-29, on scope: *"i want to know how to embed any clickup view in one of
> my pages. let me decide what actually gets rendered. i gave you an example for
> a tool i wanted. focus on the tool."*

🔴 **THREE CORRECTIONS IN THREE DAYS, ONE ROOT: the engine deciding things that
were the author's.** Which surface deserved an embed · what every site must
configure · what sentence appears under his table. Each was reasoned from a real
constraint, and **the reasoning is what made them hard to see.** The rule that
came out of it, and it governs every future key in this module:

> **The engine emits STRUCTURE. The author decides CONTENT.**

⚠️ **AND A FOURTH AND FIFTH FOLLOWED, BOTH DIFFERENT IN KIND** (D8, D9): not the
engine overreaching, but the engine **silently failing to do what a page asked**.
Worth separating, because the fix for overreach is deletion and the fix for silence
is a report.

---

## D1 · The content repo never holds the iframe

The page NAMES a view; the engine builds the element. Fourth registry to take
that shape after `links:`, `data:` and `forms:`. An `<iframe>` is machinery, and
machinery is the one thing the content tree may not contain.

⚠️ **Only the `src=` URL goes in the frontmatter.** The first real paste put the
whole `<iframe>` into `src:`, which is the predictable mistake — so the
allow-list failure message names that case explicitly and says to paste the URL.

---

## D2 · Its own module, no hook of its own

`specs/view-embed.md` §2 argued for folding this into `forms.py`: same verb,
validate a URL and emit an element.

🔴 **The fold died on a measurement.** `forms.py` was 11,740 B when the fold was
scoped and ~17.4KB one day later (PR #197 added the dead-reference marker).
Folding in landed ~21KB, past the warn line. ⚠️ **The spec had already written
*"a size written into prose is wrong within two days, every time, in this repo"*
and then had its own plan invalidated by exactly that, in one day.**

✅ **So the seam moved and both halves survived: DELEGATION.** `forms.py` keeps
the only hook and calls `views.on_page_markdown` last. `_esc` and the
`docrender-dead` span are IMPORTED from it, never re-declared.

🔴 **One hook is the point, not tidiness.** A second hook means editing
`mkdocs.yml` (28,158 B, unreadable whole, therefore unsafe to rewrite). The
delegation buys a whole directive for zero edits to any file past the ceiling.
`instance.py` (23,047 B) is dodged the same way: `view_hosts:` is read off
`state.INSTANCE`, never parsed per-key, the trick `urllinks.py` uses for `links:`.

⚠️ **The two imports look like a cycle and must not be "tidied."** `forms.py`
imports `views` INSIDE its hook function; this module imports from `forms` at
module top. By the time anything calls the hook, `forms` is loaded.

---

## D3 · The host is an engine default, not per-site config

> Michael, 2026-08-30: *"in every sits congit?????????????????? so i can do this
> anywehre i want later?"*

v1 required every site to declare `view_hosts:` in its own `site.yml` with **no
default**, on the rule that *"this engine never guesses a third-party hostname."*

🔴 **The rule was right and it was applied to the wrong noun.** "Never guess"
protects against inventing an unverified value. `sharing.clickup.com` was **read
out of a real embed code** — it is verified. **Once a value is verified it is a
FACT, and a fact does not need six copies to become true.**

⚠️ **The sibling file had already settled it.** `forms.py` hardcodes
`_FORM_HOST` and always has. ⭐ The cheap tell: **a per-site key whose correct
value is identical on every site is not configuration, it is a constant with
extra steps.**

🔴 **The real cost was a silent failure on every FUTURE site.** A seventh site
would embed a view, get a refusal, and its author would have no reason to suspect
a key nobody told them about — the same defect class PR #197 fixed one file over,
the same day, in the same feature.

✅ `_DEFAULT_HOST` carries it. `view_hosts:` survives as an **ADDITIVE** extension
for what the default cannot cover (a second ClickUp surface, a different tenant
domain). **Additive is load-bearing:** declaring a host must not silently disallow
the default.

🚫 **Still an allow-list, never a scheme check** — this element embeds
third-party content on pages that can carry a compliance instruction. 🚫 **Never
a `*.clickup.com` wildcard:** it also matches `app.clickup.com`, the LOGGED-IN
application, so a page could embed a workspace URL and serve a login wall to the
public, which reads as a broken table rather than a misconfiguration.

⚠️ **A stale default fails LOUDLY, which is why this is safe** — the refusal
names both the found URL and the allowed hosts, on the page and in the report.

---

## D4 · No CDN script, and ClickUp's own output is the evidence

`forms.py` needs `clickup-dynamic-height` + `forms-embed/v1.js` for height, and
documents the sharp edge: `height="100%"` with no sized parent is ~0px, so a CDN
failure renders an **invisible** embed rather than a broken one.

⭐ **A view embed does not have that problem, because ClickUp does not hand you
that mechanism.** The real embed code:

    <iframe class="clickup-embed" src="..." onwheel="" width="100%"
            height="700px" style="background: transparent; border: 1px solid #ccc;">

`clickup-embed` alone, **no** dynamic-height class, and a **literal `700px`**. So
ClickUp itself answered the question the spec left open: for a view the height is
declared, not scripted.

🚫 **Therefore no helper script is ever appended.** Fetching a sizing asset for an
already-sized frame is pure cost, and it would mean two registries racing to
append the same asset once per page.

⚠️ **The floor stays anyway.** `min-height` mirrors `height`, so a stylesheet
that overrides the attribute cannot collapse the frame to nothing.

🔴 **A unitless `height: 700` is reported and replaced, never passed through.** It
is invalid in an attribute and renders a collapsed, invisible frame — exactly the
failure `forms.py` exists to warn about, caught where the fix is one line.

---

## D5 · The "Everything level" claim is dead

The first shared view was `URITP PRODUCTIONS > Notes > Production Notes >
Recently Created` — **a LIST-scoped, non-Form view with a working public share.**

One Help Center article contradicts itself here: a Folders/Subfolders/Lists row
says views of a List are publicly shareable on **every** plan including Free,
while a view-types row says only Form views share from a List and everything else
needs an Everything-level view. **I stated the narrower row as a 🔴 fact twice.**
Michael pushed, and the Share modal settled it: the broader row is right.

⭐ **The durable generalization: a document contradicting itself is not evidence,
it is a prompt to go look.** The inverse of this repo's standing rule that
agreeing sources are one source — **disagreeing sources are zero.**

---

## D6 · 🚫 The caption is deleted. The engine writes no prose onto a page.

> Michael, 2026-08-30, on seeing it rendered: *"WHAT THE FUCK IS THIS SLOP.
> DELETE IT IMMEDIATELY."*

v1 emitted a line under every frame reading *"Live from ClickUp — updates
automatically."* Gone: no key, no constant, no CSS, no default.

🔴 **The defect was the CATEGORY, not the wording.** Everything else this registry
emits is STRUCTURE — a frame, a link, a failure marker. The caption was the engine
deciding an **editorial sentence** belonged in his content, in his voice, on his
page, unasked.

⚠️ **It was reasoned from a real constraint** (ClickUp's unremovable *Sign up
free* chrome) and the spec's own ruling 1 took it as a recommended default. **That
is the trap: a good argument for why a reader might want an explanation is not an
argument for the ENGINE writing it.** If a page wants that sentence, the author
types it above the directive.

🔴 **And it shipped an em dash into rendered output**, against a standing absolute
house rule. ⭐ **That is the authoring-time tell: a module emitting text that can
VIOLATE a prose rule is a module writing prose** — which this one has no business
doing.

✅ **The fallback link is not the same thing and stays.** It is a control with a
function: the answer to "the table did not load," and the only content on paper.
Its label is the author's `text:`. **Function stays, narration goes.**

⚠️ **A leftover `caption:` key is REPORTED, not silently eaten.** Pages written
against v1 still carry it, and a key that quietly does nothing is this repo's
least favourite shape.

---

## D7 · `collapsed:` — and the label is the author's or there is no disclosure

> Michael, 2026-08-30: *"can we embedd these like formas optionally to make them
> collapsable too?"*

Same mechanism `forms.py` already proves, ported whole: `collapsed: true` renders
the embed inside a closed `<details>`, and per the HTML spec **a fragment
navigation targeting content inside a closed `<details>` expands it** — so a link
to the summary's id opens it with no JavaScript, no query parameter, no state.

⭐ **WHY IT IS WORTH MORE ON A VIEW THAN ON A FORM.** A collapsed form solves a
sequencing problem (do not ask somebody to certify material they have not read).
A collapsed view solves a **weight** problem: a 700px frame is the tallest thing
on any page it sits on, and it pushes real prose below the fold whether or not
the reader wants the table today. 🔴 **The frame is also the only element here
that costs a third-party request, so a closed disclosure is the one honest way to
make a live embed free until it is wanted.**

🔴 **THE SUMMARY LABEL COMES ONLY FROM `text:`. THERE IS NO DEFAULT, AND THAT IS
D6 APPLIED ONE DAY LATER.** `forms.py` has `_DEFAULT_LABEL = "Complete this
program"` and it is correct there — a completion form has exactly one purpose, so
the engine can name it. **A view has no such purpose**; naming it would be the
engine writing page copy again, which is the mistake that had just been deleted.

✅ **So `collapsed: true` with no `text:` renders OPEN and reports why.** It does
not invent a label, and it does not swallow the request silently — the frame still
appears, so nothing is lost, and the note says exactly which line to add. **The
feature degrades to the working default rather than to engine prose.**

⚠️ **THE ANCHOR SITS ON THE `<summary>`, NOT THE `<details>`.** A fragment must
target something INSIDE the disclosure for auto-expand to apply; pointing it at
the `<details>` scrolls correctly and stays shut. `forms.py` records the same
trap, and this is a re-use of its finding rather than a re-derivation.

⭐ **The id is emitted so an AUTHOR can link to it** (`#dr-view-<slot>`), which is
the view analogue of what `program.py` does for a form's flow. Nothing in the
engine links to it today — stated so nobody hunts for a caller.

⚠️ **THE CONTROL SHARES `forms.py`'s STYLE BY EXTENDING A SELECTOR LIST, NOT BY
ADDING A BLOCK.** `assets/flow.css` is 23,188 B, already past the read ceiling
before this build existed, so `.dr-view__open > summary` joins the existing
`.dr-form__open > summary` rules — ~30 bytes rather than a new section. ✅ And it
is the honest design regardless: the two disclosures look identical because they
ARE the same control.

🔴 **AND THE PRINT CLAIM IN THIS SECTION WAS WRONG — SEE D9.** It read *"print is
unchanged and needs no rule: `print-flow.css` already forces every `<details>`
open, so a collapsed view prints exactly as an open one does."* The first half is
true and the conclusion is backwards: that rule is precisely what makes the frame
print. ⚑ **A correct fact plus a comfortable inference is how a defect gets
documented as a non-issue.**

---

## D8 · `align=` — the option the directive could not parse

> Michael, 2026-08-30, after a review turned up three dead directives: *"Teach
> form and view the option parser."*

`!!! view "x" align=center` did not match `_VIEW` at all, so the directive stayed
on the page as literal text **with nothing in the build report**, because a regex
that does not match has nothing to report on.

🔴 **THE FULL INCIDENT LIVES IN `forms-dl.md` UNDER `align=`, AND ONLY THERE.**
One claimant for a fact that spans both modules. What belongs here is the one
view-specific consequence: **alignment cannot move the frame** (it is `width:
100%`, and a box that fills its column has no slack for a margin), so what aligns
is the summary label and the fallback link. A real but partial effect, documented
as partial.

⚠️ And the shape worth carrying forward: **a guard placed inside `_html` cannot
see what the pattern turned away.** The dead-marker fix (D-adjacent, `forms.py`
PR #197) lives in the resolver, which only ever runs on a match.

---

## D9 · 🔴 THE VIEW FRAME PRINTED, AND IT WAS THE SAME DEFECT TWICE IN ONE DAY

> Michael, 2026-08-30: *"that embedded view should NOT print when we use print
> comment. it's generating sloppy irendered embeds so lets just hide it like we do
> with the embedded forms"*

### The cause, read at source rather than guessed

`assets/print-flow.css` carries:

    .md-typeset details > *:not(summary) { display: revert !important }

It exists so a collapsed `???` cannot silently lose its content on paper — a good
rule with a real reason. **And a collapsed view's `<iframe>` is a DIRECT CHILD of
that `<details>`.** Importance beats specificity, so `flow.css`'s plain
`.dr-view iframe { display: none }` **loses**, and the frame prints.

### ⚑ The finding is that this was already known, in this feature, hours earlier

`forms-dl.md` documents the identical mechanism under *"A COLLAPSED EMBED PRINTED
AS A CALLOUT"* — and `forms.py` carries a 🚫 **DO NOT tidy these back to plain
`display: none`** warning on its own print block for exactly this reason.

🔴 **The `.dr-view` rules were written as plain `display: none` anyway**, in a
session that had read that warning, because the view rules were authored as a
COPY OF THE SCREEN half and the print half was assumed to follow. ⚑ **A warning
attached to one implementation does not travel to the next one by being true.**

⚠️ **And D7 above actively argued the bug away.** It stated that print needed no
rule *because* `print-flow.css` forces every `<details>` open — the correct fact,
with the conclusion inverted. **That is worse than an omission: an omission gets
noticed, a documented non-issue gets trusted.**

### ✅ The fix, and why it is inline

An `@media print` block emitted once per page from `views.py`, every `display`
declaration `!important`, both selector spellings (`.dr-view x` and
`.md-typeset .dr-view x`) on `blocks.css`'s documented arithmetic.

🔴 **Inline because `assets/flow.css` — which owns `.dr-view*` — is past the read
ceiling and cannot be rewritten safely.** Exact precedent: `forms._RESET_CSS`, for
the same reason, on the same day. 🚩 Both move into the sheet after the split that
file's own header prescribes.

✅ **GATED ON A FRAME BEING EMITTED, NOT ON THE DIRECTIVE MATCHING.** A page whose
only view is broken renders a dead marker and no iframe, so it needs no print
rules and must not pay for them — inherited from the forms regression where print
rules rode in the wrong conditional, rather than re-learned.

### ✅ The summary is hidden too, and that is parity rather than loss

A `<summary>` is a **control**, and paper has none (`print.css`'s pen test). Its
text is the slot's own `text:` — which the fallback link already carries
**verbatim**, because this module refuses to invent a label (D7). ⭐ So a collapsed
and an uncollapsed view now print as the SAME one line naming the view, which is
the parity the forms defect was about: two embeds differing only in a SCREEN key
must not print as two different KINDS of object.

### 🔴 The honest limit: this cannot be verified from a harness

**WeasyPrint discards `display: revert` as invalid**, so it never reproduces the
bug and a harness passes on the broken and the fixed version alike. ⚠️ **Verify in
Chrome print preview.** Reproduce the failure by substituting
`display: block !important` for the revert rule.

### 🅿️ Recorded debt

`flow.css`'s print block still carries the superseded plain `.dr-view iframe
{ display: none }`, now unobservable on a collapsed embed and redundant on a bare
one. **Left alone rather than deleted:** removing it means rewriting a 23KB file
that is past the ceiling and that a parallel session has touched today. Goes with
the split — alongside the identical `.dr-form__open > summary` leftover
`forms-dl.md` already records.

---

## Standing debt

🔴 **`assets/flow.css` is past the ~22KB read ceiling and no build in this feature
could fix it.** It was already ~21.6KB before BUILD 7. `.dr-view` belongs in its
own `embed.css`, which requires registering a sheet in `docrender/assets.py` —
**32,684 B, past the read ceiling AND the write cap**, so it cannot be rewritten
safely. ⚠️ **The real fix is splitting `assets.py`**, which is its own build.
Flagged in flow.css's own header so the next editor meets it.

🅿️ **`next-build-spec.md` row 7 is OWED** — 32,840 B, over the write cap. Its own
header instructs that the hand-kept build count be DELETED rather than refreshed
the next time it is wrong, and adding row 7 makes it wrong.

🅿️ **`qr.py` still holds its own copy of the directive-option parser** — 29,915 B,
at the write cap. Conversion recipe is in `util.directive_options`.

---

## Honest limits

- Nothing here can prove a view is still shared, still exists, or shows what its
  author thinks. **The host is checked and that is all** — the same reduction
  `forms.py` and `urllinks.py` state at the top of their own files.
- 🔴 **A revoked share renders an empty frame with NO build finding.** External
  runtime behaviour is invisible at build time; the fallback link is the only
  thing distinguishing "loading" from "gone."
- **Public shares require third-party cookies**, blocked by default in a growing
  number of browsers, and the affected reader is exactly the one not logged into
  the workspace. **The acceptance test is a page loaded with them OFF.**
- **A public share is public until revoked** — indexable if that toggle is on,
  auditable by Owners/Admins on Enterprise. Logging each share in the Access
  Tracking Decision Log is recommended so it can be revoked deliberately rather
  than discovered. **What is safe to publish is the author's call, per view.**
- **Print loses the table, by design as of D9.** The fallback link is always
  rendered, but for a form a printed link is a full substitute and for a table it
  is not: the frame IS the content. A build-time copy for print was refused — two
  sources behind one element disagree the first time a filter changes.
