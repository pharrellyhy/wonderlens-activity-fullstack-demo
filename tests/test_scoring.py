"""Unit tests for prompt evaluation scoring functions."""

import sys
from pathlib import Path

import pytest

# Ensure scripts/ is importable
SCRIPTS_DIR = str(Path(__file__).resolve().parents[1] / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from scoring import (
    compute_composite_score,
    score_completion_language,
    score_item_suggestion_free,
    score_phrasing_variety,
    score_tier_compliance,
    score_validation_pass,
)

# --- score_validation_pass ---


class TestScoreValidationPass:
    def test_t0_scaffold_with_model_phrase_passes(self) -> None:
        result = score_validation_pass(
            dialogue="[excited] I think it looks like a cloud! Is it fluffy or smooth?",
            step="STEP_3_COLLECT_1",
            tier="T0",
            collection_phase="detail",
            is_first_on_step=True,
        )
        assert result == 1.0

    def test_t0_open_question_without_scaffold_fails(self) -> None:
        result = score_validation_pass(
            dialogue="[curious] What does this remind you of?",
            step="STEP_3_COLLECT_1",
            tier="T0",
            collection_phase="detail",
            is_first_on_step=True,
        )
        assert result == 0.0

    def test_non_t0_open_question_passes(self) -> None:
        result = score_validation_pass(
            dialogue="[curious] What does this remind you of?",
            step="STEP_3_COLLECT_1",
            tier="T1",
            collection_phase="detail",
            is_first_on_step=True,
        )
        assert result == 1.0

    def test_t0_synthesis_with_binary_choice_passes(self) -> None:
        result = score_validation_pass(
            dialogue="[excited] Should we make a silly story or a cozy story?",
            step="STEP_4_SYNTHESIS",
            tier="T0",
            is_first_on_step=True,
        )
        assert result == 1.0

    def test_t0_synthesis_open_question_no_choice_fails(self) -> None:
        result = score_validation_pass(
            dialogue="[curious] What kind of story do you want to tell?",
            step="STEP_4_SYNTHESIS",
            tier="T0",
            is_first_on_step=True,
        )
        assert result == 0.0

    def test_t0_round_with_model_phrase_passes(self) -> None:
        result = score_validation_pass(
            dialogue="[playful] I think it looks like a dinosaur! What do you see?",
            step="STEP_3_ROUND_1",
            tier="T0",
        )
        assert result == 1.0

    def test_hook_always_passes(self) -> None:
        result = score_validation_pass(
            dialogue="[excited] Look at this!",
            step="STEP_1_HOOK",
            tier="T0",
        )
        assert result == 1.0


# --- score_item_suggestion_free ---


class TestScoreItemSuggestionFree:
    def test_no_suggestion_scores_1(self) -> None:
        result = score_item_suggestion_free("[excited] I wonder what soft thing you'll discover next!")
        assert result == 1.0

    def test_specific_item_suggestion_scores_0(self) -> None:
        result = score_item_suggestion_free("[excited] Find a pillow or a blanket!")
        assert result == 0.0

    def test_incidental_mention_passes(self) -> None:
        result = score_item_suggestion_free("[celebrating] That pillow is so fluffy!")
        assert result == 1.0


# --- score_completion_language ---


class TestScoreCompletionLanguage:
    def test_no_completion_when_items_remain(self) -> None:
        result = score_completion_language(
            dialogue="[excited] Great find! Would you like to look for one more?",
            collected=1,
            total=3,
        )
        assert result == 1.0

    def test_premature_completion_scores_0(self) -> None:
        result = score_completion_language(
            dialogue="[proud] You found them all! Collection is complete!",
            collected=1,
            total=3,
        )
        assert result == 0.0

    def test_completion_when_done_is_fine(self) -> None:
        result = score_completion_language(
            dialogue="[proud] You found them all! Collection is complete!",
            collected=3,
            total=3,
        )
        assert result == 1.0


# --- score_tier_compliance ---


class TestScoreTierCompliance:
    def test_t0_short_with_tag_passes(self) -> None:
        result = score_tier_compliance("[excited] Wow, so fluffy!", tier="T0")
        assert result == 1.0

    def test_t0_too_many_sentences_penalized(self) -> None:
        long_dialogue = "[excited] Wow! That's amazing! I love it! Let me tell you more! This is really great!"
        result = score_tier_compliance(long_dialogue, tier="T0")
        assert result < 1.0

    def test_missing_emotion_tag_penalized(self) -> None:
        result = score_tier_compliance("Wow, so fluffy!", tier="T0")
        assert result < 1.0

    def test_t2_longer_dialogue_passes(self) -> None:
        dialogue = "[curious] That's a really interesting texture. It reminds me of velvet. What do you think makes it feel that way?"
        result = score_tier_compliance(dialogue, tier="T2")
        assert result >= 0.75


# --- score_phrasing_variety ---


class TestScorePhrasingVariety:
    def test_identical_phrases_score_low(self) -> None:
        result = score_phrasing_variety(
            [
                "That's 1 out of 3!",
                "That's 2 out of 3!",
                "That's 3 out of 3!",
            ]
        )
        assert result < 0.5

    def test_varied_phrases_score_high(self) -> None:
        result = score_phrasing_variety(
            [
                "Your first treasure!",
                "Two friends in the collection now!",
                "The squad is complete!",
            ]
        )
        assert result > 0.7

    def test_single_phrase_returns_1(self) -> None:
        assert score_phrasing_variety(["Just one!"]) == 1.0

    def test_empty_list_returns_1(self) -> None:
        assert score_phrasing_variety([]) == 1.0


# --- compute_composite_score ---


class TestComputeCompositeScore:
    def test_perfect_scores(self) -> None:
        result = compute_composite_score(
            validation_scores=[1.0, 1.0],
            item_suggestion_scores=[1.0, 1.0],
            completion_language_scores=[1.0, 1.0],
            tier_compliance_scores=[1.0, 1.0],
            variety_score=1.0,
        )
        assert result == pytest.approx(100.0)

    def test_all_zeros(self) -> None:
        result = compute_composite_score(
            validation_scores=[0.0],
            item_suggestion_scores=[0.0],
            completion_language_scores=[0.0],
            tier_compliance_scores=[0.0],
            variety_score=0.0,
        )
        assert result == pytest.approx(0.0)

    def test_empty_lists_default_to_1(self) -> None:
        result = compute_composite_score(
            validation_scores=[],
            item_suggestion_scores=[],
            completion_language_scores=[],
            tier_compliance_scores=[],
            variety_score=0.5,
        )
        # All empty lists → avg 1.0, variety 0.5
        # 1.0*50 + 1.0*25 + 1.0*15 + 1.0*5 + 0.5*5 = 97.5
        assert result == pytest.approx(97.5)

    def test_weights_are_correct(self) -> None:
        # Only validation fails — should lose 50 points
        result = compute_composite_score(
            validation_scores=[0.0],
            item_suggestion_scores=[1.0],
            completion_language_scores=[1.0],
            tier_compliance_scores=[1.0],
            variety_score=1.0,
        )
        assert result == pytest.approx(50.0)
