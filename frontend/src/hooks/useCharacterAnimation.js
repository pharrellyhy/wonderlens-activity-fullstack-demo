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
  const [animationState, setAnimationState] = useState('waving');
  const oneShotFollowUpRef = useRef(null);
  const lastProcessedMsgRef = useRef(0);

  const entity = entityFromActivity(activityType);
  const theme = entity ? getThemeForEntity(entity) : null;
  const hasVideo = !!(theme?.videoPrefix);

  // Determine the "resting" state — what to show after TTS/reactions finish
  const restingState =
    currentStep === 'STEP_4_CELEBRATE' ? 'celebrating' :
    currentStep === 'STEP_5_CLOSING' || currentStep === 'ENDED' ? 'waving' :
    currentStep?.startsWith('STEP_3_') && currentRound >= 1 && currentScenario ? 'scenario' :
    'idle';

  // Resolve clip URL from animation state
  const resolveClipUrl = useCallback((state) => {
    if (!hasVideo || !theme?.videoBasePath || !theme?.videoPrefix) return null;

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
  }, [hasVideo, theme?.videoBasePath, theme?.videoPrefix, theme?.scenarioBasePath, currentScenario, activityType]);

  // 1. Session start — waving immediately (no TTS playing yet)
  useEffect(() => {
    if (!hasVideo) return;
    if (currentStep === 'STEP_1_HOOK') {
      setAnimationState('waving');
    }
  }, [currentStep, hasVideo]);

  // 2. AI response — set character emotion clip. TTS audio plays on top (overlapped).
  useEffect(() => {
    if (!hasVideo || !characterState || messageCount <= lastProcessedMsgRef.current) return;
    lastProcessedMsgRef.current = messageCount;

    setAnimationState(characterState);
    // One-shot clips return to resting state after playing; loops keep going
    oneShotFollowUpRef.current = ONE_SHOT_STATES.has(characterState) ? restingState : null;
  }, [characterState, messageCount, hasVideo, restingState]);

  // 3. When TTS ends (true→false), return to resting state (scenario or idle).
  const wasSpeakingRef = useRef(false);
  useEffect(() => {
    if (!hasVideo) return;
    if (isSpeaking) {
      wasSpeakingRef.current = true;
    } else if (wasSpeakingRef.current) {
      wasSpeakingRef.current = false;
      setAnimationState(prev => {
        if (prev === 'waving' || prev === 'celebrating') return prev;
        return restingState;
      });
    }
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
