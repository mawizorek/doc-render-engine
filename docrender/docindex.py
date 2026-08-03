"""Hook 09 -- publish the cross-site contract.

Writes /doc-index.json at the site root. This one small file is what makes
`@peer:id` links possible in every OTHER site in the family, which means it is
the only output of this build that other people's builds depend on.

Treat its shape as an interface, not an implementation detail. Adding a key is
fine. Renaming or removing one breaks every sibling that reads it, and they
will not notice until their next build turns a working link into a marker.

Runs last because it describes the finished site.

Hidden pages are absent by construction, not by filtering: visibility.py
removed them from the file set long before this ran, so there is no code path
here that could accidentally leak an unpublished page's existence.
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path

from . import __version__, state


def on_post_build(config):
    payload = {
        "site": state.INSTANCE.get("slug"),
        "name": state.INSTANCE.get("name"),
        "base_url": str(config.site_url or "").rstrip("/") + "/",
        "built": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "engine": __version__,
        "engine_ref": os.environ.get("DOCRENDER_ENGINE_REF", ""),
        "pages": sorted(state.PAGES.values(), key=lambda p: p["id"]),
    }

    out = Path(config.site_dir) / "doc-index.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Pages must serve our files verbatim. Jekyll treats {{ }} and {% %} as
    # template tags, fails SILENTLY, and a failed build makes Pages keep
    # serving the last successful one for the whole site. Written here rather
    # than committed to the content repo, because the content repo is not
    # allowed to hold machinery -- and this is machinery.
    (Path(config.site_dir) / ".nojekyll").write_text("", encoding="utf-8")
