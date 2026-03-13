export default function PhotoDisplay({ photoUrl, description, animation, entity }) {
  return (
    <div className="relative flex flex-col items-center gap-3">
      <div className={`relative w-64 h-64 rounded-2xl overflow-hidden bg-white/40 border border-white/60 shadow-lg shadow-black/5 ${
        animation === 'sparkle_highlight' ? 'animate-pulse' : ''
      }`}>
        {photoUrl ? (
          <img src={photoUrl} alt={entity || 'Photo'} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span className="text-6xl">📷</span>
          </div>
        )}
        {animation === 'sparkle_highlight' && (
          <div className="absolute inset-0 bg-gradient-to-tr from-amber-200/20 via-transparent to-indigo-200/20 animate-pulse" />
        )}
      </div>
      {description && (
        <p className="text-sm text-gray-500 text-center max-w-xs">{description}</p>
      )}
    </div>
  );
}
