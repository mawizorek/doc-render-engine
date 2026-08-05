"""Stage 03b -- inline markers, in CLASSES, in two forms.

    [To be confirmed]{.tbc}                 accessory: a span, no underline
    Grid height [18'-0"]{.est} above deck
    A [source 4]{.term} is an ERS fixture
    Made by [ETC](@term:etc)                link: an anchor, underlined

Decision history: doc-render-engine (repo) Decision Log in ClickUp, Q6/J7 for the
class axis and J8 for the `@term:` prefix; maw-themes J11 for the colour token.
The arguments live THERE. This file states the contract and the traps.


TWO AXES OF MEANING
===================

Every marker used to be a confidence claim, and that narrowness protected the
BUILD REPORT: "what is unconfirmed across this whole site" is answerable only
while every row answers the same question. What was missing was a way to say
which kind a row IS -- so terminology was nearly built as a second, parallel
family, because the table had no column for it.

`class` is now a column, families live in theme/marker-classes.tsv, and the
report groups by class. Confidence stays answerable however many terms a site
marks.

A class carries the default SHAPE and COLOUR; a row overrides either. `est` and
`was` keep soft and struck as OVERRIDES rather than as the only mechanism, and a
new terminology row is a slug and a tooltip.

SHAPE IS STILL A CLOSED SET OF FOUR (box, plain, strike, soft): four are
distinguishable at a glance, nine are not. Terminology needed colour and weight
without an underline, which is `plain`, which already existed -- the class axis
cost the shape axis nothing.


TWO FORMS, AND THE UNDERLINE IS THE ONLY DIFFERENCE A READER SEES
================================================================

Same class, same colour, same weight; only the link is underlined. A reader
learns that in one page without being told, because underline already means
"this goes somewhere" everywhere else.

This module owns both forms and claims `@term:` itself rather than delegating to
a module of its own -- not for tidiness, but so the two forms cannot disagree
about which family they are. `_TERM_CLASS` is read by the span renderer AND the
link resolver. A second module would be a second place to name the family.

⚠️ A DEAD `@term:` NEVER DEGRADES INTO AN ACCESSORY. The resolver returns None,
links.py reports it and renders the broken-reference span. Falling back to the
underlineless form would be a silent second legal path for a reference that did
not resolve (the fallback shape struck in J2) and would make "which terms still
have no page" unanswerable -- which is why both forms are counted.

⚠️ `@term:` RESOLVES AGAINST ANY PAGE ID, deliberately loosely. There is no
`term` page TYPE, so there is nothing to check against, and inventing one here
would decide a schema question inside a rendering hook. Consequence, stated
rather than hidden: `@term:main-stage` will point at a venue page. The place to
tighten that is objects/, not here.


WHY THIS IS A HOOK AND NOT A MARKDOWN EXTENSION
===============================================

`attr_list` decorates elements that ALREADY EXIST. `[text]{.tbc}` is a bare
bracketed span -- Pandoc syntax, not an element Python-Markdown produces -- so
the attribute has nothing to attach to and the braces render as literal text.
That is what shipped on the live curtain inventory.

⭐ The LINK form is the opposite case and needs no hook: an anchor IS an element
attr_list can decorate, so the resolver hands links.py an ordinary markdown link
wearing two classes.


COLOUR IS RESOLVED ONCE PER BUILD, AND THAT IS A FIX
====================================================

`_colour()` used to run inside the per-MATCH replacement, so an unknown token
reported once per OCCURRENCE. Six markers on a page hid that completely; a
terminology class used three hundred times would have buried the report under
three hundred copies of one complaint -- and the report is the only reason this
beats a highlighter.

The table is merged and resolved in `on_files`, once. In an event and not at
import, because `mkdocs serve` rebuilds in-process and a table cached at import
would outlive an edit to either TSV.

Class colour is emitted as a REAL CSS RULE by `build_css()`. The inline custom
property survives for a ROW override only: a rule per class is cheap, a rule per
marker was not, which is what the inline property existed to avoid.


🔴 THE VALIDATOR WAS A SECOND OPINION ABOUT WHAT A COLOUR IS (fixed 2026-08-05)
==============================================================================

`_known_tokens()` read theme/colors.tsv -- the NINE-TOKEN stand-in that this
engine has been retiring for two days -- and REFUSED anything absent from it. The
canonical palette emits 22 tokens. Markers could see two of them.

So the canonical join landed and this file never noticed, for hours, in a repo
that spent the same night wiring four vectors into every other surface. ⚑ The
generalisable shape: A VALIDATION LIST IS A SECOND SOURCE OF TRUTH ABOUT ITS
SUBJECT, and it goes stale exactly like a manifest -- this repo has killed three
manifests for that and then kept one in a function. It now reads the canonical
header row, which IS the list, so there is nothing left to keep in step.

⚠️ AND THE FALLBACK IS THE LOAD-BEARING HALF. A site on a local theme emits no
canonical properties at all, and `var(--dr-accent-2)` with nothing behind it
resolves to NOTHING -- an invisible marker, worse than a wrong colour because it
reports nothing and looks like an authoring mistake. Canonical tokens are emitted
as `var(--dr-x, currentColor)`; local ones stay bare because they are always
there. The old refusal painted currentColor too, so the floor is unchanged and no
site can render worse than it did yesterday.

🔴 IT ALSO HID A REAL DEFECT FOR A WEEK. `terminology` asked for `accent-soft`,
which measures 1.29 on the dark canvas and 1.12 on the light against a floor of
4.5 -- it is the tinted BACKGROUND behind a chip, not a letters colour. The
refusal was the only thing standing between that cell and an invisible glossary.
Measured before wiring, changed to `accent-2`. ⚑ Removing a guard means checking
what it was holding back, not just that it was wrong to hold it.

Defined in theme/markers.tsv + theme/marker-classes.tsv. Adding one is a row.
"""

from __future__ import annotations

import html
import re

from . import prefixes, state, vectors
from .util import load_tsv, relative_url, sub_outside_code

# [text]{.marker} with optional whitespace, or bare {.marker}.
_MARK = re.compile(
    r"(?:\[(?P<text>[^\]\n]*)\])?\{[ \t]*\.(?P<marker>[a-z][a-z0-9-]*)[ \t]*\}"
)

# A colour that is a bare word is a TOKEN and resolves against the theme. Any
# thing else -- #hex, oklch(...), rgb(...) -- is passed through as written.
_TOKEN = re.compile(r"^[a-z][a-z0-9-]*$")

_SHAPES = {"box", "plain", "strike", "soft"}
_FALLBACK_SHAPE = "box"

#: The family `@term:` belongs to. Read by BOTH the span renderer and the link
#: resolver so the forms cannot drift. Must match a `class` row in
#: theme/marker-classes.tsv.
_TERM_CLASS = "terminology"

#: Carried by the LINK form on top of its family class, so an anchor can take the
#: family colour without also taking `.dr-mark` -- whose `cursor: help` and
#: `white-space: nowrap` are both wrong on something clickable.
_TERM_LINK_CLASS = "dr-term"

#: Marker name -> resolved row. Built by on_files, read by on_page_markdown.
_TABLE: dict[str, dict] = {}


def _rows(name: str) -> list[dict]:
    return load_tsv(state.ENGINE_ROOT / "theme" / name)


def _classes() -> dict[str, dict]:
    return {r["class"]: r for r in _rows("marker-classes.tsv") if r.get("class")}


def _local_tokens() -> set[str]:
    """The nine-token stand-in. ALWAYS emitted, so these need no fallback."""
    return {r["token"] for r in _rows("colors.tsv") if r.get("token")}


def _canonical_tokens() -> set[str]:
    """Every token the canonical palette can emit, read off its header row.

    Derived rather than listed. A hardcoded copy here would be a second opinion
    about what the design system contains, which is the defect that kept this
    validator two days behind the join it was supposed to be validating.

    Empty if the canonical table is missing, which degrades to exactly the old
    local-only behaviour rather than to a crash.
    """
    rows = vectors.rows("colors.tsv")
    if not rows:
        return set()
    return {k for k in rows[0] if k and k not in vectors.META}


def _colour(value: str, where: str, tokens: tuple[set, set], report: bool = True) -> str:
    """Resolve a colour to something CSS can use.

    `tokens` is (local, canonical) and the split decides the FALLBACK, not the
    validity. A local token is emitted bare because the local table is always
    read; a canonical one carries `, currentColor` because a site on a local
    theme emits no canonical properties and a bare var() would render the marker
    INVISIBLE -- silent, unreported, and indistinguishable from a typo.

    `report` exists because build_css() runs from assets._plan, which is called by
    BOTH on_config and on_files and would therefore complain twice about one bad
    cell. The single honest complaint comes from _build_table, which runs once.
    """
    local, canonical = tokens
    value = (value or "").strip()
    if not value:
        return "currentColor"
    if not _TOKEN.match(value):
        return value
    if value in local:
        return "var(--dr-" + value + ")"
    if value in canonical:
        return "var(--dr-" + value + ", currentColor)"
    if report:
        # Falling back silently would render an INVISIBLE marker -- var() with no
        # fallback resolves to nothing -- so it is reported and given a real colour.
        # The two lists are printed SEPARATELY because "accent-2 is not a token"
        # was the baffling part of this defect, and a merged list would keep it so.
        state.note(
            "notes",
            where + " asks for colour token '" + value + "', which no theme in "
            + "this engine emits. Using the body colour. Canonical: "
            + (", ".join(sorted(canonical)) or "none") + ". Local: "
            + ", ".join(sorted(local)) + ".",
        )
    return "currentColor"


def _token_sets() -> tuple[set, set]:
    return _local_tokens(), _canonical_tokens()


def _build_table() -> dict[str, dict]:
    """Merge every marker row with its class defaults. Once per build."""
    classes = _classes()
    tokens = _token_sets()
    table: dict[str, dict] = {}

    if not classes:
        state.note(
            "notes",
            "theme/marker-classes.tsv is missing or empty, so every marker falls "
            + "back to a boxed body-coloured chip. Markers still render; the "
            + "families do not.",
        )
    elif _TERM_CLASS not in classes:
        # @term: is claimed unconditionally at import, so the link form keeps
        # resolving even here -- it would just paint from a class rule that was
        # never generated, i.e. body colour with no explanation anywhere.
        state.note(
            "notes",
            "theme/marker-classes.tsv declares no '" + _TERM_CLASS + "' class, but "
            + "@term: links resolve against it. They will render underlined in the "
            + "body colour until that row exists.",
        )

    # Reported here rather than in build_css so one bad cell complains once.
    for name in sorted(classes):
        _colour(classes[name].get("color", ""), "marker class '" + name + "'", tokens)

    for row in _rows("markers.tsv"):
        name = row.get("marker")
        if not name:
            continue

        klass = (row.get("class") or "").strip()
        parent = classes.get(klass) or {}
        if not klass:
            state.note(
                "notes",
                "marker '" + name + "' declares no class. Every row belongs to a "
                + "family now -- that is what keeps the report answerable once not "
                + "every marker is a confidence claim.",
            )
        elif klass not in classes:
            state.note(
                "notes",
                "marker '" + name + "' is in class '" + klass + "', which is not in "
                + "theme/marker-classes.tsv. Known: "
                + (", ".join(sorted(classes)) or "none") + ".",
            )

        shape = (row.get("shape") or parent.get("shape") or _FALLBACK_SHAPE).strip()
        if shape not in _SHAPES:
            state.note(
                "notes",
                "marker '" + name + "' resolves to shape '" + shape + "', which is "
                + "not one of " + ", ".join(sorted(_SHAPES)) + ". Using '"
                + _FALLBACK_SHAPE + "'.",
            )
            shape = _FALLBACK_SHAPE

        own = (row.get("color") or "").strip()
        table[name] = {
            "class": klass,
            "label": row.get("label") or "",
            "shape": shape,
            "tooltip": row.get("tooltip") or "",
            # A row override becomes an inline property. An unset colour inherits
            # the generated class rule and needs nothing on the span at all.
            "colour": _colour(own, "marker '" + name + "'", tokens) if own else "",
        }
    return table


def build_css() -> str:
    """Class colours as real rules. Published as marks.css by assets.py.

    Specificity is deliberate: `.md-typeset .dr-mark--cls-x` is two classes and
    beats base.css's one-class `.dr-mark` currentColor default, so base.css does
    not need to know this sheet exists. A ROW override is inline and beats both.
    Shape stays in base.css -- only colour is generated.
    """
    classes = _classes()
    tokens = _token_sets()

    lines = [
        "/* GENERATED by docrender/markers.py -- do not edit.",
        "   One rule per marker CLASS, from theme/marker-classes.tsv,",
        "   plus the one static rule for the @term: link form.",
        "   Shape lives in assets/base.css; colour is data. */",
    ]
    for name in sorted(classes):
        value = _colour(
            classes[name].get("color", ""),
            "marker class '" + name + "'",
            tokens,
            report=False,
        )
        lines.append(
            ".md-typeset .dr-mark--cls-" + name
            + " { --dr-mark-color: " + value + "; }"
        )

    # THE LINK FORM. An anchor carrying its family class inherits the custom
    # property set above; this rule consumes it, deliberately WITHOUT `.dr-mark`.
    #
    # ⚠️ THE UNDERLINE IS EXPLICIT, AND THAT IS NOT REDUNDANCY. The whole design
    # rests on underline being the one visible difference between the two forms,
    # and Material's link styling is a framework default nobody has verified
    # persists an underline in this build. An affordance the design depends on is
    # not left to somebody else's default. If Material underlines too, this is a
    # no-op.
    #
    # Emitted HERE rather than in base.css for a boring reason worth stating:
    # base.css is close enough to the read ceiling that a wholesale rewrite from
    # one read is the clobber that ate util.py on 2026-08-03. This file already
    # generates the colour half.
    lines.append(
        ".md-typeset a." + _TERM_LINK_CLASS + " { color: var(--dr-mark-color);"
        + " text-decoration: underline; text-decoration-thickness: 1px;"
        + " text-underline-offset: 0.15em; }"
    )

    return "\n".join(lines) + "\n"


def _resolve_term(slug: str, page, label: str):
    """Resolve `@term:<page-id>` to an underlined, terminology-coloured link.

    Registered with docrender/prefixes.py and called from links.py while it
    rewrites inline references. Returns None to decline, which is what makes a
    term with no page render as the broken-reference span rather than an
    accessory.

    Resolves against `state.PAGES`, populated in links.on_files, which therefore
    holds only pages that were actually BUILT. A term whose page exists but is
    hidden declines here, and that is correct: a link to a page nobody can open is
    a broken link, not a working one.
    """
    hit = state.PAGES.get(slug)
    if not hit:
        return None

    # Resolved against THIS page, never from a separator count -- util.relative_url
    # carries the whole story of why that distinction cost a live 404.
    target = relative_url(str(hit.get("url", "")), page.file.url)

    # Counted like the span form, in the same shape, so the report answers "every
    # terminology reference on this site" for both forms at once.
    state.note(
        "markers",
        _TERM_CLASS + " \u00b7 term \u00b7 " + page.file.src_uri + " \u00b7 "
        + label + " \u2192 " + slug,
    )

    return (
        "[" + label + "](" + target + "){ ." + _TERM_LINK_CLASS
        + " .dr-mark--cls-" + _TERM_CLASS + " }"
    )


# Claimed at IMPORT time, which is the contract prefixes.py documents: claims
# happen when hook modules are imported, lookups happen later inside events.
# Registering is how the handler works, so it cannot be forgotten.
prefixes.claim("term", __name__, _resolve_term)


def on_files(files, config):
    global _TABLE
    _TABLE = _build_table()
    return files


def on_page_markdown(markdown, page, config, files):
    if "{" not in markdown or not _TABLE:
        return markdown

    src = page.file.src_uri

    def replace(match):
        name = match.group("marker")
        row = _TABLE.get(name)
        if not row:
            # Not one of ours. Almost certainly an attr_list attribute on a real
            # element (`{ .md-button }`), or the two-class block links.py just
            # emitted for an @term: link, so hand it back untouched rather than
            # eating syntax that belongs to somebody else.
            return match.group(0)

        text = (match.group("text") or "").strip() or row["label"] or name
        klass = row["class"]

        css = ["dr-mark", "dr-mark--" + row["shape"]]
        if klass:
            css.append("dr-mark--cls-" + klass)

        style = ""
        if row["colour"]:
            style = (
                ' style="--dr-mark-color: '
                + html.escape(row["colour"], quote=True) + '"'
            )

        # CLASS LEADS the entry, so the sorted inventory reads as families.
        state.note(
            "markers",
            (klass or "unclassed") + " \u00b7 " + name + " \u00b7 " + src
            + " \u00b7 " + text,
        )

        return (
            '<span class="' + " ".join(css) + '"'
            + ' data-mark="' + html.escape(name) + '"' + style
            + ' title="' + html.escape(row["tooltip"], quote=True) + '">'
            + html.escape(text) + "</span>"
        )

    return sub_outside_code(_MARK, replace, markdown)


def on_post_build(config):
    """Sort the inventory so it reads as families rather than as page order.

    Runs before hook 08 prints, because MkDocs dispatches an event to hooks in
    REGISTRATION order and 03b is registered before 08. That is the same ordering
    dependency mkdocs.yml already documents for the nav chain -- if this ever
    stops working, check that list before you check this function.
    """
    entries = state.REPORT.get("markers")
    if entries:
        entries.sort()
