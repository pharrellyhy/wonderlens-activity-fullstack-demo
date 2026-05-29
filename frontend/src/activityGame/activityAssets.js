export function activitiesWithAssets(manifest) {
  return Array.isArray(manifest?.activities) ? manifest.activities : [];
}

const DEFAULT_SAFE_AREA = { canvas: 480, safe: 380, center: 300 };
const SUPPORTED_LAYOUT_MODES = new Set(['single', 'singleText', 'choice2', 'choice3', 'picker']);

export function beatForId(activity, beatId) {
  return activity?.beats?.find((beat) => beat.id === beatId) || null;
}

export function assetForBeat(activity, beatId) {
  const match = beatForId(activity, beatId);
  return match?.src || activity?.icon || '';
}

function normalizedSafeArea(rawSafeArea) {
  return {
    canvas: rawSafeArea?.canvas || DEFAULT_SAFE_AREA.canvas,
    safe: rawSafeArea?.safe || DEFAULT_SAFE_AREA.safe,
    center: rawSafeArea?.center || DEFAULT_SAFE_AREA.center,
  };
}

function normalizedBackground(rawBackground, fallbackSrc) {
  if (typeof rawBackground === 'string') {
    return { src: rawBackground || fallbackSrc, fit: 'cover' };
  }

  return {
    src: rawBackground?.src || fallbackSrc,
    fit: rawBackground?.fit || 'cover',
  };
}

function normalizedLayoutItem(item, index, fallbackSrc) {
  const normalized = {
    id: item?.id || `item_${index + 1}`,
    src: item?.src || fallbackSrc,
    shape: item?.shape || 'circle',
    label: item?.label || '',
  };
  if (item?.selected) normalized.selected = true;
  return normalized;
}

function normalizedLayoutMode(rawMode, items, selection) {
  if (rawMode === 'carousel') return 'picker';
  if (selection === 'device-scroll' && items.length >= 3) return 'picker';
  if (items.length >= 4) return 'picker';
  if (SUPPORTED_LAYOUT_MODES.has(rawMode)) return rawMode;
  if (items.length === 3) return 'choice3';
  if (items.length === 2) return 'choice2';
  return 'single';
}

export function screenLayoutForBeat(activity, beatId) {
  const beat = beatForId(activity, beatId);
  const fallbackSrc = beat?.src || activity?.icon || '';
  const layout = beat?.layout || {};
  const items = Array.isArray(layout.items)
    ? layout.items.map((item, index) => normalizedLayoutItem(item, index, fallbackSrc))
    : [];
  const selection = layout.selection || (items.length > 1 ? 'device-scroll' : 'none');

  return {
    mode: normalizedLayoutMode(layout.mode || 'single', items, selection),
    safeArea: normalizedSafeArea(layout.safeArea || layout.safe_area),
    background: normalizedBackground(layout.background, fallbackSrc),
    items,
    selection,
    text: layout.text || beat?.text || '',
  };
}

function roundIdFromStep(step, fallbackRound) {
  const stepRound = step.match(/^STEP_3_(?:ROUND|COLLECT|BUILD)_(\d+)/)?.[1];
  return `round_${stepRound || fallbackRound || 1}`;
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
    return roundIdFromStep(step, sessionState?.current_round);
  }
  if (step.includes('SYNTHESIS')) return 'synthesis';
  if (step.includes('CELEBRATE') || step.includes('CLOSING')) return 'recap';
  return 'intro';
}
