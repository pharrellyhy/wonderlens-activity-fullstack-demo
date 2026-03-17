"""Pre-generated recipe loading and turn resolution for demo entities.

Demo entities (dog, cat, dinosaur, ladybug, dandelion) use pre-authored
recipes with zero LLM calls. Custom photo uploads continue using the
live agent pipeline.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

try:
    from .logger import setup_logger
    from .scenarios import SCENARIO_CATEGORIES
    from .schemas import ActivityRecipe
    from .schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from .schemas.session_state import ConversationTurn, SessionStateModel
    from .schemas.turn_response import TurnResponse
    from .schemas.voice_script import Round
    from .state_machine import EARLY_EXIT, next_step
except ImportError:
    from logger import setup_logger
    from scenarios import SCENARIO_CATEGORIES
    from schemas import ActivityRecipe
    from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from schemas.session_state import ConversationTurn, SessionStateModel
    from schemas.turn_response import TurnResponse
    from schemas.voice_script import Round
    from state_machine import EARLY_EXIT, next_step

logger = setup_logger(__name__)

_RECIPES_DIR = Path(__file__).parent / "recipes"

_DEMO_FILENAMES: set[str] = {"dog.png", "cat.png", "dinosaur.png", "ladybug.png", "dandelion.png"}

# Map demo filenames to entity names used in session state
_FILENAME_ENTITIES: dict[str, str] = {
    "dog.png": "dog",
    "cat.png": "cat",
    "dinosaur.png": "dinosaur",
    "ladybug.png": "ladybug",
    "dandelion.png": "dandelion",
}

# Default creative slots per activity type (derived from scenario YAML defaults)
_CAT1_SLOTS: dict[str, Cat1CreativeSlots] = {
    "mood_changer_dog": Cat1CreativeSlots(
        game_mechanic="what_would_it_say",
        metaphor="This fluffy dog friend has so many feelings inside!",
        role_title="Emotion Translator",
        round_scenarios=["warm sunshine on belly", "tripped and went bump", "favorite treat arrives"],
        escalation_axis="comfortable to excited",
        observation_detail="those cute floppy ears and super soft fur",
    ),
    "dream_whisperer_cat": Cat1CreativeSlots(
        game_mechanic="storytelling_chain",
        metaphor="This sleepy cat is dreaming the most magical dreams!",
        role_title="Dream Whisperer",
        round_scenarios=["floating on a cloud in the sky", "swimming in a milk ocean", "magical garden of favorites"],
        escalation_axis="familiar to fantastical",
        observation_detail="those soft little paws and fluffy fur",
    ),
    "time_machine_dinosaur": Cat1CreativeSlots(
        game_mechanic="what_would_it_say",
        metaphor="This amazing dinosaur has traveled through all of history!",
        role_title="Time Traveler",
        round_scenarios=["prehistoric jungle", "rumbling volcano", "peaceful lake at sunset"],
        escalation_axis="everyday to dramatic to peaceful",
        observation_detail="those big teeth and powerful legs",
    ),
}

_CAT5_SLOTS: dict[str, Cat5CreativeSlots] = {
    "polka_dot_patrol": Cat5CreativeSlots(
        observation_angle="pattern",
        collection_criterion="Find things with dots, spots, or circles",
        collection_count=3,
        mission_metaphor="You are a Polka-Dot Patrol Officer!",
        role_title="Polka-Dot Patrol Officer",
        synthesis_type="comparison_chart",
        stuck_hint="Try looking at flowers up close, or at the ground near your feet",
        naming_prompt="What kind of dots or spots do you see on this?",
    ),
    "fluffy_expedition_dandelion": Cat5CreativeSlots(
        observation_angle="texture",
        collection_criterion="Find things that are fluffy, fuzzy, or soft",
        collection_count=3,
        mission_metaphor="You are a Fluffy Expedition Explorer!",
        role_title="Fluffy Expedition Explorer",
        synthesis_type="comparison_chart",
        stuck_hint="Try touching things around you — look for anything soft or fuzzy",
        naming_prompt="How does this feel? Is it fuzzy, silky, or puffy?",
    ),
}


def is_demo_entity(filename: str) -> bool:
    """Check if the filename matches a demo icon."""
    return filename.lower() in _DEMO_FILENAMES


@lru_cache(maxsize=8)
def load_demo_recipe(activity_type: str) -> ActivityRecipe:
    """Load and cache a pre-authored recipe JSON file."""
    path = _RECIPES_DIR / f"{activity_type}.json"
    if not path.exists():
        raise FileNotFoundError(f"Recipe not found: {path}")
    with open(path) as f:
        data = json.load(f)
    return ActivityRecipe.model_validate(data)


def recipe_to_session_state(
    recipe: ActivityRecipe,
    session_id: str,
    tier: str,
    filename: str,
) -> tuple[SessionStateModel, TurnResponse]:
    """Build a SessionStateModel and first TurnResponse from a pre-authored recipe.

    No agents are invoked — everything comes from the recipe JSON.
    """
    activity_type = recipe.activity_type
    category = SCENARIO_CATEGORIES.get(activity_type, "category_1")
    template_type: Literal["cat1", "cat5"] = "cat5" if category == "category_5" else "cat1"

    # Get creative slots for this activity
    if template_type == "cat5":
        creative_slots = _CAT5_SLOTS[activity_type]
    else:
        creative_slots = _CAT1_SLOTS[activity_type]

    entity_name = _FILENAME_ENTITIES.get(filename.lower(), "object")

    state = SessionStateModel(
        session_id=session_id,
        tier=tier,
        template_type=template_type,
        activity_type=activity_type,
        current_step="STEP_1_HOOK",
        current_round=0,
        total_rounds=recipe.metadata.round_count,
        creative_slots=creative_slots,
        entity_name=entity_name,
        entity_attributes=[],
        entity_category="",
        scene="",
        ib_key_concepts=recipe.metadata.concepts_earned,
        photo_url="",
        is_pregenerated=True,
        recipe=recipe,
        visual_frames=recipe.screen_frames,
        celebration_frame=recipe.celebration_frame,
    )

    # Build hook turn response
    vs = recipe.voice_script
    first_turn = TurnResponse(
        dialogue=vs.hook_line,
        tone_marker=vs.hook_tone,
        screen_widget="photo_display",
        screen_widget_params={"description": f"Photo of {entity_name}", "entity": entity_name},
        screen_animation="sparkle_highlight",
        sfx_cue="wonder_chime",
    )

    # Record hook in conversation history and advance step
    state.conversation_history.append(
        ConversationTurn(role="ai", text=first_turn.dialogue, step=state.current_step, round_number=None)
    )
    state.current_step = next_step(state.current_step, state.template_type, state.current_round, state.total_rounds)
    state.turn_count = 1

    logger.info(
        f"Pre-generated session: {session_id}, activity={activity_type}, "
        f"template={template_type}, rounds={recipe.metadata.round_count}"
    )

    return state, first_turn


def resolve_turn_from_recipe(
    state: SessionStateModel,
    child_text: str,
    is_silent: bool,
    photo_id: str | None = None,
) -> TurnResponse:
    """Resolve the current turn from the pre-authored recipe.

    Maps the current step to pre-authored dialogue with acknowledgment
    selection based on child input.
    """
    recipe = state.recipe
    if recipe is None:
        raise ValueError("No recipe stored in session state")

    vs = recipe.voice_script
    step = state.current_step

    # EARLY_EXIT
    if step == EARLY_EXIT:
        dialogue = vs.early_exit_speech or "(gentle) That was really fun! We can play again anytime!"
        return TurnResponse(
            dialogue=dialogue,
            tone_marker=vs.early_exit_tone,
            screen_widget="badge_award",
            screen_widget_params={"title": "Great job!", "concepts": [], "entity": state.entity_name},
            screen_animation="badge_reveal",
            sfx_cue="badge_awarded",
        )

    # STEP_2_RULES / STEP_2_MISSION — transition line
    if step in ("STEP_2_RULES", "STEP_2_MISSION"):
        return TurnResponse(
            dialogue=vs.transition_line,
            tone_marker=vs.transition_tone,
            screen_widget="character_display",
            screen_widget_params={
                "description": "Activity introduction",
                "entity": state.entity_name,
                "round_number": 0,
            },
            screen_animation="appear",
            sfx_cue="game_start_chime",
        )

    # STEP_3_ROUND_N / STEP_3_COLLECT_N — round prompt with optional acknowledgment
    if step.startswith("STEP_3_ROUND_") or step.startswith("STEP_3_COLLECT_"):
        round_num = int(step.rsplit("_", maxsplit=1)[-1])
        round_idx = round_num - 1

        if round_idx >= len(vs.rounds):
            round_idx = len(vs.rounds) - 1
        current_round = vs.rounds[round_idx]

        # Build acknowledgment from previous round (if not the first round)
        ack = ""
        if round_num > 1:
            prev_idx = round_idx - 1
            if 0 <= prev_idx < len(vs.rounds):
                ack = _select_round_transition_ack(vs.rounds[prev_idx], child_text, is_silent, photo_id)

        dialogue = f"{ack} {current_round.prompt}".strip() if ack else current_round.prompt

        return TurnResponse(
            dialogue=dialogue,
            tone_marker=current_round.tone_marker,
            screen_widget="character_display",
            screen_widget_params={
                "description": f"Round {round_num}",
                "entity": state.entity_name,
                "round_number": round_num,
            },
            screen_animation="scene_transition" if round_num > 1 else "gentle_pulse",
            sfx_cue=current_round.sfx_cue,
        )

    # STEP_4_SYNTHESIS (cat5 only) — synthesis speech with last round ack
    if step == "STEP_4_SYNTHESIS":
        ack = ""
        if vs.rounds:
            ack = _select_round_transition_ack(vs.rounds[-1], child_text, is_silent, photo_id)

        dialogue_text = vs.synthesis_speech or "Let's look at everything you collected!"
        dialogue = f"{ack} {dialogue_text}".strip() if ack else dialogue_text

        return TurnResponse(
            dialogue=dialogue,
            tone_marker=vs.synthesis_tone,
            screen_widget="photo_grid",
            screen_widget_params={"description": "All collected items", "entity": state.entity_name},
            screen_animation="sparkle_highlight",
            sfx_cue=None,
        )

    # STEP_4_CELEBRATE / STEP_5_CELEBRATE — closing speech with last round ack
    if step in ("STEP_4_CELEBRATE", "STEP_5_CELEBRATE"):
        ack = ""
        if vs.rounds:
            ack = _select_acknowledgment(vs.rounds[-1], child_text, is_silent)

        dialogue = f"{ack} {vs.closing_speech}".strip() if ack else vs.closing_speech
        role_title = state.creative_slots.role_title

        return TurnResponse(
            dialogue=dialogue,
            tone_marker=vs.closing_tone,
            screen_widget="badge_award",
            screen_widget_params={
                "title": role_title,
                "concepts": state.ib_key_concepts,
                "entity": state.entity_name,
            },
            screen_animation="celebration_burst",
            sfx_cue="celebration_fanfare",
        )

    # STEP_5_CLOSING / STEP_6_CLOSING — tomorrow hook
    if step in ("STEP_5_CLOSING", "STEP_6_CLOSING"):
        return TurnResponse(
            dialogue=vs.tomorrow_hook,
            tone_marker=vs.tomorrow_tone,
            screen_widget="badge_award",
            screen_widget_params={
                "title": "IB Concepts",
                "concepts": state.ib_key_concepts,
                "entity": state.entity_name,
            },
            screen_animation="badge_reveal",
            sfx_cue="badge_awarded",
        )

    # Fallback
    logger.warning(f"Unhandled step in recipe resolution: {step}")
    return TurnResponse(
        dialogue=vs.closing_speech,
        tone_marker="gentle",
        screen_widget="badge_award",
        screen_widget_params={"title": "Great job!", "concepts": [], "entity": state.entity_name},
        screen_animation="badge_reveal",
        sfx_cue="badge_awarded",
    )


def resolve_wrong_photo_turn(state: SessionStateModel, photo_id: str | None) -> TurnResponse:
    """Return a 'try again' response for a wrong photo pick in cat5 collection rounds."""
    recipe = state.recipe
    if recipe is None:
        raise ValueError("No recipe stored in session state")

    vs = recipe.voice_script
    step = state.current_step

    # Get current round's on_wrong_photo if available
    if step.startswith("STEP_3_COLLECT_"):
        round_num = int(step.rsplit("_", maxsplit=1)[-1])
        round_idx = round_num - 1
        if 0 <= round_idx < len(vs.rounds):
            wrong_text = vs.rounds[round_idx].on_wrong_photo
            if wrong_text:
                return TurnResponse(
                    dialogue=wrong_text,
                    tone_marker="encouraging",
                    screen_widget="progress_tracker",
                    screen_widget_params={"description": "Try again", "entity": state.entity_name},
                    screen_animation="gentle_pulse",
                    sfx_cue=None,
                )

    # Generic fallback
    return TurnResponse(
        dialogue="Hmm, that's not quite right. Would you like to try picking a different one?",
        tone_marker="encouraging",
        screen_widget="progress_tracker",
        screen_widget_params={"description": "Try again", "entity": state.entity_name},
        screen_animation="gentle_pulse",
        sfx_cue=None,
    )


def _select_acknowledgment(round_data: Round, child_text: str, is_silent: bool) -> str:
    """Select the appropriate acknowledgment based on child input."""
    if is_silent:
        return round_data.on_silence

    if not child_text:
        return ""

    # Check for correct response (substring match)
    child_lower = child_text.lower()
    for correct in round_data.correct_responses:
        if correct.lower() in child_lower:
            return round_data.on_correct

    return round_data.on_incorrect


def _select_round_transition_ack(round_data: Round, child_text: str, is_silent: bool, photo_id: str | None) -> str:
    """Choose the ack that bridges from the just-finished round into the next step."""
    if photo_id is not None:
        return round_data.on_correct
    return _select_acknowledgment(round_data, child_text, is_silent)
