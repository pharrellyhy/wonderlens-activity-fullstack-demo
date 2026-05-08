"""Tests for the portable STT WebSocket protocol."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from server import app
from stt_stream import (
    AudioCodec,
    SttStartMessage,
    select_stt_provider_route,
    validate_first_audio_chunk,
)


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    """Create a TestClient with a temp DB, triggering startup to init tables."""
    from config import get_settings  # noqa: PLC0415

    get_settings.cache_clear()
    settings = get_settings()
    original_db_path = settings.db_path
    settings.db_path = str(tmp_path / "test.db")

    with TestClient(app) as c:
        yield c

    settings.db_path = original_db_path
    get_settings.cache_clear()


def _browser_opus_start(container: str = "webm", mime_type: str = "audio/webm;codecs=opus") -> dict:
    return {
        "type": "start",
        "audio": {
            "codec": "opus",
            "container": container,
            "mime_type": mime_type,
            "channels": 1,
            "target_bitrate_bps": 24000,
            "chunk_duration_ms": 100,
        },
        "stt": {
            "language": "en-US",
            "interim_results": True,
            "provider": "default",
        },
        "client": {
            "platform": "browser",
            "sdk_version": "1.0.0",
        },
    }


def test_accepts_browser_webm_opus_start_message() -> None:
    message = SttStartMessage.model_validate(_browser_opus_start())

    assert message.audio.codec is AudioCodec.OPUS
    assert message.audio.container == "webm"
    assert message.stt.language == "en-US"
    assert message.client.platform == "browser"


def test_rejects_pcm_start_without_sample_rate() -> None:
    payload = _browser_opus_start(container="raw", mime_type="audio/L16")
    payload["audio"]["codec"] = "pcm_s16le"

    with pytest.raises(ValidationError):
        SttStartMessage.model_validate(payload)


def test_rejects_opus_start_with_raw_container() -> None:
    payload = _browser_opus_start(container="raw", mime_type="audio/webm;codecs=opus")

    with pytest.raises(ValidationError):
        SttStartMessage.model_validate(payload)


def test_opus_provider_route_omits_pcm_only_request_fields() -> None:
    message = SttStartMessage.model_validate(_browser_opus_start())

    route = select_stt_provider_route(message.audio)

    assert route.name == "direct_opus_webm"
    assert route.mime_type == "audio/webm;codecs=opus"
    assert route.provider_request["mime_type"] == "audio/webm;codecs=opus"
    assert "encoding" not in route.provider_request
    assert "sample_rate_hz" not in route.provider_request


def test_validates_first_chunk_matches_declared_container() -> None:
    message = SttStartMessage.model_validate(_browser_opus_start(container="ogg", mime_type="audio/ogg;codecs=opus"))

    validate_first_audio_chunk(message.audio, b"OggS\x00\x00")

    with pytest.raises(ValueError, match="container signature"):
        validate_first_audio_chunk(message.audio, b"\x1a\x45\xdf\xa3\x00\x00")


def test_stt_stream_rejects_binary_before_start(client: TestClient) -> None:
    with client.websocket_connect("/api/stt/stream") as ws:
        ws.send_bytes(b"OggS\x00")
        message = ws.receive_json()

    assert message["type"] == "error"
    assert message["code"] == "start_required"


@patch("server.transcribe_audio", new_callable=AsyncMock)
def test_stt_stream_transcribes_ordered_browser_opus_chunks(
    mock_transcribe: AsyncMock,
    client: TestClient,
) -> None:
    mock_transcribe.return_value = {"text": "hello stream", "confidence": 0.91, "latency_ms": 123}

    with client.websocket_connect("/api/stt/stream") as ws:
        ws.send_json(_browser_opus_start())
        ready = ws.receive_json()
        warning = ws.receive_json()

        ws.send_bytes(b"\x1a\x45\xdf\xa3" + b"\x00" * 256)
        ws.send_bytes(b"\x01" * 128)
        ws.send_json({"type": "stop", "reason": "user_stopped"})
        closed = ws.receive_json()

    assert ready["type"] == "ready"
    assert ready["audio"]["container"] == "webm"
    assert warning["type"] == "warning"
    assert warning["code"] == "interim_results_unavailable"
    assert closed["type"] == "closed"
    assert closed["reason"] == "stream_complete"
    assert closed["final_text"] == "hello stream"
    mock_transcribe.assert_awaited_once()
    assert mock_transcribe.await_args.args == (b"\x1a\x45\xdf\xa3" + b"\x00" * 256 + b"\x01" * 128, "audio/webm;codecs=opus")
