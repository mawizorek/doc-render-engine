'''Stage 00bd -- what SURVIVED wants, which is not what was DECLARED.

WHY decisions here are the way they are: the doc-render-engine Decision Log.
Stage ordering: hooks/README.md. The `nav:` vocabulary and the cascade belong to
docrender/navstate.py; this module owns exactly one thing, and it is the LAST
word on a decision navstate is no longer allowed to make alone.

=============================================================================
THE DEFECT: A FOLDER NOBODY CAN SEE WAS COSTING EVERY PAGE ~33%
=============================================================================
Found 2026-08-16 while auditing uritp-docs, and the live instance is exact:
`roles/addendum/index.md` declares `nav: expand`, and `roles/index.md` declares
`router: [pm]`. So --

    00bb  navstate.shape   resolves addendum to `expanded`, writes it into
                           NAV_OPEN, and (until this stage existed) dropped
                           `navigation.prune` for the WHOLE BUILD
    00bc  visibility.seal  seals `roles/`, harvests addendum into ciphertext,
                           and the folder LEAVES THE SIDEBAR

Every page on the site then shipped the entire nav tree -- Material's own figure
is ~33% of page weight -- on account of a folder no reader without a code can
see, plus a toggle at 06b that cannot exist to be checked.

THE CAUSE IS NOT A WRONG RULE. It is a rule evaluated too early. `shape()` asks
*does any folder want to be open* at the only moment it can resolve the cascade
-- and the answer is still provisional then, because two later stages are allowed
to remove folders from the tree. The declaration was read correctly; it was just
not the last word.

GENERALISABLE, and this repo has now paid for it twice from opposite ends: the
00bc-before-00bb bug sealed a subtree that had not been trimmed yet, and this one
spent a global budget on a subtree that was about to be sealed. A STAGE THAT
READS A DECLARATION AND A STAGE THAT SPENDS A RESOURCE ON IT ARE NOT THE SAME
STAGE. The first belongs where the declaration can be resolved; the second
belongs after everything allowed to invalidate it has run.

=============================================================================
WHAT THIS DOES, IN ORDER
=============================================================================

    1. Walk the nav tree AS IT NOW STANDS and collect every section that still
       has a row -- i.e. every section a reader could actually click.
    2. Drop from `state.NAV_OPEN` every entry that is no longer among them, and
       REPORT each one by name with the reason it is not there.
    3. THEN, and only if something real is left, drop `navigation.prune`.

STEP 2 IS WORTH AS MUCH AS STEP 3. 06b reads NAV_OPEN to insert ` checked` into
rendered HTML; a stale entry sends it hunting a toggle that was never emitted. It
never found one and never said so, which is the quiet half of this bug -- a pass
that silently does nothing on every page of the site.

IT DOES NOT RE-ADD `navigation.prune`. Nothing here ever puts the feature back,
because nothing here can know whether it was in `mkdocs.yml` to begin with -- and
a stage that both removes and restores a theme feature is a stage that can
disagree with itself. This only ever DECLINES to remove it.

AND IT MAY IMPORT `visibility`, WHICH `navstate` MAY NOT. That looks inconsistent
and is not. The one-way law exists because `visibility` imports `navstate` (it
asks `declared()` whether a folder said `routed`), so navstate importing back
would be a cycle. Nothing imports THIS module except its own shim, so
`navsettle -> visibility -> navstate` is a straight line. The reason navstate
needs `_index_of` passed in through a shim does not apply here, and saying so is
cheaper than the next reader re-deriving it.
'''

from __future__ import annotations

from . import navstate, state
from .visibility import _index_of


def _standing(items, out: set) -> None:
    '''Every section that still has a clickable row, by its index page's url.

    Keyed the same way `navstate.shape` keys NAV_OPEN -- through `_norm` on the
    index page's url -- because two spellings of one key is how a set difference
    quietly reports everything as missing.

    `_index_of` READS THE MARK RECORDED BEFORE PRUNING, not the live children,
    and that is load-bearing rather than incidental. A routed folder's children
    are `[]` by the time this runs, so re-deriving an index from live children
    would return None for exactly the folders this stage exists to reason about.
    '''
    for item in items:
        if not getattr(item, 'is_section', False):
            continue
        index = _index_of(item)
        if index is not None:
            out.add(navstate._norm(index.file.url))
        _standing(getattr(item, 'children', None) or [], out)


def settle(items, config) -> None:
    '''Stage 00bd. See hooks/README.md for why the letter is `d`.'''
    if not state.NAV_OPEN:
        # Nothing declared `expanded` anywhere, so there is no budget to spend
        # and nothing to report. A site that never uses the feature never pays,
        # which was true before this stage and stays true.
        return

    standing: set = set()
    _standing(items, standing)

    gone = sorted(key for key in state.NAV_OPEN if key not in standing)
    for key in gone:
        del state.NAV_OPEN[key]
        state.note(
            'nav_default',
            '/' + key + ' resolved to `nav: expanded` and is NOT in the sidebar '
            + 'any more -- it was sealed behind a router, or an ancestor was. '
            + 'The declaration is ignored for this build: it cannot open a row '
            + 'that does not exist, and it no longer costs the site its '
            + '`navigation.prune` budget. Nothing is wrong with the page; if the '
            + 'folder is meant to open on a correct code, note that a revealed '
            + 'menu carries its own collapse and does not read `nav:` at all.',
        )

    if not state.NAV_OPEN:
        # THE WHOLE POINT, IN THE CASE THAT MOTIVATED IT. Every `expanded`
        # folder left the sidebar, so the site keeps `navigation.prune` and its
        # ~33% -- which is what should have happened all along.
        state.note(
            'nav_default',
            'navigation.prune KEPT: every folder that resolved to `nav: '
            + 'expanded` was sealed out of the sidebar before this stage, so '
            + 'there is nothing left to expand. Earlier builds dropped the '
            + 'feature here and shipped the whole nav tree on every page (~33% '
            + "of page weight, Material's own figure) for folders no reader "
            + 'could see.',
        )
        return

    features = list(config.theme.get('features') or [])
    if 'navigation.prune' not in features:
        return

    config.theme['features'] = [f for f in features if f != 'navigation.prune']
    state.note(
        'nav_default',
        'navigation.prune DISABLED for this build: ' + str(len(state.NAV_OPEN))
        + ' folder(s) resolved to `nav: expanded` AND are still in the sidebar, '
        + 'and a pruned nav renders no children for any section the reader is '
        + 'not already inside -- so the expansion would open an empty box. Every '
        + "page now ships the whole nav tree (~33% of page weight, Material's "
        + 'own figure). Not available per-subtree: prune is one boolean for the '
        + 'theme. Remove every `expanded` declaration, INCLUDING the site '
        + 'default, to get it back.',
    )


# THE TIMING IS STILL THE ONLY REASON THE DROP IS LEGAL, and moving the decision
# two stages later does not change that. Every `on_nav` runs before any page
# renders and the Material template reads `features` at render time, so a feature
# removed anywhere in the nav chain is removed in time. `on_config` would NOT
# work -- `state.BY_SRC` is empty then, the trap `assets.py` already fell into
# and documented.
