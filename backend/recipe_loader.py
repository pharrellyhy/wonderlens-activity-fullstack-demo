"""Instruction-based recipe loading for demo entities.

Demo entities (dog, cat, dinosaur, ladybug, dandelion) use instruction-based
recipes where each step has goals and constraints instead of exact dialogue.
The Script Agent LLM generates contextual responses guided by these instructions.
Custom photo uploads continue using the live agent pipeline.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

try:
    from .logger import setup_logger
    from .scenarios import SCENARIO_CATEGORIES
    from .schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from .schemas.recipe import InstructionRecipe
    from .schemas.session_state import SessionStateModel
except ImportError:
    from logger import setup_logger
    from scenarios import SCENARIO_CATEGORIES
    from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from schemas.recipe import InstructionRecipe
    from schemas.session_state import SessionStateModel

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
def load_instruction_recipe(activity_type: str) -> InstructionRecipe:
    """Load and cache an instruction-based recipe JSON file."""
    path = _RECIPES_DIR / f"{activity_type}.json"
    if not path.exists():
        raise FileNotFoundError(f"Recipe not found: {path}")
    with open(path) as f:
        data = json.load(f)
    return InstructionRecipe.model_validate(data)


def recipe_to_session_state(
    recipe: InstructionRecipe,
    session_id: str,
    tier: str,
    filename: str,
) -> SessionStateModel:
    """Build a SessionStateModel from an instruction recipe.

    Unlike the old dialogue-based system, the hook turn is NOT pre-generated here.
    The Script Agent will generate the hook turn using the recipe instructions.
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
        instruction_recipe=recipe,
        visual_frames=recipe.screen_frames,
        celebration_frame=recipe.celebration_frame,
    )

    logger.info(
        f"Instruction recipe session: {session_id}, activity={activity_type}, "
        f"template={template_type}, rounds={recipe.metadata.round_count}"
    )

    return state
