"""Round step generation with deferred advance and guardrails (section 7c).

Handles STEP_3_ROUND_* (Cat1) and STEP_3_COLLECT_* (Cat5) steps including:
- Deferred advance after detail phase completion
- Cat5 photo phase deterministic prompts
- Premature completion language guardrail
- Phase B detail entry guardrail
- Collection-complete override guardrail
- Cat5 immediate advance vs Cat1 deferred advance
"""

try:
    from ..agents.script_agent import ScriptAgent
    from ..logger import setup_logger
    from ..schemas.creative_slots import Cat5CreativeSlots
    from ..schemas.session_state import SessionStateModel
    from ..state_machine import is_terminal, next_step, step_needs_user_input
except ImportError:
    from agents.script_agent import ScriptAgent
    from logger import setup_logger
    from schemas.creative_slots import Cat5CreativeSlots
    from schemas.session_state import SessionStateModel
    from state_machine import is_terminal, next_step, step_needs_user_input

from .debug import _build_debug_payload
from .finalize import derive_frame, finalize_turn
from .generation import _generate_with_retry, _has_completion_language
from .helpers import (
    _advance_state,
    _append_ai_turn,
    _append_child_turn,
    _collection_photo_prompt,
    _ended_result,
    _get_response_type,
    _is_closing_step,
    _is_round_step,
    _should_auto_advance,
)
from .types import TurnInput, TurnResult

logger = setup_logger(__name__)


async def resolve_round(
    state: SessionStateModel,
    turn_input: TurnInput,
    script_agent: ScriptAgent,
    has_child_input: bool,
    *,
    collection_wrong: bool = False,
) -> TurnResult | None:
    """Handle round step generation (section 7c of resolve_turn).

    Covers STEP_3_ROUND_* and STEP_3_COLLECT_* steps with deferred advance,
    deterministic photo prompts, and three guardrails for collection integrity.

    Returns a TurnResult if the current step is a round step,
    or None if the step is not a round step (caller should continue).
    """
    if not _is_round_step(state.current_step):
        return None

    def _photo_prompt_result() -> TurnResult:
        turn_response = _collection_photo_prompt(state)
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(
            turn_response=turn_response,
            screen_frame=derive_frame(state, "stay"),
            auto_advance=False,
            response_type=_get_response_type(state.current_step),
            error_exit=False,
            debug=None,
        )

    # --- Deferred advance path ---
    # After detail phase completes, the advance is deferred to the next
    # empty turn so the naming/transition dialogue plays first.
    if state.round_advance_pending and not has_child_input:
        state.round_advance_pending = False
        if state.current_step.startswith("STEP_3_COLLECT_"):
            logger.info("Deferred advance: detail -> photo, advancing to next round")
            state.collection_phase = "photo"
        _advance_state(state)
        logger.info(
            "After advance: step=%s round=%d phase=%s",
            state.current_step,
            state.current_round,
            state.collection_phase,
        )

        if is_terminal(state.current_step):
            return _ended_result(state)

        # For collection steps entering photo phase, use deterministic
        # template — the LLM unreliably generates "you found!" when
        # nothing was found. Other steps (celebrate, closing) use LLM.
        if (
            state.current_step.startswith("STEP_3_COLLECT_")
            and state.collection_phase == "photo"
            and isinstance(state.creative_slots, Cat5CreativeSlots)
        ):
            return _photo_prompt_result()

        turn_response, gen_debug = await _generate_with_retry(script_agent, state, is_first_on_step=True)

        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1

        if _is_closing_step(state.current_step):
            state.status = "completed"

        return TurnResult(
            turn_response=turn_response,
            screen_frame=derive_frame(state, "advance"),
            auto_advance=_should_auto_advance(state),
            response_type=_get_response_type(state.current_step),
            error_exit=state.status == "error",
            debug=_build_debug_payload(state, gen_debug, script_agent, turn_response),
        )

    # --- Cat5 photo phase no-input auto-advance ---
    # Cat5 photo phase with no child input = auto-advance into new round.
    # Use a deterministic template — the LLM is unreliable here and often
    # generates "you found something!" when nothing was found.
    if (
        state.current_step.startswith("STEP_3_COLLECT_")
        and state.collection_phase == "photo"
        and not has_child_input
        and isinstance(state.creative_slots, Cat5CreativeSlots)
    ):
        return _photo_prompt_result()

    # --- Main generation path ---
    # Generate response FIRST (for current step), then decide whether to advance.
    # This lets the Script Agent help a stuck child without skipping steps.
    # Pass is_first_on_step when entering detail phase (correct photo just picked).
    entering_detail = (
        state.current_step.startswith("STEP_3_COLLECT_")
        and state.collection_phase == "detail"
        and collection_wrong is False
        and turn_input.photo_id is not None
    )
    turn_response, gen_debug = await _generate_with_retry(
        script_agent,
        state,
        is_first_on_step=entering_detail,
    )
    auto_advance = False

    # Guardrail 1: detect premature completion language during collection when items remain.
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
        turn_response, gen_debug = await _generate_with_retry(script_agent, state)
        # Remove the corrective hint from history so it doesn't leak
        state.conversation_history = [t for t in state.conversation_history if t.text != corrective_hint]

    # Guardrail 2: force stay_on_step when entering Phase B (detail question)
    # The AI just celebrated the correct photo and should ask the detail question;
    # do NOT advance to the next round yet.
    if (
        state.current_step.startswith("STEP_3_COLLECT_")
        and state.collection_phase == "detail"
        and not turn_response.stay_on_step
    ):
        logger.info("Forcing stay_on_step: Phase B detail question pending")
        turn_response.stay_on_step = True

    # Guardrail 3: Override stay_on_step when Cat5 collection is objectively complete
    # AND we are in photo phase (Phase B handler already advanced if needed)
    if (
        turn_response.stay_on_step
        and state.current_step.startswith("STEP_3_COLLECT_")
        and state.collection_phase == "photo"
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
            turn_response, gen_debug = await _generate_with_retry(script_agent, state)
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

                turn_response, gen_debug = await _generate_with_retry(script_agent, state)

    turn_response, screen_frame = await finalize_turn(
        state, turn_response, "advance" if not turn_response.stay_on_step else "stay", script_agent=script_agent
    )
    _append_ai_turn(state, turn_response.dialogue)
    state.turn_count += 1
    return TurnResult(
        turn_response=turn_response,
        screen_frame=screen_frame,
        auto_advance=auto_advance or _should_auto_advance(state),
        response_type=_get_response_type(state.current_step),
        error_exit=state.status == "error",
        debug=_build_debug_payload(state, gen_debug, script_agent, turn_response),
    )
