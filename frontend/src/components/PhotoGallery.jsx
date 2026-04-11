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
    <div className="device-gallery-layout flex flex-col items-center justify-center gap-3 max-[380px]:gap-2 h-full py-3 px-3 max-[380px]:py-2 max-[380px]:px-2">
      <div className="text-center">
        {criterion && (
          <p className="text-lg max-[380px]:text-base font-bold font-display text-[var(--color-forest-dark)] leading-tight">
            {criterion}
          </p>
        )}
        <p className="text-sm text-gray-500 mt-1">
          {collected} of {totalToCollect} found
        </p>
      </div>

      <div className="grid grid-cols-3 gap-3 max-[380px]:gap-2 w-full max-w-[22rem]">
        {items.map((photo) => {
          const isCollected = collectedPhotos.includes(photo.id);
          const isWrong = wrongPhotoId === photo.id;
          return (
            <button
              key={photo.id}
              onClick={() => handleSelect(photo.id, photo.label)}
              disabled={isCollected || selecting}
              className={`
                relative aspect-square rounded-lg flex flex-col items-center justify-center gap-0.5
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
              <LeafIcon className={`w-7 h-7 max-[380px]:w-6.5 max-[380px]:h-6.5 ${photo.image ? 'hidden' : ''} ${
                isCollected ? 'text-[var(--color-forest)]' :
                isWrong ? 'text-red-300' :
                'text-[var(--color-forest)]/40'
              }`} />
              <span className="absolute bottom-0 inset-x-0 text-xs max-[380px]:text-[10px] text-gray-700 leading-tight px-1.5 py-1 font-semibold bg-white/85 rounded-b-lg text-center">
                {photo.label}
              </span>
              {isCollected && (
                <span className="absolute top-2 right-2 max-[380px]:top-1.5 max-[380px]:right-1.5 w-7 h-7 max-[380px]:w-6 max-[380px]:h-6 bg-[var(--color-forest)] text-white rounded-full flex items-center justify-center shadow-sm">
                  <CheckmarkIcon className="w-4 h-4 max-[380px]:w-3.5 max-[380px]:h-3.5" />
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Progress circles */}
      <div className="flex gap-2 max-[380px]:gap-1.5 justify-center">
        {Array.from({ length: totalToCollect }).map((_, i) => (
          <div
            key={i}
            className={`w-7 h-7 max-[380px]:w-6 max-[380px]:h-6 rounded-full border-2 flex items-center justify-center text-xs font-bold transition-all duration-300 ${
              i < collected
                ? 'bg-[var(--color-forest)] border-[var(--color-forest)] text-white shadow-sm'
                : i === collected
                  ? 'border-[var(--color-teal)] text-[var(--color-teal)] animate-gentle-glow'
                  : 'border-gray-200 text-gray-300'
            }`}
          >
            {i < collected ? <CheckmarkIcon className="w-4 h-4 max-[380px]:w-3.5 max-[380px]:h-3.5" /> : i + 1}
          </div>
        ))}
      </div>
    </div>
  );
}
