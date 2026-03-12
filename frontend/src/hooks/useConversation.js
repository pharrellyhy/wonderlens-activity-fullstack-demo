import { useState, useCallback, useRef } from 'react';
import { startSession, sendTurn } from '../utils/api';

export default function useConversation() {
  const [messages, setMessages] = useState([]);
  const [recipe, setRecipe] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [sessionState, setSessionState] = useState(null);
  const [screenFrame, setScreenFrame] = useState(null);
  const [visionResult, setVisionResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [turnPending, setTurnPending] = useState(false);
  const [error, setError] = useState(null);
  const [latency, setLatency] = useState(0);
  const [activityType, setActivityType] = useState('');
  const [photoUrl, setPhotoUrl] = useState('');
  const photoUrlRef = useRef(null);

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

    if (data.turn?.dialogue) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'ai',
          text: data.turn.dialogue,
          responseType: data.turn.response_type,
          sfx: data.turn.audio?.sfx,
        },
      ]);
    }
  }, []);

  const start = useCallback(async (photo, tier) => {
    setLoading(true);
    setTurnPending(false);
    setError(null);
    setMessages([]);
    clearPhotoUrl();

    // Create a local URL for the photo
    const url = URL.createObjectURL(photo);
    photoUrlRef.current = url;
    setPhotoUrl(url);

    try {
      const data = await startSession(photo, tier);
      setSessionId(data.session_id);
      setRecipe(data.recipe);
      setVisionResult(data.vision_result);
      setLatency(data.latency_ms || 0);
      setActivityType(data.recipe?.activity_type || '');

      // Set initial screen frame
      if (data.first_turn?.screen_frame) {
        setScreenFrame(data.first_turn.screen_frame);
      }

      // Set initial session state
      setSessionState({
        status: 'active',
        current_round: 0,
        total_rounds: data.recipe?.voice_script?.rounds?.length || 0,
        consecutive_silence: 0,
        turn_count: 0,
      });

      // Add hook line as first AI message
      if (data.first_turn?.dialogue) {
        setMessages([{
          role: 'ai',
          text: data.first_turn.dialogue,
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

  const sendTurnRequest = useCallback(async (text, isSilent) => {
    if (!sessionId || turnPending) return null;
    setTurnPending(true);

    setMessages((prev) => [
      ...prev,
      isSilent ? { role: 'child', text: '...', isSilent: true } : { role: 'child', text },
    ]);

    try {
      const data = await sendTurn(sessionId, text, isSilent);
      applyTurnResponse(data);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setTurnPending(false);
    }
  }, [applyTurnResponse, sessionId, turnPending]);

  const sendMessage = useCallback((text) => sendTurnRequest(text, false), [sendTurnRequest]);

  const sendSilence = useCallback(() => sendTurnRequest('', true), [sendTurnRequest]);

  const reset = useCallback(() => {
    setMessages([]);
    setRecipe(null);
    setSessionId(null);
    setSessionState(null);
    setScreenFrame(null);
    setVisionResult(null);
    setError(null);
    setLatency(0);
    setActivityType('');
    setTurnPending(false);
    clearPhotoUrl();
  }, [clearPhotoUrl]);

  return {
    messages,
    recipe,
    sessionId,
    sessionState,
    screenFrame,
    visionResult,
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
  };
}
