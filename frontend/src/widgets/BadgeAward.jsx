import { BadgeIcon, StarIcon } from '../icons';

export default function BadgeAward({ title, concepts = [], animation, entity }) {
  return (
    <div className={`flex flex-col items-center gap-4 p-6 ${
      animation === 'badge_reveal' ? 'animate-celebration-large' : ''
    }`}>
      {/* Badge */}
      <div className="relative">
        <div className="w-44 h-44 rounded-full bg-gradient-to-br from-[var(--color-sunflower)] via-[var(--color-sunflower-light)] to-[var(--color-forest)] shadow-lg flex items-center justify-center border-4 border-white/80">
          <div className="w-32 h-32 rounded-full bg-white/70 flex items-center justify-center">
            <BadgeIcon className="w-16 h-16 text-[var(--color-sunflower)]" />
          </div>
        </div>
        <div className="absolute -top-2 -right-2 animate-spin-slow">
          <StarIcon className="w-8 h-8 text-[var(--color-sunflower)]" />
        </div>
        <div className="absolute -bottom-1 -left-2 animate-pulse">
          <StarIcon className="w-6 h-6 text-[var(--color-forest)]" />
        </div>
      </div>

      {/* Title */}
      <h2 className="text-xl font-bold font-display text-center text-[var(--color-forest-dark)] tracking-tight">
        {title || 'Explorer'}
      </h2>

      {entity && (
        <p className="text-sm text-gray-400">{entity}</p>
      )}

      {/* Concepts */}
      {concepts.length > 0 && (
        <div className="flex flex-wrap justify-center gap-2 mt-2">
          {concepts.map((concept, i) => (
            <span
              key={i}
              className="px-4 py-1.5 bg-[var(--color-forest)]/10 text-[var(--color-forest-dark)] rounded-full text-sm font-medium border border-[var(--color-forest)]/20 shadow-sm"
              style={{ animationDelay: `${i * 300}ms` }}
            >
              {concept}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
