"""Stage 04c -- fetch the font families the typography vector names.

⚠️ POSITION: after 00 (it reads the resolved instance) and before 05_assets (so
the font stylesheet sits ahead of the ordered asset group rather than inside it).
Both ends are real but neither is a tie-break: a font stylesheet shares no
selector with any sheet in this engine, so it cannot win or lose a specificity
fight. Contrast `_DATA_ASSETS` in docrender/assets.py, where order IS law.

🔴 A LETTER, NOT A DIGIT. `04c` sorts after `04b_router.py` on disk and in this
list; `04.5` or `042` would not. hooks/README.md carries that rule after the
J29 near-miss where a digit suffix made the filesystem and mkdocs.yml disagree
about order inside the one directory whose whole premise is that the filename
carries the order.

⚠️ AND `04_theme.py` SITTING BESIDE THIS IS UNREGISTERED AND DEAD -- mkdocs.yml
says so. Do not read the gap in the numbering as a missing stage.
"""

from docrender.fonts import on_config  # noqa: F401
