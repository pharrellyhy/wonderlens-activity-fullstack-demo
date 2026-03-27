"""Unit tests for the OGG/Opus PCM encoder in tts.py."""

import io
from unittest.mock import patch

import av
import pytest
from tts import _pcm_to_ogg_opus, synthesize_speech_ogg_stream_async


class TestPcmToOggOpus:
    def test_valid_output_starts_with_oggs_magic(self) -> None:
        pcm_data = b"\x00\x00" * 960  # 40ms of silence at 24kHz
        result = _pcm_to_ogg_opus(pcm_data, sample_rate=24000)
        assert result[:4] == b"OggS"

    def test_output_smaller_than_input(self) -> None:
        pcm_data = b"\x00\x00" * 24000  # 1 second of silence at 24kHz
        result = _pcm_to_ogg_opus(pcm_data, sample_rate=24000)
        assert len(result) < len(pcm_data)
        compression_ratio = len(pcm_data) / len(result)
        assert compression_ratio > 2.0

    def test_empty_input_raises(self) -> None:
        with pytest.raises(Exception):
            _pcm_to_ogg_opus(b"", sample_rate=24000)

    def test_longer_audio_compresses_well(self) -> None:
        pcm_data = b"\x00\x00" * (24000 * 5)  # 5 seconds of silence
        result = _pcm_to_ogg_opus(pcm_data, sample_rate=24000)
        assert result[:4] == b"OggS"
        # 5s of speech PCM = 240KB, OGG/Opus should be well under 100KB
        assert len(result) < 100_000


class TestOggStreamEncoder:
    @pytest.mark.asyncio
    async def test_streaming_encoder_yields_ogg_pages(self) -> None:
        """Streaming encoder should yield multiple OGG page chunks."""
        # Mock synthesize_speech_stream_async to yield PCM chunks
        pcm_chunks = [b"\x00\x00" * 4800 for _ in range(10)]  # 10 x 200ms = 2s

        async def _fake_pcm_stream(text, tier, max_retries=2):
            for chunk in pcm_chunks:
                yield chunk

        with patch("tts.synthesize_speech_stream_async", new=_fake_pcm_stream):
            ogg_chunks = []
            async for chunk in synthesize_speech_ogg_stream_async("test", "T0"):
                ogg_chunks.append(chunk)

        assert len(ogg_chunks) > 1, "Should yield multiple chunks for streaming"
        full_ogg = b"".join(ogg_chunks)
        assert full_ogg[:4] == b"OggS"

    @pytest.mark.asyncio
    async def test_streaming_encoder_produces_valid_ogg(self) -> None:
        """Concatenated streaming output should be a valid OGG/Opus file."""
        pcm_chunks = [b"\x00\x00" * 12000 for _ in range(5)]  # 5 x 500ms

        async def _fake_pcm_stream(text, tier, max_retries=2):
            for chunk in pcm_chunks:
                yield chunk

        with patch("tts.synthesize_speech_stream_async", new=_fake_pcm_stream):
            ogg_data = b""
            async for chunk in synthesize_speech_ogg_stream_async("test", "T0"):
                ogg_data += chunk

        # Verify it's decodable
        container = av.open(io.BytesIO(ogg_data))
        stream = container.streams.audio[0]
        assert stream.codec_context.name == "opus"
        container.close()
