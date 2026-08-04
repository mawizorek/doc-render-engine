"""Hook 03 -- links point at IDS, never at paths.

    [Main Stage](@main-stage)                 a page in this site
    [the notes](@main-stage#venue-notes)      a heading on it
    [rep plot](@oph:rep-plot)                 a page in a SIBLING site
    [the schedule](@data:schedule_table)      a data file beside THIS page

Moving the file, renaming its folder, or retitling the page cannot break an
inbound link, because none of those things is what the link points at. Set
`id:` once and never change it; that promise is the whole mechanism.

⚠️ THE COLON IS NOT ONLY A PEER SEPARATOR ANY MORE (2026-08-04). It used to be:
`token.partition(":")` and the left half was a peer site slug, full stop. Now a
RESERVED PREFIX is checked first, and only an unreserved word falls through to
peer lookup. Without that check `@data:schedule_table` resolves as peer site
`data`, page `schedule_table`, and reports "unknown peer site: data" -- a
perfectly confident error naming the wrong subsystem.

⭐ THE RESERVED LIST IS DERIVED, NOT WRITTEN HERE. See docrender/prefixes.py. A
handler claims its own prefix at import time, so adding a namespace and
forgetting to reserve it is impossible rather than merely discouraged. Do NOT
add an `if token.startswith("data:")` to this file -- that is the version that
was considered and rejected, because it is how the third namespace gets
forgotten.

⚠️ A PEER MAY NOT BE SLUGGED WITH A RESERVED WORD. A site that named a peer
`data` used to lose that namespace silently, with nothing anywhere saying so.
It is reported at build now.

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
Same-site paths are resolved by util.relative_url -- see THAT function for the
root-index bug this file shipped with, and do not reintroduce a `../` count.
"""

from __future__ import annotations

import html
import json
import re
import urllib.request
from pathlib import Path

from . import prefixes, state
from .util import relative_url, sub_outside_code

_LINK = re.compile(
    r"\[(?P<label>[^\]]*)\]\(@(?P<token>[A-Za-z0-9_.:-]+)(?P<anchor>#[A-Za-z0-9_-]+)?\)"
)

#: A bare token that is obviously a FILENAME rather than a page id. The token
#: charset accepts dots, so `[x](@circuits-and-dimmers.tsv)` matches this regex
#: and would otherwise be reported as a missing PAGE -- sending the author to
#: look for a document when what they wanted was a data slot.
_DATA_EXT = re.compile(r"\.(tsv|csv|txt|json|ya?ml)$", re.IGNORECASE)

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

    configured = state.INSTANCE.get("peers") or {}

    # A peer slugged with a reserved word cannot be reached: the prefix is
    # claimed by a handler and never reaches peer lookup. Silent until now.
    for slug in prefixes.collisions(configured):
        state.note(
            "stale_xref",
            "peer site '" + slug + "' collides with the RESERVED prefix `@" + slug
            + ":`, claimed by " + (prefixes.owner(slug) or "this engine")
            + ". Every @" + slug + ": reference resolves to that handler, not to the "
            + "peer, so this site is unreachable by link. Rename the peer.",
        )

    for slug, base in configured.items():
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
            prefix, _, rest = token.partition(":")

            # RESERVED FIRST. An unreserved prefix is a peer slug, exactly as
            # before; a reserved one never reaches that branch.
            handler = prefixes.handler(prefix)
            if handler is not None:
                ref = handler(src, rest)
                if not ref:
                    state.note(
                        "dead_links",
                        src + ": no `" + prefix + "` slot named '" + rest
                        + "' on this page. It has to be declared in this page's "
                        + "`" + prefix + ":` frontmatter.",
                    )
                    return _dead(label, "no " + prefix + " slot on this page: " + rest)
                # An embedded table is an anchor on THIS page. A declared slot
                # that is never embedded is a link to the file itself, which is
                # a legitimate way to reference a sheet you do not render.
                target = "#" + ref["anchor"] if ref.get("anchor") else ref.get("href", "")
                return "[" + label + "](" + target + ")"

            peer = state.PEERS.get(prefix)
            if not peer:
                state.note("dead_links", src + ": unknown peer site '" + prefix + "'")
                return _dead(label, "unknown peer site: " + prefix)
            hit = next(
                (c for c in peer.get("pages", []) if c.get("id") == rest), None
            )
            if not hit:
                state.note(
                    "dead_links",
                    src + ": '" + rest + "' not found in peer '" + prefix + "'",
                )
                return _dead(label, "not found in " + prefix + ": " + rest)
            base = str(peer.get("base_url", "")).rstrip("/")
            return (
                "[" + label + "](" + base + "/" + str(hit.get("url", "")) + anchor
                + "){ .docrender-xref }"
            )

        hit = state.PAGES.get(token)
        if not hit:
            # A filename in the token slot is a different mistake from a missing
            # page, and saying "no page with id circuits-and-dimmers.tsv" sends
            # somebody hunting for a document that was never meant to exist.
            if _DATA_EXT.search(token):
                state.note(
                    "dead_links",
                    src + ": `@" + token + "` names a FILE. A data file is referenced "
                    + "by its slot -- `@data:<slot>` -- and the filename lives only in "
                    + "the page's `data:` frontmatter.",
                )
                return _dead(
                    label, "data files are referenced as @data:<slot>, not by filename"
                )
            state.note("dead_links", src + ": no page with id '" + token + "'")
            return _dead(label, "no page yet with id: " + token)

        # Resolved against THIS page, never from a separator count. The root
        # index page reports its url as `./` and broke that arithmetic.
        target = relative_url(str(hit.get("url", "")), page.file.url)
        return "[" + label + "](" + target + anchor + ")"

    return sub_outside_code(_LINK, replace, markdown)
