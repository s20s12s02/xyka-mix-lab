import json
import math
import re
import tempfile
import unittest
from collections import Counter, defaultdict
from itertools import combinations
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
            self.assertTrue(item.get("copy", {}).get("titleTokens"), item["id"])
            self.assertTrue(item.get("copy", {}).get("sensoryRole"), item["id"])
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

    @staticmethod
    def overlap(first, second):
        first_shares = {component["tobaccoId"]: component["percent"] for component in first["components"]}
        second_shares = {component["tobaccoId"]: component["percent"] for component in second["components"]}
        return sum(min(first_shares.get(item_id, 0), second_shares.get(item_id, 0)) for item_id in first_shares | second_shares) / 100

    def test_recipes_have_valid_percentages_grams_and_official_component_names(self):
        self.assertGreater(len(self.recipes), 0)
        self.assertEqual(len({recipe["id"] for recipe in self.recipes}), len(self.recipes))
        for recipe in self.recipes:
            components = recipe["components"]
            self.assertGreaterEqual(len(components), 2)
            self.assertLessEqual(len(components), 4)
            self.assertEqual(sum(component["percent"] for component in components), 100)
            for component in components:
                self.assertIn(component["tobaccoId"], self.by_id)
                self.assertEqual(component["brand"], self.by_id[component["tobaccoId"]]["brand"])
                self.assertEqual(component["name"], self.by_id[component["tobaccoId"]]["name"])
                self.assertEqual(component["percent"] % 5, 0)
                self.assertEqual(component["grams"], component["percent"] / 10)
                self.assertLessEqual(component["percent"], self.by_id[component["tobaccoId"]]["maxShare"])

    def test_ingredient_sets_are_globally_unique_and_share_overlap_is_bounded(self):
        ingredient_sets = [frozenset(component["tobaccoId"] for component in recipe["components"]) for recipe in self.recipes]
        self.assertEqual(len(ingredient_sets), len(set(ingredient_sets)))
        for index, first in enumerate(self.recipes):
            for second in self.recipes[index + 1:]:
                overlap = self.overlap(first, second)
                self.assertLess(overlap, .95, (first["id"], second["id"], overlap))
                first_cell = (first["directions"][0], first["strengthLabel"])
                second_cell = (second["directions"][0], second["strengthLabel"])
                if first_cell == second_cell:
                    self.assertLess(overlap, .85, (first["id"], second["id"], overlap))

    def test_quality_floor_cell_cap_and_nonempty_published_strengths(self):
        coverage = Counter((recipe["directions"][0], recipe["strengthLabel"]) for recipe in self.recipes)
        self.assertEqual(
            {direction for direction, _ in coverage},
            {"dessert", "fruit", "berry", "citrus", "drink", "unusual"},
        )
        self.assertTrue(all(1 <= count <= 8 for count in coverage.values()))
        for recipe in self.recipes:
            self.assertGreaterEqual(recipe["qualityScore"], .65, recipe["id"])

    def test_public_direction_is_the_strongest_weighted_composition_direction(self):
        tie_order = ("unusual", "drink", "berry", "dessert", "fruit", "citrus")
        for recipe in self.recipes:
            scores = {direction: 0.0 for direction in tie_order}
            for component in recipe["components"]:
                weights = self.by_id[component["tobaccoId"]]["directionWeights"]
                percent = component["percent"]
                scores["dessert"] += weights.get("dessert", 0) * percent
                scores["fruit"] += weights.get("fruit", 0) * percent
                scores["berry"] += weights.get("berry", 0) * percent
                scores["citrus"] += weights.get("citrus", 0) * percent
                scores["drink"] += (weights.get("drink", 0) + weights.get("tea", 0)) * percent
                scores["unusual"] += (weights.get("unusual", 0) + weights.get("floral", 0)) * percent
            expected = max(tie_order, key=lambda direction: (scores[direction], -tie_order.index(direction)))
            self.assertEqual(recipe["directions"], [expected], (recipe["id"], scores))

    def test_one_ingredient_cannot_flood_a_direction_and_strength_cell(self):
        usage_by_cell = defaultdict(Counter)
        pairs_by_cell = defaultdict(Counter)
        for recipe in self.recipes:
            cell = (recipe["directions"][0], recipe["strengthLabel"])
            tobacco_ids = sorted(component["tobaccoId"] for component in recipe["components"])
            usage_by_cell[cell].update(tobacco_ids)
            pairs_by_cell[cell].update(combinations(tobacco_ids, 2))
        for cell, usage in usage_by_cell.items():
            self.assertLessEqual(max(usage.values()), 3, (cell, usage.most_common(1)[0]))
            self.assertLessEqual(max(pairs_by_cell[cell].values()), 1, (cell, pairs_by_cell[cell].most_common(1)[0]))

    def test_mix_strength_is_independently_recomputed_and_never_very_strong(self):
        for recipe in self.recipes:
            expected = round(
                sum(self.by_id[c["tobaccoId"]]["strengthIndex"] * c["percent"] for c in recipe["components"]) / 100,
                1,
            )
            self.assertEqual(recipe["strengthIndex"], expected)
            self.assertEqual(recipe["strengthLabel"], strength_label(expected))
            self.assertNotEqual(recipe["strengthLabel"], "Очень крепкая")
            strong_share = sum(
                component["percent"]
                for component in recipe["components"]
                if self.by_id[component["tobaccoId"]]["strengthIndex"] >= 6.5
            )
            if recipe["strengthLabel"] == "Лёгкая":
                self.assertLessEqual(strong_share, 10, recipe["id"])
            if recipe["strengthLabel"] == "Средне-лёгкая":
                self.assertLessEqual(strong_share, 20, recipe["id"])

    def test_every_owned_tobacco_is_used_at_least_five_times(self):
        usage = Counter(c["tobaccoId"] for r in self.recipes for c in r["components"])
        self.assertEqual(set(usage), set(self.by_id))
        self.assertGreaterEqual(min(usage.values()), 5)

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

    def test_packing_layouts_cover_every_component_exactly_once(self):
        forbidden = (
            "отвесьте 10 г",
            "самый яркий акцент",
            "остаётся отделённым",
            "остается отделенным",
        )
        for recipe in self.recipes:
            self.assertIn(recipe["packing"]["method"], {"компот", "сектора", "слои"})
            packing_text = json.dumps(recipe["packing"], ensure_ascii=False).lower()
            self.assertFalse(any(phrase in packing_text for phrase in forbidden), recipe["id"])
            layout = recipe["packing"]["layout"]
            self.assertEqual(layout["type"], {"компот": "compote", "сектора": "sectors", "слои": "layers"}[recipe["packing"]["method"]])
            component_ids = [component["tobaccoId"] for component in recipe["components"]]
            if layout["type"] == "sectors":
                sectors = layout["sectors"]
                self.assertEqual(sum(sector["percent"] for sector in sectors), 100)
                self.assertCountEqual([sector["tobaccoId"] for sector in sectors], component_ids)
            elif layout["type"] == "layers":
                layers = layout["layers"]
                self.assertGreaterEqual(len(layers), 2, recipe["id"])
                self.assertEqual(
                    recipe["packing"]["instructions"],
                    "Слой у нагревателя закладывайте в капсулу первым: он ложится на дно, а после переворота капсулы и установки в XYKA PRO окажется сверху, ближе к нагревателю.",
                    recipe["id"],
                )
                self.assertEqual(sum(layer["percent"] for layer in layers), 100)
                packed_ids = [segment["tobaccoId"] for layer in layers for segment in layer["segments"]]
                self.assertCountEqual(packed_ids, component_ids)
                self.assertEqual(layers[0]["position"], "у нагревателя")
                for layer in layers:
                    self.assertEqual(sum(segment["percent"] for segment in layer["segments"]), layer["percent"])
            else:
                self.assertTrue(recipe["packing"]["instructions"].strip())
            self.assertGreaterEqual(recipe["heat"]["startC"], 220)
            self.assertLessEqual(recipe["heat"]["startC"], 315)
            self.assertGreaterEqual(recipe["heat"]["workC"], 220)
            self.assertLessEqual(recipe["heat"]["workC"], recipe["heat"]["startC"])
            self.assertTrue(recipe["taste"]["start"])
            self.assertTrue(recipe["taste"]["middle"])
            self.assertTrue(recipe["taste"]["aftertaste"])
            self.assertTrue(recipe["whyItWorks"])
            self.assertTrue(recipe["sources"])

    def test_recipe_names_are_editorial_unique_and_replace_component_lists(self):
        names = [recipe["name"] for recipe in self.recipes]
        self.assertEqual(len(set(names)), len(names))
        expected_examples = {
            frozenset(("sapphire-italian-tiramisu", "bonche-cookie", "bonche-caramel", "kraken-medium-seco-peanut")): "Итальянский сливочный десерт с арахисом",
            frozenset(("sebero-strawberry", "sebero-energetik", "severny-raspberry-ruby")): "Клубнично-малиновый энергетик",
            frozenset(("sebero-strawberry", "satyr-california-cola", "dogma-klubyana")): "Клубничная кола",
            frozenset(("severny-chifir", "dogma-krymskaya-lavanda", "bonche-caramel", "dogma-sakura")): "Цветочный чифир",
            frozenset(("jent-lemon-pie", "banger-evergreen")): "Хвойный лимонный пирог",
            frozenset(("sapphire-italian-tiramisu", "sebero-energetik")): "Бодрый тирамису",
        }
        recipes_by_signature = {
            frozenset(component["tobaccoId"] for component in recipe["components"]): recipe
            for recipe in self.recipes
        }
        for signature, expected_name in expected_examples.items():
            self.assertEqual(recipes_by_signature[signature]["name"], expected_name)
        for recipe in self.recipes:
            self.assertNotIn("hook", recipe, recipe["id"])
            self.assertNotIn("·", recipe["name"])
            self.assertNotIn(",", recipe["name"], recipe["id"])
            self.assertNotRegex(recipe["name"], r"\s\d+$")
            self.assertNotIn(" с нотой ", recipe["name"].lower())
            self.assertNotIn(" в оттенках ", recipe["name"].lower())
            self.assertLessEqual(len(recipe["name"]), 64)
            component_tokens = {
                token.lower()
                for component in recipe["components"]
                for token in self.by_id[component["tobaccoId"]]["copy"]["titleTokens"]
            }
            self.assertTrue(any(token in recipe["name"].lower() for token in component_tokens), recipe["id"])
            self.assertTrue(recipe["copyRationale"].strip(), recipe["id"])
            self.assertNotIn("confidence", recipe)
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

    def test_editorial_qa_matrix_covers_every_generated_recipe_once(self):
        matrix = (ROOT / "qa" / "recipe-content-review.md").read_text(encoding="utf-8")
        for recipe in self.recipes:
            self.assertEqual(matrix.count(f"`{recipe['id']}`"), 1, recipe["id"])
        self.assertIn(f"- Рецептов: {len(self.recipes)}", matrix)
        self.assertIn("Редакционный статус: все строки проверены", matrix)


if __name__ == "__main__":
    unittest.main()
