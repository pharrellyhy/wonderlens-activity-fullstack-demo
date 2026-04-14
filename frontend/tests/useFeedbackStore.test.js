import { describe, it, expect, beforeEach } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import useFeedbackStore from '../src/hooks/useFeedbackStore.js';

const TESTER_ALIAS_KEY = 'wl-tester-alias';

describe('useFeedbackStore', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('adds a flag with a generated flag_id', () => {
    const { result } = renderHook(() => useFeedbackStore());

    let flagId;
    act(() => {
      flagId = result.current.addFlag({
        turnNumber: 3,
        tags: ['tone'],
        quickNote: 'too preachy',
        screenshot: new Blob(['fake'], { type: 'image/png' }),
        turnSnapshot: { step: 'detail_exchange', speaker_text: 'hello' },
      });
    });

    expect(flagId).toMatch(/^f-\d{2}$/);
    expect(result.current.flags).toHaveLength(1);
    const f = result.current.flags[0];
    expect(f.flag_id).toBe(flagId);
    expect(f.turn_number).toBe(3);
    expect(f.tags).toEqual(['tone']);
    expect(f.quick_note).toBe('too preachy');
    expect(f.review_comment).toBeNull();
    expect(f.screenshots).toHaveLength(1);
    expect(f.screenshots[0].path).toBe('screenshots/turn-03-auto.png');
    expect(f.turn_snapshot).toEqual({ step: 'detail_exchange', speaker_text: 'hello' });
    expect(result.current.hasFlags).toBe(true);
  });

  it('handles flags with no screenshot (empty screenshots array)', () => {
    const { result } = renderHook(() => useFeedbackStore());

    act(() => {
      result.current.addFlag({
        turnNumber: 5,
        tags: ['bug'],
        quickNote: '',
        screenshot: null,
        turnSnapshot: null,
      });
    });

    expect(result.current.flags[0].screenshots).toEqual([]);
  });

  it('disambiguates screenshot paths when multiple flags hit the same turn', () => {
    const { result } = renderHook(() => useFeedbackStore());

    act(() => {
      result.current.addFlag({
        turnNumber: 2,
        tags: ['tone'],
        quickNote: 'a',
        screenshot: new Blob(['a'], { type: 'image/png' }),
        turnSnapshot: null,
      });
      result.current.addFlag({
        turnNumber: 2,
        tags: ['bug'],
        quickNote: 'b',
        screenshot: new Blob(['b'], { type: 'image/png' }),
        turnSnapshot: null,
      });
    });

    const paths = result.current.flags.map((f) => f.screenshots[0].path);
    expect(paths).toEqual([
      'screenshots/turn-02-auto.png',
      'screenshots/turn-02-auto-1.png',
    ]);
  });

  it('updates a flag via updateFlag (sets review_comment)', () => {
    const { result } = renderHook(() => useFeedbackStore());

    let flagId;
    act(() => {
      flagId = result.current.addFlag({
        turnNumber: 1,
        tags: ['loved_it'],
        quickNote: 'nice',
        screenshot: null,
        turnSnapshot: null,
      });
    });

    act(() => {
      result.current.updateFlag(flagId, { review_comment: 'This was great.' });
    });

    expect(result.current.flags[0].review_comment).toBe('This was great.');
  });

  it('deletes a flag', () => {
    const { result } = renderHook(() => useFeedbackStore());

    let first;
    let second;
    act(() => {
      first = result.current.addFlag({
        turnNumber: 1,
        tags: ['tone'],
        quickNote: '',
        screenshot: null,
        turnSnapshot: null,
      });
      second = result.current.addFlag({
        turnNumber: 2,
        tags: ['bug'],
        quickNote: '',
        screenshot: null,
        turnSnapshot: null,
      });
    });

    expect(result.current.flags).toHaveLength(2);

    act(() => {
      result.current.deleteFlag(first);
    });

    expect(result.current.flags).toHaveLength(1);
    expect(result.current.flags[0].flag_id).toBe(second);
  });

  it('persists tester_alias to localStorage and reads it back on reload', () => {
    const { result: first } = renderHook(() => useFeedbackStore());
    expect(first.current.testerAlias).toBe('');

    act(() => {
      first.current.setTesterAlias('Alice');
    });

    expect(first.current.testerAlias).toBe('Alice');
    expect(localStorage.getItem(TESTER_ALIAS_KEY)).toBe('Alice');

    // Simulate a reload: fresh hook instance should read the alias back.
    const { result: second } = renderHook(() => useFeedbackStore());
    expect(second.current.testerAlias).toBe('Alice');
  });

  it('clearSession resets flags but preserves tester alias', () => {
    const { result } = renderHook(() => useFeedbackStore());

    act(() => {
      result.current.setTesterAlias('Bob');
      result.current.addFlag({
        turnNumber: 1,
        tags: ['tone'],
        quickNote: 'x',
        screenshot: null,
        turnSnapshot: null,
      });
    });

    expect(result.current.flags).toHaveLength(1);

    act(() => {
      result.current.clearSession();
    });

    expect(result.current.flags).toHaveLength(0);
    expect(result.current.hasFlags).toBe(false);
    expect(result.current.testerAlias).toBe('Bob');
  });

  it('buildPayload produces JSON matching the schema', () => {
    const { result } = renderHook(() => useFeedbackStore());

    act(() => {
      result.current.setTesterAlias('Alice');
      result.current.addFlag({
        turnNumber: 3,
        tags: ['tone'],
        quickNote: 'too preachy',
        screenshot: new Blob(['fake'], { type: 'image/png' }),
        turnSnapshot: {
          step: 'detail_exchange',
          speaker_text: 'hello',
          child_transcript: 'hi',
          widget_type: 'photo_full',
          recipe_round: 2,
        },
      });
    });

    let payload;
    act(() => {
      payload = result.current.buildPayload({
        sessionId: 'abc123def456',
        appMode: 'tester',
        activity: {
          template_type: 'mood_changer_dog',
          category: 'cat1',
          photo_filename: 'dog.jpg',
        },
        sessionStartedAt: '2026-04-13T14:28:11+08:00',
        sessionEndedAt: '2026-04-13T14:32:47+08:00',
      });
    });

    expect(payload.json.session_id).toBe('abc123def456');
    expect(payload.json.tester_alias).toBe('Alice');
    expect(payload.json.app_mode).toBe('tester');
    expect(payload.json.activity.template_type).toBe('mood_changer_dog');
    expect(payload.json.session_started_at).toBe('2026-04-13T14:28:11+08:00');
    expect(payload.json.session_ended_at).toBe('2026-04-13T14:32:47+08:00');
    expect(Array.isArray(payload.json.flags)).toBe(true);
    expect(payload.json.flags).toHaveLength(1);

    const jsonFlag = payload.json.flags[0];
    expect(jsonFlag.flag_id).toMatch(/^f-\d{2}$/);
    expect(jsonFlag.turn_number).toBe(3);
    expect(jsonFlag.tags).toEqual(['tone']);
    expect(jsonFlag.quick_note).toBe('too preachy');
    expect(jsonFlag.review_comment).toBeNull();
    expect(jsonFlag.screenshots).toEqual(['screenshots/turn-03-auto.png']);
    expect(jsonFlag.turn_snapshot.step).toBe('detail_exchange');

    // screenshots dict should contain the same relative path -> Blob mapping
    expect(Object.keys(payload.screenshots)).toEqual(['screenshots/turn-03-auto.png']);
    expect(payload.screenshots['screenshots/turn-03-auto.png']).toBeInstanceOf(Blob);
  });

  it('buildPayload omits empty review_comment as null', () => {
    const { result } = renderHook(() => useFeedbackStore());

    let flagId;
    act(() => {
      flagId = result.current.addFlag({
        turnNumber: 1,
        tags: ['bug'],
        quickNote: 'broken',
        screenshot: null,
        turnSnapshot: null,
      });
    });

    act(() => {
      result.current.updateFlag(flagId, { review_comment: '   ' });
    });

    let payload;
    act(() => {
      payload = result.current.buildPayload({
        sessionId: 's',
        appMode: 'tester',
        activity: null,
        sessionStartedAt: null,
        sessionEndedAt: null,
      });
    });

    expect(payload.json.flags[0].review_comment).toBeNull();
  });
});
