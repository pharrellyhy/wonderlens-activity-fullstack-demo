import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import useConversation from '../src/hooks/useConversation.js';
import { sendTurn, sendTurnSpeak, startDeepLinkSession } from '../src/utils/api.js';

vi.mock('../src/utils/api.js', () => ({
  startSession: vi.fn(),
  startDeepLinkSession: vi.fn(),
  sendTurn: vi.fn(),
  sendTurnSpeak: vi.fn(),
}));

describe('useConversation progressive TTS path', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    startDeepLinkSession.mockResolvedValue({
      session_id: 'session-1',
      activity_type: 'mood_changer_dog',
      template_type: 'cat1',
      first_turn: {
        dialogue: 'Hello explorer',
        response_type: 'hook',
      },
      session_state: {
        status: 'active',
        current_step: 'STEP_1_HOOK',
        current_round: 0,
        total_rounds: 2,
        turn_count: 1,
      },
    });
    sendTurn.mockResolvedValue({
      latency_ms: 123,
      turn: {
        dialogue: 'Tell me what the dog says.',
        response_type: 'prompt',
      },
      session_state: {
        status: 'active',
        current_step: 'STEP_2_ROUND',
        current_round: 1,
        total_rounds: 2,
        turn_count: 2,
      },
    });
  });

  it('sends turns through /api/turn so TTS can use the progressive audio element path', async () => {
    const { result } = renderHook(() => useConversation());

    await act(async () => {
      await result.current.startDeepLink('dog', 'T0');
    });
    await waitFor(() => expect(result.current.sessionId).toBe('session-1'));

    await act(async () => {
      await result.current.sendMessage('woof');
    });

    expect(sendTurn).toHaveBeenCalledWith('session-1', 'woof', false, null);
    expect(sendTurnSpeak).not.toHaveBeenCalled();
    expect(result.current.pendingAudioRef.current).toBeNull();
    expect(result.current.messages.at(-1).text).toBe('Tell me what the dog says.');
  });
});
