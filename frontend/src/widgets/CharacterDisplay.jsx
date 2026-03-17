import { CompassIcon, BinocularsIcon, MagnifyingGlassIcon, LeafIcon, StarIcon } from '../icons';

const ROUND_COLORS = [
  'from-[var(--color-sky-light)]/40 to-[var(--color-sky)]/20 border-[var(--color-sky)]/30',
  'from-[var(--color-sunflower-light)]/30 to-[var(--color-sunflower)]/20 border-[var(--color-sunflower)]/30',
  'from-[var(--color-forest-light)]/20 to-[var(--color-forest)]/10 border-[var(--color-forest)]/20',
  'from-[var(--color-teal-light)]/30 to-[var(--color-teal)]/20 border-[var(--color-teal)]/30',
  'from-purple-100/40 to-purple-200/20 border-purple-200/30',
];

const ROUND_ICONS = [CompassIcon, BinocularsIcon, MagnifyingGlassIcon, LeafIcon, StarIcon];

export default function CharacterDisplay({ description, animation, roundNumber = 1, entity }) {
  const idx = ((roundNumber || 1) - 1) % ROUND_COLORS.length;
  const colorClass = ROUND_COLORS[idx];
  const IconComponent = ROUND_ICONS[idx];

  return (
    <div className={`flex flex-col items-center gap-4 p-6 rounded-2xl bg-gradient-to-br ${colorClass} border-2 w-full max-w-lg transition-all duration-500 ${
      animation === 'scene_transition' ? 'animate-fade-in' : ''
    }`}>
      <div className="w-14 h-14 rounded-full bg-white/60 flex items-center justify-center shadow-sm">
        <IconComponent className="w-8 h-8 text-[var(--color-forest)]" />
      </div>

      <div className="bg-white/60 rounded-xl p-4 w-full text-center shadow-sm">
        <p className="text-gray-700 font-medium text-base">{description || `Scene ${roundNumber}`}</p>
        {entity && <p className="text-xs text-gray-500 mt-1">{entity}</p>}
      </div>

      <div className="text-xs text-[var(--color-forest)] bg-white/50 px-3 py-1 rounded-full font-medium">
        Round {roundNumber}
      </div>
    </div>
  );
}
