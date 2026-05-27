import { useCallback, useRef, useState } from 'react';
import { sendTurn, startActivitySession } from '../utils/api';

function aiMessageFromTurn(turn) {
  if (!turn?.dialogue) return null;
  return {
    role: 'ai',
    text: turn.dialogue,
    responseType: turn.response_type || 'response',
    toneMarker: turn.tone_marker || '',
    characterState: turn.character_state || 'speaking',
    autoAdvance: Boolean(turn.auto_advance),
  };
}

export default function useActivityTextSession() {
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [sessionState, setSessionState] = useState(null);
  const [screenFrame, setScreenFrame] = useState(null);
  const [loading, setLoading] = useState(false);
  const [turnPending, setTurnPending] = useState(false);
  const [error, setError] = useState(null);
  const [activityType, setActivityType] = useState('');
  const [templateType, setTemplateType] = useState('');
  const sessionIdRef = useRef(null);

  const reset = useCallback(() => {
    setMessages([]);
    setSessionId(null);
    sessionIdRef.current = null;
    setSessionState(null);
    setScreenFrame(null);
    setLoading(false);
    setTurnPending(false);
    setError(null);
    setActivityType('');
    setTemplateType('');
  }, []);

  const applyTurn = useCallback((data) => {
    if (data.session_state) {
      setSessionState(data.session_state);
    }
    if (data.turn?.screen_frame) {
      setScreenFrame(data.turn.screen_frame);
    }
    const aiMessage = aiMessageFromTurn(data.turn);
    if (aiMessage) {
      setMessages((prev) => [...prev, aiMessage]);
    }
    return data;
  }, []);

  const startActivity = useCallback(async (nextActivityType, tier = 'T1') => {
    setLoading(true);
    setTurnPending(false);
    setError(null);
    setMessages([]);
    setSessionId(null);
    sessionIdRef.current = null;
    setSessionState(null);
    setScreenFrame(null);
    setActivityType(nextActivityType);
    setTemplateType('');

    try {
      const data = await startActivitySession(nextActivityType, tier);
      setSessionId(data.session_id);
      sessionIdRef.current = data.session_id;
      setActivityType(data.activity_type || nextActivityType);
      setTemplateType(data.template_type || '');
      setSessionState(data.session_state || null);
      if (data.first_turn?.screen_frame) {
        setScreenFrame(data.first_turn.screen_frame);
      }
      const firstMessage = aiMessageFromTurn(data.first_turn);
      setMessages(firstMessage ? [firstMessage] : []);
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const sendMessage = useCallback(async (text) => {
    const trimmed = text.trim();
    const activeSessionId = sessionIdRef.current || sessionId;
    if (!activeSessionId || !trimmed || turnPending) return null;

    setTurnPending(true);
    setError(null);
    setMessages((prev) => [...prev, { role: 'child', text: trimmed }]);

    try {
      const data = await sendTurn(activeSessionId, trimmed, false);
      return applyTurn(data);
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setTurnPending(false);
    }
  }, [applyTurn, sessionId, turnPending]);

  return {
    messages,
    sessionId,
    sessionState,
    screenFrame,
    loading,
    turnPending,
    error,
    activityType,
    templateType,
    startActivity,
    sendMessage,
    reset,
  };
}
