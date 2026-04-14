import { useCallback, useRef, useState } from 'react';

const TESTER_ALIAS_KEY = 'wl-tester-alias';

function pad2(n) {
  return String(n).padStart(2, '0');
}

function readStoredAlias() {
  try {
    return localStorage.getItem(TESTER_ALIAS_KEY) || '';
  } catch {
    return '';
  }
}

function writeStoredAlias(alias) {
  try {
    if (alias) {
      localStorage.setItem(TESTER_ALIAS_KEY, alias);
    } else {
      localStorage.removeItem(TESTER_ALIAS_KEY);
    }
  } catch {
    // non-fatal (storage disabled)
  }
}

function buildScreenshotPath(turnNumber, existingFlags) {
  const prefix = `screenshots/turn-${pad2(turnNumber)}-auto`;
  let collisions = 0;
  for (const flag of existingFlags) {
    if (flag.turn_number !== turnNumber) continue;
    for (const shot of flag.screenshots || []) {
      if (shot.path && shot.path.startsWith(prefix)) collisions += 1;
    }
  }
  return collisions === 0 ? `${prefix}.png` : `${prefix}-${collisions}.png`;
}

export default function useFeedbackStore() {
  const [flags, setFlags] = useState([]);
  const [testerAlias, setTesterAliasState] = useState(() => readStoredAlias());
  const flagCounterRef = useRef(0);

  const setTesterAlias = useCallback((raw) => {
    const next = (raw || '').trim();
    writeStoredAlias(next);
    setTesterAliasState(next);
  }, []);

  const addFlag = useCallback(
    ({ turnNumber, tags, quickNote, screenshot, turnSnapshot }) => {
      flagCounterRef.current += 1;
      const flagId = `f-${pad2(flagCounterRef.current)}`;
      const flaggedAt = new Date().toISOString();
      setFlags((prev) => {
        const path = screenshot ? buildScreenshotPath(turnNumber, prev) : null;
        return [
          ...prev,
          {
            flag_id: flagId,
            turn_number: turnNumber,
            flagged_at: flaggedAt,
            tags: Array.isArray(tags) ? [...tags] : [],
            quick_note: quickNote || '',
            review_comment: null,
            screenshots: screenshot ? [{ path, blob: screenshot }] : [],
            turn_snapshot: turnSnapshot ? { ...turnSnapshot } : null,
          },
        ];
      });
      return flagId;
    },
    [],
  );

  const updateFlag = useCallback((flagId, patch) => {
    setFlags((prev) => prev.map((f) => (f.flag_id === flagId ? { ...f, ...patch } : f)));
  }, []);

  const deleteFlag = useCallback((flagId) => {
    setFlags((prev) => prev.filter((f) => f.flag_id !== flagId));
  }, []);

  // Tester alias is per-tester, not per-session — intentionally preserved.
  const clearSession = useCallback(() => {
    setFlags([]);
    flagCounterRef.current = 0;
  }, []);

  const buildPayload = useCallback(
    ({ sessionId, appMode, activity, sessionStartedAt, sessionEndedAt }) => {
      const screenshots = {};
      const jsonFlags = flags.map((f) => {
        const paths = [];
        for (const shot of f.screenshots || []) {
          if (!shot || !shot.path) continue;
          paths.push(shot.path);
          if (shot.blob) {
            screenshots[shot.path] = shot.blob;
          }
        }
        const reviewComment =
          f.review_comment && f.review_comment.trim().length > 0
            ? f.review_comment
            : null;
        return {
          flag_id: f.flag_id,
          turn_number: f.turn_number,
          flagged_at: f.flagged_at,
          tags: f.tags,
          quick_note: f.quick_note,
          review_comment: reviewComment,
          screenshots: paths,
          turn_snapshot: f.turn_snapshot,
        };
      });

      const json = {
        session_id: sessionId,
        tester_alias: testerAlias || null,
        app_mode: appMode || 'tester',
        activity: activity || null,
        session_started_at: sessionStartedAt || null,
        session_ended_at: sessionEndedAt || null,
        flags: jsonFlags,
      };

      return { json, screenshots };
    },
    [flags, testerAlias],
  );

  return {
    flags,
    hasFlags: flags.length > 0,
    testerAlias,
    setTesterAlias,
    addFlag,
    updateFlag,
    deleteFlag,
    clearSession,
    buildPayload,
  };
}
