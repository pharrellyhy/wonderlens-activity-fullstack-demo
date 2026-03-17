# Pre-generated Static Recipes for Demo Entities

## Problem

Each demo session runs a full LLM pipeline (~580ms on `/api/start`, ~200-400ms per `/api/turn`). Since the demo has only 5 fixed entities (dog, cat, dinosaur, ladybug, dandelion), every session generates fresh dialogue via the Script Agent LLM — adding latency and API cost for content that could be pre-authored and polished.

## Solution

Pre-generate complete, polished recipe JSON files for all 5 demo entities. Eliminate ALL LLM calls (Vision, Director, Script Agent) for demo sessions. Custom photo uploads continue using the live pipeline unchanged.

**Performance impact:** `/api/start` ~580ms → <5ms. `/api/turn` ~200-400ms → <1ms. Zero LLM API calls per demo session.

## Architecture

```
Demo entity (icon click) →
  /api/start: load recipe JSON → build SessionStateModel → return hook
  /api/turn:  recipe_loader maps (step, child_input) → TurnResponse (no LLM)

Custom photo (drag-and-drop) →
  /api/start: full pipeline (Vision + Director + Script + Visual) [unchanged]
  /api/turn:  Script Agent LLM per turn [unchanged]
```

---

## Implementation Steps

### Step 1: Extend Schemas (backward-compatible)

**`backend/schemas/voice_script.py`** — Add optional fields to `VoiceScript`:
- `synthesis_speech: str | None = None` — cat5 STEP_4_SYNTHESIS dialogue
- `early_exit_speech: str | None = None` — EARLY_EXIT dialogue
- Tone markers with defaults: `hook_tone`, `transition_tone`, `closing_tone`, `tomorrow_tone`, `synthesis_tone`, `early_exit_tone`

Add to `Round`:
- `tone_marker: str = "curious"` — tone for round prompt
- `on_wrong_photo: str | None = None` — cat5 wrong photo response

**`backend/schemas/session_state.py`** — Add to `SessionStateModel`:
- `is_pregenerated: bool = False` — flag for recipe-based sessions
- `recipe: ActivityRecipe | None = None` — stored recipe for turn lookups

All new fields have defaults, so existing JSON files remain valid.

### Step 2: Rename `fallbacks/` → `recipes/`

- `git mv backend/fallbacks backend/recipes`
- Update `backend/agents/pipeline.py`: `_FALLBACKS_DIR` → `_RECIPES_DIR`, rename `load_fallback()` → `load_recipe()`

### Step 3: Enrich Recipe JSON Files

Update all 5 recipes in `backend/recipes/` with new fields:
- `synthesis_speech` (cat5 only), `early_exit_speech` (all)
- Tone markers on each field and round
- `on_wrong_photo` on cat5 round entries
- Polish all dialogue for demo quality

Files: `mood_changer_dog.json`, `dream_whisperer_cat.json`, `time_machine_dinosaur.json`, `polka_dot_patrol.json`, `fluffy_expedition_dandelion.json`

### Step 4: New Module — `backend/recipe_loader.py`

#### `is_demo_entity(filename: str) -> bool`
Matches demo icon filenames: `dog.png`, `cat.png`, `dinosaur.png`, `ladybug.png`, `dandelion.png`.

#### `load_demo_recipe(activity_type: str) -> ActivityRecipe`
Loads recipe JSON from `backend/recipes/`, cached with `@lru_cache`.

#### `recipe_to_session_state(recipe, session_id, tier) -> tuple[SessionStateModel, TurnResponse]`
Builds SessionStateModel from recipe metadata without running any agents:
1. Derive `template_type` from `SCENARIO_CATEGORIES`
2. Build `creative_slots` from recipe metadata + scenario YAML defaults
3. Create state with `is_pregenerated=True`, `recipe=recipe`
4. Set `visual_frames` + `celebration_frame` from recipe
5. Build hook TurnResponse from `voice_script.hook_line`
6. Record hook in conversation_history, advance step

#### `resolve_turn_from_recipe(state, child_text, is_silent, photo_id) -> TurnResponse`
Maps current step to pre-authored dialogue:

| Step | Dialogue source | Acknowledgment |
|------|----------------|----------------|
| STEP_2_RULES/MISSION | `transition_line` | None |
| STEP_3_ROUND_N / COLLECT_N | `rounds[N-1].prompt` | Previous round's on_correct/incorrect/silence (if N > 1) |
| STEP_4_CELEBRATE / STEP_5_CELEBRATE | `closing_speech` | Last round's acknowledgment |
| STEP_4_SYNTHESIS (cat5) | `synthesis_speech` | Last round's acknowledgment |
| STEP_5_CLOSING / STEP_6_CLOSING | `tomorrow_hook` | None |
| EARLY_EXIT | `early_exit_speech` | None |

**Acknowledgment selection** (`_select_acknowledgment`):
- Silent → `on_silence`
- Child text matches any `correct_responses` (substring match) → `on_correct`
- Otherwise → `on_incorrect`

When acknowledgment exists, concatenate: `"{ack} {next_prompt}"`.

#### `resolve_wrong_photo_turn(state, photo_id) -> TurnResponse`
Cat5 only — returns `rounds[current].on_wrong_photo` or generic encouragement.

### Step 5: Modify `/api/start` in `backend/server.py`

After reading filename, branch on `is_demo_entity(filename)`:
- **Demo path:** `match_scenario()` → `load_demo_recipe()` → `recipe_to_session_state()` → generate cat5 round_items if needed → return response. No Vision/Director/Script/Visual agents.
- **Custom path:** Existing LLM pipeline unchanged.

### Step 6: Modify `/api/turn` and `/api/turn-speak` in `backend/server.py`

Replace all `_generate_turn_with_retry(script_agent, state)` calls with:
```python
if state.is_pregenerated:
    turn_response = resolve_turn_from_recipe(state, req.text, req.is_silent, req.photo_id)
else:
    turn_response = await _generate_turn_with_retry(script_agent, state)
```

Applies in 4 locations per endpoint:
1. EARLY_EXIT from silence
2. EARLY_EXIT from wrong photos
3. Wrong photo retry (cat5)
4. Main turn generation

For `/api/turn-speak`, pre-gen sessions bypass the streaming Script Agent entirely — go straight to TTS.

---

## Critical Files

| File | Change |
|------|--------|
| `backend/recipe_loader.py` | **NEW** — recipe loading + turn resolution |
| `backend/server.py` | Branch on `is_demo_entity` / `is_pregenerated` |
| `backend/schemas/voice_script.py` | Add synthesis_speech, early_exit_speech, tones |
| `backend/schemas/session_state.py` | Add is_pregenerated, recipe fields |
| `backend/agents/pipeline.py` | Update path from fallbacks/ to recipes/ |
| `backend/recipes/*.json` | Enriched with new fields + polished dialogue |

## Verification

1. Click each demo icon (dog/cat/dinosaur/ladybug/dandelion) → verify instant start, correct hook
2. Play through full sessions → verify round acknowledgments with branching
3. Stay silent twice → verify graceful exit with early_exit_speech
4. Pick wrong photo (cat5) → verify retry response
5. Drag-and-drop custom photo → verify full LLM pipeline still works
6. `uv run ruff check .` + `uv run ruff format .` + `uv run mypy .`
