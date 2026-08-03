"""Stage 01b -- draw TSV data files declared beside a page.

Runs in the content-generation family with objects (01), immediately after it
and before visibility (02). Placed there so that a data table exists before
anything downstream indexes or rewrites the page.
"""

from docrender.datatable import on_page_markdown  # noqa: F401
