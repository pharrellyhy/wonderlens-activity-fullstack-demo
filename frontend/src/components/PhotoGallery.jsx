import { useState } from 'react';
import { CheckmarkIcon, LeafIcon } from '../icons';
import BASE from '../utils/basePath';

export default function PhotoGallery({ onPhotoSelect, collectedPhotos = [], totalToCollect = 3, wrongPhotoId, items = [], criterion = '' }) {
  const [selecting, setSelecting] = useState(false);

  const handleSelect = (photoId, label) => {
    if (selecting || collectedPhotos.includes(photoId)) return;
    setSelecting(true);
    Promise.resolve(onPhotoSelect(photoId, label)).finally(() => setSelecting(false));
  };

  const collected = collectedPhotos.length;

  return (
    <div className="flex flex-col items-center justify-center gap-5 max-[380px]:gap-3 h-full p-4 max-[380px]:p-3">
      <div className="text-center">
        {criterion && (
          <p className="text-base max-[380px]:text-sm font-semibold text-[var(--color-forest-dark)]">
            {criterion}
          </p>
        )}
        <p className="text-sm max-[380px]:text-xs text-gray-500 mt-1">
          {collected} of {totalToCollect} found
        </p>
      </div>

      <div className="grid grid-cols-3 gap-4 max-[380px]:gap-2.5 w-full max-w-lg">
        {items.map((photo) => {
          const isCollected = collectedPhotos.includes(photo.id);
          const isWrong = wrongPhotoId === photo.id;
          return (
            <button
              key={photo.id}
              onClick={() => handleSelect(photo.id, photo.label)}
              disabled={isCollected || selecting}
              className={`
                relative aspect-square rounded-2xl max-[380px]:rounded-xl flex flex-col items-center justify-center gap-2 max-[380px]:gap-1
                transition-all duration-200 text-center border-2
                ${isCollected
                  ? 'bg-[var(--color-forest)]/10 border-[var(--color-forest)] opacity-60'
                  : isWrong
                    ? 'bg-red-50 border-red-300 animate-shake'
                    : 'bg-white border-[var(--color-forest)]/20 hover:border-[var(--color-forest)] hover:shadow-md cursor-pointer hover:scale-[1.02]'
                }
                ${selecting ? 'pointer-events-none' : ''}
              `}
              aria-label={`${isCollected ? 'Collected: ' : 'Select: '}${photo.label}`}
            >
              {photo.image ? (
                <img
                  src={photo.image.startsWith(BASE) ? photo.image : `${BASE}${photo.image}`}
                  alt={photo.label}
                  className="absolute inset-0 w-full h-full object-cover rounded-2xl"
                  draggable={false}
                  onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = ''; }}
                />
              ) : null}
              <LeafIcon className={`w-10 h-10 sm:w-14 sm:h-14 max-[380px]:w-8 max-[380px]:h-8 ${photo.image ? 'hidden' : ''} ${
                isCollected ? 'text-[var(--color-forest)]' :
                isWrong ? 'text-red-300' :
                'text-[var(--color-forest)]/40'
              }`} />
              <span className="absolute bottom-0 inset-x-0 text-sm max-[380px]:text-[11px] text-gray-700 leading-tight px-1.5 max-[380px]:px-1 py-1.5 max-[380px]:py-1 font-medium bg-white/80 rounded-b-2xl max-[380px]:rounded-b-xl text-center">
                {photo.label}
              </span>
              {isCollected && (
                <span className="absolute top-2 right-2 max-[380px]:top-1.5 max-[380px]:right-1.5 w-8 h-8 max-[380px]:w-6 max-[380px]:h-6 bg-[var(--color-forest)] text-white rounded-full flex items-center justify-center shadow-sm">
                  <CheckmarkIcon className="w-4.5 h-4.5 max-[380px]:w-3.5 max-[380px]:h-3.5" />
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Progress circles */}
      <div className="flex gap-3 max-[380px]:gap-2 justify-center">
        {Array.from({ length: totalToCollect }).map((_, i) => (
          <div
            key={i}
            className={`w-8 h-8 sm:w-11 sm:h-11 max-[380px]:w-7 max-[380px]:h-7 rounded-full border-2 flex items-center justify-center text-xs sm:text-sm max-[380px]:text-[11px] font-bold transition-all duration-300 ${
              i < collected
                ? 'bg-[var(--color-forest)] border-[var(--color-forest)] text-white shadow-sm'
                : i === collected
                  ? 'border-[var(--color-teal)] text-[var(--color-teal)] animate-gentle-glow'
                  : 'border-gray-200 text-gray-300'
            }`}
          >
            {i < collected ? <CheckmarkIcon className="w-4.5 h-4.5 max-[380px]:w-3.5 max-[380px]:h-3.5" /> : i + 1}
          </div>
        ))}
      </div>
    </div>
  );
}
