"""Tests for debug payload helpers in turn_handler."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
from schemas.session_state import SessionStateModel
from schemas.turn_response import TurnResponse
from turn_handling import (
    GenerationDebugInfo,
    _build_debug_payload,
    _build_phase_timeline,
    _build_step_flow,
    _generate_with_retry,
)


def _make_cat1_state(**overrides: object) -> SessionStateModel:
    defaults: dict = {
        "session_id": "test",
        "tier": "T0",
        "template_type": "cat1",
        "activity_type": "mood_changer_dog",
        "current_step": "STEP_3_ROUND_2",
        "current_round": 2,
        "total_rounds": 3,
        "creative_slots": Cat1CreativeSlots(
            game_mechanic="voice_acting",
            metaphor="A fluffy friend",
            role_title="Dog Whisperer",
            round_scenarios=["at home", "at a party", "in space"],
            escalation_axis="everyday to wild",
            observation_detail="floppy ears",
        ),
        "entity_name": "dog",
        "status": "active",
    }
    defaults.update(overrides)
    return SessionStateModel(**defaults)


def _make_cat5_state(**overrides: object) -> SessionStateModel:
    defaults: dict = {
        "session_id": "test",
        "tier": "T0",
        "template_type": "cat5",
        "activity_type": "fluffy_expedition_dandelion",
        "current_step": "STEP_3_COLLECT_2",
        "current_round": 2,
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


# ---------------------------------------------------------------------------
# _build_step_flow
# ---------------------------------------------------------------------------


class TestBuildStepFlow:
    def test_cat1_three_rounds(self) -> None:
        state = _make_cat1_state(current_step="STEP_3_ROUND_2", total_rounds=3)
        flow = _build_step_flow(state)

        assert len(flow) == 7  # hook + rules + 3 rounds + celebrate + closing
        assert flow[0] == {"step": "STEP_1_HOOK", "status": "done"}
        assert flow[1] == {"step": "STEP_2_RULES", "status": "done"}
        assert flow[2] == {"step": "STEP_3_ROUND_1", "status": "done"}
        assert flow[3] == {"step": "STEP_3_ROUND_2", "status": "current"}
        assert flow[4] == {"step": "STEP_3_ROUND_3", "status": "pending"}
        assert flow[5] == {"step": "STEP_4_CELEBRATE", "status": "pending"}
        assert flow[6] == {"step": "STEP_5_CLOSING", "status": "pending"}

    def test_cat5_three_rounds(self) -> None:
        state = _make_cat5_state(current_step="STEP_4_SYNTHESIS", total_rounds=3)
        flow = _build_step_flow(state)

        assert len(flow) == 8  # hook + mission + 3 collects + synthesis + celebrate + closing
        assert flow[0] == {"step": "STEP_1_HOOK", "status": "done"}
        assert flow[1] == {"step": "STEP_2_MISSION", "status": "done"}
        assert flow[4] == {"step": "STEP_3_COLLECT_3", "status": "done"}
        assert flow[5] == {"step": "STEP_4_SYNTHESIS", "status": "current"}
        assert flow[6] == {"step": "STEP_5_CELEBRATE", "status": "pending"}
        assert flow[7] == {"step": "STEP_6_CLOSING", "status": "pending"}

    def test_hook_step_marks_all_others_pending(self) -> None:
        state = _make_cat1_state(current_step="STEP_1_HOOK", total_rounds=2)
        flow = _build_step_flow(state)

        assert flow[0]["status"] == "current"
        assert all(f["status"] == "pending" for f in flow[1:])

    def test_closing_step_marks_all_others_done(self) -> None:
        state = _make_cat1_state(current_step="STEP_5_CLOSING", total_rounds=2)
        flow = _build_step_flow(state)

        assert all(f["status"] == "done" for f in flow[:-1])
        assert flow[-1]["status"] == "current"


# ---------------------------------------------------------------------------
# _build_debug_payload
# ---------------------------------------------------------------------------


class TestBuildDebugPayload:
    def test_includes_all_sections(self) -> None:
        state = _make_cat1_state()
        gen_debug = GenerationDebugInfo(
            step="STEP_3_ROUND_2",
            attempt_count=1,
            final_verdict="passed",
            attempts=[{"attempt": 1, "verdict": "passed", "hint": ""}],
        )
        agent = AsyncMock()
        agent.last_plan = None

        payload = _build_debug_payload(state, gen_debug, agent)

        assert "generation" in payload
        assert "retry_stats" in payload
        assert "step_flow" in payload
        assert payload["generation"]["attempt_count"] == 1
        assert payload["generation"]["final_verdict"] == "passed"

    def test_includes_planner_when_available(self) -> None:
        state = _make_cat1_state()
        agent = AsyncMock()
        agent.last_plan = AsyncMock()
        agent.last_plan.do_not_suggest_items = True
        agent.last_plan.offer_binary_choice = False
        agent.last_plan.must_model_first = True
        agent.last_plan.do_not_ask_question = False
        agent.last_plan.emotion_tag = "excited"
        agent.last_plan.question_type = "binary"

        payload = _build_debug_payload(state, None, agent)

        assert "planner" in payload
        assert payload["planner"]["do_not_suggest_items"] is True
        assert payload["planner"]["emotion_tag"] == "excited"

    def test_no_planner_when_none(self) -> None:
        state = _make_cat1_state()
        agent = AsyncMock()
        agent.last_plan = None

        payload = _build_debug_payload(state, None, agent)

        assert "planner" not in payload


# ---------------------------------------------------------------------------
# _generate_with_retry returns debug info
# ---------------------------------------------------------------------------


class TestGenerateWithRetryDebugInfo:
    @pytest.mark.asyncio
    async def test_first_pass_success(self) -> None:
        agent = AsyncMock()
        agent.generate_turn = AsyncMock(
            return_value=TurnResponse(
                dialogue="[excited] Hello!",
                tone_marker="excited",
                screen_widget="character_display",
                screen_widget_params={},
            )
        )
        agent.last_plan = None
        agent.retry_speaker_turn = AsyncMock()

        state = _make_cat1_state(current_step="STEP_1_HOOK")

        response, gen_debug = await _generate_with_retry(agent, state, is_first_on_step=True)

        assert response.dialogue == "[excited] Hello!"
        assert gen_debug.attempt_count == 1
        assert gen_debug.final_verdict == "passed"
        assert len(gen_debug.attempts) == 1
        assert gen_debug.attempts[0]["verdict"] == "passed"


# ---------------------------------------------------------------------------
# _build_phase_timeline — Cat5 collection
# ---------------------------------------------------------------------------


class TestBuildPhaseTimelineCat5Collection:
    def test_photo_phase_all_details_pending(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_3_COLLECT_1",
            tier="T1",
            collection_phase="photo",
            detail_exchange_count=0,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 3  # photo + 2 detail slots (T1 max=2)
        assert timeline[0] == {"phase": "photo", "status": "current", "label": "Photo", "meta": None}
        assert timeline[1] == {"phase": "detail", "status": "pending", "label": "Detail 1/2", "meta": None}
        assert timeline[2] == {
            "phase": "detail",
            "status": "pending",
            "label": "Detail 2/2",
            "meta": {"round_advance_pending": False},
        }

    def test_detail_phase_first_exchange(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_3_COLLECT_2",
            tier="T2",
            collection_phase="detail",
            detail_exchange_count=0,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 4  # photo + 3 detail slots (T2 max=3)
        assert timeline[0] == {"phase": "photo", "status": "done", "label": "Photo", "meta": None}
        assert timeline[1] == {"phase": "detail", "status": "current", "label": "Detail 1/3", "meta": None}
        assert timeline[2] == {"phase": "detail", "status": "pending", "label": "Detail 2/3", "meta": None}
        assert timeline[3] == {
            "phase": "detail",
            "status": "pending",
            "label": "Detail 3/3",
            "meta": {"round_advance_pending": False},
        }

    def test_detail_phase_mid_exchange(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_3_COLLECT_1",
            tier="T2",
            collection_phase="detail",
            detail_exchange_count=1,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert timeline[0] == {"phase": "photo", "status": "done", "label": "Photo", "meta": None}
        assert timeline[1] == {"phase": "detail", "status": "done", "label": "Detail 1/3", "meta": None}
        assert timeline[2] == {"phase": "detail", "status": "current", "label": "Detail 2/3", "meta": None}
        assert timeline[3] == {
            "phase": "detail",
            "status": "pending",
            "label": "Detail 3/3",
            "meta": {"round_advance_pending": False},
        }

    def test_round_advance_pending(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_3_COLLECT_1",
            tier="T0",
            collection_phase="detail",
            detail_exchange_count=1,
            round_advance_pending=True,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        # T0 max=1, so: photo(done) + detail 1/1(done)
        assert len(timeline) == 2
        assert timeline[1] == {
            "phase": "detail",
            "status": "done",
            "label": "Detail 1/1",
            "meta": {"round_advance_pending": True},
        }

    def test_t0_single_detail_slot(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_3_COLLECT_1",
            tier="T0",
            collection_phase="photo",
            detail_exchange_count=0,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 2  # photo + 1 detail (T0 max=1)


# ---------------------------------------------------------------------------
# _build_phase_timeline — Cat5 synthesis
# ---------------------------------------------------------------------------


class TestBuildPhaseTimelineCat5Synthesis:
    def test_invite_phase(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_4_SYNTHESIS",
            tier="T1",
            synthesis_phase="invite",
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 4  # invite, evaluate, improve, generate (T1 has improve)
        assert timeline[0] == {"phase": "invite", "status": "current", "label": "Invite", "meta": None}
        assert timeline[1] == {"phase": "evaluate", "status": "pending", "label": "Evaluate", "meta": None}
        assert timeline[2] == {"phase": "improve", "status": "pending", "label": "Improve", "meta": None}
        assert timeline[3] == {"phase": "generate", "status": "pending", "label": "Generate", "meta": None}

    def test_evaluate_phase(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_4_SYNTHESIS",
            tier="T2",
            synthesis_phase="evaluate",
            synthesis_prompt_count=1,
            synthesis_story_quality="weak",
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert timeline[0]["status"] == "done"
        assert timeline[1] == {
            "phase": "evaluate",
            "status": "current",
            "label": "Evaluate",
            "meta": {"prompt_count": 1, "story_quality": "weak"},
        }
        assert timeline[2]["status"] == "pending"

    def test_t0_skips_improve(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_4_SYNTHESIS",
            tier="T0",
            synthesis_phase="invite",
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 3  # invite, evaluate, generate (no improve for T0)
        phases = [e["phase"] for e in timeline]
        assert "improve" not in phases

    def test_generate_phase_all_done(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_4_SYNTHESIS",
            tier="T1",
            synthesis_phase="generate",
            synthesis_prompt_count=2,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert timeline[0]["status"] == "done"  # invite
        assert timeline[1]["status"] == "done"  # evaluate
        assert timeline[2]["status"] == "done"  # improve
        assert timeline[3] == {
            "phase": "generate",
            "status": "current",
            "label": "Generate",
            "meta": {"prompt_count": 2},
        }

    def test_improve_phase(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_4_SYNTHESIS",
            tier="T2",
            synthesis_phase="improve",
            synthesis_prompt_count=1,
            synthesis_story_quality="good",
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert timeline[0]["status"] == "done"  # invite
        assert timeline[1]["status"] == "done"  # evaluate
        assert timeline[2] == {
            "phase": "improve",
            "status": "current",
            "label": "Improve",
            "meta": {"prompt_count": 1, "story_quality": "good"},
        }
        assert timeline[3]["status"] == "pending"  # generate


# ---------------------------------------------------------------------------
# _build_phase_timeline — Cat1 invitation
# ---------------------------------------------------------------------------


class TestBuildPhaseTimelineCat1Invitation:
    def test_initial_invite(self) -> None:
        state = _make_cat1_state(
            current_step="STEP_2_RULES",
            invitation_decline_count=0,
            invitation_accepted=False,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 1
        assert timeline[0] == {"phase": "invite", "status": "current", "label": "Invite", "meta": None}

    def test_one_decline(self) -> None:
        state = _make_cat1_state(
            current_step="STEP_2_RULES",
            invitation_decline_count=1,
            invitation_accepted=False,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 2
        assert timeline[0] == {"phase": "invite", "status": "done", "label": "Invite", "meta": None}
        assert timeline[1] == {"phase": "decline", "status": "current", "label": "Decline 1", "meta": None}

    def test_two_declines(self) -> None:
        state = _make_cat1_state(
            current_step="STEP_2_RULES",
            invitation_decline_count=2,
            invitation_accepted=False,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 3
        assert timeline[0]["status"] == "done"
        assert timeline[1] == {"phase": "decline", "status": "done", "label": "Decline 1", "meta": None}
        assert timeline[2] == {"phase": "decline", "status": "current", "label": "Decline 2", "meta": None}

    def test_accepted(self) -> None:
        state = _make_cat1_state(
            current_step="STEP_2_RULES",
            invitation_accepted=True,
            invitation_decline_count=0,
        )
        timeline = _build_phase_timeline(state)

        assert timeline is not None
        assert len(timeline) == 1
        assert timeline[0] == {"phase": "invite", "status": "done", "label": "Invite", "meta": {"accepted": True}}

    def test_non_rules_step_returns_none(self) -> None:
        state = _make_cat1_state(current_step="STEP_3_ROUND_1")
        timeline = _build_phase_timeline(state)

        assert timeline is None

    def test_cat5_non_collection_returns_none(self) -> None:
        state = _make_cat5_state(current_step="STEP_1_HOOK")
        timeline = _build_phase_timeline(state)

        assert timeline is None


# ---------------------------------------------------------------------------
# _build_debug_payload — phase_timeline integration
# ---------------------------------------------------------------------------


class TestDebugPayloadPhaseTimeline:
    def test_cat5_collection_includes_timeline(self) -> None:
        state = _make_cat5_state(
            current_step="STEP_3_COLLECT_1",
            tier="T1",
            collection_phase="detail",
            detail_exchange_count=1,
        )
        agent = AsyncMock()
        agent.last_plan = None
        agent.last_best_of_n = None

        payload = _build_debug_payload(state, None, agent)

        assert "phase_timeline" in payload
        assert len(payload["phase_timeline"]) == 3  # photo + 2 details (T1)

    def test_cat1_round_excludes_timeline(self) -> None:
        state = _make_cat1_state(current_step="STEP_3_ROUND_1")
        agent = AsyncMock()
        agent.last_plan = None
        agent.last_best_of_n = None

        payload = _build_debug_payload(state, None, agent)

        assert "phase_timeline" not in payload

    def test_cat1_rules_includes_timeline(self) -> None:
        state = _make_cat1_state(
            current_step="STEP_2_RULES",
            invitation_decline_count=1,
        )
        agent = AsyncMock()
        agent.last_plan = None
        agent.last_best_of_n = None

        payload = _build_debug_payload(state, None, agent)

        assert "phase_timeline" in payload
        assert len(payload["phase_timeline"]) == 2  # invite + decline 1
