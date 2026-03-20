import { useState, useEffect } from 'react';
import { CameraIcon, BinocularsIcon, MagnifyingGlassIcon, LeafIcon } from '../icons';
import GameDetailView from './GameDetailView';
import { FALLBACK_CATEGORIES } from './photoSelectorFallbacks';

const CATEGORY_ICONS = {
  cat1: BinocularsIcon,
  cat5: MagnifyingGlassIcon,
};

export default function PhotoSelector({ onPhotoSelect, isLoading }) {
  const [dragOver, setDragOver] = useState(false);
  const [categories, setCategories] = useState(FALLBACK_CATEGORIES);
  const [selectedPhoto, setSelectedPhoto] = useState(null);

  useEffect(() => {
    let isActive = true;

    fetch('/api/entities')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch entities');
        return res.json();
      })
      .then((data) => {
        if (isActive && data.categories && data.categories.length > 0) {
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

  const handleFileUpload = (file) => {
    if (file && file.type.startsWith('image/')) {
      onPhotoSelect(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFileUpload(file);
  };

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

  const handleDropZoneKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = 'image/*';
      input.onchange = (ev) => handleFileUpload(ev.target.files[0]);
      input.click();
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

          {/* Upload zone */}
          <div
            role="button"
            tabIndex={0}
            aria-label="Upload a photo by dropping or clicking"
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onKeyDown={handleDropZoneKeyDown}
            className={`w-full max-w-md border-2 border-dashed rounded-2xl p-6 text-center transition-all cursor-pointer ${
              dragOver ? 'border-[var(--color-forest)] bg-[var(--color-forest)]/5 scale-[1.01]' : 'border-[var(--color-forest)]/30 hover:border-[var(--color-forest)]/50 hover:bg-[var(--color-forest)]/5'
            }`}
            onClick={() => {
              const input = document.createElement('input');
              input.type = 'file';
              input.accept = 'image/*';
              input.onchange = (e) => handleFileUpload(e.target.files[0]);
              input.click();
            }}
          >
            <p className="text-gray-500 text-sm">
              Drop a photo here or <span className="text-[var(--color-forest)] font-medium">click to upload</span>
            </p>
          </div>
        </>
      )}
    </div>
  );
}
