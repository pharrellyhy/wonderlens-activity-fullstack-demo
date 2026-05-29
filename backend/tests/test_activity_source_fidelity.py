import json
from dataclasses import dataclass
from pathlib import Path

from activity_catalog import activity_summaries
from agents.script_agent import _build_instruction_overlay
from game_loader import get_demo_entities, get_demo_recipe
from recipe_loader import recipe_to_session_state

SOURCE_PACKAGES_DIR = Path(
    "/Users/pharrelly/codebase/github/wonderlens-activity-autodesign/"
    "runs/20260521_163621_workbook_review_packet_full/activity_packages"
)


@dataclass(frozen=True)
class SourceFidelityContract:
    required_terms: tuple[str, ...]
    forbidden_terms: tuple[str, ...] = ()


SOURCE_FIDELITY_CONTRACTS = {
    "activity_animal_sound_imitation": SourceFidelityContract(
        required_terms=("animal", "sound", "voice", "animal_sound_cards_01", "rabbit", "cat meow", "puppy"),
    ),
    "activity_career_decision_role_play": SourceFidelityContract(
        required_terms=("firefighter", "smoke alarm", "water hose", "cooking oil", "career_portrait_cards_01"),
        forbidden_terms=("doctor", "builder", "teacher"),
    ),
    "activity_constellation_star_count": SourceFidelityContract(
        required_terms=("constellation", "star", "count", "constellation_count_cards_01", "voice only"),
    ),
    "activity_emotion_reader": SourceFidelityContract(
        required_terms=("feeling", "cue", "help", "emotion_expression_cards_01"),
    ),
    "activity_guided_drawing": SourceFidelityContract(
        required_terms=("paper", "pencil", "drawing", "caregiver", "no assessment", "guided_drawing_step_cards_01"),
    ),
    "activity_partial_reveal_guess": SourceFidelityContract(
        required_terms=(
            "distinctive part",
            "visible clue",
            "guess",
            "partial_reveal_cards_01",
            "cat ears",
            "cat paws",
            "cat face",
            "voice only",
        ),
    ),
    "activity_phoneme_treasure_hunt": SourceFidelityContract(
        required_terms=("target sound", "beginning sound", "word", "phoneme_letter_card_01", "no letter screen"),
    ),
    "activity_recognition_pop_challenge": SourceFidelityContract(
        required_terms=(
            "target",
            "match",
            "changing set",
            "distractor",
            "red apple",
            "blue car",
            "strawberry",
            "cherries",
            "basketball",
            "recognition_challenge_cards_01",
            "do not ask the child to point",
        ),
    ),
    "activity_story_challenge_unlock": SourceFidelityContract(
        required_terms=(
            "fox",
            "moon door",
            "silver",
            "white",
            "blue",
            "owl",
            "hoo hoo",
            "star page",
            "bonjour",
            "story_unlock_cards_01",
        ),
    ),
    "activity_travel_planner": SourceFidelityContract(
        required_terms=("travel", "pack", "predict", "how to travel", "vehicle", "travel_planning_cards_01"),
    ),
    "activity_vegetable_sort": SourceFidelityContract(
        required_terms=("vegetable", "sort", "rule", "photographed vegetables", "edible part", "cooking use", "vegetable_sort_cards_01"),
    ),
    "activity_word_echo_practice": SourceFidelityContract(
        required_terms=("word", "echo", "repeat", "word_echo_cards_01", "voice only"),
    ),
}


def _activity_search_text(activity_id: str) -> str:
    recipe = get_demo_recipe(activity_id)
    assert recipe is not None
    entity = next(entity for entity in get_demo_entities() if entity.activity_type == activity_id)
    game_text = (Path(__file__).parents[1] / "games" / f"{activity_id}.md").read_text(encoding="utf-8")
    return (
        json.dumps(recipe.model_dump(mode="json"), sort_keys=True)
        + " "
        + json.dumps(entity.model_dump(mode="json"), sort_keys=True)
        + " "
        + game_text
    ).lower().replace("-", " ")


def test_activity_source_packages_exist() -> None:
    for summary in activity_summaries():
        package_dir = SOURCE_PACKAGES_DIR / summary.source_export_id

        assert package_dir.exists(), f"{summary.id} source package not found: {package_dir}"
        assert (package_dir / "prod.md").exists(), f"{summary.id} source package has no prod.md"
        assert (package_dir / "spec.md").exists(), f"{summary.id} source package has no spec.md"


def test_activity_recipes_preserve_source_specific_terms() -> None:
    for activity_id, contract in SOURCE_FIDELITY_CONTRACTS.items():
        recipe_text = _activity_search_text(activity_id)

        for term in contract.required_terms:
            assert term in recipe_text, f"{activity_id} recipe lost source term: {term}"

        for term in contract.forbidden_terms:
            assert term not in recipe_text, f"{activity_id} recipe contains drift term: {term}"


def test_activity_recipes_preserve_source_dialogue_contracts() -> None:
    for summary in activity_summaries():
        recipe = get_demo_recipe(summary.id)
        assert recipe is not None

        instructions = recipe.step_instructions
        assert instructions.source_intent_lock, f"{summary.id} lost source intent lock"
        assert instructions.runtime_detail_floor_notes, f"{summary.id} lost runtime detail floor notes"

        required_steps = [instructions.hook, instructions.transition, *instructions.rounds, instructions.celebrate, instructions.closing]
        if instructions.synthesis is not None:
            required_steps.append(instructions.synthesis)

        for step in required_steps:
            source_contract = step.source_contract
            assert source_contract.runtime_instruction, f"{summary.id} lost runtime instruction for {step.goal}"
            assert source_contract.example_ai_line, f"{summary.id} lost example AI line for {step.goal}"
            assert source_contract.child_responses.ideal, f"{summary.id} lost ideal child response for {step.goal}"
            assert source_contract.child_responses.unexpected, f"{summary.id} lost unexpected child response for {step.goal}"
            assert source_contract.child_responses.no_response, f"{summary.id} lost no-response branch for {step.goal}"
            assert source_contract.ai_followups.ideal, f"{summary.id} lost ideal follow-up for {step.goal}"
            assert source_contract.ai_followups.unexpected, f"{summary.id} lost unexpected follow-up for {step.goal}"
            assert source_contract.ai_followups.no_response, f"{summary.id} lost no-response follow-up for {step.goal}"
            assert source_contract.screen, f"{summary.id} lost screen contract for {step.goal}"


def test_script_overlay_includes_source_dialogue_contract_for_current_step() -> None:
    recipe = get_demo_recipe("activity_career_decision_role_play")
    assert recipe is not None
    state = recipe_to_session_state(recipe, "source-fidelity-session", "T1", "career_decision_role_play")
    state.current_step = "STEP_3_ROUND_1"
    state.current_round = 1

    overlay = _build_instruction_overlay(state)

    assert "Source intent lock:" in overlay
    assert "Runtime instruction: Assign the profession first and keep the child inside the role." in overlay
    assert (
        'Example AI line: "Today you are the firefighter. A smoke alarm is ringing. '
        'Should your team send help now?"'
    ) in overlay
    assert "Ideal child response:" in overlay
    assert "Unexpected child response:" in overlay
    assert "No-response follow-up:" in overlay
