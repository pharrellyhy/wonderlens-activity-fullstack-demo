# Autoresearch-Style Prompt Optimization — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an evaluation and measurement harness for prompt quality — scoring generated responses against automated quality metrics across multiple dimensions. This harness measures the effectiveness of the Creative Diversity Framework (see `docs/plans/2026-03-27-creative-diversity-framework.md`), which is the primary quality improvement strategy.

> **Status update (2026-03-27):** The autonomous prompt optimization loop (`program.md`) has been deprioritized. Automated prompt word-tuning via hill-climbing hits a ceiling quickly because the quality problems are structural (fixed examples, no personality variation), not lexical. The eval harness remains valuable as a measurement tool. The Creative Diversity Framework addresses the structural issues directly.

**Architecture:** Two components: (1) an immutable evaluation harness (`scripts/evaluate_prompts.py`) that runs scenarios against the live backend, scores each response on multiple dimensions, and outputs a single composite score; (2) a `results.tsv` experiment log for human review.

**Tech Stack:** Python 3.12+, httpx, YAML scenarios, existing turn_handler validators, Jaccard distance for variety scoring (no scikit-learn dependency), TSV logging

---

## Why This Works for WonderLens

The autoresearch pattern succeeds when:
1. **The search space is constrained** — we limit the agent to prompt files + config knobs
2. **The metric is immutable and automated** — we reuse existing validators + add new scorers
3. **Each experiment is cheap and fast** — ~20 LLM calls per experiment (~$0.50, ~90 seconds)
4. **Binary keep/discard is sufficient** — greedy hill-climbing works for prompt refinement

Our existing infrastructure already provides most of what's needed:
- 9 scenario YAML files covering Cat5 happy path, decline, silence, wrong photos, off-topic, and T1
- `_validate_response()` and `_validate_plan()` in `turn_handler.py`
- `_has_completion_language()` and `_ITEM_SUGGESTION_RE` pattern matchers
- `get_retry_stats()` retry-rate telemetry
- `run_dandelion_scenarios.py` scenario runner (to be replaced by the new headless evaluator)

## Design Decisions

### Stochasticity handling
LLM output is non-deterministic. Running a scenario once tells you almost nothing — the same prompt might produce a great response 80% of the time and a terrible one 20% of the time. We run each scenario **3 times** (54 total LLM calls across 6 scenarios × 3 tiers) and report aggregate scores. This gives stable signal while keeping experiment cost under $1.

### Composite metric
A single number makes keep/discard decisions trivial. The composite score (0–100) weights:
- **Validation pass rate (50%)** — from `_validate_response()` checks (T0 scaffolding, open questions)
- **Item suggestion free rate (25%)** — no specific item suggestions in collection prompts
- **Completion language accuracy (15%)** — no premature "all done" when items remain
- **Tier compliance (5%)** — sentence count within tier max, emotion tag present
- **Phrasing variety (5%)** — Jaccard distance between progress notes across rounds (penalizes "X out of Y" repetition)

> **Note:** Plan validation dimension removed (two-pass generation is disabled). Weights redistributed to validation pass rate and item suggestion free rate.

### What can be tuned (if the optimization loop is re-enabled in future)
| File | Modifiable | Why |
|------|-----------|-----|
| `backend/skills/step_instructions/*.md` | Yes | Per-step prompt quality |
| `backend/skills/script_turn.md` | Yes | Main system prompt |
| `backend/config.py` (temperatures only) | Yes | LLM temperature tuning |
| `scripts/evaluate_prompts.py` | **No** | Immutable metric |
| `backend/turn_handler.py` | **No** | Immutable validation |
| `backend/agents/*.py` | **No** | Immutable code |
| `backend/schemas/*.py` | **No** | Immutable schemas |

> **Note:** `planner_system.md` and `speaker_system.md` removed — two-pass generation is disabled.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `scripts/evaluate_prompts.py` | Create | Immutable evaluation harness — runs scenarios headlessly, scores responses, outputs composite score |
| `scripts/scoring.py` | Create | Scoring functions — individual dimension scorers extracted for testability |
| `program.md` | Create | Agent skill file — autonomous optimization loop instructions |
| `tests/test_scoring.py` | Create | Unit tests for scoring functions |
| `results/.gitkeep` | Create | Directory for experiment results (gitignored except .gitkeep) |

---

## Tasks

### Task 1: Create the scoring module

**Files:**
- Create: `scripts/scoring.py`
- Test: `tests/test_scoring.py`

The scoring module contains pure functions that take a dialogue string + state context and return a score. These are the building blocks of the composite metric.

- [ ] **Step 1: Write tests for `score_validation_pass`**

```python
# tests/test_scoring.py
from scripts.scoring import score_validation_pass

def test_valid_t0_scaffold_passes() -> None:
    """T0 dialogue with model phrase + binary choice scores 1.0."""
    result = score_validation_pass(
        dialogue="[excited] I think it looks like a cloud! Is it fluffy or smooth?",
        step="STEP_3_COLLECT_1",
        tier="T0",
        collection_phase="detail",
        is_first_on_step=True,
    )
    assert result == 1.0

def test_t0_open_question_without_scaffold_fails() -> None:
    """T0 open question without model phrase scores 0.0."""
    result = score_validation_pass(
        dialogue="[curious] What does this remind you of?",
        step="STEP_3_COLLECT_1",
        tier="T0",
        collection_phase="detail",
        is_first_on_step=True,
    )
    assert result == 0.0

def test_non_t0_open_question_passes() -> None:
    """T1 open questions are allowed."""
    result = score_validation_pass(
        dialogue="[curious] What does this remind you of?",
        step="STEP_3_COLLECT_1",
        tier="T1",
        collection_phase="detail",
        is_first_on_step=True,
    )
    assert result == 1.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_scoring.py -v`
Expected: ImportError — `scripts.scoring` does not exist yet.

- [ ] **Step 3: Implement `score_validation_pass`**

```python
# scripts/scoring.py
"""Scoring functions for prompt evaluation.

Each function takes dialogue + context and returns a float between 0.0 and 1.0.
These are the building blocks of the composite metric used by evaluate_prompts.py.
"""

import re
import sys
from pathlib import Path

# Add backend to path so we can import turn_handler validators
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from turn_handler import _ends_with_open_question, _has_model_phrase


def score_validation_pass(
    dialogue: str,
    step: str,
    tier: str,
    collection_phase: str = "photo",
    is_first_on_step: bool = False,
) -> float:
    """Score whether dialogue passes the same validation rules as _validate_response.

    Returns 1.0 if the dialogue would pass validation, 0.0 if it would fail.
    """
    # T0 collect detail: must scaffold
    if step.startswith("STEP_3_COLLECT_") and tier == "T0" and (collection_phase == "detail" or is_first_on_step):
        if _ends_with_open_question(dialogue) and not _has_model_phrase(dialogue):
            return 0.0

    # T0 synthesis: must scaffold
    if step == "STEP_4_SYNTHESIS" and tier == "T0" and is_first_on_step:
        if _ends_with_open_question(dialogue) and " or " not in dialogue.lower():
            return 0.0

    # T0 Cat1 round: must scaffold
    if step.startswith("STEP_3_ROUND_") and tier == "T0":
        if _ends_with_open_question(dialogue) and not _has_model_phrase(dialogue):
            return 0.0

    return 1.0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_scoring.py -v`
Expected: 3 passed.

- [ ] **Step 5: Write tests for `score_item_suggestion_free`**

```python
from scripts.scoring import score_item_suggestion_free

def test_no_item_suggestion_scores_1() -> None:
    result = score_item_suggestion_free("[excited] I wonder what soft thing you'll discover next!")
    assert result == 1.0

def test_item_suggestion_scores_0() -> None:
    result = score_item_suggestion_free("[excited] Find a pillow or a blanket!")
    assert result == 0.0

def test_incidental_mention_passes() -> None:
    """Mentioning an item without 'find/look for' is fine."""
    result = score_item_suggestion_free("[celebrating] That pillow is so fluffy!")
    assert result == 1.0
```

- [ ] **Step 6: Implement `score_item_suggestion_free`**

```python
_ITEM_SUGGESTION_RE = re.compile(
    r"(?i)\b(?:find|look for|grab|get|bring|search for|spot)\b"
    r"[^.!?]{0,40}"
    r"\b(?:pillow|blanket|sock|shoe|cup|spoon|fork|plate|ball|book|toy|rock|leaf|stick"
    r"|flower|shell|stone|button|coin|bottle|box|bag|hat|glove|scarf|key|pen|pencil"
    r"|crayon|block|ring|wheel|clock|bowl|jar|lid|pan|pot|ribbon|string|bead|marble)\b"
)


def score_item_suggestion_free(dialogue: str) -> float:
    """Score 1.0 if dialogue does NOT suggest specific items to find, 0.0 if it does."""
    return 0.0 if _ITEM_SUGGESTION_RE.search(dialogue) else 1.0
```

- [ ] **Step 7: Run tests**

Run: `uv run pytest tests/test_scoring.py -v`
Expected: 6 passed.

- [ ] **Step 8: Write tests for `score_completion_language`**

```python
from scripts.scoring import score_completion_language

def test_no_completion_language_when_items_remain() -> None:
    result = score_completion_language(
        dialogue="[excited] Great find! Would you like to look for one more?",
        collected=1, total=3,
    )
    assert result == 1.0

def test_completion_language_when_items_remain_scores_0() -> None:
    result = score_completion_language(
        dialogue="[proud] You found them all! Mission complete!",
        collected=1, total=3,
    )
    assert result == 0.0

def test_completion_language_when_done_is_fine() -> None:
    result = score_completion_language(
        dialogue="[proud] You found them all! Mission complete!",
        collected=3, total=3,
    )
    assert result == 1.0
```

- [ ] **Step 9: Implement `score_completion_language`**

```python
from turn_handler import _has_completion_language


def score_completion_language(dialogue: str, collected: int, total: int) -> float:
    """Score 1.0 if completion language is appropriate for the collection state.

    Penalizes premature completion language (when collected < total).
    Allows completion language when collection is actually done.
    """
    if collected >= total:
        return 1.0
    return 0.0 if _has_completion_language(dialogue) else 1.0
```

- [ ] **Step 10: Run tests**

Run: `uv run pytest tests/test_scoring.py -v`
Expected: 9 passed.

- [ ] **Step 11: Write tests for `score_tier_compliance`**

```python
from scripts.scoring import score_tier_compliance

def test_t0_short_dialogue_passes() -> None:
    result = score_tier_compliance("[excited] Wow, so fluffy!", tier="T0")
    assert result == 1.0

def test_t0_too_many_sentences_penalized() -> None:
    long_dialogue = (
        "[excited] Wow! That's amazing! I love it! "
        "Let me tell you more! This is really great!"
    )
    result = score_tier_compliance(long_dialogue, tier="T0")
    assert result < 1.0

def test_missing_emotion_tag_penalized() -> None:
    result = score_tier_compliance("Wow, so fluffy!", tier="T0")
    assert result < 1.0
```

- [ ] **Step 12: Implement `score_tier_compliance`**

```python
import re as _re

_EMOTION_TAG_RE = _re.compile(r"^\[.+?\] ")

# Tier sentence limits from tier_rules.yaml
_TIER_MAX_SENTENCES = {"T0": 2, "T1": 3, "T2": 4}


def score_tier_compliance(dialogue: str, tier: str) -> float:
    """Score tier-level compliance: emotion tag presence + sentence count.

    Returns average of two sub-scores:
    - 1.0 if emotion tag present, 0.0 if missing
    - 1.0 if sentence count <= tier max, linear penalty for excess
    """
    tag_score = 1.0 if _EMOTION_TAG_RE.match(dialogue) else 0.0

    # Count sentences (split on . ! ? followed by space or end)
    sentences = [s.strip() for s in _re.split(r"[.!?]+\s*", dialogue) if s.strip()]
    max_sentences = _TIER_MAX_SENTENCES.get(tier, 3)
    count_score = min(1.0, max_sentences / max(len(sentences), 1))

    return (tag_score + count_score) / 2.0
```

- [ ] **Step 13: Run tests**

Run: `uv run pytest tests/test_scoring.py -v`
Expected: 12 passed.

- [ ] **Step 14: Write tests for `score_phrasing_variety`**

```python
from scripts.scoring import score_phrasing_variety

def test_identical_phrases_score_low() -> None:
    result = score_phrasing_variety([
        "That's 1 out of 3!",
        "That's 2 out of 3!",
        "That's 3 out of 3!",
    ])
    assert result < 0.5

def test_varied_phrases_score_high() -> None:
    result = score_phrasing_variety([
        "Your first treasure!",
        "Two friends in the collection now!",
        "The squad is complete!",
    ])
    assert result > 0.7

def test_single_phrase_returns_1() -> None:
    result = score_phrasing_variety(["Just one!"])
    assert result == 1.0

def test_empty_list_returns_1() -> None:
    result = score_phrasing_variety([])
    assert result == 1.0
```

- [ ] **Step 15: Implement `score_phrasing_variety`**

Uses TF-IDF + cosine distance to measure how different progress phrases are from each other. High similarity = low variety = low score.

```python
def score_phrasing_variety(progress_phrases: list[str]) -> float:
    """Score how varied progress phrasing is across rounds.

    Uses word-level Jaccard distance. Returns 1.0 for maximum variety, 0.0 for identical.
    Returns 1.0 if fewer than 2 phrases (nothing to compare).
    """
    if len(progress_phrases) < 2:
        return 1.0

    # Word-level Jaccard distance between all pairs
    word_sets = [set(p.lower().split()) for p in progress_phrases]
    similarities = []
    for i in range(len(word_sets)):
        for j in range(i + 1, len(word_sets)):
            intersection = len(word_sets[i] & word_sets[j])
            union = len(word_sets[i] | word_sets[j])
            if union > 0:
                similarities.append(intersection / union)

    if not similarities:
        return 1.0

    avg_similarity = sum(similarities) / len(similarities)
    return 1.0 - avg_similarity  # High similarity = low variety
```

Note: Uses Jaccard distance instead of scikit-learn cosine similarity to avoid adding a heavy dependency. Jaccard on word sets works well enough for short phrases.

- [ ] **Step 16: Run tests**

Run: `uv run pytest tests/test_scoring.py -v`
Expected: 16 passed.

- [ ] **Step 17: Write and implement `compute_composite_score`**

```python
def compute_composite_score(
    validation_scores: list[float],
    item_suggestion_scores: list[float],
    completion_language_scores: list[float],
    tier_compliance_scores: list[float],
    variety_score: float,
) -> float:
    """Compute the weighted composite score (0-100).

    Weights:
    - Validation pass rate: 40%
    - Item suggestion free rate: 25%
    - Completion language accuracy: 15%
    - Tier compliance: 10%
    - Phrasing variety: 10%
    """
    def _avg(scores: list[float]) -> float:
        return sum(scores) / len(scores) if scores else 1.0

    return (
        _avg(validation_scores) * 40
        + _avg(item_suggestion_scores) * 25
        + _avg(completion_language_scores) * 15
        + _avg(tier_compliance_scores) * 10
        + variety_score * 10
    )
```

- [ ] **Step 18: Run all scoring tests**

Run: `uv run pytest tests/test_scoring.py -v`

- [ ] **Step 19: Lint**

Run: `uv run ruff check scripts/scoring.py tests/test_scoring.py && uv run ruff format --check scripts/scoring.py tests/test_scoring.py`

- [ ] **Step 20: Commit**

```bash
git commit -m "feat(scoring): add prompt evaluation scoring functions"
```

---

### Task 2: Create the evaluation harness

**Files:**
- Create: `scripts/evaluate_prompts.py`

This is the "prepare.py" equivalent — the immutable evaluation script that the agent runs but cannot modify.

- [ ] **Step 1: Implement `evaluate_prompts.py`**

The harness:
1. Starts a session via `/api/start-deep-link` for each scenario × tier combination
2. Walks through the scenario turns (reusing logic from `run_dandelion_scenarios.py`)
3. Scores every AI response using the scoring functions from Task 1
4. Aggregates into a composite score
5. Prints a structured results block that the agent can grep

```python
# scripts/evaluate_prompts.py
"""Immutable evaluation harness for prompt optimization.

Runs scenario YAML files against the live backend, scores every AI response
on multiple quality dimensions, and outputs a composite score (0-100).

Usage:
    uv run python scripts/evaluate_prompts.py [--repeats N]

Requires the backend running on localhost:8000.

DO NOT MODIFY THIS FILE — it is the immutable metric for the prompt
optimization loop. If you need to change scoring, modify scripts/scoring.py.
"""

import argparse
import sys
import time
from pathlib import Path

import httpx
import yaml

from scoring import (
    compute_composite_score,
    score_completion_language,
    score_item_suggestion_free,
    score_phrasing_variety,
    score_tier_compliance,
    score_validation_pass,
)

BASE_URL = "http://localhost:8000"
SCENARIOS_DIR = Path(__file__).resolve().parents[1] / "backend" / "scenarios"
CORRECT_PHOTO_IDS = {"fuzzy_moss", "fluffy_seed", "soft_petal", "woolly_caterpillar"}

# Scenarios to evaluate — covers Cat5 across tiers and edge cases
EVAL_SCENARIOS = [
    ("fluffy_expedition_dandelion", "T0"),
    ("fluffy_expedition_dandelion_t1", "T1"),
    ("fluffy_expedition_dandelion_decline", "T0"),
    ("fluffy_expedition_dandelion_silent", "T0"),
    ("fluffy_expedition_dandelion_wrong_photos", "T0"),
    ("fluffy_expedition_dandelion_offtopic", "T0"),
]


def run_and_score(scenario_name: str, tier: str, client: httpx.Client) -> dict:
    """Run a single scenario and return per-response scores.

    Returns dict with lists of scores per dimension and progress phrases.
    """
    # ... (scenario execution logic adapted from run_dandelion_scenarios.py)
    # For each AI response:
    #   - score_validation_pass(dialogue, step, tier, phase, is_first)
    #   - score_item_suggestion_free(dialogue)
    #   - score_completion_language(dialogue, collected, total)
    #   - score_tier_compliance(dialogue, tier)
    #   - Collect progress phrases for variety scoring
    pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate prompt quality")
    parser.add_argument("--repeats", type=int, default=3, help="Runs per scenario (default: 3)")
    args = parser.parse_args()

    all_validation: list[float] = []
    all_item: list[float] = []
    all_completion: list[float] = []
    all_tier: list[float] = []
    all_progress: list[str] = []

    start = time.perf_counter()

    with httpx.Client(timeout=30) as client:
        for repeat in range(args.repeats):
            for scenario_name, tier in EVAL_SCENARIOS:
                scores = run_and_score(scenario_name, tier, client)
                all_validation.extend(scores.get("validation", []))
                all_item.extend(scores.get("item_suggestion", []))
                all_completion.extend(scores.get("completion_language", []))
                all_tier.extend(scores.get("tier_compliance", []))
                all_progress.extend(scores.get("progress_phrases", []))

    variety = score_phrasing_variety(all_progress)
    composite = compute_composite_score(all_validation, all_item, all_completion, all_tier, variety)
    elapsed = time.perf_counter() - start

    # Structured output for agent grep
    print(f"composite_score: {composite:.2f}")
    print(f"validation_pass_rate: {sum(all_validation)/len(all_validation)*100:.1f}%")
    print(f"item_suggestion_free_rate: {sum(all_item)/len(all_item)*100:.1f}%")
    print(f"completion_language_rate: {sum(all_completion)/len(all_completion)*100:.1f}%")
    print(f"tier_compliance_rate: {sum(all_tier)/len(all_tier)*100:.1f}%")
    print(f"phrasing_variety: {variety:.3f}")
    print(f"eval_duration_seconds: {elapsed:.1f}")
    print(f"total_responses_scored: {len(all_validation)}")

    sys.exit(0)


if __name__ == "__main__":
    main()
```

The full implementation of `run_and_score` should adapt the scenario walking logic from `run_dandelion_scenarios.py` (photo selection, auto-advance, silence handling) but replace the `must_contain`/`must_not_contain` checks with the scoring functions. Track which step and phase each response comes from to pass correct context to scorers.

- [ ] **Step 2: Manual test**

Start the backend (`uv run uvicorn server:app --reload --port 8000`) and run:
```bash
uv run python scripts/evaluate_prompts.py --repeats 1
```

Expected: prints composite_score and dimension breakdowns. No crashes.

- [ ] **Step 3: Lint**

Run: `uv run ruff check scripts/evaluate_prompts.py && uv run ruff format --check scripts/evaluate_prompts.py`

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(eval): add immutable prompt evaluation harness"
```

---

### Task 3: Create the results directory and gitignore

**Files:**
- Create: `results/.gitkeep`
- Modify: `.gitignore`

- [ ] **Step 1: Create results directory**

```bash
mkdir -p results && touch results/.gitkeep
```

- [ ] **Step 2: Add results to .gitignore**

Add to `.gitignore`:
```
# Prompt optimization experiment results
results/*.tsv
results/*.log
```

- [ ] **Step 3: Commit**

```bash
git commit -m "chore: add results directory for prompt optimization experiments"
```

---

### ~~Task 4: Create the agent program (program.md)~~ — DEPRIORITIZED

> **Deprioritized (2026-03-27):** The autonomous prompt hill-climbing loop is not expected to yield significant improvements. Quality problems are structural (fixed examples, no personality variation), not lexical. The Creative Diversity Framework (`docs/plans/2026-03-27-creative-diversity-framework.md`) addresses these structural issues directly. If hill-climbing is revisited in future, the eval harness from Tasks 1-3 provides the foundation.

---

### Task 4 (renumbered): Dry-run the full pipeline

**Files:** None (verification only)

- [ ] **Step 1: Start the backend**

Run: `uv run uvicorn backend.server:app --port 8000`

- [ ] **Step 2: Run the evaluator**

Run: `uv run python scripts/evaluate_prompts.py --repeats 1`

Verify: outputs composite_score and all dimension breakdowns without crashing.

- [ ] **Step 3: Run with full repeats**

Run: `uv run python scripts/evaluate_prompts.py --repeats 3`

Verify: score is stable (within ±3 points across runs with same prompts).

- [ ] **Step 4: Run all tests**

Run: `uv run pytest tests/test_scoring.py -v`

- [ ] **Step 5: Record baseline**

Create `results/results.tsv` with the header and baseline:
```
commit	score	status	description
<current_hash>	<baseline_score>	baseline	Initial prompt baseline before optimization
```

- [ ] **Step 6: Commit**

```bash
git commit -m "docs: record baseline prompt evaluation score"
```

---

## Verification

1. `uv run pytest tests/test_scoring.py -v` — all scoring tests pass
2. `uv run ruff check scripts/ && uv run ruff format --check scripts/` — clean
3. `uv run python scripts/evaluate_prompts.py --repeats 1` — outputs composite_score without errors
4. `results/results.tsv` has the baseline score recorded

## Using the Eval Harness

Run the harness to measure prompt quality before and after changes:

```bash
# Quick check (1 repeat, ~20 LLM calls)
uv run python scripts/evaluate_prompts.py --repeats 1

# Stable measurement (3 repeats, ~60 LLM calls)
uv run python scripts/evaluate_prompts.py --repeats 3
```

Use it to measure the impact of each Creative Diversity Framework phase.

## Future Extensions

These are NOT in scope for this plan but worth noting:

- **Creative Diversity Framework**: The primary quality improvement strategy — see `docs/plans/2026-03-27-creative-diversity-framework.md`. The eval harness measures its effectiveness.
- **Cat1 scenario coverage**: Add `dino_time_traveler` and `mood_changer_dog` scenarios to the evaluator for broader coverage
- **LLM-as-judge dimension**: Add a scoring dimension that uses a separate LLM to rate "warmth" and "playfulness" (expensive but captures subjective quality)
- **T2 scenario**: Create a T2 scenario to test the full tier spectrum
- **A/B comparison mode**: Run both old and new prompts and compare head-to-head
- **Parallel evaluation**: Run multiple scenarios concurrently for faster experiments
- **Re-enable optimization loop**: If hill-climbing becomes valuable after structural improvements, build `program.md` from the deprioritized Task 4 spec
