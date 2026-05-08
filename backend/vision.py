"""Vision API for entity identification using Qwen VL via DashScope."""

import asyncio
import base64
import json
import time
from functools import lru_cache
from typing import Any

import httpx
from openai import AsyncOpenAI

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
def _get_client() -> AsyncOpenAI:
    """Get or create the DashScope client."""
    settings = get_settings()
    client = AsyncOpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        max_retries=0,
        timeout=httpx.Timeout(30.0, connect=5.0),
    )
    logger.info("Initialized DashScope Vision client")
    return client


async def analyze_image(image_bytes: bytes, mime_type: str, max_retries: int = 1) -> dict[str, Any]:
    """Analyze an image to identify the main entity.

    Args:
        image_bytes: Raw image bytes.
        mime_type: MIME type of the image (e.g., "image/jpeg").
        max_retries: Number of retry attempts on connection errors.

    Returns:
        Dict with entity, confidence, scene, and features.
    """
    settings = get_settings()
    _fallback = {"entity": "unknown", "confidence": 0.0, "scene": "unknown", "features": []}

    b64_data = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64_data}"

    for attempt in range(max_retries + 1):
        start = time.perf_counter()
        try:
            client = _get_client()

            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=settings.dashscope_model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "image_url", "image_url": {"url": data_url}},
                                {"type": "text", "text": _VISION_PROMPT},
                            ],
                        }
                    ],
                    temperature=0.1,
                    max_tokens=500,
                    extra_body={"enable_thinking": False},
                ),
                timeout=settings.vision_timeout_ms / 1000,
            )

            latency_ms = int((time.perf_counter() - start) * 1000)
            text = response.choices[0].message.content or ""
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            result = json.loads(text) if text else {}
            logger.info(f"Vision analysis: entity={result.get('entity')}, latency={latency_ms}ms")
            return result

        except (ConnectionError, ConnectionResetError, OSError) as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            if attempt < max_retries:
                logger.warning(f"Vision connection error ({latency_ms}ms), retry {attempt + 1}/{max_retries}: {e}")
                await asyncio.sleep(0.5)
            else:
                logger.error(f"Vision analysis failed after {max_retries + 1} attempts ({latency_ms}ms): {e}")
                return _fallback

        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error(f"Vision analysis failed ({latency_ms}ms): {e}")
            return _fallback

    return _fallback
