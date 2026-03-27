"""Unit tests for story synthesis loop components."""

import pytest
from pydantic import ValidationError
from schemas.creative_slots import Cat5CreativeSlots
from schemas.session_state import SessionStateModel
from schemas.story_classification import StoryClassification


class TestStoryClassification:
    """Test StoryClassification schema validation."""

    def test_valid_story_attempt_good(self) -> None:
        result = StoryClassification(
            classification="story_attempt",
            is_related_to_collection=True,
            story_quality="good",
        )
        assert result.classification == "story_attempt"
        assert result.story_quality == "good"

    def test_valid_story_attempt_weak(self) -> None:
        result = StoryClassification(
            classification="story_attempt",
            is_related_to_collection=True,
            story_quality="weak",
        )
        assert result.story_quality == "weak"

    def test_valid_decline(self) -> None:
        result = StoryClassification(
            classification="decline",
            is_related_to_collection=False,
            story_quality=None,
        )
        assert result.classification == "decline"
        assert result.story_quality is None

    def test_valid_ask_ai(self) -> None:
        result = StoryClassification(
            classification="ask_ai",
            is_related_to_collection=False,
        )
        assert result.classification == "ask_ai"

    def test_valid_unrelated(self) -> None:
        result = StoryClassification(
            classification="unrelated",
            is_related_to_collection=False,
        )
        assert result.classification == "unrelated"

    def test_invalid_classification(self) -> None:
        with pytest.raises(ValidationError):
            StoryClassification(
                classification="invalid_type",
                is_related_to_collection=False,
            )

    def test_invalid_quality(self) -> None:
        with pytest.raises(ValidationError):
            StoryClassification(
                classification="story_attempt",
                is_related_to_collection=True,
                story_quality="excellent",
            )


class TestSynthesisSessionState:
    """Test synthesis-related session state fields."""

    def test_default_synthesis_fields(self) -> None:
        slots = Cat5CreativeSlots(
            observation_angle="texture",
            collection_criterion="soft things",
            collection_count=3,
            mission_metaphor="Fluffy Expedition",
            role_title="Fluffy Explorer",
            stuck_hint="Look near the ground",
            naming_prompt="What should we call this one?",
        )

        state = SessionStateModel(
            session_id="test-123",
            tier="T1",
            template_type="cat5",
            activity_type="fluffy_expedition_dandelion",
            current_step="STEP_4_SYNTHESIS",
            creative_slots=slots,
        )

        assert state.synthesis_phase == "invite"
        assert state.synthesis_prompt_count == 0
        assert state.synthesis_child_story == ""

    def test_synthesis_phase_transitions(self) -> None:
        slots = Cat5CreativeSlots(
            observation_angle="texture",
            collection_criterion="soft things",
            collection_count=3,
            mission_metaphor="Fluffy Expedition",
            role_title="Fluffy Explorer",
            stuck_hint="Look near the ground",
            naming_prompt="What should we call this one?",
        )

        state = SessionStateModel(
            session_id="test-456",
            tier="T1",
            template_type="cat5",
            activity_type="fluffy_expedition_dandelion",
            current_step="STEP_4_SYNTHESIS",
            creative_slots=slots,
        )

        # Simulate phase transitions
        state.synthesis_phase = "evaluate"
        state.synthesis_prompt_count = 1
        assert state.synthesis_phase == "evaluate"

        state.synthesis_phase = "improve"
        state.synthesis_child_story = "the dog went to sleep"
        assert state.synthesis_child_story == "the dog went to sleep"

        state.synthesis_phase = "generate"
        assert state.synthesis_phase == "generate"
