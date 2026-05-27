"""Tests for the minimal Cat3 guided-build activity flow."""

from pathlib import Path

from game_parser import parse_game_file
from state_machine import next_step, step_needs_user_input


def test_cat3_state_machine_steps() -> None:
    assert next_step("STEP_1_HOOK", "cat3", 0, 3) == "STEP_2_SETUP"
    assert next_step("STEP_2_SETUP", "cat3", 0, 3) == "STEP_3_BUILD_1"
    assert next_step("STEP_3_BUILD_1", "cat3", 1, 3) == "STEP_3_BUILD_2"
    assert next_step("STEP_3_BUILD_3", "cat3", 3, 3) == "STEP_4_CELEBRATE"
    assert next_step("STEP_4_CELEBRATE", "cat3", 3, 3) == "STEP_5_CLOSING"
    assert step_needs_user_input("STEP_4_CELEBRATE") is False


def test_guided_drawing_game_parses_as_cat3() -> None:
    path = Path("backend/games/activity_guided_drawing.md")

    entity, recipe = parse_game_file(path)

    assert entity.activity_type == "activity_guided_drawing"
    assert entity.category == "category_3"
    assert entity.creative_slots.game_mechanic == "build"
    assert recipe.metadata.round_count == 3
