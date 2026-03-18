# Step Transition Refactor Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract step transition logic from duplicated `/api/turn` and `/api/turn-speak` handlers into a single `resolve_turn()` helper with clear, testable rules per step type.

**Architecture:** The core problem is that step advancement, child input recording, auto-advance signaling, and LLM generation are interleaved differently in `/api/turn` vs `/api/turn-speak`, creating 6+ bugs. The fix is a single `resolve_turn()` function that takes session state + request, and returns `(turn_response, screen_frame, auto_advance, response_type)`. Both endpoints call this function; `/api/turn` wraps the result in JSON, `/api/turn-speak` adds TTS streaming.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic v2

---

## Root Causes

All bugs stem from three design issues:

1. **Duplicated logic** — `/api/turn` and `/api/turn-speak` each implement their own step transition logic with subtle differences (auto-advance flags, early returns, invitation handling)
2. **Interleaved concerns** — child input recording, state advancement, LLM generation, and auto-advance calculation are mixed together with ordering dependencies that are easy to get wrong
3. **Deferred invitation acceptance** — `invitation_accepted` flag creates a one-turn delay that cascades into wrong step attribution, premature gallery display, and hallucinated collections

## Bugs Fixed By This Refactor

| Bug | Description |
|-----|-------------|
| Double responses | Two AI messages generated in one request on acceptance |
| Gallery before prompt | PhotoGallery appears with acceptance message, before collect prompt |
| Synthesis skipped | STEP_4_SYNTHESIS jumped over on silence turn |
| Wrong collection context | LLM says child found dandelion when no photo was picked |
| Consecutive AI messages | Celebrate + closing fire without user interaction between them |
| Inconsistent auto-advance | `/api/turn` and `/api/turn-speak` compute auto-advance differently |

## Design: `resolve_turn()`

The function processes one turn with this clear sequence:

```
1. Handle silence exit (consecutive_silence >= 2)
2. Handle wrong photo exit (consecutive_wrong >= 2)
3. Handle wrong photo retry (stay on step)
4. Record child input in conversation history
5. Determine action based on step type:
   a. INVITATION (not yet accepted): generate invitation turn via LLM
   b. INVITATION (accepted on THIS turn): return acceptance dialogue, set auto_advance
   c. INVITATION (accepted on PREV turn, auto-advance): advance + generate round prompt
   d. ROUND STEP: generate for current step, advance if stay_on_step=false
   e. INTERACTIVE STEP (first visit): generate prompt for this step
   f. INTERACTIVE STEP (already prompted): advance + generate for next step
   g. AUTO-ADVANCE STEP: advance + generate for next step
6. Append AI response to conversation history
7. Calculate auto_advance flag
8. Return (turn_response, screen_frame, auto_advance, response_type)
```

Key rules:
- **Invitation acceptance**: On the turn where `child_intent == "accepted"`, return the acceptance dialogue with `auto_advance=True` but do NOT advance state yet. State stays on STEP_2 so the frontend doesn't show the gallery. On the NEXT turn (auto-advance), advance to STEP_3 and generate the collect prompt.
- **Round acknowledgment**: After a round with child input and `stay_on_step=false`, auto-advance ONLY if the next step is another round OR an auto-advance step. Do NOT auto-advance into interactive steps like STEP_4_SYNTHESIS.
- **Interactive steps** (STEP_4_SYNTHESIS): Generate prompt on first visit. On second visit (AI already spoke on this step), advance past it.
- **Auto-advance steps** (STEP_4_CELEBRATE, STEP_5_CELEBRATE, STEP_5_CLOSING, STEP_6_CLOSING): Advance first, then generate.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/turn_handler.py` | **Create** | `resolve_turn()` — all step transition logic |
| `backend/server.py` | **Modify** | `/api/turn` and `/api/turn-speak` call `resolve_turn()` |
| `backend/schemas/session_state.py` | **Keep** | `invitation_accepted` field stays |
| `backend/state_machine.py` | **Keep** | No changes needed |
| `tests/test_turn_handler.py` | **Create** | Unit tests for `resolve_turn()` |

---

## Task 1: Create `resolve_turn()` with invitation handling tests

**Files:**
- Create: `backend/turn_handler.py`
- Create: `tests/test_turn_handler.py`

### Subtask 1a: Write failing tests for invitation flow

- [ ] **Step 1: Write tests for invitation acceptance flow**

```python
# tests/test_turn_handler.py
import pytest
from unittest.mock import AsyncMock, patch
from schemas.session_state import SessionStateModel, ConversationTurn
from schemas.turn_response import TurnResponse
from schemas.creative_slots import Cat5CreativeSlots
from turn_handler import resolve_turn, TurnInput, TurnResult


def _mock_turn(
    dialogue: str = "",
    child_intent: str | None = None,
    stay_on_step: bool = False,
    tone_marker: str = "gentle",
) -> TurnResponse:
    """Build a mock TurnResponse for testing."""
    return TurnResponse(
        dialogue=dialogue,
        tone_marker=tone_marker,
        child_intent=child_intent,
        stay_on_step=stay_on_step,
    )


def _make_state(step: str, template: str = "cat5", **kwargs) -> SessionStateModel:
    """Helper to build minimal session state for testing."""
    defaults = {
        "session_id": "test-session",
        "activity_type": "fluffy_expedition_dandelion",
        "creative_slots": Cat5CreativeSlots(
            observation_angle="fluffy or soft texture",
            collection_criterion="fluffy, fuzzy, or soft",
            collection_count=3,
            mission_metaphor="Fluffy Expedition",
            role_title="Fluffy Expedition Explorer",
            synthesis_type="naming_story",
        ),
        "current_step": step,
        "template_type": template,
        "total_rounds": 3,
        "entity_name": "dandelion",
        "tier": "T0",
    }
    defaults.update(kwargs)
    return SessionStateModel(**defaults)


def _make_input(**kwargs) -> TurnInput:
    """Helper to build turn input."""
    return TurnInput(
        text=kwargs.get("text", ""),
        is_silent=kwargs.get("is_silent", False),
        photo_id=kwargs.get("photo_id", None),
    )


@pytest.fixture
def mock_script_agent():
    """Mock ScriptAgent that returns configurable TurnResponses."""
    agent = AsyncMock()
    agent.generate_turn = AsyncMock()
    return agent


# --- Invitation flow ---

@pytest.mark.asyncio
async def test_invitation_first_delivery_stays_on_step(mock_script_agent):
    """First STEP_2 delivery: LLM presents invitation, state stays on STEP_2."""
    mock_script_agent.generate_turn.return_value = _mock_turn(
        dialogue="Would you like to explore?",
        child_intent=None,
    )
    state = _make_state("STEP_2_MISSION")
    result = await resolve_turn(state, _make_input(text="heaven"), mock_script_agent)

    assert state.current_step == "STEP_2_MISSION"
    assert result.auto_advance is False
    assert state.invitation_accepted is False


@pytest.mark.asyncio
async def test_invitation_acceptance_stays_on_step_with_auto_advance(mock_script_agent):
    """On acceptance: state stays on STEP_2, auto_advance=True, invitation_accepted=True."""
    mock_script_agent.generate_turn.return_value = _mock_turn(
        dialogue="Yay! Let's go!",
        child_intent="accepted",
    )
    state = _make_state("STEP_2_MISSION")
    result = await resolve_turn(state, _make_input(text="yes"), mock_script_agent)

    assert state.current_step == "STEP_2_MISSION"  # NOT advanced yet
    assert result.auto_advance is True
    assert state.invitation_accepted is True


@pytest.mark.asyncio
async def test_invitation_accepted_auto_advance_generates_round_prompt(mock_script_agent):
    """Auto-advance after acceptance: advance to STEP_3, generate round prompt."""
    mock_script_agent.generate_turn.return_value = _mock_turn(
        dialogue="I wonder if something soft is nearby?",
        stay_on_step=True,
    )
    state = _make_state("STEP_2_MISSION", invitation_accepted=True)
    result = await resolve_turn(state, _make_input(), mock_script_agent)

    assert state.current_step == "STEP_3_COLLECT_1"
    assert state.invitation_accepted is False


@pytest.mark.asyncio
async def test_invitation_decline_stays_on_step(mock_script_agent):
    """Decline: stay on STEP_2, increment decline count."""
    mock_script_agent.generate_turn.return_value = _mock_turn(
        dialogue="That's okay! What if we try together?",
        child_intent="declined",
    )
    state = _make_state("STEP_2_MISSION")
    result = await resolve_turn(state, _make_input(text="no"), mock_script_agent)

    assert state.current_step == "STEP_2_MISSION"
    assert state.invitation_decline_count == 1
    assert result.auto_advance is False


@pytest.mark.asyncio
async def test_invitation_second_decline_exits(mock_script_agent):
    """Second decline: exit gracefully."""
    mock_script_agent.generate_turn.side_effect = [
        _mock_turn(dialogue="That's okay!", child_intent="declined"),
        _mock_turn(dialogue="See you next time!"),
    ]
    state = _make_state("STEP_2_MISSION", invitation_decline_count=1)
    result = await resolve_turn(state, _make_input(text="no"), mock_script_agent)

    assert state.current_step == "EARLY_EXIT"
    assert state.status == "exited"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/test_turn_handler.py -v`
Expected: FAIL — `turn_handler` module does not exist

### Subtask 1b: Implement `resolve_turn()` invitation logic

- [ ] **Step 3: Create `backend/turn_handler.py` with invitation handling**

```python
# backend/turn_handler.py
"""Unified turn resolution logic for both /api/turn and /api/turn-speak.

This module extracts the step transition logic that was previously duplicated
across the two turn endpoints, ensuring consistent behavior for invitation
acceptance, round advancement, auto-advance signaling, and history management.
"""

from dataclasses import dataclass

from agents.script_agent import ScriptAgent
from schemas import ScreenFrame
from schemas.session_state import ConversationTurn, SessionStateModel
from schemas.turn_response import TurnResponse
from state_machine import (
    EARLY_EXIT,
    get_screen_frame,
    is_terminal,
    next_step,
    step_needs_user_input,
)


@dataclass
class TurnInput:
    text: str = ""
    is_silent: bool = False
    photo_id: str | None = None


@dataclass
class TurnResult:
    turn_response: TurnResponse
    screen_frame: ScreenFrame
    auto_advance: bool
    response_type: str
    error_exit: bool = False


# --- Helper predicates ---

def _is_invitation_step(step: str) -> bool:
    return step in ("STEP_2_RULES", "STEP_2_MISSION")


def _is_round_step(step: str) -> bool:
    return step.startswith("STEP_3_ROUND_") or step.startswith("STEP_3_COLLECT_")


def _is_closing_step(step: str) -> bool:
    return step in ("STEP_5_CLOSING", "STEP_6_CLOSING")


def _already_prompted_on_step(state: SessionStateModel) -> bool:
    """Check if the AI already generated a response for the current step."""
    return any(
        t.step == state.current_step and t.role == "ai"
        for t in state.conversation_history
    )


def _advance_state(state: SessionStateModel) -> None:
    """Advance to the next step and sync round number."""
    state.current_step = next_step(
        state.current_step, state.template_type, state.current_round, state.total_rounds
    )
    _sync_round_from_step(state)


def _sync_round_from_step(state: SessionStateModel) -> None:
    """Update current_round based on the step name."""
    step = state.current_step
    for prefix in ("STEP_3_ROUND_", "STEP_3_COLLECT_"):
        if step.startswith(prefix):
            try:
                state.current_round = int(step[len(prefix):])
            except ValueError:
                pass
            return


def _state_context(state: SessionStateModel) -> dict:
    """Build context dict for screen frame generation."""
    return {
        "entity_name": state.entity_name,
        "entity": state.entity_name,
        "ib_key_concepts": getattr(state, "ib_key_concepts", []),
        "key_concepts": getattr(state, "ib_key_concepts", []),
    }


def _get_screen_frame(state: SessionStateModel) -> ScreenFrame:
    """Get screen frame for the current step."""
    return get_screen_frame(
        state.current_step,
        state.template_type,
        state.creative_slots,
        _state_context(state),
        visual_frames=state.visual_frames or None,
        celebration_frame=state.celebration_frame,
    )


def _get_response_type(step: str) -> str:
    """Map step to response type string."""
    if step == "STEP_1_HOOK":
        return "hook"
    if step in ("STEP_2_RULES", "STEP_2_MISSION"):
        return "rules"
    if step.startswith("STEP_3_"):
        return "round"
    if step in ("STEP_4_CELEBRATE", "STEP_5_CELEBRATE"):
        return "celebration"
    if step == "STEP_4_SYNTHESIS":
        return "synthesis"
    if step in ("STEP_5_CLOSING", "STEP_6_CLOSING"):
        return "closing"
    if step == "EARLY_EXIT":
        return "graceful_exit"
    return "unknown"


def _append_child_turn(state: SessionStateModel, text: str) -> None:
    """Record child input in conversation history."""
    round_number = state.current_round if state.current_round > 0 else None
    state.conversation_history.append(
        ConversationTurn(
            role="child",
            text=text,
            step=state.current_step,
            round_number=round_number,
        )
    )


def _append_ai_turn(state: SessionStateModel, dialogue: str) -> None:
    """Record AI response in conversation history and trim."""
    state.conversation_history.append(
        ConversationTurn(
            role="ai",
            text=dialogue,
            step=state.current_step,
            round_number=state.current_round if state.current_round > 0 else None,
        )
    )
    if len(state.conversation_history) > 8:
        state.conversation_history = state.conversation_history[-8:]


async def _generate(agent: ScriptAgent, state: SessionStateModel) -> TurnResponse:
    """Generate a turn with retry logic."""
    # Delegate to ScriptAgent — retry logic is inside generate_turn
    return await agent.generate_turn(state)


# --- Main entry point ---

async def resolve_turn(
    state: SessionStateModel,
    turn_input: TurnInput,
    script_agent: ScriptAgent,
) -> TurnResult:
    """Process one turn: record input, determine step action, generate response.

    Returns TurnResult with the response, screen frame, auto-advance flag,
    and response type. The caller (endpoint handler) is responsible for
    serialization, TTS, logging, and DB updates.
    """
    has_child_input = bool(turn_input.text) or bool(turn_input.photo_id) or turn_input.is_silent

    # --- 1. Record child input ---
    if turn_input.text or turn_input.is_silent:
        child_text = turn_input.text if turn_input.text else "..."
        _append_child_turn(state, child_text)

    # --- 2. Handle silence counting ---
    if turn_input.is_silent:
        state.consecutive_silence += 1
    elif not turn_input.is_silent:
        state.consecutive_silence = 0

    # --- 3. Consecutive silence exit ---
    if state.consecutive_silence >= 2:
        state.current_step = EARLY_EXIT
        state.status = "exited"
        turn_response = await _generate(script_agent, state)
        _append_ai_turn(state, turn_response.dialogue)
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type="graceful_exit",
        )

    # --- 4. Step-specific logic ---

    # 4a. Invitation: deferred acceptance (auto-advance from previous turn)
    if _is_invitation_step(state.current_step) and state.invitation_accepted:
        state.invitation_accepted = False
        _advance_state(state)
        turn_response = await _generate(script_agent, state)
        # Don't auto-advance into round steps — child needs to interact with the gallery
        auto_advance = not _is_round_step(state.current_step) and _should_auto_advance(state)
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=auto_advance,
            response_type=_get_response_type(state.current_step),
        )

    # 4b. Invitation: normal handling
    if _is_invitation_step(state.current_step):
        turn_response = await _generate(script_agent, state)

        if turn_response.child_intent == "declined":
            state.invitation_decline_count += 1
            if state.invitation_decline_count >= 2:
                state.current_step = EARLY_EXIT
                state.status = "exited"
                turn_response = await _generate(script_agent, state)
                _append_ai_turn(state, turn_response.dialogue)
                state.turn_count += 1
                return TurnResult(
                    turn_response=turn_response,
                    screen_frame=_get_screen_frame(state),
                    auto_advance=False,
                    response_type="graceful_exit",
                )
            # First decline: stay on STEP_2, re-invite
            _append_ai_turn(state, turn_response.dialogue)
            state.turn_count += 1
            return TurnResult(
                turn_response=turn_response,
                screen_frame=_get_screen_frame(state),
                auto_advance=False,
                response_type=_get_response_type(state.current_step),
            )

        if turn_response.child_intent == "accepted":
            state.invitation_decline_count = 0
            state.invitation_accepted = True
            # Stay on STEP_2, but signal auto-advance so frontend
            # sends the next turn (which will advance to STEP_3).
            _append_ai_turn(state, turn_response.dialogue)
            state.turn_count += 1
            return TurnResult(
                turn_response=turn_response,
                screen_frame=_get_screen_frame(state),
                auto_advance=True,
                response_type=_get_response_type(state.current_step),
            )

        # Null / off-topic: stay on STEP_2, no auto-advance
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type=_get_response_type(state.current_step),
        )

    # 4c. Round steps
    if _is_round_step(state.current_step):
        turn_response = await _generate(script_agent, state)
        auto_advance = False

        if not turn_response.stay_on_step:
            prev_step = state.current_step
            _advance_state(state)

            if is_terminal(state.current_step):
                state.status = "completed"

            # Auto-advance only into other rounds or auto-advance steps
            if (
                has_child_input
                and prev_step != state.current_step
                and not is_terminal(state.current_step)
                and (_is_round_step(state.current_step) or not step_needs_user_input(state.current_step))
            ):
                auto_advance = True

        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=auto_advance or _should_auto_advance(state),
            response_type=_get_response_type(state.current_step),
        )

    # 4d. Non-round, non-invitation steps (synthesis, celebrate, closing)
    if step_needs_user_input(state.current_step) and not _already_prompted_on_step(state):
        # First visit to interactive step (e.g. STEP_4_SYNTHESIS): generate prompt
        turn_response = await _generate(script_agent, state)
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type=_get_response_type(state.current_step),
        )

    if step_needs_user_input(state.current_step):
        # Already prompted: child responded (or silence). Advance past it.
        _advance_state(state)
    else:
        # Auto-advance step (celebrate, closing): advance first.
        _advance_state(state)

    if is_terminal(state.current_step):
        state.status = "completed"
        return TurnResult(
            turn_response=TurnResponse(dialogue="", tone_marker=""),
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type="ended",
        )

    turn_response = await _generate(script_agent, state)
    _append_ai_turn(state, turn_response.dialogue)
    state.turn_count += 1

    auto_advance = _should_auto_advance(state)
    if _is_closing_step(state.current_step):
        state.status = "completed"

    return TurnResult(
        turn_response=turn_response,
        screen_frame=_get_screen_frame(state),
        auto_advance=auto_advance,
        response_type=_get_response_type(state.current_step),
    )


def _should_auto_advance(state: SessionStateModel) -> bool:
    """Auto-advance for steps that don't need user input (celebrate, closing)."""
    return (
        state.status == "active"
        and not step_needs_user_input(state.current_step)
        and not _is_closing_step(state.current_step)
    )


```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/test_turn_handler.py -v`
Expected: PASS (all invitation flow tests)

- [ ] **Step 5: Lint and format**

Run: `cd backend && uv run ruff check turn_handler.py tests/test_turn_handler.py && uv run ruff format turn_handler.py tests/test_turn_handler.py`

---

## Task 2: Add round step and synthesis tests

**Files:**
- Modify: `tests/test_turn_handler.py`

- [ ] **Step 1: Write tests for round step flow**

```python
@pytest.mark.asyncio
async def test_round_correct_pick_advances(mock_script_agent):
    """Correct pick on round step: advance to next round."""
    mock_script_agent.generate_turn.return_value = _mock_turn(
        dialogue="Great find!", stay_on_step=False
    )
    state = _make_state("STEP_3_COLLECT_1", collected_photos=["item1"])
    result = await resolve_turn(state, _make_input(photo_id="item1"), mock_script_agent)

    assert state.current_step == "STEP_3_COLLECT_2"
    assert result.auto_advance is True  # next round auto-advances


@pytest.mark.asyncio
async def test_round_wrong_pick_stays(mock_script_agent):
    """Wrong pick: stay on step."""
    mock_script_agent.generate_turn.return_value = _mock_turn(
        dialogue="Try again!", stay_on_step=True
    )
    state = _make_state("STEP_3_COLLECT_1")
    result = await resolve_turn(state, _make_input(photo_id="wrong"), mock_script_agent)

    assert state.current_step == "STEP_3_COLLECT_1"
    assert result.auto_advance is False


@pytest.mark.asyncio
async def test_last_round_does_not_auto_advance_into_synthesis(mock_script_agent):
    """Last collect round: advance to STEP_4_SYNTHESIS but don't auto-advance."""
    mock_script_agent.generate_turn.return_value = _mock_turn(
        dialogue="All done!", stay_on_step=False
    )
    state = _make_state("STEP_3_COLLECT_3", current_round=3, collected_photos=["a", "b", "c"])
    result = await resolve_turn(state, _make_input(photo_id="c"), mock_script_agent)

    assert state.current_step == "STEP_4_SYNTHESIS"
    assert result.auto_advance is False  # synthesis needs interaction


@pytest.mark.asyncio
async def test_synthesis_first_visit_generates_prompt(mock_script_agent):
    """First visit to STEP_4_SYNTHESIS: generate prompt, don't advance."""
    mock_script_agent.generate_turn.return_value = _mock_turn(
        dialogue="Let's look at your collection!"
    )
    state = _make_state("STEP_4_SYNTHESIS")
    # No AI turn in history for this step yet
    result = await resolve_turn(state, _make_input(is_silent=True), mock_script_agent)

    assert state.current_step == "STEP_4_SYNTHESIS"  # stays
    assert result.response_type == "synthesis"


@pytest.mark.asyncio
async def test_synthesis_second_visit_advances(mock_script_agent):
    """Second visit to STEP_4_SYNTHESIS: advance to celebrate."""
    mock_script_agent.generate_turn.return_value = _mock_turn(
        dialogue="You're amazing!"
    )
    state = _make_state("STEP_4_SYNTHESIS")
    # Simulate AI already prompted on this step
    state.conversation_history.append(
        ConversationTurn(role="ai", text="Let's look!", step="STEP_4_SYNTHESIS")
    )
    result = await resolve_turn(state, _make_input(text="cool"), mock_script_agent)

    assert state.current_step == "STEP_5_CELEBRATE"
```

- [ ] **Step 2: Run tests**

Run: `cd backend && uv run pytest tests/test_turn_handler.py -v`

---

## Task 3: Wire `resolve_turn()` into `/api/turn`

**Files:**
- Modify: `backend/server.py` — replace step transition logic in `process_turn()` with `resolve_turn()` call

The key change: replace lines ~507–630 (the entire step-specific if/elif/else block, auto-advance calculation, history append, and turn_count increment) with:

```python
from turn_handler import TurnInput, resolve_turn

# ... (silence exit and wrong photo exit stay as-is, they return early) ...

result = await resolve_turn(state, TurnInput(text=req.text, is_silent=req.is_silent, photo_id=req.photo_id), script_agent)

# Build response
turn_data = _build_turn_response(result.turn_response, result.screen_frame, result.response_type, result.error_exit)
turn_data["auto_advance"] = result.auto_advance

# ... logging, DB updates, return JSONResponse ...
```

- [ ] **Step 1: Replace step transition logic in `/api/turn` with `resolve_turn()`**
- [ ] **Step 2: Move silence exit and wrong photo handling into `resolve_turn()` (or keep as pre-checks)**
- [ ] **Step 3: Run existing tests**

Run: `cd backend && uv run pytest tests/ -v -k "not e2e"`

- [ ] **Step 4: Lint and format**

Run: `cd backend && uv run ruff check server.py turn_handler.py && uv run ruff format server.py turn_handler.py`

---

## Task 4: Wire `resolve_turn()` into `/api/turn-speak`

**Files:**
- Modify: `backend/server.py` — replace step transition logic in turn-speak handler

Same approach as Task 3 but for the streaming handler. The handler calls `resolve_turn()`, then streams JSON metadata + TTS audio.

- [ ] **Step 1: Replace step transition logic in turn-speak with `resolve_turn()`**
- [ ] **Step 2: Test manually — start a cat5 session, complete all steps**
- [ ] **Step 3: Lint and format**

---

## Task 5: Manual QA verification

- [ ] **Step 1: Cat5 full flow** — dandelion, accept invitation, collect 3 items, synthesis, celebrate, closing
  - Verify: no double responses, gallery appears only with collect prompt, synthesis prompt plays, no hallucinated collections
- [ ] **Step 2: Cat5 decline flow** — decline invitation, re-invitation, accept
  - Verify: no scope negotiation ("just find ONE"), same mission on re-invite
- [ ] **Step 3: Cat1 full flow** — dog, accept, 3 rounds, celebrate, closing
  - Verify: round numbers correct in device panel, footer shows `-` before rounds
- [ ] **Step 4: Silence handling** — let silence timer fire on various steps
  - Verify: no steps skipped, early exit after 2 consecutive silences

---

## Task 6: Update HANDOFF.md

- [ ] **Step 1: Add entry documenting the refactor**
- [ ] **Step 2: Remove oldest entries to keep 10 max**

---

## Notes

- **Photo validation**: The `resolve_turn()` function must include photo validation logic (currently in `server.py` as `_is_correct_collection_photo()` and `_record_correct_collection_pick()`). Move these into `turn_handler.py` and call them inside `resolve_turn()` before the step-specific logic. Wrong photo handling (stay on step, increment `consecutive_wrong`) and correct photo recording should happen before the round step branch.
- **Delete `_resolve_invitation_turn()`**: After wiring both endpoints to `resolve_turn()`, explicitly delete `_resolve_invitation_turn()` from `server.py`. The invitation logic is now inline in `resolve_turn()`.
- **Delete duplicated helpers**: After wiring, delete `_is_invitation_step()`, `_is_round_step()`, `_is_closing_step()`, `_should_auto_advance()`, `_advance_state()`, `_sync_round_from_step()`, and `_get_response_type()` from `server.py` — they now live in `turn_handler.py`.
- The `_generate_turn_with_retry()` wrapper in `server.py` should be moved to `turn_handler.py` as the `_generate()` helper.
- Conversation history is increased from 6 to 8 entries to reduce context loss on longer cat5 sessions.
- The `_build_turn_response()` helper stays in `server.py` (it builds the HTTP response dict).
