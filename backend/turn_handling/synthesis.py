"""Story synthesis phase handler for STEP_4_SYNTHESIS.

Extracted verbatim from turn_handler.py during package decomposition.
"""

import asyncio
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
    from ..image_gen import get_scene_session, start_scene_images
    from ..logger import setup_logger
    from ..schemas import ScreenFrame
    from ..schemas.child_intent import ChildIntentClassification
    from ..schemas.creative_slots import Cat5CreativeSlots
    from ..schemas.session_state import ConversationTurn, SessionStateModel
    from ..schemas.structured_story import StructuredStory
    from ..schemas.turn_response import TurnResponse
    from ..state_machine import is_terminal, step_needs_user_input
    from ..synthesis_formats import get_format
    from ..synthesis_formats.loader import SynthesisFormat
    from .debug import _build_debug_payload
    from .generation import _classify_child_intent, _generate_with_retry
    from .helpers import _advance_state, _append_ai_turn, _get_response_type, _get_screen_frame
    from .types import TurnInput, TurnResult
except ImportError:
    from agents.script_agent import ScriptAgent
    from config import get_settings
    from image_gen import get_scene_session, start_scene_images
    from logger import setup_logger
    from schemas import ScreenFrame
    from schemas.child_intent import ChildIntentClassification
    from schemas.creative_slots import Cat5CreativeSlots
    from schemas.session_state import ConversationTurn, SessionStateModel
    from schemas.structured_story import StructuredStory
    from schemas.turn_response import TurnResponse
    from state_machine import is_terminal, step_needs_user_input
    from synthesis_formats import get_format
    from synthesis_formats.loader import SynthesisFormat

    from turn_handling.debug import _build_debug_payload
    from turn_handling.generation import _classify_child_intent, _generate_with_retry
    from turn_handling.helpers import _advance_state, _append_ai_turn, _get_response_type, _get_screen_frame
    from turn_handling.types import TurnInput, TurnResult

# Per-scene image wait timeout. Each Imagen call takes ~3-5s and retries add
# another ~3s, so ~15s is the realistic worst case for a single scene. 30s
# gives a 2x margin — any longer and a stuck generation would appear to the
# child as a prolonged hang rather than a fallback to no-image rendering.
_SCENE_IMAGE_WAIT_TIMEOUT_S = 30.0

logger = setup_logger(__name__)


_SYNTHESIS_INVITE_TEMPLATES = [
    "[gentle] Would you like to make up a little story about {names}?",
    "[curious] What if {names} went on an adventure? Would you like to tell that story?",
    "[whispering] I wonder what {names} would do together... would you like to imagine?",
]

# Celebration poster palette — rotating celebration props picked at image
# generation time so each session's achievement image feels fresh and, more
# importantly, looks distinct from the story's warm-ending scene 3. The LLM
# kept producing achievement descriptions that read like "characters
# together in a warm scene" — exactly what scene 3 already is — so we take
# control of the composition here with a deterministic template.
_CELEBRATION_PROPS = [
    "soft paper confetti drifting down and a warm golden sunburst halo glowing behind them",
    "tiny paper flags held above their heads and a curved ribbon banner arching overhead",
    "small paper crowns perched on each one and gentle golden particles floating around",
    "a bright spotlight beam from above and tiny bursts of coloured confetti around them",
    "a wreath of soft flower petals framing them and warm sparkles shimmering in the air",
    "a cozy campfire glow behind them and a string of tiny paper bunting stretched overhead",
]

_CELEBRATION_CAPTIONS = [
    "We did it!",
    "What a team!",
    "Friends forever.",
    "Our first adventure.",
    "A brave new team!",
    "Together we shine.",
]


def _build_achievement_prompt(characters: str, role_title: str | None) -> tuple[str, str]:
    """Return a (description, caption) pair for the achievement image.

    This is intentionally *not* derived from the LLM's story output — the
    LLM kept producing achievement descriptions that looked identical to
    scene 3 (the warm ending). Using a deterministic template forces the
    celebration image to be visually distinct: a centered hero poster with
    rotating celebration props instead of a narrative scene.

    Character names are interpolated so the characters themselves still
    match the story, but the composition is locked.
    """
    props = random.choice(_CELEBRATION_PROPS)
    description = (
        f"A celebration poster in soft watercolor storybook style: {characters} all centered "
        "side by side at the front of the frame, facing the viewer in a proud hero pose, "
        f"warmly smiling. {props}. Bright high-key lighting, rich cheerful colors, "
        "iconic centered composition. This is a CELEBRATION PORTRAIT, not a narrative scene — "
        "no ongoing action, no environment details, just the characters being celebrated."
    )
    if role_title:
        caption = f"A new {role_title}!"
        # Keep the caption within the ≤6-word budget; fall back if the role
        # title is itself long (rare, but role_title is LLM-generated).
        if len(caption.split()) > 6:
            caption = random.choice(_CELEBRATION_CAPTIONS)
    else:
        caption = random.choice(_CELEBRATION_CAPTIONS)
    return description, caption


def _role_title_for(state: SessionStateModel) -> str | None:
    """Return the Cat5 role title for ``state``, or None for other templates."""
    slots = state.creative_slots
    if isinstance(slots, Cat5CreativeSlots):
        return slots.role_title or None
    return None


def _condense_caption(text: str, max_words: int = 8) -> str | None:
    """Trim a longer string down to a short in-image caption.

    Returns None if the input is empty. Otherwise strips leading emotion
    tags like ``[gentle]``, takes the first sentence, removes trailing
    punctuation / quotes, and truncates to ``max_words`` words. Used as a
    fallback when the LLM's own caption field is missing.
    """
    if not text:
        return None
    # Strip leading "[tone]" marker if present.
    cleaned = re.sub(r"^\s*\[[^\]]+\]\s*", "", text).strip()
    if not cleaned:
        return None
    # First sentence only — split on . ! ? keeping it short and punchy.
    first = re.split(r"[.!?]", cleaned, maxsplit=1)[0].strip().strip("\"\u201c\u201d'")
    if not first:
        return None
    words = first.split()
    if len(words) > max_words:
        first = " ".join(words[:max_words])
    return first or None


def _resolve_format_id(state: SessionStateModel) -> str:
    """Return the synthesis format id for the current session state.

    Args:
        state: Session state with optional story scaffold.

    Returns:
        The synthesis format id from the scaffold, or ``"collaborative_story"`` as default.
    """
    if isinstance(state.creative_slots, Cat5CreativeSlots) and state.creative_slots.story_scaffold:
        return state.creative_slots.story_scaffold.synthesis_format
    return "collaborative_story"


def _build_template_variables(
    state: SessionStateModel,
    fmt: SynthesisFormat,
    *,
    chosen_theme: str = "",
) -> dict[str, str | int]:
    """Build the canonical render dict for story prompt and direction templates.

    Covers all template keys used by collaborative_story (and future formats).
    Every key is always present — empty string when not applicable.

    Args:
        state: Session state with collected items and story elements.
        fmt: Loaded synthesis format providing tier-specific sentence counts.
        chosen_theme: Theme string chosen by the child (or empty for no theme).

    Returns:
        Dict mapping template variable names to their rendered string values.
    """
    scaffold = None
    if isinstance(state.creative_slots, Cat5CreativeSlots) and state.creative_slots.story_scaffold:
        scaffold = state.creative_slots.story_scaffold

    # --- characters: for the LLM user_prompt ("Peter (a soft petal), ...") ---
    char_parts: list[str] = []
    for i, name in enumerate(state.collected_names):
        photo_id = state.collected_photos[i] if i < len(state.collected_photos) else ""
        item_type = photo_id.replace("_", " ") if photo_id else "unknown creature"
        char_parts.append(f"{name} (a {item_type})")
    # items must be computed before characters so the fallback can reference it.
    items = [p.replace("_", " ") for p in state.collected_photos]
    if char_parts:
        characters = ", ".join(char_parts)
    elif items:
        # Non-naming games (e.g. comparison_reveal) have no child-given names;
        # use item labels as the "characters" for the achievement poster.
        characters = ", ".join(items)
    else:
        characters = "the characters"

    # --- chars_desc: for the direction template ("Peter (soft), Spiky (wiggly), ...") ---
    elems = state.story_elements
    if elems:
        desc_parts: list[str] = []
        for e in elems:
            name = e.character_name or f"Friend {e.round_number}"
            trait = e.trait_or_detail or "soft"
            desc_parts.append(f"{name} ({trait})")
        chars_desc = ", ".join(desc_parts)
    else:
        chars_desc = ", ".join(state.collected_names) if state.collected_names else "the collected friends"

    # --- items: photo ids as human-readable strings (already computed above) ---
    items_str = ", ".join(items) if items else ""

    # --- names: comma-joined child-given names ---
    # Fallback "the friends" matches the plan's template vocabulary and lets
    # format files reference {names} unconditionally without crashing.
    names = ", ".join(state.collected_names) if state.collected_names else "the friends"

    # --- details: semicolon-joined sensory details ---
    details = "; ".join(state.collected_details) if state.collected_details else "no details"

    # --- obs_angle: observation angle from creative slots ---
    obs_angle = ""
    if isinstance(state.creative_slots, Cat5CreativeSlots):
        obs_angle = state.creative_slots.observation_angle or ""

    # --- obs_list: numbered list of round observations ---
    if elems:
        obs_parts: list[str] = []
        for i, e in enumerate(elems, 1):
            detail = e.trait_or_detail or e.child_words or f"find {i}"
            obs_parts.append(f"Find {i}: {detail}")
        obs_list = "; ".join(obs_parts)
    else:
        obs_list = "; ".join(state.collected_details) if state.collected_details else "the collected finds"

    # --- tier / tier_sentences ---
    tier = state.tier
    tier_sentences = fmt.direction_tier_sentences.get(tier, "6-10")

    # --- theme_suffix: " (theme)" when present, "" otherwise (used by collaborative_story) ---
    theme_suffix = f" ({chosen_theme})" if chosen_theme else ""

    # --- theme_angle_suffix: "Use this angle: theme. " when present (used by comparison_reveal) ---
    theme_angle_suffix = f"Use this angle: {chosen_theme}. " if chosen_theme else ""

    # --- sorting_suffix: "Sort by: criterion. " when present (used by comparison_reveal) ---
    sorting_criterion = ""
    if isinstance(state.creative_slots, Cat5CreativeSlots):
        sorting_criterion = state.creative_slots.sorting_criterion or ""
    sorting_suffix = f"Sort by: {sorting_criterion}. " if sorting_criterion else ""

    # --- goal_suffix: "\nGoal: ..." when scaffold present (used by comparison_reveal) ---
    if scaffold and scaffold.synthesis_goal:
        goal_suffix = f"\nGoal: {scaffold.synthesis_goal}. "
    else:
        goal_suffix = ""

    # --- premise_line: "Premise: ...\n" when scaffold present, "" otherwise ---
    if scaffold and scaffold.premise and scaffold.synthesis_goal:
        premise_line = f"Premise: {scaffold.premise}. Goal: {scaffold.synthesis_goal}.\n"
    else:
        premise_line = ""

    # --- child_story_line: '\nThe child tried... \n' when present, "" otherwise ---
    child_story = state.synthesis_child_story or "none"
    if state.synthesis_child_story:
        child_story_line = (
            f'\nThe child tried to tell a story: "{state.synthesis_child_story}". '
            f"Weave their idea into the story — honor what they said and expand it.\n"
        )
    else:
        child_story_line = ""

    return {
        "characters": characters,
        "chars_desc": chars_desc,
        "items": items_str,
        "count": len(items),
        "names": names,
        "details": details,
        "obs_angle": obs_angle,
        "obs_list": obs_list,
        "tier": tier,
        "tier_sentences": tier_sentences,
        "theme": chosen_theme,
        "child_story": child_story,
        "theme_suffix": theme_suffix,
        "theme_angle_suffix": theme_angle_suffix,
        "sorting_suffix": sorting_suffix,
        "goal_suffix": goal_suffix,
        "premise_line": premise_line,
        "child_story_line": child_story_line,
    }


async def _generate_structured_output(
    state: SessionStateModel,
    fmt: SynthesisFormat,
) -> StructuredStory | None:
    """Format-agnostic structured story generator driven by a SynthesisFormat.

    Renders the format's system_prompt and user_prompt templates, calls the LLM
    with the format's temperature and max_tokens, then validates, post-processes,
    and kicks off progressive scene image generation.

    Args:
        state: Current session state.
        fmt: Loaded synthesis format to drive generation.

    Returns:
        Populated StructuredStory on success, or None on any failure.
    """
    settings = get_settings()
    variables = _build_template_variables(state, fmt)
    system_prompt = fmt.system_prompt.format(**variables)
    user_prompt = fmt.user_prompt.format(**variables)
    # characters is always a str in the builder; coerce defensively so the
    # type checker can see the value as str when passed to _build_achievement_prompt.
    characters = str(variables["characters"])

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
            temperature=fmt.temperature,
            max_tokens=fmt.max_tokens,
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

    if len(story.scenes) != fmt.scene_count:
        logger.warning(
            "Structured story has %d scenes (expected %d), falling back",
            len(story.scenes),
            fmt.scene_count,
        )
        return None

    # Normalise captions
    scene_captions: list[str | None] = []
    for scene in story.scenes:
        scene.caption = _condense_caption(scene.caption or "", max_words=10) or _condense_caption(
            scene.narration, max_words=8
        )
        scene_captions.append(scene.caption)

    # Override the LLM's achievement description with a deterministic celebration-poster template
    achievement_desc, achievement_caption = _build_achievement_prompt(characters, _role_title_for(state))
    story.achievement_description = achievement_desc
    story.achievement_caption = achievement_caption

    # Progressive scene image generation — scene 1 is delivered while 2, 3 are mid-generation
    scene_descs = [s.image_description for s in story.scenes]
    start_scene_images(
        state.session_id,
        scene_descs,
        story.achievement_description,
        scene_captions=scene_captions,
        achievement_caption=story.achievement_caption,
    )

    # image_data_urls intentionally left None — _deliver_scene fills them from futures
    return story


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
    """Return a synthesis loading screen and queue generation via auto-advance.

    Format-neutral: the same dialogue works for collaborative_story (dandelion),
    comparison_reveal (ladybug), and any future synthesis format.
    """
    turn_response = TurnResponse(
        dialogue="[excited] Ooh, let me put it all together for you...",
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
    # Emit a debug payload so the loading turn appears in the History tab
    # at STEP_4_SYNTHESIS with the current synthesis phase.
    debug = _build_debug_payload(state, None, None, turn_response)
    debug["source"] = "synthesis_loading"
    return TurnResult(
        turn_response=turn_response,
        screen_frame=screen_frame,
        auto_advance=True,
        response_type=_get_response_type(state.current_step),
        debug=debug,
    )


async def _await_scene_image(session_id: str, scene_index: int) -> str | None:
    """Await the progressive future for a given scene index, if any.

    Returns the base64 data URL if the scene image landed in time, None on
    timeout / cancellation / missing session. Missing session is the normal
    case when the image was generated up front (e.g. by the blocking
    ``generate_scene_images`` wrapper used for comparison_reveal) so the
    caller can fall back to whatever ``StoryScene.image_data_url`` already
    holds.
    """
    session = get_scene_session(session_id)
    if session is None:
        return None
    if scene_index >= len(session.scene_futures):
        return None
    future = session.scene_futures[scene_index]
    try:
        return await asyncio.wait_for(asyncio.shield(future), timeout=_SCENE_IMAGE_WAIT_TIMEOUT_S)
    except asyncio.TimeoutError:
        logger.warning("Scene %d image not ready after %.0fs", scene_index + 1, _SCENE_IMAGE_WAIT_TIMEOUT_S)
        return None
    except asyncio.CancelledError:
        logger.warning("Scene %d image wait cancelled", scene_index + 1)
        return None


async def _await_achievement_image(session_id: str) -> str | None:
    """Await the progressive achievement image future, if any."""
    session = get_scene_session(session_id)
    if session is None:
        return None
    try:
        return await asyncio.wait_for(
            asyncio.shield(session.achievement_future),
            timeout=_SCENE_IMAGE_WAIT_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        logger.warning("Achievement image not ready after %.0fs", _SCENE_IMAGE_WAIT_TIMEOUT_S)
        return None
    except asyncio.CancelledError:
        logger.warning("Achievement image wait cancelled")
        return None


async def _deliver_scene(state: SessionStateModel, scene_number: int) -> TurnResult:
    """Deliver a scene as a deterministic auto-advance turn.

    Awaits the per-scene future from the progressive image session so scene
    N ships the moment its image is ready — without waiting for scenes
    N+1..M. When the last scene is delivered, the achievement image future
    is also awaited so the downstream celebrate frame has the URL available.
    """
    story = state.structured_story
    if story is None:
        raise RuntimeError("_deliver_scene called without structured_story")
    scene = story.scenes[scene_number - 1]
    is_last = scene_number == len(story.scenes)

    # Populate the image data URL lazily: the scene may have been pre-filled
    # by the blocking path (comparison_reveal) or it may still be mid-flight
    # in a progressive session. Only cache a NON-None result — if the wait
    # timed out here, a later retry delivery of the same scene should get
    # another chance to read the future (the background worker keeps running
    # even after a wait_for timeout thanks to asyncio.shield).
    if scene.image_data_url is None:
        resolved = await _await_scene_image(state.session_id, scene_number - 1)
        if resolved is not None:
            scene.image_data_url = resolved

    # On the final scene, pull the achievement image forward too so it's
    # ready by the time the celebrate frame is built on the next turn.
    # Same rule: only cache a non-None result so a retry can re-await.
    if is_last and story.achievement_image_data_url is None:
        resolved_ach = await _await_achievement_image(state.session_id)
        if resolved_ach is not None:
            story.achievement_image_data_url = resolved_ach

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

    # Full debug payload with step_flow + phase_timeline so scene delivery
    # turns show up correctly in the History tab for both Cat5 formats
    # (dandelion's 3 scenes and ladybug's 1 reveal scene).
    debug = _build_debug_payload(state, None, None, turn_response)
    debug["source"] = "structured_scene_delivery"
    debug["scene"] = {
        "scene_number": scene_number,
        "total_scenes": len(story.scenes),
        "is_last": is_last,
    }

    return TurnResult(
        turn_response=turn_response,
        screen_frame=screen_frame,
        auto_advance=auto_advance,
        response_type=response_type,
        debug=debug,
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
        return await _deliver_scene(state, scene_num)

    # --- INVITE phase: deterministic template, no LLM ---
    if phase == "invite":
        turn_response = _synthesis_invite_prompt(state)
        state.synthesis_phase = "evaluate"
        state.synthesis_prompt_count += 1
        # Emit a debug payload so the invite turn shows in the History tab.
        invite_debug = _build_debug_payload(state, None, None, turn_response)
        invite_debug["source"] = "synthesis_invite"
        return _synthesis_result(
            state,
            turn_response,
            advance=False,
            debug=invite_debug,
        )

    # Shared helper: format-agnostic structured generation with monolithic fallback.
    async def _generate_and_advance() -> TurnResult:
        state.synthesis_phase = "generate"

        fmt = get_format(_resolve_format_id(state))
        structured = await _generate_structured_output(state, fmt)

        if structured and structured.scenes:
            state.structured_story = structured
            state.current_scene = 1
            state.synthesis_phase = "scene_1"
            return await _deliver_scene(state, 1)

        # Fallback: monolithic ScriptAgent output (no images)
        turn_response, gen_debug = await _generate_with_retry(script_agent, state)

        # Length check via the format's min_sentences_total
        min_sentences = fmt.min_sentences_total.get(state.tier, 6)
        sentences = [s.strip() for s in re.split(r"[.!?]+", turn_response.dialogue) if s.strip()]
        if len(sentences) < min_sentences:
            logger.warning(
                "Synthesis [%s] too short (%d sentences, need %d), regenerating",
                fmt.id,
                len(sentences),
                min_sentences,
            )
            hint_text = f"[system: Output is too short. Generate at least {min_sentences} sentences.]"
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
