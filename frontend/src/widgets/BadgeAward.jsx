import { useState } from 'react';
import { BadgeIcon, StarIcon } from '../icons';
import BASE from '../utils/basePath';

function CssBadgeFallback() {
  return (
    <div className="w-44 h-44 rounded-full bg-gradient-to-br from-[var(--color-sunflower)] via-[var(--color-sunflower-light)] to-[var(--color-forest)] shadow-lg flex items-center justify-center border-4 border-white/80">
      <div className="w-32 h-32 rounded-full bg-white/70 flex items-center justify-center">
        <BadgeIcon className="w-16 h-16 text-[var(--color-sunflower)]" />
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
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-[var(--color-sunflower)] via-[var(--color-sunflower-light)] to-[var(--color-forest)] shadow-md flex items-center justify-center border-2 border-white/80">
          <BadgeIcon className="w-10 h-10 text-[var(--color-sunflower)]" />
        </div>
      ) : (
        <img
          src={src}
          alt={`${concept} badge`}
          className="w-20 h-20 rounded-full shadow-md border-2 border-[var(--color-sunflower)]/40 object-cover"
          onError={() => setImgFailed(true)}
        />
      )}
      <span className="px-3 py-1 bg-[var(--color-forest)]/10 text-[var(--color-forest-dark)] rounded-full text-xs font-medium border border-[var(--color-forest)]/20 shadow-sm">
        {concept}
      </span>
    </div>
  );
}

export default function BadgeAward({ title, concepts = [], animation, entity }) {
  const hasConcepts = concepts.length > 0;

  return (
    <div className={`flex flex-col items-center gap-4 p-6 ${
      animation === 'badge_reveal' ? 'animate-celebration-large' : ''
    }`}>
      {/* Main badge — show CSS fallback when no concepts, or as hero badge */}
      {!hasConcepts && (
        <div className="relative">
          <CssBadgeFallback />
          <div className="absolute -top-2 -right-2 animate-sparkle-large">
            <StarIcon className="w-7 h-7 text-[var(--color-sunflower)]" />
          </div>
          <div className="absolute -bottom-1 -left-2 animate-sparkle-large" style={{ animationDelay: '1s' }}>
            <StarIcon className="w-5 h-5 text-[var(--color-forest)]" />
          </div>
        </div>
      )}

      {/* Title */}
      <h2 className="text-xl font-bold font-display text-center text-[var(--color-forest-dark)] tracking-tight">
        {title || 'Explorer'}
      </h2>

      {entity && (
        <p className="text-sm text-gray-500">{entity}</p>
      )}

      {/* Concept badges with images */}
      {hasConcepts && (
        <div className="flex flex-wrap justify-center gap-5 mt-2">
          {concepts.map((concept, i) => (
            <ConceptBadge key={i} concept={concept} delay={i * 300} />
          ))}
        </div>
      )}
    </div>
  );
}
