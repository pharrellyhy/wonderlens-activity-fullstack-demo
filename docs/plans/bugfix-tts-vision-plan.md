# Bugfix Plan: TTS Duplication/Looping + Vision Fallback

## Bugs

1. **TTS duplicate calls & looping** — `useSessionOrchestration.js` auto-speak effect re-triggers on every `messages` array change, causing duplicate and looping TTS requests
2. **Vision fallback ignores filename** — when Vision API fails (429), entity is "unknown" and defaults to `mood_changer_dog` even when the photo filename contains the entity name

## Fix 1: TTS duplicate/looping (frontend)

**File:** `frontend/src/hooks/useSessionOrchestration.js`

**Root cause:** The auto-speak `useEffect` (line 66-72) depends on `messages` array reference. Every state update that changes `messages` re-fires the effect, calling `speak()` again for the same AI message.

**Fix:** Add a `lastSpokenIndexRef` that tracks the index of the last AI message we spoke. Only call `speak()` if the current last AI message index is different from what we already spoke.

## Fix 2: Vision fallback uses filename hint (backend)

**File:** `backend/server.py`

**Root cause:** When vision returns `entity: "unknown"`, `match_scenario()` defaults to `mood_changer_dog`. The photo filename (e.g., `ladybug.jpg`) is available but not used as a fallback hint.

**Fix:** Pass the uploaded photo's filename to `match_scenario()` as a fallback. In `scenarios.py`, try matching the filename against entity keywords before falling back to default.
