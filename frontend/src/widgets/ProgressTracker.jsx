import { CheckmarkIcon } from '../icons';

export default function ProgressTracker({ filled = 0, total = 4, description }) {
  const slots = Array.from({ length: total }, (_, i) => i < filled);

  return (
    <div className="flex flex-col items-center gap-4 p-4">
      <h3 className="text-lg font-bold font-display text-[var(--color-forest-dark)] tracking-tight">Collection Progress</h3>

      <div className="flex gap-3">
        {slots.map((isFilled, i) => (
          <div
            key={i}
            className={`w-20 h-20 rounded-full border-3 flex items-center justify-center transition-all duration-500 ${
              isFilled
                ? 'bg-gradient-to-br from-[var(--color-forest)] to-[var(--color-forest-dark)] border-white/80 scale-110 shadow-lg'
                : 'bg-[var(--color-sky-light)]/30 border-[var(--color-sky)]/50 border-dashed'
            } ${!isFilled && i === filled ? 'animate-pulse border-[var(--color-teal)]' : ''}`}
          >
            {isFilled ? (
              <CheckmarkIcon className="w-8 h-8 text-white" />
            ) : (
              <span className="text-[var(--color-sky)] text-xl font-bold">{i + 1}</span>
            )}
          </div>
        ))}
      </div>

      <p className={`text-sm font-medium ${filled >= total ? 'text-[var(--color-forest)]' : 'text-gray-400'}`}>
        {filled >= total ? 'Collection Complete!' : `${filled} of ${total} found`}
      </p>

      {description && (
        <p className="text-xs text-gray-400 text-center max-w-xs">{description}</p>
      )}
    </div>
  );
}
