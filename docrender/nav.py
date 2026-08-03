"""Stage 00b -- re-derive prev/next AFTER the nav has been sorted.

MkDocs walks the nav and wires `page.previous_page` / `page.next_page` while
BUILDING it, which happens BEFORE `on_nav` fires. So anything that reorders the
nav -- and `instance.py:on_nav` reorders all of it -- leaves those links
pointing along the ORIGINAL order.

The result is a site that disagrees with itself: the sidebar reads in `order:`
sequence and the Next button at the foot of the page reads in filesystem
sequence. Both look plausible in isolation, which is why it survives review.

This re-flattens the sorted tree and rewires the chain. Runs as its own stage
rather than at the end of the sort so that the two concerns stay separable:
one decides ORDER, this one propagates its consequences.
"""

from __future__ import annotations


def _pages_in_order(items, out):
    for item in items:
        if getattr(item, "is_page", False):
            out.append(item)
        elif getattr(item, "children", None):
            _pages_in_order(item.children, out)
    return out


def on_nav(nav, config, files):
    pages = _pages_in_order(nav.items, [])
    if not pages:
        return nav

    # Replace the flat page list too. Material reads `nav.pages` for the
    # keyboard next/prev shortcuts, so leaving it stale would fix the visible
    # button and leave the invisible one wrong -- worse than not fixing either.
    nav.pages = pages

    for i, page in enumerate(pages):
        page.previous_page = pages[i - 1] if i > 0 else None
        page.next_page = pages[i + 1] if i + 1 < len(pages) else None

    return nav
