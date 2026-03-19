# Session Handoff

Last updated: 2026-03-18

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

## Attempt gpt-image-1.5 Asset Generation via backend/.env

**Problem**: The user requested that the Cat 5 item icons be regenerated with `gpt-image-1.5` using `OPENAI_API_KEY` and `OPENAI_BASE_URL` from `backend/.env` instead of the local Pillow renderer.

**Solution**: Added an OpenAI-backed generator script at `scripts/generate_cat5_icons_openai.py` that reads `backend/.env`, builds per-item prompts from the Cat 5 asset list, and saves outputs into `frontend/public/icons/`. Smoke-tested it against a single file before attempting the full 24-image batch.

**Edits**:
- `scripts/generate_cat5_icons_openai.py` — new generator for `gpt-image-1.5`, including `.env` parsing that tolerates trailing inline comments and an optional `--base-url` override for testing alternate OpenAI-compatible endpoints without editing secrets

**NOT Changed**:
- Existing generated PNG assets in `frontend/public/icons/`
- `backend/.env` itself
- Frontend/backend runtime wiring

**Verification**:
- Confirmed `backend/.env` contains both `OPENAI_API_KEY` and `OPENAI_BASE_URL`
- `python scripts/generate_cat5_icons_openai.py --only spotted_mushroom.png --overwrite` — FAIL: configured proxy returns no image bytes for `/images/generations`
- Proxy model listing via OpenAI client reports `gpt-image-1.5` as available
- Same key against official `https://api.openai.com/v1` — FAIL (`401 invalid_api_key`), indicating the key is proxy-scoped rather than a direct OpenAI key
- Responses API image-generation path against the configured proxy — FAIL (`unsupported operation`)

---

## Generate Cat 5 Illustrated Item Icons

**Problem**: The Cat 5 collection games referenced 24 per-item icon files in `frontend/public/icons/`, but those PNGs did not exist yet. The runtime wiring was already in place, so the remaining gap was the actual illustrated assets for both the polka-dot and fluffy item sets.

**Solution**: Added a reproducible local generator at `scripts/generate_cat5_icons.py` that renders all 24 icons as warm storybook-style PNGs sized to match the existing entity icon set. Ran the generator to create the missing files under `frontend/public/icons/` and manually spot-checked the rendered output across both games.

**Edits**:
- `scripts/generate_cat5_icons.py` — new Pillow-based asset generator for all 24 Cat 5 item icons
- `frontend/public/icons/*.png` — added 24 generated item icons:
  `spotted_mushroom`, `dotted_pebble`, `speckled_leaf`, `circle_flower`, `straight_stick`, `plain_bark`, `long_grass`, `smooth_stone`, `pine_needle`, `plain_leaf`, `forked_twig`, `acorn_cap`, `fuzzy_moss`, `fluffy_seed`, `soft_petal`, `woolly_caterpillar`, `hard_rock`, `spiky_pinecone`, `rough_bark`, `sharp_thorn`, `dry_leaf`, `smooth_pebble`, `stiff_branch`, `brittle_shell`

**NOT Changed**:
- Backend/frontend runtime code — already referenced these filenames and was left unchanged in this pass
- Existing entity icons such as `ladybug.png` and `dandelion.png`
- Recipe/scenario files

**Verification**:
- `python scripts/generate_cat5_icons.py` — PASS (`Generated 24 icons ...`)
- `find frontend/public/icons ... | wc -l` — PASS (`24`)
- `file frontend/public/icons/{sample}.png` — PASS (`PNG image data, 256 x 256, 8-bit/color RGBA`) on sampled outputs
- Manual visual review via generated contact sheets for both game sets — PASS

---
