"""Per-build scratch state, shared across hooks.

MkDocs loads each hook file separately, so hooks cannot hand values to each
other directly. They all import THIS module instead, which is one shared
namespace for one build.

Why not stuff things onto `config`: config belongs to MkDocs, gets validated,
and gets copied in places. This is ours, and when a hook reads something
another hook wrote, the import makes that dependency visible in the file
instead of hiding it in a config key.

`reset()` runs from the first hook so `mkdocs serve`, which rebuilds in-process
on every save, never inherits the previous build's page map.

⚠️ EVERY VALUE HERE NEEDS A WRITER AND A READER IN DIFFERENT HOOKS. That is the
admission price, and it is worth stating because a shared namespace is the one
place a dead global survives indefinitely: nothing imports it by name, so
nothing breaks when its last user goes. `REVLOG` sat here after its reader went
away, labelled as staying \"by preference\", and was deleted with its writer on
2026-08-04. If a value is only ever touched by one module, it belongs in that
module.
"""

from pathlib import Path

#: Repo root of the engine itself (parent of this package).
ENGINE_ROOT = Path(__file__).resolve().parent.parent

#: Parsed instances/<slug>/site.yml for the site being built.
INSTANCE: dict = {}

#: Object type declarations, keyed by type name. From objects/*.yml.
TYPES: dict = {}

#: Frontmatter of every documentation page, keyed by src_uri. Populated BEFORE
#: visibility prunes anything, because a validation error on a hidden page is
#: still a validation error.
BY_SRC: dict = {}

#: The published page map, keyed by page id. Built AFTER visibility prunes, so
#: a link can never resolve to a page that was not built. That single sentence
#: is the entire reason the hook order is what it is.
#:
#: ⚠️ PLAIN ASSIGNMENT, SO A DUPLICATE ID IS LAST-WRITER-WINS. objects.py
#: REPORTS `duplicate_id` and the build still succeeds; this dict silently keeps
#: whichever page was walked second, and every inbound @-ref to that id lands
#: there. The loser still publishes -- it is a real file with a real URL -- it
#: simply becomes unreachable by id, which is the one failure the id mechanism
#: exists to prevent. /doc-refs.json makes it visible after the fact; nothing
#: prevents it yet.
PAGES: dict = {}

#: Foreign page maps from peer sites, keyed by peer slug.
PEERS: dict = {}

#: Every reference this build resolved, keyed by the SOURCE page id, each value
#: a dict of token -> {kind, target, ok, count}. Written by links.py (hook 03)
#: as each token is replaced, read by docindex.py (hook 09), which inverts it
#: into the inbound half and writes /doc-refs.json.
#:
#: ⭐ IT PAYS THE ADMISSION PRICE ABOVE, and how it pays it is the point: this
#: is not a cache of something computable later. links.py ALREADY resolves every
#: reference on every page -- it has to, that is how the token becomes an href --
#: and until 2026-08-06 it threw each answer away the instant it finished with
#: it. The graph existed for one function call per link and was never written
#: down. Recording it costs nothing because nothing new is computed, and the
#: report cannot disagree with the rendered page because the entry is written in
#: the same branch that produced the href.
#:
#: ⚠️ HIDDEN PAGES ARE ABSENT BY CONSTRUCTION, not by filtering. on_page_markdown
#: only runs for pages that survived visibility, so an unpublished page can
#: neither appear as a source nor resolve as a target. Do not add a filter
#: downstream -- there is nothing to filter, and a filter would imply otherwise.
REFS: dict = {}

#: The nav entries a ROUTED folder index took out of the sidebar, keyed by the
#: src_uri of that index page. Written by visibility.seal_nav (stage 00bc),
#: read by router.py (stage 04b), which seals each list under the page's own
#: codes and ships it as ciphertext.
#:
#: Shape, one entry per routed index:
#:
#:     anchor  the index page's own build url, so the client can find the one
#:             sidebar link it has to inject underneath
#:     items   the pruned entries in nav order. `t` title, `d` depth, and `u`
#:             the page's build url -- ABSENT on a folder heading, which is a
#:             label rather than a destination.
#:
#: ⭐ THIS IS THE CLEAREST CASE IN THE FILE FOR SOMETHING THAT GENUINELY CANNOT
#: LIVE ANYWHERE ELSE. Nav membership is decided in `on_nav`; the form that
#: unseals it is built in `on_page_content`. MkDocs runs EVERY hook's on_nav
#: before ANY hook's on_page_content, so those are two different events -- not
#: two lines that could have been moved next to each other.
#:
#: ⚠️ WHAT GOES IN HERE DEPENDS ON A STAGE ORDER, as of 2026-08-05. The seal
#: moved from 00b to 00bc so that navstate (00bb) cuts `nav: hidden` folders
#: FIRST -- otherwise their pages end up in this manifest and come back into the
#: sidebar on a correct code, which is exactly the bug that split the stages.
#: NAV_SHAPED below is how the seal checks it was not run too early.
#:
#: ⚠️ `u` is the build url exactly as MkDocs made it, root-relative and NOT
#: resolved against anything. Resolving it against the page doing the asking is
#: router.py's job, through util.relative_url. Two hooks have already shipped
#: the separator-counting version of that maths (see util.py) and a sealed url
#: gets it wrong INVISIBLY: nothing renders until somebody types a correct
#: code, and then it 404s.
NAV_SEALED: dict = {}

#: Folder indexes that resolved to `nav: expanded`, keyed by the index page's
#: build url with the slashes stripped. Written by navstate.shape (stage 00bb),
#: read by navstate.on_post_page (stage 06b), which checks the matching toggle
#: in the rendered sidebar.
#:
#: ⭐ IT PAYS THE ADMISSION PRICE ABOVE THE SAME WAY NAV_SEALED DOES, and for a
#: reason worth stating rather than assuming: what a folder does in the sidebar
#: is settled in `on_nav`, but Material expresses it as ONE attribute written
#: while rendering a page. Every hook's on_nav runs before any page is rendered,
#: so those are two events, not two lines.
#:
#: ⚠️ RESOLVED, not declared. A folder lands here because it said `expanded`
#: ITSELF, because an ancestor did, or because the SITE ROOT did -- navstate
#: settles the cascade before writing, so nothing downstream has to know which.
#:
#: ⚠️ A SET WEARING A DICT, deliberately. The membership test runs once per nav
#: toggle per page, nothing here has ever needed a set, and one shape for every
#: value in this module is what keeps `reset()` readable at a glance.
NAV_OPEN: dict = {}

#: Did stage 00bb run? Written by navstate.shape, read by visibility.seal_nav
#: (00bc), which reports loudly if it finds this false.
#:
#: ⭐ A CLAIM ABOUT THE PIPELINE, NOT A CACHED RESULT, and that is the only
#: reason a bare flag belongs in this module. Everything else here is data one
#: stage computed for another to consume. This answers "did the stage that must
#: precede me actually run" -- a question with no answer after the fact, because
#: a tree navstate never touched looks exactly like a tree where every folder
#: resolved to `collapsed`.
#:
#: ⚠️ SET UNCONDITIONALLY, AT THE TOP OF shape(), BEFORE ANY WALKING. It means
#: "the stage ran," never "the stage changed something": a site with no `nav:`
#: anywhere still shaped its tree, and keying this off whether anything moved
#: would report a broken hook list on every ordinary build.
NAV_SHAPED: bool = False

#: ONE PBKDF2 salt for every curtain VERIFIER on this build, minted on first
#: use by router.py and used by every `_check()` call on every page.
#:
#: ⭐ WHY THIS IS SHARED RATHER THAN PER-PAGE, WHICH IS WHAT IT WAS UNTIL
#: 2026-08-04. A fresh salt per page meant a code the reader had ALREADY typed
#: had to be re-derived at 120,000 iterations against a brand-new salt on every
#: single page view -- so nothing could be cached, and each navigation paid
#: 100-200ms per held key before the body appeared. Michael watched it happen:
#: "it's still like loading the menu each time and passing it immediately which
#: seems like bad architecture." It was. A shared salt makes the derived
#: verifier reusable, so the second page costs a string comparison.
#:
#: ⚠️ AND IT COSTS NOTHING, WHICH IS THE PART TO CHECK BEFORE ANYBODY
#: "HARDENS" IT BACK. A salt exists to stop ONE precomputed table being reused
#: against many targets. Every page on a site ships the same set of codes, so
#: per-page salts were defending the same secret from itself. The salt is still
#: random per build, so a table built against yesterday's deploy is worthless.
#:
#: 🚫 THIS IS FOR VERIFIERS ONLY. `router.py:_wrap` keeps its own random salt
#: and nonce per call, and must: that is AES-GCM ENCRYPTION, where reusing key
#: material across different plaintexts is a real weakness rather than a
#: cosmetic one. Do not tidy the two into one salt.
ROUTER_SALT: bytes = b""

#: Everything the build wants to tell a human. Printed in one block at the end
#: rather than scattered through 400 lines of output where nobody reads it.
#:
#: ⚠️ THIS IS THE COLLECTOR, NEVER THE RENDERER. docrender/report.py owns what
#: the sections are called, what order they print in and which of them are
#: inventory; hook 08 prints what it returns and hook 08b puts the same string on
#: the site. Writing into this dict is all a hook ever does with the report.
REPORT: dict = {}


def reset() -> None:
    global INSTANCE, TYPES, BY_SRC, PAGES, PEERS, REFS, NAV_SEALED, NAV_OPEN
    global NAV_SHAPED, ROUTER_SALT, REPORT
    INSTANCE = {}
    TYPES = {}
    BY_SRC = {}
    PAGES = {}
    PEERS = {}
    REFS = {}
    NAV_SEALED = {}
    NAV_OPEN = {}
    NAV_SHAPED = False
    ROUTER_SALT = b""
    REPORT = {
        # THE BUCKETS THAT EXIST. Roughly print order as a courtesy, and only
        # roughly -- see the warning below.
        #
        # 🔴 THIS DICT DOES NOT DECIDE THE PRINT ORDER AND THIS COMMENT USED TO
        # SAY IT DID. The report loop iterates `_LABELS`, not this, so the order
        # that matters lives there. The two are not even the same today: `leaks`
        # is second-to-last here and FIRST over there, which is correct, because
        # a site name in engine code fails the build and has to be read first.
        # Reordering this dict to move a report section does nothing at all.
        #
        # ⚠️ AND `_LABELS` MOVED HOUSE ON 2026-08-07. It was sizecheck's; it is
        # now `docrender/report.py`'s, because a second destination appeared and
        # a report built inside its printer cannot render anywhere else. Repointed
        # in the commit that moved it rather than the session after.
        #
        # ⚠️ DECLARING A BUCKET HERE IS STILL NOT ENOUGH TO MAKE IT PRINT, and
        # the split made that warning matter MORE rather than less: the second
        # edit is now in a different FILE, not three hundred lines down this one.
        # A bucket with no label in report._LABELS is collected all build and then
        # silently dropped -- a check that runs, finds things, and tells nobody.
        # Adding a report section is always TWO edits, here and there.
        "duplicate_key": [],
        "missing_status": [],
        "missing_required": [],
        # Directly under missing_required, cause before symptom: that check says
        # `summary` is absent, this one says where the text is.
        "body_lede": [],
        # The same migration one field over, added 2026-08-07: `revised:` is
        # drawn at the foot now, and these pages still type it into the body.
        # Beside body_lede on purpose -- they are the same shape, and a reader
        # hitting one wants the other in the same glance.
        #
        # ⭐ THE FIRST NEW BUCKET SINCE THE TWO-EDITS WARNING WAS WRITTEN, so
        # it is worth recording that the warning worked: the label in
        # sizecheck._LABELS went in during the same commit, and without it this
        # line would have collected findings all build and printed none.
        # (That label now lives in report._LABELS -- it moved hours later, in the
        # split described above. The history is left as it happened.)
        "body_revised": [],
        "unknown_type": [],
        "duplicate_id": [],
        "dead_links": [],
        "stale_xref": [],
        "markers": [],
        # The site-wide sidebar default, from the root index's `nav:`. Sits with
        # the nav reports rather than in `notes`, which prints last: a fact
        # governing every folder on the site cannot be the line under forty size
        # warnings. INVENTORY, not a defect -- see report._INVENTORY.
        "nav_default": [],
        # The names `publish <name>` accepts for this site: the slug plus the
        # `aliases:` block in site.yml. INVENTORY like nav_default -- a list of
        # names a site answers to is a worklist, never a defect, and counting it
        # would mean no build on any site ever prints "No findings" again.
        #
        # ⭐ WHY THE BUILD REPORTS THIS AT ALL, given that only a shell function
        # consumes the aliases: because the alternative is a config key with no
        # reader anywhere in the engine, and this repo already writes down what
        # that costs -- "a config key that does nothing while looking like it
        # does something is the failure this engine keeps writing down"
        # (instance.py, on the inert `palette:` block). Printing them makes the
        # key demonstrably live, and puts a typo'd alias in front of a human on
        # the next build instead of at 10pm on the command line.
        "aliases": [],
        # Nav sealing reports in here too, deliberately rather than in a bucket
        # of its own: somebody asking what the routers did wants the curtain
        # and the sealed subtree in one place, because each is misleading on
        # its own.
        "routers": [],
        "oversize": [],
        "leaks": [],
        "notes": [],
    }


def note(bucket: str, message: str) -> None:
    REPORT.setdefault(bucket, []).append(message)


def ref(source: str, token: str, kind: str, target: str, ok: bool) -> None:
    """Record one resolved reference. Called from links.py, once per token.

    Deduplicated per source page and COUNTED rather than listed twice: a page
    that links the same target three times has one edge with `count: 3`, which
    is the shape a reader wants and keeps the file small on an index page that
    links forty siblings.
    """
    if not source:
        return
    edges = REFS.setdefault(source, {})
    existing = edges.get(token)
    if existing:
        existing["count"] += 1
        return
    edges[token] = {"kind": kind, "target": target, "ok": ok, "count": 1}
