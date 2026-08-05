"""Stage 00bc -- seal routed subtrees out of the sidebar.

MUST sit between `00bb_navstate.py` and `00c_nav.py`, and the position is the
whole reason this stage exists as its own file.

The seal was pass 3 of `visibility.prune_nav` at 00b until 2026-08-05. From
there it harvested a routed folder's subtree into the sealed nav manifest BEFORE
navstate reached 00bb -- so a `nav: hidden` folder inside a routed folder was
sealed with its children still in it, and a correct router code injected them
straight back into the sidebar. Live on uritp: `courses/` is routed, and all 43
pages under `courses/course-info/` came back for anyone holding the code.

Splitting the function was the fix. `visibility.seal_nav` carries the full
account and the five-stage chain; `docrender/navstate.py` sets the flag this
stage checks.

⚠️ AND `00bc`, NOT `00b3`. `_` sorts after a digit and before a letter, so a
digit suffix would sort ahead of `00bb_navstate.py` on disk while running behind
it in mkdocs.yml -- the filesystem and the config disagreeing about order, in the
one directory whose entire premise is that the filename carries the order. Same
trap `00bb` was named to avoid. See hooks/README.md.

Thin on purpose: `visibility` owns the prune and the seal both, so unlike
`00bb_navstate.py` there is nothing to wire across modules here. This file holds
exactly one fact, and it is WHERE.
"""

from docrender.visibility import seal_nav as on_nav  # noqa: F401
