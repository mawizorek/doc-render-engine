"""Hook 05 -- serve stylesheets and scripts that live OUTSIDE the content tree.

This is the hook that makes the purity rule physically possible, so read this
before anyone 'fixes' it by moving the CSS back where it looks like it belongs.

MkDocs publishes files it finds inside `docs_dir` and resolves `extra_css`
relative to `docs_dir`. Read literally, that means stylesheets and scripts must
live inside the doc tree. v1 did exactly that, and it is the single largest
reason its content folder was full of machinery.

The way out is the `on_files` event: append File objects whose source is
somewhere else entirely -- here the engine's own assets/ and the instance's
folder. MkDocs treats them as ordinary site files from that point on.

🔴 THIS FILE IS 32KB AND OVER THE ~22.5KB READ CEILING. It owes an
`assets-dl.md` extraction on the `buildstamp-dl.md` standard -- the mechanism
here is ~90 lines and the rest is incident history. Flagged since 2026-08-29
(PR #190) and getting worse, not better: every asset group added since has added
prose. **The next structural change to this file should extract first.**

=============================================================================
BUG: ON_CONFIG CANNOT SEE THE PAGES. THIS BROKE THE ROUTER COMPLETELY.
=============================================================================
MkDocs runs EVERY hook's `on_config` before ANY hook's `on_files`. So at
`on_config` time `state.BY_SRC` is empty -- nothing has read a frontmatter block
yet -- and the old `_uses_router()` check therefore answered False on every
single build.

Consequence: `router.js` and `router.css` were PUBLISHED (that happens in
`on_files`, by which point BY_SRC is populated) but never LINKED from any page.
The form rendered, looked completely correct, had no JavaScript attached, and so
submitting it did what an unhandled form does: reloaded the page. Which is
precisely the symptom -- "the page reloads so my guess is the unlock just
doesn't hold." The unlock was never running.

The fix is to decide from something that EXISTS at on_config time. Two sources,
both cheap: the instance's `routes.yml`, and a scan of the content tree for the
frontmatter keys. The scan is one pass over small text files, done once and
cached, which is a fair price for a check that cannot silently answer wrong.

⭐ FEATURE ASSETS ARE STILL PUBLISHED ONLY WHERE THE FEATURE IS USED. The
principle was right; the implementation asked a question too early.

⚠️ AND THAT IS WHY THE GENERATED SHEETS ARE UNCONDITIONAL. `tokens.css`,
`marks.css` and `blocks.css` are built from theme/*.tsv, which is read straight
off disk and does not care which event is running. Nothing about them can answer
wrong early, so they are never gated on a usage check -- the trap above only
bites a decision that needs the page map.

⚠️ THE DATA-TABLE ASSETS ARE UNCONDITIONAL TOO, FOR A DIFFERENT REASON WORTH
STATING (2026-08-04). They are feature assets and they look gateable, but the
question "does this site embed a table" cannot be answered cheaply or safely at
on_config: a `!!! data` block lives in the BODY of a page, not in the first 2000
bytes a frontmatter scan reads, so the router's trick does not transfer. The
choice is between a whole-body scan of every page and ~24KB that matches nothing
and binds no listener when no table exists. A check that can answer wrong is more
expensive than the bytes -- the whole lesson of the section above.

⚠️ AND THE PRINT LAYER IS UNCONDITIONAL FOR THE SIMPLEST REASON OF THE THREE
(2026-08-06): there is no question to ask. Every page can be printed, so a
usage check would have no input and no answer. It is rules behind an
`@media print` gate that cost a screen reader nothing.

⚠️ AND THE FLOW LAYER IS UNCONDITIONAL FOR THE DATA-TABLE REASON, NOT THE PRINT
ONE (2026-08-19). `chain:` and `forms:` ARE frontmatter keys, so unlike `!!! data`
the router's scan trick genuinely would transfer here -- which makes this the
first asset group that was gateable and was left ungated on purpose. Two reasons,
both honest: a second cached scan is more code and one more thing that can answer
wrong, and `flow.css` is `.dr-flow*` rules that match nothing at all on a site
with no chains. ⭐ AND THE CONSEQUENCE OF A WRONG ANSWER IS WORSE HERE THAN
ANYWHERE ELSE IN THIS FILE: with `hide: footer` on program pages the flow strip is
the ONLY navigation on the page, so a gate that answered False by mistake would
ship an unstyled strip as a site's sole means of moving -- the exact failure
Michael reported in words on 2026-08-19 ("all this other foot matter"), arrived at
by a clever optimisation instead of a missing file.

⚠️ AND THE QR AND ALIGN LAYERS ARE UNCONDITIONAL FOR THE DATA-TABLE REASON
EXACTLY: `!!! qr` is a BODY directive and `{.align-*}` is an inline class, so the
frontmatter scan cannot see either. Not a judgement call -- there is no cheap
question to ask.

=============================================================================
⚠️ EVERY ASSET URL CARRIES A CONTENT FINGERPRINT
=============================================================================
    assets/base.a41f7c92.css

First eight hex of the file's own SHA-256, so the URL CHANGES when the bytes
change and stays identical when they do not. Not a micro-optimisation: a stable
asset URL on GitHub Pages meant a browser kept the old stylesheet after a
correct deploy, and every symptom pointed at the build. A fingerprint makes
"I published and do not see my change" impossible for assets.

=============================================================================
⭐ `hand_written_css()` IS THE SINGLE SOURCE FOR WHICH SHEETS EXIST
=============================================================================
docrender/tokenaudit.py used to keep its own hardcoded tuple of stylesheet
names, and its own docstring records that the tuple went stale WITHIN TWO HOURS
when nav.css was split out of base.css -- so the audit page under-reported
silently, which is the worst possible failure for a page whose whole job is to
be trusted. That docstring's remedy was to cross-check it against this file
whenever either changed: a manifest with a reminder attached.

This repo has killed three manifests for that defect and then kept a fourth
inside a function. One list now, derived, in the file that has to be right or
nothing ships at all.

🔴 AND THE WARNING IN `hand_written_css()` HAS NOW FIRED THREE TIMES FOR REAL.
It said "adding a fourth group and forgetting it here is precisely how the old
hardcoded tuple went stale" -- written before any fourth group existed.
`_FLOW_ASSETS` became the fourth on 2026-08-19, `_QR_ASSETS` the fifth on
08-21, and `_ALIGN_ASSETS` the sixth on 08-29; every time the line was read
first and the group joined the walk in the SAME COMMIT. **A warning obeyed three
times is worth more than any number of anecdotes about why it exists.**

🔴 AND ON 2026-08-21 THE SAME DEFECT WAS FOUND ONE LAYER DOWN, WHERE NO WARNING
WAS WATCHING. `hand_written_css()` guards against a forgotten GROUP. Nothing
guarded against a forgotten FILE INSIDE a group -- and `print-chrome.css` had
been on disk, absent from `_PRINT_ASSETS`, unpublished and unaudited since the
six-way print split. See the tuple's own header for the full account.

⚠️ THAT IS ALSO WHY `_PRINT_ASSETS` IS A CONSTANT AND NOT A LITERAL IN `_plan()`.
It is a separate group only because of WHERE it loads (see below), not because it
is a different kind of thing -- and `hand_written_css()` derives from every group
so the audit cannot go stale the way it did in 2026-08-04.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from mkdocs.structure.files import File

from . import blocks, markers, state, theme
from .util import load_yaml

_ROUTER_KEYS = ("router:", "router_code:")

#: Load order is deliberate and is NOT alphabetical. Every entry has a reason:
#:
#:   base.css       the Material mapping everything else builds on
#:   chrome.css     🔴 THE ARMOUR lives here and is a specificity TIE with
#:                  Material's compound primary rule, won purely on SOURCE
#:                  ORDER. Move this before base.css and every dark-mode link
#:                  reverts to Material's indigo -- a live bug, not a wobble.
#:   nav.css        split out of base.css 2026-08-04 at the 22KB hard line. It
#:                  OVERRIDES Material's drawer borders, so it must land AFTER
#:                  the base mapping -- move it earlier and the phones-only
#:                  double rule comes back, a defect that is invisible at desktop
#:                  width and was found from a screenshot.
#:   type.css       overrides Material's heading rules, so also after the base
#:                  mapping.
#:   foot.css       the page foot -- .pagefoot, footer chrome, the build stamp.
#:                  Position free; must follow base.css, which maps --md-footer-*.
#:   data.css       the table layer, itself split out of base.css
#:   data-list.css  overrides table rules inside a container query, so it loads
#:                  after the rules it overrides
#:   data.js        drives both table layers
#:
#: Reorder these and list mode loses to the table it is meant to replace.
_DATA_ASSETS = (
    "base.css",
    "chrome.css",
    "nav.css",
    "type.css",
    "foot.css",
    "data.css",
    "data-list.css",
    "data.js",
)

#: Published ONLY to a site that uses the feature. See `_uses_router`.
#:
#: FOUR FILES, TWO HALVES, split on 2026-08-16 when both router files hit the
#: engine's 22KB hard read limit (router.js at 22,232 B, router.css at 21,273 B
#: with no room left for the change that was needed). The seam is the one
#: router.js had already declared in its own header:
#:
#:   router.css + router.js      the FORM, the curtain, the crypto. Only where a
#:                               router is declared or inherited.
#:   navtree.css + navtree.js    the SEALED SIDEBAR. On every page of the site.
#:
#: 🔴 navtree.js MUST COME BEFORE router.js, AND THAT IS AN ORDERING LAW OF THE
#: SAME CLASS AS `_DATA_ASSETS` ABOVE -- not alphabetising, not tidiness.
#: router.js calls into `window.docrenderNavTree` during its own IIFE, so a later
#: position makes every one of those calls a TypeError on the first paint.
#: ⚠️ AND THE FAILURE IS THE QUIET SHAPE: the form keeps unlocking pages
#: perfectly while the revealed menu silently stops being injected, which is
#: exactly the class of defect that survives longest here. router.js guards the
#: reference, so a MISSING navtree.js degrades the same safe way rather than
#: killing the unlock -- but a mis-ORDERED one is still a dead sidebar, and no
#: guard can fix an order.
#:
#: ⭐ THE CSS ORDER, BY CONTRAST, IS GENUINELY FREE, and it is said out loud so
#: nobody defends a position that was never load-bearing: navtree.css is `.dr-`
#: classes overriding nothing of Material's, and the one Material class it
#: touches deliberately INHERITS nav.css's top-level caps rather than fighting
#: it. It sits beside its own JS because that reads as one feature.
_FEATURE_ASSETS = ("router.css", "navtree.css", "navtree.js", "router.js")

#: 🔴 LOADS AFTER THE GENERATED SHEETS, AND THAT IS THE ONLY REASON IT IS A
#: SEPARATE GROUP RATHER THAN MORE ENTRIES IN `_DATA_ASSETS`.
#:
#: These sheets override Material rules and scheme-scoped properties that
#: `tokens.css` and `blocks.css` also write, at equal specificity -- so they win on
#: source order or they do not win at all. Put this group in `_DATA_ASSETS` and the
#: generated sheets land later, the overrides die silently, and paper comes out
#: wrong with no error and no report.
#:
#: It still loads BEFORE the instance's `site.css`, because a site keeps the
#: final word on its own look and paper is no exception.
#:
#: 🪦 `print-scheme.css` IS UNREGISTERED (2026-08-19), a comment-only tombstone on
#: disk: theme.py emits the paper palette inside tokens.css instead. **A file in
#: assets/ absent from these tuples is never published and does nothing.**
#:
#: =========================================================================
#: 🔴 THAT SENTENCE CAME TRUE BY ACCIDENT AND COST EVERY PRINTED PAGE (2026-08-21)
#: =========================================================================
#: `print-chrome.css` -- 9,672 B, the chrome-off list and the corner stamp -- was
#: on disk and ABSENT FROM THIS TUPLE. So it was never published and did nothing,
#: and the nav drawer, the table of contents and the site header have been
#: printing on every sheet of every site since the split: the exact defect
#: print.css's opening paragraph was written to fix, reintroduced by an omission
#: rather than by a rule.
#:
#: ⭐ THE TELL WAS SITTING IN TWO FILES THAT DISAGREED IN PROSE. print.css's header
#: said "THE PRINT GROUP IS SIX FILES AS OF 2026-08-19" and listed print-chrome.css
#: among them; this tuple held five and said so. Neither number was derived from
#: anything, so both were free to be wrong, and only one of them was.
#:
#: 🔴 AND THE TOMBSTONE NOTE ABOVE IS WHAT MADE IT INVISIBLE: one file in assets/
#: is unregistered ON PURPOSE and one was unregistered BY ACCIDENT, and from this
#: tuple they are indistinguishable. A deliberate absence and a mistake look
#: identical in a list of what IS present.
#:
#: ⚠️ `hand_written_css()` COMPOUNDED IT RATHER THAN CATCHING IT. The token audit
#: derives its scan list from these tuples, so an unregistered sheet is invisible
#: to the audit as well -- no rule in print-chrome.css had ever been checked. The
#: derived list was doing its job perfectly and could not see the hole, because it
#: guards against a forgotten GROUP and this was a forgotten FILE.
#:
#: ⚠️ SO THE REMAINING GAP IS NAMED RATHER THAN LEFT: nothing compares assets/*.css
#: ON DISK against these tuples. A build that reported "on disk, unregistered:
#: print-scheme.css, print-chrome.css" would have made this obvious on day one --
#: and the tombstone would be one expected line rather than cover for a real one.
#:
#: 🔴 AND THAT GAP IS STILL OPEN, WHICH IS WHY EVERY SHEET ADDED SINCE HAS BEEN
#: REGISTERED IN THE SAME PR AS THE SHEET ITSELF (2026-08-29, three times:
#: print-identity.css, print-ink.css, align.css). The 08-21 incident is the whole
#: argument against a two-step, and a new sheet is exactly the moment the missing
#: disk-vs-tuple check would have mattered.
#:
#: EIGHT FILES, EIGHT JOBS, and each one answers exactly one question:
#:
#:   print.css          HOW WIDE IT RUNS    -- @page, the column unrailing,
#:                                             print-color-adjust, code wrapping,
#:                                             the transparent ground
#:   print-chrome.css   WHAT APPEARS AT ALL -- the chrome-off list and the corner
#:                                             stamp's own box
#:   print-flow.css     WHERE IT BREAKS     -- break-*, orphans/widows, h1-h6,
#:                                             tab labels, forced-open
#:                                             <details>, thead repetition,
#:                                             {.new-page}
#:   print-type.css     HOW BIG THE TYPE IS -- the dial, the ramp, weight,
#:                                             tracking, link decoration, and the
#:                                             data table's size anchor
#:   print-space.css    HOW MUCH AIR IS     -- block margins, list margins,
#:                      BETWEEN THINGS         justification, the tabbed set
#:   print-callout.css  WHAT THE BOX IS     -- the rule and indent, the icon,
#:                                             the font-size anchor
#:   print-identity.css WHOSE DOCUMENT IT   -- the letterhead row: the declared
#:                      IS                    logo mark, the two text weights
#:   print-ink.css      WHAT COLOUR IT IS   -- body ink black on paper; h1-h3
#:                                             keep the theme's ink
#:
#: 🔴 AND `print-ink.css` IS THE ONE MEMBER THAT CONTRADICTS print.css's FOUNDING
#: RULE -- *"THIS FILE IS STRUCTURE, NOT COLOUR"* -- which is why it carries a
#: ruling in its header rather than an argument. Michael exempted ONE property on
#: ONE medium (2026-08-29). 🚫 It is not a precedent for a second colour opinion in
#: this group; the next one needs its own ruling.
#:
#: ⚠️ THE JOB LINES ABOVE ARE ALSO CORRECTED. This table credited print.css with
#: "chrome off" AFTER that list had moved to print-chrome.css, and with a "link
#: policy" it does not contain -- print.css has no link rule at all, deliberately,
#: because base.css declares link decoration unscoped to any medium and it reaches
#: paper on its own (that file's dead-reference block is an argument for NOT
#: writing one here). A summary of somebody else's file is a second claimant.
#:
#: ⭐ EVERY ONE OF THESE SPLITS WAS FORCED BY THE SAME 22KB CEILING, and each seam
#: was already written in the header of the file that split -- which is also where
#: the measured argument for it lives, rather than being summarised here. **A FILE
#: AT ITS SIZE LIMIT IS USUALLY A FILE WITH A SEAM IN IT; trimming prose is what
#: you do instead of finding the seam.** ⭐ `print-identity.css` and `print-ink.css`
#: are the two members that were NOT forced by a split -- both are new subjects --
#: but in both cases every existing neighbour was inside ~330 B of the ceiling, so
#: the ceiling still decided WHERE they went.
#:
#: ⭐ AND THE ORDER *WITHIN* THIS GROUP IS GENUINELY FREE, stated out loud on the
#: `_FEATURE_ASSETS` precedent above so nobody later defends a position that was
#: never load-bearing. No two of these eight share a selector-and-property PAIR --
#: `.md-typeset h1` is written in print-type.css, print-space.css AND print-ink.css,
#: but they set size/weight/tracking, margins, and COLOUR respectively, and a
#: cascade fight needs both halves to match. What is load-bearing is the GROUP's
#: position.
#:
#: 🔴 AND KEEPING THAT TRUE IS WHY print-identity.css DOES NOT TOUCH
#: `.buildstamp--corner`. `display: flex` there would have been a genuine pair
#: against print-chrome.css's `display: block` on the same selector. The layout was
#: moved onto a net-new inner element (`.buildstamp__row`) specifically to avoid
#: creating the group's first real collision. That reasoning lives in the new
#: sheet's own header.
#:
#: 🔴 WITH ONE PROVEN EXCEPTION, ADDED THE DAY IT BIT: print-space.css §9 justifies
#: `.md-typeset p`, which MATCHES the corner buildstamp and beat print.css's
#: `text-align: right` on SPECIFICITY rather than order. Fixed by narrowing §9.
#: **The order is still free; what is not free is assuming two of our own files
#: cannot collide.** ⚠️ AND THAT EXCEPTION IS NOW LIVE FOR THE FIRST TIME: the
#: corner stamp it collides with has never actually been published until this
#: commit, so the narrowing has never been exercised on paper. Re-preview it.
#:
#: ⚠️ IF THAT EVER STOPS BEING TRUE, THIS COMMENT IS THE THING THAT ROTS. Three
#: likely ways now: print-type.css growing a `margin` on a heading it already sizes
#: (print-space.css's header names this as the likeliest); print-callout.css and
#: print-flow.css both reaching for `<details>` -- flow owns whether it is OPEN,
#: callout owns what it LOOKS LIKE; or print-type.css growing a `color` on a
#: heading, which is now print-ink.css's property.
_PRINT_ASSETS = (
    "print.css",
    "print-chrome.css",
    "print-flow.css",
    "print-type.css",
    "print-space.css",
    "print-callout.css",
    "print-identity.css",
    "print-ink.css",
)

#: THE FLOW STRIP AND THE EMBEDDED FORM (2026-08-19). See docrender/program.py
#: and docrender/forms.py.
#:
#: ⭐ ITS POSITION IS GENUINELY FREE AND THAT IS WORTH STATING SO NOBODY DEFENDS
#: IT LATER, on the same precedent `_FEATURE_ASSETS` and `_PRINT_ASSETS` already
#: set. Every selector in `flow.css` is a `.dr-flow*` / `.dr-form*` class that no
#: other sheet in this engine mentions, so it cannot win or lose a tie against
#: anything. It CONSUMES `--dr-*` tokens rather than defining them, and custom
#: property resolution does not depend on which sheet was parsed first.
#:
#: ⚠️ IT SITS AFTER THE PRINT GROUP BECAUSE IT CARRIES ITS OWN `@media print`
#: BLOCK, and reading it next to the other print rules is easier than hunting it.
#: That is legibility, not a load-bearing order. It stays BEFORE the instance's
#: `site.css` for the reason every group does: a site keeps the final word.
#:
#: 🔴 EVERY TOKEN IN THIS SHEET IS USED WITH A MATERIAL VARIABLE AS ITS FALLBACK,
#: which is not decoration. Tokens are generated per site from
#: theme/canonical/*.tsv, so a token that exists on `eos` may be absent on a
#: nine-token local skin -- the exact failure that left eleven callout families
#: painting `currentColor` on 2026-08-05, on the one site whose job was to break
#: loudest. Falling back to Material's own variable makes the worst case
#: Material's look rather than an invisible control, and an invisible control is
#: what this sheet exists to prevent.
_FLOW_ASSETS = ("flow.css",)

#: THE QR LAYER (2026-08-21, BUILD 6 step 5). See docrender/qr.py and
#: specs/qr-codes.md.
#:
#: 🔴 THE FIFTH GROUP, AND IT WAS THE FIRST SHEET IN THIS ENGINE THAT CARRIED BOTH
#: SCREEN AND PRINT RULES AS ONE FEATURE -- which is precisely why it is not in
#: `_PRINT_ASSETS`. That group is entirely `@media print` and loads where it does
#: for a cascade reason; a sheet with a screen half in it would make that group's
#: own header a lie. **A group is a claim about WHEN a sheet loads and WHY. Adding
#: a member that breaks the claim is worse than adding a group.**
#:
#: ⭐ ITS POSITION IS GENUINELY FREE, on the `_FLOW_ASSETS` precedent. Every
#: selector is a `.dr-qr*` class no other sheet mentions, so it can neither win
#: nor lose a specificity tie. 🚫 It also declares NO `--dr-*` token: a QR is black
#: on white because scanners need luminance contrast, not because a palette says
#: so, which makes it the one sheet here that is deliberately un-themeable.
#:
#: ⚠️ AND ITS RULES ARE FUNCTIONAL RATHER THAN COSMETIC -- the mm size floor, the
#: media gates and `print-color-adjust` all decide whether a camera can READ the
#: code. The sheet's own header carries that warning for anybody who opens it
#: meaning to tidy up.
_QR_ASSETS = ("qr.css",)

#: THE ALIGNMENT LAYER (2026-08-29). `{.align-center}` / `{.align-right}` on any
#: block, plus `align=` on `!!! qr`. See `assets/align.css` and `docrender/qr.py`.
#:
#: 🔴 THE SIXTH GROUP, AND IT EXISTS FOR THE SAME REASON `_QR_ASSETS` DOES: the
#: sheet carries screen AND print rules as one feature, because an author who
#: centres a form's title means it centred in both media -- and a class that did
#: nothing on screen would be unverifiable before printing, which is the scar
#: `qr.py` already carries about print-only elements. So it cannot join
#: `_PRINT_ASSETS` without making that group's header a lie, and the rule quoted
#: one tuple up decides it: **a group is a claim about WHEN a sheet loads and WHY.**
#:
#: ⭐ ITS POSITION IS GENUINELY FREE, on the `_FLOW_ASSETS` precedent. `.align-*`
#: is matched by no other sheet in this engine, and the one selector it borrows
#: (`.dr-qr__svg`) takes a `margin-inline` that `qr.css` never declares -- so there
#: is no selector-and-property PAIR in either medium.
#:
#: ⚠️ AND IT IS THE FIRST SHEET HERE WHOSE FEATURE HAS TWO AUTHORING SPELLINGS,
#: which is a markup constraint rather than a choice: `attr_list` cannot decorate a
#: `!!!` directive, so a QR takes `align=` and everything else takes the class.
#: Both files say so, so neither reads as arbitrary.
_ALIGN_ASSETS = ("align.css",)


def hand_written_css() -> tuple[str, ...]:
    """Every HAND-WRITTEN stylesheet this engine ships, in load order.

    THE SINGLE SOURCE for docrender/tokenaudit's scan list. See the docstring.

    Conditional sheets are included deliberately: the audit reads from DISK and
    should report on every rule that exists, because a rule is something a
    person has to reason about whether or not this particular site links it.

    Generated sheets are NOT here -- they have no file on disk, and the audit
    builds them itself. ⚠️ Nor are UNREGISTERED tombstones: `print-scheme.css` is
    on disk, absent from every tuple, and correctly invisible to the audit.

    🔴 AND THAT LAST SENTENCE IS THE ONE THAT HID A REAL BUG FOR TWO DAYS. It is
    still true, and it is not the whole truth: an unregistered file is invisible
    here whether the omission was DELIBERATE or a MISTAKE. `print-chrome.css` was
    the mistake (registered 2026-08-21), and this function could not tell the
    difference because it only ever reads what IS in the tuples. **A derived list
    guards against a forgotten GROUP; nothing guarded against a forgotten FILE.**
    See `_PRINT_ASSETS` for the account and for the disk-vs-tuple check that
    would have caught it.

    🔴 EVERY GROUP IS WALKED. Adding a group and forgetting it here is precisely
    how the old hardcoded tuple in tokenaudit.py went stale within two hours.
    ⭐ THIS WARNING HAS NOW BEEN OBEYED THREE TIMES: it was written against a
    hypothetical fourth group, and `_FLOW_ASSETS` (08-19), `_QR_ASSETS` (08-21) and
    `_ALIGN_ASSETS` (08-29) each joined this walk in the same commit that created
    them, because whoever added them read this line first.

    🪦 THE GROUP COUNT IS NO LONGER WRITTEN IN THIS SENTENCE. It said "there are
    FIVE of them as of 2026-08-21" and had already been edited twice; `len()` of
    the concatenation is derivable and a number in prose is not. ⭐ Removing it
    ends the vector rather than resetting the timer -- the same move that killed
    the fleet count in brain-config, and the sixth group is what proved it needed
    making.

    ⭐ AND THE `.css` FILTER IS WHAT MAKES A SPLIT FREE. Files join these tuples in
    mixed pairs -- navtree contributed one sheet and one script -- and the sheet is
    picked up here while the script is correctly ignored, with no edit. That is the
    whole reason this is a function and not another tuple.

    ⚠️ AND THE PRINT SHEETS SHOW UP IN THE TOKEN AUDIT LOUDLY, which is correct and
    worth expecting rather than discovering: `line-height`, `margin`, `padding`
    and `font-size` are all in tokenaudit's `_METRIC_PROPS`, so every value
    print-type.css, print-space.css and print-callout.css set is a new row in the
    metrics section. `flow.css` does the same and more.
    🔴 THREE FAMILIES OF ROW WILL LOOK LIKE FINDINGS AND ARE NOT: qr.css's
    `width: 30mm` and print-identity.css's `40.5mm` / `8.46mm` / `4mm` carry NO
    token because a physical mark on a physical sheet is not a design vector;
    print-ink.css's `#000` is a hardcoded colour BY RULING (2026-08-29); and
    align.css's `margin-inline: auto` is a keyword, not a metric. Each sheet's
    header carries its own argument. **The audit flagging them is the audit
    working.**
    """
    return tuple(
        name
        for name in (
            _DATA_ASSETS + _FEATURE_ASSETS + _PRINT_ASSETS + _FLOW_ASSETS
            + _QR_ASSETS + _ALIGN_ASSETS
        )
        if name.endswith(".css")
    )


def _uses_router(config) -> bool:
    """Does this site have a router anywhere? Answerable at on_config time.

    Cached in state because both events ask, and the answer must not differ
    between them -- a link with no file, or a file with no link, are both worse
    than either problem alone.
    """
    cached = state.REPORT.get("_router")
    if cached is not None:
        return bool(cached)

    found = bool(load_yaml(Path(state.INSTANCE.get("dir", ".")) / "routes.yml"))

    if not found:
        # A page can carry its own codes with no entry in routes.yml, so the
        # route table alone is not enough to answer this.
        docs = Path(str(config.docs_dir))
        if docs.is_dir():
            for path in docs.rglob("*.md"):
                try:
                    head = path.read_text(encoding="utf-8")[:2000]
                except (OSError, UnicodeDecodeError):
                    continue
                if any(key in head for key in _ROUTER_KEYS):
                    found = True
                    break

    state.REPORT["_router"] = found
    return found


def _fingerprint(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()[:8]


def _stamped(name: str, raw: bytes) -> str:
    """`base.css` + bytes -> `assets/base.a41f7c92.css`."""
    stem, _, suffix = name.rpartition(".")
    return "assets/" + stem + "." + _fingerprint(raw) + "." + suffix


def _read(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except OSError:
        return None


def _plan(config) -> list[tuple[str, bytes]]:
    """Every asset this build publishes, in load order, with its bytes.

    Built by both events -- `on_config` needs the URLs, `on_files` needs the
    content -- and they must never disagree. Order: base, the chrome, nav, type
    and foot layers, the data-table layers (see `_DATA_ASSETS`), then the
    generated sheets, THEN the print layers, then the flow, qr and align layers,
    then any feature sheet, then the instance sheet LAST so a site always has the
    final word on its own look.

    THE THREE GENERATED SHEETS ARE ORDERED BY WHAT THEY CONSUME:

        tokens.css   says what a colour IS
        marks.css    says which inline MARKER family uses it
        blocks.css   says which CALLOUT family uses it

    Both consumers come after the tokens, and they are separate files because
    they answer separate questions. blocks.css additionally has to beat
    Material's own admonition flavour rules, which it does on source order at
    equal specificity -- see docrender/blocks.py for that whole argument.

    ⚠️ AND THE PRINT LAYERS COME AFTER ALL THREE FOR THE SAME CLASS OF REASON:
    they override Material rules and scheme-scoped properties the generated
    sheets also write, at equal specificity. See `_PRINT_ASSETS`.

    ⭐ THE PAPER PALETTE IS THE EXCEPTION AND IS NOT IN THAT GROUP -- theme.py
    emits it INSIDE `tokens.css`, after the scheme block it corrects. An
    intra-file order is deterministic where a cross-sheet tie is not.

    ⚠️ AND THE FEATURE GROUP IS WALKED IN ITS OWN DECLARED ORDER, which is the
    only thing keeping navtree.js ahead of router.js. See `_FEATURE_ASSETS`.

    ⭐ THE FLOW, QR AND ALIGN LAYERS' POSITIONS ARE FREE and are documented as such
    on their own tuples -- none shares a selector-and-property pair with anything.
    Do not infer a rule from where they sit.

    ⚠️ AND `_read` RETURNING None IS WHY A MISSING FILE IS SILENT HERE. That is
    the correct behaviour for a sheet somebody deleted on purpose, and it is also
    why an UNREGISTERED sheet was undetectable: this loop can only skip what it
    was asked for. See `_PRINT_ASSETS` (2026-08-21).
    """
    plan: list[tuple[str, bytes]] = []

    for name in _DATA_ASSETS:
        raw = _read(state.ENGINE_ROOT / "assets" / name)
        if raw is not None:
            plan.append((name, raw))

    plan.append(("tokens.css", theme.build_css().encode("utf-8")))
    plan.append(("marks.css", markers.build_css().encode("utf-8")))
    plan.append(("blocks.css", blocks.build_css().encode("utf-8")))

    for name in _PRINT_ASSETS:
        raw = _read(state.ENGINE_ROOT / "assets" / name)
        if raw is not None:
            plan.append((name, raw))

    for name in _FLOW_ASSETS + _QR_ASSETS + _ALIGN_ASSETS:
        raw = _read(state.ENGINE_ROOT / "assets" / name)
        if raw is not None:
            plan.append((name, raw))

    if _uses_router(config):
        for name in _FEATURE_ASSETS:
            raw = _read(state.ENGINE_ROOT / "assets" / name)
            if raw is not None:
                plan.append((name, raw))

    site_css = _read(Path(state.INSTANCE.get("dir", ".")) / "theme.css")
    if site_css is not None:
        plan.append(("site.css", site_css))

    return plan


def on_config(config):
    for name, raw in _plan(config):
        url = _stamped(name, raw)
        target = config.extra_javascript if name.endswith(".js") else config.extra_css
        if url not in target:
            target.append(url)
    return config


def on_files(files, config):
    for name, raw in _plan(config):
        files.append(File.generated(config, _stamped(name, raw), content=raw))
    return files
