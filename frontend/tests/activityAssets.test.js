import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';
import manifest from '../public/activity-assets/activity-assets.manifest.json';
import { assetForBeat, activitiesWithAssets, beatIdFromSessionState } from '../src/activityGame/activityAssets.js';

const publicRoot = join(process.cwd(), 'public');

function expectPublicAssetExists(assetPath) {
  const relativePath = assetPath.replace(/^\//, '');
  expect(existsSync(join(publicRoot, relativePath)), `${assetPath} should exist`).toBe(true);
}

describe('activity asset manifest', () => {
  it('maps every activity to an icon and beat assets', () => {
    expect(activitiesWithAssets(manifest)).toHaveLength(12);
    for (const entry of manifest.activities) {
      expect(entry.icon).toMatch(/^\/activity-assets\//);
      expect(entry.beats.length).toBeGreaterThanOrEqual(5);
      expect(entry.beats.map((beat) => beat.id)).toContain('intro');
      expect(entry.beats.map((beat) => beat.id)).toContain('recap');
      expectPublicAssetExists(entry.icon);
      for (const beat of entry.beats) {
        expectPublicAssetExists(beat.src);
      }
    }
  });

  it('falls back to icon when a beat is missing', () => {
    const activity = manifest.activities[0];
    expect(assetForBeat(activity, 'unknown')).toBe(activity.icon);
  });

  it('maps session steps to variable beat ids', () => {
    expect(beatIdFromSessionState({ current_step: 'STEP_1_HOOK' })).toBe('intro');
    expect(beatIdFromSessionState({ current_step: 'STEP_2_SETUP' })).toBe('rules');
    expect(beatIdFromSessionState({ current_step: 'STEP_3_BUILD_2', current_round: 2 })).toBe('round_2');
    expect(beatIdFromSessionState({ current_step: 'STEP_4_SYNTHESIS' })).toBe('synthesis');
    expect(beatIdFromSessionState({ current_step: 'STEP_5_CLOSING' })).toBe('recap');
  });
});
