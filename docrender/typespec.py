"""`data_slots:` -- which named data files a page of this TYPE may declare.

A page names its data files by SLOT, not by filename:

    ---
    title: Audio Inventory
    type: reference
    data:
      inventory_table: audio-inventory.tsv
      revision_log: audio-inventory-revisions.tsv
    ---

and the body refers to the slot, never to the file. That is what makes one body
of prose portable across departments: audio, lighting and video pages carry the
same paragraphs and differ only in frontmatter.

WHY THE VOCABULARY IS CLOSED (Decision Log J5, option B; page-local extras were
offered as option D and REJECTED). The portability promise only holds if the
KEY is the same word everywhere. If the audio page says `inventory_table` and
the video page says `inventory`, the shared paragraph breaks on the paste -- and
it breaks as a dead reference on a page that otherwise looks perfectly fine. A
declaration above the page is the only thing that can guarantee the spelling,
so an undeclared slot is REPORTED rather than quietly honoured.

Slots are declared PER TYPE and inherit through `extends`, exactly like
`requires` and `optional`. A slot legal on `reference` is not thereby legal on
`procedure`; that is the deliberate cost of a per-type vocabulary over one
global list (option C, also rejected).

⚠️ WHY THIS IS NOT IN objects.py, WHICH IS WHERE YOU WOULD LOOK FIRST.
`objects._resolve()` flattens the `extends` chain but merges exactly three keys
-- requires, optional, renders -- so `data_slots` never reaches `meta["_spec"]`.
Teaching it a fourth key is the tidier change and it is the one to make when
somebody is in that file for another reason. It was not made here because
objects.py is over the size a single read returns whole, and rewriting a file
that cannot be read whole is how this project has clobbered working code
before. A small honest duplicate of the chain walk beats a rewrite from a
truncated read. The duplication is of the WALK, not of the data.
"""

from __future__ import annotations

from . import state


def _chain(type_name: str) -> list[dict]:
    """The declaration and its ancestors, nearest first. Cycle-safe."""
    decl = state.TYPES.get(type_name)
    chain: list[dict] = []
    seen: set = set()
    while decl and decl.get("type") not in seen:
        seen.add(decl.get("type"))
        chain.append(decl)
        parent = decl.get("extends")
        decl = state.TYPES.get(parent) if parent else None
    return chain


def data_slots(type_name: str) -> list[str]:
    """Every slot name a page of this type may declare, parent-first order."""
    slots: list[str] = []
    for decl in reversed(_chain(type_name)):
        for slot in decl.get("data_slots") or []:
            name = str(slot)
            if name not in slots:
                slots.append(name)
    return slots


def declares_slots(type_name: str) -> bool:
    """Does this type declare a data vocabulary at all.

    The distinction matters for the report wording. A type with NO `data_slots:`
    has not opted out of data, it has simply never been told about it -- so a
    page carrying `data:` under such a type should be told to declare the slot
    on the type, not accused of misspelling one.
    """
    return any(decl.get("data_slots") for decl in _chain(type_name))
