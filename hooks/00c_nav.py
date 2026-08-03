"""Stage 00c -- rewire prev/next after stage 00 reordered the nav.

MUST come after `00_instance.py` in mkdocs.yml. MkDocs runs same-named events
in the order the hooks are listed, and this one reads the tree that one sorts.
"""

from docrender.nav import on_nav  # noqa: F401
