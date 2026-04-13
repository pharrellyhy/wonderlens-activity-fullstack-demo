"""Golden-file diff tests for collaborative_story synthesis format rendering.

Each test renders a prompt or direction template against a deterministic synthetic
session state and asserts byte-for-byte equality with the pre-refactor golden
files captured by backend/tools/capture_synthesis_baselines.py.

If a test fails with a diff the format file's template is wrong — fix the format
file; do not edit the golden files.
"""

from pathlib import Path

from schemas.creative_slots import Cat5CreativeSlots, StoryScaffold
from schemas.session_state import SessionStateModel
from schemas.turn_directive import StoryElement
from synthesis_formats.loader import get_format, get_format_registry
from turn_handling.synthesis import _build_template_variables

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GOLDEN_DIR = _REPO_ROOT / "tests" / "fixtures" / "golden"

# ---------------------------------------------------------------------------
# Deterministic synthetic state — must match capture_synthesis_baselines.py
# ---------------------------------------------------------------------------

_TIER = "T1"
_COLLECTED_PHOTOS = ["soft_petal", "woolly_caterpillar", "fuzzy_moss"]
_COLLECTED_NAMES = ["Peter", "Spiky", "Sam"]
_COLLECTED_DETAILS = ["soft", "wiggly", "fluffy"]
_SYNTHESIS_CHILD_STORY = "Peter wants to fly"

_STORY_SCAFFOLD = StoryScaffold(
    premise="Each fluffy find becomes a character with a talent based on how it feels",
    harvest_per_round="character_talent",
    harvest_question_strategy="R1: direct texture question; R2: compare to previous; R3: group role",
    synthesis_goal="Characters combine their talents on a shared adventure",
    synthesis_format="collaborative_story",
    story_themes=["One friend gets lost", "A surprise storm"],
)

_STORY_ELEMENTS = [
    StoryElement(round_number=1, character_name="Peter", trait_or_detail="soft"),
    StoryElement(round_number=2, character_name="Spiky", trait_or_detail="wiggly"),
    StoryElement(round_number=3, character_name="Sam", trait_or_detail="fluffy"),
]


_COMPARISON_SCAFFOLD = StoryScaffold(
    premise="Observe how the same pattern dimension appears differently on each find",
    harvest_per_round="comparison_observation",
    harvest_question_strategy="R1: direct question; R2: compare to previous; R3: group comparison",
    synthesis_goal="Children see how pattern varies across all items",
    synthesis_format="comparison_reveal",
    story_themes=[],
)


def _make_story_state() -> SessionStateModel:
    """Build the deterministic Cat5 SessionStateModel used by all three golden tests."""
    slots = Cat5CreativeSlots(
        observation_angle="texture",
        collection_criterion="fluffy or soft things",
        collection_count=3,
        mission_metaphor="Fluffy friend finder",
        role_title="Fluffy Expedition Leader",
        stuck_hint="Look for things that feel soft or fuzzy",
        naming_prompt="What would you call this fluffy friend?",
        detail_question_template="What does it feel like?",
        story_scaffold=_STORY_SCAFFOLD,
    )
    return SessionStateModel(
        session_id="golden-baseline-story",
        tier=_TIER,
        template_type="cat5",
        activity_type="fluffy_expedition_dandelion",
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        total_rounds=3,
        creative_slots=slots,
        collected_photos=_COLLECTED_PHOTOS,
        collected_names=_COLLECTED_NAMES,
        collected_details=_COLLECTED_DETAILS,
        synthesis_child_story=_SYNTHESIS_CHILD_STORY,
        story_elements=_STORY_ELEMENTS,
    )


def _make_comparison_state() -> SessionStateModel:
    """Build the deterministic Cat5 SessionStateModel for the comparison format."""
    slots = Cat5CreativeSlots(
        observation_angle="pattern",
        collection_criterion="things with interesting patterns",
        collection_count=3,
        mission_metaphor="Pattern detective",
        role_title="Pattern Patrol Officer",
        stuck_hint="Look for things with spots, stripes, or dots",
        naming_prompt="What patterns do you see?",
        detail_question_template="What kind of pattern does it have?",
        sorting_criterion="",
        story_scaffold=_COMPARISON_SCAFFOLD,
    )
    return SessionStateModel(
        session_id="golden-baseline-comparison",
        tier=_TIER,
        template_type="cat5",
        activity_type="polka_dot_patrol",
        current_step="STEP_4_SYNTHESIS",
        current_round=3,
        total_rounds=3,
        creative_slots=slots,
        collected_photos=_COLLECTED_PHOTOS,
        collected_names=_COLLECTED_NAMES,
        collected_details=_COLLECTED_DETAILS,
        story_elements=_STORY_ELEMENTS,
    )


# ---------------------------------------------------------------------------
# Golden-file diff tests
# ---------------------------------------------------------------------------


class TestCollaborativeStorySystemPromptMatchesGolden:
    def test_collaborative_story_system_prompt_matches_golden(self) -> None:
        get_format_registry.cache_clear()
        try:
            state = _make_story_state()
            fmt = get_format("collaborative_story")
            variables = _build_template_variables(state, fmt)
            rendered = fmt.system_prompt.format(**variables)
            expected = (_GOLDEN_DIR / "story_system_prompt.txt").read_text(encoding="utf-8")
            assert rendered == expected, (
                f"System prompt mismatch.\n"
                f"Expected ({len(expected)} chars):\n{expected!r}\n\n"
                f"Got ({len(rendered)} chars):\n{rendered!r}"
            )
        finally:
            get_format_registry.cache_clear()


class TestCollaborativeStoryUserPromptMatchesGolden:
    def test_collaborative_story_user_prompt_matches_golden(self) -> None:
        get_format_registry.cache_clear()
        try:
            state = _make_story_state()
            fmt = get_format("collaborative_story")
            variables = _build_template_variables(state, fmt)
            rendered = fmt.user_prompt.format(**variables)
            expected = (_GOLDEN_DIR / "story_user_prompt.txt").read_text(encoding="utf-8")
            assert rendered == expected, (
                f"User prompt mismatch.\n"
                f"Expected ({len(expected)} chars):\n{expected!r}\n\n"
                f"Got ({len(rendered)} chars):\n{rendered!r}"
            )
        finally:
            get_format_registry.cache_clear()


class TestCollaborativeStoryDirectionMatchesGolden:
    def test_collaborative_story_direction_matches_golden(self) -> None:
        get_format_registry.cache_clear()
        try:
            state = _make_story_state()
            fmt = get_format("collaborative_story")
            variables = _build_template_variables(state, fmt, chosen_theme="One friend gets lost")
            rendered = fmt.direction_template.format(**variables)
            expected = (_GOLDEN_DIR / "story_direction_T1.txt").read_text(encoding="utf-8")
            assert rendered == expected, (
                f"Direction template mismatch.\n"
                f"Expected ({len(expected)} chars):\n{expected!r}\n\n"
                f"Got ({len(rendered)} chars):\n{rendered!r}"
            )
        finally:
            get_format_registry.cache_clear()


class TestComparisonRevealDirectionMatchesGolden:
    def test_comparison_reveal_direction_matches_golden(self) -> None:
        get_format_registry.cache_clear()
        try:
            state = _make_comparison_state()
            fmt = get_format("comparison_reveal")
            variables = _build_template_variables(state, fmt, chosen_theme="")
            rendered = fmt.direction_template.format(**variables)
            expected = (_GOLDEN_DIR / "comparison_direction_T1.txt").read_text(encoding="utf-8")
            assert rendered == expected, (
                f"Comparison direction mismatch.\n"
                f"Expected ({len(expected)} chars):\n{expected!r}\n\n"
                f"Got ({len(rendered)} chars):\n{rendered!r}"
            )
        finally:
            get_format_registry.cache_clear()
