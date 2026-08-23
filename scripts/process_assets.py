#!/usr/bin/env python3
"""Crop ImageGen atlases into standalone transparent WebP UI assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "research" / "generated-assets"
OUTPUT_DIR = ROOT / "src" / "assets" / "generated"

TOBACCO_IDS = [
    "sebero-honey-melon",
    "sebero-strawberry",
    "sebero-energetik",
    "sebero-watermelon-melon-cola",
    "jent-lemon-pie",
    "jent-tropez",
    "sapphire-italian-tiramisu",
    "sapphire-redberry",
    "xperience-multy-fruity",
    "severny-pink-flamingo",
    "severny-white-tea",
    "severny-chifir",
    "severny-raspberry-ruby",
    "trofimoffs-wild-strawberry",
    "dogma-sakura",
    "dogma-klubyana",
    "dogma-gerlinad",
    "dogma-black-currant",
    "dogma-izhevika",
    "dogma-krymskaya-lavanda",
    "banger-evergreen",
    "satyr-california-cola",
    "bonche-brownie",
    "bonche-cookie",
    "bonche-caramel",
    "kraken-medium-seco-peanut",
]

DIRECTION_SOURCES = {
    "dessert": "jent-lemon-pie",
    "fruit": "xperience-multy-fruity",
    "berry": "severny-pink-flamingo",
    "citrus": "jent-tropez",
    "drink": "satyr-california-cola",
    "unusual": "banger-evergreen",
}

STRENGTH_KEYS = ["any", "light", "medium-light", "medium", "strong"]


def _transparent_engraving(image: Image.Image) -> Image.Image:
    """Turn the generated neutral checkerboard into alpha while retaining ink."""
    rgb = image.convert("RGB")
    rgba = Image.new("RGBA", rgb.size)
    output = []
    for red, green, blue in rgb.get_flattened_data():
        maximum = max(red, green, blue)
        minimum = min(red, green, blue)
        chroma = maximum - minimum
        darkness = 255 - round((red + green + blue) / 3)
        alpha = max((darkness - 22) * 5, (chroma - 8) * 5)
        output.append((red, green, blue, max(0, min(255, alpha))))
    rgba.putdata(output)
    return rgba


def _normalized_icon(image: Image.Image, size: int = 256, inset: int = 18) -> Image.Image:
    transparent = _transparent_engraving(image)
    bbox = transparent.getbbox()
    if not bbox:
        raise ValueError("Generated asset crop is empty")
    subject = transparent.crop(bbox)
    subject.thumbnail((size - inset * 2, size - inset * 2), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    left = (size - subject.width) // 2
    top = (size - subject.height) // 2
    canvas.alpha_composite(subject, (left, top))
    return canvas


def _grid_cells(path: Path, count: int) -> Iterable[Image.Image]:
    image = Image.open(path).convert("RGB")
    for index in range(count):
        row, column = divmod(index, 3)
        left = round(column * image.width / 3)
        right = round((column + 1) * image.width / 3)
        top = round(row * image.height / 3)
        bottom = round((row + 1) * image.height / 3)
        yield image.crop((left, top, right, bottom))


def _write_webp(image: Image.Image, relative_path: Path) -> Path:
    target = ROOT / "src" / "assets" / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, "WEBP", lossless=True, method=6)
    return target


def _manifest_item(key: str, relative_path: Path, source: str) -> dict[str, object]:
    path = ROOT / "src" / "assets" / relative_path
    with Image.open(path) as image:
        width, height = image.size
    payload = path.read_bytes()
    return {
        "key": key,
        "file": relative_path.as_posix(),
        "width": width,
        "height": height,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "source": source,
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    tobacco_paths: dict[str, Path] = {}
    atlas_specs = [
        (SOURCE_DIR / "tobacco-atlas-01.png", TOBACCO_IDS[:9]),
        (SOURCE_DIR / "tobacco-atlas-02.png", TOBACCO_IDS[9:18]),
        (SOURCE_DIR / "tobacco-atlas-03.png", TOBACCO_IDS[18:]),
    ]
    for atlas_path, tobacco_ids in atlas_specs:
        for tobacco_id, crop in zip(tobacco_ids, _grid_cells(atlas_path, len(tobacco_ids))):
            relative = Path("generated") / "tobacco" / f"{tobacco_id}.webp"
            _write_webp(_normalized_icon(crop), relative)
            tobacco_paths[tobacco_id] = relative
            manifest.append(_manifest_item(f"tobacco:{tobacco_id}", relative, atlas_path.name))

    for direction, tobacco_id in DIRECTION_SOURCES.items():
        source = ROOT / "src" / "assets" / tobacco_paths[tobacco_id]
        relative = Path("generated") / "direction" / f"{direction}.webp"
        _write_webp(Image.open(source).convert("RGBA"), relative)
        manifest.append(_manifest_item(f"direction:{direction}", relative, f"derived:{tobacco_id}"))

    strength_atlas = Image.open(SOURCE_DIR / "strength-atlas.png").convert("RGB")
    for index, strength_key in enumerate(STRENGTH_KEYS):
        left = round(index * strength_atlas.width / 5)
        right = round((index + 1) * strength_atlas.width / 5)
        crop = strength_atlas.crop((left, 0, right, strength_atlas.height))
        relative = Path("generated") / "strength" / f"{strength_key}.webp"
        _write_webp(_normalized_icon(crop, inset=12), relative)
        manifest.append(_manifest_item(f"strength:{strength_key}", relative, "strength-atlas.png"))

    manifest_path = ROOT / "src" / "assets" / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(manifest)} assets to {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
