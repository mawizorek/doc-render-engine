"""Hook 00 -- become this site.

The engine starts every build as nobody. This reads instances/<slug>/site.yml
and applies it: name, URL, edit target, section titles and order.

This file is what makes "one app, many sites" literally true rather than
aspirational. There is exactly one place a site's identity enters a build, and
it is a data file the engine READS, not code the engine CONTAINS.

⭐ AND AS OF 2026-08-06 IT ALSO ASKS WHERE THE DESIGN SYSTEM CAME FROM. See the
end of `on_config`. That question belongs to the BUILD -- like the name and the
address above it -- rather than to the stylesheet generated from the answer, and
this is the only hook that runs exactly once.

⭐ AND AS OF 2026-08-07 A PUBLISH MAY OVERRIDE THE THEME. `DOCRENDER_THEME`
joins `DOCRENDER_BASE_URL` below as a fact site.yml owns that the PUBLISHING
PATH may override for the length of one build. `_theme_override` says why it
has to happen in this file specifically and nowhere else -- the short version
is that hook 00 is the only place in the pipeline that runs exactly once, and a
value that is allowed to be RANDOM must be decided somewhere that cannot be
asked twice.

CHROME COLOUR IS NO LONGER SET HERE (2026-08-04), and the reversal is worth
keeping because the reasoning it replaces was half right.

This file used to copy `palette.primary` and `palette.accent` out of site.yml
onto Material's theme config, and its docstring defended that: Material's header
and sidebar colour comes from `theme.palette`, and setting
`--md-primary-fg-color` in an UNSCOPED `:root` looks like it works, hits BOTH
colour schemes at once, and silently breaks the dark toggle.

Every sentence of that is still true. The CONCLUSION was wrong. It read a
SCOPING problem as a FILE-PLACEMENT problem -- and `assets/base.css` has been
setting every other Material variable inside a `[data-md-color-scheme]` block
for months, so the trap was already solved over there. Chrome simply never
moved with the rest.

What that cost, measured rather than argued:

  1. A named Material colour cannot be read from a table, so a canonical theme
     could never reach the header. site.yml carried `accent: amber` under the
     comment "Kept in step with the eos accent by hand" -- a documented manual
     mirror, which went out of step the instant the palette became canonical.

  2. Worse, and invisible for weeks: setting `palette.primary` is what makes
     Material emit `data-md-color-primary` on the body, and Material ships
     `[data-md-color-scheme="slate"][data-md-color-primary="black"]` -- two
     attribute selectors -- which outranked base.css's single-attribute scheme
     scope and repainted every dark-mode link and active nav row BLUE. Light
     mode was unaffected, so one declaration in one file produced two different
     answers depending on the scheme.

So the loop is gone rather than trimmed, and the attribute is never emitted, so
the override has nothing to hang from. The `palette:` block in mkdocs.yml stays:
it carries the light/dark TOGGLE, which is a real feature and not a colour.

A `palette:` key left in an instance's site.yml is now inert. It is reported, not
silently ignored -- a config key that does nothing while looking like it does
something is the failure this engine keeps writing down.

⭐ AND THAT LAST SENTENCE IS WHY `aliases:` IS READ HERE (2026-08-05). The only
CONSUMER of an alias is the `publish` shell helper, which resolves a typed name
to a slug before it dispatches the workflow. Nothing in the engine needs one to
render a page. Left unread, the block would have been precisely the defect the
paragraph above condemns: a config key that looks live and is not. So this file
normalises them, checks them against the rest of the family, and prints them in
the build report -- which makes the key demonstrably live, and puts a typo in
front of a human on the next build rather than at a command line.

NO ROUTE BACK TO THE SOURCE (LOCKED 2026-08-03, Michael).
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
import random
import sys

from . import state, vectors
from .util import load_yaml, slug_title


def _fail(message: str) -> None:
    print(f"::error::docrender: {message}", file=sys.stderr)
    raise SystemExit(1)


def _theme_override(inst: dict, slug: str) -> None:
    """`DOCRENDER_THEME` -- let ONE publish choose the theme, editing nothing.

    Michael, 2026-08-07: *"what would it take for our publish command to accept
    an additional variable that lets me set the theme at the last minute... I'd
    like to avoid switching between the renderer to define the theme, and I want
    to be able to push publishes with random themes just to debug better."*

    Same shape as `DOCRENDER_BASE_URL` in `on_config` and `DOCRENDER_EDITLINK`
    in pagefoot.py: a fact site.yml owns, overridden by the publishing PATH for
    the length of one build. **Nothing is written to disk**, so the override
    cannot outlive the run that asked for it, and the next ordinary publish
    renders the declared theme with no cleanup step to forget.

    An UNSET or EMPTY variable returns immediately and this build is byte for
    byte the build it would have been. That is not politeness, it is the whole
    safety property: an input nobody filled in must never be why a site
    suddenly looks different.

    =========================================================================
    🔴 IT HAS TO HAPPEN IN THIS FILE, AND THE REASON IS THE FINGERPRINT
    =========================================================================
    The obvious home is `vectors._declared()`, which is the ONE place the theme
    is read. That is exactly where this would have broken.

    `_declared()` is called once PER SCHEME, and `theme.build_css()` runs TWO OR
    THREE TIMES PER BUILD -- `assets._plan()` calls it from BOTH `on_config` and
    `on_files`, and tokenaudit calls it again on any page carrying a
    `!!! tokens` block. Reading a fixed env var there would be harmless.
    ROLLING A RANDOM ONE there is not: every call answers differently, so the
    dark scheme and the light scheme would come from different themes.

    ⚠️ AND THE REAL DAMAGE IS NOT THE MISMATCHED TOGGLE. `assets._plan()` names
    every generated sheet by a CONTENT FINGERPRINT: `on_config` hashes the CSS
    to build the URL it links, and `on_files` hashes it again to publish the
    file. Two different rolls give two different hashes, so every page would
    link `tokens.<a>.css` while the site contained `tokens.<b>.css`. **Every
    custom property on every page gone, behind a 404 nobody opens, with no
    error and no report line** -- and it would look like a theme bug rather
    than a caching one.

    Hook 00 runs exactly ONCE per build, before any other hook reads a vector.
    Deciding here means the answer exists before anything can ask, and every
    later reader -- both schemes, all three `build_css()` calls -- sees the one
    value. ⚠️ `mkdocs serve` re-runs `on_config` per rebuild, so a served
    session re-rolls; each rebuild is internally consistent, which is the
    property that matters.

    =========================================================================
    A BAD NAME IS DISCARDED, NOT SUBSTITUTED
    =========================================================================
    `vectors.resolve()` already falls an unknown theme back to `base` and says
    so, and that is RIGHT for a value somebody committed to site.yml -- a typo
    in a tracked file should still render a readable site.

    An override is a different kind of value: it was typed into a box thirty
    seconds ago by somebody standing there watching the run. Falling back to
    `base` would answer a typo with a THIRD theme -- neither what was typed nor
    what the site declares -- and send the reader hunting a palette bug. So a
    name outside `vectors.known()` is REFUSED, the declared theme renders
    untouched, and the report prints the legal set. Nothing substituted,
    nothing lost, one line to read.

    ⚠️ `random` ROLLS FROM `known()`, THE SAME SET AN EXPLICIT NAME IS CHECKED
    AGAINST -- deliberately one set rather than two. That includes bare colour
    entities, which resolve to a palette with no join; vectors.py already
    reports that by name when it happens, so the roulette inherits an
    explanation instead of needing its own. A second, narrower "only REAL
    themes" list would be another place stating what a theme is, which is the
    defect this repo has retired three manifests over.
    """
    raw = os.environ.get("DOCRENDER_THEME", "").strip()
    if not raw:
        return

    declared = inst.get("theme", "base")
    legal = vectors.known()

    if raw.lower() == "random":
        pool = sorted(legal)
        if not pool:
            state.note(
                "missing_required",
                "DOCRENDER_THEME=random, but NO theme names could be read at "
                "all -- not a canonical join, not a colour entity, not a local "
                "skin. The design system is unreachable AND theme/themes.tsv "
                "could not be read. Keeping the declared theme "
                + str(declared) + ".",
            )
            return
        pick = random.choice(pool)
        why = "rolled at random from " + str(len(pool)) + " legal names"
    else:
        pick = raw
        if pick not in legal:
            state.note(
                "missing_required",
                "DOCRENDER_THEME is '" + raw + "', which is not a join, a "
                "colour entity or a local theme. THE OVERRIDE IS DISCARDED and "
                "nothing is substituted -- this build renders the theme "
                "instances/" + slug + "/site.yml declares (" + str(declared)
                + "). Legal names: " + ", ".join(sorted(legal)) + ".",
            )
            return
        why = "named on the publish"

    inst["theme"] = pick
    state.note(
        "notes",
        "THEME OVERRIDDEN FOR THIS BUILD ONLY: '" + pick + "', " + why
        + ". instances/" + slug + "/site.yml still declares " + str(declared)
        + " and was NOT edited -- the next publish with an empty `theme` input "
        "renders it again.",
    )


def _register_aliases(inst: dict, slug: str) -> None:
    """Normalise this site's command-line aliases and prove they resolve here.

    An alias is an extra NAME the `publish` helper accepts for this site --
    the content repo's name, a house abbreviation, a retired slug. The engine
    never uses one; see the ⭐ block in the module docstring for why it reads
    them anyway.

    ⚠️ AN ALIAS IS AN IDENTIFIER, NOT A TITLE, and the distinction is the whole
    reason the block exists. `name:` is prose and gets edited; a command bound
    to prose breaks when somebody improves a heading. An alias is allowed to
    LOOK like a title while being immutable in practice, because nothing
    renders it.

    WARNS, NEVER FAILS. Only the portability leak fails a build. A bad alias
    cannot render a wrong page -- the worst it does is fail to resolve, which
    the resolver reports at the command line with the real list.
    """
    mine: list[str] = []
    for raw in inst.get("aliases") or []:
        alias = str(raw).strip().lower()
        if not alias:
            continue
        if alias == slug:
            state.note(
                "notes",
                "instances/" + slug + "/site.yml lists '" + alias + "' as an "
                "alias, which is this site's own slug. It already resolves; "
                "the line adds nothing.",
            )
            continue
        if alias in mine:
            state.note(
                "notes",
                "instances/" + slug + "/site.yml lists the alias '" + alias
                + "' twice (case-insensitively).",
            )
            continue
        mine.append(alias)

    inst["aliases"] = mine

    # Everybody else's slug and claims, so a name is checked against the FAMILY
    # rather than trusted. Reading sibling instance data is not a portability
    # violation: it is the engine reading its own config tree generically, with
    # no site named in code.
    others: dict[str, list[str]] = {}
    for path in sorted((state.ENGINE_ROOT / "instances").glob("*/site.yml")):
        other = path.parent.name
        if other == slug:
            continue
        decl = load_yaml(path) or {}
        others[other] = [
            str(a).strip().lower() for a in (decl.get("aliases") or []) if str(a).strip()
        ]

    for alias in mine:
        # An alias equal to ANOTHER site's slug is the dangerous one: the
        # resolver checks slugs first, so this name silently publishes the
        # wrong site and never once looks wrong.
        if alias in others:
            state.note(
                "notes",
                "ALIAS COLLISION: '" + alias + "' is declared here but is the "
                "SLUG of instance '" + alias + "'. A resolver checks slugs "
                "first, so this name publishes THAT site, not this one. "
                "Rename or remove it.",
            )
        for other, their in others.items():
            if alias in their:
                state.note(
                    "notes",
                    "ALIAS COLLISION: '" + alias + "' is claimed by both '"
                    + slug + "' and '" + other + "'. Whichever is read first "
                    "wins, which makes the target of that name a coin flip.",
                )

    if mine:
        state.note(
            "aliases",
            "`" + slug + "` (the slug) plus " + str(len(mine)) + ": "
            + ", ".join("'" + a + "'" for a in mine),
        )
    else:
        state.note(
            "aliases",
            "none declared -- `" + slug + "` is the only name that resolves to "
            "this site.",
        )


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

    # LOOK IS ALSO A PROPERTY OF THE PUBLISHING PATH, FOR ONE BUILD (2026-08-07).
    #
    # Placed here, after state.INSTANCE is bound, for two reasons that are not
    # interchangeable: `state.note` needs the report to exist, and every later
    # reader of the theme must see the SAME answer -- which is only guaranteed
    # in the one hook that runs exactly once. See `_theme_override`.
    _theme_override(inst, slug)

    # Object declarations are shared across every site by design: a `space`
    # means the same thing everywhere, or the family has no shared vocabulary.
    for path in sorted((state.ENGINE_ROOT / "objects").glob("*.yml")):
        decl = load_yaml(path)
        state.TYPES[decl.get("type") or path.stem] = decl

    config.site_name = inst.get("name", slug)
    config.site_description = inst.get("description", "")
    if inst.get("base_url"):
        config.site_url = inst["base_url"]

    # repo_url / repo_name / edit_uri are NOT set. See the module docstring.
    # If you set them to "fix" the edit link, you also put the repo widget back
    # in the header, which is the thing that was explicitly removed.

    # CHROME IS CANONICAL. Nothing is copied onto theme.palette any more -- see
    # the module docstring for what the old loop cost. Reported rather than
    # ignored, because a key that looks live and is not is worse than an error.
    if inst.get("palette"):
        state.note(
            "notes",
            "instances/" + slug + "/site.yml still declares `palette:`. It is "
            "INERT as of 2026-08-04 -- header, drawer and accent colours now "
            "come from the theme's canonical tokens via assets/base.css. "
            "Delete the block; leaving it implies a control that no longer "
            "exists.",
        )

    # The reader that keeps `aliases:` from becoming the same kind of dead key
    # as the block above. Runs AFTER state.INSTANCE is set so the normalised
    # list is what anything downstream would see.
    _register_aliases(inst, slug)

    # ⭐ WHERE THE DESIGN SYSTEM CAME FROM, SAID ONCE (2026-08-06).
    #
    # This used to be the first line of theme.build_css(), which `assets._plan`
    # calls from BOTH on_config and on_files -- and tokenaudit calls a third
    # time on any page carrying `!!! tokens`. Harmless while the check only
    # spoke about a damaged file; the live read made it speak on every build,
    # so "FELL BACK TO THE VENDORED COPY" printed three times and read as three
    # separate problems.
    #
    # Hook 00 runs exactly once, after state.reset() above and before any other
    # hook reads a vector. ⚠️ verify() reads only the environment and two
    # directories -- no instance state -- so it is safe anywhere in this
    # function; it sits last because a provenance line reads better once the
    # site has a name.
    vectors.verify()

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
