export default function StoryScene({ image_data_url, scene_number, animation }) {
  return (
    <div className={`relative flex flex-col items-center w-full h-full p-3 ${
      animation === 'appear' ? 'animate-fade-in' : ''
    }`}>
      {/* Scene image — fills the whole widget area. Progress dots live in
       * DeviceScreen's bottom indicator row so they stay visible even when
       * the image is tall (stage mode on celebrate/closing). Hover lifts
       * the image gently and deepens the shadow so children get
       * feedback when they mouse over; prefers-reduced-motion disables the
       * transition globally via index.css. */}
      <div className="flex-1 min-h-0 w-full flex items-center justify-center overflow-hidden">
        {image_data_url ? (
          <img
            src={image_data_url}
            alt={`Story scene ${scene_number}`}
            className="w-full h-full rounded-2xl shadow-lg object-contain animate-fade-in transition-transform duration-300 ease-out hover:scale-[1.03] hover:shadow-2xl"
          />
        ) : (
          <div className="w-full h-full rounded-2xl bg-gradient-to-br from-[var(--color-sunflower-light)]/20 to-[var(--color-forest)]/10 flex items-center justify-center">
            <p className="text-lg text-gray-400 font-display">Scene {scene_number}</p>
          </div>
        )}
      </div>
    </div>
  );
}
