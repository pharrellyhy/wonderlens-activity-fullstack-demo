# Portable Opus STT Streaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable low-bandwidth microphone-to-STT streaming path using Opus for browser, Android, and Linux clients.

**Architecture:** Clients encode microphone audio to Opus and send ordered binary chunks over one WebSocket session. The server treats codec/container as an explicit session property, forwards supported Opus streams directly to the STT provider, and falls back to PCM only when Opus capture or provider ingest is unavailable.

**Tech Stack:** WebSocket, Opus, WebM, Ogg, browser `MediaRecorder`, Android `MediaRecorder` / `AudioRecord`, Linux GStreamer or libopus/libopusenc.

**Repo implementation status (2026-05-08):** Browser target is implemented for this repo. The frontend now prefers browser `MediaRecorder` Opus over `WS /api/stt/stream`, then falls back to the existing batch `POST /api/stt` path and finally browser Web Speech. The backend validates the shared protocol and returns a final transcript on `stop` through the current Gemini batch STT helper. Android, Linux, true provider-live interim transcripts, and server-side Opus-to-PCM transcoding remain future work.

---

## Non-Repo-Specific Scope

This document is intentionally portable. It does not assume a specific Python, Node, Kotlin, or C++ backend. It defines the protocol, client capture strategy, server responsibilities, verification steps, and fallback rules that can be implemented in any repo.

The core recommendation is:

1. Browser clients: prefer `audio/webm;codecs=opus`, fallback to `audio/ogg;codecs=opus`, then PCM.
2. Android clients: prefer Ogg/Opus with `MediaRecorder` on API 29+, fallback to `AudioRecord` + libopus/libopusenc, then PCM.
3. Linux devices: prefer GStreamer `opusenc ! oggmux`, fallback to libopus/libopusenc, then PCM.
4. Server: use direct Opus provider ingest when available; otherwise transcode Opus to PCM near the server edge.

## Why Opus

Raw PCM is simple but expensive:

- 16 kHz mono LINEAR16: about 256 kbps before transport overhead.
- Opus speech: commonly 16-32 kbps.

For mobile, browser, and embedded devices, Opus usually reduces upstream audio bandwidth by roughly 8-16x while preserving speech quality for STT.

## Protocol Contract

Use one WebSocket per live STT session.

### Initial JSON Message

The first client message must be JSON:

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

Allowed audio values:

```text
codec: opus | pcm_s16le
container: webm | ogg | raw
mime_type:
  audio/webm;codecs=opus
  audio/ogg;codecs=opus
  audio/ogg
  audio/L16
```

Do not infer the stream format only from file extensions or magic bytes. Use the explicit `start.audio` metadata as the source of truth, then optionally verify the first binary chunk starts with the expected container signature:

- WebM / Matroska: `1A 45 DF A3`
- Ogg: `4F 67 67 53` (`OggS`)

### Binary Audio Messages

After `start`, every binary WebSocket frame is a chunk from the same continuous encoded stream. Chunks must be sent in capture order. Do not base64 encode live audio frames.

The server must preserve byte order and session continuity. For containerized streams, the first chunk normally carries container headers; reconnects must start a new STT provider stream or send a fresh container header.

### Stop Message

Client sends:

```json
{
  "type": "stop",
  "reason": "user_stopped"
}
```

Server then flushes the provider stream, waits for final transcripts, and sends:

```json
{
  "type": "closed",
  "reason": "stream_complete",
  "final_text": "..."
}
```

## Server Ingest Design

### Responsibilities

- Authenticate before accepting audio.
- Read and validate the `start` message before opening the provider stream.
- Route by `(codec, container)`, not by client platform.
- Forward Opus streams directly if the STT provider accepts the container.
- Transcode to PCM only when direct provider ingest is unavailable.
- Apply bounded queues and close slow sessions rather than buffering indefinitely.

### Provider Adapter Rules

Direct Opus forwarding:

```text
client WebSocket binary chunks
  -> server session queue
  -> STT provider live WebSocket/request body
  -> transcript events back to client
```

For containerized Opus, do not send raw-audio parameters such as `encoding=linear16` or `sample_rate=16000` unless the provider explicitly asks for them. Those parameters describe headerless PCM-style streams and can cause a provider to decode Opus bytes incorrectly.

For providers that only accept PCM:

```text
client Opus chunks
  -> server Ogg/WebM demux + Opus decode
  -> PCM frames
  -> STT provider PCM stream
```

Preferred server-side transcode tools:

- GStreamer pipeline in a worker process for long-lived device sessions.
- FFmpeg process for simpler prototypes and test tools.
- Native libopus demux/decode only when latency and resource control justify the extra code.

### Suggested Server State Machine

```text
CONNECTING
  -> WAITING_FOR_START
  -> PROVIDER_CONNECTING
  -> STREAMING
  -> FLUSHING
  -> CLOSED
```

Reject these cases early:

- Missing `start` before binary audio.
- Unsupported `(codec, container)` pair.
- Container mismatch between metadata and first bytes.
- Chunk larger than the configured max, for example 256 KiB.
- Session longer than max duration.
- Audio queue above max depth for more than a short grace period.

## Browser Client

### Recommended Path

Use `MediaRecorder` with feature detection:

```js
function chooseOpusMimeType() {
  return [
    "audio/webm;codecs=opus",
    "audio/ogg;codecs=opus",
    "audio/webm",
    "audio/ogg",
  ].find((type) => MediaRecorder.isTypeSupported(type));
}

async function startBrowserOpusStream(wsUrl) {
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });

  const mimeType = chooseOpusMimeType();
  if (!mimeType) {
    throw new Error("Opus MediaRecorder is not supported on this browser");
  }

  const ws = new WebSocket(wsUrl);
  ws.binaryType = "arraybuffer";

  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = reject;
  });

  const container = mimeType.includes("ogg") ? "ogg" : "webm";
  ws.send(JSON.stringify({
    type: "start",
    audio: {
      codec: "opus",
      container,
      mime_type: mimeType,
      channels: 1,
      target_bitrate_bps: 24000,
      chunk_duration_ms: 100,
    },
    stt: {
      language: "en-US",
      interim_results: true,
      provider: "default",
    },
    client: {
      platform: "browser",
      sdk_version: "1.0.0",
    },
  }));

  const recorder = new MediaRecorder(stream, {
    mimeType,
    audioBitsPerSecond: 24000,
  });

  recorder.ondataavailable = async (event) => {
    if (event.data.size === 0 || ws.readyState !== WebSocket.OPEN) return;
    ws.send(await event.data.arrayBuffer());
  };

  recorder.start(100);

  return {
    stop() {
      if (recorder.state !== "inactive") recorder.stop();
      stream.getTracks().forEach((track) => track.stop());
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "stop", reason: "user_stopped" }));
      }
    },
  };
}
```

### Browser Notes

- `MediaRecorder.start(timeslice)` emits chunks periodically, but browsers do not guarantee exact timing.
- Do not assume every chunk is independently playable. Treat chunks as pieces of one continuous container stream.
- Prefer 100 ms chunks for interactive STT. Use 200-250 ms if battery and bandwidth overhead matter more than first-transcript latency.
- Keep PCM capture with `AudioWorklet` as the compatibility fallback.

## Android Client

### Recommended Path: API 29+ MediaRecorder Ogg/Opus

Android exposes `MediaRecorder.OutputFormat.OGG` and `MediaRecorder.AudioEncoder.OPUS` on API 29+. Use a pipe so recorder output can be streamed instead of waiting for a complete file.

```kotlin
class AndroidOggOpusStreamer(
    private val webSocket: okhttp3.WebSocket,
    private val language: String = "en-US",
) {
    private var recorder: MediaRecorder? = null
    private var pipe: Array<ParcelFileDescriptor>? = null
    private var readerJob: Job? = null

    fun start(scope: CoroutineScope, context: Context) {
        val (readFd, writeFd) = ParcelFileDescriptor.createPipe()
        pipe = arrayOf(readFd, writeFd)

        webSocket.send("""
          {
            "type": "start",
            "audio": {
              "codec": "opus",
              "container": "ogg",
              "mime_type": "audio/ogg;codecs=opus",
              "channels": 1,
              "target_bitrate_bps": 24000,
              "chunk_duration_ms": 100
            },
            "stt": {
              "language": "$language",
              "interim_results": true,
              "provider": "default"
            },
            "client": {
              "platform": "android",
              "sdk_version": "1.0.0"
            }
          }
        """.trimIndent())

        recorder = createRecorder(context).apply {
            setAudioSource(MediaRecorder.AudioSource.VOICE_RECOGNITION)
            setOutputFormat(MediaRecorder.OutputFormat.OGG)
            setAudioEncoder(MediaRecorder.AudioEncoder.OPUS)
            setAudioChannels(1)
            setAudioEncodingBitRate(24000)
            setAudioSamplingRate(48000)
            setOutputFile(writeFd.fileDescriptor)
            prepare()
            start()
        }

        readerJob = scope.launch(Dispatchers.IO) {
            ParcelFileDescriptor.AutoCloseInputStream(readFd).use { input ->
                val buffer = ByteArray(4096)
                while (isActive) {
                    val n = input.read(buffer)
                    if (n <= 0) break
                    webSocket.send(ByteString.of(buffer, 0, n))
                }
            }
        }
    }

    fun stop() {
        runCatching { recorder?.stop() }
        runCatching { recorder?.release() }
        recorder = null
        readerJob?.cancel()
        pipe?.forEach { runCatching { it.close() } }
        pipe = null
        webSocket.send("""{"type":"stop","reason":"user_stopped"}""")
    }

    private fun createRecorder(context: Context): MediaRecorder {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            MediaRecorder(context)
        } else {
            @Suppress("DEPRECATION")
            MediaRecorder()
        }
    }
}
```

### Android Fallbacks

Use this order:

1. `MediaRecorder` Ogg/Opus on API 29+.
2. `AudioRecord` + native libopus/libopusenc when `MediaRecorder` Opus fails or lower API support is required.
3. PCM WebSocket stream when Opus cannot be created reliably.

`AudioRecord` + libopus/libopusenc gives better control over frame size, bitrate, FEC, DTX, and buffering. It costs more engineering time because you must create valid Ogg pages or define a raw Opus packet protocol and decode/mux on the server.

### Android Verification

- Test on at least one API 29+ physical device.
- Confirm the first bytes sent after `start` are `OggS`.
- Confirm `MediaRecorder.start()` failure falls back cleanly.
- Confirm stop releases mic tracks and file descriptors.
- Measure first interim transcript latency on cellular and Wi-Fi.

## Linux Device Client

### Recommended Path: GStreamer Ogg/Opus

Use GStreamer when available. It handles capture, resampling, Opus encoding, and Ogg muxing without custom codec code.

Example command-line prototype:

```bash
gst-launch-1.0 -q \
  autoaudiosrc ! \
  audioconvert ! \
  audioresample ! \
  audio/x-raw,format=S16LE,rate=48000,channels=1 ! \
  opusenc audio-type=voice bitrate=24000 frame-size=20 bitrate-type=constrained-vbr ! \
  oggmux ! \
  fdsink fd=1
```

In production, use `appsink` and send each buffer over the same WebSocket session after the `start` JSON message.

```text
autoaudiosrc
  -> audioconvert
  -> audioresample
  -> audio/x-raw,format=S16LE,rate=48000,channels=1
  -> opusenc audio-type=voice bitrate=24000 frame-size=20
  -> oggmux
  -> appsink
  -> websocket binary frames
```

### Linux Fallback: libopus/libopusenc

Use libopus directly when the device image cannot include GStreamer.

Encoder settings:

```text
sample_rate: 48000
channels: 1
application: OPUS_APPLICATION_VOIP
frame_duration_ms: 20
bitrate_bps: 16000-32000
complexity: 5-10 depending on CPU budget
inband_fec: disabled initially; enable only after packet loss testing
dtx: disabled initially; enable only after endpointing tests
container: Ogg via libopusenc
```

The Opus encoder must be stateful across the whole stream. Do not recreate the encoder per frame.

## Bitrate and Latency Defaults

Start with these defaults:

```text
channels: mono
opus_bitrate: 24000 bps
client_chunk_duration: 100 ms
opus_frame_duration: 20 ms where configurable
server_queue_limit: 100 chunks
max_binary_frame_size: 256 KiB
max_session_duration: 5 minutes for interactive sessions
```

Tune after measuring:

- 16 kbps: good bandwidth savings, may suffer in noisy rooms.
- 24 kbps: recommended default for child speech / general STT.
- 32 kbps: safer for noisy environments.
- 100 ms chunks: good latency balance.
- 250 ms chunks: lower overhead and battery use, slower first transcript.

## Server Testing Plan

### Unit Tests

- Reject binary audio before `start`.
- Reject unsupported containers, for example `codec=opus`, `container=mp4`.
- Accept `audio/webm;codecs=opus` and route to Opus provider adapter.
- Accept `audio/ogg;codecs=opus` and route to Opus provider adapter.
- Reject mismatched metadata and magic bytes.
- Ensure Opus provider requests do not include PCM-only fields.
- Ensure PCM fallback still includes explicit sample rate and encoding.
- Close session when queue remains full.

### Integration Fixtures

Generate fixtures:

```bash
# Ogg/Opus fixture
gst-launch-1.0 -q \
  audiotestsrc wave=sine num-buffers=100 ! \
  audioconvert ! audioresample ! \
  audio/x-raw,format=S16LE,rate=48000,channels=1 ! \
  opusenc audio-type=voice bitrate=24000 frame-size=20 ! \
  oggmux ! \
  filesink location=test.ogg

# WebM/Opus fixture, if ffmpeg with libopus is available
ffmpeg -f lavfi -i sine=frequency=440:duration=3 \
  -ac 1 -ar 48000 -c:a libopus -b:a 24k test.webm
```

Integration tests:

- Stream fixture chunks over WebSocket in 100 ms slices.
- Assert interim transcript arrives before `stop` when provider supports interim results.
- Assert final transcript arrives after `stop`.
- Assert reconnection starts a new provider session and requires fresh container headers.

### Manual Platform Matrix

Browser:

- Chrome or Edge desktop: WebM/Opus path.
- Firefox desktop: Ogg/Opus and/or WebM/Opus path via feature detection.
- Safari/iOS: feature-detect Opus; use PCM or batch fallback if unsupported.
- Android Chrome: WebM/Opus path.

Android native:

- API 29+ physical phone: `MediaRecorder` Ogg/Opus.
- One low-end device: verify CPU, battery, startup, and stop behavior.
- One failure case: force unsupported encoder and confirm fallback.

Linux:

- Desktop PulseAudio/PipeWire.
- Embedded ALSA-only image.
- Network loss and reconnect test.

## Operational Metrics

Record these per session:

- selected codec/container/mime type
- client platform and SDK version
- upstream audio bytes
- average and p95 chunk size
- queue depth and dropped chunks
- provider connect latency
- time to first interim transcript
- time to final transcript after stop
- close reason
- fallback reason, if used

Use metrics to decide whether to reduce chunk duration, adjust bitrate, or switch specific clients to PCM fallback.

## Security and Resource Limits

- Authenticate before accepting audio.
- Limit max session duration.
- Limit max binary frame size.
- Limit control message size, for example 4 KiB.
- Use bounded queues.
- Drop or close on sustained backpressure.
- Do not store raw mic audio by default.
- If audio must be stored, store the original container with explicit metadata and retention policy.
- Treat MIME type from the client as untrusted; verify first bytes and provider decode success.

## Implementation Tasks

### Task 1: Define the Shared WebSocket Audio Protocol

**Files:**
- Create: `docs/opus-stt-protocol.md`
- Create or modify: backend WebSocket message models in the target repo
- Test: backend protocol/model tests

- [x] **Step 1: Add protocol enums**

Define:

```text
AudioCodec = opus | pcm_s16le
AudioContainer = webm | ogg | raw
ClientPlatform = browser | android | linux | unknown
ControlMessageType = start | stop | ping
ServerMessageType = ready | transcript | warning | error | closed
```

- [x] **Step 2: Add validation rules**

Validation must require:

```text
start.audio.codec is present
start.audio.container is present
start.audio.mime_type is present
start.stt.language is present
binary messages are rejected until start is accepted
codec=pcm_s16le requires container=raw and sample_rate_hz
codec=opus requires container=webm or ogg
```

- [x] **Step 3: Add tests**

Test valid and invalid `start` messages, binary-before-start rejection, and stop handling.

### Task 2: Implement Server Provider Routing

**Files:**
- Modify: backend STT streaming service/provider adapter files in the target repo
- Test: provider routing tests

- [x] **Step 1: Add route selection**

Route by `(codec, container)`:

```text
opus + webm -> direct Opus provider adapter if available
opus + ogg -> direct Opus provider adapter if available
pcm_s16le + raw -> PCM provider adapter
unsupported -> explicit error
```

- [x] **Step 2: Add provider request builders**

For Opus containers, omit PCM-only parameters unless the provider documentation explicitly requires them.

For PCM raw audio, include sample rate, channel count, and encoding.

- [x] **Step 3: Add tests**

Assert WebM/Ogg Opus sessions do not set `encoding=linear16` or equivalent PCM-only fields.

### Task 3: Implement Browser Client

**Files:**
- Create: browser audio client module in the target repo
- Test: browser unit tests and one manual browser test page

- [x] **Step 1: Add MIME feature detection**

Use:

```js
[
  "audio/webm;codecs=opus",
  "audio/ogg;codecs=opus",
  "audio/webm",
  "audio/ogg",
]
```

- [x] **Step 2: Stream MediaRecorder chunks**

Send the `start` JSON first, then `ArrayBuffer` chunks from `dataavailable`, then `stop`.

- [x] **Step 3: Add fallback**

If no Opus MIME type is supported, use PCM capture or batch upload depending on the product's latency requirement.

### Task 4: Implement Android Client

**Files:**
- Create: Android Ogg/Opus streamer class
- Test: Android instrumentation/manual device tests

- [ ] **Step 1: Implement API 29+ MediaRecorder path**

Use:

```text
OutputFormat.OGG
AudioEncoder.OPUS
AudioSource.VOICE_RECOGNITION or MIC
ParcelFileDescriptor pipe
```

- [ ] **Step 2: Add fallback path**

If `prepare()` or `start()` fails, switch to `AudioRecord + libopus/libopusenc` or PCM based on app scope.

- [ ] **Step 3: Verify on device**

Confirm first bytes are `OggS`, transcripts arrive, and stop releases microphone resources.

### Task 5: Implement Linux Client

**Files:**
- Create: Linux capture/streaming module or system service
- Test: Linux fixture and live microphone tests

- [ ] **Step 1: Add GStreamer pipeline**

Use:

```text
autoaudiosrc ! audioconvert ! audioresample ! audio/x-raw,format=S16LE,rate=48000,channels=1 ! opusenc audio-type=voice bitrate=24000 frame-size=20 ! oggmux ! appsink
```

- [ ] **Step 2: Send appsink buffers**

Send each buffer as a binary WebSocket message after `start`.

- [ ] **Step 3: Add libopus fallback only if needed**

Use libopus/libopusenc for device images that cannot ship GStreamer.

### Task 6: Add End-to-End Verification

**Files:**
- Create: integration test fixtures
- Create: manual test checklist
- Modify: CI or smoke test scripts where practical

- [ ] **Step 1: Add Ogg and WebM fixtures**

Generate short speech fixtures, not only sine waves, for real STT verification.

- [ ] **Step 2: Test direct provider ingest**

Stream fixtures over WebSocket and verify interim/final transcripts.

- [ ] **Step 3: Test fallback**

Force Opus unsupported and verify PCM fallback still works.

## References

- MDN `MediaRecorder.isTypeSupported()`: https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/isTypeSupported_static
- MDN `MediaRecorder.dataavailable`: https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/dataavailable_event
- Android `MediaRecorder.OutputFormat`: https://developer.android.com/reference/android/media/MediaRecorder.OutputFormat
- Android `MediaRecorder.AudioEncoder`: https://developer.android.com/reference/android/media/MediaRecorder.AudioEncoder
- GStreamer `opusenc`: https://gstreamer.freedesktop.org/documentation/opus/opusenc.html
- Opus encoder API: https://www.opus-codec.org/docs/opus_api-1.1.3/group__opus__encoder.html
- Deepgram encoding guidance: https://developers.deepgram.com/docs/encoding
