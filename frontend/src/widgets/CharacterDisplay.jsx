import { getThemeForEntity } from './gameThemes';

export default function CharacterDisplay({ description, animation, roundNumber = 1, entity }) {
  const theme = getThemeForEntity(entity);

  return (
    <div className={`relative flex flex-col items-center gap-4 p-6 w-full max-w-lg transition-all duration-500 ${animation === 'scene_transition' ? 'animate-fade-in' : ''}`}>
      {/* Character icon */}
      <div className={`w-20 h-20 rounded-full ${theme.iconBg} ring-2 flex items-center justify-center shadow-sm animate-gentle-float`}>
        <img src={theme.characterPng} alt={entity || 'character'} className="w-14 h-14 object-contain" />
      </div>

      {/* Description card */}
      <div className="bg-white/80 rounded-xl p-4 w-full text-center shadow-sm">
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
