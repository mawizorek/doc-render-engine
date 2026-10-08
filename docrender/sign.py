"""Stage 06 (first half) -- `type: sign`, a page that prints AS a sign.

    ---
    type: sign
    frame: <slug in frames.tsv>
    ---

    ![Logo](@img:...)
    ## Kicker line          any number, all one size
    # The message           the big words

Spec, measurements and the seven rulings: specs/sign-layout.md.

WHAT IT DOES. Wraps the page body in a sheet-shaped card -- three nested frame
bands from `frames.tsv`, a white field, the source sign's Source Serif 4 at the
source sign's point sizes -- and injects that page's CSS and font beside it. On
paper ONLY the card prints: no letterhead, no revised / posted-by, no page
number (R5, forced). On screen the header and the print menu stay (the PR #277
lesson): the card is a preview of the sheet.

=========================================================================
⭐ THE SHEET SCALES TO THE PRINTABLE AREA, SO @page CANNOT BREAK IT
=========================================================================
The spec's top risk was a browser ignoring `@page` and spilling a sheet-sized
frame onto a second page. So nothing here is sized to the paper. The card is
`aspect-ratio: 8.5 / 11` at the full width of the content column, and every
length inside it is `--u` = one SHEET point = `100cqi / 612`. Whatever margin
the browser takes, the card is the printable width and 11/8.5 of it tall, which
is shorter than the printable height for every margin a Letter dialog offers.
The design scales as one picture instead of overflowing.

⚠️ `cqi` needs a container-query browser (Chrome 105+, Safari 16+, Firefox
110+). Older ones get `--u: 1pt` from the `@supports` fallback: correct on a
full-width sheet, cramped in a narrow screen column. Not paper-verified at ship.

=========================================================================
WHY HERE, AND WHY THE STYLE IS IN THE BODY
=========================================================================
* on_page_content, composed in hooks/06_pagefoot.py BEFORE the edit link, so
  the page body can be WRAPPED. on_post_page sees the whole template and would
  have to find the content by pattern.
* `revised` / owner lines are already appended by this stage; the body is split
  at the first of them so they stay OUTSIDE the card (screen shows them under
  it; print hides them).
* The `<style>` and the font `<link>` sit inside the content, on the chrome.py
  precedent of a page-scoped sheet only the asking page pays for. Body-placed
  stylesheets are honoured by every current browser. ⭐ And being LAST in the
  document, they beat the print menu's own <style> in <head> on @page boxes.
  🔴 Not a registered asset: docrender/assets.py is past the read ceiling.
* The frame row is read through vectors.entity(), so frames.tsv is live from
  the design system with the vendored copy as fallback, like every vector.

FAILS OPEN: an unknown frame renders a frameless card and is REPORTED; a page
that cannot be split is wrapped whole. Never a broken page.
"""

from __future__ import annotations

import re

from . import state, vectors

FONT = (
    "https://fonts.googleapis.com/css2?"
    "family=Source+Serif+4:wght@400;600&display=swap"
)

#: The first piece of foot furniture the earlier stages appended.
_FOOT = re.compile(r'<p class="dr-(?:revised|owner)\b')

_HEX = re.compile(r"^#[0-9A-Fa-f]{3,8}$")

# 1u = one point on a 612pt-wide Letter sheet. Sizes below are the source PDF's.
CSS = """
.dr-sign{--u:1pt;container-type:inline-size;width:100%;max-width:8.5in;
  aspect-ratio:8.5/11;margin:0 auto 1.4rem;background:#fff;color:#231f20;
  box-sizing:border-box;
  box-shadow:0 .2rem 1.2rem rgba(0,0,0,.35);break-inside:avoid;
  -webkit-print-color-adjust:exact;print-color-adjust:exact}
@supports (width:1cqi){.dr-sign__pad{--u:calc(100cqi / 612)}}
.dr-sign__pad{box-sizing:border-box;height:100%;padding:calc(var(--u)*18)}
.dr-sign__f1,.dr-sign__f2,.dr-sign__f3{box-sizing:border-box;height:100%;border-style:solid}
.dr-sign__f1{border-color:var(--sg-o,transparent);border-width:calc(var(--u)*var(--sg-ow,0))}
.dr-sign__f2{border-color:var(--sg-m,transparent);border-width:calc(var(--u)*var(--sg-mw,0))}
.dr-sign__f3{border-color:var(--sg-i,transparent);border-width:calc(var(--u)*var(--sg-iw,0));
  background:#fff;display:flex;flex-direction:column;align-items:center;
  text-align:center;overflow:hidden;font-family:'Source Serif 4',Georgia,serif}
html body .md-typeset .dr-sign__f3 > *{margin:0 !important;padding:0 !important;
  border:0 !important;color:#231f20 !important;max-width:94%}
html body .md-typeset .dr-sign__f3 p{font:400 calc(var(--u)*18)/1.4 'Source Serif 4',Georgia,serif !important;
  margin-top:calc(var(--u)*14) !important}
html body .md-typeset .dr-sign__f3 > p:first-child{margin-top:calc(var(--u)*35) !important;line-height:0 !important}
html body .md-typeset .dr-sign__f3 img{display:block;width:calc(var(--u)*431);max-width:100%;height:auto;margin:0 auto}
html body .md-typeset .dr-sign__f3 h2{font:600 calc(var(--u)*36)/calc(var(--u)*52) 'Source Serif 4',Georgia,serif !important;
  text-transform:uppercase;letter-spacing:.005em}
html body .md-typeset .dr-sign__f3 > p:first-child + h2{margin-top:calc(var(--u)*86) !important}
html body .md-typeset .dr-sign__f3 h1{font:400 calc(var(--u)*72)/calc(var(--u)*86) 'Source Serif 4',Georgia,serif !important;
  text-transform:uppercase;letter-spacing:0}
html body .md-typeset .dr-sign__f3 h2 + h1{margin-top:calc(var(--u)*48) !important}
html body .md-typeset .dr-sign__f3 > p:first-child + h1{margin-top:calc(var(--u)*120) !important}
.dr-sign .headerlink{display:none !important}
@media print{
  html body .md-content .md-content__inner > :not(.dr-sign){display:none !important}
  html body .md-content .md-content__inner .buildstamp--corner{display:none !important}
  .dr-sign{box-shadow:none;margin:0 auto}
  @page{@top-left{content:none}@top-center{content:none}@top-right{content:none}
    @bottom-left{content:none}@bottom-center{content:none}@bottom-right{content:none}}
}
"""


def _width(raw) -> str:
    try:
        n = float(str(raw).strip())
    except ValueError:
        return ""
    return str(n) if 0 <= n <= 72 else ""


def _vars(row: dict) -> str:
    out = []
    for key, var in (("outer", "o"), ("middle", "m"), ("inner", "i")):
        col = (row.get(key) or "").strip()
        w = _width(row.get(key + "-w") or "")
        if _HEX.match(col) and w:
            out.append("--sg-" + var + ":" + col + ";--sg-" + var + "w:" + w)
    return ";".join(out)


def _is_sign(page) -> bool:
    meta = getattr(page, "meta", None) or {}
    return str(meta.get("type") or "").strip().lower() == "sign"


def on_page_content(html, page, config, files):
    if not _is_sign(page):
        return html
    meta = page.meta
    src = getattr(getattr(page, "file", None), "src_uri", "?")

    style = ""
    name = str(meta.get("frame") or "").strip()
    if name:
        row = vectors.entity("frames.tsv", name)
        if row:
            style = _vars(row)
            if not style:
                state.note("notes", "sign: frame '" + name + "' on " + src
                           + " has no usable band (need #hex + a pt width); drawn frameless.")
        else:
            state.note("dead_links", "sign: frame '" + name + "' on " + src
                       + " is not a row in frames.tsv; drawn frameless. Rows live in "
                       + "maw-themes vectors/frames.tsv.")

    m = _FOOT.search(html)
    head, tail = (html[: m.start()], html[m.start():]) if m else (html, "")

    attr = ' style="' + style + '"' if style else ""
    return (
        '<link rel="stylesheet" href="' + FONT + '">'
        + '<style id="dr-sign">' + CSS + "</style>"
        + '<div class="dr-sign"' + attr + '><div class="dr-sign__pad"><div class="dr-sign__f1"><div class="dr-sign__f2">'
        + '<div class="dr-sign__f3">' + head.strip() + "</div></div></div></div></div>"
        + tail
    )
