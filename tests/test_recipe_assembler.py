"""Tests for the Recipe Assembler."""

import pytest

from agents.recipe_assembler import ALLOWED_SFX, RecipeAssembler
from schemas import CompositionPlan, Round, ScreenFrame, VisualComposition, VoiceScript


def _make_voice_script(
    hook_line: str = "Look at your friend!",
    round_count: int = 2,
    sfx_cue: str | None = "wonder_chime",
) -> VoiceScript:
    return VoiceScript(
        hook_line=hook_line,
        transition_line="Let's play!",
        rounds=[
            Round(
                prompt=f"Round {i + 1}",
                correct_responses=["yes"],
                on_correct="Great!",
                on_incorrect="Try again!",
                on_silence="Hello?",
                hint="Think about it",
                sfx_cue=sfx_cue,
            )
            for i in range(round_count)
        ],
        closing_speech="Well done!",
        tomorrow_hook="See you!",
    )


def _make_visuals(frame_count: int = 3) -> VisualComposition:
    frames = [
        ScreenFrame(widget="photo_display", widget_params={}, trigger="on_enter"),
    ]
    for i in range(1, frame_count):
        frames.append(
            ScreenFrame(widget="character_display", widget_params={}, trigger=f"on_round_{i}"),
        )
    return VisualComposition(
        screen_frames=frames,
        celebration_frame=ScreenFrame(widget="badge_award", widget_params={}, trigger="on_correct"),
    )


def _make_plan(**overrides: object) -> CompositionPlan:
    defaults: dict = {
        "creative_brief": "Test",
        "round_count": 2,
        "screen_strategy": "per_round",
        "emotional_arc": "build_excitement",
        "ib_concept_integration": "Weave in perspective",
        "closing_concept_targets": ["Perspective"],
        "transition_strategy": "natural_question",
    }
    defaults.update(overrides)
    return CompositionPlan(**defaults)


class TestRecipeAssembler:
    def setup_method(self) -> None:
        self.assembler = RecipeAssembler()

    def test_basic_merge(self, sample_context: dict) -> None:
        script = _make_voice_script(round_count=2)
        visuals = _make_visuals(frame_count=3)
        plan = _make_plan()
        recipe = self.assembler.merge(script, visuals, plan, sample_context)

        assert recipe.activity_type == "mood_changer_dog"
        assert len(recipe.voice_script.rounds) == 2
        assert recipe.metadata.tier == "T0"

    def test_frame_padding(self, sample_context: dict) -> None:
        """When rounds > frames, assembler should pad frames."""
        script = _make_voice_script(round_count=4)
        visuals = _make_visuals(frame_count=2)  # Only 2 frames, need 5 (1 photo + 4 rounds)
        plan = _make_plan(round_count=4)
        recipe = self.assembler.merge(script, visuals, plan, sample_context)

        # Should have been padded to at least round_count + 1
        assert len(recipe.screen_frames) >= 5

    def test_hook_rule_rejects_factual_question(self, sample_context: dict) -> None:
        script = _make_voice_script(hook_line="How many spots do you see?")
        visuals = _make_visuals()
        plan = _make_plan()

        with pytest.raises(ValueError, match="factual question"):
            self.assembler.merge(script, visuals, plan, sample_context)

    def test_hook_rule_allows_emotional_question(self, sample_context: dict) -> None:
        script = _make_voice_script(hook_line="Isn't your friend so cute?")
        visuals = _make_visuals()
        plan = _make_plan()
        recipe = self.assembler.merge(script, visuals, plan, sample_context)
        assert recipe is not None

    def test_invalid_sfx_set_to_null(self, sample_context: dict) -> None:
        script = _make_voice_script(sfx_cue="invalid_sound_xyz")
        visuals = _make_visuals()
        plan = _make_plan()
        recipe = self.assembler.merge(script, visuals, plan, sample_context)

        for rnd in recipe.voice_script.rounds:
            assert rnd.sfx_cue is None

    def test_valid_sfx_preserved(self, sample_context: dict) -> None:
        script = _make_voice_script(sfx_cue="celebration_fanfare")
        visuals = _make_visuals()
        plan = _make_plan()
        recipe = self.assembler.merge(script, visuals, plan, sample_context)

        for rnd in recipe.voice_script.rounds:
            assert rnd.sfx_cue == "celebration_fanfare"

    def test_allowed_sfx_set(self) -> None:
        expected = {
            "wonder_chime",
            "excitement_rising",
            "photo_shutter_click",
            "slot_fill_chime",
            "mission_accepted",
            "mission_complete_fanfare",
            "celebration_fanfare",
            "badge_awarded",
            "scene_woosh",
            "game_start_chime",
        }
        assert ALLOWED_SFX == expected

    def test_metadata_populated(self, sample_context: dict) -> None:
        script = _make_voice_script()
        visuals = _make_visuals()
        plan = _make_plan(closing_concept_targets=["Perspective"])
        recipe = self.assembler.merge(script, visuals, plan, sample_context)

        assert recipe.metadata.ib_theme == "Who We Are"
        assert recipe.metadata.ib_key_concept == "Perspective"
        assert recipe.metadata.concepts_earned == ["Perspective"]
