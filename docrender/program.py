"""Stage 05b -- the FLOW STRIP: which program a reader is in, and what is next.

WHY decisions here are the way they are: docrender/program-dl.md (D1 onward,
2026-09-28) and, for J19-J23 below, the older doc-render-engine Decision Log. The `chain:` vocabulary, prev/next and
FACES (`chain: "@id"`) belong to docrender/nav.py; the completion form is
docrender/forms.py. This module owns what a flow LOOKS like and, since
2026-09-28, WHICH ONE IS ACTIVE. Spec: specs/flow-context.md.

⚠️ NOT A CHANGELOG. It blew the 22,528 B read ceiling twice on dated narrative.
A post-mortem goes to the DL; the rule it produced goes to the call site.

=============================================================================
🔴 TWO SURFACES, TWO JOBS: THE PILL IS FOR CLICKING, THE STRIP IS FOR READING
=============================================================================
(program-dl D2, 2026-10-02, reverses D1's one-surface rule.) Every strip carries
a PILL: `‹ Last` / `Next ›`, position: fixed under the top-right toolbar, so the
Next button sits on the SAME PIXEL on every page and a reader can click through a
program without moving the mouse. A footer strip moves with article length; that
was the defect. The strip at the foot stays as the reference (program, step,
titles, "Also part of") but is one tight row.

  * Next is the RIGHTMOST button and the pill is right-anchored with fixed-width
    buttons, so Next/Finish/Start never shift. A missing Last renders greyed,
    never removed: removing it would not move Next, but it would make the pill
    change shape under the cursor.
  * Detail lives in the hover title + aria-label, not on the button.
  * Under 600px the pill docks BOTTOM-right instead: the thumb zone, and a
    top pill sat on the page title. Still fixed, still the same spot.
  * The pill sits INSIDE its strip, so the strip selection below hides it for
    free. No script: only the first strip's pill shows. A member pill outranks a
    start pill (`:has`), so a hub that is also a step shows one pill.
  * Material's `navigation.footer` is still suppressed: `footer` is appended to
    `page.meta['hide']`, J19's hand-typed rule made automatic.

=============================================================================
⭐ THE SERVER RENDERS EVERY STRIP; THE BROWSER PICKS ONE (program-dl D1)
=============================================================================
A page has one prev/next slot and many flows, and which is right depends on how
the reader ARRIVED. The `:target` promotion (promote.py, deleted) died on the
first in-page anchor click and did nothing for sidebar arrivals. Now:

  * every strip link carries `?via=<flow id>`;
  * a ~1KB inline script reads `?via=`, else the page's own start flow, else
    sessionStorage `dr.via`, and marks the matching strip `is-via`;
  * CSS hides every other member strip. Start strips always show;
  * no match: the first strip by `order:` shows, plus an "Also part of" line
    whose links re-open THIS page under another flow;
  * no script: every strip shows, which is the old page minus the cap.

⭐ FACES. A `chain: "@target"` page walks the target's list without owning its
buttons. Member pages render ONE strip for the target, carrying its faces as
`data-dr-faces`; under a face the script swaps the program/finish links (pill
included) to the face hub, rewrites `via=`, and on an `app` face adds
`html.dr-app` -- so the app binder stays an app all the way through, from one list.
⚠️ Hover titles keep the TARGET's name under a face. Cosmetic, known.

⚠️ The chrome.CSS block is inlined ONLY on pages whose flows have an app face,
and is inert until the script sets the class.
"""

from __future__ import annotations

import json
import re

from . import chrome, forms, nav, state
from .util import relative_url

#: What a page with no `order:` sorts as. Matches `objects.py:_child_list`.
_NO_ORDER = 10_000
_SLUG = re.compile(r"[^A-Za-z0-9_-]+")


def _esc(text) -> str:
    return (
        str(text).replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    )


def _meta(src) -> dict:
    return state.BY_SRC.get(src, {}) or {}


def _id(src) -> str:
    return str(_meta(src).get("id") or "").strip()


def _title(src, page) -> str:
    return str(_meta(src).get("title") or getattr(page, "title", "") or src)


def _url(page) -> str:
    return getattr(getattr(page, "file", None), "url", "")


def _src(page) -> str:
    return getattr(getattr(page, "file", None), "src_uri", "")


def _order(src) -> tuple:
    """Declared `order:`, then path, so the default is chosen, never a filename."""
    raw = _meta(src).get("order")
    return (raw if isinstance(raw, int) else _NO_ORDER, src)


def _href(page, here, via, frag="") -> str:
    q = ("?via=" + via) if via else ""
    return relative_url(_url(page), here) + q + frag


def _link(cls, href, text, tip) -> str:
    """One tight foot link. The full sentence rides in the hover title."""
    return (
        '<a class="' + cls + '" href="' + _esc(href) + '" title="' + _esc(tip) + '">'
        + text + "</a>"
    )


def _btn(cls, href, label, tip) -> str:
    """One pill button. No href = greyed placeholder that keeps the shape."""
    if href is None:
        return '<span class="dr-pill__btn ' + cls + ' is-off" aria-hidden="true">' + label + "</span>"
    return (
        '<a class="dr-pill__btn ' + cls + '" href="' + _esc(href) + '" title="'
        + _esc(tip) + '" aria-label="' + _esc(tip) + '">' + label + "</a>"
    )


def _pill(name, last, nxt) -> str:
    return (
        '<span class="dr-flow__pill" role="group" aria-label="' + _esc(name)
        + ' \u00b7 quick navigation">' + last + nxt + "</span>"
    )


_LAST = "\u2039 Last"
_NEXT = "Next \u203a"


def _where(name, hub, here, via, detail) -> str:
    if hub is not None:
        who = (
            '<a class="dr-flow__program" href="' + _esc(_href(hub, here, via))
            + '">' + _esc(name) + "</a>"
        )
    else:
        who = '<span class="dr-flow__program">' + _esc(name) + "</span>"
    step = (' <span class="dr-flow__step">' + _esc(detail) + "</span>") if detail else ""
    return '<span class="dr-flow__where">' + who + step + "</span>"


def _open(flow_id, name, extra="", faces=None) -> str:
    bits = ['<nav class="dr-flow' + (" " + extra if extra else "") + '"']
    if flow_id:
        bits.append(' id="flow-' + _esc(_SLUG.sub("-", flow_id)) + '"')
        bits.append(' data-dr-flow="' + _esc(flow_id) + '"')
    if faces:
        bits.append(" data-dr-faces='" + _esc(json.dumps(faces, separators=(",", ":"))).replace("'", "&#39;") + "'")
    bits.append(' aria-label="' + _esc(name) + ' \u00b7 reading order">')
    return "".join(bits)


def _faces_for(flow_src, faces_of, by_src, here) -> dict:
    """{alias id: {u: hub url?via=alias, n: title, app: 0|1}} for one flow."""
    out = {}
    for alias_src in faces_of.get(flow_src, ()):
        hub = by_src.get(alias_src)
        aid = _id(alias_src)
        if hub is None or not aid:
            continue
        app = str(_meta(alias_src).get("chrome") or "").strip().lower() == "app"
        out[aid] = {"u": _href(hub, here, aid), "n": _title(alias_src, hub), "app": 1 if app else 0}
    return out


_GAP = '<span class="dr-flow__gap"></span>'


def _member(flow_src, ids, at, page, by_id, by_src, faces) -> str:
    """One strip on a page that IS a step. Lone step: no count, keep Finish (J23)."""
    here = _url(page)
    hub = by_src.get(flow_src)
    fid = _id(flow_src)
    name = _title(flow_src, hub) if hub is not None else flow_src
    live = [p for p in ids if p in by_id]
    try:
        i = live.index(ids[at])
    except (ValueError, IndexError):
        i = at
    n = len(live)
    detail = "" if n < 2 else str(i + 1) + "/" + str(n)

    def tip(word, title, step):
        return word + ": " + title + " (" + name + (", step " + str(step) + " of " + str(n) if n > 1 else "") + ")"

    if i > 0:
        prev = by_id[live[i - 1]]
        ph, pt = _href(prev, here, fid), _title(_src(prev), prev)
        foot_prev = _link("dr-flow__prev", ph, "\u2190 " + _esc(pt), tip("Last", pt, i))
        pill_prev = _btn("dr-pill__prev", ph, _LAST, tip("Last", pt, i))
    else:
        foot_prev, pill_prev = _GAP, _btn("dr-pill__prev", None, _LAST, "")

    if i + 1 < n:
        nxt = by_id[live[i + 1]]
        nh, nt = _href(nxt, here, fid), _title(_src(nxt), nxt)
        foot_next = _link("dr-flow__next", nh, _esc(nt) + " \u2192", tip("Next", nt, i + 2))
        pill_next = _btn("dr-pill__next", nh, _NEXT, tip("Next", nt, i + 2))
    elif hub is not None:
        # THE END AIMS AT THE FORM: landing on it is the point (J20).
        slot = forms.first_slot(_meta(flow_src))
        frag = ("#" + forms.slot_anchor(slot)) if slot else ""
        eh = _href(hub, here, fid, frag)
        foot_next = _link(
            "dr-flow__end", eh,
            'Finish <span class="dr-flow__title">' + _esc(name) + "</span> \u2713",
            "Finish: back to " + name,
        )
        pill_next = _btn("dr-pill__fin", eh, "Finish \u2713", "Finish: back to " + name)
    else:
        foot_next = '<span class="dr-flow__end dr-flow__end--dead">End</span>'
        pill_next = _btn("dr-pill__next", None, "End", "")

    return (
        _open(fid, name, "", faces) + _pill(name, pill_prev, pill_next)
        + '<p class="dr-flow__move">' + foot_prev + _where(name, hub, here, fid, detail)
        + foot_next + "</p></nav>"
    )


def _start(flow_src, ids, page, by_id) -> str:
    """The strip on a page that DECLARES a chain (J22). Nothing resolved: none."""
    live = [p for p in ids if p in by_id]
    if not live:
        return ""
    here = _url(page)
    fid = _id(flow_src)
    name = _title(flow_src, page)
    first = by_id[live[0]]
    fh, ft = _href(first, here, fid), _title(_src(first), first)
    detail = str(len(live)) + (" step" if len(live) == 1 else " steps")
    t = "Start: " + ft + " (" + name + ", " + detail + ")"
    return (
        _open(fid, name, "dr-flow--start")
        + _pill(name, _btn("dr-pill__prev", None, _LAST, ""), _btn("dr-pill__next", fh, "Start \u203a", t))
        + '<p class="dr-flow__move">' + _GAP + _where(name, None, here, fid, detail)
        + _link("dr-flow__next", fh, "Start: " + _esc(ft) + " \u2192", t)
        + "</p></nav>"
    )


# The browser half. ES5, no dependencies, fails open (no class = every strip shows).
_HEAD_JS = (
    "(function(){try{var d=document.documentElement,F=%s,K='dr.via',c=[],v='',i,"
    "m=/[?&]via=([^&#]*)/.exec(location.search);if(m)c.push(decodeURIComponent(m[1]));"
    "if(F.own)c.push(F.own);try{c.push(sessionStorage.getItem(K)||'')}catch(e){}"
    "for(i=0;i<c.length;i++){if(c[i]&&(F.flows.indexOf(c[i])>-1||F.faces[c[i]]||c[i]===F.own)){v=c[i];break}}"
    "d.className+=' dr-flowjs';if(v){d.setAttribute('data-dr-via',v);"
    "try{sessionStorage.setItem(K,v)}catch(e){}if(F.faces[v]&&F.faces[v].app)d.className+=' dr-app'}"
    "else d.className+=' dr-flow-none'}catch(e){}})();"
)

_FOOT_JS = (
    "(function(){try{var d=document.documentElement,v=d.getAttribute('data-dr-via')||'',"
    "w=document.currentScript.parentNode,s=w.querySelectorAll('.dr-flow'),i,j,n,f,x,a,hit=null,first=null;"
    "for(i=0;i<s.length;i++){n=s[i];if(/dr-flow--start/.test(n.className))continue;if(!first)first=n;"
    "f=n.getAttribute('data-dr-flow');x=null;try{x=JSON.parse(n.getAttribute('data-dr-faces')||'null')}catch(e){}"
    "if(v&&(f===v||(x&&x[v]))){hit=n;if(f!==v){a=n.querySelectorAll('a');"
    "for(j=0;j<a.length;j++)a[j].href=a[j].href.replace('via='+f,'via='+v);"
    "a=n.querySelectorAll('.dr-flow__program,.dr-flow__end,.dr-pill__fin');"
    "for(j=0;j<a.length;j++){if(a[j].tagName==='A')a[j].href=x[v].u;"
    "if(/program/.test(a[j].className))a[j].textContent=x[v].n;"
    "else{var t=a[j].querySelector('.dr-flow__title');if(t)t.textContent=x[v].n}}}"
    "a=w.querySelectorAll('.dr-flows__part a[data-via=\"'+f+'\"]');for(j=0;j<a.length;j++)a[j].className+=' is-via'}}"
    "if(!hit&&first){hit=first;a=w.querySelectorAll('.dr-flows__part a[data-via=\"'+first.getAttribute('data-dr-flow')+'\"]');"
    "for(j=0;j<a.length;j++)a[j].className+=' is-via'}"
    "if(hit)hit.className+=' is-via'}catch(e){}})();"
)

_RULE = "var(--dr-border,var(--md-default-fg-color--lightest))"
_CSS = """
html.dr-flowjs .dr-flows .dr-flow:not(.dr-flow--start):not(.is-via){display:none}
.dr-flows{margin:2rem 0 0;padding-top:.7rem;border-top:1px solid RULE}
.dr-flow+.dr-flow{margin-top:.55rem;padding-top:.55rem;border-top:1px dashed RULE}
html.dr-flowjs .dr-flow.is-via{border-top:0;padding-top:0;margin-top:0}
html.dr-flowjs .dr-flow--start~.dr-flow.is-via{margin-top:.55rem;padding-top:.55rem;border-top:1px dashed RULE}
.md-typeset .dr-flow__move{display:grid;grid-template-columns:minmax(0,1fr) auto minmax(0,1fr);align-items:center;gap:.6rem;margin:0;font-size:.7rem;line-height:1.3}
.md-typeset .dr-flow__move>a{display:block;min-width:0;max-width:100%;padding:.28rem .55rem;border:1px solid var(--dr-border,var(--md-default-fg-color--lighter));border-radius:.3rem;color:var(--md-default-fg-color--light);font-weight:600;text-decoration:none;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.md-typeset .dr-flow__prev{justify-self:start}
.md-typeset .dr-flow__next,.md-typeset .dr-flow__end{justify-self:end;text-align:right}
.md-typeset .dr-flow__next{border-color:var(--dr-accent,var(--md-accent-fg-color));color:var(--md-default-fg-color)}
.md-typeset .dr-flow__move>a:hover{border-color:var(--dr-accent,var(--md-accent-fg-color));color:var(--md-default-fg-color)}
.md-typeset .dr-flow__end{border-color:var(--dr-good,#2e9d5b);color:var(--md-default-fg-color)}
.md-typeset .dr-flow__move>a.dr-flow__end:hover{border-color:var(--dr-good,#2e9d5b);background:var(--dr-good,#2e9d5b);color:var(--dr-on-accent,#fff)}
.md-typeset .dr-flow__end--dead{justify-self:end;opacity:.6}
.dr-flow__where{justify-self:center;white-space:nowrap;font-size:.66rem;letter-spacing:.02em;color:var(--md-default-fg-color--light)}
.md-typeset .dr-flow__program{font-weight:700;color:var(--md-default-fg-color--light)}
.md-typeset a.dr-flow__program:hover{color:var(--dr-accent,var(--md-typeset-a-color))}
.dr-flow__step{margin-left:.35rem;font-variant-numeric:tabular-nums;opacity:.8}
.dr-flows__part{display:none;margin:.45rem 0 0;text-align:center;font-size:.64rem;color:var(--md-default-fg-color--light)}
html.dr-flowjs .dr-flows--many .dr-flows__part{display:block}
.md-typeset .dr-flows__part a{margin-left:.4rem;font-weight:600}
.md-typeset .dr-flows__part a.is-via{display:none}
@media screen and (max-width:599px){.md-typeset .dr-flow__move{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}.dr-flow__where{grid-column:1/-1;grid-row:1}}
.dr-flow__pill{position:fixed;top:3.4rem;right:.6rem;z-index:4;display:flex;gap:.25rem;padding:.25rem;border-radius:2rem;background:var(--dr-surface-2,var(--dr-surface-raised,var(--md-default-bg-color)));box-shadow:0 .1rem .5rem rgba(0,0,0,.3)}
.md-typeset .dr-pill__btn{display:inline-flex;align-items:center;justify-content:center;box-sizing:border-box;width:4.3rem;height:1.9rem;border:1px solid var(--dr-border,var(--md-default-fg-color--lighter));border-radius:1.6rem;background:transparent;color:var(--md-default-fg-color);font-size:.66rem;font-weight:700;letter-spacing:.03em;line-height:1;text-decoration:none;user-select:none}
.md-typeset a.dr-pill__btn:hover{border-color:var(--dr-accent,var(--md-accent-fg-color));color:var(--md-default-fg-color)}
.md-typeset .dr-pill__next:not(.is-off),.md-typeset a.dr-pill__next:hover{border-color:var(--dr-accent,var(--md-accent-fg-color));background:var(--dr-accent,var(--md-accent-fg-color));color:var(--dr-on-accent,var(--md-accent-bg-color,#fff))}
.md-typeset a.dr-pill__next:hover{filter:brightness(1.1)}
.md-typeset .dr-pill__fin,.md-typeset a.dr-pill__fin:hover{border-color:var(--dr-good,#2e9d5b);color:var(--dr-good,#2e9d5b)}
.md-typeset .dr-pill__btn.is-off{opacity:.35;cursor:default}
.md-typeset a.dr-pill__btn:focus-visible{outline:2px solid var(--dr-accent,var(--md-accent-fg-color));outline-offset:2px}
html:not(.dr-flowjs) .dr-flows .dr-flow~.dr-flow .dr-flow__pill{display:none}
html.dr-flowjs .dr-flows:has(.dr-flow.is-via) .dr-flow--start .dr-flow__pill{display:none}
@media screen and (max-width:599px){.dr-flow__pill{top:auto;bottom:.8rem;right:.8rem}.dr-flows{padding-bottom:3rem}}
@media print{.dr-flow__pill{display:none!important}}
""".replace("RULE", _RULE)


def _strips(page, files):
    """(head html, foot html) for this page, or ("", "")."""
    src = _src(page)
    chains = nav.declared(report=False) if src else {}
    if not chains:
        return "", ""
    faces_map = nav.aliases()
    faces_of: dict = {}
    for a, t in faces_map.items():
        faces_of.setdefault(t, []).append(a)

    by_id, by_src = nav._built(files)
    here = _url(page)
    pid = _id(src)
    starts, members, flows, part = [], [], [], []
    face_data: dict = {}
    app_face = False

    if src in chains:
        s = _start(src, chains[src], page, by_id)
        if s:
            starts.append(s)
    if pid:
        for flow_src in sorted(chains, key=_order):
            # A face is drawn by its target's strip, never as a strip of its own.
            if flow_src == src or flow_src in faces_map:
                continue
            ids = chains[flow_src]
            if pid not in ids:
                continue
            fid = _id(flow_src)
            fc = _faces_for(flow_src, faces_of, by_src, here)
            members.append(_member(flow_src, ids, ids.index(pid), page, by_id, by_src, fc))
            flows.append(fid)
            part.append(
                '<a data-via="' + _esc(fid) + '" href="?via=' + _esc(fid) + '">'
                + _esc(_title(flow_src, by_src.get(flow_src))) + "</a>"
            )
            for k, val in fc.items():
                face_data[k] = {"app": val["app"]}
                app_face = app_face or bool(val["app"])

    if not starts and not members:
        return "", ""

    own = _id(src) if starts else ""
    data = json.dumps({"flows": flows, "faces": face_data, "own": own}, separators=(",", ":"))
    head = (
        '<style class="dr-flowctx">' + _CSS + (chrome.CSS if app_face else "") + "</style>"
        + "<script>" + (_HEAD_JS % data.replace("</", "<\\/")) + "</script>"
    )
    many = len(members) > 1
    foot = (
        '<div class="dr-flows' + (" dr-flows--many" if many else "") + '">'
        + "".join(starts) + "".join(members)
        + ('<p class="dr-flows__part">Also part of:' + "".join(part) + "</p>" if many else "")
        + "<script>" + _FOOT_JS + "</script></div>"
    )
    return head, foot


def _hide_footer(page) -> None:
    """One navigation surface: Material reads `page.meta.hide` at template time."""
    meta = getattr(page, "meta", None)
    if meta is None:
        return
    hide = meta.get("hide") or []
    if isinstance(hide, str):
        hide = [hide]
    if "footer" not in hide:
        meta["hide"] = list(hide) + ["footer"]


def on_page_content(html, page, config, files):
    """Context script + style at the top, strips at the foot, footer hidden.

    Runs BEFORE hook 06 so the strips sit above the edit line. The head block
    goes FIRST so `html.dr-app` lands before the content paints. The pill is
    position: fixed, so its place in the DOM does not decide where it draws.
    """
    head, foot = _strips(page, files)
    if not foot:
        return html
    _hide_footer(page)
    return head + html + foot
