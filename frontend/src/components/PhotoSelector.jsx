import { useState, useEffect } from 'react';
import { CameraIcon, BinocularsIcon, MagnifyingGlassIcon, LeafIcon } from '../icons';
import GameDetailView from './GameDetailView';
import { FALLBACK_CATEGORIES } from './photoSelectorFallbacks';
import BASE from '../utils/basePath';

const CATEGORY_ICONS = {
  cat1: BinocularsIcon,
  cat5: MagnifyingGlassIcon,
};

function prefixedAssetPath(path) {
  if (!path || path.startsWith(BASE) || path.startsWith('data:')) return path;
  return `${BASE}${path}`;
}

function normalizeCategories(dataCategories) {
  return (dataCategories || []).map((cat) => ({
    ...cat,
    photos: (cat.photos || []).map((photo) => ({
      ...photo,
      src: prefixedAssetPath(photo.src),
      summary: {
        ...(photo.summary || {}),
        collectible_previews: (photo.summary?.collectible_previews || []).map((item) => ({
          ...item,
          image: prefixedAssetPath(item.image),
        })),
      },
    })),
  }));
}

function photoFilename(photo) {
  return photo.filename || photo.demo_filename || `${photo.id}.png`;
}

function photoSupportStatus(photo) {
  return photo.summary?.support_status || photo.support_status || 'supported';
}

function photoTemplate(photo, categoryId) {
  return photo.summary?.template_type || photo.template_type || categoryId;
}

function photoEntity(photo) {
  return photo.summary?.entity_binding?.entity_id || photo.entity_id || photo.id;
}

function requiredMissingAssets(photo) {
  return photo.summary?.asset_readiness_detail?.required_missing || [];
}

function isPlayable(photo) {
  return (
    photoSupportStatus(photo) !== 'unsupported' &&
    photo.summary?.asset_readiness !== 'blocked' &&
    requiredMissingAssets(photo).length === 0
  );
}

export default function PhotoSelector({ onPhotoSelect, isLoading, onOpenGallery }) {
  const [categories, setCategories] = useState(FALLBACK_CATEGORIES);
  const [selectedPhoto, setSelectedPhoto] = useState(null);
  const [includeDegraded, setIncludeDegraded] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [templateFilter, setTemplateFilter] = useState('all');
  const [supportFilter, setSupportFilter] = useState('all');
  const [entityFilter, setEntityFilter] = useState('');

  useEffect(() => {
    let isActive = true;

    fetch(`${BASE}/api/entities`)
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch entities');
        return res.json();
      })
      .then((data) => {
        if (isActive && data.categories && data.categories.length > 0) {
          setCategories(normalizeCategories(data.categories));
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
    if (isLoading || !isPlayable(photo)) return;
    const filename = photoFilename(photo);
    try {
      const res = await fetch(photo.src);
      if (!res.ok) throw new Error('Demo photo unavailable');
      const blob = await res.blob();
      const file = new File([blob], filename, { type: blob.type || 'image/png' });
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
        const file = new File([blob], filename, { type: 'image/png' });
        onPhotoSelect(file);
      }, 'image/png');
    }
  };

  const filteredCategories = categories
    .filter((cat) => categoryFilter === 'all' || cat.id === categoryFilter)
    .map((cat) => {
      const photos = (cat.photos || []).filter((photo) => {
        const support = photoSupportStatus(photo);
        if (support === 'unsupported') return false;
        if (support === 'degraded' && !includeDegraded && supportFilter !== 'degraded') {
          return false;
        }
        if (supportFilter !== 'all' && supportFilter !== support) return false;
        if (templateFilter !== 'all' && photoTemplate(photo, cat.id) !== templateFilter) return false;
        if (entityFilter.trim()) {
          const entityText = `${photoEntity(photo)} ${photo.label} ${photo.activity_type || ''}`.toLowerCase();
          if (!entityText.includes(entityFilter.trim().toLowerCase())) return false;
        }
        return true;
      });
      return { ...cat, photos };
    })
    .filter((cat) => cat.photos.length > 0);

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
    <div className="relative flex flex-col items-center justify-start min-h-full p-6 max-[380px]:p-4 overflow-y-auto">
      {onOpenGallery ? (
        <button
          type="button"
          onClick={onOpenGallery}
          className="absolute top-3 right-3 max-[380px]:top-2 max-[380px]:right-2 text-xs font-medium text-[var(--color-forest-dark)]/70 hover:text-[var(--color-forest-dark)] underline-offset-2 hover:underline cursor-pointer"
        >
          View feedback gallery →
        </button>
      ) : null}
      <div className="w-10 h-10 sm:w-14 sm:h-14 max-[380px]:w-9 max-[380px]:h-9 rounded-2xl max-[380px]:rounded-xl bg-gradient-to-br from-[var(--color-forest)] to-[var(--color-forest-dark)] flex items-center justify-center mb-4 max-[380px]:mb-3 shadow-lg">
        <CameraIcon className="w-5 h-5 sm:w-7 sm:h-7 max-[380px]:w-4 max-[380px]:h-4 text-white" />
      </div>
      <h2 className="text-xl sm:text-2xl max-[380px]:text-lg font-bold font-display text-[var(--color-forest-dark)] mb-1 tracking-tight text-center">Pick a Photo to Explore!</h2>
      <p className="text-gray-500 text-sm max-[380px]:text-xs mb-8 max-[380px]:mb-5 text-center">Select a demo photo or upload your own</p>

      {isLoading ? (
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 sm:w-14 sm:h-14 max-[380px]:w-9 max-[380px]:h-9 border-[3px] border-gray-200 border-t-[var(--color-forest)] rounded-full animate-spin" />
          <p className="text-[var(--color-forest)] font-medium text-sm max-[380px]:text-xs">Starting your adventure...</p>
        </div>
      ) : (
        <>
          <div className="w-full max-w-lg mb-5 rounded-xl border border-[var(--color-forest)]/10 bg-white/70 p-3">
            <div className="grid grid-cols-2 gap-2">
              <label className="text-[11px] font-medium text-gray-500">
                Category
                <select
                  aria-label="Category filter"
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-[var(--color-forest)]/20 bg-white px-2 py-1 text-xs text-[var(--color-forest-dark)]"
                >
                  <option value="all">All</option>
                  <option value="cat1">Cat 1</option>
                  <option value="cat5">Cat 5</option>
                </select>
              </label>
              <label className="text-[11px] font-medium text-gray-500">
                Template
                <select
                  aria-label="Template filter"
                  value={templateFilter}
                  onChange={(e) => setTemplateFilter(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-[var(--color-forest)]/20 bg-white px-2 py-1 text-xs text-[var(--color-forest-dark)]"
                >
                  <option value="all">All</option>
                  <option value="cat1">Cat 1</option>
                  <option value="cat5">Cat 5</option>
                </select>
              </label>
              <label className="text-[11px] font-medium text-gray-500">
                Support
                <select
                  aria-label="Support filter"
                  value={supportFilter}
                  onChange={(e) => setSupportFilter(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-[var(--color-forest)]/20 bg-white px-2 py-1 text-xs text-[var(--color-forest-dark)]"
                >
                  <option value="all">All playable</option>
                  <option value="supported">Supported</option>
                  <option value="degraded">Degraded</option>
                </select>
              </label>
              <label className="text-[11px] font-medium text-gray-500">
                Entity
                <input
                  aria-label="Entity filter"
                  value={entityFilter}
                  onChange={(e) => setEntityFilter(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-[var(--color-forest)]/20 bg-white px-2 py-1 text-xs text-[var(--color-forest-dark)]"
                  placeholder="cat"
                />
              </label>
            </div>
            <label className="mt-2 flex items-center gap-2 text-xs text-gray-600">
              <input
                type="checkbox"
                checked={includeDegraded}
                onChange={(e) => setIncludeDegraded(e.target.checked)}
                className="h-3.5 w-3.5 accent-[var(--color-forest)]"
              />
              Include degraded
            </label>
          </div>

          {filteredCategories.map((cat, catIdx) => {
            const Icon = CATEGORY_ICONS[cat.id] || BinocularsIcon;
            return (
              <div key={cat.id} className="w-full max-w-lg mb-6 max-[380px]:mb-4">
                {/* Category header */}
                <div className="flex items-center gap-2 mb-2 max-[380px]:mb-1.5">
                  <Icon className="w-5 h-5 max-[380px]:w-4 max-[380px]:h-4 text-[var(--color-forest)]" />
                  <div>
                    <h3 className="text-sm max-[380px]:text-xs font-bold text-[var(--color-forest-dark)]">{cat.title}</h3>
                    <p className="text-xs max-[380px]:text-[11px] text-gray-500">{cat.subtitle}</p>
                  </div>
                </div>

                {/* Photo cards */}
                <div className="grid grid-cols-3 gap-3 max-[380px]:gap-2 mb-4 max-[380px]:mb-3">
                  {cat.photos.map((photo) => {
                    const playable = isPlayable(photo);
                    return (
                      <button
                        key={photo.id}
                        onClick={() => setSelectedPhoto(photo)}
                        aria-disabled={!playable}
                        className={`group relative w-full aspect-square rounded-2xl max-[380px]:rounded-xl overflow-hidden hover:shadow-md transition-all duration-200 cursor-pointer hover:scale-[1.02] ${playable ? '' : 'opacity-65 cursor-help hover:scale-100'}`}
                      >
                        <img
                          src={photo.src}
                          alt={photo.label}
                          className="w-full h-full object-cover"
                        />
                        <span className="absolute bottom-0 inset-x-0 text-xs max-[380px]:text-[10px] text-center text-[var(--color-forest-dark)] bg-white/90 py-1 max-[380px]:py-0.5 truncate font-medium">
                          {photo.label}
                        </span>
                        {photo.summary?.source === 'autodesign' && (
                          <span className="absolute left-1.5 top-1.5 rounded-full bg-white/90 px-1.5 py-0.5 text-[9px] font-bold text-[var(--color-forest-dark)]">
                            {photoSupportStatus(photo) === 'degraded' ? 'Degraded' : 'Imported'}
                          </span>
                        )}
                        {photo.summary?.asset_readiness && photo.summary.asset_readiness !== 'ready' && (
                          <span className="absolute right-1.5 top-1.5 rounded-full bg-amber-100 px-1.5 py-0.5 text-[9px] font-bold text-amber-700">
                            {photo.summary.asset_readiness}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>

                {/* Vine divider between categories */}
                {catIdx < categories.length - 1 && (
                  <div className="flex items-center gap-2 my-4 max-[380px]:my-3">
                    <div className="flex-1 h-px bg-[var(--color-forest)]/20" />
                    <LeafIcon className="w-4 h-4 max-[380px]:w-3.5 max-[380px]:h-3.5 text-[var(--color-forest)]/30" />
                    <div className="flex-1 h-px bg-[var(--color-forest)]/20" />
                  </div>
                )}
              </div>
            );
          })}

          {/* Upload zone — disabled for now */}
          <div
            aria-label="Custom photo upload coming soon"
            className="w-full max-w-md border-2 border-dashed rounded-2xl max-[380px]:rounded-xl p-6 max-[380px]:p-4 text-center border-gray-200 bg-gray-50 opacity-60 cursor-not-allowed"
          >
            <p className="text-gray-400 text-sm max-[380px]:text-xs">
              Custom photo upload coming soon
            </p>
          </div>
        </>
      )}
    </div>
  );
}
