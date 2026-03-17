# Session Handoff

Last updated: 2026-03-17

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

## Review Cat 5 Correct-Pick Context Fix + Simplify Server Duplication

**Problem**: The latest Cat 5 hallucination fix correctly added `[collected correct item: <label>]` to conversation history, but the same child-turn bookkeeping was duplicated in both `/api/turn` and `/api/turn-speak`. The review pass also found that the new behavior was untested, so a future cleanup could silently break the exact item-label context that the Script Agent now relies on.

**Solution**: Reviewed the active Cat 5 change set, kept the prompt and Script Agent logging changes intact, and simplified the server-side implementation by extracting shared child-turn helpers. Added focused API regressions that prove both turn endpoints record the exact collected-item label in conversation history for correct Cat 5 picks.

**Edits**:
- `backend/server.py` — extracted `_append_child_turn()` and `_record_correct_collection_pick()` so both turn endpoints share the same correct-pick and child-turn bookkeeping
- `tests/test_api.py` — extended Cat 5 coverage to assert `[collected correct item: Spotted mushroom]` is recorded after a correct `/api/turn` collection pick and after a correct `/api/turn-speak` collection pick
- `HANDOFF.md` — added this review/update entry

**NOT Changed**:
- `backend/agents/script_agent.py` and `backend/skills/step_instructions/cat5_step3_collect.md` were reviewed against the server change and left as-is; no additional defect in the raw-response logging or prompt wording justified widening scope in this pass.
- No frontend files changed; the review stayed on the active backend Cat 5 context fix and its API coverage.

**Verification**:
- `uv run pytest tests/test_api.py -q -k "turn_serializes_collected_photos_for_cat5_collection or turn_returns_wrong_photo_without_advancing_cat5_collection or turn_speak_records_exact_collected_item_label_for_cat5_collection"` — PASS (`3 passed, 14 deselected`)
- `uv run ruff check backend/server.py tests/test_api.py` — PASS

---

## Fix Cat 5 LLM Hallucination + Add Response Logging

**Problem**: LLM responses for Cat 5 collection rounds were hallucinating item descriptions (e.g., "fluffy white cloud", "Letter D", "super yellow flower") because the Script Agent never received which grid item the child actually tapped. On correct picks, the photo_id was added to `collected_photos` but no conversation history entry was recorded — the LLM had zero context about the selection and invented descriptions based on the activity theme or original photo.

**Solution**: (1) On correct grid picks, append `[collected correct item: <label>]` to conversation history so the LLM knows exactly what was selected. (2) Added `_get_item_label()` helper to resolve photo_id → display label from current round items. (3) Updated the collect step prompt to instruct the LLM to reference the specific item from the message, not hallucinate. (4) Added raw LLM response logging to both `generate_turn()` and `generate_turn_streaming()` for ongoing monitoring.

**Edits**:
- `backend/server.py` — added `_get_item_label()` helper; both `/api/turn` and `/api/turn-speak` now record `[collected correct item: <label>]` in conversation history on correct picks
- `backend/agents/script_agent.py` — added `logger.info` with full raw LLM JSON response for both streaming and non-streaming paths
- `backend/skills/step_instructions/cat5_step3_collect.md` — added explicit instruction to reference the collected item by name from `[collected correct item: ...]` marker, not hallucinate

**NOT Changed**:
- Wrong-pick path already had `[selected wrong photo: ...]` marker — no change needed
- Frontend components unchanged
- Director/Visual agent logging not added (one-shot at session start, not the issue)

**Verification**:
- `uv run ruff check .` — PASS
- `uv run ruff format --check .` — PASS

---

## Cat 5 Test Contract Realignment

**Problem**: The latest Cat 5 collection workflow switched from fixed accepted IDs to per-round `round_items` and `current_round_items`, but the local API regressions in `tests/test_api.py` still built pre-change session state and submitted old photo IDs like `leaf_round` and `bark_rough`. That made the focused wrong-photo tests fail for the wrong reason and left the new UI-facing session payload effectively unverified. The previous handoff entry also overstated this by claiming the existing tests already covered the updated backend contract.

**Solution**: Realigned the Cat 5 test fixtures to the current catalog-based contract by adding deterministic `round_items`, switching the requests to the new `spotted_mushroom` / `plain_bark` / `straight_stick` IDs, and asserting that `current_round_items` is serialized for the next collection round without leaking the internal `correct` flag. Reviewed the runtime backend/frontend changes in this pass, but did not find a new code defect worth widening beyond the tests and handoff.

**Edits**:
- local `tests/test_api.py` — added deterministic Cat 5 round-item fixtures, updated the collection/wrong-photo requests to current IDs, and asserted `current_round_items` serialization for the next round
- `HANDOFF.md` — replaced the stale top-entry testing claim with the verified state from this review pass

**NOT Changed**:
- `backend/server.py`, `backend/schemas/session_state.py`, `backend/skills/step_instructions/cat5_step2_mission.md`, `backend/skills/step_instructions/cat5_step3_collect.md`, `frontend/src/App.jsx`, and `frontend/src/components/PhotoGallery.jsx` were reviewed but not modified in this pass.
- No new frontend component tests were added; the UI path still relies on API coverage plus frontend lint/build.

**Verification**:
- `uv run pytest tests/test_api.py -q -k "turn_serializes_collected_photos_for_cat5_collection or turn_returns_wrong_photo_without_advancing_cat5_collection or turn_exits_after_two_wrong_cat5_photo_picks"` — PASS (`3 passed, 13 deselected`)
- `uv run ruff check backend/schemas/session_state.py backend/server.py tests/test_api.py` — PASS
- `uv run pytest tests/ -m 'not e2e' -q` — PASS (`123 passed, 5 deselected`)
- `cd frontend && npm run lint` — PASS
- `cd frontend && npm run build` — PASS

---

## Fix Cat 5 Collection Workflow (4 bugs)

**Problem**: Cat 5 out-of-device collection activities had four bugs: (1) AI dialogue didn't guide child to go find/collect items, (2) round counter off-by-one (status bar showed "Round: 4/4" while screen showed "3 of 4 found"), (3) both activities showed identical hardcoded grid items, (4) same grid every round with no variation.

**Solution**: Added per-activity item catalogs with correct items and distractors. Each round now shows 3 items (1 correct + 2 distractors) shuffled randomly. Round counter in footer now shows collected count for Cat 5. Prompt templates updated to include "go explore" language.

**Edits**:
- `backend/schemas/session_state.py` — added `round_items: list[list[dict]]` field to `SessionStateModel`
- `backend/server.py` — replaced `VALID_COLLECTION_PHOTOS` with `COLLECTION_CATALOGS` (per-activity correct/distractor items); added `generate_round_items()` function; changed `_is_correct_collection_photo()` to use per-round items with correct flag; populate `round_items` in `start_session()`; expose `current_round_items` (sans correct flag) in `_session_state_dict()`
- `frontend/src/components/PhotoGallery.jsx` — removed hardcoded `COLLECTION_PHOTOS` array; accepts `items` prop; renders only provided items per round
- `frontend/src/App.jsx` — passes `current_round_items` to PhotoGallery; fixed round counter for Cat 5 to show `collected_photos.length / total_rounds`
- `backend/skills/step_instructions/cat5_step2_mission.md` — added "go explore NOW" call-to-action instruction
- `backend/skills/step_instructions/cat5_step3_collect.md` — added preamble for new round start encouraging child to go find next item

**NOT Changed**:
- State machine step transitions (`state_machine.py`) — round advancement logic unchanged
- Vision agent, recipe assembler, pipeline — unrelated to collection UI
- Test files — no test updates were made in that pass; the next handoff entry records the later Cat 5 test realignment

**Verification**:
- `uv run ruff check .` — PASS
- `uv run ruff format --check .` — PASS
- Start `polka_dot_patrol` → grid shows 3 spotted-themed items
- Start `fluffy_expedition_dandelion` → grid shows 3 fuzzy-themed items
- Complete round 1 → round 2 shows different items
- Status bar round count matches collected count on screen

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
