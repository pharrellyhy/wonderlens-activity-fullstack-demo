# Plan: Comprehensive Turn Logging

## Context

The `turns` table currently only logs AI responses (`role = "ai"`). User turns (child speech, silence, photo picks) are never inserted. Internal state (`current_step`, `collection_phase`, `synthesis_phase`, etc.) is also absent. This makes post-session debugging extremely difficult — the synthesis gap analysis for session `a6425e09` required cross-referencing agent logs, turn timestamps, and code to reconstruct what the child did and what state transitions occurred.

## Design Decisions

- **Approach:** Extend the existing `turns` table with new nullable columns rather than creating a separate table. Both user and AI turns go through the same `log_turn()` call.
- **Schema migration:** Use `ALTER TABLE ADD COLUMN` with defaults so existing data is preserved — no destructive migration needed.
- **State snapshot:** Store a JSON blob of key state fields at the time of each turn, not the full `SessionStateModel`. This keeps the column compact while capturing what matters for debugging.
- **Logging site:** Add user turn logging in `server.py` (both `/api/turn` and `/api/turn-speak`) *before* calling `resolve_turn`, and keep the existing AI turn logging *after*. This gives a clear before/after picture.
- **Hook turn logging:** Also log the first AI turn from `/api/start` and `/api/start-deep-link` so the full conversation is in the db from turn 1.

## Schema Changes

### Existing `turns` table — add 3 columns:

```sql
ALTER TABLE turns ADD COLUMN photo_id TEXT;
ALTER TABLE turns ADD COLUMN step TEXT;
ALTER TABLE turns ADD COLUMN state_snapshot TEXT;  -- JSON blob
```

- `photo_id`: The photo the child submitted (Cat5 collection), NULL for AI turns and non-photo user turns.
- `step`: The `current_step` value at the time this turn was logged (e.g. `STEP_3_COLLECT_2`, `STEP_4_SYNTHESIS`).
- `state_snapshot`: JSON string with key state fields for debugging. Captured for every turn (user and AI). Structure:

```json
{
  "current_step": "STEP_3_COLLECT_2",
  "current_round": 2,
  "collection_phase": "detail",
  "synthesis_phase": "invite",
  "consecutive_silence": 0,
  "consecutive_wrong": 0,
  "collected_photos": ["fuzzy_moss"],
  "collected_names": ["Mossy Velvet"],
  "turn_count": 5
}
```

## Implementation Steps

### Step 1: Update schema and migration in `backend/db.py`

- Add the 3 new columns to `_SCHEMA_SQL` (`CREATE TABLE IF NOT EXISTS`)
- Add an `_MIGRATION_SQL` list with `ALTER TABLE` statements wrapped in try/except (SQLite doesn't support `IF NOT EXISTS` for columns — catch the "duplicate column" error)
- Run migrations in `init_db()` after `executescript(_SCHEMA_SQL)`
- Update `log_turn()` signature to accept `photo_id`, `step`, and `state_snapshot` (all optional, default None)
- Update the INSERT statement to include the new columns

### Step 2: Add `_build_state_snapshot()` helper in `backend/server.py`

```python
def _build_state_snapshot(state: SessionStateModel) -> str:
    """Build a compact JSON snapshot of key state fields for turn logging."""
    snapshot = {
        "current_step": state.current_step,
        "current_round": state.current_round,
        "collection_phase": state.collection_phase,
        "synthesis_phase": state.synthesis_phase,
        "consecutive_silence": state.consecutive_silence,
        "consecutive_wrong": state.consecutive_wrong,
        "collected_photos": state.collected_photos,
        "collected_names": state.collected_names,
        "turn_count": state.turn_count,
    }
    return json.dumps(snapshot, separators=(",", ":"))
```

### Step 3: Log user turns in `/api/turn` and `/api/turn-speak`

In both endpoints, *before* calling `resolve_turn()`, insert a user turn:

```python
# Log user input
await log_turn(
    settings.db_path,
    req.session_id,
    state.turn_count + 1,  # next turn number
    "user",
    text=req.text if req.text else None,
    is_silent=req.is_silent,
    photo_id=req.photo_id,
    step=state.current_step,
    state_snapshot=_build_state_snapshot(state),
)
```

### Step 4: Enhance existing AI turn logging

Update the existing `log_turn()` calls (both endpoints) to include the new fields:

```python
await log_turn(
    settings.db_path,
    req.session_id,
    state.turn_count,
    "ai",
    result.turn_response.dialogue,
    response_type,
    is_silent=req.is_silent,
    consecutive_silence=state.consecutive_silence,
    step=state.current_step,
    state_snapshot=_build_state_snapshot(state),
)
```

### Step 5: Log the first AI turn from `/api/start` and `/api/start-deep-link`

The hook turn generated during session start is currently not logged. Add a `log_turn()` call after the first turn is generated so the db has the complete conversation from turn 1.

### Step 6: Update tests

- Update `tests/test_api.py` to verify user turns appear in the db alongside AI turns
- Verify `state_snapshot` is valid JSON and contains expected keys
- Verify `photo_id` is captured for collection turns

## Files Summary

| File | Action |
|------|--------|
| `backend/db.py` | Add columns to schema, migration logic, update `log_turn()` signature and INSERT |
| `backend/server.py` | Add `_build_state_snapshot()`, log user turns, enhance AI turn logging, log first turn from start endpoints |
| `tests/test_api.py` | Add assertions for user turns and state snapshots in db |

## Verification

1. `uv run pytest tests/test_api.py -q` — verify new logging assertions pass
2. `uv run ruff check backend/db.py backend/server.py` — lint clean
3. Manual: start a session, play a few turns, query `SELECT * FROM turns WHERE session_id = '...' ORDER BY id` and verify both user and AI rows with state snapshots
4. Manual: verify existing sessions still load (migration doesn't break old data)
