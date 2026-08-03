"""Stage 00b -- remove `unlisted` pages from the sidebar.

MUST sit between `00_instance.py` and `00c_nav.py` in mkdocs.yml. 00 sorts the
tree, this prunes it, 00c rewires prev/next from what is left. Move this after
00c and the footer Next button starts walking through pages that are not in the
sidebar.

The logic lives in visibility.py with the rest of the publication gate, because
this is the same decision as `status:` and not a navigation feature. It is only
a separate hook file because MkDocs orders same-named events by hook file, so
the ORDER has to be expressed as a filename.
"""

from docrender.visibility import prune_nav as on_nav  # noqa: F401
