"""`!!! formpicker` -- the derived program menu. Runs against the real module.

Stub `state` and `util`, real `formpicker`. `forms.py` is NOT stubbed away
entirely: the four symbols this module imports from it are reproduced with the
same signatures, because the delegation IS the design and a test that fakes the
embed away would not catch the asset-inheritance bug this suite exists to pin.
⚠️ The real `forms._html` is 22,065 B and under a 22,528 B read ceiling, so it
is not copied. The integration itself is unverified until the first publish.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from docrender import forms, formpicker, state  # noqa: E402

BASE = "https://forms.clickup.com/36074068/f/12cwjm-53753/XYZ"


class _File:
    def __init__(self, src):
        self.src_uri = src


class _Page:
    def __init__(self, src):
        self.file = _File(src)


def _form(pid):
    return {"completion": {"src": BASE + "?Program_ID=" + pid, "text": "Form"}}


def setup_function(_):
    state.reset()
    state.BY_SRC.update({
        "pick.md": {"id": "page-pick", "title": "Record a completion",
                    "forms": _form("ITPSAFE-1336")},
        "lx.md": {"id": "program-general-safety-lx", "type": "program",
                  "title": "General Safety for Light Lab",
                  "forms": _form("ITPSAFE-1287")},
        "foh.md": {"id": "program-foh-safety", "type": "program",
                   "title": "FOH Performance Safety",
                   "forms": _form("ITPSAFE-1337")},
        "eh.md": {"id": "binder-emergency-handbook-spac", "type": "program",
                  "title": "URITP Emergency Handbook",
                  "forms": _form("ITPSAFE-1336")},
        "draft.md": {"id": "program-secret", "type": "program",
                     "title": "Unpublished Program",
                     "forms": _form("ITPSAFE-9999")},
        "policy.md": {"id": "policy-ppe", "type": "page", "title": "PPE"},
    })
    for pid in ("page-pick", "program-general-safety-lx", "program-foh-safety",
                "binder-emergency-handbook-spac", "policy-ppe"):
        state.PAGES[pid] = object()


def _render(src="pick.md", body='!!! formpicker "completion"'):
    return formpicker.on_page_markdown(body, _Page(src), {}, [])


# --- the catalog -----------------------------------------------------------

def test_catalog_only_published_pages():
    rows, _ = formpicker.catalog(skip="pick.md")
    pids = [r["pid"] for r in rows]
    assert "ITPSAFE-9999" not in pids, "an unpublished program leaked into the menu"
    assert set(pids) == {"ITPSAFE-1287", "ITPSAFE-1336", "ITPSAFE-1337"}


def test_catalog_skips_the_picker_page_itself():
    rows, dupes = formpicker.catalog(skip="pick.md")
    assert dupes == {}, "the picker's own default was read as a duplicate"
    owner = [r["id"] for r in rows if r["pid"] == "ITPSAFE-1336"]
    assert owner == ["binder-emergency-handbook-spac"]


def test_catalog_sorted_by_title_not_by_id():
    rows, _ = formpicker.catalog(skip="pick.md")
    assert [r["title"] for r in rows] == [
        "FOH Performance Safety",
        "General Safety for Light Lab",
        "URITP Emergency Handbook",
    ]


def test_pages_without_forms_are_ignored():
    rows, _ = formpicker.catalog(skip="pick.md")
    assert all(r["id"] != "policy-ppe" for r in rows)


def test_collision_is_won_by_the_program_page_not_by_filename_order():
    # "clone.md" sorts BEFORE "foh.md", so walk order would hand the id to the
    # interloper. The program page has to win anyway.
    state.BY_SRC["clone.md"] = {
        "id": "page-foh-hub", "type": "page", "title": "FOH Hub",
        "forms": _form("ITPSAFE-1337"),
    }
    state.PAGES["page-foh-hub"] = object()
    rows, dupes = formpicker.catalog(skip="pick.md")
    assert dupes["ITPSAFE-1337"] == ["program-foh-safety", "page-foh-hub"]
    owner = [r["id"] for r in rows if r["pid"] == "ITPSAFE-1337"]
    assert owner == ["program-foh-safety"]


def test_collision_is_reported_and_offered_once():
    state.BY_SRC["clone.md"] = {
        "id": "page-foh-hub", "type": "page", "title": "FOH Hub",
        "forms": _form("ITPSAFE-1337"),
    }
    state.PAGES["page-foh-hub"] = object()
    out = _render()
    assert out.count('value="ITPSAFE-1337"') == 1
    notes = " ".join(state.REPORT.get("notes", []))
    assert "ITPSAFE-1337" in notes and "page-foh-hub" in notes


def test_two_real_programs_sharing_an_id_still_report():
    state.BY_SRC["clone.md"] = {
        "id": "program-clone", "type": "program", "title": "A Borrowed Form",
        "forms": _form("ITPSAFE-1337"),
    }
    state.PAGES["program-clone"] = object()
    _, dupes = formpicker.catalog(skip="pick.md")
    assert set(dupes["ITPSAFE-1337"]) == {"program-foh-safety", "program-clone"}


def test_one_page_naming_one_program_twice_is_not_a_collision():
    state.BY_SRC["lx.md"]["forms"]["reprint"] = {
        "src": BASE + "?Program_ID=ITPSAFE-1287"
    }
    rows, dupes = formpicker.catalog(skip="pick.md")
    assert dupes == {}
    assert sum(1 for r in rows if r["pid"] == "ITPSAFE-1287") == 1


# --- the rendered control --------------------------------------------------

def test_menu_renders_with_the_declared_default_selected():
    out = _render()
    assert 'class="dr-pick__select"' in out
    assert '<option value="ITPSAFE-1336" selected>' in out
    assert out.count("<option ") == 3


def test_option_labels_carry_title_and_program_id():
    out = _render()
    assert "FOH Performance Safety (ITPSAFE-1337)" in out


def test_label_is_tied_to_the_select():
    out = _render()
    assert 'for="dr-pick-completion"' in out
    assert 'id="dr-pick-completion"' in out


def test_the_frame_comes_from_forms_not_from_here():
    out = _render()
    assert out.count("<iframe") == 1
    assert 'class="dr-form"' in out
    assert "dr-form__fallback" in out


def test_selection_line_names_the_default_program():
    out = _render()
    assert "URITP Emergency Handbook" in out
    assert 'class="dr-pick__now"' in out


def test_helper_is_appended_once_and_swaps_by_clone():
    out = _render(body='!!! formpicker "completion"\n\n!!! formpicker "completion"')
    assert out.count("<script>document.addEventListener('change'") == 1
    assert out.count("<style>.dr-pick__tools") == 1
    assert "cloneNode" in out and "replaceWith" in out
    assert ".src=" not in out, "assigning iframe.src hijacks the Back button"


def test_print_rules_are_important():
    out = _render()
    assert ".dr-pick__tools,.md-typeset .dr-pick__tools{display:none !important}" in out


# --- the failure shapes ----------------------------------------------------

def test_dead_slot_passes_through_with_no_menu():
    out = _render(body='!!! formpicker "nope"')
    assert "docrender-dead" in out
    assert "dr-pick__select" not in out
    assert "<script>" not in out, "a listener was bound with nothing to bind to"


def test_empty_catalog_renders_the_plain_form_and_reports():
    for pid in ("program-general-safety-lx", "program-foh-safety",
                "binder-emergency-handbook-spac"):
        state.PAGES.pop(pid)
    out = _render()
    assert "dr-pick__select" not in out
    assert "<iframe" in out, "the form itself must survive an empty menu"
    assert any("nothing to pick between" in n
               for n in state.REPORT.get("notes", []))


def test_default_outside_the_catalog_is_reported():
    state.BY_SRC["pick.md"]["forms"] = _form("ITPSAFE-0000")
    _render()
    assert any("ITPSAFE-0000" in n and "no published page declares" in n
               for n in state.REPORT.get("notes", []))


def test_base_without_a_program_id_withholds_the_menu():
    state.BY_SRC["pick.md"]["forms"] = {"completion": {"src": BASE, "text": "Form"}}
    out = _render()
    assert "dr-pick__select" not in out, "a menu that cannot swap anything was offered"
    assert "<iframe" in out
    assert any("cannot append one" in n for n in state.REPORT.get("notes", []))


def test_unknown_option_is_reported_not_dropped_silently():
    _render(body='!!! formpicker "completion" algin=center')
    assert any("algin" in n for n in state.REPORT.get("notes", []))


def test_align_reaches_the_wrapper():
    out = _render(body='!!! formpicker "completion" align=center')
    assert "dr-pick--align-center" in out


def test_directive_inside_a_fence_is_left_alone():
    body = '```\n!!! formpicker "completion"\n```\n'
    out = _render(body=body)
    assert '!!! formpicker "completion"' in out
    assert "dr-pick__select" not in out


def test_page_with_no_directive_is_untouched():
    body = "# Just a page\n\nNothing to see.\n"
    assert _render(body=body) == body


# --- the inherited page assets ---------------------------------------------

def test_picker_inherits_the_forms_page_assets():
    out = _render()
    assert forms._FORM_SCRIPT in out, "the CDN height script never shipped"
    assert forms._RESET_CSS in out, "the print rules never shipped"
    assert forms._RESET_JS in out, "the Reload button was bound to nothing"


def test_page_assets_are_not_doubled_when_both_directives_appear():
    body = '!!! form "completion"\n\n!!! formpicker "completion"'
    out = _render(body=body)
    assert out.count(forms._FORM_SCRIPT) == 1
    assert out.count(forms._RESET_CSS) == 1
    assert out.count(forms._RESET_JS) == 1


def test_withheld_menu_ships_no_picker_assets():
    out = _render(body='!!! formpicker "nope"')
    assert forms._FORM_SCRIPT not in out
    assert "dr-pick" not in out
