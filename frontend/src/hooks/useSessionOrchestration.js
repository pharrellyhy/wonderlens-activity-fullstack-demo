import { useState, useCallback, useEffect, useRef } from 'react';
import useConversation from './useConversation';
import useSilenceTimer from './useSilenceTimer';
import useSpeechRecognition from './useSpeechRecognition';
import useTTS from './useTTS';

export default function useSessionOrchestration(tier) {
  const [retryCount, setRetryCount] = useState(0);
  const silenceTimerRef = useRef({ start() {}, clear() {} });
  const lastSpokenIndexRef = useRef(-1);

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
    photoUrl,
    start,
    sendMessage,
    sendSilence,
    reset,
  } = useConversation();

  const isActive = sessionState?.status === 'active';
  const isEnded = sessionState?.status === 'completed' || sessionState?.status === 'exited';
  const isInputDisabled = isEnded || loading || turnPending;

  const handleSpeakingDone = useCallback(() => {
    if (sessionState?.status === 'active') {
      silenceTimerRef.current.start();
    }
  }, [sessionState?.status]);

  const { isSpeaking, speak, stop: stopTTS } = useTTS(handleSpeakingDone);

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

  // Auto-speak AI messages (only when a new AI message appears)
  useEffect(() => {
    if (messages.length === 0) return;
    const lastIndex = messages.length - 1;
    const lastMsg = messages[lastIndex];
    if (lastMsg.role !== 'ai') return;
    if (lastIndex <= lastSpokenIndexRef.current) return;
    lastSpokenIndexRef.current = lastIndex;
    silenceTimer.clear();
    speak(lastMsg.text, tier);
  }, [messages, silenceTimer, speak, tier]);

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
    photoUrl,
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
    toggleMic,
    resetSession,
  };
}
