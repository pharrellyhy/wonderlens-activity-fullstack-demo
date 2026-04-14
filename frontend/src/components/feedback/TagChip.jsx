import { FEEDBACK_TAGS } from './tags.js';
import { TAG_STYLES } from './tagStyles.js';

const TAGS_BY_ID = Object.fromEntries(FEEDBACK_TAGS.map((t) => [t.id, t]));

export default function TagChip({ tagId }) {
  const tag = TAGS_BY_ID[tagId];
  if (!tag) return null;
  const styles = TAG_STYLES[tag.color] || TAG_STYLES.amber;
  return (
    <span
      className={[
        'px-2 py-0.5 rounded-full text-[11px] font-semibold border',
        styles.selected,
      ].join(' ')}
    >
      {tag.label}
    </span>
  );
}
