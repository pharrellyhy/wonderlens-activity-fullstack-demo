# Plan: Immersive Character & Environment Sounds

## Context

The current audio system only has TTS voice and 10 fixed UI SFX cues that fire at predetermined game steps. There are no character-specific sounds (barks, purrs, roars) or environmental ambience, making the game feel mechanical. This plan adds a dynamic character & environment sound system where the LLM places sound cues contextually in each turn, and the frontend plays pre-recorded clips overlapping with TTS for an immersive experience.

**Design spec:** `docs/superpowers/specs/2026-03-28-immersive-character-sounds-design.md`

## Implementation Steps

### Step 1: Backend Data Layer — Sound Library
- Create `backend/data/character_sounds.yaml` with all 5 activities' sound definitions (IDs, categories, energy levels)
- Create `backend/character_sounds.py` with:
  - `load_character_sound_library()` — YAML loader with `@lru_cache`
  - `validate_character_sfx()` — validates cue IDs against activity whitelist, caps at 2 per turn
  - `get_sound_list_for_prompt()` — formats sound list for prompt injection
- **Files:** `backend/data/character_sounds.yaml` (new), `backend/character_sounds.py` (new)

### Step 2: Backend Schema Changes
- Add `CharacterSfxCue` Pydantic model to `backend/schemas/turn_response.py`
- Add `character_sfx: list[CharacterSfxCue]` field to `TurnResponse`
- **Files:** `backend/schemas/turn_response.py`

### Step 3: Script Agent Prompt Engineering
- Add character & environment sounds section to `backend/skills/script_turn.md` with timing slot instructions and guidelines
- Update `backend/agents/script_agent.py` to inject activity-specific sound list from `get_sound_list_for_prompt()` into the system prompt
- **Files:** `backend/skills/script_turn.md`, `backend/agents/script_agent.py`

### Step 4: Server Response Integration
- Update `_build_turn_response()` in `backend/server.py` to include `character_sfx` in JSON response
- Call `validate_character_sfx()` before including in response
- **Files:** `backend/server.py`

### Step 5: Placeholder Sound Assets
- Create directory structure: `frontend/public/sfx/character/{activity}/`
- Generate placeholder WAV files (~240 files: ~80 sounds × 3 variations) using `sox` or similar
- **Files:** `frontend/public/sfx/character/` (new directory tree)

### Step 6: Frontend `useCharacterSfx` Hook
- Create `frontend/src/hooks/useCharacterSfx.js` with:
  - `preload(activityType)` — prefetch all WAV files for the activity
  - Audio pool of 2-3 `Audio` elements for polyphonic playback
  - `playForTurn(cueList, callbacks)` — orchestrates intro/overlay/outro timing
  - Random variation selection (same pattern as `useSfxPlayer`)
  - Audio unlock participation
  - Volume at 0.4
- **Files:** `frontend/src/hooks/useCharacterSfx.js` (new)

### Step 7: Frontend Orchestration Wiring
- Update `frontend/src/hooks/useSessionOrchestration.js` to:
  - Import and initialize `useCharacterSfx`
  - Call `preload()` on session start
  - Wire character sounds into the turn playback flow (intro → TTS → overlay → outro)
  - Handle TTS-disabled case (intro → overlay → outro without TTS)
- **Files:** `frontend/src/hooks/useSessionOrchestration.js`

### Step 8: Backend Tests
- Unit tests for YAML loading, cue validation, prompt formatting
- Test invalid/hallucinated cue IDs are dropped
- Test cap of 2 cues per turn
- Test TurnResponse serialization with character_sfx
- **Files:** `backend/tests/` (new test files)

### Step 9: Integration Testing & Tuning
- Run full game sessions for each activity
- Verify character sounds appear in turn responses
- Test timing feels natural (intro → TTS → overlay → outro)
- Test with TTS enabled and disabled
- Run ruff check/format and mypy on changed backend files

## Key Files

| File | Action |
|------|--------|
| `backend/data/character_sounds.yaml` | Create |
| `backend/character_sounds.py` | Create |
| `backend/schemas/turn_response.py` | Modify |
| `backend/agents/script_agent.py` | Modify |
| `backend/skills/script_turn.md` | Modify |
| `backend/server.py` | Modify |
| `frontend/src/hooks/useCharacterSfx.js` | Create |
| `frontend/src/hooks/useSessionOrchestration.js` | Modify |
| `frontend/public/sfx/character/` | Create (assets) |

## Existing Code to Reuse

- `useSfxPlayer.js` pattern: variation selection, audio caching, unlock logic — mirror for `useCharacterSfx.js`
- `backend/tier_rules.yaml` loading pattern in existing code — mirror for `character_sounds.yaml` loader
- `ALLOWED_SFX` validation pattern in `recipe_assembler.py` — mirror for character sound validation
- `_strip_unsupported_tags()` in `tts.py` — reference for tag handling (but character sounds don't need text stripping)

## Verification

1. `uv run ruff check .` and `uv run ruff format .` — no lint/format errors
2. `uv run mypy .` — no type errors
3. `uv run pytest` — all tests pass including new character sound tests
4. Manual test: Start a mood_changer_dog session, verify:
   - Turn responses include `character_sfx` array in JSON
   - Frontend plays intro sounds before TTS
   - Overlay sounds play during TTS
   - Outro sounds play after TTS
   - Sounds have random variation selection
   - Volume is gentle (0.4)
   - UI SFX (wonder_chime, scene_woosh) still work independently
5. Test each of the 5 activities at least once
6. Test with TTS toggled off — character sounds should still play
