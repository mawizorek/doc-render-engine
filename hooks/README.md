# hooks/

Thin shims. Every file here imports the event functions for one stage out of
the `docrender` package and does nothing else.

**Why they exist at all.** MkDocs loads hooks by file path and calls whatever
event functions it finds at module level. The real code needs to live in an
importable package so the stages can share `state`, `util`, and each other. So
the package holds the LOGIC and these files hold the ORDER.

**Why they are numbered.** The order is load-bearing, not cosmetic.

## The nav chain, and what each misordering actually breaks

Five stages, all on `on_nav`, and every link matters:

| stage | does | file |
| --- | --- | --- |
| `00` | sorts the tree | `00_instance.py` |
| `00b` | `unlisted` pages leave the sidebar | `00b_unlisted.py` |
| `00bb` | `nav: hidden` folders lose their children | `00bb_navstate.py` |
| `00bc` | routed folders seal whatever is LEFT | `00bc_seal.py` |
| `00c` | prev/next rebuilt from what survived | `00c_nav.py` |

⚠️ **"Any other arrangement disagrees with itself" was the old wording here, and
it is true and useless.** It never said which arrangement breaks what. These two
have actually happened:

- **`00b` or `00bb` after `00c`** — the footer Next button walks through pages
  that are not in the sidebar. Visible on any page, found in minutes.
- **`00bc` before `00bb`** — a `nav: hidden` folder inside a **routed** folder
  is sealed with its children still in it, so a correct router code injects them
  back into the sidebar the folder had removed them from. **Nothing fails,
  nothing warns, and the site looks perfect to everybody without the code.**
  Live on uritp for five hours on 2026-08-05: 43 course pages. That is why the
  seal became its own stage instead of staying pass 3 of the prune, and why
  `visibility.seal_nav` **also** checks `state.NAV_SHAPED` at runtime — a
  filename convention cannot defend a `hooks:` list that somebody edits.

The other chains:

- `01` reads frontmatter before `02` can prune anything, because a broken
  declaration on a hidden page is still broken.
- `02` prunes before `03` indexes, because otherwise a link to a hidden page
  resolves cleanly to a URL that 404s for every reader.
- `01d` emits marker syntax before `03b` renders it, or the token audit page
  ships its specimens as literal text.
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

**The suffix sequence is alphabetical**, so the stage after `00bc` is `00bd`.
Two live instances now, `00bb` and `00bc`. A third letter is only needed to land
something between two adjacent stages — which is itself a signal to check whether
the thing being inserted is really its own stage.

## Two stages out of one module, and that is not a mistake

It happens three times now, and the pattern is worth naming once: **the module
owns the CONCEPT, the filenames own WHEN.** A concept that has to act at two
different moments gets two filenames rather than two copies of itself.

`00b_unlisted.py` and `02_visibility.py` both import from
`docrender/visibility.py`. `status:` is one decision, but MkDocs makes it in two
places: every hook's `on_files` runs before any hook's `on_nav`, so "built" and
"listed" cannot be settled in the same pass.

`00bb_navstate.py` and `06b_navstate.py` both import from
`docrender/navstate.py`. `nav:` is one key, but what a folder CONTAINS is a fact
about the nav tree (`on_nav`), and whether it is OPEN is one attribute Material
writes while rendering a page (`on_post_page`).

`00b_unlisted.py` and `00bc_seal.py` are the odd one out: **same module, same
event, and split anyway.** The prune and the router seal were one function until
2026-08-05 and had to come apart so a third stage could run BETWEEN them.
Nothing about MkDocs forced this one; an ordering requirement did.

⚠️ **`00bb_navstate.py` is the one shim with real code in it**, and the file
says why: `navstate` needs `_index_of` and `_unchain` from `visibility`, and
`visibility` cannot pass them in without importing `navstate` back, which is a
cycle. The wiring goes in the shim rather than a copy of either function going
into the module. If a third stage ever needs those two, that is the moment they
stop being private and get a home of their own.
