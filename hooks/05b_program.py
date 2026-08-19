"""Stage 05b -- flow strips and embedded completion forms.

TWO MODULES, TWO EVENTS, ONE REGISTRATION:

    docrender/program.py   on_page_content    append this page's flow strips
    docrender/forms.py     on_page_markdown   `!!! form "slot"` -> the embed

⭐ THE SPLIT HAPPENED ON 2026-08-19, HOURS AFTER BOTH SHIPPED IN ONE FILE, and
this shim is the only place that had to know: `program.py` reached 16,949 B and
`collapsed:` would have pushed it past the ~22KB read ceiling. Size was the
TRIGGER; cohesion is the reason (`specs/visibility-split.md` §1). A strip is
navigation, a form is an embed, and they share no state.

⚠️ THE SHIM STAYS THIN EVEN THOUGH IT NOW SPANS TWO MODULES. Each name is
imported from the module that owns it, and nothing is wired by hand here --
unlike `00bb_navstate.py`, which passes functions in as arguments to dodge an
import cycle. There is no cycle: `program → forms` is a straight line.

WHY 05b RATHER THAN LATER. `on_page_content` must run BEFORE hook 06, because
pagefoot.py appends the edit link there and a reader's next step outranks a
maintainer's -- a flow strip below "Edit this page on GitHub" reads as an
afterthought. 🔴 That ordering matters MORE as of 2026-08-19, not less: with
`hide: footer` on program pages the strip is now the ONLY navigation, so its
position is the position of the only control on the page.

⚠️ THE MARKDOWN HALF IS THEREFORE LATE, AND THAT IS SAFE RATHER THAN LUCKY. One
registration sets the position of every event a stage handles (mkdocs.yml says so
about 08b), and the form block contains no `@` references and no marker syntax,
so nothing between 03 and here had anything to resolve inside it. If a future
version puts an `@id` inside that block, this stage has to move ahead of 03.

🚨 REMOVING THIS LINE FROM mkdocs.yml IS NOT A NO-OP. Every `!!! form` would
render as an ordinary grey admonition titled "form" where a compliance form
should be, and every flow strip would silently stop rendering while `chain:`
kept working perfectly -- which now means a program page with `hide: footer`
would have NO navigation at all. Same shape as 03c and 03d.
"""

from docrender.forms import on_page_markdown  # noqa: F401
from docrender.program import on_page_content  # noqa: F401
