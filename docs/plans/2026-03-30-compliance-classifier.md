# Compliance Classifier — Dialogue-State Mismatch Detection & Auto-Advancement

## Context

The Script Agent (Gemini 2.0 Flash) sometimes generates dialogue that doesn't match the current game state during collection steps. Example from a real session:

```
[amazed] A woolly caterpillar! You found Fuzzy Wump to join Cloudy Puff! One more fluffy friend is hiding nearby—can you find it?
let's go
[curious] I think this feels fuzzy like a bunny! Is it soft like Cloudy Puff or fuzzy like a bunny?
[excited] We need one more fluffy friend to finish our team! Can you find something soft hiding nearby?
```

The AI generates a detail question ("Is it soft...?") during photo phase when no item has been found, then repeats the "find next" prompt. The current system retries up to 3 times with corrective hints but cannot break the loop because retries don't change the game state. This causes the game to feel stuck and repetitive.

**Solution:** A lightweight LLM classifier that runs after dialogue generation during collection steps. When the classifier detects a mismatch with high confidence, the turn handler advances the state machine to match the LLM's intent and regenerates fresh dialogue — breaking the repetition loop.

**Scope:** All game categories (Cat5 collection + Cat1 rounds). Three mismatch types: premature advancement, wrong-phase dialogue, repetition.

## Architecture

```
_generate_with_retry() → turn_response
       ↓
_classify_dialogue_compliance(state, dialogue, history)
       ↓
  verdict == "match" → return turn_response as-is
  verdict == "premature_advance" (confidence > 0.8) → advance state + regenerate
  verdict == "wrong_phase" (confidence > 0.8) → regenerate with corrective hint
  verdict == "repetition" (confidence > 0.8) → regenerate with variety hint
  classifier failure → return turn_response as-is (fail-open)
```

## Critical Files

| File | Action | Purpose |
|------|--------|---------|
| `backend/schemas/dialogue_compliance.py` | **Create** | `DialogueCompliance` Pydantic model |
| `backend/schemas/__init__.py` | Skip | Not needed — `StoryClassification` also not exported here |
| `backend/turn_handler.py:550-613` | **Pattern to follow** | `_classify_story_response()` — existing LLM classifier |
| `backend/turn_handler.py:1145-1268` | **Modify** | Integration points — add compliance check after generation |
| `backend/config.py:24-58` | **Modify** | Add 2 new settings |
| `backend/config.yaml` | **Modify** | Add default values |
| `tests/test_turn_handler.py` | **Modify** | Add tests for classifier + state advancement |

## Reusable Existing Patterns

- **`_classify_story_response()`** (turn_handler.py:550-613): Same LLM call pattern — `AsyncOpenAI` client, `ali_api_key`/`ali_base_url`, `temperature=0.1`, `max_tokens=150`, `response_format={"type": "json_object"}`, fail-safe default on exception
- **`StoryClassification`** (schemas/story_classification.py): Same Pydantic schema pattern for the new `DialogueCompliance` model
- **`_advance_state()`** (turn_handler.py): Existing function to advance the state machine
- **`round_advance_pending` + `auto_advance`**: Existing deferred-advance pattern (turn_handler.py:1135-1143)
- **`_generate_with_retry()`** (turn_handler.py:647-764): Used for regeneration after state advancement

---

### Task 1: Create DialogueCompliance schema

**Files:**
- Create: `backend/schemas/dialogue_compliance.py`

- [ ] **Step 1: Create the Pydantic model**

Follow the `StoryClassification` pattern at `backend/schemas/story_classification.py`. Create `backend/schemas/dialogue_compliance.py`:

```python
"""Pydantic schema for classifying dialogue-state compliance during collection steps."""

from typing import Literal

from pydantic import BaseModel, Field


class DialogueCompliance(BaseModel):
    """Result of classifying whether AI dialogue matches the current game state."""

    verdict: Literal["match", "premature_advance", "wrong_phase", "repetition"] = Field(
        description="Whether the dialogue aligns with the current game state"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Classifier confidence in the verdict (0.0-1.0)",
    )
    explanation: str = Field(
        default="",
        description="Brief explanation for logging",
    )
```

- [ ] **Step 2: Verify import works**

Run: `cd backend && uv run python -c "from schemas.dialogue_compliance import DialogueCompliance; print(DialogueCompliance(verdict='match', confidence=1.0))"`

---

### Task 2: Add config settings

**Files:**
- Modify: `backend/config.py:50-58`
- Modify: `backend/config.yaml`

- [ ] **Step 1: Add settings to config.py**

In `backend/config.py`, add two new settings after line 56 (`max_retries`):

```python
    compliance_classifier_enabled: bool = bool(_yaml_config.get("compliance_classifier_enabled", True))
    compliance_confidence_threshold: float = float(_yaml_config.get("compliance_confidence_threshold", 0.8))
```

- [ ] **Step 2: Add defaults to config.yaml**

Add to `backend/config.yaml`:

```yaml
compliance_classifier_enabled: true
compliance_confidence_threshold: 0.8
```

- [ ] **Step 3: Verify settings load**

Run: `cd backend && uv run python -c "from config import get_settings; s = get_settings(); print(s.compliance_classifier_enabled, s.compliance_confidence_threshold)"`

---

### Task 3: Implement the classifier function

**Files:**
- Modify: `backend/turn_handler.py` (add function after `_classify_story_response` at line ~614)

- [ ] **Step 1: Write failing test**

Add to `tests/test_turn_handler.py`:

```python
@pytest.mark.asyncio
async def test_classify_dialogue_compliance_premature_advance() -> None:
    """Classifier should detect 'find next' dialogue during detail phase."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        collection_phase="detail",
        detail_exchange_count=0,
        collected_photos=["photo_1"],
        total_rounds=3,
        template_type="cat5",
    )
    dialogue = "One more fluffy friend is hiding nearby—can you find it?"
    history = [
        ConversationTurn(role="ai", text="What does it feel like?", step="STEP_3_COLLECT_1"),
    ]

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "verdict": "premature_advance",
        "confidence": 0.95,
        "explanation": "Dialogue asks to find next item but we are in detail phase",
    })

    with patch("turn_handler.AsyncOpenAI") as MockClient:
        instance = AsyncMock()
        instance.chat.completions.create = AsyncMock(return_value=mock_response)
        MockClient.return_value = instance
        result = await _classify_dialogue_compliance(state, dialogue, history)

    assert result.verdict == "premature_advance"
    assert result.confidence >= 0.9
```

- [ ] **Step 2: Run test to see it fail**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py::test_classify_dialogue_compliance_premature_advance -v`

- [ ] **Step 3: Implement `_classify_dialogue_compliance()`**

Add after `_classify_story_response()` (line ~614) in `backend/turn_handler.py`. Follow the same pattern:

```python
async def _classify_dialogue_compliance(
    state: SessionStateModel,
    dialogue: str,
    recent_history: list[ConversationTurn],
) -> DialogueCompliance:
    """Classify whether AI dialogue matches the current game state.

    Uses a lightweight LLM call to detect phase mismatches, premature
    advancement, and repetition during collection/round steps.

    Returns DialogueCompliance with verdict="match" on failure (fail-open).
    """
    # Build state context for the classifier
    if state.template_type == "cat5":
        state_ctx = (
            f"Game type: Cat5 (collection game)\n"
            f"Step: {state.current_step}\n"
            f"Collection phase: {state.collection_phase} "
            f"({'child should be exploring/finding an item' if state.collection_phase == 'photo' else 'child found an item, AI should ask about its texture/appearance'})\n"
            f"Round: {state.current_round} of {state.total_rounds}\n"
            f"Items collected: {len(state.collected_photos)} of {state.total_rounds}\n"
            f"Detail exchanges this round: {state.detail_exchange_count}"
        )
    else:
        state_ctx = (
            f"Game type: Cat1 (round-based voice acting)\n"
            f"Step: {state.current_step}\n"
            f"Round: {state.current_round} of {state.total_rounds}"
        )

    history_text = "\n".join(
        f"  {t.role}: {t.text[:100]}" for t in recent_history[-3:]
    ) if recent_history else "(no recent history)"

    prompt = (
        f"You are a compliance checker for a children's game. Determine whether the "
        f"AI's dialogue matches the current game state.\n\n"
        f"Current state:\n{state_ctx}\n\n"
        f"Recent conversation:\n{history_text}\n\n"
        f'AI generated: "{dialogue}"\n\n'
        f"Classify the dialogue:\n"
        f'- "match": Dialogue fits the current phase and game state\n'
        f'- "premature_advance": Dialogue encourages finding the NEXT item when '
        f"we're still in detail phase (asking about texture/naming) or the AI is "
        f"repeating a find-next prompt that was already given\n"
        f'- "wrong_phase": Dialogue asks detail/sensory questions (texture, '
        f"appearance, naming) when in photo phase (no new item has been found yet)\n"
        f'- "repetition": Dialogue is substantially the same as a recent AI turn '
        f"(same meaning, similar phrasing)\n\n"
        f'Output JSON: {{"verdict": "...", "confidence": 0.0-1.0, "explanation": "..."}}'
    )

    try:
        settings = get_settings()
        client = AsyncOpenAI(
            api_key=settings.ali_api_key,
            base_url=settings.ali_base_url,
            max_retries=0,
            timeout=httpx.Timeout(15.0, connect=5.0),
        )
        response = await client.chat.completions.create(
            model=settings.ali_model,
            messages=[
                {"role": "system", "content": "Classify dialogue-state compliance. Output valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=150,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return DialogueCompliance(
            verdict=data.get("verdict", "match"),
            confidence=float(data.get("confidence", 0.5)),
            explanation=data.get("explanation", ""),
        )
    except Exception:
        logger.warning("Dialogue compliance classifier failed, defaulting to match (fail-open)")
        return DialogueCompliance(verdict="match", confidence=0.0, explanation="classifier_error")
```

- [ ] **Step 4: Add import for DialogueCompliance at top of turn_handler.py**

```python
from schemas.dialogue_compliance import DialogueCompliance
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py::test_classify_dialogue_compliance_premature_advance -v`

- [ ] **Step 6: Add test for classifier failure (fail-open)**

```python
@pytest.mark.asyncio
async def test_classify_dialogue_compliance_failure_returns_match() -> None:
    """Classifier failure should return match (fail-open)."""
    state = _make_state(current_step="STEP_3_COLLECT_1", collection_phase="detail", template_type="cat5")
    with patch("turn_handler.AsyncOpenAI", side_effect=RuntimeError("connection failed")):
        result = await _classify_dialogue_compliance(state, "test dialogue", [])
    assert result.verdict == "match"
    assert result.confidence == 0.0
```

- [ ] **Step 7: Lint**

Run: `cd backend && uv run ruff check turn_handler.py && uv run ruff format turn_handler.py`

---

### Task 4: Implement the mismatch handler

**Files:**
- Modify: `backend/turn_handler.py` (add function after the classifier)

- [ ] **Step 1: Write failing test for premature_advance handling**

```python
@pytest.mark.asyncio
async def test_compliance_premature_advance_triggers_state_advancement() -> None:
    """When classifier detects premature_advance, state should advance and dialogue regenerate."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        collection_phase="detail",
        detail_exchange_count=1,
        collected_photos=["photo_1"],
        total_rounds=3,
        template_type="cat5",
    )
    agent = _make_agent_mock()
    # First generation: mismatched "find next" dialogue
    # After advancement: correct Phase A dialogue
    agent.generate_turn = AsyncMock(
        side_effect=[
            _mock_turn(dialogue="Would you like to find another fluffy friend?"),
            _mock_turn(dialogue="Would you like to explore and find the next one?"),
        ]
    )

    compliance = DialogueCompliance(
        verdict="premature_advance", confidence=0.95, explanation="find next during detail"
    )
    with patch("turn_handler._classify_dialogue_compliance", AsyncMock(return_value=compliance)):
        result = await resolve_turn(state, _make_input(text="it feels soft"), agent)

    # State should have advanced: round_advance_pending set, detail cleared
    assert state.round_advance_pending is True or state.current_round == 2
    # The returned dialogue should be the regenerated one, not the mismatched one
```

- [ ] **Step 2: Run test to see it fail**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py::test_compliance_premature_advance_triggers_state_advancement -v`

- [ ] **Step 3: Implement `_handle_compliance_mismatch()`**

Add in `backend/turn_handler.py` after the classifier function:

```python
async def _handle_compliance_mismatch(
    state: SessionStateModel,
    compliance: DialogueCompliance,
    script_agent: ScriptAgent,
) -> TurnResponse:
    """Handle a dialogue-state mismatch by advancing state or regenerating.

    Actions by verdict:
    - premature_advance: Advance state machine, regenerate for new state
    - wrong_phase: Regenerate with corrective hint (cannot advance)
    - repetition: Regenerate with variety hint
    """
    logger.warning(
        "compliance_mismatch: step=%s verdict=%s confidence=%.2f explanation=%s",
        state.current_step, compliance.verdict, compliance.confidence, compliance.explanation,
    )

    if compliance.verdict == "premature_advance":
        # The LLM wants to move to the next round — trust it and advance
        if state.current_step.startswith("STEP_3_COLLECT_") and state.collection_phase == "detail":
            state.round_advance_pending = True
            state.detail_exchange_count = 0
            logger.info("Compliance: advancing from detail to next round (premature_advance)")
        elif state.current_step.startswith("STEP_3_ROUND_"):
            state.round_advance_pending = True
            logger.info("Compliance: advancing Cat1 round (premature_advance)")
        return await _generate_with_retry(script_agent, state)

    if compliance.verdict == "wrong_phase":
        # Cannot advance — no item found. Regenerate with corrective hint.
        hint = (
            f"[system: You are in {state.collection_phase} phase. "
            f"{'The child has NOT found a new item yet — encourage exploration, do NOT ask sensory questions.' if state.collection_phase == 'photo' else 'The child found an item — ask about its texture/appearance, do NOT ask them to find more.'}"
            f"]"
        )
        _append_child_turn(state, hint, include_round_number=False)
        response = await _generate_with_retry(script_agent, state)
        state.conversation_history = [t for t in state.conversation_history if t.text != hint]
        return response

    # repetition — regenerate with variety hint
    hint = "[system: Your last response was too similar to a recent turn. Use different phrasing, a different angle, or a new observation to keep the conversation fresh.]"
    _append_child_turn(state, hint, include_round_number=False)
    response = await _generate_with_retry(script_agent, state)
    state.conversation_history = [t for t in state.conversation_history if t.text != hint]
    return response
```

- [ ] **Step 4: Run test to verify it passes**

- [ ] **Step 5: Add test for wrong_phase (regenerate, no state change)**

```python
@pytest.mark.asyncio
async def test_compliance_wrong_phase_regenerates_without_state_change() -> None:
    """wrong_phase should regenerate but NOT advance state."""
    state = _make_state(
        current_step="STEP_3_COLLECT_2",
        current_round=2,
        collection_phase="photo",
        collected_photos=["photo_1"],
        total_rounds=3,
        template_type="cat5",
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        side_effect=[
            _mock_turn(dialogue="Is it soft like a bunny?"),  # wrong phase
            _mock_turn(dialogue="Would you like to find the next fluffy friend?"),  # corrected
        ]
    )

    compliance_wrong = DialogueCompliance(verdict="wrong_phase", confidence=0.9, explanation="detail in photo")
    compliance_ok = DialogueCompliance(verdict="match", confidence=1.0)
    with patch("turn_handler._classify_dialogue_compliance", AsyncMock(side_effect=[compliance_wrong, compliance_ok])):
        result = await resolve_turn(state, _make_input(text="ooh!"), agent)

    # State should NOT have advanced
    assert state.collection_phase == "photo"
    assert state.current_round == 2
```

- [ ] **Step 6: Add test for repetition**

- [ ] **Step 7: Lint**

Run: `cd backend && uv run ruff check turn_handler.py && uv run ruff format turn_handler.py`

---

### Task 5: Integrate classifier at collection step call sites

**Files:**
- Modify: `backend/turn_handler.py:1145-1268` (section 7c)

The classifier must be called at **two points** in the collection step handling:

1. **After section 7c deferred-advance regeneration** (line 1156): When processing `round_advance_pending` and generating for the new state
2. **After section 7c main generation** (line 1180): The primary collection step generation

- [ ] **Step 1: Write integration test**

```python
@pytest.mark.asyncio
async def test_compliance_classifier_integration_during_collection() -> None:
    """End-to-end: classifier detects mismatch during normal collection turn, triggers advancement."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        collection_phase="detail",
        detail_exchange_count=1,
        collected_photos=["photo_1"],
        total_rounds=3,
        template_type="cat5",
        conversation_history=[
            ConversationTurn(role="ai", text="What does it feel like?", step="STEP_3_COLLECT_1"),
        ],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        side_effect=[
            _mock_turn(dialogue="Find the next fluffy friend!"),
            _mock_turn(dialogue="Would you like to explore and see what's nearby?"),
        ]
    )

    mock_compliance = AsyncMock(side_effect=[
        DialogueCompliance(verdict="premature_advance", confidence=0.95, explanation="find next in detail"),
        DialogueCompliance(verdict="match", confidence=1.0),
    ])
    with patch("turn_handler._classify_dialogue_compliance", mock_compliance):
        result = await resolve_turn(state, _make_input(text="soft like cloud"), agent)

    assert mock_compliance.call_count >= 1
    assert state.round_advance_pending is True
```

- [ ] **Step 2: Run test to see it fail**

- [ ] **Step 3: Add compliance check after main generation (line ~1184)**

In the section 7c block, after `turn_response = await _generate_with_retry(...)` at line 1180-1184, add:

```python
        # Compliance classifier: detect dialogue-state mismatches
        settings = get_settings()
        if (
            settings.compliance_classifier_enabled
            and (state.current_step.startswith("STEP_3_COLLECT_") or state.current_step.startswith("STEP_3_ROUND_"))
        ):
            compliance = await _classify_dialogue_compliance(
                state, turn_response.dialogue, state.conversation_history,
            )
            if compliance.verdict != "match" and compliance.confidence >= settings.compliance_confidence_threshold:
                turn_response = await _handle_compliance_mismatch(state, compliance, script_agent)
```

- [ ] **Step 4: Add compliance check after deferred-advance regeneration (line ~1156)**

Same pattern, after the `_generate_with_retry()` call at line 1156.

- [ ] **Step 5: Run integration test**

- [ ] **Step 6: Add test for classifier disabled via config**

```python
@pytest.mark.asyncio
async def test_compliance_classifier_skipped_when_disabled() -> None:
    """When compliance_classifier_enabled=False, no classifier call is made."""
    # ... setup ...
    with patch("turn_handler.get_settings") as mock_settings:
        mock_settings.return_value.compliance_classifier_enabled = False
        with patch("turn_handler._classify_dialogue_compliance") as mock_classify:
            result = await resolve_turn(state, _make_input(text="soft"), agent)
        mock_classify.assert_not_called()
```

- [ ] **Step 7: Run full test suite**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py -v`

- [ ] **Step 8: Lint**

Run: `cd backend && uv run ruff check turn_handler.py && uv run ruff format turn_handler.py`

---

### Task 6: Full verification

- [ ] **Step 1: Run full test suite**

Run: `cd backend && uv run pytest ../tests/ -v`

- [ ] **Step 2: Type check**

Run: `cd backend && uv run mypy turn_handler.py schemas/dialogue_compliance.py`

- [ ] **Step 3: Lint all changed files**

Run: `cd backend && uv run ruff check turn_handler.py config.py schemas/dialogue_compliance.py && uv run ruff format turn_handler.py config.py schemas/dialogue_compliance.py`

- [ ] **Step 4: Manual smoke test**

Start the server and run a Cat5 session. During collection, observe logs for `compliance_mismatch` entries. Verify the game flows smoothly without getting stuck in repetition loops.

- [ ] **Step 5: Run eval for T0**

Run: `cd backend && uv run python ../scripts/run_eval.py --entity dandelion --tier T0 --sessions 3`

Check the eval results for improvement in collection step quality — fewer repetitive prompts and smoother phase transitions.

## Key Design Decisions

1. **Fail-open default**: Classifier errors return `verdict="match"` — the dialogue passes through unchanged. This ensures the classifier never blocks gameplay.
2. **Confidence threshold (0.8)**: Only act on high-confidence mismatches to prevent false advances. Configurable via `compliance_confidence_threshold`.
3. **State advancement only for `premature_advance`**: `wrong_phase` and `repetition` only regenerate — they cannot safely advance state (no item found, or no clear target state).
4. **Single compliance check per generation**: Runs once after `_generate_with_retry()`, not inside the retry loop, to avoid consuming retry budget.
5. **Same LLM endpoint**: Uses `ali_api_key`/`ali_base_url` (same as story classifier) for consistency.
