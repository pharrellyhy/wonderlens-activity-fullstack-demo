# Plan: Debug Panel for Manual Testing

## Context

During manual testing of the WonderLens demo, internal state (step transitions, synthesis phases, generation retries, planner constraints) is invisible. The synthesis gap analysis for session `a6425e09` required cross-referencing db logs, agent timestamps, and source code to figure out what went wrong. A real-time debug panel would make issues like "the LLM kept asking questions instead of generating a story" immediately visible.

## Design Summary

- **Toggle**: Ctrl+D keyboard shortcut, hidden by default
- **Position**: Bottom drawer, slides up over the conversation panel, max 45vh
- **Theme**: Dark (Catppuccin Mocha), monospace, compact
- **Data source**: Extended `/api/turn` response with a `debug` field (no new endpoints)
- **Two tabs**: State Machine (flow + session state) and Generation (attempts + planner + retry stats)

## Implementation

### Step 1: Backend — capture generation debug data

**File: `backend/turn_handler.py`**

1. Add `GenerationDebugInfo` dataclass (near existing `TurnResult`):
   - `step`, `attempt_count`, `final_verdict` ("passed"/"exhausted"/"error_fallback")
   - `attempts`: list of `{attempt, verdict, hint}` dicts

2. Modify `_generate_with_retry()` to return `tuple[TurnResponse, GenerationDebugInfo]`:
   - Track each attempt's validation verdict and hint in a list
   - Return the debug info alongside the response

3. Update all call sites of `_generate_with_retry()` in `resolve_turn()` and `_resolve_synthesis_turn()`:
   - Unpack as `turn_response, gen_debug = await _generate_with_retry(...)`
   - Keep a `last_gen_debug` variable in scope, overwritten by each call

4. Add `debug: dict | None = None` field to `TurnResult` dataclass

5. Add helper functions:
   - `_build_debug_payload(state, gen_debug, script_agent)` → assembles the debug dict
   - `_build_step_flow(state)` → computes step pipeline with done/current/pending status

6. Populate `result.debug` at each `return TurnResult(...)` in `resolve_turn()`

### Step 2: Backend — wire debug into API responses

**File: `backend/server.py`**

1. Add `result.debug` to the JSON response in both `/api/turn` and `/api/turn-speak`
2. Add `get_retry_stats` to the imports from `turn_handler`
3. For `/api/start` responses: include a minimal debug dict with just `step_flow` (no generation info for the first hook turn)

### Step 3: Frontend — state plumbing

**File: `frontend/src/hooks/useConversation.js`**
- Add `const [debugData, setDebugData] = useState(null)`
- Extract `data.debug` in the turn response handler
- Clear on `reset()`
- Return `debugData` from the hook

**File: `frontend/src/hooks/useSessionOrchestration.js`**
- Destructure `debugData` from `useConversation()` and include in return object

**File: `frontend/src/App.jsx`**
- Add `const [debugOpen, setDebugOpen] = useState(false)`
- Add `useEffect` with `keydown` listener for Ctrl+D toggle (with `e.preventDefault()`)
- Destructure `debugData` from `useSessionOrchestration`
- Render `<DebugPanel>` with `isOpen={debugOpen}` (always rendered, position toggled for smooth animation)

### Step 4: Frontend — DebugPanel component

**New file: `frontend/src/components/DebugPanel.jsx`**

Props: `{ debugData, sessionState, templateType, isOpen }`

Structure:
```
DebugPanel (fixed bottom-0, z-50, transition-transform)
├── Tab bar: "State Machine" | "Generation" + turn/latency indicator
├── State Machine tab
│   ├── Step flow pipeline (horizontal badges: ✓ done, ▸ current, ○ pending)
│   ├── Session state grid (round, phases, silence, auto_advance)
│   └── Collection context (cat5: names, details, collected count)
└── Generation tab
    ├── This turn (attempt count, verdict, failure reasons)
    ├── Planner constraints (boolean flags as colored badges)
    └── Session retry stats (per-step table with pass rate)
```

Styling: Tailwind classes with Catppuccin Mocha color values. Slide animation via `translate-y-full` / `translate-y-0` with `transition-transform duration-300`.

### Step 5: Tests

**New file: `tests/test_debug_payload.py`**
- Test `_build_step_flow()` for cat1 (7 steps) and cat5 (8 steps), verify correct statuses
- Test `_build_debug_payload()` with mocked state/agent, verify dict structure
- Test `_generate_with_retry()` returns debug info with correct attempt_count and verdict

**Existing file: `tests/test_api.py`**
- Add assertion that `/api/turn` response contains a `debug` key with expected sub-keys

## Key files

| File | Action |
|------|--------|
| `backend/turn_handler.py` | Add debug dataclasses, modify `_generate_with_retry()` return type, add debug helpers |
| `backend/server.py` | Wire `result.debug` into turn responses |
| `frontend/src/components/DebugPanel.jsx` | **New** — the panel component |
| `frontend/src/hooks/useConversation.js` | Add `debugData` state |
| `frontend/src/hooks/useSessionOrchestration.js` | Thread `debugData` through |
| `frontend/src/App.jsx` | Keyboard toggle, render DebugPanel |
| `tests/test_debug_payload.py` | **New** — backend debug payload tests |
| `tests/test_api.py` | Add debug field assertion |

## Verification

1. `uv run pytest tests/test_debug_payload.py tests/test_api.py tests/test_turn_handler.py -q` — all pass
2. `uv run ruff check backend/turn_handler.py backend/server.py` — lint clean
3. `cd frontend && npm run build` — builds without errors
4. Manual: start a session, press Ctrl+D, verify State Machine tab shows step flow and session state
5. Manual: send a turn, verify Generation tab shows attempt count and planner constraints
6. Manual: trigger a validation retry (e.g., T0 open question), verify attempt 1 failure reason appears
7. Manual: press Ctrl+D again, verify panel slides closed
