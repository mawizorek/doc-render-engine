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


SOME NAMESPACES TAKE AN `#anchor` AND MOST DO NOT (2026-08-09)
==============================================================

A handler's signature was `(rest, page, label)` with no anchor at all, so
`@data:x#totals` parsed fine, resolved fine, and lost the fragment on the way out.
links.py has REPORTED that loss since 2026-08-04 and its docstring called widening
the signature "a deliberate later change and not a thing to sneak into a feature
branch." This is that change.

It became blocking the moment a CALCULATION wanted to be linked. A calc has no page
of its own -- it lives at a heading on its table's page -- so
`@calc:table-workdays#calc-fkCalendar` is the whole address and the fragment is the
half that matters. Without it the link resolves perfectly and lands at the top of a
long page, which is this file's own recurring failure: resolution that succeeds while
quietly discarding half the request.

⚑ THE FLAG IS ON THE CLAIM, NOT ON THE CALL, AND THAT IS THE WHOLE DESIGN. The
obvious fix is to widen the signature for everybody. Rejected twice over. It rewrites
`datatable.py`, which is over the safe-edit ceiling, and `images.py`, to accept an
argument neither can ever use -- and it is the wrong CLAIM: `@data:` addresses a whole
table and `@img:` a whole picture. Neither has anywhere for a fragment to point, so
for them the anchor genuinely is meaningless and the existing complaint genuinely is
correct. Widening them would replace an honest report with a silent no-op.

So the handler that CAN use an anchor says so when it registers, and links.py asks the
registry rather than guessing. Handlers that never opted in are called exactly as
before, byte for byte, and keep the complaint they already emit.

🚨 DEFAULT IS FALSE AND MUST STAY FALSE. An unwidened handler handed a fourth
positional argument raises TypeError inside a page render -- a build-killer, reachable
from a data edit, which is precisely the shape of the ImportError that took all four
sites down on 2026-08-05. The default keeps the OLD call shape as the fallback rather
than the new one, so the failure mode of forgetting the flag is a dropped anchor with
a report line, never a dead site.
"""

from __future__ import annotations

from typing import Callable

#: prefix -> (owning module, resolver, takes_anchor).
#:
#: A resolver takes `(token_remainder, page, label)` -- plus a fourth positional
#: `anchor` argument ONLY if it claimed with `anchors=True` -- and returns either a
#: replacement markdown/HTML string, or None to mean "I decline, treat this as
#: unresolved". It never raises and never fails the build.
_CLAIMS: dict[str, tuple[str, Callable, bool]] = {}


def claim(prefix: str, owner: str, resolver: Callable, anchors: bool = False) -> None:
    """Register a reserved `@<prefix>:` namespace.

    Idempotent by design: MkDocs imports hook modules once per build, but `mkdocs
    serve` rebuilds in-process and a re-import must not look like a conflict. A
    SECOND owner claiming the same prefix is a real programming error and is loud.

    `anchors=True` means the resolver accepts a fourth positional argument -- the
    `#fragment` exactly as written, INCLUDING its hash, or `""` when there is none --
    and takes responsibility for putting it on the href. Leave it False and links.py
    calls the three-argument form and reports any anchor as dropped, unchanged.

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
    _CLAIMS[prefix] = (owner, resolver, bool(anchors))


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
