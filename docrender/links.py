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

⚠️ CODE IS NOT CONTENT (fixed 2026-08-03, first live build).
Substitution SKIPS fenced blocks and inline code spans. Without that, the very
page that teaches this syntax has its examples rewritten into the output it is
trying to explain -- `[Main Stage](@main-stage)` was rendering as
`[Main Stage](../../venues/example-house/main-stage/)` inside a code fence, so
the authoring guide silently taught the wrong thing.

=============================================================================
AN UNRESOLVED LINK FAILS QUIETLY (CHANGED 2026-08-03, Michael)
=============================================================================
It renders as PLAIN TEXT -- the label, unlinked, unstyled -- and lands in the
build report. It does not get a strikethrough, a red colour, or a
`[broken link]` badge.

The original loud marker was wrong, and the reasoning that produced it was
wrong in an instructive way. The argument was "a dead link that looks alive is
worse than a missing one," which is true for a READER of a finished site, and
irrelevant to how these sites actually get built: a page routinely points at
something not written yet, and every one of those became a red strikethrough
shouting at a reader about a problem only the author can fix and only the
author cares about.

So the audiences split. The AUTHOR needs to know, and gets it in the build
report, which is where a build problem belongs. The READER gets a sentence
that still reads as a sentence, with a phrase that simply is not a link yet.

The forward reference survives either way -- the text stays, the id stays in
the source, and it becomes a live link the moment the target exists.
"""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

from . import state

# Captures the LABEL too, because an unresolved link now renders as that label
# and nothing else. The old pattern started at `](` and could not see it.
_LINK = re.compile(
    r"\[(?P<label>[^\]]*)\]\(@(?P<token>[A-Za-z0-9_.:-]+)(?P<anchor>#[A-Za-z0-9_-]+)?\)"
)

# Fenced blocks (``` or ~~~, any indent, any info string) and inline spans.
# Ordered longest-first so a fence is never mistaken for an inline span that
# happens to start with three backticks.
_PROTECTED = re.compile(
    r"(?ms)^[ \t]*(?P<f>`{3,}|~{3,}).*?(?:^[ \t]*(?P=f)[ \t]*$|\Z)"
    r"|(?P<t>`+)(?:.|\n)*?(?P=t)"
)

_TIMEOUT = 10


def _cache_path() -> Path:
    return Path(state.INSTANCE.get("dir", ".")) / "xref-cache.json"


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
                    + ": link will render as plain text.",
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
        label = match.group("label")
        token = match.group("token")
        anchor = match.group("anchor") or ""

        # Unresolved: hand back the label as ordinary prose. The sentence still
        # reads; the author hears about it in the build report.
        if ":" in token:
            slug, _, foreign_id = token.partition(":")
            peer = state.PEERS.get(slug)
            if not peer:
                state.note("dead_links", src + ": unknown peer site '" + slug + "'")
                return label
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
                return label
            base = str(peer.get("base_url", "")).rstrip("/")
            target = base + "/" + str(hit.get("url", "")) + anchor
            return "[" + label + "](" + target + "){ .docrender-xref }"

        hit = state.PAGES.get(token)
        if not hit:
            state.note("dead_links", src + ": no page with id '" + token + "'")
            return label

        # Relative, so the site survives being served from a subpath, which is
        # exactly what a project Pages URL is.
        depth = page.file.url.count("/")
        prefix = "../" * depth
        return "[" + label + "](" + prefix + str(hit.get("url", "")) + anchor + ")"

    # Walk the gaps BETWEEN protected regions and substitute only there, so a
    # code sample survives verbatim. Rebuilding from slices keeps every
    # protected region byte-identical rather than round-tripping it.
    out = []
    cursor = 0
    for guard in _PROTECTED.finditer(markdown):
        out.append(_LINK.sub(replace, markdown[cursor:guard.start()]))
        out.append(guard.group(0))
        cursor = guard.end()
    out.append(_LINK.sub(replace, markdown[cursor:]))
    return "".join(out)
