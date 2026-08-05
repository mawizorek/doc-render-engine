"""Stage 06b -- open the folders that declared `nav: expanded`.

The second half of `docrender/navstate.py`. 00bb decided WHICH folders open;
this writes the one attribute Material uses to say so, on the way out.

⚠️ `on_post_page` HAS NO OTHER CLAIMANT IN THIS ENGINE, so unlike 00b/00bb/00c
this number is for a reader rather than for the runtime. It sits at 06b because
06 is the last stage that touches a single page's output and 07 onward describe
the finished site. If a second `on_post_page` ever appears, the order between
them becomes real and this comment stops being true.
"""

from docrender.navstate import on_post_page  # noqa: F401
