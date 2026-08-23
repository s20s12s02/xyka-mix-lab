#!/usr/bin/env python3
"""Generate the verified inventory, analog map and deterministic recipe library."""

from __future__ import annotations

import argparse
import itertools
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple


INTERNAL_DIRECTION_LABELS = {
    "dessert": "Десертное",
    "fruit": "Фруктово-тропическое",
    "berry": "Ягодное",
    "citrus": "Цитрусово-кислое",
    "tea": "Чайное",
    "drink": "Напиточное",
    "floral": "Цветочно-парфюмерное",
    "unusual": "Хвойно-травяное / необычное",
}

PUBLIC_DIRECTION_LABELS = {
    "dessert": "Десерты",
    "fruit": "Фрукты",
    "berry": "Ягоды",
    "citrus": "Цитрус",
    "drink": "Напитки",
    "unusual": "Необычное",
}

# Internal lanes stay unchanged so recipe IDs and compositions remain stable.
DIRECTION_LABELS = INTERNAL_DIRECTION_LABELS

ORIGIN_LABELS = {
    "exact": "Точный рецепт",
    "adapted": "Адаптированный",
    "authored": "Авторский",
    "experimental": "Экспериментальный",
}

STRENGTH_TARGETS = ("Средне-лёгкая", "Средняя", "Крепкая")
LIGHT_DIRECTIONS = ("fruit", "berry", "drink")

SOURCE_URLS = {
    "xyka-manual": "https://xyka.pro/manual",
    "xyka-packings": "https://t.me/s/xyka_pro?q=%23XYKA_%D0%B7%D0%B0%D0%B8%D0%B2%D0%BA%D0%B8",
    "vanyazabey": "https://t.me/s/vanyazabeygroop",
    "htreviews": "https://htreviews.org/",
}

VISUAL_COLORS = {
    "sebero-honey-melon": "#D9A441",
    "sebero-strawberry": "#D9676B",
    "sebero-energetik": "#C7A337",
    "sebero-watermelon-melon-cola": "#B76A4A",
    "jent-lemon-pie": "#D7B94A",
    "jent-tropez": "#E2C94B",
    "sapphire-italian-tiramisu": "#8A604C",
    "sapphire-redberry": "#A94D5F",
    "xperience-multy-fruity": "#E08A45",
    "severny-pink-flamingo": "#D26A8A",
    "severny-white-tea": "#A5A36C",
    "severny-chifir": "#796755",
    "severny-raspberry-ruby": "#B94F68",
    "trofimoffs-wild-strawberry": "#A74B56",
    "dogma-sakura": "#C78391",
    "dogma-klubyana": "#9F4054",
    "dogma-gerlinad": "#776A66",
    "dogma-black-currant": "#69506F",
    "dogma-izhevika": "#55445F",
    "dogma-krymskaya-lavanda": "#8A7194",
    "banger-evergreen": "#537C69",
    "satyr-california-cola": "#875743",
    "bonche-brownie": "#70483D",
    "bonche-cookie": "#B58C63",
    "bonche-caramel": "#B77842",
    "kraken-medium-seco-peanut": "#9B7547",
}


def strength_label(value: float) -> str:
    if value < 2:
        return "Безникотиновая"
    if value < 3.5:
        return "Лёгкая"
    if value < 4.5:
        return "Средне-лёгкая"
    if value < 6.5:
        return "Средняя"
    if value < 8.5:
        return "Крепкая"
    return "Очень крепкая"


def _item(
    item_id: str,
    brand: str,
    line: str,
    name: str,
    short_name: str,
    profile: str,
    tags: Sequence[str],
    families: Sequence[str],
    directions: Dict[str, float],
    strength: float,
    aroma_power: int,
    max_share: int,
    heat_resistance: str,
    heat_rank: int,
    rating: float | None,
    votes: int | None,
    warnings: Sequence[str] = (),
    calibration_note: str = "",
) -> Dict[str, Any]:
    return {
        "id": item_id,
        "brand": brand,
        "line": line,
        "name": name,
        "shortName": short_name,
        "profile": profile,
        "hook": profile,
        "tags": list(tags),
        "families": list(families),
        "directionWeights": directions,
        "strengthIndex": strength,
        "strengthLabel": strength_label(strength),
        "aromaPower": aroma_power,
        "maxShare": max_share,
        "heatResistance": heat_resistance,
        "heatRank": heat_rank,
        "visualColor": VISUAL_COLORS[item_id],
        "iconKey": f"tobacco:{item_id}",
        "warnings": list(warnings),
        "rating": {"value": rating, "votes": votes, "source": "HTReviews"} if rating is not None else None,
        "calibrationNote": calibration_note,
        "sources": [
            {"title": "HTReviews", "url": SOURCE_URLS["htreviews"]},
            {"title": "Фото личной коллекции", "url": "../research/source-photos/"},
        ],
    }


def build_inventory() -> List[Dict[str, Any]]:
    """Return the 26 owned tobaccos with deliberately conservative strength anchors."""
    common_sebero = "Светлая линейка; пользовательские отзывы размещают вкус внутри лёгкого диапазона, без повышения по маркетинговой категории."
    common_dogma = "Сигарное сырьё учитывается как крепкое, но не приравнивается к дохе или чистой особо крепкой безароматике."
    return [
        _item("sebero-honey-melon", "Sebero", "Classic", "Honey Melon — Медовая дыня", "медовая дыня", "Сочная спелая дыня с мягкой медовой сладостью.", ["дыня", "мёд", "сладость"], ["melon", "honey", "fruit"], {"fruit": 1.0, "dessert": 0.45, "drink": 0.25}, 3.0, 3, 70, "средняя", 2, 4.5, 39, calibration_note=common_sebero),
        _item("sebero-strawberry", "Sebero", "Classic", "Strawberry — Клубника", "клубника", "Сочная сладкая клубника без холодка.", ["клубника", "ягода", "сладость"], ["strawberry", "berry", "fruit"], {"berry": 1.0, "fruit": 0.45, "dessert": 0.25}, 3.0, 3, 70, "средняя", 2, None, None, calibration_note=common_sebero),
        _item("sebero-energetik", "Sebero", "Classic", "Energetik — Энергетик", "энергетик", "Сладко-кислый профиль энергетического напитка без ледяного эффекта.", ["энергетик", "напиток", "кисло-сладкий"], ["energy", "citrus", "drink"], {"drink": 1.0, "citrus": 0.45, "unusual": 0.2}, 3.5, 4, 65, "средняя", 2, 4.4, 51, calibration_note=common_sebero),
        _item("sebero-watermelon-melon-cola", "Sebero", "Classic", "Арбузно-дынная кола", "арбузная кола", "Фруктовая кола с арбузом и дыней, сладкая и округлая.", ["арбуз", "дыня", "кола", "напиток"], ["watermelon", "melon", "cola", "drink"], {"drink": 0.95, "fruit": 0.85, "unusual": 0.2}, 3.5, 4, 65, "средняя", 2, 4.0, 18, calibration_note=common_sebero),
        _item("jent-lemon-pie", "JENT", "Classic", "Lemon Pie — Лимонный пирог", "лимонный пирог", "Лимонный крем и выпечка с умеренной сладостью.", ["лимон", "пирог", "крем", "выпечка"], ["lemon", "pastry", "cream", "citrus"], {"dessert": 1.0, "citrus": 0.8}, 4.0, 4, 65, "средняя", 2, 4.6, 32, calibration_note="Официальная средняя крепость смягчена пользовательским восприятием до средне-лёгкой зоны."),
        _item("jent-tropez", "JENT", "Classic", "Tropez — Лимон", "лимон Tropez", "Яркий чистый лимон с цедрой и выразительной кислинкой.", ["лимон", "цедра", "кислота"], ["lemon", "peel", "citrus"], {"citrus": 1.0, "fruit": 0.4, "drink": 0.25}, 4.0, 4, 65, "средняя", 2, 4.6, 140, calibration_note="Официальная средняя крепость смягчена пользовательским восприятием до средне-лёгкой зоны."),
        _item("sapphire-italian-tiramisu", "Sapphire Crown", "Classic", "Italian Tiramisu", "тирамису", "Кофейно-сливочный десерт с какао и мягким печеньем.", ["тирамису", "кофе", "сливки", "какао"], ["coffee", "cream", "cocoa", "pastry"], {"dessert": 1.0, "drink": 0.25, "unusual": 0.2}, 4.5, 4, 60, "средняя", 2, 4.4, 63, calibration_note="Стабильный средний сегмент по сырью и пользовательскому восприятию."),
        _item("sapphire-redberry", "Sapphire Crown", "Classic", "Redberry — Брусника", "красная ягода", "Терпкая красная ягода с заметной кислинкой.", ["брусника", "красная ягода", "кислота", "терпкость"], ["lingonberry", "berry", "tart"], {"berry": 1.0, "citrus": 0.35, "drink": 0.25}, 4.5, 4, 60, "средняя", 2, 4.4, 58, calibration_note="Стабильный средний сегмент по сырью и пользовательскому восприятию."),
        _item("xperience-multy-fruity", "Xperience by Darkside", "Core", "Multy Fruity", "тропический мультифрукт", "Манго, папайя и гуава в плотной тропической композиции.", ["манго", "папайя", "гуава", "тропики"], ["mango", "papaya", "guava", "tropical"], {"fruit": 1.0, "drink": 0.35, "unusual": 0.2}, 5.0, 5, 65, "высокая", 3, 4.5, 50, calibration_note="Средняя крепость подтверждается сырьём линии и отзывами."),
        _item("severny-pink-flamingo", "Северный", "Основная", "Розовый Фламинго", "розовый фламинго", "Грейпфрут, малина, клубника и личи в готовой композиции.", ["грейпфрут", "малина", "клубника", "личи"], ["grapefruit", "raspberry", "strawberry", "lychee"], {"berry": 0.85, "fruit": 0.75, "citrus": 0.65}, 5.0, 5, 60, "средняя", 2, 4.3, 62, calibration_note="Средний диапазон без переноса маркетинговой категории в верх шкалы."),
        _item("severny-white-tea", "Северный", "Основная", "Белый чай", "белый чай", "Мягкий белый чай с фруктами и курагой.", ["белый чай", "курага", "фрукты", "терпкость"], ["white-tea", "apricot", "tea", "fruit"], {"tea": 1.0, "fruit": 0.45, "unusual": 0.25}, 5.0, 4, 60, "средняя", 2, 4.6, 70, calibration_note="Средняя линейка; чайная терпкость не повышает никотиновую крепость."),
        _item("severny-chifir", "Северный", "Основная", "Чифир в сладость", "сладкий чифир", "Насыщенный чёрный чай со сладким округлым телом.", ["чёрный чай", "сладость", "терпкость"], ["black-tea", "tea", "tart", "sweet"], {"tea": 1.0, "unusual": 0.45, "drink": 0.25}, 5.5, 5, 60, "средняя", 2, 4.6, 126, calibration_note="Большой объём оценок подтверждает средний, местами ощутимый диапазон."),
        _item("severny-raspberry-ruby", "Северный", "Основная", "Малиновый Руби", "малиновый руби", "Малина и лесная земляника с фруктовой нотой киви.", ["малина", "земляника", "киви"], ["raspberry", "wild-strawberry", "kiwi", "berry"], {"berry": 1.0, "fruit": 0.6, "citrus": 0.2}, 5.0, 5, 60, "средняя", 2, 4.2, 20, calibration_note="Средний диапазон, оценка консервативна из-за небольшого объёма голосов."),
        _item("trofimoffs-wild-strawberry", "Trofimoff’s", "Burley", "Wild Strawberry — Дикая земляника", "дикая земляника", "Натуральная земляника на плотном Burley с сухим табачным телом.", ["земляника", "burley", "сухость", "ягода"], ["wild-strawberry", "berry", "burley", "dry"], {"berry": 1.0, "unusual": 0.3}, 7.5, 5, 70, "высокая", 3, 4.5, 118, calibration_note="Burley и отзывы удерживают вкус в крепком диапазоне, но ниже уровня дохи."),
        _item("dogma-sakura", "Dogma", "100%", "Сакура", "сакура", "Цветущая сакура с сухим сигарным фоном.", ["сакура", "цветы", "сигарный лист"], ["sakura", "floral", "cigar"], {"floral": 1.0, "unusual": 0.65, "tea": 0.2}, 7.5, 5, 50, "высокая", 3, 4.4, 112, calibration_note=common_dogma),
        _item("dogma-klubyana", "Dogma", "100%", "Клубяна", "клубяна", "Плотная клубнично-земляничная ароматика на сигарном сырье.", ["клубника", "земляника", "сигарный лист"], ["strawberry", "wild-strawberry", "berry", "cigar"], {"berry": 1.0, "fruit": 0.35, "unusual": 0.25}, 7.5, 5, 65, "высокая", 3, 4.4, 97, calibration_note=common_dogma),
        _item("dogma-gerlinad", "Dogma", "100%", "Герлинад для него", "герлинад", "Сухой парфюмерно-травяной профиль с древесным шлейфом.", ["парфюм", "травы", "древесность", "сигарный лист"], ["perfume", "herbal", "wood", "cigar"], {"floral": 0.8, "unusual": 1.0, "tea": 0.2}, 7.0, 5, 35, "высокая", 3, 4.4, 83, warnings=["Использовать как яркий акцент: профиль может быстро доминировать."], calibration_note=common_dogma),
        _item("dogma-black-currant", "Dogma", "100%", "Чёрная смородина", "чёрная смородина", "Натуральная чёрная смородина с терпкой кожицей на сигарном сырье.", ["чёрная смородина", "терпкость", "сигарный лист"], ["blackcurrant", "berry", "tart", "cigar"], {"berry": 1.0, "tea": 0.2, "drink": 0.2}, 7.5, 5, 65, "высокая", 3, 4.6, 91, calibration_note=common_dogma),
        _item("dogma-izhevika", "Dogma", "100%", "Ижевика", "ижевика", "Тёмная ежевика с кисло-терпким краем на сигарном сырье.", ["ежевика", "тёмная ягода", "терпкость", "сигарный лист"], ["blackberry", "berry", "tart", "cigar"], {"berry": 1.0, "citrus": 0.2, "unusual": 0.2}, 7.5, 5, 65, "высокая", 3, 4.6, 53, calibration_note=common_dogma),
        _item("dogma-krymskaya-lavanda", "Dogma", "100%", "Крымская лаванда", "крымская лаванда", "Натуральная ферментированная лаванда с сухим цветочно-травяным шлейфом.", ["лаванда", "цветы", "травы", "сигарный лист"], ["lavender", "floral", "herbal", "cigar"], {"floral": 1.0, "tea": 0.5, "unusual": 0.8}, 7.5, 5, 25, "высокая", 3, 4.8, 90, warnings=["Цветочный аллерген: при чувствительности к лаванде рецепт не использовать.", "Доля выше 25% может перекрыть остальные ноты."], calibration_note=common_dogma),
        _item("banger-evergreen", "Banger", "Classic", "Evergreen — Фейхоа, можжевельник", "вечнозелёный фейхоа", "Фейхоа и сухой можжевельник: фруктово-хвойная композиция.", ["фейхоа", "можжевельник", "хвоя", "травы"], ["feijoa", "juniper", "conifer", "fruit"], {"unusual": 1.0, "fruit": 0.65, "citrus": 0.25, "drink": 0.2}, 4.5, 5, 55, "высокая", 3, 4.5, 48, calibration_note="Средний диапазон; хвойная сухость не считается никотиновой крепостью."),
        _item("satyr-california-cola", "Satyr", "Classic", "California Cola", "калифорнийская кола", "Пряная сладкая кола с сухим табачным фоном.", ["кола", "специи", "напиток"], ["cola", "spice", "drink", "dry"], {"drink": 1.0, "unusual": 0.45, "dessert": 0.2}, 6.0, 5, 65, "высокая", 3, 4.5, 206, calibration_note="Большой объём отзывов удерживает вкус в верхней части среднего диапазона."),
        _item("bonche-brownie", "Bonche", "Classic", "Brownie", "брауни", "Тёмный шоколадный брауни с сухим сигарным телом.", ["брауни", "шоколад", "какао", "сигарный лист"], ["brownie", "cocoa", "chocolate", "cigar"], {"dessert": 1.0, "unusual": 0.2}, 7.5, 5, 65, "высокая", 3, 4.6, 59, calibration_note="Крепкая ароматизированная сигарная смесь, но не уровень дохи."),
        _item("bonche-cookie", "Bonche", "X", "Cookie — Печенье", "сухое печенье", "Сухое сливочное печенье на крепком сигарном сырье.", ["печенье", "сливочность", "сигарный лист"], ["cookie", "pastry", "cream", "cigar"], {"dessert": 1.0, "tea": 0.2}, 7.5, 5, 65, "высокая", 3, 4.2, 39, calibration_note="Крепкая ароматизированная сигарная смесь, но не уровень дохи."),
        _item("bonche-caramel", "Bonche", "X Notes", "Caramel — Карамель", "сухая карамель", "Концентрированная сухая карамель для акцентной доли.", ["карамель", "жжёный сахар", "сигарный лист"], ["caramel", "burnt-sugar", "dessert", "cigar"], {"dessert": 1.0, "drink": 0.45, "tea": 0.35, "unusual": 0.2}, 7.0, 5, 20, "высокая", 3, 4.7, 86, warnings=["Концентрированный модификатор: не превышать 20% в рецепте."], calibration_note="Крепкая концентрированная нота; ограничение доли важнее маркетингового названия линейки."),
        _item("kraken-medium-seco-peanut", "Kraken", "Medium Seco", "Peanut — Арахис", "жареный арахис", "Сухой жареный арахис на плотном листе Medium Seco.", ["арахис", "орех", "сухость"], ["peanut", "nut", "roasted", "dry"], {"dessert": 0.85, "unusual": 0.7, "tea": 0.2}, 7.5, 5, 65, "высокая", 3, 4.8, 63, warnings=["Арахис — распространённый пищевой аллерген."], calibration_note="Сырьё Medium Seco и поставленный пользователем якорь удерживают вкус в крепком диапазоне."),
    ]


ANALOG_BLUEPRINTS = [
    ("ананас", ["xperience-multy-fruity"], {"aroma": .85, "role": .90, "sensory": .80, "strength": .85, "heat": .80, "leaf": .90}, "Тропическое тело сохраняется; вместо чистого ананаса появятся манго, папайя и гуава."),
    ("черника", ["dogma-izhevika"], {"aroma": .82, "role": .90, "sensory": .82, "strength": .75, "heat": .90, "leaf": .70}, "Тёмная ягода и терпкость сохраняются; ежевика менее конфетная и заметно крепче."),
    ("чай масала", ["severny-chifir"], {"aroma": .72, "role": .92, "sensory": .62, "strength": .82, "heat": .85, "leaf": .95}, "Сохраняется насыщенная чайная база, но специи масала не имитируются и композиция становится чище."),
    ("ройбуш с карамелью", ["severny-white-tea", "bonche-caramel"], {"aroma": .84, "role": .92, "sensory": .82, "strength": .78, "heat": .84, "leaf": .88}, "Белый чай даёт настой, Bonche Caramel — сухую карамель; связка крепче и светлее ройбуша."),
    ("банан", ["sebero-honey-melon"], {"aroma": .70, "role": .82, "sensory": .76, "strength": .95, "heat": .88, "leaf": .92}, "Сохраняется сладкий округлый фруктовый мостик, но банановая крахмалистость сменяется дынной сочностью."),
    ("Banger Crumble", ["bonche-brownie"], {"aroma": .82, "role": .94, "sensory": .84, "strength": .72, "heat": .90, "leaf": .76}, "Обе ноты работают как плотная десертная база; брауни темнее, суше и крепче крамбла."),
    ("ваниль", ["sapphire-italian-tiramisu"], {"aroma": .72, "role": .86, "sensory": .80, "strength": .82, "heat": .86, "leaf": .88}, "Сливочная связка сохраняется, но появляется кофе и какао; доля ограничена акцентом."),
    ("лимонный леденец", ["jent-lemon-pie"], {"aroma": .78, "role": .88, "sensory": .76, "strength": .86, "heat": .88, "leaf": .92}, "Лимон сохраняется, а конфетное тело заменяется мягкой выпечкой."),
    ("красный апельсин", ["jent-tropez"], {"aroma": .80, "role": .90, "sensory": .82, "strength": .90, "heat": .88, "leaf": .92}, "Цитрусовая кислотность и цедра сохраняются; профиль становится лимонным и суше."),
    ("тёмный шоколад", ["bonche-brownie"], {"aroma": .92, "role": .96, "sensory": .90, "strength": .92, "heat": .96, "leaf": .96}, "Брауни сохраняет тёмный шоколад и добавляет текстуру выпечки."),
    ("чернослив", ["dogma-black-currant"], {"aroma": .70, "role": .84, "sensory": .78, "strength": .92, "heat": .92, "leaf": .90}, "Тёмная терпкая фруктовость сохраняется, но сухофрукт заменяется свежей смородиновой кожицей."),
    ("ирга", ["dogma-izhevika"], {"aroma": .78, "role": .90, "sensory": .84, "strength": .92, "heat": .92, "leaf": .90}, "Тёмная суховатая ягода сохраняется; ежевика чуть кислее."),
    ("смородина-апельсин-виноград", ["dogma-black-currant", "jent-tropez"], {"aroma": .84, "role": .90, "sensory": .82, "strength": .80, "heat": .88, "leaf": .82}, "Смородина остаётся ядром, лимон Tropez заменяет цитрусовую часть; виноградная сладость уменьшается."),
    ("клубничный сорбет", ["sebero-strawberry"], {"aroma": .90, "role": .92, "sensory": .82, "strength": .88, "heat": .86, "leaf": .92}, "Сохраняется клубничная сладость, а охлаждающая ассоциация сорбета намеренно исключается."),
    ("ягодный пунш", ["sapphire-redberry", "severny-raspberry-ruby"], {"aroma": .90, "role": .94, "sensory": .88, "strength": .86, "heat": .88, "leaf": .90}, "Две ягоды дают кислую и сладкую части пунша без алкогольного профиля."),
]


def build_analogs(inventory: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ids = {item["id"] for item in inventory}
    weights = {"aroma": .35, "role": .20, "sensory": .15, "strength": .15, "heat": .10, "leaf": .05}
    result = []
    for source_name, replacements, criteria, differences in ANALOG_BLUEPRINTS:
        if not set(replacements).issubset(ids):
            raise ValueError(f"Unknown replacement for {source_name}")
        score = round(sum(criteria[key] * weight for key, weight in weights.items()), 2)
        result.append({
            "sourceComponent": source_name,
            "replacementIds": replacements,
            "criteria": criteria,
            "similarity": score,
            "confidence": "высокая" if score >= .80 else "средняя",
            "differences": differences,
            "allowedRoles": ["основа", "связка", "акцент"],
            "maxTotalShare": 70 if len(replacements) == 1 else 80,
        })
    return result


FAMILY_COMPATIBILITY = {
    frozenset(("berry", "tea")): .94,
    frozenset(("berry", "citrus")): .92,
    frozenset(("berry", "cream")): .90,
    frozenset(("fruit", "tea")): .88,
    frozenset(("fruit", "citrus")): .92,
    frozenset(("fruit", "cream")): .82,
    frozenset(("citrus", "tea")): .93,
    frozenset(("citrus", "cola")): .90,
    frozenset(("berry", "cola")): .88,
    frozenset(("caramel", "coffee")): .96,
    frozenset(("caramel", "tea")): .92,
    frozenset(("caramel", "nut")): .96,
    frozenset(("caramel", "cocoa")): .96,
    frozenset(("cocoa", "berry")): .90,
    frozenset(("cocoa", "coffee")): .96,
    frozenset(("cocoa", "nut")): .94,
    frozenset(("pastry", "berry")): .92,
    frozenset(("pastry", "citrus")): .90,
    frozenset(("pastry", "cream")): .96,
    frozenset(("floral", "tea")): .92,
    frozenset(("floral", "berry")): .86,
    frozenset(("herbal", "tea")): .92,
    frozenset(("herbal", "citrus")): .90,
    frozenset(("conifer", "citrus")): .94,
    frozenset(("conifer", "berry")): .84,
    frozenset(("peanut", "cocoa")): .96,
    frozenset(("peanut", "caramel")): .96,
    frozenset(("melon", "berry")): .86,
    frozenset(("melon", "citrus")): .82,
    frozenset(("energy", "tropical")): .95,
    frozenset(("energy", "berry")): .92,
}


def _pair_harmony(first: Dict[str, Any], second: Dict[str, Any]) -> float:
    values = []
    for a in first["families"]:
        for b in second["families"]:
            if a == b:
                values.append(.98)
            else:
                values.append(FAMILY_COMPATIBILITY.get(frozenset((a, b)), .58))
    return max(values) if values else .58


def _slug(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized or "mix"


def _mix_strength(components: Sequence[Dict[str, Any]], by_id: Dict[str, Dict[str, Any]]) -> float:
    return round(sum(by_id[c["tobaccoId"]]["strengthIndex"] * c["percent"] for c in components) / 100, 1)


PUBLIC_DIRECTION_TIE_ORDER = ("unusual", "drink", "berry", "dessert", "fruit", "citrus")


def _public_direction(
    internal_direction: str,
    components: Sequence[Dict[str, Any]],
    by_id: Dict[str, Dict[str, Any]],
) -> str:
    if internal_direction in PUBLIC_DIRECTION_LABELS:
        return internal_direction
    if internal_direction in {"tea", "drink"}:
        return "drink"

    scores = {direction: 0.0 for direction in PUBLIC_DIRECTION_LABELS}
    for component in components:
        weights = by_id[component["tobaccoId"]]["directionWeights"]
        percent = component["percent"]
        scores["dessert"] += weights.get("dessert", 0) * percent
        scores["fruit"] += weights.get("fruit", 0) * percent
        scores["berry"] += weights.get("berry", 0) * percent
        scores["citrus"] += weights.get("citrus", 0) * percent
        scores["drink"] += (weights.get("drink", 0) + weights.get("tea", 0)) * percent
        scores["unusual"] += (weights.get("unusual", 0) + weights.get("floral", 0)) * percent
    return max(PUBLIC_DIRECTION_TIE_ORDER, key=lambda direction: (scores[direction], -PUBLIC_DIRECTION_TIE_ORDER.index(direction)))


def _packing_and_heat(components: Sequence[Dict[str, Any]], by_id: Dict[str, Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    items = [by_id[c["tobaccoId"]] for c in components]
    aroma_range = max(i["aromaPower"] for i in items) - min(i["aromaPower"] for i in items)
    has_modifier = any(c["percent"] <= 20 and by_id[c["tobaccoId"]]["aromaPower"] >= 5 for c in components)
    strength_range = max(i["strengthIndex"] for i in items) - min(i["strengthIndex"] for i in items)
    if has_modifier or aroma_range >= 2:
        method = "сектора"
        detail = "Разложите компоненты отдельными секторами; самый яркий акцент — в меньшем секторе у края."
    elif strength_range >= 3:
        method = "слои"
        detail = "Более жаростойкие и плотные компоненты кладите первыми, деликатные — последними, без прижима."
    else:
        method = "компот"
        detail = "Мягко соедините компоненты вилкой до равномерности, не отжимая сироп."

    orientation = {
        "firstInCapsule": "Первым в пустую капсулу — после переворота ближе к нагревателю.",
        "lastInCapsule": "Последним — после переворота дальше от нагревателя.",
    }
    if method == "компот":
        names = ", ".join(by_id[c["tobaccoId"]]["shortName"] for c in components)
        steps = [{
            "order": 1,
            "tobaccoIds": [c["tobaccoId"] for c in components],
            "placement": "Смешать вне капсулы и уложить единым рыхлым объёмом.",
            "reason": f"{names.capitalize()} близки по крепости, жаростойкости и силе аромата, поэтому раскрываются равномерно.",
        }]
    elif method == "сектора":
        steps = []
        for order, component in enumerate(components, 1):
            item = by_id[component["tobaccoId"]]
            steps.append({
                "order": order,
                "tobaccoIds": [component["tobaccoId"]],
                "placement": f"Отдельный сектор площадью около {component['percent']}% капсулы.",
                "reason": f"{item['shortName'].capitalize()} остаётся отделённым, чтобы яркость можно было контролировать тягой.",
            })
    else:
        layer_order = sorted(
            components,
            key=lambda component: (
                by_id[component["tobaccoId"]]["heatRank"],
                by_id[component["tobaccoId"]]["strengthIndex"],
                component["percent"],
            ),
            reverse=True,
        )
        grouped: List[List[Dict[str, Any]]] = []
        for component in layer_order:
            heat_rank = by_id[component["tobaccoId"]]["heatRank"]
            if grouped and by_id[grouped[-1][0]["tobaccoId"]]["heatRank"] == heat_rank:
                grouped[-1].append(component)
            else:
                grouped.append([component])
        steps = []
        for order, group in enumerate(grouped, 1):
            names = ", ".join(by_id[c["tobaccoId"]]["shortName"] for c in group)
            placement = "Первый рыхлый слой" if order == 1 else ("Последний рыхлый слой" if order == len(grouped) else "Средний рыхлый слой")
            steps.append({
                "order": order,
                "tobaccoIds": [c["tobaccoId"] for c in group],
                "placement": f"{placement}: {names}.",
                "reason": "Более жаростойкие компоненты получают больше тепла; деликатные остаются дальше от нагревателя.",
            })

    min_heat = min(i["heatRank"] for i in items)
    brands = {i["brand"] for i in items}
    if brands == {"Bonche"}:
        start, work, warmup = 315, 280, "После сигнала подождите около 3 минут; через 5 минут снизьте температуру."
    elif brands == {"Banger"}:
        start, work, warmup = 310, 270, "После выхода на старт подождите около 5 минут и снизьте температуру."
    elif brands == {"Xperience by Darkside"}:
        start, work, warmup = 315, 282, "После сигнала подождите 2–3 минуты; примерно через 5 минут перейдите к рабочей температуре."
    elif min_heat == 1:
        start, work, warmup = 285, 265, "После сигнала подождите 2 минуты и оцените аромат до снижения температуры."
    elif min_heat == 2:
        start, work, warmup = 300, 275, "После сигнала подождите 2–3 минуты; через 5–7 минут снизьте температуру."
    else:
        start, work, warmup = 315, 282, "После сигнала подождите 2–3 минуты; через 5–7 минут снизьте температуру."

    packing = {
        "method": method,
        "instructions": f"Отвесьте 10 г. {detail} Уложите смесь рыхло и сохраните свободную тягу; поверхность выровняйте без уплотнения.",
        "airflowCheck": "До установки нагревателя сделайте контрольную тягу: сопротивление не должно заметно расти.",
        "orientation": orientation,
        "steps": steps,
    }
    heat = {
        "mode": "ручной",
        "startC": start,
        "warmup": warmup,
        "workC": work,
        "adjustment": "Если аромат становится сухим или горчит, сразу снизьте температуру на 5–10 °C; если вкус пустой — добавляйте по 5 °C.",
        "source": SOURCE_URLS["xyka-packings"],
    }
    return packing, heat


TITLE_BANK = {
    "dessert": [
        "Тёплая витрина", "Какао-пауза", "Ореховый шов", "Пирог после дождя", "Карамельный полдень", "Сухой тирамису", "Ягодная кондитерская", "Печенье и цедра", "Тёмная крошка", "Дынный крем", "Брауни с характером", "Лимонная глазурь",
        "Шоколадная бумага", "Карамельный чертёж", "Ореховый вечер", "Тирамису в тени", "Лимонный бисквит", "Дынный мусс", "Какао и ягоды", "Сухая кондитерская", "Печенье на полях", "Тёмный десерт", "Ягодная глазурь", "Тёплый крамбл", "Ореховая крошка", "Шоколадный архив", "Карамельная глава", "Полночный брауни", "Лимонный крем", "Ягодный пирог", "Какао на полях", "Тихая кондитерская",
    ],
    "fruit": [
        "Тропический лист", "Розовый рынок", "Дынный горизонт", "Фруктовый атлас", "Манго на севере", "Фейхоа и солнце", "Арбузный маршрут", "Личи на полях", "Гуава в чернилах", "Спелый разворот", "Тёплые тропики", "Фруктовая экспедиция",
        "Дынный меридиан", "Арбузный полдень", "Фейхоа в саду", "Розовый фрукт", "Тропический штрих", "Манговый атлас", "Гуава на закате", "Личи в дымке", "Спелая глава", "Фруктовый почерк", "Южный маршрут", "Солнечный рынок", "Арбузная глава", "Дыня после дождя", "Манговый почерк", "Тропический полдень", "Фейхоа на полях", "Розовая гуава", "Личи и солнце", "Южный гербарий",
    ],
    "berry": [
        "Тёмная корзина", "Рубиновый след", "Смородиновый лист", "Земляничный архив", "Ягодная типография", "Ежевичный полдень", "Брусничная кромка", "Малиновый штамп", "Лесная заметка", "Красная строка", "Клубничный почерк", "Северная ягода",
        "Смородиновая ночь", "Малиновый архив", "Земляника в тени", "Ежевичный штрих", "Красная корзина", "Брусника на полях", "Ягодный разворот", "Тёмный рубин", "Лесная типография", "Клубничный лист", "Северный сбор", "Рубиновая кромка", "Смородиновый архив", "Малина после дождя", "Ежевичная строка", "Земляничный полдень", "Тёмная брусника", "Ягодный маршрут", "Красный гербарий", "Лесной рубин",
    ],
    "citrus": [
        "Цедра на полях", "Лимонная линейка", "Кислая отметка", "Грейпфрутовый штрих", "Красный цитрус", "Солнечная кромка", "Лимон и хвоя", "Цитрусовый разворот", "Звонкая цедра", "Кислый маршрут", "Тонкий лимон", "Розовый цитрус",
        "Лимонный отблеск", "Грейпфрутовый лист", "Цедровый архив", "Кислый полдень", "Розовая цедра", "Цитрус в тени", "Лимонный маршрут", "Звонкий грейпфрут", "Красный лимон", "Солнечный штамп", "Цитрусовая глава", "Кислая линия", "Грейпфрут на полях", "Лимон после дождя", "Цедровый почерк", "Розовый грейпфрут", "Солнечный лимон", "Кислый архив", "Цитрусовый лист", "Яркая цедра",
    ],
    "tea": [
        "Чайный архив", "Белый настой", "Чифирный этюд", "Лавандовая чашка", "Терпкая полка", "Чай с тёмной ягодой", "Карамельный настой", "Курага в чайнике", "Цветочный чифир", "Северная заварка", "Сладкий лист", "Чайный гербарий",
        "Белая заварка", "Чайный почерк", "Терпкий настой", "Лавандовый чай", "Чифирный лист", "Чайная пауза", "Сладкая заварка", "Курага и чай", "Северный настой", "Тёмная чашка", "Цветочный лист", "Чай на закате", "Белая чашка", "Терпкая заварка", "Чай после дождя", "Лавандовый настой", "Чифирный архив", "Сладкий чайник", "Курага в чашке", "Северный чай",
    ],
    "drink": [
        "Красный энергос", "Кола на полях", "Ягодный тоник", "Тропический заряд", "Смородиновая кола", "Дынная газировка", "Рубиновый напиток", "Кислый заряд", "Фейхоа-тоник", "Карамельная кола", "Розовый лимонад", "Энергетический лист",
        "Кола без спешки", "Энергос на полях", "Красный тоник", "Ягодная газировка", "Дынный лимонад", "Тропический тоник", "Розовая кола", "Кислый лимонад", "Фейхоа и кола", "Карамельный заряд", "Смородиновый тоник", "Газированный лист", "Красная газировка", "Кола после дождя", "Ягодный заряд", "Дынный тоник", "Тропический лимонад", "Розовый энергос", "Кислая кола", "Фейхоа на ходу",
    ],
    "floral": [
        "Сакура в чернилах", "Лавандовый лист", "Крымский гербарий", "Цветочный почерк", "Парфюмерная строка", "Сад после чая", "Розовая бумага", "Сухой букет", "Фиолетовый штамп", "Цветы и ягоды", "Чайная лаванда", "Сакура и цедра",
        "Сакура на полях", "Лаванда в тени", "Крымский букет", "Цветочный контур", "Парфюмерный штрих", "Сад в чернилах", "Розовый гербарий", "Сухая лаванда", "Фиолетовая строка", "Ягодный букет", "Чайный цветок", "Сакура на закате", "Лавандовый архив", "Крымский лист", "Цветы после дождя", "Розовый сад", "Сухой цветок", "Фиолетовый гербарий", "Сакура и чай", "Парфюмерная глава",
    ],
    "unusual": [
        "Хвойная запись", "Фейхоа в лесу", "Можжевеловый лист", "Сухой гербарий", "Арахисовый чертёж", "Чайная мастерская", "Парфюмерный эскиз", "Кола и хвоя", "Терпкий маршрут", "Лесной штамп", "Сигарная ботаника", "Необычный разворот",
        "Хвоя на полях", "Лесной фейхоа", "Можжевеловый штрих", "Сухая ботаника", "Арахисовый лист", "Чайный чертёж", "Парфюмерный архив", "Хвойная кола", "Терпкий гербарий", "Лесная гравюра", "Сигарный лист", "Дикая глава", "Можжевельник и чай", "Хвоя после дождя", "Арахисовая строка", "Сухой маршрут", "Парфюмерный лист", "Кола в лесу", "Терпкая ботаника", "Сигарный гербарий",
    ],
}

def _legacy_recipe_title(direction: str, index: int, components: Sequence[Dict[str, Any]], by_id: Dict[str, Dict[str, Any]]) -> str:
    """Recreate the historical title only for the stable recipe identifier."""
    bank = TITLE_BANK[direction][:12]
    base = bank[index % len(bank)]
    if index < len(bank):
        return base
    lead = by_id[components[0]["tobaccoId"]]["shortName"]
    accent = by_id[components[1]["tobaccoId"]]["shortName"]
    cycle = index // len(bank)
    if cycle == 1:
        return f"{base} с нотой {lead}"
    return f"{base} в оттенках {lead} и {accent}"


def _recipe_title(direction: str, index: int, components: Sequence[Dict[str, Any]], by_id: Dict[str, Dict[str, Any]]) -> str:
    bank = TITLE_BANK[direction]
    if index >= len(bank):
        raise ValueError(f"Title bank exhausted for {direction}: {index}")
    return bank[index]


HOOK_BALANCE = {
    (70, 30): "Ведущий",
    (65, 35): "Выразительный",
    (60, 40): "Собранный",
    (55, 45): "Ровный",
    (60, 25, 15): "Чисто очерченный",
    (55, 25, 20): "Сфокусированный",
    (50, 30, 20): "Объёмный",
    (45, 35, 20): "Плавный",
    (40, 40, 20): "Двойной",
    (40, 35, 25): "Многослойный",
    (45, 25, 20, 10): "Глубокий",
    (40, 30, 20, 10): "Точный",
    (35, 30, 20, 15): "Тонко собранный",
}


def _recipe_hook(components: Sequence[Dict[str, Any]], by_id: Dict[str, Dict[str, Any]]) -> str:
    percents = tuple(component["percent"] for component in components)
    balance = HOOK_BALANCE.get(percents, "Сбалансированный")
    names = [by_id[component["tobaccoId"]]["shortName"] for component in components]
    if len(names) == 2:
        return f"{balance} дуэт: {names[0]} ведёт, {names[1]} даёт оттенок."
    if len(names) == 3:
        return f"{balance} профиль: {names[0]} в основе, {names[1]} и {names[2]} дают оттенки."
    return f"{balance} профиль: {names[0]} в основе, остальные ноты собирают объём."


def _note_pyramid(components: Sequence[Dict[str, Any]], by_id: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    names = [by_id[component["tobaccoId"]]["shortName"] for component in components]
    top = list(reversed(names[-2:]))
    heart = names[:2]
    strong_leaf = any(by_id[component["tobaccoId"]]["strengthIndex"] >= 6.5 for component in components)
    base = [names[0], "сухой табачный фон" if strong_leaf else "мягкое ароматическое тело"]
    return {"top": top, "heart": heart, "base": base}


def _source_links(origin_type: str, origin_source: str | None = None) -> List[Dict[str, str]]:
    links = [{"title": "Официальная инструкция XYKA PRO", "url": SOURCE_URLS["xyka-manual"]}]
    if origin_source == "xyka-packings":
        links.append({"title": "Официальный тег #XYKA_забивки", "url": SOURCE_URLS["xyka-packings"]})
    elif origin_type == "adapted":
        links.append({"title": "#ванязабей — вкусовая идея", "url": SOURCE_URLS["vanyazabey"]})
    return links


def _make_recipe(
    recipe_id: str,
    name: str,
    direction: str,
    component_pairs: Sequence[Tuple[str, int]],
    by_id: Dict[str, Dict[str, Any]],
    origin: Dict[str, Any],
    confidence: str,
    source_key: str | None = None,
) -> Dict[str, Any]:
    components = []
    for tobacco_id, percent in sorted(component_pairs, key=lambda pair: (-pair[1], pair[0])):
        item = by_id[tobacco_id]
        components.append({
            "tobaccoId": tobacco_id,
            "brand": item["brand"],
            "name": item["name"],
            "percent": percent,
            "grams": percent / 10,
            "role": "основа" if percent >= 45 else ("связка" if percent >= 25 else "акцент"),
        })
    strength = _mix_strength(components, by_id)
    packing, heat = _packing_and_heat(components, by_id)
    ordered = components
    notes = [by_id[c["tobaccoId"]]["profile"] for c in ordered]
    warnings = sorted({warning for c in components for warning in by_id[c["tobaccoId"]]["warnings"]})
    dominant = []
    for c in ordered:
        for tag in by_id[c["tobaccoId"]]["tags"][:2]:
            if tag not in dominant:
                dominant.append(tag)
    origin = dict(origin)
    origin.setdefault("label", ORIGIN_LABELS[origin["type"]])
    public_direction = _public_direction(direction, components, by_id)
    return {
        "id": recipe_id,
        "name": name,
        "directions": [public_direction],
        "generationDirections": [direction],
        "directionLabel": PUBLIC_DIRECTION_LABELS[public_direction],
        "components": components,
        "strengthIndex": strength,
        "strengthLabel": strength_label(strength),
        "confidence": confidence,
        "hook": _recipe_hook(ordered, by_id),
        "dominantNotes": dominant[:5],
        "notePyramid": _note_pyramid(ordered, by_id),
        "taste": {
            "start": f"Сначала раскрывается {ordered[0]['name'].split(' — ')[-1].lower()}: {notes[0].lower()}",
            "middle": f"В середине подключается {ordered[1]['name'].split(' — ')[-1].lower()}, делая профиль объёмнее и ровнее.",
            "aftertaste": f"В послевкусии остаются {', '.join(dominant[1:4]) or dominant[0]}, без холодящего эффекта.",
        },
        "whyItWorks": f"Композиция строится вокруг направления «{PUBLIC_DIRECTION_LABELS[public_direction]}»: ведущая нота задаёт тему, связка добавляет переход, а акцент не перекрывает основу.",
        "packing": packing,
        "heat": heat,
        "origin": origin,
        "warnings": warnings,
        "allergens": [warning for warning in warnings if "аллерген" in warning.lower()],
        "limits": "Первые 10 минут оценивайте баланс; если акцент доминирует, в следующей забивке уменьшите его на 5 процентных пунктов.",
        "sources": _source_links(origin["type"], source_key),
    }


def _substitution(analog_by_name: Dict[str, Dict[str, Any]], source_name: str) -> Dict[str, Any]:
    analog = analog_by_name[source_name]
    return {
        "originalName": source_name,
        "replacementIds": analog["replacementIds"],
        "similarity": analog["similarity"],
        "explanation": analog["differences"],
    }


def _adapted_recipes(by_id: Dict[str, Dict[str, Any]], analogs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    a = {item["sourceComponent"]: item for item in analogs}
    specs = [
        ("adapted-energy-tropics", "Тропический энергос с красной ягодой", "drink", [("sebero-energetik", 30), ("xperience-multy-fruity", 50), ("sapphire-redberry", 20)], [("Black Burn Red Energy", 30), ("ананас", 50), ("малина", 20)], ["ананас"], "Сохранена схема 30/50/20: энергетик, тропическое тело и кислая ягода."),
        ("adapted-tea-tropics", "Тёмный чай с тропиками и ежевикой", "tea", [("severny-chifir", 50), ("xperience-multy-fruity", 30), ("dogma-izhevika", 20)], [("чай масала", 50), ("ананас", 30), ("черника", 20)], ["чай масала", "ананас", "черника"], "Идея пряного чая сохранена как чайно-тропическая, но несуществующие специи не имитируются."),
        ("adapted-warm-tea", "Тёплый карамельный чай с ягодой", "tea", [("severny-white-tea", 40), ("bonche-caramel", 20), ("sebero-honey-melon", 20), ("sapphire-redberry", 20)], [("ройбуш с карамелью", 40), ("банан", 20), ("малина", 20), ("ягодный пунш", 20)], ["ройбуш с карамелью", "банан", "ягодный пунш"], "Доля чайно-карамельной связки сохранена суммарно; дыня заменяет округлый фруктовый мостик."),
        ("adapted-berry-brownie", "Ежевичный брауни-крамбл", "dessert", [("bonche-brownie", 50), ("sapphire-italian-tiramisu", 10), ("dogma-izhevika", 40)], [("Banger Crumble", 50), ("ваниль", 10), ("черника", 40)], ["Banger Crumble", "ваниль", "черника"], "Сохранена 50/10/40 архитектура: десертная база, сливочный акцент и тёмная ягода."),
        ("adapted-citrus-candy", "Красный лимонный леденец", "citrus", [("jent-lemon-pie", 30), ("jent-tropez", 50), ("sapphire-redberry", 20)], [("лимонный леденец", 30), ("красный апельсин", 50), ("Sapphire Redberry", 20)], ["лимонный леденец", "красный апельсин"], "Конфетно-цитрусовая идея сохранена без ментола: пирог даёт тело, Tropez — кислоту и цедру."),
        ("adapted-bonche-dark", "Тёмный ягодный Bonche", "dessert", [("bonche-brownie", 35), ("dogma-black-currant", 35), ("dogma-izhevika", 30)], [("тёмный шоколад", 35), ("чернослив", 35), ("ирга", 30)], ["тёмный шоколад", "чернослив", "ирга"], "Официальная геометрия примерно равных третей сохранена; сухофрукты заменены двумя тёмными терпкими ягодами."),
        ("adapted-currant-sorbet", "Смородиновая клубника без холода", "berry", [("dogma-black-currant", 35), ("jent-tropez", 15), ("sebero-strawberry", 50)], [("смородина-апельсин-виноград", 50), ("клубничный сорбет", 50)], ["смородина-апельсин-виноград", "клубничный сорбет"], "Составная замена первой половины сохраняет смородину и цитрус; сорбет адаптирован без охлаждения."),
    ]
    result = []
    for recipe_id, name, direction, components, original, substitutions, note in specs:
        origin = {
            "type": "adapted",
            "originalFormula": [{"component": n, "percent": p} for n, p in original],
            "substitutions": [_substitution(a, source) for source in substitutions],
            "adaptationNote": note,
            "sourceTitle": "Вкусовая идея из открытого источника",
        }
        source_key = "xyka-packings" if recipe_id == "adapted-bonche-dark" else "vanyazabey"
        result.append(_make_recipe(recipe_id, name, direction, components, by_id, origin, "высокая" if all(s["similarity"] >= .8 for s in origin["substitutions"]) else "средняя", source_key))
    return result


PERCENT_PATTERNS = {
    2: [(60, 40), (55, 45), (65, 35), (70, 30)],
    3: [(50, 30, 20), (45, 35, 20), (40, 35, 25), (55, 25, 20), (40, 40, 20), (60, 25, 15)],
    4: [(40, 30, 20, 10), (35, 30, 20, 15), (45, 25, 20, 10)],
}


def _candidate_pool(direction: str, inventory: Sequence[Dict[str, Any]]) -> Iterable[Tuple[float, Tuple[Tuple[str, int], ...]]]:
    relevant = [item for item in inventory if item["directionWeights"].get(direction, 0) >= .2]
    support = [item for item in inventory if any(_pair_harmony(item, core) >= .82 for core in relevant)]
    support_ids = {item["id"] for item in support}
    pool = [item for item in inventory if item["id"] in support_ids or item in relevant]
    seen = set()
    # Three components are enough for the generated library; curated source
    # adaptations may still use four. Avoiding exhaustive four-way permutations
    # keeps a complete deterministic rebuild comfortably fast on a phone-era Mac.
    for count in (2, 3):
        for combo in itertools.combinations(pool, count):
            if not any(item in relevant for item in combo):
                continue
            for percents in PERCENT_PATTERNS[count]:
                for assigned in set(itertools.permutations(percents)):
                    pairs = tuple(sorted(((item["id"], pct) for item, pct in zip(combo, assigned))))
                    if pairs in seen:
                        continue
                    seen.add(pairs)
                    if any(pct > item["maxShare"] for item, pct in zip(combo, assigned)):
                        continue
                    direction_score = sum(item["directionWeights"].get(direction, 0) * pct for item, pct in zip(combo, assigned)) / 100
                    if direction_score < .22:
                        continue
                    harmonies = [_pair_harmony(a, b) for a, b in itertools.combinations(combo, 2)]
                    harmony = sum(harmonies) / len(harmonies)
                    role_balance = 1 - (max(assigned) - min(assigned)) / 100
                    score = direction_score * .55 + harmony * .35 + role_balance * .10
                    component_pairs = tuple((item["id"], pct) for item, pct in zip(combo, assigned))
                    yield round(score, 4), component_pairs


def _signature(pairs: Sequence[Tuple[str, int]]) -> Tuple[Tuple[str, int], ...]:
    return tuple(sorted(pairs))


def build_recipes(inventory: Sequence[Dict[str, Any]], analogs: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_id = {item["id"]: item for item in inventory}
    recipes = _adapted_recipes(by_id, analogs)
    signatures = {_signature([(c["tobaccoId"], c["percent"]) for c in r["components"]]) for r in recipes}
    usage = Counter(c["tobaccoId"] for r in recipes for c in r["components"])
    coverage = Counter((r["generationDirections"][0], r["strengthLabel"]) for r in recipes)
    target_cells = [(direction, label) for direction in DIRECTION_LABELS for label in STRENGTH_TARGETS]
    target_cells.extend((direction, "Лёгкая") for direction in LIGHT_DIRECTIONS)
    title_index = defaultdict(int)

    candidates_by_cell: Dict[Tuple[str, str], List[Tuple[float, Tuple[Tuple[str, int], ...]]]] = defaultdict(list)
    for direction in DIRECTION_LABELS:
        for score, pairs in _candidate_pool(direction, inventory):
            components = [{"tobaccoId": tobacco_id, "percent": percent} for tobacco_id, percent in pairs]
            label = strength_label(_mix_strength(components, by_id))
            cell = (direction, label)
            if cell in target_cells:
                candidates_by_cell[cell].append((score, pairs))
        candidates_by_cell[(direction, "Лёгкая")].sort(key=lambda x: x[0], reverse=True)
        for label in STRENGTH_TARGETS:
            candidates_by_cell[(direction, label)].sort(key=lambda x: x[0], reverse=True)

    for cell in target_cells:
        direction, label = cell
        candidates = candidates_by_cell[cell]
        if len(candidates) < 8:
            if coverage[cell] == 0:
                continue
            raise ValueError(f"Only {len(candidates)} candidates for active cell {cell}")
        while coverage[cell] < 8:
            available = [(score, pairs) for score, pairs in candidates[:600] if _signature(pairs) not in signatures]
            if not available:
                raise ValueError(f"Cannot fill unique recipes for {cell}")
            score, pairs = max(
                available,
                key=lambda candidate: candidate[0] + sum(max(0, 8 - usage[tobacco_id]) for tobacco_id, _ in candidate[1]) * .018,
            )
            components = [{"tobaccoId": tobacco_id, "percent": percent} for tobacco_id, percent in pairs]
            idx = title_index[direction]
            title_index[direction] += 1
            name = _recipe_title(direction, idx, components, by_id)
            legacy_name = _legacy_recipe_title(direction, idx, components, by_id)
            recipe_id = f"authored-{direction}-{label.lower().replace('ё', 'е').replace(' ', '-')}-{idx + 1:02d}-{_slug(legacy_name)}"
            origin_type = "experimental" if direction in {"floral", "unusual"} and score < .75 else "authored"
            origin = {
                "type": origin_type,
                "originalFormula": [],
                "substitutions": [],
                "adaptationNote": "Самостоятельная композиция из имеющейся полки, проверенная правилами совместимости и ограничениями ярких компонентов.",
                "sourceTitle": "Авторская разработка",
            }
            confidence = "средняя" if origin_type == "experimental" else ("высокая" if score >= .82 else "средняя")
            recipe = _make_recipe(recipe_id, name, direction, pairs, by_id, origin, confidence)
            recipes.append(recipe)
            signatures.add(_signature(pairs))
            coverage[cell] += 1
            usage.update(tobacco_id for tobacco_id, _ in pairs)

    missing_usage = [item_id for item_id in by_id if usage[item_id] < 5]
    if missing_usage:
        raise ValueError(f"Ingredients underused: {missing_usage}")
    if len(recipes) < 180:
        raise ValueError(f"Only {len(recipes)} recipes generated")
    return sorted(recipes, key=lambda recipe: (recipe["directionLabel"], recipe["strengthLabel"], recipe["name"]))


def write_outputs(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    inventory = build_inventory()
    analogs = build_analogs(inventory)
    recipes = build_recipes(inventory, analogs)
    payloads = {
        "inventory.json": inventory,
        "analogs.json": analogs,
        "recipes.json": recipes,
    }
    for filename, payload in payloads.items():
        (output_dir / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = parser.parse_args()
    write_outputs(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
