import { PhotoFrameIcon } from '../icons';

export default function PhotoGrid({ photos = [], animation }) {
  const slots = Array.from({ length: 4 }, (_, i) => photos[i] || null);

  return (
    <div className="flex flex-col items-center gap-3 p-4">
      <h3 className="text-lg font-bold font-display text-[var(--color-forest-dark)] tracking-tight">Your Collection</h3>

      <div className={`grid grid-cols-2 gap-3 ${
        animation === 'connection_lines_draw' ? 'animate-pulse' : ''
      }`}>
        {slots.map((photo, i) => (
          <div
            key={i}
            className="w-36 h-36 rounded-xl overflow-hidden border-2 border-[var(--color-forest)]/20 shadow-sm flex items-center justify-center bg-white"
          >
            {photo ? (
              <img src={photo} alt={`Find ${i + 1}`} className="w-full h-full object-cover" />
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
        <p className="text-sm text-[var(--color-teal)] font-medium animate-bounce">Connected!</p>
      )}
    </div>
  );
}
