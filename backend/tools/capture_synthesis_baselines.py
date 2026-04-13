"""Capture golden baselines for synthesis prompt and direction rendering.

Run from backend/ with:
    uv run python tools/capture_synthesis_baselines.py

Writes 4 golden files to tests/fixtures/golden/:
  - story_system_prompt.txt         (collaborative_story fmt.system_prompt rendered)
  - story_user_prompt.txt           (collaborative_story fmt.user_prompt rendered)
  - story_direction_T1.txt          (_build_story_direction for story state, T1)
  - comparison_direction_T1.txt     (_build_story_direction for comparison state, T1)

Uses fixed synthetic inputs so output is deterministic. These goldens are
the canonical pre-refactor baselines — the test suite diffs rendered format
templates against them to prove Phase 2+3 preserved byte-for-byte fidelity.
"""

import sys
from pathlib import Path

# Ensure backend/ is on the path whether this script is run from backend/ or
# from the repo root.
_SCRIPT_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPT_DIR.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from schemas.creative_slots import Cat5CreativeSlots, StoryScaffold
from schemas.session_state import SessionStateModel
from schemas.turn_directive import StoryElement
from synthesis_formats.loader import get_format, get_format_registry
from turn_handling.directive import _build_story_direction
from turn_handling.synthesis import _build_template_variables

_REPO_ROOT = _BACKEND_DIR.parent
_GOLDEN_DIR = _REPO_ROOT / "tests" / "fixtures" / "golden"

# ---------------------------------------------------------------------------
# Fixed synthetic inputs (deterministic — same output every run)
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
    """Build a deterministic Cat5 SessionStateModel for the story format."""
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
    """Build a deterministic Cat5 SessionStateModel for the comparison format."""
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
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Capture all 4 golden baselines and write to tests/fixtures/golden/."""
    _GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

    # Ensure the registry is reloaded fresh (defensive — no other code mutates it).
    get_format_registry.cache_clear()

    story_state = _make_story_state()
    comparison_state = _make_comparison_state()

    print("Rendering collaborative_story system/user prompts...")
    story_fmt = get_format("collaborative_story")
    story_variables = _build_template_variables(story_state, story_fmt)
    system_prompt = story_fmt.system_prompt.format(**story_variables)
    user_prompt = story_fmt.user_prompt.format(**story_variables)

    print("Capturing story direction for T1 story state...")
    # Both directions below render via fmt.direction_template under the hood.
    story_direction, _ = _build_story_direction(story_state, chosen_theme="One friend gets lost")

    print("Capturing comparison direction for T1 comparison state...")
    comparison_direction, _ = _build_story_direction(comparison_state, chosen_theme="")

    files = {
        "story_system_prompt.txt": system_prompt,
        "story_user_prompt.txt": user_prompt,
        "story_direction_T1.txt": story_direction,
        "comparison_direction_T1.txt": comparison_direction,
    }

    for filename, content in files.items():
        path = _GOLDEN_DIR / filename
        path.write_text(content, encoding="utf-8")
        size = path.stat().st_size
        print(f"  Wrote {filename} ({size} bytes)")

    print(f"\nAll golden files written to: {_GOLDEN_DIR}")


if __name__ == "__main__":
    main()
