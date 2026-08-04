"""Hook 02 -- the publication gate.

Four states, inherited from v1 because they were right:

    hidden     not built at all. The URL 404s. This is the default a page
               starts in and the state anything unfinished stays in.
    unlisted   live URL, absent from nav and from search. Shareable by link.
    gated      *** NOT IMPLEMENTED IN ENGINE v1 -- SEE BELOW ***
    public     listed, searchable, done.

Runs before links.py, and the order is load-bearing rather than tidy: if link
resolution indexed pages first, a link to a hidden page would resolve happily
to a URL that 404s for every reader. Prune, then index.

TWO EVENTS, AND THEY CANNOT BE ONE.

`on_files` decides what gets BUILT. `on_nav` decides what gets LISTED. They are
separate stages of the MkDocs lifecycle -- every on_files in every hook runs
before any on_nav in any hook -- and `unlisted` is the one state that needs
both: keep the file, drop the sidebar entry. See prune_nav for the bug that
cost, and for why its stage number is 00b and not 02.

=============================================================================
GATED IS NOT IMPLEMENTED, AND THAT IS DELIBERATE
=============================================================================
v1 shipped `gated` as AES-encrypted page bodies unlocked by a password in the
browser. Engine v1 does not carry that over yet, and a page declaring `gated`
is downgraded to `unlisted` with a loud warning in the build report.

Why downgrade loudly instead of quietly implementing something weaker: a gate
that LOOKS like access control but is not is more dangerous than no gate,
because people put things behind it. The honest limits, which apply to v1's
real implementation just as much:

  * the password ships to the browser inside the page that it protects;
  * publication states control what reaches the SITE, never what is readable
    in the repo, which is public;
  * a GitHub Pages site is publicly reachable even from a private repo.

So the only correct rule is the one stated in every content repo's README: if
it would matter that a stranger read it, it does not belong in a doc repo at
all. Real access control means a host with real authentication in front of it,
not a checkbox here.

=============================================================================
THERE IS NO STATUS CASCADE, AND THE DOCS USED TO CLAIM OTHERWISE
=============================================================================
A folder's index.md does NOT set the state of the pages under it. Every page
carries its own `status:` and nothing here reads a parent's. The template site
asserted a cascade with "the most protective statement wins" for two days
before anybody checked, which is exactly the kind of sentence that is worse
than silence: a reader who believes it hides a folder and thinks the job is
done.

If a cascade is wanted it belongs here, in on_files, before any pruning, and it
has to be conservative -- a parent making a child MORE hidden, never less.
Until then the honest instruction is: set the status on every page.

⚠️ DO NOT READ THE SECTION BELOW AS A CASCADE. `router:` DOES cascade, and it
now takes nav entries with it, but it is not a publication state and it changes
nothing about what is BUILT. A page inside a routed folder is exactly as public
as it was before. Two different mechanisms, one of which is a lock and one of
which is a curtain, and the whole reason the paragraph above exists is that
somebody once believed the curtain was the lock.
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
            # front-matter property that the built-in search plugin honours, so
            # this half works. Setting it here keeps the rule in one file
            # instead of asking every author to remember a second key that
            # means the same thing as the first one.
            #
            # 🔴 THE NAV HALF USED TO LIVE HERE AND WAS A NO-OP. It read
            # `meta["hide"] = ["nav"]`. Wrong key name (Material's is
            # `navigation`) and, more importantly, wrong FEATURE: `hide:` is
            # about which chrome renders ON this page, not about whether this
            # page appears in anybody else's sidebar. Nav membership is not a
            # page property at all. It is decided by the tree, so it is fixed
            # in the tree -- see prune_nav.
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
# ROUTED FOLDERS: TAKE THE SUBTREE OUT OF THE SIDEBAR
# ===========================================================================
# Michael, 2026-08-04, looking at the live Safety section: "routing safety
# should ONLY show SAFETY in the nav and no subpages until the route code is
# input." Decision Log Q10 -> J14, option B.
#
# Before this, `router:` curtained the page BODY and had no opinion about the
# sidebar, so a folder's children were printed on every page of the site --
# including the home page -- to a reader who never typed anything. The section
# name was withheld and the table of contents was not.
#
# WHAT THIS DOES NOT DO, and it is the same sentence prune_nav has always
# carried: it does not unbuild anything. Every sealed page still renders, still
# has a live URL, and is still linkable by `@id`. This is a PRESENTATION
# feature. The body of a routed page is plaintext in the DOM behind the
# `hidden` attribute, it is in search_index.json, and it is markdown in a
# public repo.
#
# ⚠️ SO THE WORD "HIDDEN" DOES NOT APPEAR IN THE AUTHORING DOCS FOR THIS
# FEATURE WITHOUT THE WORD "CASUAL" NEXT TO IT. Ruled at J14, and it is the
# surviving half of the argument that lost: sealing a table of contents while
# the contents sit one <div> down does not protect anything, it just stops the
# shape of a section being handed to somebody with no code.
#
# WHY THE MANIFEST IS SEALED RATHER THAN SHIPPED AS TEXT. The titles have to
# come BACK when a code is typed, and MkDocs bakes the sidebar into every page
# at build time -- so the reveal is a client-side injection, from a payload
# that rides in the page. A plaintext payload would put every withheld title
# in the source of the page that withholds it, which is hiding that does not
# hide. router.py seals it with the AES-GCM wrap it already uses on redirect
# destinations. Michael, on being shown both: "if it's better to encrypt the
# back end and my use is exactly the same and the result is identical, then of
# course encrypt."
#
# ⚠️ KNOWN LIMIT, STATED BECAUSE NOTHING ELSE WILL STATE IT. The payload ships
# on the router's own form, and a form only renders on a page that declares or
# inherits the router. So an unlocked reader sees the revealed subtree on every
# page INSIDE the routed folder, and the section collapses again on pages
# outside it -- the home page, a sibling section -- until they navigate back.
# The alternative is shipping the ciphertext into every page on the site, which
# is more machinery for a cosmetic consistency. Revisit if it actually annoys
# somebody.


def _routed(meta: dict) -> bool:
    """Does this page's own frontmatter declare a router? (Never inherited.)"""
    return bool(meta.get("router") or meta.get("router_code"))


def _index_page(section):
    """The index page inside a section, if it has one.

    Same shape as instance.py's `_index_of`, and deliberately not imported from
    there: that one is about TITLES and this one is about the switch. Sharing it
    would couple two stages through a helper neither of them owns.
    """
    for child in getattr(section, "children", None) or []:
        if getattr(child, "is_page", False) and child.file.name == "index":
            return child
    return None


def _title(item) -> str:
    """What the sidebar would have called this.

    Frontmatter first, because a Page's `title` is not populated until the page
    is RENDERED -- which is long after on_nav. Reading item.title alone would
    have produced a manifest of empty strings that nobody would notice until a
    reader typed a correct code.
    """
    if getattr(item, "is_page", False):
        meta = state.BY_SRC.get(item.file.src_uri, {})
        return str(meta.get("title") or item.title or item.file.name)
    return str(getattr(item, "title", "") or "")


def _unchain(node) -> None:
    """Take a sealed branch out of the reading order.

    00c_nav rebuilds prev/next by flattening the tree, so anything no longer IN
    the tree simply keeps whatever MkDocs wired while building it. Same reason
    _prune nulls these by hand.
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
    """
    _unchain(node)

    if getattr(node, "is_page", False):
        out.append({"t": _title(node), "u": node.file.url, "d": depth})
        return
    if not getattr(node, "is_section", False):
        return

    index = _index_page(node)

    # A folder with an index page is ONE entry pointing at that page -- the
    # sidebar has always shown it that way, and instance.py has already given
    # the section the index page's own title. A folder without one is a label.
    entry = {"t": _title(node), "d": depth}
    if index is not None:
        entry["u"] = index.file.url
    out.append(entry)

    if index is not None and _routed(state.BY_SRC.get(index.file.src_uri, {})):
        # ⭐ THE SECOND HALF OF MICHAEL'S ASK, and it needs no rule of its own:
        # "if only a sub tree is routed (or routed separately than the route on
        # the upper index) it should also remain hidden until ungated."
        #
        # This folder declares its own router, so it is its own curtain. The
        # parent may reveal that it EXISTS and must never reveal what is inside
        # it. Sealed separately, under its own codes, exactly as router.py's
        # `_inherited` already resolves the nearest ancestor and stops.
        _seal(node, index)
        return

    for kid in getattr(node, "children", None) or []:
        if kid is index:
            continue
        _collect(kid, out, depth + 1)


def _seal(section, index) -> None:
    """Strip a routed section back to its index page and stash what was there."""
    items: list = []
    for kid in getattr(section, "children", None) or []:
        if kid is index:
            continue
        _collect(kid, items, 1)

    if not items:
        return

    state.NAV_SEALED[index.file.src_uri] = {
        "anchor": index.file.url,
        "items": items,
    }
    section.children = [index]

    pages = sum(1 for i in items if i.get("u"))
    state.note(
        "routers",
        index.file.src_uri + " · nav sealed · " + str(pages) + " of "
        + str(len(items)) + " entries are pages, withheld from the sidebar "
        + "until a code is typed. Still built, still reachable by URL.",
    )


def _seal_routers(items: list) -> None:
    for item in items:
        if not getattr(item, "is_section", False):
            continue
        index = _index_page(item)
        if index is not None and _routed(state.BY_SRC.get(index.file.src_uri, {})):
            _seal(item, index)
            continue
        _seal_routers(getattr(item, "children", None) or [])


def prune_nav(nav, config, files):
    """Stage 00b -- take `unlisted` pages, then routed subtrees, out of the sidebar.

    🔴 WHY THIS IS NOT IN on_files WITH THE REST OF THE GATE, AND WHY ITS STAGE
    NUMBER IS 00b RATHER THAN 02.

    `unlisted` means built but not listed, so the file has to survive on_files
    and the nav ENTRY has to be removed later. MkDocs runs every hook's
    on_files before any hook's on_nav, so "later" is a different event, not a
    different line.

    The stage number then follows from a second constraint: `00c_nav.py`
    rebuilds prev/next by flattening the nav tree. If this pruning ran at 02 it
    would happen AFTER that, and the footer Next button would walk through
    pages that are not in the sidebar -- the same class of disagreement 00c
    exists to fix, reintroduced from the other end. So it runs at 00b, between
    the sort and the rewire, and the numbering carries the reason.

    ⚠️ THE ROUTER PASS INHERITS THAT CONSTRAINT AND IS THE REASON IT MATTERS
    MOST. A sealed page that stayed in the prev/next chain would put its TITLE
    in the footer of the page before it -- printing the one thing the seal
    exists to withhold, on a page nobody looks at twice. Order is not tidiness
    here; it is the difference between the feature working and leaking.

    ORDER WITHIN THIS FUNCTION IS ALSO LOAD-BEARING: unlisted first, routers
    second. An unlisted page inside a routed folder must not be sealed and
    revealed -- it was never in the sidebar to begin with, and injecting it on
    unlock would put a deliberately unlisted page into a menu.

    WHAT THIS DOES NOT DO: unbuild anything. Every pruned or sealed page still
    renders, still has a live URL, and is still linkable by `@id` from any other
    page. That is the entire definition of `unlisted`, it is the whole design of
    a curtain, and it is the reason `status: hidden` exists separately for the
    other case.
    """
    nav.items = _prune(nav.items)
    _seal_routers(nav.items)

    # A router on the SITE ROOT index has no enclosing section, so there is no
    # subtree for the loop above to take -- it would seal the entire sidebar,
    # which is not a thing anybody has asked for. Reported rather than silently
    # doing nothing, because a no-op that looks like a feature is the defect
    # this file keeps finding.
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
