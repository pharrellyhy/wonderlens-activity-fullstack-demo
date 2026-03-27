"""Unified turn resolution logic for both /api/turn and /api/turn-speak.

This module extracts the step transition logic that was previously duplicated
across the two turn endpoints, ensuring consistent behavior for invitation
acceptance, round advancement, auto-advance signaling, and history management.
"""

import json
import re
from dataclasses import dataclass

import httpx
from openai import AsyncOpenAI

try:
    from .agents.script_agent import ScriptAgent, ScriptAgentError
    from .config import get_settings
    from .logger import setup_logger
    from .schemas import ScreenFrame
    from .schemas.creative_slots import Cat5CreativeSlots
    from .schemas.session_state import ConversationTurn, SessionStateModel
    from .schemas.story_classification import StoryClassification
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
    from config import get_settings
    from logger import setup_logger
    from schemas import ScreenFrame
    from schemas.creative_slots import Cat5CreativeSlots
    from schemas.session_state import ConversationTurn, SessionStateModel
    from schemas.story_classification import StoryClassification
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
    re.compile(r'["“]([^"”]{1,40})["”]'),
    re.compile(
        r"(?:how about|call (?:it|this(?: one)?)|let's call (?:it|this(?: one)?))\s+"
        r"([A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+){0,2})",
        re.IGNORECASE,
    ),
    re.compile(r"^([A-Z][A-Za-z]+(?: [A-Z][A-Za-z]+){0,2})[!,.]"),
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

    # 4. T0 synthesis: must scaffold
    if step == "STEP_4_SYNTHESIS" and tier == "T0" and is_first_on_step:
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

    return True, ""


# ---------------------------------------------------------------------------
# Plan-aware validation (two-pass diagnostics)
# ---------------------------------------------------------------------------

# Common household/outdoor items that indicate the speaker is suggesting specific
# things the child should go find — violates the do_not_suggest_items constraint.
_ITEM_SUGGESTION_RE = re.compile(
    r"(?i)\b(?:find|look for|grab|get|bring|search for|spot)\b"
    r"[^.!?]{0,40}"
    r"\b(?:pillow|blanket|sock|shoe|cup|spoon|fork|plate|ball|book|toy|rock|leaf|stick"
    r"|flower|shell|stone|button|coin|bottle|box|bag|hat|glove|scarf|key|pen|pencil"
    r"|crayon|block|ring|wheel|clock|bowl|jar|lid|pan|pot|ribbon|string|bead|marble)\b"
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
# Story synthesis classification
# ---------------------------------------------------------------------------


async def _classify_story_response(state: SessionStateModel, child_text: str) -> StoryClassification:
    """Classify a child's response during the story synthesis loop.

    Uses a lightweight LLM call to determine if the child's response is a story
    attempt, a decline, a request for the AI to tell the story, or unrelated.

    Args:
        state: Current session state with collected characters/details.
        child_text: The child's response text.

    Returns:
        StoryClassification with classification, relatedness, and quality.
    """
    collected = ", ".join(state.collected_names) if state.collected_names else "the collected items"
    prompt = (
        f"The child was asked to make up a story about these characters: {collected}.\n"
        f'The child said: "{child_text}"\n\n'
        f"Classify the child's response:\n"
        f'- "story_attempt": The child provided ANY narrative content (even a single sentence '
        f"like 'the dog went to sleep'). Set story_quality to \"good\" if it has 2+ story elements "
        f'(character + action, or action + outcome) and relates to the characters, or "weak" if '
        f"it's a single sentence with no progression.\n"
        f"- \"decline\": The child said no, refused, or doesn't want to ('no', 'I don't want to', "
        f"shakes head, 'nah').\n"
        f"- \"ask_ai\": The child wants the AI to tell the story ('you tell me', 'can you make one up?', "
        f"'tell me a story').\n"
        f'- "unrelated": The response doesn\'t relate to storytelling or the characters at all.\n\n'
        f"Set is_related_to_collection to true if the response mentions or relates to the collected "
        f"characters ({collected}).\n"
        f'Set story_quality to null unless classification is "story_attempt".'
    )

    try:
        settings = get_settings()
        client = AsyncOpenAI(
            api_key=settings.ali_api_key,
            base_url=settings.ali_base_url,
            max_retries=0,
            timeout=httpx.Timeout(15.0, connect=5.0),
        )
        response = await client.chat.completions.create(
            model=settings.ali_model,
            messages=[
                {"role": "system", "content": "Classify a child's response. Output valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=150,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return StoryClassification(
            classification=data.get("classification", "unrelated"),
            is_related_to_collection=data.get("is_related_to_collection", False),
            story_quality=data.get("story_quality"),
        )
    except Exception:
        logger.warning("Story classification LLM call failed, defaulting to 'unrelated'")
        return StoryClassification(
            classification="unrelated",
            is_related_to_collection=False,
            story_quality=None,
        )


# ---------------------------------------------------------------------------
# LLM generation with retry + validation
# ---------------------------------------------------------------------------

_MAX_GENERATION_ATTEMPTS = 3
_MAX_DETAIL_EXCHANGES = 3

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
) -> TurnResponse:
    """Generate a turn response with validation and retry.

    Attempts up to _MAX_GENERATION_ATTEMPTS times. After each generation,
    runs plan-aware validation (if a TurnPlan is available) followed by
    post-processing validation. If validation fails, appends a corrective
    hint and retries. The hint is removed from history after retry.
    """
    last_response: TurnResponse | None = None
    retry_plan: TurnPlan | None = None

    for attempt in range(_MAX_GENERATION_ATTEMPTS):
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
            logger.warning(f"Script Agent failed for step {state.current_step} (attempt {attempt + 1})")
            if attempt < _MAX_GENERATION_ATTEMPTS - 1:
                continue
            # Final attempt failed — use fallback
            logger.error(f"Script Agent failed {_MAX_GENERATION_ATTEMPTS} times, using fallback")
            state.status = "error"
            return TurnResponse(
                dialogue="[gentle] That was so much fun! Would you like to play again next time? See you soon!",
                tone_marker="gentle",
                screen_widget="badge_award",
                screen_widget_params={"title": "Great job!", "concepts": [], "entity": state.entity_name},
                screen_animation="badge_reveal",
                sfx_cue="badge_awarded",
            )

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

        is_valid, hint = _validate_response(state, response, is_first_on_step)
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
            return response

        # Log both the plan and response on validation failure for diagnostics
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
    return last_response  # type: ignore[return-value]


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
# Story synthesis loop
# ---------------------------------------------------------------------------


def _synthesis_result(
    state: SessionStateModel,
    turn_response: TurnResponse,
    *,
    advance: bool = False,
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
    )


async def _resolve_synthesis_turn(
    state: SessionStateModel,
    turn_input: TurnInput,
    script_agent: ScriptAgent,
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

    Returns:
        TurnResult with response and advancement signals.
    """
    phase = state.synthesis_phase
    child_text = turn_input.text or ""

    # --- INVITE phase: generate story invitation ---
    if phase == "invite":
        turn_response = await _generate_with_retry(script_agent, state, is_first_on_step=True)
        state.synthesis_phase = "evaluate"
        state.synthesis_prompt_count += 1
        return _synthesis_result(state, turn_response, advance=False)

    # --- EVALUATE phase: classify child's response ---
    if phase == "evaluate":
        classification = await _classify_story_response(state, child_text)
        logger.info(
            "synthesis_classification: classification=%s quality=%s related=%s text=%s",
            classification.classification,
            classification.story_quality,
            classification.is_related_to_collection,
            child_text[:80],
        )

        if classification.classification == "story_attempt":
            state.synthesis_child_story = child_text

            if classification.story_quality == "good":
                # Good story — celebrate and advance
                turn_response = await _generate_with_retry(script_agent, state)
                return _synthesis_result(state, turn_response, advance=True)

            if state.tier == "T0":
                # T0 weak story — AI expands the child's seed
                state.synthesis_phase = "generate"
                turn_response = await _generate_with_retry(script_agent, state)
                return _synthesis_result(state, turn_response, advance=True)

            # T1/T2 weak story — ask child to elaborate
            state.synthesis_phase = "improve"
            turn_response = await _generate_with_retry(script_agent, state)
            return _synthesis_result(state, turn_response, advance=False)

        if classification.classification in ("decline", "ask_ai"):
            # Child declined or asked AI to tell — generate full story
            state.synthesis_phase = "generate"
            turn_response = await _generate_with_retry(script_agent, state)
            return _synthesis_result(state, turn_response, advance=True)

        # Unrelated response
        if state.synthesis_prompt_count < 2:
            # Re-invite (stay in evaluate for next response)
            state.synthesis_prompt_count += 1
            turn_response = await _generate_with_retry(script_agent, state, is_first_on_step=True)
            return _synthesis_result(state, turn_response, advance=False)

        # Max prompts exhausted — AI generates
        state.synthesis_phase = "generate"
        turn_response = await _generate_with_retry(script_agent, state)
        return _synthesis_result(state, turn_response, advance=True)

    # --- IMPROVE phase: child's elaboration arrived ---
    if phase == "improve":
        combined_story = f"{state.synthesis_child_story} {child_text}".strip()
        classification = await _classify_story_response(state, combined_story)
        logger.info(
            "synthesis_improve_classification: quality=%s combined=%s",
            classification.story_quality,
            combined_story[:100],
        )

        if classification.story_quality == "good":
            # Elaboration is good enough — celebrate and advance
            turn_response = await _generate_with_retry(script_agent, state)
            return _synthesis_result(state, turn_response, advance=True)

        # Still weak — AI completes the story from child's seed
        state.synthesis_phase = "generate"
        state.synthesis_child_story = combined_story
        turn_response = await _generate_with_retry(script_agent, state)
        return _synthesis_result(state, turn_response, advance=True)

    # --- GENERATE phase: direct generation fallback ---
    # Shouldn't normally reach here (generate is handled inline above),
    # but acts as a safety net.
    turn_response = await _generate_with_retry(script_agent, state)
    return _synthesis_result(state, turn_response, advance=True)


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
            # Phase A -> Phase B: correct photo triggers detail-harvesting question
            state.collection_phase = "detail"
            state.detail_exchange_count = 0
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
        is_first = not _already_prompted_on_step(state)
        turn_response = await _generate_with_retry(script_agent, state, is_first_on_step=is_first)

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
        turn_response = await _generate_with_retry(script_agent, state)
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        _maybe_record_generated_name(state, turn_response.dialogue)

        remaining_count = max(0, state.total_rounds - len(state.collected_photos))
        response_type = _get_response_type(state.current_step)
        # Respect stay_on_step from the AI — the child may be confused or
        # off-topic and needs guidance back before advancing. Cap at 3
        # exchanges to prevent infinite loops.
        if turn_response.stay_on_step and state.detail_exchange_count < _MAX_DETAIL_EXCHANGES:
            logger.info(
                "Phase B: child needs guidance (exchange %d/%d), staying in detail phase",
                state.detail_exchange_count,
                _MAX_DETAIL_EXCHANGES,
            )
            return TurnResult(
                turn_response=turn_response,
                screen_frame=_get_screen_frame(state),
                auto_advance=False,
                response_type=response_type,
                error_exit=state.status == "error",
            )

        if remaining_count == 0:
            # Keep the collected-photo view for this response, then auto-advance into synthesis.
            state.round_advance_pending = True
            state.detail_exchange_count = 0
            return TurnResult(
                turn_response=turn_response,
                screen_frame=_get_screen_frame(state),
                auto_advance=True,
                response_type=response_type,
                error_exit=state.status == "error",
            )

        # Detail phase complete — move to the next collection round in photo-pick mode.
        state.collection_phase = "photo"
        state.detail_exchange_count = 0
        _advance_state(state)

        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type=response_type,
            error_exit=state.status == "error",
        )

    # 7c. Round steps (STEP_3_ROUND_* / STEP_3_COLLECT_*)
    if _is_round_step(state.current_step):
        if state.round_advance_pending and not has_child_input:
            state.round_advance_pending = False
            if state.current_step.startswith("STEP_3_COLLECT_"):
                state.collection_phase = "photo"
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
        # Pass is_first_on_step when entering detail phase (correct photo just picked).
        entering_detail = (
            state.current_step.startswith("STEP_3_COLLECT_")
            and state.collection_phase == "detail"
            and collection_wrong is False
            and turn_input.photo_id is not None
        )
        turn_response = await _generate_with_retry(
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
            turn_response = await _generate_with_retry(script_agent, state)
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

    # 7d-i. STEP_4_SYNTHESIS: story synthesis loop with phase-based routing
    if state.current_step == "STEP_4_SYNTHESIS":
        return await _resolve_synthesis_turn(state, turn_input, script_agent)

    # 7d-ii. Other interactive steps (STEP_1_HOOK): first visit or child response
    if step_needs_user_input(state.current_step) and not _already_prompted_on_step(state):
        turn_response = await _generate_with_retry(script_agent, state, is_first_on_step=True)
        _append_ai_turn(state, turn_response.dialogue)
        state.turn_count += 1
        return TurnResult(
            turn_response=turn_response,
            screen_frame=_get_screen_frame(state),
            auto_advance=False,
            response_type=_get_response_type(state.current_step),
            error_exit=state.status == "error",
        )

    if step_needs_user_input(state.current_step):
        if state.current_step == "STEP_1_HOOK":
            _advance_state(state)
            turn_response = await _generate_with_retry(script_agent, state, is_first_on_step=True)
            _append_ai_turn(state, turn_response.dialogue)
            state.turn_count += 1
            return TurnResult(
                turn_response=turn_response,
                screen_frame=_get_screen_frame(state),
                auto_advance=False,
                response_type=_get_response_type(state.current_step),
                error_exit=state.status == "error",
            )

        # Generic interactive step fallback
        turn_response = await _generate_with_retry(script_agent, state)
        if turn_response.stay_on_step:
            _append_ai_turn(state, turn_response.dialogue)
            state.turn_count += 1
            return TurnResult(
                turn_response=turn_response,
                screen_frame=_get_screen_frame(state),
                auto_advance=False,
                response_type=_get_response_type(state.current_step),
                error_exit=state.status == "error",
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
