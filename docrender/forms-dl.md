# `forms.py` — rationale

Sibling to `docrender/forms.py`. **The steps and warnings live in the module; the
arguments and the incidents live here.** Started 2026-08-30 when the module hit its
own warn line — its docstring already said *"This file is at the warn line already."*

⚠️ **THE MODULE CROSSED THE 22,528 B READ CEILING TWICE IN ONE DAY** — 24,664 B, then
24,030 B — both times while reasoning was being written into it, and **both times off
a size I estimated rather than measured.** ⚑ *If you are adding to that docstring,
write the section here first.* Suffix convention is Michael's (`publish-dl.md` set
it). Do not invent a second name for this job.

---

## ⭐ THE FOLD — THREE STATES, ONE KEY (2026-08-30)

> Michael: *"although I said the rehearsal report should be expanded when the form
> opens, it is now permanently open with no option to collapse it. How do I set it to
> default as expanded but still allow the user to collapse it later, compared to the
> rehearsal note which defaults to collapsed?"*

```
collapsed: ABSENT   a bare embed. No disclosure at all.
collapsed: false    <details open>  -- expanded on arrival, collapsible.
collapsed: true     <details>       -- closed on arrival.
```

### ⭐ Why `false` is not the same as saying nothing

The module's binary read `collapsed is True` → closed, **everything else** → no
disclosure at all. So `collapsed: false` and an omitted key produced identical output,
and the state Michael wanted — *a fold that starts open* — was unreachable.

⚑ **A MISSING KEY AND A KEY SET TO `false` ARE DIFFERENT FACTS.** "Not collapsed" is
a claim about a fold; saying nothing is not a claim at all. That is the same
distinction `reload:` turns on in this file (`is not False`) and the one
`pagefoot._enabled` has read on `edit_links` since August.

✅ **So he needed ZERO content edits.** `40-forms/rehearsal-report.md` already declared
`collapsed: false` on the report and `collapsed: true` on the note — which under the
new reading is exactly *"report expanded but foldable, note closed."* The frontmatter
was already right; the engine could not express it.

### ⚠️ What changes for pages that already wrote `collapsed: false`

Only those pages change, and they gain a disclosure they did not have:

| page | slot | before | after |
|---|---|---|---|
| `40-forms/rehearsal-report.md` | `form` | bare | **open + foldable** — the ask |
| `40-forms/rehearsal-report.md` | `rehearsal-note` | closed | closed (unchanged) |
| `40-forms/incident-report.md` | `incident-report` | bare | **open + foldable** |

🚩 **The incident-report page is the one to look at.** It gains a fold control nobody
requested. That is defensible — a reader who has submitted can now collapse a tall
embed — but it is a change to a live compliance page and it is Michael's to keep or
revert. **Reverting is deleting one line** (`collapsed: false`), which returns it to a
bare embed.

✅ Every slot that OMITS the key is byte-identical, which is what keeps DL J15's rule
alive: shipping a feature must not re-shape a page nobody touched.

### 🚫 Not a second key, and not a renamed one

`collapsible: true` beside `collapsed: true` gives **four states, one of them
unsatisfiable** (not collapsible + collapsed) — the shape `nav: hidden` +
`status: unlisted` already had to be reported as a contradiction rather than resolved.
And renaming the key to something with three honest values (`fold: open|closed|none`)
would break every live page, in a repo **agents may not commit to**. One key, three
states, no migration.

### ⭐ `open` is an attribute, so there is only one markup shape

"Expanded" and "closed" differ by five characters on the same element. That is why the
print rules, the `slot_anchor` fragment and the screen styles need no knowledge of
which state a slot asked for — **one shape, one set of rules.** ✅ And the flow-strip
fragment still lands correctly: a fragment pointing inside a *closed* `<details>`
expands it, and inside an *open* one simply scrolls.

---

## 🔴 A COLLAPSED EMBED PRINTED AS A CALLOUT (2026-08-30)

> Michael, from a print preview: *"the rehearsal report is not in a collapsed iframe,
> so it prints correctly, but because the rehearsal note form is collapsed, it renders
> differently at print and breaks the system. We need to fix that so it reads like the
> rehearsal report when printed."*

### The cause was already documented — at the other end of the same file

Material `@extend`s `.admonition` onto **every** `<details>` in typeset content, and
`print-callout.css` turns every `.md-typeset details` into a rule-and-indent: a 2pt
coloured left band plus a 0.85em indent. Correct for a real callout. Wrong for a form.

⚑ **THE DEFECT IS A DIVERGENCE, NOT A STYLE.** Two embeds declared the same way,
differing in one **screen-only** key, printed as two different KINDS of object. And
`flow.css`'s own THE CAP section fixed exactly this for `.dr-flows__others`, with the
reasoning written out — *"without this it would print with a BLUE band, because no
family rule ever gave it a colour"* — and **nobody pointed the same fix at the form.**
Second instance of one defect, in one file, found by printing rather than by reading.

### ⚠️ The summary is hidden on paper, and that is parity rather than loss

A `<summary>` is a **control**, and paper has none — `print.css`'s pen test. Its text
is the slot's own `text:`, which the fallback link already carries, so both embeds now
print as one line naming the form.

🚩 **The one case where a string genuinely goes:** a slot with no `text:` at all. Then
the summary would have read `"Complete this program"` while the link reads its own
fallback wording. The form is still named, so nothing is orphaned — but it is not the
same sentence, and that is worth knowing before somebody declares a slot with no text.

### ⚠️ Why the rules are inline instead of in `flow.css`, which owns `.dr-form*`

**`flow.css` is 23,485 B and already 957 B PAST the 22,528 B read ceiling** — it grew
**2,365 B the same morning**, when a parallel session landed the `.dr-view*` rules. So
the file that should own these rules cannot safely be edited at all.

⚠️ **And this corrects the measurement in PR #199.** That PR said flow.css sat at
21,120 B and would land three bytes under with the reload rule in it. True when
measured, false four hours later. ⚑ *A size measured once is a size that was true
once.* The conclusion — inline, on `program.py`'s per-page `<style>` precedent — now
holds for a far stronger reason than the three-byte margin it was first argued from.

🚩 **`flow.css` needs the split its own header prescribes** (*"a file at its size limit
is usually a file with a seam in it"*), and the seam is obvious: the flow strip and the
`.dr-view*` rules are different subjects. These print rules move there afterwards.

⚠️ **One superseded rule was deliberately left alone.** `flow.css`'s print block still
carries `.dr-form__open > summary { border: 0; padding: 0 }`, which is now unobservable
because the summary is `display: none`. That is precisely the *"a rule is only as real
as the state it is allowed to observe"* defect that file documents about its own deleted
position reset — **but deleting it means rewriting a 23KB file a parallel session just
touched.** Named as debt rather than fixed; it goes with the split.

---

## ✅ THE RELOAD BUTTON (2026-08-30)

> Michael: *"i want to be able to reload the embedded form without having to reload the
> entire webpage of the doc renderer."*

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
feature before it existed.**

### 🔴 It discards what was typed, with no confirmation, and that is the ask

**Refused on 2026-08-29** on data-loss grounds — a half-filled incident report wiped by
a stray click. Michael's answer: *"sometimes i do want to reset a form after i've
filled it in halfway."*

⚑ **An objection built on a guessed intent is answered by the intent, not argued
with.** The refusal assumed the click would be accidental; he is describing a
deliberate one. So the label is the entire safety mechanism: **"Reload form"**, not
something coy, and **no confirm dialog** — a dialog on a control whose purpose is to
discard is a nag.

### 🚫 Three things it deliberately is not

- **Not on a `views:` embed.** A shared view is read-only furniture with nothing typed
  into it — and `views.py` already records that the whole dynamic-height problem is
  form-only.
- **Not an anchor.** A real `<button type="button">`, because it acts on this page
  rather than going anywhere: announced correctly, keyboard-reachable with no
  `tabindex` bolted on.
- **Not one listener per form.** One delegated listener per PAGE, so a two-form page
  binds once.

### ⚠️ What it cannot do

The frame is **cross-origin**. Nothing here can read the form's state, clear one
field, or detect a submission — `contentWindow` is closed to us by the same-origin
policy. This reloads the whole embed and nothing finer. 🔴 So the
*self-redirect-after-submit* problem is **not** addressed by this button: that is a
ClickUp form setting, invisible from a build.

---

## 🔴 A BROKEN SLOT USED TO RENDER **NOTHING**. FIXED 2026-08-30.

> Michael: *"why wont the second form for NOTES render on my new rehearsal report page"*

The cause was a one-word typo — the body said `rehearesl-note`, the frontmatter
declared `rehearsal-note`. **The cause is not the finding.** `_html` returned `""` for
an unknown slot and `swap` returns `""` on falsy, so the directive line VANISHED: no
marker, no gap, no clue.

⚑ **AND ITS TWO SIBLINGS ALREADY GOT THIS RIGHT.** `qr.py` renders a struck-through
`docrender-dead` span; `links.py` renders the same for a dead reference and
`markerlinks.py` states the rule outright — *"a dead reference never degrades into a
span... falling back would be a silent second legal path."* **Three directives share
one pattern, and the only one that failed silently was the one whose absence a reader
cannot infer.** A missing QR is obviously missing. A missing form on a page that
already shows one form looks deliberate.

⚠️ **It was in the build report the whole time**, under `dead_links`, naming the bad
slot and listing the legal ones. Nobody read it — `next-build-spec.md` BUILD 2's
premise acquiring a live fourth instance. ⭐ **So the fix is not a new message. It is
the message that already existed, on a second SURFACE.**

✅ **And it reaches paper for free.** `base.css` gives `.docrender-dead` a `--dr-dead`
dotted underline unscoped to any medium. Verified live 2026-08-19.

---

## ⭐ SPLIT OUT OF `program.py` THE SAME DAY IT SHIPPED

`program.py` held the flow strip and this embed and reached 16,949 B; adding
`collapsed:` would have pushed it past the ceiling. 🔴 **But size was the TRIGGER, not
the REASON** — `specs/visibility-split.md` §1: *"The cut that is worth making follows
the concerns. It also fixes the bytes. If those two ever disagree, follow the
concerns."*

They agreed. A strip is NAVIGATION; a form is an EMBED. They share no state and call
none of each other's helpers.

⚠️ **And the same thing happened to THIS file on 2026-08-30**, twice, which is why this
document exists. Same trigger, same test, same answer: the module keeps the mechanism,
the sibling takes the arguments.

---

## ⭐ `collapsed:` AND `reload:` DEFAULT OPPOSITE WAYS, ON PURPOSE

`collapsed:` defaults to **no fold at all** because hiding a compliance form is an
editorial decision that must be declared. `reload:` defaults to **on** because
offering a reload button is not. ⭐ The asymmetry is the point: a key whose default
changes what a reader can SEE has to be explicit; a key whose default adds a harmless
affordance does not.
