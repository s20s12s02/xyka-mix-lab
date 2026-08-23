#!/usr/bin/env python3
"""Build one autonomous HTML file with CSS, code, fonts and data inlined."""

from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path


CORE_EXPORTS = [
    "filterRecipes",
    "findNearestByStrength",
    "normalizeState",
    "migrateLegacyPantryState",
    "selectRandomRecipe",
    "searchRecipes",
    "availableStrengths",
    "compositionSegments",
    "sectorGeometry",
    "layerGeometry",
    "STRENGTH_ORDER",
]
VERSIONED_FILENAME = "xyka_mix_lab_2026-08-22.html"


def _json_for_script(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</script", "<\\/script")


def _asset_data(project_root: Path) -> str:
    asset_root = project_root / "src" / "assets"
    manifest = json.loads((asset_root / "manifest.json").read_text(encoding="utf-8"))
    payload = {}
    for item in manifest:
        encoded = base64.b64encode((asset_root / item["file"]).read_bytes()).decode("ascii")
        payload[item["key"]] = f"data:image/webp;base64,{encoded}"
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</script", "<\\/script")


def _browser_core(source: str) -> str:
    transformed = re.sub(r"\bexport\s+function\s+", "function ", source)
    transformed = re.sub(r"\nexport\s*\{[^}]+\};?\s*", "\n", transformed)
    transformed += "\nwindow.XykaCore = {" + ",".join(CORE_EXPORTS) + "};\n"
    return transformed


def _font_face(font_path: Path) -> str:
    encoded = base64.b64encode(font_path.read_bytes()).decode("ascii")
    return (
        '@font-face{font-family:"Oswald Local";font-style:normal;font-weight:200 700;'
        'font-display:swap;src:url("data:font/ttf;base64,' + encoded + '") format("truetype");}'
    )


def build_html(project_root: Path, output_path: Path) -> None:
    template = (project_root / "src" / "index.html").read_text(encoding="utf-8")
    styles = (project_root / "src" / "styles.css").read_text(encoding="utf-8")
    styles = styles.replace("/*__FONT_FACE__*/", _font_face(project_root / "src" / "assets" / "oswald-variable.ttf"))
    replacements = {
        "/*__STYLES__*/": styles,
        "/*__INVENTORY__*/": _json_for_script(project_root / "data" / "inventory.json"),
        "/*__ANALOGS__*/": _json_for_script(project_root / "data" / "analogs.json"),
        "/*__RECIPES__*/": _json_for_script(project_root / "data" / "recipes.json"),
        "/*__ASSETS__*/": _asset_data(project_root),
        "/*__CORE__*/": _browser_core((project_root / "src" / "core.mjs").read_text(encoding="utf-8")),
        "/*__APP__*/": (project_root / "src" / "app.js").read_text(encoding="utf-8"),
    }
    html = template
    for marker, content in replacements.items():
        html = html.replace(marker, content)
    unresolved = re.findall(r"/\*__[A-Z_]+__\*/", html)
    if unresolved:
        raise ValueError(f"Unresolved build markers: {unresolved}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def build_pages(project_root: Path, output_root: Path | None = None) -> tuple[Path, Path]:
    """Build the versioned download and the root GitHub Pages entrypoint."""
    target_root = output_root or project_root
    versioned = target_root / "dist" / VERSIONED_FILENAME
    entrypoint = target_root / "index.html"
    build_html(project_root, versioned)
    entrypoint.write_bytes(versioned.read_bytes())
    return versioned, entrypoint


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output:
        build_html(root, args.output)
        print(args.output)
    else:
        versioned, entrypoint = build_pages(root)
        print(versioned)
        print(entrypoint)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
