export default function StoryScene({ image_data_url, scene_number, total_scenes, animation }) {
  return (
    <div className={`relative flex flex-col items-center w-full h-full p-3 ${
      animation === 'appear' ? 'animate-fade-in' : ''
    }`}>
      {/* Scene image — contained within panel, no scroll */}
      <div className="flex-1 min-h-0 w-full flex items-center justify-center overflow-hidden">
        {image_data_url ? (
          <img
            src={image_data_url}
            alt={`Story scene ${scene_number}`}
            className="w-full h-full rounded-2xl shadow-lg object-contain animate-fade-in"
          />
        ) : (
          <div className="w-full h-full rounded-2xl bg-gradient-to-br from-[var(--color-sunflower-light)]/20 to-[var(--color-forest)]/10 flex items-center justify-center">
            <p className="text-lg text-gray-400 font-display">Scene {scene_number}</p>
          </div>
        )}
      </div>

      {/* Scene progress dots — below image */}
      <div className="flex justify-center gap-2.5 pt-2.5">
        {Array.from({ length: total_scenes }, (_, i) => (
          <div
            key={i}
            className={`w-3.5 h-3.5 rounded-full transition-colors duration-300 border-2 ${
              i + 1 <= scene_number
                ? 'bg-[var(--color-sunflower)] border-[var(--color-sunflower)]'
                : 'bg-gray-200 border-gray-300'
            }`}
          />
        ))}
      </div>
    </div>
  );
}
