"""Tests for state machine visual frame matching and get_screen_frame with visual_frames."""

from schemas import ScreenFrame
from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
from state_machine import _match_visual_frame, get_screen_frame


def _cat1_slots() -> Cat1CreativeSlots:
    return Cat1CreativeSlots(
        game_mechanic="voice_acting",
        metaphor="This dog has stories.",
        role_title="Story Whisperer",
        round_scenarios=["napping"],
        escalation_axis="everyday to fantastical",
        observation_detail="floppy ears",
    )


def _cat5_slots() -> Cat5CreativeSlots:
    return Cat5CreativeSlots(
        observation_angle="shape",
        collection_criterion="Find shapes",
        collection_count=2,
        mission_metaphor="Shape Detective!",
        role_title="Shape Specialist",
        synthesis_type="naming_story",
        stuck_hint="Look around!",
        naming_prompt="What shape?",
        detail_question_template="What does it remind you of?",
        sorting_criterion="",
    )


def _make_visual_frames() -> list[ScreenFrame]:
    """Create a set of Visual Agent frames for testing."""
    return [
        ScreenFrame(
            widget="photo_display",
            trigger="on_enter",
            sfx_cue="wonder_chime",
            sfx_label="A magical chime",
            widget_label="Your adventure photo",
            animation_label="Sparkle highlights the photo",
        ),
        ScreenFrame(
            widget="character_display",
            trigger="on_round_1",
            sfx_cue="game_start_chime",
            sfx_label="Game starts",
            widget_label="Round 1 scene",
        ),
        ScreenFrame(
            widget="character_display",
            trigger="on_round_2",
            sfx_cue="scene_woosh",
            sfx_label="Scene transition",
            widget_label="Round 2 scene",
        ),
        ScreenFrame(
            widget="badge_award",
            trigger="on_correct",
            sfx_cue="badge_awarded",
            sfx_label="Badge awarded",
            widget_label="Your explorer badge",
        ),
    ]


class TestMatchVisualFrame:
    def test_matches_hook_to_on_enter(self) -> None:
        frames = _make_visual_frames()
        result = _match_visual_frame("STEP_1_HOOK", frames)
        assert result is not None
        assert result.trigger == "on_enter"
        assert result.widget == "photo_display"

    def test_matches_cat1_round_step(self) -> None:
        frames = _make_visual_frames()
        result = _match_visual_frame("STEP_3_ROUND_1", frames)
        assert result is not None
        assert result.trigger == "on_round_1"
        assert result.widget_label == "Round 1 scene"

    def test_matches_cat1_round_2(self) -> None:
        frames = _make_visual_frames()
        result = _match_visual_frame("STEP_3_ROUND_2", frames)
        assert result is not None
        assert result.trigger == "on_round_2"

    def test_matches_cat5_collect_step(self) -> None:
        frames = _make_visual_frames()
        result = _match_visual_frame("STEP_3_COLLECT_1", frames)
        assert result is not None
        assert result.trigger == "on_round_1"

    def test_matches_cat1_celebrate(self) -> None:
        frames = _make_visual_frames()
        result = _match_visual_frame("STEP_4_CELEBRATE", frames)
        assert result is not None
        assert result.trigger == "on_correct"
        assert result.widget == "badge_award"

    def test_matches_cat5_celebrate(self) -> None:
        frames = _make_visual_frames()
        result = _match_visual_frame("STEP_5_CELEBRATE", frames)
        assert result is not None
        assert result.trigger == "on_correct"

    def test_returns_none_for_rules_step(self) -> None:
        frames = _make_visual_frames()
        result = _match_visual_frame("STEP_2_RULES", frames)
        assert result is None

    def test_returns_none_for_mission_step(self) -> None:
        frames = _make_visual_frames()
        result = _match_visual_frame("STEP_2_MISSION", frames)
        assert result is None

    def test_returns_none_for_closing_step(self) -> None:
        frames = _make_visual_frames()
        result = _match_visual_frame("STEP_5_CLOSING", frames)
        assert result is None

    def test_returns_none_for_ended(self) -> None:
        frames = _make_visual_frames()
        result = _match_visual_frame("ENDED", frames)
        assert result is None

    def test_returns_none_when_trigger_not_in_frames(self) -> None:
        frames = _make_visual_frames()
        # Round 5 not in our test frames
        result = _match_visual_frame("STEP_3_ROUND_5", frames)
        assert result is None

    def test_empty_frames_returns_none(self) -> None:
        result = _match_visual_frame("STEP_1_HOOK", [])
        assert result is None


class TestGetScreenFrameWithVisualFrames:
    def test_uses_visual_frame_when_match_found(self) -> None:
        visual_frames = _make_visual_frames()
        context = {"entity_name": "dog", "ib_key_concepts": ["Perspective"]}

        frame = get_screen_frame("STEP_1_HOOK", "cat1", _cat1_slots(), context, visual_frames=visual_frames)

        assert frame.sfx_cue == "wonder_chime"
        assert frame.sfx_label == "A magical chime"
        assert frame.widget_label == "Your adventure photo"

    def test_uses_visual_frame_for_round(self) -> None:
        visual_frames = _make_visual_frames()
        context = {"entity_name": "dog", "ib_key_concepts": []}

        frame = get_screen_frame("STEP_3_ROUND_1", "cat1", _cat1_slots(), context, visual_frames=visual_frames)

        assert frame.widget == "character_display"
        assert frame.sfx_cue == "game_start_chime"
        assert frame.widget_label == "Round 1 scene"

    def test_falls_back_to_hardcoded_when_no_visual_match(self) -> None:
        visual_frames = _make_visual_frames()
        context = {"entity_name": "dog", "ib_key_concepts": []}

        # STEP_2_RULES has no trigger match in visual frames
        frame = get_screen_frame("STEP_2_RULES", "cat1", _cat1_slots(), context, visual_frames=visual_frames)

        assert frame.widget == "character_display"
        # Should be the hardcoded frame (no sfx_label)
        assert frame.sfx_label is None

    def test_falls_back_when_visual_frames_is_none(self) -> None:
        context = {"entity_name": "dog", "ib_key_concepts": []}

        frame = get_screen_frame("STEP_1_HOOK", "cat1", _cat1_slots(), context, visual_frames=None)

        assert frame.widget == "photo_display"
        # Hardcoded frame has no sfx_label
        assert frame.sfx_label is None

    def test_falls_back_when_visual_frames_is_empty(self) -> None:
        context = {"entity_name": "dog", "ib_key_concepts": []}

        frame = get_screen_frame("STEP_1_HOOK", "cat1", _cat1_slots(), context, visual_frames=[])

        assert frame.widget == "photo_display"

    def test_uses_explorer_map_for_cat5_collect(self) -> None:
        visual_frames = _make_visual_frames()
        context = {"entity_name": "leaf", "ib_key_concepts": ["Form"]}

        frame = get_screen_frame("STEP_3_COLLECT_1", "cat5", _cat5_slots(), context, visual_frames=visual_frames)

        # Cat5 now always uses explorer_map
        assert frame.widget == "explorer_map"
        assert frame.trigger == "on_enter"

    def test_cat5_collect_explorer_map_has_progress(self) -> None:
        context = {
            "entity_name": "leaf",
            "ib_key_concepts": ["Form"],
            "collection_phase": "photo",
            "collected_photos": ["leaf_heart"],
        }

        frame = get_screen_frame("STEP_3_COLLECT_2", "cat5", _cat5_slots(), context)

        assert frame.widget == "explorer_map"
        assert frame.widget_params["collected_count"] == 1

    def test_cat5_detail_phase_uses_explorer_map(self) -> None:
        context = {
            "entity_name": "leaf",
            "ib_key_concepts": ["Form"],
            "collection_phase": "detail",
            "collected_photos": ["leaf_heart"],
            "round_items": [
                [
                    {"id": "leaf_heart", "label": "Leaf heart", "correct": True, "image": "/icons/leaf_heart.png"},
                    {"id": "plain_bark", "label": "Plain bark", "image": "/icons/plain_bark.png"},
                ],
            ],
        }

        frame = get_screen_frame("STEP_3_COLLECT_1", "cat5", _cat5_slots(), context, visual_frames=None)

        assert frame.widget == "explorer_map"

    def test_cat5_detail_phase_ignores_collect_visual_frame(self) -> None:
        visual_frames = _make_visual_frames()
        context = {
            "entity_name": "leaf",
            "ib_key_concepts": ["Form"],
            "collection_phase": "detail",
            "collected_photos": ["leaf_heart"],
        }

        frame = get_screen_frame("STEP_3_COLLECT_1", "cat5", _cat5_slots(), context, visual_frames=visual_frames)

        # Cat5 always uses explorer_map regardless of visual frames
        assert frame.widget == "explorer_map"

    def test_uses_visual_frame_for_celebration(self) -> None:
        visual_frames = _make_visual_frames()
        context = {"entity_name": "dog", "ib_key_concepts": ["Perspective"]}

        frame = get_screen_frame("STEP_4_CELEBRATE", "cat1", _cat1_slots(), context, visual_frames=visual_frames)

        assert frame.widget == "badge_award"
        assert frame.sfx_cue == "badge_awarded"
        assert frame.widget_label == "Your explorer badge"
