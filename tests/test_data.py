import json
import hashlib
import math
import re
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

from scripts.generate_data import (  # noqa: E402
    build_analogs,
    build_inventory,
    build_recipes,
    strength_label,
    write_outputs,
)


class InventoryContractTests(unittest.TestCase):
    def setUp(self):
        self.inventory = build_inventory()
        self.by_id = {item["id"]: item for item in self.inventory}

    def test_inventory_has_exactly_26_unique_owned_tobaccos(self):
        self.assertEqual(len(self.inventory), 26)
        self.assertEqual(len(self.by_id), 26)
        self.assertIn("dogma-izhevika", self.by_id)
        self.assertIn("dogma-krymskaya-lavanda", self.by_id)

    def test_strength_calibration_respects_collection_anchors(self):
        for item in self.inventory:
            value = item["strengthIndex"]
            self.assertGreaterEqual(value, 1)
            self.assertLessEqual(value, 10)
            self.assertTrue(math.isclose(value * 2, round(value * 2)))
            self.assertEqual(item["strengthLabel"], strength_label(value))

        sebero = [i for i in self.inventory if i["brand"] == "Sebero"]
        dogma = [i for i in self.inventory if i["brand"] == "Dogma"]
        self.assertTrue(all(i["strengthIndex"] < 4.5 for i in sebero))
        self.assertTrue(all(i["strengthIndex"] >= 6.5 for i in dogma))
        self.assertGreaterEqual(self.by_id["kraken-medium-seco-peanut"]["strengthIndex"], 6.5)
        self.assertTrue(all(i["strengthIndex"] < 8.5 for i in self.inventory))

    def test_inventory_excludes_banned_profiles_and_documents_lavender(self):
        banned = {"алкоголь", "ментол", "лёд", "холодок", "бекон", "сыр", "мясо", "томат"}
        for item in self.inventory:
            searchable = " ".join([item["name"], item["profile"], *item["tags"]]).lower()
            tokens = set(re.findall(r"[а-яё]+", searchable))
            self.assertFalse(tokens & banned, item["id"])
        self.assertNotIn("сыр", set(re.findall(r"[а-яё]+", "сигарное сырьё")))
        self.assertIn("аллерген", " ".join(self.by_id["dogma-krymskaya-lavanda"]["warnings"]).lower())

    def test_inventory_has_visual_and_search_metadata(self):
        colors = set()
        icon_keys = set()
        for item in self.inventory:
            self.assertTrue(item.get("hook", "").strip(), item["id"])
            self.assertRegex(item.get("visualColor", ""), r"^#[0-9a-fA-F]{6}$", item["id"])
            self.assertTrue(item.get("iconKey", "").startswith("tobacco:"), item["id"])
            colors.add(item.get("visualColor", "").lower())
            icon_keys.add(item.get("iconKey", ""))
        self.assertEqual(len(icon_keys), 26)
        self.assertGreaterEqual(len(colors), 20)


class AnalogContractTests(unittest.TestCase):
    def setUp(self):
        self.inventory = build_inventory()
        self.inventory_ids = {item["id"] for item in self.inventory}
        self.analogs = build_analogs(self.inventory)

    def test_similarity_is_recomputed_from_six_declared_dimensions(self):
        weights = {
            "aroma": 0.35,
            "role": 0.20,
            "sensory": 0.15,
            "strength": 0.15,
            "heat": 0.10,
            "leaf": 0.05,
        }
        for analog in self.analogs:
            expected = round(sum(analog["criteria"][key] * weight for key, weight in weights.items()), 2)
            self.assertEqual(analog["similarity"], expected)
            self.assertGreaterEqual(analog["similarity"], 0.70)
            self.assertLessEqual(len(analog["replacementIds"]), 2)
            self.assertTrue(set(analog["replacementIds"]).issubset(self.inventory_ids))


class RecipeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = build_inventory()
        cls.by_id = {item["id"]: item for item in cls.inventory}
        cls.analogs = build_analogs(cls.inventory)
        cls.recipes = build_recipes(cls.inventory, cls.analogs)

    def test_at_least_180_unique_recipes_have_valid_percentages_and_grams(self):
        self.assertGreaterEqual(len(self.recipes), 180)
        self.assertEqual(len({recipe["id"] for recipe in self.recipes}), len(self.recipes))
        signatures = set()
        for recipe in self.recipes:
            components = recipe["components"]
            self.assertGreaterEqual(len(components), 2)
            self.assertLessEqual(len(components), 4)
            self.assertEqual(sum(component["percent"] for component in components), 100)
            for component in components:
                self.assertIn(component["tobaccoId"], self.by_id)
                self.assertEqual(component["percent"] % 5, 0)
                self.assertEqual(component["grams"], component["percent"] / 10)
                self.assertLessEqual(component["percent"], self.by_id[component["tobaccoId"]]["maxShare"])
            signature = tuple(sorted((c["tobaccoId"], c["percent"]) for c in components))
            self.assertNotIn(signature, signatures)
            signatures.add(signature)

    def test_recipe_ids_and_compositions_remain_stable(self):
        pairs = sorted(
            (
                recipe["id"],
                tuple(sorted((component["tobaccoId"], component["percent"]) for component in recipe["components"])),
            )
            for recipe in self.recipes
        )
        payload = json.dumps(pairs, ensure_ascii=False, separators=(",", ":"))
        self.assertEqual(len(pairs), 216)
        self.assertEqual(
            hashlib.sha256(payload.encode("utf-8")).hexdigest(),
            "9d793bd4e7d7659c74bb3c0bacd00af31d652ca280c193b10a099c34b8d8516f",
        )

    def test_mix_strength_is_independently_recomputed_and_never_very_strong(self):
        for recipe in self.recipes:
            expected = round(
                sum(self.by_id[c["tobaccoId"]]["strengthIndex"] * c["percent"] for c in recipe["components"]) / 100,
                1,
            )
            self.assertEqual(recipe["strengthIndex"], expected)
            self.assertEqual(recipe["strengthLabel"], strength_label(expected))
            self.assertNotEqual(recipe["strengthLabel"], "Очень крепкая")

    def test_every_owned_tobacco_is_used_at_least_five_times(self):
        usage = Counter(c["tobaccoId"] for r in self.recipes for c in r["components"])
        self.assertEqual(set(usage), set(self.by_id))
        self.assertGreaterEqual(min(usage.values()), 5)

    def test_six_public_directions_each_have_strength_coverage(self):
        coverage = defaultdict(int)
        for recipe in self.recipes:
            for direction in recipe["directions"]:
                coverage[(direction, recipe["strengthLabel"])] += 1
        self.assertEqual(
            {direction for direction, _ in coverage},
            {"dessert", "fruit", "berry", "citrus", "drink", "unusual"},
        )
        for cell, count in coverage.items():
            self.assertGreaterEqual(count, 6, cell)

    def test_adapted_recipes_disclose_original_formula_and_valid_substitutions(self):
        adapted = [recipe for recipe in self.recipes if recipe["origin"]["type"] == "adapted"]
        self.assertGreaterEqual(len(adapted), 6)
        for recipe in adapted:
            self.assertTrue(recipe["origin"]["originalFormula"])
            self.assertTrue(recipe["origin"]["adaptationNote"])
            self.assertTrue(recipe["origin"]["substitutions"])
            for substitution in recipe["origin"]["substitutions"]:
                self.assertGreaterEqual(substitution["similarity"], 0.70)
                self.assertLessEqual(len(substitution["replacementIds"]), 2)

    def test_recipes_have_complete_cooking_and_taste_guidance(self):
        for recipe in self.recipes:
            self.assertIn(recipe["packing"]["method"], {"компот", "сектора", "слои"})
            self.assertIn("10 г", recipe["packing"]["instructions"])
            self.assertIn("рыхло", recipe["packing"]["instructions"].lower())
            orientation = recipe["packing"].get("orientation", {})
            self.assertTrue(orientation, recipe["id"])
            self.assertIn("первым в пустую капсулу", orientation.get("firstInCapsule", "").lower())
            self.assertIn("после переворота ближе к нагревателю", orientation.get("firstInCapsule", "").lower())
            self.assertIn("последним", orientation.get("lastInCapsule", "").lower())
            self.assertIn("после переворота дальше от нагревателя", orientation.get("lastInCapsule", "").lower())
            self.assertTrue(recipe["packing"].get("steps"), recipe["id"])
            packed_ids = {
                tobacco_id
                for step in recipe["packing"].get("steps", [])
                for tobacco_id in step["tobaccoIds"]
            }
            self.assertEqual(packed_ids, {component["tobaccoId"] for component in recipe["components"]})
            for step in recipe["packing"].get("steps", []):
                self.assertGreaterEqual(step["order"], 1)
                self.assertTrue(step["placement"])
                self.assertTrue(step["reason"])
            self.assertGreaterEqual(recipe["heat"]["startC"], 220)
            self.assertLessEqual(recipe["heat"]["startC"], 315)
            self.assertGreaterEqual(recipe["heat"]["workC"], 220)
            self.assertLessEqual(recipe["heat"]["workC"], recipe["heat"]["startC"])
            self.assertTrue(recipe["taste"]["start"])
            self.assertTrue(recipe["taste"]["middle"])
            self.assertTrue(recipe["taste"]["aftertaste"])
            self.assertTrue(recipe["whyItWorks"])
            self.assertTrue(recipe["sources"])

    def test_recipe_names_hooks_notes_and_component_order_are_ui_ready(self):
        names = [recipe["name"] for recipe in self.recipes]
        hooks = [recipe.get("hook", "") for recipe in self.recipes]
        self.assertEqual(len(set(names)), 216)
        self.assertEqual(len(set(hooks)), 216)
        for recipe in self.recipes:
            self.assertNotIn("·", recipe["name"])
            self.assertNotRegex(recipe["name"], r"\s\d+$")
            self.assertNotIn(" с нотой ", recipe["name"].lower())
            self.assertNotIn(" в оттенках ", recipe["name"].lower())
            self.assertLessEqual(len(recipe["name"]), 42)
            self.assertTrue(recipe.get("hook", ""), recipe["id"])
            self.assertNotIn("·", recipe.get("hook", ""))
            self.assertLessEqual(len(recipe.get("hook", "")), 110)
            self.assertEqual(
                [component["percent"] for component in recipe["components"]],
                sorted((component["percent"] for component in recipe["components"]), reverse=True),
            )
            pyramid = recipe.get("notePyramid", {})
            self.assertEqual(set(pyramid), {"top", "heart", "base"})
            self.assertTrue(all(pyramid[level] for level in ("top", "heart", "base")))

    def test_write_outputs_produces_parseable_project_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            write_outputs(Path(temp_dir))
            for filename in ("inventory.json", "analogs.json", "recipes.json"):
                path = Path(temp_dir, filename)
                self.assertTrue(path.exists())
                self.assertTrue(json.loads(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
