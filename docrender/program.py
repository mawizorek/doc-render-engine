"""Stage 05b -- the FLOW STRIP: which program a reader is in, and what is next.

WHY decisions here are the way they are: the doc-render-engine Decision Log.
The `chain:` vocabulary and the prev/next wiring belong to docrender/nav.py; the
embedded completion form is docrender/forms.py. This module owns exactly one
thing, and it is what a reader SEES of a flow.

⚠️ AND ON 2026-08-28 THIS DOCSTRING HIT THE 22,528 B READ CEILING, so two dated
post-mortems were CUT to the pointers below rather than trimmed further. The line
directly above names the Decision Log as the home for *why*, and this file had
accumulated five dated narratives against it -- **the operative rules stay here,
the history stays there.** ⚑ *Two trims that each recovered less were the signal;
the seam was that a module docstring had become a changelog.*

  DL J19 · `hide: footer` and the strip becoming the ONLY footer. ⚠️ Its live
    rule survives: `hide: footer` MUST be per-page on chain members only, because
    a page in no flow with its footer hidden has ZERO navigation and nothing
    reports it.
  DL J20 · the night every Next link dropped the reader at the FOOT of the page,
    because one fragment was doing two jobs (state carrier and scroll target).
    ⚠️ Its live rule survives in `_at_id()`: two ids per flow, spelled in one
    place.
  DL J21 · the corner-stamp program name, shipped and reverted in seven minutes.
    ⚠️ Its live rule: the orientation gap on PAPER is open, and a fix needs its
    own element beside the h1 rather than a third clause on the build stamp.

=============================================================================
🔴 WHY A STRIP EXISTS: prev/next HAS ONE SLOT AND A PAGE HAS MANY FLOWS
=============================================================================
`chain:` decoupled the reading order from the sidebar and hit its own ceiling
within the hour. Michael: *"I could define workflows that go through specific
pages, even if those workflows contain some of the same pages."*

That is not a bigger chain. A MkDocs page has exactly ONE `previous_page` and
ONE `next_page`. Two programs walking through Housekeeping need it to have two
different "next" values, and which is right depends on HOW THE READER ARRIVED --
a per-request fact. This is a static site generator. There is no request.

⚑ SO THE ANSWER IS NOT A SMARTER SLOT, IT IS TO STOP COMPETING FOR ONE. The
strip is ADDITIVE: a page in three programs renders three strips and nothing
overlaps, because no strip owns anything another one wants.

=============================================================================
⭐ THE STRIP'S JOB IS ORIENTATION, NOT NAVIGATION
=============================================================================
A reader never browses to a policy. They are HANDED a program, land on it, and
walk pages that live in another folder and belong to nobody. The pages are
BORROWED. So a bare `← Housekeeping | Fire →` would say what the sidebar would
say and leave a reader three pages deep not knowing which program they are in.

    General Safety for All · step 4 of 9
    ← Proper Attire            Emergency Contacts →

The PROGRAM NAME is the payload; the arrows are the instruction.

=============================================================================
⭐ THE START STRIP -- THE HUB IS NEVER A MEMBER OF ITS OWN CHAIN
=============================================================================
Found by Michael: *"how to get the starting page to actually navigate to the
first page in the chain - right now it doesn't have any real published pointer."*

Structural: a page's `id:` was matched against chain MEMBERS, and a program
declares its list without being in it. Its only pointer was `nav.py`'s
`hub.next_page` -- IN THE DEFAULT FOOTER, the element `hide: footer` removes. So
a page that DECLARES a chain gets a `--start` variant.

=============================================================================
🔴 WHERE PURE CSS RUNS OUT, WHICH IS WORTH STATING PLAINLY
=============================================================================
A generic rule cannot say "the strip whose id matches the targeted marker" --
selectors cannot compare two values. So `_promo_css()` emits THREE SHORT RULES
PER FLOW, per page, naming both ids. That breaks a rule this file set for itself
(no inline style; every stylesheet goes through `assets.py` so
`hand_written_css()` stays the single source for the token audit) and it is
broken DELIBERATELY:

  1. it is per-PAGE DATA, not a stylesheet -- the ids are facts about this page,
     and `flow.css` still owns every look decision
  2. `assets.py` is over the engine's ~22KB read ceiling, so adding an asset
     means rewriting a file that cannot be read whole (the `util.py` clobber)
  3. it is ~180 bytes on pages in a flow, and nothing at all elsewhere

⚠️ `display: contents` ON THE DISCLOSURE IS THE EXOTIC PART, AND IT IS THE ONE
THING HERE MOST LIKELY TO SURPRISE SOMEBODY. A closed `<details>` hides its
children, and CSS cannot open one. When the targeted strip is INSIDE the
disclosure, the rule makes that `<details>` `display: contents` so its children
join the flex layout and become visible -- then `order: -1` hoists the targeted
strip above the rest.
✅ DEGRADES HONESTLY: if a browser ignores it, the reader lands at the top of the
correct page with the correct chain and one click to open the disclosure.

🔴 AND THE THIRD RULE EXISTS BECAUSE THE FIRST TWO SUCCEEDED AND LOOKED LIKE THEY
HAD FAILED (2026-08-28). Michael, expecting the arrival program to win: *"instead
of burying the current program inside the 'also in other programs' dropdown."*
The promotion was firing. **What stayed on screen was its label.**
`display: contents` removes the `<details>` BOX and not its `<summary>`, so a
successful hoist still rendered *"▸ Also part of 1 other program"* as a loose
line -- at `order: 0`, therefore BELOW the strip it was supposedly hiding, naming
a state that was no longer true.

⚑ **A FEATURE CAN BE WORKING AND STILL BE WEARING ITS OWN FAILURE MESSAGE**, and
nobody debugging it will look at the mechanism, because the label is more legible
than the layout. `flow.css` documented the loose summary as intended behaviour
and never asked what the loose summary would SAY.

🚫 STILL NO JAVASCRIPT. A script would flap the footer on every page load.

⚠️ AND IT IS `:target`-ONLY, SO IT FIRES ONLY ON ARRIVAL FROM A FLOW LINK. A
reader who reaches a policy from the SIDEBAR, a bookmark or a search result is in
no flow and gets the declared order below. That is deliberate -- guessing tells a
reader they are in MEWP training when they are not -- but it means the feature is
absent from about half of all arrivals, which is why the default matters.

=============================================================================
⭐ THE DEFAULT ORDER IS THE SIDEBAR'S OWN KEY (2026-08-28)
=============================================================================
> Michael: *"how do i write in a default???"*

**With `order:` on the program page, and it is not a new key.** `_participation`
sorted by src_uri, so `10-general/for-all.md` beat `10-general/rehearsal.md`
alphabetically and rehearsal was permanently second on every policy they share --
a default nobody chose, produced by a filename.

🚫 NO NEW VOCABULARY, WHICH IS THE POINT. `objects.py:_child_list` already sorts
by `order:` and says why: *"Two orders for the same set of pages on the same
screen is the sort of disagreement nobody reports and everybody notices."* The
strip list is a third such surface. Same key, same `10_000` sentinel for a page
that declares none, so an undeclared program falls to the old alphabetical
behaviour rather than to the front.

⚑ *A request for a default is usually a request for a KEY, and the right answer
is nearly always a key that already sorts something else.* `nav.py` refused a
program-specific `steps:` on this exact ground.

=============================================================================
🔴 A LONE STEP STATES NO COUNT (2026-08-28)
=============================================================================
> Michael: *"the navigation footer stuff that says 'step 1 of 1'."*

A one-page chain rendered `step 1 of 1`, which is not a position -- there is
nowhere else to be.

🚫 THE STRIP IS NOT SUPPRESSED, AND THAT IS THE JUDGEMENT WORTH ARGUING. Dropping
the whole block was the obvious reading and it builds a DEAD END: on a one-step
chain the strip's only other content is the `Finish <name>` link, which is the
reader's only route to the completion form. **Removing a navigation block because
its label was useless would have removed the one useful thing in it.** ⚑ *A
complaint about a label is not a complaint about the element carrying it.*

=============================================================================
⚠️ THE CAP
=============================================================================
First flow open, the rest inside a `<details>` -- which collapses with no
stylesheet and no script, and prints open because print-flow.css already forces
that. ⚠️ AND THE CAP IS FULLY SPENT WHEN A PROMOTION FIRES: `display: contents`
reveals EVERY strip in the disclosure, not only the promoted one. Correct rather
than tidy -- the reader asked for one of them by name and the rest are one line
each -- and it is why hiding the summary is consistent rather than a patch.
"""

from __future__ import annotations

from . import forms, nav, state
from .util import relative_url

#: What a page with no `order:` sorts as. Matches `objects.py:_child_list`
#: exactly, because the two are sorting the same pages for the same reader.
_NO_ORDER = 10_000


def _esc(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _meta(src) -> dict:
    return state.BY_SRC.get(src, {}) or {}


def _title(src, page) -> str:
    meta = _meta(src)
    return str(meta.get("title") or getattr(page, "title", "") or src)


def _url(page) -> str:
    return getattr(getattr(page, "file", None), "url", "")


def _src(page) -> str:
    return getattr(getattr(page, "file", None), "src_uri", "")


def _strip_id(flow_id: str) -> str:
    """The id ON THE STRIP, at the foot of the page."""
    return "flow-" + str(flow_id) if flow_id else ""


def _at_id(flow_id: str) -> str:
    """The id every LINK points at: a marker at the TOP of the page.

    ⚠️ TWO IDS PER FLOW, AND THE SPLIT IS THE WHOLE FIX (DL J20). One is where the
    reader ARRIVES (top), one is what gets PROMOTED (the strip, bottom). They were
    the same id for an hour, and that is why every Next link dropped the reader at
    the foot of the next policy: a fragment is BOTH the state carrier and the
    scroll target, and only the first job was designed for.

    ⚑ A mechanism serving two purposes must be checked against BOTH, and the one
    you did not design for is the one the reader meets first.

    Both ids are spelled here and nowhere else, exactly as `forms.slot_anchor`
    owns the form's id -- a fragment matching no element is not an error anywhere,
    so a link and its target computed in two places fails silently and forever.
    """
    return "at-flow-" + str(flow_id) if flow_id else ""


def _order(src) -> tuple:
    """The sort key for a program: its declared `order:`, then its path.

    See THE DEFAULT ORDER in the module docstring. The path stays as the
    tiebreak so two programs at the same `order:` are still deterministic --
    a build that reorders itself between runs is worse than one nobody chose.
    """
    raw = _meta(src).get("order")
    return (raw if isinstance(raw, int) else _NO_ORDER, src)


def _participation(src, pid, chains):
    """Every flow this page takes part in, as (flow_src, role, index).

    ✅ ONE WALK OVER THE CHAIN MAP, NAMED ONCE. `_strips` did this inline; a second
    consumer (`flow_names`, for the printed corner mark) forced the extraction and
    was reverted the same evening. **The extraction stayed because it was right on
    its own** -- the render order below is a real rule and it now has one place to
    live rather than being implied by the shape of a loop.

    `role` is `"start"` on the page that DECLARES the chain, `"member"` on a step
    in it. `index` is the position in the DECLARED list, or -1 for a start.

    ⚠️ ORDER IS THE RENDER ORDER AND IS LOAD-BEARING: the page's own chain first,
    because on a program page the entrance outranks any flow it is also a step in.
    Everything after it is sorted by `_order` -- the sidebar's key, never the
    filename.
    """
    out = []
    if src in chains:
        out.append((src, "start", -1))
    if pid:
        for flow_src in sorted(chains, key=_order):
            if flow_src == src:
                continue
            ids = chains[flow_src]
            if pid in ids:
                out.append((flow_src, "member", ids.index(pid)))
    return out


def _link(cls, page, here, frag, label, arrow_before=False) -> str:
    text = _esc(label)
    text = "\u2190 " + text if arrow_before else text + " \u2192"
    return (
        '<a class="' + cls + '" href="'
        + _esc(relative_url(_url(page), here) + frag) + '">' + text + "</a>"
    )


def _where(flow_name, hub, here, frag, detail) -> str:
    """The orientation line: which program, and where in it.

    ⚠️ AN EMPTY `detail` OMITS THE SPAN rather than rendering an empty one, which
    would still occupy its margins and read as a value that failed to load. Same
    argument `table.py` makes for skipping an empty detail cell.
    """
    if hub is not None:
        who = (
            '<a class="dr-flow__program" href="'
            + _esc(relative_url(_url(hub), here) + frag) + '">'
            + _esc(flow_name) + "</a>"
        )
    else:
        who = '<span class="dr-flow__program">' + _esc(flow_name) + "</span>"
    step = (
        ' <span class="dr-flow__step">' + _esc(detail) + "</span>"
        if detail else ""
    )
    return '<p class="dr-flow__where">' + who + step + "</p>"


def _open_tag(flow_id, name, extra="") -> str:
    """The `<nav>`, carrying the strip id and a machine-readable slug.

    ⚠️ `data-dr-flow` IS NOT READ BY ANYTHING IN THIS ENGINE and is emitted
    anyway, which is the sort of thing this repo normally refuses. Kept on one
    condition, stated so it can be revoked: an id is a NAVIGATION target and gets
    mangled to stay URL-safe, so it is the wrong thing for an instance's
    `theme.css` to hook when it wants to paint one program differently. If no
    site ever styles on it, delete it.
    """
    bits = ['<nav class="dr-flow' + (" " + extra if extra else "") + '"']
    if flow_id:
        bits.append(' id="' + _esc(_strip_id(flow_id)) + '"')
        bits.append(' data-dr-flow="' + _esc(flow_id) + '"')
    bits.append(' aria-label="' + _esc(name) + ' \u00b7 reading order">')
    return "".join(bits)


def _flow_meta(flow_src, by_src):
    """(hub page, display name, flow id, link fragment) for a chain's page."""
    hub = by_src.get(flow_src)
    flow_id = str(_meta(flow_src).get("id") or "").strip()
    name = _title(flow_src, hub) if hub is not None else flow_src
    at = _at_id(flow_id)
    return hub, name, flow_id, ("#" + at if at else "")


def _member_strip(flow_src, ids, at, page, by_id, by_src) -> str:
    """One strip on a page that IS a step in this flow.

    ⚠️ `at` IS THE POSITION IN THE DECLARED LIST, and the printed total is the
    length of the RESOLVED list, so a chain naming a page that does not exist
    reports "step 4 of 8" rather than claiming a step that was skipped.
    """
    here = _url(page)
    hub, name, flow_id, frag = _flow_meta(flow_src, by_src)

    live = [pid for pid in ids if pid in by_id]
    try:
        step = live.index(ids[at]) + 1
    except (ValueError, IndexError):
        step = at + 1
    i = step - 1

    # 🔴 A LONE STEP STATES NO COUNT. See the module docstring, including why the
    # STRIP survives: its `Finish` link is the only route to the form.
    detail = "" if len(live) < 2 else "step " + str(step) + " of " + str(len(live))

    moves = []
    if i > 0:
        prev = by_id[live[i - 1]]
        moves.append(
            _link(
                "dr-flow__prev", prev, here, frag,
                _title(_src(prev), prev), arrow_before=True,
            )
        )
    if i + 1 < len(live):
        nxt = by_id[live[i + 1]]
        moves.append(
            _link("dr-flow__next", nxt, here, frag, _title(_src(nxt), nxt))
        )
    elif hub is not None:
        # THE END IS A LINK, AND IT AIMS AT THE FORM.
        #
        # ⚠️ THIS IS THE ONE LINK THAT DELIBERATELY DOES NOT GO TO THE TOP. A URL
        # has one fragment, and here the destination IS the form: the reader has
        # finished reading and the only thing left is to submit. Landing on the
        # form is the point rather than a side effect -- which is exactly the
        # check that was never applied to the other links.
        slot = forms.first_slot(_meta(flow_src))
        target = relative_url(_url(hub), here)
        target += ("#" + forms.slot_anchor(slot)) if slot else frag
        moves.append(
            '<a class="dr-flow__end" href="' + _esc(target) + '">'
            + _esc("Finish " + name) + " \u2192</a>"
        )
    else:
        moves.append('<span class="dr-flow__end">end of this program</span>')

    return (
        _open_tag(flow_id, name)
        + _where(name, hub, here, frag, detail)
        + '<p class="dr-flow__move">' + " ".join(moves) + "</p></nav>"
    )


def _start_strip(flow_src, ids, page, by_id) -> str:
    """The strip on a page that DECLARES a chain.

    Returns "" when nothing in the chain resolved -- a Start button pointing
    nowhere is worse than no button, and nav.py has already reported that case.
    """
    live = [pid for pid in ids if pid in by_id]
    if not live:
        return ""

    here = _url(page)
    name = _title(flow_src, page)
    flow_id = str(_meta(flow_src).get("id") or "").strip()
    at = _at_id(flow_id)
    frag = "#" + at if at else ""
    first = by_id[live[0]]

    # 🐛 `1 steps` shipped with this variant. A count is the one string here that
    # has to agree with itself.
    detail = str(len(live)) + (" step" if len(live) == 1 else " steps")

    return (
        _open_tag(flow_id, name, "dr-flow--start")
        + _where(name, None, here, frag, detail)
        + '<p class="dr-flow__move">'
        + _link(
            "dr-flow__next", first, here, frag,
            "Start: " + _title(_src(first), first),
        )
        + "</p></nav>"
    )


def _promo_css(flow_ids) -> str:
    """Per-page rules tying the TOP marker to the strip it promotes.

    See the module docstring for why this is generated per page rather than
    living in `assets/flow.css`.

    Three rules per flow:
      1. hoist the strip above its siblings
      2. make the disclosure transparent, so a strip parked inside it is visible
         at all (a closed `<details>` hides its children and CSS cannot open one)
      3. 🔴 hide that disclosure's SUMMARY. Rule 2 removes the box and leaves the
         label, so a successful promotion still said "Also part of 1 other
         program" -- below the strip it had just hoisted, about a state that no
         longer held. The module docstring carries the argument.

    ⚠️ RULE 3 IS SCOPED BY `:has()`, SAME AS RULE 2, so it fires only when THIS
    flow's strip is the one inside the disclosure. A promoted strip that was
    already the open one leaves the label alone, correctly: the disclosure still
    describes real flows the reader has not asked for.

    ⚠️ `~` REQUIRES THE MARKER AND `.dr-flows` TO BE SIBLINGS, which they are:
    both are inserted by `on_page_content` into the same container, the marker
    first and the strips last. If either ever moves into a wrapper, these rules
    stop matching -- silently, because a selector that matches nothing is not an
    error. That is the trade for not shipping a script.
    """
    out = []
    for flow_id in flow_ids:
        at = _at_id(flow_id)
        strip = _strip_id(flow_id)
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


def _strips(page, files):
    """(markers + promo css, strips html) for this page, or ("", "")."""
    src = _src(page)
    if not src:
        return "", ""

    chains = nav.declared(report=False)
    if not chains:
        return "", ""

    by_id, by_src = nav._built(files)
    pid = str(_meta(src).get("id") or "").strip()
    rendered = []
    flow_ids = []

    def note(flow_src):
        fid = str(_meta(flow_src).get("id") or "").strip()
        if fid:
            flow_ids.append(fid)

    # ⚠️ ORDER COMES FROM `_participation`, NOT FROM HERE.
    for flow_src, role, at in _participation(src, pid, chains):
        if role == "start":
            start = _start_strip(flow_src, chains[flow_src], page, by_id)
            if start:
                rendered.append(start)
                note(flow_src)
        else:
            rendered.append(
                _member_strip(
                    flow_src, chains[flow_src], at, page, by_id, by_src
                )
            )
            note(flow_src)

    if not rendered:
        return "", ""

    # THE ARRIVAL MARKERS, at the very top of the page. Zero height, no text, and
    # one per flow this page belongs to.
    head = "".join(
        '<span class="dr-at" id="' + _esc(_at_id(f)) + '"></span>'
        for f in flow_ids
        if _at_id(f)
    )
    head += _promo_css(flow_ids)

    if len(rendered) == 1:
        return head, '<div class="dr-flows">' + rendered[0] + "</div>"

    # ⚠️ THE FIRST STRIP IS THE DECLARED DEFAULT, NOT "THE ACTIVE ONE". Which flow
    # is active is decided in the browser by the fragment; this order is what a
    # reader with no fragment sees, and `order:` on the program page is how it is
    # chosen. See THE DEFAULT ORDER in the module docstring.
    others = len(rendered) - 1
    body = (
        '<div class="dr-flows dr-flows--many">' + rendered[0]
        + '<details class="dr-flows__others"><summary>Also part of '
        + str(others) + " other program" + ("" if others == 1 else "s")
        + "</summary>" + "".join(rendered[1:]) + "</details></div>"
    )
    return head, body


def on_page_content(html, page, config, files):
    """Markers at the top, flow strips at the foot.

    Runs BEFORE hook 06 so the strips sit above the edit line rather than under
    it -- a reader's next step outranks a maintainer's.

    ⚠️ THE MARKER MUST BE FIRST IN THE RETURNED STRING and the strips last: the
    promotion rules use a sibling combinator, so their ORDER in the document is
    load-bearing. Prepending to `html` rather than wrapping it is what keeps them
    siblings. Hook 07 prepends the corner stamp ahead of the marker, which is safe
    for the same reason: another sibling in front of both changes nothing.
    """
    head, strips = _strips(page, files)
    if not strips:
        return html
    return head + html + strips
