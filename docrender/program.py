"""Stage 05b -- the FLOW STRIP: which program a reader is in, and what is next.

WHY decisions here are the way they are: docrender/program-dl.md (D1 onward,
2026-09-28) and, for J19-J23 below, the older doc-render-engine Decision Log. The `chain:` vocabulary, prev/next and
FACES (`chain: "@id"`) belong to docrender/nav.py; the completion form is
docrender/forms.py. This module owns what a flow LOOKS like and, since
2026-09-28, WHICH ONE IS ACTIVE. Spec: specs/flow-context.md.

⚠️ NOT A CHANGELOG. It blew the 22,528 B read ceiling twice on dated narrative.
A post-mortem goes to the DL; the rule it produced goes to the call site.

=============================================================================
🔴 ONE NAVIGATION SURFACE PER PAGE
=============================================================================
A page in a flow gets strips AND `footer` appended to `page.meta['hide']`, so
Material's prev/next never draws beside them. The hand-typed `hide: footer` rule
(J19) is now automatic; pages that still carry it are harmless.

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
`data-dr-faces`; under a face the script swaps the program/finish links to the
face hub, rewrites `via=`, and on an `app` face adds `html.dr-app` -- so the app
binder stays an app all the way through, from one list.

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


def _card(cls, href, direction, title) -> str:
    """The button anatomy: a direction word over the destination title."""
    return (
        '<a class="' + cls + '" href="' + _esc(href) + '">'
        '<span class="dr-flow__dir">' + _esc(direction) + "</span>"
        '<span class="dr-flow__title">' + _esc(title) + "</span></a>"
    )


def _where(name, hub, here, via, detail) -> str:
    if hub is not None:
        who = (
            '<a class="dr-flow__program" href="' + _esc(_href(hub, here, via))
            + '">' + _esc(name) + "</a>"
        )
    else:
        who = '<span class="dr-flow__program">' + _esc(name) + "</span>"
    step = (' <span class="dr-flow__step">' + _esc(detail) + "</span>") if detail else ""
    return '<p class="dr-flow__where">' + who + step + "</p>"


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
    detail = "" if len(live) < 2 else "step " + str(i + 1) + " of " + str(len(live))

    moves = []
    if i > 0:
        prev = by_id[live[i - 1]]
        moves.append(_card("dr-flow__prev", _href(prev, here, fid), "\u2190 Previous", _title(_src(prev), prev)))
    if i + 1 < len(live):
        nxt = by_id[live[i + 1]]
        moves.append(_card("dr-flow__next", _href(nxt, here, fid), "Next \u2192", _title(_src(nxt), nxt)))
    elif hub is not None:
        # THE END AIMS AT THE FORM: landing on it is the point (J20).
        slot = forms.first_slot(_meta(flow_src))
        frag = ("#" + forms.slot_anchor(slot)) if slot else ""
        moves.append(_card("dr-flow__end", _href(hub, here, fid, frag), "Finish \u2713", name))
    else:
        moves.append('<span class="dr-flow__end dr-flow__end--dead">End of this program</span>')

    return (
        _open(fid, name, "", faces) + _where(name, hub, here, fid, detail)
        + '<p class="dr-flow__move">' + "".join(moves) + "</p></nav>"
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
    detail = str(len(live)) + (" step" if len(live) == 1 else " steps")
    return (
        _open(fid, name, "dr-flow--start") + _where(name, None, here, fid, detail)
        + '<p class="dr-flow__move">'
        + _card("dr-flow__next", _href(first, here, fid), "Start \u2192", _title(_src(first), first))
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
    "a=n.querySelectorAll('.dr-flow__program,.dr-flow__end');"
    "for(j=0;j<a.length;j++){if(a[j].tagName==='A')a[j].href=x[v].u;"
    "if(/program/.test(a[j].className))a[j].textContent=x[v].n;"
    "else{var t=a[j].querySelector('.dr-flow__title');if(t)t.textContent=x[v].n}}}"
    "a=w.querySelectorAll('.dr-flows__part a[data-via=\"'+f+'\"]');for(j=0;j<a.length;j++)a[j].className+=' is-via'}}"
    "if(!hit&&first){hit=first;a=w.querySelectorAll('.dr-flows__part a[data-via=\"'+first.getAttribute('data-dr-flow')+'\"]');"
    "for(j=0;j<a.length;j++)a[j].className+=' is-via'}"
    "if(hit)hit.className+=' is-via'}catch(e){}})();"
)

_CSS = """
html.dr-flowjs .dr-flows .dr-flow:not(.dr-flow--start):not(.is-via){display:none}
.dr-flows{margin:2.5rem 0 0;padding-top:1.2rem;border-top:1px solid var(--dr-border,var(--md-default-fg-color--lightest))}
.dr-flow+.dr-flow{margin-top:1.1rem;padding-top:1.1rem;border-top:1px dashed var(--dr-border,var(--md-default-fg-color--lightest))}
html.dr-flowjs .dr-flow.is-via{border-top:0;padding-top:0;margin-top:0}
html.dr-flowjs .dr-flow--start~.dr-flow.is-via{margin-top:1.1rem;padding-top:1.1rem;border-top:1px dashed var(--dr-border,var(--md-default-fg-color--lightest))}
.dr-flow__where{margin:0 0 .6rem;font-size:.72rem;line-height:1.4;letter-spacing:.02em;color:var(--md-default-fg-color--light)}
.md-typeset .dr-flow__program{font-weight:700;color:var(--md-default-fg-color--light)}
.md-typeset a.dr-flow__program:hover{color:var(--dr-accent,var(--md-typeset-a-color))}
.dr-flow__step{display:inline-block;margin-left:.45rem;padding:.05rem .4rem;border-radius:.6rem;background:var(--dr-surface-3,var(--md-code-bg-color));font-size:.66rem;font-weight:600;white-space:nowrap}
.md-typeset .dr-flow__move{display:flex;gap:.6rem;margin:0}
.md-typeset .dr-flow__move>*{flex:1 1 0;min-width:0;display:flex;flex-direction:column;justify-content:center;min-height:2.9rem;padding:.5rem .85rem;border:1px solid var(--dr-border,var(--md-default-fg-color--lighter));border-radius:.4rem;line-height:1.25;text-decoration:none;color:var(--md-default-fg-color)}
.md-typeset .dr-flow__dir{font-size:.64rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;opacity:.8}
.md-typeset .dr-flow__title{font-size:.8rem;font-weight:600;overflow-wrap:anywhere}
.md-typeset .dr-flow__next,.md-typeset .dr-flow__end{text-align:right}
.md-typeset .dr-flow__prev{background:transparent;color:var(--md-default-fg-color--light)}
.md-typeset .dr-flow__prev:hover{border-color:var(--dr-accent,var(--md-typeset-a-color));color:var(--dr-accent,var(--md-typeset-a-color))}
.md-typeset .dr-flow__next{border-color:var(--dr-accent,var(--md-accent-fg-color));background:var(--dr-accent,var(--md-accent-fg-color));color:var(--dr-on-accent,var(--md-accent-bg-color,#fff))}
.md-typeset .dr-flow__next:hover{filter:brightness(1.1);color:var(--dr-on-accent,var(--md-accent-bg-color,#fff))}
.md-typeset .dr-flow__end{border-color:var(--dr-good,#2e9d5b);color:var(--dr-good,#2e9d5b);background:transparent}
.md-typeset a.dr-flow__end:hover{background:var(--dr-good,#2e9d5b);color:var(--dr-on-accent,#fff)}
.md-typeset .dr-flow--start .dr-flow__next{text-align:center}
.md-typeset .dr-flow__end--dead{opacity:.6;text-align:center}
.dr-flows__part{display:none;margin:.9rem 0 0;font-size:.72rem;color:var(--md-default-fg-color--light)}
html.dr-flowjs .dr-flows--many .dr-flows__part{display:block}
.md-typeset .dr-flows__part a{margin-left:.4rem;font-weight:600}
.md-typeset .dr-flows__part a.is-via{display:none}
@media screen and (max-width:599px){.md-typeset .dr-flow__move{flex-direction:column-reverse}.md-typeset .dr-flow__move>*{text-align:left}}
"""


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
    goes FIRST so `html.dr-app` lands before the content paints.
    """
    head, foot = _strips(page, files)
    if not foot:
        return html
    _hide_footer(page)
    return head + html + foot
