"""Rubric definitions, persona profiles, and eval data models."""

from pathlib import Path

import yaml
from pydantic import BaseModel


class ChildSimResponse(BaseModel):
    """Output from the child simulator."""

    text: str = ""
    photo_id: str | None = None
    is_silent: bool = False


class Persona(BaseModel):
    """Child behavior profile for simulation."""

    name: str
    tier: str
    description: str
    correct_pct: int
    wrong_pct: int
    silence_pct: int


class StepRubric(BaseModel):
    """Defines which dimensions the judge scores for a step."""

    dimensions: list[str]
    weight: int


class StepScore(BaseModel):
    """Judge output for one step."""

    step: str
    scores: dict[str, int]
    justifications: dict[str, str]
    critical_failures: list[str]


class SessionJudgement(BaseModel):
    """Full judge output for one session."""

    step_scores: list[StepScore]
    overall_score: float
    critical_failures: list[str]
    summary: str


class TurnRecord(BaseModel):
    """One turn in a session transcript."""

    turn_number: int
    step: str
    ai_dialogue: str
    child_input: ChildSimResponse
    session_state: dict
    rule_scores: dict[str, float]


class SessionTranscript(BaseModel):
    """Full session recording."""

    session_id: str
    activity: str
    tier: str
    persona: str
    model: str
    timestamp: str
    correct_items_by_round: list[list[str]]
    turns: list[TurnRecord]
    final_status: str
    total_turns: int
    rule_score: float = 0.0
    variety_score: float = 0.0


class Thresholds(BaseModel):
    combined_score_min: int = 80
    critical_failures_max: int = 0
    cross_session_variety_min: int = 70


class EvalConfig(BaseModel):
    sessions_per_combo: int = 5
    entities: list[str] = ["dandelion", "ladybug"]  # entity names for /api/start-deep-link
    tiers: list[str] = ["T0", "T1", "T2"]
    server_url: str = "http://localhost:8000"
    output_dir: str = "eval_results"
    thresholds: Thresholds = Thresholds()
    child_sim_model: str = "gemini-2.0-flash"
    judge_model: str = "gemini-2.0-flash"


PERSONAS: list[Persona] = [
    Persona(
        name="curious_toddler",
        tier="T0",
        description="Engaged, points at things, 1-3 word answers",
        correct_pct=85,
        wrong_pct=10,
        silence_pct=5,
    ),
    Persona(
        name="shy_toddler",
        tier="T0",
        description="Minimal words, sometimes silent",
        correct_pct=70,
        wrong_pct=10,
        silence_pct=20,
    ),
    Persona(
        name="distracted_toddler",
        tier="T0",
        description="Off-topic, picks wrong photos",
        correct_pct=50,
        wrong_pct=30,
        silence_pct=20,
    ),
    Persona(
        name="eager_explorer",
        tier="T1",
        description="Follows instructions, asks questions",
        correct_pct=90,
        wrong_pct=5,
        silence_pct=5,
    ),
    Persona(
        name="daydreamer",
        tier="T1",
        description="Slow to respond, sometimes off-topic",
        correct_pct=60,
        wrong_pct=20,
        silence_pct=20,
    ),
    Persona(
        name="contrarian",
        tier="T1",
        description="Says no, picks wrong things on purpose",
        correct_pct=40,
        wrong_pct=50,
        silence_pct=10,
    ),
    Persona(
        name="analytical",
        tier="T2",
        description="Full sentences, observant",
        correct_pct=90,
        wrong_pct=5,
        silence_pct=5,
    ),
    Persona(
        name="impatient",
        tier="T2",
        description="Short answers, wants to rush",
        correct_pct=80,
        wrong_pct=15,
        silence_pct=5,
    ),
    Persona(
        name="storyteller",
        tier="T2",
        description="Elaborate answers, tangential",
        correct_pct=75,
        wrong_pct=15,
        silence_pct=10,
    ),
]

STEP_RUBRICS: dict[str, StepRubric] = {
    "HOOK": StepRubric(dimensions=["age_appropriateness", "emotional_warmth", "no_question_rule"], weight=15),
    "MISSION": StepRubric(dimensions=["invitational_tone", "brevity", "clarity"], weight=10),
    "COLLECT": StepRubric(
        dimensions=["scaffolding_quality", "engagement_recovery", "variety", "celebration"], weight=35
    ),
    "SYNTHESIS": StepRubric(
        dimensions=["narrative_coherence", "age_appropriateness", "references_collected"], weight=20
    ),
    "CELEBRATE": StepRubric(dimensions=["emotional_warmth", "role_title_usage", "session_recall"], weight=10),
    "CLOSING": StepRubric(dimensions=["ib_concept_weaving", "natural_goodbye"], weight=10),
}

TIER_AGE_RANGES: dict[str, str] = {"T0": "2-4", "T1": "4-6", "T2": "6-8"}

STEP_TO_RUBRIC: dict[str, str] = {
    "STEP_1_HOOK": "HOOK",
    "STEP_2_MISSION": "MISSION",
    "STEP_4_SYNTHESIS": "SYNTHESIS",
    "STEP_5_CELEBRATE": "CELEBRATE",
    "STEP_6_CLOSING": "CLOSING",
}


def step_to_rubric_label(step: str) -> str:
    """Map a codebase step name to a rubric label; defaults to COLLECT."""
    return STEP_TO_RUBRIC.get(step, "COLLECT")


_CONFIG_PATH = Path(__file__).resolve().parent.parent / "eval_config.yaml"


def load_eval_config(path: Path | None = None) -> EvalConfig:
    """Load eval config from YAML, falling back to defaults."""
    p = path or _CONFIG_PATH
    if p.exists():
        with open(p) as f:
            data = yaml.safe_load(f) or {}
        return EvalConfig(**data)
    return EvalConfig()
