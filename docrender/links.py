"""Hook 03 -- links point at IDS, never at paths.

    [Main Stage](@main-stage)              a page in this site
    [the notes](@main-stage#venue-notes)   a heading on it
    [rep plot](@oph:rep-plot)              a page in a SIBLING site
    [the schedule](@data:circuit_schedule) a data table on THIS page
    [ETC](@term:etc)                       a defined term, styled as terminology

Moving the file, renaming its folder, or retitling the page cannot break an inbound
link, because none of those things is what the link points at. Set `id:` once and never
change it; that promise is the whole mechanism.


RESOLUTION ORDER (rewritten 2026-08-04, DL J8)
==============================================

0. A TOKEN CARRYING A FILE EXTENSION is refused, with the reason said out loud.
1. RESERVED PREFIX. `@<prefix>:<rest>` claimed by a handler in docrender/prefixes.py.
   `data` is claimed by datatable.py, `term` by markers.py. Read that module for why
   the registry is DERIVED from its handlers rather than typed as a list here.
2. PEER SITE. `@<slug>:<id>` against the peer's published index.
3. PAGE ID. `@<id>` in this site.

THE ORDER IS THE FIX, NOT A PREFERENCE. This file used to run `token.partition(":")`
first and treat everything left of the colon as a peer slug -- so `@data:inventory_table`
reported "unknown peer site: data", naming the wrong subsystem on a page that was
perfectly correct. Two namespaces built the same week by different hands is how the
second merge silently reopens the first hole.

And the extension refusal matters because the token charset accepts dots, so
`[x](@circuits-and-dimmers.tsv)` matched this regex and resolved as a page id -- the
wrong error, on a page one edit from right. Data files are reached by SLOT, never by
filename; that is the entire point of a slot.

⚠️ A RESERVED PREFIX TAKES NO `#anchor`, AND THAT WAS SILENT UNTIL 2026-08-04. A
handler's signature is `(rest, page, label)` -- no anchor -- so `@data:x#totals` or
`@term:etc#history` parsed fine, resolved fine, and lost the anchor on the way out.
The reader got a correct-looking link to the top of the wrong place. It is now
REPORTED and still dropped, which is the honest minimum: passing it through would
mean changing the signature every handler already implements, and datatable.py is
over the read ceiling tonight, so that is a deliberate later change and not a thing
to sneak into a feature branch. Same class as every other bug in this file's history
-- resolution that succeeds while quietly discarding half the request.


CROSS-SITE, with the honest limit up front. Every site in the family publishes
/doc-index.json at its root on every build. `@peer:id` resolves against the peer's
index, fetched at BUILD time and cached to disk in the instance folder. If a sibling
renames a page, our links stay wrong until we rebuild.

The cache is COMMITTED, not ignored. An unreachable peer then degrades to 'last known
good, marked stale' instead of taking our build down over somebody else's outage.

WHAT A BROKEN REFERENCE LOOKS LIKE. A `<span>`: red, struck through, carrying a
`[broken link]` badge and a tooltip naming what was not found. **It is NOT an anchor**
-- no href, no navigation, nothing to click. The link does not ACT, and the failure is
not hidden. A marked-but-dead reference is useful information on a site being written:
it says a document is coming.

Code is skipped via util.sub_outside_code -- see that function for why. Same-site paths
are resolved by util.relative_url -- see THAT function for the root-index bug this file
shipped with, and do not reintroduce a `../` count.
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

#: Suffixes that mean somebody named a FILE where an id or a slot belongs. Not a
#: security check, a legibility one: the error has to name the right subsystem.
_DATA_SUFFIXES = (".tsv", ".csv", ".json", ".yml", ".yaml", ".md", ".txt", ".xlsx")

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
    # Every hook has been imported by now, so the registry is complete. A peer slugged
    # with a reserved word would otherwise stop resolving and say nothing at all.
    prefixes.audit_peers((state.INSTANCE.get("peers") or {}).keys(), state.note)
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

        if token.lower().endswith(_DATA_SUFFIXES):
            state.note(
                "dead_links",
                src + ": '@" + token + "' names a FILE. References point at ids and "
                + "data slots, never at filenames -- that is what makes renaming a "
                + "file safe. For a table use @data:<slot> and declare the filename "
                + "once in `data:` frontmatter.",
            )
            return _dead(label, "references point at ids, not filenames: " + token)

        if ":" in token:
            prefix, _, rest = token.partition(":")

            handler = prefixes.resolver(prefix)
            if handler:
                if anchor:
                    # A handler takes no anchor, so one written here is DROPPED. Said
                    # out loud rather than swallowed: the link still works and still
                    # goes to the wrong part of the page, which is the shape of every
                    # bug this file has had.
                    state.note(
                        "dead_links",
                        src + ": '@" + token + anchor + "' carries a heading anchor, "
                        + "and the @" + prefix + ": namespace resolves whole targets "
                        + "-- it takes no anchor, so '" + anchor + "' was ignored. "
                        + "The link itself is fine; it lands at the top.",
                    )
                resolved = handler(rest, page, label)
                if resolved is None:
                    state.note(
                        "dead_links",
                        src + ": '@" + token + "' did not resolve. "
                        + prefixes.owner(prefix) + " owns the @" + prefix
                        + ": namespace and does not know '" + rest + "'.",
                    )
                    return _dead(label, "unknown " + prefix + ": " + rest)
                return resolved

            peer = state.PEERS.get(prefix)
            if not peer:
                state.note(
                    "dead_links",
                    src + ": unknown peer site '" + prefix + "'. Reserved prefixes on "
                    + "this build: "
                    + (", ".join(sorted(prefixes.reserved())) or "none") + ".",
                )
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
            state.note("dead_links", src + ": no page with id '" + token + "'")
            return _dead(label, "no page yet with id: " + token)

        # Resolved against THIS page, never from a separator count. The root index
        # page reports its url as `./` and broke that arithmetic.
        target = relative_url(str(hit.get("url", "")), page.file.url)
        return "[" + label + "](" + target + anchor + ")"

    return sub_outside_code(_LINK, replace, markdown)
