"""Focused regression tests for turn-by-turn server flow."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from agents.script_agent import ScriptAgentError
from config import get_settings
from fastapi.testclient import TestClient
from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
from schemas.session_state import SessionStateModel
from schemas.turn_response import TurnResponse
from server import _sessions, app


@pytest.fixture(autouse=True)
def reset_sessions() -> None:
    """Clear in-memory session state between tests."""
    _sessions.clear()


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    """Create a TestClient backed by a temporary SQLite database."""
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
        metaphor="This friend has stories to tell.",
        role_title="Story Whisperer",
        round_scenarios=["taking a nap"],
        escalation_axis="everyday to fantastical",
        observation_detail="soft floppy ears",
    )


def _cat1_state(current_step: str) -> SessionStateModel:
    return SessionStateModel(
        session_id="test-session",
        tier="T0",
        template_type="cat1",
        activity_type="mood_changer_dog",
        current_step=current_step,
        current_round=1,
        total_rounds=1,
        creative_slots=_cat1_slots(),
        entity_name="dog",
        entity_attributes=["soft fur"],
        entity_category="animal",
        scene="bedroom",
        ib_key_concepts=["Perspective"],
    )


def _cat5_slots() -> Cat5CreativeSlots:
    return Cat5CreativeSlots(
        observation_angle="shape",
        collection_criterion="Find different shapes",
        collection_count=2,
        mission_metaphor="You are a Shape Detective!",
        role_title="Shape Specialist",
        synthesis_type="naming_story",
        stuck_hint="Look nearby for interesting shapes.",
        naming_prompt="What does this shape remind you of?",
    )


def _cat5_state(current_step: str) -> SessionStateModel:
    return SessionStateModel(
        session_id="test-session",
        tier="T0",
        template_type="cat5",
        activity_type="texture_treasure_hunt",
        current_step=current_step,
        current_round=0,
        total_rounds=2,
        creative_slots=_cat5_slots(),
        entity_name="leaf",
        entity_attributes=["green"],
        entity_category="plant",
        scene="garden",
        ib_key_concepts=["Form"],
    )


def test_script_failure_fallback_surfaces_error_exit(client: TestClient) -> None:
    _sessions["test-session"] = _cat1_state("STEP_3_ROUND_1")

    with patch(
        "server.ScriptAgent.generate_turn",
        new=AsyncMock(side_effect=[ScriptAgentError("boom"), ScriptAgentError("boom")]),
    ):
        resp = client.post(
            "/api/turn",
            json={"session_id": "test-session", "text": "happy", "is_silent": False},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["session_state"]["status"] == "error"
    assert data["turn"]["error_exit"] is True


def test_cat5_turn_returns_collected_photos_in_session_state(client: TestClient) -> None:
    _sessions["test-session"] = _cat5_state("STEP_3_COLLECT_1")

    with patch(
        "server.ScriptAgent.generate_turn",
        new=AsyncMock(
            return_value=TurnResponse(
                dialogue="Nice find. Let's look for one more shape.",
                tone_marker="curious",
                screen_widget="progress_tracker",
                screen_widget_params={"filled": 1, "total": 2},
                screen_animation="slot_fill_chime",
                sfx_cue="wonder_chime",
            )
        ),
    ):
        resp = client.post(
            "/api/turn",
            json={"session_id": "test-session", "text": "", "is_silent": False, "photo_id": "leaf_heart"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["session_state"]["collected_photos"] == ["leaf_heart"]


def test_closing_turn_marks_session_completed_without_extra_turn(client: TestClient) -> None:
    _sessions["test-session"] = _cat1_state("STEP_4_CELEBRATE")

    with patch(
        "server.ScriptAgent.generate_turn",
        new=AsyncMock(
            return_value=TurnResponse(
                dialogue="We noticed Perspective today. Great imagining!",
                tone_marker="warm",
                screen_widget="badge_award",
                screen_widget_params={"title": "Story Whisperer", "concepts": ["Perspective"], "entity": "dog"},
                screen_animation="badge_reveal",
                sfx_cue="badge_awarded",
            )
        ),
    ):
        resp = client.post(
            "/api/turn",
            json={"session_id": "test-session", "text": "", "is_silent": False},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["turn"]["response_type"] == "closing"
    assert data["turn"]["auto_advance"] is False
    assert data["session_state"]["status"] == "completed"
