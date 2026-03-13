# Session Handoff

Last updated: 2026-03-13

---

## Cat 5 Pending Photo Tracking Fix

**Problem**: The new Cat 5 wrong-photo feedback path still had a frontend state bug. `useConversation` recorded the tapped `photoId` before `sendTurnRequest()` checked `turnPending`, while `PhotoGallery` re-enabled itself after a fixed 1-second timer. If the user tapped again before the first request finished, the second tap could overwrite the pending photo ID even though that second request was ignored, causing the later `wrong_photo` response to highlight the wrong card.

**Solution**: Moved pending photo tracking into the admitted request path so it only records the `photoId` for the turn that actually starts, and clear that ref on session start/reset. Simplified `PhotoGallery` so its temporary lock follows the `onPhotoSelect()` promise instead of an arbitrary timeout. Added focused local API coverage for the Cat 5 backend contract: wrong picks do not advance collection, and the second consecutive wrong pick exits cleanly.

**Edits**:
- `frontend/src/hooks/useConversation.js` — moved `pendingPhotoIdRef` assignment behind the `turnPending` guard; clear pending/wrong-photo state on start and reset; kept `sendPhotoCollection()` as a thin wrapper around `sendTurnRequest()`
- `frontend/src/components/PhotoGallery.jsx` — replaced the fixed 1-second unlock timer with promise-based request lifecycle locking
- local `tests/test_api.py` — added focused Cat 5 wrong-photo regression coverage in the current workspace

**NOT Changed**:
- The backend Cat 5 validation rules already added in `backend/server.py`, `backend/schemas/session_state.py`, and `backend/skills/step_instructions/cat5_step3_collect.md` were reviewed but not modified in this pass.
- The broader App/orchestration styling changes in `frontend/src/App.jsx`, `frontend/src/components/ConversationPanel.jsx`, `frontend/src/hooks/useSessionOrchestration.js`, and `frontend/src/index.css` were also reviewed without further edits.

**Verification**:
- `uv run pytest tests/test_api.py -q -k "wrong_photo_without_advancing_cat5_collection or exits_after_two_wrong_cat5_photo_picks"` — PASS
- `cd frontend && npm run lint` — PASS
- `cd frontend && npm run build` — PASS
- `uv run ruff check backend/schemas/session_state.py backend/server.py tests/test_api.py` — PASS
- `uv run pytest tests/ -m 'not e2e' -q` — PASS (`123 passed, 5 deselected`)

---

## Cat 5 Collection Validation + UI Polish

**Problem**: Cat 5 collection activities accepted any photo selection as correct, advancing progress regardless of whether the pick matched the collection criterion. The photo displayed in the camera device showed a placeholder letter instead of the actual image. The device screen had no fade transition between frames. SFX/widget/animation labels were missing from the first turn. AI chat text appeared all at once instead of streaming. The SFX badge auto-hid after 3 seconds. The photo grid in collection mode was too small, and text input was still enabled when the user should be selecting photos.

**Solution**: Multi-part fix across backend and frontend:
- **Photo validation**: Added `VALID_COLLECTION_PHOTOS` mapping per activity type (polka_dot_patrol, fluffy_expedition_dandelion). Wrong picks return `response_type: "wrong_photo"` without advancing the step. 2 consecutive wrong picks trigger graceful exit. Updated `cat5_step3_collect.md` prompt with wrong-photo handling instructions.
- **Photo display fix**: Changed `PhotoSelector` to use `/icons/*.png` as both thumbnails and the photo sent to the backend (the `/photos/` directory was empty).
- **Device screen transitions**: Added fade-in/fade-out effect to `DeviceScreen` when screen frames change.
- **First turn screen frame**: Fixed `/api/start` to use `get_screen_frame()` with Visual Agent frames instead of manually constructing a minimal dict.
- **Typewriter chat**: Added `useTypewriter` hook to `ChatBubble` — only the latest AI message types character by character at 18ms/char with a blinking cursor.
- **Persistent SFX badge**: Removed auto-hide timer from `SfxIndicator` — badge stays visible until replaced by a new frame's SFX.
- **Collection UI**: Enlarged PhotoGallery grid (`max-w-md`, larger icons/progress circles), added shake animation for wrong picks, disabled text input during collection steps with a "Tap a photo" hint.
- **Photo border**: Removed `border-2 border-[var(--color-forest)]/20 shadow-lg` from `PhotoDisplay`.

**Edits**:
- `backend/schemas/session_state.py` — Added `consecutive_wrong: int = 0` field
- `backend/server.py` — Added `VALID_COLLECTION_PHOTOS` mapping, `_is_correct_collection_photo()` helper; both `/api/turn` and `/api/turn-speak` validate photo selections (correct → advance, wrong → stay + "wrong_photo" response, 2 wrong → exit); fixed `/api/start` first turn to use `get_screen_frame()` with visual frames; added `consecutive_wrong` to `_session_state_dict`
- `backend/skills/step_instructions/cat5_step3_collect.md` — Added wrong-photo handling instructions for Script Agent
- `frontend/src/components/PhotoSelector.jsx` — Changed photo sources from `/photos/*.jpg` to `/icons/*.png`; removed separate `icon` field
- `frontend/src/components/DeviceScreen.jsx` — Added fade-in/fade-out transitions on screen frame changes via `useEffect` + opacity
- `frontend/src/components/ChatBubble.jsx` — Added `useTypewriter` hook for streaming text effect on latest AI message
- `frontend/src/components/ConversationPanel.jsx` — Pass `isLatestAi` to ChatBubble; added `collectMode` prop to replace TextInput with photo hint
- `frontend/src/components/SfxIndicator.jsx` — Removed auto-hide timer and state; renders persistently when `sfxCue` is present
- `frontend/src/components/PhotoGallery.jsx` — Larger grid (`max-w-md`), larger icons (`w-10 h-10`), larger progress circles (`w-9 h-9`); added `wrongPhotoId` prop with shake animation and red highlight
- `frontend/src/widgets/PhotoDisplay.jsx` — Removed border and shadow from photo container
- `frontend/src/index.css` — Added `@keyframes shake` and `.animate-shake`
- `frontend/src/hooks/useConversation.js` — Track `lastWrongPhotoId` from `wrong_photo` responses; store pending photo ID via ref
- `frontend/src/hooks/useSessionOrchestration.js` — Pass through `lastWrongPhotoId`
- `frontend/src/App.jsx` — Pass `wrongPhotoId` to PhotoGallery, `collectMode` to ConversationPanel, disable text input during collection

**NOT Changed**:
- State machine, Director Agent, Visual Agent, pipeline, DB layer, STT, TTS, tier rules, scenarios, fallback recipes
- useTTS, useSpeechRecognition, useSilenceTimer hooks
- All widget components except PhotoDisplay

**Verification**:
- `cd backend && uv run ruff check . && uv run ruff format --check .` — PASS
- `cd frontend && npm run build` — PASS

---

## Chat Bubble Typewriter + Local API Test Realignment

**Problem**: The newly added typewriter effect in `ChatBubble` failed frontend lint because it synchronously reset React state inside an effect. In the same review pass, the local `tests/test_api.py` file still targeted removed server contracts (`server.generate_recipe`, `SessionState`, and sync TTS patching), so the non-e2e suite was no longer a useful regression signal.

**Solution**: Simplified the typewriter hook so it only performs timer-driven updates while active, and keyed the latest AI bubble wrapper so the animation resets cleanly without effect-time state rewrites. Then updated the stale local API tests to match the current architecture: `/api/start` now patches `initialize_session`, the obsolete legacy turn-flow tests were reduced to the still-valid `session not found` case, and `/api/tts` now patches `synthesize_speech_stream_async`.

**Edits**:
- `frontend/src/components/ChatBubble.jsx` — removed synchronous effect resets from `useTypewriter()`
- `frontend/src/components/ConversationPanel.jsx` — keyed chat rows so the latest AI bubble remounts cleanly for typewriter playback
- local `tests/test_api.py` — realigned start/turn/TTS coverage to the current server contracts in the current workspace

**NOT Changed**:
- The current backend provider/runtime changes (`director.py`, `script_agent.py`, `visual_agent.py`, `vision.py`, `stt.py`, `tts.py`, config/env files) were reviewed but not modified in this pass.
- The icon/demo-photo asset changes were also reviewed, but no additional concrete issue in that path justified widening scope.

**Verification**:
- `cd frontend && npm run lint` — PASS
- `cd frontend && npm run build` — PASS
- `uv run ruff check tests/test_api.py backend/agents/director.py backend/agents/script_agent.py backend/agents/visual_agent.py backend/config.py backend/server.py backend/stt.py backend/tts.py backend/vision.py` — PASS
- `uv run pytest tests/ -m 'not e2e' -q` — PASS (`121 passed, 5 deselected`)

---

## Device Screen Frame-Key Simplification

**Problem**: The latest `DeviceScreen` transition logic introduced two issues in the redesigned UI path. First, the component keyed frame changes only by `widget + trigger`, so celebration and closing could both resolve to `badge_award + on_correct` and leave the old badge content on screen instead of updating. Second, both `DeviceScreen` and `SfxIndicator` now failed the frontend lint rules because they were calling `setState()` synchronously inside effects.

**Solution**: Removed the effect-driven frame swapping and replaced it with a deterministic frame key derived from the full screen-frame payload. `DeviceScreen` now renders directly from props, remounting the frame subtree when any meaningful screen-frame field changes, which also resets `SfxIndicator` cleanly. `SfxIndicator` keeps only the delayed hide timer, so the lint errors are gone without reintroducing state synchronization logic.

**Edits**:
- `frontend/src/components/DeviceScreen.jsx` — replaced local transition state with a full `getFrameKey()` helper and keyed frame rendering
- `frontend/src/components/SfxIndicator.jsx` — removed synchronous effect-driven visibility toggles and kept timer-only hide behavior

**NOT Changed**:
- `frontend/src/components/PhotoSelector.jsx`, `frontend/src/widgets/PhotoDisplay.jsx`, and the current demo icon assets were reviewed but not modified in this pass.
- No existing frontend component test harness covers `DeviceScreen` or `SfxIndicator`, so this pass did not add automated UI tests.

**Verification**:
- `cd frontend && npm run lint` — PASS
- `cd frontend && npm run build` — PASS

---

## Visual Agent Celebration Frame Wiring

**Problem**: The new Visual Agent stack generated and stored `celebration_frame`, but the active turn flow never used it. `backend/state_machine.py` only matched `visual_frames`, so the celebrate step still rendered the hardcoded badge frame and dropped the Visual Agent’s labels/SFX metadata on completion.

**Solution**: Extended `get_screen_frame()` to accept `celebration_frame` and prefer it for `STEP_4_CELEBRATE` / `STEP_5_CELEBRATE`. Updated the server turn paths to pass the stored frame through, and added focused regression coverage proving the celebrate response now returns the Visual Agent’s completion frame and `sfx_label`.

**Edits**:
- `backend/state_machine.py` — added `celebration_frame` handling to `get_screen_frame()` for celebrate steps
- `backend/server.py` — passed `state.celebration_frame` through all `get_screen_frame()` call sites
- local `tests/test_api.py` — added a focused regression test for Visual Agent celebration-frame delivery in the current workspace

**NOT Changed**:
- The Visual Agent prompt/schema, per-round `visual_frames` matching, and frontend SFX display components were reviewed but not modified in this pass.
- Closing-step rendering remains unchanged; this fix only makes the dedicated celebration frame live for the celebration response itself.

**Verification**:
- `uv run pytest tests/test_api.py -q -k turn_uses_visual_agent_celebration_frame_for_celebrate_step` — PASS (`1 passed, 18 deselected`)
- `uv run ruff check backend/state_machine.py backend/server.py tests/test_api.py` — PASS
- `uv run pytest tests/test_api.py -q -k "turn_enters_first_round_with_round_number_one or turn_marks_closing_delivery_complete_without_auto_advance or turn_uses_visual_agent_celebration_frame_for_celebrate_step or turn_speak_uses_final_fallback_dialogue_for_tts"` — PASS (`4 passed, 15 deselected`)

---

## Frontend Redesign + LLM Visual Agent (Full Stack)

**Problem**: The frontend used a dark glassmorphic left/right split layout with small widgets, emoji icons, and no sound effect display. The Visual Agent was rule-based with fixed widget mappings. Needed child-friendly nature/explorer theme with top/bottom layout, toy camera frame, SVG icons, SFX indicators, category-grouped landing page, and LLM-powered Visual Agent.

**Solution**: Implemented all 6 phases from `docs/plans/frontend-redesign-visual-agent.md`:
- **Phase 1 (Backend)**: Converted Visual Agent from rule-based to async LLM-based (Gemini via google.genai) with rule-based fallback. Added `sfx_cue`, `sfx_label`, `animation_label`, `widget_label` to ScreenFrame schema. Stored visual frames in session state. Updated pipeline to run Visual + Script agents in parallel. Updated state machine and all server endpoints to pass visual frames.
- **Phase 2 (Icons + CSS)**: Created 15 SVG icon components in `frontend/src/icons/`. Replaced `.bg-mesh`/`.glass` theme with `.bg-nature`/`.surface-primary`/`.surface-card` nature theme (Forest Green, Sky Blue, Warm Brown, Sunflower, Teal palette). Added larger animation keyframes.
- **Phase 3 (Layout)**: Changed from left/right to top/bottom split (42% camera top, 58% conversation bottom). Created `ToyCameraFrame` SVG component. Updated TopBar to green gradient.
- **Phase 4 (Widgets + SFX)**: Created `SfxIndicator` component. Made all widgets larger with SVG icons instead of emoji. DeviceScreen now shows widget/animation labels and SFX indicator.
- **Phase 5 (Landing)**: Redesigned PhotoSelector with two category sections (Cat 1 "In-Device Verbal" + Cat 5 "Out-of-Device Collection"), SVG icon fallbacks, leaf dividers.
- **Phase 6 (Theme)**: Updated ChatBubble (compass SVG avatar, green theme), ConversationPanel (green typing indicator), TextInput (green/teal theme), RetryButton, PhotoGallery to match nature theme. Zero emoji in UI.

**Edits**:
- `backend/schemas/visual_composition.py` — Added 4 label fields to ScreenFrame
- `backend/agents/visual_agent.py` — Full rewrite: async LLM-based + `_rule_based_fallback()` with SFX_LABELS
- `backend/agents/pipeline.py` — Visual Agent runs parallel with Script Agent via asyncio
- `backend/schemas/session_state.py` — Added `visual_frames`, `celebration_frame` fields
- `backend/state_machine.py` — Added `_match_visual_frame()`, `visual_frames` param to `get_screen_frame()`
- `backend/server.py` — All 4 `get_screen_frame()` calls pass `visual_frames`, `sfx_label` in audio dict
- `backend/prompts/visual_system.md` — NEW: Visual Agent system prompt
- `frontend/src/icons/` — NEW: 15 SVG components + barrel export
- `frontend/src/index.css` — Full theme overhaul (nature palette, surface classes, large animations)
- `frontend/src/App.jsx` — Top/bottom layout with ToyCameraFrame
- `frontend/src/components/ToyCameraFrame.jsx` — NEW: Toy camera SVG frame
- `frontend/src/components/SfxIndicator.jsx` — NEW: SFX display pill
- `frontend/src/components/TopBar.jsx` — Forest green gradient, CameraIcon
- `frontend/src/components/DeviceScreen.jsx` — SFX indicator, labels, CameraIcon placeholder
- `frontend/src/components/PhotoSelector.jsx` — Category grouping, SVG icons
- `frontend/src/components/ChatBubble.jsx` — CompassIcon avatar, green theme
- `frontend/src/components/ConversationPanel.jsx` — Green/teal accents
- `frontend/src/components/TextInput.jsx` — Green/teal theme
- `frontend/src/components/RetryButton.jsx` — Nature theme
- `frontend/src/components/PhotoGallery.jsx` — SVG icons, green theme
- `frontend/src/widgets/` — All 6 widgets enlarged, SVG icons, nature theme

**NOT Changed**:
- Backend hooks, STT, TTS, DB, config, scenarios, tier rules, fallback recipes
- Frontend hooks (useSessionOrchestration, useConversation, useTTS, useSpeechRecognition, useSilenceTimer)
- API client (utils/api.js)

**Verification**:
- `cd backend && uv run ruff check . && uv run ruff format --check .` — PASS
- `cd frontend && npm run build` — PASS (67 modules, 533ms)

---

## Turn-Speak Fallback Audio/Text Consistency

**Problem**: The new combined `/api/turn-speak` path could speak the wrong text when the streaming Script Agent emitted an early dialogue fragment and then failed. In that case, server-side TTS started from the early fragment, but the API fell back to a different final `TurnResponse`, so the spoken audio no longer matched the JSON turn payload shown in the UI.

**Solution**: Tightened the `/api/turn-speak` pipeline in `backend/server.py`. The server now tracks which dialogue string TTS started from and cancels/restarts TTS whenever the final `TurnResponse.dialogue` differs from the early streamed fragment. Added focused regression coverage to prove that fallback speech now uses the final canonical dialogue.

**Edits**:
- `backend/server.py` — restarted server-side TTS when early streamed dialogue differs from the final fallback turn, so streamed audio stays aligned with the returned turn JSON
- local `tests/test_api.py` — added focused `/api/turn-speak` regression coverage for the “early fragment then fallback” path in the current workspace (the repo ignores `tests/` new files)

**NOT Changed**:
- The binary streaming protocol, frontend `sendTurnSpeak()` parser, and progressive `useTTS()` playback path were reviewed but not modified in this pass.
- The broader streaming architecture from the previous pass remains intact; this fix only hardens the fallback boundary inside the combined endpoint.

**Verification**:
- `uv run ruff check backend/server.py tests/test_api.py` — PASS
- `uv run pytest tests/test_api.py -q -k "turn_returns_explicit_error_exit_when_script_generation_fails_twice or turn_enters_first_round_with_round_number_one or turn_serializes_collected_photos_for_cat5_collection or turn_marks_closing_delivery_complete_without_auto_advance or turn_speak_uses_final_fallback_dialogue_for_tts"` — PASS (`5 passed, 13 deselected`)

---

## Streaming Script Agent, Combined Turn+TTS Endpoint, Progressive Playback

**Problem**: Three latency bottlenecks in the turn-by-turn pipeline: (1) `/api/start` ran Vision → Director → Script hook sequentially (~22-43s), (2) Gemini 2.5 Flash's thinking mode consumed output tokens causing truncated JSON on nearly every Script Agent call, and (3) TTS time-to-first-audio (TTFA) was high because the frontend collected ALL PCM chunks before playing, and the turn response + TTS request required a full network round-trip.

**Solution**: Three optimizations applied together:

1. **Disabled Gemini thinking** (`thinking_budget=0`) — eliminates truncated JSON, reduces Script Agent latency from 3-8s to 1-2s, and hooks now succeed on first try instead of falling back to hardcoded defaults.
2. **Parallelized Vision + Director** in `/api/start` — scenario is matched from filename instantly, Director runs with filename-based entity while Vision runs concurrently. Vision results enrich the session state after both complete. Saves ~5s.
3. **Combined `/api/turn-speak` endpoint** — streams Script Agent output (extracts dialogue early via regex on partial JSON), starts TTS server-side as soon as dialogue is available (overlapping with remaining Script generation), then streams a binary response: `[4-byte JSON length][JSON turn data][PCM audio chunks]`. Frontend plays audio progressively using AudioContext time-scheduling (each chunk scheduled seamlessly after the previous), starting playback at the first TTS chunk instead of waiting for all chunks.

Measured improvement: `/api/start` dropped from 22-43s to ~12s; Script Agent turns from 3-8s (often failing) to 1-2s; TTS TTFA reduced by ~3s from progressive playback.

**Edits**:
- `backend/agents/script_agent.py` — Added `generate_turn_streaming()` with `on_dialogue` async callback for early dialogue extraction via `_DIALOGUE_RE` regex on partial JSON stream; added `ThinkingConfig(thinking_budget=0)` to both streaming and non-streaming generation configs; removed unused `_generation_config` helper and legacy `run()` method
- `backend/tts.py` — Added `synthesize_speech_stream_async()` using `client.aio.models.generate_content_stream` for proper async streaming (existing sync `synthesize_speech_stream` kept for `/api/tts` backward compat)
- `backend/server.py` — Parallelized Vision + Director in `/api/start` via `asyncio.gather`; added `_entity_from_filename()` helper; added `POST /api/turn-speak` combined endpoint with binary streaming protocol, `asyncio.Queue`-based TTS pipelining, and full state machine integration; added `expose_headers=["X-Sample-Rate"]` to CORS config; imported `json`, `struct`, `SAMPLE_RATE`, `synthesize_speech_stream_async`
- `backend/config.yaml` — Increased `script_turn_max_tokens` from 500 to 2048
- `frontend/src/utils/api.js` — Added `sendTurnSpeak()` that parses the 4-byte length-prefixed binary protocol, returns `{ turnData, audioStream, sampleRate }`
- `frontend/src/hooks/useTTS.js` — Rewrote for progressive playback: `scheduleChunk()` uses AudioContext time-scheduling for seamless gapless audio; added `playStream()` for streaming from ReadableStream; added `speakFromStream()` for playing pre-fetched audio streams; `speak()` now also uses progressive playback (was: collect-all-then-play)
- `frontend/src/hooks/useConversation.js` — `sendTurnRequest()` now uses `sendTurnSpeak()` with fallback to `sendTurn()`; exposes `pendingAudioRef` for orchestration hook to consume audio streams
- `frontend/src/hooks/useSessionOrchestration.js` — Auto-speak effect now checks `pendingAudioRef` for audio from `/api/turn-speak` and uses `speakFromStream()`, falling back to `speak()` (via `/api/tts`) for the first turn from `/api/start`

**NOT Changed**:
- `/api/turn` and `/api/tts` kept as working fallbacks
- Vision, STT, DB layer, state machine, Director Agent, scenarios, tier rules, widgets, all existing test files
- useSpeechRecognition, useSilenceTimer hooks

**Verification**:
- `uv run ruff check server.py agents/script_agent.py tts.py` — PASS
- `cd frontend && npx eslint src/utils/api.js src/hooks/useTTS.js src/hooks/useConversation.js src/hooks/useSessionOrchestration.js` — PASS
- `cd frontend && npm run build` — PASS (49 modules, 457ms)
- Server runtime: `/api/start` latency=12,623ms (was 22-43s), Script hook latency=3,617ms with no truncation (was failing), subsequent turns=1,165-1,555ms

---

## Turn Flow Contract Hardening

**Problem**: The turn-by-turn backend still had several concrete contract mismatches. Closing turns could leave the session `active` and ask the frontend to auto-advance one extra time, Cat 5 collection progress depended on `session_state.collected_photos` even though the serializer omitted it, round transitions could report `current_round = 0` after entering `STEP_3_*`, and Script Agent fallback failures did not surface as explicit `error` turns for the frontend `errorExit` path.

**Solution**: Tightened the turn contract in `backend/server.py`. The server now syncs `current_round` from the active round step, returns explicit `error` turns when Script generation fails twice, completes the session when the final closing line is delivered, suppresses auto-advance for closing and error states, and includes `collected_photos` in the serialized session state. Added focused regression coverage in tracked `tests/test_api.py` for all four paths.

**Edits**:
- `backend/server.py` — added explicit error-turn handling, `_sync_round_from_step()` / `_step_round_number()`, closing-turn completion, tighter auto-advance gating, and `collected_photos` in `session_state`
- `tests/test_api.py` — added focused turn-by-turn API tests for error fallback surfacing, first-round sync, Cat 5 collected-photo serialization, and closing-turn completion

**NOT Changed**:
- Director/Script prompt assets, state-machine templates, and frontend gallery components were reviewed but not modified in this pass.
- The older broad assertions in `tests/test_api.py` still target the pre-turn-by-turn recipe contract; this pass added focused coverage without rewriting that whole legacy file.

**Verification**:
- `uv run ruff check backend/server.py tests/test_api.py` — PASS
- `uv run pytest tests/test_api.py -q -k "turn_returns_explicit_error_exit_when_script_generation_fails_twice or turn_enters_first_round_with_round_number_one or turn_serializes_collected_photos_for_cat5_collection or turn_marks_closing_delivery_complete_without_auto_advance"` — PASS (`4 passed, 13 deselected`)

---

## Turn-by-Turn LLM Generation with Entity-Agnostic Templates

**Problem**: The architecture pre-generated the entire script upfront via the Script Agent (30-60s), then `/api/turn` was a pure recipe lookup (~5ms). This caused high initial latency and rigid dialogue that ignored what the child actually said.

**Solution**: Switched to turn-by-turn generation where the Script Agent generates only the next dialogue turn based on user input, template structure (Cat 1 or Cat 5), and conversation state. Director Agent now fills creative slots (game mechanic, metaphor, role title, etc.) that the per-turn Script Agent consumes via Gemini Flash.

**Edits**:
- `backend/schemas/creative_slots.py` — NEW: Cat1CreativeSlots and Cat5CreativeSlots Pydantic models
- `backend/schemas/turn_response.py` — NEW: TurnResponse schema (single turn output)
- `backend/schemas/session_state.py` — NEW: SessionStateModel and ConversationTurn for server-side state
- `backend/schemas/composition_plan.py` — Added template_type and creative_slots fields
- `backend/schemas/__init__.py` — Exports all new models
- `backend/state_machine.py` — NEW: Cat 1 / Cat 5 state machine (next_step, is_terminal, step_needs_user_input, get_screen_frame)
- `backend/agents/director.py` — Expanded to fill creative slots, template_type selection, default slots per category
- `backend/agents/script_agent.py` — REWRITE: Per-turn generation via Gemini Flash with modular system prompt assembly
- `backend/agents/pipeline.py` — REWRITE: initialize_session() replaces generate_recipe(), Director → state → Script hook flow
- `backend/server.py` — MAJOR REWRITE: SessionStateModel replaces SessionState, /api/start returns first_turn + session_state (no recipe), /api/turn runs Script Agent per turn with state machine advancement, auto_advance flag, error_exit handling
- `backend/config.yaml` — Added script_turn_timeout_ms (5000) and script_turn_max_tokens (500), increased director_max_tokens to 1000
- `backend/config.py` — Added script_turn_timeout_ms and script_turn_max_tokens settings
- `backend/skills/director.md` — Expanded with creative slot definitions, mechanic/angle selection logic
- `backend/skills/script_turn.md` — NEW: Modular system prompt for per-turn generation
- `backend/skills/step_instructions/` — NEW: 13 step instruction files for Cat 1 and Cat 5 steps + early exit
- `frontend/src/utils/api.js` — sendTurn now accepts optional photoId param
- `frontend/src/hooks/useConversation.js` — Removed recipe state, added templateType/errorExit/sendAutoAdvance/sendPhotoCollection
- `frontend/src/hooks/useSessionOrchestration.js` — Auto-advance for non-interactive steps (celebration/closing), errorExit passthrough, sendPhotoCollection
- `frontend/src/components/PhotoGallery.jsx` — NEW: Cat 5 collection gallery with progress indicator
- `frontend/src/App.jsx` — Conditional PhotoGallery rendering for Cat 5, error exit indicator, template type in footer
- `frontend/src/components/ConversationPanel.jsx` — Added errorExit prop

**NOT Changed**:
- Vision, STT, TTS, DB layer, tier_rules.yaml, fallback recipes, scenarios, existing widgets
- useSpeechRecognition, useTTS, useSilenceTimer hooks
- All existing test files (will need updates for new architecture)

**Verification**:
- `uv run ruff check .` — PASS
- `uv run ruff format --check .` — PASS (23 files already formatted)
- `cd frontend && npm run lint` — PASS
- `cd frontend && npm run build` — PASS (49 modules, 445ms)

---
