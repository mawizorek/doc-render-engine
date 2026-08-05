"""Hook 01d -- THE TOKEN AUDIT. What the canonical vectors actually control.

Written in a page as one line:

    !!! tokens

Everything under it is GENERATED from the files that are shipping in THIS
build. Nothing on the page is a list somebody maintains, because a hand-kept
inventory of what a stylesheet does is wrong the first time anybody edits the
stylesheet -- and this page exists precisely to be trusted about that.

WHAT IT ANSWERS, in order:

  1 VECTORS   which of the four canonical vectors this site actually consumes
  2 TOKENS    every --dr-* that reaches the browser, both schemes, and where
              the value came from: canonical row, local table, or alias
  3 CONSUMERS for each token, every selector and property that reads it
  4 LITERALS  every hardcoded colour and metric in the sheets WE wrote
  5 UNGOVERNED  surfaces nobody styles at all -- declared in
              theme/ungoverned.tsv, verdict DERIVED by probing our CSS
  6 MARKERS   live specimens, rendered by markers.py rather than by this file

SWATCHES ARE PAINTED WITH `var(--dr-token)`, NEVER WITH THE HEX. Printing a hex
proves we can read a table. Painting with the variable proves the variable
reaches the browser, which is the only question worth asking here. If the pipe
breaks, the swatch goes blank while the printed value beside it stays correct --
and that disagreement is the finding.

=============================================================================
RED THIS PAGE MAY NEVER TAKE DOWN A BUILD, AND IT DID (2026-08-05)
=============================================================================

`build()` called `theme._canonical_row()` after that function MOVED to
vectors.py in PR #71. AttributeError inside `on_page_markdown`, which mkdocs
does not catch -- so every build of any site carrying a `!!! tokens` page died.

The missed call is the shallow cause. The real one: `mkdocs.yml` sets
`strict: false` and this engine's standing rule is WARN-NEVER-DIE, because v1
built with `--strict` and one typo froze the live site twice in forty minutes.
Every other hook here obeys that. A DIAGNOSTIC page was the single surface that
could take down the site it diagnoses, which is exactly backwards.

So `build()` is wrapped. Any exception is caught, reported into the build log by
type and message, and rendered as a visible failure block where the audit would
have been. ⚑ **A report must never be able to break its own subject** -- and the
test of that is not care, it is a try block.

WARNING: RESOLUTION IS NOT THIS FILE'S JOB. Ask `vectors.resolve(scheme)`. It
knows about the join table, the map form of `theme:`, and identity-derived mode
siblings; re-deriving any of that here is how the two disagree. The original bug
was this file holding its own copy of a question vectors.py already answers.

WARNING: THE CSS SCAN IS NAIVE ON PURPOSE AND ITS LIMITS ARE STATED HERE RATHER
THAN DISCOVERED LATER. It strips comments and walks brace depth one at-rule deep.
That reads our own hand-written sheets correctly and would misread minified or
heavily nested CSS. Every row it prints carries the FILE and the SELECTOR it came
from, so any claim on the page is checkable in ten seconds -- which matters more
than parser completeness. It cannot see inline styles, and it cannot see what
Material's own stylesheet does; section 5 exists because of that second limit.

=============================================================================
STAR THE SHEET LIST IS DERIVED NOW, NOT HELD HERE (fixed 2026-08-05)
=============================================================================

This file used to carry `_SHEETS`, a hardcoded tuple of stylesheet names, and
the warning that replaced this section recorded its own failure: it went stale
WITHIN TWO HOURS when `nav.css` was split out of `base.css`, so the audit
under-reported silently -- the worst possible shape for a page whose entire job
is to be trusted. The remedy it proposed was to cross-check the tuple against
`assets.py` whenever either changed, which is a manifest with a reminder
attached.

It now calls `assets.hand_written_css()`. One list, in the file that has to be
right or nothing ships at all. `type.css` would have been invisible to this page
on the very build that introduced it.

WARNING: SECTION 5's LIST IS DECLARED, ITS ANSWERS ARE DERIVED. A human says
which surfaces are worth watching (theme/ungoverned.tsv); the build says whether
our CSS mentions them. That promise came due on 2026-08-05: blocks.css started
governing all twelve admonition families and those rows flipped from NOT OURS to
a rule count with no edit to the table.

RED AND THAT ONLY WORKS BECAUSE GENERATED SHEETS NOW CONTRIBUTE THEIR SELECTORS.
The scan used ONE flag to answer TWO questions -- skip the literal scan, and skip
the selector list -- which read as tidy while both answers happened to be the
same. A generated sheet's literals ARE the design system and must be skipped; its
SELECTORS are ours and must not be. The first sheet where those differed is
blocks.css, and before this was split section 5 would have gone on calling
admonitions ungoverned forever, on the one page nobody would think to doubt.

The WHY behind the design lives in the doc-render-engine Decision Log, per this
engine's standing split: the file states the contract, the log carries the
argument.
"""

from __future__ import annotations

import html
import re
import traceback
from pathlib import Path

from . import assets, blocks, markers, state, theme, vectors
from .util import load_tsv

_BLOCK = re.compile(r"(?m)^!!![ \t]+tokens[ \t]*(?:\"[^\"]*\")?[ \t]*$")

#: The scheme the audit reports against. Colour differs per scheme; the other
#: three vectors do not, so one scheme is the whole picture for them. Matches
#: theme.py's `_PRIMARY`.
_SCHEME = "dark"

#: (label, canonical file, local file, resolve key). The canonical design system
#: defines FOUR vectors; `key` is how vectors.resolve() names each one, and None
#: means colour, which is answered by the resolved row instead.
_VECTORS = (
    ("Colour", "canonical/colors.tsv", "colors.tsv", None),
    ("Typography", "canonical/typography.tsv", "typography.tsv", "typography"),
    ("Forms", "canonical/forms.tsv", None, "forms"),
    ("Spacing", "canonical/spacing.tsv", None, "spacing"),
)

#: Properties where a literal length is a DESIGN decision rather than plumbing.
#: `border-width: 1px` is mechanical; `padding: 0.9rem` is spacing, and spacing
#: is a canonical vector. Keeping this list short is what stops section 4 from
#: becoming a dump nobody reads.
_METRIC_PROPS = (
    "padding", "margin", "gap", "font-size", "line-height",
    "border-radius", "letter-spacing", "max-width",
)

_COLOUR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?|oklch|oklab)\(")
_LENGTH = re.compile(r"(?<![\w.-])\d*\.?\d+(?:rem|em|px|ch)\b")
_VAR = re.compile(r"var\(\s*--dr-([a-z0-9-]+)")
_DECL = re.compile(r"^--dr-([a-z0-9-]+)$")


# ---------------------------------------------------------------------------
# reading CSS
# ---------------------------------------------------------------------------


def _decls(body: str) -> list[tuple[str, str]]:
    out = []
    for chunk in body.split(";"):
        prop, sep, value = chunk.partition(":")
        if sep and prop.strip() and value.strip():
            out.append((prop.strip(), value.strip()))
    return out


def _rules(css: str) -> list[tuple[str, list[tuple[str, str]]]]:
    """(selector, declarations) for every rule. One at-rule level deep."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out: list[tuple[str, list[tuple[str, str]]]] = []

    def walk(text: str, prefix: str = "") -> None:
        depth = 0
        start = 0
        body_at = 0
        sel = ""
        for i, ch in enumerate(text):
            if ch == "{":
                depth += 1
                if depth == 1:
                    sel = " ".join(text[start:i].split())
                    body_at = i + 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    body = text[body_at:i]
                    if sel.startswith("@") and "{" in body:
                        walk(body, prefix + sel + " ")
                    else:
                        out.append((prefix + sel, _decls(body)))
                    start = i + 1

    walk(css)
    return out


def _sheets() -> list[tuple[str, str, bool]]:
    """(label, css, generated) for every stylesheet this build ships.

    The name list comes from assets.hand_written_css() rather than from a tuple
    here. See the docstring: the tuple that used to live in this file went stale
    within two hours of being written.

    `generated` is False for everything returned here -- these are files a human
    wrote, so their literals count against them.
    """
    root = Path(state.ENGINE_ROOT)
    out: list[tuple[str, str, bool]] = []
    for name in assets.hand_written_css():
        path = root / "assets" / name
        if path.is_file():
            out.append((name, path.read_text(encoding="utf-8"), False))
    site = Path(state.INSTANCE.get("dir", ".")) / "theme.css"
    if site.is_file():
        out.append(("instance theme.css", site.read_text(encoding="utf-8"), False))
    return out


# ---------------------------------------------------------------------------
# reading the theme
# ---------------------------------------------------------------------------


def _values(tokens_css: str) -> dict[str, dict[str, str]]:
    """token -> {'dark': value, 'light': value} straight out of the sheet.

    Read back from the GENERATED text rather than recomputed from the tables,
    so the page reports what was actually emitted. A bug between the table and
    the sheet is the kind of thing this page should be able to show.
    """
    found: dict[str, dict[str, str]] = {}
    for selector, decls in _rules(tokens_css):
        if "slate" in selector:
            scheme = "dark"
        elif "default" in selector:
            scheme = "light"
        else:
            scheme = "any"
        for prop, value in decls:
            match = _DECL.match(prop)
            if match:
                found.setdefault(match.group(1), {})[scheme] = value
    return found


def _origin(token: str, value: str, row: dict | None, local: set[str]) -> str:
    if value.startswith("var("):
        return "alias"
    if row and token in row and not token.startswith("alt-"):
        return "canonical"
    if token in local:
        return "local"
    return "?"


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------


E = html.escape

_STYLE = """<style>
.dr-audit{font-size:.82rem}
.dr-audit h3{margin:2rem 0 .4rem;font-size:.9rem;letter-spacing:.06em;
 text-transform:uppercase;color:var(--dr-accent)}
.dr-audit table{width:100%;border-collapse:collapse;margin:.5rem 0 1.2rem}
.dr-audit td,.dr-audit th{padding:.3rem .5rem;text-align:left;vertical-align:top;
 border-bottom:1px solid var(--dr-rule);font-size:.78rem}
.dr-audit th{color:var(--dr-ink-muted);font-weight:500;text-transform:uppercase;
 letter-spacing:.04em;font-size:.68rem}
.dr-audit code,.dr-audit .m{font-family:var(--dr-font-mono);font-size:.74rem}
.dr-audit .sw{display:inline-block;width:2.2rem;height:1.1rem;border-radius:3px;
 border:1px solid var(--dr-rule);vertical-align:-.2rem}
.dr-audit .yes{color:var(--dr-ok)}
.dr-audit .no{color:var(--dr-danger);font-weight:600}
.dr-audit .warnx{color:var(--dr-warn)}
.dr-audit .n{color:var(--dr-ink-muted)}
.dr-audit-fail{border:2px solid var(--dr-danger);padding:1rem;margin:1rem 0}
.dr-audit-fail h3{color:var(--dr-danger);margin:0 0 .5rem}
</style>"""


def _table(head: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return "<p class='n'>Nothing found.</p>"
    out = ["<table><tr>"]
    out += ["<th>" + h + "</th>" for h in head]
    out.append("</tr>")
    for row in rows:
        out.append("<tr>" + "".join("<td>" + c + "</td>" for c in row) + "</tr>")
    out.append("</table>")
    return "".join(out)


def _vector_section(got: dict) -> str:
    """Which canonical vectors this site consumes. DERIVED from the resolved
    theme, not inferred from a file being present on disk.

    The distinction matters and it is the whole point of section 1: a vendored
    file that nothing points at is not a consumed vector, and before the join
    table was read this engine had three of those.
    """
    theme_dir = Path(state.ENGINE_ROOT) / "theme"
    rows = []
    for label, canon_rel, local_rel, key in _VECTORS:
        vendored = (theme_dir / canon_rel).is_file()
        entity = got["colorRow"] if key is None else (got.get(key) or "")

        if vendored and entity:
            verdict = "<span class='yes'>CANONICAL</span>"
            source = "<code>" + E(canon_rel) + "</code>"
            note = (
                "vendored and consumed"
                + ("" if key is None else " &middot; entity <code>"
                   + E(str(entity)) + "</code>")
            )
        elif vendored:
            verdict = "<span class='warnx'>NOT POINTED AT</span>"
            source = "<code>" + E(canon_rel) + "</code>"
            note = (
                "the file is vendored but this site's theme names no entity "
                "for it -- a bare colour entity has no join, so it supplies "
                "colour only. Name a THEME rather than a palette."
            )
        elif local_rel and (theme_dir / local_rel).is_file():
            verdict = "<span class='warnx'>LOCAL ONLY</span>"
            source = "<code>" + E(local_rel) + "</code>"
            note = (
                "consumed from this engine's own table. The canonical vector "
                "was never vendored, so editing it upstream changes nothing."
            )
        else:
            verdict = "<span class='no'>ABSENT</span>"
            source = "<span class='n'>-</span>"
            note = (
                "neither vendored nor consumed. The canonical vector exists "
                "upstream; this engine has no equivalent and never reads one."
            )
        rows.append(["<strong>" + label + "</strong>", verdict, source, note])
    return _table(["Vector", "Status", "Read from", "What that means"], rows)


def _token_section(values, consumers, row, local) -> str:
    rows = []
    for token in sorted(values):
        vals = values[token]
        dark = vals.get("dark") or vals.get("any", "")
        light = vals.get("light") or vals.get("any", "")
        colourish = bool(_COLOUR.search(dark)) or dark.startswith("var(")
        swatch = (
            "<span class='sw' style='background:var(--dr-" + token + ")'></span>"
            if colourish else "<span class='n'>-</span>"
        )
        rows.append([
            swatch,
            "<code>--dr-" + E(token) + "</code>",
            "<span class='m'>" + E(dark) + "</span>",
            "<span class='m'>" + E(light) + "</span>",
            _origin(token, dark, row, local),
            str(len(consumers.get(token, []))),
        ])
    return _table(["", "Token", "Dark", "Light", "Source", "Used"], rows)


def _consumer_section(consumers) -> str:
    rows = []
    for token in sorted(consumers):
        for sheet, selector, prop in consumers[token]:
            rows.append([
                "<code>--dr-" + E(token) + "</code>",
                "<span class='m'>" + E(sheet) + "</span>",
                "<span class='m'>" + E(selector[:90]) + "</span>",
                "<span class='m'>" + E(prop) + "</span>",
            ])
    return _table(["Token", "Sheet", "Selector", "Property"], rows)


def _literal_section(literals) -> str:
    rows = [
        [
            "<span class='m'>" + E(sheet) + "</span>",
            "<span class='m'>" + E(selector[:80]) + "</span>",
            "<span class='m'>" + E(prop) + "</span>",
            "<span class='m'>" + E(value[:60]) + "</span>",
            kind,
        ]
        for sheet, selector, prop, value, kind in literals
    ]
    return _table(["Sheet", "Selector", "Property", "Value", "Kind"], rows)


def _ungoverned_section(all_css: str) -> str:
    """Declared watch list, derived verdicts."""
    watch = load_tsv(Path(state.ENGINE_ROOT) / "theme" / "ungoverned.tsv")
    if not watch:
        return "<p class='n'>theme/ungoverned.tsv is missing.</p>"
    rows = []
    for entry in watch:
        probe = (entry.get("probe") or "").strip()
        hits = all_css.count(probe) if probe else 0
        verdict = (
            "<span class='yes'>" + str(hits) + " rule(s)</span>" if hits
            else "<span class='no'>NOT OURS</span>"
        )
        rows.append([
            "<strong>" + E(entry.get("surface", "?")) + "</strong>",
            "<code>" + E(probe) + "</code>",
            verdict,
            E(entry.get("note", "")),
        ])
    return _table(["Surface", "Probe", "Our CSS says", "Note"], rows)


def _marker_section() -> str:
    """Live specimens. Rendered by markers.py, not by this file.

    `markdown="1"` is what makes that work -- the same fix J17/J18 found for
    data cells. Marker syntax ELSEWHERE on this page is written with brace
    entities so the marker hook cannot eat the documentation of itself.
    """
    theme_dir = Path(state.ENGINE_ROOT) / "theme"
    classes = {
        (r.get("class") or ""): r
        for r in load_tsv(theme_dir / "marker-classes.tsv")
    }
    out = [
        "<div class='dr-audit-marks' markdown=\"1\">", "",
        "| Type | Class | Colour cell | Live |", "|---|---|---|---|",
    ]
    for row in load_tsv(theme_dir / "markers.tsv"):
        name = (row.get("marker") or "").strip()
        if not name:
            continue
        cls = (row.get("class") or "").strip()
        colour = (row.get("color") or "").strip()
        source = (
            "row override `" + colour + "`" if colour
            else "class default `"
            + ((classes.get(cls, {}).get("color") or "?").strip() + "`")
        )
        out.append(
            "| `." + name + "` | " + (cls or "-") + " | " + source
            + " | [specimen]{." + name + "} |"
        )
    out += ["", "</div>"]
    return "\n".join(out)


# ---------------------------------------------------------------------------


def _build() -> str:
    tokens_css = theme.build_css()
    values = _values(tokens_css)

    # RESOLUTION IS NOT THIS FILE'S JOB. vectors.resolve() knows about the join
    # table, the map form of `theme:` and identity-derived siblings. Holding a
    # second copy of that question here is what broke the build.
    got = vectors.resolve(_SCHEME)
    row = got["colorRow"]

    local = {
        (r.get("token") or "").strip()
        for r in load_tsv(Path(state.ENGINE_ROOT) / "theme" / "colors.tsv")
    }

    # Said once, from a caller that runs once. blocks.build_css() cannot report
    # because assets._plan calls it from both on_config and on_files.
    blocks.report()

    consumers: dict[str, list[tuple[str, str, str]]] = {}
    literals: list[tuple[str, str, str, str, str]] = []
    selectors: list[str] = []

    scanned = _sheets() + [
        ("tokens.css", tokens_css, True),
        ("marks.css", markers.build_css(), True),
        ("blocks.css", blocks.build_css(), True),
    ]

    for sheet, css, generated in scanned:
        for selector, decls in _rules(css):
            # RED EVERY SELECTOR COUNTS, GENERATED OR NOT, and splitting this
            # from the literal skip below is what lets section 5 tell the truth.
            # A generated sheet's LITERALS are the design system and must not be
            # reported as ungoverned; its SELECTORS are ours. One flag used to
            # answer both questions, which read as tidy right up until
            # blocks.css started governing admonitions -- and then section 5
            # would have gone on calling them ungoverned forever.
            selectors.append(selector)
            for prop, value in decls:
                used = _VAR.findall(value)
                for token in used:
                    consumers.setdefault(token, []).append((sheet, selector, prop))
                if generated or used or prop.startswith("--dr-"):
                    continue
                if _COLOUR.search(value):
                    literals.append((sheet, selector, prop, value, "colour"))
                elif prop.startswith(_METRIC_PROPS) and _LENGTH.search(value):
                    literals.append((sheet, selector, prop, value, "metric"))

    ungoverned_colours = sum(1 for x in literals if x[4] == "colour")
    state.note(
        "notes",
        "token audit: " + str(len(values)) + " tokens declared, "
        + str(len(consumers)) + " of them consumed by "
        + str(sum(len(v) for v in consumers.values())) + " rules, "
        + str(len(literals)) + " hardcoded values in our own stylesheets ("
        + str(ungoverned_colours) + " of them colours).",
    )

    return "\n".join([
        _STYLE,
        "<div class='dr-audit'>",
        "<h3>1 &middot; The four canonical vectors</h3>",
        "<p class='n'>Derived from the theme this site actually resolved, not "
        "from which files exist. A vendored vector nothing points at is not a "
        "consumed one.</p>",
        _vector_section(got),
        "<h3>2 &middot; Every token that reaches the browser</h3>",
        "<p class='n'>Swatches are painted with <code>var(--dr-token)</code>, "
        "never with the printed hex. A blank swatch beside a correct value "
        "means the variable is not reaching the page.</p>",
        _token_section(values, consumers, row, local),
        "<h3>3 &middot; Which part of the site each token controls</h3>",
        _consumer_section(consumers),
        "<h3>4 &middot; Hardcoded in our own stylesheets</h3>",
        "<p class='n'>Not governed by any vector. Everything left here is a "
        "value no canonical primitive covers, or one deliberately kept local "
        "-- see the notes in each stylesheet.</p>",
        _literal_section(literals),
        "<h3>5 &middot; Surfaces our CSS never mentions</h3>",
        "<p class='n'>The list is declared in <code>theme/ungoverned.tsv</code>; "
        "each verdict is derived by searching the stylesheets above. "
        "<strong>NOT OURS</strong> means Material paints it and no theme token "
        "can change it.</p>",
        _ungoverned_section("\n".join(selectors)),
        "</div>",
        "",
        "<div class='dr-audit'><h3>6 &middot; Markers, live</h3></div>",
        _marker_section(),
    ])


def build() -> str:
    """The audit, or a visible account of why there isn't one.

    RED THIS WRAPPER IS THE POINT. On 2026-08-05 a stale call into theme.py
    raised inside `on_page_markdown` and killed every build of every site
    carrying this block. mkdocs does not catch a hook exception, and this engine
    runs `strict: false` precisely so that one bad page cannot freeze a live
    site -- a rule every other hook here already obeys.

    A diagnostic surface must never be the thing that breaks its subject. So the
    audit is allowed to fail; the site is not.
    """
    try:
        return _build()
    except Exception as exc:  # noqa: BLE001 -- deliberate, see the docstring
        detail = type(exc).__name__ + ": " + str(exc)
        state.note(
            "notes",
            "token audit FAILED to build and was replaced with a failure block "
            "on the page. The site is fine; the audit is not. " + detail,
        )
        return (
            _STYLE
            + "<div class='dr-audit dr-audit-fail'>"
            + "<h3>The token audit could not be built</h3>"
            + "<p>The rest of this site is unaffected: this page is a report, "
            + "and a report is not allowed to break its own subject.</p>"
            + "<p><code>" + E(detail) + "</code></p>"
            + "<pre><code>" + E(traceback.format_exc()) + "</code></pre>"
            + "</div>"
        )


def on_page_markdown(markdown, page=None, config=None, files=None):
    if not _BLOCK.search(markdown):
        return markdown
    return _BLOCK.sub(lambda _m: build(), markdown)
