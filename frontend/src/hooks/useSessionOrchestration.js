import { useState, useCallback, useEffect, useRef } from 'react';
import useConversation from './useConversation';
import useSilenceTimer from './useSilenceTimer';
import useSpeechRecognition from './useSpeechRecognition';
import useTTS from './useTTS';

export default function useSessionOrchestration(tier) {
  const [retryCount, setRetryCount] = useState(0);
  const silenceTimerRef = useRef({ start() {}, clear() {} });
  const lastSpokenIndexRef = useRef(-1);
  const autoAdvancePendingRef = useRef(false);

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
    pendingAudioRef,
    start,
    sendMessage,
    sendSilence,
    sendAutoAdvance,
    sendPhotoCollection,
    reset,
  } = useConversation();

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

  const { isSpeaking, speak, speakFromStream, stop: stopTTS } = useTTS(handleSpeakingDone);

  const handleSilence = useCallback(() => {
    if (sessionState?.status === 'active') {
      sendSilence();
    }
  }, [sendSilence, sessionState?.status]);

  const silenceTimer = useSilenceTimer(
    tier,
    handleSilence,
    isActive && !isSpeaking && !turnPending,
  );

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

  // Auto-speak AI messages and handle auto-advance
  useEffect(() => {
    if (messages.length === 0) return;
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

    // Check if there's a pending audio stream from /api/turn-speak
    const pendingAudio = pendingAudioRef.current;
    if (pendingAudio) {
      pendingAudioRef.current = null;
      speakFromStream(pendingAudio.stream, pendingAudio.sampleRate);
    } else {
      // Fallback: use /api/tts (e.g., for the first turn from /api/start)
      speak(lastMsg.text, tier);
    }
  }, [messages, silenceTimer, speak, speakFromStream, tier, pendingAudioRef]);

  // Clear silence timer when input is disabled
  useEffect(() => {
    if (isInputDisabled) {
      silenceTimer.clear();
    }
  }, [isInputDisabled, silenceTimer]);

  const startSession = useCallback(async (photo) => {
    try {
      setRetryCount(0);
      await start(photo, tier);
    } catch {
      setRetryCount(prev => prev + 1);
    }
  }, [start, tier]);

  const handleSendMessage = useCallback((text) => {
    if (!text.trim() || !isActive || turnPending) return;
    silenceTimer.clear();
    sendMessage(text);
  }, [isActive, sendMessage, silenceTimer, turnPending]);

  const handlePhotoCollection = useCallback((photoId) => {
    if (!isActive || turnPending) return;
    silenceTimer.clear();
    sendPhotoCollection(photoId);
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
    stopTTS();
    silenceTimer.clear();
    speech.stop();
    reset();
    setRetryCount(0);
    lastSpokenIndexRef.current = -1;
    autoAdvancePendingRef.current = false;
  }, [reset, silenceTimer, speech, stopTTS]);

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
    retryCount,
    isActive,
    isEnded,
    isInputDisabled,
    isSpeaking,
    isMicActive: speech.isListening,
    sttMode: speech.mode,
    silenceTimer,
    startSession,
    sendMessage: handleSendMessage,
    sendPhotoCollection: handlePhotoCollection,
    toggleMic,
    resetSession,
  };
}
