"""Stage 05b -- BINDERS: a program page offered to the print composer as a preset.

BUILD 11 phase 2. Spec: `specs/print-compose.md` §Phase 2.

> Michael, 2026-09-28: *"build binders by id - and keep it simple / when defining -
> one file per binder (it's just a program page type) / yes, I'd like to see them as
> preset options in the composer."*

=============================================================================
⭐ A BINDER IS A PROGRAM PAGE WITH ONE MORE KEY. NO NEW TYPE, NO NEW LIST.
=============================================================================

    ---
    title: Tech Binder
    type: program
    binder: true
    chain:
      - policy-fire
      - policy-housekeeping
    ---

🚫 THE PAGE LIST IS `chain:`, READ THROUGH `nav.declared()`. A `binder:` list of its
own would be a second vocabulary for "these ids, in this order" -- the shape `nav.py`
refused as `steps:` and `packet.py` refused by reading the same resolver. One key, one
resolver, now four consumers. ⚠️ CONSEQUENCE, STATED: a binder IS a program, so its
members also get its flow strip. That is the price of "just a program page type". If
a binder ever needs to be print-only, that is a new type, not a flag on this one.

🔴 PUBLIC MEMBERS ONLY, THE PACKET'S LEAK RULE VERBATIM. The composer lists pages from
the search index, which holds public pages only; a preset naming an `unlisted` page
would be the one way to print something a reader cannot find. Refused and named.

⭐ `binders.json` ALSO CARRIES `ids`, {url: id} for every public page, so the
composer's "Copy as binder" can hand back real `chain:` ids instead of URLs. Written
on every build, even with no binder declared -- no file means this hook is not
registered, which is a different fact from "no binders".
"""

from __future__ import annotations

import json
from pathlib import Path

from . import nav, state

_PLAN: list = []
_IDS: dict = {}


def _meta(src) -> dict:
    return state.BY_SRC.get(src, {}) or {}


def _public(src) -> bool:
    return str(_meta(src).get("status") or "").strip().lower() == "public"


def _title(src, page=None) -> str:
    return str(_meta(src).get("title") or getattr(page, "title", "") or src)


def on_nav(nav_obj, config, files):
    """Resolve every `binder: true` program into ordered page URLs."""
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
    for src in sorted(state.BY_SRC):
        meta = _meta(src)
        if meta.get("binder") is not True:
            continue
        if str(meta.get("type") or "").strip().lower() != "program":
            state.note(
                "missing_required",
                src + " declares `binder: true` and is not `type: program`. IGNORED"
                " -- a binder is a program's `chain:`, so there is nothing to collect.",
            )
            continue
        ids = chains.get(src)
        if not ids:
            state.note(
                "missing_required",
                src + " declares `binder: true` and no usable `chain:`. NO BINDER.",
            )
            continue
        pages = []
        for pid in ids:
            page = by_id.get(pid)
            if page is None:
                continue  # nav.py already reported the dead id.
            psrc = getattr(getattr(page, "file", None), "src_uri", "")
            if not _public(psrc):
                state.note(
                    "missing_required",
                    src + " binder REFUSES `" + pid + "` (" + psrc + "): not"
                    " `public`. The composer only prints what a reader can find.",
                )
                continue
            pages.append({"loc": urls.get(psrc, ""), "title": _title(psrc, page)})
        if not pages:
            state.note(
                "missing_required",
                src + " binder resolved ZERO of " + str(len(ids)) + " members. NOT OFFERED.",
            )
            continue
        _PLAN.append({
            "id": str(meta.get("id") or src),
            "title": _title(src),
            "pages": pages,
        })
        state.note(
            "notes",
            src + " BINDER: " + str(len(pages)) + " of " + str(len(ids))
            + " member(s), offered as a preset in the print composer.",
        )
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
