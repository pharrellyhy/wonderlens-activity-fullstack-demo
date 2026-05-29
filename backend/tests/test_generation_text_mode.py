from agents.script_agent import _build_directive_speaker_prompt, _enforce_text_only_dialogue
from recipe_loader import load_instruction_recipe, recipe_to_session_state
from schemas.session_state import SessionStateModel
from schemas.turn_directive import TurnDirective
from schemas.turn_response import TurnResponse
from turn_handling.generation import _enforce_text_only_interaction

TEXT_ONLY_REPRESENTATIVE_ACTIVITIES = (
    ("activity_career_decision_role_play", "career_decision_role_play"),
    ("activity_guided_drawing", "guided_drawing"),
    ("activity_phoneme_treasure_hunt", "phoneme_treasure_hunt"),
)


def _text_state(activity_type: str, filename: str) -> SessionStateModel:
    recipe = load_instruction_recipe(activity_type)
    state = recipe_to_session_state(recipe, "text-mode-session", "T1", filename)
    state.interaction_mode = "text"
    return state


def test_recognition_pop_text_mode_rewrites_physical_choice_prompts() -> None:
    state = _text_state("activity_recognition_pop_challenge", "recognition_pop_challenge")
    response = TurnResponse(
        dialogue="Can you look at the screen and point to the twin? Imagine touching the target card.",
        tone_marker="curious",
        screen_widget="photo_display",
        screen_widget_params={},
    )

    rewritten = _enforce_text_only_interaction(state, response)

    dialogue = rewritten.dialogue.lower()
    assert "type left, right, this, that, or a short description" not in dialogue
    assert "target card" not in dialogue
    assert "target picture" in dialogue
    assert "point" not in dialogue
    assert "touch" not in dialogue


def test_recognition_pop_text_mode_rewrites_directive_speaker_output() -> None:
    state = _text_state("activity_recognition_pop_challenge", "recognition_pop_challenge")

    dialogue = _enforce_text_only_dialogue(
        state,
        "[excited] Can you point out the best target card on the pop board?",
    )

    lower_dialogue = dialogue.lower()
    assert "point" not in lower_dialogue
    assert "card" not in lower_dialogue
    assert "name the best target picture" in lower_dialogue


def test_recognition_pop_directive_prompt_bans_physical_input_language() -> None:
    state = _text_state("activity_recognition_pop_challenge", "recognition_pop_challenge")
    directive = TurnDirective(
        action="advance",
        reasoning="The child agreed to play.",
        response_direction="Introduce the red apple target and ask for the best match.",
        emotion_tag="excited",
    )

    prompt = _build_directive_speaker_prompt(state, directive)

    assert "Text-only recognition mode" in prompt
    assert "NEVER say point, tap, click, touch, card, or cards." in prompt


def test_recognition_pop_text_mode_keeps_existing_choice_questions_concise() -> None:
    state = _text_state("activity_recognition_pop_challenge", "recognition_pop_challenge")
    response = TurnResponse(
        dialogue="Which picture matches the target best?",
        tone_marker="curious",
        screen_widget="photo_display",
        screen_widget_params={},
    )

    rewritten = _enforce_text_only_interaction(state, response)

    assert rewritten.dialogue == "Which picture matches the target best?"
    assert "left, right" not in rewritten.dialogue.lower()


def test_recognition_pop_text_mode_adds_natural_prompt_when_dialogue_has_no_choice_cue() -> None:
    state = _text_state("activity_recognition_pop_challenge", "recognition_pop_challenge")
    response = TurnResponse(
        dialogue="The match board is ready.",
        tone_marker="curious",
        screen_widget="photo_display",
        screen_widget_params={},
    )

    rewritten = _enforce_text_only_interaction(state, response)

    dialogue = rewritten.dialogue.lower()
    assert "type left, right, this, that, or a short description" not in dialogue
    assert dialogue.endswith("please type the matching picture name or a short description.")


def test_recognition_pop_recipe_avoids_child_facing_left_right_suffix() -> None:
    recipe = load_instruction_recipe("activity_recognition_pop_challenge")
    state = _text_state("activity_recognition_pop_challenge", "recognition_pop_challenge")

    instructions = recipe.step_instructions
    child_facing_text = " ".join(
        [
            *state.creative_slots.round_scenarios,
            instructions.hook.goal,
            instructions.hook.constraint,
            instructions.transition.goal,
            instructions.transition.constraint,
            *[
                " ".join([round_instruction.goal, round_instruction.scenario, round_instruction.constraint])
                for round_instruction in instructions.rounds
            ],
        ]
    ).lower()

    assert "left, right" not in child_facing_text
    assert "this/that" not in child_facing_text
    assert "target card" not in child_facing_text


def test_text_mode_sanitizes_device_words_for_representative_activities() -> None:
    for activity_type, filename in TEXT_ONLY_REPRESENTATIVE_ACTIVITIES:
        state = _text_state(activity_type, filename)
        response = TurnResponse(
            dialogue="Point to the card, tap the helper token, or click the picture when you know.",
            tone_marker="curious",
            screen_widget="photo_display",
            screen_widget_params={},
        )

        rewritten = _enforce_text_only_interaction(state, response)

        dialogue = rewritten.dialogue.lower()
        assert "point" not in dialogue
        assert "tap" not in dialogue
        assert "click" not in dialogue
        assert "card" not in dialogue
        assert "token" not in dialogue


def test_phoneme_text_mode_normalizes_b_sound_language_to_b_starting_words() -> None:
    state = _text_state("activity_phoneme_treasure_hunt", "phoneme_treasure_hunt")

    dialogue = _enforce_text_only_dialogue(
        state,
        "[excited] Look all around and tell me the first B thing you see with the B sound!",
    )

    lower_dialogue = dialogue.lower()
    assert "b sound" not in lower_dialogue
    assert "b thing" not in lower_dialogue
    assert "letter b start" in lower_dialogue
    assert "b word or b object" in lower_dialogue


def test_directive_prompt_bans_physical_input_language_for_representative_activities() -> None:
    directive = TurnDirective(
        action="stay",
        reasoning="The child needs a bounded text response.",
        response_direction="Repeat the current activity choice with friendly language.",
        emotion_tag="curious",
    )

    for activity_type, filename in TEXT_ONLY_REPRESENTATIVE_ACTIVITIES:
        state = _text_state(activity_type, filename)

        prompt = _build_directive_speaker_prompt(state, directive)

        assert "Text-only activity mode" in prompt
        assert "NEVER say point, tap, click, touch, card, cards, token, or tokens." in prompt
