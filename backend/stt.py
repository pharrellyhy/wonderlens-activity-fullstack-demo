"""Speech-to-text transcription using Gemini via Vertex AI."""

import asyncio
import time
from functools import lru_cache

from google import genai
from google.genai import types

try:
    from .config import get_settings
    from .logger import setup_logger
except ImportError:
    from config import get_settings
    from logger import setup_logger

logger = setup_logger(__name__)

# Magic byte signatures for audio format detection
_SIGNATURES: dict[bytes, str] = {
    b"RIFF": "audio/wav",
    b"fLaC": "audio/flac",
    b"OggS": "audio/ogg",
    b"\x1a\x45\xdf\xa3": "audio/webm",
}

_MP3_PREFIXES: set[bytes] = {b"\xff\xfb", b"\xff\xfa", b"\xff\xf3", b"\xff\xf2", b"ID3"}


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    """Get or create the Gemini STT client."""
    settings = get_settings()
    client = genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )
    logger.info("Initialized Gemini STT client")
    return client


def _detect_mime_type(audio_data: bytes) -> str:
    """Detect audio MIME type from magic bytes."""
    if len(audio_data) < 4:
        return "audio/wav"

    header = audio_data[:4]

    # Check fixed signatures
    for sig, mime in _SIGNATURES.items():
        if header.startswith(sig):
            # Verify RIFF is actually WAV (not AVI etc.)
            if sig == b"RIFF" and len(audio_data) >= 12:
                if audio_data[8:12] != b"WAVE":
                    return "audio/wav"
            return mime

    # Check MP3 signatures
    for prefix in _MP3_PREFIXES:
        if audio_data[: len(prefix)] == prefix:
            return "audio/mp3"

    return "audio/wav"


async def transcribe_audio(audio_data: bytes, mime_type: str | None = None) -> dict:
    """Transcribe audio using Gemini.

    Args:
        audio_data: Raw audio bytes (WAV, WebM, OGG, MP3, FLAC).
        mime_type: Audio MIME type. Auto-detected from magic bytes if None.

    Returns:
        Dict with 'text', 'confidence', and 'latency_ms' keys.
        Returns empty text on failure.
    """
    settings = get_settings()
    start = time.perf_counter()

    if mime_type is None:
        mime_type = _detect_mime_type(audio_data)

    try:
        client = _get_client()
        audio_part = types.Part.from_bytes(data=audio_data, mime_type=mime_type)

        loop = asyncio.get_running_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model=settings.gemini_model,
                    contents=[
                        audio_part,
                        "Please transcribe the speech in this audio. Return only the transcription text.",
                    ],
                ),
            ),
            timeout=30.0,
        )

        text = response.text.strip() if response.text else ""
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.info(f"STT: text_len={len(text)}, mime={mime_type}, latency={latency_ms}ms")

        return {
            "text": text,
            "confidence": 0.95,
            "latency_ms": latency_ms,
        }

    except asyncio.TimeoutError:
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.error(f"STT transcription timed out ({latency_ms}ms)")
        return {"text": "", "confidence": 0.0, "latency_ms": latency_ms}

    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.error(f"STT transcription failed ({latency_ms}ms): {e}")
        return {"text": "", "confidence": 0.0, "latency_ms": latency_ms}
