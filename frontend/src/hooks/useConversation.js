import { useState, useCallback, useRef } from 'react';
import { startSession, sendTurn, sendTurnSpeak } from '../utils/api';

export default function useConversation() {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [sessionState, setSessionState] = useState(null);
  const [screenFrame, setScreenFrame] = useState(null);
  const [visionResult, setVisionResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [turnPending, setTurnPending] = useState(false);
  const [error, setError] = useState(null);
  const [latency, setLatency] = useState(0);
  const [activityType, setActivityType] = useState('');
  const [templateType, setTemplateType] = useState('');
  const [photoUrl, setPhotoUrl] = useState('');
  const [errorExit, setErrorExit] = useState(false);
  const photoUrlRef = useRef(null);
  // Holds the audio stream from the latest /api/turn-speak response
  const pendingAudioRef = useRef(null);

  const clearPhotoUrl = useCallback(() => {
    if (photoUrlRef.current) {
      URL.revokeObjectURL(photoUrlRef.current);
      photoUrlRef.current = null;
    }
    setPhotoUrl('');
  }, []);

  const applyTurnResponse = useCallback((data) => {
    setLatency(data.latency_ms || 0);

    if (data.session_state) {
      setSessionState(data.session_state);
    }

    if (data.turn?.screen_frame) {
      setScreenFrame(data.turn.screen_frame);
    }

    if (data.turn?.error_exit) {
      setErrorExit(true);
    }

    if (data.turn?.dialogue) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'ai',
          text: data.turn.dialogue,
          responseType: data.turn.response_type,
          toneMarker: data.turn.tone_marker,
          sfx: data.turn.audio?.sfx,
          errorExit: data.turn.error_exit || false,
          autoAdvance: data.turn.auto_advance || false,
        },
      ]);
    }

    return data;
  }, []);

  const start = useCallback(async (photo, tier) => {
    setLoading(true);
    setTurnPending(false);
    setError(null);
    setMessages([]);
    setErrorExit(false);
    clearPhotoUrl();
    pendingAudioRef.current = null;

    // Create a local URL for the photo
    const url = URL.createObjectURL(photo);
    photoUrlRef.current = url;
    setPhotoUrl(url);

    try {
      const data = await startSession(photo, tier);
      setSessionId(data.session_id);
      setVisionResult(data.vision_result);
      setLatency(data.latency_ms || 0);
      setActivityType(data.activity_type || '');
      setTemplateType(data.template_type || '');

      // Set initial screen frame
      if (data.first_turn?.screen_frame) {
        setScreenFrame(data.first_turn.screen_frame);
      }

      // Set initial session state
      setSessionState(data.session_state || {
        status: 'active',
        current_step: 'STEP_1_HOOK',
        current_round: 0,
        total_rounds: 3,
        consecutive_silence: 0,
        turn_count: 1,
        template_type: data.template_type || 'cat1',
      });

      // Add hook line as first AI message
      if (data.first_turn?.dialogue) {
        setMessages([{
          role: 'ai',
          text: data.first_turn.dialogue,
          responseType: data.first_turn.response_type || 'hook',
          toneMarker: data.first_turn.tone_marker,
          sfx: data.first_turn.audio?.sfx,
        }]);
      }

      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [clearPhotoUrl]);

  /**
   * Send a turn using the combined /api/turn-speak endpoint.
   * Returns { turnData, audioStream, sampleRate } so the caller can play audio.
   */
  const sendTurnRequest = useCallback(async (text, isSilent, photoId = null) => {
    if (!sessionId || turnPending) return null;
    setTurnPending(true);

    // Only add child message for non-empty, non-auto-advance turns
    if (text || isSilent) {
      setMessages((prev) => [
        ...prev,
        isSilent ? { role: 'child', text: '...', isSilent: true } : { role: 'child', text },
      ]);
    }

    try {
      // Use combined turn+TTS endpoint
      const { turnData, audioStream, sampleRate } = await sendTurnSpeak(
        sessionId, text, isSilent, photoId,
      );

      // Store audio stream for the orchestration hook to play
      pendingAudioRef.current = { stream: audioStream, sampleRate };

      // Apply turn data (sets messages, screen frame, session state)
      applyTurnResponse(turnData);

      return turnData;
    } catch {
      // Fallback to regular /api/turn on failure
      try {
        const data = await sendTurn(sessionId, text, isSilent, photoId);
        pendingAudioRef.current = null;
        return applyTurnResponse(data);
      } catch (fallbackErr) {
        setError(fallbackErr.message);
        throw fallbackErr;
      }
    } finally {
      setTurnPending(false);
    }
  }, [applyTurnResponse, sessionId, turnPending]);

  const sendMessage = useCallback((text) => sendTurnRequest(text, false), [sendTurnRequest]);

  const sendSilence = useCallback(() => sendTurnRequest('', true), [sendTurnRequest]);

  const sendAutoAdvance = useCallback(() => sendTurnRequest('', false), [sendTurnRequest]);

  const sendPhotoCollection = useCallback(
    (photoId) => sendTurnRequest('', false, photoId),
    [sendTurnRequest],
  );

  const reset = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    setSessionState(null);
    setScreenFrame(null);
    setVisionResult(null);
    setError(null);
    setLatency(0);
    setActivityType('');
    setTemplateType('');
    setTurnPending(false);
    setErrorExit(false);
    clearPhotoUrl();
    pendingAudioRef.current = null;
  }, [clearPhotoUrl]);

  return {
    messages,
    sessionId,
    sessionState,
    screenFrame,
    visionResult,
    loading,
    turnPending,
    error,
    latency,
    activityType,
    templateType,
    photoUrl,
    errorExit,
    pendingAudioRef,
    start,
    sendMessage,
    sendSilence,
    sendAutoAdvance,
    sendPhotoCollection,
    reset,
  };
}
