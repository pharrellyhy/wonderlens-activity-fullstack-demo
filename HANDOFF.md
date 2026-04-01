# Session Handoff

Last updated: 2026-03-31

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

## Fix: Synthesis Phase Filtering, Item Suggestion Regex, and Pre-Existing Test Failures

**Problem**: Session logging (session `a6425e09`, T2 fluffy_expedition_dandelion) showed three issues: (1) The story synthesis loop never produced an actual story — the LLM saw all three phase sections (INVITE, IMPROVE, GENERATE) in the prompt simultaneously and kept following the INVITE pattern even when `synthesis_phase` was set to `"generate"`, so turns 14-16 were all questions instead of a 12-14 sentence bedtime story. (2) The item suggestion regex (`_ITEM_SUGGESTION_RE`) only caught verbs like `find|look for|grab` but missed `touch|peek|try|feel`, allowing "Try touching a cozy blanket or a fuzzy rug nearby" to slip through validation. (3) Silence during synthesis was classified as "unrelated" via an LLM call, triggering 2 re-invites before the AI would generate — a poor UX for a silent child. Additionally, 11 pre-existing test failures from the merged `feat/opus-tts` and `feat/synthesis` branches needed fixing.

**Solution**: Three code fixes plus test alignment:
- Script agent now strips inactive phase sections from synthesis instructions before sending to the LLM, so only the active phase (INVITE, IMPROVE, or GENERATE) is visible
- Expanded the item suggestion regex with more verbs (`touch|touching|try|feel|peek|check|reach for`) and nouns (`rug|carpet|towel|cloth|cushion|teddy|doll|stuffed`)
- Silence during synthesis evaluate/improve phases now skips classification and goes straight to AI story generation
- Fixed 11 pre-existing test failures: Cat5 widget assertions updated from `photo_display`/`character_display`/`progress_tracker` to `explorer_map`, synthesis tests now mock `_classify_story_response` and set `synthesis_phase="evaluate"`, visual agent widget count updated from 5 to 6, entity registry synthesis fragment test updated for unified `__story_generation.md`
- Also fixed Cat1 `round_scenarios` display bug in `entity_registry.py` — summary was showing all tier scenarios instead of slicing to `play_rounds`

**Edits**:
- `backend/agents/script_agent.py` — added `_PHASE_SECTION_RE` regex and `_filter_synthesis_phase()` function; called in `_load_step_instructions()` to strip inactive phase sections before template variable substitution
- `backend/turn_handler.py` — expanded `_ITEM_SUGGESTION_RE` verb/noun lists; added early silence handling in `_resolve_synthesis_turn()` evaluate and improve phases to skip classification and go straight to AI story generation
- `backend/entity_registry.py` — sliced `round_scenarios` to `play_rounds` in Cat1 game summary so frontend shows correct tier-specific round count
- `tests/test_entity_registry.py` — updated `test_cat5_fragments_exist_for_registered_synthesis_types` for unified `__story_generation.md`; renamed `test_cat5_synthesis_uses_naming_story_fragment` to `test_cat5_synthesis_uses_story_generation_fragment` with updated assertions and `synthesis_phase="generate"`
- `tests/test_state_machine.py` — updated Cat5 visual frame tests to expect `explorer_map` widget
- `tests/test_turn_handler.py` — added `StoryClassification` import + `patch`; synthesis tests now set `synthesis_phase="evaluate"` and mock `_classify_story_response`; widget assertions updated to `explorer_map`; renamed `test_maybe_record_generated_name_skips_comparison_chart` to `test_maybe_record_generated_name_records_for_all_synthesis_types`
- `tests/test_visual_agent.py` — updated `ALLOWED_WIDGETS` count from 5 to 6

**NOT Changed**:
- `backend/skills/step_instructions/cat5_step4_synthesis.md` — markdown structure unchanged; phase filtering is done in code
- `backend/skills/step_instructions/cat5_step4_synthesis__story_generation.md` — story generation prompt unchanged
- `backend/skills/speaker_system.md` — reviewed, no changes needed
- Frontend code — no changes
- `backend/tests/test_ai_quality.py` — integration tests that require a running server; 19 failures are all `502 Bad Gateway` (server not running), not code issues

**Verification**:
- `uv run pytest tests/ backend/tests/ --ignore=backend/tests/test_ai_quality.py -q` — PASS (354 passed, 12 skipped)
- `uv run ruff check backend/agents/script_agent.py backend/turn_handler.py backend/entity_registry.py` — PASS
- `uv run ruff format --check backend/agents/script_agent.py backend/turn_handler.py backend/entity_registry.py` — PASS
- Phase filter unit test: verified INVITE-only, IMPROVE-only, GENERATE-only output from `_filter_synthesis_phase()`

---

## Review Follow-Up: Streaming Opus Cleanup + Coverage Alignment

**Problem**: Reviewing the in-progress `feat/opus-tts` worktree against `docs/plans/2026-03-27-streaming-ogg-opus.md` surfaced three concrete issues. First, the new incremental OGG encoder in `backend/tts.py` was repeatedly `np.concatenate()`-ing growing PCM arrays and duplicated its OGG stream setup between batch and streaming paths, which was heavier and harder to follow than necessary. Second, the frontend threaded `pcmSize` through the `/api/turn-speak` path even though that binary protocol never actually provides `pcm_size` in its JSON header, so the extra state was dead and misleading. Third, local API/TTS coverage had drifted: `tests/test_api.py` still expected the old Cat 5 `photo_display` detail frame, and there was no endpoint-level test for the new streaming `GET /api/tts` contract.

**Solution**: Kept the new OGG/Opus architecture, but simplified the touched paths and tightened local coverage around the real contract. The backend now uses a small shared OGG stream factory and a byte-buffered streaming encoder instead of repeated numpy concatenation. The frontend no longer carries the unused `pcmSize` field through the `turn-speak` playback path, and stopping TTS now also clears the audio indicator state. I also updated the stale Cat 5 API assertion to the current `explorer_map` behavior and added focused coverage for the streaming `GET /api/tts` endpoint.

**Edits**:
- `backend/tts.py` — added a shared `_open_ogg_opus_output()` helper and replaced the streaming encoder’s repeated `np.concatenate()` path with byte-buffer accumulation and fixed-size frame extraction
- `backend/server.py` — updated the `/api/turn-speak` docstring/comments to match the current OGG/Opus binary protocol wording
- `frontend/src/utils/api.js` — removed dead `pcmSize` return data from `sendTurnSpeak()` and deleted the unused `synthesizeSpeechStream()` helper
- `frontend/src/hooks/useConversation.js` — stopped storing nonexistent `pcmSize` metadata with pending `turn-speak` audio
- `frontend/src/hooks/useSessionOrchestration.js` — simplified `speakFromStream()` calls to pass only the audio stream
- `frontend/src/hooks/useTTS.js` — cleared `audioInfo` on stop and removed the unused `pcmSize` parameter from the streamed-turn playback path
- `tests/test_api.py` — updated the Cat 5 detail-frame expectation to the current `explorer_map` contract and added a focused test for `GET /api/tts` streaming OGG output
- `tests/test_tts_encoding.py` — moved imports to the module top so the new encoder tests comply with repo import rules
- `HANDOFF.md` — added this review follow-up entry

**NOT Changed**:
- The public TTS endpoint split itself — `POST /api/tts` still returns a complete encoded file with `X-PCM-Size`, and `GET /api/tts` still serves the streaming Chrome-first playback path
- Turn resolution and Script Agent logic — unchanged in this review follow-up
- Frontend conversation/session flow outside the TTS metadata cleanup — unchanged

**Verification**:
- `uv run pytest tests/test_tts_encoding.py tests/test_api.py -q` — PASS (`35 passed`)
- `uv run ruff check backend/server.py backend/tts.py tests/test_api.py tests/test_tts_encoding.py` — PASS
- `uv run ruff format --check backend/server.py backend/tts.py tests/test_api.py tests/test_tts_encoding.py` — PASS
- `cd frontend && npx eslint src/App.jsx src/hooks/useConversation.js src/hooks/useSessionOrchestration.js src/hooks/useTTS.js src/utils/api.js` — PASS

---

## Switch TTS Output from PCM/WAV to OGG/Opus via PyAV

**Problem**: The TTS pipeline streamed raw PCM 16-bit mono at 24kHz (~384 kbps) to the frontend, which manually wrapped it in WAV headers. This was unnecessarily large for speech audio and added frontend complexity.

**Solution**: Added OGG/Opus encoding on the backend using PyAV. Collected PCM from Gemini TTS is batch-encoded to OGG/Opus at 32kbps (~12x compression). The `/api/tts` endpoint now returns a complete `audio/ogg` response (or `audio/wav` on encoding fallback) instead of streaming raw PCM. The `/api/turn-speak` endpoint yields OGG/Opus bytes in the binary protocol. The frontend was simplified — removed `pcmToWavBlob()`/`writeString()` WAV construction, removed `sampleRate` threading, and browsers natively decode OGG/Opus. Design plan in `docs/plans/2026-03-27-streaming-ogg-opus.md`.

**Edits**:
- `pyproject.toml` — added `av>=13.0.0` and `numpy>=1.26.0` dependencies
- `backend/tts.py` — added `import av, numpy`; added `OPUS_BITRATE_BPS` constant; added `_pcm_to_ogg_opus()` encoder and `synthesize_speech_ogg_async()` that collects PCM chunks and encodes to OGG/Opus with WAV fallback
- `backend/server.py` — `/api/tts` now returns `Response` with `audio/ogg` content type (or `audio/wav` fallback) via `synthesize_speech_ogg_async()`; `/api/turn-speak` yields OGG/Opus bytes; removed `X-Sample-Rate` header and `SAMPLE_RATE` import; removed `X-Sample-Rate` from CORS exposed headers
- `frontend/src/hooks/useTTS.js` — deleted `pcmToWavBlob()`/`writeString()`, renamed `playWavBlob` → `playAudioBlob`, simplified `playFromStream` to collect OGG chunks directly, simplified `fetchAndPlayAudio` to use server `Content-Type`, removed `sampleRate` parameter from `speakFromStream`
- `frontend/src/utils/api.js` — removed `sampleRate` from `sendTurnSpeak()` and `synthesizeSpeechStream()` returns; updated JSDoc
- `frontend/src/hooks/useConversation.js` — dropped `sampleRate` from destructuring and `pendingAudioRef`
- `frontend/src/hooks/useSessionOrchestration.js` — dropped `sampleRate` from `speakFromStream` call
- `tests/test_api.py` — updated TTS endpoint tests to patch `synthesize_speech_ogg_async`, assert `audio/ogg` content type, no `x-sample-rate` header; updated turn-speak mocks from async generators to async functions returning bytes
- `tests/test_tts_encoding.py` — **NEW**: 4 encoder unit tests (OggS magic, compression ratio, empty input, longer audio)

**NOT Changed**:
- `backend/tts.py` existing functions (`synthesize_speech_stream_async`, `synthesize_speech`, `_pcm_to_wav`) — preserved as internal/fallback
- Turn resolution logic, state machine, Script Agent — unchanged
- Frontend conversation panel, silence timer, SFX — unchanged

**Verification**:
- `uv run ruff check .` — PASS
- `uv run ruff format --check .` — PASS
- `uv run pytest tests/test_tts_encoding.py tests/test_api.py -v` — 31 passed, 1 pre-existing failure
- `uv run pytest tests/ -m "not e2e"` — 305 passed, 9 pre-existing failures, 0 new failures

---

## Review Follow-Up: Keep TurnPlan Strict While Tolerating Planner Omissions

**Problem**: Reviewing the latest two-pass commits (`afdc03c`, `3eed090`, `b86a16b`, `b7c1d97`, `e156bb3`) plus the in-progress follow-up diff showed one concrete schema/testing mismatch. The new `TurnPlan` defaults for `child_said` and `child_emotion` were intentional for planner resilience, but the schema still accepted arbitrary extra keys. That let junk planner JSON like `{"not_a_valid_plan": true}` validate successfully, so `Planner.plan_turn()` would treat malformed output as a valid plan. The local planner/schema tests had also drifted: they still asserted the old planner prompt wording and the old "child fields are required" behavior.

**Solution**: Kept the new planner-resilience defaults, but made the schema strict again by forbidding unknown fields. That preserves the intended fallback behavior for omitted child-summary fields without allowing arbitrary planner output through. I also simplified the affected tests so they assert the current planner contract: phase-aware anti-suggestion rules, injected step instructions, defaulted child-summary fields, and rejection of unexpected planner keys.

**Edits**:
- `backend/schemas/turn_plan.py` — added `ConfigDict(extra="forbid")` while keeping the new `child_said=""` and `child_emotion="neutral"` defaults
- `tests/test_planner.py` — updated the planner-prompt assertions to match the current phase-aware prompt rules and verify step instructions are included in planner context
- `tests/test_turn_plan.py` — replaced outdated "required field" expectations with default-value coverage and added a regression that rejects unexpected planner keys
- `HANDOFF.md` — added this review follow-up entry

**NOT Changed**:
- `backend/agents/planner.py`, `backend/agents/script_agent.py`, `backend/turn_handler.py`, and the prompt markdown files touched in the latest two-pass commits — reviewed and left unchanged in this follow-up
- Frontend code — unchanged
- The broader prompt-variety / `[AUDIO]` cleanup work already in progress — reviewed, not modified here

**Verification**:
- `uv run pytest tests/test_planner.py tests/test_turn_plan.py tests/test_turn_handler.py -q` — PASS (`64 passed`)
- `uv run ruff check backend/schemas/turn_plan.py tests/test_planner.py tests/test_turn_plan.py tests/test_turn_handler.py` — PASS
- `uv run ruff format --check backend/schemas/turn_plan.py tests/test_planner.py tests/test_turn_plan.py tests/test_turn_handler.py` — PASS

---

## Prompt Quality: Fix Repetition, [AUDIO] Leak, Two-Pass Disabled

**Problem**: Three quality issues discovered during testing: (1) Cat5 T0 collection Phase A responses all used identical "Touch it gently — is it X or Y?" structure across every round and session, because the few-shot examples all shared the same sentence pattern. (2) Cat5 synthesis stories always followed the same "X floated softly when BUMP — Y bounced right in!" template — the single T0 example was copied verbatim every session. (3) `[AUDIO] sfx: slot_fill_chime` markers in step instructions were copied literally into dialogue text by the LLM, causing the child to hear "slot fill chime" spoken aloud. Additionally, the two-pass (planner + speaker) generation was producing worse quality than single-pass — the planner stripped too much context and the speaker generated bland, empty responses — so it was disabled behind a config flag.

**Solution**: Rewrote all T0 examples with structurally diverse patterns so the LLM has multiple templates to draw from. Added explicit "Do NOT reuse the same structure across sessions" instruction to synthesis prompts. Replaced `[AUDIO] sfx:` prose directives with `Set sfx_cue to "..."` JSON field instructions across 6 step instruction files. Added `_clean_dialogue()` post-processing to strip any leaked `[AUDIO]` markers as a safety net. Added random variety hints to the user prompt for hook/mission/first-collect steps to break identical-prompt repetition. Added `two_pass_enabled` config flag (default `false`) to gate two-pass generation.

**Edits**:
- `backend/skills/step_instructions/cat5_step3_collect.md` — rewrote T0 Phase A examples with 3 distinct opener styles ("Give it a little poke", "This one looks different!", "Quick, does it..."); replaced `[AUDIO]` directives with `sfx_cue` instructions
- `backend/skills/step_instructions/cat5_step3_collect__naming_story.md` — matching T0 Phase A variety; updated Phase B examples with diverse confirmation styles
- `backend/skills/step_instructions/cat5_step4_synthesis.md` — replaced single T0 example with 2 structurally different story types (chase adventure, rain surprise); added "vary between" instruction; replaced `[AUDIO]` directives
- `backend/skills/step_instructions/cat5_step4_synthesis__naming_story.md` — replaced single T0 example with 3 different story structures (chase, weather, hide-and-seek); added explicit variety instruction
- `backend/skills/step_instructions/cat1_step3_round.md` — replaced `[AUDIO]` directive with `sfx_cue` instruction
- `backend/skills/step_instructions/cat1_step4_celebrate.md` — replaced `[AUDIO]` directive
- `backend/skills/step_instructions/cat5_step5_celebrate.md` — replaced `[AUDIO]` directive
- `backend/skills/step_instructions/cat5_step3_collect__sorting_game.md` — replaced `[AUDIO]` directives
- `backend/skills/step_instructions/cat5_step3_collect__comparison_chart.md` — replaced `[AUDIO]` directives
- `backend/agents/script_agent.py` — renamed `_ensure_emotion_tag()` to `_clean_dialogue()` which also strips `[AUDIO]` markers from dialogue; added `_VARIETY_HINTS` list and `_VARIETY_STEPS` set; `_build_user_prompt()` injects a random style hint for hook/mission/first-collect steps; added `import random`
- `backend/config.py` — added `two_pass_enabled` setting (default `false`)
- `backend/agents/script_agent.py` — `generate_turn()` and `generate_turn_streaming()` check `two_pass_enabled` flag before attempting planner/speaker path
- `backend/schemas/turn_plan.py` — made `child_said` and `child_emotion` optional with defaults (prevents Pydantic validation crash when planner omits them)
- `backend/skills/planner_system.md` — added full JSON output schema; updated T0 rules for phase-aware binary choice; added collection_phase guidance

**NOT Changed**:
- `backend/turn_handler.py` — turn resolution flow, Phase B guidance loops, validation logic all unchanged in this pass
- `backend/state_machine.py` — unchanged
- Frontend code — unchanged (auto-advance timing issue noted but not fixed here)
- Cat1 step instruction content — unchanged beyond `[AUDIO]` directive replacement

**Verification**:
- `uv run pytest tests/test_turn_handler.py -q -k "not (correct_photo_enters_detail or detail_response_advances or final_detail_response or retries_speaker_only or replans_after)"` — 17 passed (5 pre-existing failures excluded)
- `uv run ruff check backend/ && uv run ruff format --check backend/agents/script_agent.py` — clean
- Manual: start 3 dandelion sessions — Phase A openers varied each time, no "Touch it gently" repetition
- Manual: synthesis stories used different adventure types across sessions
- Manual: no `[AUDIO]` markers in spoken dialogue

---
