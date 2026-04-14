import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, fireEvent, screen, act } from '@testing-library/react';
import FeedbackReviewScreen from '../src/components/feedback/FeedbackReviewScreen.jsx';

const baseProps = {
  isOpen: true,
  sessionId: 'abc123def',
  testerAlias: 'alice',
  activity: { template_type: 'mood_changer_dog', category: 'cat1', photo_filename: 'dog.jpg' },
  sessionStartedAt: '2026-04-13T14:28:11+08:00',
  appMode: 'tester',
};

function makeFlag(overrides = {}) {
  return {
    flag_id: 'f-01',
    turn_number: 3,
    flagged_at: '2026-04-13T14:30:02+08:00',
    tags: ['tone'],
    quick_note: 'too preachy',
    review_comment: null,
    screenshots: [],
    turn_snapshot: null,
    ...overrides,
  };
}

describe('FeedbackReviewScreen', () => {
  beforeEach(() => {
    if (!globalThis.URL.createObjectURL) {
      globalThis.URL.createObjectURL = vi.fn(() => 'blob:mock');
    }
    if (!globalThis.URL.revokeObjectURL) {
      globalThis.URL.revokeObjectURL = vi.fn();
    }
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows the empty state when there are no flags', () => {
    render(
      <FeedbackReviewScreen
        {...baseProps}
        flags={[]}
        buildPayload={vi.fn()}
        onUpdateFlag={vi.fn()}
        onDeleteFlag={vi.fn()}
        onClose={vi.fn()}
        onClearSession={vi.fn()}
      />,
    );
    expect(screen.getByText(/No flags this session/i)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Done' })).toBeTruthy();
  });

  it('renders a flag with its turn header, tag chip, and textarea', () => {
    render(
      <FeedbackReviewScreen
        {...baseProps}
        flags={[makeFlag()]}
        buildPayload={vi.fn()}
        onUpdateFlag={vi.fn()}
        onDeleteFlag={vi.fn()}
        onClose={vi.fn()}
        onClearSession={vi.fn()}
      />,
    );
    expect(screen.getByText('Turn 3')).toBeTruthy();
    expect(screen.getByText('Tone')).toBeTruthy();
    expect(screen.getByLabelText('Review comment for turn 3')).toBeTruthy();
  });

  it('calls onUpdateFlag when typing in the review textarea', () => {
    const onUpdateFlag = vi.fn();
    render(
      <FeedbackReviewScreen
        {...baseProps}
        flags={[makeFlag()]}
        buildPayload={vi.fn()}
        onUpdateFlag={onUpdateFlag}
        onDeleteFlag={vi.fn()}
        onClose={vi.fn()}
        onClearSession={vi.fn()}
      />,
    );
    const textarea = screen.getByLabelText('Review comment for turn 3');
    fireEvent.change(textarea, { target: { value: 'too moralizing' } });
    expect(onUpdateFlag).toHaveBeenCalledWith('f-01', { review_comment: 'too moralizing' });
  });

  it('calls onDeleteFlag when the Delete button is clicked', () => {
    const onDeleteFlag = vi.fn();
    render(
      <FeedbackReviewScreen
        {...baseProps}
        flags={[makeFlag()]}
        buildPayload={vi.fn()}
        onUpdateFlag={vi.fn()}
        onDeleteFlag={onDeleteFlag}
        onClose={vi.fn()}
        onClearSession={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole('button', { name: /Delete flag for turn 3/i }));
    expect(onDeleteFlag).toHaveBeenCalledWith('f-01');
  });

  it('calls buildPayload when Submit is clicked', async () => {
    const buildPayload = vi.fn(() => ({ json: { flags: [] }, screenshots: {} }));
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'saved' }) }),
    );
    render(
      <FeedbackReviewScreen
        {...baseProps}
        flags={[makeFlag()]}
        buildPayload={buildPayload}
        onUpdateFlag={vi.fn()}
        onDeleteFlag={vi.fn()}
        onClose={vi.fn()}
        onClearSession={vi.fn()}
      />,
    );
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Submit' }));
    });
    expect(buildPayload).toHaveBeenCalledTimes(1);
    const callArg = buildPayload.mock.calls[0][0];
    expect(callArg.sessionId).toBe('abc123def');
    expect(callArg.appMode).toBe('tester');
    expect(callArg.activity.template_type).toBe('mood_changer_dog');

    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    const [url, init] = globalThis.fetch.mock.calls[0];
    expect(String(url)).toContain('/api/feedback');
    expect(init.method).toBe('POST');
    expect(init.body).toBeInstanceOf(FormData);
    expect(init.body.get('feedback')).toBe(JSON.stringify({ flags: [] }));
  });
});
