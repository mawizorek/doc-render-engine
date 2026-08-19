"""Stage 05b -- flow strips and embedded completion forms.

TWO EVENTS, ONE REGISTRATION, and the position is chosen for the later one:

    on_page_markdown   `!!! form "slot"` -> the embed, from `forms:`
    on_page_content    append this page's flow strips

WHY 05b RATHER THAN LATER. `on_page_content` must run BEFORE hook 06, because
pagefoot.py appends the edit link there and a reader's next step outranks a
maintainer's -- a strip below "Edit this page on GitHub" reads as an
afterthought. One registration sets the position of every event a stage handles
(mkdocs.yml says so about 08b), so the markdown half inherits this slot.

⚠️ THE MARKDOWN HALF IS THEREFORE LATE, AND THAT IS SAFE RATHER THAN LUCKY. It
emits a raw HTML block containing no `@` references and no marker syntax, so
nothing between 03 and here had anything to resolve inside it. If a future
version ever puts an `@id` link inside that block, this stage has to move ahead
of 03 and the form loses the ability to be built from a resolved reference --
which is the trade, stated now rather than discovered then.

🚨 REMOVING THIS LINE FROM mkdocs.yml IS NOT A NO-OP. Every `!!! form` on every
page would render as an ordinary admonition titled "form" -- a grey box where a
compliance form should be, on a page that looks completely correct -- and every
flow strip would silently stop rendering while `chain:` kept working perfectly.
Same shape as 03c and 03d, and the reason those two carry the same warning.
"""

from docrender.program import (  # noqa: F401
    on_page_content,
    on_page_markdown,
)
