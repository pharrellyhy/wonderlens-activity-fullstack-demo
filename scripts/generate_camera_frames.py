"""Generate toy camera frame designs using Gemini 2.5 Flash Image.

Produces several cartoon and realistic camera frame variants for the
WonderLens device panel. Output goes to frontend/public/cameras/.
"""

import time
from io import BytesIO
from pathlib import Path

import httpx
from generate_cat5_icons_openai import load_env_file
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / "backend" / ".env"
OUT_DIR = ROOT / "frontend" / "public" / "cameras"
MODEL = "gemini-2.5-flash-image"

MAX_RETRIES = 5
BASE_DELAY = 15
RETRY_DELAY = 30

BACK_SCREEN_NOTE = (
    "The camera is viewed from the BACK (the photographer's side), showing the large rear LCD screen. "
    "The screen takes up at least 70% of the camera back and is a clean flat pure white rectangle with slightly rounded corners — "
    "this is where app content will be composited, so it MUST be completely white and empty. "
    "Above the screen is a thin top bar with a small 'WonderLens' text label. "
    "No lens visible — the lens is on the other side. Only the back of the camera is shown. "
)

CAMERA_PROMPTS: list[dict[str, str]] = [
    # --- Cartoon / illustrated styles ---
    {
        "filename": "camera_cartoon_green.png",
        "prompt": (
            "A cute children's toy camera viewed from the BACK, showing the rear LCD screen side. "
            "Forest green body with warm yellow accents and a yellow shutter button on top. "
            "Cartoon illustration style with soft rounded edges, chunky friendly toy shape. "
            + BACK_SCREEN_NOTE
            + "Solid white background, no shadows, no other objects."
        ),
    },
    {
        "filename": "camera_cartoon_teal.png",
        "prompt": (
            "A cute toy camera for kids viewed from the BACK, showing the large rear screen. "
            "Teal blue-green body with coral/orange accents and buttons on top. "
            "Cartoon illustration style — soft, rounded, chunky toy camera shape. "
            + BACK_SCREEN_NOTE
            + "Playful, friendly design for ages 3-7. Solid white background."
        ),
    },
    {
        "filename": "camera_cartoon_wooden.png",
        "prompt": (
            "A cute wooden toy camera viewed from the BACK, showing the rear screen side. "
            "Warm light wood grain body with colorful painted accents — red button on top, green trim around the screen. "
            "Children's illustration style — handcrafted Montessori toy aesthetic. "
            + BACK_SCREEN_NOTE
            + "Solid white background, no shadows."
        ),
    },
    {
        "filename": "camera_cartoon_pastel.png",
        "prompt": (
            "A soft pastel-colored toy camera viewed from the BACK, showing the rear screen. "
            "Light pink body with lavender and mint green accents. Flower-shaped button on top. "
            "Kawaii cute style — very rounded, bubbly shapes. " + BACK_SCREEN_NOTE + "Solid white background."
        ),
    },
    # --- Realistic / 3D rendered styles ---
    {
        "filename": "camera_realistic_green.png",
        "prompt": (
            "A realistic 3D render of a children's toy camera viewed from the BACK, showing the rear LCD screen. "
            "Glossy forest green plastic body with a matte yellow shutter button on top. "
            "Clean product photography style. "
            + BACK_SCREEN_NOTE
            + "Pure white background, studio lighting, soft shadows."
        ),
    },
    {
        "filename": "camera_realistic_retro.png",
        "prompt": (
            "A realistic 3D render of a retro-styled children's toy camera viewed from the BACK, showing the rear screen. "
            "Two-tone body: cream/ivory top and dark teal bottom, with a brown leatherette grip strip on the right edge. "
            "Chrome accents. Red shutter button on top. "
            + BACK_SCREEN_NOTE
            + "Pure white background, product photography lighting."
        ),
    },
    {
        "filename": "camera_realistic_orange.png",
        "prompt": (
            "A realistic 3D render of a rugged kids' outdoor camera viewed from the BACK, showing the rear LCD screen. "
            "Bright orange waterproof-looking body with rubber grip edges in dark grey. Chunky buttons on top. "
            + BACK_SCREEN_NOTE
            + "Pure white background, product photography style."
        ),
    },
    {
        "filename": "camera_realistic_mint.png",
        "prompt": (
            "A realistic 3D render of a sleek modern children's toy camera viewed from the BACK, showing the rear screen. "
            "Soft mint green matte body with white accents and a silver shutter button on top. "
            "Minimalist clean design — like a simplified Fujifilm Instax for toddlers. "
            + BACK_SCREEN_NOTE
            + "Pure white background, studio lighting."
        ),
    },
]


def get_vertex_client(env: dict[str, str]) -> genai.Client:
    project = env.get("GOOGLE_CLOUD_PROJECT", "")
    location = env.get("GOOGLE_CLOUD_LOCATION", "") or "global"
    if not project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT is missing from backend/.env")
    return genai.Client(vertexai=True, project=project, location=location)


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
            is_retryable = "RESOURCE_EXHAUSTED" in str(exc) or "429" in str(exc) or isinstance(exc, httpx.ConnectError)
            if not is_retryable:
                raise
            if attempt == MAX_RETRIES - 1:
                raise
            print(f"  rate limited, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})...")
            time.sleep(delay)
            delay = min(delay * 2, 120)
    raise RuntimeError("unreachable")


def main() -> None:
    if not ENV_PATH.exists():
        raise SystemExit(f"Missing env file: {ENV_PATH}")
    env = load_env_file(ENV_PATH)
    client = get_vertex_client(env)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total = len(CAMERA_PROMPTS)
    for i, item in enumerate(CAMERA_PROMPTS):
        filename = item["filename"]
        out_path = OUT_DIR / filename
        if out_path.exists():
            print(f"skip {filename} (exists)")
        else:
            print(f"generating {filename} ({i + 1}/{total})...")
            image = generate_image(client, item["prompt"])
            image.save(out_path, format="PNG")
            print(f"  saved {filename} ({out_path.stat().st_size // 1024} KB)")

        if i < total - 1:
            print(f"  waiting {BASE_DELAY}s...")
            time.sleep(BASE_DELAY)

    print(f"\nDone! {total} camera frames in {OUT_DIR}")


if __name__ == "__main__":
    main()
