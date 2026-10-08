"""Stage 06b (second half) -- `chrome: app`, the renderer with the skin off.

specs/chrome.md reserved the `chrome:` key for BUILD 5 with two values, `bare`
and `branch`. This ships a THIRD value first, because it is the one with a real
customer: a page that should open like a small app rather than a page of a
documentation site.

    ---
    id: app-home
    status: unlisted
    chrome: app
    ---

WHAT `app` TAKES AWAY, on screen only: the tabs, both sidebars (so the nav
drawer and the table of contents), search, the site title and logo, the
footer and its prev/next, breadcrumbs, back-to-top, the edit line and the
buildstamp at the foot. WHAT IT KEEPS: the letterhead at the top, the content,
the light/dark switch, the print button and (on a program page) the docked
Last/Next icons from program.py, which float top right as a pill.

Print is untouched. print-chrome.css already strips all of this on paper, so
an app page prints exactly like any other page.

⭐ WHY THIS WRITES ITS OWN <style> INSTEAD OF A RULE IN chrome.css. The rules
only ever apply to pages that declared `chrome: app`, so shipping them to every
page on every site would be dead weight, and a class nobody sets is a rule
nobody can test. Injecting them here means the page that asks is the only page
that pays, and the CSS lives beside the one line that switches it on. It also
leaves assets.py (at the size ceiling) alone.

⚠️ `status: unlisted` IS THE PARTNER KEY, NOT THIS ONE. `chrome: app` hides the
site from the reader; it does not hide the page from the site. Unlisted keeps
it out of search and the sidebar. Neither makes a page PRIVATE: anyone with the
link can open it. Anything sensitive belongs behind a router code or in a
ClickUp shared view scoped to exactly the fields that reader should see.

⚠️ `bare` AND `branch` ARE STILL SPEC ONLY. They are reported under notes, not
guessed at, so a page asking for them renders with full chrome and a human is
told why. Same for any unknown value.

⚠️ THE FLOW STRIP IS NOT HIDDEN (2026-09-28, docrender/program-dl.md D1). An
app page that declares or faces a `chain:` shows its Start strip, and program.py
inlines `CSS` on the member pages of an app face so the reader stays in the app
all the way through. `CSS` is IMPORTED there: keep it self-contained, all of it
under html.dr-app.

Also sets the two meta tags that make "Add to Home Screen" on a phone open the
page standalone, with no browser bar. That is the whole trick of feeling like
an app, and it costs two lines.

=========================================================================
`hide: header` -- THE WHOLE BAR GONE (2026-10-08)
=========================================================================
> Michael: *"hide the header entirely and just directly insert the logo
> centered at the top of the page"* -- the uritp backstage sign.

🔴 MATERIAL IGNORES `header` IN `hide:`. specs/chrome.md already proved the
header block is gated by NOTHING, at any version, so before this the value
parsed, matched no template branch, and did nothing with no report. It is
honoured HERE, on the existing `hide:` list, rather than as a new `chrome:`
value, because `hide:` is where an author already says what to remove and
`navigation`/`toc`/`footer` sit right beside it.

⚠️ IT TAKES EVERYTHING IN THE BAR: site title, logo link home, search, the
light/dark switch and the print icon. That is the ask ("entirely"); `chrome:
app` is the answer for a page that wants to KEEP the switch and print. A
reader can still print with the browser's own Print command.

⭐ SCREEN ONLY. print-chrome.css already removes the header on paper, so a
second print rule would be a second claimant on one fact. Same page-scoped
<style> mechanism as `app`, same fail-open: a page that cannot be marked
keeps its header and is reported, never broken.
"""

from __future__ import annotations

import re

from . import state

BUILT = ("app",)
SPEC_ONLY = ("bare", "branch")

_HTML = re.compile(r"<html\b[^>]*>", re.I)
_CLASS = re.compile(r'\bclass="([^"]*)"', re.I)

# Everything under html.dr-app, so the rules are inert on any other page even
# if this block were ever pasted somewhere it should not be.
CSS = """
@media screen {
html.dr-app .md-tabs, html.dr-app .md-sidebar, html.dr-app .md-footer,
html.dr-app .md-content__button, html.dr-app .md-path, html.dr-app .md-top,
html.dr-app .md-overlay, html.dr-app .md-source-file,
html.dr-app .pagefoot, html.dr-app .pagefoot__rule,
html.dr-app .buildstamp--foot { display: none !important; }
html.dr-app .md-header {
  position: fixed; top: .6rem; right: .6rem; left: auto; width: auto;
  height: auto; background: var(--md-default-bg-color);
  color: var(--md-default-fg-color); border-radius: 2rem;
  box-shadow: 0 .1rem .5rem rgba(0,0,0,.25);
}
html.dr-app .md-header__inner { padding: 0 .3rem; height: 2.4rem; }
html.dr-app .md-header__inner > :not(.md-header__option):not(.dr-printctl__trigger):not(.dr-flow__pill) {
  display: none !important;
}
html.dr-app .md-main__inner { margin-top: 1.2rem; }
html.dr-app .md-content { max-width: 52rem; margin: 0 auto; }
html.dr-app .md-content__inner { margin: 0 1rem; padding-top: .8rem; }
}
"""

# `hide: header`. Same isolation rule as CSS: all of it under its own class.
NOHEADER_CSS = """
@media screen {
html.dr-noheader .md-header { display: none !important; }
}
"""

META = (
    '<meta name="apple-mobile-web-app-capable" content="yes">'
    '<meta name="mobile-web-app-capable" content="yes">'
)


def _mark(output: str, cls: str = "dr-app") -> str:
    m = _HTML.search(output)
    if not m:
        return output
    tag = m.group(0)
    c = _CLASS.search(tag)
    if c:
        new = tag[: c.start(1)] + (c.group(1) + " " + cls).strip() + tag[c.end(1):]
    else:
        new = tag[:-1] + ' class="' + cls + '">'
    return output[: m.start()] + new + output[m.end():]


def _head(output: str, block: str) -> str:
    i = output.lower().rfind("</head>")
    if i == -1:
        return output
    return output[:i] + block + output[i:]


def _hides_header(meta) -> bool:
    hide = meta.get("hide") or []
    if isinstance(hide, str):
        hide = [hide]
    return any(str(h).strip().lower() == "header" for h in hide)


def on_post_page(output, page, config):
    meta = getattr(page, "meta", None) or {}
    src = getattr(getattr(page, "file", None), "src_uri", "?")

    if _hides_header(meta):
        # Fail open, same as `app`: an unmarkable page keeps its header.
        try:
            output = _mark(output, "dr-noheader")
            output = _head(output, '<style id="dr-chrome-noheader">' + NOHEADER_CSS + "</style>")
        except Exception as e:  # pragma: no cover
            state.note("notes", "hide: header failed on " + src + ": " + repr(e))

    want = meta.get("chrome")
    if not want:
        return output
    want = str(want).strip().lower()
    if want not in BUILT:
        why = "spec only (specs/chrome.md)" if want in SPEC_ONLY else "unknown value"
        state.note("notes", "chrome: " + want + " on " + src + " is " + why + "; full chrome kept")
        return output
    # Fail open: a page that cannot be marked keeps its chrome, never breaks.
    try:
        output = _mark(output)
        output = _head(output, META + '<style id="dr-chrome-app">' + CSS + "</style>")
    except Exception as e:  # pragma: no cover
        state.note("notes", "chrome: app failed on " + src + ": " + repr(e))
    return output
