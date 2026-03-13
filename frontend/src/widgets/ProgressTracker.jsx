export default function ProgressTracker({ filled = 0, total = 4, description }) {
  const slots = Array.from({ length: total }, (_, i) => i < filled);

  return (
    <div className="flex flex-col items-center gap-4 p-4">
      <h3 className="text-lg font-bold font-display text-gray-700 tracking-tight">Collection Progress</h3>

      <div className="flex gap-3">
        {slots.map((isFilled, i) => (
          <div
            key={i}
            className={`w-16 h-16 rounded-full border-2 flex items-center justify-center transition-all duration-500 ${
              isFilled
                ? 'bg-gradient-to-br from-emerald-400 to-green-500 border-white/80 scale-110 shadow-lg shadow-emerald-200/50'
                : 'bg-white/40 border-gray-200/50 border-dashed'
            } ${!isFilled && i === filled ? 'animate-pulse border-indigo-300' : ''}`}
          >
            {isFilled ? (
              <span className="text-white text-2xl">✓</span>
            ) : (
              <span className="text-gray-300 text-xl">{i + 1}</span>
            )}
          </div>
        ))}
      </div>

      <p className={`text-sm font-medium ${filled >= total ? 'text-emerald-500' : 'text-gray-400'}`}>
        {filled >= total ? 'Collection Complete!' : `${filled} of ${total} found`}
      </p>

      {description && (
        <p className="text-xs text-gray-400 text-center max-w-xs">{description}</p>
      )}
    </div>
  );
}
