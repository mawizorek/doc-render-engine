"""Hook 02 -- the publication gate.

WHY decisions here are the way they are: the doc-render-engine Decision Log.
This docstring is the CONTRACT and is kept under the read-whole line.

Four states, inherited from v1 because they were right:

    hidden     not built at all. The URL 404s. The default a page starts in and
               the state anything unfinished stays in.
    unlisted   live URL, absent from nav and from search. Shareable by link.
    gated      *** NOT IMPLEMENTED. Downgraded to `unlisted`, loudly. ***
    public     listed, searchable, done.

Runs before links.py, and the order is load-bearing rather than tidy: if link
resolution indexed pages first, a link to a hidden page would resolve happily
to a URL that 404s for every reader. Prune, then index.

=============================================================================
TWO EVENTS, AND THEY CANNOT BE ONE
=============================================================================
`on_files` decides what gets BUILT. `on_nav` decides what gets LISTED. Every
hook's on_files runs before any hook's on_nav, so `unlisted` -- keep the file,
drop the sidebar entry -- needs both. See `prune_nav` for why its stage number
is 00b and not 02.

⚠️ AND THIS MODULE OWNS TWO on_nav STAGES, NOT ONE. `prune_nav` at 00b,
`seal_nav` at 00bc, with navstate's 00bb deliberately BETWEEN them. They were
one function until 2026-08-05; `seal_nav` carries the live bug that split them
and the ordering law that keeps them apart.

=============================================================================
GATED IS NOT IMPLEMENTED, AND THAT IS DELIBERATE
=============================================================================
v1 shipped `gated` as AES-encrypted page bodies. A page declaring it here is
downgraded to `unlisted` with a warning, rather than quietly given something
weaker: **a gate that LOOKS like access control but is not is more dangerous
than no gate, because people put things behind it.** The honest limits, which
applied to v1's real implementation just as much: the password ships to the
browser inside the page it protects; publication states control what reaches
the SITE, never what is readable in the repo; and a Pages site is publicly
reachable even from a private repo.

So the only correct rule is the one in every content repo's README: if it would
matter that a stranger read it, it does not belong in a doc repo at all.

=============================================================================
THERE IS NO STATUS CASCADE, AND THE DOCS USED TO CLAIM OTHERWISE
=============================================================================
A folder's index.md does NOT set the state of the pages under it. Every page
carries its own `status:` and nothing here reads a parent's. The template site
asserted a cascade for two days before anybody checked -- worse than silence,
because a reader who believes it hides a folder and thinks the job is done.

⚠️ DO NOT READ THE ROUTER SECTION BELOW AS A CASCADE. `router:` DOES cascade
and now takes nav entries with it, but it is not a publication state and
changes nothing about what is BUILT. A page inside a routed folder is exactly
as public as it was before. One is a lock, one is a curtain, and the paragraph
above exists because somebody once believed the curtain was the lock.
"""

from __future__ import annotations

from . import state


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
            # SEARCH ONLY. `search.exclude` is a real, documented, non-Insiders
            # front-matter property the built-in search plugin honours, so this
            # half works. Keeping the rule here saves every author remembering
            # a second key that means the same thing as the first.
            #
            # 🔴 THE NAV HALF USED TO LIVE HERE AND WAS A NO-OP. It read
            # `meta["hide"] = ["nav"]`: wrong key name (Material's is
            # `navigation`) and, more importantly, wrong FEATURE -- `hide:` is
            # about which chrome renders ON this page, not whether this page
            # appears in anybody else's sidebar. Nav membership is not a page
            # property at all. It is decided by the tree, so it is fixed in the
            # tree -- see prune_nav.
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
# ROUTED FOLDERS: TAKE THE SUBTREE OUT OF THE SIDEBAR (DL J14)
# ===========================================================================
# Michael, looking at the live Safety section: "routing safety should ONLY show
# SAFETY in the nav and no subpages until the route code is input." Before this,
# `router:` curtained the page BODY and had no opinion about the sidebar, so the
# section NAME was withheld and its table of contents was not.
#
# ⚠️ SEALING IS PRESENTATION, NOT PROTECTION, and the word "hidden" does not go
# into the authoring docs for it without the word "casual" next to it (J14).
# Every sealed page still renders, still has a live URL, and is still linkable
# by `@id`; the body of a routed page is plaintext in the DOM behind `hidden`
# and in search_index.json. What this stops is the SHAPE of a section being
# handed to somebody with no code.
#
# The manifest is SEALED rather than shipped as text because the titles have to
# come back on unlock, and a plaintext payload would put every withheld title in
# the source of the page withholding it. router.py does the sealing.
#
# ⚠️ KNOWN LIMIT: the payload rides on the router's form, and a form renders
# only where the router is declared or inherited. So an unlocked reader keeps
# the revealed subtree on every page INSIDE the folder and loses it on pages
# outside. Shipping ciphertext into every page on the site is more machinery for
# a cosmetic consistency. Revisit if it actually annoys somebody.
#
# ⚠️ ONE CORRECTION KEPT RATHER THAN DELETED, full version in the DL: an earlier
# draft of this block claimed the children showed "on every page of the site,
# including the home page." They did not -- `navigation.prune` renders only the
# ancestors and siblings of the active page. The complaint was real; the blast
# radius was asserted without being checked, in a file whose whole subject is
# claims that were not checked.


def _routed(meta: dict) -> bool:
    """Does this page's own frontmatter declare a router? (Never inherited.)"""
    return bool(meta.get("router") or meta.get("router_code"))


def _find_index(section):
    """The index page inside a section, read from the LIVE children."""
    for child in getattr(section, "children", None) or []:
        if getattr(child, "is_page", False) and child.file.name == "index":
            return child
    return None


def _mark_indexes(items: list) -> None:
    """Record every section's index page BEFORE anything is pruned.

    🔴 NEVER RE-DERIVE AN INDEX FROM LIVE CHILDREN AFTER THIS POINT. The seal
    used to scan surviving children for it, and an index page with `status:
    unlisted` has already been dropped by `_prune` by then -- so the lookup
    returned None, the section was never recognised as routed, and its children
    stayed listed in full. The feature failing silently on the one page that
    needed it. Live instance: `production/staff/index.md`, 2026-08-04, and the
    ordering comment in `prune_nav` is what caused it. Full account in the DL.
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

    ⭐ THIS FUNCTION KNOWS NOTHING ABOUT `nav:` AND MUST NOT LEARN. It walks a
    tree navstate has already trimmed at 00bb, so a `nav: hidden` folder arrives
    holding only its own index and contributes exactly one row for free. Teaching
    it the key would be a second copy of a rule that is already enforced by the
    stage order -- and a second copy is free to drift from the first. See
    `seal_nav` for what happened when the order was wrong.
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
        _seal(node, index)
        return

    for kid in getattr(node, "children", None) or []:
        if kid is index:
            continue
        _collect(kid, out, depth + 1)


def _seal(section, index) -> bool:
    """Strip a routed section back to its index page and stash what was there.

    Returns True if the section should stay in the sidebar. False means it has
    nothing left to show -- see the conflict below.
    """
    items: list = []
    for kid in getattr(section, "children", None) or []:
        if kid is index:
            continue
        _collect(kid, items, 1)

    if not items:
        # ⭐ A ROUTED FOLDER WITH NOTHING TO WITHHOLD, and since 2026-08-05 the
        # usual cause is `nav: hidden` on this same index getting there first at
        # stage 00bb. That is NOT a conflict and does not need resolving: never
        # offered is a stronger claim than offered to a code, and the stronger
        # one wins by arriving first. Reported because "router declared, no
        # manifest" is otherwise a silent surprise to whoever wrote the router.
        state.note(
            "routers",
            index.file.src_uri + " · router declared, nav manifest EMPTY · "
            + "nothing under this folder to withhold. If it also declares "
            + "`nav: hidden`, that is why: hidden takes the children out of the "
            + "sidebar for everybody, which is stronger than sealing them "
            + "behind a code. The body curtain works as normal.",
        )
        return True

    state.NAV_SEALED[index.file.src_uri] = {
        "anchor": index.file.url,
        "items": items,
    }

    # 🔴 `status: unlisted` ON A ROUTED FOLDER INDEX IS A DIRECT CONTRADICTION,
    # AND THE ENGINE REPORTS IT RATHER THAN PICKING A WINNER QUIETLY.
    #
    #   unlisted   says: this page is not in the sidebar.
    #   nav-seal   says: ONLY this page is in the sidebar.
    #
    # There is no arrangement satisfying both. Resolved the PROTECTIVE way --
    # the children stay sealed and the section leaves the nav entirely -- on the
    # same principle as everywhere else here: when two declarations disagree,
    # the one that shows LESS wins, and the report says so loudly enough to fix.
    #
    # ⚠️ The cost is real and is named in the report: with no index row there is
    # no anchor for router.js to inject under, so a correct code opens the page
    # BODY and cannot restore the menu. The fix is one word in the content repo,
    # and the report prints it.
    survives = index in (getattr(section, "children", None) or [])
    section.children = [index] if survives else []

    pages = sum(1 for i in items if i.get("u"))
    if survives:
        state.note(
            "routers",
            index.file.src_uri + " · nav sealed · " + str(pages) + " of "
            + str(len(items)) + " entries are pages, withheld from the sidebar "
            + "until a code is typed. Still built, still reachable by URL.",
        )
    else:
        state.note(
            "missing_required",
            index.file.src_uri + ": `status: unlisted` and a nav-sealing "
            + "`router:` contradict each other -- unlisted keeps this page OUT "
            + "of the sidebar, sealing leaves it as the ONLY thing in it. The "
            + str(len(items)) + " entries under it are sealed (the protective "
            + "reading) and the whole section is gone from the nav, so no code "
            + "can reveal the menu: there is no row to reveal it under. Set "
            + "`status: public` on this index for the collapsed-section "
            + "behaviour, or drop `router:` to list the folder normally.",
        )
    return survives


def _seal_routers(items: list) -> list:
    """Seal every routed section, dropping any left with nothing to show."""
    kept = []
    for item in items:
        if not getattr(item, "is_section", False):
            kept.append(item)
            continue
        index = _index_of(item)
        if index is not None and _routed(state.BY_SRC.get(index.file.src_uri, {})):
            if _seal(item, index):
                kept.append(item)
            continue
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
    by flattening the nav tree, so this has to happen BEFORE it or the footer
    Next button walks through pages that are not in the sidebar -- the same
    disagreement 00c exists to fix, reintroduced from the other end.

    TWO PASSES:

      1. MARK. Record each section's index page while the tree is untouched.
         Pass 2 can delete an index, and every later stage needs to know it was
         there.
      2. PRUNE unlisted pages.

    Pass 1 exists because 2 and 3 used to be the whole function and disagreed
    with each other -- see `_mark_indexes`. ⚠️ PASS 3 IS NOT HERE ANY MORE: the
    router seal is `seal_nav` at stage 00bc, with navstate's 00bb between them,
    and that split is not a tidy-up. See `seal_nav`.
    """
    _mark_indexes(nav.items)
    nav.items = _prune(nav.items)
    return nav


def seal_nav(nav, config, files):
    """Stage 00bc -- seal routed subtrees, AFTER `nav:` has shaped the tree.

    🔴 THIS WAS PASS 3 OF `prune_nav` UNTIL 2026-08-05, AND SHARING A FUNCTION
    WITH THE PRUNE IS WHAT BROKE `nav: hidden`.

    uritp declares `router: pm` on `courses/index.md` and `nav: hidden` on
    `courses/course-info/`. The seal ran at 00b and harvested the WHOLE courses
    subtree into the sealed manifest before navstate reached 00bb -- so by the
    time `nav: hidden` was read, its folder was already out of the tree and the
    cut had nothing to act on. All 43 course pages sat in the ciphertext and
    reappeared in the sidebar the moment a correct code was typed. Michael, who
    holds that code: "i never expect to see the exhaustive list of course info
    docs in the nav."

    ⚑ SIXTH INSTANCE OF ONE SHAPE HERE -- a rule correct in isolation and
    unreachable in place -- and the ordering COMMENT caused this one. navstate
    has to run after the prune because it reads index pages the prune can
    delete. True, and exactly what let the seal reach the subtree first. Same
    shape as `_mark_indexes` twenty lines up: a rule defended in one direction
    is not a rule that was thought about in both.

    ⭐ THE FIX IS THE ORDER, NOT A SECOND CHECK. `_collect` is not taught about
    `nav:` at all -- see its docstring for why that restraint is the point.

    THE on_nav CHAIN, AND EVERY LINK IS LOAD-BEARING:

      00    sort     instance.py orders the tree
      00b   prune    unlisted pages leave            <- prune_nav
      00bb  shape    `nav: hidden` folders are cut   <- navstate.shape
      00bc  seal     routers take what is LEFT       <- HERE
      00c   chain    prev/next rebuilt from all of it

    ⚠️ PRUNE AND SHAPE BOTH PRECEDE THE SEAL FOR ONE REASON, WORTH STATING ONCE:
    a page the sidebar deliberately does not show must never be sealed and then
    INJECTED into a menu on unlock. `unlisted` has always had that guarantee.
    `nav: hidden` has it now.
    """
    if not state.NAV_SHAPED:
        # 🔴 A REGRESSION DETECTOR, NOT A DEFENSIVE CROUCH, and it is the half of
        # this fix that outlives me. If 00bb is ever unregistered, renamed or
        # renumbered past this stage, the seal goes straight back to harvesting
        # untrimmed subtrees -- silently, and invisible until somebody types a
        # code and sees pages a folder had shut. The bug above was reachable for
        # five hours because nothing could notice it. This can.
        state.note(
            "missing_required",
            "STAGE ORDER BROKEN: the router nav-seal (00bc) ran before navstate "
            + "(00bb), so any `nav: hidden` folder inside a routed folder was "
            + "sealed with its children still in it -- and a correct router code "
            + "will reveal pages that were meant to be out of the sidebar "
            + "entirely. Check the `hooks:` list in mkdocs.yml: 00b, then 00bb, "
            + "then 00bc, then 00c.",
        )

    nav.items = _seal_routers(nav.items)

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
