"""Stage 03c -- the LINK form of an inline marker.

    [ETC](@term:etc)                                 a defined term
    [fkCalendar](@rel:table-events)                  a relationship
    [dateFormat](@calc:table-workdays#calc-fmt)      a calculation, at a heading
    [fkCal](@alias:table-workdays#calc-fkCalendar)   a retired name for a live one

The SPAN form -- `[text]{.rel}` -- and both TSV tables live in
docrender/markers.py. This module resolves; it owns no data and paints nothing.


TWO FORMS, AND THE UNDERLINE IS THE ONLY DIFFERENCE A READER SEES
=================================================================

Same class, same colour, same weight; only the link is underlined. A reader
learns that in one page without being told, because underline already means
"this goes somewhere" everywhere else.

⭐ AND THE TWO FORMS RECORD DIFFERENT THINGS, WHICH IS THE ACTUAL POINT. A span
is a MENTION: `schema . calc . <page> . dateFormat_Colloquial`. A link is an
EDGE: links.py writes `source -> target` into `state.REFS` for every reference
it resolves, and docindex.py inverts that into /doc-refs.json. So marking a
relationship with the link form does not merely count it, it puts it in a
graph -- and nothing new is computed to get there, because the resolution was
already happening to build the href.

That is the whole reason a FileMaker solution is worth documenting this way.
FileMaker has no screen that lists every calculation in a file; this does, and
the link form makes it a dependency list rather than an inventory.

🔴 A DEAD REFERENCE NEVER DEGRADES INTO A SPAN. The resolver returns None,
links.py reports it and renders the broken-reference span -- red, struck, no
href, impossible to click. Falling back to the underlineless form would be a
silent second legal path for a reference that did not resolve, and would make
"which of these still have no page" unanswerable.

⚠️ A PREFIX RESOLVES AGAINST ANY PAGE ID, deliberately loosely. There is no
`calc` page TYPE and no `table` page type, so there is nothing to check against,
and inventing one here would decide a schema question inside a rendering hook.
Consequence, stated rather than hidden: `@rel:safety-policy` will happily point
at a safety page. The place to tighten that is objects/, not here.


🔴 WHY THIS IS A SEPARATE MODULE, GIVEN THAT markers.py ARGUED IT SHOULD NOT BE
==============================================================================

markers.py used to claim `@term:` itself and said why: "not for tidiness, but so
the two forms cannot disagree about which family they are. `_TERM_CLASS` is read
by the span renderer AND the link resolver. A second module would be a second
place to name the family."

⚑ THAT WAS TRUE OF A PYTHON CONSTANT AND IS NOT TRUE OF A TSV CELL. The family
is in the `class` column and the namespace is in the `prefix` column, of the SAME
ROW. Both forms read that row. This file contains no marker name, no family name
and no prefix -- search it and you will not find the string "rel" or "terminology"
anywhere outside this docstring. There is nothing left for two modules to
disagree about.

🚨 AND THE SEAM IS DATA, NEVER BEHAVIOUR. This module imports `table()`,
`marker_rows()` and `LINK_CLASS`. It does NOT import `markers._colour`, and must
not. That helper encodes markers.py's policy -- an unresolvable token falls back
to the body colour -- and on 2026-08-05 sharing a resolver that encoded one
module's policy took every site in the family down at config-load time. Two
modules can ask an identical question and need different answers.


THE CLAIM HAPPENS AT IMPORT, AND THAT COSTS SOMETHING
=====================================================

`prefixes.claim()` has to run before any page renders, so `_install()` runs at
import and reads the `prefix` column straight off disk. `state.ENGINE_ROOT` is a
module-level constant derived from `__file__`, so that read is safe this early --
verified, not assumed.

⚠️ THE COST: a prefix ADDED during a live `mkdocs serve` session is not claimed
until the process restarts, and every link using it renders broken until then.
`on_files` detects exactly that and says so. Everything else about a marker --
colour, label, shape, tooltip -- is re-read per build and stays hot.

🔴 AND A PROBLEM FOUND AT IMPORT CANNOT BE REPORTED AT IMPORT. `state.reset()`
runs from the first hook, which is AFTER every module has been imported, so a
`state.note()` call made during `_install()` is wiped before anything prints.
Findings are therefore parked in `_CLAIM_NOTES` and drained in `on_files`. This
is the shape of a check that runs, finds something, and tells nobody -- which
this repo has shipped more than once -- and the two-step is what avoids it.


THREE WAYS A `prefix` CELL CAN BE WRONG, AND NONE OF THEM FAIL A BUILD
======================================================================

  ILLEGAL    not a legal token. links.py's own pattern would not match it, so
             the namespace could never be reached even if it were claimed.
  DUPLICATE  two rows asking for one prefix. `prefixes.claim` is idempotent per
             OWNER, so both rows have the same owner here and the second would
             silently overwrite the first -- one namespace quietly meaning the
             wrong marker. Caught before the call rather than by it.
  TAKEN      a prefix another module already owns (`data`, `img`). `claim` DOES
             raise on that, correctly, and a raise at import time is a dead
             site. So it is checked first and the raise is caught anyway.

⚑ THE RULE BEHIND ALL THREE: this is the first claimant built from DATA rather
than hand-written, so a mistake here is a typo in a TSV rather than a bug in a
module -- and a typo must never be able to take a site down. Every path declines,
reports, and leaves the rest of the table working.
"""

from __future__ import annotations

import re

from . import markers, prefixes, state
from .util import relative_url

#: Must agree with what links.py's `_LINK` pattern can actually capture before the
#: colon. Narrower on purpose: lowercase only, so `@Calc:` is refused here rather
#: than claimed and then never matched.
_PREFIX = re.compile(r"^[a-z][a-z0-9-]*$")

#: prefix -> the marker name that owns it. Built at import.
_CLAIMED: dict[str, str] = {}

#: Prefixes deliberately NOT claimed, with a reason already queued. Kept apart from
#: `_CLAIMED` so the staleness check below can tell "we refused this" from "nobody
#: has seen this yet" -- reporting a declined prefix twice, once as a fault and
#: again as a mystery, is how a report teaches people to stop reading it.
_DECLINED: set[str] = set()

#: Findings from `_install()`, drained in on_files. See the red note above: a
#: state.note() made at import is erased by state.reset() before anything prints.
_CLAIM_NOTES: list[str] = []


def _make(name: str):
    """Build the resolver for one marker row.

    A closure over the marker NAME only -- never over its class, colour or shape.
    Those are read from the resolved table at call time, so editing a colour during
    `mkdocs serve` repaints the link form without a restart, exactly as it does the
    span form. Closing over the row would have frozen it at import.
    """

    def resolve(rest, page, label, anchor=""):
        hit = state.PAGES.get(rest)
        if not hit:
            # Declining is what produces the broken-reference span in links.py.
            # state.PAGES holds only pages that were actually BUILT, so a target
            # that exists but is hidden declines here too -- correctly: a link to a
            # page nobody can open is a broken link, not a working one.
            return None

        # Resolved against THIS page, never from a separator count -- see
        # util.relative_url for the live 404 that arithmetic caused.
        target = relative_url(str(hit.get("url", "")), page.file.url)

        row = markers.table().get(name) or {}
        klass = (row.get("class") or "").strip()
        shape = (row.get("shape") or "").strip()

        css = [markers.LINK_CLASS]
        if klass:
            css.append("dr-mark--cls-" + klass)
        if shape == "box":
            # A boxed family's link gets the chip: border, radius, padding and the
            # class wash, all from base.css's `.dr-mark--box`, WITHOUT `.dr-mark`
            # and therefore without its `cursor: help` and `white-space: nowrap`.
            # No new CSS -- the two classes were always separate rules.
            css.append("dr-mark--box")

        # Same shape as the span entry so ONE sorted list answers "every calc on
        # this site" across both forms. The ` -> target` tail is what makes this
        # half readable as a graph.
        state.note(
            "markers",
            (klass or "unclassed") + " \u00b7 " + name + " \u00b7 "
            + page.file.src_uri + " \u00b7 " + label + " \u2192 " + rest + anchor,
        )

        # ⚠️ AT LEAST TWO CLASSES IN PRACTICE, WHICH MATTERS DOWNSTREAM. Hook 03b
        # runs after this and its `_MARK` pattern matches a single-class attr_list
        # block. A one-class block would be looked up as a marker name, miss, and
        # be handed back untouched -- safe, but only by luck. Every row in a real
        # table has a class, so this always emits two or more.
        return (
            "[" + label + "](" + target + anchor + "){ ." + " .".join(css) + " }"
        )

    return resolve


def _decline(prefix: str, message: str) -> None:
    _CLAIM_NOTES.append(message)
    _DECLINED.add(prefix)


def _install() -> None:
    """Claim one namespace per `prefix` cell. Runs at IMPORT."""
    for row in markers.marker_rows():
        name = (row.get("marker") or "").strip()
        prefix = (row.get("prefix") or "").strip()
        if not name or not prefix:
            # A blank prefix is the NORMAL case and is never reported: most markers
            # are span-only because most of them have nothing to point at.
            continue

        if not _PREFIX.match(prefix):
            _decline(prefix,
                "marker '" + name + "' asks for prefix '" + prefix + "', which is "
                + "not a legal token (lowercase letters, digits and hyphens, "
                + "starting with a letter). Nothing claimed it, so every link "
                + "using it renders as a broken reference.")
            continue

        if prefix in _CLAIMED:
            _decline(prefix,
                "markers '" + _CLAIMED[prefix] + "' and '" + name + "' both ask for "
                + "prefix '" + prefix + "'. One namespace cannot mean two things, so "
                + "'" + _CLAIMED[prefix] + "' keeps it and '" + name + "' has no link "
                + "form. Rename one.")
            continue

        if prefix in prefixes.reserved():
            _decline(prefix,
                "marker '" + name + "' asks for prefix '" + prefix + "', which is "
                + "already owned by " + prefixes.owner(prefix) + ". The existing "
                + "owner keeps it and this marker has no link form.")
            continue

        try:
            prefixes.claim(prefix, __name__, _make(name), anchors=True)
        except RuntimeError as exc:
            # Belt to the check above's braces. That check depends on the other
            # claimants having been imported first, which is true today (01b_data
            # and 01f_images are registered ahead of 03c) and is somebody else's
            # ordering to change. A raise at import time is a dead site.
            _decline(prefix, str(exc))
            continue
        _CLAIMED[prefix] = name


# Claimed at IMPORT, which is the contract prefixes.py documents: claims happen
# when hook modules are imported, lookups happen later inside events.
#
# 🚨 AND THIS LINE IS THE WHOLE FEATURE. If hooks/03c_markerlinks.py is ever
# removed from the `hooks:` list in mkdocs.yml, this module is never imported,
# nothing claims anything, and every link-form marker on every site silently
# renders as a broken reference -- no error, no clue. Same shape as
# hooks/04_theme.py, which sits in the folder unregistered and does nothing.
_install()


def on_files(files, config):
    for message in _CLAIM_NOTES:
        state.note("notes", message)

    live = {
        (r.get("prefix") or "").strip()
        for r in markers.marker_rows()
        if (r.get("prefix") or "").strip()
    }
    missed = sorted(
        p for p in live if p not in _CLAIMED and p not in _DECLINED
    )
    if missed:
        state.note(
            "notes",
            "theme/markers.tsv declares prefix(es) "
            + ", ".join("@" + p + ":" for p in missed)
            + " that nothing claimed. Prefixes are claimed once at IMPORT, so a "
            + "prefix added during a live `mkdocs serve` session needs a restart "
            + "before its link form works. Every link using it renders broken "
            + "until then.",
        )
    return files
