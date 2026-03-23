import { getThemeForEntity } from './gameThemes';

export default function CharacterDisplay({ description, animation, roundNumber = 1, entity }) {
  const theme = getThemeForEntity(entity);

  return (
    <div className={`relative flex flex-col items-center gap-2.5 max-[380px]:gap-2 p-3 max-[380px]:p-2.5 w-full max-w-md transition-all duration-500 ${animation === 'scene_transition' ? 'animate-fade-in' : ''}`}>
      {/* Character icon */}
      <div className={`w-[clamp(2.8rem,12vw,3.25rem)] h-[clamp(2.8rem,12vw,3.25rem)] rounded-full ${theme.iconBg} ring-2 flex items-center justify-center shadow-sm animate-gentle-float`}>
        <img src={theme.characterPng} alt={entity || 'character'} className="w-[clamp(1.9rem,8vw,2.2rem)] h-[clamp(1.9rem,8vw,2.2rem)] object-contain" />
      </div>

      {/* Description card */}
      <div className="bg-white/80 rounded-xl max-[380px]:rounded-lg p-2.5 max-[380px]:p-2 w-full text-center shadow-sm">
        <p className="text-gray-700 font-medium text-xs">{description || `Scene ${roundNumber}`}</p>
      </div>

      {/* Round pill badge */}
      {roundNumber > 0 && (
        <div className={`text-xs max-[380px]:text-[11px] ${theme.accent} ${theme.accentBg} px-3 max-[380px]:px-2 py-1 max-[380px]:py-0.5 rounded-full font-medium`}>
          Round {roundNumber}
        </div>
      )}
    </div>
  );
}
