import { useCallback, useEffect, useMemo, useState } from 'react';
import { FEEDBACK_TAGS } from './tags.js';
import { TAG_STYLES } from './tagStyles.js';
import {
  buildFolderNameClient,
  downloadFeedbackZip,
  submitFeedbackToBackend,
} from '../../utils/submitFeedback.js';

const TAGS_BY_ID = Object.fromEntries(FEEDBACK_TAGS.map((t) => [t.id, t]));

function TagChip({ tagId }) {
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

export default function FeedbackReviewScreen({
  isOpen,
  flags,
  sessionId,
  testerAlias,
  activity,
  sessionStartedAt,
  appMode,
  buildPayload,
  onUpdateFlag,
  onDeleteFlag,
  onClose,
  onClearSession,
  onNewSession,
}) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitComplete, setSubmitComplete] = useState(null);

  // Build one object URL per flag screenshot. Use useMemo (not setState in
  // effect) because the repo's lint rules forbid that pattern.
  const thumbnailUrls = useMemo(() => {
    const map = new Map();
    for (const flag of flags || []) {
      const first = (flag.screenshots || []).find((s) => s && s.blob);
      if (first) {
        map.set(flag.flag_id, URL.createObjectURL(first.blob));
      }
    }
    return map;
  }, [flags]);

  useEffect(() => {
    return () => {
      for (const url of thumbnailUrls.values()) {
        URL.revokeObjectURL(url);
      }
    };
  }, [thumbnailUrls]);

  useEffect(() => {
    if (!isOpen) return undefined;
    const handleKey = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose?.();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen, onClose]);

  const finishWithSuccess = useCallback(
    (kind) => {
      // Clear flag blobs from the store but keep the overlay open so the
      // tester sees an explicit thanks view instead of being dropped back
      // onto the photo picker (useful for deep-link testers who came from
      // the upstream app).
      onClearSession?.();
      setSubmitComplete(kind);
    },
    [onClearSession],
  );

  const getPayload = useCallback(() => {
    const endedAt = new Date();
    const payload = buildPayload?.({
      sessionId,
      appMode: appMode || 'tester',
      activity,
      sessionStartedAt,
      sessionEndedAt: endedAt.toISOString(),
    });
    return { payload, endedAt };
  }, [activity, appMode, buildPayload, sessionId, sessionStartedAt]);

  const handleSubmit = async () => {
    setSubmitError(null);
    setIsSubmitting(true);
    try {
      const { payload } = getPayload();
      if (!payload) throw new Error('No payload available');
      await submitFeedbackToBackend(payload);
      finishWithSuccess('submitted');
    } catch (err) {
      setSubmitError(err?.message || 'Submit failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownload = async () => {
    setSubmitError(null);
    setIsSubmitting(true);
    try {
      const { payload, endedAt } = getPayload();
      if (!payload) throw new Error('No payload available');
      const folderName = buildFolderNameClient(endedAt, testerAlias, sessionId);
      await downloadFeedbackZip({ ...payload, folderName });
      finishWithSuccess('downloaded');
    } catch (err) {
      setSubmitError(err?.message || 'Download failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNewSession = () => {
    setSubmitComplete(null);
    onNewSession?.();
    onClose?.();
  };

  const handleCloseTab = () => {
    setSubmitComplete(null);
    onClose?.();
  };

  if (!isOpen) return null;

  const hasFlags = (flags || []).length > 0;

  if (submitComplete) {
    const headline =
      submitComplete === 'downloaded' ? 'Feedback downloaded' : 'Feedback sent';
    const detail =
      submitComplete === 'downloaded'
        ? 'Hand the zip to a developer to reproduce the moments you flagged.'
        : 'Thanks — a developer will pick it up from the backend.';
    return (
      <div
        className="fixed inset-0 z-[68] bg-black/40 flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        aria-label="Feedback sent"
      >
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="mx-auto mb-4 w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="text-green-700" aria-hidden="true">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold text-[var(--color-forest-dark)] mb-1">
            {headline}
          </h2>
          <p className="text-sm text-[var(--color-forest-dark)]/70 mb-6">{detail}</p>
          <p className="text-xs text-[var(--color-forest-dark)]/60 mb-4">
            You can close this tab, or start another session to test more.
          </p>
          <div className="flex items-center justify-center gap-2">
            <button
              type="button"
              onClick={handleCloseTab}
              className="px-4 py-2 text-sm font-medium rounded-lg text-[var(--color-forest-dark)]/80 hover:bg-black/5 cursor-pointer"
            >
              Close
            </button>
            <button
              type="button"
              onClick={handleNewSession}
              className="px-4 py-2 text-sm font-semibold rounded-lg bg-[var(--color-forest)] text-white hover:bg-[var(--color-forest-dark)] shadow-sm cursor-pointer"
            >
              Start another session
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      data-feedback-overlay="true"
      className="fixed inset-0 z-[68] bg-black/40 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label="Review flags"
    >
      <div className="max-w-2xl w-full max-h-[90vh] overflow-y-auto bg-white rounded-2xl shadow-xl">
        <div className="sticky top-0 bg-white border-b border-black/5 px-6 py-4 flex items-start justify-between z-10">
          <div>
            <h2 className="text-lg font-semibold text-[var(--color-forest-dark)]">
              Review your flags
            </h2>
            <p className="text-xs text-[var(--color-forest-dark)]/70 mt-0.5">
              Add a longer comment, or delete a mis-tap.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close review screen"
            className="text-sm text-[var(--color-forest-dark)]/70 hover:text-[var(--color-forest-dark)] cursor-pointer"
          >
            × close
          </button>
        </div>

        <div className="px-6 py-4">
          {!hasFlags ? (
            <div className="py-10 text-center">
              <p className="text-sm text-[var(--color-forest-dark)]/80 mb-4">
                No flags this session. Thanks for playing!
              </p>
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-semibold rounded-lg bg-[var(--color-forest)] text-white hover:bg-[var(--color-forest-dark)] cursor-pointer"
              >
                Done
              </button>
            </div>
          ) : (
            <ul className="space-y-4">
              {flags.map((flag) => {
                const thumbUrl = thumbnailUrls.get(flag.flag_id);
                return (
                  <li
                    key={flag.flag_id}
                    className="border border-black/10 rounded-xl p-3 bg-white"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-semibold text-[var(--color-forest-dark)]">
                          Turn {flag.turn_number}
                        </span>
                        {(flag.tags || []).map((tagId) => (
                          <TagChip key={tagId} tagId={tagId} />
                        ))}
                      </div>
                      <button
                        type="button"
                        onClick={() => onDeleteFlag?.(flag.flag_id)}
                        aria-label={`Delete flag for turn ${flag.turn_number}`}
                        className="text-xs text-red-600 hover:text-red-800 cursor-pointer"
                      >
                        Delete
                      </button>
                    </div>

                    {thumbUrl ? (
                      <img
                        src={thumbUrl}
                        alt={`Screenshot of turn ${flag.turn_number}`}
                        className="w-full h-[140px] object-cover rounded-lg border border-black/10 mb-2"
                      />
                    ) : (
                      <div className="w-full h-[140px] rounded-lg border border-dashed border-black/15 bg-black/5 flex items-center justify-center text-xs text-[var(--color-forest-dark)]/60 mb-2">
                        No screenshot
                      </div>
                    )}

                    {flag.quick_note ? (
                      <p className="italic text-xs text-[var(--color-forest-dark)]/70 mb-2">
                        “{flag.quick_note}”
                      </p>
                    ) : null}

                    <textarea
                      value={flag.review_comment || ''}
                      onChange={(e) =>
                        onUpdateFlag?.(flag.flag_id, { review_comment: e.target.value })
                      }
                      maxLength={500}
                      rows={3}
                      placeholder="Why did this catch your eye? (optional)"
                      aria-label={`Review comment for turn ${flag.turn_number}`}
                      className="w-full px-3 py-2 rounded-lg border border-[var(--color-forest)]/30 bg-white text-sm text-[var(--color-forest-dark)] focus:outline-none focus:ring-2 focus:ring-[var(--color-forest)]/40"
                    />
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        {hasFlags ? (
          <div className="sticky bottom-0 bg-white border-t border-black/5 px-6 py-4">
            {submitError ? (
              <p className="text-xs text-red-600 mb-2" role="alert">
                {submitError}
              </p>
            ) : null}
            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={handleDownload}
                disabled={isSubmitting}
                className={[
                  'px-4 py-1.5 text-sm font-semibold rounded-lg border transition-all',
                  isSubmitting
                    ? 'border-black/10 text-[var(--color-forest-dark)]/40 cursor-not-allowed'
                    : 'border-[var(--color-forest)]/40 text-[var(--color-forest-dark)] hover:bg-black/5 cursor-pointer',
                ].join(' ')}
              >
                {isSubmitting ? 'Saving...' : 'Download .zip'}
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={isSubmitting}
                className={[
                  'px-4 py-1.5 text-sm font-semibold rounded-lg transition-all',
                  isSubmitting
                    ? 'bg-[var(--color-forest)]/40 text-white cursor-not-allowed'
                    : 'bg-[var(--color-forest)] text-white hover:bg-[var(--color-forest-dark)] cursor-pointer shadow-sm',
                ].join(' ')}
              >
                {isSubmitting ? 'Saving...' : 'Submit'}
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
