import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import ActivityGameApp from '../src/activityGame/ActivityGameApp.jsx';
import manifest from '../public/activity-assets/activity-assets.manifest.json';
import { sendTurn, startActivitySession } from '../src/utils/api.js';

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
    }, {
      id: 'activity_phoneme_treasure_hunt',
      name: 'Phoneme Treasure Hunt',
      kind: 'activity',
      category: 'category_5',
      mechanic: 'collect',
      tier: 'T1',
      premise: 'Find words that start with one sound.',
      core_ib_key_concepts: ['Form', 'Connection'],
      asset_manifest_id: 'activity_phoneme_treasure_hunt',
    }, {
      id: 'activity_guided_drawing',
      name: 'Guided Drawing',
      kind: 'activity',
      category: 'category_3',
      mechanic: 'build',
      tier: 'T1',
      premise: 'Draw one small step at a time.',
      core_ib_key_concepts: ['Form', 'Change'],
      asset_manifest_id: 'activity_guided_drawing',
    }],
  })),
  fetchActivityAssetManifest: vi.fn(async () => manifest),
  startActivitySession: vi.fn(),
  sendTurn: vi.fn(),
}));

describe('ActivityGameApp', () => {
  afterEach(() => {
    vi.mocked(startActivitySession).mockReset();
    vi.mocked(sendTurn).mockReset();
  });

  it('uses activity wording and no multimodal controls', async () => {
    render(<ActivityGameApp />);

    expect(await screen.findByText('WonderLens Prototype')).toBeTruthy();
    expect(await screen.findByText('Activities')).toBeTruthy();
    expect(await screen.findByText('Device Preview')).toBeTruthy();
    expect(await screen.findAllByAltText('Word Echo Practice icon')).toHaveLength(2);
    expect(screen.getAllByText('Word Echo Practice').length).toBeGreaterThan(0);
    expect(screen.queryByLabelText(/Voice input/i)).toBeNull();
    expect(screen.queryByText(/Choose a concept/i)).toBeNull();
    expect(screen.queryByText(/concept/i)).toBeNull();
    expect(screen.queryByLabelText(/Upload photo/i)).toBeNull();
    expect(screen.queryByLabelText('Layout controls')).toBeNull();
    expect(screen.queryByText('Transcript width')).toBeNull();
  });

  it('uses upper and lower scroll controls to move through activities', async () => {
    render(<ActivityGameApp />);

    expect(await screen.findByRole('heading', { name: 'Word Echo Practice' })).toBeTruthy();

    fireEvent.click(screen.getByLabelText('Next activity'));
    expect(screen.getByRole('heading', { name: 'Animal Sound Imitation' })).toBeTruthy();

    fireEvent.click(screen.getByLabelText('Previous activity'));
    expect(screen.getByRole('heading', { name: 'Word Echo Practice' })).toBeTruthy();
  });

  it('locks activity switching while a session exists and exits back to idle display', async () => {
    vi.mocked(startActivitySession).mockResolvedValue({
      session_id: 's1',
      activity_type: 'activity_word_echo_practice',
      template_type: 'cat1',
      session_state: { status: 'active', current_step: 'STEP_1_HOOK', current_round: 0, total_rounds: 3 },
      first_turn: { dialogue: 'Echo time!', response_type: 'hook' },
    });

    render(<ActivityGameApp />);

    expect(await screen.findByRole('heading', { name: 'Word Echo Practice' })).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Start activity'));

    expect(await screen.findByText('Echo time!')).toBeTruthy();
    expect(screen.getByLabelText('Next activity').disabled).toBe(true);
    expect(screen.queryByLabelText('Next device option')).toBeNull();
    expect(screen.queryByLabelText('Confirm selected device option')).toBeNull();
    expect(screen.getByLabelText('Start activity').disabled).toBe(true);
    expect(screen.getByRole('button', { name: /Animal Sound Imitation/i }).disabled).toBe(true);
    expect(screen.getAllByRole('button', { name: 'Exit activity' })).toHaveLength(1);

    fireEvent.click(screen.getByRole('button', { name: 'Exit activity' }));

    expect(screen.queryByText('Echo time!')).toBeNull();
    expect(screen.getByLabelText('Next activity').disabled).toBe(false);
    expect(screen.getByRole('button', { name: /Animal Sound Imitation/i }).disabled).toBe(false);
  });

  it('uses physical device controls for Cat5 collection item selection', async () => {
    vi.mocked(startActivitySession).mockResolvedValue({
      session_id: 'cat5',
      activity_type: 'activity_phoneme_treasure_hunt',
      template_type: 'cat5',
      session_state: {
        status: 'active',
        template_type: 'cat5',
        current_step: 'STEP_3_COLLECT_1',
        current_round: 1,
        total_rounds: 3,
        collection_phase: 'photo',
        collection_criterion: 'Choose a word that starts with b',
        collected_photos: [],
        current_round_items: [
          { id: 'ball', label: 'Ball', image: '/activity-assets/activity_phoneme_treasure_hunt/items/ball.png' },
          { id: 'cup', label: 'Cup', image: '/activity-assets/activity_phoneme_treasure_hunt/items/cup.png' },
        ],
      },
      first_turn: { dialogue: 'Pick the sound treasure.', response_type: 'round' },
    });
    vi.mocked(sendTurn).mockResolvedValue({
      session_state: {
        status: 'active',
        template_type: 'cat5',
        current_step: 'STEP_3_COLLECT_1',
        current_round: 1,
        total_rounds: 3,
        collection_phase: 'detail',
        collected_photos: ['ball'],
      },
      turn: { dialogue: 'Ball works. What sound does it start with?', response_type: 'detail' },
    });

    render(<ActivityGameApp />);

    fireEvent.click(await screen.findByRole('button', { name: /Phoneme Treasure Hunt/i }));
    fireEvent.click(screen.getByLabelText('Start activity'));

    expect(await screen.findByText('Ball')).toBeTruthy();
    expect(screen.queryByText('Choose a word that starts with b')).toBeNull();
    expect(screen.getByText('Cup')).toBeTruthy();
    expect(screen.getByRole('textbox', { name: 'Text response' }).disabled).toBe(true);
    expect(screen.queryByRole('button', { name: 'Select: Ball' })).toBeNull();
    expect(document.querySelector('.activity-screen-layout__item.is-selected span')?.textContent).toBe('Ball');

    fireEvent.click(screen.getByLabelText('Next device option'));
    expect(document.querySelector('.activity-screen-layout__item.is-selected span')?.textContent).toBe('Cup');

    fireEvent.click(screen.getByLabelText('Previous device option'));
    expect(document.querySelector('.activity-screen-layout__item.is-selected span')?.textContent).toBe('Ball');

    fireEvent.click(screen.getByLabelText('Confirm selected device option'));

    expect(vi.mocked(sendTurn)).toHaveBeenCalledWith('cat5', '', false, 'ball');
    expect(await screen.findByText('Ball works. What sound does it start with?')).toBeTruthy();
  });

  it('unlocks Cat5 text input after a selected item is recorded for the current round', async () => {
    vi.mocked(startActivitySession).mockResolvedValue({
      session_id: 'cat5',
      activity_type: 'activity_phoneme_treasure_hunt',
      template_type: 'cat5',
      session_state: {
        status: 'active',
        template_type: 'cat5',
        current_step: 'STEP_3_COLLECT_1',
        current_round: 1,
        total_rounds: 3,
        collection_phase: 'photo',
        collection_criterion: 'Choose a word that starts with b',
        collected_photos: [],
        current_round_items: [
          { id: 'ball', label: 'Ball', image: '/activity-assets/activity_phoneme_treasure_hunt/items/ball.png' },
          { id: 'cup', label: 'Cup', image: '/activity-assets/activity_phoneme_treasure_hunt/items/cup.png' },
        ],
      },
      first_turn: { dialogue: 'Pick the sound treasure.', response_type: 'round' },
    });
    vi.mocked(sendTurn).mockResolvedValue({
      session_state: {
        status: 'active',
        template_type: 'cat5',
        current_step: 'STEP_3_COLLECT_1',
        current_round: 1,
        total_rounds: 3,
        collection_phase: 'photo',
        collection_criterion: 'Choose a word that starts with b',
        collected_photos: ['ball'],
        current_round_items: [
          { id: 'ball', label: 'Ball', image: '/activity-assets/activity_phoneme_treasure_hunt/items/ball.png' },
          { id: 'cup', label: 'Cup', image: '/activity-assets/activity_phoneme_treasure_hunt/items/cup.png' },
        ],
      },
      turn: { dialogue: 'Ball works. What sound does it start with?', response_type: 'detail' },
    });

    render(<ActivityGameApp />);

    fireEvent.click(await screen.findByRole('button', { name: /Phoneme Treasure Hunt/i }));
    fireEvent.click(screen.getByLabelText('Start activity'));
    expect(await screen.findByText('Ball')).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Confirm selected device option'));

    expect(await screen.findByText('Ball works. What sound does it start with?')).toBeTruthy();
    expect(screen.queryByRole('button', { name: 'Select: Ball' })).toBeNull();
    expect(document.querySelector('.activity-screen-layout__item.is-selected span')?.textContent).toBe('Ball');
    expect(screen.getByRole('textbox', { name: 'Text response' }).disabled).toBe(false);
  });

  it('uses physical device controls for Cat3 build quick actions', async () => {
    vi.mocked(startActivitySession).mockResolvedValue({
      session_id: 'cat3',
      activity_type: 'activity_guided_drawing',
      template_type: 'cat3',
      session_state: {
        status: 'active',
        template_type: 'cat3',
        current_step: 'STEP_3_BUILD_1',
        current_round: 1,
        total_rounds: 3,
        current_build_step: 'Draw one simple line or shape to start the picture.',
        build_materials: ['paper', 'pencil'],
      },
      first_turn: { dialogue: 'Make the first mark.', response_type: 'round' },
    });
    vi.mocked(sendTurn).mockResolvedValue({
      session_state: {
        status: 'active',
        template_type: 'cat3',
        current_step: 'STEP_3_BUILD_2',
        current_round: 2,
        total_rounds: 3,
        current_build_step: 'Add one small detail that changes the picture.',
        build_materials: ['paper', 'pencil'],
      },
      turn: { dialogue: 'Nice. Add one detail now.', response_type: 'round' },
    });

    render(<ActivityGameApp />);

    fireEvent.click(await screen.findByRole('button', { name: /Guided Drawing/i }));
    fireEvent.click(screen.getByLabelText('Start activity'));

    expect((await screen.findByRole('option', { name: 'Done' })).getAttribute('aria-selected')).toBe('true');
    expect(screen.getByRole('option', { name: 'Help' }).getAttribute('aria-selected')).toBe('false');
    expect(screen.queryByText('Draw one simple line or shape to start the picture.')).toBeNull();
    expect(screen.queryByText('paper + pencil')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Done' })).toBeNull();

    fireEvent.click(screen.getByLabelText('Next device option'));
    expect(screen.getByRole('option', { name: 'Done' }).getAttribute('aria-selected')).toBe('false');
    expect(screen.getByRole('option', { name: 'Help' }).getAttribute('aria-selected')).toBe('true');

    fireEvent.click(screen.getByLabelText('Confirm selected device option'));

    expect(vi.mocked(sendTurn)).toHaveBeenCalledWith('cat3', 'help', false);
    expect(await screen.findByText('Nice. Add one detail now.')).toBeTruthy();
  });
});
