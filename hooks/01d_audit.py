"""Stage 01d -- the token audit page.

A shim, like every other hook file here: the work is in docrender/, this only
registers it. See mkdocs.yml for why the LIST is the registration and a file
sitting in this folder unlisted does nothing at all.

WHY 01d AND NOT LATER. It has to run BEFORE 03_links and 03b_markers so the
marker specimens it emits are rendered by markers.py itself -- which is what
makes them real markers, counted in the build report, painted from the same
generated CSS as every other marker on the site. Rendering them here would be a
second implementation of a thing that already works, and the two would drift.
"""

from docrender.tokenaudit import on_page_markdown  # noqa: F401
