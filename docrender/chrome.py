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

🪦 `hide: header` LIVED HERE FOR ~20 MINUTES (PR #277, reverted 2026-10-08).
It removed the screen header, which took the PRINT MENU with it, and did
nothing about the letterhead that actually prints -- Michael: *"now with the
header removed i cant edit print settings, and the header still displays on
print."* Paper furniture is a PRINT choice made at print time, so it lives in
the print panel (assets/printfurn.js, Hide header / Hide footer). 🚫 Do not
rebuild a frontmatter header switch: a page that hides its header hides the
only control that edits its print.
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

META = (
    '<meta name="apple-mobile-web-app-capable" content="yes">'
    '<meta name="mobile-web-app-capable" content="yes">'
)


def _mark(output: str) -> str:
    m = _HTML.search(output)
    if not m:
        return output
    tag = m.group(0)
    c = _CLASS.search(tag)
    if c:
        new = tag[: c.start(1)] + (c.group(1) + " dr-app").strip() + tag[c.end(1):]
    else:
        new = tag[:-1] + ' class="dr-app">'
    return output[: m.start()] + new + output[m.end():]


def on_post_page(output, page, config):
    want = (getattr(page, "meta", None) or {}).get("chrome")
    if not want:
        return output
    want = str(want).strip().lower()
    src = getattr(getattr(page, "file", None), "src_uri", "?")
    if want not in BUILT:
        why = "spec only (specs/chrome.md)" if want in SPEC_ONLY else "unknown value"
        state.note("notes", "chrome: " + want + " on " + src + " is " + why + "; full chrome kept")
        return output
    # Fail open: a page that cannot be marked keeps its chrome, never breaks.
    try:
        output = _mark(output)
        block = META + '<style id="dr-chrome-app">' + CSS + "</style>"
        i = output.lower().rfind("</head>")
        if i != -1:
            output = output[:i] + block + output[i:]
    except Exception as e:  # pragma: no cover
        state.note("notes", "chrome: app failed on " + src + ": " + repr(e))
    return output
