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
PAGES: dict = {}

#: Foreign page maps from peer sites, keyed by peer slug.
PEERS: dict = {}

#: (when, change) for every row of the committed revision-log TSV, as read by
#: revlog.py. Newest first, because the file is written that way.
#:
#: ⚠️ TWO fields as of 2026-08-04, not four, and the reason is worth keeping:
#: revlog.py no longer reads git and no longer WRITES anything. It renders the
#: TSV the content repo's own workflow commits, and it only needs the two
#: columns the table shows. The `commit` and `pr` columns exist in the file and
#: are deliberately never carried into the site -- see revlog.py on the
#: no-route-back-to-source lock.
#:
#: This is now single-consumer, so it does not strictly need to live here. It
#: stays because the report line and any future stage that wants the log should
#: read one parse of one file rather than open it again.
REVLOG: list = []

#: The nav entries a ROUTED folder index took out of the sidebar, keyed by the
#: src_uri of that index page. Written by visibility.prune_nav (stage 00b),
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
#: ⭐ THIS IS THE ONE VALUE IN THIS FILE THAT GENUINELY CANNOT LIVE ANYWHERE
#: ELSE, worth saying because REVLOG above is honest about being here by
#: preference. Nav membership is decided in `on_nav`; the form that unseals it
#: is built in `on_page_content`. MkDocs runs EVERY hook's on_nav before ANY
#: hook's on_page_content, so those are two different events -- not two lines
#: that could have been moved next to each other.
#:
#: ⚠️ `u` is the build url exactly as MkDocs made it, root-relative and NOT
#: resolved against anything. Resolving it against the page doing the asking is
#: router.py's job, through util.relative_url. Two hooks have already shipped
#: the separator-counting version of that maths (see util.py) and a sealed url
#: gets it wrong INVISIBLY: nothing renders until somebody types a correct
#: code, and then it 404s.
NAV_SEALED: dict = {}

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
REPORT: dict = {}


def reset() -> None:
    global INSTANCE, TYPES, BY_SRC, PAGES, PEERS, REVLOG, NAV_SEALED
    global ROUTER_SALT, REPORT
    INSTANCE = {}
    TYPES = {}
    BY_SRC = {}
    PAGES = {}
    PEERS = {}
    REVLOG = []
    NAV_SEALED = {}
    ROUTER_SALT = b""
    REPORT = {
        # Order here is the order the report prints, and it is deliberate:
        # a duplicate KEY is usually the CAUSE of the complaints under it, so
        # it has to be read first. A reader who fixes a symptom before seeing
        # its cause fixes the wrong file.
        #
        # ⚠️ DECLARING A BUCKET HERE IS NOT ENOUGH TO MAKE IT PRINT. The report
        # loop iterates sizecheck._LABELS, so a bucket with no label is
        # collected and then silently dropped -- a check that runs, finds
        # things, and tells nobody. Add both, always.
        "duplicate_key": [],
        "missing_status": [],
        "missing_required": [],
        # Directly under missing_required, cause before symptom again: that
        # check says `summary` is absent, this one says where the text is.
        "body_lede": [],
        "unknown_type": [],
        "duplicate_id": [],
        "dead_links": [],
        "stale_xref": [],
        "markers": [],
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
