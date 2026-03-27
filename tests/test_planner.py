"""Tests for the Planner agent — prompt building and plan parsing."""

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agents.planner import (
    Planner,
    PlannerError,
    _build_planner_system_prompt,
    _build_planner_user_prompt,
    _build_state_context,
)
from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
from schemas.session_state import ConversationTurn, SessionStateModel
from schemas.turn_plan import TurnPlan

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cat5_state(**overrides: object) -> SessionStateModel:
    """Build a Cat5 SessionStateModel with sensible defaults."""
    defaults: dict = {
        "session_id": "test-planner-session",
        "tier": "T1",
        "template_type": "cat5",
        "activity_type": "polka_dot_patrol",
        "current_step": "STEP_3_COLLECT_1",
        "current_round": 1,
        "total_rounds": 3,
        "creative_slots": Cat5CreativeSlots(
            observation_angle="texture",
            collection_criterion="Find soft and fluffy things",
            collection_count=3,
            mission_metaphor="fluffy treasure hunt",
            role_title="Chief Fluff Inspector",
            synthesis_type="naming_story",
            stuck_hint="Look under the couch",
            naming_prompt="What would you name this fluffy friend?",
        ),
        "entity_name": "dandelion",
        "entity_category": "plant",
        "status": "active",
    }
    defaults.update(overrides)
    return SessionStateModel(**defaults)


def _make_cat1_state(**overrides: object) -> SessionStateModel:
    """Build a Cat1 SessionStateModel with sensible defaults."""
    defaults: dict = {
        "session_id": "test-planner-cat1",
        "tier": "T0",
        "template_type": "cat1",
        "activity_type": "mood_changer_dog",
        "current_step": "STEP_3_ROUND_1",
        "current_round": 1,
        "total_rounds": 3,
        "creative_slots": Cat1CreativeSlots(
            game_mechanic="mood_guessing",
            metaphor="mood detective",
            role_title="Mood Master",
            round_scenarios=["happy scenario", "sad scenario", "excited scenario"],
            escalation_axis="emotional complexity",
            observation_detail="floppy ears",
        ),
        "entity_name": "dog",
        "entity_category": "animal",
        "status": "active",
    }
    defaults.update(overrides)
    return SessionStateModel(**defaults)


def _make_conversation_history(count: int = 3) -> list[ConversationTurn]:
    """Build a short conversation history."""
    turns = []
    for i in range(count):
        if i % 2 == 0:
            turns.append(ConversationTurn(role="ai", text=f"AI turn {i + 1}", step="STEP_3_COLLECT_1"))
        else:
            turns.append(ConversationTurn(role="child", text=f"Child turn {i + 1}", step="STEP_3_COLLECT_1"))
    return turns


# ---------------------------------------------------------------------------
# Test: _build_state_context
# ---------------------------------------------------------------------------


class TestBuildStateContext:
    """Test that state context is correctly assembled from session state."""

    def test_cat5_state_includes_collection_info(self) -> None:
        state = _make_cat5_state(
            collected_photos=["photo1"],
            collected_names=["Sir Spots"],
            collected_details=["It has tiny bumps"],
            collection_phase="photo",
        )
        context = _build_state_context(state)

        assert "STEP_3_COLLECT_1" in context
        assert "T1" in context
        assert "1 of 3" in context
        assert "Remaining: 2" in context
        assert "Sir Spots" in context
        assert "It has tiny bumps" in context
        assert "texture" in context
        assert "Find soft and fluffy things" in context

    def test_cat5_state_no_collected_items(self) -> None:
        state = _make_cat5_state()
        context = _build_state_context(state)

        assert "Collected: 0 of 3" in context
        assert "Remaining: 3" in context
        assert "(none yet)" in context

    def test_cat1_state_omits_collection_fields(self) -> None:
        state = _make_cat1_state()
        context = _build_state_context(state)

        assert "STEP_3_ROUND_1" in context
        assert "T0" in context
        # Cat1 should not have collection-specific fields
        assert "Collection phase" not in context
        assert "Remaining:" not in context

    def test_includes_entity_info(self) -> None:
        state = _make_cat5_state(entity_name="sunflower", entity_category="flower")
        context = _build_state_context(state)

        assert "sunflower" in context
        assert "flower" in context

    def test_includes_tier_constraints(self) -> None:
        state = _make_cat5_state(tier="T0")
        context = _build_state_context(state)

        # Should include tier info from _load_tier_constraints
        assert "T0" in context

    def test_includes_creative_slots(self) -> None:
        state = _make_cat5_state()
        context = _build_state_context(state)

        assert "fluffy treasure hunt" in context
        assert "Chief Fluff Inspector" in context


# ---------------------------------------------------------------------------
# Test: _build_planner_system_prompt
# ---------------------------------------------------------------------------


class TestBuildPlannerSystemPrompt:
    """Test that the system prompt template is filled with state data."""

    def test_prompt_contains_state_context(self) -> None:
        state = _make_cat5_state(
            collected_names=["Sir Spots"],
            collected_photos=["photo1"],
        )
        prompt = _build_planner_system_prompt(state)

        assert "Sir Spots" in prompt
        assert "STEP_3_COLLECT_1" in prompt
        assert "texture" in prompt

    def test_prompt_contains_conversation_history(self) -> None:
        history = _make_conversation_history(4)
        state = _make_cat5_state(conversation_history=history)
        prompt = _build_planner_system_prompt(state)

        assert "Child turn 2" in prompt
        assert "AI turn 1" in prompt

    def test_prompt_contains_key_rules(self) -> None:
        state = _make_cat5_state()
        prompt = _build_planner_system_prompt(state)

        assert 'When collection_phase is "photo"' in prompt
        assert "NEVER suggest what to find, look for, or collect" in prompt
        assert "do_not_ask_question" in prompt
        assert "sensory_observation" in prompt
        assert "## Step Instructions" in prompt

    def test_prompt_empty_conversation(self) -> None:
        state = _make_cat5_state(conversation_history=[])
        prompt = _build_planner_system_prompt(state)

        assert "No conversation yet" in prompt


# ---------------------------------------------------------------------------
# Test: _build_planner_user_prompt
# ---------------------------------------------------------------------------


class TestBuildPlannerUserPrompt:
    """Test that the user prompt reflects the child's last input and step."""

    def test_includes_child_message(self) -> None:
        history = [ConversationTurn(role="child", text="I found a fuzzy pillow!", step="STEP_3_COLLECT_1")]
        state = _make_cat5_state(conversation_history=history)
        prompt = _build_planner_user_prompt(state)

        assert "I found a fuzzy pillow!" in prompt

    def test_silence_when_no_history(self) -> None:
        state = _make_cat5_state(conversation_history=[])
        prompt = _build_planner_user_prompt(state)

        assert "silence" in prompt

    def test_silence_when_last_is_ai(self) -> None:
        history = [ConversationTurn(role="ai", text="What did you find?", step="STEP_3_COLLECT_1")]
        state = _make_cat5_state(conversation_history=history)
        prompt = _build_planner_user_prompt(state)

        assert "silence" in prompt

    def test_includes_step_and_round(self) -> None:
        state = _make_cat5_state(current_step="STEP_3_COLLECT_2", current_round=2, total_rounds=3)
        prompt = _build_planner_user_prompt(state)

        assert "STEP_3_COLLECT_2" in prompt
        assert "round 2 of 3" in prompt


# ---------------------------------------------------------------------------
# Test: Planner.plan_turn (mocked LLM)
# ---------------------------------------------------------------------------


class TestPlannerPlanTurn:
    """Test the full plan_turn method with mocked LLM responses."""

    @pytest.fixture()
    def mock_plan_json(self) -> str:
        """Return a valid TurnPlan JSON string."""
        return json.dumps(
            {
                "child_said": "I found a fuzzy pillow!",
                "child_emotion": "excited",
                "celebrate_item": "fuzzy pillow",
                "progress_note": "That's your first soft find!",
                "sensory_observation": "It feels like a cloud — so puffy and squishy",
                "name_choices": ["Puffsworth", "Cloudy"],
                "characters_to_reference": [],
                "question_type": "tactile",
                "must_model_first": False,
                "offer_binary_choice": False,
                "do_not_suggest_items": True,
                "do_not_ask_question": False,
                "stay_on_step": False,
                "emotion_tag": "celebrating",
                "tone_guidance": "warm, celebrating",
                "max_sentences": 2,
                "screen_widget": "photo_display",
                "screen_widget_params": {},
                "screen_animation": "sparkle_highlight",
                "sfx_cue": "wonder_chime",
                "child_intent": None,
            }
        )

    @pytest.mark.asyncio()
    async def test_plan_turn_returns_turn_plan(self, mock_plan_json: str) -> None:
        """Successful LLM call returns a valid TurnPlan."""
        mock_message = MagicMock()
        mock_message.content = mock_plan_json

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        state = _make_cat5_state(
            conversation_history=[
                ConversationTurn(role="child", text="I found a fuzzy pillow!", step="STEP_3_COLLECT_1"),
            ]
        )

        planner = Planner()
        with (
            patch("agents.planner._get_client", return_value=mock_client),
            patch("agents.planner.log_agent_call", new_callable=AsyncMock),
        ):
            plan = await planner.plan_turn(state)

        assert isinstance(plan, TurnPlan)
        assert plan.child_said == "I found a fuzzy pillow!"
        assert plan.child_emotion == "excited"
        assert plan.celebrate_item == "fuzzy pillow"
        assert plan.name_choices == ["Puffsworth", "Cloudy"]
        assert plan.emotion_tag == "celebrating"
        assert plan.screen_animation == "sparkle_highlight"

    @pytest.mark.asyncio()
    async def test_plan_turn_raises_on_empty_response(self) -> None:
        """Empty LLM response raises PlannerError."""
        mock_message = MagicMock()
        mock_message.content = ""

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        state = _make_cat5_state()

        planner = Planner()
        with (
            patch("agents.planner._get_client", return_value=mock_client),
            patch("agents.planner.log_agent_call", new_callable=AsyncMock),
        ):
            with pytest.raises(PlannerError, match="Empty response"):
                await planner.plan_turn(state)

    @pytest.mark.asyncio()
    async def test_plan_turn_raises_on_invalid_json(self) -> None:
        """Invalid JSON from LLM raises PlannerError."""
        mock_message = MagicMock()
        mock_message.content = '{"not_a_valid_plan": true}'

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        state = _make_cat5_state()

        planner = Planner()
        with (
            patch("agents.planner._get_client", return_value=mock_client),
            patch("agents.planner.log_agent_call", new_callable=AsyncMock),
        ):
            with pytest.raises(PlannerError, match="Plan generation failed"):
                await planner.plan_turn(state)

    @pytest.mark.asyncio()
    async def test_plan_turn_raises_on_llm_exception(self) -> None:
        """Network or API error raises PlannerError."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=ConnectionError("timeout"))

        state = _make_cat5_state()

        planner = Planner()
        with (
            patch("agents.planner._get_client", return_value=mock_client),
            patch("agents.planner.log_agent_call", new_callable=AsyncMock),
        ):
            with pytest.raises(PlannerError, match="Plan generation failed"):
                await planner.plan_turn(state)

    @pytest.mark.asyncio()
    async def test_plan_turn_logs_agent_call_on_success(self, mock_plan_json: str) -> None:
        """Successful plan_turn logs an agent call with success=True."""
        mock_message = MagicMock()
        mock_message.content = mock_plan_json

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        mock_log = AsyncMock()

        state = _make_cat5_state(
            conversation_history=[
                ConversationTurn(role="child", text="found something!", step="STEP_3_COLLECT_1"),
            ]
        )

        planner = Planner()
        with (
            patch("agents.planner._get_client", return_value=mock_client),
            patch("agents.planner.log_agent_call", mock_log),
        ):
            await planner.plan_turn(state)

        mock_log.assert_called_once()
        call_args = mock_log.call_args
        assert call_args[0][0] == "test-planner-session"
        assert call_args[0][1] == "planner"
        assert call_args[0][3] is True  # success

    @pytest.mark.asyncio()
    async def test_plan_turn_logs_agent_call_on_failure(self) -> None:
        """Failed plan_turn logs an agent call with success=False."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=RuntimeError("boom"))

        mock_log = AsyncMock()

        state = _make_cat5_state()

        planner = Planner()
        with (
            patch("agents.planner._get_client", return_value=mock_client),
            patch("agents.planner.log_agent_call", mock_log),
        ):
            with pytest.raises(PlannerError):
                await planner.plan_turn(state)

        mock_log.assert_called_once()
        call_args = mock_log.call_args
        assert call_args[0][1] == "planner"
        assert call_args[0][3] is False  # failure


# ---------------------------------------------------------------------------
# Test: Plan parsing from realistic LLM output
# ---------------------------------------------------------------------------


class TestPlanParsing:
    """Test parsing TurnPlan from realistic LLM JSON output."""

    def test_minimal_plan_from_json(self) -> None:
        """LLM returns only required fields — defaults fill in."""
        raw = '{"child_said": "I found a sock", "child_emotion": "neutral"}'
        plan = TurnPlan.model_validate_json(raw)

        assert plan.child_said == "I found a sock"
        assert plan.do_not_suggest_items is True
        assert plan.name_choices == []
        assert plan.screen_widget == "photo_display"

    def test_t0_plan_from_json(self) -> None:
        """T0 plan sets scaffolding constraints."""
        raw = json.dumps(
            {
                "child_said": "hmm",
                "child_emotion": "confused",
                "must_model_first": True,
                "offer_binary_choice": True,
                "name_choices": ["Fuzzy", "Puffy"],
                "sensory_observation": "It feels really soft, like a cotton ball",
                "question_type": "binary_choice",
                "emotion_tag": "gentle",
                "max_sentences": 2,
            }
        )
        plan = TurnPlan.model_validate_json(raw)

        assert plan.must_model_first is True
        assert plan.offer_binary_choice is True
        assert plan.name_choices == ["Fuzzy", "Puffy"]

    def test_final_find_plan_from_json(self) -> None:
        """Final find sets do_not_ask_question."""
        raw = json.dumps(
            {
                "child_said": "a fluffy blanket!",
                "child_emotion": "excited",
                "celebrate_item": "fluffy blanket",
                "progress_note": "You found all three!",
                "do_not_ask_question": True,
                "emotion_tag": "celebrating",
                "characters_to_reference": ["Sir Spots", "Puffsworth"],
                "screen_animation": "celebration_burst",
                "sfx_cue": "celebration_fanfare",
            }
        )
        plan = TurnPlan.model_validate_json(raw)

        assert plan.do_not_ask_question is True
        assert plan.characters_to_reference == ["Sir Spots", "Puffsworth"]
        assert plan.celebrate_item == "fluffy blanket"
