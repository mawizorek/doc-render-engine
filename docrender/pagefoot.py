"""Hook 06 -- the edit link, at the foot, in words, and switchable off.

One quiet text line at the bottom of every page:

    ----------------------------------------
    Edit this page on GitHub

WHY IT IS NOT THE THEME'S PENCIL (inherited from v1). Material's
`content.action.edit` puts a pencil at the top right, level with the title.
That reads as an invitation -- this document is editable, have a go -- on a
site whose whole job is to be the settled answer. It is also an anchor with no
text and no label, so a screen reader announces the URL. 'Edit this page on
GitHub' is self-describing and survives being read aloud.

⭐ WHY THIS BUILDS THE URL ITSELF (2026-08-03). MkDocs derives `page.edit_url`
from `repo_url`, and setting `repo_url` also plants a repository widget in the
header -- owner/name, star count, fork count. Michael's rule is that the
rendered docs must not advertise or invite access back to the source, so
`repo_url` is now unset (see instance.py) and the edit link is composed here
from `content_repo` instead.

That decoupling is the feature: the header can stay clean while the one
developer-facing line survives at the foot, and either can be switched without
dragging the other with it.

🔀 THE SWITCH, for when these go out to real readers:

    edit_links: false     in instances/<slug>/site.yml

One line, per site, and every trace of the repository leaves the rendered
output. The intent is on record: the edit line is scaffolding for now, and
nothing about a finished site should point back at git.

Environment override for a one-off build: DOCRENDER_EDITLINK=0.
"""

from __future__ import annotations

import os

from . import state

LABEL = "Edit this page on GitHub"


def _enabled() -> bool:
    if os.environ.get("DOCRENDER_EDITLINK") == "0":
        return False
    # Default ON, so a site keeps the link until it deliberately opts out.
    return state.INSTANCE.get("edit_links", True) is not False


def on_page_content(html, page, config, files):
    if not _enabled():
        return html

    repo = state.INSTANCE.get("content_repo")
    if not repo:
        return html

    # Generated pages have no source file to edit.
    src = getattr(page.file, "src_uri", "")
    if not src or not src.endswith(".md"):
        return html

    branch = state.INSTANCE.get("content_branch", "main")
    url = "https://github.com/" + repo + "/edit/" + branch + "/" + src

    return (
        html
        + '<hr class="pagefoot__rule">'
        + '<p class="pagefoot">'
        + '<a class="pagefoot__edit" href="' + url + '">' + LABEL + "</a>"
        + "</p>"
    )
