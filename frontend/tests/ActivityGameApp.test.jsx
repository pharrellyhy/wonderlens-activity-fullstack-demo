import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ActivityGameApp from '../src/activityGame/ActivityGameApp.jsx';
import manifest from '../public/activity-assets/activity-assets.manifest.json';

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
    }, {
      id: 'activity_animal_sound_imitation',
      name: 'Animal Sound Imitation',
      kind: 'activity',
      category: 'category_1',
      mechanic: 'motion_voice',
      tier: 'T1',
      premise: 'Imitate an animal sound.',
      core_ib_key_concepts: ['Form'],
      asset_manifest_id: 'activity_animal_sound_imitation',
    }],
  })),
  fetchActivityAssetManifest: vi.fn(async () => manifest),
  startActivitySession: vi.fn(),
  sendTurn: vi.fn(),
}));

describe('ActivityGameApp', () => {
  it('uses activity wording and no multimodal controls', async () => {
    render(<ActivityGameApp />);

    expect(await screen.findByText('Activity library')).toBeTruthy();
    expect(await screen.findAllByAltText('Word Echo Practice icon')).toHaveLength(2);
    expect(screen.getAllByText('Word Echo Practice').length).toBeGreaterThan(0);
    expect(screen.queryByLabelText(/Voice input/i)).toBeNull();
    expect(screen.queryByText(/Choose a concept/i)).toBeNull();
    expect(screen.queryByLabelText(/Upload photo/i)).toBeNull();
  });

  it('uses upper and lower scroll controls to move through activities', async () => {
    render(<ActivityGameApp />);

    expect(await screen.findByRole('heading', { name: 'Word Echo Practice' })).toBeTruthy();

    fireEvent.click(screen.getByLabelText('Next activity'));
    expect(screen.getByRole('heading', { name: 'Animal Sound Imitation' })).toBeTruthy();

    fireEvent.click(screen.getByLabelText('Previous activity'));
    expect(screen.getByRole('heading', { name: 'Word Echo Practice' })).toBeTruthy();
  });
});
