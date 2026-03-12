import { useState, useCallback, useRef } from 'react';
import { synthesizeSpeech } from '../utils/api';

export default function useTTS(onSpeakingDone) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const audioRef = useRef(null);
  const synthRef = useRef(null);
  const audioUrlRef = useRef(null);

  const cleanupAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.onended = null;
      audioRef.current.onerror = null;
      audioRef.current.pause();
      audioRef.current = null;
    }

    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = null;
    }
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
    synthRef.current = utterance;

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

    cleanupAudio();
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(true);

    try {
      // Try server-side TTS first
      const blob = await synthesizeSpeech(text, tier);

      if (blob) {
        // Play WAV from server
        const url = URL.createObjectURL(blob);
        audioUrlRef.current = url;
        const audio = new Audio(url);
        audioRef.current = audio;

        audio.onended = () => {
          cleanupAudio();
          setIsSpeaking(false);
          onSpeakingDone?.();
        };

        audio.onerror = () => {
          cleanupAudio();
          fallbackSpeak(text);
        };

        await audio.play();
        return;
      }
    } catch {
      // Server TTS failed, fall through to browser
    }

    // Browser SpeechSynthesis fallback
    fallbackSpeak(text);
  }, [cleanupAudio, fallbackSpeak, onSpeakingDone]);

  const stop = useCallback(() => {
    cleanupAudio();
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
  }, [cleanupAudio]);

  return {
    isSpeaking,
    speak,
    stop,
  };
}
