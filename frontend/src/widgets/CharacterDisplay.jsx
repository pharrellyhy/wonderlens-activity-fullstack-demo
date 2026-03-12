const ROUND_EMOJIS = ['🌅', '⚡', '🎉', '🌈', '✨'];

export default function CharacterDisplay({ description, animation, roundNumber = 1, entity }) {
  const idx = ((roundNumber || 1) - 1) % ROUND_EMOJIS.length;
  const emoji = ROUND_EMOJIS[idx];

  return (
    <div className={`flex flex-col items-center gap-4 p-6 rounded-2xl bg-white/5 border border-white/5 w-full max-w-sm transition-all duration-500 ${
      animation === 'scene_transition' ? 'animate-fade-in' : ''
    }`}>
      <div className="text-5xl">{emoji}</div>

      <div className="bg-[#1a1a1a] rounded-xl p-4 w-full text-center">
        <p className="text-neutral-200 font-medium">{description || `Scene ${roundNumber}`}</p>
        {entity && <p className="text-xs text-neutral-500 mt-1">{entity}</p>}
      </div>

      <div className="text-xs text-neutral-500 bg-white/5 px-3 py-1 rounded-full">
        Round {roundNumber}
      </div>
    </div>
  );
}
