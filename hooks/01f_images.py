"""Stage 01f -- the `@img:` image index.

    ![The H5 front panel](@img:h5-front){ caption="Power is on the LEFT." }

ONE EVENT:

  on_files   index every image in the content tree by the stem of its filename

⚠️ THE MODULE IMPORT IS ITSELF LOAD-BEARING AND MUST NOT BE TIDIED AWAY.
Importing `docrender.images` is what executes `prefixes.claim("img", ...)` at
module load. Without it the namespace does not exist, `links.py` falls through
to peer lookup, and every `@img:` reference reports **"unknown peer site: img"**
-- the wrong subsystem named on a page that is perfectly correct, which is the
exact failure `docrender/prefixes.py` was written to end. Both names below are
real; neither is decorative.

⚠️ ORDERING IS FREE HERE, AND THAT IS WORTH STATING SO NOBODY GUARDS IT. The
claim happens at hook IMPORT, before any event. The index is built in
`on_files`, and MkDocs runs every hook's `on_files` before any hook's
`on_page_markdown` -- so `links.py` at stage 03 cannot see a half-built index no
matter where this line sits in the list.

It is at 01f anyway, beside `01e_figure`, because to a reader they are one
feature: 01e wraps a captioned image, 01f knows where the image is.

Letter, not digit, per hooks/README.md -- `_` sorts after a digit and before a
letter, so `01e2_` would sort ahead of `01e_` on disk while running after it in
the config. `01e` is taken; this is `01f`.
"""

from docrender import images  # noqa: F401  -- the import IS the claim
from docrender.images import on_files  # noqa: F401
