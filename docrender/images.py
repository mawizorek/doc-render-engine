"""Stage 01f -- `@img:<filename>`. An image is reached by NAME, never by path.

    ![The H5 front panel](@img:h5-front){ caption="Power is on the LEFT." }

> Michael, 2026-08-07: *"whatever the file name is, that's the ID."*

**The stem of the filename IS the id.** `h5-front.png` is `@img:h5-front`.
Nothing is declared, nothing is registered, there is no frontmatter block and no
manifest. Drop the file anywhere in the content tree and every page in the tree
can reach it.


WHY A NAME AND NOT A PATH
=========================

A relative path already works and keeps working -- nothing here removes it, and
for an image sitting beside its page a bare filename is still the shortest
correct thing to type.

It stops being adequate the moment the two ends are far apart. From
`production/inventory/electrics/audio/h5-zoom/` to the repo root is FIVE levels:

    ![alt](../../../../../shared/uritp-logo.png)

That is the exact arithmetic this house shipped wrong three separate times --
`links.py`, `router.py`, `datatable.py` -- which is why `util.relative_url`
exists as a shared helper. **We wrote a helper because the counting is hard.**
Handing the counting back to an author is the same bug with a person in it.

And it fails the same way `id:` was invented to prevent: move the page one
folder deeper, or move the image, and every `../` count is silently wrong. A
name cannot go stale, because none of those things is what the reference points
at.


🔴 DUPLICATES ARE REPORTED AND THE REFERENCE IS REFUSED
=======================================================

This is STRICTER than the page-`id:` contract, deliberately.

`state.PAGES` is a plain assignment, so a duplicate page id is last-writer-wins:
reported by `objects.py`, and then quietly resolved to whichever page was walked
second. That bargain is defensible for pages -- both exist, both publish, and
the loser is merely unreachable by id.

**It is not defensible for a photograph.** Two files named `menu.png` in two
folders are two different pictures of two different things, and picking one
puts the WRONG PICTURE on the page with nothing visibly wrong. So an ambiguous
name resolves to nothing and renders as the broken-reference marker, which is a
failure the author can see.

⚠️ Reported under `duplicate_id`, the bucket that already exists. A new bucket
would be two more edits in two files (`state.reset()` and `sizecheck._LABELS`)
for a finding that is exactly what that label already says.


CASE IS FOLDED, AND A CASE COLLISION IS A DUPLICATE
===================================================

`@img:H5-Front` finds `h5-front.png`. Kind to an author, and it costs nothing.

The consequence is deliberate: `Menu.png` and `menu.png` in the same tree are
reported as duplicates. That is correct rather than pedantic -- they are already
the same file on a case-insensitive filesystem, and a repo that relies on the
difference breaks the first time somebody clones it onto a Mac.


HOW AN IMAGE COMES OUT OF A LINK RESOLVER
=========================================

⭐ The handler returns LINK markdown and the `!` does the rest.

`links._LINK` begins matching at the opening bracket, so in `![alt](@img:x)`
the bang sits OUTSIDE the match and survives untouched. Returning
`[alt](resolved/path.png)` therefore leaves `![alt](resolved/path.png)` on the
page. No new pattern, no change to `links.py`, no second resolver.

⚠️ Consequence, stated rather than discovered: `[text](@img:x)` with NO bang is
a LINK to the image file. That is legitimate -- "open the full-size plot" is a
real thing to write -- so it is allowed rather than policed.


ORDERING
========

The claim happens at hook import, which is before any event, so registration
order does not affect it. The INDEX is built in `on_files`, and every hook's
`on_files` runs before any hook's `on_page_markdown`, so `links.py` at stage 03
always finds a complete index.

Registered at 01f anyway, beside `01e_figure`, because the two are one feature
to a reader: 01e wraps a captioned image, 01f tells it where the image is.

⚠️ `prefixes.py` documents the trap this obeys: never read the registry at
import time. Everything here happens inside an event.


🚫 WHAT THIS DELIBERATELY DOES NOT DO
=====================================

**No orphan report.** Listing images nothing points at is genuinely wanted --
there is one in `uritp-docs` right now -- but this module can only see
references that arrive through `@img:`. An image placed by relative path, which
is the majority case and always will be, would be reported as unreferenced.
**A metric that is wrong about the common case is worse than no metric**, and
this engine already refused the same shape once: `docindex.py` reports
`inbound: 0` as a count and explicitly declines to call it "orphan", because
nav membership is not in its graph.

The honest version of that report belongs where the page's own HTML can be
scanned, and it is a separate build.

**No resizing, no EXIF stripping, no intake.** A reference resolver is not a
pipeline. Those are real and they are elsewhere.

**No opinion about WHERE an image lives.** Beside its page or in a shared
folder -- this module resolves both identically, which is the entire point.
"""

from __future__ import annotations

from pathlib import PurePosixPath

from . import prefixes, state
from .util import relative_url

#: What counts as an image. `.pdf` is deliberately absent -- a PDF is a document
#: to link to, not a picture to place, and giving it a name here would invite
#: `![alt](@img:some-plan)` to embed something that cannot be embedded.
SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif")

#: lowercased filename stem -> {"url": build url, "src": source path}. A name
#: with more than one file is REMOVED from here entirely and recorded below, so
#: an ambiguous reference resolves to nothing rather than to a guess.
INDEX: dict[str, dict] = {}

#: lowercased stem -> [source paths]. Only names that collided.
COLLISIONS: dict[str, list] = {}


def _stem(src: str) -> str:
    return PurePosixPath(src).stem.strip().lower()


def on_files(files, config):
    """Index every image in the content tree by the stem of its filename.

    Walks the file set MkDocs has already assembled rather than the disk, so
    this costs one pass over a list that exists and cannot disagree with what
    the build is actually publishing.
    """
    INDEX.clear()
    COLLISIONS.clear()

    seen: dict[str, list] = {}
    for f in files:
        src = getattr(f, "src_uri", "") or ""
        if not src or not src.lower().endswith(SUFFIXES):
            continue
        seen.setdefault(_stem(src), []).append(f)

    for name, hits in seen.items():
        if len(hits) == 1:
            INDEX[name] = {
                "url": getattr(hits[0], "url", "") or hits[0].src_uri,
                "src": hits[0].src_uri,
            }
            continue

        # Ambiguous. Left OUT of the index on purpose -- see the module
        # docstring on why this is stricter than the page-id contract.
        paths = sorted(h.src_uri for h in hits)
        COLLISIONS[name] = paths
        state.note(
            "duplicate_id",
            "image name '" + name + "' is used by " + str(len(paths))
            + " files: " + ", ".join(paths) + ". An image is named by the stem "
            + "of its filename and the name must be unique across the whole "
            + "content tree, so every @img:" + name + " reference renders as "
            + "broken until one is renamed. Not guessed at: two pictures with "
            + "one name are two different pictures.",
        )

    return files


def _resolve(rest: str, page, label: str):
    """Resolve `@img:<name>`. Returns markdown, or None to decline.

    Declining hands control back to `links.py`, which renders the existing
    broken-reference span -- red, struck through, no href. Never a guess.
    """
    raw = (rest or "").strip()
    name = _stem(raw) if "." in raw else raw.lower()

    if raw != name and "." in raw:
        # Forgiving, and said out loud. An extension resolves, because refusing
        # a reference that names the right file helps nobody -- but two spellings
        # for one thing is how a vocabulary starts drifting, so the canonical
        # form is stated once per occurrence rather than silently accepted.
        state.note(
            "notes",
            page.file.src_uri + ": '@img:" + raw + "' carries a file extension. "
            + "It resolved, but the name IS the stem -- write '@img:" + name
            + "'. The extension is not part of the id, which is what lets a "
            + "png become a webp without touching a single page.",
        )

    if name in COLLISIONS:
        state.note(
            "dead_links",
            page.file.src_uri + ": '@img:" + name + "' is ambiguous -- "
            + str(len(COLLISIONS[name])) + " files share that name. Rename one "
            + "and the reference resolves.",
        )
        return None

    hit = INDEX.get(name)
    if not hit:
        return None

    # Resolved against THIS page through the shared helper, never by counting
    # separators. util.relative_url carries the root-index bug that arithmetic
    # shipped; do not reintroduce it here.
    target = relative_url(hit["url"], page.file.url)
    return "[" + label + "](" + target + ")"


prefixes.claim("img", __name__, _resolve)
