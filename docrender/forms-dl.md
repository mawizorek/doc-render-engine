# `forms.py` — rationale

Sibling to `docrender/forms.py`. **The steps and warnings live in the module; the
arguments and the incidents live here.** Started 2026-08-30 when the module hit its
own warn line and the reload button's argument had nowhere to go — the module's own
docstring already said *"This file is at the warn line already."*

Suffix convention is Michael's (`publish-dl.md` set it, `buildstamp-dl.md` followed).
Do not invent a second name for this job.

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
