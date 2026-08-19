"""Stage 07 -- the build stamp: is this page the latest push?

🔴 BOTH EVENTS MUST BE IMPORTED, AND FORGETTING THE SECOND ONE DELETED THE STAMP
FROM EVERY PAGE OF EVERY SITE FOR 27 MINUTES (2026-08-19).

MkDocs discovers hook events by reading the MODULE NAMESPACE of the file named in
`mkdocs.yml`. A function that exists in `docrender/buildstamp.py` and is not
imported here does not exist as far as MkDocs is concerned -- **it is never
called, and nothing reports that it was not called.**

PR #138 moved the stamp out of Material's footer (where `print.css`'s chrome-off
list had been silently killing it) by adding `on_page_content` to the module AND
setting `config.copyright = None`. This file still imported only `on_config`. So:

    config.copyright = None   -> ran. The footer stamp was removed.
    on_page_content(...)      -> never registered. The replacement never appeared.

⚑ A MIGRATION THAT LANDS ITS DEMOLITION AND MISSES ITS CONSTRUCTION IS WORSE THAN
NOT STARTING. The old placement was broken on paper only; the half-applied fix was
broken everywhere, on all six sites, including screen -- where it had worked fine
for months.

⭐ AND THE CONTRAST INSIDE ONE PR IS THE LESSON. #138 also shipped
`assets/print-type.css`, which worked immediately, because a new STYLESHEET
registers through `assets.py`'s `_PRINT_ASSETS` tuple and `hand_written_css()`
derives from it. A new EVENT registers here, by hand, in a one-line file nobody
opens. **Two registration mechanisms, one automatic and one manual, and only the
manual one was missed.** The automatic one exists precisely because a hand-
maintained list went stale within two hours in 2026-08-04; this file is the same
shape and has no such protection.

⚠️ SO: WHEN A `docrender/` MODULE GAINS AN EVENT, THIS IS THE SECOND EDIT. Check
the sibling hooks -- `06_pagefoot.py` and `04b_router.py` both import
`on_page_content` explicitly, and that is the pattern, not an accident.
"""

from docrender.buildstamp import on_config, on_page_content  # noqa: F401
