#!/usr/bin/env python3
"""Print every packet member with the SAME browser the reader prints from, then
staple the results into ONE PDF per program.

BUILD 10 v2. Runs in CI, AFTER `mkdocs build` and BEFORE the deploy step, over the
finished site on disk. Reads `packets.json` (written by `docrender/packetbuild.py`)
and writes one `.pdf` per program into the same site tree, so the export button can
be a plain link to a real file.

=============================================================================
🔴 WHY THIS EXISTS: THE ASK WAS RIGHT AND v1 ANSWERED IT AT THE WRONG TIME
=============================================================================
Michael, 2026-08-30, first message of the feature: *"a button that essentially
navigates to each policy in the program chain, and does a print of that page, and
then stacks them all together to make a packet."* Restated hours later, after seeing
v1: *"get every single policy printed as if I went to that page and printed it
manually, stacked together in a single PDF. That's the baseline."*

v1 refused that mechanism and it refused it CORRECTLY -- for a READER. In a browser
tab `window.print()` prints only the current document, the dialog needs a human, and
the PDF never enters JavaScript. All true. **All irrelevant here.** In CI there is a
real Chrome, no dialog, and a filesystem.

⚑ **A CAPABILITY IS REFUSED IN A CONTEXT, NEVER IN GENERAL, AND v1 CARRIED THE
REFUSAL ACROSS A BOUNDARY WITHOUT RE-ASKING.** The question *"can a browser navigate,
print and stack?"* has two answers depending on WHO is driving; v1 answered for the
reader and then filed the answer as a property of browsers. ⭐ *It is the twin of the
error `runfoot.py` recorded the same afternoon -- a capability claim true when written
and false where it was used. That one rotted because the WORLD moved; this one was
wrong on arrival because the CONTEXT moved.*

=============================================================================
⭐ WHAT THIS BUYS THAT THE HTML SPLICE COULD NOT
=============================================================================
v1 re-assembled finished HTML, so it inherited every per-page element in the engine
and defended itself with a hardcoded strip list. **That list took two live defects in
four hours** -- rival `@page` rules (the last one won, so section nine's date stamped
all nine sheets) and a duplicated ownership tag -- and `packet.py`'s own closing note
admits the class is unbounded: *"any per-page element added anywhere in the engine is
silently duplicated into every packet unless somebody remembers this tuple."*

✅ **PRINTING EACH PAGE SEPARATELY MAKES THAT CLASS IMPOSSIBLE RATHER THAN MANAGED.**
Each sheet comes out of exactly the render a reader would print, one document at a
time, so per-page furniture is per-page by construction. Nothing to strip, no anchor
namespace to rewrite, and no list for a future feature to forget.

=============================================================================
🚫 THIS IS NOT THE WeasyPrint REFUSAL BEING QUIETLY REVERSED
=============================================================================
`specs/print-packet.md` §5 refused a build-time PDF renderer, and that refusal
STANDS: **a SECOND renderer means two engines and two layouts, and the printed
artifact stops being the page anybody previewed.** The objection was never "PDF at
build time" -- it was "a DIFFERENT renderer."

⭐ **CHROME IS THE RENDERER MICHAEL PRINTS FROM.** So this is the one build-time PDF
path that satisfies that refusal rather than dodging it: same engine, same eight print
sheets, same `@page` margin boxes. 🔴 It also closes the hole `runfoot.py` names in its
own § WHAT IS VERIFIED -- *"the engine that could be tested is not the engine that
prints"* -- because from here the engine that prints IS the one in the build.

=============================================================================
⚠️ IT MUST BE SERVED OVER HTTP, NOT OPENED AS file://
=============================================================================
`file://` treats every directory as its own opaque origin, so absolute asset paths
break and Chrome applies stricter rules to local documents. The site is served from a
throwaway loopback server instead, which is also the only way the fingerprinted asset
URLs resolve exactly as they will in production.

🔴 THE PORT IS NEVER HARDCODED. Port 0 asks the OS for a free one; a fixed port is a
collision with whatever else a runner is doing, and the failure would look like a
render bug rather than a port clash.
"""

from __future__ import annotations

import functools
import http.server
import json
import os
import shutil
import subprocess
import socketserver
import sys
import tempfile
import threading
from pathlib import Path

from pypdf import PdfReader, PdfWriter

#: Chrome binaries in the order a runner is likely to have them.
#:
#: ⚠️ `chromium` LAST, DELIBERATELY. On a GitHub runner `google-chrome` is the real
#: article and matches what Michael prints from; a snap/flatpak `chromium` is a
#: different build, and this whole approach rests on renderer identity.
_CHROME = ("google-chrome", "google-chrome-stable", "chromium-browser", "chromium")

#: 🔴 EVERY FLAG HERE IS LOAD-BEARING. Explained rather than listed, because a future
#: session trimming "noise" from this tuple is the likeliest way this breaks:
#:
#:   --headless=new        the modern headless. The old one is a different browser
#:                         with different print behaviour, which is the one thing
#:                         this script cannot afford.
#:   --disable-gpu         headless Chrome on a GPU-less runner otherwise stalls.
#:   --no-sandbox          required in the container; no untrusted input is loaded
#:                         (the pages are ours, served from loopback).
#:   --virtual-time-budget THE ONE THAT DECIDES CORRECTNESS. Chrome prints when it
#:                         thinks it is ready; with no budget it can print before
#:                         late CSS settles, and the failure is a CORRECT-LOOKING
#:                         sheet with the wrong layout. 8s is generous on purpose --
#:                         a slow sheet costs seconds, a short budget costs a
#:                         silently wrong safety document.
#:   --run-all-compositor-stages-before-draw  forces layout to finish first.
#:
#: 🚫 NO `--no-pdf-header-footer`. Chrome's own dialog furniture is absent from
#: `--print-to-pdf` by default, and our header/footer come from the engine's `@page`
#: margin boxes. Passing a flag to suppress furniture we do not have risks suppressing
#: furniture we DO have. ⚠️ UNVERIFIED -- there is no Chrome in the sandbox this was
#: written in. The first CI run is the proof and it is visible: a doubled page number
#: or a missing letterhead would say so on sheet one.
_FLAGS = (
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--virtual-time-budget=8000",
    "--run-all-compositor-stages-before-draw",
)


def chrome() -> str:
    """The browser to print with, or exit loudly.

    🔴 EXITS RATHER THAN SKIPPING. A missing browser means every packet PDF is absent,
    and once the export button points at one, every program page links to a 404 -- the
    dead control this engine kills on sight. A red step before the deploy is the
    correct outcome; a green build with no PDFs is not.
    """
    for name in _CHROME:
        found = shutil.which(name)
        if found:
            return found
    sys.exit(
        "print-packets: no Chrome/Chromium on PATH (tried: "
        + ", ".join(_CHROME) + "). Packet PDFs cannot be produced, and the export "
        "button would 404 on every program page. Install a browser in the workflow "
        "before this step."
    )


class _Quiet(http.server.SimpleHTTPRequestHandler):
    """A static server that does not narrate. One line per request would be ~300."""

    def log_message(self, *_args):
        return


def serve(root: Path):
    """Serve `root` on loopback. Returns (base_url, shutdown).

    ⚠️ THREADED, because a page fetches its own stylesheets: a single-threaded server
    deadlocks the moment the browser opens a second connection.
    """
    handler = functools.partial(_Quiet, directory=str(root))
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    httpd.daemon_threads = True
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return "http://127.0.0.1:" + str(port) + "/", httpd.shutdown


def print_page(browser: str, url: str, out: Path) -> None:
    """One page, one PDF, through the real print path.

    ⚠️ A FRESH `--user-data-dir` PER CALL. Chrome refuses to run two instances against
    one profile, and re-using a profile across hundreds of pages also accumulates
    state that could change a render between the first sheet and the last.
    """
    with tempfile.TemporaryDirectory() as profile:
        cmd = [browser, *_FLAGS, "--user-data-dir=" + profile,
               "--print-to-pdf=" + str(out), url]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0 or not out.exists() or out.stat().st_size == 0:
        raise RuntimeError(
            "chrome failed to print " + url + " (exit " + str(proc.returncode)
            + "): " + (proc.stderr or "").strip()[-500:]
        )


def staple(parts: list[Path], out: Path) -> int:
    """Concatenate in order. Returns the sheet count.

    ⭐ `append` PRESERVES EACH SOURCE'S OWN PAGE GEOMETRY, which is the property that
    makes this the right tool: a packet is a stack of separately-printed documents and
    must not be re-laid-out. pypdf is pure Python with no native dependency, so it adds
    no transitive build surface -- the bar `requirements.txt` sets for a new dependency
    and the reason `segno` was acceptable there and Pillow was not.

    🔴 A PAGE THAT PRINTED TO A ZERO-PAGE PDF IS A HARD FAILURE. Chrome can exit 0
    having produced a file with no pages; appending it silently drops a policy out of a
    safety packet, which is the one outcome this whole feature exists to prevent.
    """
    writer = PdfWriter()
    for part in parts:
        reader = PdfReader(str(part))
        if not reader.pages:
            raise RuntimeError("printed 0 pages: " + part.name)
        writer.append(reader)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as fh:
        writer.write(fh)
    return len(writer.pages)


def main(site: Path) -> int:
    manifest = site / "packets.json"
    if not manifest.exists():
        print("print-packets: no packets.json -- no program declares `export:`. "
              "Nothing to do, and that is not an error.")
        return 0

    plan = json.loads(manifest.read_text(encoding="utf-8"))
    packets = plan.get("packets") or []
    if not packets:
        print("print-packets: packets.json is empty. Nothing to do.")
        return 0

    browser = chrome()
    base, shutdown = serve(site)
    print("print-packets: " + browser)
    print("print-packets: serving " + str(site) + " at " + base)

    lines = []
    try:
        for packet in packets:
            pages = packet.get("pages") or []
            target = site / packet["pdf"]
            with tempfile.TemporaryDirectory() as tmp:
                parts = []
                for i, page_url in enumerate(pages, 1):
                    part = Path(tmp) / ("%03d.pdf" % i)
                    print_page(browser, base + page_url.lstrip("/"), part)
                    parts.append(part)
                sheets = staple(parts, target)
            line = (packet["pdf"] + " -- " + str(len(pages)) + " page(s), "
                    + str(sheets) + " sheet(s)")
            print("print-packets: wrote " + line)
            lines.append(line)
    finally:
        shutdown()

    # 🔴 THE SHEET COUNT IS THE FALSIFIABLE ARTIFACT. A packet with fewer sheets than
    # members means a policy printed to nothing; a human reading this summary can see
    # that, and nothing else in the pipeline can.
    #
    # 🐛 THE GUARD TESTS THE ENV STRING, NEVER A PATH BUILT FROM IT, AND THAT IS A
    # FIXED BUG RATHER THAN A STYLE CHOICE. `Path("")` IS `Path(".")` and
    # `str(Path("."))` is `"."` -- truthy -- so the obvious `if str(summary)` opened
    # the CURRENT DIRECTORY for append and raised `IsADirectoryError`, killing the step
    # AFTER every PDF had already been written correctly. ⚑ *A falsy value that becomes
    # truthy the moment it is wrapped is the whole family: test the raw input, never
    # the object built from it.* Found by running it; reading it would not have.
    summary = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("\n### Packet PDFs\n\n")
            for line in lines:
                fh.write("- `" + line + "`\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else "site")))
