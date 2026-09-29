"""Stage 06b -- the two things that rewrite a finished page on the way out.

1. `docrender/navstate.py`: open the folders that declared `nav: expanded`.
   00bb decided WHICH folders open; this writes the one attribute Material
   uses to say so.
2. `docrender/chrome.py`: `chrome: app`, the page with the site's skin off.

⚠️ `on_post_page` NOW HAS TWO CLAIMANTS, so the old comment here ("no other
claimant, the number is for a reader") stopped being true on 2026-09-28, which
is exactly what it said would happen. They are composed in ONE shim rather
than given a new hook file because mkdocs.yml is past the size ceiling and is
not to be rewritten for a registration.

The order between them is still free, and it is worth saying why so nobody
has to re-derive it: navstate only touches sidebar toggles inside <body>;
chrome only touches the <html> class and appends to <head>. Disjoint regions,
so either order produces the same bytes. If a third claimant ever lands here
and overlaps one of them, the order becomes real and belongs in this comment.
"""

from docrender import chrome, navstate


def on_post_page(output, page, config):
    output = navstate.on_post_page(output, page, config)
    return chrome.on_post_page(output, page, config)
