# hooks/

Thin shims. Every file here imports the event functions for one stage out of
the `docrender` package and does nothing else.

**Why they exist at all.** MkDocs loads hooks by file path and calls whatever
event functions it finds at module level. The real code needs to live in an
importable package so the stages can share `state`, `util`, and each other. So
the package holds the LOGIC and these files hold the ORDER.

**Why they are numbered.** The order is load-bearing, not cosmetic:

- `00` sorts the nav, `00b` prunes unlisted pages out of it, `00c` rewires
  prev/next from what is left. Any other arrangement of those three produces a
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

**Two stages come out of one module, and that is not a mistake.**
`00b_unlisted.py` and `02_visibility.py` both import from
`docrender/visibility.py`. `status:` is one decision, but MkDocs makes it in two
places: every hook's `on_files` runs before any hook's `on_nav`, so "built" and
"listed" cannot be settled in the same pass. The logic stays together in the
module that owns the concept; only the ORDER is split across two filenames,
because a filename is the only way to express order here.
