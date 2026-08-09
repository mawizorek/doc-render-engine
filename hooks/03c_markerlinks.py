"""Stage 03c -- the LINK form of an inline marker ([fkCal](@rel:table-events)).

After 03b, though the ordering is FREE and that is worth stating so nobody
defends it. The claim happens at hook IMPORT, and MkDocs runs every hook's
`on_files` before any hook's `on_page_markdown`, so links.py at 03 cannot see
a half-built registry no matter where this line sits. It is here because 03b
and 03c read as one feature: 03b renders the span, 03c resolves the link.

🚨 THE IMPORT IS THE FEATURE, WHICH MAKES THIS SHIM LOAD-BEARING IN A WAY THE
OTHERS ARE NOT. docrender/markerlinks.py calls `prefixes.claim()` at module
level, once per namespace in theme/markers.tsv. Drop this file from the
`hooks:` list in mkdocs.yml and the module is never imported, nothing claims
anything, and EVERY link-form marker on EVERY site silently renders as a
broken reference -- no error, no report entry, no clue. Same shape as
`hooks/04_theme.py`, which sits in this folder unregistered and does nothing,
and as the warning in 03b about a function that exists but is not forwarded.

Registration is explicit at both layers and both layers fail quietly.

  on_files  drains the claim-time findings into the build report, and reports
            any prefix in the TSV that nothing claimed

There is deliberately NO `on_page_markdown` here. The link form is rewritten
by links.py at stage 03, through the resolver this module registered -- one
pass over the page, not two.
"""

from docrender.markerlinks import on_files  # noqa: F401
