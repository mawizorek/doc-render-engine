"""Stage 05b -- the FLOW STRIP: which program a reader is in, and what is next.

WHY decisions here are the way they are: the doc-render-engine Decision Log.
The `chain:` vocabulary and the prev/next wiring belong to docrender/nav.py; the
embedded completion form is docrender/forms.py. This module owns exactly one
thing, and it is what a reader SEES of a flow.

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
⭐ AND IT IS THE ONLY FOOTER, WHICH CHANGED ITS JOB
=============================================================================
It was designed as a SECOND footer beside Material's prev/next. Michael read the
result and rejected it in exactly the right words: *"all this other foot matter"*
and *"is that what I'm supposed to click next? It's not actually appearing in the
main footer; it's in this other separate footer you created."*

The fix he chose was better than the one offered: 🔴 KILL THE DEFAULT FOOTER AND
LET THE STRIP BE IT (`hide: footer`). It needed no code -- the strip is appended
in `on_page_content`, so it survives a hidden footer -- and ⭐ IT DISSOLVES THE
ONE-SLOT PROBLEM: if strips are the only navigation then nothing is competing, so
two programs sharing a page both navigate correctly.

⚠️ THE COST, AND IT IS A REAL TRAP: `hide: footer` MUST BE PER-PAGE ON CHAIN
MEMBERS ONLY. A page in no flow with its footer hidden has ZERO navigation, and
nothing reports it.

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

⭐ AND THAT SENTENCE IS WHY `flow_names()` EXISTS (2026-08-28). `.dr-flows` is in
print-chrome.css's chrome-off list now -- paper has no navigation to offer -- so
the strip does not print at all. But *a payload that only survives on screen is
not a payload*, so `buildstamp.py` asks THIS module which programs a page belongs
to and prints their names on the corner mark. 🔴 It ASKS rather than deriving:
`_participation()` is the only answer to "which flows is this page in," because a
second walk over `nav.declared()` elsewhere would agree today and drift the first
time either side changed -- and nobody can diff a printed sheet against a page.

=============================================================================
⭐ THE START STRIP -- THE HUB IS NEVER A MEMBER OF ITS OWN CHAIN
=============================================================================
Found by Michael: *"how to get the starting page to actually navigate to the
first page in the chain - right now it doesn't have any real published pointer."*

Structural: `_flows_for` matched a page's `id:` against chain MEMBERS, and a
program declares its list without being in it. Its only pointer was `nav.py`'s
`hub.next_page` -- IN THE DEFAULT FOOTER, the element `hide: footer` removes. So
a page that DECLARES a chain gets a `--start` variant.

=============================================================================
🔴 WHERE A LINK LANDS YOU: THE TOP OF THE PAGE (FIXED 2026-08-19, SAME NIGHT)
=============================================================================
Michael: *"each time you hit next in for the workflow, you're at the bottom of
the next page - can you put us back to the top of each nexted page?"*

MY BUG, AND IT WAS AN HOUR OLD. The previous version pointed every strip link at
`#flow-<program id>` -- the id ON THE STRIP -- so the browser scrolled to it, and
the strip is at the BOTTOM of the page. Walking a safety program dumped the
reader past the whole policy every time.

⚑ THE LESSON IS ABOUT ROLES, NOT ABOUT SCROLLING. A fragment does TWO jobs at
once: it is the STATE CARRIER (which flow am I in) and it is the SCROLL TARGET.
I chose the anchor for the first job and never asked what the second one would
do. A mechanism serving two purposes must be checked against BOTH, and the one
you did not design for is the one the reader meets first.

⭐ SO THE TARGET MOVED TO THE TOP AND THE STATE STAYED. Each page in a flow gets
a zero-height marker at the very top:

    <span class="dr-at" id="at-flow-program-general-safety"></span>

Links point THERE. The reader lands at the top; the fragment still names the
flow, so the promotion still works.

🔴 AND THIS IS WHERE PURE CSS RUNS OUT, WHICH IS WORTH STATING PLAINLY. A
generic rule cannot say "the strip whose id matches the targeted marker" --
selectors cannot compare two values. So `_promo_css()` emits TWO SHORT RULES PER
FLOW, per page, naming both ids. That breaks a rule this file set for itself
tonight (no inline style; every stylesheet goes through `assets.py` so
`hand_written_css()` stays the single source for the token audit) and it is
broken DELIBERATELY, on three grounds:

  1. it is per-PAGE DATA, not a stylesheet -- the ids are facts about this page,
     and `flow.css` still owns every look decision
  2. `assets.py` is 22,333 B, at the engine's ~22KB read ceiling, so adding an
     asset means rewriting a file that cannot be read whole (the `util.py`
     clobber)
  3. it is ~120 bytes on pages that are in a flow, and nothing at all elsewhere

⚠️ `display: contents` ON THE DISCLOSURE IS THE EXOTIC PART, AND IT IS THE ONE
THING HERE MOST LIKELY TO SURPRISE SOMEBODY. A closed `<details>` hides its
children, and CSS cannot open one. When the targeted strip is INSIDE the
disclosure, the rule makes that `<details>` `display: contents` so its children
join the flex layout and become visible -- then `order: -1` hoists the targeted
strip above the rest. ⚠️ Its `<summary>` becomes a loose line of text when this
fires, which is why `flow.css` needs no extra rule for it: the summary reads as
a label, not a control, and the disclosure is moot once its contents are shown.
✅ DEGRADES HONESTLY: if a browser ignores it, the reader lands at the top of the
correct page with the correct chain and one click to open the disclosure. Same
degradation shape as the collapsed form -- one extra click, never a dead end.

🚫 STILL NO JAVASCRIPT. A script would flap the footer on every page load, and
the scroll fix does not need one.

⚠️ A BARE URL STILL PROMOTES NOTHING, deliberately. Somebody who bookmarked a
policy is in NO flow, and guessing tells a reader they are in MEWP training when
they are not.

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

🐛 The same pass fixed `1 steps` on the start strip -- live since that variant
shipped, invisible because no real program has one page.

=============================================================================
⚠️ THE CAP
=============================================================================
First flow open, the rest inside a `<details>` -- which collapses with no
stylesheet and no script, and prints open because print-flow.css already forces
that. The promotion rules above are what make "active" true rather than
"whichever sorted first".
"""

from __future__ import annotations

from . import forms, nav, state
from .util import relative_url


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

    ⚠️ TWO IDS PER FLOW, AND THE SPLIT IS THE WHOLE FIX. One is where the reader
    ARRIVES (top), one is what gets PROMOTED (the strip, bottom). They were the
    same id for an hour and that is why Next dropped people at the foot of every
    policy. Both are spelled here and nowhere else, exactly as
    `forms.slot_anchor` owns the form's id -- a fragment matching no element is
    not an error anywhere, so a link and its target computed in two places fails
    silently and forever.
    """
    return "at-flow-" + str(flow_id) if flow_id else ""


def _participation(src, pid, chains):
    """Every flow this page takes part in, as (flow_src, role, index).

    🔴 THE ONLY ANSWER TO "WHICH FLOWS IS THIS PAGE IN." `_strips` walked this
    inline; `flow_names()` needs the same answer for the printed corner mark, and
    two walks would be two claimants on one fact -- the defect that retired three
    manifests here.

    `role` is `"start"` on the page that DECLARES the chain, `"member"` on a step
    in it. `index` is the position in the DECLARED list, or -1 for a start.

    ⚠️ ORDER IS THE RENDER ORDER AND IS LOAD-BEARING: the page's own chain first,
    because on a program page the entrance outranks any flow it is also a step in.
    The rest is `sorted()` so a build is reproducible rather than dict-ordered.
    """
    out = []
    if src in chains:
        out.append((src, "start", -1))
    if pid:
        for flow_src in sorted(chains):
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
    living in `assets/flow.css`: a selector cannot compare a targeted element's
    id to another element's id, so the two ids have to be named literally.

    Two rules per flow:
      1. hoist the strip above its siblings
      2. make the disclosure transparent, so a strip parked inside it is visible
         at all (a closed `<details>` hides its children and CSS cannot open one)

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
        out.append(
            "#" + at + ":target ~ .dr-flows #" + strip
            + "{order:-1;margin-top:0;padding-top:0;border-top:0}"
            "#" + at + ":target ~ .dr-flows .dr-flows__others:has(#" + strip
            + "){display:contents}"
        )
    if not out:
        return ""
    return "<style>" + "".join(out) + "</style>"


def flow_names(page, files) -> list[str]:
    """The display name of every program this page takes part in, in render order.

    ⭐ THE ORIENTATION HALF OF THE STRIP, FOR A MEDIUM THAT DROPS THE STRIP --
    `buildstamp.py` prints these on the printed corner mark. Shares
    `_participation()` with `_strips` rather than re-deriving; see that function
    and the module docstring.

    `report=False` because this runs per page and every chain problem it could
    report is already reported once by `nav.py`.
    """
    src = _src(page)
    if not src:
        return []
    chains = nav.declared(report=False)
    if not chains:
        return []

    pid = str(_meta(src).get("id") or "").strip()
    seats = _participation(src, pid, chains)
    if not seats:
        return []

    _by_id, by_src = nav._built(files)
    names = []
    for flow_src, _role, _at in seats:
        _hub, name, _fid, _frag = _flow_meta(flow_src, by_src)
        if name and name not in names:
            names.append(name)
    return names


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

    # ⚠️ THE FIRST STRIP IS THE BUILD-TIME DEFAULT, NOT "THE ACTIVE ONE". Which
    # flow is active is decided in the browser by the fragment; this order is
    # only what a reader with no fragment sees.
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
