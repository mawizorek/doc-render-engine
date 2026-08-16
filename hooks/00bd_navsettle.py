"""Stage 00bd -- spend the `navigation.prune` budget on folders that SURVIVED.

MUST sit between `00bc_seal.py` and `00c_nav.py`. The seal is the last stage that
removes a section from the tree, so this is the first moment the question *does
any folder still standing want to be open* has a final answer.

Move it before 00bc and it reads a provisional tree: a folder sealed behind a
router still counts as expanded, the site loses `navigation.prune` for a row no
reader can click, and every page pays ~33% of its weight for it. That was the
live behaviour until 2026-08-16 -- see docrender/navsettle.py for the account and
the uritp instance that exposed it.

Also move it before 00bc and the report LIES in the other direction: it would
name folders as dropped that the seal had not reached yet.

00bd FOLLOWS THE LETTER SEQUENCE, NOT A DIGIT. `_` sorts after a digit and before
a letter, so a `00bc2_` stage would sort ahead of `00bc_seal.py` on disk while
running after it in mkdocs.yml. hooks/README.md carries the rule; this is its
third instance after `00bb` and `00bc`.

AND IT IS A THIN SHIM AGAIN, WHICH IS THE POINT. `00bb_navstate.py` is thick
because `navstate` cannot import `visibility` without a cycle. `navsettle` can --
nothing imports it back -- so the wiring stays in the module where it belongs and
this file only carries WHEN.
"""

from docrender import navsettle


def on_nav(nav, config, files):
    navsettle.settle(nav.items, config)
    return nav
