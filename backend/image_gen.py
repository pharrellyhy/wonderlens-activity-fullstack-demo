"""Image generation using Imagen 3 via Vertex AI / Google GenAI SDK.

Follows the same dual-auth pattern as tts.py:
- If google_cloud_project set → Vertex AI client
- Otherwise → API key client (gemini_api_key)
"""

import asyncio
import base64
import time
from functools import lru_cache

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


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    """Get or create the Imagen client (same auth pattern as TTS)."""
    settings = get_settings()
    if settings.google_cloud_project:
        client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )
    else:
        client = genai.Client(api_key=settings.gemini_api_key)
    logger.info("Initialized Imagen client")
    return client


def _extract_image_bytes(response: types.GenerateContentResponse) -> bytes:
    """Extract PNG image bytes from a Gemini/Imagen response."""
    parts = getattr(response, "parts", None)
    if parts is None and getattr(response, "candidates", None):
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

    return None


def image_to_base64(image_bytes: bytes) -> str:
    """Convert raw image bytes to a base64-encoded data URL string."""
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"


async def generate_scene_images(
    scene_descriptions: list[str],
    achievement_description: str,
) -> tuple[list[str | None], str | None]:
    """Generate all scene images + achievement image in parallel.

    Args:
        scene_descriptions: List of scene image descriptions (typically 3).
        achievement_description: Description for the achievement summary image.

    Returns:
        Tuple of (scene_image_data_urls, achievement_image_data_url).
        Each entry is a base64 data URL string or None if generation failed.
    """
    tasks = [generate_image(desc) for desc in scene_descriptions]
    tasks.append(generate_image(achievement_description, aspect_ratio="1:1"))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    scene_images: list[str | None] = []
    for i, result in enumerate(results[:-1]):
        if isinstance(result, bytes):
            scene_images.append(image_to_base64(result))
        else:
            if isinstance(result, Exception):
                logger.error("Scene %d image generation failed: %s", i + 1, result)
            scene_images.append(None)

    achievement_result = results[-1]
    achievement_image: str | None = None
    if isinstance(achievement_result, bytes):
        achievement_image = image_to_base64(achievement_result)
    elif isinstance(achievement_result, Exception):
        logger.error("Achievement image generation failed: %s", achievement_result)

    return scene_images, achievement_image
