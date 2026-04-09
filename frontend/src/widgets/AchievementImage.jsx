export default function AchievementImage({ image_data_url, title, concepts = [], animation, sessionState }) {
  const collectedNames = sessionState?.collected_names || [];

  return (
    <div className={`flex flex-col items-center gap-2 p-2 max-[380px]:p-1.5 h-full ${
      animation === 'badge_reveal' ? 'animate-celebration-large' : ''
    }`}>
      <h2 className="text-sm max-[380px]:text-xs font-bold font-display text-center text-[var(--color-forest-dark)] tracking-tight">
        {title || 'Explorer'}
      </h2>

      <div className="flex-1 min-h-0 w-full flex items-center justify-center">
        {image_data_url ? (
          <img
            src={image_data_url}
            alt="Your adventure"
            className="max-w-full max-h-full rounded-xl shadow-lg border-2 border-[var(--color-sunflower)]/30 object-contain animate-fade-in"
          />
        ) : (
          <div className="w-full aspect-square rounded-xl bg-gradient-to-br from-[var(--color-sunflower-light)]/30 to-[var(--color-forest)]/10 flex items-center justify-center">
            <p className="text-sm text-gray-400">Your adventure!</p>
          </div>
        )}
      </div>

      {collectedNames.length > 0 && (
        <div className="flex flex-wrap justify-center gap-1.5">
          {collectedNames.map((name) => (
            <span key={name} className="px-2 py-0.5 bg-[var(--color-forest)]/10 text-[var(--color-forest-dark)] rounded-full text-xs max-[380px]:text-[11px] font-medium border border-[var(--color-forest)]/20">
              {name}
            </span>
          ))}
        </div>
      )}

      {concepts.length > 0 && (
        <div className="flex flex-wrap justify-center gap-1.5">
          {concepts.map((concept) => (
            <span key={concept} className="px-2.5 py-1 bg-[var(--color-sunflower)]/20 text-[var(--color-forest-dark)] rounded-full text-xs font-semibold border border-[var(--color-sunflower)]/30">
              {concept}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
