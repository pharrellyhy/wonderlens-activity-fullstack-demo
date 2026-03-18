"""Scenario loader and matcher for WonderLens activities."""

from pathlib import Path
from typing import Any

import yaml

try:
    from .entity_registry import SCENARIO_CATEGORIES, get_feature_keyword_map, get_keyword_map
    from .logger import setup_logger
except ImportError:
    from entity_registry import SCENARIO_CATEGORIES, get_feature_keyword_map, get_keyword_map
    from logger import setup_logger

logger = setup_logger(__name__)

_SCENARIOS_DIR = Path(__file__).parent / "scenarios"
_CONTEXT_TEMPLATE_PATH = Path(__file__).parent / "skills" / "activity_context_template.md"

# Re-export for backward compatibility (used by director.py, pipeline.py, recipe_loader.py)
__all__ = ["SCENARIO_CATEGORIES", "load_scenario", "match_scenario", "build_activity_context"]


def load_scenario(activity_type: str) -> dict[str, Any]:
    """Load and parse a scenario YAML file."""
    path = _SCENARIOS_DIR / f"{activity_type}.yaml"
    if not path.exists():
        logger.warning(f"Scenario file not found: {path}")
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def match_scenario(entity: str, features: list[str] | None = None, filename: str = "") -> str:
    """Map a vision entity to the best matching scenario using keyword matching."""
    entity_lower = entity.lower().strip()
    keyword_map = get_keyword_map()

    # Direct match
    if entity_lower in keyword_map:
        return keyword_map[entity_lower]

    # Substring match
    for keyword, scenario in keyword_map.items():
        if keyword in entity_lower or entity_lower in keyword:
            return scenario

    # Feature-based matching
    if features:
        feature_text = " ".join(f.lower() for f in features)
        feature_keyword_map = get_feature_keyword_map()
        for fkw, activity_type in feature_keyword_map.items():
            if fkw in feature_text:
                return activity_type

    # Filename-based fallback (e.g., "ladybug.jpg" → "ladybug")
    if filename:
        name_lower = Path(filename).stem.lower()
        for keyword, scenario in keyword_map.items():
            if keyword in name_lower:
                logger.info(f"Matched scenario from filename '{filename}': {scenario}")
                return scenario

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
