"""Tests for the standalone activity text game API."""

from fastapi.testclient import TestClient

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
