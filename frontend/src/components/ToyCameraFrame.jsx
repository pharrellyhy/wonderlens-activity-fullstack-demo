export default function ToyCameraFrame({ children }) {
  return (
    <div className="relative w-full h-full flex flex-col">
      {/* Camera body */}
      <div className="relative flex-1 flex flex-col bg-gradient-to-b from-[var(--color-forest)] to-[var(--color-forest-dark)] rounded-3xl max-[380px]:rounded-[1.25rem] p-1.5 max-[380px]:p-1 shadow-lg overflow-hidden">
        {/* Top bar with decorative elements */}
        <div className="flex-shrink-0 flex items-center justify-between px-3 py-1 max-[380px]:px-2 max-[380px]:py-0.5">
          {/* Viewfinder circle */}
          <div className="w-4 h-4 sm:w-5 sm:h-5 max-[380px]:w-3.5 max-[380px]:h-3.5 rounded-full bg-[var(--color-brown)] border-2 border-[var(--color-brown)]/50 shadow-inner flex items-center justify-center">
            <div className="w-1.5 h-1.5 sm:w-2 sm:h-2 max-[380px]:w-1 max-[380px]:h-1 rounded-full bg-white/30" />
          </div>

          {/* WonderLens text */}
          <span className="text-[8px] sm:text-[10px] max-[380px]:text-[7px] font-bold text-white/70 tracking-widest uppercase font-display">
            WonderLens
          </span>

          {/* Shutter button */}
          <div className="w-5 h-5 sm:w-6 sm:h-6 max-[380px]:w-4.5 max-[380px]:h-4.5 rounded-full bg-[var(--color-sunflower)] border-2 border-[var(--color-sunflower-light)] shadow-md flex items-center justify-center">
            <div className="w-2.5 h-2.5 sm:w-3 sm:h-3 max-[380px]:w-2 max-[380px]:h-2 rounded-full bg-[var(--color-sunflower-light)]" />
          </div>
        </div>

        {/* Viewport — where content renders */}
        <div className="flex-1 min-h-0 bg-white rounded-2xl max-[380px]:rounded-[1rem] overflow-hidden overflow-y-auto mx-0.5 mb-0.5">
          {children}
        </div>
      </div>

      {/* Grip texture on right side */}
      <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-16 max-[380px]:h-12 flex flex-col gap-1 max-[380px]:gap-0.5 justify-center pr-0.5">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="w-1 h-1 max-[380px]:w-0.5 max-[380px]:h-0.5 rounded-full bg-[var(--color-forest-dark)]" />
        ))}
      </div>
    </div>
  );
}
