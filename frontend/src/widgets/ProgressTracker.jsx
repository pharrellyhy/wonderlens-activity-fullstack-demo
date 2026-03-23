import { CheckmarkIcon } from '../icons';

export default function ProgressTracker({ filled = 0, total = 4, description }) {
  const slots = Array.from({ length: total }, (_, i) => i < filled);

  return (
    <div className="flex flex-col items-center gap-4 max-[380px]:gap-3 p-4 max-[380px]:p-3">
      <h3 className="text-base sm:text-lg max-[380px]:text-sm font-bold font-display text-[var(--color-forest-dark)] tracking-tight">Collection Progress</h3>

      <div className="flex flex-wrap justify-center gap-2 sm:gap-3 max-[380px]:gap-1.5">
        {slots.map((isFilled, i) => (
          <div
            key={i}
            className={`w-[clamp(2.8rem,12vw,3.5rem)] h-[clamp(2.8rem,12vw,3.5rem)] sm:w-20 sm:h-20 rounded-full border-[3px] flex items-center justify-center transition-all duration-500 ${
              isFilled
                ? 'bg-gradient-to-br from-[var(--color-forest)] to-[var(--color-forest-dark)] border-white/80 shadow-md'
                : 'bg-[var(--color-sky-light)]/30 border-[var(--color-sky)]/50 border-dashed'
            } ${!isFilled && i === filled ? 'animate-gentle-glow border-[var(--color-teal)]' : ''}`}
          >
            {isFilled ? (
              <CheckmarkIcon className="w-[clamp(1rem,5vw,1.25rem)] h-[clamp(1rem,5vw,1.25rem)] sm:w-8 sm:h-8 text-white" />
            ) : (
              <span className="text-[var(--color-sky)] text-base sm:text-xl max-[380px]:text-sm font-bold">{i + 1}</span>
            )}
          </div>
        ))}
      </div>

      <p className={`text-sm max-[380px]:text-xs font-medium ${filled >= total ? 'text-[var(--color-forest)]' : 'text-gray-500'}`}>
        {filled >= total ? 'Collection Complete!' : `${filled} of ${total} found`}
      </p>

      {description && (
        <p className="text-xs max-[380px]:text-[11px] text-gray-500 text-center max-w-xs">{description}</p>
      )}
    </div>
  );
}
