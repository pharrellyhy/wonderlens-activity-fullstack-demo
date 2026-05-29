import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { cwd } from 'node:process';
import { describe, expect, it } from 'vitest';
import manifest from '../public/activity-assets/activity-assets.manifest.json';
import {
  assetForBeat,
  activitiesWithAssets,
  beatIdFromSessionState,
  screenLayoutForBeat,
} from '../src/activityGame/activityAssets.js';

const publicRoot = join(cwd(), 'public');
const assetRoot = join(publicRoot, 'activity-assets');
const stylePromptPath = join(assetRoot, 'prompts', 'wonderlens-activity-style.md');
const STANDARD_BEATS = ['intro', 'rules', 'round_1', 'round_2', 'round_3', 'recap'];
const CAT5_BEATS = ['intro', 'rules', 'round_1', 'round_2', 'round_3', 'synthesis', 'recap'];
const LAYOUT_MODES = ['single', 'singleText', 'choice2', 'choice3', 'picker'];
const REPRESENTATIVE_ACTIVITY_IDS = new Set([
  'activity_career_decision_role_play',
  'activity_guided_drawing',
  'activity_phoneme_treasure_hunt',
]);

function expectPublicAssetExists(assetPath) {
  const relativePath = assetPath.replace(/^\//, '');
  expect(existsSync(join(publicRoot, relativePath)), `${assetPath} should exist`).toBe(true);
}

function publicAssetPath(assetPath) {
  return join(publicRoot, assetPath.replace(/^\//, ''));
}

function pngDimensions(assetPath) {
  const buffer = readFileSync(publicAssetPath(assetPath));
  expect(buffer.toString('ascii', 1, 4)).toBe('PNG');
  return {
    width: buffer.readUInt32BE(16),
    height: buffer.readUInt32BE(20),
  };
}

function expectLayoutAssetExists(assetPath, label) {
  expect(assetPath, `${label} should define a public asset path`).toMatch(/^\/activity-assets\//);
  expectPublicAssetExists(assetPath);
}

describe('activity asset manifest', () => {
  it('documents the flat Nordic vector asset direction without sculpted/contact-sheet language', () => {
    const prompt = readFileSync(stylePromptPath, 'utf8').toLowerCase();

    expect(prompt).toContain('flat nordic');
    expect(prompt).toContain('approved flat nursery references');
    expect(prompt).toContain('asymmetric simple animal silhouettes');
    expect(prompt).toContain('sparse black decorative strokes');
    expect(prompt).toContain('thin colored-pencil linework');
    expect(prompt).toContain('stroke system');
    expect(prompt).toContain('broad flat color fills');
    expect(prompt).toContain('helmet panel strokes');
    expect(prompt).toContain('internal contour bands');
    expect(prompt).toContain('blank clean white');
    expect(prompt).toContain('barely tinted white');
    expect(prompt).toContain('clean white padding');
    expect(prompt).toContain('oatmeal beige');
    expect(prompt).toContain('mustard/ochre');
    expect(prompt).toContain('tiny accents');
    expect(prompt).toContain('do not let mint');
    expect(prompt).not.toMatch(/\blight-3d\b|\b3d\b|\bclay\b|plasticine|playdough|contact sheet|contact-sheet/);
  });

  it('maps every activity to an icon and beat assets', () => {
    expect(activitiesWithAssets(manifest)).toHaveLength(12);
    for (const entry of manifest.activities) {
      expect(entry.icon).toMatch(/^\/activity-assets\//);
      const expectedBeats = entry.id === 'activity_phoneme_treasure_hunt' ? CAT5_BEATS : STANDARD_BEATS;
      expect(entry.beats.map((beat) => beat.id)).toEqual(expectedBeats);
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

  it('normalizes missing layout metadata into a single full-screen asset layout', () => {
    const activity = {
      icon: '/activity-assets/test/icon.png',
      beats: [{ id: 'intro', src: '/activity-assets/test/intro.png' }],
    };

    expect(screenLayoutForBeat(activity, 'intro')).toEqual({
      mode: 'single',
      safeArea: { canvas: 480, safe: 380, center: 300 },
      background: { src: '/activity-assets/test/intro.png', fit: 'cover' },
      items: [],
      selection: 'none',
      text: '',
    });
  });

  it('preserves explicit multi-asset screen layout metadata for device-rendered choices', () => {
    const layout = screenLayoutForBeat({
      icon: '/activity-assets/test/icon.png',
      beats: [
        {
          id: 'round_1',
          src: '/activity-assets/test/round_1.png',
          layout: {
            mode: 'choice2',
            selection: 'device-scroll',
            background: { src: '/activity-assets/test/background.png', fit: 'contain' },
            items: [
              { id: 'dog', src: '/activity-assets/test/dog.png', shape: 'circle', label: 'Dog' },
              { id: 'cat', src: '/activity-assets/test/cat.png', shape: 'rect3x4', label: 'Cat' },
            ],
          },
        },
      ],
    }, 'round_1');

    expect(layout).toEqual({
      mode: 'choice2',
      safeArea: { canvas: 480, safe: 380, center: 300 },
      background: { src: '/activity-assets/test/background.png', fit: 'contain' },
      selection: 'device-scroll',
      text: '',
      items: [
        { id: 'dog', src: '/activity-assets/test/dog.png', shape: 'circle', label: 'Dog' },
        { id: 'cat', src: '/activity-assets/test/cat.png', shape: 'rect3x4', label: 'Cat' },
      ],
    });
  });

  it('preserves singleText copy through layout normalization', () => {
    const layout = screenLayoutForBeat({
      icon: '/activity-assets/test/icon.png',
      beats: [
        {
          id: 'rules',
          src: '/activity-assets/test/rules.png',
          layout: {
            mode: 'singleText',
            text: 'Draw one big circle',
            background: { src: '/activity-assets/test/rules.png', fit: 'contain' },
          },
        },
      ],
    }, 'rules');

    expect(layout).toMatchObject({
      mode: 'singleText',
      text: 'Draw one big circle',
      selection: 'none',
    });
  });

  it('normalizes scroll-controlled three-or-more choices to picker instead of a crowded grid', () => {
    const layout = screenLayoutForBeat({
      icon: '/activity-assets/test/icon.png',
      beats: [
        {
          id: 'round_1',
          src: '/activity-assets/test/round_1.png',
          layout: {
            mode: 'choice3',
            selection: 'device-scroll',
            background: '/activity-assets/test/background.png',
            items: [
              { id: 'one', src: '/activity-assets/test/one.png', label: 'One' },
              { id: 'two', src: '/activity-assets/test/two.png', label: 'Two' },
              { id: 'three', src: '/activity-assets/test/three.png', label: 'Three' },
              { id: 'four', src: '/activity-assets/test/four.png', label: 'Four' },
            ],
          },
        },
      ],
    }, 'round_1');

    expect(layout.mode).toBe('picker');
    expect(layout.items).toHaveLength(4);
    expect(layout.selection).toBe('device-scroll');
  });

  it('uses the approved representative interaction layouts for Cat1 Cat3 and Cat5', () => {
    const byId = new Map(manifest.activities.map((entry) => [entry.id, entry]));
    const career = byId.get('activity_career_decision_role_play');
    const guided = byId.get('activity_guided_drawing');
    const phoneme = byId.get('activity_phoneme_treasure_hunt');

    for (const beatId of ['round_1', 'round_2', 'round_3']) {
      expect(screenLayoutForBeat(career, beatId)).toMatchObject({
        mode: 'single',
        selection: 'none',
        items: [],
      });
      expect(screenLayoutForBeat(guided, beatId)).toMatchObject({
        mode: 'single',
        selection: 'none',
        items: [],
      });
      expect(screenLayoutForBeat(phoneme, beatId)).toMatchObject({
        mode: 'picker',
        selection: 'device-scroll',
      });
      expect(screenLayoutForBeat(phoneme, beatId).items).toHaveLength(3);
    }

    expect(screenLayoutForBeat(phoneme, 'synthesis')).toMatchObject({
      mode: 'picker',
      selection: 'none',
    });
  });

  it('documents every supported screen layout mode in the manifest', () => {
    expect(manifest.screen_style.layouts).toEqual(LAYOUT_MODES);
  });

  it('uses square 512px PNGs for every displayed activity asset', () => {
    for (const entry of manifest.activities) {
      expect(pngDimensions(entry.icon)).toEqual({ width: 512, height: 512 });
      for (const beat of entry.beats) {
        expect(pngDimensions(beat.src)).toEqual({ width: 512, height: 512 });
      }
    }
  });

  it('scopes explicit pilot layout metadata to the representative runtime beats', () => {
    for (const entry of manifest.activities) {
      for (const beat of entry.beats) {
        if (!REPRESENTATIVE_ACTIVITY_IDS.has(entry.id)) {
          expect(beat.layout, `${entry.id}/${beat.id} stays outside the three-activity pilot`).toBeUndefined();
          continue;
        }

        expect(beat.layout, `${entry.id}/${beat.id} should define pilot layout metadata`).toBeTruthy();
        const layout = screenLayoutForBeat(entry, beat.id);
        expect(LAYOUT_MODES, `${entry.id}/${beat.id} should use a known layout mode`).toContain(layout.mode);
        expect(layout.safeArea).toEqual({ canvas: 480, safe: 380, center: 300 });
        expectLayoutAssetExists(layout.background.src, `${entry.id}/${beat.id} background`);
        expect(['cover', 'contain']).toContain(layout.background.fit);

        if (layout.mode === 'single' || layout.mode === 'singleText') {
          expect(layout.items, `${entry.id}/${beat.id} single layouts should not need item cards`).toHaveLength(0);
        } else {
          expect(layout.items.length, `${entry.id}/${beat.id} multi-asset layouts need at least two items`).toBeGreaterThanOrEqual(2);
        }

        for (const item of layout.items) {
          expect(item.id, `${entry.id}/${beat.id} item id`).toBeTruthy();
          expect(['circle', 'rect3x4']).toContain(item.shape);
          expect(item.label.trim().split(/\s+/).length, `${entry.id}/${beat.id} item labels stay short`).toBeLessThanOrEqual(2);
          expectLayoutAssetExists(item.src, `${entry.id}/${beat.id}/${item.id}`);
        }
      }
    }
  });

  it('maps session steps to variable beat ids', () => {
    expect(beatIdFromSessionState({ current_step: 'STEP_1_HOOK' })).toBe('intro');
    expect(beatIdFromSessionState({ current_step: 'STEP_2_RULES' })).toBe('rules');
    expect(beatIdFromSessionState({ current_step: 'STEP_2_MISSION' })).toBe('rules');
    expect(beatIdFromSessionState({ current_step: 'STEP_2_SETUP' })).toBe('rules');
    expect(beatIdFromSessionState({ current_step: 'STEP_3_ROUND_3', current_round: 3 })).toBe('round_3');
    expect(beatIdFromSessionState({ current_step: 'STEP_3_ROUND_3' })).toBe('round_3');
    expect(beatIdFromSessionState({ current_step: 'STEP_3_ROUND_3', current_round: 1 })).toBe('round_3');
    expect(beatIdFromSessionState({ current_step: 'STEP_3_COLLECT_1', current_round: 1 })).toBe('round_1');
    expect(beatIdFromSessionState({ current_step: 'STEP_3_BUILD_2', current_round: 2 })).toBe('round_2');
    expect(beatIdFromSessionState({ current_step: 'STEP_4_SYNTHESIS' })).toBe('synthesis');
    expect(beatIdFromSessionState({ current_step: 'STEP_4_CELEBRATE' })).toBe('recap');
    expect(beatIdFromSessionState({ current_step: 'STEP_5_CELEBRATE' })).toBe('recap');
    expect(beatIdFromSessionState({ current_step: 'STEP_5_CLOSING' })).toBe('recap');
    expect(beatIdFromSessionState({ current_step: 'STEP_6_CLOSING' })).toBe('recap');
  });
});
