export default function StoryLoading() {
  return (
    <div className="flex flex-col items-center justify-center gap-6 p-6 h-full select-none">
      {/* Animated storybook mascot — large */}
      <div className="relative" style={{ animation: 'gentle-float 3s ease-in-out infinite' }}>
        <svg width="120" height="120" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect x="12" y="20" width="56" height="44" rx="4" fill="var(--color-sunflower-light)" stroke="var(--color-sunflower)" strokeWidth="2" />
          <line x1="40" y1="20" x2="40" y2="64" stroke="var(--color-sunflower)" strokeWidth="2" />
          <line x1="18" y1="30" x2="36" y2="30" stroke="var(--color-forest)" strokeWidth="1.5" opacity="0.4" strokeLinecap="round" />
          <line x1="18" y1="37" x2="34" y2="37" stroke="var(--color-forest)" strokeWidth="1.5" opacity="0.3" strokeLinecap="round" />
          <line x1="18" y1="44" x2="32" y2="44" stroke="var(--color-forest)" strokeWidth="1.5" opacity="0.2" strokeLinecap="round" />
          <path d="M54 35 l2 4 4 1 -3 3 0.5 4 -3.5-2 -3.5 2 0.5-4 -3-3 4-1z" fill="var(--color-sunflower)" opacity="0.6" />
          <path d="M12 24 Q12 18 18 18 L62 18 Q68 18 68 24" stroke="var(--color-sunflower)" strokeWidth="2" fill="none" />
        </svg>

        <div className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-[var(--color-sunflower)]"
          style={{ animation: 'sparkle-large 2s ease-in-out infinite' }} />
        <div className="absolute -bottom-2 -left-3 w-3 h-3 rounded-full bg-[var(--color-teal)]"
          style={{ animation: 'sparkle-large 2s ease-in-out infinite 0.7s' }} />
        <div className="absolute top-0 -left-4 w-3.5 h-3.5 rounded-full bg-[var(--color-forest-light)]"
          style={{ animation: 'sparkle-large 2s ease-in-out infinite 1.3s' }} />
      </div>

      {/* Shimmer text — large with gradient glow sweeping left to right */}
      <div className="text-center">
        <p className="text-xl max-[380px]:text-lg font-display font-bold story-loading-shimmer">
          Creating your adventure
        </p>
        <p className="text-sm max-[380px]:text-xs text-gray-400 mt-2 animate-pulse">
          Bringing everything together...
        </p>
      </div>

      {/* Bouncing dots — larger */}
      <div className="flex gap-3 items-center">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="w-3 h-3 rounded-full bg-[var(--color-forest)]"
            style={{
              animation: 'typing-dot 1.4s ease-in-out infinite',
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>

      <style>{`
        .story-loading-shimmer {
          background: linear-gradient(
            90deg,
            var(--color-forest-dark) 0%,
            var(--color-forest-dark) 40%,
            var(--color-sunflower) 50%,
            var(--color-forest-dark) 60%,
            var(--color-forest-dark) 100%
          );
          background-size: 200% 100%;
          -webkit-background-clip: text;
          background-clip: text;
          -webkit-text-fill-color: transparent;
          animation: shimmer-sweep 2.5s ease-in-out infinite;
        }
        @keyframes shimmer-sweep {
          0% { background-position: 100% 0; }
          100% { background-position: -100% 0; }
        }
      `}</style>
    </div>
  );
}
