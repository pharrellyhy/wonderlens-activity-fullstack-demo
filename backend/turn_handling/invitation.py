"""Invitation step routing (section 7a of resolve_turn).

Handles STEP_2 invitation acceptance, decline (with graceful exit after
two consecutive declines), and re-invitation for off-topic responses.
"""

import random

try:
    from ..agents.script_agent import ScriptAgent
    from ..logger import setup_logger
    from ..schemas.creative_slots import Cat5CreativeSlots
    from ..schemas.session_state import SessionStateModel
    from ..schemas.turn_response import TurnResponse
    from ..state_machine import EARLY_EXIT
except ImportError:
    from agents.script_agent import ScriptAgent
    from logger import setup_logger
    from schemas.creative_slots import Cat5CreativeSlots
    from schemas.session_state import SessionStateModel
    from schemas.turn_response import TurnResponse
    from state_machine import EARLY_EXIT

from .debug import _build_debug_payload
from .generation import _generate_with_retry
from .helpers import (
    _ACCEPTANCE_CELEBRATIONS,
    _advance_state,
    _already_prompted_on_step,
    _append_ai_turn,
    _collection_photo_prompt,
    _get_response_type,
    _get_screen_frame,
    _is_invitation_step,
)
from .types import TurnInput, TurnResult

logger = setup_logger(__name__)


async def resolve_invitation(
    state: SessionStateModel,
    turn_input: TurnInput,
    script_agent: ScriptAgent,
    has_child_input: bool,
) -> TurnResult | None:
    """Route an invitation step based on pre-classified child intent.

    Returns a TurnResult if the current step is an invitation step,
    or None if the step is not an invitation step (caller should continue).
    """
    if not _is_invitation_step(state.current_step):
        return None

    is_first = not _already_prompted_on_step(state)

    async def _generate_reinvite_result() -> TurnResult:
        turn_response, gen_debug = await _generate_with_retry(script_agent, state, is_first_on_step=is_first)
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type=_get_response_type(state.current_step),
            error_exit=state.status == "error",
            debug=_build_debug_payload(state, gen_debug, script_agent, turn_response),
        )

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
                debug=_build_debug_payload(state, gen_debug, script_agent, turn_response),
            )
        # First decline: stay on STEP_2, re-invite
        return await _generate_reinvite_result()

    if state.child_intent == "confirm":
        state.invitation_decline_count = 0
        state.invitation_accepted = True
        _advance_state(state)
        # Combined celebration + finding prompt in one response — no auto-advance needed.
        # Uses deterministic templates since the LLM unreliably adds extra content.
        celebration = random.choice(_ACCEPTANCE_CELEBRATIONS)
        if state.current_step.startswith("STEP_3_COLLECT_") and isinstance(state.creative_slots, Cat5CreativeSlots):
            finding = _collection_photo_prompt(state)
            dialogue = f"{celebration} {finding.dialogue}"
        else:
            dialogue = celebration
        tone = dialogue.split("]")[0].strip("[")
        turn_response = TurnResponse(
            dialogue=dialogue,
            tone_marker=tone,
            screen_widget="photo_display" if state.current_step.startswith("STEP_3_") else "character_display",
            screen_widget_params={},
            stay_on_step=True,
        )
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type=_get_response_type(state.current_step),
            error_exit=False,
            debug=None,
        )

    # substantive / off_topic: stay on STEP_2, re-invite
    return await _generate_reinvite_result()
