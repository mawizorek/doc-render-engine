"""Stage 08b -- render the finished build report into the page that asked.

A shim, like every other hook file here: the work is in docrender/report.py.
See mkdocs.yml for why the LIST is the registration and a file sitting in this
folder unlisted does nothing at all.

🔴 WHY 08b, AND IT IS THE ONLY THING ABOUT THIS STAGE THAT CAN BREAK. The report
is not finished until hook 08's `on_post_build` has run the size budget and the
leak scan -- those two are the last writers into `state.REPORT`. Substitute
before them and the page ships missing exactly the findings hook 08 exists to
produce, while looking perfectly correct.

⚠️ AND THE MARKDOWN SWAP IS LATE ONLY BECAUSE OF THAT. MkDocs dispatches every
event in hook-list order, so a stage registered early enough to rewrite markdown
early would also run its `on_post_build` before hook 08. One registration, one
position, and the post-build end is the end that matters. Nothing between 01 and
08 reads `!!!` directives it does not own, so the literal line sitting there
until now costs nothing.

`b` AND NOT `2`, per hooks/README.md: `_` sorts AFTER a digit and BEFORE a
letter, so `082_report.py` would sit ahead of `08_sizecheck.py` on disk while
running after it in mkdocs.yml -- the filesystem and the config disagreeing about
order, inside the one directory whose entire premise is that the filename carries
the order.

Three events, three jobs:

  on_files          clear last build's pending pages (`mkdocs serve` rebuilds
                    in-process, so a module global outlives its build)
  on_page_markdown  swap `!!! report` for a marker the html will carry
  on_post_build     read the built page back and substitute the finished report
"""

from docrender.report import (  # noqa: F401
    on_files,
    on_page_markdown,
    on_post_build,
)
