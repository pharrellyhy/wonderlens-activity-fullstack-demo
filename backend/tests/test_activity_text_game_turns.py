from schemas.creative_slots import Cat5CreativeSlots
from schemas.session_state import SessionStateModel
from turn_handling.collection import record_text_collection_pick
from turn_handling.helpers import _sync_round_from_step


def test_text_collection_pick_records_typed_item() -> None:
    state = SessionStateModel(
        session_id="s1",
        tier="T1",
        template_type="cat5",
        activity_type="activity_phoneme_treasure_hunt",
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=3,
        interaction_mode="text",
        creative_slots=Cat5CreativeSlots(
            observation_angle="form",
            collection_criterion="objects or words whose names start with letter B",
            collection_count=3,
            mission_metaphor="sound treasure hunt",
            role_title="Sound Treasure Hunter",
            synthesis_type="naming_story",
            stuck_hint="Try a word nearby.",
            naming_prompt="What word did you find?",
            detail_question_template="What sound does it start with?",
        ),
    )

    assert record_text_collection_pick(state, "ball") is True

    assert state.collection_phase == "detail"
    assert state.collected_text_items == ["ball"]
    assert state.collected_photos == ["text_find_1"]


def test_text_collection_pick_rejects_non_b_word_for_phoneme_hunt() -> None:
    state = SessionStateModel(
        session_id="s2",
        tier="T1",
        template_type="cat5",
        activity_type="activity_phoneme_treasure_hunt",
        current_step="STEP_3_COLLECT_1",
        current_round=1,
        total_rounds=3,
        interaction_mode="text",
        creative_slots=Cat5CreativeSlots(
            observation_angle="form",
            collection_criterion="objects or words whose names start with letter B",
            collection_count=3,
            mission_metaphor="sound treasure hunt",
            role_title="Sound Treasure Hunter",
            synthesis_type="naming_story",
            stuck_hint="Try a word nearby.",
            naming_prompt="What word did you find?",
            detail_question_template="Which B word did you choose?",
        ),
    )

    assert record_text_collection_pick(state, "screen") is False

    assert state.collection_phase == "photo"
    assert state.collected_text_items == []
    assert state.collected_photos == []


def _phoneme_state(step: str, current_round: int) -> SessionStateModel:
    return SessionStateModel(
        session_id="sync",
        tier="T1",
        template_type="cat5",
        activity_type="activity_phoneme_treasure_hunt",
        current_step=step,
        current_round=current_round,
        total_rounds=3,
        interaction_mode="text",
        creative_slots=Cat5CreativeSlots(
            observation_angle="form",
            collection_criterion="objects or words whose names start with letter B",
            collection_count=3,
            mission_metaphor="sound treasure hunt",
            role_title="Sound Treasure Hunter",
            synthesis_type="naming_story",
            stuck_hint="Try a word nearby.",
            naming_prompt="What word did you find?",
            detail_question_template="Which B word did you choose?",
        ),
    )


def test_sync_round_clears_stale_round_on_celebrate_step() -> None:
    state = _phoneme_state("STEP_5_CELEBRATE", current_round=3)
    _sync_round_from_step(state)
    # Non-round steps must not retain a round-keyed value that would make
    # round-keyed frame lookups go stale.
    assert state.current_round == 0


def test_sync_round_sets_round_on_collect_step() -> None:
    state = _phoneme_state("STEP_3_COLLECT_2", current_round=0)
    _sync_round_from_step(state)
    assert state.current_round == 2
