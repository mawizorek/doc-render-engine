"""Stage 01f (second half) -- the SCREEN header mark, named once per site.

    logo: <stem>          in instances/<slug>/site.yml

Michael, 2026-10-08: an app icon for a site "that we can add to the repo and
render in the header." The PRINTED header already had a per-site mark
(`print: logo:`, docrender/buildstamp.py). The SCREEN header did not: Material's
`md-logo` drew its default book icon on every site, because nothing in the engine
ever set `theme.logo`. This module is that missing key and nothing else.


THE VALUE IS A STEM, RESOLVED THROUGH THE `@img:` INDEX
=======================================================

Same contract as `print: logo:` and `@img:`, deliberately: the stem of an image
filename anywhere in the CONTENT tree, never a path and never an extension. So
the file can move inside the content repo and this key never has to know.

That is also why it lives BESIDE images.py rather than in instance.py: it needs
`images.INDEX`, which is built in `on_files`, so it cannot run in `on_config`.
(instance.py is past its own warn line and says the next feature gets a module.)


WHAT IT SETS
============

`theme.logo` and `theme.favicon`, both to the resolved image URL. Material passes
each through its `url` filter, so the header and the browser tab both resolve
correctly at every page depth with no arithmetic here.


POLARITY: ABSENT MEANS OFF
==========================

No `logo:` key -> nothing is touched and the site renders exactly as before,
Material's default icon included. Same polarity as `print:`, `owner:` and
`routes.yml`. A site opts IN; no site is changed by this landing except the one
that declares it.


FAILURES ARE REPORTED, NEVER GUESSED
====================================

- A stem naming no image -> reported, theme untouched.
- A stem shared by two images -> reported, theme untouched. Two pictures with
  one name are two different pictures (images.py's founding rule).

Both leave the default icon on screen, which is visible and harmless, rather than
the wrong picture, which is neither.


NOT THE PRINTED MARK
====================

`assets/print-chrome.css` strips `.md-header` from paper, so this key never
prints. The printed mark is `print: logo:`. A site may name the same stem in
both places; they are separate keys because screen and paper are separate
surfaces and a site may want different marks on each.
"""

from __future__ import annotations

from . import images, state


def apply(config) -> None:
    """Point Material's header logo and favicon at this site's declared mark."""
    raw = state.INSTANCE.get("logo")
    if not raw:
        return

    slug = state.INSTANCE.get("slug", "?")
    stem = str(raw).strip().lower()
    if "." in stem:
        stem = stem.rsplit(".", 1)[0]

    if stem in images.COLLISIONS:
        state.note(
            "missing_required",
            "instances/" + slug + "/site.yml `logo: " + str(raw) + "` is "
            "ambiguous: " + str(len(images.COLLISIONS[stem])) + " images share "
            "that stem (" + ", ".join(images.COLLISIONS[stem]) + "). The screen "
            "header keeps the default icon until one is renamed.",
        )
        return

    hit = images.INDEX.get(stem)
    if not hit:
        state.note(
            "missing_required",
            "instances/" + slug + "/site.yml `logo: " + str(raw) + "` names no "
            "image in the content tree. The screen header keeps the default "
            "icon. The value is the STEM of a filename, resolved like @img:.",
        )
        return

    url = hit["url"]
    config.theme["logo"] = url
    config.theme["favicon"] = url
    state.note(
        "notes",
        "SCREEN HEADER MARK: `" + stem + "` -> " + hit["src"] + " (theme.logo "
        "+ theme.favicon).",
    )
