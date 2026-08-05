"""Stage 00bb -- apply the `nav:` key to the sidebar tree.

MUST sit between `00b_unlisted.py` and `00c_nav.py`. 00b prunes unlisted pages
and seals routed subtrees, this applies `nav: hidden` and resolves the
expanded/collapsed cascade, 00c rewires prev/next from what is left. Move this
after 00c and a hidden page keeps a footer Next button pointing into a chain it
is no longer in.

⚠️ `00bb` RATHER THAN `00b2` ON PURPOSE. `_` sorts AFTER a digit and BEFORE a
letter, so `00b2_navstate.py` would sort ahead of `00b_unlisted.py` on disk
while running after it in mkdocs.yml -- two orderings that disagree, in a
directory whose entire premise is that the filename carries the order. `00bb`
sorts and runs in the same place.

⚠️ THIS SHIM IS THICKER THAN THE OTHERS AND THAT IS THE JOB. `navstate` needs
two functions that belong to `visibility`: `_index_of`, which returns the index
each section had BEFORE pruning, and `_unchain`, the prev/next detachment every
removal owes. `visibility` cannot hand them over directly -- it would have to
import `navstate` to call it, and `navstate` importing back is a cycle. So the
wiring lives here, which is what these files are for: the package holds the
LOGIC, hooks/ holds the ORDER, and this one also holds the one edge where two
stages of the same event have to see each other.
"""

from docrender import navstate
from docrender.visibility import _index_of, _unchain


def on_nav(nav, config, files):
    navstate.shape(nav.items, config, _index_of, _unchain)
    return nav
