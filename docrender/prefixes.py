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

⚠️ TIMING. Claims happen at hook IMPORT time; lookups happen during the FILES and
PAGE events, which are much later. Do not read the registry at import time in another
module -- the claim you are looking for may not have been made yet, and you will cache
an empty answer for the whole build. Every read in this codebase happens inside an
event handler, deliberately.

⚠️ A PEER SITE MAY NOT BE SLUGGED WITH A RESERVED WORD. Nothing stopped that before
and nothing said so; the site would simply stop resolving one of its own namespaces
and no message would appear anywhere. `audit_peers()` is called by links.py on_files
and reports the collision.
"""

from __future__ import annotations

from typing import Callable

#: prefix -> (owning module, resolver). A resolver takes (token_remainder, page, label)
#: and returns either a replacement markdown/HTML string, or None to mean "I decline,
#: treat this as unresolved" -- it never raises and never fails the build.
_CLAIMS: dict[str, tuple[str, Callable]] = {}


def claim(prefix: str, owner: str, resolver: Callable) -> None:
    """Register a reserved `@<prefix>:` namespace.

    Idempotent by design: MkDocs imports hook modules once per build, but `mkdocs
    serve` rebuilds in-process and a re-import must not look like a conflict. A
    SECOND owner claiming the same prefix is a real programming error and is loud.
    """
    existing = _CLAIMS.get(prefix)
    if existing and existing[0] != owner:
        raise RuntimeError(
            "@" + prefix + ": is claimed by both " + existing[0] + " and " + owner
            + ". Two handlers cannot own one prefix -- rename one of them."
        )
    _CLAIMS[prefix] = (owner, resolver)


def reserved() -> set[str]:
    return set(_CLAIMS)


def resolver(prefix: str):
    entry = _CLAIMS.get(prefix)
    return entry[1] if entry else None


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
