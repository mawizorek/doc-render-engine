"""Hook 08 -- the size budget, the leak scan, and printing the build report.

THREE JOBS, all of which want to run last.

1. SIZE BUDGET. A file an agent cannot read back whole is a file an agent
   cannot safely edit, so it gets edited from a partial read and something
   quietly breaks. 22KB hard, 18KB warn. v1 was over budget in four places and
   that is the single largest reason v2 was a rewrite rather than a copy.

   ⚠️ IT COVERS assets/ AS OF 2026-08-04, AND THE HOLE WAS FOUND BY SOMEBODY
   CITING A WARNING THAT COULD NEVER HAVE FIRED. This scan walked content *.md
   and docrender *.py and nothing else, so every stylesheet and script in the
   engine was unbudgeted -- including the two largest files it owns. base.css
   crossed the warn line and was split on the strength of a rule that was not
   being enforced on it. The split was still correct: the read-whole limit is a
   property of the READ PATH, not of this hook, and a stylesheet clips on a read
   exactly like a module does. But an unenforced rule is a rule that survives
   only as long as everybody remembers it, which is not a mechanism.

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
   everything.

   The distinction that makes it work: **a comment naming a site is
   documentation; a string literal naming a site is a bug.** Only the second
   changes what the engine DOES. So Python is stripped of comments and string
   literals via `tokenize` before scanning, CSS of `/* */`, and YAML/TSV of
   `#` lines. What survives is identifiers and operators -- the actual code.

   🔴 AND THERE IS A WHOLE FILE TYPE THE DISTINCTION CANNOT REACH: JSON.
   `.json` is in _SCAN_SUFFIXES, so it IS scanned, but `_code_only` has no
   branch for it and cannot have one -- JSON HAS NO COMMENT SYNTAX, so every
   word in a .json file is a string literal and there is nothing to strip.
   Prose in a .json file therefore reads exactly like a dependency. It failed a
   real site build on 2026-08-05: a theme's `intendedUse` sentence described
   what a look was FOR by naming a company whose name is also a site slug.
   The fix is not more stripping -- there is nothing to strip. It is a stricter
   DATA rule, written into the JSON files themselves: never name a customer, a
   site or a slug in engine JSON, prose included. See theme/canonical/themes.json
   `rules.no-customers-no-sites`, and note the sibling shape -- v1 of this check
   died of treating prose as code, and JSON is the one place it still does.

   ⚠️ Known and accepted hole: a site name hidden in a NON-literal expression
   walks straight through. Not worth defending against. This catches the honest
   mistake of typing a site into the engine, not somebody smuggling one in.

   ⚠️ AND IT DOES NOT SCAN instances/, WHICH IS CORRECT. That tree is the DATA
   the engine reads, and naming a site there is the entire purpose of the file --
   this scan's own error message sends leaks there. An `aliases:` entry reading
   "HML LLC" in instances/hml/site.yml is right; the same words in theme/ are a
   build failure. Same words, opposite verdicts, one rule.

   Still the ONE hard failure in the pipeline. Everything else warns.

3. PRINTING THE REPORT. Everything every hook complained about, in one block, at
   the end. Warnings scattered through 400 lines of MkDocs output are warnings
   nobody reads.

   ⭐ THE REPORT ITSELF MOVED TO docrender/report.py ON 2026-08-07, AND ONLY THE
   PRINTING IS STILL HERE. It left because a second destination appeared -- a
   page on the site -- and the section list was welded to the print loop, so
   rendering it anywhere else meant writing it twice. Two renderers of one object
   disagree within a month; this repo has retired three manifests for that shape.

   What went: `_LABELS` (which sets cause-before-symptom section order),
   `_INVENTORY`, and the walk. What stayed: the two SCANS above, because they are
   CHECKS rather than reports, and one line that prints what report.py returns.

   ⚠️ SO "ADDING A REPORT SECTION IS TWO EDITS" NOW POINTS AT A DIFFERENT FILE,
   and is unchanged in every other respect: `state.reset()` declares the bucket,
   `report._LABELS` gives it a label and therefore a place in the walk. A bucket
   carrying only one of those is collected all build and dropped without a word.

   🔴 AND THE CALL ORDER IN on_post_build IS NOW LOAD-BEARING ACROSS A MODULE
   BOUNDARY rather than inside one function, which is a weaker place for it to
   live, so it is written down: the two scans are the LAST writers into
   state.REPORT, and a report rendered before them is missing every oversize file
   and every leak. The scans run first. Nothing enforces that but this sentence.
"""

from __future__ import annotations

import io
import os
import re
import sys
import token as token_mod
import tokenize
from pathlib import Path

from . import report, state

HARD_KB = 22
WARN_KB = 18
GUIDE_KB = 12

_SCAN_SUFFIXES = {".py", ".css", ".js", ".yml", ".yaml", ".tsv", ".json", ".txt"}

#: What the size budget walks. `assets` joined on 2026-08-04 -- see job 1 above.
#: ⚠️ A DATA FILE IS NOT SOURCE AND IS NOT BUDGETED. A 40KB TSV is a big
#: spreadsheet, not an unreadable module: nothing edits it from a partial read,
#: because nothing edits it at all. Budgeting content would turn a size gate into
#: an opinion about how much documentation somebody is allowed to have.
_ENGINE_SOURCE = (
    ("docrender", (".py",)),
    ("assets", (".css", ".js")),
)


def _scan_sizes() -> None:
    content = Path(os.environ.get("DOCRENDER_CONTENT", "content"))
    targets = []
    if content.is_dir():
        targets += [p for p in content.rglob("*.md") if ".git" not in p.parts]
    for folder, suffixes in _ENGINE_SOURCE:
        root = state.ENGINE_ROOT / folder
        if not root.is_dir():
            continue
        targets += [p for p in root.rglob("*") if p.suffix in suffixes]

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

    🔴 EXCEPT FOR .json, WHICH FALLS THROUGH UNSTRIPPED, AND THAT IS A REAL
    HOLE RATHER THAN AN OVERSIGHT (documented 2026-08-05, after it failed a
    build). `.json` is in _SCAN_SUFFIXES so it reaches this function, matches
    none of the branches, and returns as raw text via the fallback at the
    bottom. There is no fix available here: JSON has no comment syntax, so
    every word in the file is a string literal and there is nothing this
    function could strip that would leave the code behind.

    The consequence is that for JSON, and ONLY for JSON, this scan behaves like
    the v1 raw-text version the redesign replaced -- prose reads as a
    dependency. Handle it as a DATA rule in the JSON file itself, never by
    loosening the scan: theme/canonical/themes.json carries
    `rules.no-customers-no-sites` for exactly this.

    ⚠️ An unparseable Python file also returns raw, deliberately (see below).
    Two different reasons, one behaviour, and neither is a silent skip.
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

    # .json lands here, raw. See the 🔴 block in this function's docstring.
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
    # THE SCANS FIRST. They are the last writers into state.REPORT, so anything
    # rendered before them is missing every oversize file and every leak.
    _scan_sizes()
    leaked = _scan_leaks()

    print(report.as_text())

    # AND THE HARD FAILURE LAST, AFTER THE PRINT, WHICH IS THE ORIGINAL ORDER AND
    # WORTH KEEPING ON PURPOSE: the report naming the leaked file has to reach the
    # log before the exit code kills the build, or the one finding that matters is
    # the one nobody gets to read.
    #
    # ⚠️ It also means hook 08b never runs on a leak, so a report page keeps its
    # marker. Correct -- the build failed and nothing deploys.
    if leaked:
        print(
            "::error::docrender: engine CODE references the site it is "
            "rendering. That is the one failure this pipeline refuses to warn "
            "about, because a portable engine stops being portable silently.",
            file=sys.stderr,
        )
        raise SystemExit(1)
