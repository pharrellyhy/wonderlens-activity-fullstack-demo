# Session Handoff

Last updated: 2026-04-04

---

## Review Follow-Up: Production Simplification Inside turn_handling/

**Problem**: After stabilizing the decomposition test surface, the production `backend/turn_handling/` package still had a couple of extraction-era duplications that made the code noisier than necessary. In `invitation.py`, the “generate a re-invite and return it” path was duplicated for both first-decline and substantive/off-topic cases. In `rounds.py`, the deterministic Cat5 photo-prompt return block appeared twice with the same append/result wiring. These were not correctness bugs, but they were exactly the kind of low-signal repetition that makes later changes riskier.

**Solution**: Kept behavior unchanged and simplified only the duplicated local paths. `invitation.py` now uses one local helper for the shared re-invite generation/result flow, and `rounds.py` now uses one local helper for deterministic collection photo-prompt responses. No branching rules, state transitions, or response semantics changed.

**Edits**:
- `backend/turn_handling/invitation.py` — extracted `_generate_reinvite_result()` to collapse the duplicated non-terminal STEP_2 re-invite path
- `backend/turn_handling/rounds.py` — extracted `_photo_prompt_result()` to collapse the duplicated deterministic Cat5 photo-phase response path
- `HANDOFF.md` — added this review follow-up entry

**NOT Changed**:
- `backend/turn_handling/core.py`, `backend/turn_handling/collection.py`, `backend/turn_handling/synthesis.py`, `backend/turn_handling/directive.py` — reviewed again and left unchanged in this pass
- State-machine behavior, turn advancement order, and deterministic acceptance/photo prompt content — unchanged
- Test fixtures from the previous review follow-up — kept as-is
- Frontend code — unchanged

**Verification**:
- `uv run pytest tests/test_turn_handler.py tests/test_api.py tests/test_server_visual.py -q` — PASS (`77 passed`)
- `uv run pytest tests/test_turn_handler.py tests/test_debug_payload.py tests/test_intent_classifier.py tests/test_deep_link.py tests/test_api.py tests/test_server_visual.py -q` — PASS (`116 passed`)
- `uv run ruff check backend/turn_handling/invitation.py backend/turn_handling/rounds.py tests/test_turn_handler.py tests/test_api.py tests/test_server_visual.py` — PASS
- `uv run ruff format --check backend/turn_handling/invitation.py backend/turn_handling/rounds.py tests/test_turn_handler.py tests/test_api.py tests/test_server_visual.py` — PASS

---

## Review Follow-Up: Stabilize Legacy turn_handling Tests

**Problem**: Picking up the `turn_handler.py` decomposition work showed that the newly updated legacy-path tests no longer matched the repo's runtime defaults. `backend/config.yaml` currently enables `turn_director_enabled`, so focused tests that were meant to exercise the classic `turn_handling.core.resolve_turn()` path were accidentally entering the directive path, making real Turn Director calls and even trying to log to the demo DB. Two other test expectations had also drifted: the synthesis-failure regression patched the wrong `get_settings()` function after the module split, and the Step 2 acceptance API/visual tests still mocked `ScriptAgent.generate_turn()` even though invitation acceptance now uses deterministic celebration templates instead of the speaker path.

**Solution**: Kept production turn-handling code unchanged and fixed the review surface instead. The touched legacy tests now explicitly disable `turn_director_enabled` in their local fixtures so they exercise the decomposed classic path they are written for. I also updated the synthesis regression to patch `turn_handling.generation.get_settings()`, aligned the Step 2 acceptance API assertion with deterministic `_ACCEPTANCE_CELEBRATIONS`, removed no-op `generate_turn()` mocks from the visual-frame acceptance tests, and fixed the stale `turn_handler` wording in `scripts/scoring.py`.

**Edits**:
- `tests/test_turn_handler.py` — added an autouse legacy-path settings stub (`turn_director_enabled=False`) and corrected the synthesis classifier-failure patch target to `turn_handling.generation.get_settings`
- `tests/test_api.py` — disabled Turn Director in the temp-client fixture; aligned the invitation-acceptance assertion with `_ACCEPTANCE_CELEBRATIONS` instead of an unused speaker mock
- `tests/test_server_visual.py` — disabled Turn Director in the temp-client fixture and removed unused `ScriptAgent.generate_turn()` mocks from Step 2 acceptance visual tests
- `scripts/scoring.py` — updated the stale comment to refer to `turn_handling` validators
- `HANDOFF.md` — added this review follow-up entry

**NOT Changed**:
- `backend/turn_handling/` production modules — reviewed and left unchanged in this follow-up
- `backend/server.py` import changes — reviewed and kept as-is
- `backend/config.yaml` — still enables Turn Director for normal runtime; the isolation is test-scoped only
- Frontend code — unchanged

**Verification**:
- `uv run pytest tests/test_turn_handler.py tests/test_debug_payload.py tests/test_intent_classifier.py tests/test_deep_link.py tests/test_api.py tests/test_server_visual.py -q` — PASS (`116 passed`)
- `uv run ruff check backend/turn_handling backend/server.py scripts/scoring.py tests/test_turn_handler.py tests/test_debug_payload.py tests/test_intent_classifier.py tests/test_deep_link.py tests/test_api.py tests/test_server_visual.py` — PASS
- `uv run ruff format --check tests/test_turn_handler.py tests/test_api.py tests/test_server_visual.py scripts/scoring.py` — PASS

---

## Decompose turn_handler.py into turn_handling/ package

**Problem**: `backend/turn_handler.py` was 2,936 lines with a 619-line god-method (`resolve_turn`) containing 60+ branches and 29 return paths. Debugging any single code path required reading the entire function and mentally filtering out irrelevant branches.

**Solution**: Replaced the monolithic file with a `backend/turn_handling/` package of 11 focused modules. Pure refactoring — no behavioral changes. Each module maps to a debuggable concern (e.g., Cat5 collection bugs → open `collection.py` at ~180 lines).

**Edits**:
- `backend/turn_handler.py` — DELETED (replaced by package)
- `backend/turn_handling/__init__.py` — NEW: Re-exports public API + backward-compatible internal symbols
- `backend/turn_handling/types.py` — NEW: TurnInput, TurnResult, GenerationDebugInfo dataclasses (~40 lines)
- `backend/turn_handling/helpers.py` — NEW: Predicates, state mutation, response builders, constants (~370 lines)
- `backend/turn_handling/generation.py` — NEW: LLM generation retry, validation, intent classification (~550 lines)
- `backend/turn_handling/invitation.py` — NEW: STEP_2 invitation routing (~130 lines)
- `backend/turn_handling/collection.py` — NEW: Cat5 photo validation, detail phase (~240 lines)
- `backend/turn_handling/rounds.py` — NEW: Round generation, deferred advance, guardrails (~240 lines)
- `backend/turn_handling/synthesis.py` — NEW: Synthesis phases (invite/evaluate/improve/generate) (~300 lines)
- `backend/turn_handling/directive.py` — NEW: Turn Director feature-flagged bypass (~960 lines)
- `backend/turn_handling/debug.py` — NEW: Debug payload, step flow, phase timelines (~190 lines)
- `backend/turn_handling/core.py` — NEW: Slim resolve_turn dispatcher (~290 lines)
- `backend/server.py` — Updated imports: `turn_handler` → `turn_handling`
- `tests/test_turn_handler.py` — Updated imports + monkeypatch targets
- `tests/test_debug_payload.py` — Updated imports
- `tests/test_intent_classifier.py` — Updated imports + patch targets
- `tests/test_deep_link.py` — Updated imports
- `tests/test_api.py` — Updated patch targets
- `tests/test_server_visual.py` — Updated patch targets
- `scripts/scoring.py` — Updated imports

**NOT Changed**:
- `backend/state_machine.py` — Step transition logic stays where it is
- `backend/agents/script_agent.py` — Called by generation.py but not modified
- `backend/schemas/` — No schema changes
- Frontend — Backend API contract is identical
- Behavioral semantics — Same branches, same order, same outputs

**Verification**:
- `uv run pytest tests/test_turn_handler.py` — 18 failed / 21 passed (identical to pre-refactor baseline on main)
- `uv run pytest tests/test_debug_payload.py tests/test_intent_classifier.py tests/test_deep_link.py` — 39/39 passed
- `uv run ruff check backend/turn_handling/` — all clean
- `uv run ruff format --check backend/turn_handling/` — all formatted

---

## Turn Director + Story Scaffold (Feature-Flagged)

**Problem**: Three interconnected issues: (1) Intent classification outputs content-type (confirm/decline/substantive/off_topic) requiring ~300 lines of if/elif routing to map to actions. (2) Fixed response templates (`_ACCEPTANCE_CELEBRATIONS`, `_PHOTO_FIND_PROMPTS`) feel robotic. (3) Cat5 collection detail questions repeat ("how does it feel?" every round) and gathered details are ignored in synthesis stories.

**Solution**: Merged classifier + planner into a single **Turn Director** LLM call behind `turn_director_enabled` feature flag. Outputs action-based intents (advance/stay/need_help/redirect/exit) + reasoning + response_direction. Added **Story Scaffold** to game definitions so collection rounds harvest story ingredients for synthesis.

**Edits**:
- `backend/schemas/turn_directive.py` — NEW: `TurnDirective` and `StoryElement` schemas
- `backend/schemas/creative_slots.py` — Added `StoryScaffold` model, `story_scaffold` optional field on `Cat5CreativeSlots`
- `backend/schemas/session_state.py` — Added `story_elements: list[StoryElement]`, `last_directive_action: str`
- `backend/schemas/__init__.py` — Added exports for new schemas
- `backend/agents/turn_director.py` — NEW: `TurnDirector` agent with step phase rules, state context builder, LLM call
- `backend/skills/turn_director_system.md` — NEW: Turn Director prompt template
- `backend/skills/speaker_directive_system.md` — NEW: Speaker prompt for directive path
- `backend/agents/script_agent.py` — Added `generate_turn_from_directive()`, `_build_directive_speaker_prompt()`
- `backend/turn_handler.py` — Added `_fast_path_directive()`, `_get_turn_directive()`, `_resolve_turn_with_directive()`, feature flag branch in `resolve_turn()`
- `backend/config.py` — Added `turn_director_enabled` setting
- `backend/config.yaml` — Added `turn_director_enabled: false`
- `backend/games/fluffy_expedition_dandelion.md` — Added `story_scaffold` section
- `backend/games/polka_dot_patrol.md` — Added `story_scaffold` section
- `docs/plans/2026-03-31-turn-director-story-scaffold.md` — Design plan

**NOT Changed**: Legacy intent classification path (fully intact behind feature flag), frontend, remaining 7 Cat5 game definitions (story_scaffold is optional — games without it use legacy path)

**Verification**:
```bash
cd backend
uv run pytest tests/ -x -q --timeout=30 --ignore=tests/test_ai_quality.py --ignore=tests/test_session_runner.py --ignore=tests/test_eval.py  # 19 passed
uv run ruff check .          # All passed
uv run ruff format --check .  # All formatted
# Enable: set turn_director_enabled: true in config.yaml, restart server
```

---

## Unified Intent Classifier + Phase Timeline Debug + Code-Controlled Transitions

**Problem**: Multiple interconnected issues: (1) Fragmented intent classification — Script Agent `child_intent`, `_classify_story_response`, and a hardcoded frozenset all classified child responses differently, causing misrouted turns (e.g., "yes" treated as story content). (2) Debug panel lacked phase-level visibility for Cat5 collection/synthesis loops and Cat1 invitation. (3) LLM-generated transition prompts were unreliable — celebration responses leaked finding prompts, collection photo prompts said "you found something!" when nothing was found, synthesis invite phase narrated stories instead of asking questions. (4) Stories were too short and ignored collected details. (5) Debug data wasn't persisted to DB.

**Solution**: Three major changes:

*Unified Intent Classifier* — Replaced all three classification mechanisms with a single `_classify_child_intent` LLM pre-classifier that runs before the Script Agent. Common phrases (yes/no/sure/maybe) are detected in code via `_CONFIRM_WORDS`/`_DECLINE_WORDS` frozensets, bypassing the LLM entirely. Removed `child_intent` from `TurnResponse` and `TurnPlan`. Added `ChildIntentClassification` schema with optional synthesis extension (`story_quality`, `is_related_to_collection`). Script Agent receives classified intent as context instead of doing classification itself.

*Code-Controlled Transitions* — Replaced unreliable LLM-generated responses with deterministic templates for critical transitions: invitation acceptance celebration (`_ACCEPTANCE_CELEBRATIONS`), collection photo prompt (`_collection_photo_prompt` with `_ANGLE_ADJECTIVES` mapping), synthesis invite (`_SYNTHESIS_INVITE_TEMPLATES`), and synthesis confirm detection (`_SYNTHESIS_CONFIRM_WORDS`). Combined celebration + finding prompt into a single response to eliminate auto-advance round trip. Added story length enforcement (`_MIN_STORY_SENTENCES`) with retry when below minimum.

*Phase Timeline Debug* — Added `_build_phase_timeline(state)` returning sub-step phase lists (done/current/pending) for Cat5 collection, Cat5 synthesis, and Cat1 invitation. Rendered as compact horizontal badge row in the debug panel State tab. Added `debug_payload` column to DB turns table. Added `child_intent` to state snapshot and session state dict.

**Edits**:
- `backend/schemas/child_intent.py` — NEW: `ChildIntentClassification` Pydantic model
- `backend/schemas/story_classification.py` — DELETED: replaced by `child_intent.py`
- `backend/schemas/session_state.py` — added `synthesis_story_quality`, `child_intent` fields
- `backend/schemas/turn_response.py` — removed `child_intent` field
- `backend/schemas/turn_plan.py` — removed `child_intent` field
- `backend/turn_handler.py` — added `_classify_child_intent`, `_CONFIRM_WORDS`/`_DECLINE_WORDS`, `_collection_photo_prompt`, `_ACCEPTANCE_CELEBRATIONS`, `_synthesis_invite_prompt`, `_SYNTHESIS_CONFIRM_WORDS`, `_build_phase_timeline`, story length enforcement; removed `_classify_story_response`, `_AFFIRMATIVE_PATTERNS`, `_is_affirmative_or_continuation`; rewrote invitation/synthesis handlers; fixed name extraction patterns; disabled `_validate_response`
- `backend/agents/script_agent.py` — removed `child_intent` from output; added intent context to prompt; removed round number from synthesis/celebrate/closing prompts
- `backend/server.py` — added `child_intent` to `_session_state_dict` and `_build_state_snapshot`; added `debug_payload` to AI turn logging
- `backend/db.py` — added `debug_payload TEXT` migration and param to `log_turn`
- `backend/config.py` — added `ali_classifier_model` (defaults to `qwen3.5-flash`)
- `backend/skills/step_instructions/cat5_step2_mission.md` — removed `child_intent` classification rules; added acceptance celebration rule
- `backend/skills/step_instructions/cat1_step2_rules.md` — same
- `backend/skills/step_instructions/cat5_step3_collect.md` — added Phase A opening rule, no-location rule, Phase B celebrate-only rule, anti-repetition rules
- `backend/skills/step_instructions/cat5_step4_synthesis.md` — hardened invite phase; moved quality standard + examples inside GENERATE phase section
- `backend/skills/step_instructions/cat5_step4_synthesis__story_generation.md` — 5-beat story framework (opening→surprise→try-and-fail→breakthrough→warm ending); increased length requirements; added context usage rules
- `backend/skills/planner_system.md` — removed `child_intent` from output
- `backend/skills/script_turn.md` — removed `child_intent` output instruction
- `backend/skills/few_shot.md` — cleaned location-specific hints
- All 15 step instruction files — updated example headers to prevent LLM copying
- `frontend/src/components/DebugPanel.jsx` — added `PhaseBadge`/`PhaseTimeline` components; added `child_intent` to State tab; removed `child_intent` from LLM Output; added phase badge to History tab
- `tests/test_intent_classifier.py` — NEW: 9 tests for classifier
- `tests/test_debug_payload.py` — 19 new tests for phase timeline
- `tests/test_turn_handler.py` — updated invitation/synthesis tests for new classifier flow
- `tests/test_api.py`, `tests/test_server_visual.py`, `tests/test_turn_plan.py`, `tests/test_planner.py` — removed `child_intent` references

**NOT Changed**:
- `backend/agents/director.py`, `backend/agents/visual_agent.py`, `backend/agents/recipe_assembler.py` — untouched
- Frontend conversation flow, TTS/STT pipeline — unchanged
- `backend/state_machine.py` — step transitions unchanged

**Verification**:
- `uv run pytest tests/ --ignore=tests/test_character_sound_frontend_contracts.py -q` — 423 passed, 12 skipped (1 pre-existing failure excluded)
- `uv run ruff check backend/ tests/` — PASS
- `grep -r "StoryClassification\|_classify_story_response\|_AFFIRMATIVE_PATTERNS" backend/ tests/` — zero matches

---

## Review Follow-Up: Immersive Character Sounds Frontend Contract + Schema Tightening

**Problem**: Reviewing the in-progress `feat/immersive-character-sounds` worktree against `docs/plans/2026-03-28-immersive-character-sounds.md` surfaced three concrete issues. First, the frontend only preserved `character_sfx` for normal `/api/turn` responses; hook turns from `/api/start` and `/api/start-deep-link` dropped that field, so first-turn ambient or character sounds would never play. Second, the muted TTS path in `useSessionOrchestration.js` triggered `playOutros()` inside the timeout callback and then called `handleSpeakingDone()`, which played the same outro cues a second time. Third, `TurnPlan.character_sfx` was still typed as raw `list[dict]` even though the branch had already introduced a dedicated `CharacterSfxCue` schema, which kept planner parsing looser than necessary and forced redundant dict-to-model conversion in `ScriptAgent`.

**Solution**: Kept the overall immersive-sound design and narrowed the fixes to the verified contract gaps. The conversation hook now carries `character_sfx` for first-turn messages as well as regular turn responses, so hook audio can reach the orchestration layer. The muted playback path now lets `handleSpeakingDone()` own outro playback, eliminating the duplicate-fire path. On the backend, `TurnPlan` now uses `CharacterSfxCue` directly, which simplifies the plan-to-turn merge and validates planner sound entries earlier without changing the server-side cue whitelist and timing normalization.

**Edits**:
- `frontend/src/hooks/useConversation.js` - preserved `characterSfx` when hydrating the initial hook message from both `/api/start` and `/api/start-deep-link`
- `frontend/src/hooks/useSessionOrchestration.js` - removed the extra muted-path `playOutros()` call so outro cues only fire once per turn
- `frontend/src/hooks/useCharacterSfx.js` - removed unused pool bookkeeping and dead preload metadata so the hook matches its current lazy-cache behavior more clearly
- `backend/schemas/turn_plan.py` - changed `character_sfx` from raw dicts to `list[CharacterSfxCue]`
- `backend/agents/script_agent.py` - simplified the two-pass merge path to reuse validated `CharacterSfxCue` models directly
- `tests/test_turn_plan.py` - added coverage for `character_sfx` defaults and dict-to-model coercion in `TurnPlan`
- `tests/test_character_sound_frontend_contracts.py` - added source-level regressions for hook-turn `character_sfx` preservation and the muted outro path
- `HANDOFF.md` - added this review follow-up entry

**NOT Changed**:
- `backend/server.py` cue validation and response wiring - unchanged in this review follow-up
- Character sound asset files under `frontend/public/sfx/character/` - reviewed, not modified
- The separate script/test formatting changes already present in the worktree - reviewed, not modified in this follow-up

**Verification**:
- `uv run pytest backend/tests/test_character_sounds.py tests/test_turn_plan.py tests/test_character_sound_frontend_contracts.py tests/test_backend_imports.py tests/test_device_screen_layout.py -q` - PASS (`40 passed`)
- `uv run ruff check backend/schemas/turn_plan.py backend/agents/script_agent.py tests/test_turn_plan.py tests/test_character_sound_frontend_contracts.py backend/tests/test_character_sounds.py tests/test_backend_imports.py tests/test_device_screen_layout.py` - PASS
- `uv run ruff format --check backend/schemas/turn_plan.py backend/agents/script_agent.py tests/test_turn_plan.py tests/test_character_sound_frontend_contracts.py` - PASS

---

## Fix: Cat5 Collection Phase Desync + Synthesis Classification Too Strict

**Problem**: Two Cat5 game flow bugs: (1) When a child completes a detail question in Phase B, the backend returned `collection_phase="photo"` + advanced `current_step` in the same response as the naming dialogue. The frontend immediately showed the next round's photo grid while TTS was still playing "Let's call it Cloud Puff!" (2) For T0 children (ages 2-4), the LLM story classifier often misclassified short story attempts like "moss go sleep" as "unrelated" instead of "story_attempt(weak)", triggering confusing re-invites. Additionally, the classification exception fallback defaulted to "unrelated", compounding the issue when the LLM was down.

**Solution**: Three targeted fixes in `turn_handler.py`:
- Bug 1: Replaced immediate `collection_phase = "photo"` + `_advance_state()` with the existing `round_advance_pending = True` + `auto_advance = True` pattern (same approach already used for the last-round → synthesis transition). The frontend now keeps showing the detail screen during TTS, then auto-advances to the next round's photo grid.
- Bug 2a: Added T0 early-return before the `_classify_story_response()` LLM call — treats any non-silent T0 response as a story seed for AI expansion.
- Bug 2b: Changed `_classify_story_response()` exception fallback from `"unrelated"` to `"story_attempt(weak)"` — fail-safe toward acceptance.
- Code simplifier removed the now-dead T0 branch in the classification handler and collapsed duplicate TurnResult blocks.

**Edits**:
- `backend/turn_handler.py` — deferred Phase B→next round advance via `round_advance_pending`; added T0 early-return in `_resolve_synthesis_turn` before LLM classification; changed exception fallback to `story_attempt(weak)`; removed dead T0 branch and collapsed duplicate TurnResult blocks
- `tests/test_turn_handler.py` — updated `test_detail_response_advances_to_next_round` and `test_silence_during_detail_phase_still_advances` to expect deferred advance; added `test_synthesis_t0_skips_classification_and_expands_seed` and `test_synthesis_classification_failure_defaults_to_story_attempt`
- `tests/test_api.py` — updated `test_turn_advances_cat5_collection_after_detail_response` to expect deferred advance
- `docs/plans/2026-03-30-cat5-workflow-diagnosis.md` — diagnostic mermaid diagrams (3 diagrams: backbone, desync sequence, synthesis state machine)
- `docs/plans/2026-03-30-fix-cat5-collection-desync-and-synthesis.md` — implementation plan

**NOT Changed**:
- `backend/state_machine.py` — step transitions unchanged; the `round_advance_pending` handler in section 7c already handled the deferred advance pattern
- `frontend/src/App.jsx` — `showPhotoGallery` condition unchanged; the fix is backend-only
- `frontend/src/hooks/` — no frontend changes needed; auto-advance already handled by `useSessionOrchestration.js`
- T1/T2 synthesis classification — still uses LLM classification as before

**Verification**:
- `cd backend && uv run pytest ../tests/ -v` — 360 passed, 7 skipped
- `cd backend && uv run ruff check turn_handler.py && uv run ruff format turn_handler.py` — clean
- `cd backend && uv run mypy turn_handler.py --ignore-missing-imports` — only pre-existing yaml stub issue

---

## Review Follow-Up: Preserve Response Step in Turn Logs

**Problem**: Reviewing the new comprehensive turn logging changes uncovered one correctness gap in `backend/server.py`. User turns were logged with the correct pre-resolution step, but AI turns were logged with `state.current_step` after `resolve_turn()`. For turns that auto-advance inside the handler, that misattributes the dialogue to the next step. The clearest case is synthesis completion: the generated story belongs to `STEP_4_SYNTHESIS`, but the logged AI row could show `STEP_5_CELEBRATE`.

**Solution**: Kept the new DB schema and state snapshot format, but fixed the AI logging path to use the step attached to the most recently appended AI conversation turn. While touching that path, I also collapsed the duplicated `/api/turn` and `/api/turn-speak` logging blocks into `_log_user_turn()` and `_log_ai_turn()` helpers so both endpoints stay aligned. Added an API regression that proves the logged AI step stays on `STEP_4_SYNTHESIS` even when the persisted state snapshot has already advanced to `STEP_5_CELEBRATE`.

**Edits**:
- `backend/server.py` — extracted `_log_user_turn()`, `_log_ai_turn()`, and `_latest_ai_turn_step()`; AI turn logging now derives `step` from conversation history instead of post-resolution `state.current_step`
- `tests/test_api.py` — added a synthesis auto-advance regression covering the AI log `step` vs `state_snapshot.current_step` distinction
- `HANDOFF.md` — added this review follow-up entry

**NOT Changed**:
- `backend/db.py` schema/migration work — reviewed and kept as-is
- Hook-turn logging on all three start paths — kept as-is
- `tests/test_deep_link.py` logging stub update — reviewed and kept as-is
- Frontend code — unchanged

**Verification**:
- `uv run pytest tests/test_api.py tests/test_deep_link.py tests/test_entity_registry.py tests/test_state_machine.py tests/test_turn_handler.py tests/test_visual_agent.py -q` — PASS (`150 passed, 1 skipped`)
- `uv run ruff check backend/db.py backend/server.py backend/agents/script_agent.py backend/entity_registry.py backend/turn_handler.py tests/test_api.py tests/test_deep_link.py tests/test_entity_registry.py tests/test_state_machine.py tests/test_turn_handler.py tests/test_visual_agent.py` — PASS
- `uv run ruff format --check backend/db.py backend/server.py backend/agents/script_agent.py backend/entity_registry.py backend/turn_handler.py tests/test_api.py tests/test_deep_link.py tests/test_entity_registry.py tests/test_state_machine.py tests/test_turn_handler.py tests/test_visual_agent.py` — PASS

---

## Comprehensive Turn Logging: User Turns + State Snapshots

**Problem**: The `turns` table only logged AI responses (`role = "ai"`). User input (child speech, silence, photo picks) and internal state machine context (`current_step`, `collection_phase`, `synthesis_phase`, etc.) were not captured. This made post-session debugging extremely difficult — the synthesis gap analysis for session `a6425e09` required cross-referencing agent logs, timestamps, and code to reconstruct what the child did and what state transitions occurred. Design plan in `docs/plans/2026-03-28-comprehensive-turn-logging.md`.

**Solution**: Extended the `turns` table with 3 new nullable columns (`photo_id`, `step`, `state_snapshot`), added user turn logging before `resolve_turn()` in both `/api/turn` and `/api/turn-speak`, enhanced existing AI turn logging with state context, and logged the first hook turn from all 3 start endpoints.

**Edits**:
- `backend/db.py` — added `photo_id TEXT`, `step TEXT`, `state_snapshot TEXT` columns to `turns` table schema; added `_MIGRATIONS` list with `ALTER TABLE` statements for existing DBs; updated `log_turn()` signature and INSERT to include new columns
- `backend/server.py` — added `_build_state_snapshot()` helper; added `_log_hook_turn()` helper called from all 3 start endpoints; added user turn `log_turn()` call before `resolve_turn()` in `/api/turn` and `/api/turn-speak`; enhanced AI turn `log_turn()` calls with `step` and `state_snapshot`
- `tests/test_api.py` — added `TestTurnLogging` class with 3 tests: user+AI turn pair with state snapshots, photo_id capture for collection turns, silence logging
- `tests/test_deep_link.py` — added `fake_log_turn` mock to match the new hook turn logging in start-deep-link endpoint

**NOT Changed**:
- `backend/turn_handler.py` — no changes to turn resolution logic
- `agent_logs` table — unchanged; agent-level timing/token logging is separate from turn logging
- Frontend code — no changes
- Existing turn data — migration uses `ALTER TABLE ADD COLUMN` with NULL defaults, preserving all existing rows

**Verification**:
- `uv run pytest tests/ backend/tests/ --ignore=backend/tests/test_ai_quality.py -q` — PASS (361 passed, 12 skipped)
- `uv run ruff check backend/db.py backend/server.py tests/test_api.py tests/test_deep_link.py` — PASS
- `uv run ruff format --check backend/db.py backend/server.py tests/test_api.py tests/test_deep_link.py` — PASS

---

## Review Follow-Up: Synthesis Regression Coverage and Summary Slice Guardrails

**Problem**: Picking up the in-progress handoff entry for synthesis phase filtering, item suggestion validation, and synthesis silence handling showed that the main code changes were reasonable, but the regression coverage was still thin in three places. There was no direct test proving inactive synthesis phase sections are stripped from `cat5_step4_synthesis.md`, no unit coverage for the new silence shortcuts in synthesis `evaluate` and `improve`, and no assertion that Cat1 API summaries now trim `round_scenarios` down to `play_rounds`.

**Solution**: Kept the reviewed backend behavior unchanged and hardened the changed test surface instead. Added direct regressions for phase filtering, both synthesis silence bypass paths, and the Cat1 summary slice. Also removed a now-unnecessary `type: ignore` in `script_agent.py` by using a concrete `re.Match[str]` annotation.

**Edits**:
- `tests/test_entity_registry.py` — added coverage that Cat1 summaries expose exactly `round_count` scenarios and that `STEP_4_SYNTHESIS` keeps only the active `GENERATE` phase instructions
- `tests/test_turn_handler.py` — added regressions proving silence in synthesis `evaluate` and `improve` skips `_classify_story_response()` and goes straight to AI generation
- `backend/agents/script_agent.py` — replaced the local regex callback annotation with `re.Match[str]` and removed the `type: ignore`
- `HANDOFF.md` — added this review follow-up entry

**NOT Changed**:
- `backend/turn_handler.py` synthesis silence logic — reviewed and kept as-is
- `backend/entity_registry.py` Cat1 summary slicing — reviewed and kept as-is
- `tests/test_state_machine.py` and `tests/test_visual_agent.py` — reviewed current assertion updates and left unchanged
- Frontend code — unchanged

**Verification**:
- `uv run pytest tests/test_entity_registry.py tests/test_state_machine.py tests/test_turn_handler.py tests/test_visual_agent.py -q` — PASS (`114 passed, 1 skipped`)
- `uv run ruff check backend/agents/script_agent.py backend/entity_registry.py backend/turn_handler.py tests/test_entity_registry.py tests/test_state_machine.py tests/test_turn_handler.py tests/test_visual_agent.py` — PASS
- `uv run ruff format --check backend/agents/script_agent.py backend/entity_registry.py backend/turn_handler.py tests/test_entity_registry.py tests/test_state_machine.py tests/test_turn_handler.py tests/test_visual_agent.py` — PASS

---
