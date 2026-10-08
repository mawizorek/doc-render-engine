"""Stage 01f -- the `@img:` image index, and the screen header mark it feeds.

    ![The H5 front panel](@img:h5-front){ caption="Power is on the LEFT." }

ONE EVENT, TWO JOBS, IN THIS ORDER:

  on_files   1. index every image in the content tree by the stem of its filename
             2. resolve the site's `logo:` stem against that index and point
                Material's header logo + favicon at it (docrender/sitemark.py)

⚠️ THE MODULE IMPORT IS ITSELF LOAD-BEARING AND MUST NOT BE TIDIED AWAY.
Importing `docrender.images` is what executes `prefixes.claim("img", ...)` at
module load. Without it the namespace does not exist, `links.py` falls through
to peer lookup, and every `@img:` reference reports **"unknown peer site: img"**
-- the wrong subsystem named on a page that is perfectly correct, which is the
exact failure `docrender/prefixes.py` was written to end.

⭐ WHY THE SITE MARK RIDES THIS SHIM INSTEAD OF A STAGE OF ITS OWN (2026-10-08).
It needs the finished index, and the index exists the instant `images.on_files`
returns, so the sitemark call goes HERE, after it, in the same event. A separate
`01g` shim would have meant editing the registration list in mkdocs.yml for a
stage whose position is not free -- it must follow 01f -- and this placement
makes the ordering impossible to get wrong rather than merely documented. This
is the second shim with real code in it (00bb is the first) and for the same
kind of reason: wiring belongs in the shim, logic in the module.

⚠️ ORDERING OF 01f ITSELF IS STILL FREE. The `@img:` claim happens at hook
IMPORT, and MkDocs runs every hook's `on_files` before any hook's
`on_page_markdown`. `theme.logo` is read at TEMPLATE render, which is later still.

Letter, not digit, per hooks/README.md.
"""

from docrender import images  # noqa: F401  -- the import IS the claim
from docrender import sitemark


def on_files(files, config):
    files = images.on_files(files, config)
    sitemark.apply(config)
    return files
