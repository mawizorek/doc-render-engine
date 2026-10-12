"""Stage 05b -- BINDERS: the print composer's presets.

Spec: `specs/binder-type.md` (2026-10-11), which supersedes `specs/print-compose.md`
§6 P1/P2. The composer itself is `assets/printcompose.js`.

=============================================================================
📚 A BINDER IS ITS OWN TYPE NOW. THE FLAG IS RETIRING.
=============================================================================

    ---
    title: Tech Binder
    type: binder
    chain:
      - section: "Safety"
      - program-general-safety     # expands: its page, then its chain
      - policy-ladders
    ---

> Michael, 2026-10-11: *"what if i want to assemble a bundle of programs."*

A program is completed in order; a binder is kept and consulted. Same `chain:`
key, resolved by `collection.expanded()`, never wired into prev/next or a strip
(`nav.declared()` skips binders). ⭐ That retires the old price this file used to
state -- "a binder IS a program, so its members also get its flow strip".

🕰 ONE DEPRECATION CYCLE (B2). `type: program` + `binder: true` is still offered
as a preset, and reported, so the live binders do not vanish from the composer
mid-migration. `binder:` on any other page, or `binder: false`, is a dead key and
reported. Delete the legacy path once the build report is clean of it.

⭐ THE MENU IS GENERATED, NEVER DECLARED (B9). Presets carry a `kind`:
`binder` for every `type: binder` (and the legacy flag), `program` for every
`type: program` with `export: [packet]`. No `print-menu:` key exists.

🔴 PUBLIC MEMBERS ONLY, THE PACKET'S LEAK RULE VERBATIM (B10). The composer lists
pages from the search index, which holds public pages only; a preset naming an
`unlisted` page would be the one way to print something a reader cannot find.

⭐ `binders.json` ALSO CARRIES `ids`, {url: id} for every public page, so the
composer's "Copy as binder" can hand back real `chain:` ids instead of URLs.
Written on every build, even with no binder declared -- no file means this hook
is not registered, which is a different fact from "no binders". Section entries
ride in `pages` as `{section, subtitle}` with no `loc`; the composer skips them
until separator sheets are built.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import collection, nav, packet, state

_PLAN: list = []
_IDS: dict = {}


def _meta(src) -> dict:
    return state.BY_SRC.get(src, {}) or {}


def _public(src) -> bool:
    return str(_meta(src).get("status") or "").strip().lower() == "public"


def _title(src, page=None) -> str:
    return str(_meta(src).get("title") or getattr(page, "title", "") or src)


def _type(src) -> str:
    return str(_meta(src).get("type") or "").strip().lower()


def _flag(src) -> None:
    """Report every `binder:` key. B2: the flag retires into the type."""
    meta = _meta(src)
    if "binder" not in meta:
        return
    val, kind = meta.get("binder"), _type(src)
    if kind == nav.BINDER:
        why = "is redundant on `type: binder`. Remove it."
    elif val is True and kind == "program":
        why = ("is DEPRECATED. Still offered as a preset this cycle; switch the page to "
               "`type: binder`, or drop the key if it is a program people complete.")
    else:
        why = "does nothing on a `type: " + (kind or "?") + "` page. Remove it."
    state.note("missing_required", src + " `binder: " + str(val).lower() + "` " + why)


def _pages(src, ids, by_id, urls, refuse) -> list:
    out = []
    for item in ids:
        if isinstance(item, dict):
            out.append({"section": item["section"], "subtitle": item.get("subtitle", "")})
            continue
        page = by_id.get(item)
        if page is None:
            continue  # nav.py already reported the dead id.
        psrc = getattr(getattr(page, "file", None), "src_uri", "")
        if not _public(psrc):
            if refuse:
                state.note(
                    "missing_required",
                    src + " binder REFUSES `" + item + "` (" + psrc + "): not"
                    " `public`. The composer only prints what a reader can find.",
                )
            continue
        out.append({"loc": urls.get(psrc, ""), "title": _title(psrc, page)})
    return out


def on_nav(nav_obj, config, files):
    """Resolve every preset into ordered page URLs."""
    _PLAN.clear()
    _IDS.clear()
    by_id, _by_src = nav._built(files)
    urls = {}
    for f in files:
        page = getattr(f, "page", None)
        if page is not None and getattr(page, "is_page", False):
            src = getattr(f, "src_uri", "")
            urls[src] = getattr(f, "url", "")
            pid = str(_meta(src).get("id") or "").strip()
            if pid and _public(src):
                _IDS[urls[src]] = pid

    chains = nav.declared(report=False)
    binds = collection.binders(report=True)
    for src in sorted(state.BY_SRC):
        _flag(src)
        meta = _meta(src)
        pid = str(meta.get("id") or "").strip()
        if src in binds:
            kind = "binder"
            ids = [
                e if "section" in e else e["id"]
                for e in collection.expanded(src, report=True)
            ]
        elif _type(src) == "program" and meta.get("binder") is True:
            kind = "binder"  # legacy flag, one cycle (B2)
            ids = chains.get(src) or []
        elif _type(src) == "program" and "packet" in packet.kinds(meta, src):
            kind = "program"
            ids = ([pid] if pid else []) + list(chains.get(src) or [])
        else:
            continue
        declared = [i for i in ids if not isinstance(i, dict)]
        if not declared:
            state.note(
                "missing_required",
                src + " is a " + kind + " preset with no usable `chain:`. NOT OFFERED.",
            )
            continue
        # Programs are refused-and-named by packet.py already; say it once.
        pages = _pages(src, ids, by_id, urls, refuse=(kind == "binder"))
        real = [p for p in pages if "loc" in p]
        if not real:
            state.note(
                "missing_required",
                src + " " + kind + " resolved ZERO of " + str(len(declared))
                + " members. NOT OFFERED.",
            )
            continue
        _PLAN.append({"id": pid or src, "title": _title(src), "kind": kind, "pages": pages})
        state.note(
            "notes",
            src + " " + kind.upper() + ": " + str(len(real)) + " of " + str(len(declared))
            + " member(s), offered as a preset in the print composer.",
        )
    _PLAN.sort(key=lambda p: (p["kind"] != "binder", p["title"].lower()))
    return nav_obj


def on_post_build(config):
    """Write `binders.json` for `assets/printcompose.js`."""
    out = Path(str(config.site_dir)) / "binders.json"
    try:
        out.write_text(
            json.dumps({"binders": _PLAN, "ids": _IDS}, indent=1), encoding="utf-8"
        )
    except OSError:
        state.note(
            "missing_required",
            "binders.json could not be written; the composer will show no binders.",
        )
