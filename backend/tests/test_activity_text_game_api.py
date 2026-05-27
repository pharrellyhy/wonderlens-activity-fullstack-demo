"""Tests for the standalone activity text game API."""

from fastapi.testclient import TestClient

import server
from schemas.turn_response import TurnResponse
from server import app


def test_activity_catalog_returns_activity_list_shape() -> None:
    client = TestClient(app)

    response = client.get("/api/activities")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == len(body["activities"])
    assert isinstance(body["activities"], list)
    assert "Choose a concept" not in str(body)


def test_start_activity_rejects_unknown_activity() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/start-activity",
        json={"activity_type": "missing_activity", "tier": "T1", "interaction_mode": "text"},
    )

    assert response.status_code == 404
    assert response.json()["error"] == "unknown_activity"


def test_start_activity_creates_text_session(monkeypatch) -> None:
    async def fake_generate_with_retry(*_args, **_kwargs):
        return (
            TurnResponse(
                dialogue="Echo time!",
                tone_marker="curious",
                screen_widget="photo_display",
                screen_widget_params={},
            ),
            None,
        )

    async def fake_log_session(*_args, **_kwargs):
        return None

    async def fake_log_turn(*_args, **_kwargs):
        return None

    server._sessions.clear()
    monkeypatch.setattr(server, "_generate_with_retry", fake_generate_with_retry)
    monkeypatch.setattr(server, "log_session", fake_log_session)
    monkeypatch.setattr(server, "log_turn", fake_log_turn)
    client = TestClient(app)

    response = client.post(
        "/api/start-activity",
        json={"activity_type": "activity_word_echo_practice", "tier": "T1", "interaction_mode": "text"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["activity_type"] == "activity_word_echo_practice"
    assert body["template_type"] == "cat1"
    assert body["first_turn"]["dialogue"] == "Echo time!"
    assert body["session_state"]["interaction_mode"] == "text"
