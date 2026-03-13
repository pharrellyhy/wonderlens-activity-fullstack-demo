import { useRef, useCallback } from 'react';

const VARIATIONS = 3;

const SFX_CUES = [
  'wonder_chime',
  'scene_woosh',
  'celebration_fanfare',
  'photo_shutter_click',
  'slot_fill_chime',
  'mission_accepted',
  'mission_complete_fanfare',
  'badge_awarded',
  'excitement_rising',
  'game_start_chime',
];

const SFX_VALID = new Set(SFX_CUES);

export default function useSfxPlayer() {
  const cacheRef = useRef({});
  const currentRef = useRef(null);

  const play = useCallback((sfxCue) => {
    if (!sfxCue || !SFX_VALID.has(sfxCue)) return;

    // Stop any currently playing SFX
    if (currentRef.current) {
      currentRef.current.pause();
      currentRef.current.currentTime = 0;
    }

    // Pick a random variation (v1, v2, or v3)
    const variant = Math.floor(Math.random() * VARIATIONS) + 1;
    const file = `/sfx/${sfxCue}_v${variant}.wav`;

    // Use cached Audio object or create new one
    if (!cacheRef.current[file]) {
      cacheRef.current[file] = new Audio(file);
    }

    const audio = cacheRef.current[file];
    audio.currentTime = 0;
    audio.volume = 0.5;
    currentRef.current = audio;
    audio.play().catch(() => {});
  }, []);

  return play;
}
