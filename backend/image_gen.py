"""Image generation using Imagen 3 via Vertex AI / Google GenAI SDK.

Follows the same dual-auth pattern as tts.py:
- If google_cloud_project set → Vertex AI client
- Otherwise → API key client (gemini_api_key)

Scene images are generated SEQUENTIALLY with the first successful image
used as a reference anchor for subsequent images. This keeps character
designs, colors, and art style visually consistent across scenes — the
previous parallel batching produced noticeably different characters per
scene because each call was independent.
"""

import asyncio
import base64
import io
import time
from functools import lru_cache
from pathlib import Path

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from PIL import Image

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

_CONSISTENCY_SUFFIX = (
    " Keep the character designs, proportions, colors, and art style "
    "visually consistent with the reference image(s)."
)

_MAX_RETRIES = 2
_RETRY_DELAY = 3.0


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


async def generate_image(
    prompt: str,
    aspect_ratio: str = "16:9",
    reference: bytes | None = None,
    anchor: bytes | None = None,
) -> bytes | None:
    """Generate a single image, optionally threaded with reference images.

    Args:
        prompt: Scene description (style prefix is added automatically).
        aspect_ratio: Image aspect ratio (default 16:9 for story scenes).
        reference: Previous scene's image bytes for immediate style continuity.
        anchor: First successful scene's image bytes — the character-design
                canon that should stay stable across all scenes. Passed as
                an additional reference part alongside ``reference`` (unless
                they're the same image).

    Returns:
        PNG image bytes, or None if generation fails.
    """
    settings = get_settings()
    if not settings.imagen_enabled:
        logger.info("Imagen disabled, skipping image generation")
        return None

    full_prompt = f"{_STYLE_PREFIX} {prompt}"
    if reference or anchor:
        full_prompt += _CONSISTENCY_SUFFIX

    contents: list = [full_prompt]
    if anchor:
        contents.append(types.Part.from_bytes(data=anchor, mime_type="image/png"))
    if reference and reference is not anchor:
        contents.append(types.Part.from_bytes(data=reference, mime_type="image/png"))

    client = _get_client()

    for attempt in range(_MAX_RETRIES):
        try:
            start = time.perf_counter()
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.imagen_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
                ),
            )
            latency_ms = int((time.perf_counter() - start) * 1000)
            image_bytes = _extract_image_bytes(response)
            has_refs = bool(anchor or reference)
            logger.info(
                "Imagen generated image (%d bytes, %dms, refs=%s)",
                len(image_bytes),
                latency_ms,
                "yes" if has_refs else "no",
            )
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


def _downscale_to_jpeg(image_bytes: bytes, max_dim: int = 768, quality: int = 85) -> bytes:
    """Downscale an image and re-encode as JPEG for much smaller payload.

    Gemini 2.5 Flash Image returns ~1024x1024 PNGs at ~1.3MB each. Base64-
    encoded inline that's ~1.75MB of text in the turn JSON response — large
    enough to cause noticeable rendering lag when the browser decodes it.
    Downscaling to 768 on the longest side + JPEG 85% quality reduces the
    payload ~10x with no visible quality loss for watercolor art.
    """
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=quality, optimize=True)
    return out.getvalue()


def image_to_base64(image_bytes: bytes, mime: str = "image/png") -> str:
    """Convert raw image bytes to a base64-encoded data URL string."""
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{mime};base64,{encoded}"


_IMAGES_DIR = Path(__file__).parent / "data" / "images"


def _save_image(image_bytes: bytes, session_id: str, filename: str) -> Path:
    """Save image bytes to disk and return the file path."""
    session_dir = _IMAGES_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / filename
    path.write_bytes(image_bytes)
    logger.info("Saved image: %s (%d bytes)", path, len(image_bytes))
    return path


async def generate_scene_images(
    scene_descriptions: list[str],
    achievement_description: str,
    session_id: str = "",
) -> tuple[list[str | None], str | None]:
    """Generate scene images sequentially for character consistency.

    Each scene after the first receives the first-scene image as an
    "anchor" (character canon) plus the immediately previous scene as a
    "reference" (style continuity). The achievement image is generated
    last, also using the anchor.

    Args:
        scene_descriptions: List of scene image descriptions (1 for
            comparison_reveal, 3 for collaborative_story).
        achievement_description: Description for the achievement image.
        session_id: Session identifier for organizing saved images on disk.

    Returns:
        Tuple of (scene_image_data_urls, achievement_image_data_url).
        Each scene entry is a base64 data URL or None if that scene failed.
    """
    sid = session_id or "unknown"
    scene_urls: list[str | None] = []
    anchor_bytes: bytes | None = None  # first successful scene — character canon
    previous_bytes: bytes | None = None  # immediately preceding scene — style continuity

    for i, desc in enumerate(scene_descriptions):
        img_bytes = await generate_image(
            desc,
            aspect_ratio="16:9",
            reference=previous_bytes,
            anchor=anchor_bytes,
        )
        if img_bytes:
            # Save the original PNG for debug/inspection on disk
            _save_image(img_bytes, sid, f"scene_{i + 1}.png")
            # Downscale + re-encode as JPEG for the browser payload
            jpeg_bytes = _downscale_to_jpeg(img_bytes, max_dim=768, quality=85)
            scene_urls.append(image_to_base64(jpeg_bytes, mime="image/jpeg"))
            logger.info(
                "Scene %d downscaled: %d bytes -> %d bytes (%.1f%%)",
                i + 1, len(img_bytes), len(jpeg_bytes),
                100 * len(jpeg_bytes) / len(img_bytes),
            )
            # Keep the ORIGINAL PNG bytes as the reference/anchor for the
            # next generation — full resolution gives Gemini more detail
            # to lock onto for character consistency.
            if anchor_bytes is None:
                anchor_bytes = img_bytes
            previous_bytes = img_bytes
        else:
            logger.error("Scene %d image generation failed", i + 1)
            scene_urls.append(None)

    # Achievement image: use the anchor + the last scene as references.
    # 16:9 matches the landscape device panel — a 1:1 square would leave
    # large empty bands on the sides after object-contain scaling.
    achievement_bytes = await generate_image(
        achievement_description,
        aspect_ratio="16:9",
        reference=previous_bytes,
        anchor=anchor_bytes,
    )
    achievement_url: str | None = None
    if achievement_bytes:
        _save_image(achievement_bytes, sid, "achievement.png")
        jpeg_bytes = _downscale_to_jpeg(achievement_bytes, max_dim=768, quality=85)
        achievement_url = image_to_base64(jpeg_bytes, mime="image/jpeg")
        logger.info(
            "Achievement downscaled: %d bytes -> %d bytes (%.1f%%)",
            len(achievement_bytes), len(jpeg_bytes),
            100 * len(jpeg_bytes) / len(achievement_bytes),
        )
    else:
        logger.error("Achievement image generation failed")

    return scene_urls, achievement_url
