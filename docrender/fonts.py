"""Stage 04c -- FETCH the faces the typography vector already names.

=============================================================================
⭐ THE VECTOR WAS NEVER THE PROBLEM. THE LOADER WAS MISSING.
=============================================================================
> Michael, 2026-08-19: *"wait - we don't dictate font via the theme vectors that
> we have....."*

He was right to push back, and the correction is worth stating here because this
module exists only because of it. `theme/canonical/typography.tsv` carries THREE
font columns as its first three fields -- `font-display`, `font-body`,
`font-mono` -- populated on all six rows, emitted by theme.py as `--dr-font-*`,
mapped onto Material's variables by base.css, and consumed by type.css, navtree,
router, data and the token audit.

🔴 SO THE NAME WAS ALWAYS DECLARED, APPLIED AND INHERITED CORRECTLY. WHAT WAS
MISSING IS THE FILE. Nothing in this engine ever requested a webfont, so `'Inter'`
resolved against locally installed families, usually found none, and fell through
to `system-ui` -- which is the stack's own third entry and therefore a DELIBERATE
fallback rather than an accident.

⚑ A GOVERNED TOKEN WITH NO ASSET BEHIND IT IS A NAME, NOT A FACE. Same family as
the `accent`/`on-accent` pair and the `data-1..4` sweep: emitted, consumed by a
real consumer, and still producing nothing, because the gap was further out than
anybody was looking.

=============================================================================
⚠️ WHY THIS IS A HOOK AND NOT A LINE IN `mkdocs.yml`
=============================================================================
The obvious move is `theme.font: {text: Inter, code: JetBrains Mono}` in
`mkdocs.yml`. It is wrong here for the reason that file states in its own first
line: it is *"deliberately almost empty of identity"*, and hook 08 fails the build
if identity appears in code.

🔴 AND A HARDCODED FAMILY WOULD BE WORSE THAN IDENTITY -- IT WOULD BE A SECOND
CLAIMANT ON A FACT THE VECTOR ALREADY OWNS. Six typography rows name different
families; a seventh copy in the base config would be right for whichever instance
was being looked at that day and silently wrong for the rest. This repo has
retired three manifests for exactly that shape.

✅ SO THE FAMILIES ARE READ FROM THE RESOLVED ROW AT BUILD TIME. Each instance
fetches what ITS OWN theme declared, no config key is added anywhere, and a new
typography row starts loading with no edit to this file.

=============================================================================
WHAT IT DOES, IN TWO PARTS
=============================================================================
1. `theme.font = False`. Material's DEFAULT is Roboto, and `mkdocs.yml` sets no
   `font:` key -- so every page in this family has been requesting Roboto from
   Google and then having it overridden away by base.css. ⚑ A webfont fetched on
   every page load and used by nothing. `False` is Material's documented switch
   for *"I am loading fonts myself"* and it removes that request.

2. One stylesheet URL appended to `config.extra_css`, built from the row.

⭐ A GOOGLE FONTS CSS URL *IS* A STYLESHEET, WHICH IS WHY THIS NEEDS NO TEMPLATE
WORK. `extra_css` already exists, assets.py already appends to it, and MkDocs
emits each entry as a `<link>`. No `custom_dir`, no partial fork, no `<head>`
injection -- the J29 precedent (a fork is a copy of somebody else's truth that we
then maintain forever) is not even engaged.

=============================================================================
🔴 THE THIRD-PARTY REQUEST IS A REAL COST AND IT IS MICHAEL'S TO REVERSE
=============================================================================
This adds one request to `fonts.googleapis.com` on every page load. That matters
more for these sites than most: `instances/uritp-safety/site.yml` records that
these are read *"in venues on variable connections"*, and the same argument is
what kept this unbuilt until now.

✅ IT IS STILL A NET REDUCTION TODAY, which is the honest framing: the Roboto
request already existed and is now gone, replaced by one request for fonts that
are actually used. Going from one wasted fetch to one useful fetch is not a new
dependency, it is a redirected one.

🚫 THE ALTERNATIVE, NAMED RATHER THAN QUIETLY SKIPPED: self-hosting. It removes
the third party entirely and costs font binaries committed to a repo that holds
only text today, plus an `@font-face` block per family per weight. If Michael
wants that, the change is confined to this module and the weight list below is
already the manifest of what to download.

=============================================================================
⚠️ THE FAILURE MODE, AND IT IS THE LOUD KIND FOR ONCE
=============================================================================
Google Fonts `css2` returns **400 for an unknown family**, and it fails the WHOLE
request rather than the one `family=` parameter. So a typography row naming a
family Google does not serve does not lose that face -- it loses ALL of them, on
every page of that site, and every stack falls back to `system-ui` exactly as it
does today.

✅ That is survivable BECAUSE the stacks name their own fallbacks, which is the
second time today that authoring has paid off. But it is silent in the sense that
nobody is told, so `_report()` names every family it asked for on every build.
If the faces do not change after this ships, THAT LINE IS THE FIRST THING TO READ
and the URL is the first thing to open by hand.

⚠️ NOT VERIFIED: which of the six vectors' families Google actually serves. All
seven names below are well-known Google Fonts families and I have not checked one
of them against the API this session. 🔴 A PROXY READ PRESENTED AS A VERIFICATION
IS A DOCUMENTED FAILURE IN THIS HOUSE (`instances/uritp-safety/site.yml`, the
`database` theme claim), so this is stated as an assumption with a named test:
open the emitted URL, or read the build report line.
"""

from __future__ import annotations

import urllib.parse

from . import state, vectors

#: Google Fonts CSS API v2.
_BASE = "https://fonts.googleapis.com/css2"

#: WEIGHTS ARE A MANIFEST OF WHAT THIS ENGINE ACTUALLY ASKS FOR, and every extra
#: one is bytes on a venue connection. Read off the stylesheets rather than
#: guessed:
#:
#:   300  Material's own screen ramp sets h1/h2 to 300, and type.css deliberately
#:        declines to override it (no weight column in the vector).
#:   400  body text everywhere.
#:   600  print-type.css sets h1-h3 to 600 on paper.
#:   700  print-type.css sets h4-h6 to 700; Material's admonition titles are 700.
#:
#: ⚠️ ITALIC 400 ONLY. `objects.py` renders the `revised:` line in italic and
#: prose carries `*emphasis*`, so one italic weight is genuinely used. Italic 600
#: and 700 are NOT requested because nothing in this engine sets them -- if a bold
#: italic ever appears it will synthesise, and that is the correct trade against
#: two more files.
_TEXT_WEIGHTS = (300, 400, 600, 700)
_TEXT_ITALICS = (400,)

#: Mono is body-weight only. Nothing sets a bold monospace anywhere: not the
#: router's code field, not a data cell, not the token audit, not a code block.
_MONO_WEIGHTS = (400,)


def _family(stack: str) -> str:
    """First family name out of a CSS stack.

    `'Inter', system-ui, sans-serif` -> `Inter`

    ⚠️ THE FIRST ENTRY IS THE ONE WE OWN AND THE REST ARE THE FALLBACK CHAIN.
    `system-ui` and `sans-serif` are keywords a font service has never heard of,
    so asking for them would 400 the entire request -- see the failure mode in the
    docstring.
    """
    first = (stack or "").split(",")[0].strip()
    return first.strip("'\"").strip()


def _generic(name: str) -> bool:
    """Is this a CSS keyword rather than a family somebody can fetch?

    A typography row is free to name only keywords -- a row reading
    `system-ui, sans-serif` is a legitimate choice to use no webfont at all -- and
    that must produce NO request rather than a broken one.
    """
    return name.lower() in {
        "system-ui",
        "ui-sans-serif",
        "ui-serif",
        "ui-monospace",
        "sans-serif",
        "serif",
        "monospace",
        "cursive",
        "fantasy",
        "inherit",
        "initial",
        "unset",
        "",
    }


def _axis(weights: tuple[int, ...], italics: tuple[int, ...]) -> str:
    """The `css2` axis-tuple spelling, which is picky and worth writing once.

    Upright only:      `wght@400;600`
    With italics:      `ital,wght@0,400;0,600;1,400`

    ⚠️ VALUES MUST BE SORTED ASCENDING or the API rejects the request. That is a
    documented requirement of the v2 API and the reason this is a function rather
    than a formatted string at each call site.
    """
    if not italics:
        return "wght@" + ";".join(str(w) for w in sorted(weights))
    pairs = [(0, w) for w in weights] + [(1, w) for w in italics]
    return "ital,wght@" + ";".join(
        str(i) + "," + str(w) for i, w in sorted(pairs)
    )


def _wanted() -> list[tuple[str, str]]:
    """(family, axis) for every fetchable face the resolved theme names.

    ⚠️ READS THE PRIMARY SCHEME'S ROW, matching theme.py's `_shared()`. Typography
    is scheme-INDEPENDENT by design -- one theme supplies it and theme.py already
    reports when the other scheme points somewhere else -- so there is exactly one
    row to read and no second decision to make here.
    """
    picked = vectors.resolve(vectors.PRIMARY)
    row = vectors.entity("typography.tsv", picked.get("typography") or "")
    if not row:
        # No join, or a theme canonical has never heard of. The local nine-token
        # underlay declares no font at all, so there is nothing to fetch and that
        # is a correct outcome rather than a failure.
        return []

    text_axis = _axis(_TEXT_WEIGHTS, _TEXT_ITALICS)
    mono_axis = _axis(_MONO_WEIGHTS, ())

    out: list[tuple[str, str]] = []
    seen: set[str] = set()

    # `font-body` first, then `font-display`, then `font-mono`. Order is cosmetic
    # in the URL and deliberate in the report: body is the face a reader spends
    # every line inside.
    for column, axis in (
        ("font-body", text_axis),
        ("font-display", text_axis),
        ("font-mono", mono_axis),
    ):
        name = _family(row.get(column) or "")
        if _generic(name):
            continue
        # DEDUPLICATED, because a row is free to name one family twice -- three of
        # the six do (`grounded` and `mobile-legible` and `papyrus` share body and
        # display). Asking twice is a longer URL for identical bytes.
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append((name, axis))

    return out


def _url(wanted: list[tuple[str, str]]) -> str:
    """One `css2` request for every family.

    `display=swap` is deliberate: the alternative renders invisible text until the
    font arrives, which on a slow venue connection is a page that looks broken.
    Swap shows the fallback immediately and repaints -- and the fallback is the
    stack's own `system-ui`, which is what every one of these sites has been
    rendering in all along, so the flash is to the CURRENT appearance rather than
    to something unstyled.
    """
    parts = [
        "family=" + urllib.parse.quote_plus(name) + ":" + axis
        for name, axis in wanted
    ]
    return _BASE + "?" + "&".join(parts) + "&display=swap"


def on_config(config):
    """Disable Material's own font fetch, then request ours.

    ⚠️ BOTH HALVES OR NEITHER. Setting `font = False` alone would remove the
    Roboto request and leave every site on `system-ui` forever with nothing
    reporting it; appending the URL alone would leave TWO font requests per page,
    one of them for a face nothing uses.
    """
    wanted = _wanted()

    # 🔴 Material's documented switch for "I load fonts myself". Set even when
    # `wanted` is empty: a theme that names only keywords wants NO webfont, and
    # leaving Roboto in place would silently fetch one anyway.
    config.theme["font"] = False

    if not wanted:
        state.note(
            "notes",
            "fonts: this theme's typography row names no fetchable family, so "
            "no webfont is requested and every stack renders in its declared "
            "fallback. Material's own Roboto request is disabled either way.",
        )
        return config

    url = _url(wanted)
    if url not in config.extra_css:
        # Prepended rather than appended: a font stylesheet is the one sheet whose
        # own rules nothing overrides, and putting it first keeps assets.py's
        # carefully ordered group (see `_DATA_ASSETS`) contiguous in the output.
        config.extra_css.insert(0, url)

    state.note(
        "notes",
        "fonts: requesting " + ", ".join(name for name, _axis in wanted)
        + " from Google Fonts, named by this theme's typography row. If the "
        "faces do not change, open that URL by hand -- css2 returns 400 for an "
        "unknown family and fails the WHOLE request, which falls every stack "
        "back to its declared fallback with no other symptom.",
    )
    return config
