import pytest
from agents.script_agent import ScriptAgentError
from recipe_loader import load_instruction_recipe, recipe_to_session_state
from turn_handling.generation import _generate_with_retry


class FailingScriptAgent:
    last_plan = None

    async def generate_turn(self, _state):
        raise ScriptAgentError("provider unavailable")

    async def retry_speaker_turn(self, *_args, **_kwargs):
        raise ScriptAgentError("provider unavailable")


@pytest.mark.asyncio
async def test_source_fidelity_fallback_uses_current_activity_recipe() -> None:
    recipe = load_instruction_recipe("activity_career_decision_role_play")
    state = recipe_to_session_state(recipe, "fallback-session", "T1", "career_decision_role_play")

    response, debug = await _generate_with_retry(FailingScriptAgent(), state, is_first_on_step=True)

    assert debug.final_verdict == "error_fallback"
    assert state.status == "active"
    assert "firefighter" in response.dialogue.lower()
    assert "is ready: career decision role play" not in response.dialogue.lower()
    assert "doctor" not in response.dialogue.lower()
    assert "builder" not in response.dialogue.lower()
    assert "teacher" not in response.dialogue.lower()
    assert response.screen_widget == state.visual_frames[0].widget
