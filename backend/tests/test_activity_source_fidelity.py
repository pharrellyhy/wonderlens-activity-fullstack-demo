import json
import re
from dataclasses import dataclass
from pathlib import Path

from activity_catalog import activity_summaries
from agents.script_agent import _build_instruction_overlay
from agents.turn_director import _select_step_phase_rules
from game_loader import get_demo_entities, get_demo_recipe
from recipe_loader import recipe_to_session_state
from turn_handling.directive import _fast_path_directive
from turn_handling.helpers import _collection_photo_prompt

SOURCE_PACKAGES_DIR = Path(
    "/Users/pharrelly/codebase/github/wonderlens-activity-autodesign/"
    "runs/20260521_163621_workbook_review_packet_full/activity_packages"
)
REPRESENTATIVE_ACTIVITY_IDS = (
    "activity_career_decision_role_play",
    "activity_guided_drawing",
    "activity_phoneme_treasure_hunt",
    "activity_animal_sound_imitation",
    "activity_constellation_star_count",
    "activity_emotion_reader",
    "activity_partial_reveal_guess",
    "activity_recognition_pop_challenge",
    "activity_story_challenge_unlock",
    "activity_travel_planner",
    "activity_vegetable_sort",
    "activity_word_echo_practice",
)
CHILD_FACING_DEVICE_WORD_RE = re.compile(r"\b(card|cards|token|tokens|tap|touch|point|click)\b", re.IGNORECASE)


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
        required_terms=("letter b", "beginning sound", "word", "phoneme_letter_card_01", "no letter screen"),
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


def _child_facing_source_contract_text(activity_id: str) -> str:
    recipe = get_demo_recipe(activity_id)
    assert recipe is not None
    instructions = recipe.step_instructions
    steps = [instructions.hook, instructions.transition, *instructions.rounds, instructions.celebrate, instructions.closing]
    if instructions.synthesis is not None:
        steps.append(instructions.synthesis)

    fields: list[str] = []
    for step in steps:
        source_contract = step.source_contract
        fields.extend(
            [
                source_contract.runtime_instruction,
                source_contract.example_ai_line,
                source_contract.child_responses.ideal,
                source_contract.child_responses.unexpected,
                source_contract.child_responses.no_response,
                source_contract.ai_followups.ideal,
                source_contract.ai_followups.unexpected,
                source_contract.ai_followups.no_response,
            ]
        )
    return "\n".join(fields)


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


def test_representative_child_facing_dialogue_avoids_device_bound_words() -> None:
    for activity_id in REPRESENTATIVE_ACTIVITY_IDS:
        child_facing_text = _child_facing_source_contract_text(activity_id)

        match = CHILD_FACING_DEVICE_WORD_RE.search(child_facing_text)

        assert match is None, f"{activity_id} child-facing dialogue contains device-bound word: {match.group(0)}"


def test_phoneme_treasure_hunt_is_b_starting_item_hunt_not_object_noise_game() -> None:
    recipe_text = _activity_search_text("activity_phoneme_treasure_hunt")

    assert "letter b" in recipe_text
    assert "starts with b" in recipe_text or "start with b" in recipe_text
    assert "ball" in recipe_text
    assert "banana" in recipe_text
    assert "basket" in recipe_text
    assert "what sound does your word start with" not in recipe_text
    assert "what sound does it make" not in recipe_text
    assert "object noise" not in recipe_text


def test_phoneme_collection_prompt_uses_letter_b_criterion_not_sensory_form() -> None:
    recipe = get_demo_recipe("activity_phoneme_treasure_hunt")
    assert recipe is not None
    state = recipe_to_session_state(recipe, "phoneme-prompt-session", "T1", "phoneme_treasure_hunt")
    state.current_step = "STEP_3_COLLECT_1"
    state.current_round = 1
    state.collection_phase = "photo"

    response = _collection_photo_prompt(state)

    dialogue = response.dialogue.lower()
    assert "letter b" in dialogue or "b word" in dialogue
    assert "start with b" in dialogue or "starts with b" in dialogue
    assert "wiggly" not in dialogue
    assert "bumpy" not in dialogue
    assert "spiky" not in dialogue
    assert "fingers" not in dialogue


def test_phoneme_turn_director_rules_stay_criterion_focused() -> None:
    recipe = get_demo_recipe("activity_phoneme_treasure_hunt")
    assert recipe is not None
    state = recipe_to_session_state(recipe, "phoneme-rules-session", "T1", "phoneme_treasure_hunt")
    state.current_step = "STEP_3_COLLECT_1"
    state.current_round = 1

    rules = _select_step_phase_rules(state).lower()

    assert "collection criterion" in rules
    assert "something {observation_angle}" not in rules
    assert "squishy or smooth" not in rules


def test_career_acceptance_fast_path_uses_decision_prompt_not_emotion_prompt() -> None:
    recipe = get_demo_recipe("activity_career_decision_role_play")
    assert recipe is not None
    state = recipe_to_session_state(recipe, "career-acceptance-session", "T1", "career_decision_role_play")
    state.current_step = "STEP_2_RULES"
    state.current_round = 0

    directive = _fast_path_directive("yes", state)

    assert directive is not None
    direction = directive.response_direction.lower()
    assert "firefighter" in direction
    assert "send help" in direction
    assert "check first" in direction
    assert "feels" not in direction
    assert "reacts" not in direction


def test_career_hook_confirmation_stays_on_rules_not_first_decision() -> None:
    recipe = get_demo_recipe("activity_career_decision_role_play")
    assert recipe is not None
    state = recipe_to_session_state(recipe, "career-hook-session", "T1", "career_decision_role_play")
    state.current_step = "STEP_1_HOOK"
    state.current_round = 0

    directive = _fast_path_directive("sure", state)

    assert directive is not None
    assert directive.action == "advance"
    direction = directive.response_direction.lower()
    assert "choice loop" in direction
    assert "ready" in direction
    assert "send help" not in direction
    assert "water hose" not in direction
    assert "cooking oil" not in direction


def test_phoneme_hook_confirmation_stays_on_rules_not_first_find() -> None:
    recipe = get_demo_recipe("activity_phoneme_treasure_hunt")
    assert recipe is not None
    state = recipe_to_session_state(recipe, "phoneme-hook-session", "T1", "phoneme_treasure_hunt")
    state.current_step = "STEP_1_HOOK"
    state.current_round = 0

    directive = _fast_path_directive("yes", state)

    assert directive is not None
    assert directive.action == "advance"
    direction = directive.response_direction.lower()
    assert "rule" in direction
    assert "starts with letter b" in direction
    assert "ready" in direction
    assert "first b word" not in direction
    assert "tell me the first" not in direction


def test_career_uncertainty_stays_on_current_bounded_decision() -> None:
    recipe = get_demo_recipe("activity_career_decision_role_play")
    assert recipe is not None
    state = recipe_to_session_state(recipe, "career-uncertainty-session", "T1", "career_decision_role_play")
    state.current_step = "STEP_3_ROUND_3"
    state.current_round = 3

    directive = _fast_path_directive("i don't know", state)

    assert directive is not None
    assert directive.action in {"stay", "need_help"}
    assert directive.stay_on_step is True
    direction = directive.response_direction.lower()
    assert "check people are safe outside" in direction
    assert "run inside alone" in direction
    assert "water hose" not in direction
    assert "cooking oil" not in direction


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
