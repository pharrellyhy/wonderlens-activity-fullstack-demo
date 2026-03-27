"""Focused tests for the prod-doc frontmatter generator."""

import importlib.util
import re
import sys
from pathlib import Path

import pytest
import yaml
from schemas.creative_slots import Cat1CreativeSlots

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_game_frontmatter.py"
PROD_GAMES_DIR = REPO_ROOT / "backend" / "games"

_has_prod_files = bool(sorted(PROD_GAMES_DIR.glob("*_prod.md")))


def _load_generator_module():
    spec = importlib.util.spec_from_file_location("generate_game_frontmatter", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


GENERATOR = _load_generator_module()


def _parse_generated_frontmatter(prod_path: Path, tmp_path: Path) -> dict:
    output_path = tmp_path / f"{prod_path.stem}_generated.md"
    GENERATOR.process_prod_file(prod_path, output_path)
    text = output_path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    assert match is not None
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict)
    return data


@pytest.mark.skipif(not _has_prod_files, reason="No *_prod.md files in backend/games/")
def test_all_prod_docs_generate_parseable_yaml_frontmatter(tmp_path: Path) -> None:
    prod_paths = sorted(PROD_GAMES_DIR.glob("*_prod.md"))
    assert prod_paths

    for prod_path in prod_paths:
        data = _parse_generated_frontmatter(prod_path, tmp_path)
        assert data["activity_type"]
        assert data["entity_name"]
        assert data["step_instructions"]
        assert data["screen_frames"]


@pytest.mark.skipif(
    not (PROD_GAMES_DIR / "stop_sign_cat1_prod.md").exists(),
    reason="stop_sign_cat1_prod.md not present",
)
def test_stop_sign_extracts_awarded_role_title(tmp_path: Path) -> None:
    data = _parse_generated_frontmatter(PROD_GAMES_DIR / "stop_sign_cat1_prod.md", tmp_path)

    assert data["creative_slots"]["role_title"] == "Safety Solver"
    assert data["celebration_frame"]["widget_params"]["title"] == "Safety Solver"


@pytest.mark.skipif(
    not (PROD_GAMES_DIR / "lion_cat5_prod.md").exists(),
    reason="lion_cat5_prod.md not present",
)
def test_lion_extracts_descriptive_collection_criterion(tmp_path: Path) -> None:
    data = _parse_generated_frontmatter(PROD_GAMES_DIR / "lion_cat5_prod.md", tmp_path)

    assert data["creative_slots"]["collection_criterion"] == "Find things that look big, strong, or tough"


@pytest.mark.skipif(
    not (PROD_GAMES_DIR / "piano_cat5_prod.md").exists(),
    reason="piano_cat5_prod.md not present",
)
def test_cat5_mission_metaphor_falls_back_to_role_title(tmp_path: Path) -> None:
    data = _parse_generated_frontmatter(PROD_GAMES_DIR / "piano_cat5_prod.md", tmp_path)

    assert data["creative_slots"]["mission_metaphor"] == "You are a Sound Detective!"


def test_new_cat1_mechanics_are_valid_schema_values() -> None:
    common_kwargs = {
        "metaphor": "Playful frame",
        "role_title": "Helper",
        "round_scenarios": ["one", "two", "three"],
        "escalation_axis": "harder each round",
        "observation_detail": "bright detail",
    }

    prediction = Cat1CreativeSlots(game_mechanic="prediction_game", **common_kwargs)
    hotline = Cat1CreativeSlots(game_mechanic="helper_hotline", **common_kwargs)

    assert prediction.game_mechanic == "prediction_game"
    assert hotline.game_mechanic == "helper_hotline"
