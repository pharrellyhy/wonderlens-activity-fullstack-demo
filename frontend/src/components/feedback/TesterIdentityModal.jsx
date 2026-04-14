import { useEffect, useRef, useState } from 'react';

export default function TesterIdentityModal({ onSubmit, onCancel }) {
  const [value, setValue] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

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

  const trimmed = value.trim();
  const canContinue = trimmed.length > 0;

  const handleContinue = () => {
    if (!canContinue) return;
    onSubmit?.(trimmed);
  };

  const handleSkip = () => {
    onSubmit?.('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleContinue();
    }
  };

  return (
    <div
      data-feedback-overlay="true"
      role="dialog"
      aria-modal="true"
      aria-label="Tester identity"
      className="fixed inset-0 z-[70] bg-black/40 flex items-center justify-center"
    >
      <div className="surface-card rounded-2xl p-6 w-[90%] max-w-sm">
        <h2 className="text-lg font-semibold text-[var(--color-forest-dark)] mb-1">
          Who's testing?
        </h2>
        <p className="text-sm text-[var(--color-forest-dark)]/70 mb-4">
          Your name is attached to flags you save this session.
        </p>
        <input
          ref={inputRef}
          type="text"
          maxLength={24}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Your name or alias"
          className="w-full px-3 py-2 rounded-lg border border-[var(--color-forest)]/30 bg-white text-sm text-[var(--color-forest-dark)] focus:outline-none focus:ring-2 focus:ring-[var(--color-forest)]/40"
        />
        <div className="mt-5 flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={handleSkip}
            className="px-4 py-2 text-sm font-medium rounded-lg text-[var(--color-forest-dark)]/80 hover:bg-black/5 transition-colors cursor-pointer"
          >
            Skip
          </button>
          <button
            type="button"
            onClick={handleContinue}
            disabled={!canContinue}
            className={[
              'px-4 py-2 text-sm font-semibold rounded-lg transition-all',
              canContinue
                ? 'bg-[var(--color-forest)] text-white hover:bg-[var(--color-forest-dark)] cursor-pointer shadow-sm'
                : 'bg-[var(--color-forest)]/40 text-white cursor-not-allowed',
            ].join(' ')}
          >
            Continue
          </button>
        </div>
      </div>
    </div>
  );
}
