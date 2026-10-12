"""Stage 05b support -- `type: binder`: a COLLECTION, resolved. No MkDocs event.

Spec: `specs/binder-type.md` (2026-10-11). A program is completed in order; a
binder is kept and consulted. Same `chain:` key, opposite behaviour, so the two
answers live behind two resolvers:

    nav.declared()          reading orders (index, program): prev/next, strips
    collection.binders()    collections (binder): NEVER wired into navigation
    collection.expanded()   one binder resolved, for binder.py / packet.py /
                            chainlist.py

⚠️ EXPANSION IS PROGRAMS ONLY, ONE LEVEL (B3). A program id opens into [its own
page, then its chain]; that page is the section's tab sheet (B7). An `index` id
stays ONE page -- expanding a hub would pull a folder in from one listed id. A
binder id is REFUSED: one hop, the alias-of-alias law. A `{section, subtitle}`
mapping passes through as a separator (B6); `nav.declared()` reports one found
on any other type. Repeats: first appearance wins, later ones are noted (B4).

⭐ ITS OWN MODULE because nav.py sat at the ~22KB read ceiling, and because the
concern is different: nav.py WIRES an order, this COLLECTS a list.
"""

from __future__ import annotations

from . import nav, state


def binders(report: bool = True) -> dict:
    """{src_uri: raw chain items} for every `type: binder` with a LIST chain.

    Items are id strings and `{section, subtitle}` mappings, untouched. Use
    `expanded()` for the resolved list; this exists so legality is reported in
    ONE place.
    """
    out: dict = {}
    for src, meta in state.BY_SRC.items():
        if not nav.is_binder(meta):
            continue
        raw = (meta or {}).get("chain")
        if raw is None:
            if report:
                state.note(
                    "missing_required",
                    src + " is `type: binder` and declares no `chain:`. A binder "
                    "IS its list, so there is nothing to collect.",
                )
            continue
        if not isinstance(raw, list):
            if report:
                state.note(
                    "missing_required",
                    src + " is `type: binder` and its `chain:` is a "
                    + type(raw).__name__ + ", not a list. A face (`\"@id\"`) of "
                    "or as a binder is OUT of v1 (specs/binder-type.md). IGNORED.",
                )
            continue
        out[src] = list(raw)
    return out


def expanded(src: str, report: bool = False) -> list:
    """One binder's chain, resolved. Entries, in order:

        {"section": title, "subtitle": text}    a separator (B6)
        {"id": page id, "via": program id}      a page; `via` is "" for a page
                                                listed directly, or the program
                                                it was reached through (B3)

    `report=True` is passed by exactly ONE caller per build (binder.py) so each
    finding prints once.
    """
    raw = binders(report=False).get(src) or []
    chains = nav.declared(report=False)
    id_src: dict = {}
    for s, m in state.BY_SRC.items():
        pid = str((m or {}).get("id") or "").strip()
        if pid and pid not in id_src:
            id_src[pid] = s

    out: list = []
    seen: dict = {}

    def add(pid, via, pos):
        if pid in seen:
            if report:
                state.note(
                    "notes",
                    src + " binder reaches `" + pid + "` again at entry " + str(pos)
                    + (" (inside `" + via + "`)" if via else "") + "; it stays at "
                    "its first appearance, entry " + str(seen[pid]) + ".",
                )
            return
        seen[pid] = pos
        out.append({"id": pid, "via": via})

    for n, item in enumerate(raw, 1):
        if isinstance(item, dict):
            title = str(item.get("section") or "").strip()
            if not title:
                if report:
                    state.note(
                        "missing_required",
                        src + " binder entry " + str(n) + " is a mapping with no "
                        "`section:` title. SKIPPED.",
                    )
                continue
            out.append({"section": title, "subtitle": str(item.get("subtitle") or "").strip()})
            continue
        pid = str(item).strip().lstrip("@")
        if not pid:
            continue
        tsrc = id_src.get(pid)
        if tsrc is None:
            if report:
                state.note(
                    "dead_links",
                    src + " binder names `" + pid + "`, which is not the id of any "
                    "page on this site. SKIPPED.",
                )
            continue
        tmeta = state.BY_SRC.get(tsrc, {}) or {}
        if nav.is_binder(tmeta):
            if report:
                state.note(
                    "missing_required",
                    src + " binder names the binder `" + pid + "`. REFUSED -- one "
                    "hop, never a binder inside a binder.",
                )
            continue
        if nav._type(tmeta) == "program" and tsrc in chains:
            add(pid, "", n)  # the program's own page: its section's tab sheet (B7)
            for mid in chains[tsrc]:
                add(mid, pid, n)
        else:
            add(pid, "", n)
    return out
