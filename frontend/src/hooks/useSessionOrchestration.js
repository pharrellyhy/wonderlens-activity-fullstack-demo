import { useState, useCallback, useEffect, useLayoutEffect, useRef } from 'react';
import useConversation from './useConversation';
import useSfxPlayer from './useSfxPlayer';
import useSilenceTimer from './useSilenceTimer';
import useSpeechRecognition from './useSpeechRecognition';
import useTTS from './useTTS';

export default function useSessionOrchestration(tier) {
  const [retryCount, setRetryCount] = useState(0);
  const [ttsEnabled, setTtsEnabled] = useState(() => localStorage.getItem('ttsEnabled') === 'true');
  const [silenceTimerOn, setSilenceTimerOn] = useState(() => localStorage.getItem('silenceTimerOn') === 'true');
  const silenceTimerRef = useRef({ start() {}, clear() {} });
  const lastSpokenIndexRef = useRef(-1);
  const autoAdvancePendingRef = useRef(false);
  const mutedCompletionTimeoutRef = useRef(null);

  const {
    messages,
    sessionId,
    sessionState,
    screenFrame,
    loading,
    turnPending,
    error,
    latency,
    activityType,
    templateType,
    photoUrl,
    errorExit,
    lastWrongPhotoId,
    debugData,
    debugHistory,
    pendingAudioRef,
    start,
    startDeepLink,
    sendMessage,
    sendSilence,
    sendAutoAdvance,
    sendPhotoCollection,
    reset,
  } = useConversation();

  const { unlock: unlockSfx } = useSfxPlayer();

  const isActive = sessionState?.status === 'active';
  const isEnded = sessionState?.status === 'completed' || sessionState?.status === 'exited' || sessionState?.status === 'error';
  const isInputDisabled = isEnded || loading || turnPending;

  const handleSpeakingDone = useCallback(() => {
    if (sessionState?.status === 'active') {
      // Check if the last message was an auto-advance step
      if (autoAdvancePendingRef.current) {
        autoAdvancePendingRef.current = false;
        sendAutoAdvance();
      } else {
        silenceTimerRef.current.start();
      }
    }
  }, [sessionState?.status, sendAutoAdvance]);

  const clearMutedCompletionTimeout = useCallback(() => {
    if (mutedCompletionTimeoutRef.current !== null) {
      clearTimeout(mutedCompletionTimeoutRef.current);
      mutedCompletionTimeoutRef.current = null;
    }
  }, []);

  const { isSpeaking, audioInfo, speak, speakFromStream, stop: stopTTS, unlock: unlockTTS } = useTTS(handleSpeakingDone);

  // Unlock audio on the first user gesture (click/touch/keydown).
  // Deep link sessions start via redirect (no user gesture), so the unlock
  // calls inside startDeepLinkSession never satisfy browser autoplay policy.
  // This listener catches the first real interaction and unlocks then.
  useLayoutEffect(() => {
    const handler = () => {
      unlockSfx();
      unlockTTS();
      for (const evt of ['click', 'touchstart', 'keydown']) {
        document.removeEventListener(evt, handler, true);
      }
    };
    for (const evt of ['click', 'touchstart', 'keydown']) {
      document.addEventListener(evt, handler, { capture: true, once: false });
    }
    return () => {
      for (const evt of ['click', 'touchstart', 'keydown']) {
        document.removeEventListener(evt, handler, true);
      }
    };
  }, [unlockSfx, unlockTTS]);

  const handleSilence = useCallback(() => {
    if (sessionState?.status === 'active') {
      sendSilence();
    }
  }, [sendSilence, sessionState?.status]);

  const silenceTimerEnabled = silenceTimerOn && isActive && !isSpeaking && !turnPending;
  const silenceTimer = useSilenceTimer(
    tier,
    handleSilence,
    silenceTimerEnabled,
  );

  // When TTS is muted and the silence timer becomes enabled but isn't running,
  // start it automatically (covers the gap where handleSpeakingDone fired
  // before the enabled flag flipped).
  useEffect(() => {
    if (silenceTimerEnabled && !ttsEnabled && !silenceTimer.isRunning && !autoAdvancePendingRef.current) {
      silenceTimer.start();
    }
  }, [silenceTimerEnabled, ttsEnabled, silenceTimer]);

  useEffect(() => {
    silenceTimerRef.current = silenceTimer;
  }, [silenceTimer]);

  const speech = useSpeechRecognition();

  // Auto-send transcript when speech recognition produces a result
  useEffect(() => {
    if (!speech.resultId || !speech.transcript || !isActive) return;
    silenceTimer.clear();
    sendMessage(speech.transcript);
  }, [isActive, sendMessage, silenceTimer, speech.resultId, speech.transcript]);

  // Persist TTS preference to localStorage
  useEffect(() => {
    localStorage.setItem('ttsEnabled', ttsEnabled);
  }, [ttsEnabled]);

  // Persist silence timer preference to localStorage
  useEffect(() => {
    localStorage.setItem('silenceTimerOn', silenceTimerOn);
  }, [silenceTimerOn]);

  const toggleSilenceTimer = useCallback(() => {
    setSilenceTimerOn(prev => {
      const next = !prev;
      if (!next) silenceTimer.clear();
      return next;
    });
  }, [silenceTimer]);

  const toggleTts = useCallback(() => {
    setTtsEnabled(prev => {
      const next = !prev;
      if (!next) {
        // Switching to muted — stop any in-progress TTS
        stopTTS();
      }
      return next;
    });
  }, [stopTTS]);

  // Auto-speak AI messages and handle auto-advance
  useEffect(() => {
    if (messages.length === 0) return;
    clearMutedCompletionTimeout();
    const lastIndex = messages.length - 1;
    const lastMsg = messages[lastIndex];
    if (lastMsg.role !== 'ai') return;
    if (lastIndex <= lastSpokenIndexRef.current) return;
    lastSpokenIndexRef.current = lastIndex;
    silenceTimer.clear();

    // Set auto-advance flag if this step doesn't need user input
    if (lastMsg.autoAdvance && !lastMsg.errorExit) {
      autoAdvancePendingRef.current = true;
    }

    if (ttsEnabled) {
      // Check if there's a pending audio stream from /api/turn-speak
      const pendingAudio = pendingAudioRef.current;
      if (pendingAudio) {
        pendingAudioRef.current = null;
        speakFromStream(pendingAudio.stream);
      } else {
        // Fallback: use /api/tts (e.g., for the first turn from /api/start)
        speak(lastMsg.text, tier);
      }
    } else {
      // TTS muted — skip audio but still trigger done callback for silence timer / auto-advance
      pendingAudioRef.current = null;
      mutedCompletionTimeoutRef.current = window.setTimeout(() => {
        mutedCompletionTimeoutRef.current = null;
        handleSpeakingDone();
      }, 0);
    }
    return clearMutedCompletionTimeout;
  }, [
    clearMutedCompletionTimeout,
    handleSpeakingDone,
    messages,
    pendingAudioRef,
    silenceTimer,
    speak,
    speakFromStream,
    tier,
    ttsEnabled,
  ]);

  // Clear silence timer when input is disabled
  useEffect(() => {
    if (isInputDisabled) {
      silenceTimer.clear();
    }
  }, [isInputDisabled, silenceTimer]);

  const startSession = useCallback(async (photo) => {
    // Unlock audio playback synchronously in the user gesture context,
    // before the async API call, to satisfy browser autoplay policy.
    clearMutedCompletionTimeout();
    unlockSfx();
    unlockTTS();
    try {
      setRetryCount(0);
      await start(photo, tier);
    } catch {
      setRetryCount(prev => prev + 1);
    }
  }, [clearMutedCompletionTimeout, start, tier, unlockSfx, unlockTTS]);

  const startDeepLinkSession = useCallback(async (entity, deepLinkTier, contextUrl = '') => {
    // Audio unlock is NOT called here — deep link sessions start via redirect
    // (useEffect), not a user gesture, so unlock would be rejected by the
    // browser.  The first-interaction listener registered above handles it.
    clearMutedCompletionTimeout();
    try {
      setRetryCount(0);
      return await startDeepLink(entity, deepLinkTier, contextUrl);
    } catch (error) {
      setRetryCount(prev => prev + 1);
      throw error;
    }
  }, [clearMutedCompletionTimeout, startDeepLink]);

  const handleSendMessage = useCallback((text) => {
    if (!text.trim() || !isActive || turnPending) return;
    silenceTimer.clear();
    sendMessage(text);
  }, [isActive, sendMessage, silenceTimer, turnPending]);

  const handlePhotoCollection = useCallback((photoId, label) => {
    if (!isActive || turnPending) return;
    silenceTimer.clear();
    return sendPhotoCollection(photoId, label);
  }, [isActive, sendPhotoCollection, silenceTimer, turnPending]);

  const toggleMic = useCallback(() => {
    if (turnPending) return;
    if (speech.isListening) {
      speech.stop();
    } else {
      silenceTimer.clear();
      speech.start();
    }
  }, [silenceTimer, speech, turnPending]);

  const resetSession = useCallback(() => {
    clearMutedCompletionTimeout();
    stopTTS();
    silenceTimer.clear();
    speech.stop();
    reset();
    setRetryCount(0);
    lastSpokenIndexRef.current = -1;
    autoAdvancePendingRef.current = false;
  }, [clearMutedCompletionTimeout, reset, silenceTimer, speech, stopTTS]);

  return {
    messages,
    sessionId,
    sessionState,
    screenFrame,
    loading,
    turnPending,
    error,
    latency,
    activityType,
    templateType,
    photoUrl,
    errorExit,
    lastWrongPhotoId,
    debugData,
    debugHistory,
    retryCount,
    isActive,
    isEnded,
    isInputDisabled,
    isSpeaking,
    audioInfo,
    ttsEnabled,
    toggleTts,
    silenceTimerOn,
    toggleSilenceTimer,
    isMicActive: speech.isListening,
    sttMode: speech.mode,
    silenceTimer,
    startSession,
    startDeepLinkSession,
    sendMessage: handleSendMessage,
    sendPhotoCollection: handlePhotoCollection,
    toggleMic,
    resetSession,
  };
}
