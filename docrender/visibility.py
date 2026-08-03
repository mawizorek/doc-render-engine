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
            # Material reads these off page.meta. Setting them here keeps the
            # rule in one file instead of asking every author to remember two
            # extra frontmatter keys that mean the same thing as the first one.
            meta["hide"] = list(set((meta.get("hide") or []) + ["nav"]))
            meta["search"] = {"exclude": True}

        kept.append(f)

    files_cls = type(files)
    return files_cls(kept)


def on_page_markdown(markdown, page, config, files):
    """Push the resolved metadata onto the page object.

    MkDocs parses frontmatter itself, so page.meta already exists. This merges
    in what hooks 01 and 02 worked out -- resolved type, spec, forced hide and
    search flags -- so templates and later hooks read ONE dictionary rather
    than reaching back into state for every lookup.
    """
    meta = state.BY_SRC.get(page.file.src_uri)
    if meta:
        page.meta.update(meta)
    return markdown
