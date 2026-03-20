import { PhotoFrameIcon } from '../icons';

export default function PhotoDisplay({ photoUrl, description, animation, entity }) {
  return (
    <div className="relative flex flex-col items-center gap-3">
      <div className={`relative w-full max-w-md aspect-square rounded-2xl overflow-hidden ${
        animation === 'sparkle_highlight' ? 'animate-fade-in' : ''
      }`}>
        {photoUrl ? (
          <img src={photoUrl} alt={entity || 'Photo'} loading="lazy" className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-[var(--color-sky-light)]/20">
            <PhotoFrameIcon className="w-16 h-16 text-[var(--color-forest)]/40" />
          </div>
        )}
        {animation === 'sparkle_highlight' && (
          <div className="absolute inset-0 bg-gradient-to-tr from-[var(--color-sunflower)]/10 via-transparent to-[var(--color-sky)]/10" />
        )}
      </div>
      {description && (
        <p className="text-sm text-gray-500 text-center max-w-xs">{description}</p>
      )}
    </div>
  );
}
