"""Story synthesis phase handler for STEP_4_SYNTHESIS.

Extracted verbatim from turn_handler.py during package decomposition.
"""

import json
import random
import re
import time

import httpx
import openai
from openai import AsyncOpenAI
from pydantic import ValidationError

try:
    from ..agents.script_agent import ScriptAgent
    from ..config import get_settings
    from ..image_gen import generate_scene_images
    from ..logger import setup_logger
    from ..schemas import ScreenFrame
    from ..schemas.child_intent import ChildIntentClassification
    from ..schemas.creative_slots import Cat5CreativeSlots
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
    from config import get_settings
    from image_gen import generate_scene_images
    from logger import setup_logger
    from schemas import ScreenFrame
    from schemas.child_intent import ChildIntentClassification
    from schemas.creative_slots import Cat5CreativeSlots
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


def _loading_result(state: SessionStateModel) -> TurnResult:
    """Return a story_loading screen and queue story generation via auto-advance."""
    names = ", ".join(state.collected_names) if state.collected_names else "your friends"
    turn_response = TurnResponse(
        dialogue=f"[excited] Ooh, let me think of a story about {names}...",
        tone_marker="excited",
        screen_widget="story_loading",
        screen_widget_params={},
        stay_on_step=True,
    )
    screen_frame = ScreenFrame(
        widget="story_loading",
        widget_params={},
        animation="appear",
        trigger="on_enter",
    )
    _append_ai_turn(state, turn_response.dialogue)
    state.turn_count += 1
    state.synthesis_phase = "generate"
    return TurnResult(
        turn_response=turn_response,
        screen_frame=screen_frame,
        auto_advance=True,
        response_type=_get_response_type(state.current_step),
    )


async def _generate_structured_story(
    state: SessionStateModel,
) -> StructuredStory | None:
    """Generate a structured 3-scene story via direct LLM call, then images in parallel.

    Calls the LLM directly (bypassing ScriptAgent) with JSON mode enforced so the
    response is guaranteed to be valid JSON matching the StructuredStory schema.
    ScriptAgent wraps all output in {"dialogue": "..."} format which conflicts
    with structured story JSON — hence the direct call.

    Returns StructuredStory with image data URLs populated, or None on failure.
    """
    settings = get_settings()
    details = "; ".join(state.collected_details) if state.collected_details else "no details"
    child_story = state.synthesis_child_story or "none"

    # Build character identity: map child-given names to what they actually are
    # e.g. "Peter (a soft petal), Spiky (a woolly caterpillar), Sam (a fuzzy moss)"
    char_parts: list[str] = []
    for i, name in enumerate(state.collected_names):
        photo_id = state.collected_photos[i] if i < len(state.collected_photos) else ""
        item_type = photo_id.replace("_", " ") if photo_id else "unknown creature"
        char_parts.append(f"{name} (a {item_type})")
    characters = ", ".join(char_parts) if char_parts else "the characters"

    system_prompt = (
        "You are a warm storyteller for young children. "
        "Generate a structured 3-scene story as a JSON object. Output ONLY valid JSON."
    )

    user_prompt = (
        f"Characters: {characters}\n"
        f"Sensory details the child shared: {details}\n"
        f"Tier: {state.tier}\n"
        f"Child's story attempt to expand (if any): {child_story}\n\n"
        "Generate a JSON object with this EXACT structure:\n"
        f'{{"scenes": ['
        f'{{"narration": "Scene 1 text (2-4 sentences)", "image_description": "Watercolor illustration description under 50 words"}},'
        f'{{"narration": "Scene 2 text (2-4 sentences)", "image_description": "Watercolor illustration description under 50 words"}},'
        f'{{"narration": "Scene 3 text (2-4 sentences)", "image_description": "Watercolor illustration description under 50 words"}}'
        f'], "achievement_description": "All characters together in a warm celebratory scene"}}\n\n'
        "SCENE STRUCTURE:\n"
        "Scene 1 — Opening + Surprise: Set the scene. Something unexpected happens.\n"
        "Scene 2 — Try and Struggle: A character tries to solve it. It doesn't work. Another has an idea.\n"
        "Scene 3 — Breakthrough + Warm Ending: They figure it out together. End with comfort.\n\n"
        "RULES:\n"
        "- Use ALL characters by name. Every character appears in at least 2 scenes.\n"
        "- Start scene 1 narration with an emotion tag like [gentle] or [warm].\n"
        "- Real emotions (scared, proud, cozy), real dialogue in quotes.\n"
        "- Warm ending on comfort, not excitement.\n"
        "- Image descriptions: watercolor storybook style. Characters are NOT human — they are the actual items listed above (petals, caterpillars, moss, seeds, etc.) drawn as cute animated versions. Include character names + physical traits, mood/lighting cues, no text in images.\n"
        "- Achievement description: show ALL characters together in a warm scene."
    )

    try:
        start = time.perf_counter()
        client = AsyncOpenAI(
            api_key=settings.ali_api_key,
            base_url=settings.ali_base_url,
            max_retries=0,
            timeout=httpx.Timeout(60.0, connect=15.0),
        )
        response = await client.chat.completions.create(
            model=settings.ali_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=2048,
            response_format={"type": "json_object"},
            extra_body={"enable_thinking": False},
        )
        raw_text = response.choices[0].message.content or ""
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.info("Structured story LLM response (%dms): %s", latency_ms, raw_text[:200])

        raw = json.loads(raw_text)
        story = StructuredStory.model_validate(raw)

    except (json.JSONDecodeError, ValidationError) as exc:
        logger.error("Failed to parse structured story JSON: %s", exc)
        return None
    except (httpx.HTTPError, openai.OpenAIError) as exc:
        logger.error("Structured story LLM call failed: %s", exc)
        return None

    if len(story.scenes) != 3:
        logger.warning("Structured story has %d scenes (expected 3), falling back", len(story.scenes))
        return None

    # Generate all images in parallel (3 scenes + 1 achievement)
    scene_descs = [s.image_description for s in story.scenes]
    scene_images, achievement_image = await generate_scene_images(
        scene_descs, story.achievement_description, session_id=state.session_id
    )

    # Populate image data URLs
    for i, scene in enumerate(story.scenes):
        scene.image_data_url = scene_images[i] if i < len(scene_images) else None
    story.achievement_image_data_url = achievement_image

    return story


async def _generate_comparison_reveal(
    state: SessionStateModel,
) -> StructuredStory | None:
    """Generate a 1-scene comparison reveal for non-story synthesis formats.

    Unlike collaborative_story which has 3 narrative scenes, comparison_reveal
    produces a single "reveal" scene that shows all collected items side by
    side, highlighting how they differ across the observation angle. Uses a
    direct LLM call with JSON mode (bypasses ScriptAgent for the same reason
    as structured story — ScriptAgent forces {"dialogue": "..."} format).

    Returns StructuredStory with 1 scene + achievement image, or None on failure.
    """
    settings = get_settings()
    items = [p.replace("_", " ") for p in state.collected_photos]
    if not items:
        return None

    obs_angle = ""
    if isinstance(state.creative_slots, Cat5CreativeSlots):
        obs_angle = state.creative_slots.observation_angle
    obs_angle = obs_angle or "special feature"

    details = "; ".join(state.collected_details) if state.collected_details else "no details"
    items_str = ", ".join(items)

    system_prompt = (
        "You are a warm guide for young children exploring patterns and observations. "
        "Generate a JSON object. Output ONLY valid JSON."
    )

    user_prompt = (
        f"Items collected: {items_str}\n"
        f"Observation angle: {obs_angle}\n"
        f"Details the child noticed: {details}\n"
        f"Tier: {state.tier}\n\n"
        "Generate a JSON object with this EXACT structure:\n"
        '{"narration": "Comparison text (3-5 sentences)", '
        '"reveal_description": "Image description under 50 words", '
        '"achievement_description": "Achievement image description under 50 words"}\n\n'
        "NARRATION RULES:\n"
        "- Start with an emotion tag like [excited] or [curious]\n"
        f"- Help the child compare the {obs_angle} across all {len(items)} items\n"
        f"- Point out how the {obs_angle} looks different on each\n"
        "- Reference the child's observations when possible\n"
        "- 3-5 warm sentences, end with celebration (not a question)\n\n"
        f"REVEAL IMAGE: Watercolor storybook illustration showing all {len(items)} items "
        f"({items_str}) arranged side by side in a row, each clearly showing their "
        f"different {obs_angle}. Soft pastel tones, warm lighting. No text in image.\n\n"
        f"ACHIEVEMENT IMAGE: Watercolor celebratory scene with all {len(items)} items "
        f"({items_str}) grouped together as friends who explored together. Warm lighting, "
        "storybook style. No text in image."
    )

    try:
        start = time.perf_counter()
        client = AsyncOpenAI(
            api_key=settings.ali_api_key,
            base_url=settings.ali_base_url,
            max_retries=0,
            timeout=httpx.Timeout(60.0, connect=15.0),
        )
        response = await client.chat.completions.create(
            model=settings.ali_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1024,
            response_format={"type": "json_object"},
            extra_body={"enable_thinking": False},
        )
        raw_text = response.choices[0].message.content or ""
        latency_ms = int((time.perf_counter() - start) * 1000)
        logger.info("Comparison reveal LLM response (%dms): %s", latency_ms, raw_text[:200])

        raw = json.loads(raw_text)
        narration = raw.get("narration", "").strip()
        reveal_desc = raw.get("reveal_description", "").strip()
        achievement_desc = raw.get("achievement_description", "").strip()

        if not narration or not reveal_desc:
            logger.warning("Comparison reveal JSON missing required fields")
            return None

    except (json.JSONDecodeError, ValidationError) as exc:
        logger.error("Failed to parse comparison reveal JSON: %s", exc)
        return None
    except (httpx.HTTPError, openai.OpenAIError) as exc:
        logger.error("Comparison reveal LLM call failed: %s", exc)
        return None

    # Generate reveal image + achievement image in parallel
    scene_images, achievement_image = await generate_scene_images(
        [reveal_desc], achievement_desc, session_id=state.session_id
    )

    scene = StoryScene(
        narration=narration,
        image_description=reveal_desc,
        image_data_url=scene_images[0] if scene_images else None,
    )

    return StructuredStory(
        scenes=[scene],
        achievement_description=achievement_desc,
        achievement_image_data_url=achievement_image,
    )


def _deliver_scene(state: SessionStateModel, scene_number: int) -> TurnResult:
    """Deliver a pre-generated scene as a deterministic auto-advance turn."""
    story = state.structured_story
    if story is None:
        raise RuntimeError("_deliver_scene called without structured_story")
    scene = story.scenes[scene_number - 1]
    is_last = scene_number == len(story.scenes)

    sfx = "celebration_fanfare" if is_last else "story_page_turn"
    widget_params: dict = {
        "scene_number": scene_number,
        "total_scenes": len(story.scenes),
    }
    if scene.image_data_url:
        widget_params["image_data_url"] = scene.image_data_url

    turn_response = TurnResponse(
        dialogue=scene.narration,
        tone_marker="gentle",
        screen_widget="story_scene",
        screen_widget_params=widget_params,
        stay_on_step=not is_last,
        sfx_cue=sfx,
    )

    response_type = _get_response_type(state.current_step)
    screen_frame = ScreenFrame(
        widget="story_scene",
        widget_params=widget_params,
        animation="appear",
        trigger="on_enter",
        sfx_cue=sfx,
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
    # Picks structured generator based on synthesis_format, falls back to monolithic.
    async def _generate_and_advance() -> TurnResult:
        state.synthesis_phase = "generate"

        # Choose generator based on synthesis format
        scaffold = None
        if isinstance(state.creative_slots, Cat5CreativeSlots) and state.creative_slots.story_scaffold:
            scaffold = state.creative_slots.story_scaffold
        is_story = bool(scaffold and scaffold.synthesis_format == "collaborative_story")

        if is_story:
            structured = await _generate_structured_story(state)
        else:
            structured = await _generate_comparison_reveal(state)

        if structured and structured.scenes:
            state.structured_story = structured
            state.current_scene = 1
            state.synthesis_phase = "scene_1"
            return _deliver_scene(state, 1)

        # Fallback: monolithic story (no images)
        turn_response, gen_debug = await _generate_with_retry(script_agent, state)

        # Sentence count check only for story format — comparison is naturally shorter
        if is_story:
            min_sentences = _MIN_STORY_SENTENCES.get(state.tier, 6)
            sentences = [s.strip() for s in re.split(r"[.!?]+", turn_response.dialogue) if s.strip()]
            if len(sentences) < min_sentences:
                logger.warning(
                    "Story too short (%d sentences, need %d), regenerating with length hint",
                    len(sentences),
                    min_sentences,
                )
                hint_text = (
                    f"[system: The story is too short. Generate a complete story with at "
                    f"least {min_sentences} sentences.]"
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

    # --- GENERATE phase: do the actual story + image generation ---
    if phase == "generate":
        return await _generate_and_advance()

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
            return _loading_result(state)

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
            return _loading_result(state)

        # substantive — child provided story content
        child_text = turn_input.text or ""
        state.synthesis_child_story = child_text
        state.synthesis_story_attempts += 1
        state.synthesis_story_quality = intent_result.story_quality or "" if intent_result else ""

        if intent_result and intent_result.story_quality == "good":
            # Child's story is strong — AI expands it monolithically (not scene-by-scene).
            # Structured scene delivery is reserved for AI-generated stories.
            turn_response, gen_debug = await _generate_with_retry(script_agent, state)
            return _synthesis_result(
                state,
                turn_response,
                advance=True,
                debug=_build_debug_payload(state, gen_debug, script_agent, turn_response),
            )

        if state.tier == "T0":
            return _loading_result(state)

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
            return _loading_result(state)

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
        return _loading_result(state)
