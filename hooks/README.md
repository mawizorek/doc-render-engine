# hooks/

Thin shims. Every file here imports the event functions for one stage out of
the `docrender` package and does nothing else.

**Why they exist at all.** MkDocs loads hooks by file path and calls whatever
event functions it finds at module level. The real code needs to live in an
importable package so the stages can share `state`, `util`, and each other. So
the package holds the LOGIC and these files hold the ORDER.

**Why they are numbered.** The order is load-bearing, not cosmetic:

- `00` sorts the nav, `00b` prunes unlisted pages and seals routed subtrees out
  of it, `00bb` applies the `nav:` key to what is left, `00c` rewires prev/next
  from what survived all three. Any other arrangement of those four produces a
  site that disagrees with itself about what its own reading order is.
- `01` reads frontmatter before `02` can prune anything, because a broken
  declaration on a hidden page is still broken.
- `02` prunes before `03` indexes, because otherwise a link to a hidden page
  resolves cleanly to a URL that 404s for every reader.
- `09` runs last because it describes the finished site.

In v1 that constraint existed only as a warning paragraph in a README, which is
the kind of thing that survives exactly until somebody reorders a list. Now the
filename carries it.

A number is not a valid Python identifier, which is fine: these are loaded by
path and never imported. The package they import FROM has ordinary names.

## A suffixed stage takes a LETTER, never a digit

⚠️ `_` sorts AFTER a digit and BEFORE a letter. So `00b2_navstate.py` would sort
ahead of `00b_unlisted.py` on disk while running after it in `mkdocs.yml` — the
filesystem and the config disagreeing about order, in the one directory whose
entire premise is that the filename carries the order. `00bb` sorts and runs in
the same place. Learned 2026-08-05, before it shipped rather than after.

## Two stages out of one module, and that is not a mistake

It happens twice now, for the same underlying reason and in two shapes.

`00b_unlisted.py` and `02_visibility.py` both import from
`docrender/visibility.py`. `status:` is one decision, but MkDocs makes it in two
places: every hook's `on_files` runs before any hook's `on_nav`, so "built" and
"listed" cannot be settled in the same pass.

`00bb_navstate.py` and `06b_navstate.py` both import from
`docrender/navstate.py`. `nav:` is one key, but what a folder CONTAINS is a fact
about the nav tree (`on_nav`), and whether it is OPEN is one attribute Material
writes while rendering a page (`on_post_page`).

In both cases the logic stays together in the module that owns the concept; only
the ORDER is split across filenames, because a filename is the only way to
express order here.

⚠️ **`00bb_navstate.py` is the one shim with real code in it**, and the file
says why: `navstate` needs `_index_of` and `_unchain` from `visibility`, and
`visibility` cannot pass them in without importing `navstate` back, which is a
cycle. The wiring goes in the shim rather than a copy of either function going
into the module. If a third stage ever needs those two, that is the moment they
stop being private and get a home of their own.
