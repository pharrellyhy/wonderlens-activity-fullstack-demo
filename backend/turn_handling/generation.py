"""Generation, validation, and intent classification for turn handling.

Provides the retry-loop generation (_generate_with_retry), response validation
helpers, plan-aware validation, and child intent classification.
"""

import json
import re
import time

import httpx
from openai import AsyncOpenAI

try:
    from ..agents.script_agent import ScriptAgent, ScriptAgentError, _enforce_text_only_dialogue
    from ..config import get_settings
    from ..logger import setup_logger
    from ..schemas.child_intent import ChildIntentClassification
    from ..schemas.session_state import ConversationTurn, SessionStateModel
    from ..schemas.turn_plan import TurnPlan
    from ..schemas.turn_response import TurnResponse
    from .types import GenerationDebugInfo
except ImportError:
    from agents.script_agent import ScriptAgent, ScriptAgentError, _enforce_text_only_dialogue
    from config import get_settings
    from logger import setup_logger
    from schemas.child_intent import ChildIntentClassification
    from schemas.session_state import ConversationTurn, SessionStateModel
    from schemas.turn_plan import TurnPlan
    from schemas.turn_response import TurnResponse

    from turn_handling.types import GenerationDebugInfo

logger = setup_logger(__name__)


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
    r"|(?:all|every)\s+\d+\s+(?:spotted|found|collected|done)"
    r"|(?:the\s+)?(?:search|hunt|patrol)\s+is\s+(?:over|complete|done)"
    r")\b"
)


def _has_completion_language(dialogue: str) -> bool:
    """Check if dialogue contains language implying the collection is complete."""
    return bool(_COMPLETION_PATTERNS.search(dialogue))


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
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
            max_retries=0,
            timeout=httpx.Timeout(10.0, connect=3.0),
        )
        response = await client.chat.completions.create(
            model=settings.dashscope_classifier_model,
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


def _activity_title(activity_type: str) -> str:
    """Convert an activity id into a readable fallback title."""
    title = activity_type.removeprefix("activity_").replace("_", " ")
    return title.title()


def _clean_fallback_goal(goal: str, activity_title: str) -> str:
    """Make authored step goals readable as child-facing fallback copy."""
    goal = goal.strip().rstrip(".")
    for prefix in ("Open ", "Explain that ", "Ask ", "Tell "):
        if goal.startswith(prefix):
            goal = goal[len(prefix) :].strip()
            break
    if goal.lower().startswith(activity_title.lower()):
        remainder = goal[len(activity_title) :].strip()
        if remainder.startswith("by "):
            return f"we will work on {remainder[3:]}"
        if remainder.startswith("with "):
            return f"we will start with {remainder[5:]}"
    return goal


def _fallback_step_goal(state: SessionStateModel):
    recipe = state.instruction_recipe
    if recipe is None:
        return None

    instructions = recipe.step_instructions
    step = state.current_step
    if step == "STEP_1_HOOK":
        return instructions.hook
    if step in {"STEP_2_RULES", "STEP_2_MISSION", "STEP_2_SETUP"}:
        return instructions.transition
    if step.startswith("STEP_3"):
        round_index = max(state.current_round - 1, 0)
        if round_index < len(instructions.rounds):
            return instructions.rounds[round_index]
    if "SYNTHESIS" in step and instructions.synthesis is not None:
        return instructions.synthesis
    if "CELEBRATE" in step:
        return instructions.celebrate
    if "CLOSING" in step:
        return instructions.closing
    return instructions.hook


def _fallback_screen_frame(state: SessionStateModel):
    if "CELEBRATE" in state.current_step or "CLOSING" in state.current_step:
        return state.celebration_frame
    if state.current_step.startswith("STEP_3"):
        frame_index = min(max(state.current_round, 1), len(state.visual_frames) - 1)
        return state.visual_frames[frame_index] if state.visual_frames else None
    return state.visual_frames[0] if state.visual_frames else None


def _source_fidelity_fallback_response(state: SessionStateModel) -> TurnResponse:
    """Create a recipe-grounded fallback when the provider is unavailable."""
    step_goal = _fallback_step_goal(state)
    tone = getattr(step_goal, "emotion_tag", "gentle")
    title = _activity_title(state.activity_type)
    role_title = getattr(state.creative_slots, "role_title", "helper")
    goal_text = _clean_fallback_goal(getattr(step_goal, "goal", f"start {title}"), title)

    scenario = getattr(step_goal, "scenario", "")
    scenario_text = f" This round is about {scenario}." if scenario else ""
    names = ", ".join(state.collected_names) if state.collected_names else ""
    is_closing_arc = (
        "CELEBRATE" in state.current_step or "CLOSING" in state.current_step or "SYNTHESIS" in state.current_step
    )
    if is_closing_arc:
        # Celebrate/closing/synthesis end the game — use closing-shaped copy
        # (no "is ready" / "What should we try?"), naming the collected crew.
        crew = f"You and {names} " if names else "You "
        dialogue = f"[{tone}] {crew}did it as the {role_title}! {goal_text}."
    else:
        dialogue = (
            f"[{tone}] {title} is ready: {goal_text}.{scenario_text} You are the {role_title}. What should we try?"
        )

    frame = _fallback_screen_frame(state)
    return TurnResponse(
        dialogue=dialogue,
        tone_marker=tone,
        screen_widget=frame.widget if frame else "photo_display",
        screen_widget_params=frame.widget_params if frame else {"entity": state.entity_name},
        screen_animation=frame.animation if frame else "gentle_pulse",
        sfx_cue=frame.sfx_cue if frame else None,
        stay_on_step=True,
        character_state="encouraging",
    )


def _enforce_text_only_interaction(state: SessionStateModel, response: TurnResponse) -> TurnResponse:
    """Normalize generated choice prompts that accidentally imply non-text input."""
    dialogue = _enforce_text_only_dialogue(state, response.dialogue)
    if dialogue == response.dialogue:
        return response
    return response.model_copy(update={"dialogue": dialogue})


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
            fallback_response = _source_fidelity_fallback_response(state)
            fallback_response = _enforce_text_only_interaction(state, fallback_response)
            return fallback_response, _make_debug("error_fallback")

        attempt_ms = int((time.perf_counter() - attempt_start) * 1000)
        response = _enforce_text_only_interaction(state, response)

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

        is_valid, hint = True, ""
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

    # All attempts failed validation — return the deterministic recipe fallback
    # (Stream 2 D) rather than the last (possibly bad) line.
    _record_retry_stat(state.current_step, exhausted=True)
    logger.warning(
        "script_generation: step=%s attempts=%d tier=%s validation=exhausted -> deterministic fallback",
        state.current_step,
        _MAX_GENERATION_ATTEMPTS,
        state.tier,
    )
    # Clean up any corrective hints from history
    state.conversation_history = [t for t in state.conversation_history if not t.text.startswith("CORRECTION:")]
    fallback_response = _source_fidelity_fallback_response(state)
    fallback_response = _enforce_text_only_interaction(state, fallback_response)
    return fallback_response, _make_debug("exhausted")
