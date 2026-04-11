import { PhotoFrameIcon } from '../icons';

export default function PhotoDisplay({ photoUrl, description, animation, entity }) {
  return (
    <div className="relative flex flex-col items-center justify-center gap-2 max-[380px]:gap-1.5 w-full h-full min-h-0">
      {/* Background photo panel — hover lifts the frame gently to match
       * the scene/achievement images so every rendered image in the demo
       * behaves consistently on hover. The frame itself (not just the
       * <img>) gets the transform so the shadow animates too. */}
      <div className={`relative h-[min(100%,8.75rem)] aspect-square w-auto max-w-[11rem] rounded-2xl max-[380px]:rounded-xl overflow-hidden bg-white shadow-md transition-transform duration-300 ease-out hover:scale-[1.03] hover:shadow-xl ${
        animation === 'sparkle_highlight' ? 'animate-fade-in' : ''
      }`}>
        {photoUrl ? (
          <img src={photoUrl} alt={entity || 'Photo'} loading="lazy" className="w-full h-full object-contain" />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-[var(--color-sky-light)]/20">
            <PhotoFrameIcon className="w-9 h-9 max-[380px]:w-8 max-[380px]:h-8 text-[var(--color-forest)]/40" />
          </div>
        )}
        {animation === 'sparkle_highlight' && (
          <div className="absolute inset-0 bg-gradient-to-tr from-[var(--color-sunflower)]/10 via-transparent to-[var(--color-sky)]/10" />
        )}
      </div>
      {description && (
        <p className="text-xs text-gray-500 text-center max-w-[14rem]">{description}</p>
      )}
    </div>
  );
}
