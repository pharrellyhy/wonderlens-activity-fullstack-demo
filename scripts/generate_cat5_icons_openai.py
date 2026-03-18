import argparse
import base64
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import httpx
from openai import BadRequestError, OpenAI
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "backend" / ".env"
OUT_DIR = ROOT / "frontend" / "public" / "icons"
TARGET_SIZE = (256, 256)
MODEL = "gpt-image-1.5"


@dataclass(frozen=True)
class AssetPrompt:
    filename: str
    description: str
    game_theme: str


ASSETS: tuple[AssetPrompt, ...] = (
    AssetPrompt(
        "spotted_mushroom.png",
        "A cute round mushroom with a creamy-white cap dotted with warm brown spots, sitting on soft green moss.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "dotted_pebble.png",
        "A friendly round pebble with charming circular dot patterns in earth tones like brown, grey, and cream.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "speckled_leaf.png",
        "A bright green leaf with playful polka-dot-like speckles in gold and russet, with visible veins.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "circle_flower.png",
        "A cheerful round daisy-like flower with white petals radiating from a bright yellow circular center.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "straight_stick.png",
        "A simple brown stick with straight wood grain lines and no dots or circles.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "plain_bark.png",
        "A section of tree trunk bark with vertical groove patterns in brown tones, showing lines and ridges instead of dots.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "long_grass.png",
        "Wispy green grass blades with flowing linear strokes and no dots or circles anywhere.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "smooth_stone.png",
        "A perfectly smooth, plain grey-blue stone with no decoration, spots, or patterns.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "pine_needle.png",
        "A neat bundle of dark green pine needles splaying outward like a tiny broom, clearly spiky and line-shaped.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "plain_leaf.png",
        "A simple solid green leaf with clean edges and visible veins running in straight lines, with no speckles or spots.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "forked_twig.png",
        "A cute Y-shaped twig in warm brown, emphasizing the angular branching shape with no dots or circles.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "acorn_cap.png",
        "A small acorn cap in warm tan-brown with a bumpy cross-hatch texture that looks woven or scaly, not dotted.",
        "Polka-Dot Patrol",
    ),
    AssetPrompt(
        "fuzzy_moss.png",
        "A pillowy mound of bright green moss with a velvety, touchable texture and soft edges.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "fluffy_seed.png",
        "A whimsical floating seed with delicate white fluffy filaments spreading like a tiny parachute.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "soft_petal.png",
        "A plush rounded flower petal in soft pink or lavender with a satiny, touchable quality.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "woolly_caterpillar.png",
        "A cute woolly caterpillar with fluffy orange and brown fur and a friendly child-safe expression.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "hard_rock.png",
        "A chunky angular rock in grey-brown tones with sharp edges, clearly hard and solid.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "spiky_pinecone.png",
        "A detailed pinecone with pointy spiky scales in warm brown, clearly sharp rather than soft.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "rough_bark.png",
        "A section of rough cracked tree bark in dark brown with jagged ridges and a hard scratchy feel.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "sharp_thorn.png",
        "A branch with prominent sharp thorns pointing outward, clearly spiky and the opposite of soft.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "dry_leaf.png",
        "A curled crispy autumn leaf in warm orange-brown with visible cracks and stiff edges.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "smooth_pebble.png",
        "A perfectly round smooth pebble in cool grey-blue tones with a hard shiny surface.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "stiff_branch.png",
        "A sturdy thick brown branch with rough bark and a snapped end, rigid and woody.",
        "Fluffy Expedition Dandelion",
    ),
    AssetPrompt(
        "brittle_shell.png",
        "A small spiral snail shell or cracked eggshell fragment in pale cream, thin, hard, and brittle.",
        "Fluffy Expedition Dandelion",
    ),
)


def load_env_file(path: Path) -> dict[str, str]:
    def parse_value(raw_value: str) -> str:
        value = raw_value.strip()
        if not value:
            return ""
        if value[0] in {'"', "'"}:
            quote = value[0]
            end = value.find(quote, 1)
            if end != -1:
                return value[1:end]
        return value.split(" #", 1)[0].strip().strip('"').strip("'")

    values: dict[str, str] = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = parse_value(value)
    return values


def build_prompt(asset: AssetPrompt) -> str:
    return (
        f"Create a square illustrated icon for a children's outdoor collection game named {asset.game_theme}. "
        f"Main subject: {asset.description} "
        "Use a warm children's-book illustration style with gentle outlines, soft painterly shading, and natural earth-toned colors. "
        "Show exactly one main object centered and large in frame, with a simple soft outdoor background and no text. "
        "Keep the silhouette very clear and easy to recognize at small UI icon size for ages 2-8. "
        "Do not add extra objects, characters, labels, borders, frames, or watermarks."
    )


def decode_png(b64_json: str) -> Image.Image:
    return Image.open(BytesIO(base64.b64decode(b64_json))).convert("RGBA")


def load_from_url(url: str) -> Image.Image:
    response = httpx.get(url, timeout=180.0)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGBA")


def save_icon(image: Image.Image, out_path: Path) -> None:
    resized = image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
    resized.save(out_path, format="PNG")


def get_client(base_url_override: str | None = None) -> OpenAI:
    if not ENV_PATH.exists():
        raise SystemExit(f"Missing env file: {ENV_PATH}")
    env = load_env_file(ENV_PATH)
    api_key = env.get("OPENAI_API_KEY", "")
    base_url = base_url_override or env.get("OPENAI_BASE_URL", "")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is missing from backend/.env")
    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    return OpenAI(**client_kwargs, timeout=180.0, max_retries=0)


def render_one(client: OpenAI, asset: AssetPrompt, size: str, quality: str, overwrite: bool) -> None:
    out_path = OUT_DIR / asset.filename
    if out_path.exists() and not overwrite:
        print(f"skip {asset.filename} (exists)")
        return

    prompt = build_prompt(asset)
    started = time.perf_counter()
    request_kwargs = {
        "model": MODEL,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "background": "opaque",
        "output_format": "png",
        "response_format": "b64_json",
    }
    try:
        response = client.images.generate(**request_kwargs)
    except BadRequestError as exc:
        message = str(exc)
        if "Unknown parameter: 'response_format'" not in message:
            raise
        request_kwargs.pop("response_format")
        response = client.images.generate(**request_kwargs)
    if not response.data:
        raise RuntimeError(
            f"No image bytes returned for {asset.filename}. "
            "The configured OpenAI-compatible base URL appears to advertise the model but not implement image generation."
        )
    item = response.data[0]
    if getattr(item, "b64_json", None):
        image = decode_png(item.b64_json)
    elif getattr(item, "url", None):
        image = load_from_url(item.url)
    else:
        raise RuntimeError(
            f"No image bytes returned for {asset.filename}. "
            "The configured OpenAI-compatible base URL appears to advertise the model but not implement image generation."
        )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    save_icon(image, out_path)
    elapsed = time.perf_counter() - started
    print(f"generated {asset.filename} in {elapsed:.1f}s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Cat 5 icons with gpt-image-1.5.")
    parser.add_argument("--only", help="Single filename to generate, e.g. spotted_mushroom.png")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing PNGs")
    parser.add_argument("--base-url", help="Optional override for OPENAI_BASE_URL without editing backend/.env")
    parser.add_argument("--size", default="1024x1024", choices=("256x256", "512x512", "1024x1024"))
    parser.add_argument("--quality", default="medium", choices=("low", "medium", "high"))
    args = parser.parse_args()

    client = get_client(args.base_url)
    assets = ASSETS
    if args.only:
        assets = tuple(asset for asset in ASSETS if asset.filename == args.only)
        if not assets:
            raise SystemExit(f"Unknown filename: {args.only}")

    for asset in assets:
        render_one(client, asset, size=args.size, quality=args.quality, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
