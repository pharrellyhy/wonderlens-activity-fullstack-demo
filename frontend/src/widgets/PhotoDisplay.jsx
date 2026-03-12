export default function PhotoDisplay({ photoUrl, description, animation, entity }) {
  return (
    <div className="relative flex flex-col items-center gap-3">
      <div className={`relative w-64 h-64 rounded-2xl overflow-hidden shadow-lg border-4 border-white ${
        animation === 'sparkle_highlight' ? 'animate-pulse' : ''
      }`}>
        {photoUrl ? (
          <img src={photoUrl} alt={entity || 'Photo'} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-purple-100 to-pink-100 flex items-center justify-center">
            <span className="text-6xl">📷</span>
          </div>
        )}
        {animation === 'sparkle_highlight' && (
          <div className="absolute inset-0 bg-gradient-to-tr from-yellow-200/20 via-transparent to-purple-200/20 animate-pulse" />
        )}
      </div>
      {description && (
        <p className="text-sm text-gray-600 text-center max-w-xs">{description}</p>
      )}
    </div>
  );
}
