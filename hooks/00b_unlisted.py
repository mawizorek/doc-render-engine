"""Stage 00b -- remove `unlisted` pages from the sidebar.

FIRST OF FOUR on_nav STAGES THAT HAVE TO RUN IN THIS ORDER:

    00    sort     instance.py orders the tree
    00b   prune    unlisted pages leave                      <- HERE
    00bb  shape    `nav: hidden` folders lose their children
    00bc  seal     routers take whatever is LEFT
    00c   chain    prev/next rebuilt from what survived

Move this after 00c and the footer Next button starts walking through pages that
are not in the sidebar. The other three orderings are argued where they are
enforced -- `visibility.seal_nav` for why the seal follows `nav:`, and
hooks/README.md for the numbering.

The logic lives in visibility.py with the rest of the publication gate, because
this is the same decision as `status:` and not a navigation feature. It is only a
separate hook file because MkDocs orders same-named events by hook file, so the
ORDER has to be expressed as a filename.

⚠️ visibility.py OWNS TWO on_nav STAGES NOW. `prune_nav` is this one; `seal_nav`
is 00bc, and it used to be pass 3 of this function. They were split on 2026-08-05
because sharing a function forced the seal to run before `nav:` was read, which
put pages a folder had hidden into a router's sealed manifest.
"""

from docrender.visibility import prune_nav as on_nav  # noqa: F401
