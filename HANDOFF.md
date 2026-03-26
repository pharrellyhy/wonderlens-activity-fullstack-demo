# Session Handoff

Last updated: 2026-03-26

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

## Fix Follow-Up: TTS Mute Toggle Replays Current AI Line

**Problem**: After the education feedback pass added a TTS mute toggle, the footer button could appear to stop working in both directions during an active session. The root cause was in `frontend/src/hooks/useSessionOrchestration.js`: the auto-speak effect always advanced `lastSpokenIndexRef` to the latest AI message even when TTS was muted, so toggling TTS back on would rerun the effect but immediately return because that same message was already marked as "spoken." Muting already stopped in-progress speech, but unmuting could not replay the current AI line, which made the toggle feel broken once a line had already appeared on screen.

**Solution**: Kept the toggle UI and muted-TTS timeout cleanup, but fixed the replay contract when turning TTS back on. `toggleTts()` now rewinds `lastSpokenIndexRef` to the previous message index when the current last message is from the AI, which lets the existing auto-speak effect treat the current line as speakable again on unmute. Muting still stops active playback immediately.

**Edits**:
- `frontend/src/hooks/useSessionOrchestration.js` — when toggling TTS from muted to enabled, rewinds `lastSpokenIndexRef` so the current AI line can replay; retains immediate `stopTTS()` behavior when muting
- local `tests/test_education_feedback_contracts.py` — added regression coverage proving the unmute path rewinds the current AI message for replay
- `HANDOFF.md` — added this follow-up entry

**NOT Changed**:
- `frontend/src/App.jsx` footer button wiring and labels — reviewed and left unchanged
- `frontend/src/hooks/useTTS.js` — playback implementation unchanged in this follow-up
- Backend/session API behavior — unchanged; this fix is local to frontend orchestration state

**Verification**:
- `uv run pytest tests/test_entity_registry.py tests/test_game_parser.py tests/test_education_feedback_contracts.py -q` — PASS (`80 passed`)
- `uv run ruff check tests/test_education_feedback_contracts.py` — PASS
- `uv run ruff format --check tests/test_education_feedback_contracts.py tests/test_entity_registry.py` — PASS
- `cd frontend && npx eslint src/App.jsx src/components/GameDetailView.jsx src/hooks/useSessionOrchestration.js` — PASS
- `cd frontend && npm run build` — PASS

---

## Review Follow-Up: Harden Education Feedback Pass + Add Coverage

**Problem**: Reviewing the new education-team feedback implementation exposed one concrete frontend bug and several missing-coverage/runtime gaps in the freshly modified surface. In `frontend/src/hooks/useSessionOrchestration.js`, the new muted-TTS path used `setTimeout(handleSpeakingDone, 0)` without storing or clearing the timeout, so a stale callback could still fire after reset, rerender, or a rapid session restart and incorrectly trigger silence timing or auto-advance from an old active-session closure. The expanded 18-game catalog also introduced a real prompt/runtime gap: Cat5 now includes `sorting_game` (`sound_detective_agency_piano`), but there were no `cat5_step3_collect__sorting_game.md` or `cat5_step4_synthesis__sorting_game.md` fragments for the Script Agent to load. The nearby registry tests were also stale: they still assumed a 5-entity demo-only registry, unique keyword ownership across all games, and older naming-story fragment copy.

**Solution**: Kept the education feedback implementation, but tightened the reviewed runtime edges and brought coverage up to date. The muted-TTS path now owns a timeout ref with explicit cleanup on rerender, reset, and new session starts before scheduling a completion callback. I added the missing Cat5 `sorting_game` collect/synthesis fragments so the new piano activity has the same style-specific prompt path as the other Cat5 activities. I also added focused review coverage for the new plain-language summary metadata and updated the stale registry/fragment assertions to match the current 18-game catalog and revised naming-story prompt contract.

**Edits**:
- `frontend/src/hooks/useSessionOrchestration.js` — added `mutedCompletionTimeoutRef` plus `clearMutedCompletionTimeout()`; clears pending muted-TTS callbacks on rerender, reset, and session start before scheduling a new completion callback
- `backend/skills/step_instructions/cat5_step3_collect__sorting_game.md` — **NEW**: Cat5 per-find collection guidance for `sorting_game`
- `backend/skills/step_instructions/cat5_step4_synthesis__sorting_game.md` — **NEW**: Cat5 synthesis guidance for `sorting_game`
- local `tests/test_education_feedback_contracts.py` — **NEW**: regression coverage for muted-TTS timeout cleanup plus `plain_description`/`steps_summary` propagation into loaded entities and API summaries
- local `tests/test_entity_registry.py` — updated stale registry assumptions to the current 18-game catalog and current naming-story fragment content
- `HANDOFF.md` — added this review follow-up entry

**NOT Changed**:
- `frontend/src/App.jsx` and `frontend/src/components/GameDetailView.jsx` — reviewed against the feedback plan and left unchanged in this follow-up
- `backend/entity_registry.py`, `backend/game_parser.py`, and the 18 game frontmatter files — no further implementation changes were needed after adding focused coverage for the new summary fields
- Prompt-wide language simplification and scaffold wording across the other step-instruction files — reviewed and left as-is in this pass

**Verification**:
- `uv run pytest tests/test_entity_registry.py tests/test_game_parser.py tests/test_education_feedback_contracts.py -q` — PASS (`79 passed`)
- `uv run ruff check backend/entity_registry.py backend/game_parser.py tests/test_entity_registry.py tests/test_education_feedback_contracts.py` — PASS
- `uv run ruff format --check backend/entity_registry.py backend/game_parser.py tests/test_entity_registry.py tests/test_education_feedback_contracts.py` — PASS
- `cd frontend && npx eslint src/App.jsx src/components/GameDetailView.jsx src/hooks/useSessionOrchestration.js` — PASS
- `cd frontend && npm run build` — PASS

---

## Education Team Feedback: Full UX Pass (6 Items)

**Problem**: The education team reviewed the demo and flagged 6 issues: (1) activity flow is unclear and lacks mini-rewards at milestones, (2) GameDetailView is too abstract/metaphorical for testers, (3) AI language is too decorated for kids, (4) TTS auto-play is disruptive, (5) questions are too open-ended, (6) activities lack "game feel." Full feedback in `docs/game_demo_feedback.txt` (Chinese). Design plan in `docs/plans/education-team-feedback.md`.

**Solution**: Prompt-first approach — most changes are in step instruction markdown files, with 2 small frontend changes and backend data additions.

**Edits**:

*Phase 1 — Language Foundation (Change 3):*
- `backend/prompts/script_system.md` — added `## Language Simplicity Rules` section with tier-specific sentence length limits (T0 ~6 words, T1 ~10, T2 ~15), one-metaphor-max rule, everyday vocabulary guidelines
- All 26 files in `backend/skills/step_instructions/` — added one-line language reminder after first heading

*Phase 2 — Scaffold + Model Pattern (Change 5):*
- `backend/skills/step_instructions/cat5_step3_collect.md` — added "model first, then invite" scaffold principle for all tiers; T0 modeling guidance for Phase A; updated silence handler to model + offer 2-3 choices
- `cat5_step3_collect__naming_story.md` — updated unexpected/silence paths to model a name + offer binary choice
- `cat5_step3_collect__comparison_chart.md` — updated unexpected/silence paths to model observation + offer binary
- `cat5_step4_synthesis.md` — added scaffold principle; updated stuck/silence handlers to offer concrete choices
- `cat5_step4_synthesis__naming_story.md` — added scaffolded question requirement (binary, not open-ended)
- `cat5_step4_synthesis__comparison_chart.md` — added T0 binary-only rule for ranking
- `cat1_step3_round.md` — added model-first for hesitation, model + binary for wrong/silence/stuck paths

*Phase 3 — Example Step + Game Feel (Changes 6, 1, 7):*
- `cat5_step2_mission.md` — added "Embedded Example Demonstration" section (demo one round before invitation, 2-3 sentences); added mission acceptance SFX (`mission_accepted`); added item 7 to "You MUST" list
- `cat5_step3_collect.md` — added mission/quest framing note; added progress count celebration on correct photo; added `sfx: slot_fill_chime` per find and `sfx: mission_complete_fanfare` on final; replaced "avoid mechanical counters" with "pair numbers with enthusiasm"
- `cat5_step3_collect__naming_story.md` — added SFX cues to progressive character introductions
- `cat5_step3_collect__comparison_chart.md` — added SFX cues to progressive comparison building
- `cat5_step5_celebrate.md` — added "Mission accomplished!" framing and `sfx: celebration_fanfare`
- `cat1_step3_round.md` — added challenge framing, progress note with `sfx: slot_fill_chime` on good answers
- `cat1_step4_celebrate.md` — added "You beat all rounds!" framing and `sfx: celebration_fanfare`

*Phase 4 — GameDetailView Redesign (Change 2):*
- `backend/entity_registry.py` — added `plain_description: str` and `steps_summary: list[str]` fields to `EntityConfig`; added both to `_build_entity_summary()` dict
- `backend/game_parser.py` — added pass-through of `plain_description` and `steps_summary` from game MD frontmatter
- All 18 files in `backend/games/` — added `plain_description` and `steps_summary` to YAML frontmatter
- `frontend/src/components/GameDetailView.jsx` — replaced metaphor quote with plain-language summary; added expandable "See detailed steps" toggle showing ordered step list; kept role_title badge and IB tags

*Phase 5 — TTS Default Muted (Change 4):*
- `frontend/src/hooks/useSessionOrchestration.js` — added `ttsEnabled` state (default false) with localStorage persistence; wrapped auto-speak effect in `ttsEnabled` condition; when muted, fires `handleSpeakingDone()` via setTimeout so silence timer and auto-advance still work; exports `ttsEnabled` and `toggleTts`
- `frontend/src/App.jsx` — destructured `ttsEnabled` and `toggleTts`; added mute/unmute toggle button in footer

**NOT Changed**:
- `backend/state_machine.py` and `backend/turn_handler.py` — no state machine or turn logic changes
- Agent pipeline (Director, Script, Visual, Recipe Assembler) — unchanged
- Frontend widget components (BadgeAward, ProgressTracker, PhotoGallery) — unchanged
- Tests — no test files modified in this pass

**Verification**:
- `cd backend && uv run ruff check entity_registry.py game_parser.py` — PASS
- `cd backend && uv run ruff format --check entity_registry.py game_parser.py` — PASS
- Manual: Start T0/T1/T2 sessions, verify AI uses shorter plain sentences
- Manual: Start Cat5, verify mission briefing includes example demo before invitation
- Manual: Play through Cat5 collection, verify progress counts with SFX directives
- Manual: Click a game photo, verify plain summary + expandable steps in GameDetailView
- Manual: Start session, verify TTS muted by default, toggle works, silence timer still fires

---
