import { renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import useSessionOrchestration from '../src/hooks/useSessionOrchestration.js';

const mocks = vi.hoisted(() => {
  const pendingAudioRef = { current: null };
  const silenceTimer = {
    clear: vi.fn(),
    start: vi.fn(),
    isRunning: false,
  };

  const baseConversation = {
    messages: [],
    sessionId: 'session-1',
    sessionState: {
      status: 'active',
      current_step: 'STEP_1_HOOK',
      current_round: 0,
    },
    screenFrame: null,
    loading: false,
    turnPending: false,
    error: null,
    latency: null,
    activityType: 'mood_changer_dog',
    templateType: 'cat1',
    photoUrl: null,
    errorExit: false,
    lastWrongPhotoId: null,
    debugData: null,
    debugHistory: [],
    pendingAudioRef,
    start: vi.fn(),
    startDeepLink: vi.fn(),
    sendMessage: vi.fn(),
    sendSilence: vi.fn(),
    sendAutoAdvance: vi.fn(),
    sendPhotoCollection: vi.fn(),
    reset: vi.fn(),
  };

  return {
    baseConversation,
    conversation: { ...baseConversation },
    pendingAudioRef,
    silenceTimer,
    useConversation: vi.fn(() => mocks.conversation),
    unlockSfx: vi.fn(),
    preloadCharacterSfx: vi.fn(),
    playForTurn: vi.fn(),
    playMicro: vi.fn(),
    stopCharacterSfx: vi.fn(),
    unlockCharacterSfx: vi.fn(),
    speak: vi.fn(),
    speakFromStream: vi.fn(),
    stopTTS: vi.fn(),
    unlockTTS: vi.fn(),
  };
});

vi.mock('../src/hooks/useConversation.js', () => ({
  default: mocks.useConversation,
}));

vi.mock('../src/hooks/useSfxPlayer.js', () => ({
  default: () => ({
    unlock: mocks.unlockSfx,
  }),
}));

vi.mock('../src/hooks/useCharacterSfx.js', () => ({
  default: () => ({
    preload: mocks.preloadCharacterSfx,
    playForTurn: mocks.playForTurn,
    playMicro: mocks.playMicro,
    stop: mocks.stopCharacterSfx,
    unlock: mocks.unlockCharacterSfx,
  }),
}));

vi.mock('../src/hooks/useTTS.js', () => ({
  default: () => ({
    isSpeaking: false,
    audioInfo: null,
    speak: mocks.speak,
    speakFromStream: mocks.speakFromStream,
    stop: mocks.stopTTS,
    unlock: mocks.unlockTTS,
  }),
}));

vi.mock('../src/hooks/useSilenceTimer.js', () => ({
  default: () => mocks.silenceTimer,
}));

vi.mock('../src/hooks/useSpeechRecognition.js', () => ({
  default: () => ({
    isListening: false,
    mode: 'idle',
    resultId: null,
    transcript: '',
    start: vi.fn(),
    stop: vi.fn(),
  }),
}));

vi.mock('../src/hooks/useCharacterAnimation.js', () => ({
  default: () => ({
    animationState: 'idle',
    currentClipUrl: null,
    isOneShot: false,
    onClipEnded: vi.fn(),
  }),
}));

describe('useSessionOrchestration progressive TTS handoff', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    localStorage.setItem('ttsEnabled', 'true');
    localStorage.setItem('silenceTimerOn', 'false');
    mocks.pendingAudioRef.current = null;
    mocks.conversation = { ...mocks.baseConversation, pendingAudioRef: mocks.pendingAudioRef, messages: [] };
  });

  it('speaks AI message text when no progressive audio stream is pending', async () => {
    const { rerender } = renderHook(() => useSessionOrchestration('T0'));

    mocks.conversation = {
      ...mocks.baseConversation,
      pendingAudioRef: mocks.pendingAudioRef,
      messages: [
        {
          role: 'ai',
          text: 'Hello explorer, tell me what you notice.',
        },
      ],
    };
    rerender();

    await waitFor(() => {
      expect(mocks.speak).toHaveBeenCalledWith('Hello explorer, tell me what you notice.', 'T0');
    });
    expect(mocks.speakFromStream).not.toHaveBeenCalled();
  });
});
