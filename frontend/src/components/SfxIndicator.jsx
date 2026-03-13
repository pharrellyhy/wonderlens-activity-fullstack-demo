import { SpeakerIcon } from '../icons';

const SFX_LABELS = {
  wonder_chime: 'Magical wonder chime',
  scene_woosh: 'Scene transition whoosh',
  celebration_fanfare: 'Celebration fanfare',
  photo_shutter_click: 'Camera shutter click',
  slot_fill_chime: 'Collection slot filled',
  mission_accepted: 'Mission accepted',
  mission_complete_fanfare: 'Mission complete',
  badge_awarded: 'Badge awarded',
  excitement_rising: 'Excitement rising',
  game_start_chime: 'Game start',
};

export default function SfxIndicator({ sfxCue, sfxLabel }) {
  if (!sfxCue) return null;

  const label = sfxLabel || SFX_LABELS[sfxCue] || sfxCue;

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-[var(--color-teal)] text-white rounded-full text-xs font-medium animate-slide-up-large animate-sfx-pulse shadow-md">
      <SpeakerIcon className="w-4 h-4 flex-shrink-0" />
      <span>{label}</span>
    </div>
  );
}
