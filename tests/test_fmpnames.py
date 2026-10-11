"""fmpnames: catalog loading, resolution, drift. No MkDocs needed.

Run: `python -m pytest tests/test_fmpnames.py` (or `python tests/test_fmpnames.py`).
Fake File/Page objects carry only the attributes the module reads.
"""

import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from docrender import fmpnames, prefixes, state  # noqa: E402

CATALOG = (
    "key\tcurrent\tproposed\tstatus\tpage\tgrain\n"
    "t.yearconfig\tBudgetCode_YearConfig\tBudgetCodeYearConfigs\trename\t\tone code in one FY\n"
    "t.alloc\tBudget_Allocation\tBudgetAllocations\trename\ttable-alloc\tmoney\n"
    "t.coded\tURF_CODED_TRANSACTIONS\t\tretire\t\tfold\n"
    "t.pending\t\tPendingTransactions\tnew\t\tpending\n"
    "t.open\tImport_URF0989\t\topen\t\t?\n"
    "l.hub\th_BudgetHub\t\tnew\t\thub\n"
    "Bad Key\tx\t\tkeep\t\t\n"
    "t.alloc\tDuplicate\t\tkeep\t\t\n"
)


def _setup():
    state.REPORT = {}
    state.PAGES = {"table-alloc": {"url": "app/tables/alloc/", "type": "reference"}}
    tmp = Path(tempfile.mkdtemp())
    (tmp / "app").mkdir()
    (tmp / "app" / "NAMES.tsv").write_text(CATALOG, encoding="utf-8")
    files = [
        SimpleNamespace(src_uri="app/NAMES.tsv", abs_src_path=str(tmp / "app" / "NAMES.tsv")),
        SimpleNamespace(src_uri="app/index.md", abs_src_path=str(tmp / "app" / "index.md")),
    ]
    fmpnames.on_files(files, {})
    return files


def _page(src, url):
    return SimpleNamespace(file=SimpleNamespace(src_uri=src, url=url))


def _r(key, src="app/50-LAYOUTS/hub.md", label="", anchor="", opts=""):
    return prefixes.resolver("fmp")(key, _page(src, "app/50-layouts/hub/"), label, anchor, opts)


def test_claimed():
    assert prefixes.resolver("fmp") is fmpnames._resolve


def test_bad_and_duplicate_rows_reported_and_skipped():
    _setup()
    notes = "\n".join(state.REPORT.get("notes", []))
    assert "Bad Key" in notes and "appears twice" in notes
    assert fmpnames._CATALOGS["app"]["t.alloc"]["current"] == "Budget_Allocation"


def test_empty_label_renders_current_as_span():
    _setup()
    out = _r("t.yearconfig")
    assert ">BudgetCode_YearConfig</span>" in out and "dr-mark--cls-schema" in out


def test_page_row_renders_link_with_anchor():
    _setup()
    out = _r("t.alloc", anchor="#grain")
    assert out.startswith("[Budget_Allocation](../../tables/alloc/#grain)")
    assert "dr-mark-link" in out


def test_new_shows_proposed_soft_and_layout_family():
    _setup()
    assert ">PendingTransactions<" in _r("t.pending") and "dr-mark--soft" in _r("t.pending")
    assert "dr-mark--cls-layout" in _r("l.hub")


def test_retire_struck_and_reported():
    _setup()
    assert "dr-mark--strike" in _r("t.coded")
    assert any("retire" in n for n in state.REPORT["notes"])


def test_open_reported_once_per_page():
    _setup()
    _r("t.open"); _r("t.open")
    assert sum("still `open`" in n for n in state.REPORT["notes"]) == 1


def test_dead_key_declines():
    _setup()
    assert _r("t.nope") is None


def test_no_catalog_above_page_declines_and_reports():
    _setup()
    assert _r("t.alloc", src="other/page.md") is None
    assert any("no NAMES.tsv" in n for n in state.REPORT["dead_links"])


def test_mismatched_label_kept_and_reported():
    _setup()
    assert ">the money table<" in _r("t.yearconfig", label="the money table")
    assert any("neither the current nor the proposed" in n for n in state.REPORT["notes"])


def test_author_classes_merged():
    _setup()
    assert "no-print" in _r("t.yearconfig", opts="{.no-print}")


def test_drift_finds_prose_and_code_spans_not_fences_or_refs():
    _setup()
    md = (
        "Rows land in `URF_CODED_TRANSACTIONS` and Budget_Allocation.\n"
        "Cited properly: [](@fmp:t.yearconfig).\n"
        "```\nSet Field [ BudgetCode_YearConfig::x ]\n```\n"
    )
    hits = {s: n for s, _, n in fmpnames.drift(md, "app/x.md")}
    assert hits == {"URF_CODED_TRANSACTIONS": 1, "Budget_Allocation": 1}


def test_drift_does_not_match_inside_longer_names():
    _setup()
    assert fmpnames.drift("Budget_Allocation_OthersCodes", "app/x.md") == []


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
