import ConceptMedallion from './ConceptMedallion';

export default function ConceptReveal({ title, concepts = [], animation }) {
  return (
    <div className={`flex flex-col items-center justify-center h-full w-full p-6 gap-8 bg-gradient-to-b from-[var(--color-sunflower-light)]/20 via-white/40 to-[var(--color-forest)]/5 ${animation === 'badge_reveal' ? 'animate-celebration-large' : ''}`}>
      {/* Title with flanking sparkle emojis */}
      <div className="flex items-center gap-3">
        <span className="text-3xl animate-sparkle-large" aria-hidden="true">✨</span>
        <h2 className="text-2xl max-[380px]:text-xl font-display font-bold text-[var(--color-forest-dark)] tracking-tight text-center">
          {title || 'Explorer'}
        </h2>
        <span className="text-3xl animate-sparkle-large" style={{ animationDelay: '0.6s' }} aria-hidden="true">
          ✨
        </span>
      </div>

      {/* Concept medallion row — flex-wrap so 4+ concepts wrap cleanly */}
      <div className="flex flex-wrap justify-center items-start gap-6 max-[380px]:gap-4">
        {concepts.map((concept, i) => (
          <ConceptMedallion key={concept} concept={concept} delayMs={i * 250} />
        ))}
      </div>
    </div>
  );
}
