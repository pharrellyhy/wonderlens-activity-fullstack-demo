export function activitiesWithAssets(manifest) {
  return Array.isArray(manifest?.activities) ? manifest.activities : [];
}

export function assetForBeat(activity, beatId) {
  const match = activity?.beats?.find((beat) => beat.id === beatId);
  return match?.src || activity?.icon || '';
}

export function beatIdFromSessionState(sessionState) {
  const step = sessionState?.current_step || '';
  if (step === 'STEP_1_HOOK') return 'intro';
  if (step === 'STEP_2_RULES' || step === 'STEP_2_MISSION' || step === 'STEP_2_SETUP') return 'rules';
  if (
    step.startsWith('STEP_3_ROUND_') ||
    step.startsWith('STEP_3_COLLECT_') ||
    step.startsWith('STEP_3_BUILD_')
  ) {
    return `round_${sessionState?.current_round || 1}`;
  }
  if (step.includes('SYNTHESIS')) return 'synthesis';
  if (step.includes('CELEBRATE') || step.includes('CLOSING')) return 'recap';
  return 'intro';
}
