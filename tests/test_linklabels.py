"""Regression tests for renderer-only automatic page labels.

Run: python -m unittest discover -s tests -v
"""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from xml.etree import ElementTree as ET

import markdown

from docrender import links, state


class AutoLabelTests(unittest.TestCase):
    def setUp(self):
        state.reset()
        self.page = SimpleNamespace(
            file=SimpleNamespace(src_uri="index.md", url="./")
        )
        state.BY_SRC["index.md"] = {"id": "home"}
        state.PAGES["course-intro-to-lx"] = {
            "id": "course-intro-to-lx",
            "title": "Introduction to Lighting for the Stage",
            "url": "courses/lighting/",
        }
        state.PEERS["other"] = {
            "base_url": "https://example.org/docs/",
            "pages": [{"id": "course", "title": "Other Course", "url": "course/"}],
        }

    def render(self, source):
        return links.on_page_markdown(source, self.page, {}, None)

    def html(self, source):
        return ET.fromstring(
            "<root>" + markdown.markdown(
                self.render(source), extensions=["attr_list", "tables", "fenced_code"]
            ) + "</root>"
        )

    def test_empty_label_inherits_title(self):
        self.assertEqual(
            self.render("[](@course-intro-to-lx)"),
            "[Introduction to Lighting for the Stage](courses/lighting/)",
        )

    def test_title_change_updates_all_auto_labels_not_override(self):
        source = "[](@course-intro-to-lx) [](@course-intro-to-lx) [LX](@course-intro-to-lx)"
        before = self.render(source)
        state.PAGES["course-intro-to-lx"]["title"] = "Stage Lighting"
        after = self.render(source)
        self.assertEqual(before.count("[Introduction to Lighting for the Stage]"), 2)
        self.assertEqual(after.count("[Stage Lighting]"), 2)
        self.assertIn("[LX](courses/lighting/)", after)

    def test_explicit_labels_remain_verbatim(self):
        for label in ["LX", "**Lighting**", " ", "<em>Lighting</em>"]:
            with self.subTest(label=label):
                self.assertEqual(
                    self.render("[" + label + "](@course-intro-to-lx)"),
                    "[" + label + "](courses/lighting/)",
                )

    def test_anchor_and_attribute_survive(self):
        anchor = self.html("[](@course-intro-to-lx#overview){.no-print}").find(".//a")
        self.assertEqual(anchor.get("href"), "courses/lighting/#overview")
        self.assertEqual(anchor.get("class"), "no-print")
        self.assertEqual(anchor.text, "Introduction to Lighting for the Stage")

    def test_nested_source_keeps_relative_url(self):
        self.page.file.url = "guides/start/"
        self.assertIn("](../../courses/lighting/)", self.render("[](@course-intro-to-lx)"))

    def test_file_style_source_keeps_relative_url(self):
        self.page.file.url = "guides/start.html"
        self.assertIn("](../courses/lighting/)", self.render("[](@course-intro-to-lx)"))

    def test_peer_title_and_anchor(self):
        result = self.render("[](@other:course#overview)")
        self.assertEqual(
            result,
            "[Other Course](https://example.org/docs/course/#overview){ .docrender-xref }",
        )
        self.assertEqual(
            self.render("[Override](@other:course)"),
            "[Override](https://example.org/docs/course/){ .docrender-xref }",
        )

    def test_special_titles_are_literal_text_not_markup(self):
        titles = [
            "Lighting [Basics] & Sound",
            "*bold* _under_ `code` ![image](x) [link](https://example.org)",
            '<script>alert("x")</script> &amp; &#60; {.role} | ~strike~',
            "C:\\Users\\stage [x](@course-intro-to-lx)",
            "Lumière 🎭 日本語",
        ]
        for title in titles:
            with self.subTest(title=title):
                state.PAGES["course-intro-to-lx"]["title"] = title
                root = self.html("[](@course-intro-to-lx)")
                anchor = root.find(".//a")
                self.assertEqual(len(root.findall(".//a")), 1)
                self.assertEqual(len(list(anchor)), 0)
                self.assertEqual(anchor.text, title)
                self.assertEqual(anchor.get("href"), "courses/lighting/")

    def test_title_pipe_does_not_split_table(self):
        state.PAGES["course-intro-to-lx"]["title"] = "Light | Sound"
        root = self.html("| Course | Note |\n| --- | --- |\n| [](@course-intro-to-lx) | Yes |")
        self.assertEqual(len(root.findall(".//tbody/tr/td")), 2)
        self.assertEqual(root.find(".//a").text, "Light | Sound")

    def test_multiline_title_is_one_inline_label(self):
        state.PAGES["course-intro-to-lx"]["title"] = "  Stage\n Lighting\tBasics  "
        self.assertEqual(self.html("[](@course-intro-to-lx)").find(".//a").text,
                         "Stage Lighting Basics")

    def test_missing_title_has_visible_reported_fallback(self):
        for value in [None, "", " \n "]:
            with self.subTest(value=value):
                state.PEERS["other"]["pages"][0]["title"] = value
                self.assertIn("[@other:course]", self.render("[](@other:course)"))
                self.assertIn("no title", state.REPORT["notes"][-1])

    def test_numeric_title_does_not_crash(self):
        state.PAGES["course-intro-to-lx"]["title"] = 101
        self.assertIn("[101]", self.render("[](@course-intro-to-lx)"))

    def test_broken_ids_are_visible_nonlinks_and_reported(self):
        for token in ["missing", "unknown:course", "other:missing", "file.md", "image.png"]:
            with self.subTest(token=token):
                root = self.html("[](@" + token + ")")
                self.assertIsNone(root.find(".//a"))
                span = root.find(".//span")
                self.assertEqual(span.get("class"), "docrender-dead")
                self.assertTrue(span.text)
                self.assertFalse(state.REFS["home"][token]["ok"])
        self.assertTrue(state.REPORT["dead_links"])

    def test_hidden_target_is_not_read_from_raw_frontmatter(self):
        state.BY_SRC["hidden.md"] = {"id": "hidden", "title": "Do not expose this"}
        result = self.render("[](@hidden)")
        self.assertNotIn("Do not expose this", result)
        self.assertIn("docrender-dead", result)

    def test_code_examples_and_incomplete_input_are_unchanged(self):
        for source in [
            "`[](@course-intro-to-lx)`",
            "```md\n[](@course-intro-to-lx)\n```",
            "~~~md\n[](@course-intro-to-lx)\n~~~",
            "[](@)",
            "[](@course-intro-to-lx",
        ]:
            with self.subTest(source=source):
                self.assertEqual(self.render(source), source)
        self.assertEqual(state.REFS, {})

    def test_reference_tracking_stays_in_existing_resolver(self):
        self.render("[](@course-intro-to-lx) [LX](@course-intro-to-lx)")
        self.assertEqual(state.REFS["home"]["course-intro-to-lx"],
                         {"kind": "page", "target": "course-intro-to-lx", "ok": True, "count": 2})

    def test_reserved_handler_still_owns_its_label(self):
        handler = Mock(return_value="[handler label](target/)")
        with patch.object(links.prefixes, "resolver", return_value=handler), \
             patch.object(links.prefixes, "takes_anchor", return_value=False), \
             patch.object(links.prefixes, "takes_opts", return_value=False):
            self.assertEqual(self.render("[](@data:inventory)"), "[handler label](target/)")
        handler.assert_called_once_with("inventory", self.page, "")


if __name__ == "__main__":
    unittest.main()
