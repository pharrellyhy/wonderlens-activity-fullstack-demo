import FallbackTrophy from './FallbackTrophy';

export default function AchievementImage({ image_data_url, title, animation, entity }) {
  return (
    <div className={`relative flex flex-col h-full w-full p-4 ${animation === 'badge_reveal' ? 'animate-celebration-large' : ''}`}>
      {/* Role title — top, centered, generous */}
      <h2 className="text-2xl max-[380px]:text-xl font-bold font-display text-center text-[var(--color-forest-dark)] tracking-tight pb-3 shrink-0">
        {title || 'Explorer'}
      </h2>

      {/* Achievement image fills remaining space — object-contain respects aspect ratio */}
      <div className="flex-1 min-h-0 w-full flex items-center justify-center">
        {image_data_url ? (
          <img
            src={image_data_url}
            alt="Your adventure"
            className="max-w-full max-h-full rounded-3xl shadow-2xl object-contain animate-fade-in"
          />
        ) : (
          <FallbackTrophy entity={entity} />
        )}
      </div>
    </div>
  );
}
