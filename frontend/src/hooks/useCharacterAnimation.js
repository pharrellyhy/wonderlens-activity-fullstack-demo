import { useState, useCallback, useEffect, useRef } from 'react';
import { getThemeForEntity, getScenarioSlug } from '../widgets/gameThemes';

const ONE_SHOT_STATES = new Set(['excited', 'encouraging', 'surprised', 'waving']);

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
}) {
  const [animationState, setAnimationState] = useState('idle');
  const oneShotFollowUpRef = useRef(null);
  const lastProcessedMsgRef = useRef(0);

  const entity = entityFromActivity(activityType);
  const theme = entity ? getThemeForEntity(entity) : null;
  const hasVideo = !!(theme?.videoPrefix);

  // Determine the "resting" state — what to return to after reactions finish
  const restingState = currentStep?.startsWith('STEP_3_') && currentRound >= 1 && currentScenario
    ? 'scenario'
    : 'idle';

  // Resolve clip URL from animation state
  const resolveClipUrl = useCallback((state) => {
    if (!hasVideo || !theme?.videoBasePath || !theme?.videoPrefix) return null;

    if (state === 'scenario') {
      if (!theme?.scenarioBasePath || !currentScenario) {
        // Fallback to character idle if scenario can't be resolved
        return `${theme.videoBasePath}/${theme.videoPrefix}_idle.mp4`;
      }
      const slug = getScenarioSlug(activityType, currentScenario);
      if (!slug) return `${theme.videoBasePath}/${theme.videoPrefix}_idle.mp4`;
      return `${theme.scenarioBasePath}/scenario_${slug}.mp4`;
    }

    return `${theme.videoBasePath}/${theme.videoPrefix}_${state}.mp4`;
  }, [hasVideo, theme?.videoBasePath, theme?.videoPrefix, theme?.scenarioBasePath, currentScenario, activityType]);

  // 1. Session lifecycle — waving at start/end
  useEffect(() => {
    if (!hasVideo) return;
    if (currentStep === 'STEP_1_HOOK' || currentStep === 'STEP_5_CLOSING' || currentStep === 'ENDED') {
      setAnimationState('waving');
      oneShotFollowUpRef.current = restingState;
    }
  }, [currentStep, hasVideo, restingState]);

  // 2. AI response — set character emotion, triggered by new messages
  useEffect(() => {
    if (!hasVideo || !characterState || messageCount <= lastProcessedMsgRef.current) return;
    lastProcessedMsgRef.current = messageCount;

    if (ONE_SHOT_STATES.has(characterState)) {
      setAnimationState(characterState);
      oneShotFollowUpRef.current = 'speaking';
    } else {
      setAnimationState(characterState);
      oneShotFollowUpRef.current = null;
    }
  }, [characterState, messageCount, hasVideo]);

  // 3. TTS state — when TTS ends, return to resting state
  useEffect(() => {
    if (!hasVideo) return;
    if (!isSpeaking) {
      // TTS finished — return to resting state (scenario or idle)
      setAnimationState(prev => {
        if (prev === 'waving') return prev;
        return restingState;
      });
    }
  }, [isSpeaking, hasVideo, restingState]);

  // 4. Round/scenario change — update resting state clip
  useEffect(() => {
    if (!hasVideo) return;
    if (restingState === 'scenario' && !isSpeaking) {
      setAnimationState('scenario');
    }
  }, [currentScenario, currentRound, hasVideo, restingState, isSpeaking]);

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
