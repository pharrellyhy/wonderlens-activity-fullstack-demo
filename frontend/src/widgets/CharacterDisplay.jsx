const ROUND_COLORS = [
  'from-blue-100/60 to-indigo-100/60 border-blue-200/30',
  'from-amber-100/60 to-orange-100/60 border-amber-200/30',
  'from-green-100/60 to-emerald-100/60 border-green-200/30',
  'from-pink-100/60 to-rose-100/60 border-pink-200/30',
  'from-violet-100/60 to-purple-100/60 border-violet-200/30',
];

const ROUND_EMOJIS = ['🌅', '⚡', '🎉', '🌈', '✨'];

export default function CharacterDisplay({ description, animation, roundNumber = 1, entity }) {
  const idx = ((roundNumber || 1) - 1) % ROUND_COLORS.length;
  const colorClass = ROUND_COLORS[idx];
  const emoji = ROUND_EMOJIS[idx];

  return (
    <div className={`flex flex-col items-center gap-4 p-6 rounded-2xl bg-gradient-to-br ${colorClass} border w-full max-w-sm transition-all duration-500 ${
      animation === 'scene_transition' ? 'animate-fade-in' : ''
    }`}>
      <div className="text-5xl">{emoji}</div>

      <div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 w-full text-center shadow-sm">
        <p className="text-gray-700 font-medium">{description || `Scene ${roundNumber}`}</p>
        {entity && <p className="text-xs text-gray-400 mt-1">{entity}</p>}
      </div>

      <div className="text-xs text-gray-400 bg-white/40 px-3 py-1 rounded-full font-medium">
        Round {roundNumber}
      </div>
    </div>
  );
}
