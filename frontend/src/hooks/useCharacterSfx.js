import { useRef, useCallback } from 'react';
import BASE from '../utils/basePath';

const VARIATIONS = 3;
const VOLUME = 0.7;
const MICRO_VOLUME = 0.3;
const FADE_OUT_MS = 400;
const INTRO_DELAY_MS = 500;
const OVERLAY_DELAY_MS = 300;

/**
 * Hook for playing ambient environment sound effects alongside TTS.
 * Uses Web Audio API for fade-out so sounds end smoothly instead of abruptly.
 * Separate from useSfxPlayer (which handles the 10 UI SFX cues).
 */
export default function useCharacterSfx() {
  const bufferCacheRef = useRef({});
  const overlayTimeoutRef = useRef(null);
  const introTimeoutRef = useRef(null);
  const unlockedRef = useRef(false);
  const activityTypeRef = useRef('');
  const audioCtxRef = useRef(null);
  const activeSourcesRef = useRef([]);

  /** Get or create the shared AudioContext. */
  const getAudioCtx = useCallback(() => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioCtxRef.current;
  }, []);

  const unlock = useCallback(() => {
    if (unlockedRef.current) return;
    const ctx = getAudioCtx();
    if (ctx.state === 'suspended') ctx.resume().catch(() => {});
    unlockedRef.current = true;
  }, [getAudioCtx]);

  /** Record the active activity so cue playback can resolve asset paths. */
  const preload = useCallback((activityType) => {
    if (!activityType) return;
    if (activityTypeRef.current !== activityType) {
      bufferCacheRef.current = {};
    }
    activityTypeRef.current = activityType;
  }, []);

  /** Fetch and decode an audio file into an AudioBuffer (cached). */
  const loadBuffer = useCallback(async (url) => {
    if (bufferCacheRef.current[url]) return bufferCacheRef.current[url];
    const ctx = getAudioCtx();
    const response = await fetch(url);
    const arrayBuffer = await response.arrayBuffer();
    const audioBuffer = await ctx.decodeAudioData(arrayBuffer);
    bufferCacheRef.current[url] = audioBuffer;
    return audioBuffer;
  }, [getAudioCtx]);

  /** Resolve a cue ID to its asset URL. Returns null if activity is unknown. */
  const resolveCueUrl = useCallback((cueId, prefix = '') => {
    const activityType = activityTypeRef.current;
    if (!activityType || !cueId) return null;
    const variant = Math.floor(Math.random() * VARIATIONS) + 1;
    return `${BASE}/sfx/character/${activityType}/${prefix}${cueId}_v${variant}.wav`;
  }, []);

  /** Play a cue with automatic fade-out at the end. */
  const playCue = useCallback((cueId) => {
    const url = resolveCueUrl(cueId);
    if (!url) return;

    loadBuffer(url).then((buffer) => {
      const ctx = getAudioCtx();
      const source = ctx.createBufferSource();
      const gain = ctx.createGain();

      source.buffer = buffer;
      gain.gain.setValueAtTime(VOLUME, ctx.currentTime);

      // Schedule fade-out near the end of the clip
      const fadeStart = Math.max(0, buffer.duration - FADE_OUT_MS / 1000);
      gain.gain.setValueAtTime(VOLUME, ctx.currentTime + fadeStart);
      gain.gain.linearRampToValueAtTime(0, ctx.currentTime + buffer.duration);

      source.connect(gain).connect(ctx.destination);
      source.start();

      // Track active sources for stop()
      activeSourcesRef.current.push({ source, gain });
      source.onended = () => {
        activeSourcesRef.current = activeSourcesRef.current.filter(s => s.source !== source);
      };
    }).catch((err) => {
      console.warn(`[CharacterSfx] Failed to play ${cueId}:`, err.message);
    });
  }, [getAudioCtx, loadBuffer, resolveCueUrl]);

  /** Clear any pending overlay/intro timeouts. */
  const clearTimers = useCallback(() => {
    for (const ref of [overlayTimeoutRef, introTimeoutRef]) {
      if (ref.current !== null) {
        clearTimeout(ref.current);
        ref.current = null;
      }
    }
  }, []);

  /**
   * Play character sounds for a turn with timing orchestration.
   *
   * @param {Array} cueList - Array of {cue, timing} objects
   * @param {Object} callbacks
   * @param {Function} callbacks.onIntrosDone - Called when intro sounds finish (or cap reached)
   */
  const playForTurn = useCallback((cueList, { onIntrosDone } = {}) => {
    clearTimers();

    if (!cueList?.length) {
      onIntrosDone?.();
      return { startOverlays: () => {}, playOutros: () => {} };
    }

    const intros = cueList.filter(c => c.timing === 'intro');
    const overlays = cueList.filter(c => c.timing === 'overlay');
    const outros = cueList.filter(c => c.timing === 'outro');

    // Play intros immediately; always defer onIntrosDone so the caller can
    // store the returned controls before the callback fires.
    for (const cue of intros) {
      playCue(cue.cue);
    }
    const introDelay = intros.length > 0 ? INTRO_DELAY_MS : 0;
    introTimeoutRef.current = setTimeout(() => {
      introTimeoutRef.current = null;
      onIntrosDone?.();
    }, introDelay);

    // Return controls for overlay and outro timing
    return {
      startOverlays: () => {
        if (overlays.length > 0) {
          overlayTimeoutRef.current = setTimeout(() => {
            overlayTimeoutRef.current = null;
            for (const cue of overlays) {
              playCue(cue.cue);
            }
          }, OVERLAY_DELAY_MS);
        }
      },
      playOutros: () => {
        for (const cue of outros) {
          playCue(cue.cue);
        }
      },
    };
  }, [clearTimers, playCue]);

  /** Stop all character sounds with a quick fade-out. */
  const stop = useCallback(() => {
    clearTimers();
    const ctx = audioCtxRef.current;
    if (!ctx) return;
    for (const { source, gain } of activeSourcesRef.current) {
      gain.gain.cancelScheduledValues(ctx.currentTime);
      gain.gain.setValueAtTime(gain.gain.value, ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0, ctx.currentTime + FADE_OUT_MS / 1000);
      source.stop(ctx.currentTime + FADE_OUT_MS / 1000);
    }
    activeSourcesRef.current = [];
  }, [clearTimers]);

  /** Play a short micro-sound instantly (no timing orchestration). */
  const playMicro = useCallback((cueId) => {
    const url = resolveCueUrl(cueId, 'micro_');
    if (!url) return;

    loadBuffer(url).then((buffer) => {
      const ctx = getAudioCtx();
      const source = ctx.createBufferSource();
      const gain = ctx.createGain();

      source.buffer = buffer;
      gain.gain.setValueAtTime(MICRO_VOLUME, ctx.currentTime);
      source.connect(gain).connect(ctx.destination);
      source.start();

      source.onended = () => {
        try { source.disconnect(); } catch {}
      };
    }).catch(() => {
      // Silently ignore missing micro-sound assets
    });
  }, [getAudioCtx, loadBuffer, resolveCueUrl]);

  return { preload, playForTurn, playMicro, stop, unlock };
}
