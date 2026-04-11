# Progressive Scene Image Delivery

**Date:** 2026-04-10
**Scope:** backend/image_gen.py, backend/turn_handling/synthesis.py

## Problem

During `collaborative_story` synthesis, the backend generates 3 scene images +
1 achievement image **sequentially** (for character consistency — each image
uses the previous as an anchor/reference so Gemini produces visually
consistent characters). The current code blocks on *all four* images inside
`_generate_structured_story()` before returning, so scene 1 only appears on
the frontend after scenes 2, 3, and the achievement image have all finished.

User-visible effect: the story loading widget stays up for the full
~20–30 seconds of image generation, then all three scenes pop in back-to-back
as the frontend auto-advances through them. There is no progressive reveal.

Expected behavior: scene 1 should be delivered as soon as its image is ready,
while scenes 2 and 3 continue generating in the background. The child reads /
listens to scene 1 narration, and by the time the frontend auto-advances,
scene 2's image is (usually) already done.

## Solution

Move scene image generation into a per-session background task that publishes
each result via an `asyncio.Future`. `_deliver_scene(n)` awaits only the
future for scene `n`, so scene 1 can ship the moment its future resolves even
while scenes 2 and 3 are still mid-generation.

The generation chain itself stays sequential — we cannot parallelize because
later scenes need earlier bytes as anchor/reference for character continuity.
What we change is **when the blocking await happens**: not upfront before any
delivery, but individually per scene at delivery time.

### Architecture

**`backend/image_gen.py`**
- New module-level `_scene_sessions: dict[str, _SceneSession]` keyed by
  `session_id`. Holds the list of futures plus a strong reference to the
  worker task so it doesn't get garbage-collected.
- New `start_scene_images(session_id, scene_descriptions, achievement_description)`:
  creates one future per scene + one for the achievement, spawns a background
  worker task, and returns the futures immediately.
- New `get_scene_futures(session_id)` lookup.
- New `clear_scene_session(session_id)` cleanup (called on session end /
  reset so finished sessions don't accumulate).
- The existing `generate_scene_images()` function becomes a thin wrapper that
  starts the session and awaits all futures, preserving its current callers
  (tests, `_generate_comparison_reveal` which only has 1 scene + achievement
  so progressive delivery doesn't matter there).

**`backend/turn_handling/synthesis.py`**
- `_generate_structured_story()`: replace the blocking
  `await generate_scene_images(...)` with `start_scene_images(...)`. Return
  the story with `scene.image_data_url = None` for all scenes and
  `achievement_image_data_url = None`.
- `_deliver_scene()` becomes `async`. Before building the `TurnResponse`, it
  awaits the future for `scene_number - 1`, populates
  `scene.image_data_url`, and caches it on the structured story so subsequent
  re-deliveries of the same scene don't re-await.
- When `is_last` is True, `_deliver_scene()` additionally awaits the
  achievement future and sets `story.achievement_image_data_url` so the
  celebrate frame (built on next /api/turn) has the image available.
- Update the two call sites in `_resolve_synthesis_turn()` and
  `_generate_and_advance()` to `await _deliver_scene(...)`.

**`backend/server.py`**
- On session cleanup (reset / delete), call `clear_scene_session(session_id)`
  to free the futures dict entry. If no such cleanup exists, add it to
  whatever handler ends a session.

### Character consistency guarantee

Unchanged. The worker task still generates scenes sequentially, passing the
first successful image as the `anchor` and the immediately prior image as the
`reference`. Only the *delivery* is progressive, not the generation.

### Timeout / failure handling

- `_deliver_scene()` uses `asyncio.wait_for(future, timeout=120.0)` so a
  wedged generation cannot block the turn forever. On timeout, the scene is
  delivered with `image_data_url = None` and the existing fallback UI
  renders. 120s accommodates the worst observed 3-scene latency.
- The worker catches exceptions per scene and resolves the corresponding
  future with `None`, matching the existing behavior of
  `generate_scene_images()` where failed scenes become `None` in the list.
- If the session entry is missing (e.g., server restart mid-session), the
  deliver helper falls through with `image_data_url = None`.

## Implementation Steps

1. Add `_SceneSession` dataclass + registry + `start_scene_images()` +
   `get_scene_futures()` + `clear_scene_session()` in `image_gen.py`. Keep
   `generate_scene_images()` as a thin wrapper that uses the new primitives.
2. Update `_generate_structured_story()` in `synthesis.py` to call
   `start_scene_images()` instead of the blocking path. Leave scene/achievement
   URLs unset on the returned story.
3. Convert `_deliver_scene()` to async, adding the per-scene `wait_for` and
   the is_last achievement await. Update both call sites to `await` it.
4. Wire `clear_scene_session(session_id)` into the reset path in
   `backend/server.py` so sessions don't leak.
5. Run `uv run ruff check`, `uv run ruff format`, `uv run mypy`.
6. Manual verification: start a Cat5 dandelion session, complete collect
   phases, reach synthesis. Watch the device panel — scene 1 should appear
   ~5s after "Ooh, let me put it all together..." (roughly the latency of a
   single Imagen call), not ~20s (sum of all four).

## Out of scope

- Not touching comparison_reveal (single scene, no progressive benefit).
- Not changing the Gemini prompt / anchor / reference logic.
- Not changing the frontend — it already handles scenes one at a time.
