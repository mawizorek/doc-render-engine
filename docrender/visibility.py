"""Hook 02 -- the publication gate.

WHY decisions here are the way they are: the doc-render-engine Decision Log.
This docstring is the CONTRACT and is kept under the read-whole line.

Four states, inherited from v1 because they were right:

    hidden     not built at all. The URL 404s. Where a page starts and where
               anything unfinished stays.
    unlisted   live URL, absent from nav and from search. Shareable by link.
    gated      *** NOT IMPLEMENTED. Downgraded to `unlisted`, loudly. ***
    public     listed, searchable, done.

Runs before links.py, and the order is load-bearing rather than tidy: if link
resolution indexed pages first, a link to a hidden page would resolve happily
to a URL that 404s for every reader. Prune, then index.

🚫 `gated` IS NOT A GATE AND IS NOT BUILT. A page declaring it publishes as
`unlisted` with a warning -- a live URL, no nav, no search, no protection. The
argument for refusing to ship a fake one, and the limits that would apply to a
real one, are in README section 7 and the authoring site's publication page.
The rule here: if it would matter that a stranger read it, it does not belong
in a doc repo.

=============================================================================
TWO EVENTS, AND THEY CANNOT BE ONE
=============================================================================
`on_files` decides what gets BUILT. `on_nav` decides what gets LISTED. Every
hook's on_files runs before any hook's on_nav, so `unlisted` -- keep the file,
drop the sidebar entry -- needs both. See `prune_nav` for why its stage number
is 00b and not 02.

⚠️ AND THIS MODULE OWNS TWO on_nav STAGES, NOT ONE. `prune_nav` at 00b,
`seal_nav` at 00bc, with navstate's 00bb deliberately BETWEEN them. They were
one function until 2026-08-05; `seal_nav` carries the ordering law that keeps
them apart and the bug that split them.

=============================================================================
THERE IS NO STATUS CASCADE
=============================================================================
Every page carries its own `status:` and nothing here reads a parent's. A
folder's index.md does NOT set the state of the pages under it. The template
site asserted a cascade for two days -- kept as a retraction rather than
deleted, because it was wrong in the expensive direction: somebody could hide a
folder index, believe the pages under it were covered, and publish all of them.

⚠️ `router:` AND `nav:` BOTH CASCADE AND NEITHER IS A PUBLICATION STATE. They
change what a reader is OFFERED, never what is BUILT. One is a lock, one is a
curtain, and the paragraph above exists because somebody once believed the
curtain was the lock.

⚠️ THIS MODULE MAY IMPORT `navstate`, AND `navstate` MAY NEVER IMPORT THIS ONE.
The dependency runs one way on purpose. `seal_nav` has to know whether a folder
declared `nav: routed`, and reading that key here would make a second
interpreter of it -- so it asks `navstate.declared()`. The reverse direction is
what the 00bb shim exists to avoid: navstate needs `_index_of` and `_unchain`
from here, and gets them passed in rather than imported.
"""

from __future__ import annotations

from . import navstate, state


def on_files(files, config):
    kept = []
    for f in files:
        if not f.is_documentation_page():
            kept.append(f)
            continue

        meta = state.BY_SRC.get(f.src_uri, {})
        status = meta.get("status")

        if status == "gated":
            state.note(
                "notes",
                f"{f.src_uri}: status 'gated' is NOT IMPLEMENTED in engine v1. "
                f"Published as 'unlisted' (live URL, no nav, no search). It is "
                f"NOT protected. See docrender/visibility.py.",
            )
            meta["status"] = status = "unlisted"

        if status not in ("unlisted", "public"):
            # hidden, missing, or malformed -- all of which mean do not build.
            continue

        if status == "unlisted":
            # SEARCH ONLY, and `search.exclude` is a real documented property
            # the built-in plugin honours. Keeping it here saves every author
            # remembering a second key meaning the same as the first.
            #
            # 🔴 THE NAV HALF USED TO LIVE HERE AND WAS A NO-OP: `meta["hide"] =
            # ["nav"]` -- wrong key name, and wrong FEATURE. `hide:` is about
            # which chrome renders ON this page. Nav membership is not a page
            # property at all; it is decided by the tree, so it is fixed in the
            # tree. See `prune_nav`.
            meta["search"] = {"exclude": True}

        kept.append(f)

    files_cls = type(files)
    return files_cls(kept)


def _prune(items: list) -> list:
    """Drop unlisted pages, and any section left with nothing in it."""
    kept = []
    for item in items:
        if getattr(item, "is_page", False):
            meta = state.BY_SRC.get(item.file.src_uri, {})
            if meta.get("status") == "unlisted":
                # No longer part of any reading order. MkDocs wired prev/next
                # while BUILDING the nav, which was before this ran, so without
                # this the page keeps a footer pointing into a chain it has
                # just been removed from.
                item.previous_page = None
                item.next_page = None
                continue
            kept.append(item)
        elif getattr(item, "is_section", False):
            item.children = _prune(item.children or [])
            if item.children:
                kept.append(item)
            else:
                # An empty section renders as a heading that expands to nothing.
                # Reported rather than removed quietly, because the usual cause
                # is one page changing status and taking its whole folder off
                # the sidebar -- a bigger effect than the edit looked like.
                state.note(
                    "notes",
                    "nav section '" + str(getattr(item, "title", "?"))
                    + "' has no listed pages left and was removed from the "
                    + "sidebar. Its pages are still built and still reachable "
                    + "by link.",
                )
        else:
            # Literal nav links. Nothing here knows anything about them.
            kept.append(item)
    return kept


# ===========================================================================
# ROUTED FOLDERS: TAKE THE SUBTREE OUT OF THE SIDEBAR (DL J14 has the account)
# ===========================================================================
# Michael: "routing safety should ONLY show SAFETY in the nav and no subpages
# until the route code is input." Before this, `router:` curtained the page BODY
# and had no opinion about the sidebar -- the section NAME was withheld and its
# table of contents was not.
#
# ⭐ AND SINCE 2026-08-06 THE SECTION NAME CAN GO TOO. `nav: routed` on the same
# index takes the folder's own row out as well, and the row travels INSIDE the
# sealed manifest so a correct code can build it. Michael: "i want the sidebar to
# feel almost dynamic if something unlocks." See `_seal`.
#
# ⚠️ SEALING IS PRESENTATION, NOT PROTECTION, and the word "hidden" does not go
# into the authoring docs for it without "casual" beside it. Every sealed page
# still renders, still has a live URL, is still linkable by `@id`, and its body
# is plaintext in the DOM behind `hidden` and in search_index.json. What this
# stops is the SHAPE of a section being handed to somebody with no code.
#
# The manifest is SEALED rather than shipped as text because the titles have to
# come back on unlock, and a plaintext payload would put every withheld title in
# the source of the page withholding it. router.py does the sealing.


def _routed(meta: dict) -> bool:
    """Does this page's own frontmatter declare a router? (Never inherited.)"""
    return bool(meta.get("router") or meta.get("router_code"))


def _nav_routed(src_uri: str) -> bool:
    """Did this folder index declare `nav: routed`?

    ⚠️ ASKED, NEVER PARSED. navstate owns the `nav:` vocabulary including its
    aliases, and a second reader here would drift the first time one is added.
    `declared()` is the silent form -- the reporting one runs once, at 00bb.
    """
    return navstate.declared(src_uri) == "routed"


def _find_index(section):
    """The index page inside a section, read from the LIVE children."""
    for child in getattr(section, "children", None) or []:
        if getattr(child, "is_page", False) and child.file.name == "index":
            return child
    return None


def _mark_indexes(items: list) -> None:
    """Record every section's index page BEFORE anything is pruned.

    🔴 NEVER RE-DERIVE AN INDEX FROM LIVE CHILDREN AFTER THIS POINT. The seal
    used to scan surviving children, and an index with `status: unlisted` has
    already been dropped by `_prune` by then -- so the lookup returned None, the
    section was never recognised as routed, and its children stayed listed in
    full: the feature failing silently on the one page that needed it. Live
    instance `production/staff/index.md`, 2026-08-04, caused by an ordering
    comment that was correct in one direction only.
    """
    for item in items:
        if not getattr(item, "is_section", False):
            continue
        item._dr_index = _find_index(item)
        _mark_indexes(getattr(item, "children", None) or [])


def _index_of(section):
    """The index recorded before pruning. Never re-derived from live children."""
    return getattr(section, "_dr_index", None)


def _title(item) -> str:
    """What the sidebar would have called this.

    Frontmatter first, because a Page's `title` is not populated until the page
    is RENDERED -- long after on_nav. Reading item.title alone would have
    produced a manifest of empty strings that nobody would notice until a reader
    typed a correct code.
    """
    if getattr(item, "is_page", False):
        meta = state.BY_SRC.get(item.file.src_uri, {})
        return str(meta.get("title") or item.title or item.file.name)
    return str(getattr(item, "title", "") or "")


def _node_url(item) -> str:
    """The url a sidebar row for this node would point at, or "".

    A section speaks through its index page; a section without one is a label
    with nowhere to go and cannot be used as an anchor.
    """
    if getattr(item, "is_page", False):
        return str(item.file.url)
    index = _index_of(item)
    return str(index.file.url) if index is not None else ""


def _next_visible_url(items: list, pos: int) -> str:
    """The url of the next sibling after `pos` that will still be in the sidebar.

    ⭐ A SCAN RATHER THAN `items[pos + 1]`, and the difference is a real case.
    Two `nav: routed` folders side by side: the naive version anchors the first
    against the second, which is not in the sidebar either -- so the lookup fails
    at runtime and both fall back to the end, which is the behaviour this whole
    change exists to replace. Rare today, free to get right now.
    """
    for later in items[pos + 1:]:
        if getattr(later, "is_section", False):
            index = _index_of(later)
            if index is not None and _nav_routed(index.file.src_uri):
                continue
        url = _node_url(later)
        if url:
            return url
    return ""


def _unchain(node) -> None:
    """Take a sealed branch out of the reading order.

    00c_nav rebuilds prev/next by flattening the tree, so anything no longer IN
    the tree keeps whatever MkDocs wired while building it. Same reason _prune
    nulls these by hand.
    """
    if getattr(node, "is_page", False):
        node.previous_page = None
        node.next_page = None
        return
    for kid in getattr(node, "children", None) or []:
        _unchain(kid)


def _collect(node, out: list, depth: int) -> None:
    """Flatten one pruned branch into manifest entries, in nav order.

    Depth travels with each entry rather than the list being nested: the client
    only has to indent, and a flat list cannot be mis-nested by a bug in the
    injection.

    ⭐ THIS KNOWS NOTHING ABOUT `nav:` AND MUST NOT LEARN. It walks a tree
    navstate already trimmed at 00bb, so a `nav: hidden` folder arrives holding
    only its own index and contributes one row for free. Teaching it the key
    would be a second copy of a rule the stage order already enforces, and a
    second copy is free to drift. See `seal_nav`.
    """
    _unchain(node)

    if getattr(node, "is_page", False):
        out.append({"t": _title(node), "u": node.file.url, "d": depth})
        return
    if not getattr(node, "is_section", False):
        return

    index = _index_of(node)

    # A folder with an index page is ONE entry pointing at that page --
    # `navigation.indexes` is on, so the sidebar has always shown it that way,
    # and instance.py has already given the section the index page's title. A
    # folder without one is a label with nowhere to go.
    #
    # ⚠️ An UNLISTED index still gets its url here, deliberately. `unlisted`
    # means live and reachable by link but not advertised, and a menu that only
    # exists behind a code is the one link surface where that is exactly right.
    entry = {"t": _title(node), "d": depth}
    if index is not None:
        entry["u"] = index.file.url
    out.append(entry)

    if index is not None and _routed(state.BY_SRC.get(index.file.src_uri, {})):
        # ⭐ THE SECOND HALF OF MICHAEL'S ASK, and it needs no rule of its own:
        # "if only a sub tree is routed (or routed separately than the route on
        # the upper index) it should also remain hidden until ungated."
        #
        # This folder is its own curtain. The parent may reveal that it EXISTS
        # and must never reveal what is inside it. Sealed separately under its
        # own codes, exactly as router.py's `_inherited` stops at the nearest
        # ancestor.
        #
        # ⚠️ NO SIBLINGS PASSED, so a nested routed folder appends rather than
        # placing itself. Correct rather than lazy: its position is meaningful
        # inside its parent, and its parent is not in the sidebar either.
        _seal(node, index)
        return

    for kid in getattr(node, "children", None) or []:
        if kid is index:
            continue
        _collect(kid, out, depth + 1)


def _seal(section, index, siblings: list | None = None, pos: int = -1) -> bool:
    """Strip a routed section back to its index page and stash what was there.

    Returns True if the section should stay in the sidebar. False means it has
    nothing left to show -- either the contradiction below, or `nav: routed`,
    where leaving is the whole point.

    `siblings`/`pos` are the list this section sits in and its place in it, and
    are used ONLY to work out where an invisible folder should be put back. They
    are absent for a nested routed folder; see `_collect`.
    """
    src = index.file.src_uri
    invisible = _nav_routed(src)

    items: list = []
    for kid in getattr(section, "children", None) or []:
        if kid is index:
            continue
        _collect(kid, items, 1)

    if invisible:
        # ⭐ THE FOLDER'S OWN ROW, AT DEPTH 0, AND IT IS THE WHOLE FEATURE.
        # Every other consumer of this manifest hangs a list under a sidebar row
        # that already exists; a routed folder HAS no row, so the client builds
        # one from this entry. That is why `nav: routed` needed no new payload,
        # no second cipher and no change to seal.py.
        #
        # The section's title rather than the index page's: instance.py has
        # already copied one onto the other, and the section is what the sidebar
        # would have shown.
        items.insert(0, {
            "t": _title(section) or _title(index),
            "u": index.file.url,
            "d": 0,
        })

    if not items:
        # ⭐ Since 2026-08-05 the usual cause is `nav: hidden` on this same index
        # getting here first at 00bb. NOT a conflict: never offered is a stronger
        # claim than offered to a code, and the stronger one wins by arriving
        # first. Reported because "router declared, no manifest" is otherwise a
        # silent surprise to whoever wrote the router.
        state.note(
            "routers",
            src + " · router declared, nav manifest EMPTY · "
            + "nothing under this folder to withhold. If it also declares "
            + "`nav: hidden`, that is why: hidden takes the children out of the "
            + "sidebar for everybody, which is stronger than sealing them "
            + "behind a code. The body curtain works as normal.",
        )
        return True

    record = {
        "anchor": "" if invisible else index.file.url,
        # 'in' is what every router has always done: find this folder's own row
        # and append underneath it. 'at' means there is no row, so the client
        # builds one and places it.
        "place": "at" if invisible else "in",
        "items": items,
    }

    if invisible:
        # ⭐ WHERE IT GOES BACK. Michael, 2026-08-06: "it needs to appear in its
        # real sort order." Two hints rather than one, because the good one can
        # go stale:
        #
        #   before  the next top-level sibling that will still be rendered. The
        #           client inserts ahead of that row, which puts this folder
        #           exactly where `order:` would have.
        #   idx     its own index in the top-level list, used only if that row
        #           cannot be found.
        #
        # ⚠️ AND IF BOTH MISS IT APPENDS, which is what shipped yesterday. That
        # graceful floor is the reason the stale-anchor objection does not block
        # this: the worst case is the previous behaviour, not a broken sidebar.
        record["before"] = (
            _next_visible_url(siblings, pos) if siblings is not None else ""
        )
        record["idx"] = pos

    state.NAV_SEALED[src] = record

    pages = sum(1 for i in items if i.get("u"))

    if invisible:
        # The whole section leaves. `_unchain` on the index as well as on the
        # children, because unlike every other path here the index is going too
        # and would otherwise keep a prev/next into a chain it has left.
        _unchain(index)
        survived = index in (getattr(section, "children", None) or [])
        section.children = []

        if not survived and state.BY_SRC.get(src, {}).get("status") == "unlisted":
            # ⭐ NOT THE CONTRADICTION BELOW, AND THE DIFFERENCE IS REAL.
            # `unlisted` + a sealing router is unsatisfiable: one says this page
            # is not in the sidebar, the other says only this page is. `routed`
            # says it is not in the sidebar EITHER, until a code -- which AGREES
            # with unlisted instead of fighting it. So this is redundancy, not a
            # conflict, and it is worth saying because unlisted costs something
            # extra that routed does not: it drops the page from SEARCH.
            state.note(
                "routers",
                src + ": `status: unlisted` adds nothing to `nav: routed` -- "
                + "routed already keeps this folder out of the sidebar until a "
                + "code is typed. It DOES additionally remove the page from "
                + "search, which is a separate decision and probably not the "
                + "one you meant. `status: public` is the usual pairing.",
            )

        where = (
            "ahead of /" + record["before"] if record["before"]
            else "at the end of the top level (no anchor available)"
        )
        state.note(
            "routers",
            src + " · nav ROUTED · the folder itself and " + str(pages - 1)
            + " page(s) under it are absent from the sidebar entirely. A correct "
            + "code puts the folder back " + where + " and keeps it there for the "
            + "rest of the session, on every page. All still built and reachable "
            + "by URL, @id and search.",
        )
        return False

    # 🔴 `status: unlisted` ON A ROUTED FOLDER INDEX IS A DIRECT CONTRADICTION --
    # unlisted says this page is not in the sidebar, nav-seal says ONLY this page
    # is. Nothing satisfies both. Resolved the PROTECTIVE way on the principle
    # used everywhere here: when two declarations disagree, the one that shows
    # LESS wins, and the report says so loudly enough to fix.
    #
    # ⚠️ AND `nav: routed` IS THE ANSWER TO IT, as of 2026-08-06. Somebody
    # reaching for unlisted here almost always wanted the folder gone from the
    # sidebar until a code arrives, which is now a thing the engine can do -- so
    # the report names it.
    survives = index in (getattr(section, "children", None) or [])
    section.children = [index] if survives else []

    if survives:
        state.note(
            "routers",
            src + " · nav sealed · " + str(pages) + " of "
            + str(len(items)) + " entries are pages, withheld from the sidebar "
            + "until a code is typed. Still built, still reachable by URL.",
        )
    else:
        state.note(
            "missing_required",
            src + ": `status: unlisted` and a nav-sealing "
            + "`router:` contradict each other -- unlisted keeps this page OUT "
            + "of the sidebar, sealing leaves it as the ONLY thing in it. The "
            + str(len(items)) + " entries under it are sealed (the protective "
            + "reading) and the whole section is gone from the nav, so no code "
            + "can reveal the menu: there is no row to reveal it under. Set "
            + "`status: public` on this index for the collapsed-section "
            + "behaviour, or add `nav: routed` beside it if what you wanted was "
            + "the whole folder absent until a code -- which is a real value "
            + "now, and does reveal the menu.",
        )
    return survives


def _seal_routers(items: list, top: bool = False) -> list:
    """Seal every routed section, dropping any left with nothing to show.

    `top` marks the outermost call, where a section's position among its
    siblings is the position it should be RESTORED to. Deeper calls do not pass
    it: a nested folder's parent is not in the sidebar either.
    """
    kept = []
    for pos, item in enumerate(items):
        if not getattr(item, "is_section", False):
            kept.append(item)
            continue
        index = _index_of(item)
        if index is not None:
            src = index.file.src_uri
            has_router = _routed(state.BY_SRC.get(src, {}))
            if has_router:
                if _seal(item, index, items if top else None, pos):
                    kept.append(item)
                continue
            if _nav_routed(src):
                # ⚠️ A FOLDER ASKED TO DISAPPEAR UNTIL A CODE, ON A PAGE WITH NO
                # CODE. Nothing reaches the seal without a router, so the folder
                # simply lists as normal -- correct, and silent, which is the
                # problem. Two very different outcomes (never hides / never
                # comes back) look identical from the author's chair, so the
                # build says which one happened.
                state.note(
                    "missing_required",
                    src + ": `nav: routed` needs a router on the same page and "
                    + "there is none. The folder is listed in the sidebar as "
                    + "normal. Add `router:` or `router_code:` here, or use "
                    + "`nav: hidden` if you meant to hide the children from "
                    + "everybody.",
                )
        item.children = _seal_routers(getattr(item, "children", None) or [])
        if item.children:
            kept.append(item)
    return kept


def prune_nav(nav, config, files):
    """Stage 00b -- take `unlisted` pages out of the sidebar.

    🔴 WHY THIS IS NOT IN on_files WITH THE REST OF THE GATE, AND WHY ITS STAGE
    NUMBER IS 00b RATHER THAN 02. `unlisted` means built but not listed, so the
    file has to survive on_files and the nav ENTRY has to be removed later.
    MkDocs runs every hook's on_files before any hook's on_nav, so "later" is a
    different event, not a different line.

    The number follows from a second constraint: `00c_nav.py` rebuilds prev/next
    by flattening the nav tree, so this has to happen BEFORE it, or the footer
    Next button walks through pages that are not in the sidebar -- the same
    disagreement 00c exists to fix, reintroduced from the other end.

    TWO PASSES: MARK each section's index while the tree is untouched, then
    PRUNE unlisted pages. Marking is first because pruning can delete an index
    and every later stage needs to know it was there -- see `_mark_indexes`.

    ⚠️ THE ROUTER SEAL IS NOT HERE ANY MORE. It is `seal_nav` at stage 00bc,
    with navstate's 00bb between them, and that split is not a tidy-up.
    """
    _mark_indexes(nav.items)
    nav.items = _prune(nav.items)
    return nav


def seal_nav(nav, config, files):
    """Stage 00bc -- seal routed subtrees, AFTER `nav:` has shaped the tree.

    🔴 THIS WAS PASS 3 OF `prune_nav` UNTIL 2026-08-05, AND SHARING A FUNCTION
    WITH THE PRUNE IS WHAT BROKE `nav: hidden`. A routed parent harvested its
    whole subtree into the sealed manifest at 00b, before navstate reached 00bb
    -- so a `nav: hidden` folder inside it was already out of the tree when its
    key was read, the cut had nothing to act on, and every page it removed sat
    in the ciphertext waiting to be injected back on a correct code. Live on
    uritp: 43 course pages under `router: pm`. DL has the account.

    ⚑ A RULE CORRECT IN ISOLATION AND UNREACHABLE IN PLACE -- the sixth of that
    shape here -- and the ordering COMMENT caused it. navstate must run after
    the prune because it reads index pages the prune can delete. True, and
    exactly what let the seal reach the subtree first.

    ⭐ THE FIX IS THE ORDER, NOT A SECOND CHECK. See `_collect`.

    ⭐ AND `nav: routed` DEPENDS ON THE SAME ORDER FROM THE OTHER DIRECTION.
    navstate deliberately does NOT cut a routed folder at 00bb: cutting there
    would hand this stage an empty subtree and the manifest -- the only thing
    that can bring the folder back -- would contain nothing. The cut happens
    here, in `_seal`, after the harvest. Same law, opposite failure.

    THE on_nav CHAIN, EVERY LINK LOAD-BEARING:

      00    sort     instance.py orders the tree
      00b   prune    unlisted pages leave            <- prune_nav
      00bb  shape    `nav: hidden` folders are cut   <- navstate.shape
      00bc  seal     routers take what is LEFT       <- HERE
      00c   chain    prev/next rebuilt from all of it

    ⚠️ PRUNE AND SHAPE BOTH PRECEDE THE SEAL FOR ONE REASON: a page the sidebar
    deliberately does not show must never be sealed and then INJECTED into a
    menu on unlock. `unlisted` always had that guarantee. `nav: hidden` has it
    now. `nav: routed` is the one deliberate exception, and it is not a leak:
    the folder is absent because it is WAITING to be injected, which is the
    opposite of a page somebody took out of the sidebar on purpose.
    """
    if not state.NAV_SHAPED:
        # 🔴 A REGRESSION DETECTOR, AND THE HALF OF THIS FIX THAT OUTLIVES ME.
        # Unregister, rename or renumber 00bb past this stage and the seal goes
        # straight back to harvesting untrimmed subtrees -- silently, invisible
        # until somebody types a code and sees pages a folder had shut. The bug
        # above survived because nothing could notice it. This can.
        state.note(
            "missing_required",
            "STAGE ORDER BROKEN: the router nav-seal (00bc) ran before navstate "
            + "(00bb), so any `nav: hidden` folder inside a routed folder was "
            + "sealed with its children still in it -- and a correct router code "
            + "will reveal pages meant to be out of the sidebar entirely. Check "
            + "the `hooks:` list in mkdocs.yml: 00b, 00bb, 00bc, 00c.",
        )

    nav.items = _seal_routers(nav.items, top=True)

    # A router on the SITE ROOT index has no enclosing section, so there is no
    # subtree to take that is not the whole sidebar. Reported rather than
    # silently doing nothing, because a no-op that looks like a feature is the
    # defect this file keeps finding.
    root = state.BY_SRC.get("index.md")
    if root and _routed(root):
        state.note(
            "routers",
            "index.md: a router on the site root does NOT seal the nav. There "
            "is no subtree to withhold that is not the whole sidebar. The body "
            "curtain works as normal.",
        )

    return nav


def on_page_markdown(markdown, page, config, files):
    """Push the resolved metadata onto the page object.

    MkDocs parses frontmatter itself, so page.meta already exists. This merges
    in what hooks 01 and 02 worked out -- resolved type, spec, forced search
    flag -- so templates and later hooks read ONE dictionary rather than
    reaching back into state for every lookup.
    """
    meta = state.BY_SRC.get(page.file.src_uri)
    if meta:
        page.meta.update(meta)
    return markdown
