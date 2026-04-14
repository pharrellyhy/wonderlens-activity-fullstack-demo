import TagChip from './TagChip.jsx';
import { feedbackImageUrl } from '../../utils/api.js';

function formatRelativeTime(iso) {
  if (!iso) return '';
  const then = Date.parse(iso);
  if (Number.isNaN(then)) return '';
  const deltaSec = Math.max(0, Math.round((Date.now() - then) / 1000));
  if (deltaSec < 60) return 'just now';
  if (deltaSec < 3600) return `${Math.round(deltaSec / 60)}m ago`;
  if (deltaSec < 86400) return `${Math.round(deltaSec / 3600)}h ago`;
  const days = Math.round(deltaSec / 86400);
  if (days < 14) return `${days}d ago`;
  return new Date(then).toLocaleDateString();
}

export default function FeedbackGalleryCard({ entry, onImageClick }) {
  const flag = entry?.flag || {};
  const session = entry?.session || {};
  const activity = session.activity || {};
  const snapshot = flag.turn_snapshot || {};
  const screenshots = Array.isArray(flag.screenshots) ? flag.screenshots : [];
  const folderName = session.folder_name || '';

  const activityLabel = [activity.category, activity.template_type]
    .filter(Boolean)
    .join(' · ');

  return (
    <li className="surface-card rounded-2xl p-4 max-[380px]:p-3">
      <div className="flex items-start justify-between gap-3 flex-wrap mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-semibold text-[var(--color-forest-dark)]">
            Turn {flag.turn_number ?? '?'}
          </span>
          {(flag.tags || []).map((tagId) => (
            <TagChip key={tagId} tagId={tagId} />
          ))}
        </div>
        <div className="text-right">
          <div className="text-xs font-medium text-[var(--color-forest-dark)]/80">
            {session.tester_alias || 'anonymous'}
          </div>
          <div className="text-[11px] text-[var(--color-forest-dark)]/60">
            {formatRelativeTime(flag.flagged_at)}
          </div>
        </div>
      </div>

      {activityLabel ? (
        <div className="text-[11px] uppercase tracking-wide text-[var(--color-forest-dark)]/50 mb-2">
          {activityLabel}
        </div>
      ) : null}

      {flag.quick_note ? (
        <p className="text-sm font-semibold text-[var(--color-forest-dark)] mb-1">
          “{flag.quick_note}”
        </p>
      ) : null}

      {flag.review_comment ? (
        <p className="text-sm text-[var(--color-forest-dark)]/80 mb-2 whitespace-pre-wrap">
          {flag.review_comment}
        </p>
      ) : null}

      {(snapshot.speaker_text || snapshot.child_transcript) ? (
        <div className="mt-2 rounded-lg bg-black/5 px-3 py-2 text-xs text-[var(--color-forest-dark)]/80 space-y-1">
          {snapshot.speaker_text ? (
            <div>
              <span className="font-semibold">Spoken:</span>{' '}
              <span className="italic">{snapshot.speaker_text}</span>
            </div>
          ) : null}
          {snapshot.child_transcript ? (
            <div>
              <span className="font-semibold">Child:</span>{' '}
              <span className="italic">{snapshot.child_transcript}</span>
            </div>
          ) : null}
          {snapshot.widget_type ? (
            <div className="text-[11px] text-[var(--color-forest-dark)]/55">
              widget: {snapshot.widget_type}
              {typeof snapshot.recipe_round === 'number'
                ? ` · round ${snapshot.recipe_round}`
                : ''}
            </div>
          ) : null}
        </div>
      ) : null}

      {screenshots.length > 0 && folderName ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {screenshots.map((relative) => {
            const url = feedbackImageUrl(folderName, relative);
            return (
              <button
                type="button"
                key={relative}
                onClick={() => onImageClick?.(url, `Screenshot for turn ${flag.turn_number}`)}
                className="block rounded-lg overflow-hidden border border-black/10 hover:border-[var(--color-forest)] focus:outline-none focus:ring-2 focus:ring-[var(--color-forest)]/40 cursor-zoom-in"
                aria-label="Open screenshot"
              >
                <img
                  src={url}
                  alt={`Screenshot for turn ${flag.turn_number}`}
                  className="w-24 h-24 object-cover"
                  loading="lazy"
                />
              </button>
            );
          })}
        </div>
      ) : null}
    </li>
  );
}
