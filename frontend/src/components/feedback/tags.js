// `id` values must stay in sync with backend schemas/feedback.py::FeedbackTag.
export const FEEDBACK_TAGS = [
  { id: 'tone',      label: 'Tone',      color: 'amber', description: 'Voice/wording feels off' },
  { id: 'confusing', label: 'Confusing', color: 'rose',  description: 'Child would be lost here' },
  { id: 'bug',       label: 'Bug',       color: 'red',   description: "Something's visibly broken" },
  { id: 'loved_it',  label: 'Loved it',  color: 'green', description: 'A great moment worth keeping' },
];

export const FEEDBACK_TAG_IDS = FEEDBACK_TAGS.map((t) => t.id);
