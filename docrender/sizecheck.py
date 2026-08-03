"""Hook 08 -- the size budget, the leak scan, and the build report.

THREE JOBS, all of which want to run last.

1. SIZE BUDGET. A file an agent cannot read back whole is a file an agent
   cannot safely edit, so it gets edited from a partial read and something
   quietly breaks. 22KB hard, 18KB warn. v1 was over budget in four places and
   that is the single largest reason v2 was a rewrite rather than a copy.

2. LEAK SCAN, and this is the one that keeps the family honest. The engine is
   only portable while it contains no site-specific string. That claim decays
   the instant nobody checks it, so we check it: if the active instance's own
   name appears anywhere in the engine source, the build FAILS. Not warns.
   This is the one hard failure in the whole pipeline, because it is the only
   check whose subject is the architecture itself.

3. THE REPORT. Everything every hook complained about, printed once, in one
   block, at the end. Warnings scattered through 400 lines of MkDocs output
   are warnings nobody reads.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from . import state

HARD_KB = 22
WARN_KB = 18
GUIDE_KB = 12

_LABELS = {
    "missing_status": "Pages with no usable status (NOT BUILT)",
    "unknown_type": "Undeclared types (fell back to 'page')",
    "missing_required": "Missing required fields",
    "duplicate_id": "Duplicate ids",
    "dead_links": "Dead links (rendered as markers)",
    "stale_xref": "Cross-site index problems",
    "oversize": "Over the size budget",
    "leaks": "SITE NAME LEAKED INTO THE ENGINE",
    "notes": "Notes",
}


def _scan_sizes() -> None:
    content = Path(os.environ.get("DOCRENDER_CONTENT", "content"))
    targets = []
    if content.is_dir():
        targets += [p for p in content.rglob("*.md") if ".git" not in p.parts]
    targets += [p for p in (state.ENGINE_ROOT / "docrender").rglob("*.py")]

    for path in targets:
        try:
            kb = path.stat().st_size / 1024
        except OSError:
            continue
        limit = GUIDE_KB if path.suffix == ".md" and "authoring" in path.parts else HARD_KB
        if kb > limit:
            state.note(
                "oversize",
                str(path) + " is " + format(kb, ".1f") + "KB, over the "
                + str(limit) + "KB limit. Split it.",
            )
        elif kb > WARN_KB and limit == HARD_KB:
            state.note(
                "notes",
                str(path) + " is " + format(kb, ".1f") + "KB, past the "
                + str(WARN_KB) + "KB warn line.",
            )


def _scan_leaks() -> bool:
    """Return True if the engine mentions the site it is currently rendering."""
    slug = str(state.INSTANCE.get("slug", "")).strip()
    name = str(state.INSTANCE.get("name", "")).strip()
    needles = [n for n in (slug, name) if len(n) > 2]
    if not needles:
        return False

    patterns = [re.compile(re.escape(n), re.I) for n in needles]
    leaked = False
    roots = [state.ENGINE_ROOT / "docrender", state.ENGINE_ROOT / "objects",
             state.ENGINE_ROOT / "theme", state.ENGINE_ROOT / "assets",
             state.ENGINE_ROOT / "hooks"]

    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for needle, pattern in zip(needles, patterns):
                if pattern.search(text):
                    leaked = True
                    state.note(
                        "leaks",
                        str(path.relative_to(state.ENGINE_ROOT)) + " mentions '"
                        + needle + "'. The engine must not know which site it "
                        + "is rendering. Move it to instances/" + slug + "/.",
                    )
    return leaked


def on_post_build(config):
    _scan_sizes()
    leaked = _scan_leaks()

    print("")
    print("=" * 72)
    print("docrender build report -- " + str(state.INSTANCE.get("name", "?"))
          + " (" + str(state.INSTANCE.get("slug", "?")) + ")")
    print("=" * 72)

    clean = True
    for bucket, label in _LABELS.items():
        entries = state.REPORT.get(bucket) or []
        if not entries:
            continue
        clean = False
        print("")
        print(label + " (" + str(len(entries)) + ")")
        for entry in entries:
            print("  - " + entry)

    print("")
    print("Pages published: " + str(len(state.PAGES)))
    peers = ", ".join(sorted(state.PEERS)) or "none"
    print("Peer indexes loaded: " + peers)
    if clean:
        print("No findings. Everything declared, everything resolved.")
    print("=" * 72)
    print("")

    if leaked:
        print(
            "::error::docrender: the engine contains the name of the site it "
            "is rendering. That is the one failure this pipeline refuses to "
            "warn about, because a portable engine stops being portable "
            "silently.",
            file=sys.stderr,
        )
        raise SystemExit(1)
