"""Portable microphone-to-STT WebSocket protocol models."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, Self

from pydantic import BaseModel, Field, model_validator

MAX_BINARY_FRAME_SIZE_BYTES = 256 * 1024


class AudioCodec(str, Enum):
    """Supported live audio codecs."""

    OPUS = "opus"
    PCM_S16LE = "pcm_s16le"


class AudioContainer(str, Enum):
    """Supported live audio containers."""

    WEBM = "webm"
    OGG = "ogg"
    RAW = "raw"


class ClientPlatform(str, Enum):
    """Client platform labels for STT telemetry and fallback decisions."""

    BROWSER = "browser"
    ANDROID = "android"
    LINUX = "linux"
    UNKNOWN = "unknown"


class ControlMessageType(str, Enum):
    """Client control message types."""

    START = "start"
    STOP = "stop"
    PING = "ping"


class ServerMessageType(str, Enum):
    """Server control message types."""

    READY = "ready"
    TRANSCRIPT = "transcript"
    WARNING = "warning"
    ERROR = "error"
    CLOSED = "closed"


class SttAudioConfig(BaseModel):
    """Audio metadata supplied by the client before binary chunks."""

    codec: AudioCodec
    container: AudioContainer
    mime_type: str
    channels: int = Field(default=1, ge=1)
    target_bitrate_bps: int | None = Field(default=None, ge=1)
    chunk_duration_ms: int | None = Field(default=None, ge=1)
    sample_rate_hz: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_codec_container_pair(self) -> Self:
        """Require codec/container combinations that the server can route explicitly."""
        if self.codec is AudioCodec.OPUS:
            if self.container not in {AudioContainer.WEBM, AudioContainer.OGG}:
                raise ValueError("codec=opus requires container=webm or container=ogg")
            if self.container is AudioContainer.WEBM and self.mime_type not in {
                "audio/webm;codecs=opus",
                "audio/webm",
            }:
                raise ValueError("webm opus audio requires audio/webm;codecs=opus or audio/webm")
            if self.container is AudioContainer.OGG and self.mime_type not in {
                "audio/ogg;codecs=opus",
                "audio/ogg",
            }:
                raise ValueError("ogg opus audio requires audio/ogg;codecs=opus or audio/ogg")
            return self

        if self.container is not AudioContainer.RAW:
            raise ValueError("codec=pcm_s16le requires container=raw")
        if self.sample_rate_hz is None:
            raise ValueError("codec=pcm_s16le requires sample_rate_hz")
        if self.mime_type != "audio/L16":
            raise ValueError("raw pcm_s16le audio requires audio/L16")
        return self


class SttOptions(BaseModel):
    """STT provider options supplied in the start message."""

    language: str = Field(min_length=1)
    interim_results: bool = True
    provider: str = "default"


class SttClientInfo(BaseModel):
    """Client metadata supplied in the start message."""

    platform: ClientPlatform = ClientPlatform.UNKNOWN
    sdk_version: str = "unknown"


class SttStartMessage(BaseModel):
    """Initial client message for a live STT WebSocket session."""

    type: Literal["start"]
    audio: SttAudioConfig
    stt: SttOptions
    client: SttClientInfo = Field(default_factory=SttClientInfo)


class SttStopMessage(BaseModel):
    """Client request to flush the provider stream and close the session."""

    type: Literal["stop"]
    reason: str = "user_stopped"


class SttPingMessage(BaseModel):
    """Client keepalive message."""

    type: Literal["ping"]


@dataclass(frozen=True)
class SttProviderRoute:
    """Provider routing details for a validated STT stream."""

    name: str
    mime_type: str
    provider_request: dict[str, Any]


def select_stt_provider_route(audio: SttAudioConfig) -> SttProviderRoute:
    """Select the provider route from explicit codec/container metadata."""
    if audio.codec is AudioCodec.OPUS and audio.container is AudioContainer.WEBM:
        return SttProviderRoute(
            name="direct_opus_webm",
            mime_type=audio.mime_type,
            provider_request={"mime_type": audio.mime_type},
        )

    if audio.codec is AudioCodec.OPUS and audio.container is AudioContainer.OGG:
        return SttProviderRoute(
            name="direct_opus_ogg",
            mime_type=audio.mime_type,
            provider_request={"mime_type": audio.mime_type},
        )

    if audio.codec is AudioCodec.PCM_S16LE and audio.container is AudioContainer.RAW:
        return SttProviderRoute(
            name="pcm_raw",
            mime_type=audio.mime_type,
            provider_request={
                "mime_type": audio.mime_type,
                "encoding": audio.codec.value,
                "sample_rate_hz": audio.sample_rate_hz,
                "channels": audio.channels,
            },
        )

    raise ValueError(f"Unsupported STT audio route: {audio.codec.value}/{audio.container.value}")


def validate_first_audio_chunk(audio: SttAudioConfig, chunk: bytes) -> None:
    """Verify the first binary chunk matches the declared container signature."""
    if audio.codec is not AudioCodec.OPUS:
        return

    expected_signature = b"\x1a\x45\xdf\xa3" if audio.container is AudioContainer.WEBM else b"OggS"
    if len(chunk) < len(expected_signature) or not chunk.startswith(expected_signature):
        raise ValueError(f"Declared {audio.container.value} container does not match first chunk container signature")
