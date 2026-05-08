# Browser Opus STT WebSocket Protocol

This repo supports browser microphone streaming through `POST /api/stt` as a batch fallback and `WS /api/stt/stream` as the low-bandwidth Opus path.

## Endpoint

```text
ws://<host>/api/stt/stream
wss://<host>/api/stt/stream
```

The frontend builds this URL from the current browser origin and Vite base path.

## Client Start Message

The first WebSocket frame must be JSON:

```json
{
  "type": "start",
  "audio": {
    "codec": "opus",
    "container": "webm",
    "mime_type": "audio/webm;codecs=opus",
    "channels": 1,
    "target_bitrate_bps": 24000,
    "chunk_duration_ms": 100
  },
  "stt": {
    "language": "en-US",
    "interim_results": true,
    "provider": "default"
  },
  "client": {
    "platform": "browser",
    "sdk_version": "1.0.0"
  }
}
```

Supported browser Opus MIME preference order:

```text
audio/webm;codecs=opus
audio/ogg;codecs=opus
audio/webm
audio/ogg
```

The server validates the explicit `codec`, `container`, and `mime_type` values. It also verifies the first binary chunk starts with the declared container signature:

```text
WebM: 1A 45 DF A3
Ogg:  4F 67 67 53
```

## Binary Chunks

After `start` is accepted, every binary frame is treated as the next chunk in the same continuous MediaRecorder container stream. The browser sends chunks in capture order using `MediaRecorder.start(100)`.

Do not base64 encode live audio. Reconnects must open a new WebSocket session and send a fresh `start` message plus fresh container headers.

## Stop Message

To finish capture, the client sends:

```json
{
  "type": "stop",
  "reason": "user_stopped"
}
```

The server concatenates received chunks, calls the current Gemini transcription helper with the declared MIME type, and returns:

```json
{
  "type": "closed",
  "reason": "stream_complete",
  "client_reason": "user_stopped",
  "final_text": "hello stream",
  "confidence": 0.91,
  "latency_ms": 123
}
```

If transcription returns no text, `reason` is `transcription_failed` and `final_text` is empty.

## Server Messages

The server can send:

```text
ready      start was accepted
warning    non-fatal limitation or fallback notice
error      protocol error; server closes after sending
closed     final transcript and close reason
```

This repo's current STT provider path is final-on-stop. When a client requests interim results, the server sends:

```json
{
  "type": "warning",
  "code": "interim_results_unavailable",
  "message": "This provider route returns the final transcript after stop."
}
```

## Rejection Rules

The WebSocket closes early with an `error` payload when:

- Binary audio arrives before `start`.
- `start.audio.codec`, `start.audio.container`, `start.audio.mime_type`, or `start.stt.language` is missing.
- `codec=opus` uses any container other than `webm` or `ogg`.
- `codec=pcm_s16le` does not use `container=raw` with `sample_rate_hz`.
- The first binary chunk does not match the declared WebM/Ogg signature.
- A binary frame exceeds 256 KiB.

## Browser Fallbacks

The React speech hook tries the WebSocket Opus path first. If browser Opus capture or the WebSocket open fails, it falls back to the existing batch upload path (`POST /api/stt`). If that also fails, it uses the browser Web Speech API when available.
