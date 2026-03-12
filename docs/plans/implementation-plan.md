# WonderLens Activity Demo — Implementation Plan

> **Created**: 2026-03-12
> **Status**: Draft
> **Build spec**: `docs/wonderlens_activity_demo_build_spec.md`

## Context

Building a split-view interactive browser demo with a multi-agent backend. A child selects a photo, the backend runs a 4-agent pipeline (Director → Script + Visual → Recipe Assembler) to generate a structured JSON recipe, and the frontend renders a conversation panel + device screen panel. After the initial recipe generation (~580ms), every subsequent turn is near-instant recipe lookup (~5ms).

**Primary demo activities:** mood_changer_dog (Cat 1, T0) + polka_dot_patrol (Cat 5, T1)

**Key decisions:**
- Agent prompts in `backend/skills/` (move existing `prompts/script_system.md` there)
- Rewrite fallback JSONs to match new ActivityRecipe Pydantic schema
- Real Gemini Vision API calls (not hardcoded)
- Working-first approach (optimize latency later)
- Frontend: Vite + React + Tailwind from scratch

---

## Phase 1: Foundation

**Goal:** Project skeleton with config, logging, and database.

| Step | File | Action | Ref |
|------|------|--------|-----|
| 1.1 | `pyproject.toml` | Add `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `aiosqlite`; remove `openai` | Spec §13 |
| 1.2 | `backend/config.yaml` | App defaults: model name, timeouts, DB path, log level | Spec §6.6 |
| 1.3 | `backend/config.py` | Pydantic BaseSettings loading `.env` (secrets) + `config.yaml` (app config). Fields: `google_cloud_project`, `google_cloud_location`, `google_application_credentials`, `gemini_model`, `director_timeout_ms`, `script_timeout_ms`, `max_retries`, `db_path`, `log_level` | Spec §6.6 |
| 1.4 | `backend/logger.py` | Structured logging setup (stdlib `logging`). Format: `%(asctime)s \| %(levelname)s \| %(name)s \| %(message)s` | Spec §6.7 |
| 1.5 | `backend/db.py` | aiosqlite init with 3 tables: `sessions`, `turns`, `agent_logs`. Helper functions for insert/query | Spec §6.8 |
| 1.6 | `backend/.env.example` | Template with placeholder Vertex AI credentials | — |

**Verify:**
```bash
cd backend && uv sync
python -c "from config import Settings; print(Settings().gemini_model)"
python -c "import asyncio; from db import init_db; asyncio.run(init_db())"
```

---

## Phase 2: Agent Skill Files

**Goal:** Create markdown skill files that serve as both LLM system prompts at runtime and code-generation context at build time.

| Step | File | Action | Ref |
|------|------|--------|-----|
| 2.1 | `backend/skills/director.md` | Director Agent system prompt — creative planner, outputs CompositionPlan JSON | Spec §5.1 |
| 2.2 | `backend/skills/script.md` | Adapt from existing `prompts/script_system.md` — **remove `[SCREEN]`/`[AUDIO]` directives**, add structured JSON output format (`VoiceScript` schema), add `{composition_plan}` and `{tier_constraints}` template placeholders | Spec §5.2, existing `prompts/script_system.md` |
| 2.3 | `backend/skills/visual.md` | Rule tables: activity→widget map, screen_strategy→frame_count, emotional_arc→animation, frame sequencing rules | Spec §5.3 |
| 2.4 | `backend/skills/assembler.md` | Validation checklist, merge rules, retry+fallback logic, allowed SFX cues | Spec §5.4 |
| 2.5 | `backend/skills/few_shot.md` | Few-shot examples derived from scenario YAML `detailed_interaction_script` sections | Spec §12 |
| 2.6 | `backend/skills/activity_context_template.md` | Template for injecting scenario context into Script Agent prompt | Spec §12 |

**Critical note:** The existing `prompts/script_system.md` (lines 77-99) has `[SCREEN]` and `[AUDIO]` directives baked in. The new `skills/script.md` must NOT have these — the Script Agent output is now pure JSON (`VoiceScript` schema), and the Visual Agent handles screen composition separately.

**Verify:** Manual review that each skill matches the spec. Confirm `script.md` has no `[SCREEN]`/`[AUDIO]` directives.

---

## Phase 3: Pydantic Schemas

**Goal:** Define data contracts between agents.

| Step | File | Model(s) | Key Fields | Ref |
|------|------|----------|------------|-----|
| 3.1 | `backend/schemas/__init__.py` | Re-exports all models | — | — |
| 3.2 | `backend/schemas/composition_plan.py` | `CompositionPlan` | `creative_brief`, `modalities`, `round_count`, `screen_strategy`, `widget_hint`, `emotional_arc`, `ib_concept_integration`, `closing_concept_targets`, `transition_strategy` | Spec §6.1 |
| 3.3 | `backend/schemas/voice_script.py` | `Round`, `VoiceScript` | Round: `prompt`, `correct_responses`, `on_correct`, `on_incorrect`, `on_silence`, `hint`, `sfx_cue`. VoiceScript: `hook_line`, `transition_line`, `rounds`, `closing_speech`, `tomorrow_hook` | Spec §6.2 |
| 3.4 | `backend/schemas/visual_composition.py` | `ScreenFrame`, `VisualComposition` | ScreenFrame: `widget`, `widget_params`, `animation`, `trigger`. VisualComposition: `screen_frames`, `celebration_frame` | Spec §6.3 |
| 3.5 | `backend/schemas/recipe.py` | `RecipeMetadata`, `ActivityRecipe` | RecipeMetadata: `tier`, `ib_theme`, `ib_key_concept`, `concepts_earned`, `round_count`. ActivityRecipe: `activity_type`, `voice_script`, `screen_frames`, `celebration_frame`, `metadata` | Spec §6.4 |

**Verify:**
```bash
python -c "from schemas.recipe import ActivityRecipe; print(ActivityRecipe.model_json_schema())"
```

---

## Phase 4: Agent Implementations

**Goal:** Build all four agents + vision + TTS + pipeline orchestrator.

### 4.1 Director Agent — `backend/agents/director.py`
- Class `DirectorAgent` with `async def run(context) -> CompositionPlan`
- Loads `skills/director.md` as system prompt on init
- Builds user content from: object entity, tier, IB theme, activity type
- Calls Gemini 2.0 Flash with JSON mode (`response_mime_type="application/json"`), temperature 0.3, max_tokens 150
- On timeout (200ms) or failure: return default CompositionPlan with sensible defaults per activity type
- Logs to `agent_logs` table via db.py
- **Ref:** `refs/llm/providers/gemini.py` for `genai.Client(vertexai=True)` + `client.models.generate_content()` pattern

### 4.2 Script Agent — `backend/agents/script_agent.py`
- Class `ScriptAgent` with `async def run(plan, context) -> VoiceScript`
- Loads `skills/script.md` + `skills/few_shot.md` on init
- Injects template placeholders at runtime:
  - `{activity_context}` — from scenario YAML (entity, key concepts, activity steps, interaction script)
  - `{composition_plan}` — JSON of Director's CompositionPlan
  - `{tier_constraints}` — formatted tier rules from `tier_rules.yaml` (words/sentence, max sentences, hook rule, closing concepts)
  - `{few_shot}` — from `skills/few_shot.md`
- Calls Gemini 2.0 Flash with JSON mode, temperature 0.7, max_tokens 600
- On timeout (600ms) or failure: raise for retry
- **Ref:** `refs/llm/providers/gemini.py`, existing `prompts/script_system.md` for prompt structure

### 4.3 Visual Agent — `backend/agents/visual_agent.py`
- Class `VisualAgent` with `def run(plan, context) -> VisualComposition` (sync, no LLM)
- Decision tables from `skills/visual.md`:
  - `ACTIVITY_WIDGET_MAP`: mood_changer→character_display, polka_dot_patrol→progress_tracker, etc.
  - `EMOTIONAL_ARC_ANIMATION`: build_excitement→celebration_burst, calm_curiosity→idle_bounce, etc.
- Frame sequencing:
  1. First frame: photo_display with sparkle_highlight (trigger: on_enter)
  2. Per-round frames: activity widget with round-specific params (trigger: on_round_N)
  3. Celebration frame: badge_award (trigger: on_correct, last round)
- Screen strategy logic:
  - `static` → 1 frame reused
  - `per_round` → N frames (one per round, different scenes)
  - `progressive` → 1 frame with progressive slot updates
- Returns `VisualComposition`

### 4.4 Recipe Assembler — `backend/agents/recipe_assembler.py`
- Class `RecipeAssembler` with `def merge(script, visuals, plan, context) -> ActivityRecipe`
- Merge rules:
  1. Take `voice_script` from Script Agent
  2. Take `screen_frames` + `celebration_frame` from Visual Agent
  3. If round count != frame count: pad shorter (repeat last frame / generic encouragement)
  4. Build `RecipeMetadata` from Director's plan + scenario
- Validation checklist (run in order):

| Check | Severity | On Failure |
|-------|----------|------------|
| JSON schema valid (Pydantic parse) | FATAL | Raise for retry |
| hook_line contains no factual questions | ERROR | Raise for retry |
| round_count within tier limits | WARNING | Truncate to tier max |
| closing_speech concepts ≤ tier max | WARNING | Trim excess |
| sfx_cue values from allowed set | WARNING | Set invalid to null |
| round count == frame count | WARNING | Pad shorter |

- Hook rule check: heuristic — reject if hook_line contains patterns like "how many", "what color", "do you know", "can you count", or ends with `?` after a factual phrase
- Returns recipe with `status`: "ok", "fixed_warnings", or "fallback"

### 4.5 Vision — `backend/vision.py`
- `async def analyze_image(image_bytes: bytes, mime_type: str) -> dict`
- Calls Gemini Vision via Vertex AI with prompt: "Identify the main object/entity. Return JSON: entity, confidence, scene, features"
- Returns `{"entity": "...", "confidence": float, "scene": "...", "features": [...]}`
- **Ref:** `refs/vision/providers/gemini.py` (image as `Part.from_bytes`)

### 4.6 TTS — `backend/tts.py`
- `async def synthesize_speech(text: str, tier: str) -> bytes | None`
- Calls Gemini TTS with tier-appropriate voice settings
- Converts PCM response to WAV format
- Returns None on failure (frontend falls back to browser SpeechSynthesis)
- **Ref:** `refs/tts/providers/gemini.py` (speech_config, PCM-to-WAV conversion)

### 4.7 Pipeline Orchestrator — `backend/agents/pipeline.py`
- `async def generate_recipe(context: PipelineContext) -> ActivityRecipe`
- Orchestration flow:
  ```
  for attempt in range(3):
      plan = await director.run(context)
      script = await script_agent.run(plan, context)
      visuals = visual_agent.run(plan, context)       # sync, ~10ms
      recipe = assembler.merge(script, visuals, plan, context)
      if recipe.status != "error": return recipe
  return load_fallback(context.activity_type)
  ```
- Logs each attempt + final outcome to `agent_logs`

### 4.8 Scenario Loader — `backend/scenarios.py`
- `load_scenario(activity_type: str) -> dict` — load + parse YAML
- `match_scenario(entity: str, features: list[str]) -> str` — map vision entity to best matching scenario (keyword matching against scenario entity fields)
- `build_activity_context(scenario: dict, vision_result: dict) -> str` — format scenario data into the activity context string for Script Agent template injection

**Verify:**
```bash
# Unit test agents with mock inputs
# Test full pipeline with a real image
```

---

## Phase 5: Fallback Recipes

**Goal:** Rewrite 2 existing fallback JSONs from Loop 1 flat-turns format to the new ActivityRecipe Pydantic schema.

### Current format (Loop 1):
Flat `turns` array with `role`, `step`, `text`, `screen`, `audio`, `raw_response` fields. Contains `[SCREEN]`/`[AUDIO]` directives in `raw_response`.

### New format (ActivityRecipe):
Structured `voice_script` (VoiceScript with rounds array containing branching paths) + `screen_frames` (ScreenFrame array) + `celebration_frame` + `metadata`.

| File | Activity | Tier | Rounds | Widget | Concepts |
|------|----------|------|--------|--------|----------|
| `backend/fallbacks/mood_changer_dog.json` | Cat 1 verbal | T0 | 3 | character_display | Perspective |
| `backend/fallbacks/polka_dot_patrol.json` | Cat 5 collection | T1 | 3 | progress_tracker | Form, Connection |

Source for content: existing fallback files + scenario YAML `detailed_interaction_script`.

Note: `polka_dot_patrol.json` replaces current `polka_dot_patrol_hard.json` (rename, since we want the standard scenario).

**Verify:**
```bash
python -c "from schemas.recipe import ActivityRecipe; import json; ActivityRecipe.model_validate(json.load(open('fallbacks/mood_changer_dog.json')))"
python -c "from schemas.recipe import ActivityRecipe; import json; ActivityRecipe.model_validate(json.load(open('fallbacks/polka_dot_patrol.json')))"
```

---

## Phase 6: FastAPI Server

**Goal:** Wire up API endpoints with session management.

### `backend/server.py`

**App setup:**
- FastAPI app with CORS middleware (allow `localhost:5173`)
- `@app.on_event("startup")`: init DB, create data directory
- In-memory session store: `dict[str, SessionState]` where `SessionState` holds recipe, current_round, consecutive_silence, status

**Endpoints:**

#### `POST /api/start` — Start new session
Request: `multipart/form-data` with `photo` (file) + `tier` (string)
Response: `{ session_id, vision_result, recipe, first_turn, status }`
Logic:
1. Read uploaded photo bytes
2. Call `analyze_image()` → vision_result
3. Call `match_scenario(vision_result.entity)` → activity_type
4. Load scenario YAML
5. Build pipeline context (vision_result, tier, scenario)
6. Call `generate_recipe(context)` → ActivityRecipe
7. Create session in DB + in-memory store
8. Build first_turn from recipe's `hook_line` + first screen_frame
9. Return everything

#### `POST /api/turn` — Process one child turn
Request: `{ session_id, text, is_silent }`
Response: `{ turn, session_state }`
Logic:
1. Load session from in-memory store
2. Get current round from recipe
3. Match response:
   - `is_silent` → use `on_silence`, increment `consecutive_silence`
   - Text matches `correct_responses` (case-insensitive keyword/substring) → use `on_correct`, reset silence
   - Else → use `on_incorrect`, reset silence
4. If `consecutive_silence >= 2` → graceful exit (warm goodbye from `closing_speech` shortened, status="exited", end_reason="consecutive_silence")
5. If last round completed → status="completed", return `closing_speech` + `celebration_frame`
6. Advance round pointer
7. Log turn to DB
8. Return matched dialogue + corresponding screen_frame + session_state

#### `POST /api/tts` — Text-to-speech
Request: `{ text, tier }`
Response: `audio/wav` stream (or 204 if TTS fails, frontend uses browser fallback)

#### `GET /api/health` — Health check
Response: `{ status: "ok" }`

**Verify:**
```bash
cd backend && uv run uvicorn server:app --reload --port 8000
curl http://localhost:8000/api/health
curl -X POST http://localhost:8000/api/start -F "photo=@test_photo.jpg" -F "tier=T0"
curl -X POST http://localhost:8000/api/turn -H "Content-Type: application/json" -d '{"session_id":"...", "text":"Happy!", "is_silent":false}'
```

---

## Phase 7: Frontend Scaffold

**Goal:** Vite + React + Tailwind running with split-view layout.

| Step | Action |
|------|--------|
| 7.1 | Initialize: `npm create vite@latest frontend -- --template react` |
| 7.2 | Install Tailwind: `npm install -D tailwindcss @tailwindcss/vite` |
| 7.3 | Configure `vite.config.js` with API proxy to `localhost:8000` |
| 7.4 | Set up `tailwind.config.js` + `postcss.config.js` + Tailwind directives in `index.css` |
| 7.5 | Build `App.jsx` — split-view layout per build spec §8 ASCII diagram |

**Layout structure:**
```
TopBar: [WonderLens Demo] [Tier: T0 v] [Activity: v] [New Session]
├── ConversationPanel (~55% left)
│   ├── Chat bubble list (scrollable)
│   ├── Text input + mic button
│   └── Silence timer indicator
└── DeviceScreen (~45% right)
    ├── Active widget area
    ├── Audio/SFX indicator
    └── Retry button (if error)
Footer: Round: 1/3 | Latency: 580ms | Tier: T1 | Status: active
```

**Verify:**
```bash
cd frontend && npm install && npm run dev
# Verify split layout renders at localhost:5173
```

---

## Phase 8: Frontend Components

**Goal:** Build all UI components and widgets.

### Components (`frontend/src/components/`)

| File | Purpose | Complexity |
|------|---------|------------|
| `ConversationPanel.jsx` | Chat bubble list, text input area, mic button, silence timer display | Medium |
| `ChatBubble.jsx` | Styled message bubble — AI (left, colored) vs child (right, gray). Shows tone marker | Simple |
| `TextInput.jsx` | Text field + submit button + mic toggle button | Simple |
| `PhotoSelector.jsx` | Grid of preloaded demo photos + file upload drop zone. On select → triggers session start | Medium |
| `TopBar.jsx` | Tier dropdown (T0/T1/T2), current activity display, New Session button | Simple |
| `DeviceScreen.jsx` | Widget switcher — renders active widget based on `screen_frame.widget` value from recipe | Medium |
| `RetryButton.jsx` | "Oops! Let's try again" button, shown on /api/start failure. After 3 fails → auto-load fallback | Simple |

### Widgets (`frontend/src/widgets/`)

| File | Purpose | Used By |
|------|---------|---------|
| `PhotoDisplay.jsx` | Child's uploaded photo with animation overlay (sparkle, glow) | First turns |
| `ProgressTracker.jsx` | Collection slots with fill animation (e.g., "2 of 4 found") | Cat 5 activities |
| `CharacterDisplay.jsx` | Scene illustration placeholder with description text | Cat 1 activities |
| `PhotoGrid.jsx` | 2x2 grid showing collected photos | Synthesis step |
| `BadgeAward.jsx` | Celebration badge with role title + concept reveal animation | Closing |
| `AnimationOverlay.jsx` | CSS animation layer (sparkle_highlight, celebration_burst, etc.) | All widgets |

### Utilities

| File | Purpose |
|------|---------|
| `frontend/src/utils/api.js` | API client: `startSession(photo, tier)`, `sendTurn(sessionId, text, isSilent)`, `synthesizeSpeech(text, tier)` |

---

## Phase 9: Frontend Hooks & Integration

**Goal:** Wire state management, speech, silence timer, and end-to-end flow.

### Hooks (`frontend/src/hooks/`)

| File | Purpose | Key Details |
|------|---------|-------------|
| `useConversation.js` | Central state manager | Holds: messages array, recipe, sessionState (status, currentRound, consecutiveSilence), loading flags. Exposes: `startSession()`, `sendMessage()`, `sendSilence()` |
| `useSilenceTimer.js` | Tier-specific silence timeout | Timeouts: T0=10s, T1=8s, T2=6s. Starts after TTS finishes speaking. Clears when user starts typing/speaking. On fire → calls `sendSilence()` |
| `useSpeechRecognition.js` | Browser Web Speech API wrapper | Start/stop mic, return transcript, handle errors/unsupported browsers gracefully |
| `useTTS.js` | Text-to-speech playback | Calls `/api/tts`, plays returned WAV via AudioContext. On failure/204 → falls back to browser `SpeechSynthesis`. Signals `onSpeakingDone` callback (triggers silence timer start) |

### Integration wiring in `App.jsx`
Connect all hooks to components for the full flow:
1. **PhotoSelector** → user picks photo + tier → `startSession()` → POST `/api/start`
2. Recipe arrives → show `hook_line` as first AI bubble → play TTS → start silence timer
3. User types/speaks OR silence fires → `sendMessage()` or `sendSilence()` → POST `/api/turn`
4. Response arrives → add AI bubble, update DeviceScreen widget, play SFX, play TTS
5. TTS finishes → restart silence timer
6. Repeat until all rounds done or graceful exit
7. On completion → show `closing_speech` + `celebration_frame` (BadgeAward widget)
8. On exit → disable input, show "Session ended — New Session" button

### Demo photos
Add 4-6 preloaded images to `frontend/public/photos/`:
- `dog.jpg` (stuffed toy dog → mood_changer_dog)
- `ladybug.jpg` (ladybug on leaf → polka_dot_patrol)
- Additional: cat, dinosaur toy, dandelion (for future scenarios)

---

## Phase 10: Polish

| Item | Details |
|------|---------|
| Loading skeleton | Show during recipe generation (~580ms) on /api/start |
| Typing indicator | Animated dots in AI bubble while waiting |
| CSS animations | sparkle_highlight (subtle pulse), celebration_burst (particles), badge_reveal (scale+glow), widget slide transitions |
| Fallback indicator | Subtle "Using backup mode" badge when `recipe.status === "fallback"` (for demo reviewer, not child) |
| Session end | Disable text input + mic when status is "exited" or "completed". Show "Session ended" message + "New Session" button |
| Error states | Network error → retry prompt. Invalid session → redirect to photo selection |

---

## Dependency Graph

```
Phase 1 (Foundation) ──┬──> Phase 2 (Skills) ──────> Phase 4 (Agents)
                       │                                     │
                       └──> Phase 3 (Schemas) ───────────────┤
                                                             │
                                                      Phase 5 (Fallbacks)
                                                             │
                                                      Phase 6 (Server)
                                                             │
Phase 7 (Frontend Scaffold) ──> Phase 8 (Components) ──> Phase 9 (Integration)
                                                             │
                                                      Phase 10 (Polish)
```

**Parallelizable:** Phases 7-8 (frontend) can run in parallel with Phases 4-6 (backend). They converge at Phase 9 (integration).

---

## Critical Reference Files

| File | Used For |
|------|----------|
| `backend/refs/llm/providers/gemini.py` | Gemini client init + `generate_content` call pattern |
| `backend/refs/vision/providers/gemini.py` | Vision API — image as `Part.from_bytes` |
| `backend/refs/tts/providers/gemini.py` | TTS synthesis — speech_config, PCM-to-WAV conversion |
| `backend/prompts/script_system.md` | Source for `skills/script.md` (remove directives, add JSON output) |
| `backend/tier_rules.yaml` | Tier constraints for all agents |
| `backend/scenarios/mood_changer_dog.yaml` | Primary Cat 1 scenario definition |
| `backend/scenarios/polka_dot_patrol.yaml` | Primary Cat 5 scenario definition |
| `backend/fallbacks/mood_changer_dog.json` | Existing fallback (Loop 1 format → rewrite) |
| `backend/fallbacks/polka_dot_patrol_hard.json` | Existing fallback (Loop 1 format → rewrite as polka_dot_patrol.json) |
| `docs/wonderlens_activity_demo_build_spec.md` | Source of truth for all schemas, API contracts, and UI layout |

---

## End-to-End Verification

```bash
# Terminal 1: Backend
cd backend && uv sync && uv run uvicorn server:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm install && npm run dev

# Test flow:
# 1. Open localhost:5173
# 2. Select preloaded dog photo, pick tier T0
# 3. Verify recipe generates — hook_line appears as first AI message
# 4. Type responses, verify branching (correct/incorrect paths work)
# 5. Stay silent twice to test graceful exit
# 6. Verify DB has session + turns logged:
#    sqlite3 backend/data/demo.db "SELECT * FROM sessions; SELECT * FROM turns;"
# 7. Start new session with ladybug photo, T1 — test polka_dot_patrol collection flow
# 8. Kill backend → restart → verify fallback recipe loads after 3 retries
# 9. Test TTS: verify audio plays, verify browser fallback when /api/tts returns 204
```

---

## Risk Areas

| Risk | Mitigation |
|------|------------|
| Gemini JSON mode may produce invalid JSON | Retry logic (3 attempts) + fallback recipes |
| 200ms Director timeout is tight for cold-start | Warm up client at startup; generous default plan fallback |
| Hook rule validation is heuristic | Simple pattern matching (V1); accept false negatives |
| Response matching (correct/incorrect) needs fuzzy logic | V1 uses case-insensitive keyword/substring; improve later |
| TTS adds latency per turn | Non-blocking audio playback; browser SpeechSynthesis fallback is instant |
| Demo photos needed | Use any CC0/stock images of target entities |
