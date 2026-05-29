"""Pure-function helpers, predicates, constants, and response builders.

Extracted verbatim from turn_handler.py during package decomposition.
"""

import random

try:
    from ..image_gen import get_scene_session
    from ..logger import setup_logger
    from ..schemas import ScreenFrame
    from ..schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from ..schemas.session_state import ConversationTurn, SessionStateModel
    from ..schemas.turn_response import TurnResponse
    from ..state_machine import (
        EARLY_EXIT,
        get_screen_frame,
        next_step,
        step_needs_user_input,
    )
    from .types import TurnResult
except ImportError:
    from image_gen import get_scene_session
    from logger import setup_logger
    from schemas import ScreenFrame
    from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from schemas.session_state import ConversationTurn, SessionStateModel
    from schemas.turn_response import TurnResponse
    from state_machine import (
        EARLY_EXIT,
        get_screen_frame,
        next_step,
        step_needs_user_input,
    )

    from turn_handling.types import TurnResult

from .generation import get_retry_stats as _get_retry_stats

logger = setup_logger(__name__)


# ---------------------------------------------------------------------------
# Helper predicates
# ---------------------------------------------------------------------------


def _is_invitation_step(step: str) -> bool:
    """Return True for STEP_2 invitation steps (rules or mission briefing)."""
    return step in {"STEP_2_RULES", "STEP_2_MISSION", "STEP_2_SETUP"}


def _is_round_step(step: str) -> bool:
    """Return True for any STEP_3 round or collection step."""
    return step.startswith("STEP_3_ROUND_") or step.startswith("STEP_3_COLLECT_") or step.startswith("STEP_3_BUILD_")


def _is_closing_step(step: str) -> bool:
    """Return True when the active step is the final closing response."""
    return step in {"STEP_5_CLOSING", "STEP_6_CLOSING"}


def _already_prompted_on_step(state: SessionStateModel) -> bool:
    """Check if the AI already generated a response for the current step."""
    return any(t.step == state.current_step and t.role == "ai" for t in state.conversation_history)


def _is_celebrate_step(step: str) -> bool:
    return step in ("STEP_4_CELEBRATE", "STEP_5_CELEBRATE")


def _is_closing_step_directive(step: str) -> bool:
    """Alias for _is_closing_step — kept for backward compatibility."""
    return _is_closing_step(step)


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
    for prefix in ("STEP_3_ROUND_", "STEP_3_COLLECT_", "STEP_3_BUILD_"):
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
        "collection_phase": state.collection_phase,
        "collected_photos": state.collected_photos,
        "collected_text_items": state.collected_text_items,
        "collected_names": state.collected_names,
        "collected_details": state.collected_details,
        "structured_story": state.structured_story,
        "round_items": state.round_items,
    }


def _backfill_achievement_failure(state: SessionStateModel) -> None:
    """Re-check the live image session before rendering a Cat5 celebrate frame.

    The synthesis layer only awaits the achievement future once, with a 30 s
    timeout, on the last scene turn (``synthesis.py:561``). If the worker
    fails after that wait — for example when Imagen returns a sustained 429
    that exhausts the retry budget seconds later, or when a tester manually
    advances before the timeout completes — ``story.achievement_image_failed``
    stays False and the celebrate frame falls back to ``image_status='pending'``
    forever, hiding the failure banner. Re-checking the live session here
    closes that gap. Failure is permanent for a session, so we mutate the
    cached story in place.
    """
    if (
        state.template_type != "cat5"
        or state.current_step != "STEP_5_CELEBRATE"
        or state.structured_story is None
        or state.structured_story.achievement_image_failed
        or state.structured_story.achievement_image_data_url is not None
    ):
        return

    image_session = get_scene_session(state.session_id)
    if image_session is not None and image_session.achievement_failed:
        state.structured_story.achievement_image_failed = True


def _get_screen_frame(state: SessionStateModel) -> ScreenFrame:
    """Get screen frame for the current step."""
    _backfill_achievement_failure(state)
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
    if step in ("STEP_2_RULES", "STEP_2_MISSION", "STEP_2_SETUP"):
        return "rules"
    if step.startswith("STEP_3_ROUND_") or step.startswith("STEP_3_COLLECT_") or step.startswith("STEP_3_BUILD_"):
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
    retry_stats = _get_retry_stats()
    if retry_stats:
        logger.info("session_retry_stats: %s", retry_stats)
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


def _badge_screen_frame(state: SessionStateModel) -> ScreenFrame:
    """Return a badge_award ScreenFrame for celebrate/closing steps."""
    role_title = ""
    if isinstance(state.creative_slots, Cat1CreativeSlots):
        role_title = state.creative_slots.role_title
    elif isinstance(state.creative_slots, Cat5CreativeSlots):
        role_title = state.creative_slots.role_title
    concepts = state.ib_key_concepts or []
    return ScreenFrame(
        widget="badge_award",
        widget_params={"title": role_title, "concepts": concepts},
        animation="badge_reveal",
        trigger="on_correct",
        sfx_cue="badge_awarded",
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
# Constants used across modules
# ---------------------------------------------------------------------------

# Code-level intent detection — bypasses the LLM classifier for common phrases.
_CONFIRM_WORDS = frozenset(
    {
        "yes",
        "yeah",
        "yep",
        "yup",
        "sure",
        "ok",
        "okay",
        "ya",
        "uh huh",
        "go ahead",
        "go on",
        "tell me",
        "you tell me",
        "you do it",
        "what's next",
        "whats next",
        "what next",
        "then what",
        "and then",
        "keep going",
        "more",
        "your turn",
        "maybe",
        "yeah maybe",
        "i guess",
        "let me think",
        "hmm ok",
        "sounds fun",
        "sounds good",
        "good",
        "cool",
        "nice",
        "awesome",
        "let's do it",
        "lets do it",
        "i'm ready",
        "im ready",
        "yes please",
        "yay",
        "alright",
        "fine",
    }
)

_DECLINE_WORDS = frozenset(
    {
        "no",
        "nah",
        "nope",
        "no thanks",
        "no thank you",
        "i don't want to",
        "i dont want to",
        "stop",
        "quit",
        "i don't like it",
        "i dont like it",
        "no way",
        "not now",
        "maybe later",
    }
)

_MAX_DETAIL_EXCHANGES: dict[str, int] = {"T0": 1, "T1": 2, "T2": 3}

_ANGLE_ADJECTIVES: dict[str, list[str]] = {
    "texture": ["soft", "fuzzy", "fluffy", "smooth"],
    "color": ["colorful", "bright", "vivid"],
    "shape": ["round", "curvy", "pointy"],
    "size": ["tiny", "big", "little"],
    "pattern": ["spotty", "stripy", "dotty"],
    "form": ["wiggly", "bumpy", "spiky"],
    "movement": ["bouncy", "wiggly", "swaying"],
    "smell": ["sweet-smelling", "fragrant"],
    "function": ["useful", "special"],
    "habitat": ["cozy", "hidden"],
}

_PHOTO_FIND_PROMPTS = [
    "[curious] I wonder if something {adj} is waiting to be found?",
    "[encouraging] Your fingers might find something {adj}...",
    "[mysterious] Hmm, I bet there is something {adj} you have not spotted yet!",
    "[playful] Something {adj} might be hiding right where you are!",
    "[whispering] Shhh... can you find something {adj} nearby?",
]

_B_WORD_FIND_PROMPTS = [
    "[curious] Can you find a word or object that starts with B, the letter B?",
    "[encouraging] Look for one B word now, like something whose name starts with B.",
    "[playful] One B word treasure is ready to be found. What starts with B?",
]

_ACCEPTANCE_CELEBRATIONS = [
    "[celebrating] Yay! Our adventure begins!",
    "[celebrating] Woohoo! Let's explore together!",
    "[excited] Amazing! Here we go!",
    "[celebrating] Yes! Adventure time!",
]


def _collection_photo_prompt(state: SessionStateModel) -> TurnResponse:
    """Deterministic prompt for collection photo phase — no LLM needed."""
    if isinstance(state.creative_slots, Cat5CreativeSlots):
        criterion = state.creative_slots.collection_criterion.lower()
        if "letter b" in criterion or "start with b" in criterion or "starts with b" in criterion:
            dialogue = random.choice(_B_WORD_FIND_PROMPTS)
            tone = dialogue.split("]")[0].strip("[")
            return TurnResponse(
                dialogue=dialogue,
                tone_marker=tone,
                screen_widget="photo_display",
                screen_widget_params={},
                stay_on_step=True,
            )

    angle = state.creative_slots.observation_angle if isinstance(state.creative_slots, Cat5CreativeSlots) else "special"
    adjectives = _ANGLE_ADJECTIVES.get(angle, [angle])
    adj = random.choice(adjectives)
    dialogue = random.choice(_PHOTO_FIND_PROMPTS).format(adj=adj)
    tone = dialogue.split("]")[0].strip("[")
    return TurnResponse(
        dialogue=dialogue,
        tone_marker=tone,
        screen_widget="photo_display",
        screen_widget_params={},
        stay_on_step=True,
    )
