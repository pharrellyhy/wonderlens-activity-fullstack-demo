"""Tests for the Visual Agent — async LLM-based with rule-based fallback."""

from unittest.mock import AsyncMock, patch

import pytest
from agents.visual_agent import (
    ACTIVITY_WIDGET_MAP,
    ALLOWED_SFX,
    ALLOWED_WIDGETS,
    EMOTIONAL_ARC_ANIMATION,
    SFX_LABELS,
    VisualAgent,
    _validate_composition,
)
from schemas import CompositionPlan, ScreenFrame, VisualComposition


def _make_plan(**overrides: object) -> CompositionPlan:
    defaults: dict = {
        "creative_brief": "Test",
        "round_count": 3,
        "screen_strategy": "per_round",
        "emotional_arc": "build_excitement",
        "ib_concept_integration": "Weave in perspective",
        "closing_concept_targets": ["Perspective"],
        "transition_strategy": "natural_question",
    }
    defaults.update(overrides)
    return CompositionPlan(**defaults)


# ---------- Constants / lookups ----------


class TestConstants:
    def test_allowed_widgets_has_six_entries(self) -> None:
        assert len(ALLOWED_WIDGETS) == 6
        assert "photo_display" in ALLOWED_WIDGETS
        assert "badge_award" in ALLOWED_WIDGETS
        assert "explorer_map" in ALLOWED_WIDGETS

    def test_allowed_sfx_has_ten_entries(self) -> None:
        assert len(ALLOWED_SFX) == 10
        assert "wonder_chime" in ALLOWED_SFX
        assert "badge_awarded" in ALLOWED_SFX

    def test_sfx_labels_covers_all_allowed_sfx(self) -> None:
        for sfx in ALLOWED_SFX:
            assert sfx in SFX_LABELS, f"Missing SFX_LABELS entry for {sfx}"
            assert isinstance(SFX_LABELS[sfx], str)
            assert len(SFX_LABELS[sfx]) > 0

    def test_widget_map_cat1(self) -> None:
        for activity in ["mood_changer_dog", "dream_whisperer_cat", "time_machine_dinosaur"]:
            assert ACTIVITY_WIDGET_MAP[activity] == "character_display"

    def test_widget_map_cat5(self) -> None:
        for activity in ["polka_dot_patrol", "fluffy_expedition_dandelion"]:
            assert ACTIVITY_WIDGET_MAP[activity] == "progress_tracker"

    def test_emotional_arc_animations(self) -> None:
        for arc in ["build_excitement", "calm_curiosity", "playful_surprise", "gentle_wonder"]:
            assert arc in EMOTIONAL_ARC_ANIMATION


# ---------- _validate_composition ----------


class TestValidateComposition:
    def test_valid_composition_passes_through(self) -> None:
        comp = VisualComposition(
            screen_frames=[
                ScreenFrame(widget="photo_display", trigger="on_enter", sfx_cue="wonder_chime"),
            ],
            celebration_frame=ScreenFrame(widget="badge_award", trigger="on_correct", sfx_cue="badge_awarded"),
        )
        result = _validate_composition(comp)
        assert result.screen_frames[0].widget == "photo_display"
        assert result.screen_frames[0].sfx_cue == "wonder_chime"
        assert result.celebration_frame.widget == "badge_award"

    def test_invalid_widget_replaced_with_photo_display(self) -> None:
        comp = VisualComposition(
            screen_frames=[
                ScreenFrame(widget="bogus_widget", trigger="on_enter"),
            ],
        )
        result = _validate_composition(comp)
        assert result.screen_frames[0].widget == "photo_display"

    def test_invalid_sfx_cleared(self) -> None:
        comp = VisualComposition(
            screen_frames=[
                ScreenFrame(
                    widget="photo_display",
                    trigger="on_enter",
                    sfx_cue="nonexistent_sound",
                    sfx_label="Should be removed",
                ),
            ],
        )
        result = _validate_composition(comp)
        assert result.screen_frames[0].sfx_cue is None
        assert result.screen_frames[0].sfx_label is None

    def test_invalid_celebration_widget_replaced(self) -> None:
        comp = VisualComposition(
            screen_frames=[],
            celebration_frame=ScreenFrame(widget="fake_widget", trigger="on_correct"),
        )
        result = _validate_composition(comp)
        assert result.celebration_frame.widget == "badge_award"

    def test_invalid_celebration_sfx_cleared(self) -> None:
        comp = VisualComposition(
            screen_frames=[],
            celebration_frame=ScreenFrame(
                widget="badge_award",
                trigger="on_correct",
                sfx_cue="fake_sfx",
                sfx_label="Should go away",
            ),
        )
        result = _validate_composition(comp)
        assert result.celebration_frame.sfx_cue is None
        assert result.celebration_frame.sfx_label is None

    def test_none_sfx_cue_not_cleared(self) -> None:
        comp = VisualComposition(
            screen_frames=[
                ScreenFrame(widget="photo_display", trigger="on_enter", sfx_cue=None),
            ],
        )
        result = _validate_composition(comp)
        assert result.screen_frames[0].sfx_cue is None


# ---------- Rule-based fallback ----------


class TestRuleBasedFallback:
    def setup_method(self) -> None:
        self.agent = VisualAgent()

    def test_per_round_strategy_frame_count(self, sample_context: dict) -> None:
        plan = _make_plan(round_count=3, screen_strategy="per_round")
        result = self.agent._rule_based_fallback(plan, sample_context)
        # 1 photo frame + 3 round frames = 4
        assert len(result.screen_frames) == 4

    def test_per_round_entry_frame(self, sample_context: dict) -> None:
        plan = _make_plan(round_count=2, screen_strategy="per_round")
        result = self.agent._rule_based_fallback(plan, sample_context)
        entry = result.screen_frames[0]
        assert entry.widget == "photo_display"
        assert entry.trigger == "on_enter"
        assert entry.sfx_cue == "wonder_chime"
        assert entry.sfx_label == SFX_LABELS["wonder_chime"]
        assert entry.animation_label is not None
        assert entry.widget_label is not None
        assert "dog" in entry.widget_label

    def test_per_round_frames_have_labels(self, sample_context: dict) -> None:
        plan = _make_plan(round_count=3, screen_strategy="per_round")
        result = self.agent._rule_based_fallback(plan, sample_context)
        for frame in result.screen_frames:
            assert frame.sfx_cue is not None, f"Frame {frame.trigger} missing sfx_cue"
            assert frame.sfx_label is not None, f"Frame {frame.trigger} missing sfx_label"
            assert frame.animation_label is not None, f"Frame {frame.trigger} missing animation_label"
            assert frame.widget_label is not None, f"Frame {frame.trigger} missing widget_label"

    def test_per_round_triggers(self, sample_context: dict) -> None:
        plan = _make_plan(round_count=3, screen_strategy="per_round")
        result = self.agent._rule_based_fallback(plan, sample_context)
        assert result.screen_frames[0].trigger == "on_enter"
        assert result.screen_frames[1].trigger == "on_round_1"
        assert result.screen_frames[2].trigger == "on_round_2"
        assert result.screen_frames[3].trigger == "on_round_3"

    def test_per_round_first_round_sfx_is_game_start(self, sample_context: dict) -> None:
        plan = _make_plan(round_count=2, screen_strategy="per_round")
        result = self.agent._rule_based_fallback(plan, sample_context)
        assert result.screen_frames[1].sfx_cue == "game_start_chime"

    def test_per_round_subsequent_rounds_sfx_is_scene_woosh(self, sample_context: dict) -> None:
        plan = _make_plan(round_count=3, screen_strategy="per_round")
        result = self.agent._rule_based_fallback(plan, sample_context)
        assert result.screen_frames[2].sfx_cue == "scene_woosh"
        assert result.screen_frames[3].sfx_cue == "scene_woosh"

    def test_progressive_strategy(self) -> None:
        plan = _make_plan(round_count=3, screen_strategy="progressive", widget_hint="progress_tracker")
        context = {"activity_type": "polka_dot_patrol", "entity": "ladybug", "key_concepts": ["Form"]}
        result = self.agent._rule_based_fallback(plan, context)
        # 1 photo frame + 3 progressive frames
        assert len(result.screen_frames) == 4
        assert result.screen_frames[1].widget == "progress_tracker"
        assert result.screen_frames[1].widget_params.get("filled") == 1
        assert result.screen_frames[1].sfx_cue == "slot_fill_chime"

    def test_progressive_last_round_sfx_is_celebration(self) -> None:
        plan = _make_plan(round_count=2, screen_strategy="progressive", widget_hint="progress_tracker")
        context = {"activity_type": "polka_dot_patrol", "entity": "ladybug"}
        result = self.agent._rule_based_fallback(plan, context)
        last_round = result.screen_frames[-1]
        assert last_round.sfx_cue == "celebration_fanfare"

    def test_static_strategy(self) -> None:
        plan = _make_plan(round_count=3, screen_strategy="static", emotional_arc="calm_curiosity")
        context = {"activity_type": "mood_changer_dog", "entity": "dog"}
        result = self.agent._rule_based_fallback(plan, context)
        # 1 photo frame + 1 static frame
        assert len(result.screen_frames) == 2
        assert result.screen_frames[1].sfx_cue == "game_start_chime"

    def test_celebration_frame(self, sample_context: dict) -> None:
        plan = _make_plan(round_count=2, emotional_arc="gentle_wonder")
        result = self.agent._rule_based_fallback(plan, sample_context)
        celeb = result.celebration_frame
        assert celeb is not None
        assert celeb.widget == "badge_award"
        assert celeb.sfx_cue == "badge_awarded"
        assert celeb.sfx_label == SFX_LABELS["badge_awarded"]
        assert celeb.animation_label is not None
        assert celeb.widget_label == "Your explorer badge"

    def test_celebration_frame_concepts(self) -> None:
        plan = _make_plan(round_count=2, emotional_arc="gentle_wonder")
        context = {"entity": "cat", "key_concepts": ["Perspective", "Empathy"]}
        result = self.agent._rule_based_fallback(plan, context)
        assert result.celebration_frame.widget_params["concepts"] == ["Perspective", "Empathy"]

    def test_all_sfx_cues_are_in_allowed_set(self, sample_context: dict) -> None:
        for strategy in ["per_round", "progressive", "static"]:
            plan = _make_plan(round_count=3, screen_strategy=strategy, widget_hint="progress_tracker")
            result = self.agent._rule_based_fallback(plan, sample_context)
            for frame in result.screen_frames:
                if frame.sfx_cue:
                    assert frame.sfx_cue in ALLOWED_SFX, f"Invalid SFX: {frame.sfx_cue}"
            if result.celebration_frame and result.celebration_frame.sfx_cue:
                assert result.celebration_frame.sfx_cue in ALLOWED_SFX

    def test_all_widgets_are_in_allowed_set(self, sample_context: dict) -> None:
        plan = _make_plan(round_count=3, screen_strategy="per_round")
        result = self.agent._rule_based_fallback(plan, sample_context)
        for frame in result.screen_frames:
            assert frame.widget in ALLOWED_WIDGETS
        if result.celebration_frame:
            assert result.celebration_frame.widget in ALLOWED_WIDGETS


# ---------- Async run() — LLM success + fallback ----------


class TestVisualAgentRun:
    @pytest.fixture()
    def agent(self) -> VisualAgent:
        return VisualAgent()

    async def test_run_falls_back_on_llm_failure(self, agent: VisualAgent, sample_context: dict) -> None:
        plan = _make_plan(round_count=2, screen_strategy="per_round")
        with patch.object(agent, "_llm_generate", new=AsyncMock(side_effect=Exception("LLM unavailable"))):
            with patch("agents.visual_agent.log_agent_call", new=AsyncMock()):
                result = await agent.run(plan, sample_context)

        # Fallback should produce valid frames: 1 photo + round_count rounds
        assert len(result.screen_frames) == 3
        assert result.screen_frames[0].widget == "photo_display"
        assert result.celebration_frame is not None

    async def test_run_returns_llm_result_when_valid(self, agent: VisualAgent) -> None:
        plan = _make_plan(round_count=2, screen_strategy="per_round")
        context = {"entity": "dog", "activity_type": "mood_changer_dog"}

        llm_result = VisualComposition(
            screen_frames=[
                ScreenFrame(
                    widget="photo_display",
                    trigger="on_enter",
                    sfx_cue="wonder_chime",
                    sfx_label="A magical chime",
                    widget_label="Your photo",
                ),
            ],
            celebration_frame=ScreenFrame(widget="badge_award", trigger="on_correct"),
        )

        with patch.object(agent, "_llm_generate", new=AsyncMock(return_value=llm_result)):
            with patch("agents.visual_agent.log_agent_call", new=AsyncMock()):
                result = await agent.run(plan, context)

        assert len(result.screen_frames) == 1
        assert result.screen_frames[0].sfx_label == "A magical chime"

    async def test_run_validates_llm_output(self, agent: VisualAgent) -> None:
        plan = _make_plan(round_count=2, screen_strategy="per_round")
        context = {"entity": "dog", "activity_type": "mood_changer_dog"}

        # LLM returns an invalid widget — should be corrected by validation
        llm_result = VisualComposition(
            screen_frames=[
                ScreenFrame(widget="invalid_widget", trigger="on_enter", sfx_cue="bad_sfx", sfx_label="Bad"),
            ],
        )

        with patch.object(agent, "_llm_generate", new=AsyncMock(return_value=llm_result)):
            with patch("agents.visual_agent.log_agent_call", new=AsyncMock()):
                result = await agent.run(plan, context)

        # Widget corrected, sfx cleared
        assert result.screen_frames[0].widget == "photo_display"
        assert result.screen_frames[0].sfx_cue is None
        assert result.screen_frames[0].sfx_label is None

    async def test_run_logs_agent_call_on_success(self, agent: VisualAgent) -> None:
        plan = _make_plan(round_count=2, screen_strategy="per_round")
        context = {"entity": "dog"}

        llm_result = VisualComposition(
            screen_frames=[ScreenFrame(widget="photo_display", trigger="on_enter")],
        )

        mock_log = AsyncMock()
        with patch.object(agent, "_llm_generate", new=AsyncMock(return_value=llm_result)):
            with patch("agents.visual_agent.log_agent_call", new=mock_log):
                await agent.run(plan, context, session_id="sess-123")

        mock_log.assert_called_once()
        call_args = mock_log.call_args
        assert call_args[0][0] == "sess-123"
        assert call_args[0][1] == "visual"
        assert call_args[0][3] is True  # success

    async def test_run_logs_agent_call_on_failure(self, agent: VisualAgent) -> None:
        plan = _make_plan(round_count=2, screen_strategy="per_round")
        context = {"entity": "dog"}

        mock_log = AsyncMock()
        with patch.object(agent, "_llm_generate", new=AsyncMock(side_effect=RuntimeError("timeout"))):
            with patch("agents.visual_agent.log_agent_call", new=mock_log):
                await agent.run(plan, context, session_id="sess-456")

        mock_log.assert_called()
        # First call is the failure log
        fail_call = mock_log.call_args_list[0]
        assert fail_call[0][3] is False  # success=False
