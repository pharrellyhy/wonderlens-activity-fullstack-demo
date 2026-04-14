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


def _write_bundle(
    base_dir: Path,
    folder_name: str,
    payload: dict,
    screenshots: dict[str, bytes] | None = None,
) -> Path:
    bundle = base_dir / folder_name
    (bundle / "screenshots").mkdir(parents=True, exist_ok=True)
    (bundle / "feedback.json").write_text(json.dumps(payload), encoding="utf-8")
    for rel, data in (screenshots or {}).items():
        (bundle / rel).parent.mkdir(parents=True, exist_ok=True)
        (bundle / rel).write_bytes(data)
    return bundle


class TestFeedbackListAndImage:
    def test_list_all_feedback_flattens_flags(self, tmp_path: Path) -> None:
        payload_a = _valid_payload_dict(session_id="aaa111bbb222")
        payload_a["flags"][0]["flagged_at"] = "2026-04-13T14:30:02+08:00"
        payload_b = _valid_payload_dict(session_id="ccc333ddd444")
        payload_b["flags"][0]["flag_id"] = "f-02"
        payload_b["flags"][0]["flagged_at"] = "2026-04-14T09:00:00+08:00"
        payload_b["tester_alias"] = "Bob"

        _write_bundle(tmp_path, "2026-04-13-1432-alice-aaa111", payload_a)
        _write_bundle(tmp_path, "2026-04-14-0901-bob-ccc333", payload_b)

        entries = feedback_storage.list_all_feedback(tmp_path)

        assert len(entries) == 2
        flag_ids = {entry["flag"]["flag_id"] for entry in entries}
        assert flag_ids == {"f-01", "f-02"}
        folders = {entry["session"]["folder_name"] for entry in entries}
        assert folders == {"2026-04-13-1432-alice-aaa111", "2026-04-14-0901-bob-ccc333"}
        aliases = {entry["session"]["tester_alias"] for entry in entries}
        assert aliases == {"Alice", "Bob"}

    def test_list_all_feedback_skips_malformed(self, tmp_path: Path) -> None:
        payload = _valid_payload_dict()
        _write_bundle(tmp_path, "2026-04-13-1432-alice-abc123", payload)

        bad_bundle = tmp_path / "2026-04-14-0000-mallory-xxxxxx"
        bad_bundle.mkdir()
        (bad_bundle / "feedback.json").write_text("{not json", encoding="utf-8")

        orphan = tmp_path / "orphan-folder"
        orphan.mkdir()

        entries = feedback_storage.list_all_feedback(tmp_path)

        assert len(entries) == 1
        assert entries[0]["flag"]["flag_id"] == "f-01"

    def test_list_all_feedback_handles_missing_root(self, tmp_path: Path) -> None:
        assert feedback_storage.list_all_feedback(tmp_path / "nope") == []

    def test_read_feedback_image_happy_path(self, tmp_path: Path) -> None:
        payload = _valid_payload_dict()
        png = b"\x89PNGCONTENT"
        _write_bundle(
            tmp_path,
            "2026-04-13-1432-alice-abc123",
            payload,
            {"screenshots/turn-03-auto.png": png},
        )

        data = feedback_storage.read_feedback_image(
            "2026-04-13-1432-alice-abc123",
            "screenshots/turn-03-auto.png",
            tmp_path,
        )
        assert data == png

    def test_read_feedback_image_missing_returns_none(self, tmp_path: Path) -> None:
        payload = _valid_payload_dict()
        _write_bundle(tmp_path, "2026-04-13-1432-alice-abc123", payload)

        data = feedback_storage.read_feedback_image(
            "2026-04-13-1432-alice-abc123",
            "screenshots/nope.png",
            tmp_path,
        )
        assert data is None

    @pytest.mark.parametrize(
        "folder_name",
        ["..", "../etc", "with/slash", "with\\backslash", "", ".git", ".", ".hidden"],
    )
    def test_read_feedback_image_rejects_unsafe_folder(self, tmp_path: Path, folder_name: str) -> None:
        with pytest.raises(ValueError):
            feedback_storage.read_feedback_image(folder_name, "screenshots/a.png", tmp_path)

    def test_read_feedback_image_rejects_symlink_escape(self, tmp_path: Path) -> None:
        outside = tmp_path.parent / "outside-bundle"
        (outside / "screenshots").mkdir(parents=True, exist_ok=True)
        (outside / "screenshots" / "secret.png").write_bytes(b"top-secret")

        (tmp_path / "escape-bundle").symlink_to(outside, target_is_directory=True)

        with pytest.raises(ValueError):
            feedback_storage.read_feedback_image("escape-bundle", "screenshots/secret.png", tmp_path)

    @pytest.mark.parametrize(
        "relative_path",
        ["../evil.png", "screenshots/../../escape.png", "/absolute.png"],
    )
    def test_read_feedback_image_rejects_unsafe_path(self, tmp_path: Path, relative_path: str) -> None:
        _write_bundle(tmp_path, "2026-04-13-1432-alice-abc123", _valid_payload_dict())
        with pytest.raises(ValueError):
            feedback_storage.read_feedback_image("2026-04-13-1432-alice-abc123", relative_path, tmp_path)

    def test_get_list_endpoint_sorted_newest_first(self, client: TestClient, tmp_path: Path) -> None:
        payload_old = _valid_payload_dict(session_id="aaa111bbb222")
        payload_old["flags"][0]["flagged_at"] = "2026-04-13T14:30:02+08:00"
        payload_new = _valid_payload_dict(session_id="ccc333ddd444")
        payload_new["flags"][0]["flag_id"] = "f-02"
        payload_new["flags"][0]["flagged_at"] = "2026-04-14T09:00:00+08:00"

        _write_bundle(tmp_path, "2026-04-13-1432-alice-aaa111", payload_old)
        _write_bundle(tmp_path, "2026-04-14-0901-alice-ccc333", payload_new)

        response = client.get("/api/feedback/list")
        assert response.status_code == 200
        body = response.json()
        assert [e["flag"]["flag_id"] for e in body["entries"]] == ["f-02", "f-01"]

    def test_get_image_endpoint_serves_png(self, client: TestClient, tmp_path: Path) -> None:
        png = b"\x89PNGBODY"
        _write_bundle(
            tmp_path,
            "2026-04-13-1432-alice-abc123",
            _valid_payload_dict(),
            {"screenshots/turn-03-auto.png": png},
        )

        response = client.get("/api/feedback/image/2026-04-13-1432-alice-abc123/screenshots/turn-03-auto.png")
        assert response.status_code == 200
        assert response.content == png
        assert response.headers["content-type"].startswith("image/png")

    def test_get_image_endpoint_404_on_missing(self, client: TestClient, tmp_path: Path) -> None:
        _write_bundle(tmp_path, "2026-04-13-1432-alice-abc123", _valid_payload_dict())
        response = client.get("/api/feedback/image/2026-04-13-1432-alice-abc123/screenshots/nope.png")
        assert response.status_code == 404
