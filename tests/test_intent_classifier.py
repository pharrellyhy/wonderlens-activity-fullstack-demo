"""Tests for the unified child intent classifier."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from schemas.child_intent import ChildIntentClassification
from schemas.creative_slots import Cat5CreativeSlots
from schemas.session_state import SessionStateModel
from turn_handler import _classify_child_intent


class TestChildIntentClassification:
    def test_base_intent(self) -> None:
        result = ChildIntentClassification(intent="confirm")
        assert result.intent == "confirm"
        assert result.story_quality is None
        assert result.is_related_to_collection is None

    def test_synthesis_extension(self) -> None:
        result = ChildIntentClassification(
            intent="substantive",
            story_quality="good",
            is_related_to_collection=True,
        )
        assert result.intent == "substantive"
        assert result.story_quality == "good"
        assert result.is_related_to_collection is True

    def test_all_intents_valid(self) -> None:
        for intent in ("confirm", "decline", "substantive", "off_topic"):
            result = ChildIntentClassification(intent=intent)
            assert result.intent == intent


def _make_cat5_state(**overrides: object) -> SessionStateModel:
    defaults: dict = {
        "session_id": "test",
        "tier": "T0",
        "template_type": "cat5",
        "activity_type": "fluffy_expedition_dandelion",
        "current_step": "STEP_3_COLLECT_1",
        "current_round": 1,
        "total_rounds": 3,
        "creative_slots": Cat5CreativeSlots(
            observation_angle="texture",
            collection_criterion="Find soft things",
            collection_count=3,
            mission_metaphor="Fluffy explorer",
            role_title="Fluffy Scout",
            synthesis_type="naming_story",
            stuck_hint="Look nearby",
            naming_prompt="What name?",
            detail_question_template="How does it feel?",
            sorting_criterion="",
        ),
        "entity_name": "dandelion",
        "status": "active",
    }
    defaults.update(overrides)
    return SessionStateModel(**defaults)


def _mock_llm_response(content: str) -> MagicMock:
    """Build a mock OpenAI chat completion response."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = content
    return response


class TestClassifyChildIntent:
    @pytest.mark.asyncio
    async def test_confirm_intent(self) -> None:
        state = _make_cat5_state(current_step="STEP_2_MISSION")
        with patch("turn_handler.AsyncOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=_mock_llm_response('{"intent": "confirm"}'))
            result = await _classify_child_intent(state, "yes!")
        assert result.intent == "confirm"
        assert result.story_quality is None

    @pytest.mark.asyncio
    async def test_decline_intent(self) -> None:
        state = _make_cat5_state(current_step="STEP_2_MISSION")
        with patch("turn_handler.AsyncOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=_mock_llm_response('{"intent": "decline"}'))
            result = await _classify_child_intent(state, "no thanks")
        assert result.intent == "decline"

    @pytest.mark.asyncio
    async def test_substantive_intent(self) -> None:
        state = _make_cat5_state(current_step="STEP_3_COLLECT_1")
        with patch("turn_handler.AsyncOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                return_value=_mock_llm_response('{"intent": "substantive"}')
            )
            result = await _classify_child_intent(state, "it feels really soft and fuzzy")
        assert result.intent == "substantive"

    @pytest.mark.asyncio
    async def test_synthesis_extension(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_4_SYNTHESIS",
            collected_names=["Mr. Fluff", "Petal"],
        )
        with patch("turn_handler.AsyncOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                return_value=_mock_llm_response(
                    '{"intent": "substantive", "story_quality": "good", "is_related_to_collection": true}'
                )
            )
            result = await _classify_child_intent(state, "Mr. Fluff went to sleep and Petal sang a song")
        assert result.intent == "substantive"
        assert result.story_quality == "good"
        assert result.is_related_to_collection is True

    @pytest.mark.asyncio
    async def test_synthesis_confirm(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_4_SYNTHESIS",
            collected_names=["Mr. Fluff"],
        )
        with patch("turn_handler.AsyncOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=_mock_llm_response('{"intent": "confirm"}'))
            result = await _classify_child_intent(state, "yes tell me a story")
        assert result.intent == "confirm"
        assert result.story_quality is None

    @pytest.mark.asyncio
    async def test_fallback_on_llm_failure(self) -> None:
        state = _make_cat5_state(current_step="STEP_3_COLLECT_1")
        with patch("turn_handler.AsyncOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("LLM down"))
            result = await _classify_child_intent(state, "something")
        assert result.intent == "substantive"
