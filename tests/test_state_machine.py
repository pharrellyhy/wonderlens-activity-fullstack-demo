"""Tests for state machine visual frame matching and get_screen_frame with visual_frames."""

import asyncio

import pytest
from image_gen import _scene_sessions, _SceneSession
from schemas import ScreenFrame
from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
from schemas.session_state import SessionStateModel
from schemas.structured_story import StructuredStory
from state_machine import _match_visual_frame, get_screen_frame
from turn_handling.helpers import _get_screen_frame


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


def _cat5_context(
    *,
    structured_story: StructuredStory | None = None,
    collected_photos: list[str] | None = None,
    collected_details: list[str] | None = None,
) -> dict:
    """Build a Cat5 get_screen_frame context with sensible defaults."""
    return {
        "entity_name": "ladybug",
        "ib_key_concepts": ["Form", "Connection"],
        "collection_phase": "photo",
        "collected_photos": collected_photos if collected_photos is not None else ["speckled_leaf"],
        "collected_names": [],
        "collected_details": collected_details if collected_details is not None else [],
        "structured_story": structured_story,
        "round_items": [],
    }


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


def test_cat5_celebrate_returns_achievement_image_without_concepts():
    """STEP_5_CELEBRATE should render achievement_image with title only, no concepts."""
    context = _cat5_context(
        collected_photos=["speckled_leaf", "circle_flower"],
        collected_details=["big dots", "small dots"],
    )

    frame = get_screen_frame("STEP_5_CELEBRATE", "cat5", _cat5_slots(), context)

    assert frame.widget == "achievement_image"
    assert frame.widget_params["title"] == "Shape Specialist"
    assert "concepts" not in frame.widget_params, "celebrate should NOT include IB concepts — those belong to closing"
    assert "image_data_url" not in frame.widget_params, "no structured_story in context means no image URL"
    assert frame.animation == "badge_reveal"
    assert frame.sfx_cue == "badge_awarded"


def test_cat5_celebrate_includes_image_when_structured_story_has_achievement_url():
    """When structured_story has an achievement image URL, celebrate passes it through."""
    structured = StructuredStory(
        scenes=[],
        achievement_description="",
        achievement_image_data_url="data:image/png;base64,FAKE",
    )
    context = _cat5_context(structured_story=structured)

    frame = get_screen_frame("STEP_5_CELEBRATE", "cat5", _cat5_slots(), context)

    assert frame.widget == "achievement_image"
    assert frame.widget_params["image_data_url"] == "data:image/png;base64,FAKE"
    assert "concepts" not in frame.widget_params


# ---------------------------------------------------------------------------
# Achievement-failure backfill (regression for "banner sometimes missing")
# ---------------------------------------------------------------------------


def _cat5_state(*, structured_story: StructuredStory) -> SessionStateModel:
    """Minimal Cat5 session at STEP_5_CELEBRATE with a structured story attached."""
    return SessionStateModel(
        session_id="sess-banner",
        tier="T0",
        template_type="cat5",
        activity_type="polka_dot_patrol",
        current_step="STEP_5_CELEBRATE",
        creative_slots=_cat5_slots(),
        structured_story=structured_story,
    )


@pytest.fixture()
def fresh_scene_session_registry():
    """Wipe and restore the module-level scene-session registry per test."""
    snapshot = dict(_scene_sessions)
    _scene_sessions.clear()
    try:
        yield
    finally:
        _scene_sessions.clear()
        _scene_sessions.update(snapshot)


def _make_scene_session(achievement_failed: bool) -> _SceneSession:
    """Build a stand-in _SceneSession. The backfill only reads ``achievement_failed``;
    the future is a placeholder to satisfy the dataclass signature."""
    return _SceneSession(
        scene_futures=[],
        achievement_future=asyncio.new_event_loop().create_future(),
        achievement_failed=achievement_failed,
    )


def test_celebrate_frame_surfaces_failure_when_live_session_failed_after_synthesis(
    fresh_scene_session_registry: object,
) -> None:
    """The banner gap: the synthesis layer's 30 s wait expires (or the tester
    manually advances) before the worker fails, so ``story.achievement_image_failed``
    stays False. Without the backfill, the celebrate frame would render
    ``image_status='pending'`` forever and hide the failure banner. With the
    backfill in ``_get_screen_frame``, the live session's failure flag wins.
    """
    structured = StructuredStory(
        scenes=[],
        achievement_description="",
        achievement_image_data_url=None,
        achievement_image_failed=False,
    )
    state = _cat5_state(structured_story=structured)
    _scene_sessions[state.session_id] = _make_scene_session(achievement_failed=True)

    frame = _get_screen_frame(state)

    assert frame.widget == "achievement_image"
    assert frame.widget_params["image_status"] == "failed", (
        "live image session reported failure but celebrate frame stayed pending — the failure banner would not render"
    )
    assert state.structured_story is not None
    assert state.structured_story.achievement_image_failed is True, (
        "expected the helper to mutate the cached story so subsequent turns stay consistent"
    )


def test_celebrate_frame_stays_pending_when_live_session_still_in_flight(
    fresh_scene_session_registry: object,
) -> None:
    """Backfill must not flip the status to 'failed' while the worker is still
    running — that would show a false-negative banner mid-generation."""
    structured = StructuredStory(
        scenes=[],
        achievement_description="",
        achievement_image_data_url=None,
        achievement_image_failed=False,
    )
    state = _cat5_state(structured_story=structured)
    _scene_sessions[state.session_id] = _make_scene_session(achievement_failed=False)

    frame = _get_screen_frame(state)

    assert frame.widget_params["image_status"] == "pending"
    assert state.structured_story is not None
    assert state.structured_story.achievement_image_failed is False


def test_celebrate_frame_keeps_existing_url_even_if_session_marked_failed(
    fresh_scene_session_registry: object,
) -> None:
    """If the cached story already has an image URL, the live failure flag
    must NOT clobber it — the worker may have failed on a *retry* after the
    URL was already cached."""
    structured = StructuredStory(
        scenes=[],
        achievement_description="",
        achievement_image_data_url="data:image/png;base64,REAL",
        achievement_image_failed=False,
    )
    state = _cat5_state(structured_story=structured)
    _scene_sessions[state.session_id] = _make_scene_session(achievement_failed=True)

    frame = _get_screen_frame(state)

    assert frame.widget_params["image_status"] == "ready"
    assert frame.widget_params["image_data_url"] == "data:image/png;base64,REAL"
    assert state.structured_story is not None
    assert state.structured_story.achievement_image_failed is False


def test_cat5_closing_returns_concept_reveal_with_concepts():
    """STEP_6_CLOSING should render concept_reveal widget with concepts, no image."""
    frame = get_screen_frame("STEP_6_CLOSING", "cat5", _cat5_slots(), _cat5_context())

    assert frame.widget == "concept_reveal"
    assert frame.widget_params["title"] == "Shape Specialist"
    assert frame.widget_params["concepts"] == ["Form", "Connection"]
    assert "image_data_url" not in frame.widget_params, "closing is concept-focused — no image"
    assert frame.animation == "badge_reveal"
    assert frame.sfx_cue == "celebration_fanfare"


def test_cat1_closing_unchanged():
    """Cat1 closing path must not be affected by the Cat5 split."""
    slots = _cat1_slots()
    context = {
        "entity_name": "dog",
        "ib_key_concepts": ["Perspective"],
        "collection_phase": "photo",
        "collected_photos": [],
        "collected_names": [],
        "collected_details": [],
        "structured_story": None,
        "round_items": [],
    }

    frame = get_screen_frame("STEP_5_CLOSING", "cat1", slots, context)

    # Cat1 uses STEP_5_CLOSING (not STEP_6) and its own badge_award widget
    assert frame.widget == "badge_award"
    assert frame.widget_params["title"] == "IB Concepts"
    assert frame.widget_params["concepts"] == ["Perspective"]
