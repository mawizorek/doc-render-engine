"""Stage 05b -- THE PROGRAM PACKET: one document, printed once, cover first.

BUILD 10. Decisions: `specs/print-packet.md`. Arguments: `specs/print-packet-dl.md`.
The `chain:` vocabulary and its resolver belong to docrender/nav.py; the flow strip
belongs to docrender/program.py; the embedded form to docrender/forms.py. This
module owns ONE artifact: a generated page that holds a whole program.

=============================================================================
🔴 WHY THERE IS NO LOOP, AND WHY THAT IS THE ARCHITECTURE
=============================================================================
The ask was a button that visits each policy, prints it, and stacks the results.
A browser cannot do any of that: `window.print()` prints the current document
only, a print job is user-mediated, and the PDF never enters JavaScript. Printing
an iframe prints that document alone -- the same wall wearing a frame.

⚑ THE ASK DESCRIBED A READER DOING IT BY HAND. THE ENGINE IS NOT A READER -- it
already holds every page of the chain in one process. So the aggregation happens
at BUILD time and the reader gets ONE page, which they print with an ordinary
Ctrl+P. Michael, 2026-08-30: *"the print should run just like a manual print
command on the page."* It IS a manual print command on a page.

⭐ THAT IS WHY THE PACKET IS A REAL MkDocs PAGE AND NOT A HAND-BUILT FILE. Being
an ordinary page is what buys every print sheet, the chrome-off list and the
corner stamp for free, with no second print path to keep in step. 🚫 A second
renderer (WeasyPrint et al) is REFUSED for the same reason and separately by
`requirements.txt`'s dependency doctrine -- see the spec §5.

=============================================================================
⚠️ FOUR EVENTS, AND EACH ONE IS THE ONLY PLACE ITS JOB CAN HAPPEN
=============================================================================
    on_files       mint the page. Files are fixed after this.
    on_nav         capture the PLAN. `files` is in hand and every File already
                   knows its own url and dest path, so nothing has to be
                   derived from a url later. Also prunes the packet from the
                   sidebar.
    on_page_markdown  `!!! export` -> the button, where an author placed it.
    on_post_build  assemble. Every member's HTML is FINISHED and on disk; at any
                   earlier event some of them are not rendered yet, and page
                   render order is not ours to depend on.

🔴 THE PLAN IS CAPTURED AT on_nav AND NEVER RE-DERIVED. `state.py`'s admission
price is that a shared value needs a writer and a reader in DIFFERENT hooks --
this one has both inside this module, so it stays here rather than in `state`.

=============================================================================
🔴 ANCHOR COLLISION IS THE ACTUAL WORK. THE STACKING IS THE EASY HALF
=============================================================================
Nine pages in one document is nine sets of heading ids in ONE id namespace. Five
policies with an `## Overview` give five `#overview` anchors and every link to
any of them lands on the first.

⚠️ IT HALF-WORKS, WHICH IS WHY IT IS THE DANGEROUS SHAPE: entry one of the cover
is correct and entries two onward are silently wrong. Nothing reports it and a
PDF has no console. So every id gets its section prefix (`overview` -> `s3-overview`)
and every href is CLASSIFIED, never blanket-rewritten:

    #frag                      -> #sN-frag        stayed inside its own section
    a path INSIDE the packet   -> #sM[-frag]      the internal jump
    a path OUTSIDE the packet  -> ABSOLUTE url    🔴 see below
    absolute / mailto / tel    -> untouched
    anything unresolvable      -> untouched AND REPORTED

🔴 THE OUTSIDE-THE-PACKET ROW IS THE SILENT ONE. A relative href surviving into a
PDF is not a visibly broken link -- it opens nothing, or resolves against whatever
folder the file was saved in. A distributed safety packet whose citations do
nothing is a compliance failure that looks like a working document, which is the
sentence `objects/program.yml` already writes about a form with no `?Program_ID=`.

⚠️ `site_url` IS THE ONE INPUT THIS MODULE CANNOT VERIFY, and BUILD 6 §1 flagged
the same source: `publish-default.yml` overrides `base_url` per publishing path.
A poisoned doc-index is repaired by the next publish; **a poisoned packet is
repaired by reprinting.** With no `site_url` the rewrite is SKIPPED and reported,
never guessed -- a wrong absolute link is worse than a relative one, because it
looks resolvable.

=============================================================================
⚠️ WHAT IS REMOVED FROM EACH SECTION, AND WHY EACH REMOVAL IS NOT TIDYING
=============================================================================
`.dr-flow*`   the flow strip. THE PACKET IS THE FLOW -- a reader holding all nine
              sheets has no next step to be told about, and nine strips would each
              claim to orient somebody who is already past it.
`buildstamp*` the corner mark. 🔴 NOT because paper does not want provenance --
              spec §8 makes per-sheet provenance load-bearing -- but because the
              print stamp is a FIXED element that repeats itself on every sheet
              from ONE instance. Nine copies is nine overlapping stamps on sheet
              one. The PACKET's own stamp is the one that prints, on every sheet,
              which is exactly what §8 asks for. Class block read off
              `buildstamp.py` (`buildstamp__icon`, `buildstamp__mark`), never
              guessed.

🚫 NOTHING ELSE IS STRIPPED. In particular semantic colour STAYS: `print.css`
applies `print-color-adjust: exact` narrowly, to elements "whose MEANING is
carried by a colour". The ask said "all the theming stripped" and that is not what
the print layer does -- a `!!! danger` border printing grey is a REGRESSION on a
photocopied safety sheet, not a target. Do not "finish the job" here.

=============================================================================
🚫 `{.new-page}` IS IGNORED IN A PACKET, AND IT IS A REFUSAL
=============================================================================
`print-type.css` §8 counts hand-placed breaks invalidated by a change to the print
layer; it stood at eight. This is the ninth and the first where every authored
break is invalidated BY DEFINITION: a break authored after a page's second heading
sits at an arbitrary offset inside a 27-sheet document. ⚑ *A page-level break
instruction is meaningless in a document the page does not know it is in.* Section
boundaries are the only breaks a packet honours and it owns those.

=============================================================================
🔴 AN AGGREGATOR IS A LEAK SURFACE
=============================================================================
`visibility.py` builds a page when `status in ("unlisted", "public")`, and
`nav: hidden` is a curtain -- the page is still built and still resolves by id.
Every previous instance of that shape was a page a reader had to go LOOKING for.
A packet brings it to them, stapled to a cover, in a file that leaves the site.

✅ SO A NON-`public` MEMBER IS REFUSED AND REPORTED, never silently included and
never silently dropped. ⚠️ uritp-safety's content repo is PRIVATE while this
engine is PUBLIC, so a visibility judgement can never be carried across from the
repo being rendered.
"""

from __future__ import annotations

import html as _html
import re
from urllib.parse import urljoin, urlsplit

from . import nav, state
from .util import relative_url

#: The splice point, written into the generated markdown and replaced at
#: on_post_build. An HTML comment survives the markdown pass untouched.
#:
#: ⚠️ IT MUST NOT LOOK LIKE A MARKER. `markers.py` owns `{...}` spans and
#: `links.py` owns `@ref` tokens; a comment is the one payload no other stage
#: claims. If this ever fails to be replaced it ships as an invisible comment
#: rather than as visible junk -- which is why the assembler REPORTS a miss
#: instead of trusting the substitution.
_MARK = "<!--dr-packet-body-->"

#: The export kinds this engine knows. A CLOSED SET, on the `markers._SHAPES`
#: precedent, because nothing else can enforce it.
#:
#: 🔴 `objects._resolve` MERGES EVERY TYPE'S `optional:` LIST AND NOTHING READS
#: IT (state.py records three separate live keys found dead that way). So a key
#: declared in `objects/program.yml` is a promise no code checks, and validation
#: of both the KEY and its VALUES has to happen right here or nowhere.
_KINDS = ("packet",)

_ARTICLE = re.compile(r"<article\b[^>]*>", re.I)
_ARTICLE_ANY = re.compile(r"</?article\b[^>]*>", re.I)
#: ⚠️ QUOTE-AGNOSTIC, AND THAT IS NOT DEFENSIVE PADDING. Python-Markdown and
#: Material both emit double quotes, so a double-only pattern passes every test
#: built from their output -- and an author's hand-written `<div id='x'>` in a
#: markdown body then slips through UNNAMESPACED, which is the half-works
#: collision this whole module exists to prevent. Found by running it, not by
#: reading it: the first fixture happened to use single quotes.
_ID = re.compile(r"""\bid=(?P<q>["'])(.*?)(?P=q)""")
_HREF = re.compile(r"""\bhref=(?P<q>["'])(.*?)(?P=q)""")
_ABSOLUTE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//)", re.I)

#: Class blocks removed from every section. See the removals block above.
_STRIP = ("dr-flow", "buildstamp")


def _esc(text) -> str:
    return _html.escape(str(text), quote=True)


def _meta(src) -> dict:
    return state.BY_SRC.get(src, {}) or {}


def kinds(meta: dict, src: str = "", report: bool = False) -> list:
    """The validated `export:` kinds on one page.

    Accepts `export: packet`, `export: [packet]` and `export: true` -- the last
    because Michael floated a boolean and a truthy value that silently did
    nothing would be the dead-control shape this repo keeps finding.

    ⚠️ AN UNKNOWN KIND IS REPORTED, NEVER IGNORED. `export: pakcet` has to be a
    finding: nothing downstream can tell a typo from a page that simply has no
    packet, and both render as no button.
    """
    raw = meta.get("export")
    if raw is None:
        return []
    if raw is True:
        return ["packet"]
    if raw is False:
        return []
    items = raw if isinstance(raw, list) else [raw]
    out = []
    for item in items:
        name = str(item).strip().lower()
        if not name:
            continue
        if name in _KINDS:
            if name not in out:
                out.append(name)
        elif report:
            state.note(
                "missing_required",
                (src or "a page") + " declares `export: " + str(item)
                + "`, which is not a known export kind. Known: "
                + ", ".join("`" + k + "`" for k in _KINDS)
                + ". IGNORED -- no button renders and no packet is built.",
            )
    return out


def packet_src(program_src: str) -> str:
    """`30-programs/for-all.md` -> `30-programs/for-all-packet.md`.

    ⚠️ A SIBLING FILE, NOT A CHILD PATH, WHICH CORRECTS THE SPEC. §1 proposed
    `<program-path>/packet/`; a program page is a FILE, so a child path would
    need a directory that does not exist and MkDocs would put the packet
    somewhere no reader could predict. A sibling keeps it adjacent in the tree
    and gives it a url a person can read.
    """
    stem = program_src[:-3] if program_src.endswith(".md") else program_src
    return stem + "-packet.md"


def wanted(report: bool = False) -> dict:
    """`{program_src: [chain ids]}` for every program asking for a packet.

    ⭐ THE CHAIN COMES FROM `nav.declared()`, WHICH IS THE WHOLE POINT: one
    vocabulary, one resolver, three consumers. A second parse of `chain:` here
    would be the defect this repo has retired three manifests over, and
    `nav.py` already refused a program-specific `steps:` on the same ground.
    """
    chains = nav.declared(report=False)
    out = {}
    for src, meta in state.BY_SRC.items():
        if "packet" not in kinds(meta or {}, src, report=report):
            continue
        if str((meta or {}).get("type") or "").strip().lower() != "program":
            if report:
                state.note(
                    "missing_required",
                    src + " asks for `export: packet` and is not `type: program`."
                    " IGNORED -- a packet is a program's reading order, so there"
                    " is nothing for it to collect.",
                )
            continue
        ids = chains.get(src)
        if not ids:
            if report:
                state.note(
                    "missing_required",
                    src + " asks for `export: packet` and declares no usable"
                    " `chain:`. NO PACKET BUILT -- a cover page with nothing"
                    " behind it is worse than no export, because zero sections"
                    " is a valid document nobody would question.",
                )
            continue
        out[src] = ids
    return out


def _cut(text: str, prefix: str) -> str:
    """Remove every element whose class carries a `prefix` token, contents and all.

    ⚠️ A DEPTH SCAN, NOT A LAZY `.*?`. `<nav class="dr-flow">` can contain another
    element of the same tag name, and a non-greedy match would close on the first
    inner `</nav>` and leave the tail of one strip in the document -- half an
    element, which renders as plausible garbage rather than as an error.
    """
    pat = re.compile(
        r"""<(?P<tag>[a-zA-Z][\w-]*)\b[^>]*\bclass=(?P<q>["'])[^"']*\b"""
        + re.escape(prefix) + r"""[\w-]*[^"']*(?P=q)[^>]*>"""
    )
    while True:
        m = pat.search(text)
        if not m:
            return text
        tag = m.group("tag")
        depth = 0
        pos = m.start()
        scan = re.compile(r"</?" + re.escape(tag) + r"\b[^>]*>", re.I)
        end = None
        for t in scan.finditer(text, m.start()):
            depth += -1 if t.group(0).startswith("</") else 1
            if depth == 0:
                end = t.end()
                break
        if end is None:
            return text[:pos]
        text = text[:pos] + text[end:]


def article(built: str) -> str:
    """The inner HTML of a built page's `<article>`, or "" if there is none.

    ⚠️ FIRST OPENING TAG TO LAST CLOSING TAG. Material renders one article per
    page; taking the LAST close rather than the first is what survives a nested
    one appearing in content without silently truncating the section.
    """
    open_m = _ARTICLE.search(built)
    if not open_m:
        return ""
    close = built.rfind("</article>")
    if close < open_m.end():
        return ""
    inner = built[open_m.end():close]
    for prefix in _STRIP:
        inner = _cut(inner, prefix)
    # A stray tag from an unbalanced cut would nest an article inside ours.
    return _ARTICLE_ANY.sub("", inner)


def _resolve(href: str, own_url: str) -> tuple:
    """(site-relative path, fragment) for a relative href seen on `own_url`."""
    joined = urljoin("http://dr.invalid/" + own_url.lstrip("/"), href)
    bits = urlsplit(joined)
    return bits.path.lstrip("/"), bits.fragment


def namespace(inner: str, n: int, own_url: str, sections: dict,
              site_url: str, src: str = "") -> str:
    """Prefix every id, and classify every href. See the module docstring.

    `sections` maps a member's built url -> its section number.
    """
    tag = "s" + str(n)

    def _pid(m):
        return 'id="' + tag + "-" + m.group(2) + '"'

    def _phref(m):
        href = m.group(2)
        if not href or _ABSOLUTE.match(href):
            return m.group(0)
        if href.startswith("#"):
            return 'href="#' + tag + "-" + href[1:] + '"'
        path, frag = _resolve(href, own_url)
        target = sections.get(path)
        if target is None and not path.endswith("/"):
            target = sections.get(path + "/")
        if target is not None:
            inner_target = "#s" + str(target) + ("-" + frag if frag else "")
            return 'href="' + inner_target + '"'
        if not site_url:
            # 🔴 NEVER GUESS AN ABSOLUTE. Reported once per build by `assemble`.
            return m.group(0)
        return 'href="' + _esc(urljoin(site_url, path + ("#" + frag if frag else ""))) + '"'

    return _HREF.sub(_phref, _ID.sub(_pid, inner))


def _cover(program_src: str, rows: list) -> str:
    """The contents list. It is the packet's ONLY navigation and its outline.

    🔴 BLINK EMITS NO PDF BOOKMARK PANE AND HAS NEVER IMPLEMENTED `@page` margin
    boxes, so there is no page number and no outline to be had from CSS. This
    list is the whole answer, which is why it is markdown-free HTML built here
    rather than left to an author.

    ⚠️ Whether these become CLICKABLE annotations in a printed PDF is the one
    OPEN ruling on this build (spec §4, Ruling 1). If they do not, this is still
    a correct printed contents list -- the element does not change, only the
    claim about it does.
    """
    items = "".join(
        '<li><a href="#s' + str(n) + '"><span class="dr-packet__n">'
        + str(n) + '</span> ' + _esc(title) + "</a></li>"
        for n, title, _url in rows
    )
    return (
        '<nav class="dr-packet__toc" aria-label="Contents of this packet">'
        '<ol class="dr-packet__list">' + items + "</ol></nav>"
    )


def button(program_src: str, meta: dict, here: str) -> str:
    """The export link, for `!!! export` or the automatic slot.

    🚫 IT DOES NOT PRINT. `assets/flow.css` already says why, in the right file
    and in the right words: *"A BUTTON ON PAPER IS A LIE."* The chrome-off rule
    ships in `assets/print-packet.css` in the same commit as the button.

    🚫 AND IT DOES NOT FIRE `window.print()`. Legal, identical to a manual print,
    and it would defeat the one check no build can do: a nine-section packet
    built from a ten-id chain is a VALID document, so the reader's glance at the
    cover is the last line of defence and an instant dialog spends it.
    """
    target = relative_url(packet_src(program_src)[:-3] + "/", here)
    return (
        '<p class="dr-packet__cta"><a class="dr-packet__button" href="'
        + _esc(target) + '">Download the whole program \u2192</a></p>'
    )
