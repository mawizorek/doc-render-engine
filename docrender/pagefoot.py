"""Hook 06 -- the edit link, at the foot, in words.

One quiet text link at the bottom of every page:

    ----------------------------------------
    Edit this page on GitHub

WHY IT IS NOT THE THEME'S PENCIL (inherited from v1, 2026-08-01). Material's
`content.action.edit` puts a pencil at the top right, level with the title.
That reads as an invitation -- this document is editable, have a go -- on a
site whose whole job is to be the settled answer. There is one editor, and the
affordance he needs is a way back to the source once he has finished reading,
not a button competing with the heading.

IT ALSO FIXES A REAL DEFECT, which is why it is a link with WORDS. The pencil
is an anchor with no text and no label, so a screen reader announces the URL.
'Edit this page on GitHub' is self-describing, survives being read aloud, and
works without an icon font.

`page.edit_url` is computed by MkDocs from repo_url + edit_uri, which
instance.py sets from the content repo. It therefore stays correct when the
repo moves or is renamed. A page with no edit_url -- anything generated --
simply gets no link rather than a broken one.

Kill switch: DOCRENDER_EDITLINK=0 in the build environment.
"""

from __future__ import annotations

import os

LABEL = "Edit this page on GitHub"


def on_page_content(html, page, config, files):
    if os.environ.get("DOCRENDER_EDITLINK") == "0":
        return html

    url = getattr(page, "edit_url", None)
    if not url:
        return html

    return (
        html
        + '<hr class="pagefoot__rule">'
        + '<p class="pagefoot">'
        + '<a class="pagefoot__edit" href="' + url + '">' + LABEL + "</a>"
        + "</p>"
    )
