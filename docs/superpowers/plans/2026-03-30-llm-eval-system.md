# LLM-Driven Eval System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an automated eval system that runs Cat5 game sessions with LLM-generated child inputs and scores AI dialogue quality via rule-based + LLM judge scoring.

**Architecture:** An eval runner orchestrates sessions against the live API. A child simulator LLM generates age-appropriate inputs per persona. After each session, a rule scorer (`scripts/scoring.py`) and LLM judge produce per-step quality scores. Results aggregate into JSON + markdown reports with CI pass/fail thresholds.

**Tech Stack:** Python 3.12+, httpx (async), Pydantic v2, PyYAML, Gemini via OpenAI-compatible API

**Spec:** `docs/superpowers/specs/2026-03-30-llm-eval-system-design.md`

---

## File Map

| File | Responsibility |
|------|---------------|
| `backend/eval/__init__.py` | Package marker |
| `backend/eval/rubrics.py` | Rubric dataclasses, persona definitions, step-dimension mapping |
| `backend/eval/child_sim.py` | Child simulator — LLM prompt + output parsing |
| `backend/eval/judge.py` | LLM judge — per-step rubric scoring |
| `backend/eval/runner.py` | Session orchestrator — API calls, scoring, transcript collection |
| `backend/eval/report.py` | Report generator — JSON summary + markdown |
| `backend/eval_config.yaml` | Default eval configuration |
| `scripts/run_eval.py` | CLI entrypoint |
| `tests/test_eval_rubrics.py` | Unit tests for rubrics + child sim + judge parsing |
| `tests/test_eval_runner.py` | Integration test for runner (1 session, mocked LLMs) |

---

### Task 1: Rubrics and data models

**Files:**
- Create: `backend/eval/__init__.py`
- Create: `backend/eval/rubrics.py`
- Create: `backend/eval_config.yaml`
- Test: `tests/test_eval_rubrics.py`

- [ ] **Step 1: Write tests for rubric models**

```python
# tests/test_eval_rubrics.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest ../tests/test_eval_rubrics.py -v`
Expected: FAIL — modules don't exist yet

- [ ] **Step 3: Create package and rubrics module**

```python
# backend/eval/__init__.py
"""LLM-driven evaluation system for Cat5 games."""
```

```python
# backend/eval/rubrics.py
"""Rubric definitions, persona profiles, and eval data models."""

from pathlib import Path

import yaml
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

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
    correct_pct: int    # photo selection: % correct picks
    wrong_pct: int      # % wrong picks
    silence_pct: int    # % silent turns


class StepRubric(BaseModel):
    """Defines which dimensions the judge scores for a step."""
    dimensions: list[str]
    weight: int  # percent, must sum to 100 across all steps


class StepScore(BaseModel):
    """Judge output for one step."""
    step: str
    scores: dict[str, int]          # dimension → 1-5
    justifications: dict[str, str]  # dimension → brief text
    critical_failures: list[str]


class SessionJudgement(BaseModel):
    """Full judge output for one session."""
    step_scores: list[StepScore]
    overall_score: float            # weighted 1-5
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
    activities: list[str] = ["fluffy_expedition_dandelion", "polka_dot_patrol"]
    tiers: list[str] = ["T0", "T1", "T2"]
    server_url: str = "http://localhost:8000"
    output_dir: str = "eval_results"
    thresholds: Thresholds = Thresholds()
    child_sim_model: str = "gemini-2.0-flash"
    judge_model: str = "gemini-2.0-flash"


# ---------------------------------------------------------------------------
# Persona definitions
# ---------------------------------------------------------------------------

PERSONAS: list[Persona] = [
    # T0
    Persona(name="curious_toddler", tier="T0", description="Engaged, points at things, 1-3 word answers", correct_pct=85, wrong_pct=10, silence_pct=5),
    Persona(name="shy_toddler", tier="T0", description="Minimal words, sometimes silent", correct_pct=70, wrong_pct=10, silence_pct=20),
    Persona(name="distracted_toddler", tier="T0", description="Off-topic, picks wrong photos", correct_pct=50, wrong_pct=30, silence_pct=20),
    # T1
    Persona(name="eager_explorer", tier="T1", description="Follows instructions, asks questions", correct_pct=90, wrong_pct=5, silence_pct=5),
    Persona(name="daydreamer", tier="T1", description="Slow to respond, sometimes off-topic", correct_pct=60, wrong_pct=20, silence_pct=20),
    Persona(name="contrarian", tier="T1", description="Says no, picks wrong things on purpose", correct_pct=40, wrong_pct=50, silence_pct=10),
    # T2
    Persona(name="analytical", tier="T2", description="Full sentences, observant", correct_pct=90, wrong_pct=5, silence_pct=5),
    Persona(name="impatient", tier="T2", description="Short answers, wants to rush", correct_pct=80, wrong_pct=15, silence_pct=5),
    Persona(name="storyteller", tier="T2", description="Elaborate answers, tangential", correct_pct=75, wrong_pct=15, silence_pct=10),
]


# ---------------------------------------------------------------------------
# Step rubrics
# ---------------------------------------------------------------------------

STEP_RUBRICS: dict[str, StepRubric] = {
    "HOOK": StepRubric(dimensions=["age_appropriateness", "emotional_warmth", "no_question_rule"], weight=15),
    "MISSION": StepRubric(dimensions=["invitational_tone", "brevity", "clarity"], weight=10),
    "COLLECT": StepRubric(dimensions=["scaffolding_quality", "engagement_recovery", "variety", "celebration"], weight=35),
    "SYNTHESIS": StepRubric(dimensions=["narrative_coherence", "age_appropriateness", "references_collected"], weight=20),
    "CELEBRATE": StepRubric(dimensions=["emotional_warmth", "role_title_usage", "session_recall"], weight=10),
    "CLOSING": StepRubric(dimensions=["ib_concept_weaving", "natural_goodbye"], weight=10),
}

# Step name → rubric label mapping
STEP_TO_RUBRIC: dict[str, str] = {
    "STEP_1_HOOK": "HOOK",
    "STEP_2_MISSION": "MISSION",
    "STEP_4_SYNTHESIS": "SYNTHESIS",
    "STEP_5_CELEBRATE": "CELEBRATE",
    "STEP_6_CLOSING": "CLOSING",
}


def step_to_rubric_label(step: str) -> str:
    """Map a codebase step name to a rubric label."""
    if step in STEP_TO_RUBRIC:
        return STEP_TO_RUBRIC[step]
    if step.startswith("STEP_3_COLLECT_"):
        return "COLLECT"
    return "COLLECT"  # fallback for round steps


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "eval_config.yaml"


def load_eval_config(path: Path | None = None) -> EvalConfig:
    """Load eval config from YAML, falling back to defaults."""
    p = path or _CONFIG_PATH
    if p.exists():
        with open(p) as f:
            data = yaml.safe_load(f) or {}
        return EvalConfig(**data)
    return EvalConfig()
```

```yaml
# backend/eval_config.yaml
sessions_per_combo: 5
activities:
  - fluffy_expedition_dandelion
  - polka_dot_patrol
tiers: [T0, T1, T2]
server_url: "http://localhost:8000"
output_dir: "eval_results"

thresholds:
  combined_score_min: 80
  critical_failures_max: 0
  cross_session_variety_min: 70

child_sim_model: "gemini-2.0-flash"
judge_model: "gemini-2.0-flash"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && uv run pytest ../tests/test_eval_rubrics.py -v`
Expected: All PASS

- [ ] **Step 5: Lint**

Run: `cd backend && uv run ruff check eval/rubrics.py && uv run ruff format eval/rubrics.py`

- [ ] **Step 6: Commit**

```bash
git add backend/eval/ backend/eval_config.yaml tests/test_eval_rubrics.py
git commit -m "feat(eval): add rubric models, personas, and eval config"
```

---

### Task 2: Child simulator

**Files:**
- Create: `backend/eval/child_sim.py`
- Test: `tests/test_eval_rubrics.py` (append)

- [ ] **Step 1: Write tests for child sim output parsing**

Append to `tests/test_eval_rubrics.py`:

```python
from unittest.mock import AsyncMock, patch

from eval.child_sim import ChildSimulator, ChildSimContext


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


@pytest.mark.asyncio
async def test_child_sim_parses_text_response() -> None:
    sim = ChildSimulator(model="test-model", api_key="fake", base_url="http://fake")
    raw = '{"text": "soft fuzzy"}'
    result = sim.parse_response(raw)
    assert result.text == "soft fuzzy"
    assert result.photo_id is None


@pytest.mark.asyncio
async def test_child_sim_parses_photo_response() -> None:
    sim = ChildSimulator(model="test-model", api_key="fake", base_url="http://fake")
    raw = '{"photo_id": "fuzzy_moss"}'
    result = sim.parse_response(raw)
    assert result.photo_id == "fuzzy_moss"


@pytest.mark.asyncio
async def test_child_sim_parses_silence() -> None:
    sim = ChildSimulator(model="test-model", api_key="fake", base_url="http://fake")
    raw = '{"is_silent": true}'
    result = sim.parse_response(raw)
    assert result.is_silent is True


@pytest.mark.asyncio
async def test_child_sim_fallback_on_bad_json() -> None:
    sim = ChildSimulator(model="test-model", api_key="fake", base_url="http://fake")
    result = sim.parse_response("just some random text")
    assert result.text == "just some random text"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest ../tests/test_eval_rubrics.py -k child_sim -v`
Expected: FAIL

- [ ] **Step 3: Implement child simulator**

```python
# backend/eval/child_sim.py
"""Child simulator — generates realistic child inputs using an LLM."""

import json
import logging
import random

import httpx
from openai import AsyncOpenAI
from pydantic import BaseModel

from eval.rubrics import PERSONAS, ChildSimResponse, Persona

logger = logging.getLogger("wonderlens")


class ChildSimContext(BaseModel):
    """Context passed to the child simulator for each turn."""
    persona: str
    tier: str
    activity_name: str
    collection_criterion: str
    current_step: str
    collection_phase: str | None = None
    round_items: list[dict] | None = None
    last_ai_dialogue: str = ""
    collected_names: list[str] = []
    turn_number: int = 0


def _persona_by_name(name: str) -> Persona:
    for p in PERSONAS:
        if p.name == name:
            return p
    return PERSONAS[0]


def pick_persona(tier: str) -> Persona:
    """Randomly select a persona for the given tier."""
    candidates = [p for p in PERSONAS if p.tier == tier]
    return random.choice(candidates)


def _should_pick_photo(ctx: ChildSimContext) -> bool:
    """Check if this turn is a photo selection turn (Phase A)."""
    return (
        ctx.current_step.startswith("STEP_3_COLLECT_")
        and ctx.collection_phase == "photo"
        and ctx.round_items is not None
    )


def _pick_photo(ctx: ChildSimContext, persona: Persona) -> ChildSimResponse:
    """Use persona probability table to pick correct, wrong, or silence."""
    roll = random.randint(1, 100)
    items = ctx.round_items or []
    correct = [i for i in items if i.get("correct")]
    wrong = [i for i in items if not i.get("correct")]

    if roll <= persona.correct_pct and correct:
        return ChildSimResponse(photo_id=correct[0]["id"])
    if roll <= persona.correct_pct + persona.wrong_pct and wrong:
        return ChildSimResponse(photo_id=random.choice(wrong)["id"])
    return ChildSimResponse(is_silent=True)


class ChildSimulator:
    """Generates child responses via LLM with persona-based photo selection."""

    def __init__(self, model: str, api_key: str, base_url: str) -> None:
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=1,
            timeout=httpx.Timeout(15.0, connect=5.0),
        )

    def parse_response(self, raw: str) -> ChildSimResponse:
        """Parse LLM output into ChildSimResponse."""
        try:
            data = json.loads(raw)
            return ChildSimResponse(**data)
        except (json.JSONDecodeError, TypeError):
            return ChildSimResponse(text=raw.strip())

    async def generate(self, ctx: ChildSimContext) -> ChildSimResponse:
        """Generate a child response for the given context."""
        persona = _persona_by_name(ctx.persona)

        # Photo selection: use probability table, not LLM
        if _should_pick_photo(ctx):
            return _pick_photo(ctx, persona)

        # Silence check based on persona probability
        if random.randint(1, 100) <= persona.silence_pct:
            return ChildSimResponse(is_silent=True)

        # LLM generates text response
        prompt = self._build_prompt(ctx, persona)
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._system_prompt(persona)},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.9,
                max_tokens=60,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or '{"text": ""}'
            return self.parse_response(raw)
        except Exception:
            logger.warning("Child sim LLM failed, returning silence")
            return ChildSimResponse(is_silent=True)

    def _system_prompt(self, persona: Persona) -> str:
        age_map = {"T0": "2-4", "T1": "4-6", "T2": "6-8"}
        age = age_map.get(persona.tier, "2-4")
        return (
            f"You are role-playing as a {age}-year-old child. "
            f"Personality: {persona.description}. "
            f"Respond with SHORT, realistic child speech. "
            f"Output JSON: {{\"text\": \"your response\"}}"
        )

    def _build_prompt(self, ctx: ChildSimContext, persona: Persona) -> str:
        parts = [
            f"Activity: {ctx.activity_name} ({ctx.collection_criterion})",
            f"Step: {ctx.current_step}",
            f"The AI just said: \"{ctx.last_ai_dialogue}\"",
        ]
        if ctx.collected_names:
            parts.append(f"Items collected so far: {', '.join(ctx.collected_names)}")
        parts.append(f"Turn number: {ctx.turn_number}")
        return "\n".join(parts)
```

- [ ] **Step 4: Run tests**

Run: `cd backend && uv run pytest ../tests/test_eval_rubrics.py -v`
Expected: All PASS

- [ ] **Step 5: Lint and commit**

Run: `cd backend && uv run ruff check eval/child_sim.py && uv run ruff format eval/child_sim.py`

```bash
git add backend/eval/child_sim.py tests/test_eval_rubrics.py
git commit -m "feat(eval): add child simulator with persona-based inputs"
```

---

### Task 3: LLM Judge

**Files:**
- Create: `backend/eval/judge.py`
- Test: `tests/test_eval_rubrics.py` (append)

- [ ] **Step 1: Write tests for judge output parsing**

Append to `tests/test_eval_rubrics.py`:

```python
from eval.judge import EvalJudge


@pytest.mark.asyncio
async def test_judge_parses_valid_json() -> None:
    judge = EvalJudge(model="test", api_key="fake", base_url="http://fake")
    raw = json.dumps({
        "step_scores": [
            {
                "step": "HOOK",
                "scores": {"age_appropriateness": 4, "emotional_warmth": 5, "no_question_rule": 5},
                "justifications": {"age_appropriateness": "good", "emotional_warmth": "warm", "no_question_rule": "ok"},
                "critical_failures": [],
            }
        ],
        "critical_failures": [],
        "summary": "Good session.",
    })
    result = judge.parse_judgement(raw)
    assert len(result.step_scores) == 1
    assert result.step_scores[0].scores["emotional_warmth"] == 5
    assert result.summary == "Good session."


@pytest.mark.asyncio
async def test_judge_fallback_on_bad_json() -> None:
    judge = EvalJudge(model="test", api_key="fake", base_url="http://fake")
    result = judge.parse_judgement("not json at all")
    assert result.overall_score == 1.0
    assert "parse" in result.summary.lower() or "fail" in result.summary.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest ../tests/test_eval_rubrics.py -k judge -v`
Expected: FAIL

- [ ] **Step 3: Implement judge**

```python
# backend/eval/judge.py
"""LLM judge — scores session transcripts against per-step rubrics."""

import json
import logging

import httpx
from openai import AsyncOpenAI

from eval.rubrics import (
    STEP_RUBRICS,
    SessionJudgement,
    SessionTranscript,
    StepScore,
    step_to_rubric_label,
)

logger = logging.getLogger("wonderlens")


def _build_judge_prompt(transcript: SessionTranscript) -> str:
    """Build the judge prompt from a session transcript."""
    age_map = {"T0": "2-4", "T1": "4-6", "T2": "6-8"}
    age = age_map.get(transcript.tier, "2-4")

    # Group turns by rubric label
    steps: dict[str, list[str]] = {}
    for turn in transcript.turns:
        label = step_to_rubric_label(turn.step)
        steps.setdefault(label, []).append(turn.ai_dialogue)

    # Build transcript section
    transcript_lines: list[str] = []
    for turn in transcript.turns:
        transcript_lines.append(f"[{turn.step}] AI: {turn.ai_dialogue}")
        if turn.child_input.text:
            transcript_lines.append(f"[{turn.step}] Child: {turn.child_input.text}")
        elif turn.child_input.photo_id:
            transcript_lines.append(f"[{turn.step}] Child: [selected photo: {turn.child_input.photo_id}]")
        elif turn.child_input.is_silent:
            transcript_lines.append(f"[{turn.step}] Child: [silence]")

    # Build rubric section
    rubric_lines: list[str] = []
    for label, rubric in STEP_RUBRICS.items():
        if label in steps:
            rubric_lines.append(f"- {label}: Score these dimensions 1-5: {', '.join(rubric.dimensions)}")

    return (
        f"You are an expert early childhood education evaluator.\n\n"
        f"Evaluate this Cat5 collection game transcript for a {transcript.tier} child (ages {age}).\n\n"
        f"Transcript:\n" + "\n".join(transcript_lines) + "\n\n"
        f"For each step present in the transcript, rate the dimensions 1-5:\n"
        + "\n".join(rubric_lines) + "\n\n"
        f"Also flag critical failures:\n"
        f"- AI suggested specific real-world items to find\n"
        f"- AI used directive language ('Go find!', 'Look for!')\n"
        f"- AI asked knowledge-test questions in the hook\n"
        f"- AI used premature completion language\n"
        f"- AI didn't celebrate correct photo selections\n\n"
        f"Output JSON with this structure:\n"
        f'{{"step_scores": [{{"step": "HOOK", "scores": {{"dim": 4}}, '
        f'"justifications": {{"dim": "reason"}}, "critical_failures": []}}], '
        f'"critical_failures": [], "summary": "2-3 sentence assessment"}}'
    )


def _compute_weighted_score(step_scores: list[StepScore]) -> float:
    """Compute weighted average 1-5 from step scores."""
    total_weight = 0
    weighted_sum = 0.0
    for ss in step_scores:
        rubric = STEP_RUBRICS.get(ss.step)
        if not rubric or not ss.scores:
            continue
        avg = sum(ss.scores.values()) / len(ss.scores)
        weighted_sum += avg * rubric.weight
        total_weight += rubric.weight
    return weighted_sum / total_weight if total_weight > 0 else 1.0


class EvalJudge:
    """Scores session transcripts via LLM against rubrics."""

    def __init__(self, model: str, api_key: str, base_url: str) -> None:
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=1,
            timeout=httpx.Timeout(30.0, connect=5.0),
        )

    def parse_judgement(self, raw: str) -> SessionJudgement:
        """Parse LLM judge output into SessionJudgement."""
        try:
            data = json.loads(raw)
            step_scores = [StepScore(**ss) for ss in data.get("step_scores", [])]
            overall = _compute_weighted_score(step_scores)
            return SessionJudgement(
                step_scores=step_scores,
                overall_score=overall,
                critical_failures=data.get("critical_failures", []),
                summary=data.get("summary", ""),
            )
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.warning("Judge output parse failed: %s", exc)
            return SessionJudgement(
                step_scores=[],
                overall_score=1.0,
                critical_failures=[f"Judge parse failed: {exc}"],
                summary="Judge output failed to parse.",
            )

    async def judge_session(self, transcript: SessionTranscript) -> SessionJudgement:
        """Score a full session transcript."""
        prompt = _build_judge_prompt(transcript)
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert early childhood education evaluator. Output valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            return self.parse_judgement(raw)
        except Exception as exc:
            logger.warning("Judge LLM call failed: %s", exc)
            return SessionJudgement(
                step_scores=[],
                overall_score=1.0,
                critical_failures=[f"Judge LLM failed: {exc}"],
                summary="Judge LLM call failed.",
            )
```

- [ ] **Step 4: Run tests**

Run: `cd backend && uv run pytest ../tests/test_eval_rubrics.py -v`
Expected: All PASS

- [ ] **Step 5: Lint and commit**

Run: `cd backend && uv run ruff check eval/judge.py && uv run ruff format eval/judge.py`

```bash
git add backend/eval/judge.py tests/test_eval_rubrics.py
git commit -m "feat(eval): add LLM judge with per-step rubric scoring"
```

---

### Task 4: Report generator

**Files:**
- Create: `backend/eval/report.py`
- Test: `tests/test_eval_rubrics.py` (append)

- [ ] **Step 1: Write tests for report generation**

Append to `tests/test_eval_rubrics.py`:

```python
from eval.report import generate_markdown_report, generate_summary_json
from eval.rubrics import SessionJudgement, SessionTranscript, StepScore


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
            StepScore(step="HOOK", scores={"emotional_warmth": 4}, justifications={"emotional_warmth": "ok"}, critical_failures=[]),
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && uv run pytest ../tests/test_eval_rubrics.py -k report -v`
Expected: FAIL

- [ ] **Step 3: Implement report generator**

```python
# backend/eval/report.py
"""Report generator — JSON summary + markdown."""

from eval.rubrics import SessionJudgement, SessionTranscript, Thresholds


def _combined_score(rule: float, judge: float) -> float:
    """Blend rule-based (0-100) and judge (1-5) into 0-100."""
    judge_normalized = (judge - 1) / 4 * 100
    return rule * 0.6 + judge_normalized * 0.4


def generate_summary_json(
    transcripts: list[SessionTranscript],
    judgements: list[SessionJudgement],
    thresholds: Thresholds,
) -> dict:
    """Generate machine-readable summary."""
    combos: dict[str, dict] = {}
    all_pass = True

    for t, j in zip(transcripts, judgements):
        key = f"{t.activity}_{t.tier}"
        if key not in combos:
            combos[key] = {"activity": t.activity, "tier": t.tier, "sessions": 0, "rule_scores": [], "judge_scores": [], "critical_failures": []}
        combos[key]["sessions"] += 1
        combos[key]["rule_scores"].append(t.rule_score)
        combos[key]["judge_scores"].append(j.overall_score)
        combos[key]["critical_failures"].extend(j.critical_failures)

    for key, combo in combos.items():
        avg_rule = sum(combo["rule_scores"]) / len(combo["rule_scores"]) if combo["rule_scores"] else 0
        avg_judge = sum(combo["judge_scores"]) / len(combo["judge_scores"]) if combo["judge_scores"] else 1
        combo["avg_rule"] = round(avg_rule, 1)
        combo["avg_judge"] = round(avg_judge, 2)
        combo["combined"] = round(_combined_score(avg_rule, avg_judge), 1)
        combo["failure_count"] = len(combo["critical_failures"])

        if combo["combined"] < thresholds.combined_score_min:
            all_pass = False
        if combo["failure_count"] > thresholds.critical_failures_max:
            all_pass = False

    return {"status": "PASS" if all_pass else "FAIL", "combos": combos}


def generate_markdown_report(
    transcripts: list[SessionTranscript],
    judgements: list[SessionJudgement],
    thresholds: Thresholds,
) -> str:
    """Generate human-readable markdown report."""
    summary = generate_summary_json(transcripts, judgements, thresholds)
    lines: list[str] = [
        f"# Eval Report",
        f"Status: **{summary['status']}**\n",
        "## Summary",
        "| Activity | Tier | Sessions | Rule | Judge | Combined | Status |",
        "|----------|------|----------|------|-------|----------|--------|",
    ]

    for combo in summary["combos"].values():
        status = "PASS" if combo["combined"] >= thresholds.combined_score_min and combo["failure_count"] <= thresholds.critical_failures_max else "FAIL"
        lines.append(
            f"| {combo['activity']} | {combo['tier']} | {combo['sessions']} | "
            f"{combo['avg_rule']} | {combo['avg_judge']}/5 | {combo['combined']}% | {status} |"
        )

    # Critical failures
    all_failures = []
    for t, j in zip(transcripts, judgements):
        for f in j.critical_failures:
            all_failures.append(f"- {t.session_id} ({t.activity} {t.tier}): {f}")

    if all_failures:
        lines.extend(["", "## Critical Failures"] + all_failures)
    else:
        lines.extend(["", "## Critical Failures", "None."])

    return "\n".join(lines) + "\n"
```

- [ ] **Step 4: Run tests**

Run: `cd backend && uv run pytest ../tests/test_eval_rubrics.py -v`
Expected: All PASS

- [ ] **Step 5: Lint and commit**

Run: `cd backend && uv run ruff check eval/report.py && uv run ruff format eval/report.py`

```bash
git add backend/eval/report.py tests/test_eval_rubrics.py
git commit -m "feat(eval): add report generator with pass/fail thresholds"
```

---

### Task 5: Eval runner

**Files:**
- Create: `backend/eval/runner.py`
- Test: `tests/test_eval_runner.py`

- [ ] **Step 1: Write integration test (mocked LLMs)**

```python
# tests/test_eval_runner.py
"""Integration test for the eval runner — mocked LLMs, real scoring."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from eval.rubrics import ChildSimResponse, EvalConfig, SessionJudgement, StepScore, Thresholds
from eval.runner import run_single_session


@pytest.mark.asyncio
async def test_run_single_session_completes() -> None:
    """A mocked session should produce a transcript with turns and scores."""
    config = EvalConfig(
        sessions_per_combo=1,
        activities=["fluffy_expedition_dandelion"],
        tiers=["T0"],
        server_url="http://localhost:8000",
    )

    # Mock the HTTP client
    mock_start_response = {
        "session_id": "eval-test-1",
        "first_turn": {"dialogue": "[excited] Wow fluffy!"},
        "session_state": {
            "current_step": "STEP_1_HOOK",
            "status": "active",
            "collection_phase": "photo",
            "collected_photos": [],
            "total_rounds": 2,
            "current_round_items": [],
        },
    }
    mock_turn_response = {
        "turn": {"dialogue": "[playful] Let's find more!", "auto_advance": False},
        "session_state": {
            "current_step": "STEP_6_CLOSING",
            "status": "completed",
            "collection_phase": "photo",
            "collected_photos": ["fuzzy_moss"],
            "total_rounds": 2,
            "current_round_items": [],
        },
    }

    mock_client = AsyncMock()
    mock_client.post = AsyncMock()

    start_resp = AsyncMock()
    start_resp.status_code = 200
    start_resp.json.return_value = mock_start_response

    turn_resp = AsyncMock()
    turn_resp.status_code = 200
    turn_resp.json.return_value = mock_turn_response

    mock_client.post.side_effect = [start_resp, turn_resp]

    # Mock child sim
    mock_child_sim = AsyncMock()
    mock_child_sim.generate = AsyncMock(return_value=ChildSimResponse(text="wow"))

    transcript = await run_single_session(
        client=mock_client,
        child_sim=mock_child_sim,
        activity="fluffy_expedition_dandelion",
        tier="T0",
        persona_name="curious_toddler",
        correct_items_by_round=[["fuzzy_moss"], ["fluffy_seed"]],
        config=config,
    )

    assert transcript.session_id == "eval-test-1"
    assert transcript.activity == "fluffy_expedition_dandelion"
    assert len(transcript.turns) >= 1
    assert transcript.final_status == "completed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest ../tests/test_eval_runner.py -v`
Expected: FAIL

- [ ] **Step 3: Implement runner**

```python
# backend/eval/runner.py
"""Eval runner — orchestrates sessions against the live API."""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

# Path setup for scoring imports
_SCRIPTS_DIR = str(Path(__file__).resolve().parents[2] / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from scoring import (
    compute_composite_score,
    score_completion_language,
    score_item_suggestion_free,
    score_phrasing_variety,
    score_tier_compliance,
    score_validation_pass,
)

from eval.child_sim import ChildSimContext, ChildSimulator
from eval.rubrics import (
    ChildSimResponse,
    EvalConfig,
    SessionTranscript,
    TurnRecord,
)

logger = logging.getLogger("wonderlens")

MAX_TURNS = 20


def _extract_dialogue(data: dict) -> str:
    """Extract AI dialogue from API response."""
    if "first_turn" in data:
        return data["first_turn"].get("dialogue", "")
    return data.get("turn", {}).get("dialogue", "")


def _extract_state(data: dict) -> dict:
    return data.get("session_state", {})


def _score_turn(
    dialogue: str, step: str, tier: str, phase: str,
    is_first: bool, collected: int, total: int,
) -> dict[str, float]:
    """Score one AI turn using rule-based functions."""
    return {
        "validation_pass": score_validation_pass(dialogue, step, tier, phase, is_first),
        "item_suggestion_free": score_item_suggestion_free(dialogue),
        "completion_language": score_completion_language(dialogue, collected, total),
        "tier_compliance": score_tier_compliance(dialogue, tier),
    }


async def run_single_session(
    client: httpx.AsyncClient,
    child_sim: ChildSimulator,
    activity: str,
    tier: str,
    persona_name: str,
    correct_items_by_round: list[list[str]],
    config: EvalConfig,
) -> SessionTranscript:
    """Run one full game session and return the transcript."""
    # Start session
    resp = await client.post(
        f"{config.server_url}/api/start-deep-link",
        json={"entity": activity, "tier": tier},
    )
    assert resp.status_code == 200, f"Start failed: {resp.status_code}"
    data = resp.json()

    session_id = data["session_id"]
    dialogue = _extract_dialogue(data)
    state = _extract_state(data)

    turns: list[TurnRecord] = []
    progress_phrases: list[str] = []
    validation_scores: list[float] = []
    item_scores: list[float] = []
    completion_scores: list[float] = []
    compliance_scores: list[float] = []
    prev_step = ""

    # Record first turn (hook)
    step = state.get("current_step", "STEP_1_HOOK")
    rule = _score_turn(dialogue, step, tier, state.get("collection_phase", "photo"), True, 0, state.get("total_rounds", 3))
    turns.append(TurnRecord(
        turn_number=0, step=step, ai_dialogue=dialogue,
        child_input=ChildSimResponse(), session_state=state, rule_scores=rule,
    ))
    for k in ("validation_pass", "item_suggestion_free", "completion_language", "tier_compliance"):
        [validation_scores, item_scores, completion_scores, compliance_scores][
            ["validation_pass", "item_suggestion_free", "completion_language", "tier_compliance"].index(k)
        ].append(rule[k])
    prev_step = step

    # Turn loop
    for turn_num in range(1, MAX_TURNS + 1):
        if state.get("status") in ("completed", "exited", "error"):
            break

        # Build round_items with correct flags for child sim
        api_items = state.get("current_round_items", [])
        round_idx = max(0, len(state.get("collected_photos", [])))
        if round_idx < len(correct_items_by_round):
            correct_ids = set(correct_items_by_round[round_idx])
        else:
            correct_ids = set()

        enriched_items = [
            {**item, "correct": item["id"] in correct_ids} for item in api_items
        ]

        ctx = ChildSimContext(
            persona=persona_name,
            tier=tier,
            activity_name=activity,
            collection_criterion="",
            current_step=state.get("current_step", ""),
            collection_phase=state.get("collection_phase"),
            round_items=enriched_items if enriched_items else None,
            last_ai_dialogue=dialogue,
            collected_names=state.get("collected_names", []),
            turn_number=turn_num,
        )

        child_resp = await child_sim.generate(ctx)

        # Send turn to API
        body: dict = {"session_id": session_id, "text": child_resp.text, "is_silent": child_resp.is_silent}
        if child_resp.photo_id:
            body["photo_id"] = child_resp.photo_id

        resp = await client.post(f"{config.server_url}/api/turn", json=body)
        if resp.status_code != 200:
            logger.warning("Turn %d failed: %d", turn_num, resp.status_code)
            break

        data = resp.json()
        dialogue = _extract_dialogue(data)
        state = _extract_state(data)
        step = state.get("current_step", "")
        is_first = step != prev_step

        rule = _score_turn(
            dialogue, step, tier, state.get("collection_phase", "photo"),
            is_first, len(state.get("collected_photos", [])), state.get("total_rounds", 3),
        )

        turns.append(TurnRecord(
            turn_number=turn_num, step=step, ai_dialogue=dialogue,
            child_input=child_resp, session_state=state, rule_scores=rule,
        ))
        validation_scores.append(rule["validation_pass"])
        item_scores.append(rule["item_suggestion_free"])
        completion_scores.append(rule["completion_language"])
        compliance_scores.append(rule["tier_compliance"])

        if step.startswith("STEP_3_COLLECT_"):
            progress_phrases.append(dialogue)

        prev_step = step

    variety = score_phrasing_variety(progress_phrases) if progress_phrases else 1.0
    composite = compute_composite_score(validation_scores, item_scores, completion_scores, compliance_scores, variety)

    return SessionTranscript(
        session_id=session_id,
        activity=activity,
        tier=tier,
        persona=persona_name,
        model=config.child_sim_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
        correct_items_by_round=correct_items_by_round,
        turns=turns,
        final_status=state.get("status", "unknown"),
        total_turns=len(turns),
        rule_score=composite,
        variety_score=variety,
    )
```

- [ ] **Step 4: Run tests**

Run: `cd backend && uv run pytest ../tests/test_eval_runner.py -v`
Expected: PASS

- [ ] **Step 5: Lint and commit**

Run: `cd backend && uv run ruff check eval/runner.py && uv run ruff format eval/runner.py`

```bash
git add backend/eval/runner.py tests/test_eval_runner.py
git commit -m "feat(eval): add session runner with rule-based scoring"
```

---

### Task 6: CLI entrypoint

**Files:**
- Create: `scripts/run_eval.py`

- [ ] **Step 1: Implement CLI**

```python
#!/usr/bin/env python3
"""CLI entrypoint for the LLM-driven eval system.

Usage:
    uv run python scripts/run_eval.py
    uv run python scripts/run_eval.py --activity fluffy_expedition_dandelion --tier T0
    uv run python scripts/run_eval.py --sessions 3
    uv run python scripts/run_eval.py --rejudge eval_results/2026-03-30/
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Path setup
_BACKEND_DIR = str(Path(__file__).resolve().parents[1] / "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import httpx

from config import get_settings
from entity_registry import get_collection_catalog
from eval.child_sim import ChildSimulator, pick_persona
from eval.judge import EvalJudge
from eval.report import generate_markdown_report, generate_summary_json
from eval.rubrics import EvalConfig, SessionTranscript, load_eval_config
from eval.runner import run_single_session
from scoring import score_cross_session_variety

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_correct_items(activity: str) -> list[list[str]]:
    """Load correct item IDs per round from entity registry."""
    catalog = get_collection_catalog(activity)
    if not catalog:
        return []
    return [[item.id for item in catalog.correct]]


async def run_eval(config: EvalConfig) -> int:
    """Run full eval and return exit code (0=pass, 1=fail)."""
    settings = get_settings()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")
    output_dir = REPO_ROOT / config.output_dir / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "transcripts").mkdir(exist_ok=True)
    (output_dir / "scores").mkdir(exist_ok=True)

    child_sim = ChildSimulator(
        model=config.child_sim_model,
        api_key=settings.gemini_api_key or settings.openai_api_key,
        base_url=settings.openai_base_url or "https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    judge = EvalJudge(
        model=config.judge_model,
        api_key=settings.gemini_api_key or settings.openai_api_key,
        base_url=settings.openai_base_url or "https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    all_transcripts: list[SessionTranscript] = []
    all_judgements = []

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
        for activity in config.activities:
            correct_items = _load_correct_items(activity)
            for tier in config.tiers:
                session_dialogues: list[list[str]] = []
                for session_n in range(config.sessions_per_combo):
                    persona = pick_persona(tier)
                    print(f"  [{activity} {tier} #{session_n + 1}] persona={persona.name}")

                    transcript = await run_single_session(
                        client=client,
                        child_sim=child_sim,
                        activity=activity,
                        tier=tier,
                        persona_name=persona.name,
                        correct_items_by_round=[correct_items[0]] if correct_items else [],
                        config=config,
                    )

                    # Save transcript
                    t_path = output_dir / "transcripts" / f"{activity}_{tier}_{session_n}.json"
                    t_path.write_text(transcript.model_dump_json(indent=2))

                    # Judge
                    judgement = await judge.judge_session(transcript)
                    all_transcripts.append(transcript)
                    all_judgements.append(judgement)

                    # Collect dialogues for cross-session variety
                    session_dialogues.append([t.ai_dialogue for t in transcript.turns])

                # Cross-session variety
                if len(session_dialogues) >= 2:
                    variety = score_cross_session_variety(session_dialogues)
                    print(f"  [{activity} {tier}] cross-session variety: {variety:.0%}")

    # Generate reports
    summary = generate_summary_json(all_transcripts, all_judgements, config.thresholds)
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    md = generate_markdown_report(all_transcripts, all_judgements, config.thresholds)
    (output_dir / "report.md").write_text(md)

    print(f"\nResults saved to {output_dir}/")
    print(f"Status: {summary['status']}")

    return 0 if summary["status"] == "PASS" else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM-driven eval for Cat5 games")
    parser.add_argument("--activity", help="Specific activity to eval")
    parser.add_argument("--tier", help="Specific tier to eval")
    parser.add_argument("--sessions", type=int, help="Sessions per activity/tier combo")
    parser.add_argument("--min-score", type=int, help="Override minimum combined score threshold")
    parser.add_argument("--config", type=Path, help="Path to eval config YAML")
    args = parser.parse_args()

    config = load_eval_config(args.config)

    if args.activity:
        config.activities = [args.activity]
    if args.tier:
        config.tiers = [args.tier]
    if args.sessions:
        config.sessions_per_combo = args.sessions
    if args.min_score:
        config.thresholds.combined_score_min = args.min_score

    print(f"Running eval: {len(config.activities)} activities x {len(config.tiers)} tiers x {config.sessions_per_combo} sessions")
    exit_code = asyncio.run(run_eval(config))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Add eval_results to .gitignore**

Append to `.gitignore`:
```
eval_results/
```

- [ ] **Step 3: Lint and commit**

Run: `cd backend && uv run ruff check ../scripts/run_eval.py && uv run ruff format ../scripts/run_eval.py`

```bash
git add scripts/run_eval.py .gitignore
git commit -m "feat(eval): add CLI entrypoint for eval runner"
```

---

### Task 7: Run full test suite and verify

- [ ] **Step 1: Run all eval tests**

Run: `cd backend && uv run pytest ../tests/test_eval_rubrics.py ../tests/test_eval_runner.py -v`
Expected: All PASS

- [ ] **Step 2: Run full project test suite**

Run: `cd backend && uv run pytest ../tests/ -v`
Expected: No regressions (360+ pass)

- [ ] **Step 3: Lint all new files**

Run: `cd backend && uv run ruff check eval/ ../scripts/run_eval.py && uv run ruff format eval/ ../scripts/run_eval.py`

- [ ] **Step 4: Smoke test CLI (dry run)**

Run: `cd backend && uv run python ../scripts/run_eval.py --help`
Expected: Shows usage with --activity, --tier, --sessions flags

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore(eval): verify full test suite passes"
```

---

## Verification

After all tasks complete:

1. `cd backend && uv run pytest ../tests/test_eval_rubrics.py ../tests/test_eval_runner.py -v` — all pass
2. `cd backend && uv run pytest ../tests/ -v` — no regressions
3. `uv run python scripts/run_eval.py --help` — shows CLI usage
4. **Live test** (requires running server): `uv run python scripts/run_eval.py --activity fluffy_expedition_dandelion --tier T0 --sessions 1`
