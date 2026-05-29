"""Tests for the minimal Cat3 guided-build activity flow."""

from pathlib import Path

from game_parser import parse_game_file
from schemas.creative_slots import Cat3CreativeSlots
from schemas.session_state import SessionStateModel
from server import _session_state_dict
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


def test_cat3_build_round_state_exposes_materials_and_current_build_step() -> None:
    state = SessionStateModel(
        session_id="s1",
        tier="T1",
        template_type="cat3",
        activity_type="activity_guided_drawing",
        current_step="STEP_3_BUILD_2",
        current_round=2,
        total_rounds=3,
        interaction_mode="text",
        creative_slots=Cat3CreativeSlots(
            game_mechanic="build",
            metaphor="Grow a drawing one small step at a time.",
            role_title="Guided Artist",
            build_materials=["paper", "pencil"],
            build_steps=[
                "Draw one simple line or shape to start the picture.",
                "Add one small detail that changes what the picture could become.",
                "Choose one finishing mark and describe the finished drawing.",
            ],
            escalation_axis="single mark to changed drawing to finished recap",
            observation_detail="a first line or shape that can change into a drawing",
        ),
    )

    payload = _session_state_dict(state)

    assert payload["build_materials"] == ["paper", "pencil"]
    assert payload["current_build_step"] == "Add one small detail that changes what the picture could become."
