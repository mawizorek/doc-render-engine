"""Stage 01c -- draw the revision log from the TSV the content repo commits.

⚠️ `on_post_build` USED TO BE IMPORTED HERE and deliberately is not any more.
revlog.py no longer generates anything -- the log is written by a workflow in
the content repo and this stage only renders it -- so the function is gone, and
an import naming it would raise ImportError at load time and take down every
stage registered after this one in mkdocs.yml.

Worth stating rather than silently deleting: a hook file is a two-line shim, so
the one thing it can get wrong is naming a function the module no longer has.
"""

from docrender.revlog import on_page_markdown  # noqa: F401
