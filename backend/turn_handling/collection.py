"""Cat5 photo validation and detail-phase logic.

Handles collection wrong-pick resolution and the detail-harvesting
exchange loop for Cat 5 out-of-device collection activities.
"""

import re

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
    _MAX_DETAIL_EXCHANGES,
    _append_ai_turn,
    _append_child_turn,
    _get_response_type,
    _get_screen_frame,
    _step_round_number,
)
from .types import GenerationDebugInfo, TurnInput, TurnResult

logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# Photo validation helpers (Cat 5 collection)
# ---------------------------------------------------------------------------


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


def record_text_collection_pick(state: SessionStateModel, text: str) -> None:
    """Record a typed Cat5 collection item in text-only mode."""
    label = text.strip()
    if not label:
        return
    item_id = f"text_find_{len(state.collected_text_items) + 1}"
    state.collected_text_items.append(label)
    state.collected_photos.append(item_id)
    state.consecutive_wrong = 0
    state.collection_phase = "detail"
    state.detail_exchange_count = 0


_GENERATED_NAME_PATTERNS = (
    re.compile('["\u201c\u201d]([^"\u201c\u201d]{1,40})["\u201c\u201d]'),
    re.compile(
        r"(?:how about|call (?:it|him|her|this(?: one)?)|let.s call (?:it|him|her|this(?: one)?))"
        r"\s+([A-Z][A-Za-z'.\-]+(?: [A-Z][A-Za-z'.\-]+){0,2})",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:Hello,?\s+|Hi,?\s+|Meet\s+)([A-Z][A-Za-z'.\-]+(?: [A-Z][A-Za-z'.\-]+){0,3})",
        re.IGNORECASE,
    ),
    re.compile(r"(?:^|\] )([A-Z][A-Za-z'.\-]+(?: [A-Z][A-Za-z'.\-]+){0,2})[!,.]"),
)


def _record_collection_detail(state: SessionStateModel, child_text: str) -> None:
    """Persist a non-empty detail response for Cat 5 collection rounds."""
    detail = child_text.strip()
    if detail and detail != "...":
        state.collected_details.append(detail)


def _maybe_record_generated_name(state: SessionStateModel, dialogue: str) -> None:
    """Store a generated character name when one is easy to extract."""
    if not isinstance(state.creative_slots, Cat5CreativeSlots):
        return
    if len(state.collected_names) >= len(state.collected_photos):
        return

    for pattern in _GENERATED_NAME_PATTERNS:
        match = pattern.search(dialogue)
        if match:
            name = match.group(1).strip(" .,!?:;")
            if name:
                state.collected_names.append(name)
                return


# ---------------------------------------------------------------------------
# Main resolution functions
# ---------------------------------------------------------------------------


async def resolve_collection_wrong_pick(
    state: SessionStateModel,
    turn_input: TurnInput,
    script_agent: ScriptAgent,
) -> TurnResult | None:
    """Handle Cat5 wrong-pick validation (sections 4-6 of resolve_turn).

    Returns a TurnResult if the pick was wrong (or triggers early exit),
    or None if the pick was correct and the caller should continue.
    """

    def _debug(gen_debug: GenerationDebugInfo | None, turn_response: TurnResponse | None = None) -> dict:
        return _build_debug_payload(state, gen_debug, script_agent, turn_response)

    # --- 4. Cat 5 collection: validate photo_id before step logic ---
    collection_wrong = False
    if turn_input.photo_id and state.current_step.startswith("STEP_3_COLLECT_"):
        if _is_correct_collection_photo(state, turn_input.photo_id):
            _record_correct_collection_pick(state, turn_input.photo_id)
            # Phase A -> Phase B: correct photo triggers detail-harvesting question
            logger.info("Phase transition: photo -> detail (correct photo %s)", turn_input.photo_id)
            state.collection_phase = "detail"
            state.detail_exchange_count = 0
        else:
            collection_wrong = True
            state.consecutive_wrong += 1

    # --- 5. Consecutive wrong picks exit (>= 2) ---
    if state.consecutive_wrong >= 2:
        state.current_step = EARLY_EXIT
        state.status = "exited"
        turn_response, gen_debug = await _generate_with_retry(script_agent, state)
        _append_ai_turn(state, turn_response.dialogue)
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type="graceful_exit",
            error_exit=state.status == "error",
            debug=_debug(gen_debug, turn_response),
        )

    # --- 6. Wrong pick retry (stay on step, generate "try again") ---
    if collection_wrong:
        _append_child_turn(state, f"[selected wrong photo: {turn_input.photo_id}]", include_round_number=False)
        turn_response, gen_debug = await _generate_with_retry(script_agent, state)
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type="wrong_photo",
            error_exit=state.status == "error",
            debug=_debug(gen_debug, turn_response),
        )

    return None


async def resolve_detail_phase(
    state: SessionStateModel,
    turn_input: TurnInput,
    script_agent: ScriptAgent,
    has_child_input: bool,
) -> TurnResult | None:
    """Handle Cat5 Phase B detail-harvesting exchange (section 7b½).

    Returns a TurnResult if the detail phase was active, or None if
    this turn does not match detail-phase conditions.
    """
    if not (
        state.current_step.startswith("STEP_3_COLLECT_")
        and state.collection_phase == "detail"
        and not turn_input.photo_id
        and has_child_input
    ):
        return None

    def _debug(gen_debug: GenerationDebugInfo | None, turn_response: TurnResponse | None = None) -> dict:
        return _build_debug_payload(state, gen_debug, script_agent, turn_response)

    # 7b½. Cat5 Phase B: child responds to detail-harvesting question
    state.detail_exchange_count += 1

    # Record the child's detail response
    child_text = turn_input.text if turn_input.text else "..."
    _record_collection_detail(state, child_text)

    # Generate AI response (processes detail, names character or acknowledges)
    turn_response, gen_debug = await _generate_with_retry(script_agent, state)

    _append_ai_turn(state, turn_response.dialogue)
    state.turn_count += 1
    _maybe_record_generated_name(state, turn_response.dialogue)

    response_type = _get_response_type(state.current_step)
    debug = _debug(gen_debug, turn_response)
    # Respect stay_on_step from the AI — the child may be confused or
    # off-topic and needs guidance back before advancing. Cap is
    # tier-dependent: T0=1, T1=2, T2=3 to reduce chatter for young children.
    max_exchanges = _MAX_DETAIL_EXCHANGES.get(state.tier, 3)
    if turn_response.stay_on_step and state.detail_exchange_count < max_exchanges:
        logger.info(
            "Phase B: child needs guidance (exchange %d/%d), staying in detail phase",
            state.detail_exchange_count,
            max_exchanges,
        )
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type=response_type,
            error_exit=state.status == "error",
            debug=debug,
        )

    # Detail phase complete — defer advance to next empty turn so the
    # naming / transition dialogue plays while the child still sees
    # the current detail screen.
    state.round_advance_pending = True
    state.detail_exchange_count = 0
    return TurnResult(
        turn_response=turn_response,
        screen_frame=_get_screen_frame(state),
        auto_advance=True,
        response_type=response_type,
        error_exit=state.status == "error",
        debug=debug,
    )
