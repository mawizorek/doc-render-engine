"""Regression tests for the existing filename-only TSV lookup.

Run: python -m unittest discover -s tests -v
The loader compiles the two production lookup functions unchanged, avoiding
unrelated Markdown/rendering dependencies in these filesystem unit tests.
"""

import ast
from pathlib import Path
import posixpath
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


def load_lookup():
    source = Path(__file__).resolve().parents[1] / "docrender/datatable.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef)
                 and node.name in {"_index", "_locate"}]
    if {node.name for node in functions} != {"_index", "_locate"}:
        raise AssertionError("Production lookup functions changed; update these tests")
    namespace = {
        "Path": Path, "posixpath": posixpath,
        "state": SimpleNamespace(note=Mock()),
        "_INDEX": {}, "_INDEX_FOR": None,
    }
    exec(compile(ast.Module(body=functions, type_ignores=[]),
                 str(source), "exec"), namespace)
    return namespace


class DataLookupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.lookup = load_lookup()
        self.files = []

    def add_tsv(self, path):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("Event\tDate\nPut-in\tNov 2\n", encoding="utf-8")
        self.files.append(SimpleNamespace(src_uri=path))

    def locate(self, name, folder="courses/onboarding-programs"):
        return self.lookup["_locate"](
            name, folder, self.root, self.files, folder + "/prod-xp.md", "crew"
        )

    def test_current_crew_files_resolve_without_paths(self):
        for name in ("dates-big-love-run-crew.tsv",
                     "dates-becoming-curious-run-crew.tsv"):
            self.add_tsv("REPO_PAGES/info-dates/" + name)
        for item in self.files:
            with self.subTest(path=item.src_uri):
                self.assertEqual(self.locate(posixpath.basename(item.src_uri)),
                                 item.src_uri)

    def test_page_can_move_without_changing_reference(self):
        self.add_tsv("records/crew.tsv")
        for folder in ("", "courses", "deep/new/course/home"):
            with self.subTest(folder=folder):
                self.assertEqual(self.locate("crew.tsv", folder), "records/crew.tsv")

    def test_data_can_move_between_builds_without_changing_reference(self):
        old, new = "records/crew.tsv", "new/home/crew.tsv"
        self.add_tsv(old)
        self.assertEqual(self.locate("crew.tsv"), old)
        (self.root / old).unlink()
        self.files = []
        self.add_tsv(new)
        self.assertEqual(self.locate("crew.tsv"), new)

    def test_duplicate_remote_names_are_refused_with_both_paths(self):
        self.add_tsv("one/crew.tsv")
        self.add_tsv("two/crew.tsv")
        self.assertEqual(self.locate("crew.tsv"), "")
        message = self.lookup["state"].note.call_args.args[1]
        self.assertIn("one/crew.tsv", message)
        self.assertIn("two/crew.tsv", message)
        self.assertIn("NOT rendered", message)

    def test_missing_filename_is_reported(self):
        self.assertEqual(self.locate("missing.tsv"), "")
        self.assertIn("nowhere", self.lookup["state"].note.call_args.args[1])

    def test_stale_explicit_path_does_not_guess_by_basename(self):
        self.add_tsv("REPO_PAGES/info-dates/crew.tsv")
        self.assertEqual(self.locate("../../production/info-dates/crew.tsv"), "")
        self.assertIn("taken literally", self.lookup["state"].note.call_args.args[1])

    def test_explicit_path_and_local_file_remain_compatible(self):
        self.add_tsv("records/crew.tsv")
        self.assertEqual(self.locate("../../records/crew.tsv"), "records/crew.tsv")
        self.files = []
        self.add_tsv("courses/onboarding-programs/local.tsv")
        self.assertEqual(self.locate("local.tsv"),
                         "courses/onboarding-programs/local.tsv")

    def test_unpublished_remote_file_is_not_discovered(self):
        self.add_tsv("excluded/crew.tsv")
        self.files = []
        self.assertEqual(self.locate("crew.tsv"), "")


if __name__ == "__main__":
    unittest.main()
