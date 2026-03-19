"""Instruction-based recipe loading for demo entities.

Demo entities are loaded from game MD files via game_loader. JSON fallback
is retained for non-demo entities or legacy recipes (e.g. polka_dot_patrol_hard).
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

try:
    from .entity_registry import entity_name_for_filename, get_creative_slots, is_demo_entity
    from .game_loader import get_demo_recipe
    from .logger import setup_logger
    from .scenarios import SCENARIO_CATEGORIES
    from .schemas.recipe import InstructionRecipe
    from .schemas.session_state import SessionStateModel
except ImportError:
    from entity_registry import entity_name_for_filename, get_creative_slots, is_demo_entity
    from game_loader import get_demo_recipe
    from logger import setup_logger
    from scenarios import SCENARIO_CATEGORIES
    from schemas.recipe import InstructionRecipe
    from schemas.session_state import SessionStateModel

logger = setup_logger(__name__)

_RECIPES_DIR = Path(__file__).parent / "recipes"


@lru_cache(maxsize=8)
def load_instruction_recipe(activity_type: str) -> InstructionRecipe:
    """Load an instruction recipe — game MD first, JSON fallback."""
    recipe = get_demo_recipe(activity_type)
    if recipe is not None:
        return recipe
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

    creative_slots = get_creative_slots(activity_type)
    entity_name = entity_name_for_filename(filename)

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
