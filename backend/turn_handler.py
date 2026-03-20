"""Unified turn resolution logic for both /api/turn and /api/turn-speak.

This module extracts the step transition logic that was previously duplicated
across the two turn endpoints, ensuring consistent behavior for invitation
acceptance, round advancement, auto-advance signaling, and history management.
"""

import re
from dataclasses import dataclass

try:
    from .agents.script_agent import ScriptAgent, ScriptAgentError
    from .logger import setup_logger
    from .schemas import ScreenFrame
    from .schemas.session_state import ConversationTurn, SessionStateModel
    from .schemas.turn_response import TurnResponse
    from .state_machine import (
        EARLY_EXIT,
        get_screen_frame,
        is_terminal,
        next_step,
        step_needs_user_input,
    )
except ImportError:
    from agents.script_agent import ScriptAgent, ScriptAgentError
    from logger import setup_logger
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

logger = setup_logger(__name__)


@dataclass
class TurnInput:
    """Encapsulates raw input from one child turn."""

    text: str = ""
    is_silent: bool = False
    photo_id: str | None = None


@dataclass
class TurnResult:
    """The resolved outcome of one turn, ready for the endpoint to serialize."""

    turn_response: TurnResponse
    screen_frame: ScreenFrame
    auto_advance: bool
    response_type: str
    error_exit: bool = False


# ---------------------------------------------------------------------------
# Helper predicates
# ---------------------------------------------------------------------------


def _is_invitation_step(step: str) -> bool:
    """Return True for STEP_2 invitation steps (rules or mission briefing)."""
    return step in {"STEP_2_RULES", "STEP_2_MISSION"}


def _is_round_step(step: str) -> bool:
    """Return True for any STEP_3 round or collection step."""
    return step.startswith("STEP_3_ROUND_") or step.startswith("STEP_3_COLLECT_")


def _is_closing_step(step: str) -> bool:
    """Return True when the active step is the final closing response."""
    return step in {"STEP_5_CLOSING", "STEP_6_CLOSING"}


def _already_prompted_on_step(state: SessionStateModel) -> bool:
    """Check if the AI already generated a response for the current step."""
    return any(t.step == state.current_step and t.role == "ai" for t in state.conversation_history)


# ---------------------------------------------------------------------------
# State mutation helpers
# ---------------------------------------------------------------------------


def _advance_state(state: SessionStateModel) -> None:
    """Advance to the next step and sync round number."""
    state.current_step = next_step(
        state.current_step,
        state.template_type,
        state.current_round,
        state.total_rounds,
    )
    _sync_round_from_step(state)


def _sync_round_from_step(state: SessionStateModel) -> None:
    """Keep current_round aligned with the active round/collect step."""
    step = state.current_step
    for prefix in ("STEP_3_ROUND_", "STEP_3_COLLECT_"):
        if step.startswith(prefix):
            try:
                state.current_round = int(step[len(prefix) :])
            except ValueError:
                pass
            return


def _step_round_number(step: str) -> int:
    """Extract a 1-based round number from a round/collect step."""
    return int(step.rsplit("_", maxsplit=1)[-1])


# ---------------------------------------------------------------------------
# Screen frame / response type helpers
# ---------------------------------------------------------------------------


def _state_context(state: SessionStateModel) -> dict:
    """Build context dict for screen frame generation."""
    return {
        "entity_name": state.entity_name,
        "entity": state.entity_name,
        "ib_key_concepts": state.ib_key_concepts,
        "key_concepts": state.ib_key_concepts,
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
    """Map a step to a response type string."""
    if step == "STEP_1_HOOK":
        return "hook"
    if step in ("STEP_2_RULES", "STEP_2_MISSION"):
        return "rules"
    if step.startswith("STEP_3_ROUND_") or step.startswith("STEP_3_COLLECT_"):
        return "round"
    if step in ("STEP_4_CELEBRATE", "STEP_5_CELEBRATE"):
        return "celebration"
    if step == "STEP_4_SYNTHESIS":
        return "synthesis"
    if step in ("STEP_5_CLOSING", "STEP_6_CLOSING"):
        return "closing"
    if step == EARLY_EXIT:
        return "graceful_exit"
    return "response"


def _ended_result(state: SessionStateModel) -> TurnResult:
    """Build the terminal response payload after advancing past the last step."""
    state.status = "completed"
    return TurnResult(
        turn_response=TurnResponse(
            dialogue="",
            tone_marker="",
            screen_widget="photo_display",
            screen_widget_params={},
        ),
        screen_frame=_get_screen_frame(state),
        auto_advance=False,
        response_type="ended",
        error_exit=False,
    )


# ---------------------------------------------------------------------------
# Conversation history helpers
# ---------------------------------------------------------------------------

_HISTORY_LIMIT = 8


def _append_child_turn(state: SessionStateModel, text: str, *, include_round_number: bool = True) -> None:
    """Record child input in conversation history."""
    round_number = state.current_round if include_round_number and state.current_round > 0 else None
    state.conversation_history.append(
        ConversationTurn(
            role="child",
            text=text,
            step=state.current_step,
            round_number=round_number,
        )
    )


def _append_ai_turn(state: SessionStateModel, dialogue: str) -> None:
    """Record AI response in conversation history and trim to limit."""
    state.conversation_history.append(
        ConversationTurn(
            role="ai",
            text=dialogue,
            step=state.current_step,
            round_number=state.current_round if state.current_round > 0 else None,
        )
    )
    if len(state.conversation_history) > _HISTORY_LIMIT:
        state.conversation_history = state.conversation_history[-_HISTORY_LIMIT:]


# ---------------------------------------------------------------------------
# Photo validation helpers (Cat 5 collection)
# ---------------------------------------------------------------------------


# Patterns that indicate the LLM is prematurely declaring the collection complete.
# Used when remaining_count > 0 to catch hallucinated completion language.
_COMPLETION_PATTERNS = re.compile(
    r"(?i)\b(?:"
    r"final\s+(?:treasure|find|discovery|one|item|piece)"
    r"|(?:last|final)\s+(?:spotted|dotted|polka|circle)"
    r"|(?:all|every)\s+(?:found|collected|done|complete)"
    r"|mission\s+(?:complete|accomplished|done)"
    r"|collection\s+(?:is\s+)?(?:complete|done|finished)"
    r"|(?:found|got|collected)\s+them\s+all"
    r"|finish(?:ed|es)?\s+(?:our|the)\s+(?:mission|collection|patrol)"
    r"|perfect\s+final"
    r")\b"
)


def _has_completion_language(dialogue: str) -> bool:
    """Check if dialogue contains language implying the collection is complete."""
    return bool(_COMPLETION_PATTERNS.search(dialogue))


def _is_correct_collection_photo(state: SessionStateModel, photo_id: str) -> bool:
    """Check if the selected photo matches the current round's correct item."""
    round_num = _step_round_number(state.current_step)
    round_idx = round_num - 1
    if round_idx < 0 or round_idx >= len(state.round_items):
        return True  # no round items configured — accept anything
    return any(item["id"] == photo_id and item.get("correct", False) for item in state.round_items[round_idx])


def _get_item_label(state: SessionStateModel, photo_id: str) -> str:
    """Look up the display label for a photo_id in the current round's items."""
    round_num = _step_round_number(state.current_step)
    round_idx = round_num - 1
    if 0 <= round_idx < len(state.round_items):
        for item in state.round_items[round_idx]:
            if item["id"] == photo_id:
                return item["label"]
    return photo_id.replace("_", " ")


def _record_correct_collection_pick(state: SessionStateModel, photo_id: str) -> None:
    """Record a correct pick: add to collected_photos, reset wrong counter, log in history."""
    state.collected_photos.append(photo_id)
    state.consecutive_wrong = 0
    _append_child_turn(state, f"[collected correct item: {_get_item_label(state, photo_id)}]")


# ---------------------------------------------------------------------------
# LLM generation with retry
# ---------------------------------------------------------------------------


async def _generate_with_retry(script_agent: ScriptAgent, state: SessionStateModel) -> TurnResponse:
    """Generate a turn response with one retry on failure, then graceful fallback."""
    try:
        return await script_agent.generate_turn(state)
    except ScriptAgentError:
        logger.warning(f"Script Agent failed for step {state.current_step}, retrying")
        try:
            return await script_agent.generate_turn(state)
        except ScriptAgentError:
            logger.error(f"Script Agent failed twice for step {state.current_step}, using fallback")
            state.status = "error"
            return TurnResponse(
                dialogue="[gentle] That was so much fun! Would you like to play again next time? See you soon!",
                tone_marker="gentle",
                screen_widget="badge_award",
                screen_widget_params={"title": "Great job!", "concepts": [], "entity": state.entity_name},
                screen_animation="badge_reveal",
                sfx_cue="badge_awarded",
            )


# ---------------------------------------------------------------------------
# Auto-advance logic
# ---------------------------------------------------------------------------


def _should_auto_advance(state: SessionStateModel) -> bool:
    """Auto-advance for steps that don't need user input (celebrate, closing).

    Does NOT auto-advance closing steps — those are terminal-adjacent and
    the frontend should not send another turn after them.
    """
    return (
        state.status == "active"
        and not step_needs_user_input(state.current_step)
        and not _is_closing_step(state.current_step)
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def resolve_turn(
    state: SessionStateModel,
    turn_input: TurnInput,
    script_agent: ScriptAgent,
) -> TurnResult:
    """Process one turn: record input, determine step action, generate response.

    This is the single source of truth for step transition logic. Both
    /api/turn and /api/turn-speak call this function; the endpoint handler
    is responsible for serialization, TTS streaming, logging, and DB updates.

    Args:
        state: Mutable session state — modified in place.
        turn_input: The child's input for this turn.
        script_agent: ScriptAgent instance for LLM generation.

    Returns:
        TurnResult with the response, screen frame, auto-advance flag,
        response type, and error_exit flag.
    """
    has_child_input = bool(turn_input.text) or bool(turn_input.photo_id) or turn_input.is_silent

    # --- 1. Silence counting ---
    if turn_input.is_silent:
        state.consecutive_silence += 1
    else:
        state.consecutive_silence = 0

    # --- 2. Consecutive silence exit (>= 2) ---
    if state.consecutive_silence >= 2:
        # Record the silence in history before exiting
        if turn_input.is_silent:
            _append_child_turn(state, "...")
        state.current_step = EARLY_EXIT
        state.status = "exited"
        turn_response = await _generate_with_retry(script_agent, state)
        _append_ai_turn(state, turn_response.dialogue)
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type="graceful_exit",
            error_exit=state.status == "error",
        )

    # --- 3. Record child input in conversation history ---
    if turn_input.text or turn_input.is_silent:
        child_text = turn_input.text if turn_input.text else "..."
        _append_child_turn(state, child_text)

    # --- 4. Cat 5 collection: validate photo_id before step logic ---
    collection_wrong = False
    if turn_input.photo_id and state.current_step.startswith("STEP_3_COLLECT_"):
        if _is_correct_collection_photo(state, turn_input.photo_id):
            _record_correct_collection_pick(state, turn_input.photo_id)
        else:
            collection_wrong = True
            state.consecutive_wrong += 1

    # --- 5. Consecutive wrong picks exit (>= 2) ---
    if state.consecutive_wrong >= 2:
        state.current_step = EARLY_EXIT
        state.status = "exited"
        turn_response = await _generate_with_retry(script_agent, state)
        _append_ai_turn(state, turn_response.dialogue)
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type="graceful_exit",
            error_exit=state.status == "error",
        )

    # --- 6. Wrong pick retry (stay on step, generate "try again") ---
    if collection_wrong:
        _append_child_turn(state, f"[selected wrong photo: {turn_input.photo_id}]", include_round_number=False)
        turn_response = await _generate_with_retry(script_agent, state)
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type="wrong_photo",
            error_exit=state.status == "error",
        )

    # --- 7. Step-specific logic ---

    # 7a. Invitation: normal handling (first delivery, acceptance, decline, off-topic)
    if _is_invitation_step(state.current_step):
        turn_response = await _generate_with_retry(script_agent, state)

        if turn_response.child_intent == "declined":
            state.invitation_decline_count += 1
            if state.invitation_decline_count >= 2:
                # Second decline: graceful exit
                state.current_step = EARLY_EXIT
                state.status = "exited"
                turn_response = await _generate_with_retry(script_agent, state)
                _append_ai_turn(state, turn_response.dialogue)
                state.turn_count += 1
                return TurnResult(
                    turn_response=turn_response,
                    screen_frame=_get_screen_frame(state),
                    auto_advance=False,
                    response_type="graceful_exit",
                    error_exit=state.status == "error",
                )
            # First decline: stay on STEP_2, re-invite
            _append_ai_turn(state, turn_response.dialogue)
            state.turn_count += 1
            return TurnResult(
                turn_response=turn_response,
                screen_frame=_get_screen_frame(state),
                auto_advance=False,
                response_type=_get_response_type(state.current_step),
                error_exit=state.status == "error",
            )

        if turn_response.child_intent == "accepted":
            state.invitation_decline_count = 0
            # Advance immediately to first round/collect step — single response
            _advance_state(state)
            turn_response = await _generate_with_retry(script_agent, state)
            _append_ai_turn(state, turn_response.dialogue)
            state.turn_count += 1
            return TurnResult(
                turn_response=turn_response,
                screen_frame=_get_screen_frame(state),
                auto_advance=_should_auto_advance(state),
                response_type=_get_response_type(state.current_step),
                error_exit=state.status == "error",
            )

        # Null / off-topic: stay on STEP_2, no auto-advance
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type=_get_response_type(state.current_step),
            error_exit=state.status == "error",
        )

    # 7c. Round steps (STEP_3_ROUND_* / STEP_3_COLLECT_*)
    if _is_round_step(state.current_step):
        if state.round_advance_pending and not has_child_input:
            state.round_advance_pending = False
            _advance_state(state)

            if is_terminal(state.current_step):
                return _ended_result(state)

            turn_response = await _generate_with_retry(script_agent, state)
            _append_ai_turn(state, turn_response.dialogue)
            state.turn_count += 1

            if _is_closing_step(state.current_step):
                state.status = "completed"

            return TurnResult(
                turn_response=turn_response,
                screen_frame=_get_screen_frame(state),
                auto_advance=_should_auto_advance(state),
                response_type=_get_response_type(state.current_step),
                error_exit=state.status == "error",
            )

        # Generate response FIRST (for current step), then decide whether to advance.
        # This lets the Script Agent help a stuck child without skipping steps.
        turn_response = await _generate_with_retry(script_agent, state)
        auto_advance = False

        # Guardrail: detect premature completion language during collection when items remain.
        # The LLM sometimes says "final treasure" or "all done" even when remaining_count > 0.
        if (
            state.current_step.startswith("STEP_3_COLLECT_")
            and len(state.collected_photos) < state.total_rounds
            and _has_completion_language(turn_response.dialogue)
        ):
            logger.warning(
                "Detected premature completion language in collection response "
                f"(collected={len(state.collected_photos)}/{state.total_rounds}), regenerating"
            )
            # Append a corrective hint to conversation history, regenerate, then remove the hint
            corrective_hint = (
                f"[system: The collection is NOT complete — {len(state.collected_photos)} of "
                f"{state.total_rounds} collected, {state.total_rounds - len(state.collected_photos)} still "
                f"needed. Do NOT use words like 'final', 'last', 'complete', 'all done', or 'mission complete'. "
                f"Celebrate this find, then ask about finding the NEXT one.]"
            )
            _append_child_turn(state, corrective_hint, include_round_number=False)
            turn_response = await _generate_with_retry(script_agent, state)
            # Remove the corrective hint from history so it doesn't leak
            state.conversation_history = [t for t in state.conversation_history if t.text != corrective_hint]

        # Override stay_on_step when Cat5 collection is objectively complete
        if (
            turn_response.stay_on_step
            and state.current_step.startswith("STEP_3_COLLECT_")
            and len(state.collected_photos) >= state.total_rounds
        ):
            logger.info("Overriding stay_on_step: collection complete, forcing advancement")
            turn_response.stay_on_step = False

        if not turn_response.stay_on_step and has_child_input:
            if state.current_step.startswith("STEP_3_COLLECT_"):
                # Cat5 collect: advance immediately — single combined response
                _advance_state(state)
                if is_terminal(state.current_step):
                    return _ended_result(state)
                turn_response = await _generate_with_retry(script_agent, state)
            else:
                # Cat1 round: check whether to defer or advance immediately
                next_step_name = next_step(
                    state.current_step,
                    state.template_type,
                    state.current_round,
                    state.total_rounds,
                )
                next_step_needs_input = step_needs_user_input(next_step_name)

                if _is_round_step(next_step_name) or not next_step_needs_input:
                    state.round_advance_pending = True
                    auto_advance = True
                else:
                    _advance_state(state)

                    if is_terminal(state.current_step):
                        return _ended_result(state)

                    turn_response = await _generate_with_retry(script_agent, state)

        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=auto_advance or _should_auto_advance(state),
            response_type=_get_response_type(state.current_step),
            error_exit=state.status == "error",
        )

    # 7d. Non-round, non-invitation steps (synthesis, celebrate, closing)

    # Interactive step (e.g. STEP_4_SYNTHESIS): first visit generates prompt
    if step_needs_user_input(state.current_step) and not _already_prompted_on_step(state):
        turn_response = await _generate_with_retry(script_agent, state)
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type=_get_response_type(state.current_step),
            error_exit=state.status == "error",
        )

    # Interactive step already prompted: hook advances into STEP_2, synthesis returns its
    # own completion response before advancing to the next auto-advance step.
    if step_needs_user_input(state.current_step):
        if state.current_step == "STEP_1_HOOK":
            _advance_state(state)
            turn_response = await _generate_with_retry(script_agent, state)
            _append_ai_turn(state, turn_response.dialogue)
            state.turn_count += 1
            return TurnResult(
                turn_response=turn_response,
                screen_frame=_get_screen_frame(state),
                auto_advance=False,
                response_type=_get_response_type(state.current_step),
                error_exit=state.status == "error",
            )

        turn_response = await _generate_with_retry(script_agent, state)

        # Guardrail: override stay_on_step when the response still invites child input.
        # The LLM sometimes sets stay_on_step=false even when the dialogue ends with a
        # question — which would auto-advance past the child's chance to respond.
        if not turn_response.stay_on_step and state.current_step == "STEP_4_SYNTHESIS":
            dialogue_stripped = turn_response.dialogue.rstrip()
            synthesis_child_turns = sum(
                1 for t in state.conversation_history if t.step == "STEP_4_SYNTHESIS" and t.role == "child"
            )
            if dialogue_stripped.endswith("?"):
                logger.info("Overriding stay_on_step: synthesis response ends with question")
                turn_response.stay_on_step = True
            elif synthesis_child_turns < 2:
                logger.info("Overriding stay_on_step: synthesis needs at least 2 child turns")
                turn_response.stay_on_step = True

        if turn_response.stay_on_step:
            # Child needs help (stuck, confused) — stay and respond
            _append_ai_turn(state, turn_response.dialogue)
            state.turn_count += 1
            return TurnResult(
                turn_response=turn_response,
                screen_frame=_get_screen_frame(state),
                auto_advance=False,
                response_type=_get_response_type(state.current_step),
                error_exit=state.status == "error",
            )
        # Step complete — return THIS response (not the next step's), then advance
        response_type = _get_response_type(state.current_step)
        screen_frame = _get_screen_frame(state)
        _append_ai_turn(state, turn_response.dialogue)
        _advance_state(state)
        state.turn_count += 1
        if is_terminal(state.current_step):
            state.status = "completed"
        return TurnResult(
            turn_response=turn_response,
            screen_frame=screen_frame,
            auto_advance=not is_terminal(state.current_step) and not step_needs_user_input(state.current_step),
            response_type=response_type,
            error_exit=state.status == "error",
        )

    # Auto-advance step (celebrate, closing): check if already generated
    if _already_prompted_on_step(state):
        # Already generated (e.g. Cat1 celebrate from round advance) — advance through
        _advance_state(state)
        if is_terminal(state.current_step):
            return _ended_result(state)
        turn_response = await _generate_with_retry(script_agent, state)
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        if _is_closing_step(state.current_step):
            state.status = "completed"
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=_should_auto_advance(state),
            response_type=_get_response_type(state.current_step),
            error_exit=state.status == "error",
        )

    # Not yet generated (e.g. Cat5 celebrate after synthesis) — generate then advance
    turn_response = await _generate_with_retry(script_agent, state)
    response_type = _get_response_type(state.current_step)
    screen_frame = _get_screen_frame(state)
    _append_ai_turn(state, turn_response.dialogue)
    state.turn_count += 1

    if _is_closing_step(state.current_step):
        state.status = "completed"
        _advance_state(state)
        return TurnResult(
            turn_response=turn_response,
            screen_frame=screen_frame,
            auto_advance=False,
            response_type=response_type,
            error_exit=state.status == "error",
        )

    _advance_state(state)
    if is_terminal(state.current_step):
        state.status = "completed"

    return TurnResult(
        turn_response=turn_response,
        screen_frame=screen_frame,
        auto_advance=not is_terminal(state.current_step) and not step_needs_user_input(state.current_step),
        response_type=response_type,
        error_exit=state.status == "error",
    )
