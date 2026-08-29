# `buildstamp.py` — rationale and post-mortems

Sibling to `docrender/buildstamp.py`. **The steps, values and warnings live in the
module; the incidents that created them live here.** Extracted 2026-08-29 when that
file reached 21,149 B against a 22,528 B hard read limit — ~70% narrative against
~40 lines of real mechanism, which is the point at which the one thing that must stay
editable stops being editable.

Suffix convention is Michael's (`publish-dl.md` set it). Do not invent a second name
for this job.

---

## 🪦 The corner mark is SITE + DATE, and it is not negotiable (2026-08-28)

> Michael, on a corner mark reading `URITP Safety · General Safety for All · 28 Aug 2026`:
> *"ew ew ew ew FUCK that header of all that additional text. NO. just site name and date, like before."*

~~The corner mark names the program.~~ Shipped in PR #182, reverted in #184, live for
about seven minutes.

🔴 **The argument for it was sound and the argument was not the point.** It went: the
flow strip stopped printing, `program.py` calls the program name its payload, so the
name should survive onto the one printed line that already carries provenance. Every
step of that is true. **What it never asked is whether the corner mark had room for a
third fact.**

⚑ **Generalises, and it is the more useful half: a line that carries two facts is a
STAMP. A line that carries three is a HEADER.** The difference is not length, it is what
a reader does on meeting it — a stamp is glanced at and dismissed, a header is read.
Adding a third clause silently changed the ELEMENT, not just its content, and nothing in
the reasoning about payloads could have caught that. 🚫 *"This fact belongs on that line"
is an argument about the FACT. Whether the line can take it is a separate question and it
has to be asked separately.*

⚠️ The orientation gap it was solving is real and is now simply open: a printed policy
sheet does not say which program handed it to a reader. 🚩 Not a licence to put it back
on this line — it needs its own element beside the h1, and Michael rules on that.

🚫 `program.flow_names()` was deleted in the same pass rather than left for a future
caller. An exported function with no caller is the dead surface this engine kills on
sight, and keeping it "for when we do this properly" is how `sort:` sat inert in eleven
content files.

---

## 🔴 It never printed. Fixed 2026-08-19 by moving it out of the footer entirely

This hook used to hand its markup to `config.copyright`, which Material renders inside
`.md-footer-meta`. `assets/print-chrome.css` hides that element in its chrome-off list,
with `!important`, and then separately tried to bring `.buildstamp` back:

```
.md-footer-meta { display: none !important; }   <- the ancestor
.buildstamp     { display: block; }             <- could never win
```

⚠️ **`display: none` on an ancestor removes the whole subtree from the box tree.** A
descendant cannot opt back in — it is not a specificity contest, the box does not exist
to style. So the exception `print.css` argued hardest for, in its own words *"the one
question nobody can answer about a piece of paper is how old it is"*, had never once fired.

⭐ **Confirmed from OUTPUT, not from reasoning**, and that distinction is why it took a
day. The suspicion came from knowing Material's footer structure, which is a PROXY read,
and this house has a scar about presenting one as a verification. The first two PDFs could
not settle it either, because that page carried `hide: [footer]` and no footer could print
there regardless. A third PDF — footer NOT hidden — showed no stamp, no PR number, no SHA,
no `unstamped`. **That** is the evidence.

🔴 **And the CSS fix would have been the wrong fix.** Hoisting `.buildstamp` out of the
hidden subtree repairs exactly one class of page and leaves the hole open, because
`hide: footer` is a CONTENT decision and pages already use it. ⚑ A rule that can be
switched off by a frontmatter key it does not know about is not a guarantee.

---

## ⭐ Two placements, and they carry different text on purpose

> Michael, 2026-08-19: *"corner mark print only."* Then, on seeing it: *"I definitely do
> not want that PR number in the header. I'm fine with URITP safety in the date, but I
> definitely do not want the PR number in that!"*

🔴 **The build identifier is screen-only, and the reason is AUDIENCE rather than taste.**
A screen reader of these sites is Michael or a collaborator, and `PR #157` answers *is this
deploy current* for exactly that person. A printed sheet goes to a guest artist, a student,
a binder, a wall — and to that reader a PR number is unreadable internal plumbing on a
safety document. ⚑ **A build identifier is provenance for the BUILDER and noise for the
READER, and print is the surface where the reader is not the builder.**

⭐ Same rule this family already locked, from a new angle. `assets/base.css` carries NO
ROUTE BACK TO THE SOURCE; `pagefoot.py` records that `repo_url` is unset so no repository
widget appears; `instances/uritp-safety/site.yml` sets `edit_links: false` because *"a link
that looks like an invitation and delivers a 404 is a DEAD CONTROL."* A PR number on a
printed policy is the same category. **The rule was already written down and the corner
stamp was the first surface to break it.**

⚠️ So the printed sheet no longer names a commit at all, and that is a real trade. Debugging
a stale PRINTED page means finding the page on screen and revealing the foot disclosure.
Correct for these documents — but if a printed sheet ever has to be traced to a specific
build, this is the decision to revisit.

⚠️ **The 08-28 revert was the SECOND trim of this line by ruling**, which is worth seeing as
a pattern rather than two incidents: first the PR number came off, then a program name went
on and came straight back off. **Both additions were defensible and both were refused on
sight.** 🚩 The next person with a fact that "belongs" here should read that as the standing
answer: it is full, and it has been full twice.

---

## ✅ The disclosure, and what it is allowed to say (2026-08-19)

> Michael: *"hide behind a small new svg icon in the footer that reveals a popup when
> hovered that displays that text. purely for debugging - no link."*

🔴 **The popup carries the PR string and nothing else.** The first version put the deploy
timestamp, the engine SHA and the content SHA in there too: *"did you add the word 'engine'
to the footer icon???? remove that. only a pr string."*

⚑ **Four facts do not answer one question faster.** "Is this the latest push" is settled by
the PR number alone — it either matches the last merge or it does not. The timestamp and both
SHAs were things I could compute rather than things the question needed, and the give-away is
that they had to be joined with separators to fit on a line. *A debugging readout that needs
punctuation is carrying more than one fact.*

⚠️ **And that sentence predicted the 08-28 revert word for word**, on a different element,
and I did not hear it while writing the thing it condemned: the corner mark's third clause
needed a second `·` to fit. **The tell was already written down in the same docstring.**

⚠️ What is genuinely lost: the ENGINE ref. Content and engine are separate repos with
separate deploys, so "the content is current but the engine that rendered it is three commits
behind" is invisible here. It is still in the build report. 🚩 If that starts getting asked,
the answer is a SECOND disclosure on the report page, not a longer string in this one — the
failure mode of a debugging readout is not being wrong, it is being too long to read.

🪦 **The `title` attribute is gone from both nodes.** On the corner copy it was dead weight
(paper has no hover); on the foot copy beside a CSS popup it would draw a browser tooltip over
ours after a delay — two renderings of one fact, the defect this repo has retired three
manifests over, arriving as a UI bug. Its removal also stopped shipping a commit SHA into
printed HTML that never renders.

🚫 **Not a link, and not a `<button>`.** There is nothing to activate: the popup is the whole
payload. A `<button>` would promise an action that does not exist — the same dead-control
argument `edit_links: false` and the print link policy already make. It is a `<span>` with
`tabindex="0"`, so a keyboard can reveal it via `:focus-visible` without claiming to be a
control.

⚠️ **The popup is hidden with `opacity`, not `display: none`, and that is an accessibility
decision.** `display: none` and `visibility: hidden` remove an element from the accessibility
tree, so a screen reader would lose the identifier entirely. At zero opacity with
`pointer-events: none` the text stays in the tree and is read normally, and it is absolutely
positioned so it costs no layout. Styling: `assets/foot.css`.

---

## 🔴 The glyph says BACK-END, not INFORMATION (2026-08-19)

> Michael: *"I want an icon that says less 'this is info' and more 'this is a back-end check-in'."*

The first version was a disc with an `i` knocked out of it. ⚑ **An `i` in a circle is a promise
about the AUDIENCE: it means "there is something here for you to read."** Every reader of these
sites — a student, a guest artist, somebody holding a printed policy — is invited by that glyph,
and the one thing behind it is a PR number they cannot use. **The icon was advertising to the
wrong person.**

✅ So it is a console prompt: a rounded square with `>` and an underscore knocked out. A terminal
window is the least ambiguous "this is machinery" mark there is, and it reads as *not for you* to
anybody who is not looking for it — exactly the audience filter the `i` was failing at.

⚠️ The previous glyph was also a guess at an ambiguous note. Michael's earlier instruction was
*"vert icon that the 'i' tho"*, which read either as INVERT the `i` or as USE SOMETHING OTHER THAN
the `i`. The disc satisfied the first reading; this satisfies the second, which was the intent.

🔴 **Inline `<svg>`, never an `<img>`.** An `<img>` is FETCHED even when hidden, and a request for
a 16px debugging glyph on every page of every site is absurd. Inline costs ~250 bytes and no
request.

---

## ⭐ THE LETTERHEAD (2026-08-29) — and what changed about "built once"

> Michael: *"i want to render logo-horizontal in the header at the left... the LOGO would be
> flush to the left, while 'URITP Safety' and the date print on the right. I also only want the
> date to ever be in buckets... with a YEAR and never the explicit date that it was printed. I
> also want to shrink the size of that text and make URITP Safety bold, while the new formatted
> date remains non-bold."*

### 🚩 This is the addition the line had NOT already refused

Two additions were refused on sight (the PR number, the program name) and this file's own
docstring said of a logo: *"a logo is not a third CLAUSE of text, it is a mark. The 08-28
objection was to reading a header; a background image adds nothing to read. That is an argument,
not a permission."* **2026-08-29 is the permission.** Recorded because the prediction and the
ruling agree, which is rare enough to be evidence the distinction was real rather than
convenient.

### ⭐ SEASONS: the buckets were CHANGED before they were built, and the reason is a live code

Michael's first proposal was **Fall Aug–Nov · Spring Dec–Mar · Summer Apr–Jul**. Shipped as
given, a sheet printed in December 2026 would have read `Spring` with no defined year — the
bucket straddles the New Year, so *"Spring 2026"* and *"Spring 2027"* are both defensible and
the engine would have had to pick one silently, forever, on a safety document.

🔴 **The fix is one boundary, not a new scheme: December belongs to Fall.** Shipped as
**Fall Aug–Dec · Spring Jan–May · Summer Jun–Jul.** Three labels, twelve months, no bucket
crossing a year, so the year is never ambiguous and never needs a rule.

⭐ **And the argument that settled it is not tidiness, it is that the house already has this
vocabulary.** `F26` is the live production code for Big Love
(`brain-config/hooks/script-breakdown.md`), and an academic Fall term ends in December. So the
printed stamp now agrees with the code on the callboard instead of inventing a second season
vocabulary beside it. ⚑ *When a system already names a thing, a new surface should read that
name rather than derive its own — a second vocabulary is a second claimant wearing a calendar.*

⚠️ **Michael asked for FOUR buckets and got three, deliberately and out loud.** Three labels
already partition all twelve months, so a fourth would have to split an existing one
(`Winter Jan–Feb`, Spring to Mar–May). Named rather than quietly delivered: the count was the
ask and the partition was the requirement, and they disagreed.

### 🔴 The date is still built ONCE. Only the URL is per page.

The 08-28 revert deleted per-page composition of this mark and said so: *"a build spanning
midnight must not stamp two different dates onto one site."* That rule is UNCHANGED and the
season string is still computed once at `on_config` — a season boundary is far less likely to
be crossed mid-build than a midnight, but the argument is identical and cheaper to keep than
to re-litigate.

⚠️ **What is per page is the logo URL, and it has to be.** `util.relative_url` needs the
consuming page, and a letterhead renders at every depth in the tree, so it is maximally exposed
to the `../` arithmetic that shipped wrong three separate times (`links.py`, `router.py`,
`datatable.py`). The element is therefore assembled in `on_page_content` from a value computed
once. **One computed fact, one resolution per page: still one claimant.**

### ⭐ The logo is declared by NAME, and the resolution was already built

```
print:
  logo: logo-horizontal      # the STEM. No path, no extension.
```

`images.on_files` indexes every image in the content tree by lowercased filename stem before any
page renders, so the file can live anywhere, a `.jpg` can become a `.svg` without touching config,
and **two files sharing a stem are refused loudly** under `duplicate_id`.

🔴 **THAT LAST ONE IS A LIVE TRAP FOR THIS SPECIFIC CHANGE AND IT IS WHY THE ENGINE CHECKS
`COLLISIONS` ITSELF.** `logo-horizontal.jpg` is in the content repo today. Dropping
`logo-horizontal.svg` beside it creates two files with one stem, the name leaves `images.INDEX`
entirely, and the letterhead silently stops rendering. **The SVG must REPLACE the JPEG, not join
it.** Reported by name with the fix in the message rather than left as a blank corner.

⚠️ **AND THE JPEG IS FINE MEANWHILE, WHICH CORRECTS SOMETHING I SAID EARLIER IN THE SESSION.**
I warned that a JPEG's opaque white box would show against the safety site's parchment ground.
That is true on SCREEN and irrelevant here: this element is print-only and paper is white, so the
white box is invisible. **A format objection has to be aimed at the surface the element actually
renders on.** The SVG is a crispness upgrade at 300dpi, not a prerequisite.

🚫 Not a path in `site.yml` (that is the `../` bug with a person in it), not `assets/` (a logo is
an organisation's identity, not engine machinery, and six sites will not share one image), not
inline base64 (binary in a config file, unreviewable in a diff).

⭐ **Absent means no letterhead** — the `_uses_router` polarity. Five of six sites print exactly
as they did. And the mark SPAN is omitted entirely when no logo resolves, rather than emitted
empty: an empty box spends the whole height budget on nothing.

### 🔴 The height cap was MEASURED and the first number was wrong

Michael capped the header at 140% of its current height. A 6mm mark, derived from the stamp's own
font-size and padding, rendered at **146%** — because the border and padding sit OUTSIDE the flex
row and the arithmetic had assumed they were inside it. Shipped at 5.5mm = **137%**.

⚑ *A budget expressed as a ratio of an existing box cannot be computed from the properties you
can see — the box you are a percentage of has to be measured.* Full table in
`assets/print-identity.css`.

### 🔴 `var()` in `background-image` rendered BLANK, and that is why the URL is inline

The intended shape was `background-image: var(--dr-print-logo)` with the URL delivered as an
inline custom property — tidy, and it kept every path out of the stylesheet. It produced an
empty box in WeasyPrint **three ways**: inline with quotes, inline bare, and declared in the
sheet itself. Browsers do support that substitution, so the tidy version is probably fine in
Chrome.

⚑ **"Probably fine" is not a standard this element can be held to, because its failure is a
blank corner that reports nothing.** The variant that rendered in the one engine available to
test is the one that shipped. The URL still never appears in a stylesheet — the engine writes it
— so the leak rule was never what that custom property was protecting.

### ⚠️ The seasonal date lands on EVERY site, and that is deliberate

The letterhead is opt-in; the date format is not. `instances/uritp-safety/site.yml` carries
Michael's own ruling that *"the content that appears in the header or footer on print should not
differ per site"*, so a per-site date format would contradict the rule this change is serving.
Said out loud rather than discovered on somebody's printer.
