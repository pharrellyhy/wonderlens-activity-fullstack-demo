export default function FallbackTrophy({ title }) {
  return (
    <div className="w-full h-full rounded-3xl bg-gradient-to-br from-[var(--color-sunflower-light)]/30 via-white/50 to-[var(--color-forest)]/10 flex flex-col items-center justify-center gap-5">
      <div className="relative">
        <div className="w-40 h-40 max-[380px]:w-32 max-[380px]:h-32 rounded-full bg-gradient-to-br from-[var(--color-sunflower)] via-[var(--color-sunflower-light)] to-[var(--color-forest)] shadow-xl flex items-center justify-center border-4 border-white/80">
          <div className="w-24 h-24 max-[380px]:w-20 max-[380px]:h-20 rounded-full bg-white/70 flex items-center justify-center">
            <span className="text-6xl max-[380px]:text-5xl">🏆</span>
          </div>
        </div>
        <div className="absolute -top-3 -right-3 w-6 h-6 rounded-full bg-[var(--color-sunflower)] animate-sparkle-large" />
        <div className="absolute -bottom-2 -left-3 w-5 h-5 rounded-full bg-[var(--color-forest-light)] animate-sparkle-large" style={{ animationDelay: '0.8s' }} />
        <div className="absolute top-0 -left-4 w-4 h-4 rounded-full bg-[var(--color-teal)] animate-sparkle-large" style={{ animationDelay: '1.4s' }} />
      </div>
      <p className="text-2xl max-[380px]:text-xl font-display font-bold text-[var(--color-forest-dark)]">
        {title || 'Explorer'}
      </p>
    </div>
  );
}
