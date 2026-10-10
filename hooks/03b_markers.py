"""Stage 03b -- inline markers ([text]{.tbc}, [source 4]{.term} and friends),
preceded by inline hover text ([text]{hover="..."}, docrender/hoverspan.py).

After links, because both rewrite inline syntax and running the id resolver
first keeps its output out of the marker pattern's way.

HOVER RUNS FIRST, AND THE ORDER IS SAFE EITHER WAY BY CONSTRUCTION: markers only
match a brace that opens with a dot (`{.est}`), hover only `{hover=`, and the
hover string is entity-escaped so a `{.est}` inside it can never become a chip.
Composed here rather than as a new hook file because mkdocs.yml is not rewritten
for a registration (06 / 06b precedent).

⚠️ THREE EVENTS, AND THE LIST IS LOAD-BEARING. MkDocs inspects THIS module for
event functions, not docrender/markers.py, so a function that exists there and is
not imported here simply never runs. This shim forwarded only
`on_page_markdown` when the class axis was built, which would have left the
resolved marker table empty on every build -- and an empty table makes
`on_page_markdown` return the page untouched, so EVERY MARKER ON EVERY SITE
would have quietly stopped rendering. No error, no report entry, no clue.

Same shape as the warning in mkdocs.yml about a file in hooks/ that is absent
from the `hooks:` list, one level further down: registration is explicit at both
layers, and both layers fail silently.

  on_files         resolves markers.tsv against marker-classes.tsv, ONCE
  on_page_markdown hover spans, then rewrites the marker spans
  on_post_build    sorts the inventory so the report reads as families
"""

from docrender import hoverspan
from docrender.markers import (  # noqa: F401
    on_files,
    on_post_build,
)
from docrender.markers import on_page_markdown as _markers_page


def on_page_markdown(markdown, page, config, files):
    markdown = hoverspan.on_page_markdown(markdown, page, config, files)
    return _markers_page(markdown, page, config, files)
