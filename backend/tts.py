"""Text-to-speech synthesis using Gemini TTS via Vertex AI."""

import asyncio
import io
import re
import time
import wave
from collections.abc import AsyncIterator
from functools import lru_cache

import av
import numpy as np
from google import genai
from google.genai import types

try:
    from .config import get_settings
    from .logger import setup_logger
except ImportError:
    from config import get_settings
    from logger import setup_logger

logger = setup_logger(__name__)

# Gemini TTS natively supported bracket tags — preserve these in text
_GEMINI_TTS_TAGS: set[str] = {
    "sigh",
    "laughing",
    "uhm",
    "sarcasm",
    "robotic",
    "shouting",
    "whispering",
    "extremely fast",
    "scared",
    "curious",
    "bored",
    "short pause",
    "medium pause",
    "long pause",
}

# Matches any [tag] anywhere in text
_BRACKET_TAG_RE = re.compile(r"\[([^\]]+)\]\s*")


def _strip_unsupported_tags(text: str) -> str:
    """Strip ALL bracket tags not supported by Gemini TTS.

    Removes emotion tags like [excited] and stray cue IDs like [nature_grass_rustle]
    that the LLM may embed in dialogue. Preserves only Gemini-native tags like
    [laughing], [whispering], [curious].
    """

    def _replace(m: re.Match) -> str:
        tag = m.group(1).lower()
        if tag in _GEMINI_TTS_TAGS:
            return m.group(0)  # keep Gemini tag as-is
        return ""  # strip non-Gemini tag

    return _BRACKET_TAG_RE.sub(_replace, text).strip()


TIER_VOICES: dict[str, str] = {
    "T0": "Puck",
    "T1": "Kore",
    "T2": "Aoede",
}

SAMPLE_RATE = 24000
OPUS_BITRATE_BPS = 32000
# OGG page duration for streaming — 200ms balances latency vs overhead
_OGG_PAGE_DURATION_US = 200_000
# Minimum PCM samples to accumulate before encoding an Opus frame (200ms at 24kHz)
_ENCODE_FRAME_SAMPLES = int(SAMPLE_RATE * 0.2)
_ENCODE_FRAME_BYTES = _ENCODE_FRAME_SAMPLES * 2


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


def _open_ogg_opus_output(
    buffer: io.BytesIO, sample_rate: int = SAMPLE_RATE, page_duration_us: int | None = None
) -> tuple:  # (OutputContainer, AudioStream) — PyAV types not resolvable by Pyright
    """Create a configured OGG/Opus output container and stream."""
    options = {"page_duration": str(page_duration_us)} if page_duration_us is not None else None
    output = av.open(buffer, mode="w", format="ogg", options=options)
    stream = output.add_stream("libopus", rate=sample_rate)
    stream.layout = "mono"
    stream.bit_rate = OPUS_BITRATE_BPS
    return output, stream


def _pcm_to_ogg_opus(pcm_data: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Encode raw PCM 16-bit mono audio to OGG/Opus using PyAV.

    Args:
        pcm_data: Raw PCM 16-bit little-endian mono audio bytes.
        sample_rate: Sample rate in Hz (default 24000).

    Returns:
        Complete OGG/Opus file bytes.
    """
    samples = np.frombuffer(pcm_data, dtype=np.int16)
    buf = io.BytesIO()
    output, stream = _open_ogg_opus_output(buf, sample_rate)

    frame = av.AudioFrame.from_ndarray(samples.reshape(1, -1), format="s16", layout="mono")
    frame.sample_rate = sample_rate
    frame.pts = 0

    for pkt in stream.encode(frame):
        output.mux(pkt)
    for pkt in stream.encode(None):
        output.mux(pkt)
    output.close()

    return buf.getvalue()


async def synthesize_speech_ogg_async(text: str, tier: str, max_retries: int = 2) -> tuple[bytes, int] | None:
    """Synthesize speech and encode to OGG/Opus.

    Collects all PCM from Gemini TTS, encodes to OGG/Opus via PyAV.
    Falls back to WAV on encoding failure.

    Args:
        text: Text to synthesize.
        tier: Age tier (T0, T1, T2) for voice selection.
        max_retries: Number of retry attempts on connection errors.

    Returns:
        Tuple of (encoded audio bytes, original PCM size in bytes), or None on TTS failure.
    """
    chunks: list[bytes] = []
    async for chunk in synthesize_speech_stream_async(text, tier, max_retries):
        chunks.append(chunk)

    if not chunks:
        return None

    pcm_data = b"".join(chunks)
    # Ensure even byte count for 16-bit PCM
    if len(pcm_data) % 2 != 0:
        pcm_data = pcm_data[:-1]

    if len(pcm_data) == 0:
        return None

    pcm_size = len(pcm_data)
    try:
        return _pcm_to_ogg_opus(pcm_data), pcm_size
    except Exception as e:
        logger.warning(f"OGG/Opus encoding failed, falling back to WAV: {e}")
        return _pcm_to_wav(pcm_data), pcm_size


async def synthesize_speech_ogg_stream_async(text: str, tier: str, max_retries: int = 2) -> AsyncIterator[bytes]:
    """Stream OGG/Opus audio, encoding incrementally as PCM arrives from Gemini.

    Yields OGG page bytes as they are produced, enabling progressive playback
    in Chrome's <audio> element. First audio chunk arrives ~200ms after Gemini's
    first PCM chunk.

    Args:
        text: Text to synthesize.
        tier: Age tier (T0, T1, T2) for voice selection.
        max_retries: Number of retry attempts on connection errors.

    Yields:
        OGG/Opus byte chunks (complete OGG pages).
    """
    buf = io.BytesIO()
    output, ogg_stream = _open_ogg_opus_output(buf, SAMPLE_RATE, _OGG_PAGE_DURATION_US)

    pcm_accum = bytearray()
    pts = 0
    total_pcm_bytes = 0
    ogg_pos = 0
    start = time.perf_counter()

    def _flush_buf() -> bytes:
        """Read any new bytes written to the OGG buffer since last flush."""
        nonlocal ogg_pos
        new_pos = buf.tell()
        if new_pos <= ogg_pos:
            return b""
        buf.seek(ogg_pos)
        data = buf.read(new_pos - ogg_pos)
        buf.seek(new_pos)
        ogg_pos = new_pos
        return data

    def _encode_frame(samples: np.ndarray) -> bytes:
        """Encode one Opus frame and return any new OGG bytes."""
        nonlocal pts
        frame = av.AudioFrame.from_ndarray(samples.reshape(1, -1), format="s16", layout="mono")
        frame.sample_rate = SAMPLE_RATE
        frame.pts = pts
        pts += len(samples)
        for pkt in ogg_stream.encode(frame):
            output.mux(pkt)
        return _flush_buf()

    try:
        async for raw_chunk in synthesize_speech_stream_async(text, tier, max_retries):
            total_pcm_bytes += len(raw_chunk)
            # Ensure even byte count for int16
            pcm_chunk = raw_chunk[: len(raw_chunk) & ~1]
            if len(pcm_chunk) == 0:
                continue

            pcm_accum.extend(pcm_chunk)

            # Encode full frames as they accumulate
            while len(pcm_accum) >= _ENCODE_FRAME_BYTES:
                frame_bytes = bytes(pcm_accum[:_ENCODE_FRAME_BYTES])
                del pcm_accum[:_ENCODE_FRAME_BYTES]
                ogg_bytes = _encode_frame(np.frombuffer(frame_bytes, dtype=np.int16))
                if ogg_bytes:
                    yield ogg_bytes

        # Encode remaining PCM
        if len(pcm_accum) > 0:
            ogg_bytes = _encode_frame(np.frombuffer(bytes(pcm_accum), dtype=np.int16))
            if ogg_bytes:
                yield ogg_bytes

        # Flush encoder and muxer
        for pkt in ogg_stream.encode(None):
            output.mux(pkt)
        output.close()
        final = _flush_buf()
        if final:
            yield final

        latency_ms = int((time.perf_counter() - start) * 1000)
        duration_ms = (total_pcm_bytes // 2) * 1000 // SAMPLE_RATE
        logger.info(f"TTS OGG stream done: duration={duration_ms}ms, pcm={total_pcm_bytes}B, latency={latency_ms}ms")

    except Exception as e:
        # Try to close the container cleanly
        try:
            output.close()
        except Exception:
            pass
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.error(f"TTS OGG stream failed ({latency_ms}ms): {e}")


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
    text = _strip_unsupported_tags(text)
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
    text = _strip_unsupported_tags(text)
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
            for part in chunk.candidates[0].content.parts or []:
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
    text = _strip_unsupported_tags(text)
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
                for part in chunk.candidates[0].content.parts or []:
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
