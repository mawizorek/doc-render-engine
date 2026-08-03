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
If a sibling renames a page, our links stay wrong until we rebuild. A nightly
scheduled build closes that gap to about a day; a repository_dispatch from a
peer's own deploy closes it to minutes. That is as close to real-time as a
static site gets without adding a server, and adding a server to a
documentation archive is a bad trade.

The cache is COMMITTED, not ignored. An unreachable peer then degrades to
'last known good, marked stale' instead of taking our build down over somebody
else's outage.

A link that resolves nowhere renders as a visible marker and lands in the
report. It does not fail the build. See objects.py for why.

⚠️ CODE IS NOT CONTENT (fixed 2026-08-03, first live build).
Substitution SKIPS fenced blocks and inline code spans. Without that, the very
page that teaches this syntax has its examples rewritten into the output it is
trying to explain -- `[Main Stage](@main-stage)` was rendering as
`[Main Stage](../../venues/example-house/main-stage/)` inside a code fence, so
the authoring guide silently taught the wrong thing. Any transform that edits
markdown text has this bug available to it; this is the one that found it.
"""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

from . import state

_LINK = re.compile(r"\]\(@([A-Za-z0-9_.:-]+)(#[A-Za-z0-9_-]+)?\)")

# Fenced blocks (``` or ~~~, any indent, any info string) and inline spans
# (one or more backticks). Ordered longest-first so a fence is never mistaken
# for an inline span that happens to start with three backticks.
_PROTECTED = re.compile(
    r"(?ms)^[ \t]*(?P<f>`{3,}|~{3,}).*?(?:^[ \t]*(?P=f)[ \t]*$|\Z)"
    r"|(?P<t>`+)(?:.|\n)*?(?P=t)"
)

_TIMEOUT = 10


def _cache_path() -> Path:
    return Path(state.INSTANCE.get("dir", ".")) / "xref-cache.json"


def _dead(reason: str) -> str:
    """Render a visibly broken link rather than a plausible wrong one."""
    return '](#){ .docrender-dead title="' + reason + '" }'


def on_files(files, config):
    """Build the local id map, then load the peers'.

    Runs after visibility has pruned, so PAGES holds only pages that will
    actually exist. A link can therefore never resolve to a 404 of our own
    making, only to a page that was never written.
    """
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

    peers = state.INSTANCE.get("peers") or {}
    for slug, base in peers.items():
        url = str(base).rstrip("/") + "/doc-index.json"
        try:
            with urllib.request.urlopen(url, timeout=_TIMEOUT) as response:
                data = json.loads(response.read().decode("utf-8"))
            cache[slug] = data
            state.PEERS[slug] = data
        except Exception as exc:  # network, JSON, DNS -- all the same answer
            if slug in cache:
                state.PEERS[slug] = cache[slug]
                built = cache[slug].get("built", "unknown")
                state.note(
                    "stale_xref",
                    "peer '" + slug + "' unreachable (" + str(exc)
                    + "); using cached index built " + str(built),
                )
            else:
                state.note(
                    "stale_xref",
                    "peer '" + slug + "' unreachable (" + str(exc)
                    + ") and no cache exists. Every @" + slug
                    + ": link will render as a dead marker.",
                )

    if state.PEERS:
        try:
            path.write_text(
                json.dumps(cache, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass


def on_page_markdown(markdown, page, config, files):
    src = page.file.src_uri

    def replace(match):
        token = match.group(1)
        anchor = match.group(2) or ""

        if ":" in token:
            slug, _, foreign_id = token.partition(":")
            peer = state.PEERS.get(slug)
            if not peer:
                state.note("dead_links", src + ": unknown peer site '" + slug + "'")
                return _dead("unknown peer site: " + slug)
            hit = None
            for candidate in peer.get("pages", []):
                if candidate.get("id") == foreign_id:
                    hit = candidate
                    break
            if not hit:
                state.note(
                    "dead_links",
                    src + ": '" + foreign_id + "' not found in peer '" + slug + "'",
                )
                return _dead("not found in " + slug + ": " + foreign_id)
            base = str(peer.get("base_url", "")).rstrip("/")
            target = base + "/" + str(hit.get("url", "")) + anchor
            return "](" + target + "){ .docrender-xref }"

        hit = state.PAGES.get(token)
        if not hit:
            state.note("dead_links", src + ": no page with id '" + token + "'")
            return _dead("no page with id: " + token)

        # Relative, so the site survives being served from a subpath, which is
        # exactly what a project Pages URL is.
        depth = page.file.url.count("/")
        prefix = "../" * depth
        return "](" + prefix + str(hit.get("url", "")) + anchor + ")"

    # Walk the gaps BETWEEN protected regions and substitute only there, so a
    # code sample survives verbatim. Rebuilding the string from slices keeps
    # every protected region byte-identical rather than round-tripping it.
    out = []
    cursor = 0
    for guard in _PROTECTED.finditer(markdown):
        out.append(_LINK.sub(replace, markdown[cursor:guard.start()]))
        out.append(guard.group(0))
        cursor = guard.end()
    out.append(_LINK.sub(replace, markdown[cursor:]))
    return "".join(out)
