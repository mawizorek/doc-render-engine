"""binder type: collection.expanded(), navigation exclusion, presets, packets, contents.

Spec: specs/binder-type.md. No MkDocs needed: fake File/Page objects carry only
the attributes the modules read.

Run: `python -m pytest tests/test_binder.py` (or `python tests/test_binder.py`).
"""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from docrender import binder, chainlist, collection, nav, packet, state  # noqa: E402

PAGES = {
    "programs/general.md": {"id": "program-general", "title": "General Safety", "type": "program",
                            "status": "public", "chain": ["policy-fire", "policy-ladders"],
                            "export": ["packet"]},
    "policies/fire.md": {"id": "policy-fire", "title": "Fire", "type": "page", "status": "public"},
    "policies/ladders.md": {"id": "policy-ladders", "title": "Ladders", "type": "page", "status": "public"},
    "policies/hours.md": {"id": "policy-hours", "title": "Shop Hours", "type": "page", "status": "public"},
    "policies/secret.md": {"id": "policy-secret", "title": "Secret", "type": "page", "status": "unlisted"},
    "shop/index.md": {"id": "shop-index", "title": "Shop", "type": "index", "status": "public",
                      "chain": ["policy-hours"]},
    "binders/other.md": {"id": "binder-other", "title": "Other", "type": "binder", "status": "public",
                         "chain": ["policy-hours"]},
    "binders/td.md": {
        "id": "binder-td", "title": "Scene Shop TD", "type": "binder", "status": "public",
        "export": ["packet"],
        "chain": [
            {"section": "Safety", "subtitle": "Programs you have completed"},
            "program-general",          # expands: tab sheet + fire + ladders
            "policy-fire",              # repeat: first appearance wins
            {"section": "Shop"},
            "shop-index",               # an index stays ONE page
            "policy-hours",
            "binder-other",             # refused
            "policy-nope",              # dead
            "policy-secret",            # unlisted: refused by presets
        ],
    },
    "legacy/old.md": {"id": "binder-old", "title": "Old Binder", "type": "program", "binder": True,
                      "status": "public", "chain": ["policy-hours"]},
    "pages/stray.md": {"id": "stray", "title": "Stray", "type": "page", "binder": True, "status": "public"},
}


def _files():
    files = []
    for src, meta in PAGES.items():
        url = src[:-3].replace("index", "").rstrip("/") + "/"
        f = SimpleNamespace(src_uri=src, url=url)
        page = SimpleNamespace(is_page=True, title=meta["title"], file=f, meta={},
                               previous_page=None, next_page=None)
        f.page = page
        files.append(f)
    return files


def _setup():
    state.BY_SRC = {k: dict(v) for k, v in PAGES.items()}
    state.REPORT = {}
    return _files()


def _report(bucket):
    return "\n".join(state.REPORT.get(bucket, []))


def test_binder_absent_from_declared():
    _setup()
    chains = nav.declared(report=False)
    assert "binders/td.md" not in chains and "programs/general.md" in chains


def test_expanded_shape():
    _setup()
    got = collection.expanded("binders/td.md", report=True)
    assert got[0] == {"section": "Safety", "subtitle": "Programs you have completed"}
    ids = [(e["id"], e["via"]) for e in got if "id" in e]
    assert ids == [
        ("program-general", ""), ("policy-fire", "program-general"),
        ("policy-ladders", "program-general"), ("shop-index", ""),
        ("policy-hours", ""), ("policy-secret", ""),
    ]
    assert any("again at entry" in n for n in state.REPORT["notes"])
    assert "binder inside a binder" in _report("missing_required")
    assert "policy-nope" in _report("dead_links")


def test_binder_never_touches_prev_next():
    files = _setup()
    nav._apply(files)
    by = {f.src_uri: f.page for f in files}
    # The program wires its own members; the binder adds nothing.
    assert by["policies/fire.md"].previous_page is by["programs/general.md"]
    assert by["policies/ladders.md"].next_page is None
    assert by["binders/td.md"].next_page is None


def test_section_on_program_is_reported_and_ignored():
    _setup()
    state.BY_SRC["programs/general.md"]["chain"] = [{"section": "x"}, "policy-fire"]
    assert nav.declared(report=True)["programs/general.md"] == ["policy-fire"]
    assert "legal on `type: binder` only" in _report("missing_required")


def test_presets_kinds_and_flags():
    files = _setup()
    binder.on_nav(None, {}, files)
    kinds = [(p["id"], p["kind"]) for p in binder._PLAN]
    assert kinds[0][1] == "binder" and ("program-general", "program") in kinds
    assert ("binder-old", "binder") in kinds and ("binder-td", "binder") in kinds
    td = next(p for p in binder._PLAN if p["id"] == "binder-td")
    assert td["pages"][0] == {"section": "Safety", "subtitle": "Programs you have completed"}
    assert not any(p.get("title") == "Secret" for p in td["pages"])
    req = _report("missing_required")
    assert "DEPRECATED" in req and "stray" not in [k for k, _ in kinds] and "pages/stray.md `binder: true` does nothing" in req
    assert "REFUSES `policy-secret`" in req


def test_packet_accepts_binder():
    _setup()
    want = packet.wanted(report=True)
    assert want["binders/td.md"][:3] == ["program-general", "policy-fire", "policy-ladders"]
    assert "programs/general.md" in want


def test_contents_sections_and_nesting():
    files = _setup()
    page = next(f.page for f in files if f.src_uri == "binders/td.md")
    out = chainlist._render("binders/td.md", "", page, files)
    lines = out.split("\n")
    assert lines[0] == "#### Safety" and "*Programs you have completed*" in lines
    assert any(l.startswith("1. [General Safety]") for l in lines)
    assert any(l.startswith("    1. [Fire]") for l in lines)
    assert "#### Shop" in lines and any(l.startswith("1. [Shop]") for l in lines)


def test_program_contents_unchanged():
    files = _setup()
    page = next(f.page for f in files if f.src_uri == "programs/general.md")
    out = chainlist._render("programs/general.md", "", page, files)
    assert out.split("\n")[0].startswith("1. [Fire]")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
