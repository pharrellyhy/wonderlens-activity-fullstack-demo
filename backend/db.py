"""Async SQLite database layer for session, turn, and agent log persistence."""

from pathlib import Path
from typing import Any

import aiosqlite

try:
    from .config import get_settings
except ImportError:
    from config import get_settings


def _db_path() -> str:
    return get_settings().db_path


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    tier TEXT NOT NULL,
    scenario TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    recipe_status TEXT DEFAULT 'ok',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    end_reason TEXT,
    total_turns INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    turn_number INTEGER NOT NULL,
    role TEXT NOT NULL,
    text TEXT,
    response_type TEXT,
    screen_widget TEXT,
    sfx_cue TEXT,
    latency_ms INTEGER,
    is_silent BOOLEAN DEFAULT FALSE,
    consecutive_silence INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    agent TEXT NOT NULL,
    latency_ms INTEGER,
    success BOOLEAN,
    fallback_used BOOLEAN DEFAULT FALSE,
    input_tokens INTEGER,
    output_tokens INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_session ON agent_logs(session_id);
"""


async def init_db(db_path: str = "data/demo.db") -> None:
    """Create the database directory and tables if they don't exist."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(_SCHEMA_SQL)
        await db.commit()


async def log_session(
    db_path: str,
    session_id: str,
    tier: str,
    scenario: str,
    status: str = "active",
    recipe_status: str = "ok",
) -> None:
    """Insert a new session record."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO sessions (session_id, tier, scenario, status, recipe_status) VALUES (?, ?, ?, ?, ?)",
            (session_id, tier, scenario, status, recipe_status),
        )
        await db.commit()


async def log_turn(
    db_path: str,
    session_id: str,
    turn_number: int,
    role: str,
    text: str | None = None,
    response_type: str | None = None,
    screen_widget: str | None = None,
    sfx_cue: str | None = None,
    latency_ms: int | None = None,
    is_silent: bool = False,
    consecutive_silence: int = 0,
) -> None:
    """Insert a turn record for a session."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """INSERT INTO turns
            (session_id, turn_number, role, text, response_type, screen_widget, sfx_cue, latency_ms, is_silent, consecutive_silence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session_id,
                turn_number,
                role,
                text,
                response_type,
                screen_widget,
                sfx_cue,
                latency_ms,
                is_silent,
                consecutive_silence,
            ),
        )
        await db.commit()


async def log_agent_call(
    session_id: str,
    agent: str,
    latency_ms: int | None = None,
    success: bool | None = None,
    fallback_used: bool = False,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    error_message: str | None = None,
) -> None:
    """Insert an agent execution log record."""
    async with aiosqlite.connect(_db_path()) as db:
        await db.execute(
            """INSERT INTO agent_logs
            (session_id, agent, latency_ms, success, fallback_used, input_tokens, output_tokens, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, agent, latency_ms, success, fallback_used, input_tokens, output_tokens, error_message),
        )
        await db.commit()


async def update_session_status(
    db_path: str,
    session_id: str,
    status: str,
    end_reason: str | None = None,
    total_turns: int | None = None,
) -> None:
    """Update a session's status, optionally setting end reason and total turns."""
    async with aiosqlite.connect(db_path) as db:
        if end_reason is not None and total_turns is not None:
            await db.execute(
                "UPDATE sessions SET status = ?, ended_at = CURRENT_TIMESTAMP, end_reason = ?, total_turns = ? WHERE session_id = ?",
                (status, end_reason, total_turns, session_id),
            )
        elif end_reason is not None:
            await db.execute(
                "UPDATE sessions SET status = ?, ended_at = CURRENT_TIMESTAMP, end_reason = ? WHERE session_id = ?",
                (status, end_reason, session_id),
            )
        elif total_turns is not None:
            await db.execute(
                "UPDATE sessions SET status = ?, total_turns = ? WHERE session_id = ?",
                (status, total_turns, session_id),
            )
        else:
            await db.execute(
                "UPDATE sessions SET status = ? WHERE session_id = ?",
                (status, session_id),
            )
        await db.commit()


async def get_session(db_path: str, session_id: str) -> dict[str, Any] | None:
    """Retrieve a session by ID, returning a dict or None if not found."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)
