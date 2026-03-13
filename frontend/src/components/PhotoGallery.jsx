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

export default function PhotoGallery({ onPhotoSelect, collectedPhotos = [], totalToCollect = 3 }) {
  const [selecting, setSelecting] = useState(false);

  const handleSelect = (photoId) => {
    if (selecting || collectedPhotos.includes(photoId)) return;
    setSelecting(true);
    onPhotoSelect(photoId);
    setTimeout(() => setSelecting(false), 500);
  };

  const collected = collectedPhotos.length;

  return (
    <div className="flex flex-col items-center gap-4 p-4">
      <div className="text-center">
        <p className="text-sm font-semibold text-[var(--color-forest-dark)] mb-1">
          Find and collect items!
        </p>
        <p className="text-xs text-gray-400">
          {collected} of {totalToCollect} collected
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3 w-full max-w-sm">
        {COLLECTION_PHOTOS.slice(0, Math.max(totalToCollect + 2, 5)).map((photo) => {
          const isCollected = collectedPhotos.includes(photo.id);
          return (
            <button
              key={photo.id}
              onClick={() => handleSelect(photo.id)}
              disabled={isCollected || selecting}
              className={`
                relative aspect-square rounded-2xl flex flex-col items-center justify-center gap-1
                transition-all duration-200 text-center border-2
                ${isCollected
                  ? 'bg-[var(--color-forest)]/10 border-[var(--color-forest)] opacity-60'
                  : 'bg-white border-[var(--color-forest)]/20 hover:border-[var(--color-forest)] hover:shadow-md cursor-pointer'
                }
                ${selecting ? 'pointer-events-none' : ''}
              `}
              aria-label={`${isCollected ? 'Collected: ' : 'Select: '}${photo.label}`}
            >
              <LeafIcon className={`w-8 h-8 ${isCollected ? 'text-[var(--color-forest)]' : 'text-[var(--color-forest)]/40'}`} />
              <span className="text-[10px] text-gray-500 leading-tight px-1">
                {photo.label}
              </span>
              {isCollected && (
                <span className="absolute top-1 right-1 w-5 h-5 bg-[var(--color-forest)] text-white rounded-full flex items-center justify-center">
                  <CheckmarkIcon className="w-3 h-3" />
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="w-full max-w-sm">
        <div className="flex gap-2 justify-center">
          {Array.from({ length: totalToCollect }).map((_, i) => (
            <div
              key={i}
              className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                i < collected
                  ? 'bg-[var(--color-forest)] border-[var(--color-forest)] text-white'
                  : i === collected
                    ? 'border-[var(--color-teal)] text-[var(--color-teal)] animate-pulse'
                    : 'border-gray-200 text-gray-300'
              }`}
            >
              {i < collected ? <CheckmarkIcon className="w-3 h-3" /> : i + 1}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
