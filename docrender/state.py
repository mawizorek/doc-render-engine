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

#: (when, commit, pr, change) for every doc-touching commit, read out of git by
#: revlog.py. Lives here because it is used in two events: the table is drawn
#: during on_page_markdown and the downloadable TSV is written during
#: on_post_build. Reading git twice could return two different answers to the
#: same question, which is the sort of disagreement nobody reports.
#:
#: ⚠️ FOUR fields, and only two of them reach the page. `commit` and `pr` are
#: file-only by house rule -- revlog.py's docstring says why, and it is a lock
#: rather than an omission.
REVLOG: list = []

#: Site-relative output directories of the pages that carried a dr:revlog
#: marker, e.g. `01-utility/automatic-revision-log`. The TSV is written into
#: each one rather than at the site root, because the table links to it with a
#: bare relative href and `use_directory_urls` puts the page one level deeper
#: than its source file suggests. Root-writing was the 404 fixed 2026-08-04.
REVLOG_DIRS: list = []

#: Everything the build wants to tell a human. Printed in one block at the end
#: rather than scattered through 400 lines of output where nobody reads it.
REPORT: dict = {}


def reset() -> None:
    global INSTANCE, TYPES, BY_SRC, PAGES, PEERS, REVLOG, REVLOG_DIRS, REPORT
    INSTANCE = {}
    TYPES = {}
    BY_SRC = {}
    PAGES = {}
    PEERS = {}
    REVLOG = []
    REVLOG_DIRS = []
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
