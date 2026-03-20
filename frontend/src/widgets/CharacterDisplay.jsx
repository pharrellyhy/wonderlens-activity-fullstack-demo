import { getThemeForEntity } from './gameThemes';

export default function CharacterDisplay({ description, animation, roundNumber = 1, entity }) {
  const theme = getThemeForEntity(entity);

  return (
    <div className={`relative flex flex-col items-center gap-4 p-6 rounded-2xl bg-gradient-to-br ${theme.gradient} ${theme.border} border-2 w-full max-w-lg transition-all duration-500 overflow-hidden ${animation === 'scene_transition' ? 'animate-fade-in' : ''}`}>
      {/* Corner decorations */}
      <span className="absolute top-2 left-3 text-lg opacity-[0.12] select-none pointer-events-none" aria-hidden="true">{theme.decorations[0]}</span>
      <span className="absolute bottom-2 right-3 text-lg opacity-[0.12] select-none pointer-events-none" aria-hidden="true">{theme.decorations[1]}</span>

      {/* Character icon */}
      <div className={`w-20 h-20 rounded-full ${theme.iconBg} ring-2 flex items-center justify-center shadow-sm animate-gentle-float`}>
        <img src={theme.characterPng} alt={entity || 'character'} className="w-14 h-14 object-contain" />
      </div>

      {/* Description card */}
      <div className="bg-white/60 rounded-xl p-4 w-full text-center shadow-sm">
        <p className="text-gray-700 font-medium text-base">{description || `Scene ${roundNumber}`}</p>
      </div>

      {/* Round pill badge */}
      {roundNumber > 0 && (
        <div className={`text-xs ${theme.accent} ${theme.accentBg} px-3 py-1 rounded-full font-medium`}>
          Round {roundNumber}
        </div>
      )}
    </div>
  );
}
