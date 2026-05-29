"""Turn-by-turn frame-sync test: screen_frame.beat matches the line spoken now."""

import pytest
from config import get_settings
from recipe_loader import load_instruction_recipe, recipe_to_session_state
from schemas.turn_response import TurnResponse
from turn_handling.core import resolve_turn
from turn_handling.finalize import beat_for_step
from turn_handling.types import TurnInput


class StubScriptAgent:
    """Deterministic ScriptAgent — never calls the provider."""

    last_plan = None
    last_best_of_n = None

    async def generate_turn(self, state) -> TurnResponse:
        return TurnResponse(
            dialogue=f"[gentle] line for {state.current_step}",
            tone_marker="gentle",
            screen_widget="photo_display",
            screen_widget_params={},
        )

    async def retry_speaker_turn(self, *_args, **_kwargs) -> TurnResponse:
        return await self.generate_turn(_args[0])

    async def generate_turn_from_directive(self, state, directive) -> TurnResponse:
        return TurnResponse(
            dialogue=f"[{directive.emotion_tag}] line for {state.current_step}",
            tone_marker=directive.emotion_tag,
            screen_widget=directive.screen_widget,
            screen_widget_params=directive.screen_widget_params,
            stay_on_step=directive.stay_on_step,
        )


@pytest.fixture()
def director_enabled():
    settings = get_settings()
    previous = settings.turn_director_enabled
    settings.turn_director_enabled = True
    yield
    settings.turn_director_enabled = previous


@pytest.mark.asyncio
async def test_cat1_career_frame_matches_spoken_line(director_enabled) -> None:
    recipe = load_instruction_recipe("activity_career_decision_role_play")
    state = recipe_to_session_state(recipe, "frame-cat1", "T1", "career_decision_role_play")
    agent = StubScriptAgent()

    # Hook -> rules
    result = await resolve_turn(state, TurnInput(text="yes"), agent)
    assert result.screen_frame.beat == beat_for_step(state.current_step, state.current_round)

    # Rules -> round 1
    result = await resolve_turn(state, TurnInput(text="yes"), agent)
    assert result.screen_frame.beat == beat_for_step(state.current_step, state.current_round)
    assert result.screen_frame.beat in {"round_1", "rules"}
