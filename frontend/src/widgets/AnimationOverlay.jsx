const ANIMATION_CLASSES = {
  sparkle_highlight: 'animate-pulse',
  celebration_burst: 'animate-bounce',
  badge_reveal: 'animate-bounce-in',
  gentle_pulse: 'animate-pulse',
  scene_transition: 'animate-fade-in',
  appear: 'animate-fade-in',
  slot_fill_chime: 'animate-bounce',
  mission_complete_fanfare: 'animate-bounce',
  concept_reveal: 'animate-fade-in',
  connection_lines_draw: 'animate-pulse',
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
