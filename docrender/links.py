"""Hook 03 -- links point at IDS, never at paths.

    [Main Stage](@main-stage)              a page in this site
    [the notes](@main-stage#venue-notes)   a heading on it
    [rep plot](@oph:rep-plot)              a page in a SIBLING site

Moving the file, renaming its folder, or retitling the page cannot break an
inbound link, because none of those things is what the link points at. Set
`id:` once and never change it; that promise is the whole mechanism.

CROSS-SITE, with the honest limit up front. Every site in the family publishes
/doc-index.json at its root on every build. `@peer:id` resolves against the
peer's index, fetched at BUILD time and cached to disk in the instance folder.
If a sibling renames a page, our links stay wrong until we rebuild.

The cache is COMMITTED, not ignored. An unreachable peer then degrades to
'last known good, marked stale' instead of taking our build down over somebody
else's outage.

WHAT A BROKEN REFERENCE LOOKS LIKE. A `<span>`: red, struck through, carrying a
`[broken link]` badge and a tooltip naming what was not found. **It is NOT an
anchor** -- no href, no navigation, nothing to click. The link does not ACT,
and the failure is not hidden. A marked-but-dead reference is useful
information on a site being written: it says a document is coming.

Code is skipped via util.sub_outside_code -- see that function for why.
"""

from __future__ import annotations

import html
import json
import re
import urllib.request
from pathlib import Path

from . import state
from .util import sub_outside_code

_LINK = re.compile(
    r"\[(?P<label>[^\]]*)\]\(@(?P<token>[A-Za-z0-9_.:-]+)(?P<anchor>#[A-Za-z0-9_-]+)?\)"
)

_TIMEOUT = 10


def _cache_path() -> Path:
    return Path(state.INSTANCE.get("dir", ".")) / "xref-cache.json"


def _dead(label: str, reason: str) -> str:
    """A span, deliberately. Marked as broken, impossible to click."""
    return (
        '<span class="docrender-dead" title="' + html.escape(reason, quote=True) + '">'
        + html.escape(label) + "</span>"
    )


def on_files(files, config):
    for f in files.documentation_pages():
        meta = state.BY_SRC.get(f.src_uri, {})
        page_id = meta.get("id")
        if not page_id:
            continue
        state.PAGES[page_id] = {
            "id": page_id,
            "type": meta.get("_type", "page"),
            "title": meta.get("title") or f.name,
            "url": f.url,
            "status": meta.get("status", "public"),
        }

    _load_peers()
    return files


def _load_peers() -> None:
    cache = {}
    path = _cache_path()
    if path.is_file():
        try:
            cache = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cache = {}

    for slug, base in (state.INSTANCE.get("peers") or {}).items():
        url = str(base).rstrip("/") + "/doc-index.json"
        try:
            with urllib.request.urlopen(url, timeout=_TIMEOUT) as response:
                data = json.loads(response.read().decode("utf-8"))
            cache[slug] = data
            state.PEERS[slug] = data
        except Exception as exc:
            if slug in cache:
                state.PEERS[slug] = cache[slug]
                state.note(
                    "stale_xref",
                    "peer '" + slug + "' unreachable (" + str(exc)
                    + "); using cached index built "
                    + str(cache[slug].get("built", "unknown")),
                )
            else:
                state.note(
                    "stale_xref",
                    "peer '" + slug + "' unreachable (" + str(exc)
                    + ") and no cache exists. Every @" + slug
                    + ": reference will render as broken.",
                )

    if state.PEERS:
        try:
            path.write_text(
                json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        except OSError:
            pass


def on_page_markdown(markdown, page, config, files):
    src = page.file.src_uri

    def replace(match):
        label = match.group("label")
        token = match.group("token")
        anchor = match.group("anchor") or ""

        if ":" in token:
            slug, _, foreign_id = token.partition(":")
            peer = state.PEERS.get(slug)
            if not peer:
                state.note("dead_links", src + ": unknown peer site '" + slug + "'")
                return _dead(label, "unknown peer site: " + slug)
            hit = next(
                (c for c in peer.get("pages", []) if c.get("id") == foreign_id), None
            )
            if not hit:
                state.note(
                    "dead_links",
                    src + ": '" + foreign_id + "' not found in peer '" + slug + "'",
                )
                return _dead(label, "not found in " + slug + ": " + foreign_id)
            base = str(peer.get("base_url", "")).rstrip("/")
            return (
                "[" + label + "](" + base + "/" + str(hit.get("url", "")) + anchor
                + "){ .docrender-xref }"
            )

        hit = state.PAGES.get(token)
        if not hit:
            state.note("dead_links", src + ": no page with id '" + token + "'")
            return _dead(label, "no page yet with id: " + token)

        depth = page.file.url.count("/")
        prefix = "../" * depth
        return "[" + label + "](" + prefix + str(hit.get("url", "")) + anchor + ")"

    return sub_outside_code(_LINK, replace, markdown)
