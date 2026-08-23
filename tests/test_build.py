import json
import base64
import hashlib
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
        manifest_path = ROOT / "src" / "assets" / "manifest.json"
        self.assertTrue(manifest_path.exists(), "asset manifest is missing")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(len(manifest), 37)
        self.assertEqual(sum(item["key"].startswith("tobacco:") for item in manifest), 26)
        self.assertEqual(sum(item["key"].startswith("direction:") for item in manifest), 6)
        self.assertEqual(sum(item["key"].startswith("strength:") for item in manifest), 5)
        for asset in manifest:
            path = ROOT / "src" / "assets" / asset["file"]
            payload = path.read_bytes()
            self.assertEqual(path.suffix, ".webp")
            self.assertEqual(hashlib.sha256(payload).hexdigest(), asset["sha256"])
            self.assertEqual(len(payload), asset["bytes"])
            self.assertGreater(asset["width"], 0)
            self.assertGreater(asset["height"], 0)
        assets_match = re.search(r'<script type="application/json" id="asset-data">(.*?)</script>', html, re.S)
        self.assertIsNotNone(assets_match)
        embedded_assets = json.loads(assets_match.group(1))
        self.assertEqual(set(embedded_assets), {item["key"] for item in manifest})
        for value in embedded_assets.values():
            self.assertTrue(value.startswith("data:image/webp;base64,"))
            self.assertTrue(base64.b64decode(value.split(",", 1)[1]))
        recipe_count = len(json.loads((ROOT / "data" / "recipes.json").read_text(encoding="utf-8")))
        for data_id, filename, expected_count in (
            ("inventory-data", "inventory.json", 26),
            ("analogs-data", "analogs.json", 15),
            ("recipes-data", "recipes.json", recipe_count),
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
        self.assertIn("xyka-mix-lab:v2", html)
        self.assertIn("xyka-mix-lab:v1", html, "v1 key is retained only for pantry migration")
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

    def test_random_action_and_icon_system_match_the_approved_surface(self):
        temp, _, html = self.build()
        self.addCleanup(temp.cleanup)
        self.assertNotIn(">×</button>", html)
        self.assertRegex(html, r'class="drawer-close"[^>]*>\s*<svg')
        self.assertNotIn('id="find-button"', html)
        self.assertNotIn(">Подобрать<", html)
        self.assertIn('id="random-button"', html)
        self.assertRegex(html, r"@media\s*\(prefers-color-scheme:\s*dark\)[\s\S]*?\.strength-option img\s*\{[^}]*background:\s*#fffaf3;")

    def test_hidden_drawer_cannot_be_overridden_by_component_display(self):
        temp, _, html = self.build()
        self.addCleanup(temp.cleanup)
        self.assertRegex(html, r"\[hidden\]\[hidden\]\s*\{\s*display:\s*none;")

    def test_mobile_action_row_collapses_without_submit_button(self):
        temp, _, html = self.build()
        self.addCleanup(temp.cleanup)
        self.assertRegex(html, r"@media\s*\(max-width:\s*380px\)[\s\S]*?\.action-row\s*\{\s*grid-template-columns:\s*1fr;")

    def test_mixlab_copy_and_hidden_quality_metadata(self):
        temp, _, html = self.build()
        self.addCleanup(temp.cleanup)
        parser = VisibleTextParser()
        parser.feed(html)
        visible = " ".join(parser.parts)
        self.assertTrue("MixLab — миксы для XYKA PRO" in html, "MixLab title is missing")
        self.assertNotIn("Моя рецептурная", visible)
        self.assertNotIn("Происхождение", visible)
        self.assertNotIn("Источники", visible)
        self.assertNotIn("Ограничения и аллергены", visible)
        self.assertNotIn("официальной инструкции XYKA PRO", visible)
        self.assertNotIn("Интернет нужен", visible)
        self.assertNotIn("Уверенность", visible)
        self.assertNotIn('id="confidence-filter"', html)
        self.assertNotIn('class="recipe-hook"', html)
        self.assertNotIn('class="detail-hook"', html)
        self.assertNotIn("<h3>Ноты</h3>", html)
        self.assertIn("Никотин вызывает зависимость", visible)

    def test_composition_ring_contract_is_embedded(self):
        temp, _, html = self.build()
        self.addCleanup(temp.cleanup)
        self.assertTrue("composition-ring" in html, "composition ring class is missing")
        self.assertTrue("rotate(-90" in html, "composition ring must start at 12 o'clock")
        self.assertTrue("stroke-dasharray" in html, "composition ring segments are missing")
        self.assertTrue("visualColor" in html, "stable ingredient colors are missing")

    def test_packing_diagrams_and_official_component_copy_are_embedded(self):
        temp, _, html = self.build()
        self.addCleanup(temp.cleanup)
        self.assertIn("packing-sector-diagram", html)
        self.assertIn("packing-layer-diagram", html)
        self.assertIn("sectorGeometry", html)
        self.assertIn("layerGeometry", html)
        self.assertIn("packing-sector-icon", html)
        self.assertIn("packing-sector-leader", html)
        self.assertIn(
            "Слой у нагревателя закладывайте в капсулу первым: он ложится на дно, а после переворота капсулы и установки в XYKA PRO окажется сверху, ближе к нагревателю.",
            html,
        )
        self.assertRegex(html, r"window\.XykaCore\s*=\s*\{[^}]*sectorGeometry")
        self.assertRegex(html, r"window\.XykaCore\s*=\s*\{[^}]*layerGeometry")
        self.assertRegex(html, r"window\.XykaCore\s*=\s*\{[^}]*migrateLegacyPantryState")
        self.assertRegex(html, r"item\.brand[\s\S]{0,160}item\.name")
        for forbidden in ("Отвесьте 10 г", "самый яркий акцент", "остаётся отделённым"):
            self.assertNotIn(forbidden, html)

    def test_pages_build_keeps_root_index_identical_to_versioned_artifact(self):
        publisher = getattr(build_module, "build_pages", None)
        self.assertIsNotNone(publisher, "Pages-сборщик ещё не реализован")
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)
            versioned, entrypoint = publisher(ROOT, output_root)
            self.assertEqual(versioned.name, "xyka_mix_lab_2026-08-22.html")
            self.assertEqual(entrypoint.name, "index.html")
            self.assertEqual(versioned.read_bytes(), entrypoint.read_bytes())
            self.assertIn("MixLab — миксы для XYKA PRO", entrypoint.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
