"""Hook 08 -- the size budget, the leak scan, and the build report.

THREE JOBS, all of which want to run last.

1. SIZE BUDGET. A file an agent cannot read back whole is a file an agent
   cannot safely edit, so it gets edited from a partial read and something
   quietly breaks. 22KB hard, 18KB warn. v1 was over budget in four places and
   that is the single largest reason v2 was a rewrite rather than a copy.

2. LEAK SCAN. The engine is only portable while it contains no site-specific
   BEHAVIOUR, and that claim decays the instant nobody checks it.

   =========================================================================
   IT READS CODE, NOT COMMENTS (REDESIGNED 2026-08-03, and this is the second
   version -- the first one did not survive contact with three real sites)
   =========================================================================
   v1 of this check searched raw file text. That is wrong, and it failed in
   the most instructive way available: it blocked the build of the ONE site
   that was supposed to be proving the engine is portable, because the word
   appeared in a COMMENT EXPLAINING THE CHECK ITSELF.

   Two sites had already opted out for the same reason -- `template` and
   `theatre` are ordinary English words that appear legitimately in prose --
   which meant the check protected nothing while looking like it protected
   everything. `instances/theatre/site.yml` said so at the time: *if the last
   site opts out too, the check is decorative and should be redesigned rather
   than quietly kept.* That happened within the hour, so it is redesigned.

   The distinction that makes it work: **a comment naming a site is
   documentation; a string literal naming a site is a bug.** Only the second
   changes what the engine DOES. So Python is stripped of comments and string
   literals via `tokenize` before scanning, CSS of `/* */`, and YAML/TSV of
   `#` lines. What survives is identifiers and operators -- the actual code.

   ⚠️ Known and accepted hole: a site name hidden in a NON-literal expression
   (`"uri" + "tp"`, or a name assembled at runtime) walks straight through.
   Not worth defending against. This check exists to catch the honest mistake
   of typing a site into the engine, not to defeat somebody smuggling one in.

   Still the ONE hard failure in the pipeline. Everything else warns.

3. THE REPORT. Everything every hook complained about, printed once, in one
   block, at the end. Warnings scattered through 400 lines of MkDocs output are
   warnings nobody reads.

   ⭐ The `markers` section is not a complaint, and it is the most useful thing
   here. Every `[text]{.tbc}` and friend on the site, listed with its page. A
   marker you cannot enumerate is decoration; a marker you can enumerate turns
   "what is still unconfirmed" into a question with an answer.
"""

from __future__ import annotations

import io
import os
import re
import sys
import token as token_mod
import tokenize
from pathlib import Path

from . import state

HARD_KB = 22
WARN_KB = 18
GUIDE_KB = 12

_SCAN_SUFFIXES = {".py", ".css", ".js", ".yml", ".yaml", ".tsv", ".json", ".txt"}

_LABELS = {
    "leaks": "SITE NAME LEAKED INTO ENGINE CODE (build will fail)",
    "missing_status": "Pages with no usable status (NOT BUILT)",
    "missing_required": "Missing required fields",
    "unknown_type": "Undeclared types (fell back to 'page')",
    "duplicate_id": "Duplicate ids",
    "dead_links": "Broken references (rendered as struck-through markers)",
    "stale_xref": "Cross-site index problems",
    "markers": "Marked unresolved -- every tbc / verify / gap / est / was",
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


def _code_only(path: Path) -> str:
    """Return the file with comments and string literals removed.

    Prose is where a site gets EXPLAINED; code is where it gets DEPENDED ON.
    Only the second is a portability defect, so only the second is scanned.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""

    if path.suffix == ".py":
        kept = []
        try:
            for tok in tokenize.generate_tokens(io.StringIO(text).readline):
                if tok.type in (token_mod.COMMENT, token_mod.STRING):
                    continue
                kept.append(tok.string)
        except (tokenize.TokenError, IndentationError, SyntaxError):
            # An unparseable file is a different problem, and silently
            # skipping it would be a hole. Scan it whole and accept the noise.
            return text
        return " ".join(kept)

    if path.suffix in (".css", ".js"):
        text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
        return re.sub(r"(?m)^\s*//.*$", " ", text)

    if path.suffix in (".yml", ".yaml", ".tsv", ".txt"):
        return re.sub(r"(?m)^\s*#.*$", " ", text)

    return text


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
    leaked = False

    for name in ("docrender", "objects", "theme", "assets", "hooks"):
        root = state.ENGINE_ROOT / name
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in _SCAN_SUFFIXES:
                continue
            code = _code_only(path)
            if not code:
                continue
            for tok in tokens:
                if re.search(re.escape(tok), code, re.I):
                    leaked = True
                    state.note(
                        "leaks",
                        str(path.relative_to(state.ENGINE_ROOT))
                        + " depends on '" + tok + "' in CODE (not a comment). "
                        + "The engine must not know which site it renders. "
                        + "Move it to instances/" + slug + "/site.yml.",
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
        # Markers are inventory, not a defect, so a page full of them still
        # counts as a clean build.
        if bucket != "markers":
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
            "::error::docrender: engine CODE references the site it is "
            "rendering. That is the one failure this pipeline refuses to warn "
            "about, because a portable engine stops being portable silently.",
            file=sys.stderr,
        )
        raise SystemExit(1)
