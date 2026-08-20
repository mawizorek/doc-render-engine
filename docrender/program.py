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
⭐ AND AS OF 2026-08-19 IT IS THE ONLY FOOTER, WHICH CHANGED ITS JOB
=============================================================================
It was designed as a SECOND footer beside Material's prev/next. Michael read the
result and rejected it in exactly the right words: *"all this other foot matter"*
and *"is that what I'm supposed to click next? It's not actually appearing in the
main footer; it's in this other separate footer you created."*

The fix he chose was better than the one offered. 🔴 KILL THE DEFAULT FOOTER AND
LET THE STRIP BE IT (`hide: footer` in a page's frontmatter). It needed no code
at all -- the strip is appended in `on_page_content`, so it survives a hidden
footer -- and ⭐ IT DISSOLVES THE ONE-SLOT PROBLEM ENTIRELY: if strips are the
only navigation then nothing is competing, so two programs sharing a page both
navigate correctly and neither loses its buttons to alphabetical order.

⚠️ THE COST, AND IT IS A REAL TRAP: `hide: footer` MUST BE PER-PAGE ON CHAIN
MEMBERS ONLY. A page in no flow with its footer hidden has ZERO navigation, and
nothing reports it. Dropping a page from a chain later removes its strip and
leaves it stranded on an already-hidden footer.

=============================================================================
⭐ THE STRIP'S JOB IS ORIENTATION, NOT NAVIGATION
=============================================================================
From Michael's own question -- *"I don't even know how this sort of thing would
realistically feel from a user perspective"* -- which was the right thing to be
suspicious of.

A reader never browses to a policy. They are HANDED a program, land on it, and
walk pages that live in another folder and belong to nobody. The pages are
BORROWED. So a bare `← Housekeeping | Fire →` would say what the sidebar would
say and leave a reader three pages deep not knowing which program they are in.

    General Safety for All · step 4 of 9
    ← Proper Attire            Emergency Contacts →

The PROGRAM NAME is the payload; the arrows are the instruction. flow.css makes
Next the only filled control, because when two arrows carry identical weight
neither reads as the instruction.

=============================================================================
⭐ THE START STRIP -- THE HUB IS NEVER A MEMBER OF ITS OWN CHAIN
=============================================================================
A hole in the original design, found by Michael: *"how to get the starting page
to actually navigate to the first page in the chain - right now it doesn't have
any real published pointer."*

He was right, and the cause is structural. `_flows_for` matches a page's `id:`
against chain MEMBERS, and a program declares its list without being in it. So a
program page could never render a strip. Its only pointer was
`nav.py`'s `hub.next_page = resolved[0]` -- IN THE DEFAULT FOOTER, the element
the plan above hides. Strip-as-only-footer had a hole exactly at the entrance.

So a page that DECLARES a chain gets a `--start` variant. 🚫 And the hand-typed
`!!! note "Start Here"` callout it replaces is now deletable rather than
load-bearing -- that callout drifts silently the moment the chain is reordered,
which is the same defect `chain:` was built to end.

=============================================================================
⭐ AND THE END OF A FLOW IS A LINK NOW, NOT A FULL STOP
=============================================================================
It shipped as dead text ("end of this program"), which is worst exactly where it
matters most: with the footer hidden, the last step is the ONE page with nowhere
to go, and it is where somebody needs the completion form.

So the last step's Next points back at the program, and -- if the program
declares a `forms:` slot -- at the FRAGMENT of that form's disclosure, which
opens a collapsed form on arrival with no script. See forms.py `collapsed:`.
⚠️ The id is spelled by `forms.slot_anchor()` and never by this file: a link and
its target computed in two places is a Next button that lands on nothing, and a
fragment matching no element is not an error anywhere.

=============================================================================
🔴 THE ACTIVE FLOW IS CARRIED IN THE FRAGMENT (2026-08-19, SAME DAY)
=============================================================================
Michael, on the shipped version: *"when entering the same page from different
workflows, the app isn't 'aware' and puts the second (now active) program inside
the 'also part of' section instead."*

Exactly right, and it was the last real gap. Strip ORDER is baked at build time
and "which flow am I in" is per-request, so the first strip was whichever program
sorted first -- and a reader walking MEWP through a shared policy found MEWP
filed under "Also part of" while somebody else's program sat on top.

⭐ THE FIX IS THE MECHANISM THE COLLAPSED FORM ALREADY PROVED. Every strip link
carries `#flow-<program id>`, so arriving from a program targets THAT program's
strip, and two things follow from the HTML spec with no code:

  1. a fragment pointing INSIDE a closed `<details>` OPENS it, so a flow parked
     in the disclosure is expanded on arrival rather than buried
  2. `:target` matches it, so flow.css hoists it with `order: -1` and inverts its
     step chip

🚫 AND THE `?flow=` QUERY PARAM IS DELETED. It shipped hours earlier and NOTHING
EVER READ IT. A URL parameter no code consumes is precisely the dead-key defect
this engine keeps paying for -- `sort:` in eleven content files, the inert
`palette:`, `revised:` declared-but-unread, `aliases:` whose only consumer was
imaginary for two days. ⚑ Worse than a dead frontmatter key, in fact: a param is
visible in the address bar, so it LOOKS like state to the person reading the URL.
The fragment does the work; the param was the decoration.

⚠️ NO JAVASCRIPT, and the reason is not only purity. A script would flap the
footer on every page load, and `docrender/assets.py` crossed the 22KB hard read
ceiling on 2026-08-19 (22,436 B), so registering a new asset now means rewriting
a file that cannot be read whole -- the clobber this repo has already paid for
once in `util.py`. Being unable to take the bad option is not the same as
choosing the good one; this is the good one.

⚠️ A BARE URL STILL PROMOTES NOTHING, deliberately. Somebody who bookmarked
Housekeeping or arrived from the sidebar is in NO flow, and guessing one tells a
reader they are in MEWP training when they are not. No fragment = every flow
shown, none claimed.

=============================================================================
⚠️ THE CAP
=============================================================================
Michael asked for only the ACTIVE workflow visible, the rest behind an icon.
First flow open, the rest inside a `<details>` -- which collapses with no
stylesheet and no script, and prints open because print-flow.css already forces
that. The `:target` rules above are what make "active" true rather than
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


def _anchor(flow_id: str) -> str:
    """The strip id, and the fragment every link in that flow points at.

    ⚠️ ONE FUNCTION SPELLS IT, exactly as `forms.slot_anchor` owns the form's id
    and for the same reason: a fragment that matches no element is not an error
    in any browser or any build, so a link and its target computed in two places
    fails silently and forever.
    """
    return "flow-" + str(flow_id) if flow_id else ""


def _link(cls, page, here, frag, label, arrow_before=False) -> str:
    text = _esc(label)
    text = "\u2190 " + text if arrow_before else text + " \u2192"
    return (
        '<a class="' + cls + '" href="'
        + _esc(relative_url(_url(page), here) + frag) + '">' + text + "</a>"
    )


def _where(flow_name, hub, here, frag, detail) -> str:
    if hub is not None:
        who = (
            '<a class="dr-flow__program" href="'
            + _esc(relative_url(_url(hub), here) + frag) + '">'
            + _esc(flow_name) + "</a>"
        )
    else:
        who = '<span class="dr-flow__program">' + _esc(flow_name) + "</span>"
    return (
        '<p class="dr-flow__where">' + who
        + ' <span class="dr-flow__step">' + _esc(detail) + "</span></p>"
    )


def _open_tag(flow_id, name, extra="") -> str:
    """The `<nav>`, carrying the id `:target` needs and a machine-readable slug.

    ⚠️ `data-dr-flow` IS NOT READ BY ANYTHING IN THIS ENGINE and is emitted
    anyway, which is the sort of thing this repo normally refuses. It is kept on
    one condition, stated here so it can be revoked: an id is a NAVIGATION target
    and gets mangled to stay URL-safe, so it is the wrong thing for an instance's
    `theme.css` to hook when it wants to paint one program differently. The
    attribute carries the slug verbatim. If no site ever styles on it, delete it.
    """
    bits = ['<nav class="dr-flow' + (" " + extra if extra else "") + '"']
    if flow_id:
        bits.append(' id="' + _esc(_anchor(flow_id)) + '"')
        bits.append(' data-dr-flow="' + _esc(flow_id) + '"')
    bits.append(' aria-label="' + _esc(name) + ' \u00b7 reading order">')
    return "".join(bits)


def _flow_meta(flow_src, by_src):
    """(hub page, display name, fragment) for a chain's declaring page."""
    hub = by_src.get(flow_src)
    flow_id = str(_meta(flow_src).get("id") or "").strip()
    name = _title(flow_src, hub) if hub is not None else flow_src
    anchor = _anchor(flow_id)
    return hub, name, flow_id, ("#" + anchor if anchor else "")


def _member_strip(flow_src, ids, at, page, by_id, by_src) -> str:
    """One strip on a page that IS a step in this flow.

    ⚠️ `at` IS THE POSITION IN THE DECLARED LIST, and the printed total is the
    length of the RESOLVED list, so a chain naming a page that does not exist
    reports "step 4 of 8" rather than claiming a step that was skipped. The two
    numbers come from different lists on purpose.
    """
    here = _url(page)
    hub, name, flow_id, frag = _flow_meta(flow_src, by_src)

    live = [pid for pid in ids if pid in by_id]
    try:
        step = live.index(ids[at]) + 1
    except (ValueError, IndexError):
        step = at + 1
    i = step - 1

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
        # THE END IS A LINK, AND IT AIMS AT THE FORM. See the docstring.
        #
        # ⚠️ THE FORM FRAGMENT REPLACES THE FLOW FRAGMENT rather than joining it:
        # a URL has ONE fragment. The form is the right target here because this
        # is the last step -- there is no next page to orient, and the whole
        # point of arriving at the hub from the end is to submit.
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
        + _where(name, hub, here, frag,
                 "step " + str(step) + " of " + str(len(live)))
        + '<p class="dr-flow__move">' + " ".join(moves) + "</p></nav>"
    )


def _start_strip(flow_src, ids, page, by_id) -> str:
    """The strip on a page that DECLARES a chain. See the docstring.

    Returns "" when nothing in the chain resolved -- a Start button pointing
    nowhere is worse than no button, and nav.py has already reported that case
    by name.
    """
    live = [pid for pid in ids if pid in by_id]
    if not live:
        return ""

    here = _url(page)
    name = _title(flow_src, page)
    flow_id = str(_meta(flow_src).get("id") or "").strip()
    anchor = _anchor(flow_id)
    frag = "#" + anchor if anchor else ""
    first = by_id[live[0]]

    return (
        _open_tag(flow_id, name, "dr-flow--start")
        + _where(name, None, here, frag, str(len(live)) + " steps")
        + '<p class="dr-flow__move">'
        + _link(
            "dr-flow__next", first, here, frag,
            "Start: " + _title(_src(first), first),
        )
        + "</p></nav>"
    )


def _strips(page, files) -> str:
    src = _src(page)
    if not src:
        return ""

    chains = nav.declared(report=False)
    if not chains:
        return ""

    by_id, by_src = nav._built(files)
    pid = str(_meta(src).get("id") or "").strip()
    rendered = []

    # The page's OWN chain first, if it has one: on a program page the entrance
    # outranks any flow that page happens also to be a step in.
    if src in chains:
        start = _start_strip(src, chains[src], page, by_id)
        if start:
            rendered.append(start)

    if pid:
        for flow_src in sorted(chains):
            if flow_src == src:
                continue
            ids = chains[flow_src]
            if pid in ids:
                rendered.append(
                    _member_strip(
                        flow_src, ids, ids.index(pid), page, by_id, by_src
                    )
                )

    if not rendered:
        return ""
    if len(rendered) == 1:
        return '<div class="dr-flows">' + rendered[0] + "</div>"

    # ⚠️ THE FIRST STRIP IS THE BUILD-TIME DEFAULT, NOT "THE ACTIVE ONE". Which
    # flow is active is decided in the browser by the fragment (see the
    # docstring); this order is only what a reader with no fragment sees.
    others = len(rendered) - 1
    return (
        '<div class="dr-flows dr-flows--many">' + rendered[0]
        + '<details class="dr-flows__others"><summary>Also part of '
        + str(others) + " other program" + ("" if others == 1 else "s")
        + "</summary>" + "".join(rendered[1:]) + "</details></div>"
    )


def on_page_content(html, page, config, files):
    """Append this page's flow strips.

    Runs BEFORE hook 06 so the strips sit above the edit line rather than under
    it -- a reader's next step outranks a maintainer's.
    """
    strips = _strips(page, files)
    return html + strips if strips else html
