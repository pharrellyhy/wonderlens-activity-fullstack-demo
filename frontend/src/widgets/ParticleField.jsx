import { memo, useMemo } from 'react';

/**
 * CSS-only emoji particle overlay that reacts to character animation state.
 * Renders absolutely-positioned emoji spans with state-driven CSS animations.
 */
const ParticleField = memo(function ParticleField({ animationState, particles }) {
  // Generate stable particle positions on mount (deterministic from particle config).
  // `useMemo` must run unconditionally before any early return to satisfy
  // React's rules-of-hooks.
  const items = useMemo(() => {
    if (!particles || particles.length === 0) return [];
    const totalCount = particles.reduce((s, p) => s + p.count, 0);
    const result = [];
    for (const { emoji, count, baseSize } of particles) {
      for (let i = 0; i < count; i++) {
        // Distribute particles in a ring around the character viewport
        const angle = (result.length / totalCount) * 360;
        const radius = 35 + (result.length % 3) * 10; // 35-55% from center
        const x = 50 + radius * Math.cos((angle * Math.PI) / 180) * 0.5;
        const y = 50 + radius * Math.sin((angle * Math.PI) / 180) * 0.5;

        result.push({
          emoji,
          size: baseSize + (result.length % 2) * 2,
          left: `${Math.max(5, Math.min(95, x))}%`,
          top: `${Math.max(5, Math.min(95, y))}%`,
          delay: `${(result.length * 0.4).toFixed(1)}s`,
          duration: `${2.5 + (result.length % 3) * 0.5}s`,
        });
      }
    }
    return result;
  }, [particles]);

  if (items.length === 0) return null;

  const stateClass = `particle-${animationState || 'idle'}`;

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
      {items.map((item, i) => (
        <span
          key={i}
          className={stateClass}
          style={{
            position: 'absolute',
            left: item.left,
            top: item.top,
            fontSize: `${item.size}px`,
            animationDelay: item.delay,
            animationDuration: item.duration,
            willChange: 'transform, opacity',
          }}
        >
          {item.emoji}
        </span>
      ))}
    </div>
  );
});

export default ParticleField;
