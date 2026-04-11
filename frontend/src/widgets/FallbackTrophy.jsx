import { useState } from 'react';
import { asset } from '../utils/basePath';

/**
 * Gradient-circle fallback shown when an AI-generated achievement image is
 * unavailable. The center is the game's entity icon (e.g. dandelion.png,
 * ladybug.png, dog.png) so each game has a distinct visual. If the entity
 * icon fails to load or no entity is provided, falls back to a trophy emoji.
 *
 * The role title is NOT rendered here — the parent AchievementImage already
 * shows it above to avoid duplication.
 */
export default function FallbackTrophy({ entity }) {
  const [iconFailed, setIconFailed] = useState(false);
  const showIcon = entity && !iconFailed;

  return (
    <div className="w-full h-full rounded-3xl bg-gradient-to-br from-[var(--color-sunflower-light)]/30 via-white/50 to-[var(--color-forest)]/10 flex items-center justify-center">
      <div className="relative">
        <div className="w-40 h-40 max-[380px]:w-32 max-[380px]:h-32 rounded-full bg-gradient-to-br from-[var(--color-sunflower)] via-[var(--color-sunflower-light)] to-[var(--color-forest)] shadow-xl flex items-center justify-center border-4 border-white/80">
          <div className="w-28 h-28 max-[380px]:w-24 max-[380px]:h-24 rounded-full bg-white/80 flex items-center justify-center overflow-hidden">
            {showIcon ? (
              <img
                src={asset(`/icons/${entity}.png`)}
                alt={entity}
                className="w-[90%] h-[90%] object-contain"
                onError={() => setIconFailed(true)}
              />
            ) : (
              <span className="text-6xl max-[380px]:text-5xl">🏆</span>
            )}
          </div>
        </div>
        <div className="absolute -top-3 -right-3 w-6 h-6 rounded-full bg-[var(--color-sunflower)] animate-sparkle-large" />
        <div className="absolute -bottom-2 -left-3 w-5 h-5 rounded-full bg-[var(--color-forest-light)] animate-sparkle-large" style={{ animationDelay: '0.8s' }} />
        <div className="absolute top-0 -left-4 w-4 h-4 rounded-full bg-[var(--color-teal)] animate-sparkle-large" style={{ animationDelay: '1.4s' }} />
      </div>
    </div>
  );
}
