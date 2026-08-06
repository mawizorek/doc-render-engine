"""Hook 09 -- publish the cross-site contract, the reference graph, and a diff.

THREE JOBS.

1. `/doc-index.json` at the site root. One small file that makes `@peer:id`
   links possible in every OTHER site in the family, which makes it the only
   output of this build that other people's builds depend on. Treat its shape
   as an interface: adding a key is fine, renaming or removing one breaks every
   sibling, and they will not notice until their next build turns a working
   link into a broken marker.

2. `/doc-refs.json` at the site root. The whole reference graph: for every
   page, what it references and what references it.

   ⭐ IT COSTS NOTHING TO BUILD, and that is the argument for it existing.
   links.py already resolves every reference on every page -- it must, that is
   how a token becomes an href -- and until 2026-08-06 it discarded each answer
   immediately. The graph was computed on every single build and never written
   down. This inverts what was recorded; the inbound half is free.

   🔴 A SEPARATE FILE, NOT MORE KEYS ON THE INDEX ABOVE. The index is an
   interface every peer fetches on every build. Hanging a full graph off it
   would make six sibling sites download the reference map of a site they read
   five keys from, forever. Two files with two jobs; only one of them is a
   contract.

   ⚠️ `inbound: 0` IS REPORTED AS A COUNT AND IS DELIBERATELY NOT CALLED
   "ORPHAN". A page reached through the sidebar has zero inbound REFERENCES and
   is perfectly reachable. Nav membership is not in this graph and this file
   does not pretend otherwise -- a metric that quietly redefines its own word is
   worse than no metric.

3. THE PUBLISH PREVIEW. Fetches the index the LIVE site is currently serving
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
accidentally lists what it was meant to exclude. The same guarantee covers the
reference graph for the same reason: on_page_markdown never ran for a hidden
page, so it is neither a source nor a resolvable target.
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


def _refs_payload(index: dict) -> dict:
    """Invert state.REFS into the two-directional graph.

    Outbound was recorded by links.py as it resolved. Inbound is this loop and
    nothing else -- an edge already known, read from the other end.
    """
    known = {p["id"]: p for p in index["pages"]}

    pages: dict = {}
    for page_id, meta in known.items():
        pages[page_id] = {
            "title": meta.get("title"),
            "url": meta.get("url"),
            "type": meta.get("type"),
            "references": [],
            "referenced_by": [],
        }

    # Sources with no `id:` of their own. They still link OUT, so their edges
    # count toward every target's inbound list, but they can never be a target
    # themselves. Kept apart rather than mixed in, because a bare path sitting
    # among page ids reads like an id and is not one.
    unidentified: dict = {}
    broken: list = []

    for source, edges in state.REFS.items():
        bucket = pages.get(source)
        if bucket is None:
            bucket = unidentified.setdefault(source, {"references": []})

        for token, edge in sorted(edges.items()):
            bucket["references"].append({
                "token": token,
                "kind": edge["kind"],
                "target": edge["target"],
                "resolved": edge["ok"],
                "count": edge["count"],
            })
            if not edge["ok"]:
                broken.append({"from": source, "token": token, "kind": edge["kind"]})
            elif edge["kind"] == "page" and edge["target"] in pages:
                back = pages[edge["target"]]["referenced_by"]
                if source not in back:
                    back.append(source)

    for page_id, bucket in pages.items():
        bucket["referenced_by"].sort()
        bucket["inbound"] = len(bucket["referenced_by"])
        bucket["outbound"] = len(bucket["references"])

    no_inbound = sorted(i for i, b in pages.items() if b["inbound"] == 0)

    return {
        "site": index["site"],
        "base_url": index["base_url"],
        "built": index["built"],
        "engine": index["engine"],
        "totals": {
            "pages": len(pages),
            "edges": sum(b["outbound"] for b in pages.values())
            + sum(len(b["references"]) for b in unidentified.values()),
            "broken": len(broken),
            "no_inbound": len(no_inbound),
        },
        # ⚠️ NOT "orphans". Zero inbound REFERENCES; the sidebar is not in this
        # graph. See the module docstring.
        "no_inbound": no_inbound,
        "broken": sorted(broken, key=lambda b: (b["from"], b["token"])),
        "pages": pages,
        "unidentified_sources": unidentified,
    }


def _refs_summary(refs: dict) -> str:
    t = refs["totals"]
    lines = [
        "",
        "### 🔗 Reference graph",
        "",
        "`" + str(t["edges"]) + "` references across `" + str(t["pages"])
        + "` pages · [`/doc-refs.json`]("
        + str(refs.get("base_url", "")) + "doc-refs.json)",
        "",
    ]

    if t["broken"]:
        lines += [
            "🔴 **" + str(t["broken"]) + " broken reference(s).** Each renders as a "
            "struck-through span with no href, so a reader sees it too.",
            "",
        ]
        for b in refs["broken"][:20]:
            lines.append("- `" + b["from"] + "` → `@" + b["token"] + "`")
        if t["broken"] > 20:
            lines.append("- _…and " + str(t["broken"] - 20) + " more in the JSON._")
        lines.append("")
    else:
        lines += ["✅ No broken references.", ""]

    if refs["unidentified_sources"]:
        lines += [
            "⚠️ **" + str(len(refs["unidentified_sources"]))
            + " page(s) link out but declare no `id:`**, so nothing can link back "
            "to them. Listed by path in the JSON.",
            "",
        ]

    if t["no_inbound"]:
        lines += [
            "ℹ️ **" + str(t["no_inbound"]) + " page(s) have no inbound references.** "
            "That is not the same as unreachable — the sidebar is navigation, not "
            "references, and is not counted here. It means nothing in the PROSE "
            "points at them.",
            "",
        ]

    return "\n".join(lines) + "\n"


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

    refs = _refs_payload(payload)
    (Path(config.site_dir) / "doc-refs.json").write_text(
        json.dumps(refs, indent=2) + "\n", encoding="utf-8"
    )

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
                fh.write(_refs_summary(refs))
        except OSError:
            pass
