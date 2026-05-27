import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import useActivityTextSession from '../src/activityGame/useActivityTextSession.js';

describe('useActivityTextSession', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    delete global.fetch;
  });

  it('starts an activity through the text endpoint', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        session_id: 's1',
        activity_type: 'activity_word_echo_practice',
        template_type: 'cat1',
        session_state: { status: 'active', current_step: 'STEP_1_HOOK', turn_count: 1 },
        first_turn: {
          dialogue: 'Echo time!',
          response_type: 'hook',
          screen_frame: { widget: 'activity_lens', widget_params: {} },
        },
      }), { status: 200 }));

    const { result } = renderHook(() => useActivityTextSession());

    await act(async () => {
      await result.current.startActivity('activity_word_echo_practice', 'T1');
    });

    expect(result.current.messages[0].text).toBe('Echo time!');
    expect(result.current.sessionId).toBe('s1');
    expect(result.current.screenFrame.widget).toBe('activity_lens');
    expect(global.fetch).toHaveBeenCalledWith('/api/start-activity', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        activity_type: 'activity_word_echo_practice',
        tier: 'T1',
        interaction_mode: 'text',
      }),
    }));
  });

  it('sends typed turns without audio or photo fields', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        session_id: 's1',
        activity_type: 'activity_word_echo_practice',
        template_type: 'cat1',
        session_state: { status: 'active', current_step: 'STEP_1_HOOK', turn_count: 1 },
        first_turn: { dialogue: 'Echo time!', response_type: 'hook' },
      }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        session_state: { status: 'active', current_step: 'STEP_2_RULES', turn_count: 2 },
        turn: {
          dialogue: 'Try one word.',
          response_type: 'rules',
          screen_frame: { widget: 'activity_lens', widget_params: {} },
        },
      }), { status: 200 }));

    const { result } = renderHook(() => useActivityTextSession());

    await act(async () => {
      await result.current.startActivity('activity_word_echo_practice', 'T1');
      await result.current.sendMessage('ready');
    });

    expect(result.current.messages.map((message) => message.text)).toEqual([
      'Echo time!',
      'ready',
      'Try one word.',
    ]);
    expect(global.fetch).toHaveBeenLastCalledWith('/api/turn', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        session_id: 's1',
        text: 'ready',
        is_silent: false,
      }),
    }));
  });
});
