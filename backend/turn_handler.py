"""Unified turn resolution logic for both /api/turn and /api/turn-speak.

This module extracts the step transition logic that was previously duplicated
across the two turn endpoints, ensuring consistent behavior for invitation
acceptance, round advancement, auto-advance signaling, and history management.
"""

import json
import random
import re
import time
from dataclasses import asdict, dataclass

import httpx
from openai import AsyncOpenAI

try:
    from .agents.script_agent import ScriptAgent, ScriptAgentError
    from .agents.turn_director import TurnDirector
    from .config import get_settings
    from .logger import setup_logger
    from .schemas import ScreenFrame
    from .schemas.child_intent import ChildIntentClassification
    from .schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from .schemas.session_state import ConversationTurn, SessionStateModel
    from .schemas.turn_directive import StoryElement, TurnDirective
    from .schemas.turn_plan import TurnPlan
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
    from agents.turn_director import TurnDirector
    from config import get_settings
    from logger import setup_logger
    from schemas import ScreenFrame
    from schemas.child_intent import ChildIntentClassification
    from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from schemas.session_state import ConversationTurn, SessionStateModel
    from schemas.turn_directive import StoryElement, TurnDirective
    from schemas.turn_plan import TurnPlan
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
class GenerationDebugInfo:
    """Debug telemetry captured during a single _generate_with_retry call."""

    step: str
    attempt_count: int
    final_verdict: str  # "passed", "exhausted", "error_fallback"
    attempts: list[dict]  # [{attempt, verdict, hint, latency_ms, call_type}]


@dataclass
class TurnResult:
    """The resolved outcome of one turn, ready for the endpoint to serialize."""

    turn_response: TurnResponse
    screen_frame: ScreenFrame
    auto_advance: bool
    response_type: str
    error_exit: bool = False
    debug: dict | None = None


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
        "collection_phase": state.collection_phase,
        "collected_photos": state.collected_photos,
        "collected_names": state.collected_names,
        "collected_details": state.collected_details,
        "round_items": state.round_items,
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
    if _retry_stats:
        logger.info("session_retry_stats: %s", _retry_stats)
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


_GENERATED_NAME_PATTERNS = (
    re.compile('["“”]([^"“”]{1,40})["“”]'),
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


_SYNTHESIS_INVITE_TEMPLATES = [
    "[gentle] Would you like to make up a little story about {names}?",
    "[curious] What if {names} went on an adventure? Would you like to tell that story?",
    "[whispering] I wonder what {names} would do together... would you like to imagine?",
]

_MIN_STORY_SENTENCES: dict[str, int] = {"T0": 7, "T1": 9, "T2": 12}

# Short responses that are always "confirm" at synthesis — no LLM needed.
_SYNTHESIS_CONFIRM_WORDS = frozenset(
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
        "let's do it",
        "i'm ready",
        "yes please",
        "yay",
    }
)


def _is_synthesis_confirm(text: str) -> bool:
    """Check if text is a simple affirmative — no LLM needed for these."""
    normalized = text.strip().lower().rstrip("!.?")
    return normalized in _SYNTHESIS_CONFIRM_WORDS


def _synthesis_invite_prompt(state: SessionStateModel) -> TurnResponse:
    """Deterministic invitation to make a story — no LLM needed."""
    names = ", ".join(state.collected_names) if state.collected_names else "your collected friends"
    dialogue = random.choice(_SYNTHESIS_INVITE_TEMPLATES).format(names=names)
    tone = dialogue.split("]")[0].strip("[")
    return TurnResponse(
        dialogue=dialogue,
        tone_marker=tone,
        screen_widget="photo_grid",
        screen_widget_params={},
        stay_on_step=True,
    )


_ACCEPTANCE_CELEBRATIONS = [
    "[celebrating] Yay! Our adventure begins!",
    "[celebrating] Woohoo! Let's explore together!",
    "[excited] Amazing! Here we go!",
    "[celebrating] Yes! Adventure time!",
]


def _collection_photo_prompt(state: SessionStateModel) -> TurnResponse:
    """Deterministic prompt for collection photo phase — no LLM needed."""
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
# Post-processing response validation
# ---------------------------------------------------------------------------

_MODEL_PHRASES = [
    "i think",
    "i'd call",
    "maybe it's",
    "it looks like",
    "i think it looks",
    "should we call",
    "it reminds me of",
    "let me show",
    "see this",
    "see the",
    "look at this",
    "i think it would",
    "it sounds like",
]

_OPEN_QUESTION_STARTS = [
    "what does",
    "what do you",
    "what did",
    "what would",
    "what happens",
    "what kind",
    "how does",
    "how do you",
    "how did",
    "how would",
    "where does",
    "where do",
    "where did",
    "why does",
    "why do",
    "why did",
    "i wonder what",
    "i wonder how",
    "i wonder where",
    "i wonder why",
    "i wonder if",
]


def _ends_with_open_question(dialogue: str) -> bool:
    """Check if dialogue ends with an open-ended wh-question."""
    if "?" not in dialogue:
        return False
    # Find last sentence containing "?"
    sentences = re.split(r"[.!]\s+", dialogue)
    last_q = ""
    for s in reversed(sentences):
        if "?" in s:
            last_q = s.strip().lower()
            break
    if not last_q:
        return False
    return any(last_q.startswith(p) or f" {p}" in last_q for p in _OPEN_QUESTION_STARTS)


def _has_model_phrase(dialogue: str) -> bool:
    """Check if dialogue contains a model/scaffold phrase."""
    lower = dialogue.lower()
    return any(p in lower for p in _MODEL_PHRASES)


def _validate_response(
    state: SessionStateModel,
    turn_response: TurnResponse,
    is_first_on_step: bool,
) -> tuple[bool, str]:
    """Validate AI response against step-specific rules.

    Returns (True, "") if valid, or (False, corrective_hint) if invalid.
    """
    step = state.current_step
    dialogue = turn_response.dialogue
    tier = state.tier

    # 1. Hook: allow questions — forced exclamation-only hooks sound unnatural
    # (validation disabled for all tiers)

    # 2. Mission/Rules: demo validation removed — AI doesn't reliably produce demos
    #    despite repeated prompt strengthening. Kept the prompt instructions as aspirational
    #    but no longer reject responses that skip the demo.

    # 3. T0 collect detail: must scaffold (not open question)
    # Fires both when entering detail (is_first_on_step) and when already in detail phase
    if step.startswith("STEP_3_COLLECT_") and tier == "T0" and (state.collection_phase == "detail" or is_first_on_step):
        if _ends_with_open_question(dialogue) and not _has_model_phrase(dialogue):
            return False, (
                "CORRECTION: For T0 (ages 2-4), do NOT ask open questions like "
                "'What does this remind you of?' Instead, model your own idea first: "
                "'I think this looks like a cloud! What do you think?' or offer a choice."
            )

    # 4. T0 synthesis: must scaffold (only during story generation, not invite phase)
    if step == "STEP_4_SYNTHESIS" and tier == "T0" and state.synthesis_phase != "invite":
        if _ends_with_open_question(dialogue) and " or " not in dialogue.lower():
            return False, (
                "CORRECTION: For T0 (ages 2-4), do NOT ask open questions in synthesis. "
                "Offer a binary choice like 'Did Cloud Puff tickle them or give a hug?'"
            )

    # 5. T0 Cat1 round questions: must scaffold
    if step.startswith("STEP_3_ROUND_") and tier == "T0":
        if _ends_with_open_question(dialogue) and not _has_model_phrase(dialogue):
            return False, (
                "CORRECTION: For T0 (ages 2-4), do NOT ask open questions like "
                "'What does your dinosaur do?' Instead, model first and offer a choice: "
                "'I think it would say ROAR! Would it say ROAR or something different?'"
            )

    # 6. Collection steps: no specific item suggestions
    if step.startswith("STEP_3_COLLECT_") and _ITEM_SUGGESTION_RE.search(dialogue):
        return False, (
            "CORRECTION: Do NOT name specific objects to find (blanket, toy, pillow, etc.). "
            "You cannot see the child's environment. Say 'something soft' not 'a fuzzy blanket'."
        )

    # 7. Cat5 steps: no directive language (but invitational framing is OK)
    if state.template_type == "cat5":
        stripped = _INVITATIONAL_PREFIX_RE.sub("", dialogue)
        if _DIRECTIVE_RE.search(stripped):
            return False, (
                "CORRECTION: Do NOT use directive language ('Go find!', 'Look for!', 'Try peeking!'). "
                "Use invitational phrasing: 'Would you like to...?' or 'I wonder if...' instead."
            )

    return True, ""


# ---------------------------------------------------------------------------
# Plan-aware validation (two-pass diagnostics)
# ---------------------------------------------------------------------------

# Common household/outdoor items that indicate the speaker is suggesting specific
# things the child should go find — violates the do_not_suggest_items constraint.
_ITEM_SUGGESTION_RE = re.compile(
    r"(?i)\b(?:find|look for|grab|get|bring|search for|spot|touch|touching|try|feel|peek"
    r"|check|reach for)\b"
    r"[^.!?]{0,40}"
    r"\b(?:pillow|blanket|sock|shoe|cup|spoon|fork|plate|ball|book|toy|rock|leaf|stick"
    r"|flower|shell|stone|button|coin|bottle|box|bag|hat|glove|scarf|key|pen|pencil"
    r"|crayon|block|ring|wheel|clock|bowl|jar|lid|pan|pot|ribbon|string|bead|marble"
    r"|rug|carpet|towel|cloth|cushion|teddy|doll|stuffed|berry|berries|petal|petals"
    r"|grass|furniture|acorn|pinecone|mushroom|feather|twig|bark|seed|moss)\b"
)

# Directive language patterns that command the child to take action.
# Invitational alternatives ("Would you like to...?", "I wonder...") are OK.
_DIRECTIVE_RE = re.compile(
    r"(?i)\b(?:try\s+\w+ing|scan\s+the|check\s+the|go\s+find|go\s+look"
    r"|look\s+for|search\s+for|now\s+let'?s|let'?s\s+go)\b"
)

# Invitational prefix + following verb phrase. The pattern consumes everything
# through the directive verb so the remaining text no longer triggers _DIRECTIVE_RE.
# e.g. "Would you like to look for" → removed; bare "Look for" → kept.
_INVITATIONAL_PREFIX_RE = re.compile(
    r"(?i)\b(?:would you like to|do you want to|shall we|how about we"
    r"|i wonder if (?:you|we) (?:could|should|can|might))\s+"
    r"(?:try\s+\w+ing|scan\s+the|check\s+the|go\s+find|go\s+look"
    r"|look\s+for|search\s+for)"
)


def _validate_plan(
    state: SessionStateModel,
    plan: TurnPlan,
    dialogue: str,
) -> str:
    """Validate the TurnPlan and compare it against the speaker's dialogue.

    Returns a diagnostic label:
    - "valid" — no plan-level issues detected
    - "speaker_violation" — plan constraints were correct but the speaker ignored them
    - "planner_failure" — the plan itself has issues that need a full retry

    Args:
        state: Current session state.
        plan: The TurnPlan from the planner pass.
        dialogue: The dialogue string from the speaker's TurnResponse.
    """
    # Check 1: do_not_suggest_items is true but dialogue names specific findable items
    if plan.do_not_suggest_items and _ITEM_SUGGESTION_RE.search(dialogue):
        logger.warning(
            "plan_validation: speaker_violation — do_not_suggest_items=true but dialogue suggests items: %s",
            dialogue[:120],
        )
        return "speaker_violation"

    # Check 2: correct-photo collection step should have a sensory_observation in the plan
    if (
        state.current_step.startswith("STEP_3_COLLECT_")
        and state.collection_phase == "detail"
        and not plan.sensory_observation
    ):
        logger.warning(
            "plan_validation: planner_failure — empty sensory_observation for detail phase on %s",
            state.current_step,
        )
        return "planner_failure"

    return "valid"


def _plan_retry_hint(plan_verdict: str) -> str:
    """Return a corrective hint for a failed plan-aware validation verdict."""
    hints = {
        "speaker_violation": (
            "CORRECTION: Keep the existing plan, but do NOT suggest specific items for the child to find. "
            "Use only generic next-step language."
        ),
        "planner_failure": (
            "CORRECTION: Re-plan this detail turn with a concrete sensory observation about the item the child "
            "already picked before writing the dialogue."
        ),
    }
    return hints.get(plan_verdict, "CORRECTION: Follow the plan more closely.")


# ---------------------------------------------------------------------------
# Unified child intent classifier
# ---------------------------------------------------------------------------


async def _classify_child_intent(state: SessionStateModel, child_text: str) -> ChildIntentClassification:
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
        f'- "confirm": agreeing, affirming, wanting to continue, asking the AI to proceed, '
        f"or any non-refusal response that doesn't provide new content. Includes hedging or "
        f'tentative agreement ("yes", "sure", "ok", "maybe", "yeah maybe", "I guess", '
        f'"what\'s next", "go ahead", "tell me", "sounds fun", "yay!", "let\'s do it", '
        f'"I\'m ready", "let me think", "hmm ok")\n'
        f'- "decline": explicitly refusing or saying no ("no", "I don\'t want to", "nah", "stop")\n'
        f'- "substantive": providing real content — a name, answer, description, detail, or story. '
        f"Must contain actual information or a creative contribution, not just agreement.\n"
        f'- "off_topic": unrelated to the current activity\n'
    )

    if is_synthesis:
        prompt += (
            f'\nIf intent is "substantive", also evaluate the story:\n'
            f'- story_quality: "good" if it has 2+ story elements (character + action, or '
            f"action + outcome) relating to these characters: {collected}. "
            f'"weak" if it\'s a single sentence with no progression.\n'
            f"- is_related_to_collection: true if the response mentions or relates to: {collected}\n\n"
            f'Output JSON: {{"intent": "...", "story_quality": "good|weak|null", '
            f'"is_related_to_collection": true/false}}'
        )
    else:
        prompt += '\nOutput JSON: {"intent": "..."}'

    try:
        settings = get_settings()
        client = AsyncOpenAI(
            api_key=settings.ali_api_key,
            base_url=settings.ali_base_url,
            max_retries=0,
            timeout=httpx.Timeout(10.0, connect=3.0),
        )
        response = await client.chat.completions.create(
            model=settings.ali_classifier_model,
            messages=[
                {"role": "system", "content": "Classify a child's response. Output valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=100,
            response_format={"type": "json_object"},
            extra_body={"enable_thinking": False},
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


# ---------------------------------------------------------------------------
# LLM generation with retry + validation
# ---------------------------------------------------------------------------

_MAX_GENERATION_ATTEMPTS = 3
_MAX_DETAIL_EXCHANGES: dict[str, int] = {"T0": 1, "T1": 2, "T2": 3}

# Per-step retry stats for measuring prompt quality improvements.
# Key: step name → {total, first_pass, retried, exhausted}
_retry_stats: dict[str, dict[str, int]] = {}


def _record_retry_stat(step: str, *, first_pass: bool = False, retried: bool = False, exhausted: bool = False) -> None:
    """Record a generation attempt outcome for the given step."""
    if step not in _retry_stats:
        _retry_stats[step] = {"total": 0, "first_pass": 0, "retried": 0, "exhausted": 0}
    stats = _retry_stats[step]
    stats["total"] += 1
    if first_pass:
        stats["first_pass"] += 1
    if retried:
        stats["retried"] += 1
    if exhausted:
        stats["exhausted"] += 1


def get_retry_stats() -> dict[str, dict[str, int]]:
    """Return a copy of the current retry stats for logging/API consumption."""
    return dict(_retry_stats)


async def _generate_with_retry(
    script_agent: ScriptAgent,
    state: SessionStateModel,
    is_first_on_step: bool = False,
) -> tuple[TurnResponse, GenerationDebugInfo]:
    """Generate a turn response with validation and retry.

    Attempts up to _MAX_GENERATION_ATTEMPTS times. After each generation,
    runs plan-aware validation (if a TurnPlan is available) followed by
    post-processing validation. If validation fails, appends a corrective
    hint and retries. The hint is removed from history after retry.

    Returns:
        A tuple of (TurnResponse, GenerationDebugInfo) capturing the response
        and diagnostic telemetry about the generation process.
    """
    last_response: TurnResponse | None = None
    retry_plan: TurnPlan | None = None
    attempts_log: list[dict] = []

    def _log_attempt(verdict: str, hint: str, latency_ms: int, call_type: str) -> None:
        attempts_log.append(
            {
                "attempt": len(attempts_log) + 1,
                "verdict": verdict,
                "hint": hint,
                "latency_ms": latency_ms,
                "call_type": call_type,
            }
        )

    def _make_debug(final_verdict: str) -> GenerationDebugInfo:
        return GenerationDebugInfo(
            step=state.current_step,
            attempt_count=len(attempts_log),
            final_verdict=final_verdict,
            attempts=attempts_log,
        )

    for attempt in range(_MAX_GENERATION_ATTEMPTS):
        attempt_start = time.perf_counter()
        call_type = "speaker_retry" if retry_plan is not None else "planner_speaker"
        try:
            if retry_plan is not None:
                response = await script_agent.retry_speaker_turn(
                    state,
                    retry_plan,
                    corrective_hint=_plan_retry_hint("speaker_violation"),
                )
                plan = retry_plan
            else:
                response = await script_agent.generate_turn(state)
                plan = script_agent.last_plan
        except ScriptAgentError:
            attempt_ms = int((time.perf_counter() - attempt_start) * 1000)
            logger.warning(f"Script Agent failed for step {state.current_step} (attempt {attempt + 1})")
            _log_attempt("error", "ScriptAgentError", attempt_ms, call_type)
            if attempt < _MAX_GENERATION_ATTEMPTS - 1:
                continue
            # Final attempt failed — use fallback
            logger.error(f"Script Agent failed {_MAX_GENERATION_ATTEMPTS} times, using fallback")
            state.status = "error"
            fallback_response = TurnResponse(
                dialogue="[gentle] That was so much fun! Would you like to play again next time? See you soon!",
                tone_marker="gentle",
                screen_widget="badge_award",
                screen_widget_params={"title": "Great job!", "concepts": [], "entity": state.entity_name},
                screen_animation="badge_reveal",
                sfx_cue="badge_awarded",
            )
            return fallback_response, _make_debug("error_fallback")

        attempt_ms = int((time.perf_counter() - attempt_start) * 1000)
        last_response = response

        # Plan-aware validation: diagnose planner vs speaker issues
        plan_hint = ""
        if plan is not None:
            plan_verdict = _validate_plan(state, plan, response.dialogue)
            if plan_verdict != "valid":
                logger.info(
                    "plan_validation: step=%s attempt=%d verdict=%s plan=%s",
                    state.current_step,
                    attempt + 1,
                    plan_verdict,
                    plan.model_dump_json(indent=None),
                )
                plan_hint = _plan_retry_hint(plan_verdict)
                if plan_verdict == "speaker_violation":
                    retry_plan = plan
                else:
                    retry_plan = None
        else:
            retry_plan = None

        is_valid, hint = True, ""  # _validate_response disabled
        if plan_hint:
            is_valid = False
            hint = plan_hint

        if is_valid:
            # Clean up any corrective hints from previous attempts
            state.conversation_history = [t for t in state.conversation_history if not t.text.startswith("CORRECTION:")]
            is_first = attempt == 0
            _record_retry_stat(state.current_step, first_pass=is_first, retried=not is_first)
            logger.info(
                "script_generation: step=%s attempts=%d tier=%s validation=passed",
                state.current_step,
                attempt + 1,
                state.tier,
            )
            _log_attempt("passed", "", attempt_ms, call_type)
            return response, _make_debug("passed")

        # Log both the plan and response on validation failure for diagnostics
        _log_attempt("failed", hint, attempt_ms, call_type)
        if plan is not None:
            logger.info(
                "validation_failure_with_plan: step=%s attempt=%d hint=%s plan=%s response_dialogue=%s",
                state.current_step,
                attempt + 1,
                hint[:80],
                plan.model_dump_json(indent=None),
                response.dialogue[:120],
            )
        else:
            logger.info(f"Validation failed for step {state.current_step} (attempt {attempt + 1}): {hint[:80]}")

        if attempt < _MAX_GENERATION_ATTEMPTS - 1:
            if retry_plan is None:
                # Append corrective hint as a system-like message in conversation history
                state.conversation_history.append(
                    ConversationTurn(
                        role="child",
                        text=hint,
                        step=state.current_step,
                    )
                )

    # All attempts failed validation — return the last response anyway
    _record_retry_stat(state.current_step, exhausted=True)
    logger.warning(
        "script_generation: step=%s attempts=%d tier=%s validation=exhausted",
        state.current_step,
        _MAX_GENERATION_ATTEMPTS,
        state.tier,
    )
    # Clean up any corrective hints from history
    state.conversation_history = [t for t in state.conversation_history if not t.text.startswith("CORRECTION:")]
    return last_response, _make_debug("exhausted")  # type: ignore[return-value]


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
# Debug payload helpers
# ---------------------------------------------------------------------------


def _build_step_flow(state: SessionStateModel) -> list[dict]:
    """Build the ordered step flow for the current session, marking each step's status."""
    if state.template_type == "cat1":
        steps = ["STEP_1_HOOK", "STEP_2_RULES"]
        steps += [f"STEP_3_ROUND_{i}" for i in range(1, state.total_rounds + 1)]
        steps += ["STEP_4_CELEBRATE", "STEP_5_CLOSING"]
    else:
        steps = ["STEP_1_HOOK", "STEP_2_MISSION"]
        steps += [f"STEP_3_COLLECT_{i}" for i in range(1, state.total_rounds + 1)]
        steps += ["STEP_4_SYNTHESIS", "STEP_5_CELEBRATE", "STEP_6_CLOSING"]

    # Terminal states: mark all steps done and append the terminal marker
    if state.current_step in (EARLY_EXIT, "ENDED"):
        flow = [{"step": s, "status": "done"} for s in steps]
        flow.append({"step": state.current_step, "status": "current"})
        return flow

    flow: list[dict] = []
    found_current = False
    for s in steps:
        if s == state.current_step:
            flow.append({"step": s, "status": "current"})
            found_current = True
        elif not found_current:
            flow.append({"step": s, "status": "done"})
        else:
            flow.append({"step": s, "status": "pending"})
    return flow


def _build_phase_timeline(state: SessionStateModel) -> list[dict] | None:
    """Build a sub-step phase timeline for steps with internal state machines."""
    step = state.current_step

    if state.template_type == "cat5" and step.startswith("STEP_3_COLLECT"):
        return _phase_timeline_cat5_collection(state)

    if state.template_type == "cat5" and step == "STEP_4_SYNTHESIS":
        return _phase_timeline_cat5_synthesis(state)

    if state.template_type == "cat1" and step == "STEP_2_RULES":
        return _phase_timeline_cat1_invitation(state)

    return None


def _phase_timeline_cat5_collection(state: SessionStateModel) -> list[dict]:
    """Phase timeline for Cat5 collection loop: photo -> detail(1..max)."""
    max_detail = _MAX_DETAIL_EXCHANGES.get(state.tier, 3)
    in_detail = state.collection_phase == "detail"
    exchange = state.detail_exchange_count
    # cursor = how many detail slots are complete (0 when still on photo)
    cursor = exchange + (1 if state.round_advance_pending else 0) if in_detail else -1

    timeline: list[dict] = [
        {"phase": "photo", "status": "done" if in_detail else "current", "label": "Photo", "meta": None}
    ]

    for i in range(1, max_detail + 1):
        status = "done" if i <= cursor else ("current" if i == cursor + 1 and in_detail else "pending")
        meta = {"round_advance_pending": state.round_advance_pending} if i == max_detail else None
        timeline.append({"phase": "detail", "status": status, "label": f"Detail {i}/{max_detail}", "meta": meta})

    return timeline


def _phase_timeline_cat5_synthesis(state: SessionStateModel) -> list[dict]:
    """Phase timeline for Cat5 synthesis loop: invite -> evaluate -> improve? -> generate."""
    ordered = ["invite", "evaluate"]
    if state.tier in ("T1", "T2"):
        ordered.append("improve")
    ordered.append("generate")

    current_idx = ordered.index(state.synthesis_phase) if state.synthesis_phase in ordered else 0

    timeline: list[dict] = []
    for i, phase in enumerate(ordered):
        status = "done" if i < current_idx else ("current" if i == current_idx else "pending")

        meta: dict | None = None
        if i == current_idx and phase != "invite":
            meta = {"prompt_count": state.synthesis_prompt_count}
            if phase in ("evaluate", "improve") and state.synthesis_story_quality:
                meta["story_quality"] = state.synthesis_story_quality

        timeline.append({"phase": phase, "status": status, "label": phase.capitalize(), "meta": meta})

    return timeline


def _phase_timeline_cat1_invitation(state: SessionStateModel) -> list[dict]:
    """Phase timeline for Cat1 invitation: invite -> decline 1 -> decline 2."""
    if state.invitation_accepted:
        return [{"phase": "invite", "status": "done", "label": "Invite", "meta": {"accepted": True}}]

    declines = state.invitation_decline_count
    timeline: list[dict] = [
        {"phase": "invite", "status": "current" if declines == 0 else "done", "label": "Invite", "meta": None}
    ]
    for i in range(1, declines + 1):
        timeline.append(
            {
                "phase": "decline",
                "status": "current" if i == declines else "done",
                "label": f"Decline {i}",
                "meta": None,
            }
        )
    return timeline


def _build_debug_payload(
    state: SessionStateModel,
    gen_debug: GenerationDebugInfo | None,
    script_agent: ScriptAgent,
    turn_response: TurnResponse | None = None,
) -> dict:
    """Assemble the debug payload dict for a turn response."""
    debug: dict = {}

    if gen_debug:
        debug["generation"] = asdict(gen_debug)

    plan = script_agent.last_plan
    if plan:
        debug["planner"] = {
            "do_not_suggest_items": plan.do_not_suggest_items,
            "offer_binary_choice": plan.offer_binary_choice,
            "must_model_first": plan.must_model_first,
            "do_not_ask_question": plan.do_not_ask_question,
            "emotion_tag": plan.emotion_tag,
            "question_type": plan.question_type,
        }

    if turn_response:
        debug["llm_output"] = {
            "tone_marker": turn_response.tone_marker,
            "stay_on_step": turn_response.stay_on_step,
            "screen_widget": turn_response.screen_widget,
            "sfx_cue": turn_response.sfx_cue,
        }

    # Synthesis loop counters (only when in or past synthesis)
    if state.synthesis_prompt_count > 0 or state.current_step == "STEP_4_SYNTHESIS":
        debug["synthesis"] = {
            "phase": state.synthesis_phase,
            "prompt_count": state.synthesis_prompt_count,
            "story_attempts": state.synthesis_story_attempts,
            "declines": state.synthesis_declines,
            "silences": state.synthesis_silences,
            "unrelated": state.synthesis_unrelated,
            "child_story": state.synthesis_child_story[:100] if state.synthesis_child_story else None,
        }

    if script_agent.last_best_of_n:
        debug["best_of_n"] = script_agent.last_best_of_n

    debug["retry_stats"] = get_retry_stats()
    debug["step_flow"] = _build_step_flow(state)

    timeline = _build_phase_timeline(state)
    if timeline:
        debug["phase_timeline"] = timeline

    return debug


# ---------------------------------------------------------------------------
# Story synthesis loop
# ---------------------------------------------------------------------------


def _synthesis_result(
    state: SessionStateModel,
    turn_response: TurnResponse,
    *,
    advance: bool = False,
    debug: dict | None = None,
) -> TurnResult:
    """Build a TurnResult for synthesis, optionally advancing to the next step."""
    response_type = _get_response_type(state.current_step)
    screen_frame = _get_screen_frame(state)
    _append_ai_turn(state, turn_response.dialogue)
    state.turn_count += 1
    if advance:
        _advance_state(state)
    auto_advance = advance and not is_terminal(state.current_step) and not step_needs_user_input(state.current_step)
    if is_terminal(state.current_step):
        state.status = "completed"
    return TurnResult(
        turn_response=turn_response,
        screen_frame=screen_frame,
        auto_advance=auto_advance,
        response_type=response_type,
        error_exit=state.status == "error",
        debug=debug,
    )


async def _resolve_synthesis_turn(
    state: SessionStateModel,
    turn_input: TurnInput,
    script_agent: ScriptAgent,
    intent_result: ChildIntentClassification | None = None,
) -> TurnResult:
    """Handle STEP_4_SYNTHESIS using phase-based story synthesis loop.

    Phases:
        invite   — Ask child to make up a story about collected characters.
        evaluate — Classify child's response and route accordingly.
        improve  — (T1/T2 only) Ask child to elaborate on weak story.
        generate — AI generates a complete story.

    Args:
        state: Mutable session state.
        turn_input: The child's input for this turn.
        script_agent: ScriptAgent instance for LLM generation.
        intent_result: Pre-classified child intent from resolve_turn (None if silent/empty).

    Returns:
        TurnResult with response and advancement signals.
    """

    def _debug(gen_debug: GenerationDebugInfo | None, turn_response: TurnResponse | None = None) -> dict:
        return _build_debug_payload(state, gen_debug, script_agent, turn_response)

    phase = state.synthesis_phase
    child_text = turn_input.text or ""

    # --- INVITE phase: deterministic template, no LLM ---
    if phase == "invite":
        turn_response = _synthesis_invite_prompt(state)
        state.synthesis_phase = "evaluate"
        state.synthesis_prompt_count += 1
        return _synthesis_result(
            state,
            turn_response,
            advance=False,
            debug=None,
        )

    # Shared helper: generate a story and advance past synthesis.
    # Enforces minimum sentence count — retries once if too short.
    async def _generate_and_advance() -> TurnResult:
        state.synthesis_phase = "generate"
        turn_response, gen_debug = await _generate_with_retry(script_agent, state)

        # Story length enforcement: count sentences, retry if too short.
        min_sentences = _MIN_STORY_SENTENCES.get(state.tier, 6)
        sentences = [s.strip() for s in re.split(r"[.!?]+", turn_response.dialogue) if s.strip()]
        if len(sentences) < min_sentences:
            logger.warning(
                "Story too short (%d sentences, need %d), regenerating with length hint",
                len(sentences),
                min_sentences,
            )
            hint_text = (
                f"[system: The story is too short. Generate a complete story with at least {min_sentences} sentences.]"
            )
            hint = ConversationTurn(
                role="child",
                text=hint_text,
                step=state.current_step,
            )
            state.conversation_history.append(hint)
            turn_response, gen_debug = await _generate_with_retry(script_agent, state)
            state.conversation_history = [t for t in state.conversation_history if t != hint]

        return _synthesis_result(state, turn_response, advance=True, debug=_debug(gen_debug, turn_response))

    # --- EVALUATE phase: use pre-classified intent ---
    if phase == "evaluate":
        # Code-level confirm override: short affirmatives bypass the LLM classifier
        # entirely. The LLM classifier sometimes misclassifies "yes" as "substantive".
        if child_text and _is_synthesis_confirm(child_text):
            state.child_intent = "confirm"
            logger.info("synthesis_classification: code-level confirm override for: %s", child_text[:40])

        # Silence / confirm / decline all skip straight to AI story generation
        if turn_input.is_silent or state.child_intent in ("confirm", "decline"):
            reason = "silence" if turn_input.is_silent else state.child_intent
            logger.info("synthesis_classification: %s — AI generates full story", reason)
            if turn_input.is_silent:
                state.synthesis_silences += 1
            elif state.child_intent == "decline":
                state.synthesis_declines += 1
            return await _generate_and_advance()

        if state.child_intent == "off_topic":
            state.synthesis_unrelated += 1
            if state.synthesis_prompt_count < 2:
                state.synthesis_prompt_count += 1
                turn_response, gen_debug = await _generate_with_retry(script_agent, state, is_first_on_step=True)
                return _synthesis_result(state, turn_response, advance=False, debug=_debug(gen_debug, turn_response))
            return await _generate_and_advance()

        # substantive — child provided story content
        child_text = turn_input.text or ""
        state.synthesis_child_story = child_text
        state.synthesis_story_attempts += 1
        state.synthesis_story_quality = intent_result.story_quality or "" if intent_result else ""

        if intent_result and intent_result.story_quality == "good":
            turn_response, gen_debug = await _generate_with_retry(script_agent, state)
            return _synthesis_result(state, turn_response, advance=True, debug=_debug(gen_debug, turn_response))

        if state.tier == "T0":
            return await _generate_and_advance()

        # T1/T2: weak story → improve phase
        state.synthesis_phase = "improve"
        turn_response, gen_debug = await _generate_with_retry(script_agent, state)
        return _synthesis_result(state, turn_response, advance=False, debug=_debug(gen_debug, turn_response))

    # --- IMPROVE phase: child's elaboration arrived ---
    if phase == "improve":
        if turn_input.is_silent:
            logger.info("synthesis_improve: silence detected — AI generating from child's seed")
            state.synthesis_silences += 1
            return await _generate_and_advance()

        combined_story = f"{state.synthesis_child_story} {child_text}".strip()
        classification = await _classify_child_intent(state, combined_story)
        logger.info(
            "synthesis_improve_classification: quality=%s combined=%s",
            classification.story_quality,
            combined_story[:100],
        )
        state.synthesis_story_quality = classification.story_quality or ""

        if classification.story_quality == "good":
            turn_response, gen_debug = await _generate_with_retry(script_agent, state)
            return _synthesis_result(state, turn_response, advance=True, debug=_debug(gen_debug, turn_response))

        # Still weak — AI completes the story from child's seed
        state.synthesis_child_story = combined_story
        return await _generate_and_advance()

    # --- GENERATE phase: direct generation fallback ---
    # Shouldn't normally reach here (generate is handled inline above),
    # but acts as a safety net.
    turn_response, gen_debug = await _generate_with_retry(script_agent, state)
    return _synthesis_result(state, turn_response, advance=True, debug=_debug(gen_debug, turn_response))


# ---------------------------------------------------------------------------
# Turn Director path (feature-flagged)
# ---------------------------------------------------------------------------

_turn_director = TurnDirector()


def _build_story_direction(state: SessionStateModel, chosen_theme: str = "") -> tuple[str, int]:
    """Build a rich synthesis direction from harvested story elements.

    The direction varies by synthesis_format:
    - collaborative_story: Tell a complete story with named characters
    - comparison_reveal: Guide comparison across observations
    - sorting_challenge: Guide sorting by criterion

    Args:
        state: Session state with story elements and scaffold.
        chosen_theme: Theme chosen by the child (or empty for random).

    Returns:
        (direction_text, max_sentences).
    """
    scaffold = None
    if isinstance(state.creative_slots, Cat5CreativeSlots) and state.creative_slots.story_scaffold:
        scaffold = state.creative_slots.story_scaffold

    synthesis_format = scaffold.synthesis_format if scaffold else "collaborative_story"

    # Use child's chosen theme, or fall back to random from scaffold
    theme = chosen_theme
    if not theme and scaffold and scaffold.story_themes:
        theme = random.choice(scaffold.story_themes)

    tier_sentences = {"T0": "4-6", "T1": "6-10", "T2": "8-14"}
    max_s = {"T0": 8, "T1": 11, "T2": 14}.get(state.tier, 11)

    if synthesis_format == "collaborative_story":
        # Named characters → story
        elems = state.story_elements
        if elems:
            parts = []
            for e in elems:
                name = e.character_name or f"Friend {e.round_number}"
                trait = e.trait_or_detail or "soft"
                parts.append(f"{name} ({trait})")
            chars_desc = ", ".join(parts)
        else:
            chars_desc = ", ".join(state.collected_names) if state.collected_names else "the collected friends"

        direction = (
            f"Tell a COMPLETE story about {chars_desc}. "
            f"The story must have:\n"
            f"- BEGINNING: Set the scene. The characters are together and something happens"
        )
        if theme:
            direction += f" ({theme})"
        direction += (
            ".\n"
            "- MIDDLE: Each character uses their special trait to help. "
            "Show what each one DOES, not just what they are.\n"
            "- END: The problem is solved and the friends celebrate together.\n\n"
        )
        if scaffold:
            direction += f"Premise: {scaffold.premise}. Goal: {scaffold.synthesis_goal}.\n"
        if state.synthesis_child_story:
            direction += (
                f'\nThe child tried to tell a story: "{state.synthesis_child_story}". '
                f"Weave their idea into the story — honor what they said and expand it.\n"
            )
        direction += (
            f"Length: {tier_sentences.get(state.tier, '6-10')} sentences. "
            f"Do NOT end with a question. End the story with a warm conclusion."
        )

    else:
        # comparison_reveal or sorting_challenge → comparison/sorting synthesis
        elems = state.story_elements
        obs_list = ""
        if elems:
            parts = []
            for i, e in enumerate(elems, 1):
                detail = e.trait_or_detail or e.child_words or f"find {i}"
                parts.append(f"Find {i}: {detail}")
            obs_list = "; ".join(parts)
        else:
            obs_list = "; ".join(state.collected_details) if state.collected_details else "the collected finds"

        obs_angle = ""
        sorting_criterion = ""
        if isinstance(state.creative_slots, Cat5CreativeSlots):
            obs_angle = state.creative_slots.observation_angle
            sorting_criterion = state.creative_slots.sorting_criterion

        direction = (
            f"Guide a fun comparison of all the finds. "
            f"Observations collected: {obs_list}.\n"
            f"Help the child see how the same thing ({obs_angle}) looks DIFFERENT on each item. "
        )
        if theme:
            direction += f"Use this angle: {theme}. "
        if sorting_criterion:
            direction += f"Sort by: {sorting_criterion}. "
        if scaffold:
            direction += f"\nGoal: {scaffold.synthesis_goal}. "
        direction += (
            f"\nThen invite the child to give each find a fun creative name "
            f"(e.g. 'Freckle Stone', 'Polka Petal'). "
            f"Length: {tier_sentences.get(state.tier, '6-10')} sentences. "
            f"End warmly — do NOT end with a question."
        )
        max_s = {"T0": 6, "T1": 8, "T2": 11}.get(state.tier, 8)

    return direction, max_s


def _fast_path_directive(normalized_text: str, state: SessionStateModel) -> TurnDirective | None:
    """Map common short phrases to TurnDirective without an LLM call.

    Context-dependent: "yes" means different things at different steps.
    Returns None when LLM classification is needed.
    """
    if normalized_text in _DECLINE_WORDS:
        if _is_invitation_step(state.current_step):
            count = state.invitation_decline_count + 1
            if count >= 2:
                return TurnDirective(
                    action="exit",
                    reasoning="Child declined the invitation twice.",
                    response_direction="Gentle goodbye, no pressure to continue.",
                    emotion_tag="gentle",
                    sfx_cue="session_end_chime",
                )
            return TurnDirective(
                action="stay",
                reasoning="Child declined once. Re-invite with different framing.",
                response_direction="Re-invite warmly with a different approach. Don't repeat the same invitation.",
                emotion_tag="warm",
                stay_on_step=True,
            )
        if state.current_step == "STEP_4_SYNTHESIS":
            story_dir, max_s = _build_story_direction(state)
            return TurnDirective(
                action="advance",
                reasoning="Child declined to make a story. AI generates the full story.",
                response_direction=story_dir,
                emotion_tag="playful",
                max_sentences=max_s,
            )
        # During collection: decline is unusual, let LLM handle
        return None

    if normalized_text in _CONFIRM_WORDS:
        if _is_invitation_step(state.current_step):
            # Build context-aware direction for the NEXT step
            if isinstance(state.creative_slots, Cat5CreativeSlots):
                angle = state.creative_slots.observation_angle
                criterion = state.creative_slots.collection_criterion
                direction = (
                    f"Celebrate acceptance briefly, then invite the child to go find their first "
                    f"{angle} item. Encourage them to explore and find something that matches: "
                    f"{criterion}. Do NOT talk about the original photo."
                )
            elif isinstance(state.creative_slots, Cat1CreativeSlots):
                # Use the instruction recipe's rich scenario text when available
                scenario = ""
                if state.instruction_recipe:
                    rounds = state.instruction_recipe.step_instructions.rounds
                    if rounds:
                        scenario = rounds[0].scenario
                if not scenario and state.creative_slots.round_scenarios:
                    scenario = state.creative_slots.round_scenarios[0]
                if state.creative_slots.game_mechanic == "storytelling_chain":
                    question_guidance = (
                        f"Ask ONE question about what the {state.entity_name} "
                        f"sees, finds, or does in the scene — NOT about how it feels."
                    )
                else:
                    question_guidance = f"Ask ONE question about how the {state.entity_name} feels or reacts."
                direction = (
                    f"Celebrate acceptance briefly. This is a verbal/imagination game — the child "
                    f'stays with the photo on screen. Present the first scenario: "{scenario}". '
                    f"{question_guidance}"
                )
            else:
                direction = "Celebrate acceptance and introduce the first round of the activity."
            return TurnDirective(
                action="advance",
                reasoning="Child accepted the invitation.",
                response_direction=direction,
                emotion_tag="celebrating",
                max_sentences=3,
            )
        if state.current_step == "STEP_4_SYNTHESIS":
            names = ", ".join(state.collected_names) if state.collected_names else "our friends"
            scaffold = None
            if isinstance(state.creative_slots, Cat5CreativeSlots) and state.creative_slots.story_scaffold:
                scaffold = state.creative_slots.story_scaffold
            is_story_game = scaffold and scaffold.synthesis_format == "collaborative_story"

            if is_story_game and state.synthesis_phase not in ("child_try", "theme_choice", "generate"):
                # Child said yes → invite them to try making a story first
                state.synthesis_phase = "child_try"
                direction = (
                    f"The child wants a story about {names}! "
                    f"Encourage the child to try making one up. "
                    f"Ask: what happens to {names}? "
                    f"Keep it simple and inviting — they can say anything."
                )
                return TurnDirective(
                    action="stay",
                    reasoning="Child confirmed synthesis. Inviting them to try a story first.",
                    response_direction=direction,
                    emotion_tag="excited",
                    stay_on_step=True,
                    max_sentences=2,
                )

            # Fallback: generate story directly (no scaffold, or already in generate phase)
            story_dir, max_s = _build_story_direction(state)
            return TurnDirective(
                action="advance",
                reasoning="Generating story for synthesis.",
                response_direction=story_dir,
                emotion_tag="playful",
                max_sentences=max_s,
            )
        if state.current_step.startswith("STEP_3_COLLECT_") and state.collection_phase == "photo":
            return TurnDirective(
                action="stay",
                reasoning="Child affirmed but hasn't selected a photo yet. Encourage finding.",
                response_direction=(
                    "Encourage the child to find and photograph something matching the collection criterion."
                ),
                emotion_tag="encouraging",
                stay_on_step=True,
            )
        # Other contexts: let LLM decide
        return None

    return None


def _is_celebrate_step(step: str) -> bool:
    return step in ("STEP_4_CELEBRATE", "STEP_5_CELEBRATE")


def _is_closing_step_directive(step: str) -> bool:
    return step in ("STEP_5_CLOSING", "STEP_6_CLOSING")


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


async def _get_turn_directive(state: SessionStateModel, turn_input: "TurnInput") -> TurnDirective:
    """Get a TurnDirective via fast-path or LLM Turn Director call."""
    child_text = turn_input.text or ""

    # Fast path: synthesis sub-phases
    # Flow: invite → child_try (yes) / theme_choice (no) → generate
    if (
        state.current_step == "STEP_4_SYNTHESIS"
        and state.synthesis_phase in ("child_try", "theme_choice")
        and child_text
        and not turn_input.is_silent
    ):
        normalized_synth = child_text.strip().lower().rstrip("!.?")

        if state.synthesis_phase == "child_try":
            # Check if child declined to make a story → offer theme choices
            if normalized_synth in _DECLINE_WORDS:
                scaffold = None
                if isinstance(state.creative_slots, Cat5CreativeSlots) and state.creative_slots.story_scaffold:
                    scaffold = state.creative_slots.story_scaffold
                names = ", ".join(state.collected_names) if state.collected_names else "our friends"
                if scaffold and scaffold.story_themes and len(scaffold.story_themes) >= 2:
                    themes = random.sample(scaffold.story_themes, min(2, len(scaffold.story_themes)))
                    state.synthesis_phase = "theme_choice"
                    direction = (
                        f"That's okay! Ask the child what kind of adventure {names} should have. "
                        f'Offer two ideas: "{themes[0]}" or "{themes[1]}". '
                    )
                    if state.tier != "T0":
                        direction += "Also say they can suggest their own idea. "
                    fast = TurnDirective(
                        action="stay",
                        reasoning="Child declined to make a story. Offering theme choices.",
                        response_direction=direction,
                        emotion_tag="encouraging",
                        stay_on_step=True,
                        max_sentences=2,
                    )
                else:
                    # No themes available → AI generates directly
                    state.synthesis_phase = "generate"
                    story_dir, max_s = _build_story_direction(state)
                    fast = TurnDirective(
                        action="advance",
                        reasoning="Child declined. No themes available. AI generates story.",
                        response_direction=story_dir,
                        emotion_tag="playful",
                        max_sentences=max_s,
                    )
                logger.info(
                    "turn_director: step=%s action=%s (child declined story, offering themes)",
                    state.current_step,
                    fast.action,
                )
                state.last_directive_action = fast.action
                return fast

            # Child gave a story attempt — use it as seed
            state.synthesis_child_story = child_text.strip()
            state.synthesis_phase = "generate"
            story_dir, max_s = _build_story_direction(state, chosen_theme="")
            logger.info(
                "turn_director: step=%s action=advance (child story attempt) text=%s",
                state.current_step,
                child_text[:50],
            )
            fast = TurnDirective(
                action="advance",
                reasoning=f"Child attempted story: '{child_text[:50]}'. AI weaves into complete story.",
                response_direction=story_dir,
                emotion_tag="playful",
                max_sentences=max_s,
            )
            state.last_directive_action = fast.action

        else:
            # theme_choice: child picked a theme (or their own idea)
            chosen_theme = child_text.strip()
            state.synthesis_phase = "generate"
            story_dir, max_s = _build_story_direction(state, chosen_theme=chosen_theme)
            logger.info(
                "turn_director: step=%s action=advance (fast-path theme chosen) theme=%s",
                state.current_step,
                chosen_theme[:50],
            )
            fast = TurnDirective(
                action="advance",
                reasoning=f"Child chose story theme: '{chosen_theme[:50]}'. Generating story.",
                response_direction=story_dir,
                emotion_tag="playful",
                max_sentences=max_s,
            )
            state.last_directive_action = fast.action
        return fast

    # Fast path: celebrate step — always advance (or stay on silence)
    if _is_celebrate_step(state.current_step):
        if turn_input.is_silent and state.consecutive_silence < 2:
            role_title = ""
            if isinstance(state.creative_slots, Cat1CreativeSlots):
                role_title = state.creative_slots.role_title
            elif isinstance(state.creative_slots, Cat5CreativeSlots):
                role_title = state.creative_slots.role_title
            names_str = ", ".join(state.collected_names) if state.collected_names else "all the friends"
            return TurnDirective(
                action="stay",
                reasoning="Child is silent at celebrate — give them a moment, don't exit.",
                response_direction=(
                    f"Award the title '{role_title}' ceremonially. "
                    f"Recap the journey with {names_str}. Celebrate warmly."
                ),
                emotion_tag="proud",
                stay_on_step=True,
                max_sentences=4,
            )
        # Any input or auto-advance → advance to closing
        role_title = ""
        if isinstance(state.creative_slots, Cat1CreativeSlots):
            role_title = state.creative_slots.role_title
        elif isinstance(state.creative_slots, Cat5CreativeSlots):
            role_title = state.creative_slots.role_title
        names_str = ", ".join(state.collected_names) if state.collected_names else "all the friends"
        return TurnDirective(
            action="advance",
            reasoning="Celebrate step — advancing to closing.",
            response_direction=(
                f"Award the title '{role_title}' ceremonially. "
                f"Recap the journey with {names_str}. Celebrate the whole process warmly."
            ),
            emotion_tag="proud",
            max_sentences=4,
            sfx_cue="badge_awarded",
            screen_widget="badge_award",
        )

    # Fast path: closing step — always advance to end
    if _is_closing_step_directive(state.current_step):
        ib_concepts = ", ".join(state.ib_key_concepts) if state.ib_key_concepts else ""
        return TurnDirective(
            action="advance",
            reasoning="Closing step — wrapping up the activity.",
            response_direction=(
                f"Name the IB concept ({ib_concepts}) naturally connected to what they discovered. "
                f"Plant a curiosity seed for next time. Warm goodbye."
            ),
            emotion_tag="warm",
            max_sentences=3,
            screen_widget="badge_award",
            sfx_cue="badge_awarded",
        )

    # Fast path: correct photo pick — child selected a photo, phase is now "detail".
    # This is NOT silence — the child acted by picking a photo.
    if (
        turn_input.photo_id
        and state.current_step.startswith("STEP_3_COLLECT_")
        and state.collection_phase == "detail"
        and state.detail_exchange_count == 0
    ):
        remaining = max(0, state.total_rounds - len(state.collected_photos))
        is_last = remaining == 0

        # Build context-aware direction using story scaffold if available
        direction = "Celebrate finding this item! Ask a detail question about it."
        scaffold = None
        if isinstance(state.creative_slots, Cat5CreativeSlots) and state.creative_slots.story_scaffold:
            scaffold = state.creative_slots.story_scaffold
            direction = (
                f"Celebrate finding this item! Based on the story scaffold strategy for round "
                f"{state.current_round}: {scaffold.harvest_question_strategy}. "
                f"Ask a question to harvest: {scaffold.harvest_per_round}."
            )
        if is_last:
            direction += (
                " This is the LAST find — you MUST still ask the harvest question. "
                "Do NOT celebrate completion or say 'all done'. The child still needs to "
                "describe this item before we move to synthesis."
            )

        sfx = "mission_complete_fanfare" if is_last else "slot_fill_chime"
        fast = TurnDirective(
            action="stay",
            reasoning=(
                f"Child selected correct photo {turn_input.photo_id}. Now in detail phase — ask a harvest question."
            ),
            response_direction=direction,
            emotion_tag="excited",
            stay_on_step=True,
            sfx_cue=sfx,
            must_model_first=state.tier == "T0",
            offer_binary_choice=state.tier == "T0",
        )
        logger.info(
            "turn_director: step=%s action=stay (fast-path photo pick) photo=%s remaining=%d",
            state.current_step,
            turn_input.photo_id,
            remaining,
        )
        state.last_directive_action = fast.action
        return fast

    # Fast path: child responded in detail phase.
    # Flow depends on synthesis_format:
    #   collaborative_story → 2 exchanges: (1) detail → ask name (2) name → advance
    #   comparison_reveal / sorting_challenge → 1 exchange: observation → advance
    if (
        child_text
        and not turn_input.is_silent
        and state.current_step.startswith("STEP_3_COLLECT_")
        and state.collection_phase == "detail"
    ):
        normalized_detail = child_text.strip().lower().rstrip("!.?")

        # Determine if this is a naming game (2 exchanges) or observation game (1 exchange)
        is_naming_game = True  # default to naming
        scaffold = None
        if isinstance(state.creative_slots, Cat5CreativeSlots):
            scaffold = state.creative_slots.story_scaffold
            if scaffold and scaffold.synthesis_format != "collaborative_story":
                is_naming_game = False

        # Detect non-answers: child is stuck, confused, or asking AI to decide
        _NON_ANSWER_PHRASES = frozenset(
            {
                "i dont know",
                "i don't know",
                "idk",
                "dunno",
                "no idea",
                "help",
                "help me",
                "i need help",
                "you pick",
                "you choose",
                "you decide",
                "you do it",
                "you provide one",
                "you tell me",
                "you name it",
                "you say",
                "hmm",
                "uh",
                "um",
                "huh",
            }
        )
        if normalized_detail in _NON_ANSWER_PHRASES:
            current_item = state.collected_photos[-1] if state.collected_photos else "this item"
            current_item_label = current_item.replace("_", " ")
            obs_angle = ""
            if isinstance(state.creative_slots, Cat5CreativeSlots):
                obs_angle = state.creative_slots.observation_angle

            if is_naming_game:
                exchange_label = "texture" if state.detail_exchange_count == 0 else "naming"
                direction = (
                    f'The child said "{child_text}" — they need help with {exchange_label}. '
                    f"We are talking about the {current_item_label}. Model an answer yourself first. "
                )
                if state.detail_exchange_count == 0:
                    direction += (
                        f"Describe how the {current_item_label} feels in a playful way. "
                        f"Then offer a binary choice about the texture."
                    )
                else:
                    names_so_far = ", ".join(state.collected_names) if state.collected_names else ""
                    direction += f"Suggest two simple ONE-WORD name choices for the {current_item_label}. "
                    if names_so_far:
                        direction += f"Existing friends: {names_so_far} — this one needs its OWN name."
            else:
                exchange_label = "observation"
                direction = (
                    f'The child said "{child_text}" — they need help describing the {obs_angle}. '
                    f"We are talking about the {current_item_label}. Model an answer yourself first. "
                    f"Describe the {obs_angle} of the {current_item_label} in a playful way. "
                    f"Then offer a binary choice about the {obs_angle}."
                )

            fast = TurnDirective(
                action="need_help",
                reasoning=f"Child needs help with {exchange_label}: '{child_text[:30]}'. Scaffolding.",
                response_direction=direction,
                emotion_tag="gentle",
                stay_on_step=True,
                must_model_first=True,
                offer_binary_choice=True,
            )
            logger.info(
                "turn_director: step=%s action=need_help (non-answer in detail) text=%s",
                state.current_step,
                child_text[:30],
            )
            state.last_directive_action = fast.action
            return fast

        state.detail_exchange_count += 1
        remaining = max(0, state.total_rounds - len(state.collected_photos))
        names_so_far = ", ".join(state.collected_names) if state.collected_names else ""
        details_so_far = ", ".join(state.collected_details) if state.collected_details else ""

        if is_naming_game:
            # --- Naming game: 2-exchange flow (detail → name) ---
            if state.detail_exchange_count == 1:
                _record_collection_detail(state, child_text)

                direction = (
                    f'Celebrate the child\'s description (they said: "{child_text}"). '
                    f"This is a NEW character that does NOT have a name yet. "
                    f"Do NOT use any previous character names for this one. "
                    f"Invite the child to give THIS NEW character a fun name. "
                )
                if state.tier == "T0":
                    direction += (
                        "Suggest two simple ONE-WORD name choices (e.g., Fuzzy or Cloudy — not compound names). "
                    )
                else:
                    direction += "Ask what they would name this friend. Let the child choose freely. "
                if names_so_far:
                    direction += (
                        f"(For reference only — PREVIOUS characters: {names_so_far}. "
                        f"Do NOT reuse these names or apply them to the current item.) "
                    )

                fast = TurnDirective(
                    action="stay",
                    reasoning=f"Child described detail: '{child_text[:50]}'. Now asking them to name.",
                    response_direction=direction,
                    emotion_tag="delighted",
                    stay_on_step=True,
                )
                logger.info(
                    "turn_director: step=%s action=stay (naming game exchange 1 — ask name) text=%s",
                    state.current_step,
                    child_text[:30],
                )
            else:
                trait = state.collected_details[-1] if state.collected_details else ""
                child_name = child_text.strip()

                _NAME_EXTRACT_PATTERNS = [
                    re.compile(r"(?:let'?s? call (?:it|him|her|them|this one)?)\s+(.+)", re.IGNORECASE),
                    re.compile(
                        r"(?:I (?:want to |wanna )?(?:name|call) (?:it|him|her|them|this one)?)\s+(.+)",
                        re.IGNORECASE,
                    ),
                    re.compile(r"(?:how about|maybe)\s+(.+)", re.IGNORECASE),
                    re.compile(r"(?:name (?:it|him|her|them))\s+(.+)", re.IGNORECASE),
                ]
                for pat in _NAME_EXTRACT_PATTERNS:
                    m = pat.search(child_name)
                    if m:
                        child_name = m.group(1).strip().rstrip("!.?,")
                        break

                story_elem = StoryElement(
                    round_number=state.current_round,
                    character_name=child_name,
                    trait_or_detail=trait,
                    child_words=child_name,
                )

                direction = f'The child named this character "{child_name}". Celebrate the name enthusiastically! '
                if names_so_far:
                    direction += f"Introduce the whole crew so far: {names_so_far} and {child_name}. "
                if remaining > 0:
                    direction += f"Then invite the child to find the next item ({remaining} more to go)."
                else:
                    direction += "This was the last find! Celebrate the full team, then transition to synthesis."

                fast = TurnDirective(
                    action="advance",
                    reasoning=f"Child named character: '{child_name}'. Harvesting and advancing.",
                    response_direction=direction,
                    emotion_tag="celebrating",
                    stay_on_step=False,
                    story_element=story_elem,
                )
                logger.info(
                    "turn_director: step=%s action=advance (naming exchange 2 — name given) name=%s",
                    state.current_step,
                    child_name[:30],
                )
        else:
            # --- Observation game (comparison_reveal / sorting_challenge): ---
            # Single exchange: child describes observation → harvest → advance
            _record_collection_detail(state, child_text)

            obs_angle = ""
            if isinstance(state.creative_slots, Cat5CreativeSlots):
                obs_angle = state.creative_slots.observation_angle

            story_elem = StoryElement(
                round_number=state.current_round,
                character_name=None,
                trait_or_detail=child_text,
                child_words=child_text,
            )

            direction = f'Celebrate the child\'s observation (they said: "{child_text}"). '
            if details_so_far:
                direction += f"Previous observations: {details_so_far}. Briefly connect to what they noticed before. "
            if remaining > 0:
                direction += (
                    f"Then invite the child to find the next item ({remaining} more to go). "
                    f"Use invitational language about finding something with {obs_angle}."
                )
            else:
                direction += (
                    "This was the last find! Celebrate the full collection, "
                    "then transition to comparing all the finds together."
                )

            fast = TurnDirective(
                action="advance",
                reasoning=f"Child described {obs_angle}: '{child_text[:50]}'. Harvesting observation and advancing.",
                response_direction=direction,
                emotion_tag="celebrating" if remaining == 0 else "delighted",
                stay_on_step=False,
                story_element=story_elem,
            )
            logger.info(
                "turn_director: step=%s action=advance (observation — %s) text=%s remaining=%d",
                state.current_step,
                obs_angle,
                child_text[:30],
                remaining,
            )

        state.last_directive_action = fast.action
        return fast

    # Fast path for common short phrases
    if child_text and not turn_input.is_silent:
        normalized = child_text.strip().lower().rstrip("!.?")
        fast = _fast_path_directive(normalized, state)
        if fast is not None:
            logger.info(
                "turn_director: step=%s action=%s (fast-path) text=%s",
                state.current_step,
                fast.action,
                normalized,
            )
            state.last_directive_action = fast.action
            return fast

    # Enrich child_text with photo context so the LLM doesn't think it's silence
    if turn_input.photo_id and not child_text:
        child_text = f"[selected photo: {turn_input.photo_id}]"

    # LLM Turn Director call
    directive = await _turn_director.direct_turn(state, child_text)

    # Post-process Cat1 advance directives: inject the EXACT next scenario text
    # from the instruction recipe so the speaker doesn't rely on the LLM's summary
    if (
        directive.action == "advance"
        and state.template_type == "cat1"
        and state.current_step.startswith("STEP_3_ROUND_")
        and state.instruction_recipe
    ):
        next_round = state.current_round + 1
        recipe_rounds = state.instruction_recipe.step_instructions.rounds
        next_scenario = ""
        for r in recipe_rounds:
            if r.round_number == next_round:
                next_scenario = r.scenario
                break
        if next_scenario:
            # Append the exact scenario to the direction so the speaker uses it
            directive.response_direction += f' NEXT SCENARIO (use this EXACT text): "{next_scenario}"'

    state.last_directive_action = directive.action
    return directive


async def _resolve_turn_with_directive(
    state: SessionStateModel,
    turn_input: "TurnInput",
    script_agent: ScriptAgent,
    directive: TurnDirective,
) -> TurnResult:
    """Process a turn using the Turn Director's action-based routing.

    Replaces the ~300-line if/elif routing in the legacy path with a
    simple match on directive.action.
    """

    speaker_errors: list[str] = []

    def _debug(gen_debug: GenerationDebugInfo | None, turn_response: TurnResponse | None = None) -> dict:
        debug = _build_debug_payload(state, gen_debug, script_agent, turn_response)
        debug["turn_director"] = {
            "action": directive.action,
            "reasoning": directive.reasoning,
            "response_direction": directive.response_direction[:200],
            "emotion_tag": directive.emotion_tag,
        }
        if directive.story_element:
            debug["turn_director"]["story_element"] = {
                "round": directive.story_element.round_number,
                "character_name": directive.story_element.character_name,
                "trait_or_detail": directive.story_element.trait_or_detail,
                "child_words": directive.story_element.child_words[:100],
            }
        if speaker_errors:
            debug["turn_director"]["speaker_errors"] = speaker_errors
        return debug

    # Record story element if harvested
    if directive.story_element:
        state.story_elements.append(directive.story_element)
        if directive.story_element.character_name:
            state.collected_names.append(directive.story_element.character_name)
        if directive.story_element.trait_or_detail:
            state.collected_details.append(directive.story_element.trait_or_detail)

    # --- Pre-generation state mutations per action ---
    action = directive.action
    auto_advance = False
    response_type = _get_response_type(state.current_step)
    stay_on_step = False
    turn_response: TurnResponse | None = None

    if action == "advance":
        if _is_invitation_step(state.current_step) and not state.invitation_accepted:
            state.invitation_accepted = True
            state.invitation_decline_count = 0

        # Reset collection phase when advancing from a collection step
        if state.current_step.startswith("STEP_3_COLLECT_"):
            state.collection_phase = "photo"
            state.detail_exchange_count = 0

        # Synthesis: generate the story at STEP_4_SYNTHESIS BEFORE advancing
        # to CELEBRATE. Otherwise the speaker runs at CELEBRATE and ignores
        # the story direction.
        if state.current_step == "STEP_4_SYNTHESIS" and "story" in directive.response_direction.lower():
            try:
                turn_response = await script_agent.generate_turn_from_directive(state, directive)
            except Exception as e:
                speaker_errors.append(f"synthesis: {e}")
                logger.warning("Directive speaker failed at synthesis, falling back: %s", e)
                turn_response, _ = await _generate_with_retry(script_agent, state)
            _append_ai_turn(state, turn_response.dialogue)
            state.turn_count += 1
            _advance_state(state)  # STEP_4_SYNTHESIS → STEP_5_CELEBRATE

            # Now auto-generate celebrate + closing inline
            if _is_celebrate_step(state.current_step):
                turn_response.screen_widget = "badge_award"
                turn_response.sfx_cue = "badge_awarded"
            return TurnResult(
                turn_response=turn_response,
                screen_frame=_get_screen_frame(state),
                auto_advance=_should_auto_advance(state),
                response_type=_get_response_type(state.current_step),
                error_exit=False,
                debug=_debug(None, turn_response),
            )

        # Celebrate: generate celebrate dialogue, show badge, then auto-advance
        # to closing on the NEXT turn. This keeps celebrate and closing as
        # separate turns so the badge stays visible long enough.
        if _is_celebrate_step(state.current_step):
            directive.screen_widget = "badge_award"
            directive.sfx_cue = "badge_awarded"
            try:
                turn_response = await script_agent.generate_turn_from_directive(state, directive)
            except Exception as e:
                speaker_errors.append(f"celebrate: {e}")
                logger.warning("Directive speaker failed at celebrate, falling back: %s", e)
                turn_response, _ = await _generate_with_retry(script_agent, state)
            turn_response.screen_widget = "badge_award"
            turn_response.sfx_cue = "badge_awarded"
            _append_ai_turn(state, turn_response.dialogue)
            state.turn_count += 1

            # Advance to closing now, so the next auto-advance turn
            # arrives at STEP_5_CLOSING instead of looping at celebrate.
            _advance_state(state)
            return TurnResult(
                turn_response=turn_response,
                screen_frame=_badge_screen_frame(state),
                auto_advance=_should_auto_advance(state),
                response_type="celebrate",
                error_exit=False,
                debug=_debug(None, turn_response),
            )

        # Generate speaker output BEFORE advancing state so the speaker
        # loads step instructions for the CURRENT step (where the response
        # direction was authored), not the NEXT step.
        is_closing = _is_closing_step_directive(state.current_step)
        try:
            turn_response = await script_agent.generate_turn_from_directive(state, directive)
        except Exception as e:
            speaker_errors.append(f"speaker: {e}")
            logger.warning("Directive speaker failed, falling back to legacy path: %s", e)
            turn_response, _ = await _generate_with_retry(script_agent, state)
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1

        # For closing, keep the badge visible — use badge_award frame
        if is_closing:
            turn_response.screen_widget = "badge_award"

        _advance_state(state)
        if is_terminal(state.current_step):
            state.status = "completed"
            # Return the closing turn_response (with badge) instead of
            # the generic ended result, so the closing dialogue + badge
            # are delivered to the frontend.
            return TurnResult(
                turn_response=turn_response,
                screen_frame=_badge_screen_frame(state),
                auto_advance=False,
                response_type="closing",
                error_exit=False,
                debug=_debug(None, turn_response),
            )

        auto_advance = _should_auto_advance(state)
        response_type = _get_response_type(state.current_step)

    elif action in ("stay", "need_help", "redirect"):
        stay_on_step = True
        if action == "stay" and _is_invitation_step(state.current_step):
            normalized = (turn_input.text or "").strip().lower().rstrip("!.?")
            if normalized in _DECLINE_WORDS:
                state.invitation_decline_count += 1

    elif action == "exit":
        state.current_step = EARLY_EXIT
        state.status = "exited"
        response_type = "graceful_exit"

    if action != "advance":
        # For non-advance actions, generate after state mutations
        try:
            turn_response = await script_agent.generate_turn_from_directive(state, directive)
        except Exception as e:
            speaker_errors.append(f"speaker: {e}")
            logger.warning("Directive speaker failed, falling back to legacy path: %s", e)
            turn_response, _ = await _generate_with_retry(script_agent, state)

        turn_response.stay_on_step = stay_on_step
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1

    assert turn_response is not None, "turn_response must be set by advance/stay/exit branch"

    return TurnResult(
        turn_response=turn_response,
        screen_frame=_get_screen_frame(state),
        auto_advance=auto_advance,
        response_type=response_type,
        error_exit=state.status == "error",
        debug=_debug(None, turn_response),
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

    def _debug(gen_debug: GenerationDebugInfo | None, turn_response: TurnResponse | None = None) -> dict:
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

    # --- 7. Step-specific logic ---

    # 7a. Invitation: route on pre-classified intent
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

    # 7b½. Cat5 Phase B: child responds to detail-harvesting question
    if (
        state.current_step.startswith("STEP_3_COLLECT_")
        and state.collection_phase == "detail"
        and not turn_input.photo_id
        and has_child_input
    ):
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

    # 7c. Round steps (STEP_3_ROUND_* / STEP_3_COLLECT_*)
    if _is_round_step(state.current_step):
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
                turn_response = _collection_photo_prompt(state)
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

            turn_response, gen_debug = await _generate_with_retry(script_agent, state, is_first_on_step=True)

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

        # Cat5 photo phase with no child input = auto-advance into new round.
        # Use a deterministic template — the LLM is unreliable here and often
        # generates "you found something!" when nothing was found.
        if (
            state.current_step.startswith("STEP_3_COLLECT_")
            and state.collection_phase == "photo"
            and not has_child_input
            and isinstance(state.creative_slots, Cat5CreativeSlots)
        ):
            turn_response = _collection_photo_prompt(state)
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
            turn_response, gen_debug = await _generate_with_retry(script_agent, state)
            # Remove the corrective hint from history so it doesn't leak
            state.conversation_history = [t for t in state.conversation_history if t.text != corrective_hint]

        # Guardrail: force stay_on_step when entering Phase B (detail question)
        # The AI just celebrated the correct photo and should ask the detail question;
        # do NOT advance to the next round yet.
        if (
            state.current_step.startswith("STEP_3_COLLECT_")
            and state.collection_phase == "detail"
            and not turn_response.stay_on_step
        ):
            logger.info("Forcing stay_on_step: Phase B detail question pending")
            turn_response.stay_on_step = True

        # Override stay_on_step when Cat5 collection is objectively complete
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

        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=auto_advance or _should_auto_advance(state),
            response_type=_get_response_type(state.current_step),
            error_exit=state.status == "error",
            debug=_debug(gen_debug, turn_response),
        )

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
