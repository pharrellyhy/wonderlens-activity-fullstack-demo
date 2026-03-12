# Streaming TTS Plan

## Problem
TTS latency is 6-30s because the backend waits for the full Gemini TTS response before sending anything to the frontend. The frontend can't play audio until the entire WAV is received.

## Solution
Stream PCM audio chunks from backend to frontend as they arrive from Gemini, and play them incrementally using Web Audio API.

### Backend Changes (`tts.py` + `server.py`)
1. Add `synthesize_speech_stream()` generator that uses `generate_content_stream` and yields raw PCM chunks as they arrive
2. Change `/api/tts` endpoint to use FastAPI `StreamingResponse` with `media_type="audio/pcm"` and add sample rate in a custom header

### Frontend Changes (`api.js` + `useTTS.js`)
1. `synthesizeSpeech()` returns a `ReadableStream` reader instead of a blob
2. `useTTS` uses `AudioContext` to decode and play PCM chunks progressively:
   - Create AudioContext with 24kHz sample rate
   - Read chunks from the stream
   - Convert PCM16 to Float32 samples
   - Queue AudioBufferSourceNodes back-to-back for gapless playback
