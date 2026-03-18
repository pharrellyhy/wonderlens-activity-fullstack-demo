# QA Monitor Workflow + Known Bug Fixes

## Context

After implementing the instruction-based recipe system, iterative testing revealed many LLM response quality issues (premature celebration, directive language, round bundling, etc.) that were caught one-by-one through manual testing. This plan establishes:

1. **Fix known bugs** — two display bugs identified during testing
2. **QA monitor workflow** — ongoing development workflow where Claude monitors server logs in real-time, flags issues, and batch-fixes after testing sessions

---

## Part 1: Fix Known Bugs

### Bug 1: Cat1 device panel always shows "Round 1"

**Root cause**: Backend `state_machine.py:193` sends `"round_number": rnd` in `widget_params`, but frontend `CharacterDisplay.jsx:13` destructures `roundNumber` (camelCase). Since `roundNumber` is never in the params, it defaults to `1`.

**Fix**: Rename `round_number` → `roundNumber` in all `widget_params` for `character_display` widgets.

**Files**:
- `backend/state_machine.py` — lines 182, 193, 225: `round_number` → `roundNumber`
- `backend/recipes/*.json` — all `round_number` keys in screen frame widget_params → `roundNumber`

### Bug 2: Round display "0/3" before rounds start

**Root cause**: `_sync_round_from_step()` in `server.py:1206` only updates `current_round` when the step starts with `STEP_3_ROUND_` or `STEP_3_COLLECT_`. Before that, `current_round` remains `0`. The frontend `Math.max(current_round, 1)` should show `1` not `0`, but user reports seeing `0`.

**Fix**: Show `-` before rounds start instead of a number. Update `App.jsx:120-126` to check if `current_step` is a round step before showing the round counter, similar to how cat5 already handles it.

**File**: `frontend/src/App.jsx` — line 120-126

---

## Part 2: QA Monitor Workflow

### Workflow

1. User starts the server: `cd backend && uv run uvicorn server:app --reload --port 8000`
2. Claude tails the server log output in background
3. User tests interactions in the browser
4. Claude periodically reads log output, analyzing two categories:

### Monitoring: Script Agent LLM Responses

Watch for `--- LLM RAW ---` blocks and check:
- Emotion tag present and appropriate for step
- Invitational language (no directives: "Go find!", "Now let's...", "Tell me!")
- Responds to child's actual words before scripted content
- One step per turn (no bundling next round scenario)
- Round escalation progressing
- Cat5 collection progress accurate (no premature celebration)
- `stay_on_step: true` when child is confused/stuck
- `child_intent` set correctly on STEP_2

### Monitoring: State Machine Transitions

Watch server logs for:
- `current_round` advancing correctly (1→2→3, not stuck or skipping)
- `current_step` transitions matching expected flow
- Auto-advance firing only when appropriate
- `invitation_decline_count` tracked correctly
- Session status transitions (active → completed, not premature)
- Screen frame `widget_params` containing correct round numbers

### Log Patterns

```
# LLM responses
"Script LLM response: step=..., round=..., activity=..."
"--- LLM RAW ---"

# State transitions
"Instruction recipe session started: ..."
"Script turn: step=..., round=..., latency=..."

# Errors
"Script Agent turn failed"
"Script Agent streaming failed"
```

### Findings Format

For each issue found, record:
- Entity / step / round
- Child input
- LLM response (relevant excerpt)
- What's wrong
- Fix target (which file + what to change)

### Fix Strategy: Option B (batch)

- Do NOT edit files mid-session (server --reload kills active session)
- Queue all findings during testing
- Batch-apply fixes after user finishes testing
- Critical issues (completely broken flow) can be flagged for immediate attention

---

## Verification

1. Fix Bug 1 → start Cat1 activity → device panel should show correct round numbers (1, 2, 3)
2. Fix Bug 2 → before rounds start → footer should show `-` not `0/3`
3. Monitor workflow → start server, tail logs, run through all 5 entities, collect findings
4. Run `uv run ruff check . && uv run ruff format .` after all fixes
