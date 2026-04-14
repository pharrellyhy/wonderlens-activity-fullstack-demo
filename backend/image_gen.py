"""Image generation using Imagen 3 via Vertex AI / Google GenAI SDK.

Follows the same dual-auth pattern as tts.py:
- If google_cloud_project set → Vertex AI client
- Otherwise → API key client (gemini_api_key)

Scene images are generated SEQUENTIALLY with the first successful image
used as a reference anchor for subsequent images. This keeps character
designs, colors, and art style visually consistent across scenes — the
previous parallel batching produced noticeably different characters per
scene because each call was independent.

Progressive delivery: the sequential worker publishes each finished image
via a per-session ``asyncio.Future`` the moment it resolves, so scene 1
can be delivered to the frontend while scenes 2 and 3 are still mid-
generation. See ``start_scene_images`` / ``get_scene_futures``.
"""

import asyncio
import base64
import io
import time
from dataclasses import dataclass, field
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

_STYLE_PREFIX = "Soft watercolor children's storybook illustration. Gentle pastel tones, warm lighting."

_CONSISTENCY_SUFFIX = (
    " Keep the character designs, proportions, colors, and art style visually consistent with the reference image(s)."
)

# Caption template: Gemini 2.5 Flash Image is decent at rendering short
# quoted text when we spell out exactly what should appear. Keeping the
# caption short (≤10 words) and quoted improves fidelity dramatically —
# longer or unquoted captions tend to get misspelled. We build this with
# simple concatenation (not str.format) so captions containing literal
# braces from an LLM don't crash the call.
_CAPTION_PREFIX = (
    ' Include exactly ONE short hand-lettered caption along the bottom of the illustration that reads EXACTLY: "'
)
_CAPTION_SUFFIX = (
    '". Paint it in a cozy hand-lettered storybook style, clearly readable,'
    " no other words, no extra letters, no speech bubbles elsewhere in the image."
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
    caption: str | None = None,
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
        caption: Optional short (≤10 word) caption to bake into the image as
                hand-lettered text along the bottom. When None, the image is
                rendered without any text.

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
    if caption:
        # String concatenation rather than .format() so a caption
        # containing literal "{" or "}" (possible from an LLM) can't
        # trigger a KeyError / IndexError at runtime. We also strip any
        # pre-existing double quotes from the caption so they don't
        # collide with the quoted-instruction wrapper.
        safe_caption = caption.strip().replace('"', "").replace("\u201c", "").replace("\u201d", "")
        if safe_caption:
            full_prompt += _CAPTION_PREFIX + safe_caption + _CAPTION_SUFFIX

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


@dataclass
class _SceneSession:
    """Per-session state for progressive scene image delivery.

    ``scene_futures`` holds one future per scene description (in order),
    ``achievement_future`` holds the future for the achievement image, and
    ``task`` is kept as a strong reference so the event loop doesn't garbage-
    collect the background worker while it's still running.

    ``scene_failed`` + ``achievement_failed`` are mutated by the worker
    when generation returns no bytes. They let callers distinguish a
    confirmed failure from "still pending" when a future resolves to None.
    """

    scene_futures: list[asyncio.Future[str | None]]
    achievement_future: asyncio.Future[str | None]
    scene_failed: list[bool] = field(default_factory=list)
    achievement_failed: bool = False
    task: asyncio.Task[None] | None = field(default=None, repr=False)


_scene_sessions: dict[str, _SceneSession] = {}


def _process_generated_image(img_bytes: bytes, session_id: str, filename: str, label: str) -> str:
    """Save PNG to disk and return a downscaled JPEG data URL for the browser."""
    _save_image(img_bytes, session_id, filename)
    jpeg_bytes = _downscale_to_jpeg(img_bytes, max_dim=768, quality=85)
    logger.info(
        "%s downscaled: %d bytes -> %d bytes (%.1f%%)",
        label,
        len(img_bytes),
        len(jpeg_bytes),
        100 * len(jpeg_bytes) / len(img_bytes),
    )
    return image_to_base64(jpeg_bytes, mime="image/jpeg")


async def _scene_image_worker(
    session: "_SceneSession",
    session_id: str,
    scene_descriptions: list[str],
    achievement_description: str,
    scene_captions: list[str | None],
    achievement_caption: str | None,
) -> None:
    """Sequential scene generator that resolves each future as its image lands.

    Generation order is preserved (later scenes use earlier images as
    anchor/reference for character consistency), but each finished image is
    published immediately so callers awaiting scene N don't have to wait for
    scenes N+1..M to finish.

    On failure the worker records the outcome on the shared
    ``_SceneSession`` (``scene_failed[i] = True`` or ``achievement_failed =
    True``) so callers can distinguish "generation failed" from "still
    pending" when a future resolves to None.

    ``scene_captions`` and ``achievement_caption`` are optional short (<=10
    word) strings baked into the bottom of each image as hand-lettered text.
    When a caption is None the corresponding image renders without any text.
    """
    sid = session_id or "unknown"
    anchor_bytes: bytes | None = None  # first successful scene — character canon
    previous_bytes: bytes | None = None  # immediately preceding scene — style continuity

    def _set(future: asyncio.Future[str | None], value: str | None) -> None:
        if not future.done():
            future.set_result(value)

    for i, desc in enumerate(scene_descriptions):
        data_url: str | None = None
        caption = scene_captions[i] if i < len(scene_captions) else None
        try:
            img_bytes = await generate_image(
                desc,
                aspect_ratio="16:9",
                reference=previous_bytes,
                anchor=anchor_bytes,
                caption=caption,
            )
        except Exception as exc:
            logger.error("Scene %d generation raised: %s", i + 1, exc)
            img_bytes = None

        if img_bytes:
            data_url = _process_generated_image(img_bytes, sid, f"scene_{i + 1}.png", f"Scene {i + 1}")
            # Keep the ORIGINAL PNG bytes as the reference/anchor for the
            # next generation — full resolution gives Gemini more detail
            # to lock onto for character consistency.
            if anchor_bytes is None:
                anchor_bytes = img_bytes
            previous_bytes = img_bytes
        else:
            logger.error("Scene %d image generation failed", i + 1)
            session.scene_failed[i] = True

        _set(session.scene_futures[i], data_url)

    # Achievement image: use the anchor + the last scene as references.
    # 16:9 matches the landscape device panel — a 1:1 square would leave
    # large empty bands on the sides after object-contain scaling.
    achievement_url: str | None = None
    try:
        achievement_bytes = await generate_image(
            achievement_description,
            aspect_ratio="16:9",
            reference=previous_bytes,
            anchor=anchor_bytes,
            caption=achievement_caption,
        )
    except Exception as exc:
        logger.error("Achievement generation raised: %s", exc)
        achievement_bytes = None

    if achievement_bytes:
        achievement_url = _process_generated_image(achievement_bytes, sid, "achievement.png", "Achievement")
    else:
        logger.error("Achievement image generation failed")
        session.achievement_failed = True

    _set(session.achievement_future, achievement_url)


def start_scene_images(
    session_id: str,
    scene_descriptions: list[str],
    achievement_description: str,
    scene_captions: list[str | None] | None = None,
    achievement_caption: str | None = None,
) -> _SceneSession:
    """Kick off sequential scene image generation as a background task.

    Returns immediately with a ``_SceneSession`` whose futures resolve
    progressively as each image lands. Callers should await
    ``scene_futures[n]`` for scene N and ``achievement_future`` for the
    achievement image. A strong reference to the worker task is held inside
    the returned session (and the module-level registry) so the event loop
    doesn't garbage-collect it mid-run.

    ``scene_captions`` (one per scene) and ``achievement_caption`` are
    optional short strings baked into each image as hand-lettered text. When
    omitted the images render without captions, preserving the pre-caption
    behaviour for callers that don't care about in-image text.

    If a session already exists for ``session_id``, its previous worker is
    cancelled before the new one starts — this keeps reset / retry flows
    from leaking stale tasks.
    """
    clear_scene_session(session_id)

    # Normalise captions to a list aligned with scene_descriptions so the
    # worker can index by scene number without extra bounds checks.
    normalized_captions: list[str | None]
    if scene_captions is None:
        normalized_captions = [None] * len(scene_descriptions)
    elif len(scene_captions) < len(scene_descriptions):
        normalized_captions = list(scene_captions) + [None] * (len(scene_descriptions) - len(scene_captions))
    else:
        normalized_captions = list(scene_captions)

    loop = asyncio.get_running_loop()
    scene_futures: list[asyncio.Future[str | None]] = [loop.create_future() for _ in scene_descriptions]
    achievement_future: asyncio.Future[str | None] = loop.create_future()

    # Create the session first so the worker can mutate its failure flags.
    session = _SceneSession(
        scene_futures=scene_futures,
        achievement_future=achievement_future,
        scene_failed=[False] * len(scene_descriptions),
    )
    _scene_sessions[session_id] = session

    session.task = asyncio.create_task(
        _scene_image_worker(
            session,
            session_id,
            scene_descriptions,
            achievement_description,
            normalized_captions,
            achievement_caption,
        ),
        name=f"scene-images-{session_id}",
    )
    return session


def get_scene_session(session_id: str) -> _SceneSession | None:
    """Look up the active scene-image session for ``session_id``, if any."""
    return _scene_sessions.get(session_id)


def clear_scene_session(session_id: str) -> None:
    """Cancel and drop any scene-image session registered for ``session_id``."""
    session = _scene_sessions.pop(session_id, None)
    if session is None:
        return
    if session.task is not None and not session.task.done():
        session.task.cancel()
    for fut in (*session.scene_futures, session.achievement_future):
        if not fut.done():
            fut.cancel()


async def generate_scene_images(
    scene_descriptions: list[str],
    achievement_description: str,
    session_id: str = "",
    scene_captions: list[str | None] | None = None,
    achievement_caption: str | None = None,
) -> tuple[list[str | None], str | None]:
    """Generate all scene images + achievement and wait for them.

    Thin wrapper around ``start_scene_images`` preserved for callers that
    want the old "block until everything is ready" behaviour (comparison
    reveal, ad-hoc scripts, tests). Progressive callers should use
    ``start_scene_images`` directly and await individual futures.

    Returns:
        Tuple of (scene_image_data_urls, achievement_image_data_url).
        Each scene entry is a base64 data URL or None if that scene failed.
    """
    session = start_scene_images(
        session_id,
        scene_descriptions,
        achievement_description,
        scene_captions=scene_captions,
        achievement_caption=achievement_caption,
    )
    scene_urls = [await fut for fut in session.scene_futures]
    achievement_url = await session.achievement_future
    return scene_urls, achievement_url
