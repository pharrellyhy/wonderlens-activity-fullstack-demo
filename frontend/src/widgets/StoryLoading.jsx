import BASE from '../utils/basePath';

export default function StoryLoading({ sessionState }) {
  const entity = sessionState?.entity_name || 'friend';

  return (
    <div className="flex flex-col items-center justify-center gap-4 p-4 h-full">
      <div className="animate-[bounce_3s_ease-in-out_infinite]">
        <div className="w-20 h-20 max-[380px]:w-16 max-[380px]:h-16 rounded-full overflow-hidden border-3 border-[var(--color-sunflower)]/40 shadow-lg">
          <img
            src={`${BASE}/icons/${entity}.png`}
            alt={entity}
            className="w-full h-full object-cover"
            onError={(e) => { e.target.style.display = 'none'; }}
          />
        </div>
      </div>

      <div className="text-center">
        <p className="text-sm font-display font-bold text-[var(--color-forest-dark)]">
          Creating your story
          <span className="animate-pulse">...</span>
        </p>
        <p className="text-xs text-gray-400 mt-1">This might take a moment</p>
      </div>

      <div className="flex gap-3">
        <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-sunflower)] animate-sparkle-large" />
        <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-forest)] animate-sparkle-large" style={{ animationDelay: '0.5s' }} />
        <div className="w-1.5 h-1.5 rounded-full bg-[var(--color-teal)] animate-sparkle-large" style={{ animationDelay: '1s' }} />
      </div>
    </div>
  );
}
