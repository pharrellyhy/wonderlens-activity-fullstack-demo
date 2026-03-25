import { useEffect, useRef, useCallback, useState, useMemo } from 'react';

const SILENCE_TIMEOUT = 30000;

export default function useSilenceTimer(tier, onSilence, enabled) {
  const timerRef = useRef(null);
  const startTimeRef = useRef(null);
  const [elapsed, setElapsed] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const intervalRef = useRef(null);

  const timeout = SILENCE_TIMEOUT;

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

    // Update elapsed every 500ms for the progress bar (reduced from 100ms)
    intervalRef.current = setInterval(() => {
      if (startTimeRef.current) {
        setElapsed(Date.now() - startTimeRef.current);
      }
    }, 500);

    timerRef.current = setTimeout(() => {
      clear();
      onSilence?.();
    }, timeout);
  }, [clear, enabled, onSilence, timeout]);

  // Clean up on unmount
  useEffect(() => {
    return clear;
  }, [clear]);

  // Memoize the return object to avoid triggering re-renders in consumers
  const progress = Math.min(elapsed / timeout, 1);

  return useMemo(() => ({
    start,
    clear,
    elapsed,
    timeout,
    progress,
    isRunning,
  }), [start, clear, elapsed, timeout, progress, isRunning]);
}
