"""Stage 06 -- page-body rewrites on_page_content, composed in ONE shim.

1. `docrender/sign.py`: `type: sign` wraps the body in its sheet card (2026-10-08).
2. `docrender/pagefoot.py`: the edit link at the foot of every page.

⚠️ ORDER IS LOAD-BEARING. sign wraps FIRST so the edit link lands outside the
card, never inside the sign. Composed here rather than as a new hook file because
mkdocs.yml is past the size ceiling and is not rewritten for a registration (the
06b shim states the same rule).
"""

from docrender import pagefoot, sign


def on_page_content(html, page, config, files):
    html = sign.on_page_content(html, page, config, files)
    return pagefoot.on_page_content(html, page, config, files)
