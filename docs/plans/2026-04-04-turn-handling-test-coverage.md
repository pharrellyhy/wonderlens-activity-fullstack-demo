# Turn Handling Test Coverage Expansion

**Date:** 2026-04-04
**Goal:** Fill the ~28 highest-value test gaps in `backend/turn_handling/` to cover Tier 1 (high-risk) and Tier 2 (decomposition-confidence) code paths.

## Context

After decomposing `turn_handler.py` into `turn_handling/`, existing tests cover ~50% of code paths. The decomposition introduced zero regressions (18 pre-existing failures, 21+39 passing). Now we add tests for the untested paths, organized by module.

## Approach

Add tests to `tests/test_turn_handler.py` (the existing primary test file), reusing its fixtures (`_make_state`, `_make_agent_mock`, `_make_input`, `_mock_turn`, `_make_round_items`). All tests use the legacy path (Turn Director disabled) since the autouse fixture already stubs `turn_director_enabled=False`.

No production code changes. Tests only.

## Test Plan by Module

### rounds.py — Guardrails & advance logic (7 tests)

1. **`test_guardrail_premature_completion_regenerates`**
   - Setup: STEP_3_COLLECT_1, collected_photos=["leaf_heart"] (1 of 3), LLM returns "This is your final treasure!"
   - Assert: `_generate_with_retry` called twice (original + corrective regeneration)
   - Tests: lines 151-172 in rounds.py

2. **`test_guardrail_force_stay_on_step_in_detail_phase`**
   - Setup: STEP_3_COLLECT_1, collection_phase="detail", LLM returns stay_on_step=False
   - Assert: result has stay_on_step behavior (detail question asked, no advance)
   - Tests: lines 174-183 in rounds.py

3. **`test_guardrail_override_stay_when_collection_complete`**
   - Setup: STEP_3_COLLECT_3, collected_photos has 3 items (all collected), collection_phase="photo", LLM returns stay_on_step=True
   - Assert: advances past collection (stay overridden)
   - Tests: lines 185-194 in rounds.py

4. **`test_deferred_advance_resets_flag_and_advances`**
   - Setup: STEP_3_COLLECT_1, round_advance_pending=True, empty turn (no text, no photo, not silent)
   - Assert: round_advance_pending reset to False, state advanced to STEP_3_COLLECT_2
   - Tests: lines 76-120 in rounds.py

5. **`test_cat5_photo_phase_no_input_deterministic_template`**
   - Setup: STEP_3_COLLECT_1, collection_phase="photo", empty turn
   - Assert: response uses deterministic template (ScriptAgent.generate_turn NOT called)
   - Tests: lines 122-132 in rounds.py

6. **`test_cat1_round_defers_advance_to_next_round`**
   - Setup: Cat1, STEP_3_ROUND_1, total_rounds=3, LLM returns stay_on_step=False, child input present
   - Assert: round_advance_pending=True, auto_advance=True (next step is STEP_3_ROUND_2)
   - Tests: lines 205-215 in rounds.py

7. **`test_cat1_round_advances_immediately_to_celebrate`**
   - Setup: Cat1, STEP_3_ROUND_3 (last round), total_rounds=3, LLM returns stay_on_step=False
   - Assert: advances to STEP_4_CELEBRATE (not deferred)
   - Tests: lines 216-222 in rounds.py

### collection.py — Wrong pick handling (4 tests)

8. **`test_first_wrong_pick_stays_on_step`**
   - Setup: STEP_3_COLLECT_1 with round_items, submit wrong photo_id
   - Assert: consecutive_wrong=1, response_type="wrong_photo", stays on step

9. **`test_second_wrong_pick_exits_gracefully`**
   - Setup: Same as above but state.consecutive_wrong=1 already
   - Assert: EARLY_EXIT, status="exited", response_type="graceful_exit"

10. **`test_correct_pick_resets_consecutive_wrong`**
    - Setup: state.consecutive_wrong=1, then submit correct photo_id
    - Assert: consecutive_wrong=0, collection_phase="detail"

11. **`test_no_photo_id_skips_collection_validation`**
    - Setup: STEP_3_COLLECT_1, turn_input with text but no photo_id
    - Assert: resolve_collection_wrong_pick returns None

### synthesis.py — Missing paths (5 tests)

12. **`test_synthesis_decline_in_evaluate_generates_story`**
    - Setup: STEP_4_SYNTHESIS, synthesis_phase="evaluate", child_intent="decline"
    - Assert: synthesis_declines incremented, advances to STEP_5_CELEBRATE

13. **`test_synthesis_off_topic_under_limit_reprompts`**
    - Setup: STEP_4_SYNTHESIS, synthesis_phase="evaluate", child_intent="off_topic", synthesis_prompt_count=1
    - Assert: synthesis_prompt_count=2, stays on STEP_4_SYNTHESIS, does NOT advance

14. **`test_synthesis_off_topic_at_limit_generates`**
    - Setup: Same but synthesis_prompt_count=2
    - Assert: advances to STEP_5_CELEBRATE (generates full story)

15. **`test_synthesis_improve_substantive_good_advances`**
    - Setup: STEP_4_SYNTHESIS, synthesis_phase="improve", non-silent child input, classify returns story_quality="good"
    - Assert: advances to STEP_5_CELEBRATE

16. **`test_synthesis_improve_substantive_weak_generates`**
    - Setup: Same but classify returns story_quality="weak"
    - Assert: synthesis_child_story updated with combined text, advances to STEP_5_CELEBRATE

### generation.py — Error paths & validation helpers (6 tests)

17. **`test_generate_all_attempts_fail_returns_fallback`**
    - Setup: ScriptAgent.generate_turn raises ScriptAgentError 3 times
    - Assert: returns fallback TurnResponse with gentle goodbye, state.status="error"

18. **`test_generate_exhausted_returns_last_response`**
    - Setup: ScriptAgent returns responses that fail plan validation 3 times
    - Assert: returns last response anyway, debug.final_verdict="exhausted"

19. **`test_has_completion_language_matches`**
    - Assert: matches "final treasure", "all found", "mission complete", "collection complete"

20. **`test_has_completion_language_rejects_normal`**
    - Assert: does NOT match "What a treasure!", "Let's find more"

21. **`test_ends_with_open_question_detects_wh_question`**
    - Assert: matches "What does it look like?", "How would you describe it?"

22. **`test_has_model_phrase_detects_scaffolding`**
    - Assert: matches "I think it looks like a cloud", "Maybe it's soft"

### core.py — Dispatcher edge paths (4 tests)

23. **`test_hook_first_visit_generates_prompt`**
    - Setup: STEP_1_HOOK, empty conversation_history (no prior AI turn)
    - Assert: generates response, stays on STEP_1_HOOK (doesn't advance)

24. **`test_single_silence_does_not_exit`**
    - Setup: Any step, is_silent=True, consecutive_silence=0
    - Assert: consecutive_silence=1, NOT EARLY_EXIT, continues normally

25. **`test_celebrate_auto_advances_to_closing`**
    - Setup: Cat5 STEP_5_CELEBRATE, no prior AI turn on this step
    - Assert: generates response, advances to STEP_6_CLOSING

26. **`test_closing_marks_session_completed`**
    - Setup: Cat5 STEP_6_CLOSING, no prior AI turn
    - Assert: state.status="completed"

### helpers.py — History & auto-advance (2 tests)

27. **`test_append_ai_turn_trims_at_history_limit`**
    - Setup: conversation_history already has 8 turns, append 1 more
    - Assert: len(conversation_history) == 8 (oldest trimmed)

28. **`test_should_auto_advance_false_for_closing`**
    - Setup: STEP_5_CLOSING, status="active"
    - Assert: _should_auto_advance returns False

## Verification

After writing all tests:
1. `uv run pytest tests/test_turn_handler.py -q` — all new tests pass
2. `uv run ruff check tests/test_turn_handler.py` — clean
3. `uv run ruff format --check tests/test_turn_handler.py` — clean
