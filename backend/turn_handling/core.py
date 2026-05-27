"""Core dispatcher for turn resolution.

The ``resolve_turn`` function is the single entry point called by both
``/api/turn`` and ``/api/turn-speak``.  It records input, classifies intent,
and dispatches to the appropriate step-specific handler module.
"""

try:
    from ..agents.script_agent import ScriptAgent
    from ..config import get_settings
    from ..logger import setup_logger
    from ..schemas.child_intent import ChildIntentClassification
    from ..schemas.session_state import SessionStateModel
    from ..state_machine import EARLY_EXIT, is_terminal, step_needs_user_input
except ImportError:
    from agents.script_agent import ScriptAgent
    from config import get_settings
    from logger import setup_logger
    from schemas.child_intent import ChildIntentClassification
    from schemas.session_state import SessionStateModel
    from state_machine import EARLY_EXIT, is_terminal, step_needs_user_input

from .collection import (
    _is_correct_collection_photo,
    _record_correct_collection_pick,
    record_text_collection_pick,
    resolve_collection_wrong_pick,
    resolve_detail_phase,
)
from .debug import _build_debug_payload
from .directive import _get_turn_directive, _resolve_turn_with_directive
from .generation import _classify_child_intent, _generate_with_retry
from .helpers import (
    _CONFIRM_WORDS,
    _DECLINE_WORDS,
    _advance_state,
    _already_prompted_on_step,
    _append_ai_turn,
    _append_child_turn,
    _ended_result,
    _get_response_type,
    _get_screen_frame,
    _is_closing_step,
    _should_auto_advance,
)
from .invitation import resolve_invitation
from .rounds import resolve_round
from .synthesis import _deliver_scene, _resolve_synthesis_turn
from .types import TurnInput, TurnResult

logger = setup_logger(__name__)


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

    def _debug(gen_debug, turn_response=None):
        """Build debug payload with state and script_agent already captured."""
        return _build_debug_payload(state, gen_debug, script_agent, turn_response)

    # Phase/state logging for debugging collection and synthesis flow
    if state.current_step.startswith("STEP_3_"):
        logger.info(
            "resolve_turn: step=%s phase=%s round=%d/%d photos=%s names=%s "
            "detail_count=%d pending=%s input=(text=%s photo=%s silent=%s)",
            state.current_step,
            state.collection_phase,
            state.current_round,
            state.total_rounds,
            [p[:20] for p in state.collected_photos],
            state.collected_names,
            state.detail_exchange_count,
            state.round_advance_pending,
            repr(turn_input.text[:30]) if turn_input.text else None,
            turn_input.photo_id,
            turn_input.is_silent,
        )
    elif state.current_step.startswith("STEP_4_") or state.current_step.startswith("STEP_5_"):
        logger.info(
            "resolve_turn: step=%s synthesis_phase=%s names=%s details=%s child_story=%s input=(text=%s silent=%s)",
            state.current_step,
            state.synthesis_phase,
            state.collected_names,
            state.collected_details,
            repr(state.synthesis_child_story[:40]) if state.synthesis_child_story else None,
            repr(turn_input.text[:30]) if turn_input.text else None,
            turn_input.is_silent,
        )

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

    # --- 3. Record child input in conversation history ---
    if turn_input.text or turn_input.is_silent:
        child_text = turn_input.text if turn_input.text else "..."
        _append_child_turn(state, child_text)

    if (
        state.interaction_mode == "text"
        and state.template_type == "cat5"
        and state.current_step.startswith("STEP_3_COLLECT_")
        and state.collection_phase == "photo"
        and turn_input.text
    ):
        record_text_collection_pick(state, turn_input.text)

    # --- 3a. Turn Director path (feature-flagged) ---
    settings = get_settings()
    if settings.turn_director_enabled:
        # Cat5 photo validation still runs in the directive path
        if turn_input.photo_id and state.current_step.startswith("STEP_3_COLLECT_"):
            if _is_correct_collection_photo(state, turn_input.photo_id):
                _record_correct_collection_pick(state, turn_input.photo_id)
                logger.info("Phase transition: photo -> detail (correct photo %s)", turn_input.photo_id)
                state.collection_phase = "detail"
                state.detail_exchange_count = 0
            else:
                state.consecutive_wrong += 1
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
                        debug=_build_debug_payload(state, gen_debug, script_agent, turn_response),
                    )

        # Round advance pending (Cat5 detail -> next photo round)
        if state.round_advance_pending:
            state.round_advance_pending = False
            state.collection_phase = "photo"
            _advance_state(state)
            if is_terminal(state.current_step):
                return _ended_result(state)

        # Scene delivery and generate phase bypass the Turn Director entirely
        if (
            state.current_step == "STEP_4_SYNTHESIS"
            and state.synthesis_phase.startswith("scene_")
            and state.structured_story
        ):
            scene_num = int(state.synthesis_phase.split("_")[1])
            return await _deliver_scene(state, scene_num)
        if state.current_step == "STEP_4_SYNTHESIS" and state.synthesis_phase == "generate":
            return await _resolve_synthesis_turn(state, turn_input, script_agent)

        directive = await _get_turn_directive(state, turn_input)
        return await _resolve_turn_with_directive(state, turn_input, script_agent, directive)

    # --- 3b. Classify child intent (runs before any step-specific logic) ---
    child_text_for_intent = turn_input.text or ""
    if child_text_for_intent and not turn_input.is_silent:
        # Code-level override: short common phrases bypass unreliable LLM classifier
        normalized = child_text_for_intent.strip().lower().rstrip("!.?")
        if normalized in _CONFIRM_WORDS:
            state.child_intent = "confirm"
            intent_result = ChildIntentClassification(intent="confirm")
            logger.info(
                "child_intent_classification: step=%s intent=confirm (code) text=%s", state.current_step, normalized
            )
        elif normalized in _DECLINE_WORDS:
            state.child_intent = "decline"
            intent_result = ChildIntentClassification(intent="decline")
            logger.info(
                "child_intent_classification: step=%s intent=decline (code) text=%s", state.current_step, normalized
            )
        else:
            intent_result = await _classify_child_intent(state, child_text_for_intent)
            state.child_intent = intent_result.intent
            logger.info(
                "child_intent_classification: step=%s intent=%s text=%s",
                state.current_step,
                intent_result.intent,
                child_text_for_intent[:80],
            )
    else:
        state.child_intent = ""
        intent_result = None

    # --- 4-6. Cat 5 collection: validate photo_id before step logic ---
    collection_result = await resolve_collection_wrong_pick(state, turn_input, script_agent)
    if collection_result is not None:
        return collection_result

    # Track whether a wrong pick happened (for rounds.py guardrail)
    collection_wrong = bool(
        turn_input.photo_id and state.current_step.startswith("STEP_3_COLLECT_") and state.collection_phase != "detail"
    )

    # --- 7. Step-specific logic ---

    # 7a. Invitation: route on pre-classified intent
    invitation_result = await resolve_invitation(state, turn_input, script_agent, has_child_input)
    if invitation_result is not None:
        return invitation_result

    # 7b½. Cat5 Phase B: child responds to detail-harvesting question
    detail_result = await resolve_detail_phase(state, turn_input, script_agent, has_child_input)
    if detail_result is not None:
        return detail_result

    # 7c. Round steps (STEP_3_ROUND_* / STEP_3_COLLECT_*)
    round_result = await resolve_round(
        state, turn_input, script_agent, has_child_input, collection_wrong=collection_wrong
    )
    if round_result is not None:
        return round_result

    # 7d. Non-round, non-invitation steps (synthesis, celebrate, closing)

    # 7d-i. STEP_4_SYNTHESIS: story synthesis loop with phase-based routing
    if state.current_step == "STEP_4_SYNTHESIS":
        return await _resolve_synthesis_turn(state, turn_input, script_agent, intent_result)

    # 7d-ii. Other interactive steps (STEP_1_HOOK): first visit or child response
    if step_needs_user_input(state.current_step) and not _already_prompted_on_step(state):
        turn_response, gen_debug = await _generate_with_retry(script_agent, state, is_first_on_step=True)
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

    if step_needs_user_input(state.current_step):
        if state.current_step == "STEP_1_HOOK":
            _advance_state(state)
            turn_response, gen_debug = await _generate_with_retry(script_agent, state, is_first_on_step=True)
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

        # Generic interactive step fallback
        turn_response, gen_debug = await _generate_with_retry(script_agent, state)
        if turn_response.stay_on_step:
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
            debug=_debug(gen_debug, turn_response),
        )

    # Auto-advance step (celebrate, closing): check if already generated
    if _already_prompted_on_step(state):
        # Already generated (e.g. Cat1 celebrate from round advance) — advance through
        _advance_state(state)
        if is_terminal(state.current_step):
            return _ended_result(state)
        turn_response, gen_debug = await _generate_with_retry(script_agent, state)
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
            debug=_debug(gen_debug, turn_response),
        )

    # Not yet generated (e.g. Cat5 celebrate after synthesis) — generate then advance
    turn_response, gen_debug = await _generate_with_retry(script_agent, state)
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
            debug=_debug(gen_debug, turn_response),
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
        debug=_debug(gen_debug, turn_response),
    )
