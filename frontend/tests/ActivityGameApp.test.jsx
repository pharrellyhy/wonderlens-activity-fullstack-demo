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
      id: 'activity_career_decision_role_play',
      name: 'Career Decision Role Play',
      kind: 'activity',
      category: 'category_1',
      mechanic: 'decide',
      tier: 'T1',
      premise: 'Make firefighter safety choices.',
      core_ib_key_concepts: ['Form', 'Responsibility'],
      asset_manifest_id: 'activity_career_decision_role_play',
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
    }, {
      id: 'activity_recognition_pop_challenge',
      name: 'Recognition Pop Challenge',
      kind: 'activity',
      category: 'category_1',
      mechanic: 'compare',
      tier: 'T1',
      premise: 'Find the picture that matches the target.',
      core_ib_key_concepts: ['Form'],
      asset_manifest_id: 'activity_recognition_pop_challenge',
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

  it('lets testers adjust the activity game grid size', async () => {
    render(<ActivityGameApp />);

    expect(await screen.findByText('WonderLens Prototype')).toBeTruthy();
    const grid = document.querySelector('.activity-game');
    const sizeInput = screen.getByLabelText('Activity game grid size');

    expect(grid.style.getPropertyValue('--activity-game-size')).toBe('1.00');
    expect(sizeInput.value).toBe('1');
    expect(sizeInput.max).toBe('1.5');
    expect(screen.getByText('100%')).toBeTruthy();

    fireEvent.change(sizeInput, { target: { value: '1.12' } });

    expect(grid.style.getPropertyValue('--activity-game-size')).toBe('1.12');
    expect(screen.getByText('112%')).toBeTruthy();
  });

  it('keeps the grid stable while the size slider is dragged', async () => {
    render(<ActivityGameApp />);

    expect(await screen.findByText('WonderLens Prototype')).toBeTruthy();
    const grid = document.querySelector('.activity-game');
    const sizeInput = screen.getByLabelText('Activity game grid size');

    fireEvent.pointerDown(sizeInput);
    fireEvent.change(sizeInput, { target: { value: '1.5' } });

    expect(sizeInput.value).toBe('1.5');
    expect(screen.getByText('150%')).toBeTruthy();
    expect(grid.style.getPropertyValue('--activity-game-size')).toBe('1.00');

    fireEvent.pointerUp(sizeInput);

    expect(grid.style.getPropertyValue('--activity-game-size')).toBe('1.50');
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
          { id: 'book', label: 'Book', image: '/activity-assets/activity_phoneme_treasure_hunt/items/book.png' },
        ],
      },
      first_turn: { dialogue: 'Pick the B word.', response_type: 'round' },
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
      turn: { dialogue: 'Ball works. Which B word did you choose?', response_type: 'detail' },
    });

    render(<ActivityGameApp />);

    fireEvent.click(await screen.findByRole('button', { name: /Phoneme Treasure Hunt/i }));
    fireEvent.click(screen.getByLabelText('Start activity'));

    expect(await screen.findByText('Ball')).toBeTruthy();
    expect(screen.queryByText('Choose a word that starts with b')).toBeNull();
    expect(screen.getByText('Cup')).toBeTruthy();
    expect(screen.getByText('Book')).toBeTruthy();
    expect(document.querySelector('.activity-screen-layout--picker')).toBeTruthy();
    expect(screen.getByRole('textbox', { name: 'Text response' }).disabled).toBe(true);
    expect(screen.queryByRole('button', { name: 'Select: Ball' })).toBeNull();
    expect(document.querySelector('.activity-screen-layout__item.is-selected span')?.textContent).toBe('Ball');

    fireEvent.click(screen.getByLabelText('Next device option'));
    expect(document.querySelector('.activity-screen-layout__item.is-selected span')?.textContent).toBe('Cup');

    fireEvent.click(screen.getByLabelText('Previous device option'));
    expect(document.querySelector('.activity-screen-layout__item.is-selected span')?.textContent).toBe('Ball');

    fireEvent.click(screen.getByLabelText('Confirm selected device option'));

    expect(vi.mocked(sendTurn)).toHaveBeenCalledWith('cat5', '', false, 'ball');
    expect(await screen.findByText('Ball works. Which B word did you choose?')).toBeTruthy();
  });

  it('uses collected Cat5 item order for synthesis instead of static manifest recap items', async () => {
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
        collected_photos: [],
        current_round_items: [
          { id: 'ball', label: 'Ball', image: '/activity-assets/activity_phoneme_treasure_hunt/items/ball.png' },
          { id: 'cup', label: 'Cup', image: '/activity-assets/activity_phoneme_treasure_hunt/items/cup.png' },
          { id: 'book', label: 'Book', image: '/activity-assets/activity_phoneme_treasure_hunt/items/book.png' },
        ],
      },
      first_turn: { dialogue: 'Pick the first B word.', response_type: 'round' },
    });
    vi.mocked(sendTurn).mockResolvedValue({
      session_state: {
        status: 'active',
        template_type: 'cat5',
        current_step: 'STEP_4_SYNTHESIS',
        current_round: 3,
        total_rounds: 3,
        collection_phase: 'photo',
        collected_photos: ['ball', 'basket', 'banana'],
      },
      turn: { dialogue: 'Ready for the B chant.', response_type: 'synthesis' },
    });

    render(<ActivityGameApp />);

    fireEvent.click(await screen.findByRole('button', { name: /Phoneme Treasure Hunt/i }));
    fireEvent.click(screen.getByLabelText('Start activity'));
    expect(await screen.findByText('Ball')).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Confirm selected device option'));

    expect(await screen.findByText('Ready for the B chant.')).toBeTruthy();
    const labels = Array.from(
      document.querySelectorAll('.activity-screen-layout--picker .activity-screen-layout__item span'),
    ).map((node) => node.textContent);
    expect(labels).toEqual(['Ball', 'Basket', 'Banana']);
    expect(labels).not.toContain('Book');
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
      turn: { dialogue: 'Ball works. Which B word did you choose?', response_type: 'detail' },
    });

    render(<ActivityGameApp />);

    fireEvent.click(await screen.findByRole('button', { name: /Phoneme Treasure Hunt/i }));
    fireEvent.click(screen.getByLabelText('Start activity'));
    expect(await screen.findByText('Ball')).toBeTruthy();
    fireEvent.click(screen.getByLabelText('Confirm selected device option'));

    expect(await screen.findByText('Ball works. Which B word did you choose?')).toBeTruthy();
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
        current_step: 'STEP_3_BUILD_1',
        current_round: 1,
        total_rounds: 3,
        current_build_step: 'Draw one simple line or shape to start the picture.',
        build_materials: ['paper', 'pencil'],
      },
      turn: { dialogue: 'Try the same first mark again. I can help with that step.', response_type: 'round' },
    });

    render(<ActivityGameApp />);

    fireEvent.click(await screen.findByRole('button', { name: /Guided Drawing/i }));
    fireEvent.click(screen.getByLabelText('Start activity'));

    expect((await screen.findByRole('option', { name: 'Done' })).getAttribute('aria-selected')).toBe('true');
    expect(screen.getByRole('option', { name: 'Help' }).getAttribute('aria-selected')).toBe('false');
    expect(screen.getByRole('listbox', { name: 'Crown picker' })).toBeTruthy();
    expect(screen.getByRole('textbox', { name: 'Text response' }).disabled).toBe(true);
    expect(screen.queryByText('Draw one simple line or shape to start the picture.')).toBeNull();
    expect(screen.queryByText('paper + pencil')).toBeNull();
    expect(screen.queryByRole('button', { name: 'Done' })).toBeNull();

    fireEvent.click(screen.getByLabelText('Next device option'));
    expect(screen.getByRole('option', { name: 'Done' }).getAttribute('aria-selected')).toBe('false');
    expect(screen.getByRole('option', { name: 'Help' }).getAttribute('aria-selected')).toBe('true');

    fireEvent.click(screen.getByLabelText('Confirm selected device option'));

    expect(vi.mocked(sendTurn)).toHaveBeenCalledWith('cat3', 'help', false);
    expect(await screen.findByText('Try the same first mark again. I can help with that step.')).toBeTruthy();
    expect(screen.getByText('1/3')).toBeTruthy();
  });

  it('keeps Cat1 career screen passive and synced to the current backend step', async () => {
    vi.mocked(startActivitySession).mockResolvedValue({
      session_id: 'career',
      activity_type: 'activity_career_decision_role_play',
      template_type: 'cat1',
      session_state: {
        status: 'active',
        template_type: 'cat1',
        current_step: 'STEP_3_ROUND_2',
        current_round: 2,
        total_rounds: 3,
      },
      first_turn: { dialogue: 'Firefighter, water hose or cooking oil?', response_type: 'round' },
    });

    render(<ActivityGameApp />);

    fireEvent.click(await screen.findByRole('button', { name: /Career Decision Role Play/i }));
    fireEvent.click(screen.getByLabelText('Start activity'));

    expect(await screen.findByText('Firefighter, water hose or cooking oil?')).toBeTruthy();
    expect(screen.queryByLabelText('Next device option')).toBeNull();
    expect(document.querySelector('.activity-screen-layout--picker')).toBeNull();
    expect(screen.getByAltText('Career Decision Role Play visual').getAttribute('src')).toContain('round_2.png');
  });

  it('uses a crown picker to browse and start activities from the library', async () => {
    render(<ActivityGameApp />);

    expect(await screen.findByRole('heading', { name: 'Word Echo Practice' })).toBeTruthy();
    const listbox = screen.getByRole('listbox', { name: 'Crown picker' });
    expect(listbox).toBeTruthy();
    expect(screen.getByRole('option', { name: 'Word Echo Practice' }).getAttribute('aria-selected')).toBe('true');

    fireEvent.keyDown(listbox, { key: 'ArrowDown' });
    expect(screen.getByRole('heading', { name: 'Animal Sound Imitation' })).toBeTruthy();
    expect(screen.getByRole('option', { name: 'Animal Sound Imitation' }).getAttribute('aria-selected')).toBe('true');

    fireEvent.keyDown(listbox, { key: 'ArrowUp' });
    expect(screen.getByRole('heading', { name: 'Word Echo Practice' })).toBeTruthy();
  });

  it('drives Cat3 Done/Help through the crown picker', async () => {
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
        current_step: 'STEP_3_BUILD_1',
        current_round: 1,
        total_rounds: 3,
        current_build_step: 'Draw one simple line or shape to start the picture.',
        build_materials: ['paper', 'pencil'],
      },
      turn: { dialogue: 'I can help with that step.', response_type: 'round' },
    });

    render(<ActivityGameApp />);

    fireEvent.click(await screen.findByRole('button', { name: /Guided Drawing/i }));
    fireEvent.click(screen.getByLabelText('Start activity'));

    expect((await screen.findByRole('option', { name: 'Done' })).getAttribute('aria-selected')).toBe('true');
    const listbox = screen.getByRole('listbox', { name: 'Crown picker' });

    fireEvent.keyDown(listbox, { key: 'ArrowDown' });
    expect(screen.getByRole('option', { name: 'Help' }).getAttribute('aria-selected')).toBe('true');

    fireEvent.keyDown(listbox, { key: 'Enter' });
    expect(vi.mocked(sendTurn)).toHaveBeenCalledWith('cat3', 'help', false);
    expect(await screen.findByText('I can help with that step.')).toBeTruthy();
  });

  it('steps the Cat3 crown with global up/down arrows when the picker is unfocused', async () => {
    vi.mocked(startActivitySession).mockResolvedValue({
      session_id: 'cat3-keys',
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

    render(<ActivityGameApp />);

    fireEvent.click(await screen.findByRole('button', { name: /Guided Drawing/i }));
    fireEvent.click(screen.getByLabelText('Start activity'));

    expect((await screen.findByRole('option', { name: 'Done' })).getAttribute('aria-selected')).toBe('true');

    // Crown listbox is not focused; arrows dispatched on the document should
    // still drive the selection via the device-level key handler.
    fireEvent.keyDown(document.body, { key: 'ArrowDown' });
    expect(screen.getByRole('option', { name: 'Help' }).getAttribute('aria-selected')).toBe('true');

    fireEvent.keyDown(document.body, { key: 'ArrowUp' });
    expect(screen.getByRole('option', { name: 'Done' }).getAttribute('aria-selected')).toBe('true');
  });

  it('drives Cat1 recognition_pop choices through device selection', async () => {
    vi.mocked(startActivitySession).mockResolvedValue({
      session_id: 'cat1rp',
      activity_type: 'activity_recognition_pop_challenge',
      template_type: 'cat1',
      session_state: {
        status: 'active',
        template_type: 'cat1',
        current_step: 'STEP_3_ROUND_1',
        current_round: 1,
        total_rounds: 3,
      },
      first_turn: { dialogue: 'Which picture matches the apple?', response_type: 'round' },
    });
    vi.mocked(sendTurn).mockResolvedValue({
      session_state: {
        status: 'active',
        template_type: 'cat1',
        current_step: 'STEP_3_ROUND_2',
        current_round: 2,
        total_rounds: 3,
      },
      turn: { dialogue: 'Good looking!', response_type: 'round' },
    });

    render(<ActivityGameApp />);

    fireEvent.click(await screen.findByRole('button', { name: /Recognition Pop Challenge/i }));
    fireEvent.click(screen.getByLabelText('Start activity'));

    // Cat1 choice rounds enter device-option mode: text input is locked and the
    // green select button confirms the highlighted card as the turn.
    const selectButton = await screen.findByLabelText('Confirm selected device option');
    expect(screen.getByPlaceholderText('Type a response').disabled).toBe(true);

    // Default highlight is the first option (apple); step to the second (car).
    fireEvent.keyDown(document.body, { key: 'ArrowDown' });
    fireEvent.click(selectButton);

    expect(vi.mocked(sendTurn)).toHaveBeenCalledWith('cat1rp', 'Car', false, null, true);
    expect(await screen.findByText('Good looking!')).toBeTruthy();
  });

  it('shows a brief intro for the selected activity before starting', async () => {
    render(<ActivityGameApp />);

    // The first activity is selected by default; its tester-facing intro (not
    // the generic placeholder) renders in the transcript area before start.
    expect(await screen.findByText(/Up next/i)).toBeTruthy();
    expect(screen.getByText('Repeat a word back.')).toBeTruthy();
    expect(screen.getByText(/Press the green button/i)).toBeTruthy();
    // Tester-facing details include the category.
    expect(screen.getByText(/Cat1/)).toBeTruthy();
  });

  it('drives Cat5 item selection through the crown picker', async () => {
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
        collected_photos: [],
        current_round_items: [
          { id: 'ball', label: 'Ball', image: '/activity-assets/activity_phoneme_treasure_hunt/items/ball.png' },
          { id: 'cup', label: 'Cup', image: '/activity-assets/activity_phoneme_treasure_hunt/items/cup.png' },
          { id: 'book', label: 'Book', image: '/activity-assets/activity_phoneme_treasure_hunt/items/book.png' },
        ],
      },
      first_turn: { dialogue: 'Pick the B word.', response_type: 'round' },
    });
    vi.mocked(sendTurn).mockResolvedValue({
      session_state: {
        status: 'active',
        template_type: 'cat5',
        current_step: 'STEP_3_COLLECT_1',
        current_round: 1,
        total_rounds: 3,
        collection_phase: 'detail',
        collected_photos: ['cup'],
      },
      turn: { dialogue: 'Cup it is.', response_type: 'detail' },
    });

    render(<ActivityGameApp />);

    fireEvent.click(await screen.findByRole('button', { name: /Phoneme Treasure Hunt/i }));
    fireEvent.click(screen.getByLabelText('Start activity'));

    expect((await screen.findByRole('option', { name: 'Ball' })).getAttribute('aria-selected')).toBe('true');
    const listbox = screen.getByRole('listbox', { name: 'Crown picker' });

    fireEvent.keyDown(listbox, { key: 'ArrowDown' });
    expect(screen.getByRole('option', { name: 'Cup' }).getAttribute('aria-selected')).toBe('true');

    fireEvent.keyDown(listbox, { key: 'Enter' });
    expect(vi.mocked(sendTurn)).toHaveBeenCalledWith('cat5', '', false, 'cup');
    expect(await screen.findByText('Cup it is.')).toBeTruthy();
  });
});
