"""Unit tests for the step->beat table and derive_frame in finalize."""

import inspect

from recipe_loader import load_instruction_recipe, recipe_to_session_state
from turn_handling import core as core_module
from turn_handling import directive as directive_module
from turn_handling.finalize import STEP_BEAT_TABLE, beat_for_step, derive_frame


def _state(activity_type: str, filename: str):
    recipe = load_instruction_recipe(activity_type)
    return recipe_to_session_state(recipe, "finalize-session", "T1", filename)


def test_beat_for_step_covers_all_pilot_steps() -> None:
    assert beat_for_step("STEP_1_HOOK", 0) == "intro"
    assert beat_for_step("STEP_2_RULES", 0) == "rules"
    assert beat_for_step("STEP_2_MISSION", 0) == "rules"
    assert beat_for_step("STEP_2_SETUP", 0) == "rules"
    assert beat_for_step("STEP_3_ROUND_2", 2) == "round_2"
    assert beat_for_step("STEP_3_COLLECT_1", 1) == "round_1"
    assert beat_for_step("STEP_3_BUILD_3", 3) == "round_3"
    assert beat_for_step("STEP_4_SYNTHESIS", 0) == "synthesis"
    # Distinct celebrate/closing beats — no collapse to a single "recap".
    assert beat_for_step("STEP_4_CELEBRATE", 0) == "celebrate"
    assert beat_for_step("STEP_5_CELEBRATE", 0) == "celebrate"
    assert beat_for_step("STEP_5_CLOSING", 0) == "closing"
    assert beat_for_step("STEP_6_CLOSING", 0) == "closing"
    assert beat_for_step("EARLY_EXIT", 0) == "closing"


def test_step_beat_table_has_no_celebrate_closing_collision() -> None:
    # The fixed (non-round) entries must map celebrate and closing distinctly.
    assert STEP_BEAT_TABLE["STEP_4_CELEBRATE"] == "celebrate"
    assert STEP_BEAT_TABLE["STEP_5_CELEBRATE"] == "celebrate"
    assert STEP_BEAT_TABLE["STEP_5_CLOSING"] == "closing"
    assert STEP_BEAT_TABLE["STEP_6_CLOSING"] == "closing"
    assert STEP_BEAT_TABLE["STEP_4_CELEBRATE"] != STEP_BEAT_TABLE["STEP_5_CLOSING"]


def test_derive_frame_stamps_beat_matching_current_step() -> None:
    state = _state("activity_career_decision_role_play", "career_decision_role_play")
    state.current_step = "STEP_3_ROUND_2"
    state.current_round = 2

    frame = derive_frame(state, "advance")

    assert frame.beat == "round_2"
    # derive_frame still returns a real ScreenFrame for the current step.
    assert frame.widget


def test_derive_frame_celebrate_uses_celebrate_beat_not_closing() -> None:
    state = _state("activity_phoneme_treasure_hunt", "phoneme_treasure_hunt")
    state.current_step = "STEP_5_CELEBRATE"
    state.current_round = 3

    frame = derive_frame(state, "advance")

    assert frame.beat == "celebrate"


def test_no_residual_get_screen_frame_callers_in_result_paths() -> None:
    # 1a: every TurnResult must derive its frame via finalize/derive_frame,
    # so the scattered _get_screen_frame(state) calls are gone from the
    # result-building modules.
    core_src = inspect.getsource(core_module)
    directive_src = inspect.getsource(directive_module)
    assert "_get_screen_frame(state)" not in core_src
    assert "_get_screen_frame(state)" not in directive_src
    # The two ad-hoc pre-advance snapshots are removed.
    assert "celebrate_screen_frame" not in directive_src
    assert "pre_advance_frame" not in directive_src
