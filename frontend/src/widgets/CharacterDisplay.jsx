const ROUND_GRADIENTS = [
  'from-blue-100 to-indigo-100',
  'from-amber-100 to-orange-100',
  'from-green-100 to-emerald-100',
  'from-pink-100 to-rose-100',
  'from-purple-100 to-violet-100',
];

const ROUND_EMOJIS = ['🌅', '⚡', '🎉', '🌈', '✨'];

export default function CharacterDisplay({ description, animation, roundNumber = 1, entity }) {
  const gradientIdx = ((roundNumber || 1) - 1) % ROUND_GRADIENTS.length;
  const gradient = ROUND_GRADIENTS[gradientIdx];
  const emoji = ROUND_EMOJIS[gradientIdx];

  return (
    <div className={`flex flex-col items-center gap-4 p-6 rounded-2xl bg-gradient-to-br ${gradient} w-full max-w-sm transition-all duration-500 ${
      animation === 'scene_transition' ? 'animate-fade-in' : ''
    }`}>
      <div className="text-5xl">{emoji}</div>

      <div className="bg-white/60 backdrop-blur-sm rounded-xl p-4 w-full text-center">
        <p className="text-gray-700 font-medium">{description || `Scene ${roundNumber}`}</p>
        {entity && <p className="text-xs text-gray-500 mt-1">{entity}</p>}
      </div>

      <div className="text-xs text-gray-400 bg-white/40 px-3 py-1 rounded-full">
        Round {roundNumber}
      </div>
    </div>
  );
}
