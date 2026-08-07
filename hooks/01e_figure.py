"""Stage 01e -- a captioned image becomes a real `<figure>`.

    ![alt](rep-plot.png){ caption="Rep plot, Ogunquit 2026" }

ONE EVENT, and the position in the `hooks:` list is the load-bearing part:

  on_page_markdown   wraps the image, leaves the caption as markdown

⚠️ BEFORE 03_links AND 03b_markers, NOT AFTER. The caption is emitted as
markdown inside a `markdown="span"` figcaption precisely so those two stages
resolve its `@`-references and `{.tbc}` markers on their ordinary pass over the
page. Move this after either one and a caption keeps its raw `@id` and brace
syntax as literal text -- the page renders, the figure appears, and only the
caption is wrong. Same relationship `01d_audit` has with `03b`.

⚠️ AFTER 01b_data is not required, but it is correct: a caption inside a TSV
cell is `cells.render`'s problem and never reaches this pattern, and keeping the
two emitters in declaration order makes that easy to check.

Letter, not digit, per hooks/README.md -- `_` sorts after a digit and before a
letter, so `01d2_` would sort ahead of `01d_` on disk while running after it
here. `01d` is taken; this is `01e`.
"""

from docrender.figure import on_page_markdown  # noqa: F401
