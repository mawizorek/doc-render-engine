"""WHICH FLOW IS ACTIVE -- the two ids, and the rules that act on them.

Split out of `docrender/program.py` on 2026-08-28. ⚠️ SIZE WAS THE TRIGGER AND NOT
THE REASON, and the distinction is `specs/visibility-split.md` §1's ruling: *"The
cut that is worth making follows the concerns. It also fixes the bytes. If those
two ever disagree, follow the concerns."* They agree here.

    program.py   WHAT A FLOW LOOKS LIKE   -- strips, labels, prev/next, the cap
    this file    WHICH FLOW IS ACTIVE     -- the ids, and the promotion

They share no state. `program.py` calls three functions here and this file calls
nothing back; it does not read `state`, does not touch a Page, and has no MkDocs
event of its own. Third module to leave that file after `forms.py` and
`chainlist.py`, and the cleanest of the three seams.

⚑ AND THE TRIGGER IS WORTH RECORDING BECAUSE I IGNORED MY OWN RULE TWICE FIRST.
`program.py` went over the 22,528 B read ceiling on this change, was trimmed,
went over again, was trimmed again -- **each trim recovering less than the last.**
That is the exact spiral `print-chrome.css`, `print-space.css` and `data.css` all
carry a sentence about: *a file at its size limit is usually a file with a seam in
it, and trimming prose is what you do instead of finding the seam.* Two trims is
two more than the rule allows.


=============================================================================
🔴 WHY THERE ARE TWO IDS PER FLOW (DL J20)
=============================================================================
One is where the reader ARRIVES -- a zero-height marker at the TOP of the page.
One is what gets PROMOTED -- the strip, at the FOOT of it.

They were the same id for an hour, and that is why every Next link dropped the
reader at the bottom of the next policy. ⚑ **A fragment does TWO jobs: it carries
STATE (which flow am I in) and it is the SCROLL TARGET.** Only the first was
designed for, and the one nobody designed for is the one the reader meets first.

🔴 BOTH SPELLINGS LIVE HERE AND NOWHERE ELSE, which is the whole reason this is a
module rather than two string literals. A fragment matching no element is not an
error in any browser, in any validator, or in this engine's build report -- so a
link and its target computed in two places fails **silently and forever.** Same
argument `forms.slot_anchor` makes about the completion form's anchor.


=============================================================================
🔴 WHERE PURE CSS RUNS OUT, WHICH IS WORTH STATING PLAINLY
=============================================================================
A selector cannot compare a targeted element's id to another element's id, so no
generic rule can say *"the strip whose id matches the targeted marker."* `css()`
therefore emits THREE SHORT RULES PER FLOW, per page, naming both ids literally.

That breaks a rule `program.py` set for itself -- no inline style; every
stylesheet goes through `assets.py` so `hand_written_css()` stays the single
source for the token audit -- and it is broken DELIBERATELY:

  1. it is per-PAGE DATA, not a stylesheet. The ids are facts about this page,
     and `assets/flow.css` still owns every look decision.
  2. `assets.py` is over the ~22KB read ceiling, so registering a new asset means
     rewriting a file that cannot be read whole (the `util.py` clobber).
  3. it is ~180 bytes on a page that is in a flow, and nothing at all elsewhere.

⚠️ AND IT IS `:target`-ONLY, SO IT FIRES ONLY ON ARRIVAL FROM A FLOW LINK. A
reader reaching a policy from the SIDEBAR, a bookmark or a search result is in no
flow and gets `program.py`'s declared order instead. Deliberate -- guessing tells a
reader they are in MEWP training when they are not -- but it means the promotion is
absent from about half of all arrivals, which is why the `order:` default matters
as much as this file does.

🚫 STILL NO JAVASCRIPT. A script would flap the footer on every page load, and
nothing here needs one.
"""

from __future__ import annotations


def at_id(flow_id: str) -> str:
    """The id every flow LINK points at: a marker at the TOP of the page."""
    return "at-flow-" + str(flow_id) if flow_id else ""


def strip_id(flow_id: str) -> str:
    """The id ON THE STRIP, at the foot of the page."""
    return "flow-" + str(flow_id) if flow_id else ""


def css(flow_ids) -> str:
    """A `<style>` block tying each TOP marker to the strip it promotes.

    Three rules per flow:
      1. hoist the strip above its siblings
      2. make the disclosure transparent, so a strip parked inside it is visible
         at all
      3. hide that disclosure's SUMMARY

    ⚠️ RULE 2 IS THE EXOTIC ONE. A closed `<details>` hides its children and CSS
    cannot open one, so the rule makes it `display: contents`: its children join
    the flex layout and become visible, and rule 1's `order: -1` then hoists the
    targeted strip above the rest. ✅ Degrades honestly -- a browser that ignores it
    leaves the reader on the right page with the right chain and one click to open
    the disclosure.

    ⚠️ AND THE CAP IS FULLY SPENT WHEN THIS FIRES: `display: contents` reveals
    EVERY strip in the disclosure, not only the promoted one. Correct rather than
    tidy -- the reader asked for one of them by name and the rest are a line each --
    and it is why rule 3 is consistent rather than a patch.

    🔴 RULE 3 EXISTS BECAUSE RULES 1 AND 2 SUCCEEDED AND LOOKED LIKE THEY HAD
    FAILED (2026-08-28). Michael, expecting the arrival program to win: *"instead
    of burying the current program inside the 'also in other programs' dropdown."*
    The promotion was firing. **What stayed on screen was its label.**
    `display: contents` removes the `<details>` BOX and not its `<summary>`, so a
    successful hoist still rendered *"▸ Also part of 1 other program"* as a loose
    line -- at `order: 0`, therefore BELOW the strip it was supposedly hiding,
    naming a state that was no longer true.

    ⚑ **A FEATURE CAN BE WORKING AND STILL BE WEARING ITS OWN FAILURE MESSAGE**,
    and nobody debugging it will look at the mechanism, because the label is more
    legible than the layout. `flow.css` documented the loose summary as intended
    behaviour and never asked what the loose summary would SAY.

    ⚠️ RULE 3 IS SCOPED BY `:has()`, SAME AS RULE 2, so it fires only when THIS
    flow's strip is the one inside the disclosure. A promoted strip that was
    already the open one leaves the label alone, correctly: the disclosure still
    describes real flows the reader has not asked for.

    🔴 `~` REQUIRES THE MARKER AND `.dr-flows` TO BE SIBLINGS, which they are:
    `program.on_page_content` inserts both into the same container, the marker
    first and the strips last. If either ever moves into a wrapper these rules
    stop matching -- silently, because a selector that matches nothing is not an
    error. That is the trade for not shipping a script, and it is the one thing to
    re-check if the footer ever stops promoting.

    ⚠️ UNVERIFIED ON A RENDERED PAGE. `:has()` and `display: contents` are both
    widely supported and neither has been proven HERE, on a real build, in a real
    browser -- and this engine has nothing that looks at a rendered page.
    """
    out = []
    for flow_id in flow_ids:
        at, strip = at_id(flow_id), strip_id(flow_id)
        if not at or not strip:
            continue
        held = "#" + at + ":target ~ .dr-flows .dr-flows__others:has(#" + strip
        out.append(
            "#" + at + ":target ~ .dr-flows #" + strip
            + "{order:-1;margin-top:0;padding-top:0;border-top:0}"
            + held + "){display:contents}"
            + held + ")>summary{display:none}"
        )
    if not out:
        return ""
    return "<style>" + "".join(out) + "</style>"
