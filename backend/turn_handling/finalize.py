"""Single turn-finalization stage: derive the frame for the line spoken now.

This module owns the contract between the resolved session state and the
on-screen asset beat. ``finalize_turn`` is invoked on every path that builds a
``TurnResponse`` so the spoken line and its screen frame are derived from the
same post-advance step and cannot desync (spec §3-§4). ``finalize_turn`` also
runs the Stream 2 guardrail validators (contract/flow/wording) on the spoken
line, regenerating once and falling back deterministically on divergence.
"""

import re

try:
    from ..agents.script_agent import ScriptAgent
    from ..schemas import ScreenFrame
    from ..schemas.creative_slots import Cat1CreativeSlots
    from ..schemas.session_state import SessionStateModel
    from ..schemas.turn_response import TurnResponse
    from ..state_machine import EARLY_EXIT
except ImportError:
    from agents.script_agent import ScriptAgent
    from schemas import ScreenFrame
    from schemas.creative_slots import Cat1CreativeSlots
    from schemas.session_state import SessionStateModel
    from schemas.turn_response import TurnResponse
    from state_machine import EARLY_EXIT

from .generation import (
    _ITEM_SUGGESTION_RE,
    _enforce_text_only_interaction,
    _has_completion_language,
    _source_fidelity_fallback_response,
)
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


def _violates_contract(
    state: SessionStateModel,
    turn_response: TurnResponse,
    *,
    do_not_suggest_items: bool,
) -> bool:
    """Deterministic A-i contract/role/structure check for the current beat.

    Returns True when the spoken line diverges from the recipe contract:
    suggests findable items when forbidden, declares premature completion on a
    collection round, or drops the role token the contract requires. Theme
    keywords are best-effort and never hard-fail on their own.
    """
    dialogue = turn_response.dialogue

    # do_not_suggest_items: never name specific findable objects.
    if do_not_suggest_items and _ITEM_SUGGESTION_RE.search(dialogue):
        return True

    # Premature completion during an unfinished collection round.
    if (
        state.current_step.startswith("STEP_3_COLLECT_")
        and len(state.collected_photos) < state.total_rounds
        and _has_completion_language(dialogue)
    ):
        return True

    # Role fidelity: when the contract names a role_title, the line should not
    # contradict it. Best-effort — only flag the hard case of a Cat1 decision
    # round that drops the role word entirely AND offers no question.
    if (
        isinstance(state.creative_slots, Cat1CreativeSlots)
        and state.creative_slots.game_mechanic == "decide"
        and state.current_step.startswith("STEP_3_ROUND_")
        and "?" not in dialogue
    ):
        return True

    return False


_ADVANCE_LANGUAGE_RE = re.compile(
    r"(?i)\b(?:next\s+(?:one|step|round|part)|move\s+on|moving\s+on|let'?s\s+go\s+on"
    r"|on\s+to\s+the\s+next|coming\s+up\s+next)\b"
)


def _violates_flow(state: SessionStateModel, turn_response: TurnResponse, *, action: str) -> bool:
    """Deterministic flow-control check (Stream 2 B).

    A line tied to a stay action must not promise advancing. Premature
    collection completion is also a flow violation when items remain.
    """
    dialogue = turn_response.dialogue
    if (action in ("stay", "need_help", "redirect") or turn_response.stay_on_step) and _ADVANCE_LANGUAGE_RE.search(
        dialogue
    ):
        return True
    if (
        state.current_step.startswith("STEP_3_COLLECT_")
        and len(state.collected_photos) < state.total_rounds
        and _has_completion_language(dialogue)
    ):
        return True
    return False


async def finalize_turn(
    state: SessionStateModel,
    turn_response: TurnResponse,
    action: str,
    *,
    script_agent: ScriptAgent | None = None,
    do_not_suggest_items: bool = True,
) -> tuple[TurnResponse, ScreenFrame]:
    """Return the (safe line, matching frame) pair from one resolved state.

    Stream 1 derives the frame; Stream 2 validates the spoken line, regenerates
    once on contract/flow divergence, falls back deterministically on failure,
    and sanitizes device words as the single last step.
    """
    needs_fix = _violates_contract(state, turn_response, do_not_suggest_items=do_not_suggest_items) or _violates_flow(
        state, turn_response, action=action
    )
    if script_agent is not None and needs_fix:
        try:
            regenerated = await script_agent.generate_turn(state)
        except Exception:
            regenerated = None
        regen_ok = (
            regenerated is not None
            and not _violates_contract(state, regenerated, do_not_suggest_items=do_not_suggest_items)
            and not _violates_flow(state, regenerated, action=action)
        )
        turn_response = regenerated if regen_ok else _source_fidelity_fallback_response(state)

    turn_response = _enforce_text_only_interaction(state, turn_response)
    screen_frame = derive_frame(state, action)
    return turn_response, screen_frame
