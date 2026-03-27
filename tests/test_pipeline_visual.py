"""Tests for pipeline Visual Agent integration — parallel execution and state storage."""

from unittest.mock import AsyncMock, patch

import pytest
from agents.pipeline import initialize_session
from schemas import CompositionPlan, ScreenFrame, VisualComposition
from schemas.creative_slots import Cat1CreativeSlots
from schemas.session_state import SessionStateModel
from schemas.turn_response import TurnResponse


def _mock_plan() -> CompositionPlan:
    return CompositionPlan(
        creative_brief="Test activity",
        round_count=2,
        screen_strategy="per_round",
        emotional_arc="build_excitement",
        ib_concept_integration="Perspective",
        closing_concept_targets=["Perspective"],
        transition_strategy="natural_question",
        template_type="cat1",
        creative_slots=Cat1CreativeSlots(
            game_mechanic="what_would_it_say",
            metaphor="This dog has stories!",
            role_title="Dog Whisperer",
            round_scenarios=["napping", "at a party"],
            escalation_axis="everyday to fantastical",
            observation_detail="floppy ears",
        ),
    )


def _mock_visual_result() -> VisualComposition:
    return VisualComposition(
        screen_frames=[
            ScreenFrame(
                widget="photo_display",
                trigger="on_enter",
                sfx_cue="wonder_chime",
                sfx_label="A magical wonder chime",
                widget_label="Your dog adventure photo",
            ),
            ScreenFrame(
                widget="character_display",
                trigger="on_round_1",
                sfx_cue="game_start_chime",
                sfx_label="Game start chime",
                widget_label="Round 1 with your dog",
            ),
        ],
        celebration_frame=ScreenFrame(
            widget="badge_award",
            trigger="on_correct",
            sfx_cue="badge_awarded",
            sfx_label="Badge awarded sparkle",
            widget_label="Your explorer badge",
        ),
    )


def _mock_hook_turn() -> TurnResponse:
    return TurnResponse(
        dialogue="Wow, look at that dog!",
        tone_marker="excited",
        screen_widget="photo_display",
        screen_widget_params={"entity": "dog"},
        screen_animation="sparkle_highlight",
        sfx_cue="wonder_chime",
    )


class TestPipelineVisualIntegration:
    async def test_visual_frames_stored_in_session_state(self, sample_context: dict) -> None:
        plan = _mock_plan()
        visual_result = _mock_visual_result()
        hook_turn = _mock_hook_turn()

        with (
            patch("agents.pipeline.DirectorAgent.run", new=AsyncMock(return_value=plan)),
            patch("agents.pipeline.ScriptAgent.generate_turn", new=AsyncMock(return_value=hook_turn)),
            patch("agents.pipeline.VisualAgent.run", new=AsyncMock(return_value=visual_result)),
        ):
            state, first_turn = await initialize_session(sample_context, "test-sess")

        assert len(state.visual_frames) == 2
        assert state.visual_frames[0].widget == "photo_display"
        assert state.visual_frames[0].sfx_label == "A magical wonder chime"
        assert state.visual_frames[1].widget == "character_display"
        assert state.celebration_frame is not None
        assert state.celebration_frame.widget == "badge_award"
        assert state.celebration_frame.sfx_label == "Badge awarded sparkle"

    async def test_visual_failure_does_not_break_session(self, sample_context: dict) -> None:
        plan = _mock_plan()
        hook_turn = _mock_hook_turn()

        with (
            patch("agents.pipeline.DirectorAgent.run", new=AsyncMock(return_value=plan)),
            patch("agents.pipeline.ScriptAgent.generate_turn", new=AsyncMock(return_value=hook_turn)),
            patch("agents.pipeline.VisualAgent.run", new=AsyncMock(side_effect=RuntimeError("LLM down"))),
        ):
            state, first_turn = await initialize_session(sample_context, "test-sess")

        # Visual Agent failure should not block session
        assert first_turn.dialogue == "Wow, look at that dog!"
        assert state.visual_frames == []
        assert state.celebration_frame is None

    async def test_script_and_visual_run_concurrently(self, sample_context: dict) -> None:
        """Verify both agents are called (not that one blocks the other)."""
        plan = _mock_plan()
        visual_result = _mock_visual_result()
        hook_turn = _mock_hook_turn()

        visual_mock = AsyncMock(return_value=visual_result)
        script_mock = AsyncMock(return_value=hook_turn)

        with (
            patch("agents.pipeline.DirectorAgent.run", new=AsyncMock(return_value=plan)),
            patch("agents.pipeline.ScriptAgent.generate_turn", new=script_mock),
            patch("agents.pipeline.VisualAgent.run", new=visual_mock),
        ):
            state, first_turn = await initialize_session(sample_context, "test-sess")

        # Both should have been called
        visual_mock.assert_called_once()
        script_mock.assert_called_once()

    async def test_session_state_defaults_when_no_visual_agent(self) -> None:
        """SessionStateModel defaults to empty visual_frames."""
        state = SessionStateModel(
            session_id="test",
            tier="T0",
            template_type="cat1",
            activity_type="mood_changer_dog",
            current_step="STEP_1_HOOK",
            creative_slots=Cat1CreativeSlots(
                game_mechanic="what_would_it_say",
                metaphor="Stories",
                role_title="Whisperer",
                round_scenarios=["napping"],
                escalation_axis="everyday",
                observation_detail="ears",
            ),
        )
        assert state.visual_frames == []
        assert state.celebration_frame is None
