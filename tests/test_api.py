"""Integration tests for the FastAPI server endpoints.

These tests mock the LLM/Vision/TTS calls and test the full request → response cycle.
"""

import io
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from agents.script_agent import ScriptAgentError
from fastapi.testclient import TestClient
from schemas import ConversationTurn
from schemas.child_intent import ChildIntentClassification
from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
from schemas.session_state import SessionStateModel
from schemas.turn_response import TurnResponse
from server import app


@pytest.fixture(autouse=True)
def _reset_sessions() -> None:
    """Clear in-memory session store between tests."""
    from server import _sessions  # noqa: PLC0415

    _sessions.clear()


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    """Create a TestClient with a temp DB, triggering startup to init tables."""
    from config import get_settings  # noqa: PLC0415

    get_settings.cache_clear()
    settings = get_settings()
    original_db_path = settings.db_path
    settings.db_path = str(tmp_path / "test.db")

    with TestClient(app) as c:
        yield c

    settings.db_path = original_db_path
    get_settings.cache_clear()


def _mock_vision_result() -> dict:
    return {
        "entity": "dog",
        "confidence": 0.95,
        "scene": "stuffed dog on a bed",
        "features": ["floppy ears", "soft fur"],
    }


def _turn_by_turn_state() -> SessionStateModel:
    return SessionStateModel(
        session_id="test-sess",
        tier="T0",
        template_type="cat1",
        activity_type="mood_changer_dog",
        current_step="STEP_1_HOOK",
        current_round=0,
        total_rounds=2,
        creative_slots=Cat1CreativeSlots(
            game_mechanic="voice_acting",
            metaphor="This dog has so many stories!",
            role_title="Dog Whisperer",
            round_scenarios=["at home", "at a party"],
            escalation_axis="everyday to playful",
            observation_detail="the floppy ears",
        ),
        entity_name="dog",
        entity_attributes=["floppy ears", "soft fur"],
        entity_category="toy",
        scene="bedroom",
        ib_key_concepts=["Perspective"],
        conversation_history=[
            ConversationTurn(role="ai", text="[excited] Look at this dog!", step="STEP_1_HOOK"),
        ],
    )


def _polka_dot_round_items() -> list[list[dict[str, object]]]:
    return [
        [
            {"id": "spotted_mushroom", "label": "Spotted mushroom", "correct": True},
            {"id": "plain_bark", "label": "Plain bark"},
            {"id": "straight_stick", "label": "Straight stick"},
        ],
        [
            {"id": "dotted_pebble", "label": "Dotted pebble", "correct": True},
            {"id": "smooth_stone", "label": "Smooth stone"},
            {"id": "pine_needle", "label": "Pine needles"},
        ],
    ]


def _polka_dot_collection_state() -> SessionStateModel:
    return SessionStateModel(
        session_id="test-sess",
        tier="T0",
        template_type="cat5",
        activity_type="polka_dot_patrol",
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=2,
        creative_slots=Cat5CreativeSlots(
            observation_angle="pattern",
            collection_criterion="Find things with spots or dots",
            collection_count=2,
            mission_metaphor="You are a Dot Detective!",
            role_title="Dot Detective",
            synthesis_type="naming_story",
            stuck_hint="Look for circles or speckles nearby!",
            naming_prompt="What kind of spots do you see?",
            detail_question_template="How are these dots different?",
            sorting_criterion="dot size",
        ),
        entity_name="ladybug",
        entity_attributes=["red shell", "black spots"],
        entity_category="insect",
        scene="leaf",
        ib_key_concepts=["Form"],
        round_items=_polka_dot_round_items(),
    )


def _step_2_state() -> SessionStateModel:
    state = _turn_by_turn_state()
    state.current_step = "STEP_2_RULES"
    state.conversation_history.append(
        ConversationTurn(role="ai", text="[playful] Would you like to try?", step="STEP_2_RULES")
    )
    return state


def _synthesis_state() -> SessionStateModel:
    return SessionStateModel(
        session_id="test-sess",
        tier="T0",
        template_type="cat5",
        activity_type="polka_dot_patrol",
        current_step="STEP_4_SYNTHESIS",
        current_round=2,
        total_rounds=2,
        creative_slots=Cat5CreativeSlots(
            observation_angle="pattern",
            collection_criterion="Find things with spots or dots",
            collection_count=2,
            mission_metaphor="You are a Dot Detective!",
            role_title="Dot Detective",
            synthesis_type="naming_story",
            stuck_hint="Look for circles or speckles nearby!",
            naming_prompt="What kind of spots do you see?",
            detail_question_template="How are these dots different?",
            sorting_criterion="dot size",
        ),
        entity_name="ladybug",
        ib_key_concepts=["Form"],
        collected_photos=["spotted_mushroom", "dotted_pebble"],
        collected_names=["Speckle Cap", "Pebble Dot"],
        collected_details=["big dots", "tiny dots"],
        synthesis_phase="evaluate",
        synthesis_prompt_count=1,
        conversation_history=[
            ConversationTurn(
                role="ai",
                text="[wonder] Would you like to tell a story about Speckle Cap and Pebble Dot?",
                step="STEP_4_SYNTHESIS",
            ),
        ],
    )


class TestHealthEndpoint:
    def test_health(self, client: TestClient) -> None:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestEntitiesEndpoint:
    def test_entities_returns_categories(self, client: TestClient) -> None:
        resp = client.get("/api/entities")
        assert resp.status_code == 200
        data = resp.json()
        assert "categories" in data
        categories = data["categories"]
        assert len(categories) == 2
        assert categories[0]["id"] == "cat1"
        assert categories[1]["id"] == "cat5"
        assert len(categories[0]["photos"]) == 3
        assert len(categories[1]["photos"]) == 2

    def test_entities_photo_structure(self, client: TestClient) -> None:
        resp = client.get("/api/entities")
        data = resp.json()
        for cat in data["categories"]:
            for photo in cat["photos"]:
                assert "id" in photo
                assert "label" in photo
                assert "src" in photo

    def test_entities_include_game_summary(self, client: TestClient) -> None:
        resp = client.get("/api/entities")
        data = resp.json()
        photos_by_id = {photo["id"]: photo for category in data["categories"] for photo in category["photos"]}

        cat_summary = photos_by_id["cat"]["summary"]
        assert cat_summary["category"] == "category_1"
        assert cat_summary["tier"] == "T0"
        assert cat_summary["round_count"] == 3  # play_rounds from game frontmatter
        assert cat_summary["round_scenarios"]
        assert cat_summary["collection_criterion"] is None

        dandelion_summary = photos_by_id["dandelion"]["summary"]
        assert dandelion_summary["category"] == "category_5"
        assert dandelion_summary["collection_count"] == 3
        assert len(dandelion_summary["collectible_previews"]) == 4
        assert dandelion_summary["game_mechanic"] is None


class TestStartEndpoint:
    @patch("server.initialize_session", side_effect=AssertionError("live pipeline should be bypassed"))
    @patch("server.analyze_image", side_effect=AssertionError("vision should be bypassed"))
    def test_start_session_uses_instruction_recipe_for_demo_entity(
        self,
        mock_vision: AsyncMock,
        mock_initialize_session: AsyncMock,
        client: TestClient,
    ) -> None:
        hook_turn = TurnResponse(
            dialogue="[excited] What a cozy dog friend!",
            tone_marker="excited",
            screen_widget="photo_display",
            screen_widget_params={"description": "Photo of dog", "entity": "dog"},
            screen_animation="sparkle_highlight",
            sfx_cue="wonder_chime",
        )
        fake_photo = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=hook_turn)):
            resp = client.post(
                "/api/start",
                files={"photo": ("dog.png", fake_photo, "image/png")},
                data={"tier": "T0"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["activity_type"] == "mood_changer_dog"
        assert data["template_type"] == "cat1"
        assert data["first_turn"]["dialogue"] == "[excited] What a cozy dog friend!"
        assert data["session_state"]["current_step"] == "STEP_1_HOOK"
        mock_vision.assert_not_called()
        mock_initialize_session.assert_not_called()

    @patch("server.initialize_session")
    @patch("server.analyze_image")
    def test_start_session(
        self,
        mock_vision: AsyncMock,
        mock_initialize_session: AsyncMock,
        client: TestClient,
    ) -> None:
        state = _turn_by_turn_state()
        first_turn = TurnResponse(
            dialogue="What a wonderful dog photo!",
            tone_marker="excited",
            screen_widget="photo_display",
            screen_widget_params={"description": "Photo of dog", "entity": "dog"},
            screen_animation="sparkle_highlight",
            sfx_cue="wonder_chime",
        )

        mock_vision.return_value = _mock_vision_result()
        mock_initialize_session.return_value = (state, first_turn)

        fake_photo = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
        resp = client.post(
            "/api/start",
            files={"photo": ("test.jpg", fake_photo, "image/jpeg")},
            data={"tier": "T0"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "session_id" in data
        assert data["first_turn"]["dialogue"]
        assert data["first_turn"]["response_type"] == "hook"

    @patch("server.initialize_session", side_effect=Exception("Pipeline failed"))
    @patch("server.analyze_image")
    def test_start_session_error(
        self,
        mock_vision: AsyncMock,
        mock_initialize_session: AsyncMock,
        client: TestClient,
    ) -> None:
        mock_vision.return_value = _mock_vision_result()

        fake_photo = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
        resp = client.post(
            "/api/start",
            files={"photo": ("test.jpg", fake_photo, "image/jpeg")},
            data={"tier": "T0"},
        )

        assert resp.status_code == 500
        assert resp.json()["status"] == "error"


class TestTurnEndpoint:
    def test_session_not_found(self, client: TestClient) -> None:
        resp = client.post(
            "/api/turn",
            json={"session_id": "nonexistent", "text": "hello", "is_silent": False},
        )
        assert resp.status_code == 404


class TestTurnByTurnEndpoint:
    def test_turn_returns_explicit_error_exit_when_script_generation_fails_twice(self, client: TestClient) -> None:
        from server import _sessions  # noqa: PLC0415

        _sessions["test-sess"] = _turn_by_turn_state()

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(side_effect=ScriptAgentError("boom"))):
            response = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "hello", "is_silent": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["session_state"]["status"] == "error"
        assert data["turn"]["response_type"] == "error"
        assert data["turn"]["error_exit"] is True

    def test_turn_delivers_step_two_rules_before_first_round(self, client: TestClient) -> None:
        from server import _sessions  # noqa: PLC0415

        _sessions["test-sess"] = _turn_by_turn_state()

        turn = TurnResponse(
            dialogue="[playful] Would you like to try imagining what the dog feels?",
            tone_marker="excited",
            screen_widget="character_display",
            screen_widget_params={"description": "Rules"},
            screen_animation="appear",
            sfx_cue="wonder_chime",
        )

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=turn)):
            response = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "ready", "is_silent": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["session_state"]["current_step"] == "STEP_2_RULES"
        assert data["session_state"]["current_round"] == 0
        assert data["turn"]["response_type"] == "rules"
        # Debug payload is included in turn responses
        assert "debug" in data
        debug = data["debug"]
        assert "step_flow" in debug
        assert "retry_stats" in debug
        assert "generation" in debug
        assert debug["generation"]["final_verdict"] == "passed"

    def test_turn_advances_to_first_round_after_step_two_acceptance(self, client: TestClient) -> None:
        from server import _sessions  # noqa: PLC0415

        _sessions["test-sess"] = _step_2_state()

        celebration_turn = TurnResponse(
            dialogue="[playful] Yay!",
            tone_marker="excited",
            screen_widget="character_display",
            screen_widget_params={"description": "Rules"},
            screen_animation="appear",
            sfx_cue="wonder_chime",
        )

        confirm_intent = ChildIntentClassification(intent="confirm")

        with (
            patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=celebration_turn)),
            patch("turn_handler._classify_child_intent", new=AsyncMock(return_value=confirm_intent)),
        ):
            response = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "yes!", "is_silent": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["session_state"]["current_step"] == "STEP_3_ROUND_1"
        assert data["session_state"]["current_round"] == 1
        assert data["turn"]["response_type"] == "round"
        assert data["turn"]["dialogue"] == "[playful] Yay!"
        assert data["session_state"]["invitation_decline_count"] == 0

    def test_turn_stays_on_step_two_after_first_decline(self, client: TestClient) -> None:
        from server import _sessions  # noqa: PLC0415

        _sessions["test-sess"] = _step_2_state()

        reinvitation_turn = TurnResponse(
            dialogue="[gentle] That's okay. Would you like to try together?",
            tone_marker="gentle",
            screen_widget="character_display",
            screen_widget_params={"description": "Rules"},
            screen_animation="appear",
            sfx_cue="wonder_chime",
        )

        decline_intent = ChildIntentClassification(intent="decline")

        with (
            patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=reinvitation_turn)),
            patch("turn_handler._classify_child_intent", new=AsyncMock(return_value=decline_intent)),
        ):
            response = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "no thanks", "is_silent": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["session_state"]["current_step"] == "STEP_2_RULES"
        assert data["session_state"]["invitation_decline_count"] == 1
        assert data["turn"]["response_type"] == "rules"
        assert data["turn"]["dialogue"] == "[gentle] That's okay. Would you like to try together?"

    def test_turn_exits_after_second_step_two_decline(self, client: TestClient) -> None:
        from server import _sessions  # noqa: PLC0415

        state = _step_2_state()
        state.invitation_decline_count = 1
        _sessions["test-sess"] = state

        exit_turn = TurnResponse(
            dialogue="[gentle] We can play another time.",
            tone_marker="gentle",
            screen_widget="badge_award",
            screen_widget_params={"title": "Great job!", "entity": "dog", "concepts": []},
            screen_animation="badge_reveal",
            sfx_cue="badge_awarded",
        )

        decline_intent = ChildIntentClassification(intent="decline")

        with (
            patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=exit_turn)),
            patch("turn_handler._classify_child_intent", new=AsyncMock(return_value=decline_intent)),
        ):
            response = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "still no", "is_silent": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["session_state"]["current_step"] == "EARLY_EXIT"
        assert data["session_state"]["status"] == "exited"
        assert data["session_state"]["invitation_decline_count"] == 2
        assert data["turn"]["response_type"] == "graceful_exit"
        assert data["turn"]["dialogue"] == "[gentle] We can play another time."

    def test_turn_enters_detail_phase_for_correct_cat5_photo_pick(self, client: TestClient) -> None:
        from server import _sessions  # noqa: PLC0415

        _sessions["test-sess"] = _polka_dot_collection_state()

        detail_turn = TurnResponse(
            dialogue="Spotted mushroom! How are these dots different?",
            tone_marker="excited",
            screen_widget="photo_display",
            screen_widget_params={"photo_id": "spotted_mushroom"},
            screen_animation="appear",
            sfx_cue="wonder_chime",
        )

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=detail_turn)):
            response = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "", "is_silent": False, "photo_id": "spotted_mushroom"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["session_state"]["collected_photos"] == ["spotted_mushroom"]
        assert data["session_state"]["current_step"] == "STEP_3_COLLECT_1"
        assert data["session_state"]["collection_phase"] == "detail"
        assert data["turn"]["auto_advance"] is False
        assert data["session_state"]["collection_criterion"] == "Find things with spots or dots"
        assert data["turn"]["screen_frame"]["widget"] == "explorer_map"
        assert data["turn"]["screen_frame"]["widget_params"]["game_phase"] == "collect_detail"
        assert data["session_state"]["current_round_items"] == [
            {"id": "spotted_mushroom", "label": "Spotted mushroom", "image": ""},
            {"id": "plain_bark", "label": "Plain bark", "image": ""},
            {"id": "straight_stick", "label": "Straight stick", "image": ""},
        ]
        assert [turn.text for turn in _sessions["test-sess"].conversation_history if turn.role == "child"] == [
            "[collected correct item: Spotted mushroom]"
        ]
        assert data["turn"]["dialogue"] == "Spotted mushroom! How are these dots different?"

    def test_turn_advances_cat5_collection_after_detail_response(self, client: TestClient) -> None:
        from server import _sessions  # noqa: PLC0415

        state = _polka_dot_collection_state()
        state.collection_phase = "detail"
        state.collected_photos = ["spotted_mushroom"]
        _sessions["test-sess"] = state

        next_round_turn = TurnResponse(
            dialogue="Those giant dots are bold. Want to find one more?",
            tone_marker="excited",
            screen_widget="progress_tracker",
            screen_widget_params={"filled": 1, "total": 2},
            screen_animation="appear",
            sfx_cue="wonder_chime",
        )

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=next_round_turn)):
            response = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "big dots", "is_silent": False},
            )

        assert response.status_code == 200
        data = response.json()
        # Detail completion now defers advance via round_advance_pending + auto_advance
        assert data["session_state"]["current_step"] == "STEP_3_COLLECT_1"
        assert data["session_state"]["collection_phase"] == "detail"
        assert data["session_state"]["collected_details"] == ["big dots"]
        assert data["turn"]["auto_advance"] is True
        assert data["turn"]["dialogue"] == "Those giant dots are bold. Want to find one more?"

    def test_turn_detail_response_exposes_collected_names_and_details(self, client: TestClient) -> None:
        from server import _sessions  # noqa: PLC0415

        state = _polka_dot_collection_state()
        state.collection_phase = "detail"
        state.collected_photos = ["spotted_mushroom"]
        state.creative_slots.synthesis_type = "naming_story"
        _sessions["test-sess"] = state

        detail_turn = TurnResponse(
            dialogue="\u201cSpeckle Cap\u201d is a great name!",
            tone_marker="excited",
            screen_widget="progress_tracker",
            screen_widget_params={"filled": 1, "total": 2},
            screen_animation="appear",
            sfx_cue="wonder_chime",
        )

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=detail_turn)):
            response = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "like a speckled cap", "is_silent": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["session_state"]["collected_details"] == ["like a speckled cap"]
        assert data["session_state"]["collected_names"] == ["Speckle Cap"]

    def test_turn_returns_wrong_photo_without_advancing_cat5_collection(self, client: TestClient) -> None:
        from server import _sessions  # noqa: PLC0415

        _sessions["test-sess"] = _polka_dot_collection_state()

        turn = TurnResponse(
            dialogue="That bark is interesting, but let's keep hunting for spots.",
            tone_marker="encouraging",
            screen_widget="progress_tracker",
            screen_widget_params={"filled": 0, "total": 2},
            screen_animation="appear",
            sfx_cue="wonder_chime",
        )

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=turn)):
            response = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "", "is_silent": False, "photo_id": "plain_bark"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["turn"]["response_type"] == "wrong_photo"
        assert data["session_state"]["current_step"] == "STEP_3_COLLECT_1"
        assert data["session_state"]["collected_photos"] == []
        assert data["session_state"]["consecutive_wrong"] == 1

    def test_turn_exits_after_two_wrong_cat5_photo_picks(self, client: TestClient) -> None:
        from server import _sessions  # noqa: PLC0415

        _sessions["test-sess"] = _polka_dot_collection_state()

        turn = TurnResponse(
            dialogue="Let's look for something with dots.",
            tone_marker="gentle",
            screen_widget="progress_tracker",
            screen_widget_params={"filled": 0, "total": 2},
            screen_animation="appear",
            sfx_cue="wonder_chime",
        )

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=turn)):
            first_response = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "", "is_silent": False, "photo_id": "plain_bark"},
            )
            second_response = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "", "is_silent": False, "photo_id": "straight_stick"},
            )

        assert first_response.status_code == 200
        assert first_response.json()["turn"]["response_type"] == "wrong_photo"

        assert second_response.status_code == 200
        data = second_response.json()
        assert data["turn"]["response_type"] == "graceful_exit"
        assert data["session_state"]["status"] == "exited"
        assert data["session_state"]["consecutive_wrong"] == 2

    def test_turn_marks_closing_delivery_complete_without_auto_advance(self, client: TestClient) -> None:
        from server import _sessions  # noqa: PLC0415

        state = _turn_by_turn_state()
        state.current_step = "STEP_4_CELEBRATE"
        state.current_round = state.total_rounds
        state.conversation_history.append(
            ConversationTurn(
                role="ai",
                text="[excited] You earned your explorer badge!",
                step="STEP_4_CELEBRATE",
            )
        )
        _sessions["test-sess"] = state

        turn = TurnResponse(
            dialogue="You noticed so many amazing details today!",
            tone_marker="gentle",
            screen_widget="badge_award",
            screen_widget_params={"title": "Dog Whisperer", "concepts": ["Perspective"]},
            screen_animation="badge_reveal",
            sfx_cue="badge_awarded",
        )

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=turn)):
            response = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "", "is_silent": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["turn"]["response_type"] == "closing"
        assert data["turn"]["auto_advance"] is False
        assert data["session_state"]["status"] == "completed"

    def test_turn_uses_visual_agent_celebration_frame_for_celebrate_step(self, client: TestClient) -> None:
        from schemas import ScreenFrame  # noqa: PLC0415
        from server import _sessions  # noqa: PLC0415
        from state_machine import get_screen_frame  # noqa: PLC0415

        state = _turn_by_turn_state()
        state.current_step = "STEP_3_ROUND_2"
        state.current_round = state.total_rounds
        state.celebration_frame = ScreenFrame(
            widget="badge_award",
            widget_params={"title": "Visual Celebration", "concepts": ["Perspective"], "entity": "dog"},
            animation="badge_reveal",
            trigger="on_correct",
            sfx_cue="badge_awarded",
            sfx_label="A shiny badge appears",
            animation_label="The badge lands with a flourish",
            widget_label="Visual Agent finale",
        )
        _sessions["test-sess"] = state

        round_turn = TurnResponse(
            dialogue="You wrapped up the last round!",
            tone_marker="excited",
            screen_widget="character_display",
            screen_widget_params={"description": "Round 2"},
            screen_animation="scene_transition",
            sfx_cue="wonder_chime",
        )
        celebrate_turn = TurnResponse(
            dialogue="You earned your explorer badge!",
            tone_marker="excited",
            screen_widget="badge_award",
            screen_widget_params={"title": "Dog Whisperer", "concepts": ["Perspective"]},
            screen_animation="badge_reveal",
            sfx_cue="badge_awarded",
        )

        direct_frame = get_screen_frame(
            "STEP_4_CELEBRATE",
            state.template_type,
            state.creative_slots,
            {"entity_name": state.entity_name, "key_concepts": state.ib_key_concepts},
            visual_frames=state.visual_frames or None,
            celebration_frame=state.celebration_frame,
        )
        assert direct_frame.widget_label == "Visual Agent finale"

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(side_effect=[round_turn, celebrate_turn])):
            response = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "happy", "is_silent": False},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["turn"]["response_type"] == "round"
            assert data["turn"]["auto_advance"] is True

            response = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "", "is_silent": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["turn"]["response_type"] == "celebration"
        assert data["session_state"]["current_step"] == "STEP_4_CELEBRATE"
        assert data["turn"]["screen_frame"]["widget_label"] == "Visual Agent finale"
        assert data["turn"]["audio"]["sfx_label"] == "A shiny badge appears"


class TestTurnSpeakEndpoint:
    @patch(
        "server.ScriptAgent.generate_turn_streaming", side_effect=AssertionError("streaming agent should be bypassed")
    )
    def test_turn_speak_uses_final_early_exit_dialogue_after_second_decline(
        self,
        mock_generate_turn_streaming: AsyncMock,
        client: TestClient,
    ) -> None:
        from server import _sessions  # noqa: PLC0415

        state = _step_2_state()
        state.invitation_decline_count = 1
        _sessions["test-sess"] = state

        exit_turn = TurnResponse(
            dialogue="[gentle] We can play another time.",
            tone_marker="gentle",
            screen_widget="badge_award",
            screen_widget_params={"title": "Great job!", "entity": "dog", "concepts": []},
            screen_animation="badge_reveal",
            sfx_cue="badge_awarded",
        )

        decline_intent = ChildIntentClassification(intent="decline")

        spoken_texts: list[str] = []

        async def _fake_tts_ogg_stream(text, tier, max_retries=2):
            spoken_texts.append(text)
            yield b"OggS\x00\x01"

        with (
            patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=exit_turn)),
            patch("turn_handler._classify_child_intent", new=AsyncMock(return_value=decline_intent)),
            patch("server.synthesize_speech_ogg_stream_async", new=_fake_tts_ogg_stream),
        ):
            response = client.post(
                "/api/turn-speak",
                json={"session_id": "test-sess", "text": "still no", "is_silent": False},
            )

        assert response.status_code == 200
        payload = response.content
        json_length = int.from_bytes(payload[:4], "big")
        data = json.loads(payload[4 : 4 + json_length])

        assert data["turn"]["dialogue"] == "[gentle] We can play another time."
        assert data["turn"]["response_type"] == "graceful_exit"
        assert spoken_texts == [data["turn"]["dialogue"]]
        mock_generate_turn_streaming.assert_not_called()

    def test_turn_speak_records_exact_collected_item_label_for_cat5_collection(self, client: TestClient) -> None:
        from server import _sessions  # noqa: PLC0415

        _sessions["test-sess"] = _polka_dot_collection_state()

        final_turn = TurnResponse(
            dialogue="Great collecting! Let's find one more.",
            tone_marker="excited",
            screen_widget="progress_tracker",
            screen_widget_params={"filled": 2, "total": 2},
            screen_animation="slot_fill_chime",
            sfx_cue="wonder_chime",
        )

        async def _fake_tts_ogg_stream(text, tier, max_retries=2):
            yield b"OggS\x00\x01"

        with patch("server.ScriptAgent.generate_turn_streaming", new=AsyncMock(return_value=final_turn)):
            with patch("server.synthesize_speech_ogg_stream_async", new=_fake_tts_ogg_stream):
                response = client.post(
                    "/api/turn-speak",
                    json={"session_id": "test-sess", "text": "", "is_silent": False, "photo_id": "spotted_mushroom"},
                )

        assert response.status_code == 200
        assert [turn.text for turn in _sessions["test-sess"].conversation_history if turn.role == "child"] == [
            "[collected correct item: Spotted mushroom]"
        ]

    def test_turn_speak_uses_final_fallback_dialogue_for_tts(self, client: TestClient) -> None:
        from server import _sessions  # noqa: PLC0415

        _sessions["test-sess"] = _turn_by_turn_state()

        async def _fail_streaming(*args, **kwargs):
            on_dialogue = kwargs.get("on_dialogue")
            if on_dialogue:
                await on_dialogue("early streamed dialogue")
            raise ScriptAgentError("stream failed")

        final_turn = TurnResponse(
            dialogue="final fallback dialogue",
            tone_marker="gentle",
            screen_widget="character_display",
            screen_widget_params={"description": "Rules"},
            screen_animation="appear",
            sfx_cue="wonder_chime",
        )
        spoken_texts: list[str] = []

        async def _fake_tts_ogg_stream(text, tier, max_retries=2):
            spoken_texts.append(text)
            yield b"OggS\x00\x01"

        with patch("server.ScriptAgent.generate_turn_streaming", new=_fail_streaming):
            with patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=final_turn)):
                with patch("server.synthesize_speech_ogg_stream_async", new=_fake_tts_ogg_stream):
                    response = client.post(
                        "/api/turn-speak",
                        json={"session_id": "test-sess", "text": "ready", "is_silent": False},
                    )

        assert response.status_code == 200
        payload = response.content
        json_length = int.from_bytes(payload[:4], "big")
        data = json.loads(payload[4 : 4 + json_length])

        assert data["turn"]["dialogue"] == "final fallback dialogue"
        assert spoken_texts == ["final fallback dialogue"]


class TestTTSEndpoint:
    @patch("server.synthesize_speech_ogg_async")
    def test_tts_success(self, mock_tts: AsyncMock, client: TestClient) -> None:
        mock_tts.return_value = (b"OggS" + b"\x00" * 20, 48000)
        resp = client.post("/api/tts", json={"text": "Hello world", "tier": "T0"})
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("audio/ogg")
        assert resp.headers["x-pcm-size"] == "48000"
        assert "x-sample-rate" not in resp.headers
        assert resp.content == b"OggS" + b"\x00" * 20

    @patch("server.synthesize_speech_ogg_async")
    def test_tts_wav_fallback(self, mock_tts: AsyncMock, client: TestClient) -> None:
        mock_tts.return_value = (b"RIFF" + b"\x00" * 20, 48000)
        resp = client.post("/api/tts", json={"text": "Hello world", "tier": "T0"})
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("audio/wav")

    @patch("server.synthesize_speech_ogg_async")
    def test_tts_empty_stream(self, mock_tts: AsyncMock, client: TestClient) -> None:
        mock_tts.return_value = None
        resp = client.post("/api/tts", json={"text": "Hello world", "tier": "T0"})
        assert resp.status_code == 204

    @patch("server.synthesize_speech_ogg_stream_async")
    def test_tts_streaming_get_success(self, mock_tts_stream: AsyncMock, client: TestClient) -> None:
        async def _fake_stream(text: str, tier: str, max_retries: int = 2):
            assert text == "Hello world"
            assert tier == "T1"
            yield b"OggS"
            yield b"\x00\x01"

        mock_tts_stream.side_effect = _fake_stream

        resp = client.get("/api/tts", params={"text": "Hello world", "tier": "T1"})

        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("audio/ogg")
        assert resp.content == b"OggS\x00\x01"


class TestSTTEndpoint:
    @patch("server.transcribe_audio")
    def test_stt_success(self, mock_stt: AsyncMock, client: TestClient) -> None:
        mock_stt.return_value = {"text": "hello world", "confidence": 0.95, "latency_ms": 200}

        fake_audio = io.BytesIO(b"\x00" * 2000)
        resp = client.post(
            "/api/stt",
            files={"audio": ("recording.webm", fake_audio, "audio/webm")},
        )

        assert resp.status_code == 200
        assert resp.json()["text"] == "hello world"

    @patch("server.transcribe_audio")
    def test_stt_empty_transcription(self, mock_stt: AsyncMock, client: TestClient) -> None:
        mock_stt.return_value = {"text": "", "confidence": 0.0, "latency_ms": 100}

        fake_audio = io.BytesIO(b"\x00" * 2000)
        resp = client.post(
            "/api/stt",
            files={"audio": ("recording.webm", fake_audio, "audio/webm")},
        )

        assert resp.status_code == 422
        assert resp.json()["error"] == "transcription_failed"


class TestTurnLogging:
    """Verify that both user and AI turns are logged with state snapshots."""

    def test_turn_logs_both_user_and_ai(self, client: TestClient) -> None:
        import sqlite3  # noqa: PLC0415

        from config import get_settings  # noqa: PLC0415
        from server import _sessions  # noqa: PLC0415

        _sessions["test-sess"] = _turn_by_turn_state()

        turn = TurnResponse(
            dialogue="[playful] Would you like to try?",
            tone_marker="playful",
            screen_widget="character_display",
            screen_widget_params={},
        )

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=turn)):
            resp = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "hello doggy", "is_silent": False},
            )

        assert resp.status_code == 200

        db_path = get_settings().db_path
        conn = sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT role, text, step, state_snapshot, photo_id, is_silent FROM turns WHERE session_id = 'test-sess' ORDER BY id"
        ).fetchall()
        conn.close()

        assert len(rows) >= 2
        user_row = rows[0]
        ai_row = rows[1]

        # User turn
        assert user_row[0] == "user"
        assert user_row[1] == "hello doggy"
        assert user_row[2] is not None  # step logged
        snapshot = json.loads(user_row[3])
        assert "current_step" in snapshot
        assert "consecutive_silence" in snapshot

        # AI turn
        assert ai_row[0] == "ai"
        assert ai_row[1] == "[playful] Would you like to try?"
        assert ai_row[2] is not None
        ai_snapshot = json.loads(ai_row[3])
        assert "current_step" in ai_snapshot

    def test_turn_logs_photo_id_for_collection(self, client: TestClient) -> None:
        import sqlite3  # noqa: PLC0415

        from config import get_settings  # noqa: PLC0415
        from server import _sessions  # noqa: PLC0415

        state = _polka_dot_collection_state()
        _sessions["test-sess"] = state

        turn = TurnResponse(
            dialogue="[amazed] A dotty leaf!",
            tone_marker="amazed",
            screen_widget="explorer_map",
            screen_widget_params={},
        )

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=turn)):
            resp = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "", "is_silent": False, "photo_id": "spotted_mushroom"},
            )

        assert resp.status_code == 200

        db_path = get_settings().db_path
        conn = sqlite3.connect(db_path)
        user_rows = conn.execute(
            "SELECT photo_id FROM turns WHERE session_id = 'test-sess' AND role = 'user'"
        ).fetchall()
        conn.close()

        assert len(user_rows) >= 1
        assert user_rows[0][0] == "spotted_mushroom"

    def test_silence_logged_for_user_turn(self, client: TestClient) -> None:
        import sqlite3  # noqa: PLC0415

        from config import get_settings  # noqa: PLC0415
        from server import _sessions  # noqa: PLC0415

        _sessions["test-sess"] = _turn_by_turn_state()

        turn = TurnResponse(
            dialogue="[gentle] Are you there?",
            tone_marker="gentle",
            screen_widget="character_display",
            screen_widget_params={},
        )

        with patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=turn)):
            resp = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "", "is_silent": True},
            )

        assert resp.status_code == 200

        db_path = get_settings().db_path
        conn = sqlite3.connect(db_path)
        user_rows = conn.execute(
            "SELECT is_silent, text FROM turns WHERE session_id = 'test-sess' AND role = 'user'"
        ).fetchall()
        conn.close()

        assert len(user_rows) >= 1
        assert user_rows[0][0] == 1  # is_silent = True
        assert user_rows[0][1] is None  # no text

    def test_ai_turn_keeps_response_step_after_synthesis_auto_advance(self, client: TestClient) -> None:
        import sqlite3  # noqa: PLC0415

        from config import get_settings  # noqa: PLC0415
        from server import _sessions  # noqa: PLC0415

        _sessions["test-sess"] = _synthesis_state()

        turn = TurnResponse(
            dialogue="[gentle] Speckle Cap and Pebble Dot curled up under the moon.",
            tone_marker="gentle",
            screen_widget="explorer_map",
            screen_widget_params={},
        )
        classification = ChildIntentClassification(
            intent="substantive",
            is_related_to_collection=True,
            story_quality="good",
        )

        with (
            patch("server.ScriptAgent.generate_turn", new=AsyncMock(return_value=turn)),
            patch("turn_handler._classify_child_intent", new=AsyncMock(return_value=classification)),
        ):
            resp = client.post(
                "/api/turn",
                json={"session_id": "test-sess", "text": "they snuggled together", "is_silent": False},
            )

        assert resp.status_code == 200
        assert resp.json()["session_state"]["current_step"] == "STEP_5_CELEBRATE"

        db_path = get_settings().db_path
        conn = sqlite3.connect(db_path)
        ai_row = conn.execute(
            "SELECT step, state_snapshot FROM turns WHERE session_id = 'test-sess' AND role = 'ai' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()

        assert ai_row is not None
        assert ai_row[0] == "STEP_4_SYNTHESIS"
        assert json.loads(ai_row[1])["current_step"] == "STEP_5_CELEBRATE"
