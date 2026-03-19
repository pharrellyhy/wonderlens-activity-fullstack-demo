# Plan: Turn-by-Turn LLM Generation with Entity-Agnostic Templates

## Context

The current architecture pre-generates the entire script upfront via the Script Agent (30-60s), then `/api/turn` is a pure recipe lookup (~5ms). This causes two problems: (1) high initial latency, and (2) rigid dialogue that ignores what the child actually says. The fix is to switch to turn-by-turn generation where the Script Agent generates only the next dialogue turn based on user input, template structure, and conversation state.

Reference: `docs/wonderlens_demo_activity_templates_v1.md`

## Architecture Decisions

1. **Director fills creative slots** (GPT-5.2, runs once) → **Script generates per-turn** (Gemini Flash, runs each turn)
2. **Gemini Flash** for per-turn Script Agent (~1-3s per turn)
3. **Pre-selected photo gallery** for Cat 5 collection rounds (child picks from curated options)
4. **Hybrid state**: server stores full state, client sends only `session_id + user_input`
5. **Retry once → graceful exit** with UI indicator on LLM failure
6. **System prompt carries structure**, only last 2-3 turns in messages

## Expected Latency

| Step | Before | After |
|------|--------|-------|
| `/api/start` | ~150s (vision + director + full script) | ~12s (vision 5s + director 5s + first turn 2s) |
| `/api/turn` | ~5ms (recipe lookup) | ~1-3s (Gemini Flash per turn) |

---

## Phase 1: New Pydantic Schemas

No behavior changes — pure additions.

### 1a. `backend/schemas/creative_slots.py` (NEW)

```python
class Cat1CreativeSlots(BaseModel):
    game_mechanic: Literal["mood_guessing", "true_or_silly", "voice_acting",
                           "storytelling_chain", "riddle_game", "sound_imitation"]
    metaphor: str
    role_title: str
    round_scenarios: list[str]
    escalation_axis: str
    observation_detail: str

class Cat5CreativeSlots(BaseModel):
    observation_angle: Literal["color", "shape", "texture", "size", "pattern", "function", "habitat"]
    collection_criterion: str
    collection_count: int  # 2-4
    mission_metaphor: str
    role_title: str
    synthesis_type: Literal["naming_story", "comparison_chart", "creative_narrative", "sorting_game"]
    stuck_hint: str
    naming_prompt: str

CreativeSlots = Cat1CreativeSlots | Cat5CreativeSlots
```

### 1b. `backend/schemas/turn_response.py` (NEW)

```python
class TurnResponse(BaseModel):
    dialogue: str
    tone_marker: str  # e.g. "excited", "curious"
    screen_widget: str
    screen_widget_params: dict
    screen_animation: str | None = None
    sfx_cue: str | None = None
```

### 1c. `backend/schemas/session_state.py` (NEW)

```python
class ConversationTurn(BaseModel):
    role: Literal["ai", "child"]
    text: str
    step: str
    round_number: int | None = None

class SessionStateModel(BaseModel):
    session_id: str
    tier: str
    template_type: Literal["cat1", "cat5"]
    activity_type: str
    current_step: str  # state machine value
    current_round: int = 0
    total_rounds: int = 3
    creative_slots: Cat1CreativeSlots | Cat5CreativeSlots
    conversation_history: list[ConversationTurn] = []
    collected_photos: list[str] = []  # Cat 5 photo IDs
    consecutive_silence: int = 0
    turn_count: int = 0
    status: Literal["active", "completed", "exited", "error"] = "active"
    # Vision/entity context
    entity_name: str = ""
    entity_attributes: list[str] = []
    entity_category: str = ""
    scene: str = ""
    ib_key_concepts: list[str] = []
    photo_url: str = ""
```

### 1d. `backend/schemas/composition_plan.py` (MODIFY)

Add `creative_slots` and `template_type` fields to `CompositionPlan`:
```python
template_type: Literal["cat1", "cat5"] = "cat1"
creative_slots: Cat1CreativeSlots | Cat5CreativeSlots | None = None
```

### 1e. `backend/schemas/__init__.py` (MODIFY)

Export all new models.

---

## Phase 2: State Machine Engine

### `backend/state_machine.py` (NEW)

Template state machine that determines the next step and maps steps to widgets.

**Cat 1 states**: `STEP_1_HOOK` → `STEP_2_RULES` → `STEP_3_ROUND_1..N` → `STEP_4_CELEBRATE` → `STEP_5_CLOSING` → `ENDED`

**Cat 5 states**: `STEP_1_HOOK` → `STEP_2_MISSION` → `STEP_3_COLLECT_1..N` → `STEP_4_SYNTHESIS` → `STEP_5_CELEBRATE` → `STEP_6_CLOSING` → `ENDED`

**Both**: `EARLY_EXIT` → `ENDED`

Key functions:
- `next_step(current_step, template_type, current_round, total_rounds) -> str`
- `is_terminal(step) -> bool`
- `step_needs_user_input(step) -> bool` (STEP_3 rounds do; STEP_4/5/6 don't — they auto-advance)
- `get_screen_frame(step, template_type, creative_slots, context) -> ScreenFrame` — replaces Visual Agent for most cases

**Auto-advancing steps**: After the child responds to a round, the server generates the AI response AND checks if the next step auto-advances (celebration, closing). If so, it chains those steps without waiting for user input. This means some turns may return multiple dialogue chunks (the round response + celebration + closing). Alternatively, return one at a time and let the frontend call `/api/turn` with empty input to advance through non-interactive steps.

**Decision**: Return one step at a time. Frontend calls `/api/turn` with `text=""` and `is_silent=false` to advance non-interactive steps. Simpler, and each step gets its own TTS/screen frame.

---

## Phase 3: Director Expansion + New Script Agent

### 3a. `backend/agents/director.py` (MODIFY)

- Keep OpenAI GPT-5.2
- Expand output to include `creative_slots` and `template_type` in `CompositionPlan`
- Update `_default_plan()` to include default creative slots per activity type
- Increase `director_max_tokens` from 500 → 1000

### 3b. `backend/skills/director.md` (MODIFY)

- Add creative slot definitions from template doc (sections 4.1 and 5.1)
- Add mechanic/angle selection logic guidance (section 4.2 mechanic selection, section 5.1)
- Update output format to include `creative_slots` and `template_type`
- Add examples of filled creative slots

### 3c. `backend/agents/script_agent.py` (REWRITE)

Complete rewrite — Gemini Flash, per-turn generation:

- **Input**: `SessionStateModel` (contains everything needed)
- **Output**: `TurnResponse` (single turn)
- **LLM**: Gemini Flash via `google.genai` with JSON mode
- **System prompt**: assembled from template + step instructions + creative slots + tier rules + entity context
- **Messages**: only last 2-3 turns from `conversation_history`
- **Config**: `script_turn_timeout_ms: 5000`, `script_turn_max_tokens: 500`
- **Error handling**: raise `ScriptAgentError` on failure (caller handles retry)

### 3d. `backend/skills/script_turn.md` (NEW)

New modular system prompt for per-turn generation. Structure per template doc section 6:
1. Role & Persona (Kido)
2. Tier Rules (injected)
3. Current step instructions (injected based on `current_step`)
4. Creative slots (injected from Director)
5. Vision context (entity, attributes, scene)
6. Output format (TurnResponse JSON)
7. Conversation state summary

### 3e. `backend/skills/step_instructions/` (NEW DIRECTORY)

One file per template step with the "LLM must do" instructions from the template doc:
- `cat1_step1_hook.md`, `cat1_step2_rules.md`, `cat1_step3_round.md`, `cat1_step4_celebrate.md`, `cat1_step5_closing.md`
- `cat5_step1_hook.md`, `cat5_step2_mission.md`, `cat5_step3_collect.md`, `cat5_step4_synthesis.md`, `cat5_step5_celebrate.md`, `cat5_step6_closing.md`
- `early_exit.md`

---

## Phase 4: Server Endpoint Changes

### `backend/server.py` (MAJOR REWRITE)

**SessionState** → replace with `SessionStateModel`

**`POST /api/start` new flow**:
1. Read photo + tier (same)
2. Vision analysis with 5s timeout (same)
3. Match scenario + determine `template_type` from category mapping
4. Run Director Agent (expanded, fills creative slots) — ~5s
5. Create `SessionStateModel` with creative slots, `current_step="STEP_1_HOOK"`
6. Run Script Agent for hook turn (Gemini Flash) — ~2s
7. Add hook to conversation history, advance to next step
8. Return: `{ session_id, vision_result, first_turn, activity_type, template_type, session_state }`
9. **No longer returns full `recipe`**

**`POST /api/turn` new flow**:
1. Look up `SessionStateModel`
2. Handle silence (consecutive_silence >= 2 → set step to `EARLY_EXIT`, generate graceful exit via Script Agent)
3. Record child input in `conversation_history`
4. Advance state machine: `next_step()`
5. For Cat 5 collection: record `photo_id` in `collected_photos`
6. Call Script Agent (Gemini Flash) for next turn — ~1-3s
7. Record AI response in `conversation_history`
8. Trim history to last 6 entries (3 exchanges) for prompt injection
9. Get screen frame from state machine
10. Return: `{ turn: { dialogue, tone_marker, screen_frame, sfx, response_type }, session_state, latency_ms }`

**Error handling in `/api/turn`**:
- Script Agent fails → retry once
- Still fails → hardcoded graceful exit, set `status="error"`, return `error_exit: true`

**`TurnRequest` model**: add optional `photo_id: str | None = None`

**Remove**: `_matches_correct()` helper, recipe-based turn logic

### `backend/config.yaml` (MODIFY)

```yaml
script_turn_timeout_ms: 5000
script_turn_max_tokens: 500
director_max_tokens: 1000
```

### `backend/config.py` (MODIFY)

Add `script_turn_timeout_ms` and `script_turn_max_tokens` settings.

---

## Phase 5: Pipeline Simplification

### `backend/agents/pipeline.py` (REWRITE)

- Rename `generate_recipe()` → `initialize_session()`
- New signature: `async def initialize_session(context, session_id) -> tuple[CompositionPlan, TurnResponse]`
- Flow: Director → create state → Script (hook turn) → return
- Fallback: Director fails → `_default_plan()` with default creative slots. Script fails for hook → hardcoded generic hook

### `backend/agents/recipe_assembler.py` (DEPRECATE)

Not used in new architecture. Keep file but mark deprecated.

### `backend/agents/visual_agent.py` (SIMPLIFY)

Logic absorbed into `state_machine.py`'s `get_screen_frame()`. Keep file with simplified helper if needed.

---

## Phase 6: Frontend Changes

### 6a. `frontend/src/utils/api.js` (MODIFY)

- `startSession`: expect `{ session_id, first_turn, template_type, session_state }` (no `recipe`)
- `sendTurn`: add optional `photoId` param → `{ session_id, text, is_silent, photo_id }`

### 6b. `frontend/src/hooks/useConversation.js` (MODIFY)

- Remove `recipe` state entirely
- Add `templateType` state
- `start()`: use `data.session_state.total_rounds` instead of `data.recipe.voice_script.rounds.length`
- Add `sendPhotoCollection(photoId)` for Cat 5
- Handle `data.turn.error_exit` flag
- Non-interactive steps: after receiving celebration/closing response_type, auto-call `/api/turn` with empty text to advance

### 6c. `frontend/src/hooks/useSessionOrchestration.js` (MODIFY)

- Pass through `templateType`
- Expose `errorExit` state for UI indicator
- Handle auto-advance for non-interactive steps (after TTS finishes for celebration, auto-send empty turn)

### 6d. `frontend/src/components/PhotoGallery.jsx` (NEW)

Cat 5 collection gallery component:
- Shows 3-5 curated candidate photos
- Child taps to "collect" one
- Dims already-collected photos
- Shows progress (e.g., "2 of 3 collected")
- Only rendered when `templateType === 'cat5'` and step is `STEP_3_COLLECT_*`

### 6e. `frontend/public/photos/collection/` (NEW DIRECTORY)

Add 5-8 curated photos for Cat 5 collection (leaves, textures, shapes, etc.)

### 6f. `frontend/src/App.jsx` (MODIFY)

- Remove recipe from footer debug info
- Add error exit indicator (gentle message when `status === 'error'`)
- Conditionally render PhotoGallery in DeviceScreen during Cat 5 collection

### 6g. `frontend/src/components/ConversationPanel.jsx` (MODIFY)

- When `error_exit` is true on a message, show subtle warning indicator (icon or colored border)

---

## Verification

1. **Backend unit tests**: Test state machine transitions for both Cat 1 and Cat 5 (all paths including early exit)
2. **Schema tests**: Validate creative slot models parse correctly
3. **Integration test**: Start session → verify Director fills creative slots → verify first turn (hook) follows hook rule
4. **Manual E2E**:
   - Start Cat 1 session with dog photo → verify hook → play 3 rounds → verify celebration → closing
   - Start Cat 5 session with dandelion photo → verify hook → mission → collect 3 photos from gallery → synthesis → closing
   - Test silence: 2 consecutive silences → graceful exit
   - Test LLM failure: kill network mid-session → verify graceful exit with UI indicator
5. **Latency check**: `/api/start` < 15s, `/api/turn` < 5s
6. **Run linting**: `uv run ruff check . && uv run ruff format . && uv run mypy .`
