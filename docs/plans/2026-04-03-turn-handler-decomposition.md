# Turn Handler Decomposition — Design Spec

**Date:** 2026-04-03
**Status:** Draft
**Goal:** Decompose `backend/turn_handler.py` (2,936 lines) into a `backend/turn_handling/` package for debuggability.

## 1. Problem

`turn_handler.py` contains all turn orchestration logic in a single file. Its main function, `resolve_turn`, is 619 lines with 60+ branches, 29 return paths, and state mutations across ~20 session fields. Debugging any single code path (e.g., Cat5 collection, invitation routing, synthesis) requires reading the entire function and mentally filtering out irrelevant branches.

## 2. Approach

Replace `backend/turn_handler.py` with a `backend/turn_handling/` package. Each module maps to a debuggable concern: when a bug surfaces in Cat5 collection, you open `collection.py` (~120 lines) instead of scrolling through 2,936.

Pure refactoring — no behavioral changes. The public API (`resolve_turn`, `TurnInput`, `TurnResult`, `get_retry_stats`) stays identical.

## 3. Package Structure

```
backend/turn_handling/
├── __init__.py      # Re-exports: resolve_turn, TurnInput, TurnResult, get_retry_stats
├── types.py         # ~35 lines  — TurnInput, TurnResult, GenerationDebugInfo dataclasses
├── helpers.py       # ~130 lines — Predicates, state mutation, screen frame, history helpers
├── generation.py    # ~280 lines — _generate_with_retry, validation, retry stats, intent classification
├── invitation.py    # ~80 lines  — Invitation step routing (decline/confirm/substantive)
├── collection.py    # ~120 lines — Cat5 photo validation, wrong-pick exit, detail phase
├── rounds.py        # ~180 lines — Round generation, deferred advance, guardrails
├── synthesis.py     # ~150 lines — Synthesis turn (invite/evaluate/improve phases)
├── directive.py     # ~150 lines — Turn Director path (feature-flagged bypass)
├── debug.py         # ~120 lines — Debug payload, step flow, phase timelines
└── core.py          # ~100 lines — resolve_turn dispatcher, silence, auto-advance
```

## 4. Module Responsibilities

### types.py (~35 lines)
Dataclasses only. No logic, no local dependencies.

- `TurnInput` — encapsulates raw input from one child turn (text, is_silent, photo_id)
- `TurnResult` — resolved outcome ready for endpoint serialization (turn_response, screen_frame, auto_advance, response_type, error_exit, debug)
- `GenerationDebugInfo` — telemetry captured during `_generate_with_retry`

### helpers.py (~130 lines)
Stateless predicates and small state mutation helpers. Imported by all step handlers.

**Predicates (read-only):**
- `is_invitation_step(step)` — checks if step is STEP_2_INVITATION
- `is_round_step(step)` — checks if step starts with STEP_3_ROUND_ or STEP_3_COLLECT_
- `is_closing_step(step)` — checks if step is a closing step
- `is_celebrate_step(step)` — checks if step is a celebration step
- `already_prompted_on_step(state)` — checks if AI already spoke on current step

**State mutation:**
- `advance_state(state)` — moves to next step via state machine
- `sync_round_from_step(state)` — synchronizes round number from step name
- `step_round_number(step)` — extracts round number from step string

**Response building:**
- `state_context(state)` — builds context dict for screen frame lookup
- `get_screen_frame(state)` — returns ScreenFrame for current state
- `get_response_type(state)` — determines response type string
- `ended_result(state, reason, dialogue)` — builds a TurnResult for session-ending conditions

**Conversation history:**
- `append_child_turn(state, text)` — adds child turn to history
- `append_ai_turn(state, dialogue, character_state)` — adds AI turn to history

### generation.py (~280 lines)
LLM generation with retry, validation, and retry stats.

- `generate_with_retry(state, turn_input, script_agent, ...)` — 3-attempt retry loop with plan-aware validation
- `validate_response(response, state)` — step-specific response validation rules
- `validate_plan(plan, response)` — validates response against turn plan
- `plan_retry_hint(state, response, plan_verdict)` — builds corrective hint for retry
- `record_retry_stat(state, ...)` / `get_retry_stats()` — retry telemetry

### invitation.py (~80 lines)
Handles STEP_2_INVITATION routing. Three paths:

- **Decline:** increment counter, exit on 2nd decline, re-invite on 1st
- **Confirm:** set `invitation_accepted`, advance, return deterministic celebration template
- **Substantive/off-topic:** stay on STEP_2, re-invite with LLM

### collection.py (~120 lines)
Cat5 collection phase handling. Two sub-concerns:

**Photo validation (`resolve_collection_photo`):**
- Check if photo_id matches correct item
- Wrong pick: increment counter, exit on 2nd consecutive wrong, return "try again" on 1st
- Correct pick: record photo, transition `collection_phase` to "detail"

**Detail phase (`resolve_detail_phase`):**
- Handle child response to detail question
- Increment `detail_exchange_count`, record detail
- Respect `stay_on_step` with tier-dependent exchange limit (T0=1, T1=2, T2=3)
- Set `round_advance_pending` when phase complete

Also contains: `is_correct_collection_photo`, `get_item_label`, `record_correct_collection_pick`, `has_completion_language`.

### rounds.py (~180 lines)
Round step generation (STEP_3_ROUND_* and STEP_3_COLLECT_*).

**Deferred advance:** When `round_advance_pending` is true and no child input, advance state and generate for new round.

**Main generation path:** Call `generate_with_retry`, then apply 3 guardrails in order:
1. **Premature completion language:** If LLM says "final" but items remain, regenerate with corrective hint
2. **Force stay_on_step:** When entering Phase B detail, force `stay_on_step = True`
3. **Override stay_on_step:** When collection is complete, force `stay_on_step = False`

Then handle stay vs. advance, including Cat5 immediate-advance vs. Cat1 deferred-advance.

### synthesis.py (~150 lines)
STEP_4_SYNTHESIS handling. Four phases:

- **Invite:** Deterministic template, early return
- **Evaluate:** Classify intent → confirm/decline advances, substantive → check story quality → advance or enter improve
- **Improve:** Re-evaluate combined story, advance regardless
- **Generate:** Final synthesis generation

Contains: `is_synthesis_confirm`, `synthesis_result`.

### debug.py (~120 lines)
Debug payload construction for development tooling.

- `build_debug_payload(state, gen_debug, ...)` — assembles full debug dict
- `build_step_flow(state)` — step transition visualization
- `build_phase_timeline(state)` — phase timeline for Cat1
- `phase_timeline_cat5_collection(state)` — Cat5 collection timeline
- `phase_timeline_cat5_synthesis(state)` — Cat5 synthesis timeline

### directive.py (~150 lines)
Turn Director path — the feature-flagged bypass that replaces classic step routing.

- `resolve_turn_with_directive(state, turn_input, script_agent)` — full turn resolution using Turn Director's intent + plan
- `get_turn_directive(state, turn_input, script_agent)` — calls TurnDirector for structured directive

When `settings.turn_director_enabled` is true, `core.py` delegates here instead of classic step dispatch.

### core.py (~100 lines)
The slim dispatcher. Contains:

**`resolve_turn(state, turn_input, script_agent) -> TurnResult`** — the public entry point:
1. Silence counting + graceful exit (consecutive_silence >= 2)
2. Record child input in conversation history
3. Turn Director bypass (feature-flagged) → delegates to `directive.resolve_turn_with_directive`
4. Intent classification (code-level override for confirm/decline, then LLM via `generation.classify_intent`)
5. Step-specific dispatch → calls into invitation/collection/rounds/synthesis modules
6. Auto-advance steps (celebrate, closing) — handled inline since they're simple
7. Hook step and generic interactive fallback

Also contains:
- `_handle_silence(state, turn_input, has_child_input)` — silence counting logic
- `resolve_hook(state, turn_input, script_agent, has_child_input)` — STEP_1_HOOK handling
- `resolve_auto_advance(state, turn_input, script_agent)` — celebrate/closing steps
- `resolve_generic_step(state, turn_input, script_agent, has_child_input)` — fallback

### __init__.py
```python
from turn_handling.core import resolve_turn
from turn_handling.types import GenerationDebugInfo, TurnInput, TurnResult
from turn_handling.generation import get_retry_stats
```

## 5. Module Dependency Graph

```
types.py          (leaf — schemas only)
    ↑
helpers.py        (leaf — depends on types)
    ↑
generation.py     (depends on types, helpers)
    ↑
┌───┼───┬───┬───┐
│   │   │   │   │
invitation  collection  rounds  synthesis  directive  (each depends on types, helpers, generation)
│   │   │   │   │
└───┼───┴───┴───┘
    ↑
debug.py          (depends on types, helpers)
    ↑
core.py           (depends on all modules above)
```

**No circular dependencies.** `types` and `helpers` are leaves. Step handlers depend on the same shared base but never on each other.

## 6. Cross-Module State Access

All handlers receive `state`, `turn_input`, and `script_agent` as explicit function arguments. No module-level singletons or shared mutable state. This keeps dependencies visible — you can see exactly what each handler has access to.

The `_debug()` nested function (currently defined inside `resolve_turn` to capture closure variables) is replaced: each handler returns debug info in `TurnResult`, and `core.py` calls `debug.build_debug_payload()` once at the end.

## 7. Import Changes

### server.py
```python
# Before
from turn_handler import TurnInput, resolve_turn

# After
from turn_handling import TurnInput, resolve_turn
```

### Tests
Same pattern — `from turn_handler import ...` → `from turn_handling import ...`. No test logic changes; only import paths.

## 8. What Does NOT Change

| Item | Reason |
|------|--------|
| `SessionStateModel` schema | State shape is unchanged; handlers just mutate it |
| `ScriptAgent` interface | Handlers call the same `generate_turn` / `retry_speaker_turn` methods |
| `server.py` endpoint logic | Only import paths change |
| `state_machine.py` | Step transition logic stays where it is |
| `agents/` directory | No agent changes |
| Frontend | Backend API contract is identical |
| Behavioral semantics | Pure refactoring — same branches, same order, same outputs |

## 9. Test Coverage Assessment

Existing tests (97 functions across 5 files) cover ~45-50% of `resolve_turn` code paths.

**Covered:** Invitation routing, Cat5 correct photo + detail phase, synthesis phases, consecutive silence exit, `_generate_with_retry` retry logic, debug payload builders, intent classification.

**Gaps:** Turn Director path (0%), wrong photo handling (0%), post-generation guardrails (0%), Cat1 round advancement (0%), celebrate/closing auto-advance (0%), synthesis off_topic/decline (0%).

**Mitigation:** This is a pure refactoring — untested code paths move verbatim with no logic changes. Existing tests catch import breakage and major regressions in covered paths. After refactoring, the modular structure makes it easier to add the missing tests per-module.

**Internal imports to update in tests:** `_generate_with_retry`, `_maybe_record_generated_name`, `_record_collection_detail`, `_DIRECTIVE_RE`, `_INVITATIONAL_PREFIX_RE`, `_ITEM_SUGGESTION_RE`.

## 10. Verification

1. **Unit tests pass:** `uv run pytest tests/test_turn_handler.py tests/test_turn_flow.py tests/test_turn_plan.py` (after import path updates)
2. **Full test suite:** `uv run pytest` — no regressions anywhere
3. **Type checking:** `uv run mypy backend/turn_handling/` — clean
4. **Lint:** `uv run ruff check backend/turn_handling/` — clean
5. **Manual smoke test:** Start a Cat1 session (mood_changer_dog), play through invitation → 2 rounds → closing. Start a Cat5 session (polka_dot_patrol), play through collection → detail → synthesis. Verify identical behavior.
6. **Debug validation:** Set a breakpoint in `collection.py:resolve_collection_photo` — confirm it hits on Cat5 photo submission. Set a breakpoint in `invitation.py:resolve_invitation` — confirm it hits on invitation step.
