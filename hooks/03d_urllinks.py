"""Stage 03d -- the `@url:` namespace (an external link, named once in config).

After 03c, and the ordering is FREE for exactly the reason 03c's and 01f's are,
which is worth restating so nobody defends this number. The prefix claim happens
at hook IMPORT, and MkDocs runs every hook's `on_files` before any hook's
`on_page_markdown`, so links.py at stage 03 cannot see a half-built registry no
matter where this line sits. It is here because 03c and 03d are the same kind of
thing: a module whose whole job is to own an `@` namespace.

🚨 THE IMPORT IS THE FEATURE, WHICH MAKES THIS SHIM LOAD-BEARING IN THE WAY 03c
IS AND MOST OF THE OTHERS ARE NOT. docrender/urllinks.py calls
`prefixes.claim('url', ...)` at module level. Drop this file from the `hooks:`
list in mkdocs.yml and the module is never imported, nothing claims the
namespace, and every `@url:` on every site renders as *unknown peer site: url* --
which is links.py behaving correctly and is a complete mystery from the author's
chair. Same shape as `hooks/04_theme.py`, which sits in this folder unregistered
and does nothing whatsoever.

  on_files  audits every declared `links:` entry -- in site.yml and in page
            frontmatter -- whether or not anything references one yet. ⭐ That is
            the half a resolve-time check cannot do: the report is most useful to
            whoever just typed the entry.

There is deliberately NO `on_page_markdown` here. The reference is rewritten by
links.py at stage 03, through the resolver this module registered -- one pass
over the page, not two.
"""

from docrender.urllinks import on_files  # noqa: F401
