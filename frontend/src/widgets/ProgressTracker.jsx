export default function ProgressTracker({ filled = 0, total = 4, description }) {
  const slots = Array.from({ length: total }, (_, i) => i < filled);

  return (
    <div className="flex flex-col items-center gap-4 p-4">
      <h3 className="text-lg font-bold text-purple-700">Collection Progress</h3>

      <div className="flex gap-3">
        {slots.map((isFilled, i) => (
          <div
            key={i}
            className={`w-16 h-16 rounded-full border-3 flex items-center justify-center transition-all duration-500 ${
              isFilled
                ? 'bg-gradient-to-br from-green-400 to-emerald-500 border-green-300 shadow-lg shadow-green-200 scale-110'
                : 'bg-gray-100 border-gray-300 border-dashed'
            } ${!isFilled && i === filled ? 'animate-pulse border-purple-400' : ''}`}
          >
            {isFilled ? (
              <span className="text-white text-2xl">✓</span>
            ) : (
              <span className="text-gray-300 text-xl">{i + 1}</span>
            )}
          </div>
        ))}
      </div>

      <p className={`text-sm font-medium ${filled >= total ? 'text-green-600' : 'text-gray-600'}`}>
        {filled >= total ? 'Collection Complete!' : `${filled} of ${total} found`}
      </p>

      {description && (
        <p className="text-xs text-gray-500 text-center max-w-xs">{description}</p>
      )}
    </div>
  );
}
