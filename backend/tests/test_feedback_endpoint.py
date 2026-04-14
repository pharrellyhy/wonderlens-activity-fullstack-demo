"""Tests for the POST /api/feedback endpoint and feedback storage helpers."""

import json
from pathlib import Path

import feedback_storage
import pytest
from fastapi.testclient import TestClient
from schemas.feedback import FeedbackPayload
from server import app


def _valid_payload_dict(
    *,
    session_id: str = "abc123def456",
    screenshots: list[str] | None = None,
) -> dict:
    if screenshots is None:
        screenshots = ["screenshots/turn-03-auto.png"]
    return {
        "session_id": session_id,
        "tester_alias": "Alice",
        "app_mode": "tester",
        "activity": {
            "template_type": "mood_changer_dog",
            "category": "cat1",
            "photo_filename": "dog-on-couch.jpg",
        },
        "session_started_at": "2026-04-13T14:28:11+08:00",
        "session_ended_at": "2026-04-13T14:32:47+08:00",
        "flags": [
            {
                "flag_id": "f-01",
                "turn_number": 3,
                "flagged_at": "2026-04-13T14:30:02+08:00",
                "tags": ["tone"],
                "quick_note": "too preachy",
                "review_comment": "The dog shouldn't moralize.",
                "screenshots": screenshots,
                "turn_snapshot": {
                    "step": "detail_exchange",
                    "speaker_text": "Wow, look at that dog!",
                    "child_transcript": "he looks happy",
                    "widget_type": "photo_full",
                    "recipe_round": 2,
                },
            }
        ],
    }


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(feedback_storage, "FEEDBACK_DIR", tmp_path)
    return TestClient(app)


class TestFeedbackEndpoint:
    def test_happy_path_saves_bundle(self, client: TestClient, tmp_path: Path) -> None:
        payload = _valid_payload_dict()
        png_bytes = b"\x89PNG\r\n\x1a\nFAKEBODY"
        response = client.post(
            "/api/feedback",
            data={"feedback": json.dumps(payload)},
            files=[("screenshots", ("turn-03-auto.png", png_bytes, "image/png"))],
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "saved"
        assert "path" in body

        bundles = list(tmp_path.iterdir())
        assert len(bundles) == 1
        bundle_dir = bundles[0]
        assert bundle_dir.name == "2026-04-13-1432-alice-abc123"

        feedback_json_path = bundle_dir / "feedback.json"
        assert feedback_json_path.exists()
        parsed = FeedbackPayload.model_validate_json(feedback_json_path.read_text(encoding="utf-8"))
        assert parsed.tester_alias == "Alice"
        assert parsed.flags[0].flag_id == "f-01"

        screenshot_path = bundle_dir / "screenshots" / "turn-03-auto.png"
        assert screenshot_path.exists()
        assert screenshot_path.read_bytes() == png_bytes

    def test_unknown_tag_returns_422(self, client: TestClient) -> None:
        payload = _valid_payload_dict()
        payload["flags"][0]["tags"] = ["not-a-real-tag"]
        response = client.post(
            "/api/feedback",
            data={"feedback": json.dumps(payload)},
            files=[("screenshots", ("turn-03-auto.png", b"\x89PNG", "image/png"))],
        )

        assert response.status_code == 422
        body = response.json()
        assert body["status"] == "error"
        assert body["error"] == "invalid_feedback_payload"
        serialized = json.dumps(body)
        assert "not-a-real-tag" in serialized

    def test_mismatched_filenames_returns_422(self, client: TestClient, tmp_path: Path) -> None:
        payload = _valid_payload_dict()
        response = client.post(
            "/api/feedback",
            data={"feedback": json.dumps(payload)},
            files=[("screenshots", ("other.png", b"\x89PNG", "image/png"))],
        )

        assert response.status_code == 422
        body = response.json()
        assert body["error"] == "screenshot_filename_mismatch"
        assert "turn-03-auto.png" in body["missing"]
        assert "other.png" in body["extra"]
        assert list(tmp_path.iterdir()) == []

    def test_path_escape_in_json_returns_422(self, client: TestClient, tmp_path: Path) -> None:
        payload = _valid_payload_dict(screenshots=["screenshots/../evil.png"])
        response = client.post(
            "/api/feedback",
            data={"feedback": json.dumps(payload)},
            files=[("screenshots", ("evil.png", b"\x89PNG", "image/png"))],
        )

        assert response.status_code == 422
        body = response.json()
        assert body["error"] == "unsafe_screenshot_path"
        assert list(tmp_path.iterdir()) == []
