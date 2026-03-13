"""Vision API for entity identification using Gemini Vision via Vertex AI."""

import asyncio
import json
import time
from functools import lru_cache
from typing import Any

from google import genai
from google.genai import types

try:
    from .config import get_settings
    from .logger import setup_logger
except ImportError:
    from config import get_settings
    from logger import setup_logger

logger = setup_logger(__name__)

_VISION_PROMPT = (
    "Identify the main object or entity in this image. "
    "Return JSON with exactly these fields: "
    '{"entity": "short name", "confidence": 0.0-1.0, "scene": "brief scene description", '
    '"features": ["visual feature 1", "visual feature 2", ...]}'
)


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    """Get or create the Gemini client."""
    settings = get_settings()
    client = genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )
    logger.info("Initialized Gemini Vision client")
    return client


async def analyze_image(image_bytes: bytes, mime_type: str) -> dict[str, Any]:
    """Analyze an image to identify the main entity.

    Args:
        image_bytes: Raw image bytes.
        mime_type: MIME type of the image (e.g., "image/jpeg").

    Returns:
        Dict with entity, confidence, scene, and features.
    """
    settings = get_settings()
    start = time.perf_counter()

    try:
        client = _get_client()
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        loop = asyncio.get_running_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=settings.gemini_model,
                    contents=[image_part, _VISION_PROMPT],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1,
                        max_output_tokens=500,
                    ),
                ),
            ),
            timeout=settings.vision_timeout_ms / 1000,
        )

        latency_ms = int((time.perf_counter() - start) * 1000)
        result = json.loads(response.text) if response.text else {}
        logger.info(f"Vision analysis: entity={result.get('entity')}, latency={latency_ms}ms")
        return result

    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.error(f"Vision analysis failed ({latency_ms}ms): {e}")
        return {
            "entity": "unknown",
            "confidence": 0.0,
            "scene": "unknown",
            "features": [],
        }
