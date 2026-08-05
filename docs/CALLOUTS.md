# CALLOUTS -- why the `!!!` blocks look the way they do

The machinery is `docrender/blocks.py` (the emitter) and `theme/blocks.tsv` (the
thirteen rows). **Adding or recolouring a family is a row in the TSV.** Nothing in
this file is needed to do that.

This file holds the ARGUMENT: what Material does, what we take from it, what we
beat, and the measurements behind the choices.

> **Why this exists as a separate file.** The argument reached ~15KB inside a
> Python docstring and pushed the module 5,127 bytes past the hard read limit.
> What belongs in a module docstring is what somebody editing *that file* needs in
> front of them. A contributor asking "why is the focus ring at full strength" is
> not editing the emitter.

---

## Where the thirteen come from

Twelve are **Material's** names. They are what a reader TYPES, and Material ships
an icon and a flavour rule keyed to each one, so they are not ours to rename.

⚠️ **That is not the same as the list being closed, and the table's header used to
imply it was.** Python-Markdown's admonition extension matches the word after
`!!!` and lowercases it straight into a class, with **no validation of any kind**
(verified in its source). Any word has always rendered. `good` is the first family
we **declare** rather than inherit.

**The bar for a fourteenth:** you can say in one sentence what it means that none
of the thirteen does. A vocabulary nobody can recite is decoration.

---

## Material paints FIVE surfaces per family, all from one hardcoded hex

Read out of
`src/templates/assets/stylesheets/main/extensions/markdown/_admonition.scss`,
not remembered:

```scss
$admonitions: ("note": pencil-circle $clr-blue-a200, ...12 entries)

:root { --md-admonition-icon--#{$name}: svg-load(...) }

.md-typeset .admonition {
  box-shadow: var(--md-shadow-z1);
  transition: box-shadow 125ms;                          // A LITERAL
  &:focus-within { box-shadow: 0 0 0 4px rgba($clr-blue-a200, .1) }
}
.md-typeset .admonition.#{$name} {
  border-color: $tint;
  &:focus-within { box-shadow: 0 0 0 4px rgba($tint, .1) }
}
.md-typeset .#{$name} > .admonition-title {
  background-color: color.adjust($tint, $alpha: -0.9);
  &::before { background-color: $tint; mask-image: ...icon }
  &::after  { color: $tint }
}
```

The box border, the title bar wash at 10% alpha, the **icon** (a mask whose
visible colour comes from `background-color`), the details marker on a
collapsible, and **the focus ring**. Not one of them is a variable, which is the
whole reason no theme change ever reached a callout before 2026-08-05.

🔴 **Reading the source is why the selectors worked first time.** The previous
attempt to beat a Material rule in this engine, the dark-mode blue link, shipped
against a selector quoted from memory, was wrong in both halves, and survived a
full day because the fix looked structural. **A selector stated from memory is a
guess wearing a bracket.**

---

## Specificity: a TIE, won on source order, and that is its only honest name

Material's flavour rules compute to **(0,3,0)**. The generated rules use the same
selectors, so they are also (0,3,0), and every stylesheet this engine ships is
linked **after** `main.css`. Equal specificity plus later in the cascade means we
win.

⚠️ **There is nothing to delete.** Material's rule stays in its own stylesheet.
`chrome.css`'s ARMOUR block carries the same warning for the same reason: the last
time somebody in this repo called a cascade tie "structural," the mislabel is what
let a wrong diagnosis ship for a day.

⭐ **The per-family FOCUS rules are the exception.** They carry one more class, so
`.admonition.good:focus-within` is **(0,4,0)** -- it beats Material **outright**
and does not depend on load order at all. The base ring is (0,3,0) and does tie.
Two mechanisms in one sheet, labelled differently on purpose.

⚠️ **The `details` selectors are defensive and could not be verified.**
`_admonition.scss` says its styles "also apply to details tags, which are rendered
as collapsible admonitions with summary elements as titles" -- but the rule that
makes that true lives in a file this pass did not read. So every rule is emitted
for both spellings. A selector that matches nothing costs a few bytes; a missing
one costs a family that quietly stays blue.

---

## 🔴 The focus ring was hardcoded blue, and was never a focus indicator anyway

Found 2026-08-05 while reading the SCSS for an unrelated question (which glyph
each family gets).

**Half of it was ordinary wiring.** Material paints the ring twice, base and per
flavour, so tabbing to a `success` box flashed *Material's* green rather than the
theme's -- and `good`, which Material has never heard of, flashed a **blue ring
inside a green box.** Every family now emits its own from the same token that
paints its border. One cell, five surfaces.

**The other half is the finding.** Material's ring is the tint at **10% alpha**. A
10% mix composites to 90% of the ground it sits on, so it *cannot* separate from
that ground. That is arithmetic, not a property of any palette.

Measured on the real `eos` rows against `bg` -- the ring sits **outside** the box,
so the page ground is what it composites over, not the callout:

| alpha | eos dark | eos light |
| --- | --- | --- |
| **10%** (Material's) | 1.12 FAIL | 1.13 FAIL |
| 40% | 1.82 FAIL | 1.69 FAIL |
| 70% | 3.09 pass | 2.68 FAIL |
| **100%** | **5.06 PASS** | **4.63 PASS** |

WCAG 1.4.11 asks **3.0** of a non-text indicator. Nothing below full strength
clears it on both schemes, because the worst case is `text-faint` -- a grey,
sitting near its own ground **by design**, which no opacity can pull away from it.

⚠️ **So porting the 10% faithfully would have wired up a broken value.** The ring
takes the token at full strength, justified by the numbers this repo already holds
the *border* to:

| token | dark | light |
| --- | --- | --- |
| `accent` | 7.05 | 5.84 |
| `accent-2` | 6.63 | 5.81 |
| `good` | 7.27 | 5.42 |
| `warn` | 9.91 | 5.30 |
| `bad` | 5.82 | 5.05 |
| `info` | 7.94 | 4.96 |
| `text-faint` | 5.06 | 4.63 |

One bar, one set of numbers, no new column.

**An alpha is not a colour choice, it is a CEILING on how different two things can
be.** "Match the framework" and "be visible" were not both available, and the
framework does not get to be the tie-breaker on an accessibility floor this repo
has already written down.

🚫 **The 10% wash stays on the title bar**, which is the surface it is right for: a
tint behind bold text, not an indicator that has to be seen from across a room.
Same construction, different job. **Do not "fix" that one to match this one.**

⚠️ **The ring WIDTH is still a literal, and it is an honest gap.** `0.2rem`,
because no token in any vector expresses a ring width. `border-w` is the obvious
candidate and it is wrong -- a hairline at 1-1.5px, which would make the ring
vanish. Naming a token that means something else to avoid a literal is precisely
the bridge-row mistake PR #82 had to revert.

---

## The glyphs are real SVG files, which is why the table holds a NAME

Material's `$admonitions` map pairs each family with an icon **name**
(`note` -> `pencil-circle`, `success` -> `check`), and `svg-load()` inlines that
file's markup into a custom property at **its** build time. So by the time a page
renders, `--md-admonition-icon--success` is already a complete data URL -- 129
bytes of `<svg>` for the check -- and borrowing it costs a pointer.

⭐ **That is the whole reason an `icon` column is allowed to exist.** An earlier
version of `blocks.tsv` refused one outright, on the grounds that changing an icon
means authoring an SVG data URL and image data does not belong in a colour table.
**That refusal stands.** The column holds a name.

⚠️ **A declared family with no icon wears the NOTE PENCIL.** Material's base rule
sets `mask-image: var(--md-admonition-icon--note)` unconditionally, so a family it
has never heard of does not *lose* its glyph. That is the harder failure to see: a
missing glyph is obvious, a wrong glyph on a correctly-coloured box reads as a
near-miss in the stylesheet rather than as an unfinished row in a table. Reported
by the build.

⚠️ **An unknown icon name is REFUSED rather than passed through.** Emitting
`var(--md-admonition-icon--nonsense)` gives an undefined var with no fallback,
which is invalid at computed-value time, which sets `mask-image: none`, which
removes the mask, which leaves the `::before` painting its full
`background-color` as a solid **20x20px square.** Keeping the pencil is wrong and
legible; the square is wrong and alarming.

🔴 **And the same square arrives from an old browser, which that guard cannot
see.** Unprefixed `mask-image` needs **Safari 16.4**; below that the declaration
is dropped as unknown and a *correct* icon name paints the square. Material's own
compiled stylesheet emits both spellings -- read off the published
`main.ec1eaa64.min.css`, not recalled -- so `_icon` emits both, prefix first.

**A guard against one CAUSE of a symptom is not a guard against the symptom.**

---

## ⚠️ Every colour carries a fallback, and here that is not defensiveness

`markers.py` deliberately emits `var(--dr-x)` with **no** fallback, and says so: a
marker naming a token the active theme does not emit paints nothing, and an
unstyled marker is still readable text.

**A callout is not.** On a nine-token local theme (`utility`, `database`, `base`)
nine of the twelve inherited families name a canonical token that is never
emitted:

```
border-color: var(--dr-accent-2)     -> invalid at computed-value time
                                     -> unset -> currentColor
background-color on the ICON         -> unset -> transparent
                                     -> THE ICON DISAPPEARS ENTIRELY
```

The icon is a mask whose visible colour comes from `background-color`, so no
colour means **no icon at all.**

⚠️ **And the fallback has to be INSIDE the `var()`.** A second `border-color`
declaration ahead of it does not help: a property that is invalid at
computed-value time is set to `unset`, and earlier declarations in the same rule
are **discarded rather than used**. `var(--dr-x, currentColor)` is the only
mechanism that works.

---

## The 10% wash, and why it is computed one layer later

Material computes the title bar as the tint at 10% alpha at **build** time, from a
Sass colour. That is not available to us -- the value is not known until the
browser resolves the custom property -- so the wash is
`color-mix(in oklch, TOKEN 10%, transparent)`. Same result, one layer later.

`in oklch` matches what `base.css` already uses for marker chips, so the mixing
space is consistent across the two places this engine tints a token.

---

## 🔴 Post-mortem: this module killed every build on 2026-08-05, at import time

`blocks.py` imported `_token_sets` from `markers.py`. That function existed only
in one session's version of `markers.py`, on a branch closed unmerged as **PR
#84** after a parallel session shipped the same features first (**#83**). Their
markers exports `_known_tokens`. **The caller was kept and the callee was lost.**

```
hooks/01d_audit -> tokenaudit -> assets -> blocks -> markers
ImportError: cannot import name '_token_sets' from 'docrender.markers'
```

**An ImportError in a hook is not a render failure.** It is raised while mkdocs
**validates its config**, before a single page is read -- so `strict: false`, the
warn-never-die rule and the token audit's own `try/except` are all downstream of
it and none can help. All four sites, at once, with no page to report on.

**Second occurrence of one shape in one day.** That morning `tokenaudit` called
`theme._canonical_row()` after that function moved to `vectors.py`, with the same
result. **A cross-module call whose callee moved.** The post-mortem for the first
was written eight hours before the second shipped, which is the argument for a
CHECK rather than a lesson.

🔴 **And the verification that missed it was the real defect.** The generator was
run in a sandbox before shipping and its output checked -- rule count, brace
balance, specificity -- but the test script **reimplemented `_colour`** rather
than importing it. So the logic was genuinely proven and the import was never
executed once.

⭐ **A test that reimplements its subject tests the reimplementation.** The only
defence that has worked since is stubbing at the I/O boundary and importing
everything above it.

⚠️ **The underlying defect is narrowed, not fixed.** `_TOKEN` and `_known_tokens`
still cross a module boundary as private names. What is gone is the one that
encoded a POLICY `blocks.py` does not share -- `markers._colour` has no fallback
by design, and routing callouts through it would have cost **10 of 12 families
their icons on 3 of 4 sites.** The honest fix is a shared resolver both modules
import from, probably in `vectors.py`, which already owns *what does the theme
contain*. That is a refactor.

---

## 🔴 Post-mortem: the transition claim was half true, which is worse than wrong

The comment above the box block read: *"A shadow and a transition, both of which
Material states as its own variables -- so those are mapped in chrome.css and NOT
restated here."*

`box-shadow: var(--md-shadow-z1)` **is** a variable and **is** mapped.
`transition: box-shadow 125ms` is a **bare literal** in Material's source and
`chrome.css` never touched it.

**A sentence that is true about one of two things it names reads as verified, so
nobody checks the other half.** Now
`var(--dr-motion-fast, 125ms) var(--dr-ease, linear)`.

---

## Where the values live

| What | Where |
| --- | --- |
| the thirteen families and their tokens | `theme/blocks.tsv` |
| the emitter | `docrender/blocks.py` |
| token to Material variable mappings | `assets/chrome.css` |
| the measured pairs and their floors | `theme/contrast.tsv` |
| what authors are told | `template-docs` `authoring/writing.md` |

⚠️ **The last row does not derive from the first.** Adding, recolouring or
retiring a family means editing both, in the same session. That is not a
hypothetical: on 2026-08-05 twelve governed families shipped and the authoring
page went on telling authors there were three, for four hours.
