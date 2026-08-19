"""Stage 05b -- the FLOW STRIP, and the embedded completion FORM.

WHY decisions here are the way they are: the doc-render-engine Decision Log.
The `chain:` vocabulary and the prev/next wiring belong to docrender/nav.py;
this module owns what a reader SEES of a flow, and the one element that lets a
program be completed without leaving the page.

=============================================================================
🔴 WHY A STRIP EXISTS AT ALL: prev/next HAS ONE SLOT AND A PAGE HAS MANY FLOWS
=============================================================================
`chain:` (2026-08-19) decoupled the reading order from the sidebar, and within
the hour it hit its own ceiling. Michael: *"I could define workflows that go
through specific pages, even if those workflows contain some of the same
pages."*

That is not a bigger chain. A MkDocs page has exactly ONE `previous_page` and
ONE `next_page`. Two programs walking through Housekeeping need it to have two
different "next" values, and which one is right depends on HOW THE READER
ARRIVED -- a per-request fact. This is a static site generator. There is no
request.

⚑ SO THE ANSWER IS NOT TO MAKE THE SLOT SMARTER, IT IS TO STOP COMPETING FOR
IT. The strip is ADDITIVE: a page in three programs renders three strips and
nothing overlaps, because no strip owns anything another one wants. nav.py keeps
prev/next as the single default order and the first-declared flow keeps the
buttons; everything else is a strip. ⭐ A CONSTRAINT YOU CANNOT REMOVE IS
SOMETIMES A CONSTRAINT YOU SHOULD STOP ROUTING THROUGH.

=============================================================================
⭐ THE STRIP'S JOB IS ORIENTATION, NOT NAVIGATION
=============================================================================
This is the design decision that shapes the markup, and it came from Michael's
own question -- *"I don't even know how this sort of thing would realistically
feel from a user perspective"* -- which was the right thing to be suspicious of.

A reader never browses to a policy. They are HANDED a program ("complete General
Safety for All"), land on the program page, and walk nine policies that live in
another folder and belong to nobody. The pages are BORROWED. So a bare
`← Housekeeping | Fire →` would be useless: it says what the sidebar would say,
and a reader three pages deep would not know which program they are inside or
how much of it is left.

    General Safety for All · step 4 of 9
    ← Proper Attire            Emergency Contacts →

The PROGRAM NAME is the payload. The arrows are a convenience.

⭐ AND MULTIPLE STRIPS ARE THE TRUTH BECOMING VISIBLE, not clutter: *this policy
is step 4 of General Safety and step 2 of MEWP Training, and reading it once
satisfies both.* uritp-safety expresses that today with a hand-typed "Part of X"
line on every policy -- one direction, no position, no count. This is that line,
derived, with the position added.

=============================================================================
⚠️ THE CAP, AND THE HALF OF IT A STATIC SITE CANNOT DO
=============================================================================
Michael asked for only the ACTIVE workflow visible, with the rest behind an
icon. The cap is real and it is here: the first flow renders open, the rest sit
inside a `<details>` -- which collapses with NO stylesheet and NO script, and
prints in the open state that print-flow.css already forces.

🔴 "ACTIVE" IS THE PART THAT NEEDS STATE, AND HE HAD ALREADY SOLVED IT WITHOUT
SAYING SO. His own completion form URL carries `?Program_ID=ITPSAFE-1225`.
State in the URL. So every link in a strip carries `?flow=<program id>`, and
walking a program keeps you in it -- shareable, bookmarkable, no server.

🚫 WHAT IS DELIBERATELY NOT BUILT: PROMOTING A FLOW TO PRIMARY FROM THAT PARAM.
It needs a script, and a script means the footer says one thing before it runs
and another after. More importantly there is no correct answer for a BARE url --
somebody who bookmarked Housekeeping, or arrived from the sidebar, is in NO
flow, and guessing one tells a reader they are in MEWP training when they are
not. So: no param = every flow shown, none claimed, position stated as
membership. Param = that flow is opened. The distinction maps to how people
actually arrive -- handed a program, or looking something up.

=============================================================================
⭐ `forms:` -- THE COMPLETION ARTIFACT, INSIDE THE PAGE
=============================================================================
Michael, 2026-08-19: *"can i embed an actual clickup form as content in the
bottom of these pages... so that users dont have to leave the page"* and then,
on where it should be declared: *"love that i can define in frontmatter, well
outside of the actual body content."*

    forms:
      completion:
        src: https://forms.clickup.com/36074068/f/...?Program_ID=ITPSAFE-1225
        text: General Safety completion form

    !!! form "completion"

🚫 THE CONTENT REPO NEVER HOLDS THE IFRAME. An `<iframe>` and a CDN `<script>`
are machinery, and machinery is the one thing the content tree may not contain.
The page NAMES a form; the engine builds the element. Exactly the split that
`data:` slots and the `links:` registry already use, and the reason the block
directive is `!!! form` rather than pasted HTML.

🔴 `height="100%"` COLLAPSES TO NOTHING WITHOUT THEIR SCRIPT, AND THAT IS THE
SHARP EDGE IN THE EMBED CODE CLICKUP HANDS YOU. `clickup-dynamic-height` plus
`forms-embed/v1.js` is what gives the frame a real height. If that CDN is slow,
blocked by an extension, or the asset ever moves, the form is not BROKEN, it is
INVISIBLE -- a blank gap on a compliance page, with nothing in the build report,
because an external script's runtime behaviour cannot be observed at build time.
So a `min-height` floor is written onto the frame: a script failure degrades to
a scrollable form rather than a hole.

⚠️ AND THE FALLBACK LINK IS ALWAYS RENDERED, NOT ONLY FOR PRINT. An iframe
prints as a blank rectangle, and this engine has a print identity spec, so a
printed program packet would carry a hole where the completion form belongs. The
visible link doubles as the answer to "the form did not load."

🔴 THE PREFILL PARAM IS THE RECORD. `?Program_ID=` is what makes a submission
attributable. A form embedded without it collects rows nobody can match to a
program, which is a compliance failure that looks like a working page. Reported,
not corrected -- the engine cannot know which id is right.

⚠️ UNVERIFIABLE AT BUILD TIME, the same reduction `urllinks.py` states at the
top of its own file: the host and scheme are checked, and nothing here can prove
the form is active, public, or still exists.

=============================================================================
⚠️ NO STYLESHEET YET, AND THAT IS A DECISION RATHER THAN AN OMISSION
=============================================================================
Every class here is semantic and unstyled. Registering a sheet means editing
`assets.py`'s asset groups, and `hand_written_css()` is the SINGLE SOURCE that
keeps tokenaudit from going stale -- a sheet added anywhere else is a sheet the
audit cannot see, which is the exact defect that file's docstring celebrates
killing. 🚫 So no inline `<style>` and no second asset registrar were added
here. The markup is `<nav>`, `<details>` and `<p>`: it reads correctly,
collapses correctly and prints correctly with no CSS at all, and the sheet is a
follow-up that goes through `assets.py` properly.
"""

from __future__ import annotations

import re

from . import nav, state
from .util import relative_url, sub_outside_code

#: `!!! form "slot"` on its own line. Deliberately the same shape as the
#: `!!! data "slot"` directive datatable.py already owns, so the body vocabulary
#: stays one pattern rather than two spellings of one idea.
_FORM = re.compile(r'(?m)^[ \t]*!!![ \t]+form[ \t]+"([^"\n]+)"[ \t]*$')

#: The one host an embedded form may come from. A narrow allow-list rather than
#: a scheme check: this element executes a third-party script in the reader's
#: browser on a page that carries a compliance instruction, so "any https URL"
#: is not a good enough answer.
_FORM_HOST = "https://forms.clickup.com/"

#: ClickUp's own embed helper. It is what `clickup-dynamic-height` needs.
_FORM_SCRIPT = "https://app-cdn.clickup.com/assets/js/forms-embed/v1.js"

#: The floor that keeps a script failure from rendering an invisible form.
_FORM_MIN_HEIGHT = "40rem"


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


# ---------------------------------------------------------------- flow strips


def _flows_for(src, files):
    """Every flow this page is a step in: (flow_src, ids, position).

    Reads `nav.declared(report=False)` rather than re-parsing `chain:`. One
    vocabulary, one parser -- see that function's docstring for why it is public.
    """
    out = []
    for flow_src, ids in sorted(nav.declared(report=False).items()):
        pid = str(_meta(src).get("id") or "").strip()
        if pid and pid in ids:
            out.append((flow_src, ids, ids.index(pid)))
    return out


def _strip(flow_src, ids, at, page, by_id, by_src) -> str:
    """One flow's strip, as HTML.

    ⚠️ `at` IS THE POSITION IN THE DECLARED LIST, and the printed count is the
    length of the RESOLVED list, so a chain naming a page that does not exist
    reports "step 4 of 8" rather than claiming a step that was skipped. The two
    numbers come from different lists on purpose.
    """
    here = getattr(page.file, "url", "")
    hub = by_src.get(flow_src)
    flow_id = str(_meta(flow_src).get("id") or "").strip()
    flow_name = _title(flow_src, hub) if hub is not None else flow_src
    param = "?flow=" + flow_id if flow_id else ""

    live = [pid for pid in ids if pid in by_id]
    try:
        step = live.index(ids[at]) + 1
    except ValueError:
        step = at + 1

    bits = ['<nav class="dr-flow"']
    if flow_id:
        bits.append(' data-dr-flow="' + _esc(flow_id) + '"')
    bits.append(' aria-label="' + _esc(flow_name) + ' · reading order">')

    where = ""
    if hub is not None:
        where = (
            '<a class="dr-flow__program" href="'
            + _esc(relative_url(getattr(hub.file, "url", ""), here) + param)
            + '">' + _esc(flow_name) + "</a>"
        )
    else:
        where = '<span class="dr-flow__program">' + _esc(flow_name) + "</span>"
    bits.append(
        '<p class="dr-flow__where">' + where
        + ' <span class="dr-flow__step">step ' + str(step) + " of "
        + str(len(live)) + "</span></p>"
    )

    moves = []
    at_live = step - 1
    if at_live > 0:
        prev = by_id[live[at_live - 1]]
        moves.append(
            '<a class="dr-flow__prev" href="'
            + _esc(relative_url(getattr(prev.file, "url", ""), here) + param)
            + '">← '
            + _esc(_title(getattr(prev.file, "src_uri", ""), prev)) + "</a>"
        )
    if at_live + 1 < len(live):
        nxt = by_id[live[at_live + 1]]
        moves.append(
            '<a class="dr-flow__next" href="'
            + _esc(relative_url(getattr(nxt.file, "url", ""), here) + param)
            + '">'
            + _esc(_title(getattr(nxt.file, "src_uri", ""), nxt)) + " →</a>"
        )
    else:
        # 🚫 An authored flow ENDS. Said in words rather than left as a missing
        # button, because a strip that simply stops looks like a broken one --
        # and on a program the end is the point at which somebody submits.
        moves.append('<span class="dr-flow__end">end of this program</span>')

    bits.append('<p class="dr-flow__move">' + " ".join(moves) + "</p></nav>")
    return "".join(bits)


def _strips(page, files) -> str:
    src = getattr(page.file, "src_uri", "")
    flows = _flows_for(src, files)
    if not flows:
        return ""

    by_id, by_src = nav._built(files)
    rendered = [_strip(f, ids, at, page, by_id, by_src) for f, ids, at in flows]

    if len(rendered) == 1:
        return '<div class="dr-flows">' + rendered[0] + "</div>"

    # THE CAP. First open, the rest behind one disclosure. `<details>` because
    # it collapses with no stylesheet and no script, and print-flow.css already
    # forces every `<details>` open on paper -- so a printed packet shows every
    # program this page belongs to, which is the right answer for a compliance
    # document and would have needed its own rule with any other mechanism.
    others = len(rendered) - 1
    return (
        '<div class="dr-flows dr-flows--many">'
        + rendered[0]
        + '<details class="dr-flows__others"><summary>Also part of '
        + str(others) + " other program" + ("" if others == 1 else "s")
        + "</summary>" + "".join(rendered[1:]) + "</details></div>"
    )


# ----------------------------------------------------------------- form slots


def _form_entry(src, slot):
    """One entry out of a page's `forms:` map, or None.

    Two spellings, matching the `links:` registry: a bare string is the src, a
    mapping carries `src:` and `text:`.
    """
    block = _meta(src).get("forms")
    if not isinstance(block, dict):
        return None
    raw = block.get(slot)
    if raw is None:
        return None
    if isinstance(raw, str):
        return (raw.strip(), "")
    if isinstance(raw, dict):
        return (str(raw.get("src", "")).strip(), str(raw.get("text", "")).strip())
    return ("", "")


def _form_html(src, slot) -> str:
    entry = _form_entry(src, slot)
    if entry is None:
        state.note(
            "dead_links",
            src + ': `!!! form "' + slot + '"` names a slot that is not in this '
            "page's `forms:` block. Nothing was embedded.",
        )
        return ""

    url, text = entry
    if not url.startswith(_FORM_HOST):
        state.note(
            "dead_links",
            src + ": `forms: " + slot + "` must be a " + _FORM_HOST
            + " address (found '" + url + "'). NOT embedded -- this element runs "
            "a third-party script in the reader's browser, so the host is an "
            "allow-list rather than a scheme check.",
        )
        return ""

    if "Program_ID=" not in url:
        state.note(
            "notes",
            src + ": `forms: " + slot + "` carries no `Program_ID=` parameter. "
            "It will embed and submit, and the submissions will not be "
            "attributable to this program -- a compliance gap that looks like a "
            "working page.",
        )

    label = text or "Open this form in a new tab"
    return (
        '<div class="dr-form" data-dr-form="' + _esc(slot) + '">'
        '<iframe class="clickup-embed clickup-dynamic-height" src="' + _esc(url)
        + '" onwheel="" width="100%" height="100%" title="' + _esc(label)
        + '" style="background: transparent; border: 1px solid #ccc; '
        "min-height: " + _FORM_MIN_HEIGHT + ';"></iframe>'
        '<p class="dr-form__fallback">'
        '<a href="' + _esc(url) + '">' + _esc(label) + "</a>"
        "</p></div>"
    )


def on_page_markdown(markdown, page, config, files):
    """Replace each `!!! form "slot"` with the embed, and load the helper once.

    ⚠️ `sub_outside_code` IS NOT OPTIONAL HERE. The authoring page that
    documents this directive contains the directive, and util's own docstring
    records the first time that bit this engine: the page teaching
    `[Main Stage](@main-stage)` shipped with the resolved URL inside its own code
    fence.

    ⭐ THE HELPER SCRIPT IS APPENDED ONCE PER PAGE, NOT ONCE PER FORM. Two forms
    on a page would otherwise fetch and execute the same CDN asset twice.
    """
    src = getattr(page.file, "src_uri", "")
    if "!!!" not in markdown:
        return markdown

    hits = []

    def swap(match):
        html = _form_html(src, match.group(1).strip())
        if not html:
            return ""
        hits.append(1)
        return "\n\n" + html + "\n\n"

    out = sub_outside_code(_FORM, swap, markdown)
    if hits:
        out += (
            '\n\n<script async src="' + _FORM_SCRIPT + '"></script>\n'
        )
    return out


def on_page_content(html, page, config, files):
    """Append this page's flow strips.

    Runs BEFORE hook 06 so the strips sit above the edit line rather than under
    it -- a reader's next step outranks a maintainer's.
    """
    strips = _strips(page, files)
    return html + strips if strips else html
