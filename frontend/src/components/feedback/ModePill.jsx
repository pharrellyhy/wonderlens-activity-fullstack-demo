import { useEffect, useState } from 'react';
import {
  APP_MODE_KEY,
  getInitialAppMode,
  readHintDismissed,
  readStoredAppMode,
  writeHintDismissed,
  writeStoredAppMode,
} from './appMode.js';

export default function ModePill({ onChange }) {
  const [mode, setMode] = useState(() => getInitialAppMode());
  const [hintDismissed, setHintDismissed] = useState(() => readHintDismissed());

  useEffect(() => {
    const handleStorage = (e) => {
      if (e.key === APP_MODE_KEY) setMode(readStoredAppMode());
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const dismissHint = () => {
    writeHintDismissed();
    setHintDismissed(true);
  };

  const flipMode = () => {
    setMode((prev) => {
      const next = prev === 'dev' ? 'tester' : 'dev';
      writeStoredAppMode(next);
      onChange?.(next);
      return next;
    });
  };

  const togglePill = () => {
    // Interacting with the pill counts as acknowledging the hint.
    if (!hintDismissed) dismissHint();
    flipMode();
  };

  const activateHint = () => {
    dismissHint();
    if (mode !== 'tester') flipMode();
  };

  const label = mode === 'tester' ? 'Tester' : 'Dev';
  const dotClass = mode === 'tester' ? 'bg-[var(--color-sunflower)]' : 'bg-[var(--color-teal)]';
  const showHint = mode === 'dev' && !hintDismissed;

  return (
    <div data-feedback-overlay="true" className="fixed top-3 right-3 z-[60] flex items-center gap-2">
      {showHint && (
        <div className="flex items-center rounded-full bg-amber-100/95 border border-amber-300 shadow-sm backdrop-blur-sm animate-fade-in">
          <button
            type="button"
            onClick={activateHint}
            className="pl-3 pr-1 py-1.5 text-[11px] font-medium text-amber-900 hover:text-amber-950 cursor-pointer"
          >
            Testing this flow? Switch to tester mode
          </button>
          <button
            type="button"
            onClick={dismissHint}
            aria-label="Dismiss tester mode hint"
            className="pr-2 pl-1 py-1.5 text-sm leading-none text-amber-700 hover:text-amber-900 cursor-pointer"
          >
            ×
          </button>
        </div>
      )}
      <button
        type="button"
        onClick={togglePill}
        aria-label="Toggle app mode"
        title={`Mode: ${label} (click to switch)`}
        className="h-8 px-3 rounded-full flex items-center gap-1.5 text-xs font-semibold bg-white/80 backdrop-blur-sm border border-[var(--color-forest)]/20 text-[var(--color-forest-dark)] shadow-sm hover:shadow-md hover:bg-white transition-all cursor-pointer"
      >
        <span aria-hidden="true" className={`inline-block w-2 h-2 rounded-full ${dotClass}`} />
        <span>{label}</span>
      </button>
    </div>
  );
}
