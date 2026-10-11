"""Stage 02b -- the `@fmp:` namespace (a FileMaker name, written once in NAMES.tsv).

🔴 ITS POSITION IS NOT FREE, unlike 03c and 03d. The CLAIM is position-free (it
happens at import), but `on_page_markdown` here is the DRIFT scan, and it has to see
each page BEFORE stage 03 rewrites `@fmp:` references into names. Registered after
03, it would report this module's own output as hand-spelled names on every page.

🚨 AND ITS PRESENCE IS NOT OPTIONAL. Remove this line from mkdocs.yml and the module
is never imported, nothing claims `@fmp:`, and every reference renders as "unknown
peer site: fmp". See docrender/fmpnames.py and specs/fmp-names.md.
"""

from docrender.fmpnames import on_files, on_page_markdown  # noqa: F401
