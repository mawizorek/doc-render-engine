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

⭐ IT HAS SILENTLY ABSORBED FIVE NEW SHEETS SINCE 2026-08-16 -- navtree, then
print-flow, print-type, print-callout and print-space -- with no edit to
tokenaudit.py in any of them. 🪦 FOUR PARAGRAPHS OF INDIVIDUAL PAYOFF ANECDOTES
WERE TRIMMED TO THAT ONE SENTENCE ON 2026-08-19, to buy the bytes to register the
fifth. **Four stories proving one rule is three stories too many, and the file
being out of room to describe its own contents is the loudest possible argument
for the trim.** Same call as print-type.css §6, one evening apart.

🔴 AND THE WARNING IN `hand_written_css()` FIRED FOR REAL ON 2026-08-19, which is
better evidence than any of those anecdotes were. It said "adding a fourth group
and forgetting it here is precisely how the old hardcoded tuple went stale" --
written before any fourth group existed. `_FLOW_ASSETS` became the fourth, the
line was read, and the group joined the walk in the SAME commit.

⚠️ THAT IS ALSO WHY `_PRINT_ASSETS` IS A CONSTANT AND NOT A LITERAL IN `_plan()`.
It is a separate group only because of WHERE it loads (see below), not because it
is a different kind of thing -- and `hand_written_css()` derives from all four
groups so the audit cannot go stale the way it did in 2026-08-04.
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
#: print.css re-points custom properties on `[data-md-color-scheme="slate"]`
#: so that a reader in dark mode gets black ink on white paper. That is the
#: SAME selector `tokens.css` writes, at the SAME specificity -- so the winner
#: is decided purely by source order. Put this in `_DATA_ASSETS` and the
#: generated sheet lands later and wins, the overrides die, and a dark-mode
#: print comes out as pale grey ink on a background the browser drops. No
#: error, no report, just a near-blank sheet.
#:
#: It still loads BEFORE the instance's `site.css`, because a site keeps the
#: final word on its own look and paper is no exception.
#:
#: FIVE FILES, FIVE JOBS, and each one answers exactly one question:
#:
#:   print.css          WHAT THE SHEET IS   -- @page, chrome off, the column
#:                                             unrailing, the slate->light
#:                                             neutrals, print-color-adjust,
#:                                             code wrapping, link policy
#:   print-flow.css     WHERE IT BREAKS     -- break-*, orphans/widows, h1-h6,
#:                                             tab labels, forced-open
#:                                             <details>, thead repetition,
#:                                             {.new-page}
#:   print-type.css     HOW BIG THE TYPE IS -- the dial, the ramp, weight,
#:                                             tracking, link decoration
#:   print-space.css    HOW MUCH AIR IS     -- block margins, list margins,
#:                      BETWEEN THINGS         justification's word spaces
#:   print-callout.css  WHAT THE BOX IS     -- the callout/details box: the rule
#:                                             and indent, the icon, the
#:                                             font-size anchor
#:
#: ⭐ EVERY ONE OF THESE SPLITS WAS FORCED BY THE SAME 22KB CEILING, and each seam
#: was already written in the header of the file that split -- the measured
#: argument lives in the header of the file that RECEIVED the rules rather than
#: being copied here. **A FILE AT ITS SIZE LIMIT IS USUALLY A FILE WITH A SEAM IN
#: IT; trimming prose is what you do instead of finding the seam.**
#:
#: ✅ AND print-space.css IS THE FIRST ONE TAKEN ON A FORECAST RATHER THAN A
#: COLLISION (2026-08-19). print.css and print-type.css both split after a write
#: had already bounced off the limit; print-type.css was reported to Michael at
#: 21,703 B with 825 B of headroom and he asked for the split before anything
#: failed. That is what the size budget in hooks/08_sizecheck.py exists to buy and
#: had never once been spent on.
#:
#: ⭐ AND THE ORDER *WITHIN* THIS GROUP IS GENUINELY FREE, stated out loud on the
#: `_FEATURE_ASSETS` precedent above so nobody later defends a position that was
#: never load-bearing. No two of these five share a selector-and-property PAIR --
#: `.md-typeset h1` is written in both print-type.css and print-space.css, but one
#: sets size and weight while the other sets margins, and a cascade fight needs
#: both halves to match. What is load-bearing is the GROUP's position.
#:
#: ⚠️ IF THAT EVER STOPS BEING TRUE, THIS COMMENT IS THE THING THAT ROTS. Three
#: likely ways now: print-type.css growing a `margin` on a heading it already
#: sizes (print-space.css's header names this as the most likely of the three);
#: print-type.css or print-space.css growing a rule print.css also sets; or
#: print-callout.css and print-flow.css both reaching for `<details>` -- flow owns
#: whether it is OPEN, callout owns what it LOOKS LIKE.
_PRINT_ASSETS = (
    "print.css",
    "print-flow.css",
    "print-type.css",
    "print-space.css",
    "print-callout.css",
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


def hand_written_css() -> tuple[str, ...]:
    """Every HAND-WRITTEN stylesheet this engine ships, in load order.

    THE SINGLE SOURCE for docrender/tokenaudit's scan list. See the docstring.

    Conditional sheets are included deliberately: the audit reads from DISK and
    should report on every rule that exists, because a rule is something a
    person has to reason about whether or not this particular site links it.

    Generated sheets are NOT here -- they have no file on disk, and the audit
    builds them itself.

    ⚠️ ALL FOUR GROUPS ARE WALKED. Adding a fifth group and forgetting it here is
    precisely how the old hardcoded tuple in tokenaudit.py went stale within two
    hours. 🔴 That warning was aimed at a hypothetical fourth group, a fourth
    group arrived on 2026-08-19, and it joined this walk in the same commit
    because this line was read first -- so the count in that sentence is the one
    part of this function that can rot.

    ⭐ AND THE `.css` FILTER IS WHAT MAKES A SPLIT FREE. Files join these tuples in
    mixed pairs -- navtree contributed one sheet and one script -- and the sheet is
    picked up here while the script is correctly ignored, with no edit. That is the
    whole reason this is a function and not a fifth tuple.

    ⚠️ AND THE PRINT SHEETS SHOW UP IN THE TOKEN AUDIT LOUDLY, which is correct and
    worth expecting rather than discovering: `line-height`, `margin`, `padding`
    and `font-size` are all in tokenaudit's `_METRIC_PROPS`, so every value
    print-type.css, print-space.css and print-callout.css set is a new row in the
    metrics section. `flow.css` does the same and more.
    """
    return tuple(
        name
        for name in _DATA_ASSETS + _FEATURE_ASSETS + _PRINT_ASSETS + _FLOW_ASSETS
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
    content -- and they must never disagree. Order: base, the chrome, nav and
    type layers, the data-table layers (see `_DATA_ASSETS`), then the generated
    sheets, THEN the print layers, then the flow layer, then any feature sheet,
    then the instance sheet LAST so a site always has the final word on its own
    look.

    THE THREE GENERATED SHEETS ARE ORDERED BY WHAT THEY CONSUME:

        tokens.css   says what a colour IS
        marks.css    says which inline MARKER family uses it
        blocks.css   says which CALLOUT family uses it

    Both consumers come after the tokens, and they are separate files because
    they answer separate questions. blocks.css additionally has to beat
    Material's own admonition flavour rules, which it does on source order at
    equal specificity -- see docrender/blocks.py for that whole argument.

    ⚠️ AND THE PRINT LAYERS COME AFTER ALL THREE FOR THE SAME CLASS OF REASON.
    print.css overrides scheme-scoped custom properties that tokens.css also
    writes, at equal specificity, so it wins on source order or it does not win
    at all. See `_PRINT_ASSETS`.

    ⚠️ AND THE FEATURE GROUP IS WALKED IN ITS OWN DECLARED ORDER, which is the
    only thing keeping navtree.js ahead of router.js. See `_FEATURE_ASSETS`.

    ⭐ THE FLOW LAYER'S POSITION IS FREE and is documented as such on
    `_FLOW_ASSETS` -- it shares no selector with anything. Do not infer a rule
    from where it sits.
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

    for name in _FLOW_ASSETS:
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
