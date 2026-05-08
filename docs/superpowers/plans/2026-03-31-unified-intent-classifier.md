# Unified Child Intent Classifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Use code-reviewer and code-simplifier agents after all tasks are complete.

**Goal:** Replace fragmented intent classification (Script Agent `child_intent`, `_classify_story_response`, `_is_affirmative_or_continuation`) with a single LLM pre-classifier that runs before Script Agent on every turn with child input.

**Architecture:** New `_classify_child_intent(state, child_text)` function calls the Ali/Qwen LLM to classify child responses as confirm/decline/substantive/off_topic. Runs once before Script Agent. Result stored on `state.child_intent`. Step handlers route on this instead of Script Agent's `child_intent`. Optional synthesis extension adds `story_quality`/`is_related_to_collection` during STEP_4.

**Tech Stack:** Python 3.12+, Pydantic v2, OpenAI-compatible API (Ali/Qwen), pytest

**Spec:** `docs/superpowers/specs/2026-03-31-unified-intent-classifier-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `backend/schemas/child_intent.py` | Create | `ChildIntentClassification` Pydantic model |
| `backend/schemas/story_classification.py` | Delete | Replaced by `child_intent.py` |
| `backend/schemas/turn_response.py` | Modify | Remove `child_intent` field |
| `backend/schemas/turn_plan.py` | Modify | Remove `child_intent` field |
| `backend/schemas/session_state.py` | Modify | Add `child_intent` field |
| `backend/schemas/__init__.py` | Modify | Update exports |
| `backend/turn_handler.py` | Modify | Add `_classify_child_intent`, remove old classifiers, update step handlers |
| `backend/agents/script_agent.py` | Modify | Remove `child_intent` from output schema, add `{child_intent}` context |
| `backend/skills/script_turn.md` | Modify | Remove `child_intent` output instruction |
| `backend/skills/planner_system.md` | Modify | Remove `child_intent` from planner output |
| `backend/skills/step_instructions/cat5_step2_mission.md` | Modify | Remove classification rules |
| `backend/skills/step_instructions/cat1_step2_rules.md` | Modify | Remove classification rules |
| `tests/test_intent_classifier.py` | Create | Tests for `_classify_child_intent` |
| `tests/test_turn_handler.py` | Modify | Update invitation/synthesis tests |
| `tests/test_turn_plan.py` | Modify | Remove `child_intent` assertions |
| `tests/test_api.py` | Modify | Remove `child_intent` from mock TurnResponse |
| `tests/test_server_visual.py` | Modify | Remove `child_intent` from mock TurnResponse |
| `tests/test_planner.py` | Modify | Remove `child_intent` from assertions |

---

### Task 1: Create ChildIntentClassification Schema

**Files:**
- Create: `backend/schemas/child_intent.py`
- Test: `tests/test_intent_classifier.py`

- [ ] **Step 1: Write the schema test**

Create `tests/test_intent_classifier.py`:

```python
"""Tests for the unified child intent classifier."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from schemas.child_intent import ChildIntentClassification


class TestChildIntentClassification:
    def test_base_intent(self) -> None:
        result = ChildIntentClassification(intent="confirm")
        assert result.intent == "confirm"
        assert result.story_quality is None
        assert result.is_related_to_collection is None

    def test_synthesis_extension(self) -> None:
        result = ChildIntentClassification(
            intent="substantive",
            story_quality="good",
            is_related_to_collection=True,
        )
        assert result.intent == "substantive"
        assert result.story_quality == "good"
        assert result.is_related_to_collection is True

    def test_all_intents_valid(self) -> None:
        for intent in ("confirm", "decline", "substantive", "off_topic"):
            result = ChildIntentClassification(intent=intent)
            assert result.intent == intent
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest ../tests/test_intent_classifier.py::TestChildIntentClassification -v`
Expected: FAIL — `schemas.child_intent` not found

- [ ] **Step 3: Create the schema**

Create `backend/schemas/child_intent.py`:

```python
"""Pydantic schema for unified child intent classification."""

from typing import Literal

from pydantic import BaseModel, Field


class ChildIntentClassification(BaseModel):
    """Result of classifying a child's response before Script Agent generation."""

    intent: Literal["confirm", "decline", "substantive", "off_topic"] = Field(
        description="What the child's response represents"
    )
    # Synthesis extension — only populated during STEP_4_SYNTHESIS
    story_quality: Literal["good", "weak"] | None = Field(
        default=None,
        description="Quality of story attempt — only set when intent is substantive and step is STEP_4_SYNTHESIS",
    )
    is_related_to_collection: bool | None = Field(
        default=None,
        description="Whether the response references collected characters — only set during STEP_4_SYNTHESIS",
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest ../tests/test_intent_classifier.py::TestChildIntentClassification -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Run ruff**

Run: `cd backend && uv run ruff check schemas/child_intent.py ../tests/test_intent_classifier.py && uv run ruff format schemas/child_intent.py ../tests/test_intent_classifier.py`

- [ ] **Step 6: Commit**

```bash
git add backend/schemas/child_intent.py tests/test_intent_classifier.py
git commit -m "$(cat <<'EOF'
feat(schemas): add ChildIntentClassification model
EOF
)"
```

---

### Task 2: Implement `_classify_child_intent` Function

**Files:**
- Modify: `backend/turn_handler.py`
- Test: `tests/test_intent_classifier.py`

- [ ] **Step 1: Write tests for the classifier function**

Add to `tests/test_intent_classifier.py`. These test the prompt construction and LLM response parsing, using mocked LLM calls:

```python
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from schemas.creative_slots import Cat5CreativeSlots
from schemas.session_state import SessionStateModel
from turn_handler import _classify_child_intent


def _make_cat5_state(**overrides: object) -> SessionStateModel:
    defaults: dict = {
        "session_id": "test",
        "tier": "T0",
        "template_type": "cat5",
        "activity_type": "fluffy_expedition_dandelion",
        "current_step": "STEP_3_COLLECT_1",
        "current_round": 1,
        "total_rounds": 3,
        "creative_slots": Cat5CreativeSlots(
            observation_angle="texture",
            collection_criterion="Find soft things",
            collection_count=3,
            mission_metaphor="Fluffy explorer",
            role_title="Fluffy Scout",
            synthesis_type="naming_story",
            stuck_hint="Look nearby",
            naming_prompt="What name?",
            detail_question_template="How does it feel?",
            sorting_criterion="",
        ),
        "entity_name": "dandelion",
        "status": "active",
    }
    defaults.update(overrides)
    return SessionStateModel(**defaults)


def _mock_llm_response(content: str) -> MagicMock:
    """Build a mock OpenAI chat completion response."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    return response


class TestClassifyChildIntent:
    @pytest.mark.asyncio
    async def test_confirm_intent(self) -> None:
        state = _make_cat5_state(current_step="STEP_2_MISSION")
        with patch("turn_handler.AsyncOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                return_value=_mock_llm_response('{"intent": "confirm"}')
            )
            result = await _classify_child_intent(state, "yes!")
        assert result.intent == "confirm"
        assert result.story_quality is None

    @pytest.mark.asyncio
    async def test_decline_intent(self) -> None:
        state = _make_cat5_state(current_step="STEP_2_MISSION")
        with patch("turn_handler.AsyncOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                return_value=_mock_llm_response('{"intent": "decline"}')
            )
            result = await _classify_child_intent(state, "no thanks")
        assert result.intent == "decline"

    @pytest.mark.asyncio
    async def test_substantive_intent(self) -> None:
        state = _make_cat5_state(current_step="STEP_3_COLLECT_1")
        with patch("turn_handler.AsyncOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                return_value=_mock_llm_response('{"intent": "substantive"}')
            )
            result = await _classify_child_intent(state, "it feels really soft and fuzzy")
        assert result.intent == "substantive"

    @pytest.mark.asyncio
    async def test_synthesis_extension(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_4_SYNTHESIS",
            collected_names=["Mr. Fluff", "Petal"],
        )
        with patch("turn_handler.AsyncOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                return_value=_mock_llm_response(
                    '{"intent": "substantive", "story_quality": "good", "is_related_to_collection": true}'
                )
            )
            result = await _classify_child_intent(state, "Mr. Fluff went to sleep and Petal sang a song")
        assert result.intent == "substantive"
        assert result.story_quality == "good"
        assert result.is_related_to_collection is True

    @pytest.mark.asyncio
    async def test_synthesis_confirm(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_4_SYNTHESIS",
            collected_names=["Mr. Fluff"],
        )
        with patch("turn_handler.AsyncOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                return_value=_mock_llm_response('{"intent": "confirm"}')
            )
            result = await _classify_child_intent(state, "yes tell me a story")
        assert result.intent == "confirm"
        assert result.story_quality is None

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self) -> None:
        state = _make_cat5_state(current_step="STEP_3_COLLECT_1")
        with patch("turn_handler.AsyncOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("LLM down"))
            result = await _classify_child_intent(state, "something")
        assert result.intent == "substantive"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest ../tests/test_intent_classifier.py::TestClassifyChildIntent -v`
Expected: FAIL — `_classify_child_intent` not found

- [ ] **Step 3: Implement `_classify_child_intent`**

In `backend/turn_handler.py`, replace the section from `_AFFIRMATIVE_PATTERNS` through the end of `_classify_story_response` (lines 562-660) with:

```python
# ---------------------------------------------------------------------------
# Unified child intent classifier
# ---------------------------------------------------------------------------


async def _classify_child_intent(
    state: SessionStateModel, child_text: str
) -> ChildIntentClassification:
    """Classify a child's response before Script Agent generation.

    Runs once per turn on any turn with non-empty child text. Returns intent
    (confirm/decline/substantive/off_topic) plus optional synthesis extension
    (story_quality, is_related_to_collection) when in STEP_4_SYNTHESIS.
    """
    is_synthesis = state.current_step == "STEP_4_SYNTHESIS"
    collected = ", ".join(state.collected_names) if state.collected_names else "the collected items"

    step_context = state.current_step.replace("_", " ").lower()

    prompt = (
        f'The child is playing a "{state.activity_type.replace("_", " ")}" game. '
        f"Current step: {step_context}.\n"
        f'The child said: "{child_text}"\n\n'
        f"Classify the child's intent:\n"
        f'- "confirm": agreeing, affirming, wanting to continue, asking the AI to proceed '
        f"(\"yes\", \"sure\", \"ok\", \"what's next\", \"go ahead\", \"tell me\", \"sounds fun\", "
        f"\"yay!\", \"let's do it\", \"I'm ready\")\n"
        f'- "decline": refusing or saying no ("no", "I don\'t want to", "nah", "stop")\n'
        f'- "substantive": providing real content — an answer, description, detail, or story\n'
        f'- "off_topic": unrelated to the current activity\n'
    )

    if is_synthesis:
        prompt += (
            f"\nIf intent is \"substantive\", also evaluate the story:\n"
            f"- story_quality: \"good\" if it has 2+ story elements (character + action, or "
            f"action + outcome) relating to these characters: {collected}. "
            f"\"weak\" if it's a single sentence with no progression.\n"
            f"- is_related_to_collection: true if the response mentions or relates to: {collected}\n\n"
            f'Output JSON: {{"intent": "...", "story_quality": "good|weak|null", '
            f'"is_related_to_collection": true/false}}'
        )
    else:
        prompt += f'\nOutput JSON: {{"intent": "..."}}'

    try:
        settings = get_settings()
        client = AsyncOpenAI(
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
            max_retries=0,
            timeout=httpx.Timeout(15.0, connect=5.0),
        )
        response = await client.chat.completions.create(
            model=settings.dashscope_model,
            messages=[
                {"role": "system", "content": "Classify a child's response. Output valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=100,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)

        intent = data.get("intent", "substantive")
        if intent not in ("confirm", "decline", "substantive", "off_topic"):
            intent = "substantive"

        story_quality = None
        is_related = None
        if is_synthesis and intent == "substantive":
            sq = data.get("story_quality")
            story_quality = sq if sq in ("good", "weak") else None
            is_related = bool(data.get("is_related_to_collection", False))

        return ChildIntentClassification(
            intent=intent,
            story_quality=story_quality,
            is_related_to_collection=is_related,
        )
    except Exception:
        logger.warning("Child intent classification failed, defaulting to substantive")
        return ChildIntentClassification(intent="substantive")
```

Also add the import at the top of `turn_handler.py`:

```python
from schemas.child_intent import ChildIntentClassification
```

And remove the old import:

```python
from schemas.story_classification import StoryClassification  # DELETE THIS LINE
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest ../tests/test_intent_classifier.py -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Run ruff**

Run: `cd backend && uv run ruff check turn_handler.py ../tests/test_intent_classifier.py && uv run ruff format turn_handler.py ../tests/test_intent_classifier.py`

- [ ] **Step 6: Commit**

```bash
git add backend/turn_handler.py tests/test_intent_classifier.py
git commit -m "$(cat <<'EOF'
feat(turn): add unified _classify_child_intent function
EOF
)"
```

---

### Task 3: Add `child_intent` to SessionStateModel

**Files:**
- Modify: `backend/schemas/session_state.py`

- [ ] **Step 1: Add the field**

In `backend/schemas/session_state.py`, add after the `synthesis_story_quality` field:

```python
    child_intent: str = Field(default="", description="Pre-classified intent for the current turn: confirm, decline, substantive, off_topic")
```

- [ ] **Step 2: Run existing tests**

Run: `cd backend && uv run pytest ../tests/test_debug_payload.py -v`
Expected: All tests PASS (new field has a default, so existing tests are unaffected)

- [ ] **Step 3: Run ruff**

Run: `cd backend && uv run ruff check schemas/session_state.py && uv run ruff format schemas/session_state.py`

- [ ] **Step 4: Commit**

```bash
git add backend/schemas/session_state.py
git commit -m "$(cat <<'EOF'
feat(schemas): add child_intent field to SessionStateModel
EOF
)"
```

---

### Task 4: Wire Classifier into `resolve_turn`

**Files:**
- Modify: `backend/turn_handler.py`
- Test: `tests/test_turn_handler.py`

This is the core integration. The classifier must run near the top of `resolve_turn`, before any step-specific logic. Read `resolve_turn` to find the insertion point — it should be after child input is extracted but before step-specific handling.

- [ ] **Step 1: Find the insertion point**

Read `backend/turn_handler.py` to find where `resolve_turn` processes child input. Look for where `child_text` or `turn_input.text` is first available. The classifier call goes right after, setting `state.child_intent`.

- [ ] **Step 2: Add classifier call**

In `resolve_turn`, after the child input is extracted and appended to conversation history, add:

```python
    # --- Classify child intent (runs before any step-specific logic) ---
    child_text = turn_input.text or ""
    if child_text and not turn_input.is_silent:
        intent_result = await _classify_child_intent(state, child_text)
        state.child_intent = intent_result.intent
        logger.info(
            "child_intent_classification: step=%s intent=%s text=%s",
            state.current_step,
            intent_result.intent,
            child_text[:80],
        )
    else:
        state.child_intent = ""
        intent_result = None
```

Store `intent_result` in a local variable so step handlers can access the full classification (including synthesis extension fields) without another attribute on state.

- [ ] **Step 3: Run existing tests**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py -v`

Some tests may fail because the classifier LLM call isn't mocked. If tests fail, add a fixture or patch to mock `_classify_child_intent` in the test file. The mock should return `ChildIntentClassification(intent="substantive")` by default, or the appropriate intent for specific test cases (e.g., `intent="confirm"` for acceptance tests, `intent="decline"` for decline tests).

- [ ] **Step 4: Update test mocks**

In `tests/test_turn_handler.py`, add a module-level `autouse` fixture or patch `_classify_child_intent`:

```python
from schemas.child_intent import ChildIntentClassification

@pytest.fixture(autouse=True)
def _mock_intent_classifier(monkeypatch):
    """Default mock: classify all child input as substantive."""
    async def _mock_classify(state, text):
        return ChildIntentClassification(intent="substantive")
    monkeypatch.setattr("turn_handler._classify_child_intent", _mock_classify)
```

Then for tests that need specific intents, override the mock locally:

```python
async def test_invitation_acceptance_advances_immediately() -> None:
    # ... existing setup ...
    # Override classifier to return "confirm"
    with patch("turn_handler._classify_child_intent", new_callable=AsyncMock) as mock_cls:
        mock_cls.return_value = ChildIntentClassification(intent="confirm")
        result = await resolve_turn(state, _make_input(text="yes!"), agent)
    assert state.child_intent == "confirm"
    # ... rest of assertions ...
```

- [ ] **Step 5: Run tests**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py -v`
Expected: All tests PASS

- [ ] **Step 6: Run ruff**

Run: `cd backend && uv run ruff check turn_handler.py ../tests/test_turn_handler.py && uv run ruff format turn_handler.py ../tests/test_turn_handler.py`

- [ ] **Step 7: Commit**

```bash
git add backend/turn_handler.py tests/test_turn_handler.py
git commit -m "$(cat <<'EOF'
feat(turn): wire _classify_child_intent into resolve_turn
EOF
)"
```

---

### Task 5: Update Invitation Step Handlers

**Files:**
- Modify: `backend/turn_handler.py`
- Test: `tests/test_turn_handler.py`

Change invitation step handlers (STEP_2_RULES / STEP_2_MISSION) to route on `state.child_intent` instead of `turn_response.child_intent`.

- [ ] **Step 1: Read the current invitation handler**

Read `backend/turn_handler.py` around the `_is_invitation_step` block (currently ~line 1395). The current flow is:

```python
if _is_invitation_step(state.current_step):
    is_first = not _already_prompted_on_step(state)
    turn_response, gen_debug = await _generate_with_retry(script_agent, state, is_first_on_step=is_first)

    if turn_response.child_intent == "declined":
        # ... decline handling ...

    if turn_response.child_intent == "accepted":
        # ... acceptance handling ...

    # Null / off-topic
    # ... stay on step ...
```

- [ ] **Step 2: Rewrite to use pre-classified intent**

Replace the invitation handler with:

```python
if _is_invitation_step(state.current_step):
    is_first = not _already_prompted_on_step(state)

    if state.child_intent == "decline":
        state.invitation_decline_count += 1
        if state.invitation_decline_count >= 2:
            state.current_step = EARLY_EXIT
            state.status = "exited"
            turn_response, gen_debug = await _generate_with_retry(script_agent, state)
            _append_ai_turn(state, turn_response.dialogue)
            state.turn_count += 1
            return TurnResult(
                turn_response=turn_response,
                screen_frame=_get_screen_frame(state),
                auto_advance=False,
                response_type="graceful_exit",
                error_exit=state.status == "error",
                debug=_debug(gen_debug, turn_response),
            )
        # First decline: stay on STEP_2, re-invite
        turn_response, gen_debug = await _generate_with_retry(script_agent, state, is_first_on_step=is_first)
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type=_get_response_type(state.current_step),
            error_exit=state.status == "error",
            debug=_debug(gen_debug, turn_response),
        )

    if state.child_intent == "confirm":
        state.invitation_decline_count = 0
        state.invitation_accepted = True
        turn_response, gen_debug = await _generate_with_retry(script_agent, state, is_first_on_step=is_first)
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        _advance_state(state)
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=True,
            response_type=_get_response_type(state.current_step),
            error_exit=state.status == "error",
            debug=_debug(gen_debug, turn_response),
        )

    # substantive / off_topic: stay on STEP_2, re-invite
    turn_response, gen_debug = await _generate_with_retry(script_agent, state, is_first_on_step=is_first)
    _append_ai_turn(state, turn_response.dialogue)
    state.turn_count += 1
    return TurnResult(
        turn_response=turn_response,
        screen_frame=_get_screen_frame(state),
        auto_advance=False,
        response_type=_get_response_type(state.current_step),
        error_exit=state.status == "error",
        debug=_debug(gen_debug, turn_response),
    )
```

Key changes:
- Routes on `state.child_intent` (pre-classified) instead of `turn_response.child_intent` (Script Agent output)
- Script Agent only generates dialogue AFTER intent is known
- Acceptance: generates celebration, appends, advances, returns with auto_advance=True (one LLM call, not two)

- [ ] **Step 3: Update tests**

In `tests/test_turn_handler.py`, update the invitation tests to mock the classifier intent instead of the Script Agent's `child_intent`:

- `test_invitation_acceptance_advances_immediately`: mock classifier returns `confirm`
- `test_invitation_decline_increments_count`: mock classifier returns `decline`
- `test_second_decline_exits_gracefully`: mock classifier returns `decline`
- `test_invitation_first_delivery_stays_on_step2`: mock classifier returns `off_topic` or `substantive`

The `_mock_turn` helper should no longer need `child_intent` parameter.

- [ ] **Step 4: Run tests**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run ruff**

Run: `cd backend && uv run ruff check turn_handler.py ../tests/test_turn_handler.py && uv run ruff format turn_handler.py ../tests/test_turn_handler.py`

- [ ] **Step 6: Commit**

```bash
git add backend/turn_handler.py tests/test_turn_handler.py
git commit -m "$(cat <<'EOF'
refactor(turn): use pre-classified intent for invitation steps
EOF
)"
```

---

### Task 6: Update Synthesis Step Handler

**Files:**
- Modify: `backend/turn_handler.py`
- Test: `tests/test_turn_handler.py`

Replace the T0 `_is_affirmative_or_continuation` check and the T1/T2 `_classify_story_response` call with the unified classifier result.

- [ ] **Step 1: Read the current synthesis evaluate phase**

Read the EVALUATE phase in `_handle_synthesis` (or the inline synthesis handler in `resolve_turn`). The current flow has three paths: silence, T0 shortcut, T1/T2 classification.

- [ ] **Step 2: Rewrite to use pre-classified intent**

Replace the entire EVALUATE phase with:

```python
    # --- EVALUATE phase: use pre-classified intent ---
    if phase == "evaluate":
        if turn_input.is_silent:
            logger.info("synthesis_classification: silence detected — skipping to AI story generation")
            state.synthesis_silences += 1
            state.synthesis_phase = "generate"
            turn_response, gen_debug = await _generate_with_retry(script_agent, state)
            return _synthesis_result(state, turn_response, advance=True, debug=_debug(gen_debug, turn_response))

        if state.child_intent == "confirm":
            # Child wants AI to tell the story (all tiers)
            logger.info("synthesis_classification: confirm — AI generates full story")
            state.synthesis_declines += 1
            state.synthesis_phase = "generate"
            turn_response, gen_debug = await _generate_with_retry(script_agent, state)
            return _synthesis_result(state, turn_response, advance=True, debug=_debug(gen_debug, turn_response))

        if state.child_intent == "decline":
            # Child declined — AI generates anyway
            logger.info("synthesis_classification: decline — AI generates full story")
            state.synthesis_declines += 1
            state.synthesis_phase = "generate"
            turn_response, gen_debug = await _generate_with_retry(script_agent, state)
            return _synthesis_result(state, turn_response, advance=True, debug=_debug(gen_debug, turn_response))

        if state.child_intent == "off_topic":
            state.synthesis_unrelated += 1
            if state.synthesis_prompt_count < 2:
                state.synthesis_prompt_count += 1
                turn_response, gen_debug = await _generate_with_retry(script_agent, state, is_first_on_step=True)
                return _synthesis_result(state, turn_response, advance=False, debug=_debug(gen_debug, turn_response))
            state.synthesis_phase = "generate"
            turn_response, gen_debug = await _generate_with_retry(script_agent, state)
            return _synthesis_result(state, turn_response, advance=True, debug=_debug(gen_debug, turn_response))

        # substantive — child provided story content
        child_text = turn_input.text or ""
        state.synthesis_child_story = child_text
        state.synthesis_story_attempts += 1
        state.synthesis_story_quality = intent_result.story_quality or "" if intent_result else ""

        if intent_result and intent_result.story_quality == "good":
            turn_response, gen_debug = await _generate_with_retry(script_agent, state)
            return _synthesis_result(state, turn_response, advance=True, debug=_debug(gen_debug, turn_response))

        if state.tier == "T0":
            # T0: no improve phase — generate from seed
            state.synthesis_phase = "generate"
            turn_response, gen_debug = await _generate_with_retry(script_agent, state)
            return _synthesis_result(state, turn_response, advance=True, debug=_debug(gen_debug, turn_response))

        # T1/T2: weak story → improve phase
        state.synthesis_phase = "improve"
        turn_response, gen_debug = await _generate_with_retry(script_agent, state)
        return _synthesis_result(state, turn_response, advance=False, debug=_debug(gen_debug, turn_response))
```

Note: `intent_result` is the local variable from the `resolve_turn` scope (set in Task 4).

- [ ] **Step 3: Update synthesis tests**

Update synthesis tests in `tests/test_turn_handler.py` to mock the classifier instead of `_classify_story_response`:

- `test_synthesis_t0_skips_classification_and_expands_seed`: mock classifier returns `substantive` with `story_quality="weak"` — should go to generate for T0
- `test_synthesis_can_finish_after_first_child_reply`: mock classifier returns `substantive` with `story_quality="good"` — should advance
- Add new test: `test_synthesis_confirm_generates_full_story`: mock classifier returns `confirm` for "yes" — should go straight to generate with no child_story seed

- [ ] **Step 4: Run tests**

Run: `cd backend && uv run pytest ../tests/test_turn_handler.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run ruff**

Run: `cd backend && uv run ruff check turn_handler.py ../tests/test_turn_handler.py && uv run ruff format turn_handler.py ../tests/test_turn_handler.py`

- [ ] **Step 6: Commit**

```bash
git add backend/turn_handler.py tests/test_turn_handler.py
git commit -m "$(cat <<'EOF'
refactor(turn): use pre-classified intent for synthesis steps
EOF
)"
```

---

### Task 7: Remove Old Classifiers and Update Script Agent

**Files:**
- Modify: `backend/turn_handler.py` — remove `_classify_story_response`, `_is_affirmative_or_continuation`, `_AFFIRMATIVE_PATTERNS`
- Modify: `backend/schemas/turn_response.py` — remove `child_intent` field
- Modify: `backend/schemas/turn_plan.py` — remove `child_intent` field
- Delete: `backend/schemas/story_classification.py`
- Modify: `backend/agents/script_agent.py` — remove `child_intent` from output schema, add `{child_intent}` context
- Modify: `backend/skills/script_turn.md` — remove `child_intent` output instruction
- Modify: `backend/skills/planner_system.md` — remove `child_intent` from planner output
- Modify: `backend/skills/step_instructions/cat5_step2_mission.md` — remove classification rules
- Modify: `backend/skills/step_instructions/cat1_step2_rules.md` — remove classification rules

- [ ] **Step 1: Remove old classifiers from turn_handler.py**

Delete the entire block from `_AFFIRMATIVE_PATTERNS` through the end of `_classify_story_response` (the section between the `# Unified child intent classifier` section and the `# LLM generation with retry + validation` section).

Also remove the import: `from schemas.story_classification import StoryClassification`

- [ ] **Step 2: Remove `child_intent` from TurnResponse**

In `backend/schemas/turn_response.py`, delete:

```python
    child_intent: str | None = Field(
        default=None, description="STEP_2 only: 'accepted', 'declined', 'off_topic', or null"
    )
```

- [ ] **Step 3: Remove `child_intent` from TurnPlan**

In `backend/schemas/turn_plan.py`, delete:

```python
    child_intent: str | None = Field(default=None)
```

- [ ] **Step 4: Delete StoryClassification schema**

Delete the file `backend/schemas/story_classification.py`.

- [ ] **Step 5: Update Script Agent**

In `backend/agents/script_agent.py`:

a) Remove the `child_intent_field` construction and injection (lines ~1338-1341, ~1389).

b) Remove `turn.child_intent = plan.child_intent` at lines ~815 and ~1125.

c) Add a `{child_intent}` context line in the user prompt where `child_input` is constructed (around line 1336). After the child input line, add:

```python
        intent_context = ""
        if state.child_intent:
            intent_context = f"\nChild's intent has been classified as: {state.child_intent}."
```

And include `{intent_context}` in the prompt string.

- [ ] **Step 6: Update prompt files**

In `backend/skills/script_turn.md`, remove the `child_intent` bullet from the output format section (line ~97).

In `backend/skills/planner_system.md`, remove `"child_intent"` from the planner JSON output (line ~49).

In `backend/skills/step_instructions/cat5_step2_mission.md`, remove rule 3 about setting `child_intent` and update rule 4 about acceptance behavior (remove the `child_intent = "accepted"` reference — just say "On acceptance").

In `backend/skills/step_instructions/cat1_step2_rules.md`, remove the `child_intent` instructions from the Invitation section and update the acceptance behavior note.

- [ ] **Step 7: Update all test files**

In `tests/test_turn_handler.py`: Remove `child_intent` from `_mock_turn` helper and all `_mock_turn(child_intent=...)` calls. The tests now mock the classifier (from Task 5).

In `tests/test_api.py`: Remove `child_intent` from all `TurnResponse(...)` constructions (lines ~386, ~427, ~457, ~771).

In `tests/test_server_visual.py`: Remove `child_intent` from all `TurnResponse(...)` constructions (lines ~106, ~145, ~180, ~229).

In `tests/test_turn_plan.py`: Remove `child_intent` assertions (line ~50, ~80, ~95, ~191, ~223).

In `tests/test_planner.py`: Remove `child_intent` from assertions (line ~275).

- [ ] **Step 8: Run full test suite**

Run: `cd backend && uv run pytest ../tests/ -v --timeout=30`
Expected: All tests PASS

- [ ] **Step 9: Run ruff on all changed files**

Run: `cd backend && uv run ruff check . && uv run ruff format .`

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "$(cat <<'EOF'
refactor(turn): remove old classifiers, update script agent
EOF
)"
```

---

### Task 8: Update Debug Panel for Intent Display

**Files:**
- Modify: `frontend/src/components/DebugPanel.jsx`

- [ ] **Step 1: Update LLM Output section**

In the `GenerationTab`, the `llm_output.child_intent` display should now read from `session_state.child_intent` instead. Find the `child_intent` rendering in the LLM Output column and update it:

```jsx
{sessionState?.child_intent && (
    <KV label="intent"><Badge color={C.peach}>{sessionState.child_intent}</Badge></KV>
)}
```

This should be in the `StateMachineTab` Session State section rather than the Generation tab's LLM Output section, since intent is now a state-level property.

- [ ] **Step 2: Remove from LLM Output section**

Remove the `child_intent` line from the LLM Output section in `GenerationTab` (if it exists there).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/DebugPanel.jsx
git commit -m "$(cat <<'EOF'
feat(debug): show child_intent from session state
EOF
)"
```

---

### Task 9: Final Verification

**Files:** None (verification only)

- [ ] **Step 1: Run full backend test suite**

Run: `cd backend && uv run pytest ../tests/ -v --timeout=30`
Expected: All tests PASS

- [ ] **Step 2: Run ruff check and format**

Run: `cd backend && uv run ruff check . && uv run ruff format .`

- [ ] **Step 3: Verify StoryClassification is fully removed**

Run: `cd backend && grep -r "StoryClassification" . --include="*.py"` — should return no results (except possibly in test files that import the old schema, which should have been updated).

Run: `cd backend && grep -r "_classify_story_response" . --include="*.py"` — should return no results.

Run: `cd backend && grep -r "_is_affirmative_or_continuation" . --include="*.py"` — should return no results.

Run: `cd backend && grep -r "_AFFIRMATIVE_PATTERNS" . --include="*.py"` — should return no results.

- [ ] **Step 4: Launch code-reviewer and code-simplifier agents**

Run code-reviewer and code-simplifier sub-agents in parallel on all changed files.
