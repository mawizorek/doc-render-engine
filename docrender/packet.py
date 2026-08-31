"""Stage 05b -- THE PROGRAM PACKET: every page printed as itself, then stapled.

BUILD 10 v3. Decisions: `specs/print-packet.md`. Arguments: `specs/print-packet-dl.md`.
The `chain:` vocabulary and its resolver belong to docrender/nav.py; the flow strip
belongs to docrender/program.py; the embedded form to docrender/forms.py. This module
declares the `export:` key, names the artifacts, and draws the button.

=============================================================================
🪦 THE HTML PACKET PAGE IS GONE (2026-08-31), AND THE CULL IS THE FEATURE
=============================================================================
> Michael, three times across one evening: *"i thoght we decideed to NOT be using a
> combined page wiht conatn at top"* / *"How do we make this the most like standing on
> the progrma page - hitdn cmd+p ... then i step to the foirst polciy in the chain.
> cmd-p that page just as if i had fomratted and done it by that page itsefl"* /
> *"lets now cull the unneccsary page you were generating."*

v1 minted a generated `-packet.md` per program and spliced every member's finished
HTML into it. **That page and every mechanism serving it is deleted here:**

    _MARK / on_post_build splice   the assembly
    article()                      pulling a member's <article> out
    _cut() / _STRIP                removing per-page furniture N-1 times
    namespace()                    re-prefixing every id and href
    _cover()                       a generated contents list
    on_files / _prune              minting the page and hiding its nav row

⭐ **EVERY ONE OF THOSE EXISTED ONLY TO REPAIR DAMAGE THE SPLICE CAUSED.** None of
them served the ask; they served the mechanism. Printing each page as its own document
does not need them, which is why this file is a third of its former size and why the
`packetbuild.py` split it forced is retired with it -- **the reason for the split was
the transform, and the transform is gone.**

🔴 AND THE STRIP LIST IS THE PART WORTH REMEMBERING, BECAUSE IT WAS ALREADY LOSING.
It took two live defects in four hours (rival `@page` rules stamping section nine's
date on all nine sheets; a duplicated ownership tag), and the file's own closing note
admitted the class was unbounded: *"any per-page element added anywhere in the engine
is silently duplicated into every packet unless somebody remembers this tuple."*
⚑ *A defence that must be updated by everyone who never reads it is not a defence.
One document per page makes the whole class impossible rather than managed* -- and
that is the real argument for the cull, over and above it being what he asked for.

⚠️ CREDIT WHERE IT IS DUE: another session patched that tuple correctly on 08-30,
adding `runfoot.STYLE_CLASS` and `dr-owner` while REFUSING to strip `dr-revised`
because a revision date VARIES between members. **That judgement was right and it is
deleted here only because the surface it defended no longer exists.**

=============================================================================
⭐ WHAT REPLACES IT: A PLAN, AND CHROME
=============================================================================
`packets.json` names, per program, the ORDERED page URLs to print -- the program page
first, then the chain. `bin/print-packets.py` drives real Chrome over the finished
site, one page per launch, and pypdf staples the results.

    <program>-packet.pdf     the stapled packet, what the button points at
    <page>/print.pdf         each page on its own, beside the page itself

🔴 THE PER-PAGE PDF IS NOT AN EXTRA FEATURE, IT IS THE INTERMEDIATE FILE KEPT.
Michael: *"Take allll the pages from eacah of those steps and export them as
indidivial fiels. fine."* Every member is printed separately regardless, so keeping
the file costs a `copy` and buys a policy anybody can hand out alone. ⭐ It also
DEDUPES: a policy in three programs is printed once and stapled three times, which is
fewer browser launches than v1's own per-program work.

🚫 AND THE ENGINE STILL PRODUCES NO PDF. It writes a JSON plan naming pages that
already exist -- no renderer, no dependency, no bytes. `specs/print-packet.md` §5's
refusal of a second renderer is untouched; Chrome is the renderer Michael prints from.
"""

from __future__ import annotations

import html as _html

from . import nav, state
from .util import relative_url

#: The export kinds this engine knows. A CLOSED SET, on the `markers._SHAPES`
#: precedent, because nothing else can enforce it.
#:
#: 🔴 `objects._resolve` MERGES EVERY TYPE'S `optional:` LIST AND NOTHING READS IT
#: (state.py records three separate live keys found dead that way). So a key declared
#: in `objects/program.yml` is a promise no code checks, and validation of both the
#: KEY and its VALUES has to happen right here or nowhere.
_KINDS = ("packet",)


def _esc(text) -> str:
    return _html.escape(str(text), quote=True)


def kinds(meta: dict, src: str = "", report: bool = False) -> list:
    """The validated `export:` kinds on one page.

    Accepts `export: packet`, `export: [packet]` and `export: true` -- the last
    because Michael floated a boolean and a truthy value that silently did nothing
    would be the dead-control shape this repo keeps finding.

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


def pdf_uri(program_src: str) -> str:
    """`30-programs/for-all.md` -> `30-programs/for-all-packet.pdf`.

    🪦 THE `-packet` STEM SURVIVES ITS OWN PAGE. It was shared with the generated
    `-packet.md` so the two artifacts sat beside each other; the page is gone and the
    name stays, because it is the URL Michael has already opened and any link he has
    kept still resolves. **A rename would be a second change riding along in a
    deletion, and the only thing it would buy is tidiness.**
    """
    stem = program_src[:-3] if program_src.endswith(".md") else program_src
    return stem + "-packet.pdf"


def page_pdf_uri(page_url: str) -> str:
    """`20-policies/fire/` -> `20-policies/fire/print.pdf`.

    ⚠️ KEYED ON THE BUILT URL, NOT THE SOURCE PATH, and that is deliberate: it is what
    `bin/print-packets.py` navigates and what a reader sees, so the PDF lands exactly
    beside the page it is a print of. A source path would need `use_directory_urls`
    arithmetic, which `util.py` records three separate hooks getting wrong invisibly.
    """
    return page_url.rstrip("/") + "/print.pdf" if page_url else ""


def wanted(report: bool = False) -> dict:
    """`{program_src: [chain ids]}` for every program asking for a packet.

    ⭐ THE CHAIN COMES FROM `nav.declared()`, WHICH IS THE WHOLE POINT: one vocabulary,
    one resolver, three consumers. A second parse of `chain:` here would be the defect
    this repo has retired three manifests over, and `nav.py` already refused a
    program-specific `steps:` on the same ground.
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
                    " `chain:`. NO PACKET -- a cover sheet with nothing behind it"
                    " is a valid document nobody would question.",
                )
            continue
        out[src] = ids
    return out


def button(program_src: str, here: str) -> str:
    """The export link. It points at the PDF.

    🔴 IT USED TO POINT AT THE GENERATED HTML PAGE, and repointing it is the whole
    visible half of the cull. The link is now a plain file: a reader gets the stapled
    document with no intermediate stop, which is what Michael asked for on the first
    message of the feature and again on the last.

    🚫 IT DOES NOT PRINT, AND THAT MATTERS MORE NOW THAN IT DID. `assets/flow.css`
    says why in the right words -- *"A BUTTON ON PAPER IS A LIE"* -- and the program
    page is now SHEET ONE of the packet, so an unsuppressed button would appear on the
    cover of the document it produced. The chrome-off rule is `print-packet.css`.

    ⚠️ `download` IS DELIBERATELY ABSENT. It forces a save instead of opening the
    viewer, and the packet's own navigation is the PDF's internal links -- a reader who
    cannot see the file cannot check that their whole program is in it, which is the
    one verification no build can do for them.
    """
    target = relative_url(pdf_uri(program_src), here)
    return (
        '<p class="dr-packet__cta"><a class="dr-packet__button" href="'
        + _esc(target) + '">Download the whole program (PDF) \u2192</a></p>'
    )


# =============================================================================
# THE EVENTS. Two, where v1 needed five.
# =============================================================================
# 🪦 `docrender/packetbuild.py` IS RETIRED INTO THIS FILE BY THIS COMMIT. It existed
# because `packet.py` hit 18,004 B against a ~22.5 KB read ceiling and had to be cut
# on the concern (`specs/visibility-split.md` §1): pure transforms one side, MkDocs and
# disk the other. ⭐ **The transform is deleted, so the reason for the split is
# deleted.** Both halves together are now smaller than either file was alone, and a
# two-file feature whose second file holds two functions is a seam nobody needs.
#
# ⚠️ v1 HELD on_files, on_nav, on_page_markdown, on_page_content AND on_post_build.
# `on_files` minted the page; `on_post_build` spliced it. **Both are gone with the
# page** -- and the splice going is the one to notice, because it was the only place in
# this feature that WROTE to the built site. The engine now writes one JSON plan and
# nothing else.

import json  # noqa: E402  -- kept beside its only consumer, `on_post_build`
from pathlib import Path  # noqa: E402

#: `{program_src: {"pdf", "pages": [urls], "titles": [...]}}`
#:
#: 🔴 CAPTURED AT on_nav AND NEVER RE-DERIVED. At that event every File already knows
#: its own `url`, so nothing downstream reconstructs a path from a source stem --
#: `util.py` records two hooks that shipped the separator-counting version of that
#: maths and got it wrong invisibly.
#:
#: ⚠️ IT LIVES HERE, NOT IN `state`. `state.py`'s admission price is a writer and a
#: reader in DIFFERENT hooks; both are in this module.
_PLAN: dict = {}


def _title(src) -> str:
    meta = state.BY_SRC.get(src, {}) or {}
    return str(meta.get("title") or src.rsplit("/", 1)[-1][:-3])


def on_nav(nav_obj, config, files):
    """Resolve each program's chain into an ordered list of page URLs.

    🚫 IT NO LONGER PRUNES THE SIDEBAR, because there is no generated page to hide.
    v1's `_prune` walked the whole nav tree to remove a row it had just created --
    a cost that existed entirely to undo `on_files`.
    """
    _PLAN.clear()
    programs = wanted(report=True)
    if not programs:
        return nav_obj

    by_id, _by_src = nav._built(files)
    urls = {}
    for f in files:
        page = getattr(f, "page", None)
        if page is not None and getattr(page, "is_page", False):
            urls[getattr(f, "src_uri", "")] = getattr(f, "url", "")

    for src, ids in programs.items():
        cover = urls.get(src, "")
        if not cover:
            state.note(
                "missing_required",
                src + " asks for `export: packet` and has no built URL of its own."
                " NO PACKET -- the program page IS the cover sheet.",
            )
            continue
        pages, titles = [cover], [_title(src)]
        for pid in ids:
            page = by_id.get(pid)
            if page is None:
                continue  # nav.py already reported this id as dead.
            psrc = getattr(getattr(page, "file", None), "src_uri", "")
            status = str((state.BY_SRC.get(psrc, {}) or {}).get("status")
                         or "public").strip().lower()
            if status != "public":
                # 🔴 THE LEAK REFUSAL, UNCHANGED BY THE CULL. `nav: hidden` and
                # `unlisted` are curtains for somebody BROWSING; a PDF leaves the
                # site. Refused and named, never silently included or dropped.
                state.note(
                    "missing_required",
                    src + " packet REFUSES `" + pid + "` (" + psrc + "): status `"
                    + status + "`. A packet is a distribution channel, not a"
                    " reader. Make it `public` or take it out of the chain.",
                )
                continue
            url = urls.get(psrc, "")
            if not url:
                # A blank URL would print the site ROOT and look like a real sheet.
                state.note(
                    "dead_links",
                    src + " packet member `" + pid + "` has no built URL and is"
                    " OMITTED. A blank URL prints the site root, which looks like"
                    " a real sheet and is not one.",
                )
                continue
            pages.append(url)
            titles.append(_title(psrc) or getattr(page, "title", pid))

        if len(pages) < 2:
            state.note(
                "missing_required",
                src + " packet resolved ZERO of " + str(len(ids)) + " members."
                " NOT WRITTEN -- a cover sheet alone is a valid document nobody"
                " would question.",
            )
            continue
        _PLAN[src] = {"pdf": pdf_uri(src), "pages": pages, "titles": titles}
        # ⚠️ `notes`, NOT A NEW BUCKET. A new one costs two edits in two large files
        # (`state.reset()` + `report._LABELS`) and a bucket declared in only one of
        # them is collected all build and SILENTLY DROPPED. Every packet DEFECT above
        # lands in `missing_required` / `dead_links`, which are annotated per BUILD 2
        # Piece A. This line is inventory -- same shape as nav.py's reading-order note.
        state.note(
            "notes",
            src + " PACKET: " + str(len(pages) - 1) + " of " + str(len(ids))
            + " declared member(s) -> " + pdf_uri(src) + ". Printed in chain order"
            " behind the program page; each member also lands as its own"
            " `print.pdf` beside itself.",
        )
    return nav_obj


def on_page_markdown(markdown, page, config, files):
    """`!!! export` -> the button, exactly where the author put it.

    ⭐ THE `forms:` SPLIT, WHICH IS THE PATTERN MICHAEL ASKED FOR BY NAME: the
    frontmatter DECLARES (*"love that i can define in frontmatter, well outside of the
    actual body content"*) and a body directive DRAWS. With no directive the button
    lands automatically -- see `on_page_content`.
    """
    if "!!! export" not in markdown:
        return markdown
    src = getattr(getattr(page, "file", None), "src_uri", "")
    if src not in wanted(report=False):
        state.note(
            "dead_links",
            (src or "a page") + " uses `!!! export` and has no packet to export"
            " (needs `type: program`, an `export:` kind and a live `chain:`)."
            " The directive is left as text rather than drawing a dead button.",
        )
        return markdown
    here = getattr(getattr(page, "file", None), "url", "")
    html = button(src, here)
    out = []
    for line in markdown.split("\n"):
        if line.strip().startswith("!!! export"):
            out.extend(("", html, ""))
            page.__dict__["_dr_packet_placed"] = True
        else:
            out.append(line)
    return "\n".join(out)


def on_page_content(html, page, config, files):
    """The automatic slot, when no `!!! export` claimed it.

    ⚠️ THE POSITION IS CONSTRAINED, NOT CHOSEN. `hide: footer` makes the flow strip the
    only navigation on a program page, and a SECOND footer was rejected by name on
    08-19 -- *"all this other foot matter... is that what I'm supposed to click
    next?"* So the button rides with the strip. `program.py` appends the strips at this
    same event and the 05b shim runs this AFTER it.
    """
    if page.__dict__.pop("_dr_packet_placed", False):
        return html
    src = getattr(getattr(page, "file", None), "src_uri", "")
    if not src or src not in _PLAN:
        return html
    return html + button(src, getattr(getattr(page, "file", None), "url", ""))


def on_post_build(config):
    """Write `packets.json`: what `bin/print-packets.py` should print, in order.

    🔴 URLS, NOT DISK PATHS, AND THAT IS THE INTERFACE. The script serves the built
    site over loopback HTTP and navigates these, because `file://` breaks absolute
    asset paths and gives Chrome a different origin per directory.

    ⚠️ WRITTEN ON EVERY BUILD, INCLUDING `dry_run`. It names pages rather than
    producing artifacts, so a preview that writes it is telling the truth about what a
    publish would print. **A missing `packets.json` therefore means exactly one thing:
    no program declares `export:`.**

    ⚠️ THE TITLES ARE CARRIED AND NOTHING READS THEM. They are here so a human can
    read the manifest and see WHICH policies a PDF claims to contain -- the same
    falsifiability argument as the script's sheet count. 🚩 If nothing consumes them
    in a week, cut them: an unread field is the shape this repo retires manifests over.
    """
    if not _PLAN:
        return
    packets = [
        {
            "program": src,
            "title": plan["titles"][0],
            "pdf": plan["pdf"],
            "pages": plan["pages"],
            "titles": plan["titles"],
        }
        for src, plan in sorted(_PLAN.items())
    ]
    out = Path(str(config.site_dir)) / "packets.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"packets": packets}, indent=2), encoding="utf-8")
    except OSError:
        state.note(
            "missing_required",
            "packets.json could not be written, so NO packet PDF will be printed by"
            " this build and every export button will 404.",
        )
