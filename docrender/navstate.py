'''The `nav:` frontmatter key -- what a FOLDER does in the sidebar.

WHY decisions here are the way they are: the doc-render-engine Decision Log.
Stage ordering (why 00bb, why 06b): hooks/README.md. Reader-facing contract and
the cost of `expanded`: README section 3 and section 7. This docstring holds
what someone EDITING this file has to know, and points at the rest.

Declared on a folder's `index.md`, and NOWHERE ELSE. Three values, each with a
bare-verb alias, because Michael asked for one and a vocabulary where only one
value has a short form is a vocabulary you have to remember:

    hidden | hide         the folder keeps its own sidebar row and loses its
                          children. Still BUILT, still live URLs, still resolve
                          by `@id`. The curtain, not the lock -- same family as
                          `unlisted` and the router seal, same warning.
    collapsed | collapse  a closed row you click to open.
    expanded | expand     opens by itself, and so does everything under it,
                          until a descendant index says otherwise.

THE SITE ROOT DECLARES THE DEFAULT; THIS FILE ONLY HOLDS THE FALLBACK.
Michael, 2026-08-05: *SITE md index file gets nav: collapsed to dictate that.
no other back end should control that.* `DEFAULT` below is not the site's answer
any more, it is what a site that never gave one gets.

🔴 AND THE KEY WAS ALREADY DEAD IN THAT EXACT SLOT, which is why this is a
filled hole rather than a new feature. `_misplaced` exempts `index.md` from the
wrong-place warning -- but `_walk` only visits SECTIONS, and the root index is a
top-level PAGE. So a `nav:` written there parsed, was excused from the one check
that would have flagged it, and did nothing. An exemption with no implementation
behind it is the worst-shaped dead control available: the engine had already
promised to take the key seriously there.

🚫 ROOT `nav: hidden` IS REFUSED, OUT LOUD. Inherited by every top-level folder
it leaves a sidebar of bare labels. `_walk`'s non-cascade rule would already
degrade it, but silently, as a side effect of a rule written for something else.
A refusal nobody can see is not a refusal.

⚠️ A ROOT WITH NO `nav:` IS REPORTED AND COLLAPSES. Michael floated a build
failure and ruled against his own suggestion, correctly: this engine warns and
never dies, with exactly one hard failure in the pipeline (the leak scan). It
reports into its own SECTION rather than `notes`, because notes print last and a
fact governing every folder cannot be the line under forty size warnings.

WHY THIS IS ADD-ONLY, AND WHY THAT IS THE WHOLE DESIGN. Michael: *active stays
open.* Material writes `checked` onto a toggle only when the section is an
ancestor of the current page, so 'active stays open' is implemented by NEVER
REMOVING it and 'collapsed by default' by DOING NOTHING. The entire feature is:
add `checked` where `expanded` resolved true.

⭐ An add-only pass over rendered HTML cannot break a sidebar. The worst failure
available to it is a folder open when it should have been shut. Fail-open, on
the surface a reader navigates by.

TWO STAGES, BECAUSE MKDOCS SPLITS THE TWO QUESTIONS. `hidden` is a question
about the nav TREE (`on_nav`); `expanded` is a question about rendered HTML
(`on_post_page`). They are two events, not two lines that could have been moved
next to each other.

    shape()          stage 00bb. Reads the site default, applies `hidden`,
                     resolves the cascade, fills NAV_OPEN. Raises NAV_SHAPED,
                     which visibility.seal_nav (00bc) checks to prove this ran
                     before it -- see shape() for why that is not paranoia.
    on_post_page()   stage 06b. Reads NAV_OPEN, checks the toggles.

⚠️ THE SHIM PASSES IN `_index_of` AND `_unchain` FROM visibility.py, AND THAT IS
THE POINT RATHER THAN A SHORTCUT. Both belong to visibility -- `_index_of`
returns the index a section had BEFORE pruning, recorded in its pass 1 precisely
because reading it afterwards was a live bug, and `_unchain` is the prev/next
detachment every removal in this engine owes. Copying either here would create a
second copy free to drift.

⚠️ `navigation.prune` AND `expanded` CANNOT BOTH BE ON. A pruned nav renders no
children for any section the reader is not inside, so checking that toggle opens
an empty box. `shape()` drops the feature -- but only when something actually
resolved to `expanded`, so a site that never uses it never pays. NOT available
per-subtree: prune is one boolean for the whole theme. Cost and consequences in
README section 7.

⚠️ THE TIMING IS THE ONLY REASON THAT DROP IS LEGAL. Every `on_nav` runs before
any page renders, and the template reads `features` at render time. `on_config`
would NOT work -- `state.BY_SRC` is empty then, the trap `assets.py` already
fell into and documented.

WHAT THIS DOES NOT DO: unbuild anything, touch search, or have any opinion about
`status:`. A `hidden` folder is exactly as public as it was before. 🚫 And it is
NOT a status cascade -- `nav:` on a non-index page does nothing at all, and is
REPORTED rather than ignored, because a key that silently does nothing is the
failure this whole file was written to avoid.
'''

from __future__ import annotations

import posixpath
import re

from . import state

#: The content repo's own landing page. Its `nav:` is the site-wide default.
SITE_ROOT = 'index.md'

#: The vocabulary, in the spelling everything else in this engine uses.
VALUES = ('hidden', 'collapsed', 'expanded')

#: Michael, 2026-08-05: *I'd like to be able to say "expanded" or "expand".*
#:
#: ⭐ ALL THREE GOT A SHORT FORM, not just the one asked for. A vocabulary where
#: `expand` works and `collapse` does not is one you have to remember rather
#: than guess, and the failure is silent: an unknown value falls back to the
#: default, which on a `collapse` typo is indistinguishable from success.
ALIASES = {
    'hide': 'hidden',
    'hidden': 'hidden',
    'collapse': 'collapsed',
    'collapsed': 'collapsed',
    'expand': 'expanded',
    'expanded': 'expanded',
}

#: What a site that has NOT declared a default gets. No longer the site's answer
#: -- the root index is -- just the answer for a site that never gave one.
DEFAULT = 'collapsed'


# ===========================================================================
# STAGE 00bb -- shape the tree, resolve the cascade
# ===========================================================================


def _canon(raw):
    '''Normalise a declared value, or None if it is not one of ours.'''
    return ALIASES.get(str(raw).strip().lower())


def _value(src_uri: str):
    '''This index page's own declared `nav:`, canonical. None if it has none.'''
    raw = state.BY_SRC.get(src_uri, {}).get('nav')
    if raw is None:
        return None
    value = _canon(raw)
    if value:
        return value
    state.note(
        'notes',
        src_uri + ': `nav: ' + str(raw) + '` is not a value this engine knows. '
        + 'Valid: ' + ' | '.join(VALUES) + ' (or hide | collapse | expand). '
        + 'Falling back to the site default.',
    )
    return None


def _site_default() -> str:
    '''What every folder inherits: the root index's `nav:`, or the fallback.

    ⚠️ THE ROOT IS THE ONE PLACE A MISSING DECLARATION IS WORTH A REPORT. On a
    folder, silence means "whatever my parent said", which is the feature. On the
    site index there is no parent, so silence means the site never answered a
    question about every folder in it.
    '''
    raw = state.BY_SRC.get(SITE_ROOT, {}).get('nav')

    if raw is None:
        state.note(
            'nav_default',
            SITE_ROOT + " declares no `nav:`, so every folder on this site "
            + "defaults to '" + DEFAULT + "'. That is almost certainly what you "
            + 'want, and it is reported anyway because the alternative is a '
            + 'site-wide behaviour nobody chose. Write `nav: ' + DEFAULT + '` to '
            + 'say so on purpose, or `nav: expanded` to open every folder that '
            + 'does not shut itself.',
        )
        return DEFAULT

    value = _canon(raw)

    if value is None:
        state.note(
            'nav_default',
            SITE_ROOT + ': `nav: ' + str(raw) + '` is not a value this engine '
            + "knows, so the site default is '" + DEFAULT + "'. Valid: "
            + ' | '.join(VALUES) + ' (or hide | collapse | expand).',
        )
        return DEFAULT

    if value == 'hidden':
        # 🚫 Inherited by every top-level folder, this renders a sidebar of bare
        # labels with nothing under any of them. `_walk` would already degrade
        # it -- `hidden` does not cascade -- but as a side effect of a rule
        # written to stop an inherited value reaching past a cut, not as an
        # answer to this.
        state.note(
            'nav_default',
            SITE_ROOT + ': `nav: hidden` cannot be the SITE default -- inherited '
            + 'by every top-level folder it empties the whole sidebar and leaves '
            + "a row of labels. Using '" + DEFAULT + "'. Put `nav: hidden` on the "
            + 'individual folders you meant.',
        )
        return DEFAULT

    state.note(
        'nav_default',
        SITE_ROOT + ': site default is `nav: ' + value + '`. Every folder '
        + 'inherits it until an index page under it says otherwise.',
    )
    return value


def _misplaced() -> None:
    '''Report `nav:` on any page that is not a folder index or the site root.

    A folder's open state is a fact about the FOLDER, so the only page that can
    speak for it is the one MkDocs already treats as the folder's own page. On a
    leaf page the key resolves to nothing, renders nothing, and errors nowhere
    -- so it gets said out loud here instead of being absorbed.

    ⭐ THE `index.md` EXEMPTION IS LOAD-BEARING NOW AND WAS NOT BEFORE. It was
    written when the root index could not be read by anything, which made it an
    exemption protecting a dead key. `_site_default` is the implementation it
    was always implying.
    '''
    for src, meta in state.BY_SRC.items():
        if 'nav' not in meta:
            continue
        if src == SITE_ROOT or src.endswith('/index.md'):
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
    '''Stage 00bb. See hooks/README.md for why the number has two b's.'''
    # ⭐ FIRST, AND UNCONDITIONALLY. visibility.seal_nav (00bc) reads this to
    # prove this stage ran before it, because it MUST: the seal harvests a routed
    # subtree into ciphertext, and a `nav: hidden` folder that has not been cut
    # yet goes into that payload and comes back into the sidebar on a correct
    # code. That was the live bug on uritp courses, 2026-08-05.
    #
    # It means "the stage ran", never "the stage changed something". A site with
    # no `nav:` anywhere still shapes its tree -- every folder resolves to the
    # site default and nothing is cut -- so keying this off whether anything
    # moved would fire the warning on every ordinary build, and a detector that
    # cries on healthy sites is a detector nobody reads.
    state.NAV_SHAPED = True

    _misplaced()
    _walk(items, index_of, unchain, _site_default())

    if not state.NAV_OPEN:
        return

    features = list(config.theme.get('features') or [])
    if 'navigation.prune' not in features:
        return

    config.theme['features'] = [f for f in features if f != 'navigation.prune']
    state.note(
        'nav_default',
        'navigation.prune DISABLED for this build: ' + str(len(state.NAV_OPEN))
        + ' folder(s) resolved to `nav: expanded`, and a pruned nav renders no '
        + 'children for any section the reader is not already inside -- so the '
        + 'expansion would open an empty box. Every page now ships the whole '
        + "nav tree (~33% of page weight, Material's own figure). Not available "
        + 'per-subtree: prune is one boolean for the theme. Remove every '
        + '`expanded` declaration, INCLUDING the site default, to get it back.',
    )


# ===========================================================================
# STAGE 06b -- check the toggles in the rendered page
# ===========================================================================
#
# ⚠️ THIS READS RENDERED HTML, WHICH IS A THING THIS REPO HAS NOT DONE BEFORE.
# Open state is decided by Material's `nav-item.html` and expressed as ONE
# attribute. Forking that partial into a `custom_dir` would be a copy of
# somebody else's truth that we then maintain forever -- the defect that killed
# roster.json, registry.json and app-index.md -- and doing it in the browser
# flaps the sidebar on every page load. Editing the attribute on the way out is
# the only option that adds no second copy of anything.
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
