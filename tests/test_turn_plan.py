"""Tests for the TurnPlan schema."""

import json

from schemas import TurnPlan


class TestTurnPlanDefaults:
    """Test construction with all defaults — only required fields provided."""

    def test_minimal_construction(self) -> None:
        plan = TurnPlan(child_said="found a flower", child_emotion="excited")
        assert plan.child_said == "found a flower"
        assert plan.child_emotion == "excited"

    def test_optional_content_fields_default_none(self) -> None:
        plan = TurnPlan(child_said="silence", child_emotion="silent")
        assert plan.celebrate_item is None
        assert plan.progress_note is None
        assert plan.sensory_observation is None
        assert plan.question_type is None
        assert plan.story_beat is None

    def test_list_fields_default_empty(self) -> None:
        plan = TurnPlan(child_said="hello", child_emotion="neutral")
        assert plan.name_choices == []
        assert plan.characters_to_reference == []

    def test_constraint_defaults(self) -> None:
        plan = TurnPlan(child_said="hello", child_emotion="neutral")
        assert plan.must_model_first is False
        assert plan.offer_binary_choice is False
        assert plan.do_not_suggest_items is True
        assert plan.do_not_ask_question is False
        assert plan.stay_on_step is False

    def test_tone_and_format_defaults(self) -> None:
        plan = TurnPlan(child_said="hello", child_emotion="neutral")
        assert plan.emotion_tag == "excited"
        assert plan.tone_guidance == ""
        assert plan.max_sentences == 2

    def test_screen_audio_defaults(self) -> None:
        plan = TurnPlan(child_said="hello", child_emotion="neutral")
        assert plan.screen_widget == "photo_display"
        assert plan.screen_widget_params == {}
        assert plan.screen_animation is None
        assert plan.sfx_cue is None
        assert plan.child_intent is None


class TestTurnPlanFull:
    """Test construction with all fields explicitly set."""

    def test_full_construction(self) -> None:
        plan = TurnPlan(
            child_said="I found a spotty leaf!",
            child_emotion="excited",
            celebrate_item="spotty leaf",
            progress_note="That's your second find!",
            sensory_observation="It has tiny bumps all over — feels like braille dots",
            name_choices=["Bumpy", "Dotsworth"],
            characters_to_reference=["Sir Spots"],
            question_type="tactile",
            story_beat=None,
            must_model_first=False,
            offer_binary_choice=False,
            do_not_suggest_items=True,
            do_not_ask_question=False,
            stay_on_step=False,
            emotion_tag="celebrating",
            tone_guidance="warm, celebrating",
            max_sentences=3,
            screen_widget="collection_grid",
            screen_widget_params={"items": ["leaf"]},
            screen_animation="sparkle_burst",
            sfx_cue="collect_chime",
            child_intent="accepted",
        )
        assert plan.celebrate_item == "spotty leaf"
        assert plan.sensory_observation == "It has tiny bumps all over — feels like braille dots"
        assert plan.name_choices == ["Bumpy", "Dotsworth"]
        assert plan.characters_to_reference == ["Sir Spots"]
        assert plan.question_type == "tactile"
        assert plan.emotion_tag == "celebrating"
        assert plan.tone_guidance == "warm, celebrating"
        assert plan.max_sentences == 3
        assert plan.screen_widget == "collection_grid"
        assert plan.screen_widget_params == {"items": ["leaf"]}
        assert plan.screen_animation == "sparkle_burst"
        assert plan.sfx_cue == "collect_chime"
        assert plan.child_intent == "accepted"

    def test_t0_constraints(self) -> None:
        """T0 tier plans should model first and offer binary choices."""
        plan = TurnPlan(
            child_said="...",
            child_emotion="confused",
            must_model_first=True,
            offer_binary_choice=True,
            max_sentences=2,
        )
        assert plan.must_model_first is True
        assert plan.offer_binary_choice is True

    def test_closing_turn_constraints(self) -> None:
        """Closing turns should not ask a question."""
        plan = TurnPlan(
            child_said="I found everything!",
            child_emotion="excited",
            do_not_ask_question=True,
            emotion_tag="proud",
        )
        assert plan.do_not_ask_question is True

    def test_synthesis_with_story_beat(self) -> None:
        """Synthesis steps carry a story_beat for the Speaker to weave in."""
        plan = TurnPlan(
            child_said="all items collected",
            child_emotion="excited",
            story_beat="All the polka-dot friends gathered for a parade in the garden.",
            do_not_ask_question=True,
            emotion_tag="proud",
        )
        assert plan.story_beat == "All the polka-dot friends gathered for a parade in the garden."


class TestTurnPlanValidation:
    """Test field constraint validation."""

    def test_child_said_required(self) -> None:
        """child_said is a required field with no default."""
        try:
            TurnPlan(child_emotion="neutral")  # type: ignore[call-arg]
            raise AssertionError("Should have raised a ValidationError")
        except Exception as exc:
            assert "child_said" in str(exc)

    def test_child_emotion_required(self) -> None:
        """child_emotion is a required field with no default."""
        try:
            TurnPlan(child_said="hello")  # type: ignore[call-arg]
            raise AssertionError("Should have raised a ValidationError")
        except Exception as exc:
            assert "child_emotion" in str(exc)

    def test_max_sentences_accepts_positive_int(self) -> None:
        plan = TurnPlan(child_said="hi", child_emotion="neutral", max_sentences=5)
        assert plan.max_sentences == 5

    def test_screen_widget_params_accepts_nested_dict(self) -> None:
        plan = TurnPlan(
            child_said="hi",
            child_emotion="neutral",
            screen_widget_params={"layout": {"cols": 2, "rows": 3}},
        )
        assert plan.screen_widget_params["layout"]["cols"] == 2


class TestTurnPlanSerialization:
    """Test JSON round-trip serialization."""

    def test_json_roundtrip(self) -> None:
        original = TurnPlan(
            child_said="found a rock",
            child_emotion="excited",
            celebrate_item="rock",
            name_choices=["Rocky", "Pebbles"],
            characters_to_reference=["Sir Spots"],
            question_type="tactile",
            emotion_tag="celebrating",
            tone_guidance="warm",
            max_sentences=3,
            screen_widget="collection_grid",
            screen_widget_params={"count": 2},
            screen_animation="sparkle",
            sfx_cue="chime",
            child_intent="accepted",
        )
        json_str = original.model_dump_json()
        restored = TurnPlan.model_validate_json(json_str)
        assert restored == original

    def test_model_dump_includes_all_fields(self) -> None:
        plan = TurnPlan(child_said="hi", child_emotion="neutral")
        dumped = plan.model_dump()
        expected_fields = {
            "child_said",
            "child_emotion",
            "celebrate_item",
            "progress_note",
            "sensory_observation",
            "name_choices",
            "characters_to_reference",
            "question_type",
            "story_beat",
            "must_model_first",
            "offer_binary_choice",
            "do_not_suggest_items",
            "do_not_ask_question",
            "stay_on_step",
            "emotion_tag",
            "tone_guidance",
            "max_sentences",
            "screen_widget",
            "screen_widget_params",
            "screen_animation",
            "sfx_cue",
            "child_intent",
        }
        assert set(dumped.keys()) == expected_fields

    def test_json_parse_from_raw_dict(self) -> None:
        """Simulate parsing LLM JSON output into a TurnPlan."""
        raw = json.loads(
            '{"child_said":"saw a bug","child_emotion":"excited",'
            '"celebrate_item":"ladybug","name_choices":["Dotty","Bugsy"]}'
        )
        plan = TurnPlan.model_validate(raw)
        assert plan.celebrate_item == "ladybug"
        assert plan.name_choices == ["Dotty", "Bugsy"]
        # Defaults filled in
        assert plan.do_not_suggest_items is True
        assert plan.screen_widget == "photo_display"
