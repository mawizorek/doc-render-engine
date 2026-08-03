"""Hook 01 -- read every page's frontmatter, hold it to its type, and DRAW it.

This is the upgrade the whole redesign exists for. v1 had ONE page shape: every
file rendered the same way, so any structure a venue page had was structure the
author typed by hand, every time, slightly differently.

Here a page declares `type:` and objects/<type>.yml says what that kind of
thing must have, may have, and how it draws. Three consequences worth stating
plainly:

  * every space in the family gets the same spec table, because the TYPE draws
    it and not the author;
  * a missing required field is caught at build time, with the file and the
    field named;
  * adding a field to every venue is one line in one declaration, not thirty
    edits across three repos.

This is FileMaker thinking pointed at a static site. _base.yml is the parent
table, each type file is a table occurrence, requires/optional are the field
list, layout is the layout, and a page's frontmatter block is the record. That
correspondence is intentional: the repo objects are deliberately modelled after
FMP structure so the two runtimes share one vocabulary.

Runs FIRST, before visibility, deliberately: a page with a broken declaration
is broken whether or not it happens to be hidden today. Catching it only when
someone publishes is catching it at the worst possible moment.

FAILURE POSTURE: warn, never die. v1 built with --strict and on 2026-08-01 a
single typo froze the entire live site twice in forty minutes while Pages
cheerfully kept serving a stale commit. Broken things get reported and render
as visible markers; the deploy continues. A site that stops updating silently
is worse than a site with one ugly page on it.
"""

from __future__ import annotations

import re

from . import state
from .util import read_frontmatter, slug_title

VALID_STATUS = {"hidden", "unlisted", "gated", "public"}


def _resolve(type_name: str) -> dict:
    """Flatten a declaration and its `extends` chain into one spec."""
    decl = state.TYPES.get(type_name)
    if not decl:
        return {}
    merged: dict = {"requires": [], "optional": [], "renders": []}
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
        if decl.get("label"):
            merged["label"] = decl["label"]
    return merged


def on_files(files, config):
    seen_ids: dict[str, str] = {}

    for f in files.documentation_pages():
        meta = read_frontmatter(f.abs_src_path)
        state.BY_SRC[f.src_uri] = meta

        status = meta.get("status")
        if status not in VALID_STATUS:
            # The single most valuable rule in the contract, inherited from v1:
            # no status means the page does not publish. Nothing reaches the
            # public web because somebody forgot a line.
            detail = (
                "is '" + str(status) + "', not one of " + str(sorted(VALID_STATUS))
                if status else "is missing -- page will NOT be built"
            )
            state.note("missing_status", f.src_uri + ": status " + detail)

        page_id = meta.get("id")
        if page_id:
            if page_id in seen_ids:
                state.note(
                    "duplicate_id",
                    "'" + str(page_id) + "' claimed by both " + seen_ids[page_id]
                    + " and " + f.src_uri + ". Links to it are a coin flip.",
                )
            else:
                seen_ids[page_id] = f.src_uri

        type_name = meta.get("type", "page")
        if type_name not in state.TYPES:
            state.note(
                "unknown_type",
                f.src_uri + ": type '" + str(type_name) + "' is not declared. "
                + "Falling back to 'page'. Known: "
                + ", ".join(sorted(state.TYPES)),
            )
            type_name = "page"

        spec = _resolve(type_name)
        missing = [k for k in spec.get("requires", []) if not meta.get(k)]
        if missing:
            state.note(
                "missing_required",
                f.src_uri + " (type: " + type_name + ") is missing required "
                + ", ".join(missing),
            )

        meta["_type"] = type_name
        meta["_spec"] = spec

    return files


def _spec_table(meta: dict, fields: list[str]) -> str:
    rows = []
    for field in fields:
        value = meta.get(field)
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        rows.append("| " + slug_title(field) + " | " + str(value) + " |")
    if not rows:
        return ""
    return "\n".join(
        ['<div class="dr-spec" markdown="1">', "", "| | |", "| --- | --- |"]
        + rows + ["", "</div>", ""]
    )


def _insert_after_lede(markdown: str, block: str) -> str:
    """Place generated content after the H1 and its opening paragraph.

    The first paragraph is the lede and is also what a search result shows, so
    nothing generated may come before it. Anything we cannot parse confidently
    goes at the top instead of guessing wrong and splitting a sentence.
    """
    lines = markdown.splitlines()
    heading = next((i for i, ln in enumerate(lines) if ln.startswith("# ")), None)
    if heading is None:
        return block + "\n" + markdown
    i = heading + 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    while i < len(lines) and lines[i].strip():
        i += 1
    return "\n".join(lines[:i] + ["", block] + lines[i:])


def on_page_markdown(markdown, page, config, files):
    """Draw whatever the page's type declares.

    Two directives are implemented in engine v1:

        spec_table: [a, b, c]      a two-column table of those fields
        callout_if_missing: [a]    a visible note naming what is not known yet

    The second is the quiet one that earns its place. A venue page missing its
    grid height currently looks identical to a venue that genuinely has no
    grid. Saying 'this is not documented yet' out loud turns a silent gap into
    a visible one, which is the only way it ever gets filled.
    """
    meta = state.BY_SRC.get(page.file.src_uri, {})
    spec = meta.get("_spec") or {}
    blocks = []

    for directive in spec.get("renders", []):
        if not isinstance(directive, dict):
            continue
        for name, fields in directive.items():
            if name == "spec_table":
                table = _spec_table(meta, list(fields or []))
                if table:
                    blocks.append(table)
            elif name == "callout_if_missing":
                absent = [f for f in (fields or []) if not meta.get(f)]
                if absent:
                    blocks.append(
                        '!!! note "Not documented yet"\n\n    '
                        + ", ".join(slug_title(a) for a in absent)
                        + " for this page "
                        + ("has" if len(absent) == 1 else "have")
                        + " not been recorded. Treat as unknown, not as absent."
                    )

    if not blocks:
        return markdown
    return _insert_after_lede(markdown, "\n\n".join(blocks))
