"""Stage 03e -- the `!!! qr "name"` directive (BUILD 6 step 2).

🔴 THREE EVENTS, AND ALL THREE ARE IMPORTED EXPLICITLY BECAUSE OF hooks/07's
CAUTIONARY TALE. That shim imported `on_config` and not the other half for the
first 27 minutes of a change, so the line that REMOVED the old build stamp ran
and the line that added its replacement never did -- the stamp vanished from every
page of every site, including screen, where it had worked for months. mkdocs.yml's
own comment records the lesson: **a shim that imports one event out of two is
indistinguishable from a correct one until you look at the output.**

  on_config         clears the collector. ⚠️ NOT decoration: `mkdocs serve`
                    rebuilds IN-PROCESS, so without this a deleted page's code is
                    carried into the next build and written as a file nothing
                    references.
  on_page_markdown  rewrites each directive into its download link.
  on_post_build     writes the collected PNGs into `site_dir`. 🔴 THE HALF THAT
                    PRODUCES THE ARTIFACT. Drop it and every download link on
                    every page 404s while the pages themselves look perfect.

⚠️ UNLIKE 03c AND 03d, THIS SHIM CLAIMS NO `@` NAMESPACE. `!!! qr` is a BLOCK
DIRECTIVE on the `!!! form` precedent, not a reference, so nothing here registers
with docrender/prefixes.py and the "nothing claims the namespace" failure those
two warn about cannot happen. 🔴 specs/qr-codes.md's file table still describes
this shim in those terms -- carried over from an earlier revision where the
feature was `@qr:` -- and that line is wrong. The shim is load-bearing for a
different reason: it is the only thing that registers the events above.

POSITION. After 03d, and it is FREE in the way this list's comment keeps having to
restate. The directive is matched in this module's own `on_page_markdown` rather
than by links.py, and its output is raw HTML containing no `@` reference and no
marker syntax -- so no earlier stage had anything to resolve inside it and no
later stage has anything to find. It sits here because it reads as the next member
of the 03-series family.

⚠️ ONE REAL CONSTRAINT, STATED SO IT IS NOT DISCOVERED: `on_post_build` must run
while `state.REPORT` can still be written, because a failed write reports itself.
Hook 08 is the report's last writer and 08b renders it, so this stage's post-build
half lands EARLIER than both and its findings are still counted.
"""

from docrender.qr import (  # noqa: F401
    on_config,
    on_page_markdown,
    on_post_build,
)
