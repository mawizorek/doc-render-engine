"""Hook 00 -- become this site.

The engine starts every build as nobody. This reads instances/<slug>/site.yml
and applies it: name, URL, edit target, palette, section titles and order.

This file is what makes "one app, many sites" literally true rather than
aspirational. There is exactly one place a site's identity enters a build, and
it is a data file the engine READS, not code the engine CONTAINS.

THE CHROME-COLOUR TRAP (inherited from v1, and the reason primary/accent are
set here rather than in a stylesheet): Material's header and sidebar colour
comes from `theme.palette`, not from CSS custom properties. Setting
`--md-primary-fg-color` in an unscoped `:root` looks like it works, hits BOTH
colour schemes at once, and silently breaks the dark toggle. So chrome is
config and only finer detail is CSS. That split is not cosmetic and it cost
real time to learn the first time.

🚫 THE SITE NEVER ADVERTISES ITS REPOSITORY (LOCKED 2026-08-03, Michael).
`repo_url` is deliberately NOT set. Setting it makes Material render a repo
widget in the header with the owner/name and a star count, and these are
reference documents for designers and guest artists -- not a project asking
for contributors. A reader looking up a grid height should never be invited to
fork anything.

The consequence is that `page.edit_url`, which MkDocs derives from `repo_url`,
is empty. That is handled where it belongs: pagefoot.py builds the edit link
itself from `content_repo`, so the one quiet line at the foot survives while
the header stays clean. The two used to be the same switch; they are not any
more, which is the entire point of the change.
"""

from __future__ import annotations

import os
import sys

from . import state
from .util import load_yaml, slug_title


def _fail(message: str) -> None:
    print(f"::error::docrender: {message}", file=sys.stderr)
    raise SystemExit(1)


def on_config(config):
    state.reset()

    slug = os.environ.get("DOCRENDER_INSTANCE", "").strip()
    if not slug:
        _fail(
            "DOCRENDER_INSTANCE is not set. The engine has no default site and "
            "must never guess one."
        )

    inst_dir = state.ENGINE_ROOT / "instances" / slug
    inst = load_yaml(inst_dir / "site.yml")
    if not inst:
        known = sorted(
            p.name for p in (state.ENGINE_ROOT / "instances").glob("*") if p.is_dir()
        )
        _fail(
            f"no instance '{slug}': instances/{slug}/site.yml is missing or "
            f"empty. Known instances: {', '.join(known) or 'none'}"
        )

    inst["slug"] = slug
    inst["dir"] = str(inst_dir)

    # ADDRESS IS A PROPERTY OF THE PUBLISHING PATH, NOT OF THE SITE.
    #
    # The same instance can be published to more than one address: the matrix
    # pushes it to its own content repo's Pages, while the default-publish
    # workflow serves it from the engine's Pages at an entirely different URL.
    # site.yml can only state one of those, so whichever it states is wrong for
    # the other path -- and a wrong base_url is not cosmetic. It is written
    # into doc-index.json, which is the one file every SIBLING site reads to
    # resolve cross-site links, so a stale value sends other people's readers
    # somewhere that does not exist.
    override = os.environ.get("DOCRENDER_BASE_URL", "").strip()
    if override:
        inst["base_url"] = override

    state.INSTANCE = inst

    # Object declarations are shared across every site by design: a `space`
    # means the same thing everywhere, or the family has no shared vocabulary.
    for path in sorted((state.ENGINE_ROOT / "objects").glob("*.yml")):
        decl = load_yaml(path)
        state.TYPES[decl.get("type") or path.stem] = decl

    config.site_name = inst.get("name", slug)
    config.site_description = inst.get("description", "")
    if inst.get("base_url"):
        config.site_url = inst["base_url"]

    # 🚫 repo_url / repo_name / edit_uri are NOT set. See the module docstring.
    # If you set them to "fix" the edit link, you also put the repo widget back
    # in the header, which is the thing that was explicitly removed.

    palette = inst.get("palette") or {}
    for scheme in (config.theme.get("palette") or []):
        if not isinstance(scheme, dict):
            continue
        chosen = palette.get("dark" if scheme.get("scheme") == "slate" else "light") or {}
        if chosen.get("primary"):
            scheme["primary"] = chosen["primary"]
        if chosen.get("accent"):
            scheme["accent"] = chosen["accent"]

    return config


def _index_of(section):
    """The index page inside a section, if it has one."""
    for child in getattr(section, "children", None) or []:
        if getattr(child, "is_page", False) and child.file.name == "index":
            return child
    return None


def on_nav(nav, config, files):
    """Order the sidebar, and let a folder be named by the page inside it.

    Two problems solved here, and the second is the one that shows.

    ORDER. A pure content repo cannot hold a nav manifest -- that is machinery,
    and machinery is what the content tree may not contain. So order comes from
    the two places allowed to hold it: a page's own `order:` frontmatter, and
    the instance's `sections:` block, which lives with the app. Unranked items
    sort after ranked ones, alphabetically, so a new page always lands
    somewhere sane rather than at a random position.

    TITLES. MkDocs names a folder after the FOLDER, so `venues/spac/` shows up
    in the sidebar as "Spac" even though the page inside it is called Swan
    Auditorium. That is not a cosmetic mismatch: the sidebar and the page
    disagree about what a place is called, and the reader has to work out that
    they are the same thing. So a section takes the title of its own index
    page, when it has one. Failing that, the instance can name it. Failing
    that, the folder slug is prettified as a last resort.

    The precedence is deliberate: the CONTENT names itself first, config only
    covers folders with no index page, and the folder name is the fallback
    nobody should have to rely on.
    """
    sections = {k.lower(): v for k, v in (state.INSTANCE.get("sections") or {}).items()}

    def rank(item):
        if getattr(item, "is_page", False):
            meta = state.BY_SRC.get(item.file.src_uri, {})
            if item.file.name == "index":
                return (-1, "")
            order = meta.get("order")
            title = meta.get("title") or item.title or ""
            return (order if isinstance(order, int) else 10_000, str(title).lower())

        # A section sorts by its config entry, or by its index page's `order:`.
        key = (getattr(item, "_dr_slug", "") or getattr(item, "title", "") or "").lower()
        cfg = sections.get(key) or {}
        if "order" in cfg:
            return (cfg["order"], key)
        index = _index_of(item)
        if index is not None:
            order = state.BY_SRC.get(index.file.src_uri, {}).get("order")
            if isinstance(order, int):
                return (order, key)
        return (10_000, key)

    def walk(items):
        for item in items:
            if not getattr(item, "is_section", False):
                continue

            # Remember the folder name before renaming, so config lookups and
            # sorting keep working against a stable key.
            slug = (item.title or "").lower()
            item._dr_slug = slug

            if getattr(item, "children", None):
                walk(item.children)
                item.children.sort(key=rank)

            index = _index_of(item)
            cfg = sections.get(slug) or {}
            if index is not None:
                meta = state.BY_SRC.get(index.file.src_uri, {})
                item.title = meta.get("title") or index.title or slug_title(slug)
            elif cfg.get("title"):
                item.title = cfg["title"]
            elif item.title:
                item.title = slug_title(item.title)

    walk(nav.items)
    nav.items.sort(key=rank)
    return nav
