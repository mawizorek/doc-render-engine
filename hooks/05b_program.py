"""Stage 05b -- flow strips, embedded completion forms, live worksheets, launcher
cards, the chain index, the PROGRAM PACKET, and BINDERS.

SEVEN MODULES, ONE REGISTRATION:

    docrender/tally.py       on_page_markdown   `!!! tally "name"` -> a worksheet
    docrender/cards.py       on_page_markdown   `!!! cards` -> a Material card grid
    docrender/forms.py       on_page_markdown   `!!! form "slot"` -> the embed
    docrender/chainlist.py   on_page_markdown   `!!! chain` -> an ordered index
    docrender/packet.py      on_page_markdown   `!!! export` -> the button
                             on_nav             resolve the chain to page URLs
                             on_page_content    the automatic button slot
                             on_post_build      write `packets.json`
    docrender/program.py     on_page_content    append this page's flow strips
    docrender/binder.py      on_nav             `binder: true` programs -> presets
                             on_post_build      write `binders.json` (composer)

⭐ `tally.py` (2026-09-28) IS HERE BECAUSE A WORKSHEET HANDS ITS NUMBERS TO A FORM,
and forms live here. It is the same body-directive job as its neighbours, and a new
stage would mean editing `mkdocs.yml` (see the packet paragraph below). Its argued
contract is `specs/tally.md`.

⭐ `cards.py` (2026-09-28) IS HERE BECAUSE IT IS THE SAME BODY-DIRECTIVE JOB and a
new stage means editing `mkdocs.yml`. It runs AFTER hook 03, so it reads resolved
links and must resolve a bare `@id` card itself, against `state.PAGES`, recording
the edge with `state.ref`. Its contract is `specs/cards.md`.

🪦 IT WAS FIVE MODULES AND FIVE PACKET EVENTS UNTIL 2026-08-31. `packetbuild.py` is
retired into `packet.py`, and the packet dropped `on_files` (it minted a generated
`-packet.md`) and its `on_post_build` SPLICE (it assembled that page out of every
member's finished HTML). ⭐ **The event it kept at `on_post_build` writes one JSON file
and touches no page** -- Michael culled the combined page, and what fell out is that
this stage stopped writing to the built site at all. `binder.py` (2026-09-28, BUILD 11
phase 2) keeps that shape: one more JSON file, no page touched.

⭐ THE SPLIT IS BY EVENT AND BY CONCERN, NOT BY SIZE ALONE. A body directive that
rewrites markdown is a different job from appending navigation to finished HTML,
and an embed is a different job from a list. Size was the trigger each time --
`program.py` reached 16,949 B before `forms.py` came out of it and 18,350 B before
`chainlist.py` did, against a ~22KB hard read ceiling -- but
`specs/visibility-split.md` §1 is the rule that decided WHERE to cut: follow the
concerns, and if bytes and concerns ever disagree, follow the concerns. ⚠️ That rule
ran BACKWARDS on 08-31 and it was still the rule: `packet.py` was split from
`packetbuild.py` on the pure-versus-impure seam, the pure half was deleted, and
**merging them back is the same principle applied to a concern that no longer exists.**

🔴 AND THIS SHIM WIRES BY HAND, WHICH IT DID NOT ORIGINALLY. MkDocs looks up ONE
function per event name per hook FILE, so two modules handling `on_page_markdown`
cannot both be imported under that name -- the second import would silently shadow the
first and one directive would stop working with no error anywhere. The composition
below is the whole reason this file is not four import lines. ⚠️ `on_nav` and
`on_post_build` are now composed too, for exactly that reason: packet AND binder.

⚠️ THE PACKET LIVES HERE RATHER THAN IN A HOOK OF ITS OWN, and the reason is not
laziness. A new stage means an edit to `mkdocs.yml`, which is past the ~22.5KB read
ceiling -- so it cannot be read whole and therefore cannot be safely rewritten. The
packet is a PROGRAM concern and this is the program stage, so the composition below is
the honest home for it: one more voice in a file that already exists to compose
several. A binder is a program page too, so it lives here on the same argument.

⚠️ ORDER INSIDE THE MARKDOWN COMPOSITION IS FREE TODAY AND IS NOT GUARANTEED TO STAY
SO. `!!! tally`, `!!! cards`, `!!! form`, `!!! chain` and `!!! export` are disjoint patterns and
none emits another's syntax, so none can consume another's output. ⭐ A worksheet's
Send button finds its form IN THE BROWSER, after both have rendered, so tally running
first is a choice, not a dependency. 🚨 If any ever emits a `!!!` block, this order
becomes load-bearing and must be argued here -- exactly the relationship 01d/03b
already have, where the token audit emits marker syntax that a later stage renders.

🔴 ONE ORDER IS ALREADY LOAD-BEARING AND IT IS IN `on_page_content`: program's strips
are appended FIRST and the packet button SECOND. `hide: footer` makes the strip the
only navigation on a program page, and Michael rejected a separate second footer by
name on 08-19 -- so the button belongs immediately below the strip it travels with,
never above it and never in foot matter of its own.

🔴 AND `on_nav` IS NOT OPTIONAL FOR THE BUTTON EITHER, which is easy to miss now that
the packet's other events are gone: `on_page_content` only draws a button for a program
in `packet._PLAN`, and the plan is built at `on_nav`. Drop that line and every button
silently disappears while `export:` keeps validating perfectly.

WHY 05b RATHER THAN LATER. `on_page_content` must run BEFORE hook 06, because
pagefoot.py appends the edit link there and a reader's next step outranks a
maintainer's -- a flow strip below "Edit this page on GitHub" reads as an
afterthought. 🔴 That ordering matters MORE since `hide: footer` landed on program
pages: the strip is now the ONLY navigation, so its position is the position of the
only control on the page.

⚠️ THE MARKDOWN HALF IS THEREFORE LATE, AND THAT IS SAFE RATHER THAN LUCKY. One
registration sets the position of every event a stage handles (mkdocs.yml says so
about 08b). None of the four directives emits `@` references or marker syntax, so
nothing between 03 and here had anything to resolve inside them. ⭐ It is also what
lets tally's appended CSS carry `@media` safely. 🔴 THE CONSEQUENCE IS A REAL
CONSTRAINT ON chainlist.py: hook 03 resolved every `@id` on this page long ago,
so the index MUST emit finished relative URLs. An `@id` written there would ship to the
reader as literal text. ⚠️ The same constraint binds the packet button, which is why
`packet.button` builds its href through `util.relative_url` rather than writing a
reference.

🚨 REMOVING THIS LINE FROM mkdocs.yml IS NOT A NO-OP. Every `!!! tally`, `!!! form`,
`!!! chain` and `!!! export` would render as an ordinary grey admonition titled
"tally", "form", "chain" or "export" -- a box where a compliance form or a box office
sheet should be -- every flow strip would silently
stop rendering while `chain:` kept working perfectly, which now means a program page
with `hide: footer` would have NO navigation at all, AND no `packets.json` would be
written, so **every packet PDF would vanish from the next deploy and every export
button would 404.** Same shape as 03c and 03d.
"""

from docrender import binder, cards, chainlist, forms, packet, program, tally


def on_page_markdown(markdown, page, config, files):
    """All five body directives, in one registration. See the red block above."""
    markdown = tally.on_page_markdown(markdown, page, config, files)
    markdown = cards.on_page_markdown(markdown, page, config, files)
    markdown = forms.on_page_markdown(markdown, page, config, files)
    markdown = chainlist.on_page_markdown(markdown, page, config, files)
    return packet.on_page_markdown(markdown, page, config, files)


def on_page_content(html, page, config, files):
    """Flow strips, then the packet button beneath them. The order is a rule."""
    html = program.on_page_content(html, page, config, files)
    return packet.on_page_content(html, page, config, files)


def on_nav(nav, config, files):
    """Packet plan, then binder plan. Independent of each other; order free."""
    nav = packet.on_nav(nav, config, files)
    return binder.on_nav(nav, config, files)


def on_post_build(config):
    """`packets.json`, then `binders.json`. Neither reads the other."""
    packet.on_post_build(config)
    binder.on_post_build(config)
