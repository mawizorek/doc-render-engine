# `forms.py` — rationale

Sibling to `docrender/forms.py`. **The steps and warnings live in the module; the
arguments and the incidents live here.** Started 2026-08-30 when the module reached
**24,664 B against a 22,528 B read ceiling** while the reload button's argument was
being written into it — the module's own docstring had already said *"This file is at
the warn line already."*

⚠️ **The trigger was the reload button; the CAUSE was four accumulated arguments.**
The sections below were MOVED out of the module verbatim rather than trimmed, on the
`buildstamp-dl.md` standard: *the steps, values and conditions stay in the file; why a
step exists at all moves to the sibling.* Suffix convention is Michael's
(`publish-dl.md` set it). Do not invent a second name for this job.

---

## ✅ THE RELOAD BUTTON (2026-08-30)

> Michael: *"when i'm working ON THE REHEARSAL REPORT page and interacting only with
> the embedded add note clickup form, i want to be able to reload the embedded form
> without having to reload the entire webpage of the doc renderer."*

Every embed carries one `<button class="dr-form__reset">Reload form</button>`. On by
default; `reload: false` on the slot removes it.

### 🔴 `cloneNode` + `replaceWith`, and `iframe.src = src` is the wrong answer

Assigning `src` **navigates the existing browsing context**, which pushes a
session-history entry — so after three reloads the reader's Back button walks
backwards through iframe states instead of leaving the page. Inserting a FRESH node
is an *initial load*, not a navigation, and pushes nothing.

✅ **Verified by execution rather than by reasoning.** The handler was transcribed
into a DOM model and asserted: node replaced · exactly one fresh load fired · the
OTHER form on the page untouched · **zero history entries** — against the naive
version, which pushed one per click.

### ⭐ The `min-height` floor is what makes it survivable, and it predicted this

`forms.py` has carried this sentence since August: *"Anything that replaces or
re-creates this element at runtime — **a refresh control, for instance** — orphans
the CDN script's listener, so the frame falls back to exactly this value instead of
collapsing."*

A replaced node orphans ClickUp's `clickup-dynamic-height` binding, so a fresh frame
that is never re-measured would collapse to ~0px without the floor. ⚑ **A guard
written for a CDN outage is what made a later feature safe, and the file named the
feature before it existed.** Second consumer, same value, no new number.

### 🔴 It discards what was typed, with no confirmation, and that is the ask

This was **refused on 2026-08-29** on data-loss grounds — a half-filled incident
report wiped by a stray click. Michael's answer: *"sometimes i do want to reset a
form after i've filled it in halfway."*

⚑ **An objection built on a guessed intent is answered by the intent, not argued
with.** The refusal assumed the click would be accidental; he is describing a
deliberate one. So the label is the entire safety mechanism: **"Reload form"**, not
something coy, and **no confirm dialog** — a dialog on a control whose purpose is to
discard is a nag, and this engine's own dead-control rule says a control should say
what it does.

### ⚠️ The styles are inline, once per page, and that is a byte budget not a taste

`assets/flow.css` owns `.dr-form*` and is the obvious home. Measured:

```
flow.css at HEAD ............ 21,120 B
rule block + print rule ..... +1,405 B
                              22,525 B against a 22,528 B ceiling
                              -> THREE BYTES of headroom
```

That is a tripwire, not a home — the next person to touch that file breaks it. A new
sheet needs a group in `assets.py`, which is **32,684 B and past the 30KB write ban**
(LOCKED 2026-07-02, after that path corrupted a file four times in one session).

✅ So the styles ride with the markup, on **`program.py`'s precedent** — it already
emits a per-page `<style>` block for its promotion rules. 🚩 When `flow.css` splits,
they move into it.

⚠️ **And I told Michael this was blocked before I measured it.** I said flow.css plus
a rule went over the ceiling; it fits, by three bytes. ⚑ *A blocker asserted from a
remembered size is the same defect as a version asserted from one — measure at the
moment you act.* The conclusion held for a different reason than the one I gave.

### 🚫 Three things it deliberately is not

- **Not on a `views:` embed.** A shared view is read-only furniture with nothing typed
  into it, so a reload control there answers a question nobody asked — and `views.py`
  already records that the whole dynamic-height problem is form-only.
- **Not an anchor.** A real `<button type="button">`, because it performs an action on
  this page rather than going anywhere: announced correctly, keyboard-reachable with
  no `tabindex` bolted on.
- **Not one listener per form.** One delegated listener per PAGE, appended beside the
  CDN script, so a two-form page binds once.

### ⚠️ What it cannot do, stated so nobody assumes otherwise

The frame is **cross-origin**. Nothing here can read the form's state, clear one
field, or detect a submission — `contentWindow` is closed to us by the same-origin
policy. This reloads the whole embed and nothing finer, and no amount of engine work
changes that. 🔴 So the *self-redirect-after-submit* problem is **not** addressed by
this button: that is a ClickUp form setting, invisible from a build.

---

## 🔴 A BROKEN SLOT USED TO RENDER **NOTHING**. FIXED 2026-08-30.

> Michael, 2026-08-30: *"why wont the second form for NOTES render on my new rehearsal
> report page"*

The cause was a one-word typo — the body said `rehearesl-note`, the frontmatter
declared `rehearsal-note`. **The cause is not the finding.** `_html` returned `""` for
an unknown slot and `swap` returns `""` on falsy, so the directive line VANISHED: no
marker, no gap, no clue.

⚑ **AND THE TELL IS THAT ITS TWO SIBLINGS ALREADY GOT THIS RIGHT.** `qr.py` renders a
struck-through `docrender-dead` span; `links.py` renders the same thing for a dead
reference and `markerlinks.py` states the rule outright — *"a dead reference never
degrades into a span... falling back would be a silent second legal path."* **Three
directives share one pattern and one vocabulary, and the only one that failed silently
was the one whose absence a reader cannot infer.** A missing QR is obviously missing. A
missing form on a page that already shows one form looks deliberate.

⚠️ **It was in the build report the whole time**, under `dead_links`, naming the bad
slot and listing the legal ones. Nobody read it — which is `next-build-spec.md` BUILD
2's entire premise (*"the build report has no reader"*) acquiring a live fourth
instance. ⭐ **So the fix is not a new message. It is the message that already existed,
on a second SURFACE** — the page — rather than a second claimant on one truth.

✅ **And it reaches paper for free.** `assets/base.css` gives `.docrender-dead` a
`--dr-dead` dotted underline unscoped to any medium, and `print.css` carries a whole
block arguing AGAINST re-declaring it. Verified live 2026-08-19: two dead references
printed in red on a policy sheet with no print rule at all.

🚫 **Not an anchor**, on `qr.py`'s precedent: a form that failed to resolve must not
offer a control. The `title` carries the diagnosis; the span carries no href.

---

## ⭐ SPLIT OUT OF `program.py` THE SAME DAY IT SHIPPED, AND THE REASON IS COHESION

`program.py` held the flow strip and this embed and reached 16,949 B; adding
`collapsed:` would have pushed it past the ~22KB read ceiling. 🔴 **But size was the
TRIGGER, not the REASON** — `specs/visibility-split.md` §1 already ruled on exactly
this: *"The cut that is worth making follows the concerns. It also fixes the bytes. If
those two ever disagree, follow the concerns."*

They agree here. A strip is NAVIGATION — it reads the chain graph, resolves pages, and
computes position. A form is an EMBED — it validates a URL and emits an element. They
share no state and call none of each other's helpers. The only thing they ever shared
was a hook shim, and they still do.

⚠️ **And the same thing happened to THIS file on 2026-08-30**, which is why this
document exists. Same trigger, same test, and the concerns agreed again: the module
keeps the mechanism, the sibling takes the arguments.

---

## ⭐ `collapsed:` — A PROGRAM PAGE IS BOTH THE ENTRANCE AND THE EXIT

> Michael, 2026-08-19: *"if the form could not be so stand out on the first landing but
> then when we circle back to ending there on the same page - it's easily found."*

That is a real sequencing problem rather than a styling preference. A reader lands on
the program page BEFORE reading anything and returns to it to submit. An open form on
arrival instructs somebody to certify material they have not read yet, which is the
pre-filled-checklist hazard `30-programs/index.md` already warns about in its own
words.

🔴 **The mechanism is a FRAGMENT, not a script.** `collapsed: true` renders the embed
inside a closed `<details>`, and the LAST STEP of the flow links to the `<summary>`'s
own id. Per the HTML spec, a fragment navigation targeting content inside a closed
`<details>` expands it — so arriving from the end of the program opens the form, with
no JavaScript, no query parameter and no state.

⚠️ **It degrades honestly where that behaviour is missing**, which is why it was safe
to ship without browser-support arithmetic nobody could verify: the reader lands on a
visible, obviously-clickable "Complete this program" control and clicks once. One extra
click, never a dead end.

🚫 **Not automatic on a program page**, though it easily could be. It is a DECLARED
key, because a form on a single policy page acknowledging one rule wants to be open,
and an engine deciding that by type would be a rule nobody can see in the content.
Declared beats inferred; `objects/program.yml` carries the vocabulary.

⭐ **AND `reload:` DEFAULTS THE OTHER WAY, WHICH IS THE CONTRAST WORTH KEEPING.** A
reload control is useful on every embed and harmless where nobody clicks it, so it is
on by default and `reload: false` is the opt-out. Hiding a compliance form is an
editorial decision that must be declared; offering a reload button is not.
