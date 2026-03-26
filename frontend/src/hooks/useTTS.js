import { useState, useCallback, useRef } from 'react';
import BASE from '../utils/basePath';

const SILENT_WAV_DATA_URI = 'data:audio/wav;base64,UklGRiYAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQIAAAAAAA==';

/**
 * Build a WAV file (Blob) from raw PCM 16-bit LE mono samples.
 */
function pcmToWavBlob(pcmData, sampleRate) {
  const wavHeader = 44;
  const buffer = new ArrayBuffer(wavHeader + pcmData.byteLength);
  const view = new DataView(buffer);

  // RIFF header
  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + pcmData.byteLength, true);
  writeString(view, 8, 'WAVE');

  // fmt sub-chunk
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);           // sub-chunk size
  view.setUint16(20, 1, true);            // PCM format
  view.setUint16(22, 1, true);            // mono
  view.setUint32(24, sampleRate, true);    // sample rate
  view.setUint32(28, sampleRate * 2, true); // byte rate
  view.setUint16(32, 2, true);            // block align
  view.setUint16(34, 16, true);           // bits per sample

  // data sub-chunk
  writeString(view, 36, 'data');
  view.setUint32(40, pcmData.byteLength, true);

  // Copy PCM data
  new Uint8Array(buffer, wavHeader).set(new Uint8Array(pcmData));

  return new Blob([buffer], { type: 'audio/wav' });
}

function writeString(view, offset, str) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i));
  }
}

export default function useTTS(onSpeakingDone) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const abortRef = useRef(null);
  const audioElRef = useRef(null);
  const audioUrlRef = useRef(null);
  const unlockedRef = useRef(false);

  const getAudioElement = useCallback(() => {
    if (!audioElRef.current) {
      const audio = new Audio();
      audio.preload = 'auto';
      audio.playsInline = true;
      audioElRef.current = audio;
    }
    return audioElRef.current;
  }, []);

  const clearAudioElement = useCallback(() => {
    if (audioElRef.current) {
      audioElRef.current.onended = null;
      audioElRef.current.onerror = null;
      audioElRef.current.pause();
      audioElRef.current.removeAttribute('src');
      audioElRef.current.load();
    }
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }
  }, []);

  const stop = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    clearAudioElement();
    setIsSpeaking(false);
  }, [clearAudioElement]);

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
   * Play a WAV blob via an <audio> element — the most reliable cross-platform
   * approach, especially on mobile browsers that restrict AudioContext.
   */
  const playWavBlob = useCallback((wavBlob) => {
    const url = URL.createObjectURL(wavBlob);
    const audio = getAudioElement();

    clearAudioElement();
    audioUrlRef.current = url;
    audio.muted = false;
    audio.volume = 1;
    audio.src = url;

    audio.onended = () => {
      clearAudioElement();
      setIsSpeaking(false);
      onSpeakingDone?.();
    };
    audio.onerror = () => {
      console.warn('Audio element playback failed');
      clearAudioElement();
      setIsSpeaking(false);
      onSpeakingDone?.();
    };

    audio.play().catch((err) => {
      console.warn('Audio play() rejected:', err);
      clearAudioElement();
      setIsSpeaking(false);
      onSpeakingDone?.();
    });
  }, [clearAudioElement, getAudioElement, onSpeakingDone]);

  /**
   * Fetch PCM from a ReadableStream, convert to WAV, and play via <audio>.
   */
  const playFromStream = useCallback(async (audioStream, sampleRate, signal) => {
    if (!audioStream) {
      setIsSpeaking(false);
      onSpeakingDone?.();
      return;
    }

    try {
      // Collect all PCM chunks into a single buffer
      const reader = audioStream.getReader();
      const chunks = [];
      let totalLength = 0;

      while (true) {
        if (signal?.aborted) return;
        const { done, value } = await reader.read();
        if (done) break;
        if (value && value.byteLength > 0) {
          chunks.push(value);
          totalLength += value.byteLength;
        }
      }

      if (signal?.aborted) return;
      if (totalLength === 0) {
        setIsSpeaking(false);
        onSpeakingDone?.();
        return;
      }

      // Merge chunks
      const pcmData = new Uint8Array(totalLength);
      let offset = 0;
      for (const chunk of chunks) {
        pcmData.set(chunk, offset);
        offset += chunk.byteLength;
      }

      // Ensure even byte count (PCM 16-bit)
      const evenLength = pcmData.byteLength & ~1;
      const wavBlob = pcmToWavBlob(pcmData.slice(0, evenLength).buffer, sampleRate);
      playWavBlob(wavBlob);
    } catch (err) {
      if (err.name === 'AbortError') return;
      console.warn('Stream-to-WAV playback failed:', err);
      setIsSpeaking(false);
      onSpeakingDone?.();
    }
  }, [onSpeakingDone, playWavBlob]);

  /**
   * Fetch PCM as a single ArrayBuffer (no streaming), convert to WAV, and play.
   * More reliable on mobile browsers that don't support ReadableStream well.
   */
  const fetchAndPlayWav = useCallback(async (text, tier, signal) => {
    try {
      const res = await fetch(`${BASE}/api/tts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, tier }),
        signal,
      });
      if (signal?.aborted) return;
      if (res.status === 204 || !res.ok) {
        fallbackSpeak(text);
        return;
      }
      const sampleRate = parseInt(res.headers.get('X-Sample-Rate') || '24000', 10);
      const pcmBuffer = await res.arrayBuffer();
      if (signal?.aborted) return;
      if (pcmBuffer.byteLength < 2) {
        fallbackSpeak(text);
        return;
      }
      const evenLength = pcmBuffer.byteLength & ~1;
      const wavBlob = pcmToWavBlob(pcmBuffer.slice(0, evenLength), sampleRate);
      playWavBlob(wavBlob);
    } catch (err) {
      if (err.name === 'AbortError') return;
      console.warn('TTS fetch failed, using browser speech:', err);
      fallbackSpeak(text);
    }
  }, [fallbackSpeak, playWavBlob]);

  /**
   * Speak text using /api/tts — fetches full PCM, converts to WAV, plays via <audio>.
   */
  const speak = useCallback(async (text, tier) => {
    if (!text) return;

    stop();
    setIsSpeaking(true);

    const controller = new AbortController();
    abortRef.current = controller;

    await fetchAndPlayWav(text, tier, controller.signal);
  }, [stop, fetchAndPlayWav]);

  /**
   * Play audio from an already-available ReadableStream (from /api/turn-speak).
   * Collects the stream into a WAV blob and plays via <audio>.
   */
  const speakFromStream = useCallback(async (audioStream, sampleRate) => {
    stop();
    setIsSpeaking(true);

    const controller = new AbortController();
    abortRef.current = controller;

    await playFromStream(audioStream, sampleRate, controller.signal);
  }, [stop, playFromStream]);

  const unlock = useCallback(() => {
    if (unlockedRef.current) {
      return;
    }

    try {
      const audio = getAudioElement();
      audio.muted = true;
      audio.volume = 0;
      audio.src = SILENT_WAV_DATA_URI;

      const playPromise = audio.play();
      if (playPromise?.then) {
        playPromise
          .then(() => {
            audio.pause();
            audio.currentTime = 0;
            audio.removeAttribute('src');
            audio.load();
            audio.muted = false;
            audio.volume = 1;
            unlockedRef.current = true;
          })
          .catch(() => { });
      }
    } catch {
      // Best effort only — fallback speech still exists if this fails.
    }
  }, [getAudioElement]);

  return { isSpeaking, speak, speakFromStream, stop, unlock };
}
