"""Image generation using Imagen 3 via Vertex AI / Google GenAI SDK.

Follows the same dual-auth pattern as tts.py:
- If google_cloud_project set → Vertex AI client
- Otherwise → API key client (gemini_api_key)
"""

import asyncio
import base64
import time
from functools import lru_cache
from pathlib import Path

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

try:
    from .config import get_settings
    from .logger import setup_logger
except ImportError:
    from config import get_settings
    from logger import setup_logger

logger = setup_logger(__name__)

_STYLE_PREFIX = (
    "Soft watercolor children's storybook illustration. "
    "Gentle pastel tones, warm lighting, no text or words in the image."
)

_MAX_RETRIES = 2
_RETRY_DELAY = 3.0
_BATCH_SIZE = 2


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    """Get or create the image generation client (same auth pattern as TTS)."""
    settings = get_settings()
    if settings.google_cloud_project:
        client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location="global",
        )
    else:
        client = genai.Client(api_key=settings.gemini_api_key)
    logger.info("Initialized image generation client")
    return client


def _extract_image_bytes(response: types.GenerateContentResponse) -> bytes:
    """Extract PNG image bytes from a Gemini/Imagen response."""
    parts = getattr(response, "parts", None)
    if parts is None and response.candidates:
        candidate = response.candidates[0]
        parts = getattr(getattr(candidate, "content", None), "parts", None)
    for part in parts or []:
        if getattr(part, "inline_data", None):
            return part.inline_data.data
    raise RuntimeError("Imagen returned no inline image data")


async def generate_image(prompt: str, aspect_ratio: str = "16:9") -> bytes | None:
    """Generate a single image from a text prompt.

    Args:
        prompt: Scene description (style prefix is added automatically).
        aspect_ratio: Image aspect ratio (default 16:9 for story scenes).

    Returns:
        PNG image bytes, or None if generation fails.
    """
    settings = get_settings()
    if not settings.imagen_enabled:
        logger.info("Imagen disabled, skipping image generation")
        return None

    full_prompt = f"{_STYLE_PREFIX} {prompt}"
    client = _get_client()

    for attempt in range(_MAX_RETRIES):
        try:
            start = time.perf_counter()
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.imagen_model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
                ),
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
            image_bytes = _extract_image_bytes(response)
            logger.info("Imagen generated image (%d bytes, %dms)", len(image_bytes), latency_ms)
            return image_bytes

        except (genai_errors.ClientError, genai_errors.APIError) as exc:
            is_retryable = "RESOURCE_EXHAUSTED" in str(exc) or "429" in str(exc)
            if not is_retryable or attempt == _MAX_RETRIES - 1:
                logger.error("Imagen generation failed (attempt %d): %s", attempt + 1, exc)
                return None
            logger.warning("Imagen rate-limited, retrying in %.1fs", _RETRY_DELAY)
            await asyncio.sleep(_RETRY_DELAY)

        except Exception as exc:
            logger.error("Imagen unexpected error: %s", exc)
            return None


def image_to_base64(image_bytes: bytes) -> str:
    """Convert raw image bytes to a base64-encoded data URL string."""
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"


_IMAGES_DIR = Path(__file__).parent / "data" / "images"


def _save_image(image_bytes: bytes, session_id: str, filename: str) -> Path:
    """Save image bytes to disk and return the file path."""
    session_dir = _IMAGES_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / filename
    path.write_bytes(image_bytes)
    logger.info("Saved image: %s (%d bytes)", path, len(image_bytes))
    return path


def _result_to_data_url(result: bytes | BaseException | None, label: str, session_id: str, filename: str) -> str | None:
    """Convert a gather result to a base64 data URL, saving to disk. Logs failures."""
    if isinstance(result, bytes):
        _save_image(result, session_id, filename)
        return image_to_base64(result)
    if isinstance(result, BaseException):
        logger.error("%s image generation failed: %s", label, result)
    return None


async def generate_scene_images(
    scene_descriptions: list[str],
    achievement_description: str,
    session_id: str = "",
) -> tuple[list[str | None], str | None]:
    """Generate scene images + achievement image with staggered concurrency.

    Generates in two batches (2 + 2) with a short delay between batches to
    avoid Imagen rate-limit (429) errors from firing all 4 requests at once.
    Saves each generated image to backend/data/images/{session_id}/.

    Args:
        scene_descriptions: List of scene image descriptions (typically 3).
        achievement_description: Description for the achievement summary image.
        session_id: Session identifier for organizing saved images on disk.

    Returns:
        Tuple of (scene_image_data_urls, achievement_image_data_url).
        Each entry is a base64 data URL string or None if generation failed.
    """
    all_prompts = list(scene_descriptions) + [achievement_description]
    all_ratios = ["16:9"] * len(scene_descriptions) + ["1:1"]

    # Batch 1
    batch1 = [generate_image(p, r) for p, r in zip(all_prompts[:_BATCH_SIZE], all_ratios[:_BATCH_SIZE])]
    results1 = await asyncio.gather(*batch1, return_exceptions=True)

    # Short delay to avoid rate-limit
    await asyncio.sleep(1.0)

    # Batch 2: remaining images
    batch2 = [generate_image(p, r) for p, r in zip(all_prompts[_BATCH_SIZE:], all_ratios[_BATCH_SIZE:])]
    results2 = await asyncio.gather(*batch2, return_exceptions=True)

    results = list(results1) + list(results2)

    sid = session_id or "unknown"
    scene_images = [
        _result_to_data_url(r, f"Scene {i + 1}", sid, f"scene_{i + 1}.png") for i, r in enumerate(results[:-1])
    ]
    achievement_image = _result_to_data_url(results[-1], "Achievement", sid, "achievement.png")

    return scene_images, achievement_image
