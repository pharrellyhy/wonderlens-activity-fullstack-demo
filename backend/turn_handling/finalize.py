"""Single turn-finalization stage: derive the frame for the line spoken now.

This module owns the contract between the resolved session state and the
on-screen asset beat. ``finalize_turn`` is invoked on every path that builds a
``TurnResponse`` so the spoken line and its screen frame are derived from the
same post-advance step and cannot desync (spec §3-§4). Stream 2 guardrail
validators are layered into ``finalize_turn`` in later tasks.
"""

try:
    from ..schemas import ScreenFrame
    from ..schemas.session_state import SessionStateModel
    from ..schemas.turn_response import TurnResponse
    from ..state_machine import EARLY_EXIT
except ImportError:
    from schemas import ScreenFrame
    from schemas.session_state import SessionStateModel
    from schemas.turn_response import TurnResponse
    from state_machine import EARLY_EXIT

from .helpers import _get_screen_frame

# Explicit step -> beat lookup table. Shared contract with the frontend
# (frontend/src/activityGame/activityAssets.js beatForStep). Non-round steps
# only; round/collect/build steps derive ``round_N`` from the round number so
# both surfaces agree on the asset for the step whose line is spoken now.
STEP_BEAT_TABLE: dict[str, str] = {
    "STEP_1_HOOK": "intro",
    "STEP_2_RULES": "rules",
    "STEP_2_MISSION": "rules",
    "STEP_2_SETUP": "rules",
    "STEP_4_SYNTHESIS": "synthesis",
    "STEP_4_CELEBRATE": "celebrate",
    "STEP_5_CELEBRATE": "celebrate",
    "STEP_5_CLOSING": "closing",
    "STEP_6_CLOSING": "closing",
    EARLY_EXIT: "closing",
}

_ROUND_PREFIXES = ("STEP_3_ROUND_", "STEP_3_COLLECT_", "STEP_3_BUILD_")


def beat_for_step(step: str, current_round: int) -> str:
    """Return the asset beat id for the step whose line is spoken now.

    Args:
        step: Current state-machine step (post-advance — the same step the
            frontend reads from ``sessionState.current_step``).
        current_round: Active round number, used as a fallback when the step
            string carries no round suffix.

    Returns:
        The beat id (e.g. ``intro``, ``round_2``, ``celebrate``, ``closing``).
    """
    for prefix in _ROUND_PREFIXES:
        if step.startswith(prefix):
            try:
                round_number = int(step[len(prefix) :])
            except ValueError:
                round_number = current_round or 1
            return f"round_{round_number}"
    return STEP_BEAT_TABLE.get(step, "intro")


def derive_frame(state: SessionStateModel, action: str) -> ScreenFrame:
    """Derive the screen frame for the current (post-advance) step.

    The frame represents the step whose line is being spoken now — not a
    preview of the next step. ``action`` is the resolved directive action
    (advance/stay/need_help/redirect/exit) kept for future action-aware frame
    selection; today the frame is keyed purely on the resolved step.
    """
    frame = _get_screen_frame(state)
    frame.beat = beat_for_step(state.current_step, state.current_round)
    return frame


def finalize_turn(
    state: SessionStateModel,
    turn_response: TurnResponse,
    action: str,
) -> tuple[TurnResponse, ScreenFrame]:
    """Return the (safe line, matching frame) pair from one resolved state.

    Stream 1: derive the frame from the resolved step so dialogue and frame
    cannot desync. Stream 2 validators (contract/flow/wording/exhaustion) are
    added to this function in later tasks.
    """
    screen_frame = derive_frame(state, action)
    return turn_response, screen_frame
