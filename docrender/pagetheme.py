"""Stage 06b (third claimant) -- a page's own `theme:`, honoured.

    ---
    theme: papyrus                        # one theme, both toggle states
    theme: {dark: sharp-mclaren, light: papyrus}   # or name each slot
    ---

Same grammar as `site.yml`'s `theme:`, resolved by the SAME code. The rules are
maw-themes `docs/HOW-A-THEME-IS-CHOSEN.md`; nothing here restates them.

=============================================================================
⭐ HOW: THE SITE'S OWN EMITTER, RUN ONCE MORE, INLINED ON THE PAGE THAT ASKED
=============================================================================
For the length of one call the instance's theme declaration is swapped for the
page's, `theme.build_css()` runs, and the declaration is put back. The string it
returns goes into a `<style>` at the end of that page's `<head>`.

Why this and not specs/scoped-theme.md §4 (scoped selectors in the shared
sheet), which was the priced plan:

  1. ZERO SECOND CLAIMANTS. Every ordering law theme.py documents (local base,
     canonical row, aliases LAST, the bridge, the paper block and its unscoped
     :root copy) is reused byte-for-byte because it IS the same function. §4
     needed a second emitter walking the same laws under new selectors.
  2. NO SPECIFICITY ESCALATION, SO §4c CANNOT FIRE. The inline sheet uses the
     site's own selectors at the site's own specificity and wins on SOURCE ORDER
     alone: it is the last sheet on the page. Inside it the paper block still
     follows the screen blocks, so paper still beats screen. §4c's near-blank
     dark-mode print was a two-attribute selector outranking the paper block;
     nothing here is two-attribute.
  3. `:root`-RESOLVED BRIDGES FOLLOW FOR FREE. base.css maps `--md-text-font`
     and print-md-bridge.css maps five `--md-*` colours on `:root`. Those
     resolve against `:root`'s `--dr-*`, which this sheet overrides, so a page
     theme changes the FONT and a headless print too, not just the swatches. A
     body-scoped design would have left both on the site theme.
  4. THE PAGE THAT ASKS IS THE ONLY PAGE THAT PAYS. chrome.py's argument.

🔴 COSTS, STATED:
  * A themed page also beats the instance's `theme.css`, because it loads last.
    A page that names a theme has made a more specific choice than the site.
  * A few KB of inline CSS per themed page, uncached across pages. Fine at a
    handful. If dozens of pages ever carry `theme:`, publish one sheet per theme
    through assets.py instead; the mechanism changes, the grammar does not.
  * FOLDER INHERITANCE IS NOT BUILT. `objects/_base.yml` says "a page beats its
    folder on LOOK": the page half is true now, the folder half is still spec.
  * The print composer stitches pages into ONE document, which wears the host
    page's theme, not each source page's.
  * 🔴 TRIPWIRE: `navigation.instant` is absent from mkdocs.yml. Instant
    navigation swaps the body and keeps the head, so a themed page's <style>
    would leak onto every page clicked to after it. specs/chrome.md carries the
    same tripwire for the same reason.

⚠️ UNKNOWN NAMES ARE SKIPPED, NEVER FALLEN BACK. vectors.resolve() falls an
unknown SITE theme back to `base`; for a page that would repaint it in a skin
nobody asked for. So every name is checked against vectors.known() first, and an
unknown one leaves the page on the SITE theme, reported by page and name. Born
2026-09-28 of `theme: paper` on app-home-sm, which is not a slug.

⚠️ NOTES THE EMITTER WRITES DURING THE SWAP ARE RE-LABELLED, NOT SUPPRESSED. A
dangling pointer in a page's theme is still a defect and still reported, just
prefixed so it cannot be mistaken for the site's. Exact repeats of a note the
site build already wrote (the contrast floor, say) are dropped.

⚠️ WEBFONTS. The page theme's typography row may name faces the site never
fetched, so fonts.py's own builder runs under the same swap and a second
`<link>` is added when its URL differs from the site's.

⚠️ `data-dr-theme` ON <html> IS A HOOK, NOT A MECHANISM. Nothing in the engine
selects on it; it is there so a site's theme.css or a human in devtools can see
which pages are wearing their own theme.
"""

from __future__ import annotations

import html
import re

from . import fonts, state, theme, vectors

_HTML = re.compile(r"<html\b[^>]*>", re.I)
_SLOTS = ("dark", "light")
_MISSING = object()

#: Rendered sheets for THIS build, keyed by declaration. Reset whenever
#: state.REPORT is a new object, i.e. on every state.reset(), so `mkdocs serve`
#: never paints the previous build's vectors. Lives here, not in state.py: only
#: this module reads or writes it (state.py's admission price).
_CACHE: dict = {"report": None, "sheets": {}, "site_font": None}


def _fresh() -> dict:
    if _CACHE["report"] is not state.REPORT:
        _CACHE.update(report=state.REPORT, sheets={}, site_font=None)
    return _CACHE


def _key(decl) -> str:
    if isinstance(decl, dict):
        return " ".join(s + "=" + str(decl.get(s) or "") for s in _SLOTS)
    return str(decl).strip()


def _names(decl) -> list[str]:
    if isinstance(decl, dict):
        return [str(decl[s]).strip() for s in _SLOTS if decl.get(s)]
    return [str(decl).strip()]


def _relabel(before: dict, label: str) -> None:
    """Prefix every note written since `before`; drop exact repeats."""
    for items in state.REPORT.values():
        if not isinstance(items, list):
            continue
        start = before.get(id(items), None)
        if start is None:
            continue
        old, new = items[:start], items[start:]
        if new:
            seen = set(old)
            items[start:] = [label + m for m in new if m not in seen]


def _font_url() -> str:
    wanted = fonts._wanted()
    return fonts._url(wanted) if wanted else ""


def _quietly(label: str, fn):
    """Run `fn`, then relabel whatever it reported. Buckets are snapshotted by
    identity so a bucket created mid-call is still covered."""
    before = {id(v): len(v) for v in state.REPORT.values() if isinstance(v, list)}
    buckets = set(state.REPORT)
    try:
        return fn()
    finally:
        for name in set(state.REPORT) - buckets:
            items = state.REPORT[name]
            if isinstance(items, list):
                before[id(items)] = 0
        _relabel(before, label)


def _swapped(decl, fn):
    """Call `fn` with the instance's theme declaration swapped for `decl`."""
    saved = state.INSTANCE.get("theme", _MISSING)
    state.INSTANCE["theme"] = decl
    try:
        return fn()
    finally:
        if saved is _MISSING:
            state.INSTANCE.pop("theme", None)
        else:
            state.INSTANCE["theme"] = saved


def _render(decl) -> tuple[str, str]:
    """(css, font_url or "") for one declaration, once per build."""
    cache = _fresh()
    key = _key(decl)
    if key in cache["sheets"]:
        return cache["sheets"][key]
    if cache["site_font"] is None:
        cache["site_font"] = _quietly("", _font_url)
    css, font = _quietly(
        "page theme '" + key + "': ",
        lambda: _swapped(decl, lambda: (theme.build_css(), _font_url())),
    )
    out = (css, "" if font == cache["site_font"] else font)
    cache["sheets"][key] = out
    return out


def _stamp(output: str, value: str) -> str:
    m = _HTML.search(output)
    if not m or "data-dr-theme=" in m.group(0):
        return output
    tag = m.group(0)
    new = tag[:-1] + ' data-dr-theme="' + html.escape(value, quote=True) + '">'
    return output[: m.start()] + new + output[m.end():]


def _problem(decl) -> str:
    """Why this declaration cannot be honoured, or "" if it can."""
    if isinstance(decl, dict):
        extra = sorted(str(k) for k in decl if k not in _SLOTS)
        if extra:
            return "names slot(s) " + ", ".join(extra) + "; only dark and light exist"
        if not any(decl.get(s) for s in _SLOTS):
            return "is a mapping with neither dark nor light"
    elif not isinstance(decl, (str, int, float)):
        return "is not a theme name or a {dark, light} mapping"
    known = vectors.known()
    unknown = [n for n in _names(decl) if n not in known]
    if unknown:
        return ("names " + ", ".join("'" + n + "'" for n in unknown)
                + ", which is not a theme in the registry")
    return ""


def on_post_page(output, page, config):
    decl = (getattr(page, "meta", None) or {}).get("theme")
    if decl is None or decl == "" or decl == {}:
        return output
    src = getattr(getattr(page, "file", None), "src_uri", "?")

    why = _problem(decl)
    if why:
        state.note(
            "notes",
            "page theme: " + src + " `theme:` " + why + ". Page kept on the "
            "SITE theme; nothing substituted. Fix the frontmatter.",
        )
        return output

    key = _key(decl)
    if key == _key(state.INSTANCE.get("theme", "base")):
        return output  # names the site's own theme: already wearing it

    # Fail open, chrome.py's rule: a page that cannot be themed keeps the site
    # theme and says so; it never breaks.
    try:
        i = output.lower().rfind("</head>")
        if i == -1:
            state.note("notes", "page theme: " + src + " has no </head>; site theme kept.")
            return output
        css, font = _render(decl)
        block = ""
        if font:
            block += '<link rel="stylesheet" href="' + html.escape(font, quote=True) + '">'
        block += '<style id="dr-page-theme">\n' + css + "</style>"
        output = output[:i] + block + output[i:]
        output = _stamp(output, key)
        state.note(
            "notes",
            "page theme: " + src + " wears '" + key + "' (inlined, last sheet "
            "on the page" + (", plus its own webfonts" if font else "") + ").",
        )
    except Exception as e:  # pragma: no cover
        state.note("notes", "page theme: failed on " + src + ": " + repr(e) + "; site theme kept.")
    return output
