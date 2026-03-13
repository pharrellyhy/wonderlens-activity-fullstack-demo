import { useState } from 'react';
import { CheckmarkIcon, LeafIcon } from '../icons';

const COLLECTION_PHOTOS = [
  { id: 'leaf_heart', label: 'Heart-shaped leaf' },
  { id: 'leaf_long', label: 'Long thin leaf' },
  { id: 'leaf_round', label: 'Round leaf' },
  { id: 'stone_smooth', label: 'Smooth stone' },
  { id: 'flower_small', label: 'Small flower' },
  { id: 'bark_rough', label: 'Rough bark' },
];

export default function PhotoGallery({ onPhotoSelect, collectedPhotos = [], totalToCollect = 3, wrongPhotoId }) {
  const [selecting, setSelecting] = useState(false);

  const handleSelect = (photoId) => {
    if (selecting || collectedPhotos.includes(photoId)) return;
    setSelecting(true);
    Promise.resolve(onPhotoSelect(photoId)).finally(() => setSelecting(false));
  };

  const collected = collectedPhotos.length;

  return (
    <div className="flex flex-col items-center justify-center gap-3 h-full p-3">
      <div className="text-center">
        <p className="text-sm font-semibold text-[var(--color-forest-dark)]">
          Tap a photo to collect it!
        </p>
        <p className="text-xs text-gray-400">
          {collected} of {totalToCollect} found
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3 w-full max-w-md">
        {COLLECTION_PHOTOS.slice(0, Math.max(totalToCollect + 2, 5)).map((photo) => {
          const isCollected = collectedPhotos.includes(photo.id);
          const isWrong = wrongPhotoId === photo.id;
          return (
            <button
              key={photo.id}
              onClick={() => handleSelect(photo.id)}
              disabled={isCollected || selecting}
              className={`
                relative aspect-square rounded-2xl flex flex-col items-center justify-center gap-2
                transition-all duration-200 text-center border-2
                ${isCollected
                  ? 'bg-[var(--color-forest)]/10 border-[var(--color-forest)] opacity-60'
                  : isWrong
                    ? 'bg-red-50 border-red-300 animate-shake'
                    : 'bg-white border-[var(--color-forest)]/20 hover:border-[var(--color-forest)] hover:shadow-lg cursor-pointer hover:scale-105'
                }
                ${selecting ? 'pointer-events-none' : ''}
              `}
              aria-label={`${isCollected ? 'Collected: ' : 'Select: '}${photo.label}`}
            >
              <LeafIcon className={`w-10 h-10 ${
                isCollected ? 'text-[var(--color-forest)]' :
                isWrong ? 'text-red-300' :
                'text-[var(--color-forest)]/40'
              }`} />
              <span className="text-xs text-gray-600 leading-tight px-1 font-medium">
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
                  ? 'border-[var(--color-teal)] text-[var(--color-teal)] animate-pulse'
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
