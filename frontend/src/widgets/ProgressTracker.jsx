import { CheckmarkIcon } from '../icons';

export default function ProgressTracker({ filled = 0, total = 4, description }) {
  const slots = Array.from({ length: total }, (_, i) => i < filled);

  return (
    <div className="flex flex-col items-center gap-3 max-[380px]:gap-2.5 p-3 max-[380px]:p-2.5">
      <h3 className="text-sm font-bold font-display text-[var(--color-forest-dark)] tracking-tight">Collection Progress</h3>

      <div className="flex flex-wrap justify-center gap-1.5 max-[380px]:gap-1">
        {slots.map((isFilled, i) => (
          <div
            key={i}
            className={`w-[clamp(2.45rem,10vw,3rem)] h-[clamp(2.45rem,10vw,3rem)] rounded-full border-[3px] flex items-center justify-center transition-all duration-500 ${
              isFilled
                ? 'bg-gradient-to-br from-[var(--color-forest)] to-[var(--color-forest-dark)] border-white/80 shadow-md'
                : 'bg-[var(--color-sky-light)]/30 border-[var(--color-sky)]/50 border-dashed'
            } ${!isFilled && i === filled ? 'animate-gentle-glow border-[var(--color-teal)]' : ''}`}
          >
            {isFilled ? (
              <CheckmarkIcon className="w-[clamp(0.9rem,4vw,1.1rem)] h-[clamp(0.9rem,4vw,1.1rem)] text-white" />
            ) : (
              <span className="text-[var(--color-sky)] text-sm font-bold">{i + 1}</span>
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
