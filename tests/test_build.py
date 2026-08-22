import json
import re
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from scripts import build_html as build_module  # noqa: E402


build_html = build_module.build_html


class VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden_depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "template"}:
            self.hidden_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "template"} and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data):
        if not self.hidden_depth:
            self.parts.append(data)


class AutonomousBuildTests(unittest.TestCase):
    def build(self):
        temp = tempfile.TemporaryDirectory()
        output = Path(temp.name, "xyka.html")
        build_html(ROOT, output)
        return temp, output, output.read_text(encoding="utf-8")

    def test_build_inlines_assets_and_all_three_datasets(self):
        temp, output, html = self.build()
        self.addCleanup(temp.cleanup)
        self.assertTrue(output.exists())
        self.assertNotRegex(html, r"<script[^>]+src=")
        self.assertNotRegex(html, r"<link[^>]+href=[\"']https?://")
        self.assertIn('rel="icon" href="data:image/svg+xml,', html)
        self.assertNotIn("fetch(", html)
        self.assertNotIn("XMLHttpRequest", html)
        self.assertNotIn("serviceWorker", html)
        for data_id, filename, expected_count in (
            ("inventory-data", "inventory.json", 26),
            ("analogs-data", "analogs.json", 15),
            ("recipes-data", "recipes.json", 216),
        ):
            match = re.search(rf'<script type="application/json" id="{data_id}">(.*?)</script>', html, re.S)
            self.assertIsNotNone(match, data_id)
            self.assertEqual(len(json.loads(match.group(1))), expected_count)
            self.assertEqual(len(json.loads((ROOT / "data" / filename).read_text(encoding="utf-8"))), expected_count)

    def test_build_keeps_direction_contract_and_offline_state_contract(self):
        temp, _, html = self.build()
        self.addCleanup(temp.cleanup)
        for block in ("THESIS:", "OWN-WORLD:", "STORY:", "FIRST VIEWPORT:", "FORM:", "FINISH:"):
            self.assertIn(block, html)
        self.assertIn("xyka-mix-lab:v1", html)
        self.assertIn("safe-area-inset-bottom", html)
        self.assertIn("prefers-reduced-motion", html)

    def test_visible_static_copy_never_exposes_numeric_strength_scale(self):
        temp, _, html = self.build()
        self.addCleanup(temp.cleanup)
        parser = VisibleTextParser()
        parser.feed(html)
        visible = " ".join(parser.parts)
        self.assertNotIn("/10", visible)
        self.assertNotRegex(visible, r"крепост\w*\s+[1-9](?:[,.][05])?")
        self.assertNotIn("ползунок крепости", visible.lower())

    def test_signature_action_and_icon_system_match_the_approved_surface(self):
        temp, _, html = self.build()
        self.addCleanup(temp.cleanup)
        self.assertNotIn(">×</button>", html)
        self.assertRegex(html, r'class="drawer-close"[^>]*>\s*<svg')
        self.assertRegex(html, r"\.primary-action\s*\{[^}]*clip-path:")

    def test_pages_build_keeps_root_index_identical_to_versioned_artifact(self):
        publisher = getattr(build_module, "build_pages", None)
        self.assertIsNotNone(publisher, "Pages-сборщик ещё не реализован")
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            versioned, entrypoint = publisher(ROOT, output_root)
            self.assertEqual(versioned.name, "xyka_mix_lab_2026-08-22.html")
            self.assertEqual(entrypoint.name, "index.html")
            self.assertEqual(versioned.read_bytes(), entrypoint.read_bytes())
            self.assertIn("Моя рецептурная — XYKA PRO", entrypoint.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
