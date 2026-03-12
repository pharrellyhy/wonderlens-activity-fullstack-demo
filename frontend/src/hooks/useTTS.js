import { useState, useCallback, useRef } from 'react';
import { synthesizeSpeechStream } from '../utils/api';

export default function useTTS(onSpeakingDone) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const abortRef = useRef(null);
  const ctxRef = useRef(null);
  const sourceRef = useRef(null);

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
    if (sourceRef.current) {
      sourceRef.current.onended = null;
      sourceRef.current.stop();
      sourceRef.current = null;
    }
    if (ctxRef.current) {
      ctxRef.current.close();
      ctxRef.current = null;
    }
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

      const { stream, sampleRate } = result;
      const reader = stream.getReader();

      // Collect all PCM chunks, then play as one continuous buffer
      const chunks = [];
      let totalBytes = 0;

      while (true) {
        if (controller.signal.aborted) return;
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
        totalBytes += value.byteLength;
      }

      if (controller.signal.aborted || totalBytes === 0) {
        if (totalBytes === 0) fallbackSpeak(text);
        return;
      }

      // Concatenate all chunks into a single PCM buffer
      const pcmBytes = new Uint8Array(totalBytes);
      let offset = 0;
      for (const chunk of chunks) {
        pcmBytes.set(chunk, offset);
        offset += chunk.byteLength;
      }

      // Convert PCM 16-bit LE to Float32
      const pcm16 = new Int16Array(pcmBytes.buffer, pcmBytes.byteOffset, pcmBytes.byteLength >> 1);
      const float32 = new Float32Array(pcm16.length);
      for (let i = 0; i < pcm16.length; i++) {
        float32[i] = pcm16[i] / 32768;
      }

      // Play as a single AudioBuffer — no chunk boundary noise
      const ctx = getAudioContext(sampleRate);
      const buffer = ctx.createBuffer(1, float32.length, sampleRate);
      buffer.getChannelData(0).set(float32);

      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);
      sourceRef.current = source;

      source.onended = () => {
        sourceRef.current = null;
        setIsSpeaking(false);
        onSpeakingDone?.();
      };

      source.start();
    } catch (err) {
      if (err.name === 'AbortError') return;
      fallbackSpeak(text);
    }
  }, [stop, getAudioContext, fallbackSpeak, onSpeakingDone]);

  return { isSpeaking, speak, stop };
}
