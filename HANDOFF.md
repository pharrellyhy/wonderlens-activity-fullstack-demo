# Session Handoff

Last updated: 2026-03-27

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

## Review Follow-Up: Final Phase-B Guidance Loop Now Works

**Problem**: Reviewing the newest prompt/turn-flow commit (`afdc03c`, `fix(prompts): simplify T0 naming flow, allow Phase B guidance loops`) exposed one concrete control-flow mismatch in `backend/turn_handler.py`. The commit message and updated prompt assets both say Cat5 Phase B can stay in detail mode for up to three guidance exchanges when the AI sets `stay_on_step=true`, but the runtime still auto-advanced immediately on the final collected item because the `remaining_count == 0` branch ran before the new guidance-loop check. That meant the final naming/synthesis bridge ignored the newly added T0 guidance path on the very case the prompt change was trying to improve. The local ignored turn-handler tests also had no regression covering this new final-item loop behavior.

**Solution**: Kept the new prompt direction intact, but fixed the runtime ordering so final-item Phase B honors `stay_on_step` before auto-advancing into synthesis. `resolve_turn()` now checks the guidance-loop branch first and only sets `round_advance_pending` for the last item once the child no longer needs another detail exchange or the 3-exchange cap is reached. I also added a focused local regression proving that the final Phase B exchange stays in detail mode when the AI explicitly asks for another texture-guidance turn.

**Edits**:
- `backend/turn_handler.py` — reordered the final-item Phase B logic so `stay_on_step` is respected before the `remaining_count == 0` auto-advance path; the existing 3-exchange cap is preserved
- local `tests/test_turn_handler.py` — added a regression for the final-item guidance-loop case so the new Cat5 Phase B behavior is locked in during local review runs
- `HANDOFF.md` — added this review follow-up entry and refreshed the header date

**NOT Changed**:
- `backend/skills/planner_system.md` and the Cat5 collection prompt fragments updated by `afdc03c` — reviewed and left unchanged in this follow-up
- `backend/schemas/session_state.py` `detail_exchange_count` field — reviewed and left unchanged; only the consuming control flow needed correction
- Frontend code — unchanged

**Verification**:
- `uv run pytest tests/test_turn_handler.py -q -k 'final_detail_guidance_loop_stays_on_detail_before_synthesis'` — PASS (`1 passed, 22 deselected`)
- `uv run pytest tests/test_turn_handler.py -q` — PASS (`23 passed`)
- `uv run ruff check backend/turn_handler.py tests/test_turn_handler.py` — PASS
- `uv run ruff format --check backend/turn_handler.py tests/test_turn_handler.py` — PASS

---

## Review Follow-Up: Enforce Plan-Aware Retry Paths

**Problem**: Reviewing the last two-pass generation commits against `docs/plans/2026-03-26-two-pass-generation.md` exposed a concrete gap in the new validation path. `backend/turn_handler.py` added `_validate_plan()` and logged `speaker_violation` / `planner_failure`, but `_generate_with_retry()` still accepted the turn whenever the older `_validate_response()` checks passed. That meant the new two-pass flow could keep a response that violated `do_not_suggest_items`, and it could also keep a detail-phase plan with no `sensory_observation` instead of forcing a re-plan. While tightening local coverage around that path, the new `last_plan` / `retry_speaker_turn` accesses also revealed that the local ignored `tests/test_turn_handler.py` was using overly-generic `AsyncMock()` agents that emitted unawaited-coroutine warnings during pytest cleanup.

**Solution**: Turned the new plan-aware verdicts into real retry decisions. `_generate_with_retry()` now treats `speaker_violation` as a speaker-only retry that reuses the same `TurnPlan` with a corrective hint, and treats `planner_failure` as a full retry that pushes a correction back through the normal planner path. I also simplified the speaker-side prompt assembly by extracting shared prompt/user-prompt helpers and added a `retry_speaker_turn()` entrypoint on `ScriptAgent` so the speaker-only retry path is explicit instead of reaching into private methods. Local review tests now cover both retry branches and use ScriptAgent-shaped mocks so the verification run stays warning-free.

**Edits**:
- `backend/turn_handler.py` — added `_plan_retry_hint()` and changed `_generate_with_retry()` so `_validate_plan()` failures no longer act as diagnostics only; `speaker_violation` now retries the speaker with the same plan, while `planner_failure` forces a full regenerate with a corrective hint
- `backend/agents/script_agent.py` — extracted shared speaker prompt builders, added `_format_words_per_sentence()`, and introduced `retry_speaker_turn()` to support plan-preserving speaker retries without duplicating prompt-building logic
- local `tests/test_turn_handler.py` — added regressions for speaker-only retry vs full re-plan behavior and replaced loose `AsyncMock()` agents with ScriptAgent-shaped mocks to eliminate unawaited-coroutine warnings after the new plan-aware accesses
- `HANDOFF.md` — added this review follow-up entry

**NOT Changed**:
- `backend/agents/planner.py`, `backend/schemas/turn_plan.py`, and the two-pass prompt markdown files — reviewed and left unchanged in this follow-up
- `backend/turn_handler.py` step transition/state machine behavior outside retry validation — unchanged
- Frontend code — unchanged

**Verification**:
- `uv run pytest tests/test_turn_handler.py -q -k 'correct_photo_enters_detail_phase_and_holds_the_round or synthesis_first_visit_generates_prompt'` — PASS (`2 passed, 20 deselected`) and the previous unawaited-coroutine warnings are gone
- `uv run pytest tests/test_turn_handler.py tests/test_planner.py tests/test_turn_plan.py -q` — PASS (`62 passed`)
- `uv run ruff check backend/agents/script_agent.py backend/turn_handler.py tests/test_turn_handler.py` — PASS
- `uv run ruff format --check backend/agents/script_agent.py backend/turn_handler.py tests/test_turn_handler.py` — PASS

---

## Two-Pass Generation (Planner + Speaker)

**Problem**: The single-call Script Agent asks the LLM to simultaneously understand child input, make structural decisions (question type, item suggestions, progress phrasing), track game state, and generate warm age-appropriate language — all in one JSON response. This produces responses where language is right but structure is wrong (suggesting specific items, asking wrong question types, repeating patterns). Structural decisions and creative language compete for the same context window.

**Solution**: Replaced the single Script Agent LLM call with two sequential calls — a Planner that outputs structured JSON (`TurnPlan`) describing WHAT to say, and a Speaker that generates natural dialogue from the plan. Both use the same Qwen 3.5+ model via ALI DashScope. Post-processing validation now runs plan-aware checks. Old single-pass path is preserved as fallback. Design plan in `docs/plans/2026-03-26-two-pass-generation.md`.

**Edits**:
- `backend/schemas/turn_plan.py` — **NEW**: `TurnPlan` Pydantic model with content decisions (celebrate_item, sensory_observation, name_choices, question_type, story_beat), constraints (must_model_first, offer_binary_choice, do_not_suggest_items), tone/format guidance, and screen/audio pass-through fields
- `backend/schemas/__init__.py` — added `TurnPlan` to exports
- `backend/agents/planner.py` — **NEW**: `Planner` class with `plan_turn()` method; builds state context, loads planner prompt template, calls LLM with JSON mode at lower temperature (0.3); reuses `_build_conversation_context`, `_build_creative_slots_text`, `_load_tier_constraints`, `_get_client` from script_agent
- `backend/skills/planner_system.md` — **NEW**: Planner system prompt focused on decisions (no language generation); includes key rules for item suggestion avoidance, T0 scaffolding, progress variation
- `backend/skills/speaker_system.md` — **NEW**: Minimal Speaker system prompt — converts TurnPlan to warm dialogue with tier-appropriate sentence limits
- `backend/agents/script_agent.py` — restructured `ScriptAgent` for two-pass: added `__init__` with `last_plan` attribute; new `_plan_turn()` (calls Planner), `_speak_turn()` (calls Speaker with plan + tier info), `_speak_turn_streaming()` (streaming Speaker for early TTS); `generate_turn()` and `generate_turn_streaming()` now orchestrate planner→speaker→merge with single-pass fallback on failure; original logic preserved in `_generate_turn_single_pass()` and `_generate_turn_streaming_single_pass()`; added `_load_tier_rules_raw()` helper
- `backend/config.py` — added `planner_max_tokens` (400), `planner_temperature` (0.3), `speaker_temperature` (0.7) settings
- `backend/turn_handler.py` — added `TurnPlan` import; added `_validate_plan()` for plan-aware diagnostics (speaker_violation vs planner_failure); `_generate_with_retry()` now reads `script_agent.last_plan` to log plan JSON alongside response on validation failures
- `tests/test_turn_plan.py` — **NEW**: 17 tests for TurnPlan schema (defaults, full construction, validation, JSON roundtrip)
- `tests/test_planner.py` — **NEW**: 23 tests for Planner agent (state context building, prompt assembly, LLM call mocking, plan parsing)

**NOT Changed**:
- `backend/skills/script_turn.md` — existing system prompt unchanged (used by single-pass fallback)
- `backend/skills/step_instructions/` — all step instruction files unchanged
- `backend/state_machine.py` — step flow logic unchanged
- `backend/turn_handler.py` `_validate_response()` — existing post-processing validation unchanged
- `backend/turn_handler.py` `resolve_turn()` — turn resolution flow unchanged; two-pass is transparent to callers
- Frontend code — no changes

**Verification**:
- `uv run pytest tests/test_turn_plan.py tests/test_planner.py tests/test_turn_handler.py -v` — 60 passed
- `uv run ruff check backend/ && uv run ruff format --check backend/` — clean (pre-existing server.py format issue)
- `uv run pytest tests/ -q --ignore=tests/test_ai_quality.py` — 288 passed, 29 failed (all failures pre-existing)

---

## Review Follow-Up: Fix Example-Driven Prompt Interpolation + Tighten Local Coverage

**Problem**: Reviewing the code modified for `docs/plans/example-driven-prompts-implementation.md` exposed one concrete script-agent bug and several stale local tests. The new Cat5 mission prompt introduced `{activity_name}` and `{tier}` placeholders, but `backend/agents/script_agent.py` did not inject either value, so literal braces leaked into the generated prompt text. The new compact tier summary also still emitted raw Python list reprs like `~[5, 10]` and `['simple', 'playful', 'exclamations']`, which makes the prompt noisier than intended. On the local test side, one naming-story fragment assertion still expected the old rule-heavy copy, and the scenario matcher tests were still relying on registry side effects plus old demo-catalog assumptions instead of isolating the current feature-matching path.

**Solution**: Kept the example-driven prompt refactor intact, but fixed the prompt-helper interpolation path and tightened the local review coverage around it. `script_agent.py` now interpolates the new Cat5 mission placeholders and formats tier ranges/styles into compact readable strings. I also moved the helper assertions into existing local test modules, updated the naming-story fragment expectation to the new example-driven copy, and made the scenario matcher tests populate the registry explicitly while checking the intended feature-driven path.

**Edits**:
- `backend/agents/script_agent.py` — added `{activity_name}` and `{tier}` replacements in `_load_step_instructions()` and formatted `words_per_sentence` / `response_style` into prompt-friendly strings inside `_load_tier_constraints()`
- local `tests/test_entity_registry.py` — added regression coverage for fully interpolated Cat5 mission instructions and readable compact tier constraints; updated the naming-story fragment assertion to the new example-driven content
- local `tests/test_scenarios.py` — added coverage for the new `fluffy_expedition_dandelion` scenario asset, populated the registry explicitly via `get_demo_entities()`, and relaxed the ambiguous dot-feature assertion to the current 18-game catalog
- `HANDOFF.md` — added this review follow-up entry

**NOT Changed**:
- Example-driven Cat5 step-instruction markdown files in `backend/skills/step_instructions/` — reviewed and left unchanged in this follow-up
- `backend/turn_handler.py` retry-stat collection/logging — reviewed against the current implementation plan and left unchanged in this pass
- Frontend code — unchanged; this review stayed on backend prompt/helper behavior and local coverage

**Verification**:
- `uv run pytest tests/test_turn_handler.py tests/test_entity_registry.py tests/test_scenarios.py -q` — PASS (`73 passed`)
- `uv run ruff check backend/agents/script_agent.py backend/turn_handler.py tests/test_entity_registry.py tests/test_scenarios.py` — PASS
- `uv run ruff format --check backend/agents/script_agent.py backend/turn_handler.py tests/test_entity_registry.py tests/test_scenarios.py` — PASS

---

## Example-Driven Prompt Refactor (Cat5 Prototype)

**Problem**: The prompt system uses 28 step instruction files with 889 total lines and 65+ rules in the heaviest file. More rules means worse per-rule compliance — the system was in a cycle of: AI violates rule → add more rules → prompt gets longer → AI violates different rule. LLMs are pattern-matching engines; examples are concrete and composable, rules are abstract and competing.

**Solution**: Replaced rule-heavy Cat5 step instructions with a hybrid format: minimal structural rules (~5-7 per step) + few-shot example transcripts per tier (T0/T1/T2). Examples carry tone, scaffolding, sentence length, and conversational style. Code-enforced constraints (state machine, post-processing validation) unchanged. Added retry-rate logging to measure before/after impact. Design plan in `docs/plans/example-driven-prompts.md`, implementation plan in `docs/plans/example-driven-prompts-implementation.md`.

**Edits**:

*Retry-rate logging:*
- `backend/turn_handler.py` — added `_retry_stats` dict, `_record_retry_stat()` helper, and `get_retry_stats()` accessor; logs attempt count + validation outcome after each generation; logs session summary stats at session end

*Cat5 step instruction conversions (all in `backend/skills/step_instructions/`):*
- `cat5_step1_hook.md` (30→32 lines) — GOAL + 3 structural rules + examples for T0/T1/T2 (cold start, child responds, warm start)
- `cat5_step2_mission.md` (68→54 lines) — GOAL + 5 structural rules + examples for accept/decline/silence per tier
- `cat5_step3_collect.md` (125→97 lines) — GOAL + 7 structural rules + ~24 examples covering Phase A/B × correct/wrong/silence × T0/T1/T2
- `cat5_step3_collect__naming_story.md` (39→55 lines) — 2 variant rules + naming-specific examples per tier
- `cat5_step4_synthesis.md` (35→49 lines) — GOAL + 6 structural rules + examples for T0/T1/T2 × ideal/stuck/silent
- `cat5_step4_synthesis__naming_story.md` (96→55 lines) — 3 variant rules + 4-beat story examples per tier
- `cat5_step5_celebrate.md` (23→19 lines) — GOAL + 3 structural rules + 3 tier examples
- `cat5_step6_closing.md` (23→20 lines) — GOAL + 3 structural rules + 3 tier examples with natural concept weaving
- `early_exit.md` (15→22 lines) — GOAL + 2 structural rules + examples with/without collected characters

*System prompt simplification:*
- `backend/skills/script_turn.md` — removed invitational/forbidden language rule block from Section 2 (now in examples)
- `backend/agents/script_agent.py` — simplified `_load_tier_constraints()` from 14-line verbose format to compact 4-line summary with per-tier key rule

*New test scenario:*
- `backend/scenarios/fluffy_expedition_dandelion.yaml` — **NEW**: full Cat5 T0 happy path + wrong photo + silence recovery

**NOT Changed**:
- `backend/turn_handler.py` post-processing validation (`_validate_response`, `_ends_with_open_question`, `_has_model_phrase`) — unchanged
- `backend/state_machine.py` — step flow logic unchanged
- `backend/agents/script_agent.py` template loading (`_load_step_instructions`, `_build_instruction_overlay`, `_build_system_prompt`) — unchanged (format change is transparent)
- Cat1 step instruction files — not converted in this prototype phase
- Cat5 comparison_chart and sorting_game variants — not converted in this prototype phase
- Frontend code — no changes

**Verification**:
- `uv run ruff check .` — PASS
- `uv run ruff format --check .` — PASS
- Template variable audit: all `{variables}` in new files match existing script agent injection points
- Manual: start fluffy_expedition_dandelion session, verify AI responds with example-style tone/scaffolding
- Manual: check retry-rate logs appear in server output after a session

---

## Review Follow-Up: Restore Tier-Specific Silence Timeouts

**Problem**: While reviewing the code modified alongside `docs/plans/education-team-feedback-round2.md`, I found one concrete frontend regression in `frontend/src/hooks/useSilenceTimer.js`: the silence timeout table had been flattened to `20s` for every tier. That diverged from the WonderLens spec and tier rules, which require tier-specific silence handling (`T0=10s`, `T1=8s`, `T2=6s`). Leaving the flattened values in place would make higher tiers noticeably less responsive and violate the project’s age-tier behavior contract.

**Solution**: Restored the documented tier-specific timeout values and added a focused regression test so future review passes catch this contract break immediately.

**Edits**:
- `frontend/src/hooks/useSilenceTimer.js` — restored `T0: 10000`, `T1: 8000`, `T2: 6000`, and the `10000` default fallback instead of the temporary `20000` values
- local `tests/test_education_feedback_contracts.py` — added `test_silence_timer_stays_tier_specific()` to lock the frontend timeout table to the documented tier rules
- `HANDOFF.md` — added this review follow-up entry

**NOT Changed**:
- `frontend/src/hooks/useSessionOrchestration.js` muted-TTS timer-start workaround — reviewed and left intact
- `frontend/src/components/ConversationPanel.jsx`, `frontend/src/components/GameDetailView.jsx`, and `frontend/src/components/ChatBubble.jsx` — reviewed for the newly added progress/detail messaging behavior and left unchanged in this pass
- Prompt/game-content files from the round-2 plan — reviewed separately and left unchanged in this follow-up

**Verification**:
- `uv run pytest tests/test_education_feedback_contracts.py::test_silence_timer_stays_tier_specific -q` — PASS (`1 passed`)
- `uv run pytest tests/test_entity_registry.py tests/test_game_parser.py tests/test_education_feedback_contracts.py -q` — PASS (`82 passed`)
- `uv run ruff check tests/test_education_feedback_contracts.py` — PASS
- `uv run ruff format --check tests/test_education_feedback_contracts.py` — PASS
- `cd frontend && npx eslint src/App.jsx src/components/ChatBubble.jsx src/components/ConversationPanel.jsx src/components/GameDetailView.jsx src/hooks/useSessionOrchestration.js src/hooks/useSilenceTimer.js` — PASS
- `cd frontend && npm run build` — PASS

---

## Education Team Feedback Round 2: Short Phrases, Guided Questions, Synthesis Transition

**Problem**: Second round of education team feedback (`docs/game_demo_feedback_2.txt`) identified three remaining issues: (1) when the AI models a phrase for the child to echo, it's too long to remember (e.g., "SPLASH TIME! This is the best day ever!"), (2) Cat1 voice_acting and storytelling_chain round questions are too open ("If your dinosaur could talk, what would it say?"), and (3) Cat5 synthesis jumps in too abruptly without any transition. Design plan in `docs/plans/education-team-feedback-round2.md`.

**Solution**: Prompt-level fixes only — no code changes.

**Edits**:

*A) Short repeat phrases:*
- `backend/prompts/script_system.md` — added "Short model phrases" rule to Language Simplicity section: 2-4 words max when modeling a phrase a child might echo
- `backend/skills/step_instructions/cat1_step2_rules.md` — added 2-4 word constraint to demo round instruction
- `backend/skills/step_instructions/cat1_step2_rules__voice_acting.md` — changed demo example from "SPLASH TIME! This is the best day EVER!" to just "SPLASH TIME!" with explicit short-phrase requirement

*B) Cat1 open questions:*
- `backend/skills/step_instructions/cat1_step3_round__voice_acting.md` — replaced open "what would it say?" pattern with model-first + binary choice: "I think it would say 'WOW!' Would it say 'WOW!' or something different?"
- `backend/skills/step_instructions/cat1_step3_round__storytelling_chain.md` — replaced open "what happens next?" with 2 concrete choices: "Does the cat find a fish or a ball of yarn?"

*C) Synthesis softer transition:*
- `backend/skills/step_instructions/cat5_step4_synthesis.md` — relaxed "NO celebration, NO recap" to allow ONE short transition sentence (max 8 words) before the creative prompt, e.g., "Now that all your fluffy friends are here..."
- `backend/skills/step_instructions/cat5_step4_synthesis__naming_story.md` — same: allow one brief transition sentence before the 4-beat story

**NOT Changed**:
- Backend code (`state_machine.py`, `turn_handler.py`, `entity_registry.py`) — no logic changes
- Frontend code — no changes
- Other Cat1 mechanic variants (prediction_game, riddle_game, helper_hotline) — unchanged in this pass
- Cat5 comparison_chart and sorting_game synthesis variants — unchanged

**Verification**:
- Start Cat1 voice_acting (dog): verify demo phrase is short (2-4 words), round questions offer model + binary choice
- Start Cat1 storytelling_chain (cat): verify story continuation offers 2 choices, not open "what happens next?"
- Start Cat5 naming_story (dandelion): verify synthesis has a brief transition before launching into the story

---

## Fix Follow-Up: Clarify When Demo Steps Happen In Game Detail View

**Problem**: The education feedback pass made `steps_summary` always visible in `frontend/src/components/GameDetailView.jsx`, which exposed a wording mismatch in the pre-start UI. For games whose first step says things like "Learn the voice acting game with a quick demo round" or "See a quick example of finding something fluffy and giving it a name," the screen showed that promise but did not explain that the demo/example happens only after pressing Start. That made the "How It Works" section read like the demo should already be visible on the detail screen.

**Solution**: Kept the always-visible `steps_summary` list, but added a small inline clarification when the first step mentions a demo or example. The detail view now tells the user "This happens right after you press Start." so the pre-start summary matches the actual flow without changing the game content itself.

**Edits**:
- `frontend/src/components/GameDetailView.jsx` — detects when the first `steps_summary` item mentions a demo/example and shows a short note under the step list clarifying that it happens after Start
- local `tests/test_education_feedback_contracts.py` — added regression coverage for the new GameDetailView clarification
- `HANDOFF.md` — added this follow-up entry

**NOT Changed**:
- Game frontmatter `steps_summary` text — unchanged; the fix is UI clarification rather than content rewrite
- Backend entity summary plumbing (`entity_registry.py`, `game_parser.py`) — unchanged
- Conversation/session flow and prompt behavior after session start — unchanged

**Verification**:
- `uv run pytest tests/test_entity_registry.py tests/test_game_parser.py tests/test_education_feedback_contracts.py -q` — PASS (`81 passed`)
- `uv run ruff check tests/test_education_feedback_contracts.py` — PASS
- `uv run ruff format --check tests/test_education_feedback_contracts.py` — PASS
- `cd frontend && npx eslint src/components/GameDetailView.jsx` — PASS
- `cd frontend && npm run build` — PASS

---

## Fix Follow-Up: TTS Toggle No Longer Perturbs Silence Timer

**Problem**: The previous TTS toggle follow-up made unmuting replay the current AI line by rewinding `lastSpokenIndexRef` inside `frontend/src/hooks/useSessionOrchestration.js`. That made the mute button feel more responsive, but it also introduced a concrete UX regression: if the current turn was already muted and the silence timer had started, turning TTS back on replayed the same AI line and cleared the timer for that turn. The result was that the silence timer appeared to start and stop based on the mute button, which is confusing during child input time.

**Solution**: Simplified the toggle contract so it no longer changes the current turn state. Muting still stops active playback immediately, but unmuting now applies only to subsequent AI lines instead of replaying the current one. That keeps the silence timer tied to turn flow rather than to the footer toggle state.

**Edits**:
- `frontend/src/hooks/useSessionOrchestration.js` — removed the current-message replay rewind from `toggleTts()`; mute still calls `stopTTS()` immediately
- local `tests/test_education_feedback_contracts.py` — replaced the previous unmute-replay assertion with a regression that ensures the hook does not rewind the current AI message on unmute
- `HANDOFF.md` — added this follow-up entry

**NOT Changed**:
- `frontend/src/App.jsx` mute button rendering and labels — unchanged
- `frontend/src/hooks/useTTS.js` playback transport and unlock logic — unchanged
- Silence-timer durations and backend turn orchestration — unchanged

**Verification**:
- `uv run pytest tests/test_entity_registry.py tests/test_game_parser.py tests/test_education_feedback_contracts.py -q` — PASS (`80 passed`)
- `uv run ruff check tests/test_education_feedback_contracts.py` — PASS
- `uv run ruff format --check tests/test_education_feedback_contracts.py` — PASS
- `cd frontend && npx eslint src/App.jsx src/components/GameDetailView.jsx src/hooks/useSessionOrchestration.js` — PASS
- `cd frontend && npm run build` — PASS

---
