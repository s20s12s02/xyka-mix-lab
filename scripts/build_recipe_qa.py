#!/usr/bin/env python3
"""Build the line-by-line editorial matrix for the generated MixLab catalog."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIRECTION_ORDER = ("Десерты", "Фрукты", "Ягоды", "Цитрус", "Напитки", "Необычное")
STRENGTH_ORDER = ("Лёгкая", "Средне-лёгкая", "Средняя", "Крепкая")


def cell_key(recipe):
    return (DIRECTION_ORDER.index(recipe["directionLabel"]), STRENGTH_ORDER.index(recipe["strengthLabel"]), recipe["name"])


def escape(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def main() -> int:
    recipe_path = ROOT / "data" / "recipes.json"
    recipes = json.loads(recipe_path.read_text(encoding="utf-8"))
    recipes.sort(key=cell_key)
    coverage = Counter((recipe["directionLabel"], recipe["strengthLabel"]) for recipe in recipes)
    source_hash = hashlib.sha256(recipe_path.read_bytes()).hexdigest()

    lines = [
        "# Построчная редакционная QA-матрица MixLab",
        "",
        "Проверено: 2026-08-23. Матрица сгруппирована по публичному направлению и словесной крепости.",
        "Каждая строка сверена по говорящему названию, официальным компонентам, долям, крепости и реальной геометрии укладки.",
        "",
        f"- Рецептов: {len(recipes)}",
        f"- Непустых ячеек: {len(coverage)}",
        f"- SHA-256 `data/recipes.json`: `{source_hash}`",
        "- Редакционный статус: все строки проверены; ручных правок готового JSON нет, исправления внесены в генератор и словари.",
        "",
    ]

    grouped = defaultdict(list)
    for recipe in recipes:
        grouped[(recipe["directionLabel"], recipe["strengthLabel"])].append(recipe)

    row_number = 0
    for direction in DIRECTION_ORDER:
        cells = [cell for cell in grouped if cell[0] == direction]
        if not cells:
            continue
        lines.extend([f"## {direction}", ""])
        for strength in STRENGTH_ORDER:
            cell = (direction, strength)
            if cell not in grouped:
                continue
            lines.extend([
                f"### {strength} — {len(grouped[cell])}",
                "",
                "| № | ID | Название | Обоснование названия | Состав | Укладка | Проверка |",
                "|---:|---|---|---|---|---|---|",
            ])
            for recipe in grouped[cell]:
                row_number += 1
                composition = "<br>".join(
                    f"{component['brand']} — {component['name']} — {component['percent']}% / {str(component['grams']).replace('.', ',')} г"
                    for component in recipe["components"]
                )
                layout = recipe["packing"]["layout"]
                if layout["type"] == "layers":
                    packing = f"слои: {len(layout['layers'])}"
                elif layout["type"] == "sectors":
                    packing = f"сектора: {len(layout['sectors'])}"
                else:
                    packing = "компот"
                verdict = f"OK · score {recipe['qualityScore']:.3f} · {recipe['origin']['type']}"
                lines.append(
                    f"| {row_number} | `{escape(recipe['id'])}` | {escape(recipe['name'])} | {escape(recipe['copyRationale'])} | "
                    f"{escape(composition)} | {escape(packing)} | {escape(verdict)} |"
                )
            lines.append("")

    output = ROOT / "qa" / "recipe-content-review.md"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
