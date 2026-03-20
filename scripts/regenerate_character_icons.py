"""Regenerate the 5 character icons with transparent backgrounds using Gemini."""

import argparse
import time
from dataclasses import dataclass
from pathlib import Path

from generate_cat5_icons_gemini import (
    BASE_DELAY,
    generate_image,
    get_api_key_client,
    get_vertex_client,
    save_icon,
)
from generate_cat5_icons_openai import load_env_file

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "backend" / ".env"
OUT_DIR = ROOT / "frontend" / "public" / "icons"


@dataclass(frozen=True)
class CharacterIcon:
    entity: str
    filename: str
    description: str


ICONS: tuple[CharacterIcon, ...] = (
    CharacterIcon(
        "dog",
        "dog.png",
        "A cute, happy puppy sitting and facing forward with floppy brown ears, a light tan body, and a cheerful smile",
    ),
    CharacterIcon(
        "cat",
        "cat.png",
        "A cute, happy orange tabby kitten sitting and facing forward with perky ears, striped fur, and a cheerful smile",
    ),
    CharacterIcon(
        "dinosaur",
        "dinosaur.png",
        "A cute, happy green baby dinosaur standing and facing forward with small spikes, stubby arms, rosy cheeks, and a cheerful smile",
    ),
    CharacterIcon(
        "ladybug",
        "ladybug.png",
        "A cute, happy ladybug facing forward with a shiny red shell with black dots, small legs, big expressive eyes, and rosy cheeks",
    ),
    CharacterIcon(
        "dandelion",
        "dandelion.png",
        "A cute dandelion flower with a fluffy white seed head, green stem with leaves, and a few seeds floating away in the breeze",
    ),
)


def build_prompt(icon: CharacterIcon) -> str:
    return (
        f"Create a square illustrated icon of: {icon.description}. "
        "Use a warm children's-book kawaii illustration style with gentle outlines, "
        "soft painterly shading, and friendly natural colors. "
        "CRITICAL: The background MUST be completely transparent (PNG alpha channel). "
        "There must be NO background color, NO ground plane, NO shadow underneath, "
        "NO colored rectangle behind the character. Just the character floating on "
        "a fully transparent background. "
        "The character should be centered and large, filling most of the square. "
        "No text, no letters, no words, no watermarks, no frames, no borders."
    )


def render_one(env: dict[str, str], icon: CharacterIcon, mode: str, overwrite: bool) -> None:
    out_path = OUT_DIR / icon.filename
    if out_path.exists() and not overwrite:
        print(f"skip {icon.filename} (exists)")
        return

    prompt = build_prompt(icon)

    if mode == "vertex":
        image = generate_image(get_vertex_client(env), prompt)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        save_icon(image, out_path)
        print(f"generated {icon.filename} via vertex")
        return

    if mode == "api-key":
        image = generate_image(get_api_key_client(env), prompt)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        save_icon(image, out_path)
        print(f"generated {icon.filename} via api-key")
        return

    # auto: try vertex first, fall back to api-key
    try:
        image = generate_image(get_vertex_client(env), prompt)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        save_icon(image, out_path)
        print(f"generated {icon.filename} via vertex")
        return
    except Exception as exc:
        print(f"vertex failed for {icon.filename}: {exc}")

    image = generate_image(get_api_key_client(env), prompt)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    save_icon(image, out_path)
    print(f"generated {icon.filename} via api-key")


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate character icons with transparent backgrounds.")
    parser.add_argument("--only", help="Single filename to generate, e.g. dog.png")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing PNGs")
    parser.add_argument("--mode", default="auto", choices=("auto", "vertex", "api-key"))
    args = parser.parse_args()

    if not ENV_PATH.exists():
        raise SystemExit(f"Missing env file: {ENV_PATH}")
    env = load_env_file(ENV_PATH)

    if args.only:
        icon = next((i for i in ICONS if i.filename == args.only), None)
        if icon is None:
            raise SystemExit(f"Unknown filename: {args.only}")
        render_one(env, icon, mode=args.mode, overwrite=args.overwrite)
        return

    total = len(ICONS)
    for i, icon in enumerate(ICONS):
        render_one(env, icon, mode=args.mode, overwrite=args.overwrite)
        if i < total - 1:
            print(f"  ({i + 1}/{total}) waiting {BASE_DELAY}s before next request...")
            time.sleep(BASE_DELAY)


if __name__ == "__main__":
    main()
