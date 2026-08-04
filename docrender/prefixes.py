"""The reserved half of the `@token` namespace, DERIVED and never typed.

Every reference in this engine is spelled `[label](@token)`. links.py resolves a
token by splitting on the first colon and treating the left half as a PEER SITE
SLUG. That was true when exactly one thing wanted the slot. It is not any more:

    [Main Stage](@main-stage)                  a page id, no prefix
    [rep plot](@oph:rep-plot)                  a page in a SIBLING site
    [inventory table](@data:inventory_table)   a data file beside this page

So `data` is now a RESERVED word on the left of that colon, and anything else
still falls through to peer lookup exactly as before.

WHY THIS IS A MODULE AND NOT AN `if` IN links.py (Decision Log J8, option D).
The cheap version was a hand-written list of reserved prefixes. That list would
have been a second copy of a fact the code already knows -- the same defect as
the lede declared in three places, the same defect as a filename typed in both
frontmatter and the body, the same defect as a hand-maintained agent roster. It
would have been the fourth hand-maintained index in a system whose entire
thesis is that hand-maintained indexes rot.

So the list is ASSEMBLED. A handler calls `claim()` at import time and the
registry is whatever has claimed. Adding a namespace and forgetting to reserve
it is not discouraged, it is impossible: the claim IS the registration.

    # docrender/datatable.py
    from . import prefixes
    prefixes.claim("data", _resolve_reference, owner="datatable.py")

ORDER MATTERS AND IT IS NOT SUBTLE. `claim()` runs at import time; `reserved()`
is read while a page is being rewritten, long after every module is loaded. A
handler that is never imported never claims, and its prefix silently resolves
as a peer site again -- which is the exact bug this file exists to prevent. If
a namespace stops working, check that its module is imported by a hook that
mkdocs.yml actually registers. A file in hooks/ that is absent from that list
is never loaded at all.

A PEER MAY NOT BE SLUGGED WITH A RESERVED WORD, and until now nothing said so.
A site that named a peer `data` would simply lose one of its own namespaces,
quietly, with no error anywhere. `collisions()` is what links.py calls to
report that at build time.
"""

from __future__ import annotations

from typing import Callable, Iterable

#: prefix -> (handler, owning module). Populated by claim(), never literal.
_CLAIMED: dict[str, tuple[Callable, str]] = {}


def claim(prefix: str, handler: Callable, *, owner: str = "") -> None:
    """Reserve `prefix` on the left of the colon and route it to `handler`.

    Idempotent on re-import (a hook module can be imported twice in one build
    without that being an error), but a SECOND owner claiming the same prefix
    is a genuine conflict and raises. Two handlers on one namespace is not a
    thing that can be resolved at runtime, and a silent last-wins would be the
    worst possible outcome: whichever module happened to import later would
    take the prefix, and the losing feature would look simply broken.
    """
    existing = _CLAIMED.get(prefix)
    if existing and existing[0] is not handler:
        raise ValueError(
            "@" + prefix + ": already claimed by " + (existing[1] or "?")
            + ", cannot be re-claimed by " + (owner or "?")
        )
    _CLAIMED[prefix] = (handler, owner)


def reserved() -> frozenset[str]:
    """Every prefix that must NOT be read as a peer site slug."""
    return frozenset(_CLAIMED)


def handler(prefix: str) -> Callable | None:
    entry = _CLAIMED.get(prefix)
    return entry[0] if entry else None


def owner(prefix: str) -> str:
    entry = _CLAIMED.get(prefix)
    return entry[1] if entry else ""


def collisions(peer_slugs: Iterable[str]) -> list[str]:
    """Peer slugs that collide with a reserved prefix, for the build report."""
    return sorted(set(peer_slugs) & reserved())
