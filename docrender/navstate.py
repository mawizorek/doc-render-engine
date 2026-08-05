'''The `nav:` frontmatter key -- what a FOLDER does in the sidebar.

WHY decisions here are the way they are: the doc-render-engine Decision Log.
This docstring is the CONTRACT and is kept under the read-whole line.

Declared on a folder's `index.md`, and NOWHERE ELSE. Three values:

    hidden     the folder keeps its own sidebar row and loses its children.
               The pages are still BUILT, still have live URLs, still resolve
               by `@id`. This is the curtain, not the lock -- same family as
               `unlisted` and the router seal, and the same warning applies.
    collapsed  THE DEFAULT. The folder is a closed row you click to open.
    expanded   the folder opens by itself, and so does everything under it,
               until a descendant index says `collapsed` or `hidden`.

=============================================================================
WHY THIS IS ADD-ONLY, AND WHY THAT IS THE WHOLE DESIGN
=============================================================================
Michael, 2026-08-05: *active stays open.*

Material decides a section's open state in ONE place -- `nav-item.html` writes
`checked` onto the toggle input if `nav_item.active`. `navigation.expand` is not
enabled here, so **the only checked toggles in a rendered page are the ancestors
of the page you are on.**

So 'active stays open' is implemented by NEVER REMOVING `checked`, and
'collapsed by default' is implemented by DOING NOTHING, because that is already
what Material does. The entire feature is: add `checked` where `expanded`
resolved true.

⭐ That matters beyond tidiness. An add-only pass over rendered HTML cannot
break a sidebar: the worst failure available to it is a folder that is open when
it should have been shut. Fail-open, on the surface a reader navigates by.

=============================================================================
TWO STAGES, BECAUSE MKDOCS SPLITS THE TWO QUESTIONS
=============================================================================
`hidden` is a question about the nav TREE, answered in `on_nav`.
`expanded` is a question about rendered HTML, answered in `on_post_page`.

    shape()          stage 00bb. Applies `hidden`, resolves the cascade,
                     fills NAV_OPEN.
    on_post_page()   stage 06b. Reads NAV_OPEN, checks the toggles.

⚠️ STAGE 00bb IS A SLOT BETWEEN TWO EXISTING HOOKS AND THE FILENAME IS HOW IT
SAYS SO. `hidden` has to land AFTER 00b prunes unlisted pages and seals routed
subtrees -- it reads the same index pages those passes can delete -- and BEFORE
00c rewires prev/next, or a hidden page keeps a footer Next button pointing into
a chain it is no longer in, which is the exact defect 00c exists to fix,
reintroduced from the other end. `00bb` sorts after `00b_unlisted.py` and before
`00c_nav.py` on disk as well as in mkdocs.yml, so the two orderings cannot
disagree with each other.

⚠️ THE SHIM PASSES IN `_index_of` AND `_unchain` FROM visibility.py, AND THAT IS
THE POINT RATHER THAN A SHORTCUT. Both belong to visibility: `_index_of` returns
the index each section had BEFORE pruning (recorded in its pass 1, precisely
because reading it afterwards was a live bug), and `_unchain` is the prev/next
detachment every removal in this engine owes. Copying either into this module
would create a second copy free to drift from the first. Wiring them in the shim
puts the dependency at the one place that already knows the order.

🚫 THE REJECTED ALTERNATIVE was calling `shape()` from inside
`visibility.prune_nav` as a fourth pass. It reads better and costs too much:
that file is already 20,266 B against a 22KB hard read limit, and a file that
cannot be read whole cannot be safely edited.

=============================================================================
KNOWN LIMIT, HANDLED: `navigation.prune` AND `expanded` CANNOT BOTH BE ON
=============================================================================
🔴 THIS IS THE PART THAT WOULD HAVE MADE `expanded` A DEAD CONTROL, so it is
handled here rather than documented and forgotten.

`navigation.prune` renders only the ancestors and siblings of the active page.
Every other section arrives in the DOM with NO CHILDREN AT ALL. Checking that
section's toggle opens an empty box -- the control works perfectly and produces
nothing, on every page except the ones where the section was already open.

This log has five entries about rules that were correct in isolation and
unreachable in place. Rather than write the sixth, `shape()` DROPS
`navigation.prune` from `config.theme['features']` -- but ONLY if some page in
this content repo actually declared `expanded`. A site that never uses the
feature never pays for it, and the report says so on any build where it happens.

⚠️ THE TIMING IS THE ONLY REASON THIS IS LEGAL. Every hook's `on_nav` runs
before any page is rendered, and the template reads `features` at render time.
`on_config` would NOT work -- `state.BY_SRC` is empty then, which is the trap
`assets.py` already fell into and documented.

⚠️ THE COST IS REAL: without pruning, every page ships the whole nav tree.
Material's own figure is ~33% of page weight. `hidden` claws a large part of
that back, which is not an accident -- it is why both values live in one key.

=============================================================================
WHAT THIS DOES NOT DO
=============================================================================
It does not unbuild anything, it does not touch search, and it has no opinion
about `status:`. A `hidden` folder is exactly as public as it was before.

🚫 And it is NOT a status cascade. `nav:` on a non-index page does nothing at
all, and is REPORTED rather than ignored, because a key that silently does
nothing is the failure this whole file was written to avoid.
'''

from __future__ import annotations

import posixpath
import re

from . import state

#: The vocabulary. Anything else is reported and treated as the default.
VALUES = ('hidden', 'collapsed', 'expanded')

#: Michael, 2026-08-05: default should now be fully collapsed all the time.
DEFAULT = 'collapsed'


# ===========================================================================
# STAGE 00bb -- shape the tree, resolve the cascade
# ===========================================================================


def _value(src_uri: str):
    '''This index page's own declared `nav:`, validated. None if it has none.'''
    raw = state.BY_SRC.get(src_uri, {}).get('nav')
    if raw is None:
        return None
    value = str(raw).strip().lower()
    if value in VALUES:
        return value
    state.note(
        'notes',
        src_uri + ': `nav: ' + str(raw) + '` is not a value this engine knows. '
        + 'Valid: ' + ' | '.join(VALUES) + ". Treated as '" + DEFAULT + "'.",
    )
    return None


def _misplaced() -> None:
    '''Report `nav:` on any page that is not a folder index.

    A folder's open state is a fact about the FOLDER, so the only page that can
    speak for it is the one MkDocs already treats as the folder's own page. On a
    leaf page the key resolves to nothing, renders nothing, and errors nowhere
    -- so it gets said out loud here instead of being absorbed.
    '''
    for src, meta in state.BY_SRC.items():
        if 'nav' not in meta:
            continue
        if src == 'index.md' or src.endswith('/index.md'):
            continue
        state.note(
            'notes',
            src + ': `nav:` only means something on a folder index.md. Ignored '
            + 'here. Move it to the index of the folder you meant.',
        )


def _count_pages(nodes) -> int:
    total = 0
    for node in nodes:
        if getattr(node, 'is_page', False):
            total += 1
        else:
            total += _count_pages(getattr(node, 'children', None) or [])
    return total


def _hide(section, index, unchain) -> None:
    '''Strip a folder back to its own row and drop the subtree.

    ⚠️ The removed branch is unchained by hand for the same reason `_prune` and
    `_seal` do it: 00c rebuilds prev/next by flattening the tree, so anything no
    longer IN the tree keeps whatever MkDocs wired while building it.
    '''
    children = list(getattr(section, 'children', None) or [])
    removed = [kid for kid in children if kid is not index]
    for kid in removed:
        unchain(kid)
    section.children = [index]

    state.note(
        'notes',
        index.file.src_uri + ' - nav hidden - ' + str(_count_pages(removed))
        + ' page(s) taken out of the sidebar. Still built, still reachable by '
        + 'URL and by @id.',
    )


def _walk(items, index_of, unchain, inherited: str) -> None:
    for item in items:
        if not getattr(item, 'is_section', False):
            continue

        index = index_of(item)
        own = _value(index.file.src_uri) if index is not None else None

        # `hidden` deliberately does NOT cascade, and it does not need to: the
        # whole subtree leaves the sidebar in one cut, so there is nothing left
        # underneath for an inherited value to reach. Letting it flow onward
        # would only hand a state nobody declared to a folder further down.
        carried = inherited if inherited != 'hidden' else DEFAULT
        resolved = own or carried

        if resolved == 'hidden':
            if index is None:
                # Unreachable from a declaration -- `own` is read off the index
                # -- so this is defensive only.
                continue
            if index not in (getattr(item, 'children', None) or []):
                # 🔴 SAME CONTRADICTION SHAPE AS A SEALED ROUTER ON AN UNLISTED
                # INDEX, and resolved the same way: reported, never guessed.
                #   unlisted    says: this page is not in the sidebar.
                #   nav hidden  says: ONLY this page is in the sidebar.
                # With the index already pruned there is no row left to hang the
                # folder on, so hiding the children would leave a heading that
                # expands to nothing.
                state.note(
                    'missing_required',
                    index.file.src_uri + ': `status: unlisted` and `nav: hidden`'
                    + ' contradict each other -- unlisted keeps this page OUT of'
                    + ' the sidebar, hidden leaves it as the ONLY thing in it.'
                    + ' The folder is listed in full instead. Set `status:'
                    + ' public` on this index, or drop `nav: hidden`.',
                )
                _walk(getattr(item, 'children', None) or [], index_of,
                      unchain, DEFAULT)
                continue
            _hide(item, index, unchain)
            continue

        if resolved == 'expanded' and index is not None:
            state.NAV_OPEN[_norm(index.file.url)] = True

        _walk(getattr(item, 'children', None) or [], index_of, unchain, resolved)


def shape(items, config, index_of, unchain) -> None:
    '''Stage 00bb. See this module's docstring for why the number has two b's.'''
    _misplaced()
    _walk(items, index_of, unchain, DEFAULT)

    if not state.NAV_OPEN:
        return

    features = list(config.theme.get('features') or [])
    if 'navigation.prune' not in features:
        return

    config.theme['features'] = [f for f in features if f != 'navigation.prune']
    state.note(
        'notes',
        'navigation.prune DISABLED for this build: ' + str(len(state.NAV_OPEN))
        + ' folder(s) declare `nav: expanded`, and a pruned nav renders no '
        + 'children for any section the reader is not already inside -- so the '
        + 'expansion would open an empty box. Every page now ships the whole '
        + 'nav tree. Remove the `nav: expanded` declarations to get pruning '
        + 'back.',
    )


# ===========================================================================
# STAGE 06b -- check the toggles in the rendered page
# ===========================================================================
#
# ⚠️ THIS READS RENDERED HTML, WHICH IS A THING THIS REPO HAS NOT DONE BEFORE,
# so the reason is written down rather than left as a preference.
#
# Open state is decided by Material's `nav-item.html` and expressed as ONE
# attribute. There are exactly three ways to reach it: fork the partial into a
# `custom_dir` (a copy of somebody else's truth that we then maintain forever --
# the same defect that killed roster.json, registry.json and app-index.md), do it
# in the browser (a visible flap of the sidebar on every page load), or edit the
# attribute on the way out. The third is the only one that adds no second copy
# of anything.
#
# It is written to be UNABLE to do damage: it only ever INSERTS ` checked`, only
# into a tag it has fully matched, and only when the adjacent href resolves to a
# folder index that asked for it. Anything it does not recognise, it leaves
# exactly as Material wrote it.

_INPUT = re.compile(r'<input class="md-nav__toggle md-toggle"[^>]*>')
_HREF = re.compile(r'href="([^"]*)"')

#: How far past the toggle to look for the folder's own link. Material puts it in
#: the very next element; this is a bound, not an estimate.
_WINDOW = 800


def _norm(url: str) -> str:
    return url.strip('/')


def _resolve(page_url: str, href: str) -> str:
    '''Turn a sidebar href back into a site-root-relative page url.

    Material writes hrefs through its own `url` filter, i.e. relative to the page
    doing the asking, so the same folder is a different string on every page.
    Normalising here rather than pre-computing per page keeps the comparison one
    line and keeps this the only place the maths happens. `util.relative_url` is
    the other direction and is not reusable for it.
    '''
    if not href or href.startswith(('http://', 'https://', '//', '#', 'mailto:')):
        return ''
    base = page_url or ''
    if base and not base.endswith('/'):
        base = posixpath.dirname(base) + '/'
    return posixpath.normpath(posixpath.join('/', base, href)).strip('/')


def on_post_page(output, page, config):
    if not state.NAV_OPEN:
        return output

    out = []
    cursor = 0
    for match in _INPUT.finditer(output):
        tag = match.group(0)
        if ' checked' in tag:
            # Active. Michael's rule: it stays open, and nothing here touches it.
            continue

        tail = output[match.end():match.end() + _WINDOW]
        # The folder's own link sits between the toggle and the <nav> holding its
        # children. Stopping at that boundary is what keeps this from matching
        # the first CHILD page's href on a section that has no index page.
        cut = tail.find('<nav ')
        if cut != -1:
            tail = tail[:cut]

        href = _HREF.search(tail)
        if href is None:
            continue
        if not state.NAV_OPEN.get(_resolve(page.url, href.group(1))):
            continue

        out.append(output[cursor:match.start()])
        out.append(tag[:-1] + ' checked>')
        cursor = match.end()

    if not out:
        return output

    out.append(output[cursor:])
    return ''.join(out)
