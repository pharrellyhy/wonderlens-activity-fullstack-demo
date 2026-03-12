import { useEffect, useRef, useCallback, useState } from 'react';

const SILENCE_TIMEOUTS = {
  T0: 10000,
  T1: 8000,
  T2: 6000,
};

export default function useSilenceTimer(tier, onSilence, enabled) {
  const timerRef = useRef(null);
  const startTimeRef = useRef(null);
  const [elapsed, setElapsed] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const intervalRef = useRef(null);

  const timeout = SILENCE_TIMEOUTS[tier] || 10000;

  const clear = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    startTimeRef.current = null;
    setIsRunning(false);
    setElapsed(0);
  }, []);

  const start = useCallback(() => {
    clear();
    if (!enabled) return;

    startTimeRef.current = Date.now();
    setIsRunning(true);

    // Update elapsed every 100ms for the progress bar
    intervalRef.current = setInterval(() => {
      if (startTimeRef.current) {
        setElapsed(Date.now() - startTimeRef.current);
      }
    }, 100);

    timerRef.current = setTimeout(() => {
      clear();
      onSilence?.();
    }, timeout);
  }, [clear, enabled, onSilence, timeout]);

  // Clean up on unmount
  useEffect(() => {
    return clear;
  }, [clear]);

  return {
    start,
    clear,
    elapsed,
    timeout,
    progress: Math.min(elapsed / timeout, 1),
    isRunning,
  };
}
