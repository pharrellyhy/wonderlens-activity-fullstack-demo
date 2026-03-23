#!/usr/bin/env python3
"""Generate character entity icon PNGs via Gemini Imagen.

Produces kawaii-style illustrated icons matching the existing character icon
aesthetic. Can read entity metadata from game files to enrich the prompt.

Usage:
    uv run python scripts/generate_icon.py bicycle
    uv run python scripts/generate_icon.py bicycle --style-ref frontend/public/icons/dog.png
    uv run python scripts/generate_icon.py --all
    uv run python scripts/generate_icon.py --all --style-ref frontend/public/icons/dog.png
"""

import argparse
import re
import sys
import time
from pathlib import Path

import httpx
import yaml
from generate_cat5_icons_gemini import (
    BASE_DELAY,
    MAX_RETRIES,
    RETRY_DELAY,
    extract_image,
    generate_image,
    get_api_key_client,
    get_vertex_client,
    save_icon,
)
from generate_cat5_icons_openai import load_env_file
from google.genai import errors as genai_errors
from google.genai import types
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "backend" / ".env"
GAMES_DIR = ROOT / "backend" / "games"
OUT_DIR = ROOT / "frontend" / "public" / "icons"


# ---------------------------------------------------------------------------
# Entity description from game file
# ---------------------------------------------------------------------------


def _extract_frontmatter(md_file: Path) -> dict:
    """Read YAML frontmatter from a game markdown file."""
    text = md_file.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        raise ValueError(f"No YAML frontmatter found in {md_file}")
    data = yaml.safe_load(match.group(1))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML frontmatter in {md_file}")
    return data


def _iter_game_frontmatters() -> list[dict]:
    """Load frontmatter from non-prod game files."""
    frontmatters: list[dict] = []
    for md_file in sorted(GAMES_DIR.glob("*.md")):
        if md_file.name.endswith("_prod.md"):
            continue
        try:
            frontmatters.append(_extract_frontmatter(md_file))
        except (OSError, ValueError, yaml.YAMLError):
            continue
    return frontmatters


def _read_game_frontmatter(entity_name: str) -> dict | None:
    """Try to find and read frontmatter from the entity's game file."""
    for data in _iter_game_frontmatters():
        if data.get("entity_name") == entity_name:
            return data
    return None


def _build_description(entity_name: str, description_override: str | None = None) -> str:
    """Build an entity description for the icon prompt."""
    if description_override:
        return description_override

    # Try to enrich from game file frontmatter
    data = _read_game_frontmatter(entity_name)
    if data:
        display_label = data.get("display_label", entity_name.replace("_", " ").title())
        photo_features = data.get("photo_features", [])
        if photo_features:
            features_str = ", ".join(photo_features[:4])
            return f"A cute, friendly {display_label.lower()} facing forward with {features_str}"
        return f"A cute, friendly {display_label.lower()} facing forward"

    # Fallback
    label = entity_name.replace("_", " ")
    return f"A cute, friendly {label} facing forward"


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def _build_icon_prompt(description: str, style: str = "character") -> str:
    """Build the icon generation prompt.

    Args:
        description: What to draw.
        style: "character" for entity icons (white bg) or "collection" for
               collection item icons (outdoor scenic bg).
    """
    if style == "collection":
        return (
            f"Create a square illustrated icon for a children's outdoor collection game. "
            f"Main subject: {description}. "
            "Use a warm children's-book illustration style with gentle outlines, "
            "soft painterly shading, and natural earth-toned colors. "
            "Show exactly one main object centered and large in frame, with a simple soft "
            "outdoor background that matches where this item would naturally be found — "
            "vary the setting (park path, pond edge, forest floor, garden, sidewalk, sky view, etc.). "
            "Use different color palettes and compositions for each scene. "
            "The background must extend to ALL edges of the image — no black borders, "
            "no white borders, no empty margins, no rounded corner mask. "
            "Keep the silhouette very clear and easy to recognize at small UI icon size for ages 2-8. "
            "Do not add extra objects, characters, labels, borders, frames, or watermarks."
        )
    return (
        f"Create a square illustrated icon of: {description}. "
        "Use a warm children's-book kawaii illustration style with gentle outlines, "
        "soft painterly shading, and friendly natural colors. "
        "The background MUST be plain solid white (#FFFFFF). "
        "There must be NO ground plane, NO shadow underneath, NO gradient, "
        "NO patterns, NO colored background. Just the character on a clean white background. "
        "The character should be centered and large, filling most of the square. "
        "No text, no letters, no words, no watermarks, no frames, no borders."
    )


# ---------------------------------------------------------------------------
# Image generation with style reference
# ---------------------------------------------------------------------------


def _generate_with_style_ref(
    client,
    prompt: str,
    style_ref_path: Path | None,
) -> Image.Image:
    """Generate an icon, optionally using a style reference image."""
    if style_ref_path and style_ref_path.exists():
        ref_image = Image.open(style_ref_path).convert("RGBA")
        delay = RETRY_DELAY
        for attempt in range(MAX_RETRIES):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash-image",
                    contents=[
                        ref_image,
                        "Match this illustration style exactly. " + prompt,
                    ],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(aspect_ratio="1:1"),
                    ),
                )
                return extract_image(response)
            except (genai_errors.ClientError, genai_errors.APIError, httpx.ConnectError) as exc:
                is_retryable = (
                    "RESOURCE_EXHAUSTED" in str(exc) or "429" in str(exc) or isinstance(exc, httpx.ConnectError)
                )
                if not is_retryable or attempt == MAX_RETRIES - 1:
                    raise
                print(f"  rate limited, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})...")
                time.sleep(delay)
                delay = min(delay * 2, 120)
        raise RuntimeError("unreachable")
    else:
        return generate_image(client, prompt)


# ---------------------------------------------------------------------------
# Client creation
# ---------------------------------------------------------------------------


def _get_client(env: dict[str, str], mode: str):
    """Create a Gemini client based on mode."""
    if mode == "vertex":
        return get_vertex_client(env)
    if mode == "api-key":
        return get_api_key_client(env)
    try:
        return get_vertex_client(env)
    except RuntimeError:
        return get_api_key_client(env)


# ---------------------------------------------------------------------------
# Icon generation for a single entity
# ---------------------------------------------------------------------------


def generate_entity_icon(
    entity_name: str,
    client,
    description: str | None = None,
    style_ref: Path | None = None,
    output_path: Path | None = None,
    overwrite: bool = False,
    icon_style: str = "character",
) -> Path | None:
    """Generate an icon for a single entity.

    Args:
        icon_style: "character" for entity icons (white bg) or "collection"
                    for collection item icons (outdoor scenic bg).
    """
    if output_path is None:
        output_path = OUT_DIR / f"{entity_name}.png"

    if output_path.exists() and not overwrite:
        print(f"skip {entity_name} (exists, use --overwrite to replace)")
        return None

    desc = _build_description(entity_name, description)
    prompt = _build_icon_prompt(desc, style=icon_style)

    print(f"Generating icon for {entity_name}...")
    print(f"  description: {desc}")

    image = _generate_with_style_ref(client, prompt, style_ref)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_icon(image, output_path)
    print(f"  saved {output_path.name}")
    return output_path


# ---------------------------------------------------------------------------
# Find entities needing icons
# ---------------------------------------------------------------------------


def _find_entities_needing_icons() -> list[str]:
    """Find entities that have game files but no icon."""
    entities = []
    for data in _iter_game_frontmatters():
        entity_name = data.get("entity_name")
        if not entity_name:
            continue
        icon_path = OUT_DIR / f"{entity_name}.png"
        if not icon_path.exists():
            entities.append(entity_name)
    return entities


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate character entity icon PNGs via Gemini Imagen.",
    )
    parser.add_argument(
        "entity",
        nargs="?",
        default=None,
        help="Entity name (e.g., bicycle)",
    )
    parser.add_argument("--description", default=None, help="Custom description override")
    parser.add_argument("--style-ref", type=Path, default=None, help="Existing icon PNG for style reference")
    parser.add_argument("--output", type=Path, default=None, help="Custom output path")
    parser.add_argument("--mode", default="auto", choices=("auto", "vertex", "api-key"), help="Gemini client mode")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite if icon exists")
    parser.add_argument("--all", action="store_true", help="Generate icons for all entities missing icons")
    parser.add_argument(
        "--icon-style",
        default="character",
        choices=("character", "collection"),
        help="'character' = white bg entity icon, 'collection' = outdoor bg collection item icon",
    )
    args = parser.parse_args()

    if not args.all and args.entity is None:
        parser.error("Either provide an entity name or use --all")

    if not ENV_PATH.exists():
        print(f"Error: {ENV_PATH} not found", file=sys.stderr)
        sys.exit(1)

    env = load_env_file(ENV_PATH)
    client = _get_client(env, args.mode)

    if args.all:
        entities = _find_entities_needing_icons()
        if not entities:
            print("All entities already have icons (or no game files found)")
            return
        print(f"Found {len(entities)} entities needing icons: {', '.join(entities)}\n")
        for i, entity in enumerate(entities):
            generate_entity_icon(
                entity,
                client=client,
                style_ref=args.style_ref,
                overwrite=args.overwrite,
                icon_style=args.icon_style,
            )
            if i < len(entities) - 1:
                print(f"  ({i + 1}/{len(entities)}) waiting {BASE_DELAY}s before next request...")
                time.sleep(BASE_DELAY)
    else:
        generate_entity_icon(
            args.entity,
            client=client,
            description=args.description,
            style_ref=args.style_ref,
            output_path=args.output,
            overwrite=args.overwrite,
            icon_style=args.icon_style,
        )


if __name__ == "__main__":
    main()
