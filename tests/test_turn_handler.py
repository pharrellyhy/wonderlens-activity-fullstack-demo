"""Tests for the turn_handler module — step transitions and auto-advance logic."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from schemas.creative_slots import Cat5CreativeSlots
from schemas.session_state import ConversationTurn, SessionStateModel
from schemas.story_classification import StoryClassification
from schemas.turn_plan import TurnPlan
from schemas.turn_response import TurnResponse
from state_machine import EARLY_EXIT
from turn_handler import (
    TurnInput,
    _generate_with_retry,
    _maybe_record_generated_name,
    _record_collection_detail,
    resolve_turn,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_turn(**overrides: object) -> TurnResponse:
    """Build a TurnResponse with sensible defaults, overridden as needed."""
    defaults: dict = {
        "dialogue": "Test dialogue.",
        "tone_marker": "playful",
        "screen_widget": "character_display",
        "screen_widget_params": {},
        "child_intent": None,
        "stay_on_step": False,
    }
    defaults.update(overrides)
    return TurnResponse(**defaults)


def _make_agent_mock() -> AsyncMock:
    """Build a ScriptAgent-shaped mock without synthetic coroutine attributes."""
    agent = AsyncMock()
    agent.last_plan = None
    agent.retry_speaker_turn = AsyncMock()
    return agent


def _make_state(**overrides: object) -> SessionStateModel:
    """Build a Cat5 SessionStateModel with required fields, overridden as needed."""
    defaults: dict = {
        "session_id": "test-session",
        "tier": "T0",
        "template_type": "cat5",
        "activity_type": "polka_dot_patrol",
        "current_step": "STEP_2_MISSION",
        "current_round": 0,
        "total_rounds": 3,
        "creative_slots": Cat5CreativeSlots(
            observation_angle="shape",
            collection_criterion="round things",
            collection_count=3,
            mission_metaphor="Shape detective",
            role_title="Shape Scout",
            synthesis_type="naming_story",
            stuck_hint="Look near the ground",
            naming_prompt="What would you name this?",
            detail_question_template="What does it remind you of?",
            sorting_criterion="",
        ),
        "entity_name": "dandelion",
        "status": "active",
    }
    defaults.update(overrides)
    return SessionStateModel(**defaults)


def _make_input(**overrides: object) -> TurnInput:
    """Build a TurnInput with defaults."""
    defaults: dict = {
        "text": "",
        "is_silent": False,
        "photo_id": None,
    }
    defaults.update(overrides)
    return TurnInput(**defaults)


def _make_round_items() -> list[list[dict[str, object]]]:
    """Build predictable Cat5 round items for collection tests."""
    return [
        [
            {"id": "leaf_heart", "label": "Leaf heart", "correct": True},
            {"id": "plain_bark", "label": "Plain bark"},
        ],
        [
            {"id": "rock_circle", "label": "Rock circle", "correct": True},
            {"id": "twig_line", "label": "Twig line"},
        ],
        [
            {"id": "puddle_ring", "label": "Puddle ring", "correct": True},
            {"id": "mud_patch", "label": "Mud patch"},
        ],
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hook_second_visit_advances_to_mission() -> None:
    """Hook with prior AI turn should advance and return the mission prompt."""
    state = _make_state(
        current_step="STEP_1_HOOK",
        current_round=0,
        conversation_history=[
            ConversationTurn(role="ai", text="Look what we found!", step="STEP_1_HOOK"),
        ],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        side_effect=lambda current_state: _mock_turn(
            dialogue=f"Prompt for {current_state.current_step}",
            stay_on_step=False,
        )
    )

    result = await resolve_turn(state, _make_input(text="ready"), agent)

    assert state.current_step == "STEP_2_MISSION"
    assert result.turn_response.dialogue == "Prompt for STEP_2_MISSION"
    assert result.response_type == "rules"
    assert result.auto_advance is False


@pytest.mark.asyncio
async def test_invitation_first_delivery_stays_on_step2() -> None:
    """child_intent=null on STEP_2: stays on STEP_2, no auto-advance."""
    state = _make_state()
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(child_intent=None))

    result = await resolve_turn(state, _make_input(), agent)

    assert state.current_step == "STEP_2_MISSION"
    assert result.auto_advance is False
    assert result.response_type == "rules"


@pytest.mark.asyncio
async def test_invitation_acceptance_advances_immediately() -> None:
    """child_intent=accepted: advances immediately to STEP_3_COLLECT_1."""
    state = _make_state()
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(child_intent="accepted"))

    result = await resolve_turn(state, _make_input(text="yes!"), agent)

    assert state.current_step == "STEP_3_COLLECT_1"
    assert result.auto_advance is False
    assert result.response_type == "round"


@pytest.mark.asyncio
async def test_invitation_decline_increments_count() -> None:
    """First decline: stays on STEP_2, decline_count incremented."""
    state = _make_state()
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(child_intent="declined"))

    result = await resolve_turn(state, _make_input(text="no thanks"), agent)

    assert state.current_step == "STEP_2_MISSION"
    assert state.invitation_decline_count == 1
    assert result.auto_advance is False


@pytest.mark.asyncio
async def test_second_decline_exits_gracefully() -> None:
    """Second decline: EARLY_EXIT, status=exited."""
    state = _make_state(invitation_decline_count=1)
    agent = _make_agent_mock()
    # First call returns decline, second call generates exit dialogue
    agent.generate_turn = AsyncMock(
        side_effect=[
            _mock_turn(child_intent="declined"),
            _mock_turn(dialogue="Okay, see you next time!"),
        ]
    )

    result = await resolve_turn(state, _make_input(text="no"), agent)

    assert state.current_step == EARLY_EXIT
    assert state.status == "exited"
    assert result.response_type == "graceful_exit"
    assert result.auto_advance is False


@pytest.mark.asyncio
async def test_correct_photo_enters_detail_phase_and_holds_the_round() -> None:
    """Correct Cat5 picks should enter detail mode before advancing the round."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=2,
        round_items=_make_round_items()[:2],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="Leaf heart! What does it remind you of?"))

    result = await resolve_turn(state, _make_input(photo_id="leaf_heart"), agent)

    assert state.current_step == "STEP_3_COLLECT_1"
    assert state.collection_phase == "detail"
    assert state.collected_photos == ["leaf_heart"]
    assert result.turn_response.dialogue == "Leaf heart! What does it remind you of?"
    assert result.turn_response.stay_on_step is True
    assert result.screen_frame.widget == "explorer_map"
    assert result.auto_advance is False


@pytest.mark.asyncio
async def test_detail_response_advances_to_next_round() -> None:
    """A Cat5 detail reply should finish the current round and reset to photo mode."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=2,
        collection_phase="detail",
        collected_photos=["leaf_heart"],
        round_items=_make_round_items()[:2],
    )
    agent = _make_agent_mock()

    def _phase_b_turn(current_state: SessionStateModel) -> TurnResponse:
        assert current_state.collection_phase == "detail"
        return _mock_turn(dialogue="Cloud Puff! What a perfect name.")

    agent.generate_turn = AsyncMock(side_effect=_phase_b_turn)

    result = await resolve_turn(state, _make_input(text="like a cloud"), agent)

    assert state.current_step == "STEP_3_COLLECT_2"
    assert state.current_round == 2
    assert state.collection_phase == "photo"
    assert state.collected_details == ["like a cloud"]
    assert result.turn_response.dialogue == "Cloud Puff! What a perfect name."
    assert state.collected_names == ["Cloud Puff"]
    assert result.screen_frame.widget == "explorer_map"
    assert result.auto_advance is False
    assert result.response_type == "round"


@pytest.mark.asyncio
async def test_final_detail_response_auto_advances_into_synthesis_prompt() -> None:
    """The last Cat5 detail reply should bridge into synthesis via auto-advance."""
    state = _make_state(
        current_step="STEP_3_COLLECT_2",
        current_round=2,
        total_rounds=2,
        collection_phase="detail",
        collected_photos=["leaf_heart", "rock_circle"],
        round_items=_make_round_items()[:2],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        side_effect=[
            _mock_turn(dialogue="Moon Buddy belongs in our collection."),
            _mock_turn(dialogue="Would you like to make a story about your finds?", stay_on_step=True),
        ]
    )

    result = await resolve_turn(state, _make_input(text="like the moon"), agent)

    assert state.current_step == "STEP_3_COLLECT_2"
    assert state.collection_phase == "detail"
    assert state.round_advance_pending is True
    assert result.turn_response.dialogue == "Moon Buddy belongs in our collection."
    assert result.screen_frame.widget == "explorer_map"
    assert result.auto_advance is True
    assert result.response_type == "round"

    follow_up = await resolve_turn(state, _make_input(), agent)

    assert state.current_step == "STEP_4_SYNTHESIS"
    assert state.collection_phase == "photo"
    assert follow_up.turn_response.dialogue == "Would you like to make a story about your finds?"
    assert follow_up.response_type == "synthesis"
    assert follow_up.auto_advance is False


@pytest.mark.asyncio
async def test_final_detail_guidance_loop_stays_on_detail_before_synthesis() -> None:
    """Final Phase B should respect stay_on_step before auto-advancing into synthesis."""
    state = _make_state(
        current_step="STEP_3_COLLECT_2",
        current_round=2,
        total_rounds=2,
        collection_phase="detail",
        collected_photos=["leaf_heart", "rock_circle"],
        round_items=_make_round_items()[:2],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        return_value=_mock_turn(
            dialogue="Touch it gently again. Does it feel soft or bumpy?",
            stay_on_step=True,
        )
    )

    result = await resolve_turn(state, _make_input(text="what?"), agent)

    assert state.current_step == "STEP_3_COLLECT_2"
    assert state.collection_phase == "detail"
    assert state.round_advance_pending is False
    assert state.detail_exchange_count == 1
    assert result.turn_response.dialogue == "Touch it gently again. Does it feel soft or bumpy?"
    assert result.auto_advance is False
    assert result.response_type == "round"


@pytest.mark.asyncio
async def test_synthesis_first_visit_generates_prompt() -> None:
    """Synthesis with no prior AI turn: generates prompt, stays on STEP_4_SYNTHESIS."""
    state = _make_state(current_step="STEP_4_SYNTHESIS", current_round=3)
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="What would you name your collection?"))

    result = await resolve_turn(state, _make_input(), agent)

    assert state.current_step == "STEP_4_SYNTHESIS"
    assert result.auto_advance is False
    assert result.response_type == "synthesis"


@pytest.mark.asyncio
async def test_synthesis_can_finish_after_first_child_reply() -> None:
    """A single child synthesis reply should be enough to finish the activity prompt."""
    state = _make_state(
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        synthesis_phase="evaluate",
        synthesis_prompt_count=1,
        conversation_history=[
            ConversationTurn(
                role="ai", text="Cloud Puff bumped into Mossy Dot. What happened next?", step="STEP_4_SYNTHESIS"
            ),
        ],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        return_value=_mock_turn(dialogue="They rolled into a fluffy pile and laughed together.")
    )

    mock_classification = AsyncMock(
        return_value=StoryClassification(
            classification="story_attempt", is_related_to_collection=True, story_quality="good"
        )
    )
    with patch("turn_handler._classify_story_response", mock_classification):
        result = await resolve_turn(state, _make_input(text="they giggled"), agent)

    assert state.current_step == "STEP_5_CELEBRATE"
    assert result.turn_response.dialogue == "They rolled into a fluffy pile and laughed together."
    assert result.response_type == "synthesis"
    assert result.auto_advance is True


@pytest.mark.asyncio
async def test_synthesis_second_visit_advances_to_celebrate() -> None:
    """Synthesis completion returns the synthesis reply, then advances to celebrate."""
    state = _make_state(
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        synthesis_phase="evaluate",
        synthesis_prompt_count=1,
        conversation_history=[
            ConversationTurn(role="ai", text="What would you name it?", step="STEP_4_SYNTHESIS"),
            ConversationTurn(role="child", text="Maybe Sunny?", step="STEP_4_SYNTHESIS"),
        ],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="Great name!"))

    mock_classification = AsyncMock(
        return_value=StoryClassification(
            classification="story_attempt", is_related_to_collection=True, story_quality="good"
        )
    )
    with patch("turn_handler._classify_story_response", mock_classification):
        result = await resolve_turn(state, _make_input(text="I call it Sunny"), agent)

    assert state.current_step == "STEP_5_CELEBRATE"
    assert result.turn_response.dialogue == "Great name!"
    assert result.response_type == "synthesis"
    assert result.auto_advance is True


@pytest.mark.asyncio
async def test_synthesis_evaluate_silence_skips_classification_and_generates() -> None:
    """Silence in evaluate should bypass classification and let the AI finish the story."""
    state = _make_state(
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        synthesis_phase="evaluate",
        synthesis_prompt_count=1,
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="The friends curled up under the stars."))

    with patch("turn_handler._classify_story_response", new=AsyncMock()) as mock_classification:
        result = await resolve_turn(state, _make_input(is_silent=True), agent)

    mock_classification.assert_not_called()
    assert state.synthesis_phase == "generate"
    assert state.current_step == "STEP_5_CELEBRATE"
    assert result.turn_response.dialogue == "The friends curled up under the stars."
    assert result.auto_advance is True


@pytest.mark.asyncio
async def test_synthesis_improve_silence_skips_classification_and_generates() -> None:
    """Silence in improve should preserve the child's seed and let the AI complete it."""
    state = _make_state(
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        synthesis_phase="improve",
        synthesis_child_story="Cloud Puff met Mossy Dot.",
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="Cloud Puff met Mossy Dot and they became brave."))

    with patch("turn_handler._classify_story_response", new=AsyncMock()) as mock_classification:
        result = await resolve_turn(state, _make_input(is_silent=True), agent)

    mock_classification.assert_not_called()
    assert state.synthesis_phase == "generate"
    assert state.synthesis_child_story == "Cloud Puff met Mossy Dot."
    assert state.current_step == "STEP_5_CELEBRATE"
    assert result.turn_response.dialogue == "Cloud Puff met Mossy Dot and they became brave."
    assert result.auto_advance is True


@pytest.mark.asyncio
async def test_consecutive_silence_exit() -> None:
    """Two consecutive silences: EARLY_EXIT."""
    state = _make_state(consecutive_silence=1)
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="See you later!"))

    result = await resolve_turn(state, _make_input(is_silent=True), agent)

    assert state.current_step == EARLY_EXIT
    assert state.status == "exited"
    assert result.response_type == "graceful_exit"
    assert result.auto_advance is False


@pytest.mark.asyncio
async def test_silence_during_detail_phase_still_advances() -> None:
    """Silence during Phase B should still transition back to photo mode."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=2,
        collection_phase="detail",
        collected_photos=["leaf_heart"],
        round_items=_make_round_items()[:2],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="That's okay! Let's find the next one."))

    result = await resolve_turn(state, _make_input(is_silent=True), agent)

    # First silence doesn't trigger exit (consecutive_silence == 1)
    assert state.current_step == "STEP_3_COLLECT_2"
    assert state.collection_phase == "photo"
    # Silence should NOT be recorded as a detail
    assert state.collected_details == []
    assert result.auto_advance is False


# ---------------------------------------------------------------------------
# Unit tests for detail/name helpers
# ---------------------------------------------------------------------------


def test_record_collection_detail_stores_non_empty_text() -> None:
    state = _make_state()
    _record_collection_detail(state, "like a cloud")
    assert state.collected_details == ["like a cloud"]


def test_record_collection_detail_ignores_silence() -> None:
    state = _make_state()
    _record_collection_detail(state, "...")
    assert state.collected_details == []


def test_record_collection_detail_ignores_empty() -> None:
    state = _make_state()
    _record_collection_detail(state, "  ")
    assert state.collected_details == []


def test_maybe_record_generated_name_from_quotes() -> None:
    state = _make_state(collected_photos=["leaf_heart"])
    _maybe_record_generated_name(state, "I love it! \u201cCloud Puff\u201d is such a perfect name!")
    assert state.collected_names == ["Cloud Puff"]


def test_maybe_record_generated_name_from_call_pattern() -> None:
    state = _make_state(collected_photos=["leaf_heart"])
    _maybe_record_generated_name(state, "Let's call it Fuzzy Green!")
    assert state.collected_names == ["Fuzzy Green"]


def test_maybe_record_generated_name_records_for_all_synthesis_types() -> None:
    """All synthesis types now use story generation, so names are always recorded."""
    state = _make_state(
        collected_photos=["leaf_heart"],
        creative_slots=Cat5CreativeSlots(
            observation_angle="pattern",
            collection_criterion="Find dots",
            collection_count=3,
            mission_metaphor="Dot detective",
            role_title="Dot Scout",
            synthesis_type="comparison_chart",
            stuck_hint="Look around",
            naming_prompt="What dots?",
            detail_question_template="How are dots different?",
            sorting_criterion="dot size",
        ),
    )
    _maybe_record_generated_name(state, 'I see "Big Dots" everywhere!')
    assert state.collected_names == ["Big Dots"]


def test_maybe_record_generated_name_skips_when_already_named() -> None:
    state = _make_state(collected_photos=["leaf_heart"], collected_names=["Cloud Puff"])
    _maybe_record_generated_name(state, 'How about "Another Name"?')
    # Already have 1 name for 1 photo — should not add another
    assert state.collected_names == ["Cloud Puff"]


@pytest.mark.asyncio
async def test_generate_with_retry_retries_speaker_only_after_plan_violation() -> None:
    """Speaker-only violations should keep the original plan and retry just the speaker."""

    class _SpeakerRetryAgent:
        def __init__(self) -> None:
            self.last_plan: TurnPlan | None = None
            self.generate_calls = 0
            self.retry_speaker_turn = AsyncMock(return_value=_mock_turn(dialogue="Try spotting one more thing."))

        async def generate_turn(self, state: SessionStateModel) -> TurnResponse:
            self.generate_calls += 1
            self.last_plan = TurnPlan(
                child_said="found a soft thing",
                child_emotion="excited",
                do_not_suggest_items=True,
                sensory_observation="It feels puffy and light.",
            )
            return _mock_turn(dialogue="Find a pillow next!")

    state = _make_state(
        tier="T1",
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        collection_phase="photo",
    )
    agent = _SpeakerRetryAgent()

    response = await _generate_with_retry(agent, state)

    assert response.dialogue == "Try spotting one more thing."
    assert agent.generate_calls == 1
    agent.retry_speaker_turn.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_with_retry_replans_after_planner_failure() -> None:
    """Planner failures should force a new full generate_turn attempt."""

    class _PlannerRetryAgent:
        def __init__(self) -> None:
            self.last_plan: TurnPlan | None = None
            self.generate_calls = 0
            self.retry_speaker_turn = AsyncMock()

        async def generate_turn(self, state: SessionStateModel) -> TurnResponse:
            self.generate_calls += 1
            if self.generate_calls == 1:
                self.last_plan = TurnPlan(
                    child_said="that one feels bumpy",
                    child_emotion="excited",
                    do_not_suggest_items=True,
                    sensory_observation=None,
                )
                return _mock_turn(dialogue="That one has such a fun texture.")

            self.last_plan = TurnPlan(
                child_said="that one feels bumpy",
                child_emotion="excited",
                do_not_suggest_items=True,
                sensory_observation="It feels bumpy, like tiny pebbles.",
            )
            return _mock_turn(dialogue="That one feels bumpy, like tiny pebbles.")

    state = _make_state(
        tier="T1",
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        collection_phase="detail",
        collected_photos=["leaf_heart"],
    )
    agent = _PlannerRetryAgent()

    response = await _generate_with_retry(agent, state)

    assert response.dialogue == "That one feels bumpy, like tiny pebbles."
    assert agent.generate_calls == 2
    agent.retry_speaker_turn.assert_not_awaited()
