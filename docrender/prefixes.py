"""The `@` prefix namespace, DERIVED from the handlers that claim it.

WHY THIS FILE EXISTS AT ALL.

`links.py` resolves every `@token` by `token.partition(":")` and treats whatever sits
left of the colon as a PEER SITE SLUG. That was fine while peers were the only thing
that wanted the slot. They are not any more: `@data:` claims it here, and `@term:` is
decided and coming. Two namespaces built by different hands in the same week, each
correct on its own branch, is how the second merge silently reopens the first hole.

So the resolution order is now: RESERVED PREFIX FIRST, peer partition second. A prefix
nobody claimed falls through to peer lookup exactly as it always did.

WHY IT IS DERIVED AND NOT A LIST.

The obvious version of this file is a dict literal naming every reserved word. That is
a second copy of a fact the code already knows, and this repo has now been bitten by
that exact shape four times: the lede defined in three languages, `data:` declared
twice, a hand-maintained agent roster, a hand-typed token list in the theme. A list
here would have been the fifth, and the failure mode is specific and quiet -- somebody
adds a hook, forgets the row, and their namespace resolves as a missing peer site.

Here a handler CLAIMS its prefix at import time and the registry IS the set of claims.
Forgetting to register is not possible, because registering is how the handler works.

    from . import prefixes
    prefixes.claim("data", __name__, _resolve_data_reference)

⭐ AND AS OF 2026-08-09 ONE CLAIMANT IS ITSELF DERIVED. `markerlinks.py` reads the
`prefix` column of theme/markers.tsv and claims one namespace per row, so `@rel:` and
`@calc:` exist because a TSV cell says so and not because this codebase names them
anywhere. That is the same argument one layer further out: the registry is derived
from its handlers, and that handler is derived from its data.

⚠️ TIMING. Claims happen at hook IMPORT time; lookups happen during the FILES and
PAGE events, which are much later. Do not read the registry at import time in another
module -- the claim you are looking for may not have been made yet, and you will cache
an empty answer for the whole build. Every read in this codebase happens inside an
event handler, deliberately.

⚠️ A PEER SITE MAY NOT BE SLUGGED WITH A RESERVED WORD. Nothing stopped that before
and nothing said so; the site would simply stop resolving one of its own namespaces
and no message would appear anywhere. `audit_peers()` is called by links.py on_files
and reports the collision.


THREE CALL SHAPES, ONE LADDER, AND THE LADDER IS DELIBERATELY NOT A MATRIX
==========================================================================

A resolver's signature grows in rungs, and a handler declares how far up it goes:

    claim(p, owner, fn)                 fn(rest, page, label)
    claim(p, owner, fn, anchors=True)   fn(rest, page, label, anchor)
    claim(p, owner, fn, opts=True)      fn(rest, page, label, anchor, opts)

🚨 `opts=True` IMPLIES THE ANCHOR ARGUMENT. That is the whole reason this is a ladder
rather than two independent booleans: two flags would mean FOUR call shapes in
links.py, and three of them would exist for one real consumer. A rung costs one
`elif`; a matrix costs a combinatorial branch nobody exercises.


WHY THE FLAGS EXIST AT ALL, WHICH IS THE SAME ARGUMENT TWICE
============================================================

A handler's signature was `(rest, page, label)` with no anchor, so `@data:x#totals`
parsed fine, resolved fine, and lost the fragment on the way out. links.py REPORTED
that loss and its docstring called widening the signature "a deliberate later change."
The `anchors` flag was that change; `opts` is the identical move for the author's
attr_list block.

⚑ THE FLAG IS ON THE CLAIM, NOT ON THE CALL, AND THAT IS THE WHOLE DESIGN. The
obvious fix both times is to widen the signature for everybody. Rejected both times.
It rewrites `datatable.py`, which is over the safe-edit ceiling, and `images.py`, to
accept arguments neither can ever use -- and it is the wrong CLAIM: `@data:` addresses
a whole table and `@img:` a whole picture. Neither has anywhere for a fragment to
point, and neither has an element an author's class could sensibly decorate. Widening
them would replace an honest report with a silent no-op.

So the handler that CAN use a thing says so when it registers, and links.py asks the
registry rather than guessing. Handlers that never opted in are called exactly as
before, byte for byte, and keep the behaviour they already have.

🚨 DEFAULTS ARE FALSE AND MUST STAY FALSE. An unwidened handler handed an extra
positional argument raises TypeError inside a page render -- a build-killer, reachable
from a data edit, which is precisely the shape of the ImportError that took all four
sites down on 2026-08-05. The default keeps the OLD call shape as the fallback rather
than the new one, so the failure mode of forgetting a flag is a dropped argument with
a report line, never a dead site.
"""

from __future__ import annotations

from typing import Callable

#: prefix -> (owning module, resolver, takes_anchor, takes_opts).
#:
#: A resolver takes `(token_remainder, page, label)`, plus `anchor` if it claimed
#: with `anchors=True`, plus `opts` if it claimed with `opts=True`. It returns either
#: a replacement markdown/HTML string, or None to mean "I decline, treat this as
#: unresolved". It never raises and never fails the build.
_CLAIMS: dict[str, tuple[str, Callable, bool, bool]] = {}


def claim(
    prefix: str,
    owner: str,
    resolver: Callable,
    anchors: bool = False,
    opts: bool = False,
) -> None:
    """Register a reserved `@<prefix>:` namespace.

    Idempotent by design: MkDocs imports hook modules once per build, but `mkdocs
    serve` rebuilds in-process and a re-import must not look like a conflict. A
    SECOND owner claiming the same prefix is a real programming error and is loud.

    `anchors=True` means the resolver accepts a fourth positional argument -- the
    `#fragment` exactly as written, INCLUDING its hash, or `""` when there is none --
    and takes responsibility for putting it on the href.

    `opts=True` means it accepts a FIFTH positional argument: the author's trailing
    attr_list block exactly as written, braces included (`{.no-print}`), or `""`.
    ⚠️ IT IMPLIES `anchors` -- see the ladder in the module docstring -- and it also
    makes the handler RESPONSIBLE for that block. links.py stops re-emitting it, so a
    handler that opts in and then ignores the value silently eats the author's
    classes, which is exactly the failure this argument exists to end.

    ⚠️ A CALLER THAT RAISES HERE IS A PROGRAMMING ERROR AND A CALLER THAT IS DATA IS
    NOT. `markerlinks.py` builds its claims from a TSV, where a duplicate is a typo
    rather than a bug, so it checks and reports before calling and catches this
    anyway. Do not soften the raise to accommodate it: the loud version is correct
    for every hand-written claimant, which is all the others.
    """
    existing = _CLAIMS.get(prefix)
    if existing and existing[0] != owner:
        raise RuntimeError(
            "@" + prefix + ": is claimed by both " + existing[0] + " and " + owner
            + ". Two handlers cannot own one prefix -- rename one of them."
        )
    # `opts` implies `anchors`: the rungs are cumulative, so a handler cannot ask for
    # the fifth argument while declining the fourth.
    _CLAIMS[prefix] = (owner, resolver, bool(anchors) or bool(opts), bool(opts))


def reserved() -> set[str]:
    return set(_CLAIMS)


def resolver(prefix: str):
    entry = _CLAIMS.get(prefix)
    return entry[1] if entry else None


def takes_anchor(prefix: str) -> bool:
    """Did this prefix's owner opt in to receiving the `#fragment`?

    Read by links.py to choose the call shape. An unclaimed prefix answers False,
    which is correct and never actually reached -- links.py only asks after
    `resolver()` has already returned a handler.
    """
    entry = _CLAIMS.get(prefix)
    return bool(entry[2]) if entry else False


def takes_opts(prefix: str) -> bool:
    """Did this prefix's owner opt in to receiving the author's attr_list block?

    True implies `takes_anchor` is also True -- `claim()` enforces that rather than
    trusting the caller, because a handler asking for the fifth argument without the
    fourth would be called with the anchor in the opts position and would silently
    put a fragment where classes belong.
    """
    entry = _CLAIMS.get(prefix)
    return bool(entry[3]) if entry else False


def owner(prefix: str) -> str:
    entry = _CLAIMS.get(prefix)
    return entry[0] if entry else ""


def audit_peers(peer_slugs, note) -> None:
    """Report any peer site whose slug collides with a reserved prefix.

    Called once, from links.on_files, after every hook has been imported. The peer
    keeps working as a peer for this build -- the reserved prefix wins, so `@data:x`
    goes to the data handler and the peer becomes unreachable by name. That is a
    configuration error on the instance, not something the engine should silently
    resolve one way or the other.

    ⚠️ THE RESERVED SET IS BIGGER THAN IT LOOKS NOW. Since markerlinks derives its
    claims from theme/markers.tsv, adding a marker row can newly collide with a peer
    slug that has been fine for months. This check is what turns that into a line in
    the report instead of a peer that quietly stops resolving.
    """
    for slug in sorted(peer_slugs):
        if slug in _CLAIMS:
            note(
                "dead_links",
                "peer site '" + slug + "' collides with the reserved prefix @" + slug
                + ": (owned by " + _CLAIMS[slug][0] + "). The reserved prefix wins, so "
                + "every cross-site link to that peer is unreachable. Rename the peer "
                + "in this instance's site.yml.",
            )
