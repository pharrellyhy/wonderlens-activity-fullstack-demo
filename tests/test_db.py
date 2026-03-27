"""Tests for the async SQLite database layer."""

import tempfile
from pathlib import Path

import pytest

from db import get_session, init_db, log_session, log_turn, update_session_status


@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> str:
    return str(tmp_path / "test.db")


@pytest.mark.asyncio
async def test_init_db_creates_file(tmp_db_path: str) -> None:
    await init_db(tmp_db_path)
    assert Path(tmp_db_path).exists()


@pytest.mark.asyncio
async def test_log_and_get_session(tmp_db_path: str) -> None:
    await init_db(tmp_db_path)
    await log_session(tmp_db_path, "sess-1", "T0", "mood_changer_dog")

    session = await get_session(tmp_db_path, "sess-1")
    assert session is not None
    assert session["tier"] == "T0"
    assert session["scenario"] == "mood_changer_dog"
    assert session["status"] == "active"


@pytest.mark.asyncio
async def test_get_session_not_found(tmp_db_path: str) -> None:
    await init_db(tmp_db_path)
    session = await get_session(tmp_db_path, "nonexistent")
    assert session is None


@pytest.mark.asyncio
async def test_update_session_status(tmp_db_path: str) -> None:
    await init_db(tmp_db_path)
    await log_session(tmp_db_path, "sess-2", "T1", "polka_dot_patrol")
    await update_session_status(tmp_db_path, "sess-2", "completed", "all_rounds_done", 6)

    session = await get_session(tmp_db_path, "sess-2")
    assert session is not None
    assert session["status"] == "completed"
    assert session["end_reason"] == "all_rounds_done"
    assert session["total_turns"] == 6


@pytest.mark.asyncio
async def test_log_turn(tmp_db_path: str) -> None:
    await init_db(tmp_db_path)
    await log_session(tmp_db_path, "sess-3", "T0", "mood_changer_dog")
    await log_turn(
        tmp_db_path,
        "sess-3",
        turn_number=1,
        role="ai",
        text="Hello!",
        response_type="hook",
        is_silent=False,
        consecutive_silence=0,
    )
    # If we get here without error, the turn was logged successfully


@pytest.mark.asyncio
async def test_init_db_creates_parent_dirs() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        nested = Path(tmpdir) / "a" / "b" / "test.db"
        await init_db(str(nested))
        assert nested.exists()
