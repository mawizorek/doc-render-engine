"""Stage 01c -- replace a dr:revlog marker with the committed revision-log TSV.

⚠️ `on_post_build` is deliberately NOT imported any more. This stage used to
generate a second TSV into the site at post-build; the content repo's own
workflow now owns that file, so the generator was deleted (2026-08-04). Leaving
the import behind would raise ImportError at load and take EVERY later hook down
with it, because MkDocs imports this module before the build starts.
"""

from docrender.revlog import on_page_markdown  # noqa: F401
