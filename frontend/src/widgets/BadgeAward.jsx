import { useState } from 'react';
import { BadgeIcon, StarIcon } from '../icons';
import BASE from '../utils/basePath';

function CssBadgeFallback() {
  return (
    <div className="w-[clamp(5.5rem,24vw,8rem)] h-[clamp(5.5rem,24vw,8rem)] sm:w-44 sm:h-44 rounded-full bg-gradient-to-br from-[var(--color-sunflower)] via-[var(--color-sunflower-light)] to-[var(--color-forest)] shadow-lg flex items-center justify-center border-[3px] sm:border-4 border-white/80">
      <div className="w-[clamp(4rem,17vw,5.5rem)] h-[clamp(4rem,17vw,5.5rem)] sm:w-32 sm:h-32 rounded-full bg-white/70 flex items-center justify-center">
        <BadgeIcon className="w-[clamp(1.75rem,8vw,2.5rem)] h-[clamp(1.75rem,8vw,2.5rem)] sm:w-16 sm:h-16 text-[var(--color-sunflower)]" />
      </div>
    </div>
  );
}

function ConceptBadge({ concept, delay }) {
  const [imgFailed, setImgFailed] = useState(false);
  const src = `${BASE}/badges/${concept.toLowerCase()}.png`;

  return (
    <div
      className="flex flex-col items-center gap-2 animate-badge-pop"
      style={{ animationDelay: `${delay}ms` }}
    >
      {imgFailed ? (
        <div className="w-[clamp(3.25rem,14vw,3.5rem)] h-[clamp(3.25rem,14vw,3.5rem)] sm:w-20 sm:h-20 rounded-full bg-gradient-to-br from-[var(--color-sunflower)] via-[var(--color-sunflower-light)] to-[var(--color-forest)] shadow-md flex items-center justify-center border-2 border-white/80">
          <BadgeIcon className="w-[clamp(1.5rem,6vw,1.75rem)] h-[clamp(1.5rem,6vw,1.75rem)] sm:w-10 sm:h-10 text-[var(--color-sunflower)]" />
        </div>
      ) : (
        <img
          src={src}
          alt={`${concept} badge`}
          className="w-[clamp(3.25rem,14vw,3.5rem)] h-[clamp(3.25rem,14vw,3.5rem)] sm:w-20 sm:h-20 rounded-full shadow-md border-2 border-[var(--color-sunflower)]/40 object-cover"
          onError={() => setImgFailed(true)}
        />
      )}
      <span className="px-3 max-[380px]:px-2 py-1 max-[380px]:py-0.5 bg-[var(--color-forest)]/10 text-[var(--color-forest-dark)] rounded-full text-xs max-[380px]:text-[11px] font-medium border border-[var(--color-forest)]/20 shadow-sm">
        {concept}
      </span>
    </div>
  );
}

export default function BadgeAward({ title, concepts = [], animation, entity }) {
  const hasConcepts = concepts.length > 0;

  return (
    <div className={`flex flex-col items-center gap-3 sm:gap-4 max-[380px]:gap-2.5 p-4 sm:p-6 max-[380px]:p-3 ${
      animation === 'badge_reveal' ? 'animate-celebration-large' : ''
    }`}>
      {/* Main badge — show CSS fallback when no concepts, or as hero badge */}
      {!hasConcepts && (
        <div className="relative">
          <CssBadgeFallback />
          <div className="absolute -top-2 -right-2 animate-sparkle-large">
            <StarIcon className="w-5 h-5 sm:w-7 sm:h-7 max-[380px]:w-4 max-[380px]:h-4 text-[var(--color-sunflower)]" />
          </div>
          <div className="absolute -bottom-1 -left-2 animate-sparkle-large" style={{ animationDelay: '1s' }}>
            <StarIcon className="w-4 h-4 sm:w-5 sm:h-5 max-[380px]:w-3.5 max-[380px]:h-3.5 text-[var(--color-forest)]" />
          </div>
        </div>
      )}

      {/* Title */}
      <h2 className="text-lg sm:text-xl max-[380px]:text-base font-bold font-display text-center text-[var(--color-forest-dark)] tracking-tight">
        {title || 'Explorer'}
      </h2>

      {entity && (
        <p className="text-sm max-[380px]:text-xs text-gray-500">{entity}</p>
      )}

      {/* Concept badges with images */}
      {hasConcepts && (
        <div className="flex flex-wrap justify-center gap-5 max-[380px]:gap-3 mt-2">
          {concepts.map((concept, i) => (
            <ConceptBadge key={i} concept={concept} delay={i * 300} />
          ))}
        </div>
      )}
    </div>
  );
}
