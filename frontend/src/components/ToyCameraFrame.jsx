export default function ToyCameraFrame({ children }) {
  return (
    <div className="relative w-full h-full flex flex-col">
      {/* Camera body */}
      <div className="relative flex-1 bg-gradient-to-b from-[var(--color-forest)] to-[var(--color-forest-dark)] rounded-3xl p-1.5 shadow-lg overflow-hidden">
        {/* Top bar with decorative elements */}
        <div className="flex items-center justify-between px-3 py-1">
          {/* Viewfinder circle */}
          <div className="w-5 h-5 rounded-full bg-[var(--color-brown)] border-2 border-[var(--color-brown)]/50 shadow-inner flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-white/30" />
          </div>

          {/* WonderLens text */}
          <span className="text-[10px] font-bold text-white/70 tracking-widest uppercase font-display">
            WonderLens
          </span>

          {/* Shutter button */}
          <div className="w-6 h-6 rounded-full bg-[var(--color-sunflower)] border-2 border-[var(--color-sunflower-light)] shadow-md flex items-center justify-center">
            <div className="w-3 h-3 rounded-full bg-[var(--color-sunflower-light)]" />
          </div>
        </div>

        {/* Viewport — where content renders */}
        <div className="flex-1 bg-white rounded-2xl overflow-hidden mx-0.5 mb-0.5" style={{ minHeight: 0, height: 'calc(100% - 36px)' }}>
          {children}
        </div>
      </div>

      {/* Grip texture on right side */}
      <div className="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-16 flex flex-col gap-1 justify-center pr-0.5">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="w-1 h-1 rounded-full bg-[var(--color-forest-dark)]" />
        ))}
      </div>
    </div>
  );
}
