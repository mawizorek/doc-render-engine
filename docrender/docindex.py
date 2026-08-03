"""Hook 09 -- publish the cross-site contract, and report what changed.

TWO JOBS.

1. `/doc-index.json` at the site root. One small file that makes `@peer:id`
   links possible in every OTHER site in the family, which makes it the only
   output of this build that other people's builds depend on. Treat its shape
   as an interface: adding a key is fine, renaming or removing one breaks every
   sibling, and they will not notice until their next build turns a working
   link into a broken marker.

2. THE PUBLISH PREVIEW. Fetches the index the LIVE site is currently serving
   and diffs it against the one just built, then writes the result to the
   Actions run summary.

   This exists because of a real gap in the workflow, not as a nicety. A
   content repo holds no workflow of its own -- that is the purity rule -- so
   publishing is a deliberate act somebody takes, and until now that act was
   blind: you pressed a button and hoped. Now the run tells you exactly which
   pages are new, which are gone, and which were renamed or re-typed, before
   or after they land.

   In `dry_run` mode nothing deploys and this report is the entire output. That
   is the difference between a manual build and a publish step you can trust:
   the second one shows you the diff first.

Runs last because it describes the finished site.

Hidden pages are absent by construction, not by filtering: visibility.py
removed them from the file set long before this ran, so there is no code path
here that could leak an unpublished page's existence -- including into this
report, which is worth stating because a diff is exactly the sort of thing that
accidentally lists what it was meant to exclude.
"""

from __future__ import annotations

import datetime
import json
import os
import urllib.request
from pathlib import Path

from . import __version__, state

_TIMEOUT = 10


def _live_index(base_url: str) -> dict | None:
    """What the published site is serving right now, or None if unreachable."""
    if not base_url:
        return None
    url = base_url.rstrip("/") + "/doc-index.json"
    try:
        with urllib.request.urlopen(url, timeout=_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        # A site that has never published has no index. Not an error: it is the
        # first publish, and the report says so rather than showing a diff
        # against nothing and calling every page "new" without explanation.
        return None


def _summary(payload: dict) -> str:
    name = str(state.INSTANCE.get("name", "?"))
    slug = str(state.INSTANCE.get("slug", "?"))
    dry = os.environ.get("DOCRENDER_DRY_RUN") == "1"

    lines = [
        "## " + ("🔍 Preview: " if dry else "🚀 Publishing: ") + name,
        "",
        "`" + slug + "` · " + str(len(payload["pages"])) + " pages · "
        + str(payload["base_url"]),
        "",
    ]

    live = _live_index(str(payload.get("base_url", "")))
    if live is None:
        lines += [
            "**First publish.** No index is being served at that address yet, "
            "so there is nothing to compare against. Everything below is new.",
            "",
        ]
        for page in payload["pages"]:
            lines.append("- 🆕 `" + page["id"] + "` — " + page["title"])
        return "\n".join(lines) + "\n"

    was = {p.get("id"): p for p in live.get("pages", []) if p.get("id")}
    now = {p["id"]: p for p in payload["pages"]}

    added = [i for i in now if i not in was]
    removed = [i for i in was if i not in now]
    changed = [
        i for i in now
        if i in was and (
            now[i]["title"] != was[i].get("title")
            or now[i]["url"] != was[i].get("url")
            or now[i]["type"] != was[i].get("type")
        )
    ]

    if not (added or removed or changed):
        lines += [
            "**No page-level changes.** Same pages, same titles, same URLs.",
            "",
            "Page BODIES may still have changed — this compares the index, "
            "not the prose. An edit to a paragraph shows up here as nothing, "
            "which is correct and worth knowing before you read too much into "
            "a quiet report.",
            "",
            "Live index built: " + str(live.get("built", "unknown")),
        ]
        return "\n".join(lines) + "\n"

    if added:
        lines += ["### 🆕 New pages (" + str(len(added)) + ")", ""]
        for i in sorted(added):
            lines.append("- `" + i + "` — " + now[i]["title"] + "  \n  " + now[i]["url"])
        lines.append("")

    if removed:
        lines += [
            "### 🗑️ Pages that will DISAPPEAR (" + str(len(removed)) + ")",
            "",
            "⚠️ A page vanishes for two very different reasons: it was deleted, "
            "or its `status:` is no longer public. Both look identical here. "
            "Check before publishing — and remember that any OTHER site linking "
            "to one of these ids will start rendering a broken reference.",
            "",
        ]
        for i in sorted(removed):
            lines.append("- `" + i + "` — " + str(was[i].get("title", "?")))
        lines.append("")

    if changed:
        lines += ["### ✏️ Moved or renamed (" + str(len(changed)) + ")", ""]
        for i in sorted(changed):
            old, new = was[i], now[i]
            bits = []
            if old.get("title") != new["title"]:
                bits.append(str(old.get("title")) + " → " + new["title"])
            if old.get("url") != new["url"]:
                bits.append("`" + str(old.get("url")) + "` → `" + new["url"] + "`")
            if old.get("type") != new["type"]:
                bits.append("type " + str(old.get("type")) + " → " + new["type"])
            lines.append("- `" + i + "` — " + "; ".join(bits))
        lines.append("")

    lines.append("Live index built: " + str(live.get("built", "unknown")))
    return "\n".join(lines) + "\n"


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

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        try:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write(_summary(payload))
        except OSError:
            pass
