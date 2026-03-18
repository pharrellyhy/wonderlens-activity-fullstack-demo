import argparse
import time
from io import BytesIO
from pathlib import Path

import httpx
from generate_cat5_icons_openai import (
    ASSETS,
    OUT_DIR,
    PHOTO_ASSETS,
    TARGET_SIZE,
    build_prompt,
    build_prompt_photo,
    load_env_file,
)
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from PIL import Image

MAX_RETRIES = 5
BASE_DELAY = 15  # seconds between requests to avoid quota exhaustion
RETRY_DELAY = 30  # initial retry delay on 429, doubles each attempt

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "backend" / ".env"
MODEL = "gemini-2.5-flash-image"


def save_icon(image: Image.Image, out_path: Path) -> None:
    resized = image.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
    resized.save(out_path, format="PNG")


def get_vertex_client(env: dict[str, str]) -> genai.Client:
    project = env.get("GOOGLE_CLOUD_PROJECT", "")
    location = env.get("GOOGLE_CLOUD_LOCATION", "") or "global"
    if not project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is missing from backend/.env")
    return genai.Client(vertexai=True, project=project, location=location)


def get_api_key_client(env: dict[str, str]) -> genai.Client:
    api_key = env.get("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing from backend/.env")
    return genai.Client(api_key=api_key)


def extract_image(response) -> Image.Image:
    parts = getattr(response, "parts", None)
    if parts is None and getattr(response, "candidates", None):
        candidate = response.candidates[0]
        parts = getattr(getattr(candidate, "content", None), "parts", None)
    parts = parts or []
    for part in parts:
        if getattr(part, "inline_data", None):
            return Image.open(BytesIO(part.inline_data.data)).convert("RGBA")
    raise RuntimeError("Gemini returned no inline image data")


def generate_image(client: genai.Client, prompt: str) -> Image.Image:
    delay = RETRY_DELAY
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio="1:1"),
                ),
            )
            return extract_image(response)
        except (genai_errors.ClientError, genai_errors.APIError, httpx.ConnectError) as exc:
            is_retryable = (
                "RESOURCE_EXHAUSTED" in str(exc)
                or "429" in str(exc)
                or isinstance(exc, httpx.ConnectError)
            )
            if not is_retryable:
                raise
            if attempt == MAX_RETRIES - 1:
                raise
            print(f"  rate limited, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})...")
            time.sleep(delay)
            delay = min(delay * 2, 120)
    raise RuntimeError("unreachable")


def render_one(env: dict[str, str], filename: str, mode: str, overwrite: bool, style: str = "illustrated") -> None:
    asset_list = PHOTO_ASSETS if style == "photo" else ASSETS
    prompt_fn = build_prompt_photo if style == "photo" else build_prompt
    asset = next((a for a in asset_list if a.filename == filename), None)
    if asset is None:
        raise SystemExit(f"Unknown filename: {filename}")

    out_path = OUT_DIR / filename
    if out_path.exists() and not overwrite:
        print(f"skip {filename} (exists)")
        return

    prompt = prompt_fn(asset)

    if mode == "vertex":
        image = generate_image(get_vertex_client(env), prompt)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        save_icon(image, out_path)
        print(f"generated {filename} via vertex")
        return

    if mode == "api-key":
        image = generate_image(get_api_key_client(env), prompt)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        save_icon(image, out_path)
        print(f"generated {filename} via api-key")
        return

    try:
        image = generate_image(get_vertex_client(env), prompt)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        save_icon(image, out_path)
        print(f"generated {filename} via vertex")
        return
    except (RuntimeError, httpx.HTTPError, genai_errors.APIError) as exc:
        print(f"vertex failed for {filename}: {exc}")

    image = generate_image(get_api_key_client(env), prompt)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    save_icon(image, out_path)
    print(f"generated {filename} via api-key")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Cat 5 icons with gemini-2.5-flash-image.")
    parser.add_argument("--only", help="Single filename to generate, e.g. spotted_mushroom.png")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing PNGs")
    parser.add_argument("--mode", default="auto", choices=("auto", "vertex", "api-key"))
    parser.add_argument("--style", default="illustrated", choices=("illustrated", "photo"))
    args = parser.parse_args()

    if not ENV_PATH.exists():
        raise SystemExit(f"Missing env file: {ENV_PATH}")
    env = load_env_file(ENV_PATH)
    asset_list = PHOTO_ASSETS if args.style == "photo" else ASSETS
    filenames = [args.only] if args.only else [asset.filename for asset in asset_list]
    total = len(filenames)
    for i, filename in enumerate(filenames):
        render_one(env, filename, mode=args.mode, overwrite=args.overwrite, style=args.style)
        if i < total - 1 and not args.only:
            print(f"  ({i + 1}/{total}) waiting {BASE_DELAY}s before next request...")
            time.sleep(BASE_DELAY)


if __name__ == "__main__":
    main()
