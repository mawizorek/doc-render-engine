"""Regression tests for renderer-only automatic page labels.

Run: python -m unittest discover -s tests -v
"""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from xml.etree import ElementTree as ET

import markdown

from docrender import cells, linklabels, links, state


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

    def test_six_icon_shortcuts_and_literal_glyphs(self):
        for shortcut, glyph in linklabels.ICONS.items():
            for label in [shortcut, " " + shortcut + " ", glyph]:
                with self.subTest(label=label):
                    a = self.html("[" + label + "](@course-intro-to-lx)").find(".//a")
                    self.assertEqual(a.find("span").text, glyph)
                    self.assertEqual(a.find("span").get("aria-hidden"), "true")
                    self.assertEqual(a.get("aria-label"), "Introduction to Lighting for the Stage")
                    self.assertEqual(a.get("data-gloss"), a.get("aria-label"))
                    self.assertEqual(a.get("href"), "courses/lighting/")

    def test_icon_colors_follow_only_theme_roles(self):
        for color in linklabels.COLORS:
            with self.subTest(color=color):
                a = self.html("[*](@course-intro-to-lx){color=" + color + "}").find(".//a")
                self.assertEqual(a.get("style"), "--dr-link-icon-color:var(--dr-" + color + ")")
        for color in ["#ff0000", "red", "accent-1", "accent-soft", "url(evil)"]:
            with self.subTest(color=color):
                a = self.html("[!](@course-intro-to-lx){color=" + color + "}").find(".//a")
                self.assertIsNone(a.get("style"))
                self.assertIn("ignored", state.REPORT["notes"][-1])

    def test_icon_class_anchor_and_keyboard_semantics(self):
        a = self.html("[->](@course-intro-to-lx#intro){.custom color=accent}").find(".//a")
        self.assertEqual(a.get("href"), "courses/lighting/#intro")
        self.assertIn("custom", a.get("class").split())
        self.assertIn("dr-gloss", a.get("class").split())
        self.assertIsNone(a.get("tabindex"))
        self.assertIsNone(a.get("data-role-print"))

    def test_custom_gloss_on_auto_custom_and_icon_links(self):
        target = state.PAGES["course-intro-to-lx"]
        target["gloss"] = "Lighting basics."
        for label in ["", "**LX**", "->"]:
            with self.subTest(label=label):
                a = self.html("[" + label + "](@course-intro-to-lx)").find(".//a")
                self.assertEqual(a.get("aria-description"), "Lighting basics.")
                self.assertIn("Lighting basics.", a.get("data-gloss"))
                self.assertIsNone(a.get("data-role-print"))
        self.assertEqual(self.html("[**LX**](@course-intro-to-lx)").find(".//strong").text, "LX")

    def test_gloss_summary_precedence_and_empty_opt_out(self):
        resolve = linklabels.entity_gloss
        self.assertIsNone(resolve({"summary": "Summary"}, "target.md"))
        self.assertEqual(resolve({"summary": "Summary", "gloss_from_summary": True}, "target.md"), "Summary")
        self.assertEqual(resolve({"summary": "Summary", "gloss_from_summary": True,
                                  "gloss": "Custom"}, "target.md"), "Custom")
        self.assertEqual(resolve({"summary": "Summary", "gloss_from_summary": True,
                                  "gloss": ""}, "target.md"), "")
        self.assertIsNone(resolve({"summary": "Summary", "gloss_from_summary": False}, "target.md"))
        self.assertIsNone(resolve({"summary": "Summary", "gloss_from_summary": "false"}, "target.md"))
        self.assertIn("must be true or false", state.REPORT["notes"][-1])
        self.assertEqual(resolve({"gloss_from_summary": True}, "target.md"), "")
        self.assertIn("summary is empty", state.REPORT["notes"][-1])

    def test_frontmatter_flows_through_published_page_map(self):
        state.BY_SRC["target.md"] = {"id": "target", "title": "Target",
                                    "summary": "Shared explanation", "gloss_from_summary": True}
        files = SimpleNamespace(documentation_pages=lambda: [
            SimpleNamespace(src_uri="target.md", name="target", url="target/")])
        with patch.object(links, "_load_peers"):
            links.on_files(files, {})
        self.assertEqual(state.PAGES["target"]["gloss"], "Shared explanation")
        self.assertNotIn("summary", state.PAGES["target"])
        self.assertEqual(self.html("[](@target)").find(".//a").get("data-gloss"), "Shared explanation")
        # Rebuilding after an edit picks up the new value without a copied label.
        state.BY_SRC["target.md"]["summary"] = "Updated explanation"
        with patch.object(links, "_load_peers"):
            links.on_files(files, {})
        self.assertEqual(self.html("[!](@target)").find(".//a").get("aria-description"),
                         "Updated explanation")

    def test_peer_icon_uses_published_gloss(self):
        state.PEERS["other"]["pages"][0]["gloss"] = "Peer explanation"
        a = self.html("[<-](@other:course)").find(".//a")
        self.assertEqual(a.get("href"), "https://example.org/docs/course/")
        self.assertEqual(a.get("aria-label"), "Other Course")
        self.assertEqual(a.get("aria-description"), "Peer explanation")
        self.assertIn("docrender-xref", a.get("class").split())

    def test_gloss_and_title_injection_are_literal_in_prose_and_cells(self):
        title = 'Page "name" & <img src=x onerror=bad> [x](@other:course) | {.x}'
        gloss = 'A "quote" & <script>bad</script> [x](@other:course) {.x} | .fake\nnext'
        target = state.PAGES["course-intro-to-lx"]
        target.update(title=title, gloss=gloss)
        for label in ["", "!", "Text"]:
            source = "[" + label + "](@course-intro-to-lx)"
            outputs = [self.html(source), ET.fromstring("<root>" + cells.render(source, self.page) + "</root>")]
            for root in outputs:
                with self.subTest(label=label):
                    a = root.find(".//a")
                    self.assertEqual(a.get("aria-description"), gloss.replace("\n", " "))
                    self.assertIsNone(root.find(".//script"))
                    self.assertIsNone(root.find(".//img"))
                    self.assertEqual(len(root.findall(".//a")), 1)
                    self.assertNotIn("fake", a.get("class", "").split())
                    if label == "!":
                        self.assertEqual(a.get("aria-label"), title)

    def test_tsv_auto_title_entities_are_not_double_escaped(self):
        target = state.PAGES["course-intro-to-lx"]
        target["title"] = "Light [Basics] & Sound <literal> *star*"
        a = ET.fromstring(cells.render("[](@course-intro-to-lx)", self.page))
        self.assertEqual(a.text, target["title"])
        self.assertEqual(len(list(a)), 0)

    def test_tsv_icon_color_and_numeric_behavior(self):
        a = ET.fromstring(cells.render("[vv](@course-intro-to-lx){color=warn}", self.page))
        self.assertEqual(a.find("span").text, "↓")
        self.assertEqual(a.get("style"), "--dr-link-icon-color:var(--dr-warn)")
        for text, expected in [("12", 12), ("-4", -4), ("**3.5**", 3.5)]:
            self.assertEqual(cells.number(text), expected)
        self.assertIsNone(cells.number("[!](@course-intro-to-lx)"))
        self.assertIsNone(cells.number("12 units"))

    def test_icon_shorthand_does_not_rewrite_other_prose(self):
        for label in ["Next ->", "Wow!", "vv text", r"\*", r"\!"]:
            result = self.render("[" + label + "](@course-intro-to-lx)")
            self.assertEqual(result, "[" + label + "](courses/lighting/)")
        for source in ["`[->](@course-intro-to-lx)`", "```md\n[!](@course-intro-to-lx)\n```"]:
            self.assertEqual(self.render(source), source)

    def test_invalid_id_never_becomes_clickable_icon(self):
        root = self.html("[->](@missing)")
        self.assertIsNone(root.find(".//a"))
        self.assertEqual(root.find(".//span").get("class"), "docrender-dead")
        self.assertFalse(state.REFS["home"]["missing"]["ok"])

    def test_no_gloss_does_not_add_hover_to_text_links(self):
        result = self.render("[Lighting](@course-intro-to-lx)")
        self.assertEqual(result, "[Lighting](courses/lighting/)")

    def test_existing_marker_attributes_escape_once_in_cells(self):
        result = cells._inline('[Role](role/){ .dr-gloss data-gloss="A &amp; B .fake" }')
        a = ET.fromstring(result)
        self.assertEqual(a.get("data-gloss"), "A & B .fake")
        self.assertEqual(a.get("class"), "dr-gloss")

    def test_color_and_event_attributes_cannot_inject_css_or_script(self):
        a = self.html('[!](@course-intro-to-lx){color="accent;display:none" onclick="evil"}').find(".//a")
        self.assertIsNone(a.get("style"))
        self.assertIsNone(a.get("onclick"))
        self.assertGreaterEqual(len(state.REPORT["notes"]), 2)


if __name__ == "__main__":
    unittest.main()
