"""Text-to-speech synthesis using Gemini TTS via Vertex AI."""

import asyncio
import io
import time
import wave
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
    client = genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location="global",
    )
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


async def synthesize_speech(text: str, tier: str) -> bytes | None:
    """Synthesize speech from text using Gemini TTS.

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
        speech_config = types.SpeechConfig(
            voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name))
        )

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
