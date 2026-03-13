"""Text-to-speech synthesis using Gemini TTS via Vertex AI."""

import asyncio
import io
import time
import wave
from collections.abc import AsyncIterator
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

TIER_VOICES: dict[str, str] = {
    "T0": "Puck",
    "T1": "Kore",
    "T2": "Aoede",
}

SAMPLE_RATE = 24000


@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    """Get or create the Gemini TTS client."""
    settings = get_settings()
    if settings.google_cloud_project:
        client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location="global",
        )
    else:
        client = genai.Client(api_key=settings.gemini_api_key)
    logger.info("Initialized Gemini TTS client")
    return client


def _pcm_to_wav(pcm_data: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Convert raw PCM 16-bit audio data to WAV format."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm_data)
    return buf.getvalue()


def _get_speech_config(tier: str) -> types.SpeechConfig:
    """Build SpeechConfig for the given age tier."""
    voice_name = TIER_VOICES.get(tier, "Kore")
    return types.SpeechConfig(
        voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name))
    )


async def synthesize_speech(text: str, tier: str) -> bytes | None:
    """Synthesize speech from text using Gemini TTS (non-streaming).

    Args:
        text: Text to synthesize.
        tier: Age tier (T0, T1, T2) for voice selection.

    Returns:
        WAV audio bytes, or None on failure.
    """
    settings = get_settings()
    start = time.perf_counter()
    voice_name = TIER_VOICES.get(tier, "Kore")

    try:
        client = _get_client()
        speech_config = _get_speech_config(tier)

        loop = asyncio.get_running_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=settings.tts_model,
                contents=text,
                config=types.GenerateContentConfig(speech_config=speech_config),
            ),
        )

        # Extract PCM audio from response
        pcm_data = None
        if response.candidates and response.candidates[0].content:
            parts = response.candidates[0].content.parts
            if parts and hasattr(parts[0], "inline_data") and parts[0].inline_data:
                pcm_data = parts[0].inline_data.data

        if not pcm_data:
            logger.warning("No audio data in TTS response")
            return None

        wav_data = _pcm_to_wav(pcm_data)
        latency_ms = int((time.perf_counter() - start) * 1000)
        duration_ms = (len(pcm_data) // 2) * 1000 // SAMPLE_RATE
        logger.info(f"TTS: voice={voice_name}, duration={duration_ms}ms, latency={latency_ms}ms")
        return wav_data

    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.error(f"TTS synthesis failed ({latency_ms}ms): {e}")
        return None


async def synthesize_speech_stream(text: str, tier: str) -> AsyncIterator[bytes]:
    """Stream PCM audio chunks from Gemini TTS (sync iteration, for /api/tts).

    Yields raw PCM 16-bit mono 24kHz chunks as they arrive from the model,
    enabling the frontend to start playback before the full response is ready.

    Args:
        text: Text to synthesize.
        tier: Age tier (T0, T1, T2) for voice selection.

    Yields:
        Raw PCM 16-bit audio bytes chunks.
    """
    settings = get_settings()
    start = time.perf_counter()
    voice_name = TIER_VOICES.get(tier, "Kore")
    total_bytes = 0
    first_chunk = True

    try:
        client = _get_client()
        speech_config = _get_speech_config(tier)

        loop = asyncio.get_running_loop()
        stream = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content_stream(
                model=settings.tts_model,
                contents=text,
                config=types.GenerateContentConfig(speech_config=speech_config),
            ),
        )

        for chunk in stream:
            if not chunk.candidates or not chunk.candidates[0].content:
                continue
            for part in chunk.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                    pcm_chunk = part.inline_data.data
                    total_bytes += len(pcm_chunk)
                    if first_chunk:
                        ttfb_ms = int((time.perf_counter() - start) * 1000)
                        logger.info(f"TTS stream: voice={voice_name}, first chunk at {ttfb_ms}ms")
                        first_chunk = False
                    yield pcm_chunk

        latency_ms = int((time.perf_counter() - start) * 1000)
        duration_ms = (total_bytes // 2) * 1000 // SAMPLE_RATE
        logger.info(f"TTS stream done: voice={voice_name}, duration={duration_ms}ms, total_latency={latency_ms}ms")

    except Exception as e:
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.error(f"TTS stream failed ({latency_ms}ms): {e}")


async def synthesize_speech_stream_async(text: str, tier: str, max_retries: int = 2) -> AsyncIterator[bytes]:
    """Fully async TTS streaming using client.aio with retry on connection errors.

    Uses the async streaming API for proper event loop integration.
    Preferred for server-side pipelining (e.g., combined turn+TTS endpoint).

    Args:
        text: Text to synthesize.
        tier: Age tier (T0, T1, T2) for voice selection.
        max_retries: Number of retry attempts on connection errors.

    Yields:
        Raw PCM 16-bit audio bytes chunks.
    """
    settings = get_settings()
    voice_name = TIER_VOICES.get(tier, "Kore")

    for attempt in range(max_retries + 1):
        start = time.perf_counter()
        total_bytes = 0
        first_chunk = True

        try:
            client = _get_client()
            speech_config = _get_speech_config(tier)

            response_stream = await client.aio.models.generate_content_stream(
                model=settings.tts_model,
                contents=text,
                config=types.GenerateContentConfig(speech_config=speech_config),
            )

            async for chunk in response_stream:
                if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
                    continue
                for part in chunk.candidates[0].content.parts:
                    if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
                        pcm_chunk = part.inline_data.data
                        total_bytes += len(pcm_chunk)
                        if first_chunk:
                            ttfb_ms = int((time.perf_counter() - start) * 1000)
                            logger.info(f"TTS async: voice={voice_name}, first chunk at {ttfb_ms}ms")
                            first_chunk = False
                        yield pcm_chunk

            latency_ms = int((time.perf_counter() - start) * 1000)
            duration_ms = (total_bytes // 2) * 1000 // SAMPLE_RATE
            logger.info(f"TTS async done: voice={voice_name}, duration={duration_ms}ms, total_latency={latency_ms}ms")
            return  # Success — exit retry loop

        except (ConnectionError, ConnectionResetError, OSError) as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            if attempt < max_retries:
                logger.warning(f"TTS async connection error ({latency_ms}ms), retry {attempt + 1}/{max_retries}: {e}")
                await asyncio.sleep(0.5 * (attempt + 1))
            else:
                logger.error(f"TTS async stream failed after {max_retries + 1} attempts ({latency_ms}ms): {e}")

        except Exception as e:
            latency_ms = int((time.perf_counter() - start) * 1000)
            logger.error(f"TTS async stream failed ({latency_ms}ms): {e}")
            return  # Non-retryable error
