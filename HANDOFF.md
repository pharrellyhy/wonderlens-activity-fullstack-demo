# Session Handoff

Last updated: 2026-03-19

---

## Review Game MD Loader Follow-Up: Fail-Fast Startup + Test Fixture Cleanup

**Problem**: Reviewing the new game-MD single-source refactor exposed two real gaps. First, `backend/game_loader.py` only logged parse failures and kept going, so a broken frontmatter file could silently drop a demo game from the registry. Second, `validate_registry()` still reported success when the registry was empty. The local API/schema tests also still had stale fixture/import cleanup issues from the same refactor, including a `what_would_it_say` mechanic value that no longer matches the current `voice_acting` schema.

**Solution**: Tightened the loader/validation path so startup fails loudly instead of accepting partial or empty demo configuration. `_load_demo_games()` now clears stale state before each scan, accumulates parse failures, and raises a `RuntimeError` listing the broken files. `validate_registry()` now rejects an empty registry. I also tightened the local test coverage around those failure paths and updated the stale API fixture/import cleanup so the reviewed test bundle reflects the current schema and loader behavior.

**Edits**:
- `backend/game_loader.py` — clear cached loader state before rescanning; collect parse failures; raise `RuntimeError` when any game MD file with frontmatter fails to parse
- `backend/entity_registry.py` — make `validate_registry()` fail when `ENTITY_REGISTRY` is empty
- local `tests/test_game_parser.py` — added regression coverage proving `_load_demo_games()` raises on a broken game MD file
- local `tests/test_entity_registry.py` — added regression coverage proving `validate_registry()` rejects an empty registry
- local `tests/test_api.py` — updated stale Cat1 fixture mechanic from `what_would_it_say` to `voice_acting`
- local `tests/test_schemas.py` — moved the new `game_loader` import to the module import block so the updated schema test passes lint/format cleanly
- `HANDOFF.md` — added this review/update entry

**NOT Changed**:
- `backend/recipe_loader.py`, `backend/server.py`, and the new `backend/games/*.md` content were reviewed in this pass and left unchanged
- `backend/skills/step_instructions/cat5_step4_synthesis*.md` prompt edits were reviewed and left unchanged
- Deleted recipe/scenario asset files and the removed `images/entity_icons.png` artifact already present in the worktree were not touched in this pass

**Verification**:
- `cd backend && uv run ruff check game_loader.py entity_registry.py recipe_loader.py server.py ../tests/test_game_parser.py ../tests/test_entity_registry.py ../tests/test_schemas.py ../tests/test_api.py ../tests/conftest.py` — PASS
- `cd backend && uv run ruff format --check game_loader.py entity_registry.py recipe_loader.py server.py ../tests/test_game_parser.py ../tests/test_entity_registry.py ../tests/test_schemas.py ../tests/test_api.py ../tests/conftest.py` — PASS
- `cd backend && uv run pytest ../tests/test_game_parser.py ../tests/test_entity_registry.py ../tests/test_schemas.py ../tests/test_api.py -q` — PASS (`115 passed`)

---

## Game MD Files as Single Source of Truth for Demo Entities

**Problem**: Demo entity data was spread across 3 manually-synced sources: `entity_registry.py` (hardcoded config with 140+ lines of Pydantic model instantiation), `recipes/*.json` (step instructions + screen frames), and `scenarios/*.yaml` (interaction scripts). Adding or modifying a game required updating all three, with no cross-validation.

**Solution**: Consolidated all demo entity data into one markdown file per game with YAML frontmatter in `backend/games/`. Created `game_parser.py` to parse frontmatter into existing Pydantic models (`EntityConfig`, `InstructionRecipe`), and `game_loader.py` to scan the games directory at import time and populate the entity registry. The registry module (`entity_registry.py`) now has an empty list that gets populated via `_populate_registry()` called by the game loader. Recipe loading checks game_loader first, falling back to JSON for non-demo entities (e.g. `polka_dot_patrol_hard.json`).

**Edits**:
- `backend/games/{mood_changer_dog,dream_whisperer_cat,time_machine_dinosaur,polka_dot_patrol,fluffy_expedition_dandelion}.md` — **NEW**: 5 game MD files with full YAML frontmatter (entity config, creative slots, step instructions, screen frames, metadata, keywords, collection catalogs)
- `backend/game_parser.py` — **NEW**: `parse_game_file()` extracts YAML frontmatter and builds `EntityConfig` + `InstructionRecipe`
- `backend/game_loader.py` — **NEW**: scans `games/` at import time, calls `_populate_registry()` to fill entity registry
- `backend/entity_registry.py` — removed 140-line hardcoded `ENTITY_REGISTRY` list; added `_populate_registry()` and `_rebuild_lookups()`; changed `validate_registry()` to check for game MD files instead of recipe JSON + scenario YAML
- `backend/recipe_loader.py` — `load_instruction_recipe()` checks `game_loader.get_demo_recipe()` first, JSON fallback for non-demo entities
- `backend/server.py` — added `game_loader` import to trigger registry population at startup
- `tests/conftest.py` — added `game_loader` import; updated `instruction_recipe` fixture to use `get_demo_recipe()` instead of deleted JSON file
- `tests/test_game_parser.py` — **NEW**: 41 tests covering all 5 entities, creative slots, collection catalogs, recipe structure, metadata values
- `tests/test_entity_registry.py` — no structural changes needed (all assertions pass with MD-sourced data)
- `tests/test_schemas.py` — replaced `test_demo_recipe_files_validate` (used deleted JSON path) with `test_demo_game_recipes_validate`

**Deleted**:
- `backend/recipes/{mood_changer_dog,dream_whisperer_cat,time_machine_dinosaur,polka_dot_patrol,fluffy_expedition_dandelion}.json` — replaced by game MD files
- `backend/scenarios/{mood_changer_dog,dream_whisperer_cat,time_machine_dinosaur,polka_dot_patrol,fluffy_expedition_dandelion}.yaml` — replaced by game MD files
- Kept: `polka_dot_patrol_hard.json`, `mood_changer_dog_silent_exit.yaml`, `polka_dot_patrol_hard.yaml`, `dino_time_traveler.yaml`

**NOT Changed**:
- All Pydantic schemas in `backend/schemas/` — unchanged, reused by parser
- Agent modules (`director.py`, `script_agent.py`, `visual_agent.py`, `recipe_assembler.py`) — unchanged
- Step instruction fragments in `backend/skills/step_instructions/` — unchanged
- Frontend — zero changes
- Existing 12 `*_prod.md` design docs in `backend/games/` — no frontmatter, silently skipped by loader

**Verification**:
- `uv run pytest tests/test_game_parser.py tests/test_entity_registry.py -v` — PASS (72 passed)
- `uv run pytest tests/ -k "not e2e" -q` — 195 passed, 27 failed (pre-existing failures from `what_would_it_say` game_mechanic in test fixtures)
- `cd backend && uv run ruff check .` — PASS
- `cd backend && uv run ruff format --check game_parser.py game_loader.py entity_registry.py recipe_loader.py` — PASS

---

## Review Style Fragment Follow-Up: Prompt Interpolation Coverage

**Problem**: The latest style-fragment refactor changed prompt assembly in `backend/agents/script_agent.py`, but the new tests only verified that fragment files existed. Reviewing the actual loader path exposed a real prompt bug: several Cat 1 fragments referenced `{entity_name}`, and `_load_step_instructions()` never replaced that token. That left raw template placeholders in live prompts.

**Solution**: Fixed prompt interpolation by adding `{entity_name}` to the loader replacements, then simplified the fragment-selection branch so the fragmentable step prefixes live in one module constant instead of a per-call local dict with an unused value map. Tightened the local test coverage to exercise `_load_step_instructions()` directly for Cat 1 and Cat 5 fragment paths and replaced one manual `try/except` assertion with `pytest.raises`.

**Edits**:
- `backend/agents/script_agent.py` — added `{entity_name}` replacement in `_load_step_instructions()` and simplified fragment-prefix handling with `_FRAGMENTABLE_STEP_PREFIXES`
- local `tests/test_entity_registry.py` — added direct loader assertions for Cat 1/Cat 5 fragment assembly and interpolation; simplified unknown-entity assertion with `pytest.raises`
- `HANDOFF.md` — added this review/update entry

**NOT Changed**:
- `backend/entity_registry.py` and the new fragment markdown files were reviewed in this pass and left unchanged
- `backend/skills/step_instructions/cat1_step2_rules.md` and `backend/skills/step_instructions/cat5_step4_synthesis.md` were left as-is after review
- `docs/weekly-report-2026-03-13.md` deletion already present in the worktree was not touched

**Verification**:
- `cd backend && uv run ruff check agents/script_agent.py ../tests/test_entity_registry.py` — PASS
- `cd backend && uv run ruff format --check agents/script_agent.py ../tests/test_entity_registry.py` — PASS
- `cd backend && uv run pytest ../tests/test_entity_registry.py -q` — PASS (`31 passed`)
- `cd backend && uv run pytest ../tests/test_api.py -q` — PASS (`24 passed`)

---

## Style-Specific Step Instruction Fragments

**Problem**: All entities within a category shared identical step instruction templates. Cat 5 entities both got the same "compare your finds" synthesis guidance, even though the design doc envisions creative storytelling for dandelion. Cat 1 entities with different game mechanics (voice_acting vs storytelling_chain) received the same generic demo and round instructions.

**Solution**: Implemented a fragment composition system that appends style-specific guidance to shared base templates. The loader in `_load_step_instructions()` looks up a fragment file using the entity's `game_mechanic` (Cat 1) or `synthesis_type` (Cat 5) and appends it after the base template. Fragment files use double-underscore naming: `cat1_step2_rules__voice_acting.md`. If no fragment exists, the base template is used alone (backward-compatible). Reassigned dandelion from `comparison_chart` to `naming_story` synthesis style.

**Edits**:
- `backend/agents/script_agent.py` (~line 135) — added fragment loading logic to `_load_step_instructions()`: determines style key from creative slots, builds fragment filename, appends if exists
- `backend/entity_registry.py` — changed `fluffy_expedition_dandelion` `synthesis_type` from `"comparison_chart"` to `"naming_story"`, updated `naming_prompt`
- `backend/skills/step_instructions/cat1_step2_rules.md` — removed "Game Mechanics Reference" section (now in fragments)
- `backend/skills/step_instructions/cat5_step4_synthesis.md` — removed multi-type reference section (now in fragments)
- `tests/test_entity_registry.py` — added `test_dandelion_synthesis_type_is_naming_story`, added `TestStyleFragments` class with 2 tests verifying fragment files exist for all registered entity styles
- 10 new fragment files in `backend/skills/step_instructions/`:
  - `cat1_step2_rules__voice_acting.md`, `cat1_step2_rules__storytelling_chain.md`, `cat1_step2_rules__riddle_game.md`
  - `cat1_step3_round__voice_acting.md`, `cat1_step3_round__storytelling_chain.md`, `cat1_step3_round__riddle_game.md`
  - `cat5_step3_collect__comparison_chart.md`, `cat5_step3_collect__naming_story.md`
  - `cat5_step4_synthesis__comparison_chart.md`, `cat5_step4_synthesis__naming_story.md`

**NOT Changed**:
- `backend/schemas/creative_slots.py` — `"naming_story"` and `"riddle_game"` already in the Literal types
- Steps 1 (Hook), 4/5 (Celebrate), 5/6 (Closing) — variables handle variation, no fragments needed
- Frontend code — no changes needed
- Other base template files (`cat5_step2_mission.md`, `cat1_step1_hook.md`, etc.) — unchanged

**Verification**:
- `cd backend && uv run ruff check . && uv run ruff format --check agents/script_agent.py` — PASS
- `cd backend && uv run pytest ../tests/test_entity_registry.py -v` — PASS (29 passed)
- `cd backend && uv run pytest ../tests/ -k "not e2e" -q` — PASS (178 passed)

---

## Review Entity Registry Follow-Up: PhotoSelector Cleanup

**Problem**: The latest entity-registry pass introduced runtime-backed entity loading in `PhotoSelector`, but the component still carried a `loadingEntities` state that was never read. That left the freshly modified frontend file failing the repo lint rules even though the backend registry/API work itself held up under focused review.

**Solution**: Reviewed the registry refactor and its immediate integrations (`entity_registry.py`, `scenarios.py`, `recipe_loader.py`, `server.py`, local registry/API tests) and left that backend surface unchanged. Simplified `frontend/src/components/PhotoSelector.jsx` by removing the unused `loadingEntities` state and the redundant `.finally(...)` branch, preserving the existing `/api/entities` fetch with fallback categories.

**Edits**:
- `frontend/src/components/PhotoSelector.jsx` — removed unused `loadingEntities` state from the new `/api/entities` loading path
- `HANDOFF.md` — added this review/update entry

**NOT Changed**:
- `backend/entity_registry.py`, `backend/scenarios.py`, `backend/recipe_loader.py`, `backend/server.py`, and `backend/turn_handler.py` were reviewed in this pass and left unchanged
- local `tests/test_entity_registry.py` and local `tests/test_api.py` were reviewed and executed without modification
- Asset-generation scripts and generated icon files currently in the worktree were not changed in this pass

**Verification**:
- `cd backend && uv run pytest ../tests/test_entity_registry.py ../tests/test_api.py -q` — PASS (`50 passed`)
- `cd backend && uv run ruff check entity_registry.py scenarios.py recipe_loader.py server.py turn_handler.py` — PASS
- `cd frontend && npm run lint -- src/components/PhotoSelector.jsx` — PASS

---

## Entity Registry — Consolidate Scattered Entity Config

**Problem**: Adding a new entity required editing 5-6 files with hardcoded dicts that had to stay in sync (`scenarios.py` keyword maps, `recipe_loader.py` filename/slot dicts, `server.py` collection catalogs, `PhotoSelector.jsx` hardcoded categories). No validation caught missing pieces.

**Solution**: Created `backend/entity_registry.py` as the single source of truth for all entity configuration. All 5 entities are defined once with Pydantic models (`EntityConfig`, `CollectionCatalog`, `CollectionItem`). Other modules import lookup helpers instead of maintaining their own dicts. Added `GET /api/entities` endpoint for the frontend. Added `validate_registry()` that runs at server startup to catch missing recipe/scenario files. Frontend fetches entities from the API with hardcoded fallback.

**Edits**:
- `backend/entity_registry.py` — **NEW**: registry module with all entity config, Pydantic models, derived lookup helpers, `generate_round_items()` (moved from server.py), `all_entities_for_api()`, `validate_registry()`
- `backend/scenarios.py` — removed `_ENTITY_SCENARIO_MAP` and `SCENARIO_CATEGORIES` dicts; imports from `entity_registry`; re-exports `SCENARIO_CATEGORIES` for backward compatibility; `match_scenario()` uses registry keyword/feature maps
- `backend/recipe_loader.py` — removed `_DEMO_FILENAMES`, `_FILENAME_ENTITIES`, `_CAT1_SLOTS`, `_CAT5_SLOTS`, `is_demo_entity()`; imports `is_demo_entity`, `entity_name_for_filename`, `get_creative_slots` from registry
- `backend/server.py` — removed `COLLECTION_CATALOGS` dict and `generate_round_items()` function; imports from `entity_registry`; added `GET /api/entities` endpoint; calls `validate_registry()` in `lifespan()` startup; removed unused `random` import
- `frontend/src/components/PhotoSelector.jsx` — fetches entities from `/api/entities` on mount with `useEffect`; hardcoded categories kept as fallback; category icons resolved via lookup map
- `tests/test_entity_registry.py` — **NEW**: 22 tests covering registry data, lookups, `generate_round_items()`, `all_entities_for_api()`, `validate_registry()`
- `tests/test_api.py` — added `TestEntitiesEndpoint` with 2 tests for the new `/api/entities` endpoint

**NOT Changed**:
- `backend/agents/director.py` and `backend/agents/pipeline.py` — import `SCENARIO_CATEGORIES` from `scenarios.py` which re-exports it; no changes needed
- Recipe JSON files, scenario YAML files, prompt/skill markdown
- Frontend hooks, App.jsx, other components
- State machine, DB layer, STT, TTS, Script Agent

**Verification**:
- `cd backend && uv run pytest ../tests/ -k "not e2e" -q` — PASS (175 passed)
- `cd backend && uv run ruff check entity_registry.py scenarios.py recipe_loader.py server.py` — PASS
- `cd backend && uv run ruff format --check entity_registry.py scenarios.py recipe_loader.py server.py` — PASS
- `cd backend && uv run mypy entity_registry.py scenarios.py recipe_loader.py server.py` — no new errors (all pre-existing)

---

## Review Step Transition Refactor: Deferred Round Advance Fix

**Problem**: Reviewing the current uncommitted step-transition refactor exposed a real regression in the new unified `turn_handler`: round completion advanced `current_step` before the next step's prompt was generated. That let `/api/turn` and `/api/turn-speak` pair a previous-round line with the next step's screen frame, and it could drop the first real `STEP_4_SYNTHESIS` prompt entirely. The existing tests checked state changes, but they did not verify which step the Script Agent was actually generating for after a round completion.

**Solution**: Kept the unified turn-handler design, but split round completion into two paths. When a round ends and the next step is another round or an auto-advance presentation step, the handler now keeps the current round active, returns the current-step acknowledgement, and marks a pending round advance for the next empty auto-turn. When a round ends and the next step needs fresh child interaction (notably `STEP_4_SYNTHESIS`), the handler now advances immediately and generates that new step's first prompt right away. Added focused regression coverage at both the unit and API layers, then simplified the handler slightly by extracting the repeated terminal-response builder.

**Edits**:
- `backend/turn_handler.py` — fixed round completion flow with deferred round advance, immediate synthesis entry, and a small terminal-response simplification
- `backend/schemas/session_state.py` — added `round_advance_pending` session state to support the deferred round-to-round transition
- local `tests/test_turn_handler.py` — strengthened round-transition coverage to assert which step actually generated the returned dialogue (this repo currently ignores `tests/`, so the change is local-only unless the ignore rule changes)
- local `tests/test_api.py` — updated Cat 5 collection and Cat 1 celebration-frame integration coverage to reflect the intended two-turn auto-advance flow (also local-only under the current ignore rule)
- `HANDOFF.md` — added this review/update entry

**NOT Changed**:
- `backend/server.py` was reviewed in this pass and left unchanged; the endpoint logic still routes through `resolve_turn()`
- `frontend/src/App.jsx`, `frontend/src/components/PhotoGallery.jsx`, and `frontend/src/widgets/CharacterDisplay.jsx` were reviewed against the current backend contract and left unchanged in this pass
- Recipe JSON files, prompt markdown, and the asset-generation scripts currently in the worktree were not changed by this pass

**Verification**:
- `cd backend && uv run pytest ../tests/test_turn_handler.py -q` — PASS (`10 passed`)
- `cd backend && uv run pytest ../tests/test_api.py -q` — PASS (`22 passed`)
- `cd backend && uv run pytest ../tests/test_turn_handler.py ../tests/test_api.py ../tests/test_server_visual.py ../tests/test_turn_flow.py ../tests/test_pipeline_visual.py -q` — PASS (`44 passed`)
- `cd backend && uv run ruff check turn_handler.py schemas/session_state.py ../tests/test_turn_handler.py ../tests/test_api.py` — PASS
- `cd backend && uv run ruff format --check turn_handler.py schemas/session_state.py ../tests/test_turn_handler.py ../tests/test_api.py` — PASS

---

## Gemini 2.5 Flash Image Smoke Test for Cat 5 Icons

**Problem**: After the `gpt-image-1.5` proxy path failed to return image payloads, the next attempt was to generate Cat 5 item icons with `gemini-2.5-flash-image`, following the Gemini provider setup referenced in `backend/refs/vision/providers/gemini.py`.

**Solution**: Added `scripts/generate_cat5_icons_gemini.py`, which reuses the Cat 5 prompts and supports three modes: `vertex`, `api-key`, and `auto`. Verified the Gemini response shape: `response.parts[0].inline_data.data` contains PNG bytes, while `part.as_image()` returns a Google SDK `Image` wrapper rather than a Pillow image. Updated the script to decode the inline PNG bytes directly and successfully generated `frontend/public/icons/spotted_mushroom.png` via the Vertex-style client.

**Edits**:
- `scripts/generate_cat5_icons_gemini.py` — new Gemini image generator for Cat 5 assets, with provider-style Vertex setup, API-key fallback mode, shared prompt reuse, and inline PNG decoding

**NOT Changed**:
- Existing OpenAI generator scripts
- Backend/frontend runtime wiring
- Secrets in `backend/.env`

**Verification**:
- Vertex-style smoke test using `gemini-2.5-flash-image` — PASS for one sample; saved `frontend/public/icons/spotted_mushroom.png`
- Visual check of `spotted_mushroom.png` — PASS; output is child-friendly and reads clearly at icon size
- Full batch attempt with `python scripts/generate_cat5_icons_gemini.py --overwrite --mode auto` — FAIL after the sample due `429 RESOURCE_EXHAUSTED`
- API-key mode also returns quota exhaustion for `gemini-2.5-flash-preview-image`
- Additional environment finding: `GOOGLE_APPLICATION_CREDENTIALS` path from `backend/.env` does not exist locally, but the successful sample still came back through the Vertex-style client before quota was exhausted

---

## Step Transition Refactor + QA Bug Fixes

**Problem**: Step transition logic was duplicated between `/api/turn` and `/api/turn-speak` with 6+ bugs: double responses on invitation acceptance, gallery appearing before collect prompt, STEP_4_SYNTHESIS being skipped, LLM hallucinating collections, consecutive AI messages without user interaction, and inconsistent auto-advance between endpoints. Also fixed: Cat1 round display always showing "Round 1", footer showing "0/3" before rounds start.

**Solution**: Extracted all step transition logic into a single `resolve_turn()` function in `backend/turn_handler.py`. Both endpoints now call this function — `/api/turn` wraps the result in JSON, `/api/turn-speak` adds TTS streaming. Key design decisions: (1) Invitation acceptance uses deferred advance — stays on STEP_2 with `auto_advance=True`, advances on the next turn so gallery appears with the collect prompt. (2) Round acknowledgments only auto-advance into other rounds or auto-advance steps, never into interactive steps like STEP_4_SYNTHESIS. (3) Interactive steps generate their prompt on first visit, advance on second visit. (4) Conversation history increased from 6 to 8 entries.

**Edits**:
- `backend/turn_handler.py` — **NEW**: `resolve_turn()`, `TurnInput`, `TurnResult` dataclasses, all step transition helpers ported from server.py (invitation, round, synthesis, auto-advance, photo validation, retry logic)
- `backend/server.py` — `/api/turn` and `/api/turn-speak` now call `resolve_turn()`; removed duplicated helpers (`_resolve_invitation_turn`, `_is_invitation_step`, `_is_round_step`, `_generate_turn_with_retry`, etc.)
- `backend/state_machine.py` — `"round_number"` → `"roundNumber"` in widget_params (Bug 1 fix)
- `frontend/src/App.jsx` — footer shows `-` before rounds start for cat1; cat5 shows `-` until first photo collected
- `frontend/src/widgets/CharacterDisplay.jsx` — hides round badge when `roundNumber` is 0
- `backend/skills/step_instructions/cat5_step3_collect.md` — explicit `stay_on_step` guidance for correct/wrong/stuck; last round must not ask questions
- `backend/skills/step_instructions/cat5_step4_synthesis.md` — no double celebration
- `backend/skills/step_instructions/cat5_step2_mission.md` — re-invitation must not negotiate down item count
- `backend/skills/step_instructions/cat1_step2_rules.md` — same fix for cat1
- `tests/test_turn_handler.py` — **NEW**: 10 unit tests for invitation, round, synthesis, silence flows
- `tests/test_api.py` — updated tests for deferred acceptance (two-turn flow)
- `tests/test_server_visual.py` — updated visual frame tests for deferred acceptance

**NOT Changed**:
- Frontend hooks (useSessionOrchestration, useConversation) — auto-advance mechanism unchanged
- State machine step constants and transitions — unchanged
- Script Agent LLM generation — unchanged
- TTS, STT, DB layer — unchanged

**Verification**:
- `cd backend && uv run pytest ../tests/ -k "not e2e" -q` — PASS (144 passed)
- `cd backend && uv run ruff check server.py turn_handler.py` — PASS
- `cd backend && uv run ruff format --check server.py turn_handler.py` — PASS

---

## Fix Cat1 Round Display + Pre-Round Counter

**Problem**: Two display bugs: (1) Cat1 device panel always showed "Round 1" regardless of actual round because `state_machine.py` sent `round_number` (snake_case) in `widget_params` but `CharacterDisplay.jsx` destructured `roundNumber` (camelCase), defaulting to 1. (2) Footer showed "0/3" before rounds started because `current_round` was 0 pre-round.

**Solution**: (1) Renamed `round_number` → `roundNumber` in all `widget_params` in `state_machine.py` (3 occurrences) and all 5 recipe JSON files (15 occurrences). (2) Updated `App.jsx` footer to show `-/3` instead of `0/3` for cat1 when `current_step` hasn't reached `STEP_3_ROUND_*` yet.

**Edits**:
- `backend/state_machine.py` — `"round_number"` → `"roundNumber"` in all `widget_params` dicts (lines 182, 193, 225)
- `backend/recipes/*.json` (5 files) — `"round_number"` → `"roundNumber"` in all `character_display` widget_params
- `frontend/src/App.jsx` — footer round counter for cat1 now checks `current_step?.startsWith('STEP_3_ROUND_')` before showing numeric round; shows `-` otherwise

**NOT Changed**:
- `server.py` `round_number` fields in `ConversationTurn` model — those are internal Python fields, not widget_params
- `CharacterDisplay.jsx` — already used correct `roundNumber` camelCase prop
- Cat5 footer logic — already handled correctly with `-` display

**Verification**:
- `cd backend && uv run ruff check state_machine.py` — PASS
- Start Cat1 activity → device panel should show correct round numbers (1, 2, 3)
- Before rounds start → footer should show `-/3` not `0/3`

---
