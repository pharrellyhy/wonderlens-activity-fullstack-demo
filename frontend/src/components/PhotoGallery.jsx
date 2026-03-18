import { useState } from 'react';
import { CheckmarkIcon, LeafIcon } from '../icons';

export default function PhotoGallery({ onPhotoSelect, collectedPhotos = [], totalToCollect = 3, wrongPhotoId, items = [], criterion = '' }) {
  const [selecting, setSelecting] = useState(false);

  const handleSelect = (photoId, label) => {
    if (selecting || collectedPhotos.includes(photoId)) return;
    setSelecting(true);
    Promise.resolve(onPhotoSelect(photoId, label)).finally(() => setSelecting(false));
  };

  const collected = collectedPhotos.length;

  return (
    <div className="flex flex-col items-center justify-center gap-3 h-full p-3">
      <div className="text-center">
        {criterion && (
          <p className="text-sm font-semibold text-[var(--color-forest-dark)]">
            {criterion}
          </p>
        )}
        <p className="text-xs text-gray-500 mt-0.5">
          {collected} of {totalToCollect} found
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3 w-full max-w-md">
        {items.map((photo) => {
          const isCollected = collectedPhotos.includes(photo.id);
          const isWrong = wrongPhotoId === photo.id;
          return (
            <button
              key={photo.id}
              onClick={() => handleSelect(photo.id, photo.label)}
              disabled={isCollected || selecting}
              className={`
                relative aspect-square rounded-2xl flex flex-col items-center justify-center gap-2
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
                  src={photo.image}
                  alt={photo.label}
                  className="absolute inset-0 w-full h-full object-cover rounded-2xl"
                  draggable={false}
                  onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = ''; }}
                />
              ) : null}
              <LeafIcon className={`w-10 h-10 ${photo.image ? 'hidden' : ''} ${
                isCollected ? 'text-[var(--color-forest)]' :
                isWrong ? 'text-red-300' :
                'text-[var(--color-forest)]/40'
              }`} />
              <span className="absolute bottom-0 inset-x-0 text-xs text-gray-700 leading-tight px-1 py-1 font-medium bg-white/80 rounded-b-2xl text-center">
                {photo.label}
              </span>
              {isCollected && (
                <span className="absolute top-1.5 right-1.5 w-6 h-6 bg-[var(--color-forest)] text-white rounded-full flex items-center justify-center shadow-sm">
                  <CheckmarkIcon className="w-3.5 h-3.5" />
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Progress circles */}
      <div className="flex gap-2.5 justify-center">
        {Array.from({ length: totalToCollect }).map((_, i) => (
          <div
            key={i}
            className={`w-9 h-9 rounded-full border-2 flex items-center justify-center text-xs font-bold transition-all duration-300 ${
              i < collected
                ? 'bg-[var(--color-forest)] border-[var(--color-forest)] text-white shadow-sm'
                : i === collected
                  ? 'border-[var(--color-teal)] text-[var(--color-teal)] animate-gentle-glow'
                  : 'border-gray-200 text-gray-300'
            }`}
          >
            {i < collected ? <CheckmarkIcon className="w-3.5 h-3.5" /> : i + 1}
          </div>
        ))}
      </div>
    </div>
  );
}
