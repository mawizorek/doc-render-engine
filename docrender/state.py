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

#: Everything the build wants to tell a human. Printed in one block at the end
#: rather than scattered through 400 lines of output where nobody reads it.
REPORT: dict = {}


def reset() -> None:
    global INSTANCE, TYPES, BY_SRC, PAGES, PEERS, REVLOG, REPORT
    INSTANCE = {}
    TYPES = {}
    BY_SRC = {}
    PAGES = {}
    PEERS = {}
    REVLOG = []
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
        "routers": [],
        "oversize": [],
        "leaks": [],
        "notes": [],
    }


def note(bucket: str, message: str) -> None:
    REPORT.setdefault(bucket, []).append(message)
