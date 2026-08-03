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


def prune_nav(nav, config, files):
    """Stage 00b -- take `unlisted` pages out of the sidebar.

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

    WHAT THIS DOES NOT DO: unbuild anything. Every pruned page still renders,
    still has a live URL, and is still linkable by `@id` from any other page.
    That is the entire definition of `unlisted` and the reason `status: hidden`
    exists separately for the other case.
    """
    nav.items = _prune(nav.items)
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
