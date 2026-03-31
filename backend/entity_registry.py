"""Single source of truth for all entity configuration.

Demo entities are loaded from game MD files in backend/games/ via game_loader.
Other modules import lookup helpers instead of maintaining their own data.
"""

import random
from pathlib import Path

from pydantic import BaseModel

try:
    from .schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots, CreativeSlots
except ImportError:
    from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots, CreativeSlots

try:
    from .logger import setup_logger
except ImportError:
    from logger import setup_logger

logger = setup_logger(__name__)

_GAMES_DIR = Path(__file__).parent / "games"


# --- Pydantic models ---


class CollectionItem(BaseModel):
    """A single item in a Cat 5 collection catalog."""

    id: str
    label: str
    image: str


class CollectionCatalog(BaseModel):
    """Correct items and distractors for a Cat 5 collection activity."""

    correct: list[CollectionItem]
    distractors: list[CollectionItem]


class EntityConfig(BaseModel):
    """Complete configuration for a single demo entity."""

    activity_type: str
    category: str
    entity_name: str
    demo_filename: str
    display_label: str
    icon_src: str
    keywords: list[str]
    feature_keywords: list[str]
    creative_slots: CreativeSlots
    collection_catalog: CollectionCatalog | None = None
    tier: str = ""
    ib_theme: str = ""
    ib_key_concept: str = ""
    concepts_earned: list[str] = []
    plain_description: str = ""
    steps_summary: list[str] = []
    play_rounds: int | None = None


# --- Registry data (populated by game_loader at import time) ---

ENTITY_REGISTRY: list[EntityConfig] = []


def _populate_registry(entities: list[EntityConfig]) -> None:
    """Replace the registry contents with entities from game_loader."""
    ENTITY_REGISTRY.clear()
    ENTITY_REGISTRY.extend(entities)
    _rebuild_lookups()


# --- Derived lookups (rebuilt when registry is populated) ---

_BY_ACTIVITY_TYPE: dict[str, EntityConfig] = {}
_BY_DEMO_FILENAME: dict[str, EntityConfig] = {}
_KEYWORD_MAP: dict[str, str] = {}
SCENARIO_CATEGORIES: dict[str, str] = {}
_FEATURE_KEYWORD_MAP: dict[str, str] = {}


def _rebuild_lookups() -> None:
    """Rebuild all derived lookup dicts from the current ENTITY_REGISTRY."""
    _BY_ACTIVITY_TYPE.clear()
    _BY_DEMO_FILENAME.clear()
    _KEYWORD_MAP.clear()
    SCENARIO_CATEGORIES.clear()
    _FEATURE_KEYWORD_MAP.clear()

    for entity in ENTITY_REGISTRY:
        _BY_ACTIVITY_TYPE[entity.activity_type] = entity
        _BY_DEMO_FILENAME[entity.demo_filename.lower()] = entity
        SCENARIO_CATEGORIES[entity.activity_type] = entity.category
        # Always register entity_name as a keyword for direct matching
        _KEYWORD_MAP[entity.entity_name] = entity.activity_type
        for kw in entity.keywords:
            _KEYWORD_MAP[kw] = entity.activity_type
        for fkw in entity.feature_keywords:
            if fkw not in _FEATURE_KEYWORD_MAP:
                _FEATURE_KEYWORD_MAP[fkw] = entity.activity_type


# --- Public API ---


def get_entity(activity_type: str) -> EntityConfig:
    """Look up an entity config by activity type."""
    entity = _BY_ACTIVITY_TYPE.get(activity_type)
    if not entity:
        raise KeyError(f"Unknown activity type: {activity_type}")
    return entity


def get_creative_slots(activity_type: str) -> CreativeSlots:
    """Return creative slots for an activity type."""
    return get_entity(activity_type).creative_slots


def get_collection_catalog(activity_type: str) -> CollectionCatalog | None:
    """Return collection catalog for an activity type (None for cat1)."""
    return get_entity(activity_type).collection_catalog


def get_category(activity_type: str) -> str:
    """Return the category string for an activity type."""
    return get_entity(activity_type).category


def is_demo_entity(filename: str) -> bool:
    """Check if the filename matches a demo entity."""
    return filename.lower() in _BY_DEMO_FILENAME


def entity_name_for_filename(filename: str) -> str:
    """Return the entity name for a demo filename, or 'object' if not found."""
    entity = _BY_DEMO_FILENAME.get(filename.lower())
    return entity.entity_name if entity else "object"


def keyword_to_activity_type(keyword: str) -> str | None:
    """Map a keyword to its activity type, or None if not found."""
    return _KEYWORD_MAP.get(keyword.lower())


def get_keyword_map() -> dict[str, str]:
    """Return the full keyword → activity_type map (for scenarios.py matching)."""
    return _KEYWORD_MAP


def get_feature_keyword_map() -> dict[str, str]:
    """Return feature keyword → activity_type map (for feature-based matching)."""
    return _FEATURE_KEYWORD_MAP


def lookup_by_entity_name(entity_name: str) -> EntityConfig | None:
    """Look up an entity config by entity name (case-insensitive), with keyword fallback."""
    name_lower = entity_name.lower().strip()
    for entity in ENTITY_REGISTRY:
        if entity.entity_name.lower() == name_lower:
            return entity
    activity_type = _KEYWORD_MAP.get(name_lower)
    if activity_type:
        return _BY_ACTIVITY_TYPE.get(activity_type)
    return None


def generate_round_items(activity_type: str, total_rounds: int) -> list[list[dict]]:
    """Generate per-round item sets: 1 correct + 2 distractors per round."""
    entity = _BY_ACTIVITY_TYPE.get(activity_type)
    if not entity or not entity.collection_catalog:
        return []
    catalog = entity.collection_catalog
    correct = [item.model_dump() for item in catalog.correct]
    distractors = [item.model_dump() for item in catalog.distractors]
    random.shuffle(correct)
    random.shuffle(distractors)

    rounds: list[list[dict]] = []
    dist_idx = 0
    for r in range(total_rounds):
        correct_item = {**correct[r % len(correct)], "correct": True}
        items: list[dict] = [correct_item]
        items.extend(distractors[dist_idx : dist_idx + 2])
        dist_idx += 2
        random.shuffle(items)
        rounds.append(items)
    return rounds


_TIER_META = {
    "T0": {"label": "Sensory Explorer", "ages": "2–4"},
    "T1": {"label": "Function Discoverer", "ages": "4–6"},
    "T2": {"label": "System Thinker", "ages": "6–8"},
}


def _build_entity_summary(entity: EntityConfig) -> dict:
    """Build a summary payload for the game detail view."""
    slots = entity.creative_slots
    tier_info = _TIER_META.get(entity.tier, {"label": entity.tier, "ages": ""})

    summary: dict = {
        "category": entity.category,
        "tier": entity.tier,
        "ages": tier_info["ages"],
        "tierLabel": tier_info["label"],
        "ib_theme": entity.ib_theme,
        "ib_key_concept": entity.ib_key_concept,
        "concepts_earned": entity.concepts_earned,
        "role_title": slots.role_title,
        "plain_description": entity.plain_description,
        "steps_summary": entity.steps_summary,
    }

    if isinstance(slots, Cat1CreativeSlots):
        summary.update(
            {
                "metaphor": slots.metaphor,
                "game_mechanic": slots.game_mechanic,
                "round_count": entity.play_rounds if entity.play_rounds is not None else len(slots.round_scenarios),
                "round_scenarios": slots.round_scenarios[: entity.play_rounds]
                if entity.play_rounds is not None
                else slots.round_scenarios,
                "escalation_axis": slots.escalation_axis,
                "collection_criterion": None,
                "collection_count": None,
                "synthesis_type": None,
                "observation_angle": None,
                "collectible_previews": None,
            }
        )
    elif isinstance(slots, Cat5CreativeSlots):
        previews = []
        if entity.collection_catalog:
            previews = [{"label": item.label, "image": item.image} for item in entity.collection_catalog.correct]
        summary.update(
            {
                "metaphor": slots.mission_metaphor,
                "game_mechanic": None,
                "round_count": slots.collection_count,
                "round_scenarios": None,
                "escalation_axis": None,
                "collection_criterion": slots.collection_criterion,
                "collection_count": slots.collection_count,
                "synthesis_type": slots.synthesis_type,
                "observation_angle": slots.observation_angle,
                "collectible_previews": previews,
            }
        )

    return summary


_DEMO_ENTITIES = {"dog", "cat", "dinosaur", "dandelion", "ladybug"}


def all_entities_for_api() -> list[dict]:
    """Return entity data structured for the frontend /api/entities endpoint."""
    categories: dict[str, dict] = {}
    for entity in ENTITY_REGISTRY:
        if entity.entity_name not in _DEMO_ENTITIES:
            continue
        cat_id = "cat1" if entity.category == "category_1" else "cat5"
        if cat_id not in categories:
            if cat_id == "cat1":
                categories[cat_id] = {
                    "id": "cat1",
                    "title": "In-Device Verbal",
                    "subtitle": "Imagine stories with your photo friend!",
                    "photos": [],
                }
            else:
                categories[cat_id] = {
                    "id": "cat5",
                    "title": "Out-of-Device Collection",
                    "subtitle": "Go on a real-world scavenger hunt!",
                    "photos": [],
                }
        categories[cat_id]["photos"].append(
            {
                "id": entity.entity_name,
                "label": entity.display_label,
                "src": entity.icon_src,
                "summary": _build_entity_summary(entity),
            }
        )
    # Return in stable order: cat1 first, then cat5
    result = []
    for key in ["cat1", "cat5"]:
        if key in categories:
            result.append(categories[key])
    return result


def validate_registry() -> None:
    """Validate that all registered entities have required game MD files on disk.

    Raises ValueError if any entity is missing its game MD source file,
    or if a cat5 entity lacks a collection catalog.
    """
    errors: list[str] = []
    if not ENTITY_REGISTRY:
        errors.append("Entity registry is empty")

    for entity in ENTITY_REGISTRY:
        game_path = _GAMES_DIR / f"{entity.activity_type}.md"
        if not game_path.exists():
            errors.append(f"Missing game MD: {game_path}")

        if entity.category == "category_5" and not entity.collection_catalog:
            errors.append(f"Cat5 entity '{entity.activity_type}' missing collection_catalog")

    if errors:
        raise ValueError("Entity registry validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    logger.info(f"Entity registry validated: {len(ENTITY_REGISTRY)} entities OK")
