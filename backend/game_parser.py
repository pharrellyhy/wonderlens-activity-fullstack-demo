"""Parse game MD files with YAML frontmatter into EntityConfig + InstructionRecipe."""

import re
from pathlib import Path

import yaml

try:
    from .entity_registry import CollectionCatalog, CollectionItem, EntityConfig
    from .schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from .schemas.recipe import InstructionRecipe, RecipeMetadata
    from .schemas.step_instruction import RoundInstruction, StepGoal, StepInstruction
    from .schemas.visual_composition import ScreenFrame
except ImportError:
    from entity_registry import CollectionCatalog, CollectionItem, EntityConfig
    from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from schemas.recipe import InstructionRecipe, RecipeMetadata
    from schemas.step_instruction import RoundInstruction, StepGoal, StepInstruction
    from schemas.visual_composition import ScreenFrame


def _extract_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        raise ValueError("No YAML frontmatter found")
    return yaml.safe_load(match.group(1))


def _build_entity_config(data: dict) -> EntityConfig:
    """Build an EntityConfig from parsed frontmatter dict."""
    entity_name = data["entity_name"]
    category = data["category"]
    slots_data = data["creative_slots"]

    if category == "category_5":
        creative_slots = Cat5CreativeSlots(**slots_data)
    else:
        creative_slots = Cat1CreativeSlots(**slots_data)

    collection_catalog = None
    if "collection_catalog" in data:
        cat_data = data["collection_catalog"]
        collection_catalog = CollectionCatalog(
            correct=[CollectionItem(**item) for item in cat_data["correct"]],
            distractors=[CollectionItem(**item) for item in cat_data["distractors"]],
        )

    return EntityConfig(
        activity_type=data["activity_type"],
        category=category,
        entity_name=entity_name,
        demo_filename=f"{entity_name}.png",
        display_label=data["display_label"],
        icon_src=f"/icons/{entity_name}.png",
        keywords=data.get("keywords", []),
        feature_keywords=data.get("feature_keywords", []),
        creative_slots=creative_slots,
        collection_catalog=collection_catalog,
        tier=data["tier"],
        ib_theme=data["ib_theme"],
        ib_key_concept=data["ib_key_concept"],
        concepts_earned=data.get("concepts_earned", []),
    )


def _build_step_instruction(si_data: dict) -> StepInstruction:
    """Build a StepInstruction from the step_instructions frontmatter dict."""
    rounds = [RoundInstruction(**r) for r in si_data["rounds"]]
    synthesis = StepGoal(**si_data["synthesis"]) if "synthesis" in si_data else None

    return StepInstruction(
        hook=StepGoal(**si_data["hook"]),
        transition=StepGoal(**si_data["transition"]),
        rounds=rounds,
        celebrate=StepGoal(**si_data["celebrate"]),
        closing=StepGoal(**si_data["closing"]),
        synthesis=synthesis,
        early_exit=StepGoal(**si_data["early_exit"]),
    )


def _build_collection_items(data: dict) -> dict:
    """Build collection_items dict for Cat5 entities."""
    if "collection_catalog" not in data:
        return {}
    catalog = data["collection_catalog"]
    return {
        "correct": [item["id"] for item in catalog["correct"]],
        "distractors": [item["id"] for item in catalog["distractors"]],
    }


def parse_game_file(path: Path) -> tuple[EntityConfig, InstructionRecipe]:
    """Parse a game MD file into an EntityConfig and InstructionRecipe.

    Args:
        path: Path to the markdown file with YAML frontmatter.

    Returns:
        Tuple of (EntityConfig, InstructionRecipe).
    """
    text = path.read_text()
    data = _extract_frontmatter(text)

    entity_config = _build_entity_config(data)

    step_instructions = _build_step_instruction(data["step_instructions"])

    entity_name = data["entity_name"]
    screen_frames = []
    for frame in data["screen_frames"]:
        # Inject entity into character_display widget_params so the frontend
        # can render the correct game character icon
        if frame.get("widget") == "character_display":
            params = frame.get("widget_params") or {}
            if "entity" not in params:
                params["entity"] = entity_name
                frame["widget_params"] = params
        screen_frames.append(ScreenFrame(**frame))

    celebration_frame = None
    if "celebration_frame" in data:
        celebration_frame = ScreenFrame(**data["celebration_frame"])

    metadata = RecipeMetadata(
        tier=data["tier"],
        ib_theme=data["ib_theme"],
        ib_key_concept=data["ib_key_concept"],
        concepts_earned=data.get("concepts_earned", []),
        round_count=len(step_instructions.rounds),
    )

    collection_items = _build_collection_items(data)

    recipe = InstructionRecipe(
        activity_type=data["activity_type"],
        step_instructions=step_instructions,
        screen_frames=screen_frames,
        celebration_frame=celebration_frame,
        metadata=metadata,
        photo_features=data.get("photo_features", []),
        collection_items=collection_items,
    )

    return entity_config, recipe
