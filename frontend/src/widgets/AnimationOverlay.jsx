const ANIMATION_CLASSES = {
  sparkle_highlight: 'animate-sparkle-large',
  celebration_burst: 'animate-celebration-large',
  badge_reveal: 'animate-celebration-large',
  gentle_pulse: 'animate-pulse',
  scene_transition: 'animate-fade-in',
  appear: 'animate-fade-in',
  slot_fill_chime: 'animate-bounce',
  mission_complete_fanfare: 'animate-celebration-large',
  concept_reveal: 'animate-slide-up-large',
  connection_lines_draw: 'animate-sparkle-large',
  card_slide_in: 'animate-slide-in',
};

export default function AnimationOverlay({ animation, children }) {
  const animClass = animation ? ANIMATION_CLASSES[animation] || '' : '';

  return (
    <div className={`transition-all duration-500 ${animClass}`}>
      {children}
    </div>
  );
}
