// Split from ModePill.jsx so the component file only exports components
// (react-refresh/only-export-components lint rule).

export const APP_MODE_KEY = 'wl-app-mode';
export const VALID_APP_MODES = ['dev', 'tester'];
export const MODE_HINT_DISMISSED_KEY = 'wl-mode-hint-dismissed';

export function readHintDismissed() {
  try {
    return localStorage.getItem(MODE_HINT_DISMISSED_KEY) === '1';
  } catch {
    return false;
  }
}

export function writeHintDismissed() {
  try {
    localStorage.setItem(MODE_HINT_DISMISSED_KEY, '1');
  } catch {
    // non-fatal
  }
}

export function readStoredAppMode() {
  try {
    const stored = localStorage.getItem(APP_MODE_KEY);
    if (stored && VALID_APP_MODES.includes(stored)) return stored;
  } catch {
    // storage disabled
  }
  return 'dev';
}

export function writeStoredAppMode(mode) {
  try {
    localStorage.setItem(APP_MODE_KEY, mode);
  } catch {
    // non-fatal
  }
}

// Precedence: ?mode=X query param (persisted) → localStorage → 'dev'.
export function getInitialAppMode() {
  try {
    const queryMode = new URLSearchParams(window.location.search).get('mode');
    if (queryMode && VALID_APP_MODES.includes(queryMode)) {
      writeStoredAppMode(queryMode);
      return queryMode;
    }
  } catch {
    // fall through
  }
  return readStoredAppMode();
}
