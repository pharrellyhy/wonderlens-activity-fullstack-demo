"""Regression checks for the immersive character sound frontend contracts."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
USE_CONVERSATION_PATH = REPO_ROOT / "frontend" / "src" / "hooks" / "useConversation.js"
USE_SESSION_ORCHESTRATION_PATH = REPO_ROOT / "frontend" / "src" / "hooks" / "useSessionOrchestration.js"


def test_hook_turns_keep_character_sfx_on_session_start() -> None:
    """First-turn character sounds should survive the initial conversation state setup."""
    source = USE_CONVERSATION_PATH.read_text(encoding="utf-8")

    assert source.count("characterSfx: data.first_turn.character_sfx || [],") == 2


def test_muted_tts_path_does_not_play_outros_twice() -> None:
    """Muted playback should leave outro playback to handleSpeakingDone()."""
    source = USE_SESSION_ORCHESTRATION_PATH.read_text(encoding="utf-8")

    timeout_block = (
        "mutedCompletionTimeoutRef.current = window.setTimeout(() => {\n"
        "          mutedCompletionTimeoutRef.current = null;\n"
        "          handleSpeakingDone();\n"
        "        }, 500);"
    )
    assert timeout_block in source
