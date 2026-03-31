"""Focused regression tests for deep-link game entry."""

from types import SimpleNamespace

import pytest
import server
from entity_registry import lookup_by_entity_name
from fastapi.testclient import TestClient
from schemas.turn_response import TurnResponse
from turn_handler import GenerationDebugInfo


@pytest.fixture()
def deep_link_client(monkeypatch: pytest.MonkeyPatch, tmp_path):
    async def fake_init_db(_: str) -> None:
        return None

    async def fake_log_session(*_args: object, **_kwargs: object) -> None:
        return None

    async def fake_log_turn(*_args: object, **_kwargs: object) -> None:
        return None

    async def fake_generate_with_retry(*_args: object, **_kwargs: object) -> tuple:
        response = TurnResponse(
            dialogue="[curious] We were just talking about your dinosaur's spikes. Would you like to play?",
            tone_marker="curious",
            screen_widget="character_display",
            screen_widget_params={},
            screen_animation="appear",
        )
        debug_info = GenerationDebugInfo(
            step="STEP_1_HOOK",
            attempt_count=1,
            final_verdict="passed",
            attempts=[],
        )
        return response, debug_info

    monkeypatch.setattr(server, "init_db", fake_init_db)
    monkeypatch.setattr(server, "log_session", fake_log_session)
    monkeypatch.setattr(server, "log_turn", fake_log_turn)
    monkeypatch.setattr(server, "_generate_with_retry", fake_generate_with_retry)
    monkeypatch.setattr(server, "get_settings", lambda: SimpleNamespace(db_path=str(tmp_path / "test.db")))

    server._sessions.clear()
    with TestClient(server.app) as client:
        yield client
    server._sessions.clear()


def test_lookup_by_entity_name_matches_name_and_keyword() -> None:
    dog = lookup_by_entity_name("dog")
    stuffed_dog = lookup_by_entity_name("stuffed dog")

    assert dog is not None
    assert stuffed_dog is not None
    assert dog.activity_type == "mood_changer_dog"
    assert stuffed_dog.activity_type == "mood_changer_dog"


def test_start_deep_link_uses_supplied_conversation_context(deep_link_client: TestClient) -> None:
    payload = {
        "entity": "dinosaur",
        "tier": "T0",
        "conversation_context": [
            {"role": "child", "text": "I see a big dinosaur."},
            {"role": "ai", "text": "What do you notice about it?"},
            {"role": "child", "text": "It has spikes on its back."},
        ],
    }

    response = deep_link_client.post("/api/start-deep-link", json=payload)

    assert response.status_code == 200
    data = response.json()
    session = server._sessions[data["session_id"]]

    assert data["activity_type"] == "time_machine_dinosaur"
    assert data["photo_url"] == "/icons/dinosaur.png"
    assert session.deep_linked is True
    assert [turn.model_dump() for turn in session.upstream_conversation] == payload["conversation_context"]
    assert data["first_turn"]["dialogue"].startswith("[curious]")


def test_start_deep_link_unknown_entity_returns_available_entities(deep_link_client: TestClient) -> None:
    response = deep_link_client.post("/api/start-deep-link", json={"entity": "elephant", "tier": "T0"})

    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "Unknown entity"
    assert "dog" in data["available_entities"]
    assert "dinosaur" in data["available_entities"]
