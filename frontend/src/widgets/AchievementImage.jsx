import FallbackTrophy from './FallbackTrophy';

export default function AchievementImage({ image_data_url, title, animation, entity }) {
  return (
    <div className={`relative flex flex-col h-full w-full p-4 ${animation === 'badge_reveal' ? 'animate-celebration-large' : ''}`}>
      {/* Role title — top, centered, generous */}
      <h2 className="text-2xl max-[380px]:text-xl font-bold font-display text-center text-[var(--color-forest-dark)] tracking-tight pb-3 shrink-0">
        {title || 'Explorer'}
      </h2>

      {/* Achievement image fills remaining space — object-contain respects
       * aspect ratio. Hover lifts the image gently and deepens the drop
       * shadow for a tactile feel matching the scene image; the global
       * prefers-reduced-motion rule in index.css disables the scale for
       * users who opt out of motion. */}
      <div className="flex-1 min-h-0 w-full flex items-center justify-center">
        {image_data_url ? (
          <img
            src={image_data_url}
            alt="Your adventure"
            className="max-w-full max-h-full rounded-3xl shadow-2xl object-contain animate-fade-in transition-transform duration-300 ease-out hover:scale-[1.03] hover:shadow-[0_25px_60px_-10px_rgba(76,175,80,0.35)]"
          />
        ) : (
          <FallbackTrophy entity={entity} />
        )}
      </div>
    </div>
  );
}
