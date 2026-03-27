"""Shared test fixtures for the WonderLens Activity Demo."""

import sys
from pathlib import Path

import pytest

# Ensure backend/ is importable when running from repo root
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import game_loader  # noqa: E402, F401 — triggers demo game loading + registry population
from game_loader import get_demo_recipe  # noqa: E402


@pytest.fixture()
def instruction_recipe() -> dict:
    recipe = get_demo_recipe("mood_changer_dog")
    assert recipe is not None
    return recipe.model_dump()


@pytest.fixture()
def sample_context() -> dict:
    return {
        "entity": "dog",
        "tier": "T0",
        "activity_type": "mood_changer_dog",
        "scene": "stuffed dog on a bed",
        "features": ["floppy ears", "soft fur"],
        "key_concepts": ["Perspective"],
        "ib_theme": "Who We Are",
    }


@pytest.fixture()
def sample_vision_result() -> dict:
    return {
        "entity": "dog",
        "confidence": 0.95,
        "scene": "stuffed toy dog on a bed",
        "features": ["floppy ears", "soft fur", "plush toy"],
    }
