"""Scenario loader and matcher for WonderLens activities."""

from pathlib import Path
from typing import Any

import yaml

try:
    from .logger import setup_logger
except ImportError:
    from logger import setup_logger

logger = setup_logger(__name__)

_SCENARIOS_DIR = Path(__file__).parent / "scenarios"
_CONTEXT_TEMPLATE_PATH = Path(__file__).parent / "skills" / "activity_context_template.md"

# Entity keywords → scenario mapping for quick matching
_ENTITY_SCENARIO_MAP: dict[str, str] = {
    "dog": "mood_changer_dog",
    "puppy": "mood_changer_dog",
    "stuffed dog": "mood_changer_dog",
    "toy dog": "mood_changer_dog",
    "cat": "dream_whisperer_cat",
    "kitten": "dream_whisperer_cat",
    "stuffed cat": "dream_whisperer_cat",
    "dinosaur": "time_machine_dinosaur",
    "dino": "time_machine_dinosaur",
    "toy dinosaur": "time_machine_dinosaur",
    "ladybug": "polka_dot_patrol",
    "ladybird": "polka_dot_patrol",
    "beetle": "polka_dot_patrol",
    "dandelion": "fluffy_expedition_dandelion",
    "flower": "fluffy_expedition_dandelion",
}

# Category mapping for default plan generation
SCENARIO_CATEGORIES: dict[str, str] = {
    "mood_changer_dog": "category_1",
    "dream_whisperer_cat": "category_1",
    "time_machine_dinosaur": "category_1",
    "polka_dot_patrol": "category_5",
    "fluffy_expedition_dandelion": "category_5",
}


def load_scenario(activity_type: str) -> dict[str, Any]:
    """Load and parse a scenario YAML file."""
    path = _SCENARIOS_DIR / f"{activity_type}.yaml"
    if not path.exists():
        logger.warning(f"Scenario file not found: {path}")
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def match_scenario(entity: str, features: list[str] | None = None) -> str:
    """Map a vision entity to the best matching scenario using keyword matching."""
    entity_lower = entity.lower().strip()

    # Direct match
    if entity_lower in _ENTITY_SCENARIO_MAP:
        return _ENTITY_SCENARIO_MAP[entity_lower]

    # Substring match
    for keyword, scenario in _ENTITY_SCENARIO_MAP.items():
        if keyword in entity_lower or entity_lower in keyword:
            return scenario

    # Feature-based matching
    if features:
        feature_text = " ".join(f.lower() for f in features)
        if any(kw in feature_text for kw in ["spot", "dot", "polka"]):
            return "polka_dot_patrol"
        if any(kw in feature_text for kw in ["fluffy", "dandelion", "soft", "fuzzy"]):
            return "fluffy_expedition_dandelion"
        if any(kw in feature_text for kw in ["plush", "stuffed", "toy"]):
            return "mood_changer_dog"

    # Default
    logger.info(f"No scenario match for entity '{entity}', defaulting to mood_changer_dog")
    return "mood_changer_dog"


def build_activity_context(scenario: dict[str, Any], vision_result: dict[str, Any]) -> str:
    """Format scenario data into the activity context string for Script Agent."""
    template = _CONTEXT_TEMPLATE_PATH.read_text() if _CONTEXT_TEMPLATE_PATH.exists() else _DEFAULT_TEMPLATE

    visual_features = scenario.get("visual_features", [])
    if isinstance(visual_features, list):
        visual_features = ", ".join(visual_features)

    key_concepts = scenario.get("key_concepts", [])
    if isinstance(key_concepts, list):
        key_concepts = ", ".join(key_concepts)

    return template.format(
        entity=vision_result.get("entity", scenario.get("entity", "unknown")),
        activity_name=scenario.get("activity_name", "Activity"),
        category=scenario.get("category", "Unknown"),
        scene=vision_result.get("scene", scenario.get("scene", "")),
        visual_features=visual_features,
        key_concepts=key_concepts,
        activity_steps_summary=scenario.get("activity_steps_summary", ""),
        detailed_interaction_script=scenario.get("detailed_interaction_script", ""),
    )


_DEFAULT_TEMPLATE = """## Entity
{entity}

## Activity
{activity_name} ({category})

## Scene
{scene}

## Visual Features
{visual_features}

## Key Concepts
{key_concepts}

## Activity Steps
{activity_steps_summary}

## Detailed Interaction Script
{detailed_interaction_script}
"""
