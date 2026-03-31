"""Tests for eval rubric data models."""

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from eval.child_sim import ChildSimContext, ChildSimulator
from eval.judge import EvalJudge
from eval.report import generate_markdown_report, generate_summary_json
from eval.rubrics import (
    PERSONAS,
    STEP_RUBRICS,
    ChildSimResponse,
    EvalConfig,
    SessionJudgement,
    SessionTranscript,
    StepScore,
    Thresholds,
    TurnRecord,
    load_eval_config,
)


def test_child_sim_response_defaults() -> None:
    r = ChildSimResponse()
    assert r.text == ""
    assert r.photo_id is None
    assert r.is_silent is False


def test_child_sim_response_photo() -> None:
    r = ChildSimResponse(photo_id="fuzzy_moss")
    assert r.photo_id == "fuzzy_moss"
    assert r.text == ""


def test_personas_cover_all_tiers() -> None:
    for tier in ("T0", "T1", "T2"):
        tier_personas = [p for p in PERSONAS if p.tier == tier]
        assert len(tier_personas) == 3, f"Expected 3 personas for {tier}"


def test_persona_probabilities_sum_to_100() -> None:
    for p in PERSONAS:
        total = p.correct_pct + p.wrong_pct + p.silence_pct
        assert total == 100, f"{p.name} probabilities sum to {total}"


def test_step_rubrics_cover_all_steps() -> None:
    expected = {"HOOK", "MISSION", "COLLECT", "SYNTHESIS", "CELEBRATE", "CLOSING"}
    assert set(STEP_RUBRICS.keys()) == expected


def test_step_rubric_weights_sum_to_100() -> None:
    total = sum(r.weight for r in STEP_RUBRICS.values())
    assert total == 100


def test_step_score_model() -> None:
    s = StepScore(
        step="HOOK",
        scores={"age_appropriateness": 4, "emotional_warmth": 5},
        justifications={"age_appropriateness": "good", "emotional_warmth": "great"},
        critical_failures=[],
    )
    assert s.step == "HOOK"
    assert s.scores["emotional_warmth"] == 5


def test_turn_record_model() -> None:
    t = TurnRecord(
        turn_number=0,
        step="STEP_1_HOOK",
        ai_dialogue="[excited] Wow!",
        child_input=ChildSimResponse(text="hi"),
        session_state={},
        rule_scores={"validation_pass": 1.0},
    )
    assert t.ai_dialogue == "[excited] Wow!"


def test_load_eval_config() -> None:
    config = load_eval_config()
    assert config.sessions_per_combo >= 1
    assert len(config.entities) >= 1
    assert len(config.tiers) >= 1
    assert config.thresholds.combined_score_min > 0


def test_child_sim_context_model() -> None:
    ctx = ChildSimContext(
        persona="curious_toddler",
        tier="T0",
        activity_name="fluffy_expedition_dandelion",
        collection_criterion="Find fluffy things",
        current_step="STEP_3_COLLECT_1",
        collection_phase="photo",
        round_items=[{"id": "fuzzy_moss", "label": "Fuzzy moss", "correct": True}],
        last_ai_dialogue="[excited] Wow! Let's find fluffy things!",
        collected_names=[],
        turn_number=3,
    )
    assert ctx.persona == "curious_toddler"


def test_child_sim_parses_text_response() -> None:
    sim = ChildSimulator(model="test-model", api_key="fake", base_url="http://fake")
    raw = '{"text": "soft fuzzy"}'
    result = sim.parse_response(raw)
    assert result.text == "soft fuzzy"
    assert result.photo_id is None


def test_child_sim_parses_photo_response() -> None:
    sim = ChildSimulator(model="test-model", api_key="fake", base_url="http://fake")
    raw = '{"photo_id": "fuzzy_moss"}'
    result = sim.parse_response(raw)
    assert result.photo_id == "fuzzy_moss"


def test_child_sim_parses_silence() -> None:
    sim = ChildSimulator(model="test-model", api_key="fake", base_url="http://fake")
    raw = '{"is_silent": true}'
    result = sim.parse_response(raw)
    assert result.is_silent is True


def test_child_sim_fallback_on_bad_json() -> None:
    sim = ChildSimulator(model="test-model", api_key="fake", base_url="http://fake")
    result = sim.parse_response("just some random text")
    assert result.text == "just some random text"


# --- Judge tests ---


def test_judge_parses_valid_json() -> None:
    judge = EvalJudge(model="test", api_key="fake", base_url="http://fake")
    raw = json.dumps(
        {
            "step_scores": [
                {
                    "step": "HOOK",
                    "scores": {"age_appropriateness": 4, "emotional_warmth": 5, "no_question_rule": 5},
                    "justifications": {
                        "age_appropriateness": "good",
                        "emotional_warmth": "warm",
                        "no_question_rule": "ok",
                    },
                    "critical_failures": [],
                }
            ],
            "critical_failures": [],
            "summary": "Good session.",
        }
    )
    result = judge.parse_judgement(raw)
    assert len(result.step_scores) == 1
    assert result.step_scores[0].scores["emotional_warmth"] == 5
    assert result.summary == "Good session."


def test_judge_fallback_on_bad_json() -> None:
    judge = EvalJudge(model="test", api_key="fake", base_url="http://fake")
    result = judge.parse_judgement("not json at all")
    assert result.overall_score == 1.0
    assert len(result.critical_failures) > 0


# --- Report tests ---


def _make_transcript(activity: str = "fluffy_expedition_dandelion", tier: str = "T0") -> SessionTranscript:
    return SessionTranscript(
        session_id="test-1",
        activity=activity,
        tier=tier,
        persona="curious_toddler",
        model="test-model",
        timestamp="2026-03-30T14:00:00Z",
        correct_items_by_round=[["fuzzy_moss"]],
        turns=[],
        final_status="completed",
        total_turns=8,
        rule_score=85.0,
        variety_score=0.8,
    )


def _make_judgement() -> SessionJudgement:
    return SessionJudgement(
        step_scores=[
            StepScore(
                step="HOOK",
                scores={"emotional_warmth": 4},
                justifications={"emotional_warmth": "ok"},
                critical_failures=[],
            ),
        ],
        overall_score=4.0,
        critical_failures=[],
        summary="Good session.",
    )


def test_generate_summary_json() -> None:
    transcripts = [_make_transcript()]
    judgements = [_make_judgement()]
    summary = generate_summary_json(transcripts, judgements, Thresholds())
    assert summary["status"] in ("PASS", "FAIL")
    assert "combos" in summary


def test_generate_markdown_report() -> None:
    transcripts = [_make_transcript()]
    judgements = [_make_judgement()]
    md = generate_markdown_report(transcripts, judgements, Thresholds())
    assert "# Eval Report" in md
    assert "fluffy_expedition_dandelion" in md
