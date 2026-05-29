import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import useActivityTextSession from '../src/activityGame/useActivityTextSession.js';

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, resolve, reject };
}

describe('useActivityTextSession', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    delete globalThis.fetch;
  });

  it('starts an activity through the text endpoint', async () => {
    globalThis.fetch = vi.fn()
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
    expect(globalThis.fetch).toHaveBeenCalledWith('/api/start-activity', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        activity_type: 'activity_word_echo_practice',
        tier: 'T1',
        interaction_mode: 'text',
      }),
    }));
  });

  it('sends typed turns without audio or photo fields', async () => {
    globalThis.fetch = vi.fn()
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
    expect(globalThis.fetch).toHaveBeenLastCalledWith('/api/turn', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        session_id: 's1',
        text: 'ready',
        is_silent: false,
      }),
    }));
  });

  it('sends Cat5 collection item turns with photo_id', async () => {
    globalThis.fetch = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        session_id: 'cat5',
        activity_type: 'activity_phoneme_treasure_hunt',
        template_type: 'cat5',
        session_state: {
          status: 'active',
          template_type: 'cat5',
          current_step: 'STEP_3_COLLECT_1',
          turn_count: 1,
        },
        first_turn: { dialogue: 'Pick one.', response_type: 'round' },
      }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        session_state: {
          status: 'active',
          template_type: 'cat5',
          current_step: 'STEP_3_COLLECT_1',
          collection_phase: 'detail',
          collected_photos: ['ball'],
          turn_count: 2,
        },
        turn: { dialogue: 'Ball works.', response_type: 'detail' },
      }), { status: 200 }));

    const { result } = renderHook(() => useActivityTextSession());

    await act(async () => {
      await result.current.startActivity('activity_phoneme_treasure_hunt', 'T1');
      await result.current.sendCollectionItem('ball', 'Ball');
    });

    expect(result.current.messages.map((message) => message.text)).toEqual([
      'Pick one.',
      'Ball',
      'Ball works.',
    ]);
    expect(globalThis.fetch).toHaveBeenLastCalledWith('/api/turn', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({
        session_id: 'cat5',
        text: '',
        is_silent: false,
        photo_id: 'ball',
      }),
    }));
  });

  it('does not send typed turns after an activity is completed', async () => {
    globalThis.fetch = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        session_id: 's1',
        activity_type: 'activity_word_echo_practice',
        template_type: 'cat1',
        session_state: { status: 'completed', current_step: 'STEP_5_CLOSING', turn_count: 8 },
        first_turn: { dialogue: 'Great echo work!', response_type: 'closing' },
      }), { status: 200 }));

    const { result } = renderHook(() => useActivityTextSession());

    await act(async () => {
      await result.current.startActivity('activity_word_echo_practice', 'T1');
      await result.current.sendMessage('again');
    });

    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    expect(result.current.messages.map((message) => message.text)).toEqual(['Great echo work!']);
  });

  it('ignores in-flight turn responses after reset', async () => {
    const pendingTurn = deferred();
    globalThis.fetch = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        session_id: 's1',
        activity_type: 'activity_word_echo_practice',
        template_type: 'cat1',
        session_state: { status: 'active', current_step: 'STEP_1_HOOK', turn_count: 1 },
        first_turn: { dialogue: 'Echo time!', response_type: 'hook' },
      }), { status: 200 }))
      .mockReturnValueOnce(pendingTurn.promise);

    const { result } = renderHook(() => useActivityTextSession());

    let sendPromise;
    await act(async () => {
      await result.current.startActivity('activity_word_echo_practice', 'T1');
    });
    await act(async () => {
      sendPromise = result.current.sendMessage('ready');
    });

    expect(result.current.messages.map((message) => message.text)).toEqual(['Echo time!', 'ready']);

    act(() => {
      result.current.reset();
    });
    pendingTurn.resolve(new Response(JSON.stringify({
      session_state: { status: 'active', current_step: 'STEP_2_RULES', turn_count: 2 },
      turn: { dialogue: 'Try one word.', response_type: 'rules' },
    }), { status: 200 }));

    await act(async () => {
      await sendPromise;
    });

    expect(result.current.sessionId).toBeNull();
    expect(result.current.sessionState).toBeNull();
    expect(result.current.messages).toEqual([]);
    expect(result.current.turnPending).toBe(false);
  });
});
