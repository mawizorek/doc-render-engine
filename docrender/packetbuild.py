"""Stage 05b -- WHEN a packet is minted and assembled. BUILD 10.

⚠️ SPLIT FROM `packet.py` AT 18,004 B AGAINST A ~22.5 KB READ CEILING, and cut on
the CONCERN rather than at the byte that forced it -- `specs/visibility-split.md`
§1 is the rule, and `program.py` -> `forms.py` -> `chainlist.py` -> `promote.py` is
the precedent. `packet.py` answers *what a packet IS and how its HTML is
transformed* and every function in it is pure and testable. This file answers
*when*, and every function in it touches MkDocs or the disk.

🔴 THE PLAN IS BUILT AT on_nav AND NEVER RE-DERIVED. At that event every File
already knows its own `url` AND its `abs_dest_path`, so nothing downstream has to
reconstruct a disk path from a url. `util.py` records two hooks that already
shipped the separator-counting version of that maths and got it wrong invisibly.

⚠️ IT LIVES IN THIS MODULE, NOT IN `state`. `state.py`'s admission price is a
writer and a reader in DIFFERENT hooks; both of these are here.

🚨 REMOVING THIS FROM THE 05b SHIM IS NOT A NO-OP: every `!!! export` renders as a
grey admonition titled "export", no packet page is minted, and any link a reader
already has to one 404s.

=============================================================================
⭐ `packets.json` -- THE PRINT PLAN, AND THE ROAD OUT OF THE HTML SPLICE (v2)
=============================================================================
Michael, 2026-08-30, on the spliced page: *"that extra page that we navigate to
doesn't print right. I don't like this implementation so far."* And the baseline,
restated: *"every single policy printed as if I went to that page and printed it
manually, stacked together in a single PDF."*

`_manifest()` writes exactly that instruction to disk: for each program, the ORDERED
list of page URLs to print. `bin/print-packets.py` then drives real Chrome over the
finished site and staples the results. ⭐ **The engine's job is the PLAN, never the
PDF** -- no renderer, no dependency, no bytes; a JSON file naming pages that already
exist.

🔴 THE PROGRAM PAGE IS ENTRY ONE, AND THAT IS HIS COVER ASK ANSWERED FOR FREE. He
wanted *"the local program thing"* as the cover eventually; printing the program page
first IS that, with no cover renderer, no contents generator and nothing to keep in
step with the pages it describes. ⚑ *The splice needed a cover BUILT because it threw
the program page away; printing it needs the cover only ADDED to a list.*

⚠️ THIS PASS IS PURELY ADDITIVE AND THE BUTTON STILL POINTS AT THE HTML PAGE. The
manifest and the PDF land first; the button repoints and the splice comes out in ONE
deletion pass, once a printed PDF has been seen. **A feature whose replacement is
unproven leaves the old half one deletion away** -- the rule `print-identity.css`
wrote for the letterhead the same day, and the reason nothing here is removed yet.

⚠️ AND THE MANIFEST IS WRITTEN ON EVERY BUILD, INCLUDING `dry_run`. It names pages
rather than producing artefacts, so a preview build that writes it is telling the
truth about what a publish would print. A missing `packets.json` therefore means one
thing only: no program declares `export:`.
"""

from __future__ import annotations

import json
from pathlib import Path

from mkdocs.structure.files import File

from . import nav, packet, state

#: `{program_src: {"uri", "dest", "cover", "rows": [(n, id, title, url, dest)]}}`
_PLAN: dict = {}

#: Frontmatter of the generated page. `hide:` mirrors what a program page already
#: carries: the packet has no sidebar row, no TOC worth drawing, and the flow
#: strip it would otherwise inherit is the thing it REPLACES.
_HEAD = (
    "---\ntitle: {title}\nstatus: unlisted\nsearch:\n  exclude: true\n"
    "hide:\n  - navigation\n  - toc\n  - footer\n---\n\n# {title}\n\n"
)


def _title(src) -> str:
    meta = state.BY_SRC.get(src, {}) or {}
    return str(meta.get("title") or src.rsplit("/", 1)[-1][:-3])


def pdf_uri(program_src: str) -> str:
    """`30-programs/for-all.md` -> `30-programs/for-all-packet.pdf`.

    ⭐ DERIVED FROM `packet.packet_src`, NEVER SPELLED SEPARATELY. The stem is shared
    with the HTML page on purpose, so the two artifacts sit beside each other with one
    naming rule between them -- and when the page goes away the rule does not move.
    """
    return packet.packet_src(program_src)[:-3] + ".pdf"


def on_files(files, config):
    """Mint one page per program that asked for a packet. Files close after this.

    ⚠️ `report=False` HERE. `on_files` can run more than once under
    `mkdocs serve`, and a validation complaint printed twice reads as two
    defects. `on_nav` reports, once.
    """
    for src in packet.wanted(report=False):
        uri = packet.packet_src(src)
        if any(getattr(f, "src_uri", "") == uri for f in files):
            continue
        title = _title(src)
        files.append(
            File.generated(
                config, uri,
                content=_HEAD.format(title=title) + packet._MARK + "\n",
            )
        )
    return files


def _prune(items, drop):
    """Drop the packet pages from the sidebar, keeping them built and reachable.

    ⚠️ THE PAGE IS NOT HIDDEN, IT IS UNLISTED -- the same curtain `nav.py`
    describes. It has a real url that the button points at; it simply is not a row
    a reader browses to, because a packet is something you are HANDED.
    """
    keep = []
    for item in items:
        if getattr(item, "is_page", False):
            if getattr(getattr(item, "file", None), "src_uri", "") in drop:
                continue
        elif getattr(item, "children", None):
            item.children = _prune(item.children, drop)
        keep.append(item)
    return keep


def on_nav(nav_obj, config, files):
    """Capture the plan, refuse what must be refused, prune the sidebar."""
    _PLAN.clear()
    programs = packet.wanted(report=True)
    if not programs:
        return nav_obj

    by_id, _by_src = nav._built(files)
    dest = {}
    for f in files:
        page = getattr(f, "page", None)
        if page is not None and getattr(page, "is_page", False):
            dest[getattr(f, "src_uri", "")] = f

    for src, ids in programs.items():
        uri = packet.packet_src(src)
        mine = dest.get(uri)
        if mine is None:
            state.note(
                "missing_required",
                src + " asked for a packet and its generated page is absent from"
                " the build. NO PACKET -- the button would 404.",
            )
            continue
        rows = []
        for pid in ids:
            page = by_id.get(pid)
            if page is None:
                continue  # nav.py already reported this id as dead.
            psrc = getattr(getattr(page, "file", None), "src_uri", "")
            status = str((state.BY_SRC.get(psrc, {}) or {}).get("status")
                         or "public").strip().lower()
            if status != "public":
                # 🔴 THE LEAK REFUSAL. See packet.py's aggregator block.
                state.note(
                    "missing_required",
                    src + " packet REFUSES `" + pid + "` (" + psrc + "): status `"
                    + status + "`. A packet is a distribution channel, not a"
                    " reader -- an unlisted page is a curtain for somebody"
                    " browsing, and a PDF leaves the site. Make it `public` or"
                    " take it out of the chain.",
                )
                continue
            rows.append((
                len(rows) + 1, pid, _title(psrc) or getattr(page, "title", pid),
                getattr(getattr(page, "file", None), "url", ""),
                getattr(dest.get(psrc), "abs_dest_path", ""),
            ))
        if not rows:
            state.note(
                "missing_required",
                src + " packet resolved ZERO of " + str(len(ids)) + " members."
                " NOT WRITTEN -- a cover with nothing behind it is a valid"
                " document nobody would question.",
            )
            continue
        _PLAN[src] = {
            "uri": uri,
            "dest": getattr(mine, "abs_dest_path", ""),
            # 🔴 THE PROGRAM PAGE'S OWN URL -- sheet one of the printed packet, and the
            # whole of the cover. Read off the File here rather than derived later,
            # for the reason the docstring gives about reconstructing paths.
            "cover": getattr(dest.get(src), "url", ""),
            "rows": rows,
        }
        # ⚠️ `notes`, NOT A NEW `packet` BUCKET, AND THE DEVIATION IS DELIBERATE.
        # spec §6 asked for its own bucket; a new one costs TWO edits in TWO large
        # files (`state.reset()` + `report._LABELS`) and buys a section heading,
        # while a bucket declared in only one of them is collected all build and
        # SILENTLY DROPPED. Every actual packet DEFECT already lands in
        # `missing_required` / `dead_links`, which are annotated defect buckets per
        # BUILD 2 Piece A. This line is inventory -- the same shape as nav.py's
        # AUTHORED READING ORDER note. 🚩 Owed if the heading is wanted.
        state.note(
            "notes",
            src + " PACKET: " + str(len(rows)) + " of " + str(len(ids))
            + " declared member(s) -> " + uri + " and " + pdf_uri(src)
            + ". Print order is the program page, then the chain.",
        )

    if _PLAN:
        nav_obj.items = _prune(
            nav_obj.items, {p["uri"] for p in _PLAN.values()}
        )
    return nav_obj


def on_page_markdown(markdown, page, config, files):
    """`!!! export` -> the button, exactly where the author put it.

    ⭐ THE `forms:` SPLIT, WHICH IS THE PATTERN MICHAEL ASKED FOR BY NAME: the
    frontmatter DECLARES (*"love that i can define in frontmatter, well outside of
    the actual body content"*) and a body directive DRAWS. With no directive the
    button lands automatically -- see `on_page_content`.
    """
    if "!!! export" not in markdown:
        return markdown
    src = getattr(getattr(page, "file", None), "src_uri", "")
    if src not in packet.wanted(report=False):
        state.note(
            "dead_links",
            (src or "a page") + " uses `!!! export` and has no packet to export"
            " (needs `type: program`, an `export:` kind and a live `chain:`)."
            " The directive is left as text rather than drawing a dead button.",
        )
        return markdown
    here = getattr(getattr(page, "file", None), "url", "")
    html = packet.button(src, state.BY_SRC.get(src, {}) or {}, here)
    out = []
    for line in markdown.split("\n"):
        if line.strip().startswith("!!! export"):
            out.append("")
            out.append(html)
            out.append("")
            page.__dict__["_dr_packet_placed"] = True
        else:
            out.append(line)
    return "\n".join(out)


def on_page_content(html, page, config, files):
    """The automatic slot, when no `!!! export` claimed it.

    ⚠️ THE POSITION IS CONSTRAINED, NOT CHOSEN. `hide: footer` makes the flow
    strip the only navigation on a program page, and a SECOND footer was rejected
    by name on 08-19 -- *"all this other foot matter... is that what I'm supposed
    to click next?"* So the button rides with the strip. `program.py` appends the
    strips at this same event; the 05b shim runs this AFTER it, so appending here
    puts the button below the strip it belongs to and above the edit line.
    """
    if page.__dict__.pop("_dr_packet_placed", False):
        return html
    src = getattr(getattr(page, "file", None), "src_uri", "")
    if not src or src not in _PLAN:
        return html
    return html + packet.button(
        src, state.BY_SRC.get(src, {}) or {},
        getattr(getattr(page, "file", None), "url", ""),
    )


def _manifest(config) -> None:
    """Write `packets.json`: what `bin/print-packets.py` should print, in order.

    🔴 URLS, NOT DISK PATHS, AND THAT IS THE INTERFACE. The script serves the built
    site over loopback HTTP and navigates these URLs, because `file://` breaks
    absolute asset paths and gives Chrome a different origin per directory. A disk
    path here would invite the wrong one.

    ⭐ THE PROGRAM PAGE IS FIRST. That is the cover, and it costs one list entry
    rather than a renderer.

    ⚠️ IT NAMES THE MEMBER TITLES TOO, WHICH NOTHING READS YET. They are here so a
    human can read the manifest and see WHICH policies a PDF claims to contain -- the
    same falsifiability argument as the sheet count in the script's own summary. 🚩 If
    nothing consumes them by the time the HTML page is deleted, cut them: an unread
    field is the shape this repo retires manifests over.
    """
    if not _PLAN:
        return
    packets = []
    for src, plan in sorted(_PLAN.items()):
        pages = [plan["cover"]] + [row[3] for row in plan["rows"]]
        if not all(pages):
            # A blank url would print the site ROOT and look like a real sheet.
            state.note(
                "missing_required",
                src + " packet has a member with no URL, so no print plan was"
                " written for it. A blank URL prints the site root, which looks"
                " like a real sheet and is not one.",
            )
            continue
        packets.append({
            "program": src,
            "title": _title(src),
            "pdf": pdf_uri(src),
            "pages": pages,
            "sections": [row[2] for row in plan["rows"]],
        })
    if not packets:
        return
    out = Path(str(config.site_dir)) / "packets.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"packets": packets}, indent=2), encoding="utf-8")
    except OSError:
        state.note(
            "missing_required",
            "packets.json could not be written, so NO packet PDF will be printed"
            " by this build. The HTML packet pages are unaffected.",
        )


def on_post_build(config):
    """Write the print plan, then splice every HTML packet.

    ⚠️ THE MANIFEST GOES FIRST AND IS INDEPENDENT OF THE SPLICE. They are two
    artifacts of one plan, and the splice is the half on its way out -- so a failure
    in the older half must never take the newer one down with it.

    🔴 A MISSED SUBSTITUTION IS REPORTED, NEVER ASSUMED AWAY. The marker is an
    HTML comment, so a failure ships as an invisible nothing -- a cover page with
    no program behind it, which is the exact artifact this build refuses to
    produce silently.
    """
    if not _PLAN:
        return
    _manifest(config)

    site_url = str(getattr(config, "site_url", "") or "")
    if not site_url:
        state.note(
            "notes",
            "PACKET: no `site_url`, so links OUT of a packet are left relative"
            " and will not resolve from a saved PDF. Reported rather than"
            " guessed -- a wrong absolute link looks resolvable.",
        )
    for src, plan in _PLAN.items():
        dest = Path(plan["dest"])
        try:
            shell = dest.read_text(encoding="utf-8")
        except OSError:
            state.note("missing_required",
                       src + " packet page is not on disk. NOT WRITTEN.")
            continue
        if packet._MARK not in shell:
            state.note(
                "missing_required",
                src + " packet marker was consumed before assembly, so the"
                " program body has nowhere to go. NOT WRITTEN.",
            )
            continue
        sections = {row[3]: row[0] for row in plan["rows"]}
        body = []
        for n, pid, title, url, member_dest in plan["rows"]:
            try:
                built = Path(member_dest).read_text(encoding="utf-8")
            except OSError:
                state.note("dead_links",
                           src + " packet could not read section " + str(n)
                           + " (`" + pid + "`) from disk. SECTION OMITTED.")
                continue
            inner = packet.article(built)
            if not inner.strip():
                state.note("dead_links",
                           src + " packet found no article in section " + str(n)
                           + " (`" + pid + "`). SECTION OMITTED.")
                continue
            body.append(
                '<section class="dr-packet__section" id="s' + str(n) + '">'
                + packet.namespace(inner, n, url, sections, site_url, pid)
                + "</section>"
            )
        cover = packet._cover(src, [(r[0], r[2], r[3]) for r in plan["rows"]])
        shell = shell.replace(packet._MARK, cover + "".join(body))
        try:
            dest.write_text(shell, encoding="utf-8")
        except OSError:
            state.note("missing_required",
                       src + " packet could not be written back to disk.")
