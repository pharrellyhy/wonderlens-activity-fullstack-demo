"""Story synthesis phase handler for STEP_4_SYNTHESIS.

Extracted verbatim from turn_handler.py during package decomposition.
"""

import json
import random
import re

try:
    from ..agents.script_agent import ScriptAgent
    from ..image_gen import generate_scene_images
    from ..logger import setup_logger
    from ..schemas import ScreenFrame
    from ..schemas.child_intent import ChildIntentClassification
    from ..schemas.session_state import ConversationTurn, SessionStateModel
    from ..schemas.structured_story import StoryScene, StructuredStory
    from ..schemas.turn_response import TurnResponse
    from ..state_machine import is_terminal, step_needs_user_input
    from .debug import _build_debug_payload
    from .generation import _classify_child_intent, _generate_with_retry
    from .helpers import _advance_state, _append_ai_turn, _get_response_type, _get_screen_frame
    from .types import TurnInput, TurnResult
except ImportError:
    from agents.script_agent import ScriptAgent
    from image_gen import generate_scene_images
    from logger import setup_logger
    from schemas import ScreenFrame
    from schemas.child_intent import ChildIntentClassification
    from schemas.session_state import ConversationTurn, SessionStateModel
    from schemas.structured_story import StoryScene, StructuredStory
    from schemas.turn_response import TurnResponse
    from state_machine import is_terminal, step_needs_user_input

    from turn_handling.debug import _build_debug_payload
    from turn_handling.generation import _classify_child_intent, _generate_with_retry
    from turn_handling.helpers import _advance_state, _append_ai_turn, _get_response_type, _get_screen_frame
    from turn_handling.types import TurnInput, TurnResult

logger = setup_logger(__name__)


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


async def _generate_structured_story(
    script_agent: ScriptAgent,
    state: SessionStateModel,
) -> StructuredStory | None:
    """Generate a structured 3-scene story and all images in parallel.

    Returns StructuredStory with image data URLs populated, or None on failure.
    Falls back to None if the LLM doesn't produce valid structured JSON.
    """
    # Generate the structured story via LLM
    turn_response, _ = await _generate_with_retry(script_agent, state)
    dialogue = turn_response.dialogue

    # Strip emotion tag prefix if present: "[gentle] {json...}" → "{json...}"
    stripped = re.sub(r"^\[[\w, ]+\]\s*", "", dialogue).strip()
    # Strip markdown code fences if present
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)

    try:
        raw = json.loads(stripped)
        story = StructuredStory(
            scenes=[StoryScene(**s) for s in raw["scenes"]],
            achievement_description=raw.get("achievement_description", ""),
        )
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        logger.error("Failed to parse structured story JSON: %s — dialogue: %s", exc, dialogue[:200])
        return None

    if len(story.scenes) != 3:
        logger.warning("Structured story has %d scenes (expected 3), falling back", len(story.scenes))
        return None

    # Generate all images in parallel (3 scenes + 1 achievement)
    scene_descs = [s.image_description for s in story.scenes]
    scene_images, achievement_image = await generate_scene_images(scene_descs, story.achievement_description)

    # Populate image data URLs
    for i, scene in enumerate(story.scenes):
        scene.image_data_url = scene_images[i] if i < len(scene_images) else None
    story.achievement_image_data_url = achievement_image

    return story


def _deliver_scene(state: SessionStateModel, scene_number: int) -> TurnResult:
    """Deliver a pre-generated scene as a deterministic auto-advance turn."""
    story = state.structured_story
    scene = story.scenes[scene_number - 1]
    is_last = scene_number == len(story.scenes)

    widget_params: dict = {
        "scene_number": scene_number,
        "total_scenes": len(story.scenes),
    }
    if scene.image_data_url:
        widget_params["image_data_url"] = scene.image_data_url

    turn_response = TurnResponse(
        dialogue=scene.narration,
        tone_marker="gentle",
        screen_widget="story_scene" if scene.image_data_url else "photo_grid",
        screen_widget_params=widget_params,
        stay_on_step=not is_last,
        sfx_cue="story_page_turn" if not is_last else "celebration_fanfare",
    )

    response_type = _get_response_type(state.current_step)
    screen_frame = ScreenFrame(
        widget=turn_response.screen_widget,
        widget_params=widget_params,
        animation="appear",
        trigger="on_enter",
        sfx_cue=turn_response.sfx_cue,
    )
    _append_ai_turn(state, turn_response.dialogue)
    state.turn_count += 1

    if is_last:
        # Last scene: advance to celebrate
        _advance_state(state)
        auto_advance = not is_terminal(state.current_step) and not step_needs_user_input(state.current_step)
    else:
        # More scenes: auto-advance to next scene
        state.current_scene = scene_number + 1
        state.synthesis_phase = f"scene_{scene_number + 1}"
        auto_advance = True

    return TurnResult(
        turn_response=turn_response,
        screen_frame=screen_frame,
        auto_advance=auto_advance,
        response_type=response_type,
    )


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

    phase = state.synthesis_phase
    child_text = turn_input.text or ""

    # --- SCENE delivery phases: deterministic, no LLM ---
    if phase.startswith("scene_") and state.structured_story:
        scene_num = int(phase.split("_")[1])
        return _deliver_scene(state, scene_num)

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
    # Tries structured scene-by-scene generation first, falls back to monolithic.
    async def _generate_and_advance() -> TurnResult:
        state.synthesis_phase = "generate"

        # Try structured scene-by-scene generation (with images)
        structured = await _generate_structured_story(script_agent, state)
        if structured:
            state.structured_story = structured
            state.current_scene = 1
            state.synthesis_phase = "scene_1"
            return _deliver_scene(state, 1)

        # Fallback: monolithic story (no images)
        turn_response, gen_debug = await _generate_with_retry(script_agent, state)

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

        return _synthesis_result(
            state,
            turn_response,
            advance=True,
            debug=_build_debug_payload(state, gen_debug, script_agent, turn_response),
        )

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
                return _synthesis_result(
                    state,
                    turn_response,
                    advance=False,
                    debug=_build_debug_payload(state, gen_debug, script_agent, turn_response),
                )
            return await _generate_and_advance()

        # substantive — child provided story content
        child_text = turn_input.text or ""
        state.synthesis_child_story = child_text
        state.synthesis_story_attempts += 1
        state.synthesis_story_quality = intent_result.story_quality or "" if intent_result else ""

        if intent_result and intent_result.story_quality == "good":
            turn_response, gen_debug = await _generate_with_retry(script_agent, state)
            return _synthesis_result(
                state,
                turn_response,
                advance=True,
                debug=_build_debug_payload(state, gen_debug, script_agent, turn_response),
            )

        if state.tier == "T0":
            return await _generate_and_advance()

        # T1/T2: weak story → improve phase
        state.synthesis_phase = "improve"
        turn_response, gen_debug = await _generate_with_retry(script_agent, state)
        return _synthesis_result(
            state,
            turn_response,
            advance=False,
            debug=_build_debug_payload(state, gen_debug, script_agent, turn_response),
        )

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
            return _synthesis_result(
                state,
                turn_response,
                advance=True,
                debug=_build_debug_payload(state, gen_debug, script_agent, turn_response),
            )

        # Still weak — AI completes the story from child's seed
        state.synthesis_child_story = combined_story
        return await _generate_and_advance()

    # --- GENERATE phase: direct generation fallback ---
    # Shouldn't normally reach here (generate is handled inline above),
    # but acts as a safety net.
    turn_response, gen_debug = await _generate_with_retry(script_agent, state)
    return _synthesis_result(
        state,
        turn_response,
        advance=True,
        debug=_build_debug_payload(state, gen_debug, script_agent, turn_response),
    )
