"""Hook 01 -- read every page's frontmatter and hold it to its type.

This is the upgrade the whole redesign exists for. v1 had ONE page shape: every
file rendered the same way, so any structure a venue page had was structure the
author typed by hand, every time, slightly differently.

Here a page declares `type:` and the matching objects/<type>.yml says what that
kind of thing must have, may have, and how it draws. Add a field to every venue
in the family and it is one line in one declaration, not thirty edits.

Runs FIRST, before visibility, deliberately: a page with a broken declaration
is broken whether or not it happens to be hidden today. Catching it only once
someone publishes it means catching it at the worst possible moment.

FAILURE POSTURE: warn, never die. v1 built with --strict and on 2026-08-01 a
single typo froze the entire live site twice in forty minutes while Pages
cheerfully kept serving a stale commit. Broken things get reported and render
as visible markers; the deploy continues. A site that stops updating silently
is worse than a site with one ugly page on it.
"""

from __future__ import annotations

from . import state
from .util import read_frontmatter

VALID_STATUS = {"hidden", "unlisted", "gated", "public"}


def _resolve(type_name: str) -> dict:
    """Flatten a declaration and its `extends` chain into one spec."""
    decl = state.TYPES.get(type_name)
    if not decl:
        return {}
    merged = {"requires": [], "optional": [], "renders": []}
    chain, seen = [], set()
    while decl and decl.get("type") not in seen:
        seen.add(decl.get("type"))
        chain.append(decl)
        parent = decl.get("extends")
        decl = state.TYPES.get(parent) if parent else None
    for decl in reversed(chain):
        for key in ("requires", "optional", "renders"):
            for value in decl.get(key) or []:
                if value not in merged[key]:
                    merged[key].append(value)
        if decl.get("layout"):
            merged["layout"] = decl["layout"]
    return merged


def on_files(files, config):
    seen_ids: dict[str, str] = {}

    for f in files.documentation_pages():
        meta = read_frontmatter(f.abs_src_path)
        state.BY_SRC[f.src_uri] = meta

        status = meta.get("status")
        if status not in VALID_STATUS:
            # Inherited from v1 and kept as the single most valuable rule in
            # the contract: no status means the page does not publish. Nothing
            # reaches the public web because someone forgot a line.
            state.note(
                "missing_status",
                f"{f.src_uri}: status is "
                + (f"'{status}', not one of {sorted(VALID_STATUS)}" if status
                   else "missing -- page will NOT be built"),
            )

        page_id = meta.get("id")
        if page_id:
            if page_id in seen_ids:
                state.note(
                    "duplicate_id",
                    f"'{page_id}' claimed by both {seen_ids[page_id]} and "
                    f"{f.src_uri}. Links to it are a coin flip.",
                )
            else:
                seen_ids[page_id] = f.src_uri

        type_name = meta.get("type", "page")
        if type_name not in state.TYPES:
            state.note(
                "unknown_type",
                f"{f.src_uri}: type '{type_name}' is not declared. Falling "
                f"back to 'page'. Known: {', '.join(sorted(state.TYPES))}",
            )
            type_name = "page"

        spec = _resolve(type_name)
        missing = [k for k in spec.get("requires", []) if not meta.get(k)]
        if missing:
            state.note(
                "missing_required",
                f"{f.src_uri} (type: {type_name}) is missing required "
                f"{', '.join(missing)}",
            )

        meta["_type"] = type_name
        meta["_spec"] = spec

    return files
