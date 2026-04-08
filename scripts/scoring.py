"""Scoring functions for prompt evaluation.

Each function takes dialogue + context and returns a float between 0.0 and 1.0.
These are the building blocks of the composite metric used by evaluate_prompts.py.
"""

import re
import sys
from pathlib import Path

# Add backend to path so we can import turn_handling validators
_BACKEND_DIR = str(Path(__file__).resolve().parents[1] / "backend")
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from turn_handling import (
    _ITEM_SUGGESTION_RE,
    _ends_with_open_question,
    _has_completion_language,
    _has_model_phrase,
)

# Emotion tag regex — must start with [tag]
_EMOTION_TAG_RE = re.compile(r"^\[.+?\] ")

# Tier sentence limits from tier_rules.yaml
_TIER_MAX_SENTENCES: dict[str, int] = {"T0": 2, "T1": 3, "T2": 4}


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
    # T0 collect detail: must scaffold (model phrase required if open question)
    if step.startswith("STEP_3_COLLECT_") and tier == "T0" and (collection_phase == "detail" or is_first_on_step):
        if _ends_with_open_question(dialogue) and not _has_model_phrase(dialogue):
            return 0.0

    # T0 synthesis: must offer binary choice if asking open question
    if step == "STEP_4_SYNTHESIS" and tier == "T0" and is_first_on_step:
        if _ends_with_open_question(dialogue) and " or " not in dialogue.lower():
            return 0.0

    # T0 Cat1 round: must scaffold
    if step.startswith("STEP_3_ROUND_") and tier == "T0":
        if _ends_with_open_question(dialogue) and not _has_model_phrase(dialogue):
            return 0.0

    return 1.0


def score_item_suggestion_free(dialogue: str) -> float:
    """Score 1.0 if dialogue does NOT suggest specific items to find, 0.0 if it does."""
    return 0.0 if _ITEM_SUGGESTION_RE.search(dialogue) else 1.0


def score_completion_language(dialogue: str, collected: int, total: int) -> float:
    """Score 1.0 if completion language is appropriate for the collection state.

    Penalizes premature completion language (when collected < total).
    Allows completion language when collection is actually done.
    """
    if collected >= total:
        return 1.0
    return 0.0 if _has_completion_language(dialogue) else 1.0


def score_tier_compliance(dialogue: str, tier: str) -> float:
    """Score tier-level compliance: emotion tag presence + sentence count.

    Returns average of two sub-scores:
    - 1.0 if emotion tag present, 0.0 if missing
    - 1.0 if sentence count <= tier max, linear penalty for excess
    """
    tag_score = 1.0 if _EMOTION_TAG_RE.match(dialogue) else 0.0

    # Count sentences (split on . ! ? followed by space or end)
    sentences = [s.strip() for s in re.split(r"[.!?]+\s*", dialogue) if s.strip()]
    max_sentences = _TIER_MAX_SENTENCES.get(tier, 3)
    count_score = min(1.0, max_sentences / max(len(sentences), 1))

    return (tag_score + count_score) / 2.0


def score_phrasing_variety(progress_phrases: list[str]) -> float:
    """Score how varied progress phrasing is across rounds.

    Uses word-level Jaccard distance. Returns 1.0 for maximum variety, 0.0 for identical.
    Returns 1.0 if fewer than 2 phrases (nothing to compare).
    """
    if len(progress_phrases) < 2:
        return 1.0

    word_sets = [set(p.lower().split()) for p in progress_phrases]
    similarities: list[float] = []
    for i in range(len(word_sets)):
        for j in range(i + 1, len(word_sets)):
            intersection = len(word_sets[i] & word_sets[j])
            union = len(word_sets[i] | word_sets[j])
            if union > 0:
                similarities.append(intersection / union)

    if not similarities:
        return 1.0

    avg_similarity = sum(similarities) / len(similarities)
    return 1.0 - avg_similarity


def score_cross_session_variety(session_dialogues: list[list[str]]) -> float:
    """Score how different dialogues are ACROSS sessions for the same scenario.

    Takes a list of sessions, where each session is a list of AI dialogue strings.
    Compares corresponding turns across sessions using Jaccard distance.
    Returns 1.0 for maximum variety, 0.0 for identical outputs across sessions.
    Returns 1.0 if fewer than 2 sessions.
    """
    if len(session_dialogues) < 2:
        return 1.0

    # Compare corresponding turns across sessions
    max_turns = max(len(s) for s in session_dialogues)
    turn_varieties: list[float] = []

    for turn_idx in range(max_turns):
        phrases = [s[turn_idx] for s in session_dialogues if turn_idx < len(s)]
        if len(phrases) < 2:
            continue
        turn_varieties.append(score_phrasing_variety(phrases))

    if not turn_varieties:
        return 1.0

    return sum(turn_varieties) / len(turn_varieties)


def compute_composite_score(
    validation_scores: list[float],
    item_suggestion_scores: list[float],
    completion_language_scores: list[float],
    tier_compliance_scores: list[float],
    variety_score: float,
) -> float:
    """Compute the weighted composite score (0-100).

    Weights:
    - Validation pass rate: 50%
    - Item suggestion free rate: 25%
    - Completion language accuracy: 15%
    - Tier compliance: 5%
    - Phrasing variety: 5%
    """

    def _avg(scores: list[float]) -> float:
        return sum(scores) / len(scores) if scores else 1.0

    return (
        _avg(validation_scores) * 50
        + _avg(item_suggestion_scores) * 25
        + _avg(completion_language_scores) * 15
        + _avg(tier_compliance_scores) * 5
        + variety_score * 5
    )
