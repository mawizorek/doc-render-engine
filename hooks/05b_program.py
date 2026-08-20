"""Stage 05b -- flow strips, embedded completion forms, and the chain index.

THREE MODULES, TWO EVENTS, ONE REGISTRATION:

    docrender/forms.py       on_page_markdown   `!!! form "slot"` -> the embed
    docrender/chainlist.py   on_page_markdown   `!!! chain` -> an ordered index
    docrender/program.py     on_page_content    append this page's flow strips

⭐ THE SPLIT IS BY EVENT AND BY CONCERN, NOT BY SIZE ALONE. A body directive that
rewrites markdown is a different job from appending navigation to finished HTML,
and an embed is a different job from a list. Size was the trigger each time --
`program.py` reached 16,949 B before `forms.py` came out of it and 18,350 B before
`chainlist.py` did, against a ~22KB hard read ceiling -- but
`specs/visibility-split.md` §1 is the rule that decided WHERE to cut: follow the
concerns, and if bytes and concerns ever disagree, follow the concerns.

🔴 AND THIS SHIM NOW WIRES BY HAND, WHICH IT DID NOT BEFORE. MkDocs looks up ONE
function per event name per hook FILE, so two modules handling
`on_page_markdown` cannot both be imported under that name -- the second import
would silently shadow the first and one directive would stop working with no
error anywhere. The composition below is the whole reason this file is not four
import lines.

⚠️ ORDER INSIDE THE COMPOSITION IS FREE TODAY AND IS NOT GUARANTEED TO STAY SO.
`!!! form` and `!!! chain` are disjoint patterns and neither emits the other's
syntax, so neither can consume the other's output. 🚨 If either ever emits a `!!!`
block, this order becomes load-bearing and must be argued here -- exactly the
relationship 01d/03b already have, where the token audit emits marker syntax that
a later stage renders.

WHY 05b RATHER THAN LATER. `on_page_content` must run BEFORE hook 06, because
pagefoot.py appends the edit link there and a reader's next step outranks a
maintainer's -- a flow strip below "Edit this page on GitHub" reads as an
afterthought. 🔴 That ordering matters MORE since `hide: footer` landed on program
pages: the strip is now the ONLY navigation, so its position is the position of
the only control on the page.

⚠️ THE MARKDOWN HALF IS THEREFORE LATE, AND THAT IS SAFE RATHER THAN LUCKY. One
registration sets the position of every event a stage handles (mkdocs.yml says so
about 08b). Neither directive emits `@` references or marker syntax, so nothing
between 03 and here had anything to resolve inside them. 🔴 THE CONSEQUENCE IS A
REAL CONSTRAINT ON chainlist.py: hook 03 resolved every `@id` on this page long
ago, so the index MUST emit finished relative URLs. An `@id` written there would
ship to the reader as literal text.

🚨 REMOVING THIS LINE FROM mkdocs.yml IS NOT A NO-OP. Every `!!! form` and
`!!! chain` would render as an ordinary grey admonition titled "form" or "chain"
-- a box where a compliance form should be -- and every flow strip would silently
stop rendering while `chain:` kept working perfectly, which now means a program
page with `hide: footer` would have NO navigation at all. Same shape as 03c and
03d.
"""

from docrender import chainlist, forms, program


def on_page_markdown(markdown, page, config, files):
    """Both body directives, in one registration. See the red block above."""
    markdown = forms.on_page_markdown(markdown, page, config, files)
    return chainlist.on_page_markdown(markdown, page, config, files)


on_page_content = program.on_page_content
