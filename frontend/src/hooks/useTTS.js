import { useState, useCallback, useRef } from 'react';
import { synthesizeSpeechStream } from '../utils/api';

export default function useTTS(onSpeakingDone) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const abortRef = useRef(null);
  const ctxRef = useRef(null);
  const scheduledEndRef = useRef(0);
  const lastSourceRef = useRef(null);

  const getAudioContext = useCallback((sampleRate) => {
    if (ctxRef.current && ctxRef.current.sampleRate === sampleRate) {
      return ctxRef.current;
    }
    if (ctxRef.current) {
      ctxRef.current.close();
    }
    ctxRef.current = new AudioContext({ sampleRate });
    return ctxRef.current;
  }, []);

  const stop = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    if (lastSourceRef.current) {
      lastSourceRef.current.onended = null;
      lastSourceRef.current.stop();
      lastSourceRef.current = null;
    }
    if (ctxRef.current) {
      ctxRef.current.close();
      ctxRef.current = null;
    }
    scheduledEndRef.current = 0;
    setIsSpeaking(false);
  }, []);

  const fallbackSpeak = useCallback((text) => {
    if (!window.speechSynthesis) {
      setIsSpeaking(false);
      onSpeakingDone?.();
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    utterance.pitch = 1.1;
    utterance.onend = () => {
      setIsSpeaking(false);
      onSpeakingDone?.();
    };
    utterance.onerror = () => {
      setIsSpeaking(false);
      onSpeakingDone?.();
    };
    window.speechSynthesis.speak(utterance);
  }, [onSpeakingDone]);

  /**
   * Schedule a PCM chunk for seamless playback at the correct time offset.
   * Returns the AudioBufferSourceNode for the chunk.
   */
  const scheduleChunk = useCallback((ctx, float32Data) => {
    const buffer = ctx.createBuffer(1, float32Data.length, ctx.sampleRate);
    buffer.getChannelData(0).set(float32Data);

    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);

    // Schedule at the end of the previous chunk (or now for the first)
    const startAt = Math.max(ctx.currentTime, scheduledEndRef.current);
    source.start(startAt);
    scheduledEndRef.current = startAt + buffer.duration;

    return source;
  }, []);

  /**
   * Convert raw PCM 16-bit LE bytes to Float32 samples.
   */
  const pcmToFloat32 = useCallback((pcmBytes) => {
    const pcm16 = new Int16Array(
      pcmBytes.buffer, pcmBytes.byteOffset, pcmBytes.byteLength >> 1,
    );
    const float32 = new Float32Array(pcm16.length);
    for (let i = 0; i < pcm16.length; i++) {
      float32[i] = pcm16[i] / 32768;
    }
    return float32;
  }, []);

  /**
   * Play audio progressively from a ReadableStream of PCM chunks.
   * Each chunk is scheduled seamlessly after the previous one — no gaps, no noise.
   * Audio starts playing as soon as the first chunk arrives (low TTFA).
   */
  const playStream = useCallback(async (audioStream, sampleRate, signal) => {
    if (!audioStream) {
      setIsSpeaking(false);
      onSpeakingDone?.();
      return;
    }

    const ctx = getAudioContext(sampleRate);
    scheduledEndRef.current = 0;
    const reader = audioStream.getReader();
    let lastSource = null;
    let leftover = null; // carry odd trailing byte across chunks

    try {
      while (true) {
        if (signal?.aborted) return;
        const { done, value } = await reader.read();
        if (done) {
          // Flush any remaining leftover (single byte — discard, can't form a sample)
          break;
        }
        if (!value || value.byteLength === 0) continue;

        // Prepend leftover byte from previous chunk to maintain 2-byte PCM alignment
        let chunk = value;
        if (leftover) {
          const merged = new Uint8Array(leftover.byteLength + chunk.byteLength);
          merged.set(leftover);
          merged.set(chunk, leftover.byteLength);
          chunk = merged;
          leftover = null;
        }

        // If odd number of bytes, save the last byte for next iteration
        if (chunk.byteLength % 2 !== 0) {
          leftover = chunk.slice(-1);
          chunk = chunk.slice(0, -1);
        }

        if (chunk.byteLength < 2) continue;

        const float32 = pcmToFloat32(chunk);
        lastSource = scheduleChunk(ctx, float32);
        lastSourceRef.current = lastSource;
      }

      // Set onended callback on the very last scheduled source
      if (lastSource) {
        lastSource.onended = () => {
          lastSourceRef.current = null;
          setIsSpeaking(false);
          onSpeakingDone?.();
        };
      } else {
        setIsSpeaking(false);
        onSpeakingDone?.();
      }
    } catch (err) {
      if (err.name === 'AbortError') return;
      console.warn('Progressive playback failed:', err);
      setIsSpeaking(false);
      onSpeakingDone?.();
    }
  }, [getAudioContext, onSpeakingDone, pcmToFloat32, scheduleChunk]);

  /**
   * Speak text using /api/tts with progressive playback.
   * Used for the first turn (from /api/start) and as fallback.
   */
  const speak = useCallback(async (text, tier) => {
    if (!text) return;

    stop();
    setIsSpeaking(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const result = await synthesizeSpeechStream(text, tier);
      if (!result || !result.stream) {
        fallbackSpeak(text);
        return;
      }

      await playStream(result.stream, result.sampleRate, controller.signal);
    } catch (err) {
      if (err.name === 'AbortError') return;
      fallbackSpeak(text);
    }
  }, [stop, fallbackSpeak, playStream]);

  /**
   * Play audio from an already-available stream (from /api/turn-speak).
   * Skips the separate /api/tts call entirely.
   */
  const speakFromStream = useCallback(async (audioStream, sampleRate) => {
    stop();
    setIsSpeaking(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      await playStream(audioStream, sampleRate, controller.signal);
    } catch (err) {
      if (err.name === 'AbortError') return;
      setIsSpeaking(false);
      onSpeakingDone?.();
    }
  }, [stop, playStream, onSpeakingDone]);

  return { isSpeaking, speak, speakFromStream, stop };
}
