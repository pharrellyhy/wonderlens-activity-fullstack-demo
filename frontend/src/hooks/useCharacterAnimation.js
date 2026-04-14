import { useState, useCallback, useEffect, useRef } from 'react';
import { getThemeForEntity, getScenarioSlug } from '../widgets/gameThemes';

const ONE_SHOT_STATES = new Set(['excited', 'encouraging', 'surprised']);

function entityFromActivity(activityType) {
  if (!activityType) return null;
  const parts = activityType.split('_');
  return parts[parts.length - 1] || null;
}

/**
 * Manages character animation state and video clip selection.
 *
 * Priority (highest to lowest):
 * 1. Session lifecycle: waving at start/end
 * 2. AI response: emotion clip (excited, encouraging, surprised, speaking)
 * 3. TTS active: speaking clip
 * 4. Round idle: scenario clip loops as the "world"
 * 5. Default: character idle clip
 */
export default function useCharacterAnimation({
  isSpeaking,
  characterState,
  messageCount,
  currentStep,
  currentRound,
  currentScenario,
  activityType,
  templateType,
}) {
  const [animationState, setAnimationState] = useState(null);
  const oneShotFollowUpRef = useRef(null);
  const lastProcessedMsgRef = useRef(0);

  const entity = entityFromActivity(activityType);
  const theme = entity ? getThemeForEntity(entity) : null;
  const hasVideo = !!(templateType === 'cat1' && theme?.videoPrefix);

  // Determine the "resting" state — what to show after TTS/reactions finish
  const restingState =
    currentStep === 'STEP_4_CELEBRATE' ? 'celebrating' :
    currentStep === 'STEP_5_CLOSING' || currentStep === 'ENDED' ? 'waving' :
    currentStep?.startsWith('STEP_3_') && currentRound >= 1 && currentScenario ? 'scenario' :
    'idle';

  // Resolve clip URL from animation state
  const resolveClipUrl = useCallback((state) => {
    if (!state || !hasVideo || !theme?.videoBasePath || !theme?.videoPrefix) return null;

    if (state === 'scenario') {
      if (!theme?.scenarioBasePath || !currentScenario) {
        return `${theme.videoBasePath}/${theme.videoPrefix}_idle.mp4`;
      }
      const slug = getScenarioSlug(activityType, currentScenario);
      if (!slug) {
        return `${theme.videoBasePath}/${theme.videoPrefix}_idle.mp4`;
      }
      return `${theme.scenarioBasePath}/scenario_${slug}.mp4`;
    }

    return `${theme.videoBasePath}/${theme.videoPrefix}_${state}.mp4`;
  }, [hasVideo, theme, currentScenario, activityType]);

  // 1. Game intro — waving once (8s) then idle, triggered at STEP_2.
  //    setState is scheduled via setTimeout so the repo's `set-state-in-effect`
  //    lint rule is satisfied (it only flags synchronous setState in effect
  //    bodies; timer callbacks are allowed).
  const hasPlayedWavingRef = useRef(false);
  useEffect(() => {
    if (!hasVideo) return;
    if (!currentStep?.startsWith('STEP_2_') || hasPlayedWavingRef.current) return;
    hasPlayedWavingRef.current = true;
    const startTimer = setTimeout(() => setAnimationState('waving'), 0);
    const idleTimer = setTimeout(() => setAnimationState('idle'), 8000);
    return () => {
      clearTimeout(startTimer);
      clearTimeout(idleTimer);
    };
  }, [currentStep, hasVideo]);

  // 2. AI response — set character emotion clip. TTS audio plays on top (overlapped).
  useEffect(() => {
    if (!hasVideo || !characterState || messageCount <= lastProcessedMsgRef.current) return;
    lastProcessedMsgRef.current = messageCount;
    const timer = setTimeout(() => {
      setAnimationState(characterState);
      // One-shot clips return to resting state after playing; loops keep going
      oneShotFollowUpRef.current = ONE_SHOT_STATES.has(characterState) ? restingState : null;
    }, 0);
    return () => clearTimeout(timer);
  }, [characterState, messageCount, hasVideo, restingState]);

  // 2b. New scenario introduced — override emotion clip with scenario world.
  //     Only fires when we're actually in a round step (STEP_3_*), not during
  //     hook/invitation where session_state already has scenario preloaded.
  const prevScenarioRef = useRef(null);
  useEffect(() => {
    if (!hasVideo || !currentScenario) return;
    if (!currentStep?.startsWith('STEP_3_') || currentRound < 1) return;
    if (currentScenario === prevScenarioRef.current) return;
    prevScenarioRef.current = currentScenario;
    const timer = setTimeout(() => {
      setAnimationState('scenario');
      oneShotFollowUpRef.current = null;
    }, 0);
    return () => clearTimeout(timer);
  }, [hasVideo, currentScenario, currentStep, currentRound]);

  // 3. When TTS ends (true→false), return to resting state (scenario or idle).
  const wasSpeakingRef = useRef(false);
  useEffect(() => {
    if (!hasVideo) return;
    if (isSpeaking) {
      wasSpeakingRef.current = true;
      return undefined;
    }
    if (!wasSpeakingRef.current) return undefined;
    wasSpeakingRef.current = false;
    const timer = setTimeout(() => {
      setAnimationState((prev) => {
        if (prev === 'waving' || prev === 'celebrating') return prev;
        return restingState;
      });
    }, 0);
    return () => clearTimeout(timer);
  }, [isSpeaking, hasVideo, restingState]);

  // Callback for when a one-shot video clip ends
  const onClipEnded = useCallback(() => {
    if (oneShotFollowUpRef.current) {
      setAnimationState(oneShotFollowUpRef.current);
      oneShotFollowUpRef.current = null;
    }
  }, []);

  const isOneShot = ONE_SHOT_STATES.has(animationState);
  const currentClipUrl = resolveClipUrl(animationState);
  return {
    animationState,
    currentClipUrl,
    isOneShot,
    onClipEnded,
  };
}
