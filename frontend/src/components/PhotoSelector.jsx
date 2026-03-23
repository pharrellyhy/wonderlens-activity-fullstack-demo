import { useState, useEffect } from 'react';
import { CameraIcon, BinocularsIcon, MagnifyingGlassIcon, LeafIcon } from '../icons';
import GameDetailView from './GameDetailView';
import { FALLBACK_CATEGORIES } from './photoSelectorFallbacks';
import BASE from '../utils/basePath';

const CATEGORY_ICONS = {
  cat1: BinocularsIcon,
  cat5: MagnifyingGlassIcon,
};

export default function PhotoSelector({ onPhotoSelect, isLoading }) {
  const [categories, setCategories] = useState(FALLBACK_CATEGORIES);
  const [selectedPhoto, setSelectedPhoto] = useState(null);

  useEffect(() => {
    let isActive = true;

    fetch(`${BASE}/api/entities`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch entities');
        return res.json();
      })
      .then((data) => {
        if (isActive && data.categories && data.categories.length > 0) {
          // Prefix asset paths from backend with BASE so they route through the proxy
          for (const cat of data.categories) {
            for (const photo of cat.photos || []) {
              if (photo.src && !photo.src.startsWith(BASE)) {
                photo.src = `${BASE}${photo.src}`;
              }
              const previews = photo.summary?.collectible_previews;
              if (previews) {
                for (const item of previews) {
                  if (item.image && !item.image.startsWith(BASE)) {
                    item.image = `${BASE}${item.image}`;
                  }
                }
              }
            }
          }
          setCategories(data.categories);
        }
      })
      .catch(() => {
        // Keep fallback categories on error
      });

    return () => {
      isActive = false;
    };
  }, []);

  const handlePhotoClick = async (photo) => {
    if (isLoading) return;
    try {
      const res = await fetch(photo.src);
      if (!res.ok) throw new Error('Demo photo unavailable');
      const blob = await res.blob();
      const file = new File([blob], `${photo.id}.png`, { type: blob.type || 'image/png' });
      onPhotoSelect(file);
    } catch {
      // Create fallback image with label text — read colors from CSS tokens
      const canvas = document.createElement('canvas');
      canvas.width = 400;
      canvas.height = 400;
      const ctx = canvas.getContext('2d');
      const styles = getComputedStyle(document.documentElement);
      ctx.fillStyle = styles.getPropertyValue('--color-nature-canvas-bg').trim() || '#E8F5E9';
      ctx.fillRect(0, 0, 400, 400);
      ctx.fillStyle = styles.getPropertyValue('--color-forest').trim() || '#4CAF50';
      ctx.font = '80px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(photo.label[0], 200, 200);
      canvas.toBlob((blob) => {
        const file = new File([blob], `${photo.id}.png`, { type: 'image/png' });
        onPhotoSelect(file);
      }, 'image/png');
    }
  };

  if (selectedPhoto) {
    return (
      <GameDetailView
        photo={selectedPhoto}
        onBack={() => setSelectedPhoto(null)}
        onStart={() => handlePhotoClick(selectedPhoto)}
        isLoading={isLoading}
      />
    );
  }

  return (
    <div className="flex flex-col items-center justify-center h-full p-6 overflow-y-auto">
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-[var(--color-forest)] to-[var(--color-forest-dark)] flex items-center justify-center mb-4 shadow-lg">
        <CameraIcon className="w-7 h-7 text-white" />
      </div>
      <h2 className="text-2xl font-bold font-display text-[var(--color-forest-dark)] mb-1 tracking-tight">Pick a Photo to Explore!</h2>
      <p className="text-gray-500 text-sm mb-8">Select a demo photo or upload your own</p>

      {isLoading ? (
        <div className="flex flex-col items-center gap-4">
          <div className="w-14 h-14 border-[3px] border-gray-200 border-t-[var(--color-forest)] rounded-full animate-spin" />
          <p className="text-[var(--color-forest)] font-medium text-sm">Starting your adventure...</p>
        </div>
      ) : (
        <>
          {categories.map((cat, catIdx) => {
            const Icon = CATEGORY_ICONS[cat.id] || BinocularsIcon;
            return (
              <div key={cat.id} className="w-full max-w-lg mb-6">
                {/* Category header */}
                <div className="flex items-center gap-2 mb-2">
                  <Icon className="w-5 h-5 text-[var(--color-forest)]" />
                  <div>
                    <h3 className="text-sm font-bold text-[var(--color-forest-dark)]">{cat.title}</h3>
                    <p className="text-xs text-gray-500">{cat.subtitle}</p>
                  </div>
                </div>

                {/* Photo cards */}
                <div className="grid grid-cols-3 gap-3 mb-4">
                  {cat.photos.map((photo) => (
                    <button
                      key={photo.id}
                      onClick={() => setSelectedPhoto(photo)}
                      className="group relative w-full aspect-square rounded-2xl overflow-hidden hover:shadow-md transition-all duration-200 cursor-pointer hover:scale-[1.02]"
                    >
                      <img
                        src={photo.src}
                        alt={photo.label}
                        className="w-full h-full object-cover"
                      />
                      <span className="absolute bottom-0 inset-x-0 text-xs text-center text-[var(--color-forest-dark)] bg-white/90 py-1 truncate font-medium">
                        {photo.label}
                      </span>
                    </button>
                  ))}
                </div>

                {/* Vine divider between categories */}
                {catIdx < categories.length - 1 && (
                  <div className="flex items-center gap-2 my-4">
                    <div className="flex-1 h-px bg-[var(--color-forest)]/20" />
                    <LeafIcon className="w-4 h-4 text-[var(--color-forest)]/30" />
                    <div className="flex-1 h-px bg-[var(--color-forest)]/20" />
                  </div>
                )}
              </div>
            );
          })}

          {/* Upload zone — disabled for now */}
          <div
            aria-label="Custom photo upload coming soon"
            className="w-full max-w-md border-2 border-dashed rounded-2xl p-6 text-center border-gray-200 bg-gray-50 opacity-60 cursor-not-allowed"
          >
            <p className="text-gray-400 text-sm">
              Custom photo upload coming soon
            </p>
          </div>
        </>
      )}
    </div>
  );
}
