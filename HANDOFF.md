# Session Handoff

Last updated: 2026-03-13

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

## Glassmorphic UI Redesign — Reference Image Match

**Problem**: User provided 4 chatbot UI reference images (`docs/chatbot-ui-1.png`, `chatbot-ui-2.png`, `chatbot-ui-3.png`, `chatbot_UI.png`) showing a light glassmorphic design with pastel gradient mesh background, frosted glass panels, rounded cards, soft shadows, avatar on AI bubbles, pill-shaped input, and clean typography. Current dark fuchsia theme did not match.

**Solution**: Complete visual redesign to match the reference. Fonts changed to Plus Jakarta Sans (display) + Outfit (body). Background uses multi-stop radial gradient mesh (lavender/mint/pink/blue washes). All surfaces use `.glass` / `.glass-strong` / `.glass-subtle` utility classes with `backdrop-blur` and semi-transparent white backgrounds. AI chat bubbles have a small indigo/purple avatar icon. User bubbles are `bg-gray-700` (dark, as shown in reference for user messages). Input is pill-shaped with mic inside the input container and a separate dark send button. All widgets use frosted glass surfaces with soft colored shadows.

**Edits**:
- `frontend/index.html` — Switched fonts to Plus Jakarta Sans 400-800 + Outfit 300-700
- `frontend/src/index.css` — New `@theme` (Outfit + Plus Jakarta Sans), `.bg-mesh` multi-gradient background, `.glass` / `.glass-strong` / `.glass-subtle` utility classes
- `frontend/src/App.jsx` — `bg-mesh`, glass panels with `rounded-3xl`, outer padding/gap, footer as glass pill
- `frontend/src/components/TopBar.jsx` — Glass bar with indigo/purple gradient logo icon, dark "New Session" button, glass select
- `frontend/src/components/ChatBubble.jsx` — AI bubbles: `bg-white/70` with indigo avatar circle. User: `bg-gray-700 text-white`. Tone badge: `bg-indigo-50 text-indigo-400`
- `frontend/src/components/TextInput.jsx` — Pill container `bg-white/50` with inline mic button, separate dark send button with up-arrow icon
- `frontend/src/components/ConversationPanel.jsx` — Empty state with gradient icon, glass timer bar
- `frontend/src/components/PhotoSelector.jsx` — Gradient camera icon, glass photo cards with hover scale, indigo accents
- `frontend/src/components/RetryButton.jsx` — Dark button, amber glass badge
- `frontend/src/components/DeviceScreen.jsx` — Transparent device frame (inherits parent glass), white/40 surfaces
- `frontend/src/widgets/BadgeAward.jsx` — Amber/gold badge with white/60 backdrop center, indigo concept tags
- `frontend/src/widgets/PhotoDisplay.jsx` — `bg-white/40 border-white/60` glass frame
- `frontend/src/widgets/ProgressTracker.jsx` — Emerald filled slots with colored shadow, glass empty slots
- `frontend/src/widgets/CharacterDisplay.jsx` — Pastel gradient backgrounds with glass inner cards
- `frontend/src/widgets/PhotoGrid.jsx` — Glass grid slots, indigo "Connected!" text

**NOT Changed**:
- Backend code, hooks, AnimationOverlay, API client, all ARIA attributes, responsive stacking unchanged

**Verification**:
- `cd frontend && npm run build` — PASS (48 modules, 630ms)
- `cd frontend && npm run lint` — PASS (no errors)

---

## OpenAI Agent Timeout Handling

**Problem**: The latest backend change set switched the Director and Script agents from Gemini to `AsyncOpenAI`, but the timeout path still only caught built-in `TimeoutError`. In the installed OpenAI SDK, request timeouts raise `openai.APITimeoutError`, so the Director timeout fallback would miss the intended timeout branch and the Script agent would log a generic failure instead of an explicit timeout.

**Solution**: Updated both OpenAI-backed agents to catch `APITimeoutError` directly and switched the parsed chat completion calls to `max_completion_tokens`, which matches the current SDK signature for structured chat completions more closely than the older `max_tokens` field.

**Edits**:
- `backend/agents/director.py` — catch `APITimeoutError` for the default-plan timeout path and use `max_completion_tokens`
- `backend/agents/script_agent.py` — catch `APITimeoutError` explicitly for timeout logging and use `max_completion_tokens`

**NOT Changed**:
- Vision, TTS, and the rule-based Visual Agent remain on their existing implementations.
- Config values, dependency pins, and the OpenAI migration plan doc were reviewed but not changed in this pass.

**Verification**:
- `ruff check backend/agents/director.py backend/agents/script_agent.py backend/config.py pyproject.toml` — PASS
- `python - <<'PY' ... from agents.director import DirectorAgent; from agents.script_agent import ScriptAgent ... PY` — PASS
- `uv run pytest tests/ -m 'not e2e' -q` — PASS (`63 passed, 5 deselected`)

---

## Session Start Error Retry Visibility

**Problem**: [`frontend/src/App.jsx`](/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/frontend/src/App.jsx) had a real control-flow bug after the recent frontend refactor. When session start failed, the initial `showPhotoSelector` branch still won before the error branch, so the retry UI never rendered and users were dropped straight back to photo selection.

**Solution**: Split the branch conditions into explicit `showRetry` and `showPhotoSelector` flags so the error state takes precedence when there is no active session. This keeps the current layout logic simple and makes the existing retry path reachable again.

**Edits**:
- `frontend/src/App.jsx` — prioritized the retry state over the photo-selector state for failed session starts

**NOT Changed**:
- Session orchestration hook internals, retry button behavior, and backend API flows were not modified in this pass.
- The earlier TTS streaming test alignment and scenario filename hardening remain unchanged.

**Verification**:
- `cd frontend && npm run lint && npm run build` — PASS

---

## Streaming TTS Test Alignment

**Problem**: The latest backend/frontend verification exposed a regression in [`tests/test_api.py`](/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/tests/test_api.py): the `/api/tts` coverage still patched the removed non-streaming helper and still expected the old `204` fallback path, even though the implementation now streams PCM chunks via `synthesize_speech_stream()`. That left the suite out of sync with the actual route contract.

**Solution**: Updated the TTS API tests to patch `server.synthesize_speech_stream`, assert the streaming response headers/body for a successful chunked response, and cover the empty-stream case that the current frontend treats as a browser-fallback trigger.

**Edits**:
- `tests/test_api.py` — rewrote the `/api/tts` tests around the streaming contract instead of the removed non-streaming helper

**NOT Changed**:
- `/api/tts` implementation and frontend playback behavior were left unchanged in this pass.
- The frontend redesign/refactor work was reviewed again, but no additional concrete regressions were found from lint/build plus source review.

**Verification**:
- `uv run pytest tests/test_api.py::TestTTSEndpoint -q` — PASS
- `uv run pytest tests/ -m 'not e2e' -q` — PASS (`63 passed, 5 deselected`)
- `ruff check backend frontend/src tests` — PASS
- `cd frontend && npm run lint && npm run build` — PASS

---
