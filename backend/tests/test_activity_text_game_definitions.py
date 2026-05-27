from activity_catalog import activity_summaries
from game_loader import get_demo_recipe


EXPECTED_IDS = {
    "activity_phoneme_treasure_hunt",
    "activity_partial_reveal_guess",
    "activity_animal_sound_imitation",
    "activity_word_echo_practice",
    "activity_emotion_reader",
    "activity_constellation_star_count",
    "activity_career_decision_role_play",
    "activity_vegetable_sort",
    "activity_travel_planner",
    "activity_guided_drawing",
    "activity_story_challenge_unlock",
    "activity_recognition_pop_challenge",
}


def test_activity_text_game_definitions_load() -> None:
    summaries = activity_summaries()

    assert {summary.id for summary in summaries} == EXPECTED_IDS
    assert all(summary.kind == "activity" for summary in summaries)
    assert all(summary.source_export_id.startswith("concept_") for summary in summaries)
    assert all(summary.premise for summary in summaries)


def test_each_activity_has_recipe() -> None:
    for activity_id in EXPECTED_IDS:
        recipe = get_demo_recipe(activity_id)
        assert recipe is not None
        assert recipe.metadata.round_count >= 3
