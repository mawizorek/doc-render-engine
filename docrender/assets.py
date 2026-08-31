"""Hook 05 -- serve stylesheets and scripts that live OUTSIDE the content tree.

MkDocs resolves `extra_css` relative to `docs_dir`, so read literally the assets
must live inside the doc tree. They do not: `on_files` accepts File objects whose
source is anywhere, and that is what makes the content-purity rule possible.
🚫 Do not "fix" this by moving the CSS back where it looks like it belongs.

📚 HISTORY AND ARGUMENTS: docrender/assets-dl.md -- the on_config outage that
killed the router (D2), why each group is unconditional (D3), the fingerprint
(D4), the four dead manifests behind `hand_written_css` (D5), the print-chrome.css
omission (D6), the print group's eight jobs (D7), which positions are free (D8),
the two proven collisions (D9).

⭐ EXTRACTED 2026-08-30 (32,684 B -> this). The mechanism was always ~90 lines.
🔴 THE LOAD-ORDER LAWS DID NOT GO WITH IT, and that is deliberate: a guardrail
belongs where the hand is about to act, and this repo has five recorded instances
of a rule that was correct in isolation and unreachable in place. Every comment
below that says MUST is one of those laws. Everything else is in the sidecar.

⚠️ EVERY ASSET URL CARRIES A CONTENT FINGERPRINT -- `assets/base.a41f7c92.css`.
The URL changes when the bytes change, which is what makes "I published and do
not see my change" impossible for assets. See D4.

⚠️ STILL MISSING, and the split does not fix it: nothing compares assets/*.css ON
DISK against the tuples below. Until it exists, REGISTER A NEW SHEET IN THE SAME
PR AS THE SHEET ITSELF. See D6 for the two days that rule cost.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from mkdocs.structure.files import File

from . import blocks, markers, state, theme
from .util import load_yaml

_ROUTER_KEYS = ("router:", "router_code:")

#: 🔴 LOAD ORDER IS A LAW HERE, NOT ALPHABETISING. Reorder these and list mode
#: loses to the table it is meant to replace.
#:
#:   base.css       the Material mapping everything else builds on
#:   chrome.css     🔴 THE ARMOUR is a specificity TIE with Material's compound
#:                  primary rule, won purely on SOURCE ORDER. Move this before
#:                  base.css and every dark-mode link reverts to Material's
#:                  indigo -- a live bug, not a wobble.
#:   nav.css        MUST land AFTER the base mapping: it OVERRIDES Material's
#:                  drawer borders. Earlier and the phones-only double rule comes
#:                  back -- invisible at desktop width, found from a screenshot.
#:   type.css       overrides Material's heading rules, so also after base.
#:   foot.css       .pagefoot, footer chrome, the build stamp. Position free, but
#:                  must follow base.css, which maps --md-footer-*.
#:   data.css       the table layer, split out of base.css
#:   data-list.css  MUST follow data.css: it overrides those rules inside a
#:                  container query.
#:   data.js        drives both table layers
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
#: Four files, two halves, split 2026-08-16 when both router files hit the 22KB
#: read limit: router.css + router.js are THE FORM (curtain, crypto, only where a
#: router is declared); navtree.css + navtree.js are THE SEALED SIDEBAR.
#:
#: 🔴 navtree.js MUST COME BEFORE router.js. router.js calls into
#: `window.docrenderNavTree` during its own IIFE, so a later position makes every
#: one of those calls a TypeError on the first paint. ⚠️ AND THE FAILURE IS THE
#: QUIET SHAPE: the form keeps unlocking pages perfectly while the revealed menu
#: silently stops being injected. router.js guards the reference, so a MISSING
#: navtree.js degrades safely -- but a mis-ORDERED one is a dead sidebar, and no
#: guard can fix an order.
#:
#: ⭐ THE CSS ORDER IS GENUINELY FREE. See D8 -- do not defend a position that was
#: never load-bearing.
_FEATURE_ASSETS = ("router.css", "navtree.css", "navtree.js", "router.js")

#: 🔴 THIS GROUP MUST LOAD AFTER THE GENERATED SHEETS, and that is the only reason
#: it is a separate group rather than more entries in `_DATA_ASSETS`. These sheets
#: override Material rules and scheme-scoped properties that tokens.css and
#: blocks.css also write, AT EQUAL SPECIFICITY -- so they win on source order or
#: not at all. Put them in `_DATA_ASSETS` and paper comes out wrong with no error
#: and no report. It still loads BEFORE the instance's site.css: a site keeps the
#: final word on its own look, and paper is no exception.
#:
#: 🪦 `print-scheme.css` IS UNREGISTERED ON PURPOSE -- a comment-only tombstone;
#: theme.py emits the paper palette inside tokens.css. ⚠️ A file in assets/ absent
#: from these tuples is never published and does nothing. 🔴 That sentence came
#: true BY ACCIDENT once and cost every printed page for two days -- and the
#: tombstone is what made it invisible, because a deliberate absence and a mistake
#: look identical in a list of what IS present. See D6.
#:
#: ⭐ NINE FILES, NINE JOBS, one question each -- the table is D7. The ORDER
#: WITHIN this group is free (no two share a selector-and-property pair) with two
#: proven exceptions, both in D9. What is load-bearing is the GROUP's position.
#:
#: ⚠️ `print-md-bridge.css` JOINED 2026-08-31 AND IT IS THE ONE MEMBER THAT
#: DECLARES A `--md-*` CUSTOM PROPERTY rather than consuming a `--dr-*` one. It
#: re-points five of Material's own variables at our tokens, UNSCOPED, because
#: base.css does that mapping ONLY under a `[data-md-color-scheme]` attribute --
#: and a headless print carries no attribute, so Material painted its own dark
#: values straight over a correct light palette. 🔴 Its position within the group is
#: FREE (nothing else declares those names) but its MEMBERSHIP is not decorative:
#: it has to land after base.css, and every group here does.
#:
#: ⚠️ BUILD 10's `print-packet.css` IS DELIBERATELY NOT HERE. It is @media print
#: and it would look like a tenth member of this group, but it shares no selector
#: with any sheet at all, so it has no cascade fight to win and this group's claim
#: does not describe it. See `_PACKET_ASSETS`.
_PRINT_ASSETS = (
    "print.css",
    "print-chrome.css",
    "print-flow.css",
    "print-type.css",
    "print-space.css",
    "print-callout.css",
    "print-identity.css",
    "print-ink.css",
    "print-md-bridge.css",
)

#: THE FLOW STRIP, THE EMBEDDED FORM AND THE VIEW EMBED. See docrender/program.py,
#: forms.py and views.py. Position FREE (D8): every selector is a .dr-flow* /
#: .dr-form* / .dr-view* class no other sheet mentions.
#:
#: 🔴 EVERY TOKEN IN THIS SHEET IS USED WITH A MATERIAL VARIABLE AS ITS FALLBACK,
#: which is not decoration: tokens are generated per site, so a token that exists
#: on `eos` may be absent on a nine-token local skin -- the failure that left
#: eleven callout families painting `currentColor` on 2026-08-05. Material's own
#: variable makes the worst case Material's look rather than an invisible control,
#: and an invisible control is what this sheet exists to prevent.
_FLOW_ASSETS = ("flow.css",)

#: THE QR LAYER (BUILD 6 step 5). See docrender/qr.py and specs/qr-codes.md.
#: Position FREE (D8). 🚫 Declares NO --dr-* token: a QR is black on white because
#: scanners need luminance contrast, not because a palette says so.
#:
#: ⚠️ ITS RULES ARE FUNCTIONAL, NOT COSMETIC -- the mm size floor, the media gates
#: and print-color-adjust all decide whether a camera can READ the code. The
#: sheet's own header carries that warning for anybody meaning to tidy up.
_QR_ASSETS = ("qr.css",)

#: THE ALIGNMENT LAYER. `{.align-center}` / `{.align-right}` on any block, plus
#: `align=` on `!!! qr`, `!!! form` and `!!! view`. Position FREE (D8).
#:
#: ⚠️ TWO AUTHORING SPELLINGS, which is a markup constraint rather than a choice:
#: attr_list cannot decorate a `!!!` directive, so a directive takes `align=` and
#: everything else takes the class. Both files say so, so neither reads as
#: arbitrary.
_ALIGN_ASSETS = ("align.css",)

#: THE ROLE GLOSS (BUILD 9, 2026-08-30). The hover box on a marker LINK and the
#: parenthesis it becomes on paper. See docrender/markerlinks.py, objects/role.yml
#: and specs/hover-text.md.
#:
#: 🔴 ITS OWN GROUP RATHER THAN A `_PRINT_ASSETS` MEMBER, on the `_QR_ASSETS` and
#: `_ALIGN_ASSETS` precedent: the sheet carries SCREEN and PRINT rules as one
#: feature, and that group is entirely `@media print` and loads where it does for a
#: cascade reason. **A group is a claim about WHEN a sheet loads and WHY. Adding a
#: member that breaks the claim is worse than adding a group.**
#:
#: ⭐ AND IT IS ONE FEATURE RATHER THAN TWO, WHICH IS THE POINT OF THE SHEET: the
#: SAME `::after` is the hover box on screen and the printed parenthesis on paper,
#: reading a different attribute in each medium. Splitting the two halves across
#: two sheets would put one element's two states in two files.
#:
#: ⚠️ UNCONDITIONAL, FOR THE DATA-TABLE REASON AND NOT THE PRINT ONE (D3). `@role:`
#: is an inline reference in a page BODY, so the router's frontmatter-scan trick
#: cannot see it and there is no cheap question to ask. The cost of being wrong is
#: also low: these are `.dr-gloss` / `[data-role-print]` rules that match nothing
#: at all on a site with no roles.
#:
#: ⭐ POSITION FREE, said out loud so nobody later defends it. The only selector it
#: shares with any other sheet is `.md-typeset a`, and it sets `position` there
#: while nothing else does -- so there is no selector-and-property PAIR in either
#: medium. Its print half needs no group position either: every declaration in it
#: carries `!important`, because print-flow.css's `display: revert !important` has
#: already beaten a plain rule twice in this feature family.
_GLOSS_ASSETS = ("gloss.css",)

#: THE PROGRAM PACKET (BUILD 10, 2026-08-30). The export button on screen; the
#: one rule that keeps it off paper. See docrender/packet.py and
#: specs/print-packet.md.
#:
#: ⭐ TWO FILES IN ONE GROUP, ON THE `_GLOSS_ASSETS` REASONING APPLIED HONESTLY.
#: gloss.css kept screen and print in ONE sheet because one `::after` served both
#: mediums, so splitting would have put one element's two states in two files.
#: Here the two halves share no element. Two files, one group -- the group is the
#: feature, the file split follows the medium.
#:
#: 🔴 `print-packet.css` IS NOT IN `_PRINT_ASSETS` AND THAT IS A DECISION. That
#: group's claim is "must beat the generated sheets at equal specificity." Its one
#: rule shares no selector with any other sheet, so the claim is false about it,
#: and a member that breaks its group's claim is worse than a new group. ✅ It still
#: lands AFTER the print group, because this group is appended after it in `_plan`
#: -- which is what keeps it clear of print-flow.css, the only sheet that has ever
#: contested a rule in this feature family.
#:
#: ⚠️ UNCONDITIONAL, like every group but the router's (D3). `export:` is
#: frontmatter, so a scan COULD answer "does this site have a packet" cheaply --
#: and the cost of being wrong is a couple of `.dr-packet*` rules that match
#: nothing, against the cost of a second place stating which sites use the
#: feature. The router's scan exists because its assets are 63 KB; these are 6.
_PACKET_ASSETS = ("packet.css", "print-packet.css")

#: THE TASK-LIST CHECKBOX (2026-08-30). `- [ ]` / `- [x]` on a worksheet page.
#: See `mkdocs.yml` -> pymdownx.tasklist for the WORKSHEET/RECORD rule that
#: governs where an author may use one. Position FREE (D8): the only selectors
#: are `.task-list-*` and the two `--md-tasklist-icon*` variables, and no other
#: sheet in the tree mentions either (grepped).
#:
#: 🔴 IT EXISTS BECAUSE MATERIAL'S OWN DEFAULTS ARE UNUSABLE ON THESE THEMES, and
#: both defects were read out of `_tasklist.scss` at the pinned version rather
#: than guessed. (1) The unchecked indicator paints
#: `--md-default-fg-color--lightest` = `#00000012`, **7% opacity**, measured at
#: **1.17:1** on the papyrus light row against a 3.0 UI floor -- invisible, which
#: is exactly how Michael reported it. (2) `--md-tasklist-icon` and
#: `--md-tasklist-icon--checked` are **THE SAME GLYPH**, so state is carried by
#: COLOUR ALONE -- `$clr-green-a400` measures 1.35:1 on that same row, and the
#: distinction dies outright on a greyscale printer.
#:
#: ⭐ (2) IS THE ONE THAT MATTERED. This engine's whole reason for a clickable
#: checkbox is Michael's worksheet: *"whatever isn't checked off is what I need to
#: order."* A printed sheet whose two states differ only in hue cannot express
#: that -- and `base.css` had already written the general rule for `docrender-dead`
#: (*"unclickable is not a cue, it is the ABSENCE of one"*). Same law, second
#: element.
#:
#: ⚠️ UNCONDITIONAL, like every group but the router's (D3). A task list is body
#: markup, so no frontmatter scan can see it, and the cost of being wrong is a few
#: `.task-list-*` rules matching nothing.
_TASKLIST_ASSETS = ("tasklist.css",)


def hand_written_css() -> tuple[str, ...]:
    """Every HAND-WRITTEN stylesheet this engine ships, in load order.

    THE SINGLE SOURCE for docrender/tokenaudit's scan list, which used to keep its
    own hardcoded tuple and went stale WITHIN TWO HOURS. See D5.

    Conditional sheets are included deliberately: the audit reads from DISK and
    should report on every rule that exists, because a rule is something a person
    has to reason about whether or not this particular site links it. Generated
    sheets are NOT here -- they have no file on disk and the audit builds them.

    🔴 EVERY GROUP IS WALKED. Adding a group and forgetting it here is precisely
    how that tuple went stale. ⭐ THIS WARNING HAS BEEN OBEYED SIX TIMES --
    _FLOW_ASSETS (08-19), _QR_ASSETS (08-21), _ALIGN_ASSETS (08-29),
    _GLOSS_ASSETS, _PACKET_ASSETS and _TASKLIST_ASSETS (all 08-30) each joined
    this walk in the same commit that created them, because whoever added them
    read this line first. ⚠️ The number is safe to write ONLY because the list
    beside it is exhaustive: a bare count here would rot the way every
    hand-maintained total in this repo has. ⭐ `print-md-bridge.css` (08-31) needed
    no edit here at all -- it joined an EXISTING group, which is the payoff for
    walking groups rather than filenames.

    ⚠️ It guards against a forgotten GROUP. Nothing guards against a forgotten
    FILE, and an unregistered sheet is invisible here whether the omission was
    deliberate or a mistake -- which hid a real bug for two days. See D6.

    ⭐ THE `.css` FILTER IS WHAT MAKES A SPLIT FREE: files join these tuples in
    mixed pairs, and a script is correctly ignored with no edit. That is why this
    is a function and not another tuple.

    ⚠️ Expect the print sheets to fill the token audit's metrics section, and
    expect three families of row that look like findings and are not. See D11.
    🔴 gloss.css adds a fourth: its `min(32ch, 80vw)`, its `em` type sizes and its
    `rgb(0 0 0 / 22%)` shadow carry no token, because a tooltip's measure is a
    function of its own text rather than a design vector. The sheet's header says
    so where somebody would go looking.
    """
    return tuple(
        name
        for name in (
            _DATA_ASSETS + _FEATURE_ASSETS + _PRINT_ASSETS + _FLOW_ASSETS
            + _QR_ASSETS + _ALIGN_ASSETS + _GLOSS_ASSETS + _PACKET_ASSETS
            + _TASKLIST_ASSETS
        )
        if name.endswith(".css")
    )


def _uses_router(config) -> bool:
    """Does this site have a router anywhere? Answerable at on_config time.

    🔴 THE WHOLE POINT IS THE "answerable" -- state.BY_SRC is EMPTY at on_config,
    so the obvious version of this check answered False on every build and the
    router shipped published-but-unlinked. Never reintroduce a page-map read here.
    Full account: D2.

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
    """`base.css` + bytes -> `assets/base.a41f7c92.css`. See D4."""
    stem, _, suffix = name.rpartition(".")
    return "assets/" + stem + "." + _fingerprint(raw) + "." + suffix


def _read(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except OSError:
        return None


def _plan(config) -> list[tuple[str, bytes]]:
    """Every asset this build publishes, in load order, with its bytes.

    🔴 BUILT BY BOTH EVENTS -- on_config needs the URLs, on_files needs the
    content -- AND THEY MUST NEVER DISAGREE. That is why the plan is one function
    rather than two lists.

    THE THREE GENERATED SHEETS ARE ORDERED BY WHAT THEY CONSUME:

        tokens.css   says what a colour IS
        marks.css    says which inline MARKER family uses it
        blocks.css   says which CALLOUT family uses it

    Both consumers come after the tokens. blocks.css additionally has to beat
    Material's own admonition flavour rules, which it does on source order at
    equal specificity -- see docrender/blocks.py for that argument.

    ⚠️ THE PRINT LAYERS COME AFTER ALL THREE for the same class of reason: equal
    specificity, so source order decides. See `_PRINT_ASSETS`.

    ⭐ THE PAPER PALETTE IS THE EXCEPTION and is not in that group -- theme.py
    emits it INSIDE tokens.css, after the scheme block it corrects. An intra-file
    order is deterministic where a cross-sheet tie is not. ⚠️ AND IT IS ONLY HALF
    THE PAPER STORY: that block sets `--dr-*`, and Material paints from `--md-*`.
    `print-md-bridge.css` is the other half -- see its header.

    ⚠️ THE FEATURE GROUP IS WALKED IN ITS OWN DECLARED ORDER, which is the only
    thing keeping navtree.js ahead of router.js.

    ⭐ THE FLOW, QR, ALIGN, GLOSS, PACKET AND TASKLIST POSITIONS ARE FREE (D8). Do
    not infer a rule from where they sit. ⚠️ ONE EXCEPTION, AND IT IS NOT A CASCADE
    RULE: the packet group must stay AFTER `_PRINT_ASSETS` in this list, because
    print-packet.css's `display: none` on the export button competes with
    print-flow.css's `display: revert !important` on details children. It also
    carries `!important` itself, so the order is belt AND braces rather than the
    only defence.

    ⚠️ `_read` RETURNING None IS WHY A MISSING FILE IS SILENT HERE -- correct for a
    sheet deleted on purpose, and also why an UNREGISTERED sheet was undetectable:
    this loop can only skip what it was asked for. See D6, D10.
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

    for name in (_FLOW_ASSETS + _QR_ASSETS + _ALIGN_ASSETS + _GLOSS_ASSETS
                 + _PACKET_ASSETS + _TASKLIST_ASSETS):
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
