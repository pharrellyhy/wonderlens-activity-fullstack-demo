import { asset } from '../utils/basePath';
import { StarIcon } from '../icons';

export default function ConceptMedallion({ concept, delayMs = 0 }) {
  const badgeSrc = asset(`/badges/${concept.toLowerCase()}.png`);

  return (
    <div className="flex flex-col items-center gap-2 animate-badge-pop" style={{ animationDelay: `${delayMs}ms` }}>
      {/* Outer gradient circle — mirrors ExplorerMap ZoneSlot shape */}
      <div className="relative">
        <div className="w-[clamp(6rem,22vw,8rem)] h-[clamp(6rem,22vw,8rem)] rounded-full bg-gradient-to-br from-[var(--color-sunflower)] via-[var(--color-sunflower-light)] to-[var(--color-forest)] border-[4px] border-white/90 shadow-xl flex items-center justify-center animate-gentle-float" style={{ animationDelay: `${delayMs + 200}ms` }}>
          {/* Inner white disc holds the badge PNG */}
          <div className="w-[78%] h-[78%] rounded-full bg-white/90 flex items-center justify-center overflow-hidden">
            <img
              src={badgeSrc}
              alt={concept}
              className="w-[85%] h-[85%] object-contain"
              onError={(e) => {
                // Graceful fallback: if the PNG is missing, show a sparkle emoji
                const parent = e.currentTarget.parentElement;
                if (parent) {
                  parent.innerHTML = '<span class="text-3xl">✨</span>';
                }
              }}
            />
          </div>
        </div>

        {/* Star accent top-right, mirrors ZoneSlot's checkmark accent */}
        <div className="absolute -top-1 -right-1 animate-sparkle-large" style={{ animationDelay: `${delayMs + 800}ms` }}>
          <StarIcon className="w-6 h-6 text-[var(--color-sunflower)] drop-shadow" />
        </div>
      </div>

      {/* Concept name pill — same treatment as ZoneSlot character label */}
      <span className="px-4 py-1 bg-white/90 backdrop-blur-sm rounded-full text-base max-[380px]:text-sm font-semibold text-[var(--color-forest-dark)] shadow-sm border border-[var(--color-forest)]/15 animate-fade-in" style={{ animationDelay: `${delayMs + 400}ms` }}>
        {concept}
      </span>
    </div>
  );
}
