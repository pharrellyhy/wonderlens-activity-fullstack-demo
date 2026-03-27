import { useState, useCallback, useRef } from 'react';
import BASE from '../utils/basePath';

const SILENT_WAV_DATA_URI = 'data:audio/wav;base64,UklGRiYAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQIAAAAAAA==';

export default function useTTS(onSpeakingDone) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [audioInfo, setAudioInfo] = useState(null);
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
    setAudioInfo(null);
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
   * Play an audio blob (OGG/Opus or WAV) via an <audio> element.
   * Browsers natively decode OGG/Opus — no manual header construction needed.
   */
  const playAudioBlob = useCallback((blob, pcmSize = 0) => {
    const format = blob.type.includes('ogg') ? 'OGG/Opus' : blob.type.includes('wav') ? 'WAV' : blob.type;
    const sizeKB = (blob.size / 1024).toFixed(1);
    const pcmSizeKB = pcmSize ? (pcmSize / 1024).toFixed(1) : null;
    setAudioInfo({ format, size: blob.size, sizeKB, pcmSize, pcmSizeKB });

    const url = URL.createObjectURL(blob);
    const audio = getAudioElement();

    clearAudioElement();
    audioUrlRef.current = url;
    audio.muted = false;
    audio.volume = 1;
    audio.src = url;

    audio.onloadedmetadata = () => {
      const duration = audio.duration;
      if (duration && isFinite(duration)) {
        setAudioInfo((prev) => prev ? { ...prev, durationSec: duration.toFixed(1) } : prev);
      }
    };

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
   * Collect OGG/Opus audio from a ReadableStream and play via <audio>.
   * The backend already encodes to OGG/Opus — just collect and play.
   */
  const playFromStream = useCallback(async (audioStream, signal) => {
    if (!audioStream) {
      setIsSpeaking(false);
      onSpeakingDone?.();
      return;
    }

    try {
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

      const blob = new Blob(chunks, { type: 'audio/ogg' });
      playAudioBlob(blob);
    } catch (err) {
      if (err.name === 'AbortError') return;
      console.warn('Stream playback failed:', err);
      setIsSpeaking(false);
      onSpeakingDone?.();
    }
  }, [onSpeakingDone, playAudioBlob]);

  /**
   * Speak text using GET /api/tts — streams OGG/Opus via <audio src> for
   * progressive playback in Chrome. Falls back to browser speech on error.
   */
  const speak = useCallback(async (text, tier) => {
    if (!text) return;

    stop();
    setIsSpeaking(true);
    setAudioInfo({ format: 'OGG/Opus', sizeKB: '...', pcmSize: 0, pcmSizeKB: null, durationSec: null, streaming: true });

    const audio = getAudioElement();
    clearAudioElement();

    const url = `${BASE}/api/tts?text=${encodeURIComponent(text)}&tier=${encodeURIComponent(tier)}`;
    audio.src = url;
    audio.muted = false;
    audio.volume = 1;

    audio.onloadedmetadata = () => {
      const duration = audio.duration;
      if (duration && isFinite(duration)) {
        setAudioInfo((prev) => prev ? { ...prev, durationSec: duration.toFixed(1) } : prev);
      }
    };

    audio.onended = () => {
      clearAudioElement();
      setIsSpeaking(false);
      onSpeakingDone?.();
    };
    audio.onerror = () => {
      console.warn('Streaming audio playback failed, using browser speech');
      clearAudioElement();
      fallbackSpeak(text);
    };

    audio.play().catch(() => {
      clearAudioElement();
      fallbackSpeak(text);
    });
  }, [stop, clearAudioElement, getAudioElement, fallbackSpeak, onSpeakingDone]);

  /**
   * Play audio from an already-available ReadableStream (from /api/turn-speak).
   * The stream contains OGG/Opus data — just collect and play.
   */
  const speakFromStream = useCallback(async (audioStream) => {
    stop();
    setIsSpeaking(true);

    const controller = new AbortController();
    abortRef.current = controller;

    await playFromStream(audioStream, controller.signal);
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

  return { isSpeaking, audioInfo, speak, speakFromStream, stop, unlock };
}
