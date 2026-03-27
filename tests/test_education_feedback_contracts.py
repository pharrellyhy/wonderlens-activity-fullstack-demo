"""Regression checks for the education-team feedback implementation."""

from pathlib import Path

from entity_registry import all_entities_for_api
from game_loader import get_demo_entities

REPO_ROOT = Path(__file__).resolve().parents[1]
USE_SESSION_ORCHESTRATION_PATH = REPO_ROOT / "frontend" / "src" / "hooks" / "useSessionOrchestration.js"
USE_SILENCE_TIMER_PATH = REPO_ROOT / "frontend" / "src" / "hooks" / "useSilenceTimer.js"
GAME_DETAIL_VIEW_PATH = REPO_ROOT / "frontend" / "src" / "components" / "GameDetailView.jsx"


def test_muted_tts_path_clears_pending_completion_timeout() -> None:
    """Muted TTS should not leave a stale completion callback alive after reset/rerender."""
    source = USE_SESSION_ORCHESTRATION_PATH.read_text(encoding="utf-8")

    assert "const mutedCompletionTimeoutRef = useRef(null);" in source
    assert "const clearMutedCompletionTimeout = useCallback(() => {" in source
    assert "clearTimeout(mutedCompletionTimeoutRef.current);" in source
    assert "mutedCompletionTimeoutRef.current = window.setTimeout(() => {" in source
    assert "return clearMutedCompletionTimeout;" in source
    assert "clearMutedCompletionTimeout();" in source


def test_unmuting_does_not_replay_the_current_ai_message() -> None:
    """Toggling TTS back on should not perturb the current turn's silence timer."""
    source = USE_SESSION_ORCHESTRATION_PATH.read_text(encoding="utf-8")

    assert "lastSpokenIndexRef.current = messages.length - 2;" not in source
    assert "stopTTS();" in source


def test_silence_timer_uses_flat_timeout() -> None:
    """Frontend silence timeout should be a single flat constant."""
    source = USE_SILENCE_TIMER_PATH.read_text(encoding="utf-8")

    assert "const SILENCE_TIMEOUT = 30000;" in source
    assert "const timeout = SILENCE_TIMEOUT;" in source


def test_demo_entity_summaries_include_plain_description_and_steps() -> None:
    """The API-facing demo summaries should expose the new plain-language metadata."""
    for category in all_entities_for_api():
        for photo in category["photos"]:
            summary = photo["summary"]
            assert summary["plain_description"]
            assert summary["steps_summary"]
            assert isinstance(summary["steps_summary"], list)


def test_loaded_demo_entities_include_plain_description_and_steps() -> None:
    """Loaded demo entities should carry the new metadata from game frontmatter."""
    for entity in get_demo_entities():
        assert entity.plain_description
        assert entity.steps_summary


def test_game_detail_view_shows_steps_and_game_details() -> None:
    """The pre-start screen should display steps and expandable game design details."""
    source = GAME_DETAIL_VIEW_PATH.read_text(encoding="utf-8")

    assert "How It Works" in source
    assert "steps_summary" in source
    assert "Game design details" in source
