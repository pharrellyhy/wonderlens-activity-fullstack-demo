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

function isTerminalStatus(status) {
  return status === 'completed' || status === 'exited' || status === 'error';
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
  const sessionStatusRef = useRef('');
  const requestGenerationRef = useRef(0);

  const reset = useCallback(() => {
    requestGenerationRef.current += 1;
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
    sessionStatusRef.current = '';
  }, []);

  const isCurrentRequest = useCallback((expectedGeneration, expectedSessionId = null) => (
    expectedGeneration === requestGenerationRef.current
    && (!expectedSessionId || sessionIdRef.current === expectedSessionId)
  ), []);

  const applyTurn = useCallback((data, expectedGeneration = requestGenerationRef.current, expectedSessionId = null) => {
    if (!isCurrentRequest(expectedGeneration, expectedSessionId)) return null;

    if (data.session_state) {
      setSessionState(data.session_state);
      sessionStatusRef.current = data.session_state.status || '';
    }
    if (data.turn?.screen_frame) {
      setScreenFrame(data.turn.screen_frame);
    }
    const aiMessage = aiMessageFromTurn(data.turn);
    if (aiMessage) {
      setMessages((prev) => [...prev, aiMessage]);
    }
    return data;
  }, [isCurrentRequest]);

  const startActivity = useCallback(async (nextActivityType, tier = 'T1') => {
    const requestGeneration = requestGenerationRef.current + 1;
    requestGenerationRef.current = requestGeneration;
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
      if (!isCurrentRequest(requestGeneration)) return null;
      setSessionId(data.session_id);
      sessionIdRef.current = data.session_id;
      setActivityType(data.activity_type || nextActivityType);
      setTemplateType(data.template_type || '');
      setSessionState(data.session_state || null);
      sessionStatusRef.current = data.session_state?.status || '';
      if (data.first_turn?.screen_frame) {
        setScreenFrame(data.first_turn.screen_frame);
      }
      const firstMessage = aiMessageFromTurn(data.first_turn);
      setMessages(firstMessage ? [firstMessage] : []);
      return data;
    } catch (err) {
      if (isCurrentRequest(requestGeneration)) {
        setError(err.message);
        throw err;
      }
      return null;
    } finally {
      if (isCurrentRequest(requestGeneration)) {
        setLoading(false);
      }
    }
  }, [isCurrentRequest]);

  const sendMessage = useCallback(async (text) => {
    const trimmed = text.trim();
    const activeSessionId = sessionIdRef.current || sessionId;
    const status = sessionStatusRef.current || sessionState?.status;
    const requestGeneration = requestGenerationRef.current;
    if (!activeSessionId || !trimmed || turnPending || isTerminalStatus(status)) return null;

    setTurnPending(true);
    setError(null);
    setMessages((prev) => [...prev, { role: 'child', text: trimmed }]);

    try {
      const data = await sendTurn(activeSessionId, trimmed, false);
      return applyTurn(data, requestGeneration, activeSessionId);
    } catch (err) {
      if (isCurrentRequest(requestGeneration, activeSessionId)) {
        setError(err.message);
        throw err;
      }
      return null;
    } finally {
      if (isCurrentRequest(requestGeneration, activeSessionId)) {
        setTurnPending(false);
      }
    }
  }, [applyTurn, isCurrentRequest, sessionId, sessionState?.status, turnPending]);

  const sendCollectionItem = useCallback(async (photoId, label = '') => {
    const activeSessionId = sessionIdRef.current || sessionId;
    const status = sessionStatusRef.current || sessionState?.status;
    const selectedLabel = label || photoId;
    const requestGeneration = requestGenerationRef.current;
    if (!activeSessionId || !photoId || turnPending || isTerminalStatus(status)) return null;

    setTurnPending(true);
    setError(null);
    setMessages((prev) => [...prev, { role: 'child', text: selectedLabel }]);

    try {
      const data = await sendTurn(activeSessionId, '', false, photoId);
      return applyTurn(data, requestGeneration, activeSessionId);
    } catch (err) {
      if (isCurrentRequest(requestGeneration, activeSessionId)) {
        setError(err.message);
        throw err;
      }
      return null;
    } finally {
      if (isCurrentRequest(requestGeneration, activeSessionId)) {
        setTurnPending(false);
      }
    }
  }, [applyTurn, isCurrentRequest, sessionId, sessionState?.status, turnPending]);

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
    sendCollectionItem,
    reset,
  };
}
