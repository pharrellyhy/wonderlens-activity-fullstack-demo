export default function PhotoGrid({ photos = [], animation }) {
  const slots = Array.from({ length: 4 }, (_, i) => photos[i] || null);

  return (
    <div className="flex flex-col items-center gap-3 p-4">
      <h3 className="text-lg font-bold font-display text-gray-700 tracking-tight">Your Collection</h3>

      <div className={`grid grid-cols-2 gap-3 ${
        animation === 'connection_lines_draw' ? 'animate-pulse' : ''
      }`}>
        {slots.map((photo, i) => (
          <div
            key={i}
            className="w-28 h-28 rounded-xl overflow-hidden bg-white/40 border border-white/60 shadow-sm flex items-center justify-center"
          >
            {photo ? (
              <img src={photo} alt={`Find ${i + 1}`} className="w-full h-full object-cover" />
            ) : (
              <div className="text-center">
                <span className="text-3xl text-gray-300">📷</span>
                <p className="text-xs text-gray-300 mt-1">#{i + 1}</p>
              </div>
            )}
          </div>
        ))}
      </div>

      {animation === 'connection_lines_draw' && (
        <p className="text-sm text-indigo-500 font-medium animate-bounce">Connected!</p>
      )}
    </div>
  );
}
