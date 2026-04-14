# Imagen Concurrency Limit (429 fix)

## Context

Cat5 sessions hit Vertex Imagen 429 errors most reliably on
`polka_dot_patrol` (and any other `comparison_reveal` format) because:

- `_scene_image_worker` fires scene images sequentially, then immediately
  fires the achievement image (`backend/image_gen.py:288-339`).
- `comparison_reveal` has `scene_count: 1`, so the worker does scene 1 →
  achievement back-to-back with zero spacing.
- `_get_client` (`backend/image_gen.py:65-78`) builds a singleton
  `genai.Client` with **no concurrency cap**. There is no semaphore,
  queue, or rate limiter anywhere in the image pipeline.
- `start_scene_images` is fire-and-forget
  (`backend/turn_handling/synthesis.py:391`), so multiple Cat5 sessions
  hitting synthesis in parallel produce overlapping background workers
  that all hammer the same client.
- Existing 429 handling: a 2-attempt retry with a flat 3-second sleep
  (`backend/image_gen.py:61-62, 166-172`). That recovers from a single
  burst but doesn't prevent the burst, and a single `_MAX_RETRIES = 2`
  means one retry then give up — easy to exhaust.

The 429s show up as missing achievement images (the gallery feedback
the user is debugging). Fixing this is one small change away.

## Approach

Add a **module-level `asyncio.Semaphore`** inside `image_gen.py` that
gates the actual Imagen API call. Every caller of `generate_image()`
will acquire it before invoking the client, including:

- intra-session bursts (scene 1 → achievement on `comparison_reveal`)
- cross-session races (two sessions reaching synthesis at once)

Concurrency limit: **1**. Imagen's per-project burst limit is the bottleneck
— allowing more than one in flight at a time on a small project just
re-introduces the race. If we ever scale beyond a single-tenant demo we
can lift this from config.

## Changes

### `backend/image_gen.py`

1. Add a module-level `_imagen_semaphore = asyncio.Semaphore(1)` near the
   other module constants (around line 62, next to `_MAX_RETRIES`).
2. Inside `generate_image()`, wrap **only the API call + 429 retry loop**
   in `async with _imagen_semaphore:`. Prompt assembly (style prefix,
   caption building, contents list) stays outside the lock — it's pure
   CPU work and shouldn't block other callers.
3. Optional micro-improvement: log when a caller waits >100 ms for the
   semaphore so we can see contention in the logs.

### `backend/tests/test_image_gen_concurrency.py` (new)

A single focused test that proves the semaphore serializes calls:

- Patch `genai.Client` (or the `_get_client` cache) so `client.models.generate_content`
  sleeps 200 ms then returns a stub response.
- Set `imagen_enabled=True` and patch `_extract_image_bytes` to return
  fake bytes.
- Fire two `generate_image()` calls via `asyncio.gather()`.
- Assert total wall-clock time ≥ 400 ms (would be ~200 ms without the
  semaphore).

Out of scope for this test: actual Imagen contract, latency budgets, or
retry behaviour — all already implicitly covered by other backend tests
and manual runs.

## Out of Scope

- Tuning `_MAX_RETRIES` / `_RETRY_DELAY` (separate cleanup, not the bug).
- The hardcoded `aspect_ratio="16:9"` for achievement that ignores
  `achievement_aspect_ratio` from the format YAML — orthogonal bug,
  flagged separately.
- Per-session vs global semaphore granularity. Global is right for a
  single-tenant demo.
- Making the limit configurable via `config.yaml`. Defer until we have a
  reason to tune it.
- Anything in `start_scene_images`, the worker loop, or
  `turn_handling/synthesis.py`. The fix lives entirely in
  `generate_image()`.

## Critical Files

- `backend/image_gen.py:61-178` — semaphore declaration + wrapping the
  API-call branch of `generate_image`.
- `backend/tests/test_image_gen_concurrency.py` — new file.

## Verification

```bash
cd backend
uv run ruff check image_gen.py tests/test_image_gen_concurrency.py
uv run ruff format image_gen.py tests/test_image_gen_concurrency.py
uv run pytest tests/test_image_gen_concurrency.py -v
uv run pytest tests/ -q       # ensure nothing else regressed
```

Manual sanity: kick off a polka_dot_patrol session, watch backend logs
for `Imagen generated image` lines — they should now appear strictly
sequentially, not concurrently, even across sessions.
