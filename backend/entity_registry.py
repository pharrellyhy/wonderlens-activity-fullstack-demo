"""Single source of truth for all entity configuration.

Every demo entity is defined once here. Other modules import lookup helpers
instead of maintaining their own hardcoded dicts.
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

_RECIPES_DIR = Path(__file__).parent / "recipes"
_SCENARIOS_DIR = Path(__file__).parent / "scenarios"


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


# --- Registry data ---

ENTITY_REGISTRY: list[EntityConfig] = [
    # --- Category 1: In-Device Verbal ---
    EntityConfig(
        activity_type="mood_changer_dog",
        category="category_1",
        entity_name="dog",
        demo_filename="dog.png",
        display_label="Stuffed Dog",
        icon_src="/icons/dog.png",
        keywords=["dog", "puppy", "stuffed dog", "toy dog"],
        feature_keywords=["plush", "stuffed", "toy"],
        creative_slots=Cat1CreativeSlots(
            game_mechanic="voice_acting",
            metaphor="This fluffy dog friend has so many feelings inside!",
            role_title="Emotion Translator",
            round_scenarios=["warm sunshine on belly", "tripped and went bump", "favorite treat arrives"],
            escalation_axis="comfortable to excited",
            observation_detail="those cute floppy ears and super soft fur",
        ),
    ),
    EntityConfig(
        activity_type="dream_whisperer_cat",
        category="category_1",
        entity_name="cat",
        demo_filename="cat.png",
        display_label="Cat",
        icon_src="/icons/cat.png",
        keywords=["cat", "kitten", "stuffed cat"],
        feature_keywords=["plush", "stuffed", "toy"],
        creative_slots=Cat1CreativeSlots(
            game_mechanic="storytelling_chain",
            metaphor="This sleepy cat is dreaming the most magical dreams!",
            role_title="Dream Whisperer",
            round_scenarios=[
                "floating on a cloud in the sky",
                "swimming in a milk ocean",
                "magical garden of favorites",
            ],
            escalation_axis="familiar to fantastical",
            observation_detail="those soft little paws and fluffy fur",
        ),
    ),
    EntityConfig(
        activity_type="time_machine_dinosaur",
        category="category_1",
        entity_name="dinosaur",
        demo_filename="dinosaur.png",
        display_label="Dinosaur",
        icon_src="/icons/dinosaur.png",
        keywords=["dinosaur", "dino", "toy dinosaur"],
        feature_keywords=["plush", "stuffed", "toy"],
        creative_slots=Cat1CreativeSlots(
            game_mechanic="voice_acting",
            metaphor="This amazing dinosaur has traveled through all of history!",
            role_title="Time Traveler",
            round_scenarios=["prehistoric jungle", "rumbling volcano", "peaceful lake at sunset"],
            escalation_axis="everyday to dramatic to peaceful",
            observation_detail="those big teeth and powerful legs",
        ),
    ),
    # --- Category 5: Out-of-Device Collection ---
    EntityConfig(
        activity_type="polka_dot_patrol",
        category="category_5",
        entity_name="ladybug",
        demo_filename="ladybug.png",
        display_label="Ladybug",
        icon_src="/icons/ladybug.png",
        keywords=["ladybug", "ladybird", "beetle"],
        feature_keywords=["spot", "dot", "polka"],
        creative_slots=Cat5CreativeSlots(
            observation_angle="pattern",
            collection_criterion="Find things with dots, spots, or circles",
            collection_count=3,
            mission_metaphor="You are a Polka-Dot Patrol Officer!",
            role_title="Polka-Dot Patrol Officer",
            synthesis_type="comparison_chart",
            stuck_hint="Try looking at flowers up close, or at the ground near your feet",
            naming_prompt="What kind of dots or spots do you see on this?",
        ),
        collection_catalog=CollectionCatalog(
            correct=[
                CollectionItem(id="spotted_mushroom", label="Spotted mushroom", image="/icons/spotted_mushroom.png"),
                CollectionItem(id="dotted_pebble", label="Dotted pebble", image="/icons/dotted_pebble.png"),
                CollectionItem(id="speckled_leaf", label="Speckled leaf", image="/icons/speckled_leaf.png"),
                CollectionItem(id="circle_flower", label="Flower with circles", image="/icons/circle_flower.png"),
            ],
            distractors=[
                CollectionItem(id="straight_stick", label="Straight stick", image="/icons/straight_stick.png"),
                CollectionItem(id="plain_bark", label="Plain bark", image="/icons/plain_bark.png"),
                CollectionItem(id="long_grass", label="Long grass blade", image="/icons/long_grass.png"),
                CollectionItem(id="smooth_stone", label="Smooth stone", image="/icons/smooth_stone.png"),
                CollectionItem(id="pine_needle", label="Pine needles", image="/icons/pine_needle.png"),
                CollectionItem(id="plain_leaf", label="Plain leaf", image="/icons/plain_leaf.png"),
                CollectionItem(id="forked_twig", label="Forked twig", image="/icons/forked_twig.png"),
                CollectionItem(id="acorn_cap", label="Acorn cap", image="/icons/acorn_cap.png"),
            ],
        ),
    ),
    EntityConfig(
        activity_type="fluffy_expedition_dandelion",
        category="category_5",
        entity_name="dandelion",
        demo_filename="dandelion.png",
        display_label="Dandelion",
        icon_src="/icons/dandelion.png",
        keywords=["dandelion", "flower"],
        feature_keywords=["fluffy", "dandelion", "soft", "fuzzy"],
        creative_slots=Cat5CreativeSlots(
            observation_angle="texture",
            collection_criterion="Find things that are fluffy, fuzzy, or soft",
            collection_count=3,
            mission_metaphor="You are a Fluffy Expedition Explorer!",
            role_title="Fluffy Expedition Explorer",
            synthesis_type="naming_story",
            stuck_hint="Try touching things around you — look for anything soft or fuzzy",
            naming_prompt="What would you name this fluffy friend?",
        ),
        collection_catalog=CollectionCatalog(
            correct=[
                CollectionItem(id="fuzzy_moss", label="Fuzzy moss", image="/icons/fuzzy_moss.png"),
                CollectionItem(id="fluffy_seed", label="Fluffy seed head", image="/icons/fluffy_seed.png"),
                CollectionItem(id="soft_petal", label="Soft petal", image="/icons/soft_petal.png"),
                CollectionItem(
                    id="woolly_caterpillar", label="Woolly caterpillar", image="/icons/woolly_caterpillar.png"
                ),
            ],
            distractors=[
                CollectionItem(id="hard_rock", label="Hard rock", image="/icons/hard_rock.png"),
                CollectionItem(id="spiky_pinecone", label="Spiky pinecone", image="/icons/spiky_pinecone.png"),
                CollectionItem(id="rough_bark", label="Rough bark", image="/icons/rough_bark.png"),
                CollectionItem(id="sharp_thorn", label="Sharp thorn", image="/icons/sharp_thorn.png"),
                CollectionItem(id="dry_leaf", label="Dry crunchy leaf", image="/icons/dry_leaf.png"),
                CollectionItem(id="smooth_pebble", label="Smooth pebble", image="/icons/smooth_pebble.png"),
                CollectionItem(id="stiff_branch", label="Stiff branch", image="/icons/stiff_branch.png"),
                CollectionItem(id="brittle_shell", label="Brittle shell", image="/icons/brittle_shell.png"),
            ],
        ),
    ),
]


# --- Derived lookups (built at module load time) ---

_BY_ACTIVITY_TYPE: dict[str, EntityConfig] = {e.activity_type: e for e in ENTITY_REGISTRY}
_BY_DEMO_FILENAME: dict[str, EntityConfig] = {e.demo_filename.lower(): e for e in ENTITY_REGISTRY}
_KEYWORD_MAP: dict[str, str] = {}
for _entity in ENTITY_REGISTRY:
    for _kw in _entity.keywords:
        _KEYWORD_MAP[_kw] = _entity.activity_type

SCENARIO_CATEGORIES: dict[str, str] = {e.activity_type: e.category for e in ENTITY_REGISTRY}

# Feature keyword groups: maps each feature keyword to its activity_type
_FEATURE_KEYWORD_MAP: dict[str, str] = {}
for _entity in ENTITY_REGISTRY:
    for _fkw in _entity.feature_keywords:
        # First entity to claim a feature keyword wins (order matters for default fallback)
        if _fkw not in _FEATURE_KEYWORD_MAP:
            _FEATURE_KEYWORD_MAP[_fkw] = _entity.activity_type


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


def all_entities_for_api() -> list[dict]:
    """Return entity data structured for the frontend /api/entities endpoint."""
    categories: dict[str, dict] = {}
    for entity in ENTITY_REGISTRY:
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
            }
        )
    # Return in stable order: cat1 first, then cat5
    result = []
    for key in ["cat1", "cat5"]:
        if key in categories:
            result.append(categories[key])
    return result


def validate_registry() -> None:
    """Validate that all registered entities have required files on disk.

    Raises ValueError if any entity is missing its recipe JSON or scenario YAML,
    or if a cat5 entity lacks a collection catalog.
    """
    errors: list[str] = []
    for entity in ENTITY_REGISTRY:
        recipe_path = _RECIPES_DIR / f"{entity.activity_type}.json"
        if not recipe_path.exists():
            errors.append(f"Missing recipe: {recipe_path}")

        scenario_path = _SCENARIOS_DIR / f"{entity.activity_type}.yaml"
        if not scenario_path.exists():
            errors.append(f"Missing scenario: {scenario_path}")

        if entity.category == "category_5" and not entity.collection_catalog:
            errors.append(f"Cat5 entity '{entity.activity_type}' missing collection_catalog")

        if not entity.keywords:
            errors.append(f"Entity '{entity.activity_type}' has no keywords")

    if errors:
        raise ValueError("Entity registry validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    logger.info(f"Entity registry validated: {len(ENTITY_REGISTRY)} entities OK")
