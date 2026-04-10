"""Tests for the turn_handler module — step transitions and auto-advance logic."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agents.script_agent import ScriptAgentError
from schemas.child_intent import ChildIntentClassification
from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
from schemas.session_state import ConversationTurn, SessionStateModel
from schemas.turn_directive import TurnDirective
from schemas.turn_plan import TurnPlan
from schemas.turn_response import TurnResponse
from state_machine import EARLY_EXIT
from turn_handling import (
    _DIRECTIVE_RE,
    _INVITATIONAL_PREFIX_RE,
    _ITEM_SUGGESTION_RE,
    TurnInput,
    _ends_with_open_question,
    _generate_with_retry,
    _has_completion_language,
    _has_model_phrase,
    _maybe_record_generated_name,
    _record_collection_detail,
    resolve_turn,
)
from turn_handling.directive import _resolve_turn_with_directive
from turn_handling.helpers import _HISTORY_LIMIT, _append_ai_turn, _should_auto_advance

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


async def _run_directive_advance(
    state: SessionStateModel,
    turn_response: TurnResponse,
    *,
    emotion_tag: str = "gentle",
):
    """Run _resolve_turn_with_directive with a canned advance directive.

    Wraps the boilerplate shared by tests that exercise the directive handler:
    builds a ScriptAgent mock returning ``turn_response``, constructs a basic
    advance directive, and invokes the resolver.
    """
    agent = _make_agent_mock()
    agent.generate_turn_from_directive = AsyncMock(return_value=turn_response)
    directive = TurnDirective(
        action="advance",
        reasoning="test",
        response_direction="test",
        emotion_tag=emotion_tag,
    )
    return await _resolve_turn_with_directive(state, _make_input(), agent, directive)


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
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_intent_classifier(monkeypatch):
    """Keep legacy-path tests on the classic resolver and mock child intent."""

    monkeypatch.setattr("turn_handling.core.get_settings", lambda: SimpleNamespace(turn_director_enabled=False))

    async def _mock_classify(state, text):
        return ChildIntentClassification(intent="substantive")

    monkeypatch.setattr("turn_handling.core._classify_child_intent", _mock_classify)


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
    """child_intent=substantive on STEP_2: stays on STEP_2, no auto-advance."""
    state = _make_state()
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn())

    result = await resolve_turn(state, _make_input(), agent)

    assert state.current_step == "STEP_2_MISSION"
    assert result.auto_advance is False
    assert result.response_type == "rules"


@pytest.mark.asyncio
async def test_invitation_acceptance_advances_immediately(monkeypatch) -> None:
    """child_intent=confirm: delivers celebration, auto-advances to STEP_3_COLLECT_1."""
    state = _make_state()
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn())

    async def _confirm_classify(s, t):
        return ChildIntentClassification(intent="confirm")

    monkeypatch.setattr("turn_handling.core._classify_child_intent", _confirm_classify)

    result = await resolve_turn(state, _make_input(text="yes!"), agent)

    assert state.current_step == "STEP_3_COLLECT_1"
    assert state.invitation_accepted is True
    assert state.child_intent == "confirm"
    # Combined celebration + finding prompt — no auto-advance needed
    assert result.auto_advance is False
    assert result.response_type == "round"
    # Deterministic templates — no LLM call
    assert agent.generate_turn.call_count == 0
    assert "celebrating" in result.turn_response.dialogue or "excited" in result.turn_response.dialogue


@pytest.mark.asyncio
async def test_invitation_decline_increments_count(monkeypatch) -> None:
    """First decline: stays on STEP_2, decline_count incremented."""
    state = _make_state()
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn())

    async def _decline_classify(s, t):
        return ChildIntentClassification(intent="decline")

    monkeypatch.setattr("turn_handling.core._classify_child_intent", _decline_classify)

    result = await resolve_turn(state, _make_input(text="no thanks"), agent)

    assert state.current_step == "STEP_2_MISSION"
    assert state.invitation_decline_count == 1
    assert result.auto_advance is False


@pytest.mark.asyncio
async def test_second_decline_exits_gracefully(monkeypatch) -> None:
    """Two declines → graceful exit."""
    state = _make_state(invitation_decline_count=1)
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="Okay, see you next time!"))

    async def _decline_classify(s, t):
        return ChildIntentClassification(intent="decline")

    monkeypatch.setattr("turn_handling.core._classify_child_intent", _decline_classify)

    result = await resolve_turn(state, _make_input(text="no"), agent)

    assert state.current_step == EARLY_EXIT
    assert state.status == "exited"
    assert result.response_type == "graceful_exit"


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

    # First response: naming dialogue, state still on COLLECT_1 detail
    assert state.current_step == "STEP_3_COLLECT_1"
    assert state.collection_phase == "detail"
    assert state.round_advance_pending is True
    assert result.auto_advance is True
    assert result.turn_response.dialogue == "Cloud Puff! What a perfect name."
    assert state.collected_details == ["like a cloud"]
    assert state.collected_names == ["Cloud Puff"]

    # Follow-up auto-advance: now flips to COLLECT_2 photo mode
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="Would you like to find the next one?"))
    follow_up = await resolve_turn(state, _make_input(), agent)

    assert state.current_step == "STEP_3_COLLECT_2"
    assert state.current_round == 2
    assert state.collection_phase == "photo"
    assert follow_up.screen_frame.widget == "explorer_map"
    assert follow_up.auto_advance is False
    assert follow_up.response_type == "round"


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
        tier="T1",  # T1 allows 2 detail exchanges (T0 only allows 1)
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
async def test_synthesis_can_finish_after_first_child_reply(monkeypatch) -> None:
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

    async def _good_story(s, t):
        return ChildIntentClassification(intent="substantive", story_quality="good", is_related_to_collection=True)

    monkeypatch.setattr("turn_handling.core._classify_child_intent", _good_story)
    result = await resolve_turn(state, _make_input(text="they giggled"), agent)

    assert state.current_step == "STEP_5_CELEBRATE"
    assert result.turn_response.dialogue == "They rolled into a fluffy pile and laughed together."
    assert result.response_type == "synthesis"
    assert result.auto_advance is True


@pytest.mark.asyncio
async def test_synthesis_second_visit_advances_to_celebrate(monkeypatch) -> None:
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

    async def _good_story(s, t):
        return ChildIntentClassification(intent="substantive", story_quality="good", is_related_to_collection=True)

    monkeypatch.setattr("turn_handling.core._classify_child_intent", _good_story)
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

    result = await resolve_turn(state, _make_input(is_silent=True), agent)

    # Silence triggers the loading screen first (auto-advance to generate phase)
    assert state.synthesis_phase == "generate"
    assert state.current_step == "STEP_4_SYNTHESIS"
    assert "story" in result.turn_response.dialogue.lower() or result.turn_response.screen_widget == "story_loading"
    assert result.auto_advance is True


@pytest.mark.asyncio
async def test_synthesis_confirm_generates_full_story(monkeypatch) -> None:
    """Confirm during synthesis: AI generates full story, no child seed."""
    state = _make_state(
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        synthesis_phase="evaluate",
        synthesis_prompt_count=1,
        collected_names=["Cloud Puff", "Mossy Dot"],
        conversation_history=[
            ConversationTurn(role="ai", text="Would you like to make up a story?", step="STEP_4_SYNTHESIS"),
        ],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        return_value=_mock_turn(dialogue="Cloud Puff and Mossy Dot went on a big adventure!")
    )

    async def _confirm(s, t):
        return ChildIntentClassification(intent="confirm")

    monkeypatch.setattr("turn_handling.core._classify_child_intent", _confirm)
    result = await resolve_turn(state, _make_input(text="yes"), agent)

    # confirm should NOT set synthesis_child_story to "yes"
    assert state.synthesis_child_story == ""
    # confirm is not a decline — counter should not increment
    assert state.synthesis_declines == 0
    # Confirm triggers loading screen first (auto-advance to generate phase)
    assert state.synthesis_phase == "generate"
    assert state.current_step == "STEP_4_SYNTHESIS"
    assert result.auto_advance is True


@pytest.mark.asyncio
async def test_synthesis_t0_substantive_generates_from_seed(monkeypatch) -> None:
    """T0 substantive response: use as story seed, generate."""
    state = _make_state(
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        tier="T0",
        synthesis_phase="evaluate",
        synthesis_prompt_count=1,
        collected_names=["Cloud Puff", "Mossy Dot"],
        conversation_history=[
            ConversationTurn(role="ai", text="Would you like to make up a story?", step="STEP_4_SYNTHESIS"),
        ],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        return_value=_mock_turn(dialogue="Cloud Puff bounced over to Mossy Dot and they snuggled up.")
    )

    async def _substantive(s, t):
        return ChildIntentClassification(intent="substantive", story_quality="weak")

    monkeypatch.setattr("turn_handling.core._classify_child_intent", _substantive)
    result = await resolve_turn(state, _make_input(text="moss go sleep"), agent)

    # T0 substantive with weak quality: routes to loading → generate phase
    assert state.synthesis_phase == "generate"
    assert state.synthesis_child_story == "moss go sleep"
    assert state.current_step == "STEP_4_SYNTHESIS"
    assert result.auto_advance is True


@pytest.mark.asyncio
async def test_synthesis_classification_failure_defaults_to_story_attempt() -> None:
    """If the classification LLM fails, default to substantive (weak) not off_topic."""
    state = _make_state(
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        tier="T1",
        synthesis_phase="evaluate",
        synthesis_prompt_count=1,
        collected_names=["Cloud Puff"],
        conversation_history=[
            ConversationTurn(role="ai", text="Tell me a story!", step="STEP_4_SYNTHESIS"),
        ],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="What happened next?"))

    # Force the classifier config lookup to fail inside generation.py so the
    # internal except branch runs. Fallback returns intent="substantive" with
    # story_quality=None, which the evaluate phase treats as weak.
    with patch("turn_handling.generation.get_settings", side_effect=RuntimeError("LLM timeout")):
        result = await resolve_turn(state, _make_input(text="cloud puff danced"), agent)

    # Should treat as weak story (T1 → improve phase), NOT as off_topic
    assert state.synthesis_phase == "improve"
    assert state.synthesis_child_story == "cloud puff danced"
    assert result.auto_advance is False


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

    result = await resolve_turn(state, _make_input(is_silent=True), agent)

    # Silence in improve triggers loading → generate (doesn't advance immediately)
    assert state.synthesis_phase == "generate"
    assert state.synthesis_child_story == "Cloud Puff met Mossy Dot."
    assert state.current_step == "STEP_4_SYNTHESIS"
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

    # First silence doesn't trigger exit (consecutive_silence == 1).
    # Advance is deferred via round_advance_pending (same as non-silent detail).
    assert state.current_step == "STEP_3_COLLECT_1"
    assert state.collection_phase == "detail"
    assert state.round_advance_pending is True
    assert result.auto_advance is True
    # Silence should NOT be recorded as a detail
    assert state.collected_details == []

    # Follow-up auto-advance flips to next round's photo mode
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="Let's keep looking!"))
    follow_up = await resolve_turn(state, _make_input(), agent)

    assert state.current_step == "STEP_3_COLLECT_2"
    assert state.collection_phase == "photo"
    assert follow_up.auto_advance is False


# ---------------------------------------------------------------------------
# Regex pattern tests
# ---------------------------------------------------------------------------


def test_item_suggestion_catches_berry() -> None:
    assert _ITEM_SUGGESTION_RE.search("Try finding a berry or a button nearby!")


def test_item_suggestion_catches_petal() -> None:
    assert _ITEM_SUGGESTION_RE.search("Look for a soft petal on the ground")


def test_item_suggestion_catches_grass() -> None:
    assert _ITEM_SUGGESTION_RE.search("Feel the grass — is it soft?")


def test_item_suggestion_allows_observation_angle() -> None:
    assert not _ITEM_SUGGESTION_RE.search("Something soft might be nearby")


def test_directive_catches_try_peeking() -> None:
    assert _DIRECTIVE_RE.search("Try peeking at something round!")


def test_directive_catches_scan_the() -> None:
    assert _DIRECTIVE_RE.search("Scan the floor for dots!")


def test_directive_catches_go_find() -> None:
    assert _DIRECTIVE_RE.search("Go find the next one!")


def test_directive_catches_look_for() -> None:
    assert _DIRECTIVE_RE.search("Look for something soft!")


def test_directive_allows_invitational() -> None:
    assert not _DIRECTIVE_RE.search("Would you like to keep looking?")


def test_directive_allows_wonder() -> None:
    assert not _DIRECTIVE_RE.search("I wonder what else is soft nearby...")


def test_directive_catches_bare_look_for_but_allows_invitational() -> None:
    """Bare 'Look for' is directive, but 'Would you like to look for' is OK."""
    bare = "Look for something soft!"
    invitational = "Would you like to look for something soft?"

    # Bare directive: should be caught
    assert _DIRECTIVE_RE.search(bare)

    # Invitational: after stripping prefix, no directive remains
    stripped = _INVITATIONAL_PREFIX_RE.sub("", invitational)
    assert not _DIRECTIVE_RE.search(stripped)


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
            self.retry_speaker_turn = AsyncMock(return_value=_mock_turn(dialogue="I wonder what else is nearby!"))

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

    response, gen_debug = await _generate_with_retry(agent, state)

    assert response.dialogue == "I wonder what else is nearby!"
    assert agent.generate_calls == 1
    agent.retry_speaker_turn.assert_awaited_once()
    assert gen_debug.final_verdict == "passed"
    assert gen_debug.attempt_count == 2


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

    response, gen_debug = await _generate_with_retry(agent, state)

    assert response.dialogue == "That one feels bumpy, like tiny pebbles."
    assert agent.generate_calls == 2
    agent.retry_speaker_turn.assert_not_awaited()
    assert gen_debug.final_verdict == "passed"
    assert gen_debug.attempt_count == 2


# ---------------------------------------------------------------------------
# rounds.py — Guardrails & advance logic
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_guardrail_premature_completion_regenerates() -> None:
    """Premature completion language mid-collection triggers corrective regeneration."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=3,
        collection_phase="photo",
        round_items=_make_round_items(),
    )
    agent = _make_agent_mock()
    # First generation (after correct photo enters detail) returns completion language.
    # Second generation (corrective retry) returns clean dialogue.
    bad_response = _mock_turn(dialogue="Your final treasure is found! Mission complete!")
    good_response = _mock_turn(dialogue="What a wonderful find! What does it remind you of?")
    agent.generate_turn = AsyncMock(side_effect=[bad_response, good_response])

    result = await resolve_turn(state, _make_input(photo_id="leaf_heart"), agent)

    # The first response contained completion language, so a second generation happened
    assert agent.generate_turn.call_count == 2
    assert "final treasure" not in result.turn_response.dialogue
    assert result.turn_response.dialogue == "What a wonderful find! What does it remind you of?"


@pytest.mark.asyncio
async def test_guardrail_force_stay_on_step_in_detail_phase() -> None:
    """Guardrail 2: force stay_on_step when in Phase B detail, even if LLM says False."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=3,
        collection_phase="photo",
        round_items=_make_round_items(),
    )
    agent = _make_agent_mock()
    # LLM returns stay_on_step=False, but entering detail phase forces it True
    agent.generate_turn = AsyncMock(
        return_value=_mock_turn(
            dialogue="What does it remind you of?",
            stay_on_step=False,
        )
    )

    # Correct photo submission transitions to detail phase; guardrail forces stay
    result = await resolve_turn(state, _make_input(photo_id="leaf_heart"), agent)

    assert state.collection_phase == "detail"
    assert len(state.collected_photos) == 1
    assert result.auto_advance is False


@pytest.mark.asyncio
async def test_guardrail_override_stay_when_collection_complete() -> None:
    """Guardrail 3: override stay_on_step when all items collected in photo phase."""
    state = _make_state(
        current_step="STEP_3_COLLECT_3",
        current_round=3,
        total_rounds=3,
        collection_phase="photo",
        collected_photos=["leaf_heart", "rock_circle", "puddle_ring"],
        round_items=_make_round_items(),
    )
    agent = _make_agent_mock()
    # LLM says stay, but collection is complete — guardrail overrides
    agent.generate_turn = AsyncMock(
        return_value=_mock_turn(
            dialogue="Would you like to keep looking?",
            stay_on_step=True,
        )
    )

    result = await resolve_turn(state, _make_input(text="yes"), agent)

    # stay_on_step should have been overridden to False, triggering advancement
    assert state.current_step == "STEP_4_SYNTHESIS"
    assert result.response_type == "synthesis"


@pytest.mark.asyncio
async def test_deferred_advance_resets_flag_and_advances() -> None:
    """Deferred advance: pending flag reset, state advances to next collect step."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=3,
        collection_phase="detail",
        collected_photos=["leaf_heart"],
        round_items=_make_round_items(),
        round_advance_pending=True,
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="Let's find the next one!"))

    # Empty turn triggers the deferred advance path
    result = await resolve_turn(state, _make_input(), agent)

    assert state.round_advance_pending is False
    assert state.current_step == "STEP_3_COLLECT_2"
    assert state.current_round == 2
    assert state.collection_phase == "photo"
    assert result.auto_advance is False


@pytest.mark.asyncio
async def test_cat5_photo_phase_no_input_deterministic_template() -> None:
    """Cat5 photo phase with no input uses deterministic template, not the LLM."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=3,
        collection_phase="photo",
        round_items=_make_round_items(),
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="LLM should not be called"))

    result = await resolve_turn(state, _make_input(), agent)

    # ScriptAgent.generate_turn should NOT have been called — deterministic template used
    agent.generate_turn.assert_not_awaited()
    # Deterministic prompts contain tone markers in brackets
    assert "[" in result.turn_response.dialogue
    assert result.auto_advance is False


@pytest.mark.asyncio
async def test_cat1_round_defers_advance_to_next_round() -> None:
    """Cat1 round: stay_on_step=False defers advance via round_advance_pending."""
    cat1_state = _make_state(
        template_type="cat1",
        activity_type="mood_changer_dog",
        creative_slots=Cat1CreativeSlots(
            game_mechanic="voice_acting",
            metaphor="A fluffy friend",
            role_title="Dog Whisperer",
            round_scenarios=["sunny day", "rainy day", "snowy day"],
            escalation_axis="weather",
            observation_detail="fluffy ears",
        ),
        current_step="STEP_3_ROUND_1",
        current_round=1,
        total_rounds=3,
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        return_value=_mock_turn(dialogue="Great job! That was a sunny voice!", stay_on_step=False)
    )

    result = await resolve_turn(cat1_state, _make_input(text="woof woof"), agent)

    assert cat1_state.round_advance_pending is True
    assert result.auto_advance is True
    # State hasn't advanced yet — that happens on the next empty turn
    assert cat1_state.current_step == "STEP_3_ROUND_1"

    # Follow-up empty turn completes the deferred advance
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="Round 2!"))
    await resolve_turn(cat1_state, _make_input(), agent)

    assert cat1_state.current_step == "STEP_3_ROUND_2"
    assert cat1_state.current_round == 2
    assert cat1_state.round_advance_pending is False


# ---------------------------------------------------------------------------
# collection.py — Wrong pick handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_first_wrong_pick_stays_on_step() -> None:
    """First wrong photo pick: consecutive_wrong=1, stays on step."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=3,
        collection_phase="photo",
        round_items=_make_round_items(),
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="Hmm, that one isn't quite right."))

    result = await resolve_turn(state, _make_input(photo_id="plain_bark"), agent)

    assert state.consecutive_wrong == 1
    assert state.current_step == "STEP_3_COLLECT_1"
    assert result.response_type == "wrong_photo"
    assert result.auto_advance is False


@pytest.mark.asyncio
async def test_second_wrong_pick_exits_gracefully() -> None:
    """Two consecutive wrong picks triggers early exit."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=3,
        collection_phase="photo",
        consecutive_wrong=1,
        round_items=_make_round_items(),
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="That's okay! See you next time!"))

    result = await resolve_turn(state, _make_input(photo_id="plain_bark"), agent)

    assert state.current_step == EARLY_EXIT
    assert state.status == "exited"
    assert result.response_type == "graceful_exit"


@pytest.mark.asyncio
async def test_correct_pick_resets_consecutive_wrong() -> None:
    """A correct pick after a previous wrong pick resets the counter."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=3,
        collection_phase="photo",
        consecutive_wrong=1,
        round_items=_make_round_items(),
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="Great find! What does it remind you of?"))

    await resolve_turn(state, _make_input(photo_id="leaf_heart"), agent)

    assert state.consecutive_wrong == 0
    assert state.collection_phase == "detail"
    assert state.collected_photos == ["leaf_heart"]


@pytest.mark.asyncio
async def test_no_photo_id_skips_collection_validation() -> None:
    """Text input without photo_id on a collect step skips wrong-pick validation."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=3,
        collection_phase="photo",
        round_items=_make_round_items(),
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="Keep looking!"))

    result = await resolve_turn(state, _make_input(text="hello"), agent)

    # No photo validation happened — response_type should NOT be "wrong_photo"
    assert result.response_type != "wrong_photo"
    assert state.consecutive_wrong == 0


# ---------------------------------------------------------------------------
# generation.py — Error paths & validation helpers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_all_attempts_fail_returns_fallback() -> None:
    """All 3 generation attempts failing returns a fallback response."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(side_effect=ScriptAgentError("LLM timeout"))

    response, gen_debug = await _generate_with_retry(agent, state)

    assert state.status == "error"
    assert "play again" in response.dialogue or "fun" in response.dialogue
    assert gen_debug.final_verdict == "error_fallback"
    assert gen_debug.attempt_count == 3


@pytest.mark.asyncio
async def test_generate_exhausted_returns_last_response() -> None:
    """All 3 attempts fail plan validation — returns last response with exhausted verdict."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        collection_phase="photo",
    )

    class _AlwaysFailPlanAgent:
        def __init__(self) -> None:
            self.last_plan: TurnPlan | None = None
            self.generate_calls = 0
            self.retry_speaker_turn = AsyncMock(return_value=_mock_turn(dialogue="Find a pillow next!"))

        async def generate_turn(self, s: SessionStateModel) -> TurnResponse:
            self.generate_calls += 1
            # Plan says do_not_suggest_items=True, but dialogue names items
            self.last_plan = TurnPlan(
                child_said="found something",
                child_emotion="excited",
                do_not_suggest_items=True,
                sensory_observation="It feels soft.",
            )
            return _mock_turn(dialogue="Find a pillow next!")

    agent = _AlwaysFailPlanAgent()

    response, gen_debug = await _generate_with_retry(agent, state)

    assert gen_debug.final_verdict == "exhausted"
    assert response.dialogue == "Find a pillow next!"
    assert gen_debug.attempt_count == 3


def test_has_completion_language_matches() -> None:
    """Completion patterns detect premature completion language."""
    assert _has_completion_language("This is your final treasure!")
    assert _has_completion_language("You found them all!")
    assert _has_completion_language("Mission complete!")
    assert _has_completion_language("Our collection is complete!")


def test_has_completion_language_rejects_normal() -> None:
    """Normal dialogue without completion language passes clean."""
    assert not _has_completion_language("What a treasure!")
    assert not _has_completion_language("Let's find more!")
    assert not _has_completion_language("Great job with that one!")


def test_ends_with_open_question_detects_wh_question() -> None:
    """Open-ended wh-questions at the end of dialogue are detected."""
    assert _ends_with_open_question("What does it look like?")
    assert _ends_with_open_question("That's wonderful! How would you describe it?")
    assert _ends_with_open_question("Nice find. I wonder what makes it so soft?")


def test_has_model_phrase_detects_scaffolding() -> None:
    """Model phrases used for scaffolding are detected in dialogue."""
    assert _has_model_phrase("I think it looks like a cloud")
    assert _has_model_phrase("Maybe it's soft like cotton")
    assert _has_model_phrase("It looks like a little pillow")
    assert not _has_model_phrase("What do you see?")


# ---------------------------------------------------------------------------
# helpers.py — History & auto-advance
# ---------------------------------------------------------------------------


def test_append_ai_turn_trims_at_history_limit() -> None:
    """Appending past _HISTORY_LIMIT trims the oldest turns."""
    state = _make_state(
        conversation_history=[
            ConversationTurn(role="ai" if i % 2 == 0 else "child", text=f"Turn {i}", step="STEP_2_MISSION")
            for i in range(_HISTORY_LIMIT)
        ]
    )
    assert len(state.conversation_history) == _HISTORY_LIMIT

    _append_ai_turn(state, "New AI turn")

    assert len(state.conversation_history) == _HISTORY_LIMIT
    # Oldest turn (Turn 0) should be gone
    assert state.conversation_history[0].text != "Turn 0"
    assert state.conversation_history[-1].text == "New AI turn"


def test_should_auto_advance_false_for_closing() -> None:
    """Closing steps should NOT auto-advance — they are terminal-adjacent."""
    state = _make_state(current_step="STEP_5_CLOSING", status="active")
    assert _should_auto_advance(state) is False

    state_cat5 = _make_state(current_step="STEP_6_CLOSING", status="active")
    assert _should_auto_advance(state_cat5) is False


# ---------------------------------------------------------------------------
# Synthesis, Core dispatcher, and Helpers tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_synthesis_decline_in_evaluate_generates_story(monkeypatch) -> None:
    """Decline during evaluate phase should increment declines and generate AI story."""
    state = _make_state(
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        synthesis_phase="evaluate",
        synthesis_prompt_count=1,
        collected_names=["Cloud Puff", "Mossy Dot"],
        conversation_history=[
            ConversationTurn(role="ai", text="Would you like to make up a story?", step="STEP_4_SYNTHESIS"),
        ],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        return_value=_mock_turn(dialogue="Cloud Puff and Mossy Dot had a grand adventure together!")
    )

    async def _decline(s, t):
        return ChildIntentClassification(intent="decline")

    monkeypatch.setattr("turn_handling.core._classify_child_intent", _decline)
    result = await resolve_turn(state, _make_input(text="no thanks"), agent)

    assert state.synthesis_declines == 1
    # Decline triggers loading → generate (doesn't advance immediately)
    assert state.current_step == "STEP_4_SYNTHESIS"
    assert state.synthesis_phase == "generate"
    assert result.auto_advance is True


@pytest.mark.asyncio
async def test_synthesis_off_topic_under_limit_reprompts(monkeypatch) -> None:
    """Off-topic with prompt_count < 2 should reprompt without advancing."""
    state = _make_state(
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        synthesis_phase="evaluate",
        synthesis_prompt_count=1,
        collected_names=["Cloud Puff"],
        conversation_history=[
            ConversationTurn(role="ai", text="Would you like to make up a story?", step="STEP_4_SYNTHESIS"),
        ],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        return_value=_mock_turn(dialogue="That's interesting! How about we tell a story about Cloud Puff?")
    )

    async def _off_topic(s, t):
        return ChildIntentClassification(intent="off_topic")

    monkeypatch.setattr("turn_handling.core._classify_child_intent", _off_topic)
    result = await resolve_turn(state, _make_input(text="I had pizza for lunch"), agent)

    assert state.synthesis_prompt_count == 2
    assert state.synthesis_unrelated == 1
    assert state.current_step == "STEP_4_SYNTHESIS"
    assert result.auto_advance is False
    assert result.response_type == "synthesis"


@pytest.mark.asyncio
async def test_synthesis_off_topic_at_limit_generates(monkeypatch) -> None:
    """Off-topic at prompt limit (2) should generate AI story and advance."""
    state = _make_state(
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        synthesis_phase="evaluate",
        synthesis_prompt_count=2,
        collected_names=["Cloud Puff"],
        conversation_history=[
            ConversationTurn(role="ai", text="Would you like to make up a story?", step="STEP_4_SYNTHESIS"),
            ConversationTurn(role="child", text="I like pizza", step="STEP_4_SYNTHESIS"),
            ConversationTurn(role="ai", text="How about a story with Cloud Puff?", step="STEP_4_SYNTHESIS"),
        ],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        return_value=_mock_turn(dialogue="Cloud Puff went on a magical journey through the garden!")
    )

    async def _off_topic(s, t):
        return ChildIntentClassification(intent="off_topic")

    monkeypatch.setattr("turn_handling.core._classify_child_intent", _off_topic)
    result = await resolve_turn(state, _make_input(text="I want a puppy"), agent)

    assert state.synthesis_unrelated == 1
    assert state.current_step == "STEP_4_SYNTHESIS"
    assert state.synthesis_phase == "generate"
    assert result.auto_advance is True


@pytest.mark.asyncio
async def test_synthesis_improve_substantive_good_advances(monkeypatch) -> None:
    """Improve phase with good combined story quality should advance past synthesis."""
    state = _make_state(
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        tier="T1",
        synthesis_phase="improve",
        synthesis_child_story="Cloud Puff jumped high.",
        collected_names=["Cloud Puff"],
        conversation_history=[
            ConversationTurn(role="ai", text="That's a great start! What happened next?", step="STEP_4_SYNTHESIS"),
        ],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        return_value=_mock_turn(dialogue="Cloud Puff jumped high and landed on a rainbow where Mossy Dot was waiting!")
    )

    async def _good_combined(s, t):
        return ChildIntentClassification(intent="substantive", story_quality="good", is_related_to_collection=True)

    # The improve phase calls _classify_child_intent from synthesis module directly
    monkeypatch.setattr("turn_handling.synthesis._classify_child_intent", _good_combined)
    # Also override the core classifier so the dispatcher routes correctly
    monkeypatch.setattr("turn_handling.core._classify_child_intent", _good_combined)

    result = await resolve_turn(state, _make_input(text="and then Mossy Dot was there waiting on a rainbow"), agent)

    assert state.current_step == "STEP_5_CELEBRATE"
    assert result.auto_advance is True
    assert result.response_type == "synthesis"


@pytest.mark.asyncio
async def test_synthesis_improve_substantive_weak_generates(monkeypatch) -> None:
    """Improve phase with weak combined story should update child_story and advance."""
    state = _make_state(
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        tier="T1",
        synthesis_phase="improve",
        synthesis_child_story="Cloud Puff sat.",
        collected_names=["Cloud Puff"],
        conversation_history=[
            ConversationTurn(role="ai", text="Can you tell me more?", step="STEP_4_SYNTHESIS"),
        ],
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        return_value=_mock_turn(dialogue="Cloud Puff sat on a big rock and looked at the stars twinkling above.")
    )

    async def _weak_combined(s, t):
        return ChildIntentClassification(intent="substantive", story_quality="weak")

    monkeypatch.setattr("turn_handling.synthesis._classify_child_intent", _weak_combined)
    monkeypatch.setattr("turn_handling.core._classify_child_intent", _weak_combined)

    result = await resolve_turn(state, _make_input(text="and looked up"), agent)

    assert state.synthesis_child_story == "Cloud Puff sat. and looked up"
    assert state.current_step == "STEP_4_SYNTHESIS"
    assert state.synthesis_phase == "generate"
    assert result.auto_advance is True


@pytest.mark.asyncio
async def test_hook_first_visit_generates_prompt() -> None:
    """Hook with no prior AI turn should generate prompt and stay on STEP_1_HOOK."""
    state = _make_state(
        current_step="STEP_1_HOOK",
        current_round=0,
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="Look what I found!"))

    result = await resolve_turn(state, _make_input(), agent)

    assert state.current_step == "STEP_1_HOOK"
    assert result.turn_response.dialogue == "Look what I found!"
    assert result.response_type == "hook"
    assert result.auto_advance is False


@pytest.mark.asyncio
async def test_single_silence_does_not_exit() -> None:
    """A single silence should increment counter but NOT trigger early exit."""
    state = _make_state(
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=3,
        collection_phase="photo",
        round_items=_make_round_items(),
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="Take your time!"))

    result = await resolve_turn(state, _make_input(is_silent=True), agent)

    assert state.consecutive_silence == 1
    assert state.current_step != EARLY_EXIT
    assert state.status == "active"
    assert result.response_type != "graceful_exit"


@pytest.mark.asyncio
async def test_celebrate_auto_advances_to_closing() -> None:
    """Cat5 STEP_5_CELEBRATE with no prior AI turn should generate and advance."""
    state = _make_state(
        current_step="STEP_5_CELEBRATE",
        current_round=3,
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(
        side_effect=[
            _mock_turn(dialogue="What an amazing adventure you had!"),
            _mock_turn(dialogue="Remember all the wonderful things you discovered today."),
        ]
    )

    result = await resolve_turn(state, _make_input(), agent)

    assert result.turn_response.dialogue == "What an amazing adventure you had!"
    # Celebrate is auto-advance and should advance toward closing
    assert result.auto_advance is True
    assert result.response_type == "celebration"
    assert state.current_step == "STEP_6_CLOSING"


@pytest.mark.asyncio
async def test_closing_marks_session_completed() -> None:
    """Cat5 STEP_6_CLOSING should mark session as completed."""
    state = _make_state(
        current_step="STEP_6_CLOSING",
        current_round=3,
    )
    agent = _make_agent_mock()
    agent.generate_turn = AsyncMock(return_value=_mock_turn(dialogue="Goodbye, Shape Scout! See you next time!"))

    result = await resolve_turn(state, _make_input(), agent)

    assert state.status == "completed"
    assert result.response_type == "closing"
    assert result.auto_advance is False


@pytest.mark.asyncio
async def test_cat5_celebrate_handler_returns_achievement_image_frame() -> None:
    """Celebrate turn must return an achievement_image frame even though state
    advances to STEP_6_CLOSING.

    Regression test for the pre-advance snapshot bug: if _get_screen_frame is
    called after _advance_state, it returns the closing concept_reveal frame
    instead and the achievement image never renders.
    """
    state = _make_state(
        current_step="STEP_5_CELEBRATE",
        current_round=3,
    )
    turn_response = _mock_turn(
        dialogue="[celebrating] You did it!",
        tone_marker="celebrating",
        screen_widget="achievement_image",
    )

    result = await _run_directive_advance(state, turn_response, emotion_tag="celebrating")

    # Critical: the screen frame returned for celebrate must be achievement_image,
    # NOT concept_reveal (even though state has now advanced to STEP_6_CLOSING).
    assert result.screen_frame.widget == "achievement_image", (
        f"celebrate should render achievement_image, got {result.screen_frame.widget}"
    )
    assert state.current_step == "STEP_6_CLOSING"
    assert result.response_type == "celebrate"


@pytest.mark.asyncio
async def test_cat5_closing_handler_sets_concept_reveal_widget() -> None:
    """Cat5 closing handler should set turn_response.screen_widget to 'concept_reveal'."""
    state = _make_state(
        current_step="STEP_6_CLOSING",
        status="active",
        template_type="cat5",
    )
    turn_response = _mock_turn(dialogue="[gentle] You learned about Form and Connection.")

    result = await _run_directive_advance(state, turn_response)

    assert result.turn_response.screen_widget == "concept_reveal", (
        f"Cat5 closing should set screen_widget to concept_reveal, got {result.turn_response.screen_widget}"
    )


@pytest.mark.asyncio
async def test_cat1_closing_handler_keeps_achievement_image_widget() -> None:
    """Cat1 closing must continue to use achievement_image — the Cat5 change is scoped."""
    state = _make_state(
        template_type="cat1",
        activity_type="mood_changer_dog",
        creative_slots=Cat1CreativeSlots(
            game_mechanic="voice_acting",
            metaphor="A fluffy friend",
            role_title="Dog Whisperer",
            round_scenarios=["sunny day", "rainy day", "snowy day"],
            escalation_axis="weather",
            observation_detail="fluffy ears",
        ),
        current_step="STEP_5_CLOSING",
        status="active",
    )
    turn_response = _mock_turn(dialogue="[gentle] You discovered so much.")

    result = await _run_directive_advance(state, turn_response)

    assert result.turn_response.screen_widget == "achievement_image", (
        f"Cat1 closing should stay on achievement_image, got {result.turn_response.screen_widget}"
    )
