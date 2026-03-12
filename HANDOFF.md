# Session Handoff

Last updated: 2026-03-12

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

## Scenario Filename Matching Hardening

**Problem**: The new filename-based scenario fallback in [`backend/scenarios.py`](/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/backend/scenarios.py) was too permissive. Very short filenames such as `c.jpg` could match unrelated keywords because the fallback checked both `keyword in filename` and `filename in keyword`, which produced incorrect activity selection when vision/entity matching failed. The latest backend pass also still left [`backend/tts.py`](/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/backend/tts.py) outside Ruff's formatting check.

**Solution**: Added a focused regression test for filename fallback behavior, then tightened the matcher so filename fallback only triggers when a known keyword appears in the filename stem. Reformatted `backend/tts.py` so the backend check is clean again.

**Edits**:
- `tests/test_scenarios.py` — added filename fallback coverage for a valid match (`ladybug.jpg`) and a short unrelated filename (`c.jpg`)
- `backend/scenarios.py` — removed reverse containment from filename fallback matching to avoid false-positive activity selection
- `backend/tts.py` — reformatted to satisfy Ruff

**NOT Changed**:
- Entity-based and feature-based scenario matching logic were left unchanged.
- Frontend TTS playback behavior and backend route contracts were not modified in this pass.

**Verification**:
- `uv run pytest tests/test_scenarios.py -k filename -q` — PASS
- `ruff check backend tests && ruff format --check backend tests` — PASS
- `uv run pytest tests/ -m 'not e2e' -q` — PASS (`63 passed, 5 deselected`)
- `cd frontend && npm run lint && npm run build` — PASS

---

## Dark Theme — Fuchsia/Pink Chatbot UI Design

**Problem**: User provided a reference design (`docs/chatbot_UI.png`) showing a dark chatbot UI with near-black backgrounds (#0a0a0a), fuchsia/pink accent color, gradient user bubbles (fuchsia→purple), dark AI bubbles, rounded pill-shaped inputs, and subtle `white/5`–`white/10` borders.

**Solution**: Redesigned the entire frontend to match the reference. Near-black base (#0a0a0a, #111, #1a1a1a), fuchsia-500 as primary accent, user bubbles with `from-fuchsia-500 to-purple-600` gradient, AI bubbles flat dark (#1a1a1a), rounded-full buttons, pill input, ultra-thin `border-white/5` and `border-white/10` borders. All widgets updated to fuchsia accent on dark surfaces.

**Edits**:
- All components + all 5 widgets updated: backgrounds → #0a0a0a/#111/#1a1a1a, accent → fuchsia-500, borders → white/5 and white/10, text → white/neutral-200/neutral-500
- `ChatBubble.jsx` — User bubble: `from-fuchsia-500 to-purple-600` gradient. AI bubble: `bg-[#1a1a1a]`
- `TextInput.jsx` — Input `bg-[#1a1a1a]`, mic idle `bg-white/5`, send `bg-fuchsia-500`, placeholder "Send message..."
- `TopBar.jsx` — `bg-[#111]`, brand dot `bg-fuchsia-500`, buttons `bg-fuchsia-500 rounded-full`
- `PhotoSelector.jsx` — Hover `border-fuchsia-500/50`, hover overlay `bg-fuchsia-500/10`, spinner `border-t-fuchsia-500`
- `DeviceScreen.jsx` — `bg-[#111] rounded-3xl border-white/5`
- All widgets — fuchsia-400 headings, fuchsia-500/10 accent surfaces, white/5 borders

**NOT Changed**:
- Backend, hooks, AnimationOverlay, API client, ARIA attributes, responsive stacking, font setup unchanged

**Verification**:
- `cd frontend && npm run build` — PASS (48 modules, 433ms)
- `cd frontend && npm run lint` — PASS (no errors)

---

## Frontend Refactoring — Animation Fix, Orchestration Extraction, Visual Refresh, Accessibility, Polish

**Problem**: Frontend had a confirmed animation bug (ChatBubble uses `animate-bubble-in` but only `animate-fade-in` existed), an overloaded App.jsx (~210 LOC mixing orchestration with layout), generic purple/indigo styling with system fonts, missing accessibility attributes, wrong page title, silent STT fallback, and no responsive stacking.

**Solution**: Implemented 5-phase refactoring plan:
- **Phase 1** — Fixed bubble animation by adding `bubble-in` keyframe + `.animate-bubble-in` with `animation-fill-mode: forwards`; removed useEffect/useRef workaround from ChatBubble; fixed page title; added Google Fonts (Nunito + Fredoka); registered custom fonts in Tailwind v4 `@theme` block
- **Phase 2** — Extracted `useSessionOrchestration` hook (~120 LOC) from App.jsx, moving all 4 hook invocations, coordination effects, and handler callbacks; App.jsx dropped from ~210 to ~80 LOC with zero useEffect hooks
- **Phase 3** — Replaced purple/indigo palette with teal/cyan primary + amber accent across all components; added `.bg-dots` radial-gradient texture to device screen; applied `shadow-inner` to DeviceScreen; added `font-display` (Fredoka) to headings in TopBar, PhotoSelector, BadgeAward
- **Phase 4** — Added ARIA labels to mic/send/tier/new-session buttons; added `role="log"` + `aria-live="polite"` to message container; added `role="button"` + `tabIndex={0}` + keyboard handler to photo drop zone
- **Phase 5** — Added dismissible STT fallback banner in ConversationPanel when `sttMode === 'browser'`; added responsive `flex-col md:flex-row` stacking on main layout; photo grid responsive: `grid-cols-2 sm:grid-cols-3 md:grid-cols-5`

**Edits**:
- `frontend/index.html` — Updated title, added Google Fonts preconnect + stylesheet links
- `frontend/src/index.css` — Added `@theme` block (custom fonts), `bubble-in` keyframe, `.animate-bubble-in` class, `.bg-dots` utility
- `frontend/src/hooks/useSessionOrchestration.js` — New file: extracted orchestration from App.jsx
- `frontend/src/App.jsx` — Simplified to pure layout (~80 LOC), new color palette, responsive stacking, ARIA landmarks
- `frontend/src/components/ChatBubble.jsx` — Removed useEffect/useRef workaround, teal/cyan gradient
- `frontend/src/components/TopBar.jsx` — Teal palette, font-display, ARIA labels
- `frontend/src/components/TextInput.jsx` — Teal palette, ARIA labels + aria-pressed
- `frontend/src/components/PhotoSelector.jsx` — Teal palette, font-display, responsive grid, keyboard-accessible drop zone
- `frontend/src/components/ConversationPanel.jsx` — role="log", aria-live, STT fallback banner, sttMode prop
- `frontend/src/components/RetryButton.jsx` — Teal palette
- `frontend/src/components/DeviceScreen.jsx` — Teal/cyan gradient, shadow-inner
- `frontend/src/widgets/BadgeAward.jsx` — Teal/cyan gradient, font-display, teal concept badges

**NOT Changed**:
- Backend code, API endpoints, agent pipeline, schemas, and tests unchanged
- Hook internals (useConversation, useTTS, useSpeechRecognition, useSilenceTimer) unchanged
- Widget components other than BadgeAward unchanged

**Verification**:
- `cd frontend && npm run build` — PASS (48 modules, 421ms)
- `cd frontend && npm run lint` — PASS (no errors)

---

## FastAPI Lifespan + Test Fixture Cleanup

**Problem**: The new test suite passed, but the backend still emitted FastAPI deprecation warnings because [`backend/server.py`](/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/backend/server.py) used `@app.on_event("startup")`. The API test client fixture in [`tests/test_api.py`](/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/tests/test_api.py) also mutated the cached settings object without restoring it, which made the test setup more stateful than it needed to be.

**Solution**: Replaced the deprecated startup hook with a FastAPI lifespan handler and removed the now-redundant `Path("data").mkdir(...)` call because `init_db()` already creates the database parent directory. Tightened the API test fixture so it clears the settings cache before use, restores the original DB path after the client closes, and clears the cache again.

**Edits**:
- `backend/server.py` — switched startup initialization to `FastAPI(lifespan=...)`, keeping the same DB init behavior with less deprecated wiring
- `tests/test_api.py` — restored cached settings after each client fixture run to avoid leaking a temp DB path between tests

**NOT Changed**:
- Endpoint behavior, route shape, and session flow were not changed in this pass.
- Frontend code and backend agent logic were not modified here.

**Verification**:
- `ruff check backend tests && ruff format --check backend tests` — PASS
- `uv run pytest tests/ -m 'not e2e' -q` — PASS (`61 passed, 5 deselected`)
- `cd frontend && npm run lint && npm run build` — PASS

---

## Backend + Integration Test Suite

**Problem**: No test coverage existed beyond a single import compatibility test. Needed unit tests for schemas, agents, DB layer, scenarios, and integration tests for all API endpoints.

**Solution**: Created 7 test files with 61 tests covering schemas, scenarios, visual agent, recipe assembler, DB layer, and full API integration (mocking LLM/Vision/TTS calls). Added Playwright e2e test scaffold (marked `e2e`, skipped by default). Configured pytest in pyproject.toml with `pythonpath = ["backend"]`, asyncio_mode, and custom markers. Added `httpx` to dependencies and dev dependency group.

**Edits**:
- `tests/conftest.py` — Shared fixtures: fallback_recipe, sample_context, sample_vision_result, sys.path setup
- `tests/test_schemas.py` — 8 tests: CompositionPlan, VoiceScript, Round, ScreenFrame, ActivityRecipe, fallback validation, round-trip serialization
- `tests/test_scenarios.py` — 12 tests: match_scenario (direct/substring/feature/default), load_scenario, build_activity_context, categories
- `tests/test_visual_agent.py` — 8 tests: per_round/progressive/static strategies, widget maps, animation maps, celebration frame
- `tests/test_recipe_assembler.py` — 8 tests: merge, frame padding, hook rule validation, SFX validation, metadata
- `tests/test_db.py` — 6 tests: init_db, log/get session, update status, log turn, nested dir creation
- `tests/test_api.py` — 14 tests: /api/health, /api/start (success + error), /api/turn (correct/incorrect/silence/graceful exit/full completion/404), /api/tts (success + 204), /api/stt (success + empty)
- `tests/test_e2e.py` — 5 Playwright e2e tests (requires running servers, skipped by default)
- `pyproject.toml` — Added httpx dependency, dev dependency group, pytest config with pythonpath/markers/asyncio_mode

**NOT Changed**:
- Backend server, agents, schemas, and frontend code unchanged
- Existing test_backend_imports.py preserved

**Verification**: `uv run pytest tests/ -m "not e2e" -v --tb=short` — 61 passed, 0 failed (2.83s)

---

## Server-side STT + Speech Hook Stabilization

**Problem**: Speech-to-text relied entirely on the browser's Web Speech API, which is vendor-dependent, inconsistent across browsers, and not using Gemini. The backend also had Ruff findings around shared client setup, and the first server-STT frontend hook revision still had a React hook-order lint error that made the handoff's frontend verification stale.

**Solution**: Added server-side STT via Gemini, wired a new `/api/stt` endpoint, and updated the frontend speech hook to use MediaRecorder → server transcription with browser Web Speech API fallback. Fixed the backend Ruff issues by replacing `global _client` singletons with `@lru_cache(maxsize=1)` and cleaning the overwritten loop variable in `recipe_assembler`. Follow-up review then simplified the speech hook ordering so frontend lint/build now pass again.

**Edits**:
- `backend/stt.py` — New file: `transcribe_audio()` via Gemini, auto-detects MIME from magic bytes, 30s timeout
- `backend/server.py` — Added `POST /api/stt` endpoint (multipart audio upload → transcription JSON), imported `transcribe_audio`
- `backend/agents/director.py` — Replaced `global _client` with `@lru_cache(maxsize=1)`
- `backend/agents/script_agent.py` — Replaced `global _client` with `@lru_cache(maxsize=1)`
- `backend/tts.py` — Replaced `global _client` with `@lru_cache(maxsize=1)`
- `backend/vision.py` — Replaced `global _client` with `@lru_cache(maxsize=1)`
- `backend/stt.py` — Uses `@lru_cache(maxsize=1)` from the start
- `backend/agents/recipe_assembler.py` — Renamed loop variable `sentence` → `fragment` to fix PLW2901
- `frontend/src/utils/api.js` — Added `transcribeAudio(audioBlob)` API client function
- `frontend/src/hooks/useSpeechRecognition.js` — Rewritten: server STT via MediaRecorder as default, browser Web Speech API as fallback, with hook-order cleanup after review

**NOT Changed**:
- TTS flow, conversation state management, and all other frontend components unchanged
- Backend agent pipeline logic, schemas, and fallback recipes unchanged

**Verification**:
- `cd backend && ruff check . && ruff format --check .` — all passed
- `python -m unittest tests/test_backend_imports.py` — PASS
- `cd backend && python -c "from stt import transcribe_audio; print('OK')"` — OK
- `cd backend && python -c "from server import app; print(len(app.routes))"` — 9 routes
- `cd frontend && npm run lint` — PASS
- `cd frontend && npm run build` — PASS

---

## Review: Backend Import Compatibility

**Problem**: The newly added backend only imported when executed from inside `backend/`. Importing `backend.server` from the repo root failed because the source files used cwd-dependent absolute imports such as `from agents...` and `from config...`.

**Solution**: Added a regression test covering both import modes, then updated the backend modules to prefer package-relative imports with a fallback to the existing local-module style. This keeps `cd backend && import server` working while also supporting `import backend.server` from the repo root and from tests.

**Edits**:
- `tests/test_backend_imports.py` — Added subprocess-based regression coverage for both backend import paths
- `backend/server.py` — Switched imports to relative-first with fallback
- `backend/db.py` — Switched imports to relative-first with fallback
- `backend/scenarios.py` — Switched imports to relative-first with fallback
- `backend/vision.py` — Switched imports to relative-first with fallback
- `backend/tts.py` — Switched imports to relative-first with fallback
- `backend/agents/director.py` — Switched imports to relative-first with fallback
- `backend/agents/script_agent.py` — Switched imports to relative-first with fallback
- `backend/agents/recipe_assembler.py` — Switched imports to relative-first with fallback and cleaned touched imports
- `backend/agents/visual_agent.py` — Switched imports to relative-first with fallback
- `backend/agents/pipeline.py` — Switched imports to relative-first with fallback

**NOT Changed**:
- Session logging order versus `agent_logs` insertion timing was reviewed but not changed in this pass.
- Turn-flow semantics around `transition_line` and `Round.prompt` usage were reviewed but not changed in this pass.
- Frontend code and fallback recipe content were not modified here.

**Verification**:
- `python -m unittest tests/test_backend_imports.py` — PASS
- `python -m compileall backend` — PASS

---

## Code Review + Frontend Stabilization

**Problem**: Newly added frontend code had React hook/lint violations, turn-processing race conditions, and a few avoidable complexity points. `HANDOFF.md` also did not yet reflect this review-and-fix pass.

**Solution**: Simplified the frontend conversation/speech flow without changing the user-facing demo model. Fixed timer/TTS callback ordering, prevented overlapping `/api/turn` requests, made repeated speech transcripts submit reliably, cleaned up photo object URLs, and hardened demo photo loading so missing assets fall back cleanly instead of uploading HTML as fake JPEGs.

**Edits**:
- `frontend/src/App.jsx` — removed hook ordering issue, tightened effect dependencies, disabled input during in-flight turns, centralized timer clears
- `frontend/src/hooks/useConversation.js` — added shared turn-response handling, in-flight turn guard, and object URL cleanup
- `frontend/src/hooks/useSilenceTimer.js` — replaced ref-derived render state with explicit `isRunning` state
- `frontend/src/hooks/useSpeechRecognition.js` — removed unnecessary effect-driven `supported` state and added `resultId` so identical transcripts can still submit
- `frontend/src/hooks/useTTS.js` — reordered fallback logic to satisfy hook rules and cleaned up audio URL lifecycle
- `frontend/src/components/PhotoSelector.jsx` — verify fetched demo assets are real images before converting to `File`
- `frontend/src/widgets/ProgressTracker.jsx` — removed an unused prop

**NOT Changed**:
- Backend agent pipeline, FastAPI endpoints, and schema shape were left as-is.
- Existing fallback recipe content and scenario YAML behavior were not modified in this pass.
- No dependency upgrades or broad refactors were performed.

**Verification**:
- `cd frontend && npm run lint` — PASS
- `cd frontend && npm run build` — PASS
- `python -m compileall backend` — PASS
- `python - <<'PY' ... from server import app; print(len(app.routes)) ... PY` — PASS (`8`)

---


---


---


---


---
