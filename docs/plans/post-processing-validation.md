# Post-Processing Response Validation

## Context

Prompt-level instructions for the Script Agent have diminishing returns — the AI skips rules (no question in hook, must include demo, scaffold for T0) when the prompt is long. We need programmatic checks after generation that reject non-compliant responses and regenerate with a corrective hint.

## Approach

Add a validation layer between AI response generation and response delivery in `backend/turn_handler.py`. When a validator fails, append a corrective hint to the conversation context and regenerate (using the existing retry budget). If all retries fail validation, accept the last response anyway (don't block the game).

## Validators

### 1. Hook: No questions
- **When:** `current_step == STEP_1_HOOK`
- **Check:** `"?" not in turn_response.dialogue`
- **Hint:** "CORRECTION: Your hook response contained a question mark. The hook MUST be a pure emotional reaction with NO questions. Remove all questions and rewrite as exclamations only."

### 2. Mission/Rules: Demo must exist
- **When:** `current_step in (STEP_2_MISSION, STEP_2_RULES)` AND this is the first AI turn on this step (not a re-invitation after decline)
- **Check:** The dialogue must reference `{entity_name}` in a demo context. Heuristic: dialogue contains the entity name AND contains a model phrase pattern (e.g., "I'd call it", "I think it would say", "it looks like", "it sounds like").
- **Hint:** "CORRECTION: You must include a demo example using {entity_name}. Show one quick example of how the game works before the invitation."

### 3. T0 Detail question: Must scaffold
- **When:** `current_step.startswith(STEP_3_COLLECT_)` AND `tier == T0` AND child just selected correct photo (entering detail phase)
- **Check:** The dialogue should NOT end with an open wh-question ("what does", "what do you", "how does", "how do you") without also containing a model phrase ("I think", "maybe it's", "it looks like", "should we call").
- **Hint:** "CORRECTION: For T0 children, you must model your own idea first before asking. Say what YOU think it looks like, then ask 'What do you think?' or offer a choice."

### 4. T0 Synthesis question: Must scaffold
- **When:** `current_step == STEP_4_SYNTHESIS` AND `tier == T0` AND first synthesis turn
- **Check:** If dialogue ends with a question, it must contain "or" (binary choice) OR a model phrase.
- **Hint:** "CORRECTION: For T0 children, do not ask open questions. Offer a binary choice like 'Did X tickle them or give a hug?'"

## Implementation

### File: `backend/turn_handler.py`

Add a `_validate_response()` function that takes `(state, turn_response, is_first_on_step)` and returns `(is_valid, hint_message)`.

Modify `_generate_with_retry()` to accept an optional validator. After each generation attempt, run the validator. If it fails, append the hint to conversation history as a system message and retry. Strip the hint from history after the retry (same pattern as the existing corrective hints for wrong photos).

```python
def _validate_response(
    state: SessionStateModel,
    turn_response: TurnResponse,
    is_first_on_step: bool,
) -> tuple[bool, str]:
    """Validate AI response against step-specific rules.

    Returns (True, "") if valid, or (False, corrective_hint) if invalid.
    """
    step = state.current_step
    dialogue = turn_response.dialogue
    tier = state.tier

    # 1. Hook: no questions
    if step == "STEP_1_HOOK" and "?" in dialogue:
        return False, "CORRECTION: ..."

    # 2. Mission/Rules: demo must exist
    if step in ("STEP_2_MISSION", "STEP_2_RULES") and is_first_on_step:
        has_entity_ref = state.entity_name.lower() in dialogue.lower()
        has_model_phrase = any(p in dialogue.lower() for p in [
            "i'd call", "i think it would", "it looks like", "i think it looks",
            "see this", "see the", "look at this", "let me show",
        ])
        if not (has_entity_ref and has_model_phrase):
            return False, "CORRECTION: ..."

    # 3. T0 collect detail: must scaffold
    if (step.startswith("STEP_3_COLLECT_")
        and tier == "T0"
        and state.collection_phase == "detail"
        and is_first_on_step):
        if _ends_with_open_question(dialogue) and not _has_model_phrase(dialogue):
            return False, "CORRECTION: ..."

    # 4. T0 synthesis: must scaffold
    if step == "STEP_4_SYNTHESIS" and tier == "T0" and is_first_on_step:
        if _ends_with_open_question(dialogue) and " or " not in dialogue.lower():
            return False, "CORRECTION: ..."

    return True, ""
```

### Helper functions:
```python
def _ends_with_open_question(dialogue: str) -> bool:
    """Check if dialogue ends with an open wh-question."""
    # Extract last sentence, check for wh-word + question mark
    ...

def _has_model_phrase(dialogue: str) -> bool:
    """Check if dialogue contains a model/scaffold phrase."""
    return any(p in dialogue.lower() for p in [
        "i think", "maybe it's", "it looks like", "should we call",
        "i'd call", "it reminds me of",
    ])
```

### Integration into `_generate_with_retry()`:

The existing function signature:
```python
async def _generate_with_retry(script_agent, state, ...) -> TurnResponse
```

Add a `validator` parameter. After each generation, run the validator. If it fails and retries remain, append the hint and regenerate.

## Files Modified

| File | Change |
|------|--------|
| `backend/turn_handler.py` | Add `_validate_response()`, `_ends_with_open_question()`, `_has_model_phrase()`; integrate validator into retry loop |

## Verification

- Start T0 fluffy_expedition_dandelion session
- Check hook response has no question marks
- Check mission response references the dandelion in a demo
- Check detail question (correct photo) models first for T0
- Check synthesis question offers a binary choice for T0
- Monitor server logs for "CORRECTION:" hints indicating validation fired
- `uv run ruff check backend/turn_handler.py`
- `uv run pytest tests/`
