"""Stage 00c -- prev/next, and the ONE place a reading order may disagree with
the sidebar.

MkDocs walks the nav and wires `page.previous_page` / `page.next_page` while
BUILDING it, which happens BEFORE `on_nav` fires. So anything that reorders the
nav -- and `instance.py:on_nav` reorders all of it -- leaves those links
pointing along the ORIGINAL order.

The result is a site that disagrees with itself: the sidebar reads in `order:`
sequence and the Next button at the foot of the page reads in filesystem
sequence. Both look plausible in isolation, which is why it survives review.

This re-flattens the sorted tree and rewires the chain. Runs as its own stage
rather than at the end of the sort so that the two concerns stay separable:
one decides ORDER, this one propagates its consequences.

=============================================================================
⭐ `chain:` -- A READING ORDER THAT OUTLIVES THE SIDEBAR (2026-08-19)
=============================================================================
Found on uritp-safety `20-policies/`, and the folder is the whole argument:
eleven policy pages, `nav: hidden` on the folder index, `status: unlisted` on
eight of the pages. Michael expected the footer to walk Proper Attire ->
Emergency Contacts -> Active Shooter -> Shelter-in-place. It walked four pages
and crossed out of the folder, because ALL FOUR of the pages he named are
absent from the surviving nav by the time this stage runs.

🔴 THE DEFECT IS NOT A WRONG ORDER. IT IS THAT THERE WAS ONLY ONE. Three
separate questions were welded into a single cascade:

    is this page reachable and searchable      `status:`
    is it a ROW in the sidebar                 `status:` + `nav:`
    is it in the READING ORDER                 whatever survived the above

The third had no voice of its own. It read the tree left behind by stages 00b
(unlisted leave), 00bb (`nav: hidden` folders lose children) and 00bc (routers
seal), so EVERY sidebar-removal mechanism silently amputated the reading chain
as a side effect. Four stages, four chances to shrink it, and the footer never
said a word about what it lost.

⚑ GENERALISABLE, and it is the same shape `navsettle.py` wrote down three days
ago from the other end: A STAGE THAT CONSUMES A TREE IS NOT ENTITLED TO ASSUME
THE TREE IS THE ONLY ANSWER TO ITS QUESTION. navsettle found a rule evaluated
too early; this is a rule with no way to be stated at all.

⭐ AND MICHAEL HAD ALREADY AUTHORED THE ORDER TWICE, BY HAND, IN CONTENT. The
folder index lists eight policies in a deliberate sequence, and
`10-safety-responsibilities.md` carries a hand-typed "Up Next" callout pointing
at Emergency Contacts. That callout is a human building prev/next manually
because the real one could not be reached. The feature did not need inventing;
it needed a key.

    chain:
      - policy-housekeeping
      - policy-fire
      - policy-proper-attire

🚥 IT IS AN OVERRIDE, NOT A REPLACEMENT, AND THAT IS THE WHOLE SAFETY ARGUMENT.
The default rewiring below runs FIRST and unchanged. A `chain:` block then
re-points prev/next among the pages it NAMES and touches nothing else on the
site. So a site with no `chain:` anywhere builds byte for byte what it built
before -- which is what keeps `specs/visibility-split.md` §8's byte-identical
test alive for every instance except the one that opted in.

⚠️ A HUB ONLY EVER DONATES ITS `next`. It keeps its own `previous`, and keeps
its place in the default chain. A hub is a doorway INTO a flow, not a link in
it -- and stripping its `previous` would cut the site's spine to give a folder a
reading order, which is a trade nobody asked for.

🚫 THE LAST PAGE'S `next` IS None, DELIBERATELY. An authored flow ENDS; it does
not leak the reader back into whatever the nav happened to put next. Reported,
so it reads as a decision rather than a dead button.

=============================================================================
⚠️ LEGALITY IS A CAPABILITY, NOT A FILENAME (WIDENED 2026-08-19, SAME DAY)
=============================================================================
This file shipped hours earlier saying `chain:` was legal "on an `index.md`
only", mirroring `nav:`. That rule was too narrow and it was narrow for the
wrong reason: it described WHERE the key sat rather than WHAT it does.

🔴 A `chain:` IS LEGAL ON A PAGE THAT OWNS AN ORDERING. Two types qualify:

    index      the order of the pages BENEATH it. Its ordering is its folder.
    program    a curriculum ACROSS the tree. Its ordering is a PATH, and the
               pages on it live wherever they live.

⭐ THE SECOND ONE IS WHY: uritp-safety already had `30-programs/`, where
`general-safety-for-all.md` said "Review the following policies:" and listed
them, while every policy carried the inverse "Part of [General Safety for All]"
line TYPED BY HAND. A flow object already existed in the content and had been
maintained in both directions manually. A `type: flow` was drafted for it and
dropped, because `30-programs/index.md` had already ruled: "a training is a
program wearing a different word. It is not a separate kind of object and does
not get separate machinery."

🚫 AND NO SECOND KEY. A program-specific `steps:` would be a second name for
one idea resolved by one function -- the shape this repo has retired three
manifests for. One key, one resolver, two types allowed to speak it.

⚠️ REPORTED, NEVER SILENTLY DROPPED, on a page that owns no ordering. That is
not politeness: this whole build exists because `sort:` sat in eleven content
files parsing as valid YAML and doing nothing, reported by no one.

⚠️ IT READS `state.BY_SRC`, NEVER THE NAV. That is the decoupling, in one line:
BY_SRC is populated at `on_files`, before anything prunes, so a chain can name
a page that no sidebar will ever show. Resolving through the nav would have
rebuilt the exact bug.

🔴 CROSS-FOLDER ALWAYS WORKED. IT WAS THE REPORT THAT WAS WRONG. Ids resolve
against every built page with no folder filter, so a program could always name
a policy two folders away. `_stragglers` was written folder-scoped in the same
commit and would have reported the OTHER PROGRAMS as missing from a program's
chain while never once mentioning the policies. ⚑ A feature that spans a tree
and a check that assumes a folder is one defect, not two, and the check is the
half that lies.
"""

from __future__ import annotations

from . import state

#: Types whose pages may declare `chain:`. See the legality section above.
#:
#: ⚠️ `index` IS ALSO MATCHED BY FILENAME, deliberately, and the two tests are
#: not redundant. A folder's landing page is frequently typed as its SUBJECT --
#: `venue`, `reference`, whatever it is genuinely about -- which frontmatter.md
#: explicitly blesses, and navstate already reads the site root's `nav:` by
#: filename for exactly this reason. A folder index typed `venue` still owns its
#: folder's order.
_CHAIN_TYPES = ("index", "program")


def _pages_in_order(items, out):
    for item in items:
        if getattr(item, "is_page", False):
            out.append(item)
        elif getattr(item, "children", None):
            _pages_in_order(item.children, out)
    return out


def _meta(src):
    return state.BY_SRC.get(src, {}) or {}


def _folder(src):
    """The directory part of a src_uri, '' at the site root."""
    return src.rsplit("/", 1)[0] if "/" in src else ""


def _built(files):
    """Every BUILT page, keyed by `id:` and by src_uri.

    ⚠️ INCLUDES PAGES THE NAV NO LONGER HOLDS, which is the entire point. An
    `unlisted` page is still built, still has a URL and still has a live Page
    object -- it was only removed from the sidebar. Walking `files` therefore
    sees exactly what walking the nav cannot.

    A duplicate `id:` is reported by objects.py already; here the FIRST one
    wins and the collision is named again, because a chain silently pointing at
    whichever page was walked second is worse than a chain that says so.

    ⚠️ `report=False` EXISTS FOR flowstrip, WHICH ASKS THE SAME QUESTION AT A
    LATER EVENT. Two callers and one implementation; the duplicate-id note would
    otherwise print twice per build and read as two collisions.
    """
    by_id: dict = {}
    by_src: dict = {}
    for f in files:
        page = getattr(f, "page", None)
        if page is None or not getattr(page, "is_page", False):
            continue
        src = getattr(f, "src_uri", "")
        if not src:
            continue
        by_src[src] = page
        pid = str(_meta(src).get("id") or "").strip()
        if not pid:
            continue
        if pid in by_id:
            state.note(
                "duplicate_id",
                "`chain:` resolution met the id `" + pid + "` twice ("
                + src + "). The FIRST page wins for every chain that names it.",
            )
            continue
        by_id[pid] = page
    return by_id, by_src


def _owns_ordering(src, meta) -> bool:
    """May this page declare a `chain:`? See `_CHAIN_TYPES`."""
    if src.rsplit("/", 1)[-1] == "index.md":
        return True
    return str((meta or {}).get("type") or "").strip().lower() in _CHAIN_TYPES


def declared(report: bool = True) -> dict:
    """Every legal `chain:` block, keyed by the src_uri that declared it.

    ⭐ PUBLIC, AND THAT IS THE POINT. `docrender/program.py` renders the flow
    strip from exactly this answer rather than re-parsing the key, because two
    parsers for one vocabulary is the defect this repo keeps killing. It passes
    `report=False` so the complaints are written once, by the stage that owns
    the decision.
    """
    out: dict = {}
    for src, meta in state.BY_SRC.items():
        raw = (meta or {}).get("chain")
        if raw is None:
            continue
        if not isinstance(raw, list):
            if report:
                state.note(
                    "missing_required",
                    src + " declares `chain:` as a " + type(raw).__name__
                    + ", not a list of ids. IGNORED -- that page's reading "
                    "order falls back to the sidebar.",
                )
            continue
        if not _owns_ordering(src, meta):
            if report:
                state.note(
                    "missing_required",
                    src + " declares `chain:`, which is legal only on a page "
                    "that OWNS AN ORDERING -- a folder `index.md`, or a page "
                    "typed " + " / ".join("`" + t + "`" for t in _CHAIN_TYPES)
                    + ". IGNORED, nothing was reordered.",
                )
            continue
        ids = [str(i).strip().lstrip("@") for i in raw if str(i).strip()]
        if ids:
            out[src] = ids
    return out


# Kept as a private alias so nothing that already imported the old name breaks.
_declared = declared


def _stragglers(src, ids, mine):
    """Pages that sit alongside this chain's MEMBERS and are not in it.

    🔴 SCOPED TO THE FOLDERS THE CHAIN ACTUALLY TOUCHES, not to the folder that
    DECLARED it. Those are the same place for a folder index and completely
    different places for a program, whose members live wherever they live. The
    first version of this function used the declaring page's folder and would
    have reported a program's SIBLING PROGRAMS as missing from its own chain
    while never mentioning a single policy.

    Not a defect and not corrected -- an omission is how an empty stub or a
    second hub stays out of a flow. It is reported because the OTHER reason a
    page is missing is that somebody forgot it, and those two are
    indistinguishable from here. Naming them is the join check; deciding is
    Michael's.
    """
    folders = {_folder(m) for m in mine}
    if not folders:
        return
    missing = []
    for other, meta in state.BY_SRC.items():
        if other == src or other in mine or _folder(other) not in folders:
            continue
        name = other.rsplit("/", 1)[-1]
        pid = str((meta or {}).get("id") or "").strip()
        # A folder index is a hub, never a step. Reporting it as "missing" on
        # every chain would train a reader to ignore this line.
        if pid and name != "index.md":
            missing.append(pid)
    if missing:
        state.note(
            "notes",
            src + " declares a `chain:` of " + str(len(ids)) + " and "
            + str(len(missing)) + " page(s) beside its members are NOT in it: "
            + ", ".join(sorted(missing))
            + ". Deliberate omissions are fine -- this is the join check, not a "
            "correction.",
        )


def _apply(files):
    decls = declared()
    if not decls:
        return

    by_id, by_src = _built(files)
    claimed: dict = {}

    for src in sorted(decls):
        ids = decls[src]
        hub = by_src.get(src)
        resolved = []
        mine = []
        for pid in ids:
            page = by_id.get(pid)
            if page is None:
                state.note(
                    "dead_links",
                    src + " `chain:` names `" + pid + "`, which is not the id "
                    "of any page on this site. SKIPPED -- the rest of the "
                    "chain still wires, so the flow has a gap rather than "
                    "being abandoned.",
                )
                continue
            if pid in claimed:
                # ⚠️ THE HONEST LIMIT OF prev/next, AND THE REASON THE FLOW
                # STRIP EXISTS. A MkDocs page has exactly ONE previous_page and
                # ONE next_page, so two flows through one page cannot both own
                # its buttons -- and which is correct depends on how the reader
                # ARRIVED, a per-request fact a static site does not have. The
                # first declaration keeps the buttons; program.py then renders a
                # strip for EVERY flow the page belongs to, which is additive
                # and has no slot to fight over.
                state.note(
                    "notes",
                    "`" + pid + "` is in two chains (" + claimed[pid] + " and "
                    + src + "). prev/next has ONE slot, so the first "
                    "declaration keeps the buttons. Both flows still render a "
                    "strip on that page -- that is what the strip is for.",
                )
                continue
            claimed[pid] = src
            resolved.append(page)
            mine.append(getattr(page.file, "src_uri", ""))

        if not resolved:
            state.note(
                "missing_required",
                src + " declares `chain:` and NONE of its " + str(len(ids))
                + " ids resolved. That page keeps the sidebar's reading order.",
            )
            continue

        for i, page in enumerate(resolved):
            page.previous_page = resolved[i - 1] if i > 0 else hub
            page.next_page = resolved[i + 1] if i + 1 < len(resolved) else None

        # The hub donates its Next and keeps its own Previous. See the docstring.
        if hub is not None:
            hub.next_page = resolved[0]

        state.note(
            "nav_default",
            src + " AUTHORED READING ORDER: " + str(len(resolved))
            + " page(s), independent of the sidebar. Pages that are `unlisted` "
            "or behind a `nav: hidden` folder are IN this chain and still out "
            "of the sidebar and out of search -- that separation is the "
            "feature. The last page's Next is deliberately empty: an authored "
            "flow ends rather than leaking back into the nav.",
        )
        _stragglers(src, ids, set(mine))


def on_nav(nav, config, files):
    pages = _pages_in_order(nav.items, [])
    if pages:
        # Replace the flat page list too. Material reads `nav.pages` for the
        # keyboard next/prev shortcuts, so leaving it stale would fix the
        # visible button and leave the invisible one wrong -- worse than not
        # fixing either.
        nav.pages = pages

        for i, page in enumerate(pages):
            page.previous_page = pages[i - 1] if i > 0 else None
            page.next_page = pages[i + 1] if i + 1 < len(pages) else None

    # AFTER the default wiring, never instead of it. An authored chain is an
    # override on the pages it names; everything else keeps the sidebar order.
    #
    # ⚠️ `nav.pages` is NOT re-derived from the chains. It drives Material's
    # keyboard shortcuts, and those walk the SIDEBAR -- a shortcut that jumps to
    # a page with no row to highlight would strand the reader somewhere the nav
    # cannot show them. The visible button follows the authored flow; the
    # keyboard follows the tree. Stated because the asymmetry is deliberate and
    # reads like an oversight.
    _apply(files)

    return nav
