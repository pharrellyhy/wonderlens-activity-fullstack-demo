"""Tests for the minimal Cat3 guided-build activity flow."""

from pathlib import Path

from game_parser import parse_game_file
from recipe_loader import load_instruction_recipe, recipe_to_session_state
from schemas.session_state import ConversationTurn
from server import _session_state_dict
from state_machine import next_step, step_needs_user_input
from turn_handling.directive import _fast_path_directive

EXPECTED_GUIDED_DRAWING_STEPS = [
    "Draw one big circle.",
    "Add two small ears or petals.",
    "Add one face/detail and say it is done.",
]


def test_cat3_state_machine_steps() -> None:
    assert next_step("STEP_1_HOOK", "cat3", 0, 3) == "STEP_2_SETUP"
    assert next_step("STEP_2_SETUP", "cat3", 0, 3) == "STEP_3_BUILD_1"
    assert next_step("STEP_3_BUILD_1", "cat3", 1, 3) == "STEP_3_BUILD_2"
    assert next_step("STEP_3_BUILD_3", "cat3", 3, 3) == "STEP_4_CELEBRATE"
    assert next_step("STEP_4_CELEBRATE", "cat3", 3, 3) == "STEP_5_CLOSING"
    assert step_needs_user_input("STEP_4_CELEBRATE") is False


def test_guided_drawing_game_parses_as_cat3() -> None:
    path = Path(__file__).parents[1] / "games" / "activity_guided_drawing.md"

    entity, recipe = parse_game_file(path)

    assert entity.activity_type == "activity_guided_drawing"
    assert entity.category == "category_3"
    assert entity.creative_slots.game_mechanic == "build"
    assert recipe.metadata.round_count == 3


def test_cat3_build_round_state_exposes_materials_and_current_build_step() -> None:
    recipe = load_instruction_recipe("activity_guided_drawing")
    state = recipe_to_session_state(recipe, "s1", "T1", "guided_drawing")
    state.current_step = "STEP_3_BUILD_2"
    state.current_round = 2

    payload = _session_state_dict(state)

    assert payload["build_materials"] == ["paper", "pencil"]
    assert state.creative_slots.build_steps == EXPECTED_GUIDED_DRAWING_STEPS
    assert payload["current_build_step"] == "Add two small ears or petals."


def test_cat3_help_stays_on_current_build_step() -> None:
    recipe = load_instruction_recipe("activity_guided_drawing")
    state = recipe_to_session_state(recipe, "s2", "T1", "guided_drawing")
    state.current_step = "STEP_3_BUILD_2"
    state.current_round = 2

    directive = _fast_path_directive("help", state)

    assert directive is not None
    assert directive.action == "stay"
    assert directive.stay_on_step is True
    direction = directive.response_direction.lower()
    assert "add two small ears or petals" in direction
    assert "same step" in direction


def test_cat3_help_repeats_last_requested_build_step_when_state_has_just_advanced() -> None:
    recipe = load_instruction_recipe("activity_guided_drawing")
    state = recipe_to_session_state(recipe, "s3", "T1", "guided_drawing")
    state.current_step = "STEP_3_BUILD_1"
    state.current_round = 1
    state.conversation_history.append(
        ConversationTurn(
            role="ai",
            text="Now we can add two tiny ears or petals to our round shape.",
            step="STEP_3_BUILD_1",
            round_number=1,
        )
    )

    directive = _fast_path_directive("help", state)

    assert directive is not None
    assert directive.action == "stay"
    assert "add two small ears or petals" in directive.response_direction.lower()


def test_cat3_setup_confirmation_cues_first_fixed_build_step() -> None:
    recipe = load_instruction_recipe("activity_guided_drawing")
    state = recipe_to_session_state(recipe, "s4", "T1", "guided_drawing")
    state.current_step = "STEP_2_SETUP"
    state.current_round = 0

    directive = _fast_path_directive("yes", state)

    assert directive is not None
    assert directive.action == "advance"
    direction = directive.response_direction.lower()
    assert "draw one big circle" in direction
    assert "done" in direction
    assert "help" in direction
    assert "what shape would you like" not in direction


def test_cat1_device_selection_advances_round() -> None:
    recipe = load_instruction_recipe("activity_recognition_pop_challenge")
    state = recipe_to_session_state(recipe, "s-sel", "T1", "recognition_pop")
    state.current_step = "STEP_3_ROUND_1"
    state.current_round = 1

    # A bare label without the selection flag is left to normal classification.
    assert _fast_path_directive("apple", state) is None

    # A confirmed device selection is the round's answer-of-record: advance.
    directive = _fast_path_directive("apple", state, is_selection=True)
    assert directive is not None
    assert directive.action == "advance"
    assert "apple" in directive.response_direction.lower()
