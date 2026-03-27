# Plan: Streaming OGG/Opus TTS Playback

## Context

The current OGG/Opus TTS pipeline is batch: collect all PCM from Gemini, encode the entire buffer to OGG/Opus, return complete file. Audio doesn't start until TTS is fully complete (~3-5s). Chrome's `<audio>` element supports progressive playback of chunked OGG — it starts decoding and playing as OGG pages arrive, before the full response finishes.

Target: Chrome only (desktop + Android). Native Android apps also support OGG/Opus streaming natively.

## Approach

Encode OGG/Opus incrementally on the backend: as PCM chunks arrive from Gemini TTS, encode them to Opus frames and mux into OGG pages. Stream the OGG bytes to the frontend via chunked HTTP. The `<audio>` element plays progressively — first audio heard within ~200ms of first Gemini chunk.

Key insight: PyAV can encode Opus frames incrementally. Each `stream.encode(frame)` + `output.mux(pkt)` writes complete OGG pages to the output buffer. We flush these pages to the HTTP response as they're produced.

## Changes

### Step 1: Add streaming OGG encoder to `backend/tts.py`

New async generator `synthesize_speech_ogg_stream_async(text, tier)`:
- Opens an in-memory OGG container via `av.open(BytesIO(), mode='w', format='ogg')`
- Calls `synthesize_speech_stream_async()` to get PCM chunks
- Accumulates PCM into a buffer; when buffer reaches ≥960 samples (one Opus frame at 24kHz = 40ms), encodes a frame
- After each encode, checks if BytesIO has new bytes; yields the delta
- On stream end, flushes remaining PCM + encoder, yields final bytes
- Yields `(chunk_bytes, is_header)` tuples — first yield includes OGG header pages
- Track total PCM bytes for the indicator

### Step 2: Update `/api/tts` endpoint

Change from batch `Response` to `StreamingResponse`:
```python
@app.post("/api/tts")
async def text_to_speech(req: TTSRequest) -> Response:
    return StreamingResponse(
        synthesize_speech_ogg_stream_async(req.text, req.tier),
        media_type="audio/ogg",
    )
```

Keep the `X-PCM-Size` header approach: since we don't know total PCM size upfront with streaming, either:
- (a) Drop PCM size from streaming path — indicator shows format + encoded size only
- (b) Add a trailing header (not standard)
- (c) Frontend estimates PCM from duration × sample_rate × 2

Go with (a) for simplicity. The indicator shows `OGG/Opus · streaming · 15.3 KB` during playback.

### Step 3: Update `/api/turn-speak` endpoint

The binary protocol stays: `[4-byte JSON len][JSON][audio bytes...]`

But audio bytes are now streamed OGG pages instead of a complete file. The `_stream()` generator:
1. Resolves the turn, yields JSON header
2. Yields OGG/Opus chunks as they arrive from the streaming encoder

### Step 4: Update frontend `useTTS.js` — progressive `<audio>` playback

For the `/api/tts` path (`fetchAndPlayAudio`):
- Use `fetch()` and set `audio.src` to a `URL.createObjectURL(mediaSource)` or simply pipe to a blob URL
- Actually simpler: use `audio.src = url` with the fetch URL directly — Chrome's `<audio>` handles chunked OGG natively when loaded via URL
- Problem: `<audio src>` needs a URL, not a ReadableStream

Two sub-approaches:

**(A) Direct URL**: Change `/api/tts` to accept GET with query params, set `audio.src = '/api/tts?text=...&tier=T0'`. Chrome streams and plays. Simplest, but exposes text in URL.

**(B) Blob accumulation with early play**: Fetch via POST, accumulate chunks into a growing Blob, create/revoke object URLs as chunks arrive. `<audio>` sees the Blob URL but only has partial data — Chrome may or may not handle this.

**(C) MediaSource Extensions**: Create MediaSource, get SourceBuffer. Problem: MSE doesn't support `audio/ogg; codecs=opus` in Chrome. Only `audio/webm; codecs=opus` is supported in MSE.

**(D) Web Audio API with Opus decoding**: Decode OGG/Opus chunks manually... too complex.

**(E) Hybrid — stream PCM to Web Audio, encode OGG in parallel for download**: Over-engineered.

**Decision: Go with (A) — GET endpoint for streaming playback.**

Add `GET /api/tts?text=...&tier=T0` that returns `StreamingResponse` with `audio/ogg`. The `<audio>` element can load this URL directly and Chrome will progressively play.

For the `/api/turn-speak` path (`playFromStream`):
- The audio bytes come embedded in the binary response, not as a standalone URL
- Collect all OGG bytes from the stream (they arrive faster now due to chunking), create blob, play
- This path is already fast since turn resolution + TTS happen concurrently on the backend
- Progressive improvement: use a ServiceWorker to proxy the stream as a URL for `<audio>` — defer for now

### Step 5: Update audio indicator

- Streaming `/api/tts` path: `audio.src` is a direct URL, so we get duration from `loadedmetadata`. Show `OGG/Opus · streaming · {duration}s`. Encoded size available after `loadend` event.
- Binary `/api/turn-speak` path: same as today (blob URL), show format + size + PCM size.

---

## Files to Modify

| File | Change |
|------|--------|
| `backend/tts.py` | Add `synthesize_speech_ogg_stream_async()` streaming encoder |
| `backend/server.py` | Add `GET /api/tts` streaming endpoint; update `POST /api/turn-speak` to stream OGG |
| `frontend/src/hooks/useTTS.js` | Use direct URL for streaming `<audio>` playback on `/api/tts` path |

## Verification

```bash
# Backend: verify chunked OGG streaming
curl -N -s http://localhost:8000/api/tts?text=Hello&tier=T0 | head -c 100 | xxd | head -3
# Should show OggS magic bytes arriving immediately

# Frontend: open Chrome, start session, verify audio starts playing
# before the TTS loading indicator disappears (audio overlaps with generation)
# Check DevTools Network: /api/tts response should show "streaming" transfer
```
