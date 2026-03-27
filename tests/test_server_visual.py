"""Integration tests for server visual frame handling and sfx_label in responses."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from config import get_settings
from fastapi.testclient import TestClient
from schemas import ScreenFrame
from schemas.creative_slots import Cat1CreativeSlots
from schemas.session_state import SessionStateModel
from schemas.turn_response import TurnResponse
from server import _sessions, app


@pytest.fixture(autouse=True)
def reset_sessions() -> None:
    _sessions.clear()


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    get_settings.cache_clear()
    settings = get_settings()
    original_db_path = settings.db_path
    settings.db_path = str(tmp_path / "test.db")

    with TestClient(app) as test_client:
        yield test_client

    settings.db_path = original_db_path
    get_settings.cache_clear()


def _cat1_slots() -> Cat1CreativeSlots:
    return Cat1CreativeSlots(
        game_mechanic="what_would_it_say",
        metaphor="This dog has stories.",
        role_title="Story Whisperer",
        round_scenarios=["napping"],
        escalation_axis="everyday to fantastical",
        observation_detail="floppy ears",
    )


def _visual_frames() -> list[ScreenFrame]:
    return [
        ScreenFrame(
            widget="photo_display",
            trigger="on_enter",
            sfx_cue="wonder_chime",
            sfx_label="A magical wonder chime",
            animation_label="Sparkle highlights the photo",
            widget_label="Your adventure photo",
        ),
        ScreenFrame(
            widget="character_display",
            trigger="on_round_1",
            sfx_cue="game_start_chime",
            sfx_label="Game start chime",
            animation_label="Scene comes alive",
            widget_label="Round 1 scene",
        ),
        ScreenFrame(
            widget="badge_award",
            trigger="on_correct",
            sfx_cue="badge_awarded",
            sfx_label="Badge awarded sparkle",
            animation_label="A shining badge appears",
            widget_label="Your explorer badge",
        ),
    ]


def _state_with_visual_frames(step: str = "STEP_2_RULES") -> SessionStateModel:
    return SessionStateModel(
        session_id="test-sess",
        tier="T0",
        template_type="cat1",
        activity_type="mood_changer_dog",
        current_step=step,
        current_round=0,
        total_rounds=1,
        creative_slots=_cat1_slots(),
        entity_name="dog",
        entity_attributes=["soft fur"],
        entity_category="animal",
        scene="bedroom",
        ib_key_concepts=["Perspective"],
        visual_frames=_visual_frames(),
    )


class TestVisualFramesInTurnResponse:
    def test_turn_response_uses_visual_frame_for_round(self, client: TestClient) -> None:
        """When visual_frames are present, screen_frame should come from Visual Agent."""
        _sessions["test-sess"] = _state_with_visual_frames("STEP_2_RULES")

        classifier_turn = TurnResponse(
            dialogue="That sounds fun!",
            tone_marker="excited",
            screen_widget="character_display",
            screen_widget_params={"description": "Rules"},
            screen_animation="appear",
            sfx_cue="wonder_chime",
            child_intent="accepted",
        )
        round_turn = TurnResponse(
            dialogue="Let's play a game!",
            tone_marker="excited",
            screen_widget="character_display",
            screen_widget_params={"description": "Round 1"},
            screen_animation="appear",
            sfx_cue="wonder_chime",
        )

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(side_effect=[classifier_turn, round_turn])):
            # Single turn: acceptance advances immediately to STEP_3_ROUND_1
            resp = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "ready", "is_silent": False},
            )

        assert resp.status_code == 200
        data = resp.json()
        screen_frame = data["turn"]["screen_frame"]

        # Acceptance advances to STEP_3_ROUND_1 -> matched on_round_1 from visual frames
        assert screen_frame["widget"] == "character_display"
        assert screen_frame["sfx_cue"] == "game_start_chime"
        assert screen_frame["sfx_label"] == "Game start chime"
        assert screen_frame["widget_label"] == "Round 1 scene"

    def test_turn_response_includes_sfx_label_in_audio(self, client: TestClient) -> None:
        """The audio dict should include sfx_label from the screen frame."""
        _sessions["test-sess"] = _state_with_visual_frames("STEP_2_RULES")

        classifier_turn = TurnResponse(
            dialogue="That sounds fun!",
            tone_marker="excited",
            screen_widget="character_display",
            screen_widget_params={"description": "Rules"},
            screen_animation="appear",
            sfx_cue="wonder_chime",
            child_intent="accepted",
        )
        round_turn = TurnResponse(
            dialogue="Let's play a game!",
            tone_marker="excited",
            screen_widget="character_display",
            screen_widget_params={"description": "Round 1"},
            screen_animation="appear",
            sfx_cue="wonder_chime",
        )

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(side_effect=[classifier_turn, round_turn])):
            # Single turn: acceptance advances immediately to STEP_3_ROUND_1
            resp = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "ready", "is_silent": False},
            )

        assert resp.status_code == 200
        data = resp.json()
        audio = data["turn"]["audio"]
        assert "sfx_label" in audio
        assert audio["sfx_label"] == "Game start chime"

    def test_turn_response_screen_frame_has_label_fields(self, client: TestClient) -> None:
        """The screen_frame in the response should include all label fields."""
        _sessions["test-sess"] = _state_with_visual_frames("STEP_2_RULES")

        classifier_turn = TurnResponse(
            dialogue="That sounds fun!",
            tone_marker="excited",
            screen_widget="character_display",
            screen_widget_params={},
            screen_animation="appear",
            sfx_cue="wonder_chime",
            child_intent="accepted",
        )
        round_turn = TurnResponse(
            dialogue="Let's play!",
            tone_marker="excited",
            screen_widget="character_display",
            screen_widget_params={},
            screen_animation="appear",
            sfx_cue="wonder_chime",
        )

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(side_effect=[classifier_turn, round_turn])):
            # Single turn: acceptance advances immediately, screen frame from new step
            resp = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "ready", "is_silent": False},
            )

        data = resp.json()
        sf = data["turn"]["screen_frame"]
        assert "sfx_cue" in sf
        assert "sfx_label" in sf
        assert "animation_label" in sf
        assert "widget_label" in sf

    def test_no_sfx_label_in_audio_when_frame_has_none(self, client: TestClient) -> None:
        """When the matched frame has no sfx_label, audio dict should not have sfx_label key."""
        state = SessionStateModel(
            session_id="test-sess",
            tier="T0",
            template_type="cat1",
            activity_type="mood_changer_dog",
            current_step="STEP_2_RULES",
            current_round=0,
            total_rounds=1,
            creative_slots=_cat1_slots(),
            entity_name="dog",
            ib_key_concepts=["Perspective"],
            # No visual frames — will fall back to hardcoded (no sfx_label)
        )
        _sessions["test-sess"] = state

        classifier_turn = TurnResponse(
            dialogue="That sounds fun!",
            tone_marker="excited",
            screen_widget="character_display",
            screen_widget_params={},
            screen_animation="appear",
            sfx_cue="wonder_chime",
            child_intent="accepted",
        )
        round_turn = TurnResponse(
            dialogue="Let's play!",
            tone_marker="excited",
            screen_widget="character_display",
            screen_widget_params={},
            screen_animation="appear",
            sfx_cue="wonder_chime",
        )

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(side_effect=[classifier_turn, round_turn])):
            # Single turn: acceptance advances immediately
            resp = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "ready", "is_silent": False},
            )

        data = resp.json()
        audio = data["turn"]["audio"]
        assert "sfx_label" not in audio


class TestVisualFramesInGracefulExit:
    def test_graceful_exit_uses_visual_frames(self, client: TestClient) -> None:
        state = _state_with_visual_frames("STEP_3_ROUND_1")
        state.current_round = 1
        state.consecutive_silence = 1
        _sessions["test-sess"] = state

        turn = TurnResponse(
            dialogue="It's okay, let's play again next time!",
            tone_marker="gentle",
            screen_widget="badge_award",
            screen_widget_params={"title": "Great job!"},
            screen_animation="badge_reveal",
            sfx_cue="badge_awarded",
        )

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=turn)):
            resp = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "", "is_silent": True},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["turn"]["response_type"] == "graceful_exit"
        assert data["session_state"]["status"] == "exited"
