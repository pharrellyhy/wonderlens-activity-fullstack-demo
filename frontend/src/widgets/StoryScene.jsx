export default function StoryScene({ image_data_url, scene_number, total_scenes, animation }) {
  return (
    <div className={`flex flex-col items-center gap-2 p-2 max-[380px]:p-1.5 h-full ${
      animation === 'appear' ? 'animate-fade-in' : ''
    }`}>
      <div className="flex items-center gap-1.5">
        {Array.from({ length: total_scenes }, (_, i) => (
          <div
            key={i}
            className={`w-2 h-2 rounded-full transition-colors duration-300 ${
              i + 1 <= scene_number
                ? 'bg-[var(--color-sunflower)]'
                : 'bg-gray-200'
            }`}
          />
        ))}
      </div>

      <div className="flex-1 min-h-0 w-full flex items-center justify-center">
        {image_data_url ? (
          <img
            src={image_data_url}
            alt={`Story scene ${scene_number}`}
            className="max-w-full max-h-full rounded-xl shadow-md border-2 border-[var(--color-sunflower)]/20 object-contain animate-fade-in"
          />
        ) : (
          <div className="w-full aspect-video rounded-xl bg-gradient-to-br from-[var(--color-sunflower-light)]/20 to-[var(--color-forest)]/10 flex items-center justify-center">
            <p className="text-sm text-gray-400">Scene {scene_number}</p>
          </div>
        )}
      </div>
    </div>
  );
}
