export default function AchievementImage({ image_data_url, title, concepts = [], animation, sessionState }) {
  const collectedNames = sessionState?.collected_names || [];

  return (
    <div className={`flex flex-col items-center gap-3 p-4 h-full ${
      animation === 'badge_reveal' ? 'animate-celebration-large' : ''
    }`}>
      {/* Role title — large and prominent */}
      <h2 className="text-xl max-[380px]:text-lg font-bold font-display text-center text-[var(--color-forest-dark)] tracking-tight">
        {title || 'Explorer'}
      </h2>

      {/* Achievement image or decorative fallback */}
      <div className="flex-1 min-h-0 w-full flex items-center justify-center overflow-hidden">
        {image_data_url ? (
          <img
            src={image_data_url}
            alt="Your adventure"
            className="w-full h-full rounded-2xl shadow-lg object-contain animate-fade-in"
          />
        ) : (
          <div className="w-full h-full rounded-2xl bg-gradient-to-br from-[var(--color-sunflower-light)]/30 via-white/50 to-[var(--color-forest)]/10 flex flex-col items-center justify-center gap-5">
            <div className="relative">
              <div className="w-32 h-32 max-[380px]:w-24 max-[380px]:h-24 rounded-full bg-gradient-to-br from-[var(--color-sunflower)] via-[var(--color-sunflower-light)] to-[var(--color-forest)] shadow-xl flex items-center justify-center border-4 border-white/80">
                <div className="w-20 h-20 max-[380px]:w-16 max-[380px]:h-16 rounded-full bg-white/70 flex items-center justify-center">
                  <span className="text-5xl max-[380px]:text-4xl">🏆</span>
                </div>
              </div>
              <div className="absolute -top-3 -right-3 w-6 h-6 rounded-full bg-[var(--color-sunflower)] animate-sparkle-large" />
              <div className="absolute -bottom-2 -left-3 w-5 h-5 rounded-full bg-[var(--color-forest-light)] animate-sparkle-large" style={{ animationDelay: '0.8s' }} />
              <div className="absolute top-0 -left-4 w-4 h-4 rounded-full bg-[var(--color-teal)] animate-sparkle-large" style={{ animationDelay: '1.4s' }} />
            </div>
            <p className="text-xl max-[380px]:text-lg font-display font-bold text-[var(--color-forest-dark)]">
              {title || 'Explorer'}
            </p>
          </div>
        )}
      </div>

      {/* Character names — large pills */}
      {collectedNames.length > 0 && (
        <div className="flex flex-wrap justify-center gap-2">
          {collectedNames.map((name) => (
            <span key={name} className="px-3.5 py-1 bg-[var(--color-forest)]/10 text-[var(--color-forest-dark)] rounded-full text-sm max-[380px]:text-xs font-semibold border border-[var(--color-forest)]/20 shadow-sm">
              {name}
            </span>
          ))}
        </div>
      )}

      {/* IB Concept badges — large */}
      {concepts.length > 0 && (
        <div className="flex flex-wrap justify-center gap-2.5">
          {concepts.map((concept) => (
            <span key={concept} className="px-4 py-1.5 bg-[var(--color-sunflower)]/20 text-[var(--color-forest-dark)] rounded-full text-base font-bold border border-[var(--color-sunflower)]/30 shadow-sm animate-badge-pop">
              {concept}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
