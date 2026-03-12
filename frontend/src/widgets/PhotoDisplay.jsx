export default function PhotoDisplay({ photoUrl, description, animation, entity }) {
  return (
    <div className="relative flex flex-col items-center gap-3">
      <div className={`relative w-64 h-64 rounded-2xl overflow-hidden border border-white/10 ${
        animation === 'sparkle_highlight' ? 'animate-pulse' : ''
      }`}>
        {photoUrl ? (
          <img src={photoUrl} alt={entity || 'Photo'} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full bg-[#1a1a1a] flex items-center justify-center">
            <span className="text-6xl">📷</span>
          </div>
        )}
        {animation === 'sparkle_highlight' && (
          <div className="absolute inset-0 bg-fuchsia-500/10 animate-pulse" />
        )}
      </div>
      {description && (
        <p className="text-sm text-neutral-400 text-center max-w-xs">{description}</p>
      )}
    </div>
  );
}
