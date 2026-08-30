"""Stage 05b -- flow strips, embedded completion forms, the chain index, and the
PROGRAM PACKET.

FOUR MODULES, FIVE EVENTS, ONE REGISTRATION:

    docrender/forms.py       on_page_markdown   `!!! form "slot"` -> the embed
    docrender/chainlist.py   on_page_markdown   `!!! chain` -> an ordered index
    docrender/packetbuild.py on_page_markdown   `!!! export` -> the button
                             on_files           mint the packet page
                             on_nav             capture the plan, prune the row
                             on_page_content    the automatic button slot
                             on_post_build      splice the packet together
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

⚠️ BUILD 10 ADDED `packetbuild` HERE RATHER THAN AS A NEW HOOK FILE, and the
reason is not laziness. A new stage would mean an edit to `mkdocs.yml`, which is
28,158 B: past the ~22.5KB read ceiling, so it cannot be read whole and therefore
cannot be safely rewritten. The packet is a PROGRAM concern and this is the
program stage, so the composition below is the honest home for it -- one more
voice in a file that already exists to compose several.

⚠️ ORDER INSIDE THE COMPOSITION IS FREE TODAY AND IS NOT GUARANTEED TO STAY SO.
`!!! form`, `!!! chain` and `!!! export` are disjoint patterns and none emits
another's syntax, so none can consume another's output. 🚨 If any ever emits a
`!!!` block, this order becomes load-bearing and must be argued here -- exactly the
relationship 01d/03b already have, where the token audit emits marker syntax that
a later stage renders.

🔴 ONE ORDER IS ALREADY LOAD-BEARING AND IT IS IN `on_page_content`: program's
strips are appended FIRST and the packet button SECOND. `hide: footer` makes the
strip the only navigation on a program page, and Michael rejected a separate
second footer by name on 08-19 -- so the button belongs immediately below the
strip it travels with, never above it and never in foot matter of its own.

⚠️ `on_files` AND `on_post_build` ARE THE TWO EVENTS THE PACKET CANNOT DO
WITHOUT, and neither has any other candidate: files are fixed after `on_files`,
and every member page's HTML is only finished and on disk by `on_post_build`.
Adding them here sets the packet's position for both -- one registration decides
the position of every event a stage handles.

WHY 05b RATHER THAN LATER. `on_page_content` must run BEFORE hook 06, because
pagefoot.py appends the edit link there and a reader's next step outranks a
maintainer's -- a flow strip below "Edit this page on GitHub" reads as an
afterthought. 🔴 That ordering matters MORE since `hide: footer` landed on program
pages: the strip is now the ONLY navigation, so its position is the position of
the only control on the page.

⚠️ THE MARKDOWN HALF IS THEREFORE LATE, AND THAT IS SAFE RATHER THAN LUCKY. One
registration sets the position of every event a stage handles (mkdocs.yml says so
about 08b). None of the three directives emits `@` references or marker syntax, so
nothing between 03 and here had anything to resolve inside them. 🔴 THE CONSEQUENCE
IS A REAL CONSTRAINT ON chainlist.py: hook 03 resolved every `@id` on this page
long ago, so the index MUST emit finished relative URLs. An `@id` written there
would ship to the reader as literal text. ⚠️ The same constraint binds the packet
button, which is why `packet.button` builds its href through `util.relative_url`
rather than writing a reference.

🚨 REMOVING THIS LINE FROM mkdocs.yml IS NOT A NO-OP. Every `!!! form`,
`!!! chain` and `!!! export` would render as an ordinary grey admonition titled
"form", "chain" or "export" -- a box where a compliance form should be -- every
flow strip would silently stop rendering while `chain:` kept working perfectly,
which now means a program page with `hide: footer` would have NO navigation at
all, AND no packet page would be minted, so every link a reader already holds to
one would 404. Same shape as 03c and 03d.
"""

from docrender import chainlist, forms, packetbuild, program


def on_page_markdown(markdown, page, config, files):
    """All three body directives, in one registration. See the red block above."""
    markdown = forms.on_page_markdown(markdown, page, config, files)
    markdown = chainlist.on_page_markdown(markdown, page, config, files)
    return packetbuild.on_page_markdown(markdown, page, config, files)


def on_page_content(html, page, config, files):
    """Flow strips, then the packet button beneath them. The order is a rule."""
    html = program.on_page_content(html, page, config, files)
    return packetbuild.on_page_content(html, page, config, files)


on_files = packetbuild.on_files
on_nav = packetbuild.on_nav
on_post_build = packetbuild.on_post_build
