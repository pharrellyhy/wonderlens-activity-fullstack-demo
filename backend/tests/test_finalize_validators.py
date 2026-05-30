"""Unit tests for Stream 2 guardrail validators in finalize_turn."""

import pytest
from agents.script_agent import _build_instruction_overlay
from recipe_loader import load_instruction_recipe, recipe_to_session_state
from schemas.turn_plan import TurnPlan
from schemas.turn_response import TurnResponse
from turn_handling.finalize import (
    _scaffold_t0_line,
    _t0_needs_scaffold,
    _violates_contract,
    _violates_flow,
    finalize_turn,
)
from turn_handling.generation import (
    _generate_with_retry,
    _has_completion_language,
    _source_fidelity_fallback_response,
)


class _StubAgent:
    last_plan = None
    last_best_of_n = None

    def __init__(self, replies):
        self._replies = list(replies)

    async def generate_turn(self, state):
        return self._replies.pop(0)

    async def retry_speaker_turn(self, *_a, **_k):
        return self._replies.pop(0)


def _career_state(step: str, current_round: int):
    recipe = load_instruction_recipe("activity_career_decision_role_play")
    state = recipe_to_session_state(recipe, "validator-a", "T1", "career_decision_role_play")
    state.current_step = step
    state.current_round = current_round
    return state


def test_violates_contract_flags_item_suggestion_when_do_not_suggest() -> None:
    state = _career_state("STEP_3_ROUND_1", 1)
    bad = TurnResponse(
        dialogue="[gentle] Go find a pillow and a sock to fight the fire!",
        tone_marker="gentle",
        screen_widget="photo_display",
        screen_widget_params={},
    )
    assert _violates_contract(state, bad, do_not_suggest_items=True) is True


def test_violates_contract_allows_in_role_firefighter_line() -> None:
    state = _career_state("STEP_3_ROUND_1", 1)
    good = TurnResponse(
        dialogue="[gentle] You are the firefighter. Should your team send help now, or check first?",
        tone_marker="gentle",
        screen_widget="photo_display",
        screen_widget_params={},
    )
    assert _violates_contract(state, good, do_not_suggest_items=True) is False


@pytest.mark.asyncio
async def test_finalize_regenerates_then_falls_back_on_contract_divergence() -> None:
    state = _career_state("STEP_3_ROUND_1", 1)
    bad = TurnResponse(
        dialogue="[gentle] Go grab a teddy and a marble!",
        tone_marker="gentle",
        screen_widget="photo_display",
        screen_widget_params={},
    )
    # First (the bad line passed in) -> regen returns another bad line ->
    # finalize must fall back to the deterministic recipe response.
    agent = _StubAgent([bad])  # one corrective regen attempt
    turn, frame = await finalize_turn(state, bad, action="stay", script_agent=agent, do_not_suggest_items=True)
    # Deterministic fallback is recipe-grounded (firefighter), not a leaked item line.
    assert "teddy" not in turn.dialogue.lower()
    assert "marble" not in turn.dialogue.lower()
    assert frame.beat == "round_1"


def test_completion_regex_catches_creative_variants() -> None:
    assert _has_completion_language("Wow, all 3 spotted!") is True
    assert _has_completion_language("The search is over, friend!") is True
    assert _has_completion_language("Let's find the next one!") is False


def test_violates_flow_flags_advance_language_on_stay() -> None:
    state = _career_state("STEP_3_ROUND_1", 1)
    moving_on = TurnResponse(
        dialogue="[gentle] Great, let's move on to the next part!",
        tone_marker="gentle",
        screen_widget="photo_display",
        screen_widget_params={},
        stay_on_step=True,
    )
    assert _violates_flow(state, moving_on, action="stay") is True


def test_violates_flow_allows_stay_without_advance_language() -> None:
    state = _career_state("STEP_3_ROUND_1", 1)
    staying = TurnResponse(
        dialogue="[gentle] Take your time — should the team send help now or check first?",
        tone_marker="gentle",
        screen_widget="photo_display",
        screen_widget_params={},
        stay_on_step=True,
    )
    assert _violates_flow(state, staying, action="stay") is False


@pytest.mark.asyncio
async def test_finalize_sanitizes_device_words_in_text_mode() -> None:
    state = _career_state("STEP_3_ROUND_1", 1)
    state.interaction_mode = "text"
    leaky = TurnResponse(
        dialogue="[gentle] Tap the card when you decide!",
        tone_marker="gentle",
        screen_widget="photo_display",
        screen_widget_params={},
        stay_on_step=True,
    )
    turn, _frame = await finalize_turn(state, leaky, action="stay")
    lower = turn.dialogue.lower()
    assert "tap" not in lower
    assert "card" not in lower


def test_overlay_example_ai_line_sanitized_in_text_mode() -> None:
    recipe = load_instruction_recipe("activity_phoneme_treasure_hunt")
    state = recipe_to_session_state(recipe, "overlay-text", "T1", "phoneme_treasure_hunt", interaction_mode="text")
    state.current_step = "STEP_3_COLLECT_1"
    state.current_round = 1

    overlay = _build_instruction_overlay(state)

    # The example line, if it carried a device word, is sanitized before it
    # reaches the model as an "official example."
    assert "tap" not in overlay.lower()
    assert " card " not in overlay.lower()


class _ExhaustingAgent:
    """Always returns a line that fails plan validation, never raises."""

    last_plan = TurnPlan()
    last_best_of_n = None

    async def generate_turn(self, state):
        # An item-suggestion line that _validate_plan rejects when
        # do_not_suggest_items is on (Cat5 collection detail).
        return TurnResponse(
            dialogue="[gentle] Go find a pillow and a sock!",
            tone_marker="gentle",
            screen_widget="photo_display",
            screen_widget_params={},
        )

    async def retry_speaker_turn(self, *_a, **_k):
        return await self.generate_turn(_a[0])


@pytest.mark.asyncio
async def test_exhaustion_returns_deterministic_fallback_not_last_bad_line() -> None:
    recipe = load_instruction_recipe("activity_phoneme_treasure_hunt")
    state = recipe_to_session_state(recipe, "exhaust", "T1", "phoneme_treasure_hunt")
    state.current_step = "STEP_3_COLLECT_2"
    state.current_round = 2
    state.collection_phase = "detail"
    state.collected_photos = ["text_find_1"]
    state.collected_names = ["Fluffy", "Bouncy"]

    response, debug = await _generate_with_retry(_ExhaustingAgent(), state)

    assert debug.final_verdict == "exhausted"
    # Not the last bad line.
    assert "pillow" not in response.dialogue.lower()
    assert "sock" not in response.dialogue.lower()


def test_fallback_response_uses_collected_names_not_generic_friends() -> None:
    recipe = load_instruction_recipe("activity_phoneme_treasure_hunt")
    state = recipe_to_session_state(recipe, "names", "T1", "phoneme_treasure_hunt")
    state.current_step = "STEP_5_CELEBRATE"
    state.collected_names = ["Fluffy", "Bouncy"]

    response = _source_fidelity_fallback_response(state)

    lower = response.dialogue.lower()
    assert "fluffy" in lower and "bouncy" in lower
    assert "our friends" not in lower
    # Celebrate fallback reads like a closing, not a start.
    assert "is ready:" not in lower
    assert "what should we try" not in lower


def test_t0_needs_scaffold_flags_open_question_without_model_phrase() -> None:
    assert _t0_needs_scaffold("[gentle] How does the dog feel right now?") is True


def test_t0_needs_scaffold_passes_with_model_phrase_or_binary_question() -> None:
    # A recognized scaffold present anywhere clears it.
    assert _t0_needs_scaffold("[gentle] It sounds like fun. How does the dog feel?") is False
    # A binary/non-wh question is not an open question.
    assert _t0_needs_scaffold("[gentle] Should the team go left or right?") is False


def test_scaffold_t0_line_inserts_recognized_phrase_before_first_question() -> None:
    line = "[gentle] What do you see? How does the dog feel?"
    lead = "It sounds like a lot is happening right now."
    scaffolded = _scaffold_t0_line(line, 0)
    assert scaffolded.startswith("[gentle]")  # tone marker preserved
    # Idempotent: the scaffolded line no longer needs scaffolding.
    assert _t0_needs_scaffold(scaffolded) is False
    # The scaffold lands before the FIRST question, not between the two.
    assert lead in scaffolded
    assert scaffolded.index(lead) < scaffolded.index("What do you see?")


def test_scaffold_t0_line_rotates_lead_by_round() -> None:
    line = "[gentle] How does the dog feel?"
    leads = {_scaffold_t0_line(line, r) for r in range(3)}
    assert len(leads) == 3  # three distinct rounds -> three distinct leads


@pytest.mark.asyncio
async def test_finalize_scaffolds_t0_round_open_question() -> None:
    state = _career_state("STEP_3_ROUND_1", 1)
    state.tier = "T0"
    open_line = TurnResponse(
        dialogue="[gentle] How does the firefighter feel right now?",
        tone_marker="gentle",
        screen_widget="photo_display",
        screen_widget_params={},
    )
    turn, _frame = await finalize_turn(state, open_line, action="advance")
    assert _t0_needs_scaffold(turn.dialogue) is False


@pytest.mark.asyncio
async def test_finalize_scaffold_inert_at_t1() -> None:
    state = _career_state("STEP_3_ROUND_1", 1)
    state.tier = "T1"
    open_line = TurnResponse(
        dialogue="[gentle] How does the firefighter feel right now?",
        tone_marker="gentle",
        screen_widget="photo_display",
        screen_widget_params={},
    )
    turn, _frame = await finalize_turn(state, open_line, action="advance")
    assert turn.dialogue == open_line.dialogue  # unchanged at T1
