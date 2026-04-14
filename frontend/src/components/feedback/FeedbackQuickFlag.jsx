import { useEffect, useMemo, useState } from 'react';
import { FEEDBACK_TAGS } from './tags.js';
import { TAG_STYLES } from './tagStyles.js';

export default function FeedbackQuickFlag({
  screenshotBlob,
  turnNumber,
  initialTags,
  initialQuickNote,
  isEditing = false,
  onSave,
  onCancel,
}) {
  const [selectedTags, setSelectedTags] = useState(() =>
    Array.isArray(initialTags) ? [...initialTags] : [],
  );
  const [quickNote, setQuickNote] = useState(() => initialQuickNote || '');

  const previewUrl = useMemo(
    () => (screenshotBlob ? URL.createObjectURL(screenshotBlob) : null),
    [screenshotBlob],
  );
  useEffect(() => {
    if (!previewUrl) return undefined;
    return () => URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  const canSave = selectedTags.length > 0 || quickNote.trim().length > 0;

  const toggleTag = (tagId) => {
    setSelectedTags((prev) =>
      prev.includes(tagId) ? prev.filter((t) => t !== tagId) : [...prev, tagId],
    );
  };

  const handleSave = () => {
    if (!canSave) return;
    onSave?.({ tags: selectedTags, quickNote: quickNote.trim() });
  };

  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onCancel?.();
      }
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [onCancel]);

  // Auto-dismiss when the tester interacts with anything outside the
  // feedback UI (e.g. types in the conversation panel, taps the device
  // screen). Any element under [data-feedback-overlay="true"] is treated
  // as "inside" the popover for this purpose.
  useEffect(() => {
    const isOutside = (target) =>
      target instanceof Element && !target.closest('[data-feedback-overlay="true"]');

    const handlePointerDown = (e) => {
      if (isOutside(e.target)) onCancel?.();
    };
    const handleFocusIn = (e) => {
      if (isOutside(e.target)) onCancel?.();
    };

    document.addEventListener('mousedown', handlePointerDown, true);
    document.addEventListener('touchstart', handlePointerDown, true);
    document.addEventListener('focusin', handleFocusIn, true);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown, true);
      document.removeEventListener('touchstart', handlePointerDown, true);
      document.removeEventListener('focusin', handleFocusIn, true);
    };
  }, [onCancel]);

  const handleNoteKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (canSave) handleSave();
    }
  };

  return (
    <div
      data-feedback-overlay="true"
      role="dialog"
      aria-modal="false"
      aria-label={`Flag turn ${turnNumber}`}
      className="fixed z-[65] bottom-4 right-4 left-4 sm:left-auto sm:bottom-20 sm:right-4 sm:w-[340px] surface-card rounded-2xl shadow-xl p-4 animate-fade-in"
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-base font-semibold text-[var(--color-forest-dark)]">
          {isEditing ? `Edit flag for turn ${turnNumber}` : `Flag turn ${turnNumber}`}
        </h3>
        <button
          type="button"
          onClick={onCancel}
          aria-label="Close flag popover"
          className="w-7 h-7 rounded-full flex items-center justify-center text-[var(--color-forest-dark)]/60 hover:bg-black/5 cursor-pointer"
        >
          <span aria-hidden="true" className="text-lg leading-none">×</span>
        </button>
      </div>

      <div className="mb-3">
        {previewUrl ? (
          <img
            src={previewUrl}
            alt={`Screenshot of turn ${turnNumber}`}
            className="w-full h-[120px] object-cover rounded-lg border border-[var(--color-forest)]/20"
          />
        ) : (
          <div className="w-full h-[120px] rounded-lg border border-dashed border-[var(--color-forest)]/30 bg-black/5 flex items-center justify-center text-xs text-[var(--color-forest-dark)]/60">
            No preview
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2 mb-3">
        {FEEDBACK_TAGS.map((tag) => {
          const active = selectedTags.includes(tag.id);
          const styles = TAG_STYLES[tag.color] || TAG_STYLES.amber;
          return (
            <button
              key={tag.id}
              type="button"
              onClick={() => toggleTag(tag.id)}
              aria-pressed={active}
              className={[
                'px-3 py-1 rounded-full text-xs font-semibold border transition-all cursor-pointer',
                active ? styles.selected : styles.idle,
              ].join(' ')}
            >
              {tag.label}
            </button>
          );
        })}
      </div>

      <input
        type="text"
        aria-label="Quick note"
        value={quickNote}
        onChange={(e) => setQuickNote(e.target.value)}
        onKeyDown={handleNoteKeyDown}
        maxLength={60}
        placeholder="Short note (optional)"
        className="w-full px-3 py-2 rounded-lg border border-[var(--color-forest)]/30 bg-white text-sm text-[var(--color-forest-dark)] focus:outline-none focus:ring-2 focus:ring-[var(--color-forest)]/40 mb-3"
      />

      {!canSave && (
        <p className="text-[11px] text-[var(--color-forest-dark)]/60 mb-2">
          Select a tag or type a note
        </p>
      )}

      <div className="flex items-center justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-1.5 text-sm font-medium rounded-lg text-[var(--color-forest-dark)]/80 hover:bg-black/5 transition-colors cursor-pointer"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleSave}
          disabled={!canSave}
          className={[
            'px-4 py-1.5 text-sm font-semibold rounded-lg transition-all',
            canSave
              ? 'bg-[var(--color-forest)] text-white hover:bg-[var(--color-forest-dark)] cursor-pointer shadow-sm'
              : 'bg-[var(--color-forest)]/40 text-white cursor-not-allowed',
          ].join(' ')}
        >
          Save
        </button>
      </div>
    </div>
  );
}
