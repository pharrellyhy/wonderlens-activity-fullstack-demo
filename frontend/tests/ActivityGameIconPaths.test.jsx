import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ActivityGameApp from '../src/activityGame/ActivityGameApp.jsx';

vi.mock('../src/utils/basePath.js', () => ({
  default: '/wonderlens',
  asset: (path) => (path ? `/wonderlens${path}` : path),
}));

vi.mock('../src/utils/api.js', () => ({
  fetchActivities: vi.fn(async () => ({
    count: 1,
    activities: [{
      id: 'activity_word_echo_practice',
      name: 'Word Echo Practice',
      kind: 'activity',
      category: 'category_1',
      mechanic: 'remember',
      tier: 'T1',
      premise: 'Repeat a word back.',
      core_ib_key_concepts: ['Form'],
      asset_manifest_id: 'activity_word_echo_practice',
    }],
  })),
  fetchActivityAssetManifest: vi.fn(async () => ({
    activities: [{
      id: 'activity_word_echo_practice',
      icon: '/activity-assets/activity_word_echo_practice/icon.png',
      beats: [{
        id: 'intro',
        src: '/activity-assets/activity_word_echo_practice/intro.png',
        layout: { mode: 'single', background: { src: '/activity-assets/activity_word_echo_practice/intro.png' } },
      }],
    }],
  })),
  startActivitySession: vi.fn(),
  sendTurn: vi.fn(),
}));

describe('ActivityGameApp icon paths', () => {
  it('prefixes activity library and preview icons with the deployment base path', async () => {
    render(<ActivityGameApp />);

    const icons = await screen.findAllByAltText('Word Echo Practice icon');

    expect(icons).toHaveLength(2);
    icons.forEach((icon) => {
      expect(icon.getAttribute('src')).toBe('/wonderlens/activity-assets/activity_word_echo_practice/icon.png');
    });
  });
});
