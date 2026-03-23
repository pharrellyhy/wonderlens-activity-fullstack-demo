import { PhotoFrameIcon } from '../icons';
import BASE from '../utils/basePath';

export default function PhotoGrid({ photos = [], animation, sessionState }) {
  const collectedIds = sessionState?.collected_photos || [];
  const totalToCollect = sessionState?.total_rounds || collectedIds.length || 1;

  // Build slots from collected photo IDs — each gets its icon image
  const slots = Array.from({ length: totalToCollect }, (_, i) => {
    const id = collectedIds[i];
    return id ? `${BASE}/icons/${id}.png` : null;
  });

  return (
    <div className="flex flex-col items-center gap-3 p-4">
      <h3 className="text-lg font-bold font-display text-[var(--color-forest-dark)] tracking-tight">Your Collection</h3>

      <div className={`grid ${totalToCollect <= 2 ? 'grid-cols-2' : 'grid-cols-3'} gap-3 ${
        animation === 'connection_lines_draw' ? 'animate-sparkle-large' : ''
      }`}>
        {slots.map((photo, i) => (
          <div
            key={i}
            className="w-28 h-28 rounded-xl overflow-hidden border-2 border-[var(--color-forest)]/20 shadow-sm flex items-center justify-center bg-white"
          >
            {photo ? (
              <img src={photo} alt={`Collected ${i + 1}`} loading="lazy" className="w-full h-full object-cover" />
            ) : (
              <div className="text-center">
                <PhotoFrameIcon className="w-10 h-10 text-[var(--color-forest)]/30 mx-auto" />
                <p className="text-xs text-gray-300 mt-1">#{i + 1}</p>
              </div>
            )}
          </div>
        ))}
      </div>

      {animation === 'connection_lines_draw' && (
        <p className="text-sm text-[var(--color-teal)] font-medium animate-fade-in">Connected!</p>
      )}
    </div>
  );
}
