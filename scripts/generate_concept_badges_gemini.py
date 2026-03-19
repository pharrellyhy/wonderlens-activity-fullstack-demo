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
OUT_DIR = ROOT / "frontend" / "public" / "badges"


@dataclass(frozen=True)
class ConceptBadge:
    concept: str
    filename: str
    description: str


BADGES: tuple[ConceptBadge, ...] = (
    ConceptBadge(
        "Perspective",
        "perspective.png",
        "Binoculars on a hilltop looking at a landscape",
    ),
    ConceptBadge(
        "Reflection",
        "reflection.png",
        "Calm pond reflecting trees and sky",
    ),
    ConceptBadge(
        "Change",
        "change.png",
        "Caterpillar and butterfly together on a branch",
    ),
    ConceptBadge(
        "Causation",
        "causation.png",
        "Row of falling dominoes",
    ),
    ConceptBadge(
        "Form",
        "form.png",
        "Magnifying glass revealing leaf patterns",
    ),
    ConceptBadge(
        "Connection",
        "connection.png",
        "Two hands holding a woven friendship bracelet",
    ),
    ConceptBadge(
        "Function",
        "function.png",
        "Key fitting into a colorful lock",
    ),
    ConceptBadge(
        "Responsibility",
        "responsibility.png",
        "Child's hands cupping a plant seedling",
    ),
)


def build_prompt(badge: ConceptBadge) -> str:
    return (
        f'Create a square illustrated badge icon for a children\'s learning concept called "{badge.concept}". '
        f"Main subject: {badge.description} "
        "Use a warm children's-book illustration style with gentle outlines, soft painterly shading, and natural earth-toned colors. "
        "The image should feel like a badge or emblem — the subject should be centered, large, and framed within a soft circular or shield-shaped border with a warm golden-tan edge. "
        "Show exactly one clear visual metaphor, no text, no letters, no words. "
        "The background must extend to ALL edges of the image — no black borders, no white borders, no empty margins. "
        "Keep the silhouette very clear and easy to recognize at small size for ages 2-8. "
        "Do not add extra objects, characters, labels, text, borders, frames, or watermarks."
    )


def render_one(env: dict[str, str], badge: ConceptBadge, mode: str, overwrite: bool) -> None:
    out_path = OUT_DIR / badge.filename
    if out_path.exists() and not overwrite:
        print(f"skip {badge.filename} (exists)")
        return

    prompt = build_prompt(badge)

    if mode == "vertex":
        image = generate_image(get_vertex_client(env), prompt)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        save_icon(image, out_path)
        print(f"generated {badge.filename} via vertex")
        return

    if mode == "api-key":
        image = generate_image(get_api_key_client(env), prompt)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        save_icon(image, out_path)
        print(f"generated {badge.filename} via api-key")
        return

    # auto mode: try vertex first, fall back to api-key
    try:
        image = generate_image(get_vertex_client(env), prompt)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        save_icon(image, out_path)
        print(f"generated {badge.filename} via vertex")
        return
    except Exception as exc:
        print(f"vertex failed for {badge.filename}: {exc}")

    image = generate_image(get_api_key_client(env), prompt)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    save_icon(image, out_path)
    print(f"generated {badge.filename} via api-key")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate IB concept badge images with gemini-2.5-flash-image.")
    parser.add_argument("--only", help="Single filename to generate, e.g. perspective.png")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing PNGs")
    parser.add_argument("--mode", default="auto", choices=("auto", "vertex", "api-key"))
    args = parser.parse_args()

    if not ENV_PATH.exists():
        raise SystemExit(f"Missing env file: {ENV_PATH}")
    env = load_env_file(ENV_PATH)

    if args.only:
        badge = next((b for b in BADGES if b.filename == args.only), None)
        if badge is None:
            raise SystemExit(f"Unknown filename: {args.only}")
        render_one(env, badge, mode=args.mode, overwrite=args.overwrite)
        return

    total = len(BADGES)
    for i, badge in enumerate(BADGES):
        render_one(env, badge, mode=args.mode, overwrite=args.overwrite)
        if i < total - 1:
            print(f"  ({i + 1}/{total}) waiting {BASE_DELAY}s before next request...")
            time.sleep(BASE_DELAY)


if __name__ == "__main__":
    main()
