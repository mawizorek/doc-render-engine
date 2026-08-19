"""Stage 00c -- prev/next, and the ONE place a reading order may disagree with
the sidebar.

MkDocs walks the nav and wires `page.previous_page` / `page.next_page` while
BUILDING it, which happens BEFORE `on_nav` fires. So anything that reorders the
nav -- and `instance.py:on_nav` reorders all of it -- leaves those links
pointing along the ORIGINAL order.

The result is a site that disagrees with itself: the sidebar reads in `order:`
sequence and the Next button at the foot of the page reads in filesystem
sequence. Both look plausible in isolation, which is why it survives review.

This re-flattens the sorted tree and rewires the chain. Runs as its own stage
rather than at the end of the sort so that the two concerns stay separable:
one decides ORDER, this one propagates its consequences.

=============================================================================
⭐ `chain:` -- A READING ORDER THAT OUTLIVES THE SIDEBAR (2026-08-19)
=============================================================================
Found on uritp-safety `20-policies/`, and the folder is the whole argument:
eleven policy pages, `nav: hidden` on the folder index, `status: unlisted` on
eight of the pages. Michael expected the footer to walk Proper Attire ->
Emergency Contacts -> Active Shooter -> Shelter-in-place. It walked four pages
and crossed out of the folder, because ALL FOUR of the pages he named are
absent from the surviving nav by the time this stage runs.

🔴 THE DEFECT IS NOT A WRONG ORDER. IT IS THAT THERE WAS ONLY ONE. Three
separate questions were welded into a single cascade:

    is this page reachable and searchable      `status:`
    is it a ROW in the sidebar                 `status:` + `nav:`
    is it in the READING ORDER                 whatever survived the above

The third had no voice of its own. It read the tree left behind by stages 00b
(unlisted leave), 00bb (`nav: hidden` folders lose children) and 00bc (routers
seal), so EVERY sidebar-removal mechanism silently amputated the reading chain
as a side effect. Four stages, four chances to shrink it, and the footer never
said a word about what it lost.

⚑ GENERALISABLE, and it is the same shape `navsettle.py` wrote down three days
ago from the other end: A STAGE THAT CONSUMES A TREE IS NOT ENTITLED TO ASSUME
THE TREE IS THE ONLY ANSWER TO ITS QUESTION. navsettle found a rule evaluated
too early; this is a rule with no way to be stated at all.

⭐ AND MICHAEL HAD ALREADY AUTHORED THE ORDER TWICE, BY HAND, IN CONTENT. The
folder index lists eight policies in a deliberate sequence, and
`10-safety-responsibilities.md` carries a hand-typed "Up Next" callout pointing
at Emergency Contacts. That callout is a human building prev/next manually
because the real one could not be reached. The feature did not need inventing;
it needed a key.

    chain:
      - policy-housekeeping
      - policy-fire
      - policy-proper-attire

🚥 IT IS AN OVERRIDE, NOT A REPLACEMENT, AND THAT IS THE WHOLE SAFETY ARGUMENT.
The default rewiring below runs FIRST and unchanged. A `chain:` block then
re-points prev/next among the pages it NAMES and touches nothing else on the
site. So a site with no `chain:` anywhere builds byte for byte what it built
before -- which is what keeps `specs/visibility-split.md` §8's byte-identical
test alive for every instance except the one that opted in.

⚠️ AN INDEX PAGE ONLY EVER DONATES ITS `next`. It keeps its own `previous`, and
keeps its place in the default chain. A hub is a doorway INTO a flow, not a
link in it -- and stripping its `previous` would cut the site's spine to give a
folder a reading order, which is a trade nobody asked for.

🚫 THE LAST PAGE'S `next` IS None, DELIBERATELY. An authored flow ENDS; it does
not leak the reader back into whatever the nav happened to put next. Reported,
so it reads as a decision rather than a dead button.

⚠️ LEGAL ON AN `index.md` ONLY, mirroring `nav:` in objects/index.yml -- a
reading order through a folder is a fact about the FOLDER. Declared anywhere
else it is REPORTED and ignored, never silently dropped. That rule is not
cosmetic here: this build exists because `sort:` sat in eleven files doing
absolutely nothing, parsing as valid YAML, reported by no one. A key that looks
live and is not is the defect this engine keeps paying for.

⚠️ IT READS `state.BY_SRC`, NEVER THE NAV. That is the decoupling, in one line:
BY_SRC is populated at `on_files`, before anything prunes, so a chain can name
a page that no sidebar will ever show. Resolving through the nav would have
rebuilt the exact bug.
"""

from __future__ import annotations

from . import state


def _pages_in_order(items, out):
    for item in items:
        if getattr(item, "is_page", False):
            out.append(item)
        elif getattr(item, "children", None):
            _pages_in_order(item.children, out)
    return out


def _meta(src):
    return state.BY_SRC.get(src, {}) or {}


def _folder(src):
    """The directory part of a src_uri, '' at the site root."""
    return src.rsplit("/", 1)[0] if "/" in src else ""


def _built(files):
    """Every BUILT page, keyed by `id:` and by src_uri.

    ⚠️ INCLUDES PAGES THE NAV NO LONGER HOLDS, which is the entire point. An
    `unlisted` page is still built, still has a URL and still has a live Page
    object -- it was only removed from the sidebar. Walking `files` therefore
    sees exactly what walking the nav cannot.

    A duplicate `id:` is reported by objects.py already; here the FIRST one
    wins and the collision is named again, because a chain silently pointing at
    whichever page was walked second is worse than a chain that says so.
    """
    by_id: dict = {}
    by_src: dict = {}
    for f in files:
        page = getattr(f, "page", None)
        if page is None or not getattr(page, "is_page", False):
            continue
        src = getattr(f, "src_uri", "")
        if not src:
            continue
        by_src[src] = page
        pid = str(_meta(src).get("id") or "").strip()
        if not pid:
            continue
        if pid in by_id:
            state.note(
                "duplicate_id",
                "`chain:` resolution met the id `" + pid + "` twice ("
                + src + "). The FIRST page wins for every chain that names it.",
            )
            continue
        by_id[pid] = page
    return by_id, by_src


def _declared():
    """Every `chain:` block, keyed by the src_uri that declared it.

    Reports and discards a block on any page that is not an `index.md`. See the
    module docstring: the alternative is a key that parses and does nothing,
    which is the failure that produced this build.
    """
    out: dict = {}
    for src, meta in state.BY_SRC.items():
        raw = (meta or {}).get("chain")
        if raw is None:
            continue
        if not isinstance(raw, list):
            state.note(
                "missing_required",
                src + " declares `chain:` as a " + type(raw).__name__
                + ", not a list of ids. IGNORED -- the reading order for that "
                "folder falls back to the sidebar.",
            )
            continue
        name = src.rsplit("/", 1)[-1]
        if name != "index.md":
            state.note(
                "missing_required",
                src + " declares `chain:`, which is legal on a folder's "
                "`index.md` only -- a reading order through a folder is a fact "
                "about the folder. IGNORED, nothing was reordered.",
            )
            continue
        ids = [str(i).strip().lstrip("@") for i in raw if str(i).strip()]
        if ids:
            out[src] = ids
    return out


def _stragglers(src, ids, chain_ids):
    """Sibling pages the chain never named.

    Not a defect and not corrected -- an omission is how Michael keeps an empty
    stub or a hub out of a reading flow. It is reported because the OTHER
    reason a page is missing is that somebody forgot it, and those two look
    identical from here. Naming them is the join check; deciding is his.
    """
    here = _folder(src)
    missing = []
    for other, meta in state.BY_SRC.items():
        if other == src or _folder(other) != here:
            continue
        pid = str((meta or {}).get("id") or "").strip()
        if pid and pid not in chain_ids:
            missing.append(pid)
    if missing:
        state.note(
            "notes",
            src + " declares a `chain:` of " + str(len(ids)) + " and "
            + str(len(missing)) + " sibling page(s) are NOT in it: "
            + ", ".join(sorted(missing))
            + ". Deliberate omissions are fine -- this is the join check, not a "
            "correction.",
        )


def _apply(files):
    decls = _declared()
    if not decls:
        return

    by_id, by_src = _built(files)
    claimed: dict = {}

    for src in sorted(decls):
        ids = decls[src]
        index_page = by_src.get(src)
        resolved = []
        for pid in ids:
            page = by_id.get(pid)
            if page is None:
                state.note(
                    "dead_links",
                    src + " `chain:` names `" + pid + "`, which is not the id "
                    "of any page on this site. SKIPPED -- the rest of the "
                    "chain still wires, so the flow has a gap rather than "
                    "being abandoned.",
                )
                continue
            if pid in claimed:
                state.note(
                    "notes",
                    "`" + pid + "` is claimed by two chains (" + claimed[pid]
                    + " and " + src + "). A page has ONE previous and ONE next, "
                    "so the first declaration keeps it and this one skips it.",
                )
                continue
            claimed[pid] = src
            resolved.append(page)

        if not resolved:
            state.note(
                "missing_required",
                src + " declares `chain:` and NONE of its " + str(len(ids))
                + " ids resolved. The folder keeps the sidebar's reading order.",
            )
            continue

        for i, page in enumerate(resolved):
            page.previous_page = resolved[i - 1] if i > 0 else index_page
            page.next_page = resolved[i + 1] if i + 1 < len(resolved) else None

        # The hub donates its Next and keeps its own Previous. See the docstring.
        if index_page is not None:
            index_page.next_page = resolved[0]

        state.note(
            "nav_default",
            src + " AUTHORED READING ORDER: " + str(len(resolved))
            + " page(s), independent of the sidebar. Pages that are `unlisted` "
            "or behind a `nav: hidden` folder are IN this chain and still out "
            "of the sidebar and out of search -- that separation is the "
            "feature. The last page's Next is deliberately empty: an authored "
            "flow ends rather than leaking back into the nav.",
        )
        _stragglers(src, ids, set(claimed))


def on_nav(nav, config, files):
    pages = _pages_in_order(nav.items, [])
    if pages:
        # Replace the flat page list too. Material reads `nav.pages` for the
        # keyboard next/prev shortcuts, so leaving it stale would fix the
        # visible button and leave the invisible one wrong -- worse than not
        # fixing either.
        nav.pages = pages

        for i, page in enumerate(pages):
            page.previous_page = pages[i - 1] if i > 0 else None
            page.next_page = pages[i + 1] if i + 1 < len(pages) else None

    # AFTER the default wiring, never instead of it. An authored chain is an
    # override on the pages it names; everything else keeps the sidebar order.
    #
    # ⚠️ `nav.pages` is NOT re-derived from the chains. It drives Material's
    # keyboard shortcuts, and those walk the SIDEBAR -- a shortcut that jumps to
    # a page with no row to highlight would strand the reader somewhere the nav
    # cannot show them. The visible button follows the authored flow; the
    # keyboard follows the tree. Stated because the asymmetry is deliberate and
    # reads like an oversight.
    _apply(files)

    return nav
