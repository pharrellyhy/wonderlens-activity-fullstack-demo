# Session Handoff

Last updated: 2026-05-27

---

## Standalone Activity Text Game

**Problem**: The exported WonderLens activity packet needed a standalone frontend game that matches the prototype device appearance, runs inside this repo's feature worktree, calls the existing demo backend, and supports typed input/output only for now. The previous runtime had Cat1 and Cat5 flows, but not the Cat3 guided-build flow needed by the exported activities.

**Solution**: Added a standalone `/?view=activities` React surface with an activity library, transcript, typed response form, and a WonderLens device companion. The device preserves the white/mint prototype proportions, includes the top-right scroll rocker, and uses committed static beat assets generated with Codex imagegen. Backend support now exposes the 12 authored activities, starts text sessions through the existing Script Agent path, and adds Cat3 flow support.

**Edits**:
- `backend/activity_catalog.py`, `backend/server.py` — added `GET /api/activities` and `POST /api/start-activity`.
- `backend/games/activity_*.md` — added 12 authored activity recipes from the export packet.
- `backend/schemas/creative_slots.py`, `backend/game_parser.py`, `backend/state_machine.py`, `backend/turn_handling/*`, `backend/agents/script_agent.py`, `backend/skills/step_instructions/cat3_*.md` — added Cat3 guided-build support.
- `backend/schemas/session_state.py`, `backend/recipe_loader.py`, `backend/turn_handling/collection.py` — added text interaction mode and Cat5 typed collection support.
- `frontend/src/activityGame/*`, `frontend/src/App.jsx`, `frontend/src/index.css`, `frontend/src/utils/api.js` — added the standalone activity UI, text-session hook, and prototype device frame.
- `frontend/public/activity-assets/` — added static activity icons and per-beat display assets with `activity-assets.manifest.json`.
- `docs/activity-authoring.md`, `docs/plans/2026-05-27-activity-text-game.md`, `docs/superpowers/specs/2026-05-27-activity-text-game-design.md` — documented the design and reuse workflow.

**NOT Changed**:
- The original photo-upload, STT, TTS, and full split-view demo remains reachable at `/`.
- The standalone activity game intentionally does not render mic, TTS, speech, camera, or photo-upload controls.
- Static display assets are committed files; runtime does not call an image generation API for them.

**Verification**:
- `uv run pytest backend/tests/test_activity_text_game_api.py backend/tests/test_activity_text_game_definitions.py backend/tests/test_activity_text_game_cat3.py backend/tests/test_activity_text_game_turns.py -q` — 8 passed.
- `npm test -- tests/activityAssets.test.js tests/useActivityTextSession.test.jsx tests/WonderLensDevice.test.jsx tests/ActivityGameApp.test.jsx` — 7 passed.
- `npm run build` — passed; Vite emitted the existing large chunk warning.
- Live backend started from the feature worktree while sourcing the original backend `.env` and Google credential JSON. `GET /api/activities`, Cat1 start, Cat3 start, Cat5 start, and a typed Cat3 `/api/turn` smoke call all returned `status: ok`.
- Browser verification at `http://127.0.0.1:5173/?view=activities` confirmed 12 activities, no forbidden voice/photo controls, no "concept" selection wording, visible text input, full device visibility at 1280x720, visible top-right scroll rocker, working scroll selection, working activity start, typed child message display, and no app console warnings/errors.

---

## Browser Opus STT Streaming

**Problem**: Browser STT used `MediaRecorder` but waited until recording stopped, then uploaded one blob to `POST /api/stt`. The portable Opus streaming plan called for explicit start metadata, ordered binary chunks over one WebSocket session, route selection by codec/container, and browser feature detection.

**Solution**: Added a browser-targeted STT WebSocket path. The frontend now prefers `MediaRecorder` Opus streaming to `WS /api/stt/stream`, sends the portable `start` JSON first, forwards binary chunks in capture order, and sends `stop` when the mic is released. The backend validates the start message, rejects binary-before-start and container mismatches, selects Opus/PCM routes from explicit metadata, and returns the final transcript after `stop` using the existing Gemini STT helper. The existing batch upload and browser Web Speech fallbacks remain in place.

**Edits**:
- `backend/stt_stream.py` — added protocol enums, Pydantic models, route selection, first-chunk signature validation, and frame-size limit.
- `backend/server.py` — added `WS /api/stt/stream` alongside the existing `POST /api/stt` fallback.
- `frontend/src/utils/opusSttStream.js` — added browser MIME feature detection, WebSocket URL construction, MediaRecorder chunk forwarding, server-message handling, and stop cleanup.
- `frontend/src/hooks/useSpeechRecognition.js` — wired speech input to prefer WebSocket Opus streaming, then batch upload, then browser speech.
- `docs/opus-stt-protocol.md`, `README.md`, `docs/plans/2026-05-08-portable-opus-stt-streaming.md` — documented the implemented browser protocol and status.
- `tests/test_stt_stream.py`, `frontend/tests/opusSttStream.test.js` — added focused backend and frontend regression tests.

**NOT Changed**:
- No Android or Linux client implementation.
- No true interim transcripts yet; current provider path returns the final transcript after `stop`.
- No server-side Opus-to-PCM transcoder; unsupported direct provider ingest still requires future work.

**Verification**:
- Red backend test first: `uv run pytest tests/test_stt_stream.py -q` failed because `stt_stream` did not exist.
- Red frontend test first: `npm run test -- opusSttStream.test.js` failed because `frontend/src/utils/opusSttStream.js` did not exist.
- Cleanup regression test first: `npm run test -- opusSttStream.test.js` failed because a server `error` left the recorder active.
- `uv run pytest tests/test_stt_stream.py tests/test_api.py::TestSTTEndpoint tests/test_backend_imports.py -q` — 11 passed.
- `uv run ruff check backend/stt_stream.py backend/server.py tests/test_stt_stream.py` — passed.
- `npm run test -- opusSttStream.test.js` — 4 passed.
- `npm run lint` — passed.
- `npm run build` — passed; Vite emitted the pre-existing large bundle warning.
- `git diff --check` — passed.

---

## DashScope Settings Rename

**Problem**: Runtime code and docs still used the older provider-prefixed setting names and their uppercase environment variants. The requested convention is `dashscope_api_key`, `dashscope_base_url`, `dashscope_model`, `dashscope_classifier_model` and `DASHSCOPE_*`.

**Solution**: Renamed the settings fields, config YAML keys, call sites, scripts, tests, and documentation references to the DashScope naming. Added a focused config regression test proving uppercase `DASHSCOPE_*` environment variables populate `Settings`.

**Edits**:
- `backend/config.py`, `backend/config.yaml`, `backend/.env.example` — renamed settings/config/env names.
- Backend call sites in `backend/agents/`, `backend/turn_handling/`, and `backend/vision.py` — updated to `settings.dashscope_*`.
- `scripts/run_eval.py` — updated fallback model endpoint settings.
- `tests/test_config.py` — added regression coverage for uppercase DashScope env vars.
- `README.md`, `docs/aigc-pipeline-reference.md`, and historical plan docs — updated references.

**NOT Changed**:
- Actual model defaults remain `qwen3.5-plus` and `qwen3.5-flash`.
- No local `.env` or credentials were edited.

**Verification**:
- Red test first: `uv run pytest tests/test_config.py -q` failed because `Settings` had no `dashscope_api_key`.
- `uv run pytest tests/test_config.py -q` — 1 passed.
- `uv run pytest tests/test_backend_imports.py -q` — 2 passed.
- `uv run ruff check backend/config.py backend/vision.py backend/agents/director.py backend/agents/planner.py backend/agents/script_agent.py backend/agents/turn_director.py backend/agents/visual_agent.py backend/turn_handling/generation.py backend/turn_handling/synthesis.py scripts/run_eval.py tests/test_config.py` — passed.
- Exact old-name and provider-word sweep — no matches.

---

## Achievement Failure Banner Reliability

**Problem**: The "Couldn't create this image" banner on the Cat5 celebration screen sometimes did not show even when the Imagen worker had clearly returned 429 / failed. Trace: when the worker eventually flips `_SceneSession.achievement_failed = True`, the only place that propagated that flag onto the cached `StructuredStory` was `backend/turn_handling/synthesis.py:561-568`, which awaits the achievement future once with a 30-second timeout on the **last scene turn**. Two failure modes leaked through that single check: (1) the worker fails *after* the 30 s wait expires (very common with `_MAX_RETRIES > 2` because the retry budget exceeds the wait window), and (2) the tester clicks Continue / manually advances past synthesis before the wait completes. In both cases `story.achievement_image_failed` stays `False`, the celebrate frame builder at `backend/state_machine.py:326-347` falls into the `else` branch and renders `image_status="pending"`, the frontend shows the fallback trophy, and the banner never appears.

**Solution**: Added a private `_backfill_achievement_failure(state)` helper in `backend/turn_handling/helpers.py` that re-checks the live `_SceneSession.achievement_failed` whenever a Cat5 `STEP_5_CELEBRATE` frame is about to be built. If the cached story has no achievement URL AND `achievement_image_failed` is still `False` AND the live session reports the worker has failed, the helper mutates the cached story to `True`. Called from `_get_screen_frame()` before delegating to `state_machine.get_screen_frame()`, so any code path that lands on the celebrate screen now picks up the latest worker state instead of a possibly-stale cache. Failure is monotonic (False → True only), so the in-place mutation is safe across turns. Investigated the analogous gap for **scene** images (`synthesis.py:547-556`) and intentionally left it alone — scene turns auto-advance, the user never re-renders past scenes, and there's no celebrate-equivalent for them; the existing synchronous check inside `_deliver_scene` already covers the cases that have visible UX impact.

**Edits**:
- `backend/turn_handling/helpers.py` — added `from ..image_gen import get_scene_session` (and the matching fallback branch), added `_backfill_achievement_failure(state)` private helper, called it from `_get_screen_frame(state)` before delegating to `get_screen_frame`.
- `tests/test_state_machine.py` — added 3 regression tests under `test_celebrate_frame_*`: live session failed → frame surfaces `image_status='failed'` and mutates `structured.achievement_image_failed` to `True`; live session still in flight → frame stays `pending` and cache stays `False`; cached story already has a URL → live failure does NOT clobber the success. Includes a `fresh_scene_session_registry` fixture that snapshots and restores the module-level `_scene_sessions` dict in a `try/finally` so a failing test can't leak state. `_make_scene_session()` builds an `_SceneSession` with a placeholder `Future` (the backfill only reads `achievement_failed`, never awaits the future).
- `backend/image_gen.py` — also captured an unrelated `imagen_model` config alignment from the prior session (still pointed at `gemini-2.5-flash-image`).

**NOT Changed**:
- `synthesis.py:547-568` — the existing per-turn check for scene + achievement futures is unchanged. The new helper layers on top, doesn't replace it.
- `_deliver_scene` and the scene-image failure path — the same race technically exists but has zero user-visible impact (scenes auto-advance, no re-render). Documented as out of scope after investigation; would require either a behavior change to `_await_scene_image` or a new "missing scenes" recap UI to be worth fixing.
- The achievement image hardcoded `aspect_ratio="16:9"` at `backend/image_gen.py:324` — orthogonal bug, still flagged.
- Frontend `StoryScene.jsx` already had the `{failed && <ImageFailedBanner />}` wiring on `image_status === 'failed'`, so no frontend changes were needed even though we walked through it.

**Verification**:
```bash
cd backend
uv run ruff check turn_handling/helpers.py ../tests/test_state_machine.py    # pass
uv run ruff format turn_handling/helpers.py ../tests/test_state_machine.py   # 1 file reformatted
uv run pytest ../tests/test_state_machine.py -v                              # 29 passed (3 new)
uv run pytest ../tests/ -q --timeout=30 --ignore=../tests/test_ai_quality.py  # 508 passed, 1 pre-existing failure (test_device_screen_layout — unrelated)
```

**Manual repro plan** (the user should verify on prod once Imagen recovers):
1. Bump `_MAX_RETRIES` past `_RETRY_DELAY × 30 / 30` to force the worker to fail after the synthesis layer's 30 s wait expires (or trigger a sustained 429 by saturating the project quota).
2. Run a `polka_dot_patrol` session through synthesis to celebrate.
3. Confirm the celebrate screen renders the amber "Couldn't create this image" banner in the top-right of the achievement widget instead of staying stuck on the fallback trophy with no indicator.

**Post-implementation review**:
- `code-review-specialist` confirmed the guards are correct (no clobbering of a success URL, safe mutation of the Pydantic model, no circular-import risk between `helpers.py` and `image_gen.py`). Caught one MEDIUM: the `fresh_scene_session_registry` fixture wasn't using `try/finally`, so a teardown line raising could leave `_scene_sessions` polluted. Applied the fix. Also flagged that the backfill keys on `current_step == "STEP_5_CELEBRATE"` rather than "frame will render achievement_image" — accepted as out of scope since today's state machine has a single celebrate entry point.
- `code-simplifier` removed the unnecessary `asyncio.new_event_loop()` dance from `_make_scene_session` (the backfill never awaits the future, so the loop was pure overhead) and dropped the `Iterator` import that was only used for an annotation.

---

## Imagen Concurrency Limit (429 fix)

**Problem**: Cat5 sessions running `polka_dot_patrol` (and any other `comparison_reveal` synthesis format) hit Vertex Imagen 429 errors on the achievement image, leaving the celebration screen with a missing image. Root cause traced through `backend/image_gen.py:288-339`: `_scene_image_worker` generates scenes sequentially then immediately fires the achievement image. `comparison_reveal` has `scene_count: 1` (`backend/synthesis_formats/comparison_reveal.md:4`), so the worker fires scene 1 → achievement back-to-back with zero spacing. Worse, `_get_client` (`backend/image_gen.py:65-78`) builds a singleton `genai.Client` with no concurrency cap, no semaphore, no rate limiter. Cross-session races compound the problem because `start_scene_images` is fire-and-forget (`backend/turn_handling/synthesis.py:391`). Existing 429 handling is just a 2-attempt retry with a flat 3-second sleep, which recovers from a single burst but doesn't prevent the burst.

**Solution**: Added a module-level `asyncio.Semaphore(1)` in `backend/image_gen.py` that gates the actual Imagen API call inside `generate_image()`. Single-permit collapses both intra-session bursts (scene N → achievement on `comparison_reveal`) and cross-session races into a serial queue. The `async with` block wraps the API call + 429 retry loop so a 429 sleep also blocks other queued callers — no thundering-herd retry storm. Prompt assembly stays outside the lock (pure CPU work). Wait-time ≥ 100 ms emits an INFO log so contention is visible. Concurrency limit is intentionally `1` for this single-tenant demo; can be lifted via config later if needed.

**Edits**:
- `backend/image_gen.py` — added `_imagen_semaphore = asyncio.Semaphore(1)` next to existing module constants (line 69), wrapped the API-call + retry-loop branch of `generate_image()` in `async with _imagen_semaphore:` (lines 151-192), added a wait-time log line for visibility under contention.
- `backend/tests/test_image_gen_concurrency.py` (new) — `_FakeImagenClient` records `peak_in_flight` using a blocking `time.sleep(0.2)` inside `client.models.generate_content` (production code wraps it in `asyncio.to_thread`, so a real blocking sleep is the right tool for measuring serialization). `fake_client` fixture patches `_get_client`, `_extract_image_bytes`, the semaphore (via `monkeypatch.setattr` so cleanup is automatic), and `imagen_enabled`. Two tests: `test_concurrent_calls_are_serialized` proves two `gather`ed calls take >= 0.35s and never overlap; `test_single_call_does_not_block` proves a lone caller pays no penalty.
- `docs/plans/2026-04-14-imagen-concurrency-limit.md` (new) — design doc per the project's plan-before-code rule.

**NOT Changed**:
- `_MAX_RETRIES` / `_RETRY_DELAY` — out of scope; the bug is missing concurrency control, not bad backoff.
- The hardcoded `aspect_ratio="16:9"` for the achievement image at `backend/image_gen.py:324` (which ignores `achievement_aspect_ratio` from the format YAML) — orthogonal bug, flagged but not fixed in this change.
- `start_scene_images` / `_scene_image_worker` / anything in `backend/turn_handling/synthesis.py` — fix lives entirely in `generate_image()`.
- The pre-existing bare `except Exception` inside `generate_image`'s retry loop — flagged by reviewer as a CLAUDE.md violation, but it predates this work and changing it could silently change error semantics; left alone.

**Verification**:
```bash
cd backend
uv run ruff check image_gen.py tests/test_image_gen_concurrency.py   # pass
uv run ruff format image_gen.py tests/test_image_gen_concurrency.py  # 2 files left unchanged
uv run pytest tests/test_image_gen_concurrency.py -v                  # 2 passed
uv run pytest tests/ -q --timeout=30 --ignore=tests/test_ai_quality.py # 45 passed
```

**Post-implementation review**:
- `code-review-specialist` confirmed semaphore scope is correct (prompt assembly outside, retry loop inside so 429 sleeps block queued callers and prevent retry storms). Flagged the pre-existing bare `except Exception` as CLAUDE.md non-compliance — left alone since this diff didn't introduce it.
- `code-simplifier` inlined the `_SEMAPHORE_WAIT_LOG_MS = 100` constant (single-use), flattened `TestImagenSemaphore` class into module-level test functions, and removed a redundant teardown reset in the autouse fixture. Then I followed up: dropped `raising=False` on the `imagen_enabled` patch (it's a real Pydantic field, so a future rename should fail loudly), and switched the semaphore reset from autouse-rebind to `monkeypatch.setattr` so cleanup is automatic and bound-name leakage isn't possible.

---

## Feedback Gallery Panel (read-only)

**Problem**: Testers flag moments during a session and submit feedback via `POST /api/feedback`, which persists a JSON bundle + screenshots per session on disk. Nothing could browse the result — reviewers had to shell into `backend/feedback/` to read anything. The data was effectively write-only.

**Solution**: Added a read-only gallery, reachable from the landing page via `?view=feedback` (linked from a "View feedback gallery →" button on `PhotoSelector`). Backend gains two GET endpoints that walk the feedback directory, flatten flags across sessions, and serve screenshot bytes with strict path-traversal + symlink-escape guarding. Frontend renders a flat, filterable list (tag chip row + tester alias dropdown + newest/oldest sort toggle) with a fullscreen lightbox for thumbnails. No moderation surface — explicitly read-only to keep auth out of scope.

**Edits**:
- `backend/feedback_storage.py` — added `list_all_feedback(base_dir)` walking the feedback root, loading each `feedback.json`, and flattening each flag into `{flag, session}` enriched with `folder_name`; added `read_feedback_image(folder_name, relative_path, base_dir)` that resolves `bundle_root` and requires `bundle_root.is_relative_to(root)` before delegating to the existing `_resolve_safe` helper — catches both traversal and symlink-escape attacks; tightened `_is_safe_folder_name` to reject dotfile-prefixed names (`.git`, `.hidden`, `.`, `..`).
- `backend/server.py` — added `GET /api/feedback/list` (sorts by `flagged_at` desc) and `GET /api/feedback/image/{folder_name}/{relative_path:path}` (uses `mimetypes.guess_type`, returns 400 on unsafe path / 404 on missing); imports `list_all_feedback` and `read_feedback_image` in both try/except ImportError branches.
- `backend/tests/test_feedback_endpoint.py` — new `TestFeedbackListAndImage` class with 20 new assertions covering list flattening, malformed-bundle skipping, missing-root handling, image happy-path, path-traversal parametrized cases (including new `.git`/`.hidden` cases), **symlink-escape test** that plants a symlink to an outside tmp dir and asserts `ValueError`, and endpoint coverage for sort order + image serving + 404.
- `frontend/src/components/feedback/TagChip.jsx` — NEW shared component extracted from `FeedbackReviewScreen` so `FeedbackReviewScreen`, `FeedbackGalleryCard`, and any future card all use the same chip styling.
- `frontend/src/components/feedback/FeedbackReviewScreen.jsx` — replaced inline `TagChip` + `TAGS_BY_ID` with the shared import.
- `frontend/src/components/feedback/FeedbackGalleryPanel.jsx` — NEW: fetches `/api/feedback/list` once on mount (initial state `loading: true`, no setState-in-effect since the project's lint rule forbids it), renders filter bar (tag chips, tester dropdown, sort toggle) with `useMemo` for filtered/sorted entries, portals the lightbox via state, handles loading/error/empty states.
- `frontend/src/components/feedback/FeedbackGalleryCard.jsx` — NEW: flat card per flag — tag chips + turn number + tester alias + relative time + activity label + quick_note + review_comment + turn snapshot block + thumbnail row (each thumbnail is a button that opens the lightbox).
- `frontend/src/components/feedback/ScreenshotLightbox.jsx` — NEW: React portal into `document.body`, fullscreen dark backdrop, Escape-to-close, click-backdrop-to-close, centered image.
- `frontend/src/utils/api.js` — added `fetchFeedbackList()` and `feedbackImageUrl(folderName, relativePath)` (encodes each path segment).
- `frontend/src/App.jsx` — added `galleryView` state initialized from `?view=feedback`, unified `setGalleryViewWithUrl(on)` helper that mutates the URL via `history.pushState` and updates state, `popstate` listener, and an early-return render branch: `if (galleryView && !sessionId) return <FeedbackGalleryPanel onBack={closeGalleryView} />`.
- `frontend/src/components/PhotoSelector.jsx` — accepts an `onOpenGallery` prop and renders a "View feedback gallery →" link in the top-right of the panel header.
- `docs/plans/2026-04-14-feedback-gallery.md` — NEW design doc per the project's plan-before-code rule.

**NOT Changed**:
- `POST /api/feedback`, `FeedbackQuickFlag`, `FeedbackReviewScreen` submission flow — unchanged; gallery is purely additive.
- Schema (`backend/schemas/feedback.py`) — the list endpoint returns raw dicts (no `FeedbackListResponse` model) because the pipeline is already validated via the write path; adding a read-side schema was deferred.
- No pagination, delete, resolve, edit, or auth — explicitly out of scope per the brainstorming decisions.
- Pre-existing `# noqa: F401` comments on `get_demo_recipe` imports in `server.py` — left alone (CLAUDE.md forbids `noqa` but these predate this work).
- Pre-existing mypy "cannot perform relative import" error in `server.py` — unchanged by this work.

**Verification**:
```bash
# Backend
cd backend
uv run ruff check feedback_storage.py server.py tests/test_feedback_endpoint.py   # pass
uv run ruff format feedback_storage.py server.py tests/test_feedback_endpoint.py  # formatted
uv run pytest tests/test_feedback_endpoint.py -q                                   # 24 passed (4 pre-existing + 20 new)

# Frontend
cd ../frontend
npm run lint   # pass
npm run build  # pass

# End-to-end smoke test (playwright-mcp against backend-served dist)
# 1. Start backend on :8765, plant a fake 2-flag bundle in backend/feedback/
# 2. GET /api/feedback/list → returned both flags sorted newest first
# 3. GET /api/feedback/image/.../screenshots/turn-03.png → 200, image/png, 20 bytes
# 4. Navigate to /?view=feedback → gallery renders, "2 of 2 flags"
# 5. Click "Tone" chip → filter reduces to "1 of 2 flags", correct card shown
# 6. Click thumbnail → lightbox portal opens with backdrop + close button
# 7. Close lightbox → click "← Back to photos" → URL cleared, PhotoSelector shows link
# 8. Click "View feedback gallery →" → URL becomes /?view=feedback again
```

**Post-implementation review**:
- `code-review-specialist` sub-agent found a **HIGH-severity symlink escape** in `read_feedback_image` (passing an unresolved `bundle_root` to `_resolve_safe` let symlinks in the feedback dir widen the boundary to the symlink target). Fixed by resolving `bundle_root` and asserting `is_relative_to(root)` before touching files; added a symlink-escape regression test that plants a symlink to an out-of-tree `secret.png` and asserts `ValueError`.
- Reviewer also flagged dotfile folder names (`.git`, `.hidden`) passing the regex — fixed via `startswith(".")` rejection in `_is_safe_folder_name` + parametrized test cases.
- `code-simplifier` sub-agent trimmed a redundant `bundle_root.exists()` + `target.is_file()` double-check in `read_feedback_image`, collapsed `openGalleryView`/`closeGalleryView` in `App.jsx` into a single `setGalleryViewWithUrl(on)` helper, replaced the inline `_sort_key` function in `server.py` with a `lambda` on `entries.sort`, and removed a dead `|| ''` fallback in the panel's sort comparator.

---

## Synthesis Format Registry — Phases 3–6 (completed)

**Problem**: After Phase 2 landed `collaborative_story.md` alongside the legacy Python generators, the codebase still carried ~270 lines of dead code (`_generate_structured_story`, `_generate_comparison_reveal`, `_MIN_STORY_SENTENCES`), hardcoded `synthesis_format == "collaborative_story"` branches across `directive.py`, and a `Literal[...]` enum in `creative_slots.py` that blocked new formats from being added without a Python edit.

**Solution**: Completed phases 3–6 of `docs/plans/2026-04-10-synthesis-format-registry.md`. Phase 3 added `comparison_reveal.md`, deleted the legacy generators, and made `_generate_and_advance` fully format-agnostic. Phase 4 rewrote `_build_story_direction` to render `fmt.direction_template`, collapsed the fast-path invite/confirm branches, and replaced the detail-phase naming check with `fmt.is_naming_game`. Phase 5 dropped the `Literal` enum and added a pydantic `field_validator` on `StoryScaffold.synthesis_format` that calls `get_format()` to fail-fast at scaffold creation. Phase 6 proved the registry's purpose by adding `sorting_challenge.md` as a markdown-only new format — zero Python changes required.

**Edits**:
- `backend/synthesis_formats/comparison_reveal.md` — NEW: 1-scene format, `is_naming_game: false`, `confirm_goes_to: generate`, direction_template uses `{theme_angle_suffix}`/`{sorting_suffix}`/`{goal_suffix}`
- `backend/synthesis_formats/sorting_challenge.md` — NEW: 1-scene format, a third registered format added as Phase 6 proof; uses the existing template vocabulary unchanged
- `backend/turn_handling/synthesis.py` — Deleted `_generate_structured_story`, `_generate_comparison_reveal`, `_MIN_STORY_SENTENCES` (~270 lines removed); `_generate_and_advance` now always calls `_generate_structured_output(state, get_format(_resolve_format_id(state)))`; min_sentences fallback read from `fmt.min_sentences_total`; removed unused `generate_scene_images` and `StoryScene` imports; `_build_template_variables` `names` fallback changed from `""` to `"the friends"`
- `backend/turn_handling/directive.py` — `_build_story_direction` rewritten from 105 lines of inline f-strings to 14 lines that render `fmt.direction_template.format(**variables)`; fast-path confirm at STEP_4_SYNTHESIS uses `fmt.confirm_goes_to` to decide story-try routing; fast-path invite at STEP_4_SYNTHESIS renders `fmt.invite_direction.format(**variables)`; detail-phase `is_naming_game` reads from `fmt.is_naming_game`; added `get_format`, `_build_template_variables`, `_resolve_format_id` to top-of-file imports
- `backend/schemas/creative_slots.py` — `StoryScaffold.synthesis_format` changed from `Literal[...]` to `str` with `@field_validator` that calls `get_format()` to raise at scaffold creation on unknown ids
- `backend/tools/capture_synthesis_baselines.py` — Rewritten to render format templates directly via `_build_template_variables` instead of mocking `AsyncOpenAI`; goldens in `tests/fixtures/golden/` remain byte-identical
- `tests/test_synthesis_format_loader.py` — Added `TestRealRegistryLoadsComparisonReveal`, `TestRealRegistryLoadsSortingChallenge`, `TestStoryScaffoldValidatesFormat`
- `tests/test_format_rendering.py` — Added `_make_comparison_state` helper and `TestComparisonRevealDirectionMatchesGolden` (byte-for-byte match against `comparison_direction_T1.txt`)

**NOT Changed**:
- Golden files in `tests/fixtures/golden/` — unchanged across all 4 phases (capture script produces bit-identical output)
- `backend/games/*.md` — no game YAML edits required; existing `synthesis_format` references still resolve to the same ids
- ScriptAgent step instructions under `backend/skills/step_instructions/cat5_step4_synthesis__*.md` — deferred per plan decision
- Frontend — no changes; it already consumed `StructuredStory` generically

**Verification**:
```bash
# Full suite
uv run pytest tests/ --ignore=tests/test_ai_quality.py --deselect tests/test_device_screen_layout.py::test_device_screen_keeps_widget_area_centered_on_tall_viewports -q
# → 500 passed, 12 skipped (baseline 482; +18 new loader / rendering / validator tests)

# Goldens byte-identical after capture script runs
cd backend && uv run python tools/capture_synthesis_baselines.py
cd .. && git diff --stat tests/fixtures/golden/    # → empty

# Lint + format
cd backend && uv run ruff check . && uv run ruff format --check .    # → clean

# Success criteria greps
grep -rn "is_story_game" backend/    # → empty
grep -rn "synthesis_format ==" backend/    # → empty
```

---

## Phase 2: Migrate collaborative_story to data-driven format file

**Problem**: The `collaborative_story` synthesis format had its LLM prompts and direction template hardcoded as Python string literals in `synthesis.py` and `directive.py`. Any change to prompt wording required a code edit; the prompts were invisible to non-Python tooling; and there was no single source of truth linking the LLM parameters (temperature, max_tokens, scene_count) to the prompt body.

**Solution**: Extracted the collaborative_story format into `backend/synthesis_formats/collaborative_story.md` (YAML frontmatter + three body sections). Added `_build_template_variables`, `_resolve_format_id`, and `_generate_structured_output` to `synthesis.py`. Wired the story branch of `_generate_and_advance` to use the registry. Three golden-file diff tests assert byte-for-byte fidelity between the new template rendering and the pre-refactor baselines captured in Phase 0.

**Edits**:
- `backend/synthesis_formats/collaborative_story.md` — NEW: YAML frontmatter (scene_count, LLM params, tier constraints, invite templates) + `# system_prompt`, `# user_prompt`, `# direction_template` body sections; JSON `{` / `}` in user_prompt escaped as `{{` / `}}`; direction template uses `{theme_suffix}`, `{premise_line}`, `{child_story_line}` placeholders for optional segments
- `backend/turn_handling/synthesis.py` — Added `get_format` / `SynthesisFormat` imports (try/except pattern); added `_resolve_format_id`, `_build_template_variables`, `_generate_structured_output`; changed story branch of `_generate_and_advance` from `_generate_structured_story(state)` to `_generate_structured_output(state, get_format("collaborative_story"))`; fixed mislabeled `# obs_list` comment to `# obs_angle`; removed unnecessary "Build full characters string" comment
- `tests/test_format_rendering.py` — NEW: three golden-file diff tests (system_prompt, user_prompt, direction) using the same deterministic synthetic state as `capture_synthesis_baselines.py`
- `tests/test_synthesis_format_loader.py` — Added `TestRealRegistryLoadsCollaborativeStory` class exercising the real format file (not a mock)

**NOT Changed**:
- `_generate_structured_story` — preserved for Phase 3 cleanup
- `_build_story_direction` in `directive.py` — untouched; Phase 4 will refactor
- `_generate_comparison_reveal` — untouched; comparison branch still unchanged
- `_MIN_STORY_SENTENCES` — preserved; Phase 3 will delete it and read from fmt
- Golden files in `tests/fixtures/golden/` — unchanged (capture script verified zero diffs)

**Verification**:
```bash
# New and existing loader + rendering tests
uv run pytest tests/test_synthesis_format_loader.py tests/test_format_rendering.py -v
# → 13 passed

# Full suite
uv run pytest tests/ --ignore=tests/test_ai_quality.py --deselect tests/test_device_screen_layout.py::test_device_screen_keeps_widget_area_centered_on_tall_viewports -q
# → 495 passed, 12 skipped

# Lint
cd backend && uv run ruff check . && uv run ruff format --check .
# → All checks passed / 59 files already formatted

# Golden sanity
uv run python tools/capture_synthesis_baselines.py && git diff --stat tests/fixtures/golden/
# → 0 diffs
```

---

## Progressive Scene Delivery, In-Image Captions, Distinct Celebration + Turn Director Robustness

**Problem**: Three rounds of playtesting Cat5 synthesis surfaced compound issues. (1) The backend blocked on all 3 scene images plus the achievement image before delivering scene 1 to the frontend, so the child watched the loading widget for ~20s even though each scene only takes ~5s. (2) The generated achievement image was visually indistinguishable from scene 3 because the LLM kept producing "characters together in a warm scene" as the achievement description — which is exactly what scene 3 already is. (3) Generated images had no text, while storybook pages traditionally carry a short caption. (4) TurnDirective parsing hard-failed when the LLM returned `screen_widget` as a structured dict `{type: ..., options: [...]}` instead of a plain string, dropping the whole turn into fallback handling. (5) On the last Cat5 collection round the Turn Director wrote a 4-part directive ("celebrate + introduce crew + mark last find + tease story") but forgot to raise `max_sentences`, so the Speaker respected the schema default of 2 and dropped the story-tease half. (6) Device panel rendered-image widgets had no hover feedback; progress dots drifted off-center when label/SFX indicator widths were uneven; ConceptReveal's "You are now a X!" line duplicated the H2 title; and `index.css` still had leftover `!important` stage-mode overrides from before the inline-style fix landed.

**Solution**: Three focused commits:
- `feat(synthesis)`: per-session `_SceneSession` background worker in `image_gen.py` publishes each finished image to its own `asyncio.Future`; `_deliver_scene` awaits only the future for the scene it's shipping via `asyncio.wait_for(asyncio.shield(future), timeout=30s)` so scene 1 ships the moment it's ready. Last-scene delivery also awaits the achievement future so the celebrate frame has the URL. Only non-None results are cached onto `scene.image_data_url` so a timed-out wait doesn't poison retries. Added `_build_achievement_prompt` in `synthesis.py` that returns a deterministic celebration-poster template with rotating props (confetti / crowns / banners / spotlight / petals / campfire) — character names are interpolated so the portrait matches the story but the composition is locked to a centered hero shot. Removed "no text" from `_STYLE_PREFIX`; `generate_image` now accepts an optional `caption` that gets threaded through the worker and baked into the image via plain string concat (not `str.format` — LLM-produced braces would KeyError). Schema: `StructuredStory.achievement_description` is now optional (default `""`) since the prompt no longer asks for it.
- `feat(ui)`: `StoryScene`, `AchievementImage`, and `PhotoDisplay` get `transition-transform duration-300 ease-out hover:scale-[1.03]` + a deeper shadow. Global `prefers-reduced-motion` rule already disables the transform for opt-outs. Progress dots moved to `absolute left-1/2 -translate-x-1/2` inside a `relative` parent. ConceptReveal drops the redundant role-line. `index.css` stage-mode `!important` overrides removed now that App.jsx owns device-panel sizing via inline style.
- `fix(turn-director)`: `TurnDirective` gains a `model_validator(mode="before")` that peels `type` / `widget` / `name` out of a dict `screen_widget` and merges the remainder into `screen_widget_params` (caller-provided params still win). Turn Director system prompt tightened with CORRECT/WRONG examples. `_CAT5_COLLECTION_RULES` detail-phase advance split into "NOT the last round" (`max_sentences=2`, lean celebrate) and "IS the last round" (`max_sentences=4`, explicit 4-sentence structure: celebrate → name crew → mark last find → tease story).

**Edits**:
- `backend/image_gen.py` — new `_SceneSession` dataclass, `_scene_sessions` registry, `start_scene_images()`, `get_scene_session()`, `clear_scene_session()`, `_scene_image_worker()`, `_process_generated_image()` helper; `generate_image` accepts optional `caption` param; `_STYLE_PREFIX` no longer bans text; brace-safe string-concat prompt assembly with `_CAPTION_PREFIX` / `_CAPTION_SUFFIX`
- `backend/turn_handling/synthesis.py` — `_generate_structured_story` kicks off background delivery and returns story immediately with image URLs unset; `_deliver_scene` is now async, awaits per-scene future, and pulls the achievement future forward on `is_last`; new `_build_achievement_prompt`, `_CELEBRATION_PROPS` / `_CELEBRATION_CAPTIONS` palettes, `_role_title_for` helper, and `_condense_caption` utility; LLM prompts ask for a per-scene `caption` instead of `achievement_description`
- `backend/turn_handling/core.py` — updated `_deliver_scene` call site to `await`
- `backend/schemas/structured_story.py` — `caption` field on `StoryScene`, `achievement_caption` field on `StructuredStory`, `achievement_description` now optional with default `""`
- `backend/schemas/turn_directive.py` — new `_normalize_screen_widget` model validator coerces dict → name + params split
- `backend/skills/turn_director_system.md` — explicit `screen_widget` MUST-be-string note with CORRECT/WRONG JSON examples
- `backend/agents/turn_director.py` — `_CAT5_COLLECTION_RULES` detail-advance split into NOT-last-round vs IS-last-round with explicit `max_sentences`
- `frontend/src/components/DeviceScreen.jsx` — progress dots absolutely positioned for true panel-center alignment
- `frontend/src/index.css` — removed `!important` stage-mode overrides; updated comment explaining the inline-style approach
- `frontend/src/widgets/StoryScene.jsx`, `AchievementImage.jsx`, `PhotoDisplay.jsx` — hover scale + deeper shadow on the image element
- `frontend/src/widgets/ConceptReveal.jsx` — dropped redundant "You are now a {role}!" paragraph
- `docs/plans/2026-04-10-celebration-bugfixes-and-consistency.md`, `docs/plans/2026-04-10-progressive-scene-image-delivery.md`, `docs/plans/2026-04-11-hover-caption-distinct-celebration.md` — plan docs

**NOT Changed**:
- Gemini 2.5 Flash Image model selection, anchor/reference character-consistency chain, JPEG downscale pipeline — all preserved
- Blocking `generate_scene_images()` wrapper — still used by `_generate_comparison_reveal` (1 scene, no progressive benefit)
- `prefers-reduced-motion` handling — already present in `index.css`, unchanged
- Cat1 rules, Cat1 Round rules, Synthesis / Celebrate / Closing rules — unchanged; fix was scoped to Cat5 collection only
- Tests and pytest suite — no new tests added (all verification was manual + focused import smoke tests)

**Verification**:
- `cd backend && uv run ruff check . && uv run ruff format --check .` — clean on all changed files
- Import smoke tests: progressive delivery, caption threading, brace-escape, `_build_achievement_prompt`, `_condense_caption` edge cases, `TurnDirective` dict / string / default / alias / merge all pass
- `cd frontend && npx vite build` — clean (85 modules)
- LLM regression test: the exact failing `TurnDirective` payload from the playtest log now parses correctly with `screen_widget="binary_choice"`, `screen_widget_params={"options": [...]}`

---

## Scene-by-Scene Story Images + Achievement Image

**Problem**: Cat5 story synthesis delivered a single monolithic text story with no visual accompaniment. The story felt disconnected from the collection experience — no illustrations, no scene-by-scene pacing, and the celebrate step used a generic explorer map instead of showing the characters together.

**Solution**: Added Imagen 3 watercolor illustration generation (3 scene images + 1 achievement image) to the Cat5 synthesis flow. Stories are now structured as 3 scenes delivered turn-by-turn with auto-advance, each with a narration + generated illustration. The celebrate step shows a generated achievement image of all characters together. Graceful fallback: if structured generation or Imagen fails, the monolithic story path is preserved.

**Edits**:
- `backend/image_gen.py` — NEW: Imagen 3 module with dual-auth (Vertex AI / API key), parallel generation, base64 data URL output, retry on rate-limit
- `backend/config.py` — Added `imagen_model` and `imagen_enabled` settings
- `backend/.env.example` — Added Imagen 3 comment block
- `backend/schemas/structured_story.py` — NEW: `StoryScene` and `StructuredStory` Pydantic models
- `backend/schemas/__init__.py` — Exported new schemas
- `backend/schemas/session_state.py` — Added `structured_story` and `current_scene` fields
- `backend/skills/step_instructions/cat5_step4_synthesis__story_generation.md` — Restructured from monolithic prose to 3-scene JSON output with image descriptions
- `backend/turn_handling/synthesis.py` — Added `_generate_structured_story()` (LLM → JSON parse → parallel Imagen), `_deliver_scene()` (deterministic auto-advance), modified `_generate_and_advance()` with structured-first fallback
- `backend/turn_handling/helpers.py` — Added `structured_story` to `_state_context`
- `backend/state_machine.py` — Added Cat5 celebrate step achievement_image widget override before explorer map return
- `backend/skills/step_instructions/cat5_step5_celebrate.md` — Updated widget reference to achievement_image
- `frontend/src/widgets/StoryScene.jsx` — NEW: Scene progress dots + watercolor illustration
- `frontend/src/widgets/StoryLoading.jsx` — NEW: Animated loading state during generation
- `frontend/src/widgets/AchievementImage.jsx` — NEW: Achievement illustration with character names + IB concepts
- `frontend/src/components/DeviceScreen.jsx` — Registered 3 new widgets in WIDGET_MAP + getFrameKey

**NOT Changed**:
- Existing monolithic story path (fully preserved as fallback)
- Cat1 activities (no scene images)
- Turn Director, intent classification, state machine transitions
- Frontend conversation flow, TTS/STT pipeline
- Agent pipeline (Director → Script → Visual → Assembler)

**Verification**:
- `uv run ruff check . && uv run ruff format --check .` — PASS
- `uv run pytest -x -q --ignore=tests/test_ai_quality.py` — 36 passed (2 pre-existing failures excluded: `test_muted_tts_path_does_not_play_outros_twice`, `test_device_screen_keeps_widget_area_centered_on_tall_viewports`)
- `npx vite build` — clean (82 modules)

---

## Edu Team Content Feedback (5 Issues)

**Problem**: Edu team reviewed demo sessions (feedback in `edu_team_feedback_0406.txt`) and identified five content quality issues: (1) narrow answer acceptance treating creative responses as wrong, (2) directive language in templates, (3) story activities lacking follow-through after naming, (4) scavenger hunt instructions too complex for T0, (5) closing summaries too long with no visual recall.

**Solution**: Created content design principles doc (`P1-P5`), then systematically applied across Turn Director rules, step instructions, game definitions, tier rules, and frontend. Approach B from spec — shared principles + systematic pass, no architecture changes.

**Edits**:
- `backend/skills/content_design_rules.md` — NEW: 5 content design principles (accept creative answers, invitational framing, concrete before abstract, story continuity, show don't summarize)
- `backend/agents/turn_director.py` — Split `wrong/unexpected` into `unexpected-but-on-topic` (advance) and `off-topic` (stay) in both `_CAT1_ROUND_RULES_VOICE_ACTING` and `_CAT1_ROUND_RULES_STORYTELLING`
- `backend/skills/turn_director_system.md` — Added `## Answer Acceptance` section
- `backend/agents/script_agent.py:644` — Reframed `acceptable_themes` label to "Theme examples (for inspiration — any on-topic answer is valid)"
- `backend/skills/step_instructions/cat1_step3_round.md` — Renamed "Wrong/unexpected" to "Off-topic", expanded "Good/creative" to include unexpected-but-on-topic
- `backend/tier_rules.yaml` — Expanded `forbidden_directives` in all 3 tiers with `Touch.../Describe.../Show me.../Try to.../Find...`
- `backend/games/fluffy_expedition_dandelion.md` — Rewrote `detail_question_template` to invitational; dropped "Find" from `collection_criterion`
- 8 more game `.md` files — Dropped "Find" imperative from `collection_criterion`
- `backend/skills/step_instructions/cat5_step3_collect.md` — Added story bridge to last-round rule 6; added T0 entity anchoring + stuck scaffolding sub-rules to rule 2
- `backend/skills/step_instructions/cat5_step4_synthesis.md` — Reworked INVITE phase: T0 gets story starter, T1/T2 gets character bridge
- `backend/skills/step_instructions/cat5_step5_celebrate.md` — Changed screen widget to `photo_recall_grid`
- `backend/skills/step_instructions/cat5_step6_closing.md` — Full rewrite with tier-specific density limits (T0: 2 elements/20 words, T1: 3/35, T2: 4/50)
- `frontend/src/widgets/PhotoRecallGrid.jsx` — NEW: Photo grid with character name labels for celebrate/closing steps
- `frontend/src/components/DeviceScreen.jsx` — Registered `photo_recall_grid` widget

**NOT Changed**:
- Turn Director architecture (LLM pipeline, TurnDirective schema, state machine)
- `acceptable_themes` field name in schema (only prompt label changed)
- Scoring/evaluation (follows separately)
- Frontend conversation flow, TTS/STT
- `backend/turn_handling/` package

**Verification**:
- `uv run ruff check agents/script_agent.py agents/turn_director.py` — PASS
- `uv run pytest -x -q --ignore=tests/test_ai_quality.py` — 19 passed
- `npx vite build` — clean (79 modules)

---

## Review Follow-Up: Production Simplification Inside turn_handling/

**Problem**: After stabilizing the decomposition test surface, the production `backend/turn_handling/` package still had a couple of extraction-era duplications that made the code noisier than necessary. In `invitation.py`, the “generate a re-invite and return it” path was duplicated for both first-decline and substantive/off-topic cases. In `rounds.py`, the deterministic Cat5 photo-prompt return block appeared twice with the same append/result wiring. These were not correctness bugs, but they were exactly the kind of low-signal repetition that makes later changes riskier.

**Solution**: Kept behavior unchanged and simplified only the duplicated local paths. `invitation.py` now uses one local helper for the shared re-invite generation/result flow, and `rounds.py` now uses one local helper for deterministic collection photo-prompt responses. No branching rules, state transitions, or response semantics changed.

**Edits**:
- `backend/turn_handling/invitation.py` — extracted `_generate_reinvite_result()` to collapse the duplicated non-terminal STEP_2 re-invite path
- `backend/turn_handling/rounds.py` — extracted `_photo_prompt_result()` to collapse the duplicated deterministic Cat5 photo-phase response path
- `HANDOFF.md` — added this review follow-up entry

**NOT Changed**:
- `backend/turn_handling/core.py`, `backend/turn_handling/collection.py`, `backend/turn_handling/synthesis.py`, `backend/turn_handling/directive.py` — reviewed again and left unchanged in this pass
- State-machine behavior, turn advancement order, and deterministic acceptance/photo prompt content — unchanged
- Test fixtures from the previous review follow-up — kept as-is
- Frontend code — unchanged

**Verification**:
- `uv run pytest tests/test_turn_handler.py tests/test_api.py tests/test_server_visual.py -q` — PASS (`77 passed`)
- `uv run pytest tests/test_turn_handler.py tests/test_debug_payload.py tests/test_intent_classifier.py tests/test_deep_link.py tests/test_api.py tests/test_server_visual.py -q` — PASS (`116 passed`)
- `uv run ruff check backend/turn_handling/invitation.py backend/turn_handling/rounds.py tests/test_turn_handler.py tests/test_api.py tests/test_server_visual.py` — PASS
- `uv run ruff format --check backend/turn_handling/invitation.py backend/turn_handling/rounds.py tests/test_turn_handler.py tests/test_api.py tests/test_server_visual.py` — PASS

---

## Review Follow-Up: Stabilize Legacy turn_handling Tests

**Problem**: Picking up the `turn_handler.py` decomposition work showed that the newly updated legacy-path tests no longer matched the repo's runtime defaults. `backend/config.yaml` currently enables `turn_director_enabled`, so focused tests that were meant to exercise the classic `turn_handling.core.resolve_turn()` path were accidentally entering the directive path, making real Turn Director calls and even trying to log to the demo DB. Two other test expectations had also drifted: the synthesis-failure regression patched the wrong `get_settings()` function after the module split, and the Step 2 acceptance API/visual tests still mocked `ScriptAgent.generate_turn()` even though invitation acceptance now uses deterministic celebration templates instead of the speaker path.

**Solution**: Kept production turn-handling code unchanged and fixed the review surface instead. The touched legacy tests now explicitly disable `turn_director_enabled` in their local fixtures so they exercise the decomposed classic path they are written for. I also updated the synthesis regression to patch `turn_handling.generation.get_settings()`, aligned the Step 2 acceptance API assertion with deterministic `_ACCEPTANCE_CELEBRATIONS`, removed no-op `generate_turn()` mocks from the visual-frame acceptance tests, and fixed the stale `turn_handler` wording in `scripts/scoring.py`.

**Edits**:
- `tests/test_turn_handler.py` — added an autouse legacy-path settings stub (`turn_director_enabled=False`) and corrected the synthesis classifier-failure patch target to `turn_handling.generation.get_settings`
- `tests/test_api.py` — disabled Turn Director in the temp-client fixture; aligned the invitation-acceptance assertion with `_ACCEPTANCE_CELEBRATIONS` instead of an unused speaker mock
- `tests/test_server_visual.py` — disabled Turn Director in the temp-client fixture and removed unused `ScriptAgent.generate_turn()` mocks from Step 2 acceptance visual tests
- `scripts/scoring.py` — updated the stale comment to refer to `turn_handling` validators
- `HANDOFF.md` — added this review follow-up entry

**NOT Changed**:
- `backend/turn_handling/` production modules — reviewed and left unchanged in this follow-up
- `backend/server.py` import changes — reviewed and kept as-is
- `backend/config.yaml` — still enables Turn Director for normal runtime; the isolation is test-scoped only
- Frontend code — unchanged

**Verification**:
- `uv run pytest tests/test_turn_handler.py tests/test_debug_payload.py tests/test_intent_classifier.py tests/test_deep_link.py tests/test_api.py tests/test_server_visual.py -q` — PASS (`116 passed`)
- `uv run ruff check backend/turn_handling backend/server.py scripts/scoring.py tests/test_turn_handler.py tests/test_debug_payload.py tests/test_intent_classifier.py tests/test_deep_link.py tests/test_api.py tests/test_server_visual.py` — PASS
- `uv run ruff format --check tests/test_turn_handler.py tests/test_api.py tests/test_server_visual.py scripts/scoring.py` — PASS
