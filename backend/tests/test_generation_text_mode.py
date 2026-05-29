from agents.script_agent import _build_directive_speaker_prompt, _enforce_text_only_dialogue
from recipe_loader import load_instruction_recipe, recipe_to_session_state
from schemas.turn_directive import TurnDirective
from schemas.turn_response import TurnResponse
from turn_handling.generation import _enforce_text_only_interaction


def test_recognition_pop_text_mode_rewrites_physical_choice_prompts() -> None:
    recipe = load_instruction_recipe("activity_recognition_pop_challenge")
    state = recipe_to_session_state(recipe, "text-mode-session", "T1", "recognition_pop_challenge")
    state.interaction_mode = "text"
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
    recipe = load_instruction_recipe("activity_recognition_pop_challenge")
    state = recipe_to_session_state(recipe, "text-mode-session", "T1", "recognition_pop_challenge")
    state.interaction_mode = "text"

    dialogue = _enforce_text_only_dialogue(
        state,
        "[excited] Can you point out the best target card on the pop board?",
    )

    lower_dialogue = dialogue.lower()
    assert "point" not in lower_dialogue
    assert "card" not in lower_dialogue
    assert "name the best target picture" in lower_dialogue


def test_recognition_pop_directive_prompt_bans_physical_input_language() -> None:
    recipe = load_instruction_recipe("activity_recognition_pop_challenge")
    state = recipe_to_session_state(recipe, "text-mode-session", "T1", "recognition_pop_challenge")
    state.interaction_mode = "text"
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
    recipe = load_instruction_recipe("activity_recognition_pop_challenge")
    state = recipe_to_session_state(recipe, "text-mode-session", "T1", "recognition_pop_challenge")
    state.interaction_mode = "text"
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
    recipe = load_instruction_recipe("activity_recognition_pop_challenge")
    state = recipe_to_session_state(recipe, "text-mode-session", "T1", "recognition_pop_challenge")
    state.interaction_mode = "text"
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
    state = recipe_to_session_state(recipe, "text-mode-session", "T1", "recognition_pop_challenge")

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
