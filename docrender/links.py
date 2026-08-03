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

⚠️ CODE IS NOT CONTENT. Substitution SKIPS fenced blocks and inline code spans.
Without that, the very page that teaches this syntax has its examples rewritten
into the output it is trying to explain.

=============================================================================
WHAT A DEAD LINK LOOKS LIKE, and the distinction that took two tries
=============================================================================
An unresolved reference renders as a `<span>`: red, struck through, carrying a
`[broken link]` badge and a tooltip saying what was not found.

**It is NOT an anchor.** No href, no navigation, no pointer cursor, nothing to
click. "Fail silently" means the link does not ACT -- it does not take a reader
somewhere broken -- and it does NOT mean the failure is hidden. The visual
marker is the point: it is a visible reference to a document that is coming,
which is genuinely useful information on a site being written.

Briefly rendered as plain text (PR #12) on a misreading of "fail silently."
That was wrong in both directions at once: it hid the fact from the reader AND
erased the forward reference from the page. Reverted.

Three audiences, three signals, all of them correct now:
  * the READER sees a phrase marked as not-yet-a-document, and cannot click it
    into a 404;
  * the AUTHOR sees it on the page while writing;
  * the BUILD reports every one of them in the report block.
"""

from __future__ import annotations

import html
import json
import re
import urllib.request
from pathlib import Path

from . import state

_LINK = re.compile(
    r"\[(?P<label>[^\]]*)\]\(@(?P<token>[A-Za-z0-9_.:-]+)(?P<anchor>#[A-Za-z0-9_-]+)?\)"
)

_PROTECTED = re.compile(
    r"(?ms)^[ \t]*(?P<f>`{3,}|~{3,}).*?(?:^[ \t]*(?P=f)[ \t]*$|\Z)"
    r"|(?P<t>`+)(?:.|\n)*?(?P=t)"
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

    out = []
    cursor = 0
    for guard in _PROTECTED.finditer(markdown):
        out.append(_LINK.sub(replace, markdown[cursor:guard.start()]))
        out.append(guard.group(0))
        cursor = guard.end()
    out.append(_LINK.sub(replace, markdown[cursor:]))
    return "".join(out)
