"""Focused tests for the activity text-game live smoke helper."""

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
SCRIPT_PATH = SCRIPTS_DIR / "run_activity_text_smoke.py"


def _load_smoke_module():
    sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location("run_activity_text_smoke", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SMOKE = _load_smoke_module()


def test_check_dialogue_contract_accepts_source_specific_activity_terms() -> None:
    failures = SMOKE.check_dialogue_contract(
        "activity_career_decision_role_play",
        [
            "Firefighter mission. The smoke alarm is ringing.",
            "Choose the water hose before we talk about cooking oil.",
        ],
    )

    assert failures == []


def test_check_dialogue_contract_rejects_activity_drift_terms() -> None:
    failures = SMOKE.check_dialogue_contract(
        "activity_career_decision_role_play",
        ["Let's pretend to be a doctor, builder, or teacher today."],
    )

    assert any("forbidden term" in failure for failure in failures)


def test_career_contract_accepts_firefighter_alarm_paraphrase() -> None:
    failures = SMOKE.check_dialogue_contract(
        "activity_career_decision_role_play",
        [
            "You are now a Firefighter Helper ready to stop the ringing alarm.",
            "What do you think is the very first thing we should do?",
        ],
    )

    assert failures == []


def test_recognition_contract_rejects_physical_input_language() -> None:
    failures = SMOKE.check_dialogue_contract(
        "activity_recognition_pop_challenge",
        ["Point to the matching target."],
    )

    assert any("forbidden term" in failure for failure in failures)


def test_recognition_contract_accepts_natural_text_choice_language() -> None:
    failures = SMOKE.check_dialogue_contract(
        "activity_recognition_pop_challenge",
        ["Which picture matches the target? Please type the matching picture name or a short description."],
    )

    assert failures == []


def test_recognition_contract_rejects_old_left_right_suffix() -> None:
    failures = SMOKE.check_dialogue_contract(
        "activity_recognition_pop_challenge",
        ["Please type left, right, this, that, or a short description."],
    )

    assert any("forbidden term" in failure for failure in failures)


def test_partial_reveal_contract_accepts_live_clue_paraphrase() -> None:
    failures = SMOKE.check_dialogue_contract(
        "activity_partial_reveal_guess",
        [
            "A mystery lens reveals small clues before the whole picture.",
            "Let's be Picture Clue Detectives and spot tiny peeks of hiding things.",
        ],
    )

    assert failures == []


def test_phoneme_contract_accepts_sound_and_plural_words() -> None:
    failures = SMOKE.check_dialogue_contract(
        "activity_phoneme_treasure_hunt",
        [
            "If we find three words that start with its sound, we'll unlock a treasure map.",
            "Here comes the shiny letter card for the B sound.",
        ],
    )

    assert failures == []


def test_resolve_activity_ids_uses_catalog_order_and_validates_requested_ids() -> None:
    activities = [
        {"id": "activity_word_echo_practice", "name": "Word Echo Practice"},
        {"id": "activity_story_challenge_unlock", "name": "Story Challenge Unlock"},
    ]

    assert SMOKE.resolve_activity_ids(activities, []) == [
        "activity_word_echo_practice",
        "activity_story_challenge_unlock",
    ]
    assert SMOKE.resolve_activity_ids(activities, ["activity_story_challenge_unlock"]) == [
        "activity_story_challenge_unlock",
    ]

    try:
        SMOKE.resolve_activity_ids(activities, ["missing_activity"])
    except ValueError as exc:
        assert "missing_activity" in str(exc)
    else:
        raise AssertionError("expected missing activity to fail")


def test_build_http_client_ignores_proxy_environment() -> None:
    client = SMOKE.build_http_client(timeout=3.0)

    try:
        assert client.trust_env is False
    finally:
        client.close()


def test_check_start_payload_validates_text_session_contract() -> None:
    payload = {
        "status": "ok",
        "session_id": "session-1",
        "activity_type": "activity_word_echo_practice",
        "template_type": "cat1",
        "first_turn": {"dialogue": "Echo time!"},
        "session_state": {"status": "active", "interaction_mode": "text", "current_step": "STEP_1_HOOK"},
    }

    assert SMOKE.check_start_payload("activity_word_echo_practice", payload) == []

    payload["session_state"]["interaction_mode"] = "voice"
    failures = SMOKE.check_start_payload("activity_word_echo_practice", payload)

    assert "session_state.interaction_mode is not text" in failures
