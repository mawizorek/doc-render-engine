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

⚠️ AND `print.css` IS UNCONDITIONAL FOR THE SIMPLEST REASON OF THE THREE
(2026-08-06): there is no question to ask. Every page can be printed, so a
usage check would have no input and no answer. It is ~9KB of rules behind an
`@media print` gate that costs a screen reader nothing.

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

⚠️ THAT IS WHY `_PRINT_ASSETS` IS A CONSTANT AND NOT A LITERAL IN `_plan()`.
It is a third group only because of WHERE it loads (see below), not because it
is a different kind of thing -- and `hand_written_css()` derives from all three
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
#: 🔴 navtree.js COMES BEFORE router.js, AND THAT IS AN ORDERING LAW OF THE SAME
#: CLASS AS `_DATA_ASSETS` ABOVE -- not alphabetising, not tidiness.
#: assets/navtree.js was split out of router.js on 2026-08-16 at 22,232 B, past
#: the engine's 22KB hard read limit, along the seam router.js had already
#: declared in its own header: the FORM and its crypto stay there, everything
#: that DRAWS the sealed sidebar moved here.
#:
#: router.js calls into `window.docrenderNavTree` during its own IIFE, so a
#: later position makes every one of those calls a TypeError on the first paint.
#: ⚠️ AND THE FAILURE IS THE QUIET SHAPE: the form keeps unlocking pages
#: perfectly while the revealed menu silently stops being injected, which is
#: exactly the class of defect that survives longest here. router.js guards the
#: reference so a MISSING navtree.js degrades the same safe way rather than
#: killing the unlock -- but a mis-ORDERED one is still a dead sidebar, and no
#: guard can fix an order.
_FEATURE_ASSETS = ("router.css", "navtree.js", "router.js")

#: 🔴 LOADS AFTER THE GENERATED SHEETS, AND THAT IS THE ONLY REASON IT IS A
#: SEPARATE GROUP RATHER THAN THE EIGHTH ENTRY IN `_DATA_ASSETS`.
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
_PRINT_ASSETS = ("print.css",)


def hand_written_css() -> tuple[str, ...]:
    """Every HAND-WRITTEN stylesheet this engine ships, in load order.

    THE SINGLE SOURCE for docrender/tokenaudit's scan list. See the docstring.

    Conditional sheets are included deliberately: the audit reads from DISK and
    should report on every rule that exists, because a rule is something a
    person has to reason about whether or not this particular site links it.

    Generated sheets are NOT here -- they have no file on disk, and the audit
    builds them itself.

    ⚠️ ALL THREE GROUPS ARE WALKED. Adding a fourth group and forgetting it
    here is precisely how the old hardcoded tuple in tokenaudit.py went stale
    within two hours.

    ⭐ AND THE `.css` FILTER IS WHAT MADE A GROUP GAINING A SCRIPT FREE.
    `navtree.js` joined `_FEATURE_ASSETS` on 2026-08-16 and needed no edit
    here, because this DERIVES from the groups instead of restating them. That
    is the whole reason it is a function and not a fourth tuple.
    """
    return tuple(
        name
        for name in _DATA_ASSETS + _FEATURE_ASSETS + _PRINT_ASSETS
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
    sheets, THEN the print layer, then any feature sheet, then the instance
    sheet LAST so a site always has the final word on its own look.

    THE THREE GENERATED SHEETS ARE ORDERED BY WHAT THEY CONSUME:

        tokens.css   says what a colour IS
        marks.css    says which inline MARKER family uses it
        blocks.css   says which CALLOUT family uses it

    Both consumers come after the tokens, and they are separate files because
    they answer separate questions. blocks.css additionally has to beat
    Material's own admonition flavour rules, which it does on source order at
    equal specificity -- see docrender/blocks.py for that whole argument.

    ⚠️ AND THE PRINT LAYER COMES AFTER ALL THREE FOR THE SAME CLASS OF REASON.
    It overrides scheme-scoped custom properties that tokens.css also writes,
    at equal specificity, so it wins on source order or it does not win at all.
    See `_PRINT_ASSETS`.

    ⚠️ AND THE FEATURE GROUP IS WALKED IN ITS OWN DECLARED ORDER, which is the
    only thing keeping navtree.js ahead of router.js. See `_FEATURE_ASSETS`.
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
