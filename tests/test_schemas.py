"""Tests for Pydantic schemas."""

import json
from pathlib import Path

import pytest
from game_loader import get_demo_entities, get_demo_recipe
from pydantic import ValidationError
from schemas import (
    CompositionPlan,
    InstructionRecipe,
    RecipeMetadata,
    Round,
    RoundInstruction,
    ScreenFrame,
    StepGoal,
    StepInstruction,
    VisualComposition,
    VoiceScript,
)


class TestCompositionPlan:
    def test_required_fields(self) -> None:
        plan = CompositionPlan(
            creative_brief="Test brief",
            round_count=3,
            screen_strategy="per_round",
            emotional_arc="build_excitement",
            ib_concept_integration="Weave in perspective",
            closing_concept_targets=["Perspective"],
            transition_strategy="natural_question",
        )
        assert plan.round_count == 3
        assert plan.screen_strategy == "per_round"
        assert plan.emotional_arc == "build_excitement"
        assert plan.widget_hint is None
        assert plan.modalities == ["voice", "screen"]

    def test_full_plan(self) -> None:
        plan = CompositionPlan(
            creative_brief="Guide the child on an adventure",
            modalities=["voice", "screen"],
            round_count=4,
            screen_strategy="progressive",
            widget_hint="progress_tracker",
            emotional_arc="calm_curiosity",
            ib_concept_integration="Notice patterns",
            closing_concept_targets=["Form", "Connection"],
            transition_strategy="challenge",
        )
        assert plan.round_count == 4
        assert plan.closing_concept_targets == ["Form", "Connection"]


class TestVoiceScript:
    def test_minimal_round(self) -> None:
        rnd = Round(
            prompt="What do you see?",
            correct_responses=["dog"],
            on_correct="Great!",
            on_incorrect="Try again!",
            on_silence="Are you there?",
            hint="Think about what's in the picture",
        )
        assert rnd.sfx_cue is None
        assert rnd.hint == "Think about what's in the picture"

    def test_voice_script_with_rounds(self) -> None:
        script = VoiceScript(
            hook_line="Look at your friend!",
            transition_line="Let's play!",
            rounds=[
                Round(
                    prompt="What does it say?",
                    correct_responses=["happy"],
                    on_correct="Yes!",
                    on_incorrect="Not quite!",
                    on_silence="Hello?",
                    hint="Think about feelings",
                )
            ],
            closing_speech="Great job!",
            tomorrow_hook="See you tomorrow!",
        )
        assert len(script.rounds) == 1
        assert script.hook_line == "Look at your friend!"


class TestScreenFrame:
    def test_minimal(self) -> None:
        frame = ScreenFrame(widget="photo_display", widget_params={}, trigger="on_enter")
        assert frame.animation is None
        assert frame.sfx_cue is None
        assert frame.sfx_label is None
        assert frame.animation_label is None
        assert frame.widget_label is None

    def test_with_animation(self) -> None:
        frame = ScreenFrame(
            widget="character_display",
            widget_params={"description": "scene"},
            animation="gentle_pulse",
            trigger="on_round_1",
        )
        assert frame.animation == "gentle_pulse"

    def test_with_label_fields(self) -> None:
        frame = ScreenFrame(
            widget="photo_display",
            widget_params={"entity": "dog"},
            trigger="on_enter",
            sfx_cue="wonder_chime",
            sfx_label="A magical wonder chime",
            animation_label="A gentle sparkle highlights the photo",
            widget_label="Your adventure photo",
        )
        assert frame.sfx_cue == "wonder_chime"
        assert frame.sfx_label == "A magical wonder chime"
        assert frame.animation_label == "A gentle sparkle highlights the photo"
        assert frame.widget_label == "Your adventure photo"

    def test_label_fields_serialization(self) -> None:
        frame = ScreenFrame(
            widget="badge_award",
            trigger="on_correct",
            sfx_cue="badge_awarded",
            sfx_label="Badge awarded sparkle",
            animation_label="A shining badge appears",
            widget_label="Your explorer badge",
        )
        dumped = frame.model_dump()
        assert dumped["sfx_cue"] == "badge_awarded"
        assert dumped["sfx_label"] == "Badge awarded sparkle"
        assert dumped["animation_label"] == "A shining badge appears"
        assert dumped["widget_label"] == "Your explorer badge"

    def test_label_fields_none_in_serialization(self) -> None:
        frame = ScreenFrame(widget="photo_display", trigger="on_enter")
        dumped = frame.model_dump()
        assert dumped["sfx_cue"] is None
        assert dumped["sfx_label"] is None
        assert dumped["animation_label"] is None
        assert dumped["widget_label"] is None


class TestStepInstruction:
    def test_round_instruction_defaults(self) -> None:
        instruction = RoundInstruction(
            round_number=1,
            goal="Notice how the dog feels in warm sunshine.",
            scenario="warm sunshine on belly",
            constraint="T0 max 2 sentences, invitational phrasing",
            emotion_tag="warm",
        )
        assert instruction.acceptable_themes == []
        assert instruction.escalation_note == ""

    def test_step_instruction_allows_optional_synthesis(self) -> None:
        step_instruction = StepInstruction(
            hook=StepGoal(goal="Hook", constraint="Short and warm", emotion_tag="excited"),
            transition=StepGoal(goal="Invite play", constraint="Ask gently", emotion_tag="playful"),
            rounds=[
                RoundInstruction(
                    round_number=1,
                    goal="Round one",
                    scenario="first idea",
                    constraint="Ask one playful question",
                    emotion_tag="curious",
                )
            ],
            celebrate=StepGoal(goal="Celebrate", constraint="Mention Perspective", emotion_tag="proud"),
            closing=StepGoal(goal="Close", constraint="Leave a warm hook", emotion_tag="warm"),
            early_exit=StepGoal(goal="Exit gently", constraint="No pressure", emotion_tag="gentle"),
        )
        assert step_instruction.synthesis is None
        assert step_instruction.rounds[0].round_number == 1

    def test_round_numbers_must_be_sequential(self) -> None:
        with pytest.raises(ValidationError, match="Round numbers must be sequential"):
            StepInstruction(
                hook=StepGoal(goal="Hook", constraint="Short and warm", emotion_tag="excited"),
                transition=StepGoal(goal="Invite play", constraint="Ask gently", emotion_tag="playful"),
                rounds=[
                    RoundInstruction(
                        round_number=1,
                        goal="Round one",
                        scenario="first idea",
                        constraint="Ask one playful question",
                        emotion_tag="curious",
                    ),
                    RoundInstruction(
                        round_number=3,
                        goal="Round three",
                        scenario="third idea",
                        constraint="Ask another playful question",
                        emotion_tag="excited",
                    ),
                ],
                celebrate=StepGoal(
                    goal="Celebrate",
                    constraint="Mention Perspective",
                    emotion_tag="proud",
                ),
                closing=StepGoal(goal="Close", constraint="Leave a warm hook", emotion_tag="warm"),
                early_exit=StepGoal(goal="Exit gently", constraint="No pressure", emotion_tag="gentle"),
            )


class TestInstructionRecipe:
    def test_instruction_recipe_validates(self, instruction_recipe: dict) -> None:
        recipe = InstructionRecipe.model_validate(instruction_recipe)
        assert recipe.activity_type == "mood_changer_dog"
        assert len(recipe.step_instructions.rounds) == 3
        assert len(recipe.screen_frames) == 4
        assert recipe.celebration_frame is not None
        assert recipe.metadata.tier == "T0"
        assert recipe.photo_features == ["floppy ears", "soft fur", "cute face", "fluffy body"]

    def test_round_trip_serialization(self, instruction_recipe: dict) -> None:
        recipe = InstructionRecipe.model_validate(instruction_recipe)
        dumped = json.loads(recipe.model_dump_json())
        recipe2 = InstructionRecipe.model_validate(dumped)
        assert recipe2.activity_type == recipe.activity_type
        assert len(recipe2.step_instructions.rounds) == len(recipe.step_instructions.rounds)

    def test_instruction_recipe_requires_matching_round_count(self, instruction_recipe: dict) -> None:
        instruction_recipe["metadata"]["round_count"] = 99

        with pytest.raises(ValidationError, match="metadata.round_count must match"):
            InstructionRecipe.model_validate(instruction_recipe)

    def test_collection_recipe_requires_synthesis_step(self) -> None:
        collection_recipe = {
            "activity_type": "polka_dot_patrol",
            "step_instructions": {
                "hook": {"goal": "Hook", "constraint": "Short", "emotion_tag": "excited"},
                "transition": {"goal": "Transition", "constraint": "Invite", "emotion_tag": "playful"},
                "rounds": [
                    {
                        "round_number": 1,
                        "goal": "Round one",
                        "scenario": "spots",
                        "constraint": "Ask about spots",
                        "emotion_tag": "curious",
                    }
                ],
                "celebrate": {"goal": "Celebrate", "constraint": "Be proud", "emotion_tag": "proud"},
                "closing": {"goal": "Close", "constraint": "Be warm", "emotion_tag": "warm"},
                "early_exit": {"goal": "Exit", "constraint": "Be gentle", "emotion_tag": "gentle"},
            },
            "screen_frames": [{"widget": "photo_display", "widget_params": {}, "trigger": "on_enter"}],
            "metadata": {
                "tier": "T1",
                "ib_theme": "How We Express Ourselves",
                "ib_key_concept": "Form",
                "concepts_earned": ["Form", "Connection"],
                "round_count": 1,
            },
            "photo_features": ["spots"],
            "collection_items": {"correct": ["flower"], "distractors": ["stick"]},
        }

        with pytest.raises(ValidationError, match="Collection recipes must define a synthesis step"):
            InstructionRecipe.model_validate(collection_recipe)

    def test_demo_game_recipes_validate(self) -> None:
        """Ensure all demo game MD files produce valid InstructionRecipe instances."""
        entities = get_demo_entities()
        assert len(entities) >= 5
        for entity in entities:
            recipe = get_demo_recipe(entity.activity_type)
            assert recipe is not None
            assert recipe.activity_type == entity.activity_type
            assert len(recipe.step_instructions.rounds) > 0
