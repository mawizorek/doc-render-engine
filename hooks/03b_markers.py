"""Stage 03b -- inline markers ([text]{.tbc}, [source 4]{.term} and friends).

After links, because both rewrite inline syntax and running the id resolver
first keeps its output out of the marker pattern's way.

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
  on_page_markdown rewrites the spans
  on_post_build    sorts the inventory so the report reads as families
"""

from docrender.markers import (  # noqa: F401
    on_files,
    on_page_markdown,
    on_post_build,
)
