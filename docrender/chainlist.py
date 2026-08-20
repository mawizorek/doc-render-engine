"""Stage 05b -- `!!! chain`, the reading order as a CONTENTS LIST in the body.

WHY decisions here are the way they are: the doc-render-engine Decision Log.
The `chain:` vocabulary and prev/next belong to docrender/nav.py; the flow strip
is docrender/program.py; the embedded form is docrender/forms.py. This module
owns one thing: drawing a chain as a list where an author asks for one.

    !!! chain                              this page's own chain
    !!! chain "program-general-safety"     another program's chain, by id

Michael: *"i want `!!! chain "index"` to be able to render ...an index... of the
pages in that chain. a SIMPLE index."*

=============================================================================
⚠️ THE ARGUMENT IS AN ID, NOT A MODE WORD -- AND `"index"` WAS THE WRONG SPELLING
=============================================================================
The ask arrived as `!!! chain "index"`, and taking that literally would have made
the quoted word mean STYLE here while it means WHICH THING in `!!! form "slot"`
and `!!! data "slot"` -- two grammars for one syntax, decided per directive, with
nothing to tell an author which is which.

So the argument names the OWNER of a chain, matching its siblings, and it is
OPTIONAL because the common case is a program drawing its own. `!!! chain` bare
is the normal form.

🚫 AND `"index"` IS NOT SILENTLY IGNORED. It resolves as an id, finds nothing, and
is reported by name -- because a quoted word that parses and does nothing is the
defect this engine keeps paying for (`sort:` in eleven files, the inert
`palette:`, the `?flow=` param deleted three hours ago). An author who types the
word from the original ask gets a report line, not silence.

=============================================================================
⭐ IT IS A THIRD MODULE ON ONE STAGE, AND THE SEAM IS THE EVENT
=============================================================================
05b now wires three modules. That is a lot for one stage number, and the reason
is not tidiness:

    forms.py       on_page_markdown    an EMBED, from a `forms:` slot
    chainlist.py   on_page_markdown    a LIST, from a `chain:` declaration
    program.py     on_page_content     the STRIP, appended to rendered HTML

⚠️ THIS COULD HAVE LIVED IN program.py AND DELIBERATELY DOES NOT. That file is
18,350 B against the engine's ~22KB hard read limit, and this would have taken it
to ~21KB -- a file nobody can safely edit is how `util.py` got clobbered and how
`assets.py` became untouchable tonight. ⚑ But size is the TRIGGER, not the
reason: `specs/visibility-split.md` §1 rules that a cut follows the CONCERNS, and
the concern here is a different MkDocs event on a different surface. A body
directive that rewrites markdown is not the same job as appending navigation to
finished HTML.

=============================================================================
WHAT "SIMPLE" MEANT, AND WHAT WAS REFUSED TO KEEP IT THAT WAY
=============================================================================
An ordered list of links, in chain order, with the current page marked and not
linked. That is the whole feature.

🚫 NO SUMMARIES, NO STEP COUNTS, NO PROGRESS. Every one was available and every
one is a second claimant: `summary` is the lede lede.py already draws, the count
is what the flow strip already says, and "progress" is state a static site does
not have. Michael said SIMPLE in capitals; this file takes that as a spec.

⚠️ THE CURRENT PAGE IS MARKED BY BEING UNLINKED, not by a badge. A link to the
page you are on is the one link in any index that cannot do anything, and
removing it is both the marker and the fix.

🔴 IT RENDERS AS MARKDOWN, NOT HTML, WHICH IS THE ONE THING THAT MAKES IT CHEAP.
An ordered list of `[title](url)` lines hands the styling to Material's own
typeset rules, so this feature ships NO CSS -- and `assets.py` is over the read
ceiling tonight, so a feature needing a stylesheet could not have shipped at all.
⚠️ Consequence, stated rather than discovered: the list inherits the page's list
spacing, so it looks like any other numbered list on the site. That is the
intent, and it is also the reason nobody can restyle it without a new sheet.

⚠️ AND IT MUST EMIT REAL URLs, NOT `@id` TOKENS. Hook 03 (links.py) resolved
every reference on this page LONG before stage 05b runs, so an `@id` written here
would ship to the reader as literal text. `relative_url` is used for the same
reason links.py uses it -- separator counting was wrong on exactly one page per
site, the landing page, and that is documented in util.py.
"""

from __future__ import annotations

import re

from . import nav, state
from .util import relative_url, sub_outside_code

#: `!!! chain` alone on a line, with an OPTIONAL quoted owner id.
#:
#: ⚠️ THE ARGUMENT IS OPTIONAL AND THE PATTERN SAYS SO, which is the difference
#: from `!!! form "slot"` -- that one has nothing to fall back to, this one has
#: the page's own chain. Same `!!!` shape either way, so the body vocabulary
#: stays one thing an author learns once.
_CHAIN = re.compile(r'(?m)^[ \t]*!!![ \t]+chain(?:[ \t]+"([^"\n]*)")?[ \t]*$')


def _meta(src) -> dict:
    return state.BY_SRC.get(src, {}) or {}


def _owner_of(want_id: str, chains: dict) -> str:
    """The src_uri of the page whose `id:` is `want_id` AND which owns a chain."""
    for src in chains:
        if str(_meta(src).get("id") or "").strip() == want_id:
            return src
    return ""


def _list(owner_src, ids, page, by_id) -> str:
    """The chain as an ordered markdown list.

    ⚠️ AN UNRESOLVABLE ID IS SKIPPED HERE AND NOT DRAWN AS A DEAD ROW. nav.py
    already reports it by name against the chain that declared it, and a second
    complaint about one typo trains people to skim the report. The numbering
    therefore counts what a reader can actually open, which is the same rule the
    flow strip's "step 4 of 8" follows.
    """
    here = getattr(page.file, "url", "")
    mine = getattr(page.file, "src_uri", "")
    rows = []

    for pid in ids:
        target = by_id.get(pid)
        if target is None:
            continue
        tsrc = getattr(target.file, "src_uri", "")
        title = str(
            _meta(tsrc).get("title") or getattr(target, "title", "") or pid
        )
        if tsrc == mine:
            # THE CURRENT PAGE, UNLINKED. See the docstring.
            rows.append("1. **" + title + "**")
        else:
            url = relative_url(getattr(target.file, "url", ""), here)
            rows.append("1. [" + title + "](" + url + ")")

    if not rows:
        state.note(
            "missing_required",
            mine + ": `!!! chain` found a chain on `" + owner_src + "` whose ids "
            "resolve to NO built pages, so nothing was drawn. The chain itself "
            "is reported against that page.",
        )
        return ""

    # `1.` on every line: Python-Markdown renumbers an ordered list from its
    # first marker, so the source stays diff-stable when a step is inserted.
    return "\n".join(rows)


def _render(src, want, page, files) -> str:
    chains = nav.declared(report=False)
    if not chains:
        state.note(
            "notes",
            src + ": `!!! chain` was written but no page on this site declares a "
            "`chain:`. Nothing was drawn.",
        )
        return ""

    if want:
        owner = _owner_of(want, chains)
        if not owner:
            state.note(
                "dead_links",
                src + ': `!!! chain "' + want + '"` names `' + want + "`, which is "
                "not the id of any page declaring a `chain:`. Nothing was drawn. "
                "The argument is an ID (a program or a folder index), not a mode "
                'word -- write `!!! chain` bare to draw this page\'s own chain.',
            )
            return ""
    elif src in chains:
        owner = src
    else:
        # A step in somebody else's flow, asking for "the" chain. There may be
        # several, so it is refused rather than guessed -- the same reason a bare
        # URL promotes no flow in program.py.
        holders = [
            str(_meta(s).get("id") or s).strip()
            for s in sorted(chains)
            if str(_meta(src).get("id") or "").strip() in chains[s]
        ]
        state.note(
            "missing_required",
            src + ": `!!! chain` needs an id here -- this page declares no "
            "`chain:` of its own"
            + (
                ", and is a step in " + str(len(holders)) + ": "
                + ", ".join(holders) + ". Name the one you want."
                if holders else " and is not in any chain."
            ),
        )
        return ""

    by_id, _by_src = nav._built(files)
    return _list(owner, chains[owner], page, by_id)


def on_page_markdown(markdown, page, config, files):
    """Replace each `!!! chain` with an ordered list of that chain's pages.

    ⚠️ `sub_outside_code` IS NOT OPTIONAL. The page documenting this directive
    contains the directive, and util.py records the first time that bit this
    engine: the page teaching `[Main Stage](@main-stage)` shipped with the
    resolved URL inside its own code fence.
    """
    if "!!!" not in markdown:
        return markdown

    src = getattr(page.file, "src_uri", "")

    def swap(match):
        drawn = _render(src, (match.group(1) or "").strip(), page, files)
        return ("\n\n" + drawn + "\n\n") if drawn else ""

    return sub_outside_code(_CHAIN, swap, markdown)
