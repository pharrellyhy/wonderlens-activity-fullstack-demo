# Session Handoff

Last updated: 2026-03-18

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

## Cat 5 Image Asset Wiring

**Problem**: Cat 5 collection items (spotted_mushroom, fuzzy_moss, etc.) displayed with a generic LeafIcon. No per-item images existed, and the data pipeline didn't support an `image` field.

**Solution**: Added `image` path field to all `COLLECTION_CATALOGS` items in `server.py`, pointing to `/icons/{id}.png`. Updated `_session_state_dict()` to pass `image` to the frontend. Updated `PhotoGallery.jsx` to render `<img>` when `photo.image` is present, with `onError` fallback to the existing LeafIcon. Actual PNG images must be generated externally (DALL-E) and placed in `frontend/public/icons/`.

**Edits**:
- `backend/server.py` — added `"image": "/icons/{id}.png"` to all 24 items in `COLLECTION_CATALOGS`; included `image` in `current_round_items` response dict
- `frontend/src/components/PhotoGallery.jsx` — renders `<img>` when `photo.image` is truthy, with `onError` handler that hides broken image and shows LeafIcon fallback
- `docs/plans/cat5-image-assets.md` — plan document listing all 16+8 images needed

**NOT Changed**:
- Recipe JSON files — `collection_items` lists remain unchanged (IDs match catalog)
- Entity icon images (ladybug.png, dandelion.png) — already exist
- State machine, script agent, other agents — unrelated

**Verification**:
- `cd backend && uv run ruff check server.py` — PASS
- `cd frontend && npm run build` — verify no build errors
- Without actual PNG files, items gracefully fall back to LeafIcon via `onError` handler

---

## Review Latest Recipe/Audio Changes + Harden Recipe Contracts

**Problem**: `HANDOFF.md` was behind the current repo state. The latest reviewed changes spanned two areas: the committed frontend audio-unlock fix (`fix(sfx): unlock audio before async API call`) and the new recipe wording/design pass reflected in `docs/WonderLens_Game_Designs.md` plus the five modified `backend/recipes/*.json` files. The frontend fix itself looked coherent on review, but the recipe updates still depended on informal reviewer checks: schema validation did not enforce sequential round numbering, metadata round counts could drift from the actual rounds, and collection recipes could omit a synthesis step without failing fast.

**Solution**: Reviewed the latest committed frontend audio path and left it unchanged after lint/build validation. Reviewed `docs/WonderLens_Game_Designs.md` against the currently modified instruction recipes and kept those recipe edits intact. Hardened the instruction-recipe schema layer so malformed recipe structure now fails at load time: round numbers must be sequential from 1, `metadata.round_count` must match the actual round list, and any recipe with `collection_items` must define a synthesis step. Added focused local schema regressions covering those contracts so future recipe copy/design edits are checked immediately.

**Edits**:
- `backend/schemas/step_instruction.py` — added post-validation for sequential round numbering
- `backend/schemas/recipe.py` — added post-validation for round-count consistency and collection-recipe synthesis requirements
- local `tests/test_schemas.py` — added regression tests for the new instruction-recipe contracts (note: this path is ignored by the repo git config, so the coverage is local-only unless the ignore rule changes)
- `HANDOFF.md` — added this review/update entry

**NOT Changed**:
- `frontend/src/hooks/useSfxPlayer.js`, `frontend/src/hooks/useSessionOrchestration.js`, and `frontend/src/components/DeviceScreen.jsx` were reviewed against the latest committed SFX unlock fix and left unchanged
- `docs/WonderLens_Game_Designs.md` was reviewed for context and left unchanged
- `backend/recipes/dream_whisperer_cat.json`, `backend/recipes/fluffy_expedition_dandelion.json`, `backend/recipes/mood_changer_dog.json`, `backend/recipes/polka_dot_patrol.json`, and `backend/recipes/time_machine_dinosaur.json` were reviewed against the new design direction and left unchanged in this pass

**Verification**:
- `cd backend && uv run pytest ../tests/test_schemas.py -q` — PASS (`17 passed`)
- `cd backend && uv run pytest ../tests/test_api.py ../tests/test_schemas.py -q` — PASS (`39 passed`)
- `cd backend && uv run ruff check schemas/recipe.py schemas/step_instruction.py ../tests/test_schemas.py` — PASS
- `cd frontend && npm run lint` — PASS
- `cd frontend && npm run build` — PASS

---

## Review Instruction-Recipe STEP_2 Flow + Refresh Tests

**Problem**: The new instruction-based recipe pass landed with two concrete gaps. First, the actual turn flow still skipped over STEP_2 in practice: sessions advanced away from the hook immediately, `/api/turn` moved past STEP_2 before invitation replies could be interpreted, and `/api/turn-speak` could start streaming audio for the wrong line before a second decline switched into `EARLY_EXIT`. Second, the tests had drifted from the implementation: shared fixtures still pointed at the deleted `backend/fallbacks/` path, API tests still imported removed pre-generated helpers, and schema coverage still targeted the old `ActivityRecipe` format instead of the new instruction-recipe models.

**Solution**: Reviewed the active instruction-recipe code against `docs/plans/instruction-based-recipes.md`, kept the instruction-driven architecture intact, and fixed the STEP_2 invitation flow instead of papering over it in tests. Session initialization now leaves the hook as the active delivered step, STEP_2 invitation replies are resolved explicitly before advancing into round 1, second declines exit cleanly in both `/api/turn` and `/api/turn-speak`, and the session payload now surfaces `invitation_decline_count`. The test suite was updated to match the current contract: instruction-recipe fixtures now load from `backend/recipes/`, schema tests validate `InstructionRecipe`/`StepInstruction`, and API/visual tests cover the real STEP_2 rules, acceptance, decline, and streamed early-exit behavior.

**Edits**:
- `backend/server.py` — fixed the active-step flow for instruction recipes; added shared invitation-step helpers; kept STEP_2 declines on the invitation step until exit/acceptance; added `invitation_decline_count` to the serialized session state; made `/api/turn-speak` resolve STEP_2 invitation replies non-streaming so TTS speaks the final canonical turn
- `backend/agents/pipeline.py` — stopped pre-advancing past the hook during session initialization so STEP_2 can actually be delivered on the next turn
- `tests/conftest.py` — replaced deleted fallback fixtures with recipe fixtures from `backend/recipes/`
- `tests/test_schemas.py` — shifted schema coverage from the removed dialogue-based recipe JSONs to `InstructionRecipe`, `StepInstruction`, and the current demo recipe files
- `tests/test_api.py` — replaced stale pre-generated-path assertions with instruction-recipe coverage for demo `/api/start`, STEP_2 rules delivery, STEP_2 acceptance, first decline, second decline exit, and `/api/turn-speak` early-exit audio
- `tests/test_server_visual.py` — updated visual-frame tests to account for the new STEP_2 acceptance branch before round rendering
- `HANDOFF.md` — added this review/update entry

**NOT Changed**:
- `backend/agents/script_agent.py`, `backend/recipe_loader.py`, the new instruction recipe JSON files, the prompt/skill markdown files, and the tier rules added in the instruction-recipe pass were reviewed in this pass and left unchanged
- Frontend files currently modified in the worktree were not changed in this pass; they remain whatever state they were already in before this review started
- No broader state-machine refactor or frontend orchestration change was introduced beyond the backend/session flow fix above

**Verification**:
- `cd backend && uv run pytest ../tests/test_api.py ../tests/test_server_visual.py ../tests/test_turn_flow.py ../tests/test_schemas.py ../tests/test_pipeline_visual.py -q` — PASS (`48 passed`)
- `cd backend && uv run ruff check agents/pipeline.py server.py ../tests/test_api.py ../tests/test_server_visual.py ../tests/test_schemas.py ../tests/conftest.py` — PASS
- `cd backend && uv run ruff format --check agents/pipeline.py server.py ../tests/test_api.py ../tests/test_server_visual.py ../tests/test_schemas.py ../tests/conftest.py` — PASS

---

## Instruction-Based Recipe System

**Problem**: Pre-generated recipes contained exact sentences — if a child said something unexpected, they got a canned response that didn't acknowledge what they said. Prompts also used directive tone ("Tell me!", "Go find!") instead of invitational language ("Would you like to...?"). No feature validation ensured AI only referenced visible photo features.

**Solution**: Converted recipes from fixed dialogue scripts to instruction documents (goal + constraints per step). Every turn now calls the Script Agent LLM, which generates contextual, invitational, emotion-tagged responses guided by the recipe instructions. Added invitation decline handling at STEP_2 with graceful exit after 2 declines.

**Edits**:
- `backend/schemas/step_instruction.py` — **NEW**: `StepGoal`, `RoundInstruction`, `StepInstruction` models for instruction-based recipes
- `backend/schemas/recipe.py` — Added `InstructionRecipe` model with `step_instructions`, `photo_features`, `collection_items`
- `backend/schemas/turn_response.py` — Added `child_intent` field for STEP_2 invitation handling
- `backend/schemas/session_state.py` — Replaced `is_pregenerated`/`recipe` with `instruction_recipe`/`invitation_decline_count`
- `backend/schemas/__init__.py` — Exported new models
- `backend/recipes/*.json` (5 files) — Converted from exact dialogue to instruction format with goals, constraints, emotion tags, acceptable themes, photo features
- `backend/agents/script_agent.py` — Added instruction overlay (`_build_instruction_overlay`), emotion tag fallback (`_ensure_emotion_tag`, `_get_suggested_emotion_tag`), photo feature anchors in system prompt, invitational patterns in tier constraints, updated user prompt for bracket emotion tags and child_intent
- `backend/skills/script_turn.md` — Changed emotion format from `(excited)` to `[excited]`, added feature anchors section, added invitational language rules, added `child_intent` output rule
- `backend/skills/step_instructions/cat1_step2_rules.md` — Added invitation handling with child_intent
- `backend/skills/step_instructions/cat5_step2_mission.md` — Added invitation handling with child_intent
- `backend/tier_rules.yaml` — Added `invitational_patterns` and `forbidden_directives` per tier
- `backend/recipe_loader.py` — Major rewrite: removed `resolve_turn_from_recipe`, `resolve_wrong_photo_turn`, `_select_acknowledgment`, `_select_round_transition_ack`; renamed `load_demo_recipe` to `load_instruction_recipe`; simplified `recipe_to_session_state` (no first turn generation)
- `backend/server.py` — Demo entities now use Script Agent for hook turn; removed all `is_pregenerated` branching; always calls Script Agent for turn generation; added invitation decline logic at STEP_2 in both `/api/turn` and `/api/turn-speak`

**NOT Changed**:
- Frontend components — no changes needed, responses use the same API shape
- Live pipeline path (custom photo uploads) — unchanged
- State machine, DB layer, STT, TTS, scenarios, pipeline.py
- `polka_dot_patrol_hard.json` — not a demo recipe, different format

**Verification**:
- `uv run ruff check . && uv run ruff format .` — PASS
- `uv run python -c "from recipe_loader import load_instruction_recipe; ..."` — all 5 recipes validated
- `uv run python -c "from recipe_loader import ..., recipe_to_session_state; ..."` — session state creation OK
- `uv run python -c "from agents.script_agent import _build_system_prompt; ..."` — prompt includes feature anchors, invitational patterns, forbidden directives
- `uv run python -c "from agents.script_agent import _ensure_emotion_tag; ..."` — emotion tag enforcement OK

---

## Review Pre-generated Recipe Path + Restore Cat5 Round Acknowledgment

**Problem**: The new pre-generated recipe feature added a no-LLM path for demo entities, but the turn resolver had a cat5 regression and no matching API coverage. After a correct collection pick, `/api/turn` advanced to the next step and called `resolve_turn_from_recipe()`, but the resolver ignored the successful `photo_id` and dropped the previous round’s `on_correct` acknowledgment entirely. The current test file also still hardcoded the old `backend/fallbacks/` recipe path and had no coverage for the demo `/api/start` shortcut or the pre-generated `/api/turn-speak` bypass path.

**Solution**: Reviewed the pre-generated recipe implementation, kept the no-LLM architecture intact, and fixed the cat5 transition logic by treating a non-null `photo_id` as a successful round completion when building the acknowledgment that bridges into the next round or synthesis step. Added focused API regressions for the demo start shortcut, the cat5 correct-pick acknowledgment, the cat5 wrong-photo recipe retry line, and the `/api/turn-speak` pre-generated bypass path. Updated the legacy recipe test path from `fallbacks/` to `recipes/`.

**Edits**:
- `backend/recipe_loader.py` — added `_select_round_transition_ack()` and used it for pre-generated round/synthesis transitions so cat5 correct photo picks retain the prior round’s `on_correct` acknowledgment before the next prompt
- `tests/test_api.py` — switched the recipe fixture path to `backend/recipes/`; added focused coverage for demo `/api/start`, pre-generated cat5 correct-pick acknowledgment, pre-generated cat5 wrong-photo retry text, and pre-generated `/api/turn-speak` bypass behavior
- `HANDOFF.md` — added this review/update entry

**NOT Changed**:
- `backend/server.py`, `backend/agents/pipeline.py`, `backend/schemas/creative_slots.py`, `backend/schemas/session_state.py`, `backend/schemas/voice_script.py`, the updated prompt files, and `docs/plans/pre-generated-recipes.md` were reviewed in this pass and left unchanged after the targeted fix above.
- `backend/recipes/polka_dot_patrol_hard.json` remains in its older non-`ActivityRecipe` format and was not rewritten in this pass; the pre-generated demo path and the new validation run cover only the five demo recipes listed in the feature plan.
- No frontend files changed; this pass stayed on the new backend pre-generated recipe path and its missing regression coverage.

**Verification**:
- `uv run pytest tests/test_api.py -q -k "start_session_uses_pregenerated_recipe_for_demo_entity or pregenerated_cat5_correct_pick_keeps_round_acknowledgment or pregenerated_cat5_wrong_photo_uses_recipe_retry_line or turn_speak_uses_pregenerated_recipe_without_streaming_agent"` — PASS (`4 passed, 17 deselected`)
- `uv run ruff check backend/server.py backend/recipe_loader.py backend/agents/pipeline.py backend/schemas/creative_slots.py backend/schemas/session_state.py backend/schemas/voice_script.py tests/test_api.py` — PASS
- `uv run ruff format --check backend/recipe_loader.py tests/test_api.py` — PASS
- `cd backend && uv run python - <<'PY' ...` — PASS (`validated 5 demo recipes`)

---

## Pre-generated Static Recipes for Demo Entities

**Problem**: Each demo session ran the full LLM pipeline (~580ms on `/api/start`, ~200-400ms per `/api/turn`) for the 5 fixed demo entities (dog, cat, dinosaur, ladybug, dandelion), adding latency and API cost for content that could be pre-authored.

**Solution**: Pre-authored complete recipe JSON files for all 5 demo entities. Demo sessions now load recipes directly — zero LLM calls (Vision, Director, Script Agent all bypassed). Custom photo uploads continue using the live pipeline unchanged.

**Edits**:
- `backend/schemas/voice_script.py` — Added `synthesis_speech`, `early_exit_speech`, tone markers (`hook_tone`, `transition_tone`, `closing_tone`, `tomorrow_tone`, `synthesis_tone`, `early_exit_tone`) to `VoiceScript`; added `tone_marker`, `on_wrong_photo` to `Round`
- `backend/schemas/session_state.py` — Added `is_pregenerated: bool`, `recipe: ActivityRecipe | None` fields to `SessionStateModel`
- `backend/agents/pipeline.py` — Renamed `_FALLBACKS_DIR` → `_RECIPES_DIR`, `load_fallback()` → `load_recipe()`, path now points to `recipes/`
- `backend/fallbacks/` → `backend/recipes/` — Git-moved directory
- `backend/recipes/*.json` (5 files) — Enriched with `early_exit_speech`, tone markers on all fields, `on_wrong_photo` on cat5 rounds, `synthesis_speech` on cat5 recipes
- `backend/recipe_loader.py` — **NEW**: `is_demo_entity()`, `load_demo_recipe()` (with `@lru_cache`), `recipe_to_session_state()`, `resolve_turn_from_recipe()`, `resolve_wrong_photo_turn()`, `_select_acknowledgment()` for correct/incorrect/silence branching
- `backend/server.py` — `/api/start` branches on `is_demo_entity()` to skip Vision/Director/Script pipeline; `/api/turn` and `/api/turn-speak` branch on `state.is_pregenerated` at all 4 turn-generation points (silence exit, wrong-photo exit, wrong-photo retry, main turn); pre-gen `/api/turn-speak` bypasses streaming Script Agent entirely

**NOT Changed**:
- Live pipeline path (custom photo uploads) — unchanged, still runs full Vision + Director + Script + Visual agents
- Frontend components — no changes needed, pre-gen responses use the same API response shape
- State machine, DB layer, STT, TTS, scenarios, tier rules, tests
- `polka_dot_patrol_hard.json` — kept as-is (not a core demo entity)

**Verification**:
- `uv run ruff check .` — PASS
- `uv run ruff format --check .` — PASS
- Recipe JSON validation: all 5 files parse against updated `ActivityRecipe` schema
- Integration test: full cat1 turn flow (hook → rules → 3 rounds with correct/incorrect/silence ack → celebrate → closing → early_exit)
- Integration test: cat5 wrong photo returns `on_wrong_photo` text from recipe
- `is_demo_entity()` matches all 5 demo filenames, rejects custom uploads

---

## Review Latest Cat 5 Gallery Prompt Pass + Restore Request Locking

**Problem**: The latest Cat 5 UI/backend pass added `collection_criterion` to the session payload and started passing the tapped item label through the frontend, but it also reintroduced a request-locking bug. `PhotoGallery` now waits on the promise returned by `onPhotoSelect()`, while `useSessionOrchestration.handlePhotoCollection()` stopped returning the `sendPhotoCollection()` promise. That meant the gallery could unlock immediately again, allowing fast repeat taps before the in-flight collection turn finished. The new backend payload field for the gallery prompt also had no explicit API coverage.

**Solution**: Reviewed the active Cat 5 change set, kept the prompt/content changes intact, restored promise-based locking by returning the collection request from `handlePhotoCollection()`, and extended the focused Cat 5 API regression to assert the new `collection_criterion` field alongside the existing round-item payload. This keeps the frontend lock aligned with the admitted request lifecycle and gives the new gallery prompt contract a backend test.

**Edits**:
- `frontend/src/hooks/useSessionOrchestration.js` — returned `sendPhotoCollection(photoId, label)` from `handlePhotoCollection()` so `PhotoGallery` stays locked until the collection request settles
- `tests/test_api.py` — added an assertion that Cat 5 turn responses serialize `session_state.collection_criterion` for the gallery prompt path
- `HANDOFF.md` — added this review/update entry

**NOT Changed**:
- `frontend/src/App.jsx`, `frontend/src/components/PhotoGallery.jsx`, `frontend/src/hooks/useConversation.js`, `backend/server.py`, `backend/agents/script_agent.py`, `backend/db.py`, `backend/skills/step_instructions/cat5_step2_mission.md`, and `backend/skills/step_instructions/cat5_step3_collect.md` were reviewed in this pass and left as-is after the targeted fix above.
- There is still no frontend unit/integration test harness in the current workspace, so the UI-side fix is covered by lint/build plus code-path review rather than an automated component test.

**Verification**:
- `uv run pytest tests/test_api.py -q -k "turn_serializes_collected_photos_for_cat5_collection or turn_returns_wrong_photo_without_advancing_cat5_collection or turn_speak_records_exact_collected_item_label_for_cat5_collection"` — PASS (`3 passed, 14 deselected`)
- `uv run ruff check backend/server.py backend/agents/script_agent.py backend/db.py tests/test_api.py` — PASS
- `cd frontend && npm run lint` — PASS
- `cd frontend && npm run build` — PASS

---
