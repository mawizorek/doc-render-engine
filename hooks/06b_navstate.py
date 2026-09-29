"""Stage 06b -- the three things that rewrite a finished page on the way out.

1. `docrender/navstate.py`: open the folders that declared `nav: expanded`.
   00bb decided WHICH folders open; this writes the one attribute Material
   uses to say so.
2. `docrender/chrome.py`: `chrome: app`, the page with the site's skin off.
3. `docrender/pagetheme.py`: `theme:` in a page's frontmatter, honoured
   (2026-09-28). Inlines that page's theme as the last sheet in <head>.

⚠️ `on_post_page` NOW HAS THREE CLAIMANTS. They are composed in ONE shim
rather than given new hook files because mkdocs.yml is past the size ceiling
and is not to be rewritten for a registration.

The order between them is still free, and it is worth saying why so nobody
has to re-derive it: navstate only touches sidebar toggles inside <body>;
chrome touches the <html> class and appends to <head>; pagetheme adds a
`data-dr-theme` attribute to <html> and appends to <head>. chrome and
pagetheme share a TAG but not an attribute, and each re-finds the tag rather
than trusting an offset, so either order produces equivalent markup. Their
<head> blocks share no selector-and-property pair (chrome writes layout rules,
pagetheme writes custom properties). pagetheme runs LAST anyway, so its
<style> is the final sheet on the page, which is the one thing its mechanism
leans on. If a fourth claimant lands here and appends a sheet that writes
`--dr-*` or `--md-*` properties, it must go BEFORE pagetheme.
"""

from docrender import chrome, navstate, pagetheme


def on_post_page(output, page, config):
    output = navstate.on_post_page(output, page, config)
    output = chrome.on_post_page(output, page, config)
    return pagetheme.on_post_page(output, page, config)
