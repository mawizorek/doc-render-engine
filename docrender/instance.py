"""Hook 00 -- become this site.

The engine starts every build as nobody. This reads instances/<slug>/site.yml
and applies it: name, URL, source repo, edit target, palette, section titles
and order.

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
    #
    # The publishing path knows its own address, so it passes it in. site.yml
    # keeps the canonical one for humans reading the config.
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

    repo = inst.get("content_repo")
    if repo:
        config.repo_url = f"https://github.com/{repo}"
        config.repo_name = repo
        config.edit_uri = f"edit/{inst.get('content_branch', 'main')}/"

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


def on_nav(nav, config, files):
    """Order the sidebar from frontmatter and instance config.

    Nav order is the hardest problem a pure content repo has: the usual answer
    is a manifest inside the content tree, which is precisely what the content
    tree may not contain. So order comes from the two places allowed to hold it
    -- a page's own `order:` frontmatter, and the instance's `sections:` block,
    which lives with the app.

    Unranked items sort after ranked ones, alphabetically, so a brand new page
    always lands somewhere sane rather than at a random position.
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
        key = (getattr(item, "title", "") or "").lower()
        return ((sections.get(key) or {}).get("order", 10_000), key)

    def walk(items):
        for item in items:
            if getattr(item, "is_section", False):
                cfg = sections.get((item.title or "").lower()) or {}
                if getattr(item, "children", None):
                    walk(item.children)
                    item.children.sort(key=rank)
                if cfg.get("title"):
                    item.title = cfg["title"]
                elif item.title:
                    item.title = slug_title(item.title)

    walk(nav.items)
    nav.items.sort(key=rank)
    return nav
