# Fix Cat5 Collection Desync + Synthesis Classification — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix two Cat5 bugs: (1) collection phase desync where photo grid appears while AI is still naming the previous round's character, and (2) synthesis classification too strict for T0 children (ages 2-4).

**Architecture:** Both fixes are in `backend/turn_handler.py`. Bug 1 changes 3 lines to use the existing `round_advance_pending` + `auto_advance` pattern. Bug 2 adds a T0 early-return before the LLM classification call. One existing test must be updated; two new tests are added.

**Tech Stack:** Python 3.12+, pytest, pytest-mock

**Spec:** `docs/plans/2026-03-30-cat5-workflow-diagnosis.md`

---

### Task 1: Fix collection phase desync (Bug 1)

**Files:**
- Modify: `backend/turn_handler.py:1114-1125`
- Modify: `tests/test_turn_handler.py:230-259` (update existing test)
- Test: `tests/test_turn_handler.py` (new test)

- [ ] **Step 1: Update the existing test to expect deferred advance**

The test `test_detail_response_advances_to_next_round` (line 231) currently asserts the old (buggy) behavior. Update it to expect the new `round_advance_pending` + `auto_advance` pattern — same pattern already tested in `test_final_detail_response_auto_advances_into_synthesis_prompt` (line 263).

In `tests/test_turn_handler.py`, replace lines 249-259:

```python
    result = await resolve_turn(state, _make_input(text="like a cloud"), agent)

    # First response: naming dialogue, state still on COLLECT_1 detail
    assert state.current_step == "STEP_3_COLLECT_1"
    assert state.collection_phase == "detail"
    assert state.round_advance_pending is True
    assert result.auto_advance is True
    assert result.turn_response.dialogue == "Cloud Puff! What a perfect name."
    assert state.collected_details == ["like a cloud"]
    assert state.collected_names == ["Cloud Puff"]

    # Follow-up auto-advance: now flips to COLLECT_2 photo mode
    agent.generate_turn = AsyncMock(
        return_value=_mock_turn(dialogue="Would you like to find the next one?")
    )
    follow_up = await resolve_turn(state, _make_input(), agent)

    assert state.current_step == "STEP_3_COLLECT_2"
    assert state.current_round == 2
    assert state.collection_phase == "photo"
    assert follow_up.screen_frame.widget == "explorer_map"
    assert follow_up.auto_advance is False
    assert follow_up.response_type == "round"
```

- [ ] **Step 2: Run the updated test to verify it fails**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py::test_detail_response_advances_to_next_round -v`
Expected: FAIL — the old code still advances immediately

- [ ] **Step 3: Apply the fix in turn_handler.py**

In `backend/turn_handler.py`, replace lines 1114-1125:

```python
        # Detail phase complete — defer advance to next empty turn so the
        # naming dialogue plays while the child still sees the detail screen.
        state.round_advance_pending = True
        state.detail_exchange_count = 0

        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=True,
            response_type=response_type,
            error_exit=state.status == "error",
        )
```

This mirrors the existing `remaining_count == 0` pattern at lines 1102-1112. The `round_advance_pending` flag is already processed by section 7c (lines 1129-1133) which correctly resets `collection_phase = "photo"` and calls `_advance_state()` on the next empty turn.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py::test_detail_response_advances_to_next_round -v`
Expected: PASS

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py -v`
Expected: All tests PASS

- [ ] **Step 6: Lint**

Run: `cd backend && uv run ruff check turn_handler.py && uv run ruff format turn_handler.py`

---

### Task 2: Fix synthesis classification for T0 (Bug 2)

**Files:**
- Modify: `backend/turn_handler.py:819-828`
- Test: `tests/test_turn_handler.py` (new test)

- [ ] **Step 1: Write the failing test**

Add a new test in `tests/test_turn_handler.py` after the existing synthesis tests (after line ~427):

```python
@pytest.mark.asyncio
async def test_synthesis_t0_skips_classification_and_expands_seed() -> None:
    """T0 synthesis should skip LLM classification and treat any response as a story seed."""
    state = _make_state(
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        tier="T0",
        synthesis_phase="evaluate",
        synthesis_prompt_count=1,
        collected_names=["Cloud Puff", "Mossy Dot"],
        conversation_history=[
            ConversationTurn(
                role="ai", text="Would you like to make up a story?", step="STEP_4_SYNTHESIS"
            ),
        ],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        return_value=_mock_turn(dialogue="Cloud Puff bounced over to Mossy Dot and they snuggled up.")
    )

    with patch("turn_handler._classify_story_response", new=AsyncMock()) as mock_classify:
        result = await resolve_turn(state, _make_input(text="moss go sleep"), agent)

    # LLM classification should NOT be called for T0
    mock_classify.assert_not_called()
    # Should route to generate phase (AI expands the seed)
    assert state.synthesis_phase == "generate"
    assert state.synthesis_child_story == "moss go sleep"
    assert state.current_step == "STEP_5_CELEBRATE"
    assert result.auto_advance is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py::test_synthesis_t0_skips_classification_and_expands_seed -v`
Expected: FAIL — `mock_classify` is currently called

- [ ] **Step 3: Write the fix in turn_handler.py**

In `backend/turn_handler.py`, in the `_resolve_synthesis_turn` function, add a T0 early-return **before** the `_classify_story_response` call (after the silence check at line 826, before line 828):

```python
        # T0 (ages 2-4): skip LLM classification — treat any non-silent
        # response as a story seed and let the AI expand it.
        if state.tier == "T0":
            state.synthesis_child_story = child_text
            state.synthesis_phase = "generate"
            turn_response = await _generate_with_retry(script_agent, state)
            return _synthesis_result(state, turn_response, advance=True)
```

This leverages the existing T0 weak-story expansion at the generate phase. No new code paths are introduced — the AI already knows how to expand a child's seed into a full story when `synthesis_phase == "generate"` and `synthesis_child_story` is set.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py::test_synthesis_t0_skips_classification_and_expands_seed -v`
Expected: PASS

- [ ] **Step 5: Also verify silence still works for T0**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py::test_synthesis_evaluate_silence_skips_classification_and_generates -v`
Expected: PASS (silence check is above our new code)

- [ ] **Step 6: Run full test suite**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py -v`
Expected: All tests PASS

- [ ] **Step 7: Lint**

Run: `cd backend && uv run ruff check turn_handler.py && uv run ruff format turn_handler.py`

---

### Task 3: Change exception fallback to fail-safe (Bug 2 hardening)

**Files:**
- Modify: `backend/turn_handler.py:580-586`
- Test: `tests/test_turn_handler.py` (new test)

- [ ] **Step 1: Write the failing test**

Add a test that verifies the fallback on classification error is `story_attempt(weak)` not `unrelated`:

```python
@pytest.mark.asyncio
async def test_synthesis_classification_failure_defaults_to_story_attempt() -> None:
    """If the classification LLM fails, default to story_attempt(weak) not unrelated."""
    state = _make_state(
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        tier="T1",
        synthesis_phase="evaluate",
        synthesis_prompt_count=1,
        collected_names=["Cloud Puff"],
        conversation_history=[
            ConversationTurn(
                role="ai", text="Tell me a story!", step="STEP_4_SYNTHESIS"
            ),
        ],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        return_value=_mock_turn(dialogue="What happened next?")
    )

    # Force classification to raise an exception
    mock_classify = AsyncMock(side_effect=RuntimeError("LLM timeout"))
    with patch("turn_handler._classify_story_response", mock_classify):
        result = await resolve_turn(state, _make_input(text="cloud puff danced"), agent)

    # Should treat as weak story (T1 → improve phase), NOT as unrelated
    assert state.synthesis_phase == "improve"
    assert state.synthesis_child_story == "cloud puff danced"
    assert result.auto_advance is False
```

Note: This test uses T1 (not T0) because T0 now skips classification entirely (Task 2). For T1+, the fallback matters.

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py::test_synthesis_classification_failure_defaults_to_story_attempt -v`
Expected: FAIL — current fallback returns `unrelated`

- [ ] **Step 3: Apply the fix**

In `backend/turn_handler.py`, replace lines 580-586 (the except block in `_classify_story_response`):

```python
    except Exception:
        logger.warning("Story classification LLM call failed, defaulting to story_attempt(weak)")
        return StoryClassification(
            classification="story_attempt",
            is_related_to_collection=True,
            story_quality="weak",
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py::test_synthesis_classification_failure_defaults_to_story_attempt -v`
Expected: PASS

- [ ] **Step 5: Run full test suite + type check**

Run: `cd backend && uv run pytest ../tests/ -v && uv run ruff check turn_handler.py && uv run ruff format turn_handler.py && uv run mypy turn_handler.py`
Expected: All pass

---

## Verification

After all tasks complete:

1. **Unit tests:** `cd backend && uv run pytest ../tests/test_turn_handler.py -v` — all pass
2. **Full test suite:** `cd backend && uv run pytest ../tests/ -v` — no regressions
3. **Type check:** `cd backend && uv run mypy turn_handler.py`
4. **Manual test (Bug 1):** Start a Cat5 session, complete Phase B detail → verify the naming dialogue plays while ExplorerMap still shows the character, then photo grid appears after TTS finishes
5. **Manual test (Bug 2):** Start a T0 Cat5 session, reach synthesis, type a short response like "moss sleep" → verify AI immediately expands into a story without re-inviting
