import BASE from '../utils/basePath';
import { PhotoFrameIcon } from '../icons';

export default function PhotoRecallGrid({ animation, sessionState }) {
  const collectedIds = sessionState?.collected_photos || [];
  const collectedNames = sessionState?.collected_names || [];

  if (collectedIds.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 p-3">
        <p className="text-sm text-gray-400">No photos yet</p>
      </div>
    );
  }

  return (
    <div className={`flex flex-col items-center gap-2.5 max-[380px]:gap-2 p-3 max-[380px]:p-2.5 ${
      animation === 'badge_reveal' ? 'animate-celebration-large' : ''
    }`}>
      <h3 className="text-sm font-bold font-display text-[var(--color-forest-dark)] tracking-tight">
        Your Discoveries
      </h3>

      <div className={`grid ${collectedIds.length <= 2 ? 'grid-cols-2' : 'grid-cols-3'} gap-3 max-[380px]:gap-2`}>
        {collectedIds.map((id, i) => (
          <div key={id} className="flex flex-col items-center gap-1">
            <div className="w-[clamp(3.1rem,14vw,4rem)] h-[clamp(3.1rem,14vw,4rem)] rounded-xl max-[380px]:rounded-lg overflow-hidden border-2 border-[var(--color-sunflower)]/40 shadow-sm">
              <img
                src={`${BASE}/icons/${id}.png`}
                alt={collectedNames[i] || `Item ${i + 1}`}
                loading="lazy"
                className="w-full h-full object-cover"
              />
            </div>
            {collectedNames[i] && (
              <span className="text-xs max-[380px]:text-[11px] font-medium text-[var(--color-forest-dark)] text-center leading-tight max-w-[4.5rem] truncate">
                {collectedNames[i]}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
