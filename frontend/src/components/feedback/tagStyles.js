// Shared Tailwind style map keyed by FEEDBACK_TAGS[i].color.
// Consumed by both FeedbackQuickFlag (toggleable chips) and
// FeedbackReviewScreen (read-only chips). Keep in sync with tags.js.
export const TAG_STYLES = {
  amber: {
    selected: 'bg-amber-400 text-amber-950 border-amber-500',
    idle: 'bg-transparent text-amber-700 border-amber-400 hover:bg-amber-50',
  },
  rose: {
    selected: 'bg-rose-400 text-rose-950 border-rose-500',
    idle: 'bg-transparent text-rose-700 border-rose-400 hover:bg-rose-50',
  },
  red: {
    selected: 'bg-red-500 text-white border-red-600',
    idle: 'bg-transparent text-red-700 border-red-400 hover:bg-red-50',
  },
  green: {
    selected: 'bg-green-500 text-white border-green-600',
    idle: 'bg-transparent text-green-700 border-green-500 hover:bg-green-50',
  },
};
