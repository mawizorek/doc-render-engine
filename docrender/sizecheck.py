"""Hook 08 -- the size budget, the leak scan, and the build report.

THREE JOBS, all of which want to run last.

1. SIZE BUDGET. A file an agent cannot read back whole is a file an agent
   cannot safely edit, so it gets edited from a partial read and something
   quietly breaks. 22KB hard, 18KB warn. v1 was over budget in four places and
   that is the single largest reason v2 was a rewrite rather than a copy.

2. LEAK SCAN, and this is the one that keeps the family honest. The engine is
   only portable while it contains no site-specific string. That claim decays
   the instant nobody checks it, so we check it: if the active instance's own
   proper nouns appear anywhere in the engine source, the build FAILS. Not
   warns. It is the one hard failure in the pipeline, because it is the only
   check whose subject is the architecture itself rather than a page.

   An instance may narrow the scan with `leak_tokens:` in its site.yml. That
   exists for one honest reason: a slug that is also an ordinary English word
   produces noise rather than signal, and a check that cries wolf gets muted,
   which is worse than not having it.

3. THE REPORT. Everything every hook complained about, printed once, in one
   block, at the end. Warnings scattered through 400 lines of MkDocs output are
   warnings nobody reads.
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
    "leaks": "SITE NAME LEAKED INTO THE ENGINE (build will fail)",
    "missing_status": "Pages with no usable status (NOT BUILT)",
    "missing_required": "Missing required fields",
    "unknown_type": "Undeclared types (fell back to 'page')",
    "duplicate_id": "Duplicate ids",
    "dead_links": "Dead links (rendered as visible markers)",
    "stale_xref": "Cross-site index problems",
    "oversize": "Over the size budget",
    "notes": "Notes",
}


def _scan_sizes() -> None:
    content = Path(os.environ.get("DOCRENDER_CONTENT", "content"))
    targets = []
    if content.is_dir():
        targets += [p for p in content.rglob("*.md") if ".git" not in p.parts]
    targets += list((state.ENGINE_ROOT / "docrender").rglob("*.py"))

    for path in targets:
        try:
            kb = path.stat().st_size / 1024
        except OSError:
            continue
        is_guide = path.suffix == ".md" and "authoring" in path.parts
        limit = GUIDE_KB if is_guide else HARD_KB
        if kb > limit:
            state.note(
                "oversize",
                str(path) + " is " + format(kb, ".1f") + "KB, over the "
                + str(limit) + "KB limit. Split it.",
            )
        elif kb > WARN_KB and not is_guide:
            state.note(
                "notes",
                str(path) + " is " + format(kb, ".1f") + "KB, past the "
                + str(WARN_KB) + "KB warn line.",
            )


def _leak_tokens() -> list[str]:
    declared = state.INSTANCE.get("leak_tokens")
    if declared is not None:
        return [str(t) for t in declared if len(str(t)) > 2]
    candidates = [
        str(state.INSTANCE.get("slug", "")).strip(),
        str(state.INSTANCE.get("name", "")).strip(),
    ]
    return [c for c in candidates if len(c) > 2]


def _scan_leaks() -> bool:
    tokens = _leak_tokens()
    if not tokens:
        state.note(
            "notes",
            "leak scan skipped: this instance declares no tokens to scan for. "
            "The portability seam is unverified for this build.",
        )
        return False

    slug = str(state.INSTANCE.get("slug", "?"))
    roots = ["docrender", "objects", "theme", "assets", "hooks"]
    leaked = False

    for name in roots:
        root = state.ENGINE_ROOT / name
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for token in tokens:
                if re.search(re.escape(token), text, re.I):
                    leaked = True
                    state.note(
                        "leaks",
                        str(path.relative_to(state.ENGINE_ROOT)) + " mentions '"
                        + token + "'. The engine must not know which site it is "
                        + "rendering. Move it to instances/" + slug + "/.",
                    )
    return leaked


def on_post_build(config):
    _scan_sizes()
    leaked = _scan_leaks()

    name = str(state.INSTANCE.get("name", "?"))
    slug = str(state.INSTANCE.get("slug", "?"))

    print("")
    print("=" * 72)
    print("docrender build report -- " + name + " (" + slug + ")")
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
    print("Peer indexes loaded: " + (", ".join(sorted(state.PEERS)) or "none"))
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
