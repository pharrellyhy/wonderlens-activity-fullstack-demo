# LLM-Driven Eval System for Cat5 Games — Design Spec

## Goal

Build an automated evaluation system that runs full Cat5 game sessions end-to-end using LLM-generated child inputs, scores AI dialogue quality against per-step rubrics, and reports regressions with CI-compatible pass/fail thresholds.

## Scope

- **Phase 1 (this spec):** Eval runner + child simulator + LLM judge + reporting with threshold alerts. **Cat5 activities only** (Cat1 is out of scope for Phase 1).
- **Phase 2 (future):** Active prompt improvement loop (eval identifies weaknesses, suggests prompt changes, re-evals). Cat1 support.
- **Model upgrade:** Gemini 2.0 Flash → user-specified new models. The eval system is built model-agnostic — model IDs are configurable in `eval_config.yaml`. The model upgrade itself is a separate task validated by the first eval run.

## Architecture

```
eval_runner.py
  │
  ├── Loads correct items from entity registry (not from API)
  │
  ├── Starts session via /api/start-deep-link (entity, tier)
  │
  ├── For each turn:
  │   ├── Child Simulator (configurable LLM)
  │   │   reads AI dialogue + game context → generates child input
  │   │
  │   └── Sends child input to /api/turn
  │       returns AI dialogue + session_state
  │
  ├── Session complete → save transcript + rule scores to disk
  │
  ├── Rule Scorer (scoring.py, pattern-based)
  │   └── validation pass, item suggestion, completion language, tier compliance, variety
  │
  ├── LLM Judge (configurable LLM, default: stronger model)
  │   └── per-step quality scoring against rubrics
  │
  └── Report Generator
      └── JSON summary + markdown report + exit code
```

Requires a running backend server (`uv run uvicorn server:app --port 8000`).

## Components

### 1. Eval Runner (`backend/eval/runner.py`)

Orchestrates the eval loop. Runs `sessions_per_combo` sessions (default 5) for each `(activity, tier)` combination.

**Configuration** (`backend/eval_config.yaml` — in backend root, next to `config.yaml`):
```yaml
sessions_per_combo: 5
activities:
  - fluffy_expedition_dandelion
  - polka_dot_patrol
tiers: [T0, T1, T2]
server_url: "http://localhost:8000"
output_dir: "eval_results"   # relative to repo root

thresholds:
  combined_score_min: 80       # percent
  critical_failures_max: 0
  cross_session_variety_min: 70  # percent

models:
  child_sim: gemini-2.0-flash   # override to test new models
  judge: gemini-2.0-flash       # override to test new models
```

**Session loop:**
1. Load correct item IDs from entity registry via `load_instruction_recipe(activity_type)` — the API strips `is_correct` flags from `round_items`, so the runner resolves correctness from the game definition before starting
2. Call `/api/start-deep-link` with `{entity, tier}`
3. Extract `session_id`, `session_state`, first AI dialogue
4. Loop until session ends or max 20 turns:
   a. Feed AI dialogue + game context + correct item IDs to child simulator
   b. Child sim returns `{text, photo_id, is_silent}`
   c. Send to `/api/turn`
   d. Record turn in transcript, run per-turn rule scoring
5. Save transcript + rule scores to `{output_dir}/{timestamp}/transcripts/`
6. Pass transcript to LLM judge
7. Aggregate scores, generate report

**Output path anchoring:** All paths resolve relative to the repo root (`Path(__file__).resolve().parents[2]` from `runner.py`).

### 2. Child Simulator (`backend/eval/child_sim.py`)

Generates realistic child responses using the configured LLM.

**Persona system** — 3 personas per tier, randomly assigned per session:

| Tier | Personas | Correct% | Wrong% | Silence% |
|------|----------|----------|--------|----------|
| T0 (2-4) | `curious_toddler` (engaged, points) | 85 | 10 | 5 |
| T0 (2-4) | `shy_toddler` (minimal, sometimes silent) | 70 | 10 | 20 |
| T0 (2-4) | `distracted_toddler` (off-topic, wrong picks) | 50 | 30 | 20 |
| T1 (4-6) | `eager_explorer` (follows instructions) | 90 | 5 | 5 |
| T1 (4-6) | `daydreamer` (slow, off-topic) | 60 | 20 | 20 |
| T1 (4-6) | `contrarian` (says no, wrong picks) | 40 | 50 | 10 |
| T2 (6-8) | `analytical` (full sentences) | 90 | 5 | 5 |
| T2 (6-8) | `impatient` (short, rushing) | 80 | 15 | 5 |
| T2 (6-8) | `storyteller` (elaborate, tangential) | 75 | 15 | 10 |

**Input to child sim:**
```python
@dataclass
class ChildSimContext:
    persona: str                    # e.g. "curious_toddler"
    tier: str                       # T0, T1, T2
    activity_name: str
    collection_criterion: str
    current_step: str
    collection_phase: str | None    # "photo" or "detail" (Cat5 only)
    round_items: list[dict] | None  # with correct flags (from entity registry)
    last_ai_dialogue: str
    collected_names: list[str]
    turn_number: int
```

**Output:**
```python
@dataclass
class ChildSimResponse:
    text: str = ""
    photo_id: str | None = None
    is_silent: bool = False
```

**Photo selection logic**: During STEP_3_COLLECT Phase A, the child sim receives `round_items` with `correct` flags from the entity registry (loaded at runner startup, NOT from the API response which strips this field). The persona's probability table determines whether the child picks correct, wrong, or stays silent. The LLM generates the response text; the runner applies the probability table for photo_id selection.

### 3. LLM Judge (`backend/eval/judge.py`)

Scores transcripts using the configured judge LLM against per-step rubrics.

**Step name mapping** (rubric label → codebase step names):

| Rubric Label | Matches |
|---|---|
| HOOK | `STEP_1_HOOK` |
| MISSION | `STEP_2_MISSION` |
| COLLECT | `STEP_3_COLLECT_*` (all rounds) |
| SYNTHESIS | `STEP_4_SYNTHESIS` |
| CELEBRATE | `STEP_5_CELEBRATE` |
| CLOSING | `STEP_6_CLOSING` |

**Per-step rubrics:**

| Rubric Label | Dimensions | Weight |
|------|-----------|--------|
| HOOK | age_appropriateness, emotional_warmth, no_question_rule | 15% |
| MISSION | invitational_tone, brevity, clarity | 10% |
| COLLECT | scaffolding_quality, engagement_recovery, variety, celebration | 35% |
| SYNTHESIS | narrative_coherence, age_appropriateness, references_collected | 20% |
| CELEBRATE | emotional_warmth, role_title_usage, session_recall | 10% |
| CLOSING | ib_concept_weaving, natural_goodbye | 10% |

Each dimension scored 1-5 with brief justification.

**Judge output schema:**
```python
@dataclass
class StepScore:
    step: str                       # rubric label: HOOK, MISSION, etc.
    scores: dict[str, int]          # dimension → 1-5
    justifications: dict[str, str]  # dimension → brief text
    critical_failures: list[str]    # e.g. "suggested specific item"

@dataclass
class SessionJudgement:
    step_scores: list[StepScore]
    overall_score: float            # weighted average 1-5
    critical_failures: list[str]    # aggregated across steps
    summary: str                    # 2-3 sentence assessment
```

**Critical failure detection** (in addition to LLM scoring):
- AI suggested specific items to find
- AI used directive language ("Go find!", "Look for!")
- AI asked knowledge-test questions in hook
- AI used premature completion language
- AI didn't celebrate correct photo selections

### 4. Scoring Integration

**Two scoring layers run per session:**

**Layer 1 — Rule-based** (existing `scripts/scoring.py`):

The runner calls these functions per-turn during the session loop, collecting scores as it goes:

| Function | Input Source (from transcript) |
|----------|------|
| `score_validation_pass(dialogue, step, tier, phase, is_first)` | Turn's `ai_dialogue`, `step`, `tier`, `collection_phase` |
| `score_item_suggestion_free(dialogue)` | Turn's `ai_dialogue` |
| `score_completion_language(dialogue, collected, total)` | Turn's `ai_dialogue`, `len(collected_photos)`, `total_rounds` from session_state |
| `score_tier_compliance(dialogue, tier)` | Turn's `ai_dialogue`, `tier` |

After all sessions for an activity/tier combo:
| Function | Input Source |
|----------|------|
| `score_phrasing_variety(progress_phrases)` | All COLLECT round dialogues within one session |
| `score_cross_session_variety(session_dialogues)` | Corresponding turns across all sessions for this activity/tier |

`compute_composite_score()` aggregates all per-turn scores into a 0-100 `rule_score`.

**Layer 2 — LLM judge** (per session, after completion):
Returns `SessionJudgement` with `overall_score` (1-5).

**Combined scoring formula:**
```
judge_normalized = (overall_judge_score - 1) / 4 * 100   # maps 1-5 → 0-100
combined = (rule_score * 0.6) + (judge_normalized * 0.4)
```

### 5. Report Generator (`backend/eval/report.py`)

**Outputs** (all under `{repo_root}/{output_dir}/{timestamp}/`):
- `transcripts/*.json` — raw session transcripts + per-turn rule scores
- `scores/*.json` — per-session combined scores + judge results
- `summary.json` — machine-readable aggregate
- `report.md` — human-readable markdown

Transcripts include per-turn rule scores so `--rejudge` can re-run only the LLM judge without re-deriving rule scores.

**Exit codes:**
- `0` — all thresholds passed
- `1` — at least one threshold breached (details in report)

### 6. Session Transcript Format

```json
{
  "session_id": "eval-abc123",
  "activity": "fluffy_expedition_dandelion",
  "tier": "T0",
  "persona": "curious_toddler",
  "model": "gemini-2.0-flash",
  "timestamp": "2026-03-30T14:30:00Z",
  "correct_items_by_round": [["fuzzy_moss"], ["fluffy_seed"], ["soft_petal"]],
  "turns": [
    {
      "turn_number": 0,
      "step": "STEP_1_HOOK",
      "ai_dialogue": "[excited] Ooh! Look at those tiny fluffy parachutes!",
      "child_input": {"text": "soft!", "photo_id": null, "is_silent": false},
      "session_state": { "current_step": "...", "collected_photos": [], "..." : "..." },
      "rule_scores": {
        "validation_pass": 1.0,
        "item_suggestion_free": 1.0,
        "tier_compliance": 1.0
      }
    }
  ],
  "final_status": "completed",
  "total_turns": 12,
  "rule_score": 87.5,
  "variety_score": 0.82
}
```

### 7. Model Configuration

Model IDs are configured in `eval_config.yaml` (not hardcoded). The game model is configured in `backend/config.py` / `backend/config.yaml` as it is today.

The eval system is **model-agnostic** — to test a new model:
1. Update `backend/config.yaml` with the new game model ID
2. Run the eval to establish a baseline
3. Compare with previous runs via `--compare`

## File Structure

```
backend/
  eval/
    __init__.py
    runner.py            # Session orchestrator
    child_sim.py         # Child simulator LLM
    judge.py             # LLM judge with per-step rubrics
    rubrics.py           # Rubric dataclasses and definitions
    report.py            # JSON + markdown report generator
  eval_config.yaml       # Default configuration (backend root, next to config.yaml)
scripts/
  scoring.py             # Existing rule-based scorer (unchanged)
  run_eval.py            # CLI entrypoint
eval_results/            # Output directory (gitignored, repo root)
```

## CLI Interface

```bash
# Full eval run (30 sessions: 2 activities x 3 tiers x 5 sessions)
uv run python scripts/run_eval.py

# Specific activity/tier
uv run python scripts/run_eval.py --activity fluffy_expedition_dandelion --tier T0

# Override session count
uv run python scripts/run_eval.py --sessions 3

# Re-judge existing transcripts (re-runs LLM judge only, reuses saved rule scores)
uv run python scripts/run_eval.py --rejudge eval_results/2026-03-30_14-30/

# Compare two eval runs (regression detection)
uv run python scripts/run_eval.py --compare eval_results/run1/ eval_results/run2/

# Override thresholds
uv run python scripts/run_eval.py --min-score 85 --max-failures 1
```

## Testing Strategy

- **Unit tests** for child_sim (mock LLM, verify output parsing and persona selection), judge (mock LLM, verify rubric scoring and step mapping), report (verify markdown generation)
- **Integration test**: Run 1 session of fluffy_expedition_dandelion T0 against live API, verify transcript + score format
- **Existing tests**: `test_scoring.py` already covers rule-based scorer

## Constraints

- Requires running backend server (not pure offline)
- LLM costs per full run (30 sessions): ~480 child sim calls + ~30 judge calls
- Cost depends on model pricing — with current Gemini 2.0 Flash: ~$3.50/run
- Cat1 activities are explicitly out of scope for Phase 1
