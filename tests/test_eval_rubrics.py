"""Tests for eval rubric data models."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from eval.rubrics import (
    PERSONAS,
    STEP_RUBRICS,
    ChildSimResponse,
    EvalConfig,
    SessionTranscript,
    StepScore,
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
    assert len(config.activities) >= 1
    assert len(config.tiers) >= 1
    assert config.thresholds.combined_score_min > 0
