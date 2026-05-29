# Pilot Flow Robustness + Asset Regeneration + Crown UI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the three pilot activities (frame-sync + live-LLM guardrails), regenerate their flat-Nordic art via Codex, and add a Digital-Crown scroll picker — without changing the live-LLM experience.

**Architecture:** A single backend turn-finalization stage (`finalize_turn`) derives the screen frame and validates the spoken line from one resolved state, so dialogue and frame cannot desync; the frontend mirrors an explicit step→beat table; assets are raster-regenerated via Codex built-in imagegen; one reusable `CrownPicker` drives all device navigation.

**Tech Stack:** Python 3.12 / FastAPI / Pydantic v2 (backend; `uv` tooling, pytest, asyncio_mode=auto, pythonpath=backend); React JSX / Vite / vitest + @testing-library/react (frontend); Codex built-in imagegen (assets).

**Design source:** `docs/plans/2026-05-29-pilot-flow-robustness-and-asset-regen.md` (the approved spec). This plan implements that spec, stream by stream.

---

## Tech & Conventions (read first)

- Backend tests/tools run from the **worktree root** via `uv run` (e.g. `uv run pytest backend/tests/<file>.py -q`); ruff is run from `backend/`. Python: no `__future__`, imports at top, type hints, line length 120, Google docstrings, no `noqa`/`type: ignore`.
- Frontend tests run from `frontend/` via `npm run test -- <name>`; lint via `npm run lint`.
- Commit at every task with conventional-commit messages. **Never attribute Claude/AI** as author or co-author.
- After each stream, run `code-reviewer` + `code-simplifier` before declaring it done (project rule); update `HANDOFF.md`.
- **Live-API verification:** source the main-repo `backend/.env` + `backend/.elaborate-baton-480304-r8-a8a39bcb34f1.json` (see the goal file's Live Provider Credential Rule) and run `scripts/run_activity_text_smoke.py --timeout 120` against the **live provider** as part of verification — do not rely on mocked unit tests alone. Never print or commit secret values.

## File Structure

- **New backend module:** `backend/turn_handling/finalize.py` — `finalize_turn`, `derive_frame`, `beat_for_step`, `STEP_BEAT_TABLE`, validators `_violates_contract`/`_violates_flow`. Single responsibility: produce the `(safe line, matching frame)` pair from one resolved state.
- **Backend modified:** `turn_handling/{core,directive,rounds,helpers,generation}.py` (route through finalize; broaden completion regex; exhaustion fallback), `agents/script_agent.py` (sanitize `example_ai_line`), `schemas/visual_composition.py` (add `beat` to `ScreenFrame`).
- **Frontend new:** `src/activityGame/CrownPicker.jsx` (+ CSS in `src/index.css`). **Frontend modified:** `activityAssets.js` (explicit step→beat table), `ActivityGameApp.jsx` (crown wiring across 3 surfaces).
- **Assets:** `public/activity-assets/<pilot>/(items/)` (regenerated PNGs), `public/activity-assets/activity-assets.manifest.json` (celebrate/closing beats; rebuilt), `scripts/build_activity_screen_assets.py` (drop stale pilot `ITEM_CROPS`).
- **Tests:** new `backend/tests/test_finalize_frame.py`, `test_finalize_frame_sync.py`, `test_finalize_validators.py`; updated `tests/test_activity_text_game_asset_contract.py`, `frontend/tests/activityAssets.test.js`, new `frontend/tests/CrownPicker.test.jsx`, updated `frontend/tests/ActivityGameApp.test.jsx`.

## Execution Order & Integration Notes

1. **Order: Stream 1+2 (backend) → Stream 3 (assets) → Stream 4 (crown).** Stream 4 is frontend-isolated and may overlap Stream 3.
2. **`_required_beat_ids` is edited exactly once** — in Stream 1+2 **Task 3** (representative-gated: the 3 pilots require `celebrate`/`closing`; the other 9 keep `recap`). Stream 3 **Task 4** must NOT redefine it (its all-categories form is wrong); Stream 3 Task 4 only removes stale `ITEM_CROPS` + rebuilds/validates.
3. Stream 1+2 Task 3 creates **placeholder** `celebrate.png`/`closing.png` (copies of `recap.png`) so Stream-1 tests stay green; Stream 3 replaces them with real art.
4. `scripts/build_activity_screen_assets.py` (Stream 3) rewrites the manifest — confirm it **preserves** the `celebrate`/`closing` beats added in Stream 1+2 Task 3; if the builder drops unknown beats, re-add them post-build (the asset-contract test guards this).
5. Pre-existing unrelated red to ignore: `test_activity_text_game_asset_contract.py::test_representative_activity_layout_contracts_match_touchless_goal` asserts synthesis `carousel` vs manifest `picker` — out of scope.

---

## Stream 1+2 — Backend turn-finalization (frame-sync F + guardrails A/B/C/D)

> Tasks 1–5 are Stream 1 (frame-sync); Tasks 6–10 are Stream 2 (guardrails, ending by wiring `finalize_turn` into the live paths so validators run).

### Task 1: Create `backend/turn_handling/finalize.py` with the step→beat table, `derive_frame`, and a pass-through `finalize_turn`

**Files:**
- Create: `backend/turn_handling/finalize.py`
- Create: `backend/tests/test_finalize_frame.py`
- Test: `backend/tests/test_finalize_frame.py`

This task establishes the shared module and the explicit step→beat lookup table that is the contract shared with the frontend (`activityAssets.js`). `finalize_turn` starts as a thin wrapper that attaches the derived frame to a `TurnResponse`; Stream 2 validators are layered in later tasks. The `beat` value lives on `ScreenFrame` so it serializes via the existing `screen_frame.model_dump()` path in `server.py:1073` and can be asserted in tests and read by the frontend.

- [ ] **Step: Add an optional `beat` field to `ScreenFrame`** so `derive_frame` can stamp it and it survives `model_dump()`. In `backend/schemas/visual_composition.py`, after the `widget_label` field (line 16), add:

```python
    beat: str | None = Field(default=None, description="Asset beat id matching the line spoken now")
```

- [ ] **Step: Write the failing test** for the step→beat table and `derive_frame`. Create `backend/tests/test_finalize_frame.py`:

```python
"""Unit tests for the step->beat table and derive_frame in finalize."""

from recipe_loader import load_instruction_recipe, recipe_to_session_state
from turn_handling.finalize import STEP_BEAT_TABLE, beat_for_step, derive_frame


def _state(activity_type: str, filename: str):
    recipe = load_instruction_recipe(activity_type)
    return recipe_to_session_state(recipe, "finalize-session", "T1", filename)


def test_beat_for_step_covers_all_pilot_steps() -> None:
    assert beat_for_step("STEP_1_HOOK", 0) == "intro"
    assert beat_for_step("STEP_2_RULES", 0) == "rules"
    assert beat_for_step("STEP_2_MISSION", 0) == "rules"
    assert beat_for_step("STEP_2_SETUP", 0) == "rules"
    assert beat_for_step("STEP_3_ROUND_2", 2) == "round_2"
    assert beat_for_step("STEP_3_COLLECT_1", 1) == "round_1"
    assert beat_for_step("STEP_3_BUILD_3", 3) == "round_3"
    assert beat_for_step("STEP_4_SYNTHESIS", 0) == "synthesis"
    # Distinct celebrate/closing beats — no collapse to a single "recap".
    assert beat_for_step("STEP_4_CELEBRATE", 0) == "celebrate"
    assert beat_for_step("STEP_5_CELEBRATE", 0) == "celebrate"
    assert beat_for_step("STEP_5_CLOSING", 0) == "closing"
    assert beat_for_step("STEP_6_CLOSING", 0) == "closing"
    assert beat_for_step("EARLY_EXIT", 0) == "closing"


def test_step_beat_table_has_no_celebrate_closing_collision() -> None:
    # The fixed (non-round) entries must map celebrate and closing distinctly.
    assert STEP_BEAT_TABLE["STEP_4_CELEBRATE"] == "celebrate"
    assert STEP_BEAT_TABLE["STEP_5_CELEBRATE"] == "celebrate"
    assert STEP_BEAT_TABLE["STEP_5_CLOSING"] == "closing"
    assert STEP_BEAT_TABLE["STEP_6_CLOSING"] == "closing"
    assert STEP_BEAT_TABLE["STEP_4_CELEBRATE"] != STEP_BEAT_TABLE["STEP_5_CLOSING"]


def test_derive_frame_stamps_beat_matching_current_step() -> None:
    state = _state("activity_career_decision_role_play", "career_decision_role_play")
    state.current_step = "STEP_3_ROUND_2"
    state.current_round = 2

    frame = derive_frame(state, "advance")

    assert frame.beat == "round_2"
    # derive_frame still returns a real ScreenFrame for the current step.
    assert frame.widget


def test_derive_frame_celebrate_uses_celebrate_beat_not_closing() -> None:
    state = _state("activity_phoneme_treasure_hunt", "phoneme_treasure_hunt")
    state.current_step = "STEP_5_CELEBRATE"
    state.current_round = 3

    frame = derive_frame(state, "advance")

    assert frame.beat == "celebrate"
```

- [ ] **Step: Run it, expect FAIL** with `uv run pytest tests/test_finalize_frame.py -q` from `backend/` (run as the repo runs it: `cd` not required by the harness, but the canonical command is `uv run pytest backend/tests/test_finalize_frame.py -q` from the worktree root). Expected: `ModuleNotFoundError: No module named 'turn_handling.finalize'`.

- [ ] **Step: Minimal implementation** — create `backend/turn_handling/finalize.py`:

```python
"""Single turn-finalization stage: derive the frame for the line spoken now.

This module owns the contract between the resolved session state and the
on-screen asset beat. ``finalize_turn`` is invoked on every path that builds a
``TurnResponse`` so the spoken line and its screen frame are derived from the
same post-advance step and cannot desync (spec §3-§4). Stream 2 guardrail
validators are layered into ``finalize_turn`` in later tasks.
"""

try:
    from ..schemas import ScreenFrame
    from ..schemas.session_state import SessionStateModel
    from ..schemas.turn_response import TurnResponse
    from ..state_machine import EARLY_EXIT
except ImportError:
    from schemas import ScreenFrame
    from schemas.session_state import SessionStateModel
    from schemas.turn_response import TurnResponse
    from state_machine import EARLY_EXIT

from .helpers import _get_screen_frame

# Explicit step -> beat lookup table. Shared contract with the frontend
# (frontend/src/activityGame/activityAssets.js beatForStep). Non-round steps
# only; round/collect/build steps derive ``round_N`` from the round number so
# both surfaces agree on the asset for the step whose line is spoken now.
STEP_BEAT_TABLE: dict[str, str] = {
    "STEP_1_HOOK": "intro",
    "STEP_2_RULES": "rules",
    "STEP_2_MISSION": "rules",
    "STEP_2_SETUP": "rules",
    "STEP_4_SYNTHESIS": "synthesis",
    "STEP_4_CELEBRATE": "celebrate",
    "STEP_5_CELEBRATE": "celebrate",
    "STEP_5_CLOSING": "closing",
    "STEP_6_CLOSING": "closing",
    EARLY_EXIT: "closing",
}

_ROUND_PREFIXES = ("STEP_3_ROUND_", "STEP_3_COLLECT_", "STEP_3_BUILD_")


def beat_for_step(step: str, current_round: int) -> str:
    """Return the asset beat id for the step whose line is spoken now.

    Args:
        step: Current state-machine step (post-advance — the same step the
            frontend reads from ``sessionState.current_step``).
        current_round: Active round number, used as a fallback when the step
            string carries no round suffix.

    Returns:
        The beat id (e.g. ``intro``, ``round_2``, ``celebrate``, ``closing``).
    """
    for prefix in _ROUND_PREFIXES:
        if step.startswith(prefix):
            try:
                round_number = int(step[len(prefix):])
            except ValueError:
                round_number = current_round or 1
            return f"round_{round_number}"
    return STEP_BEAT_TABLE.get(step, "intro")


def derive_frame(state: SessionStateModel, action: str) -> ScreenFrame:
    """Derive the screen frame for the current (post-advance) step.

    The frame represents the step whose line is being spoken now — not a
    preview of the next step. ``action`` is the resolved directive action
    (advance/stay/need_help/redirect/exit) kept for future action-aware frame
    selection; today the frame is keyed purely on the resolved step.
    """
    frame = _get_screen_frame(state)
    frame.beat = beat_for_step(state.current_step, state.current_round)
    return frame


def finalize_turn(
    state: SessionStateModel,
    turn_response: TurnResponse,
    action: str,
) -> tuple[TurnResponse, ScreenFrame]:
    """Return the (safe line, matching frame) pair from one resolved state.

    Stream 1: derive the frame from the resolved step so dialogue and frame
    cannot desync. Stream 2 validators (contract/flow/wording/exhaustion) are
    added to this function in later tasks.
    """
    screen_frame = derive_frame(state, action)
    return turn_response, screen_frame
```

- [ ] **Step: Run it, expect PASS** with `uv run pytest backend/tests/test_finalize_frame.py -q` from the worktree root.

- [ ] **Step: Run ruff** with `uv run ruff check turn_handling/finalize.py schemas/visual_composition.py && uv run ruff format turn_handling/finalize.py` from `backend/`.

- [ ] **Step: Commit** with message `feat(finalize): add step-beat table and frame derivation`.

---

### Task 2 (1a): Route every TurnResponse-producing path in `core.py` and `directive.py` through `finalize_turn`

**Files:**
- Modify: `backend/turn_handling/core.py:127-373` (8 `_get_screen_frame` call sites)
- Modify: `backend/turn_handling/directive.py:1024-1231` (the 4 `_get_screen_frame` calls + the 2 ad-hoc pre-advance snapshots at `1128-1142` and `1169-1187`)
- Modify: `backend/turn_handling/rounds.py:63-233` and `backend/turn_handling/helpers.py:191-208` (`_ended_result`) for the remaining callers
- Test: `backend/tests/test_finalize_frame.py`

Replace each `screen_frame=_get_screen_frame(state)` / pre-advance snapshot with `derive_frame(state, <action>)` (or build the `TurnResult` via `finalize_turn`) so the frame is always derived from the resolved post-advance step. After this task, no `TurnResult.screen_frame` is computed before `_advance_state`.

- [ ] **Step: Write the failing test** that asserts no residual pre-advance `_get_screen_frame` snapshots remain on the directive path and that the directive path returns a beat-stamped frame. Append to `backend/tests/test_finalize_frame.py`:

```python
import inspect

from turn_handling import core as core_module
from turn_handling import directive as directive_module


def test_no_residual_get_screen_frame_callers_in_result_paths() -> None:
    # 1a: every TurnResult must derive its frame via finalize/derive_frame,
    # so the scattered _get_screen_frame(state) calls are gone from the
    # result-building modules.
    core_src = inspect.getsource(core_module)
    directive_src = inspect.getsource(directive_module)
    assert "_get_screen_frame(state)" not in core_src
    assert "_get_screen_frame(state)" not in directive_src
    # The two ad-hoc pre-advance snapshots are removed.
    assert "celebrate_screen_frame" not in directive_src
    assert "pre_advance_frame" not in directive_src
```

- [ ] **Step: Run it, expect FAIL** with `uv run pytest backend/tests/test_finalize_frame.py::test_no_residual_get_screen_frame_callers_in_result_paths -q`. Expected: `AssertionError` on `"_get_screen_frame(state)" not in core_src`.

- [ ] **Step: Minimal implementation — `core.py` imports.** Replace the `_get_screen_frame` import in `backend/turn_handling/core.py` (line 42 in the `from .helpers import (...)` block) — remove `_get_screen_frame` from that import list and add a new import after the helpers import block (after line 45):

```python
from .finalize import derive_frame
```

- [ ] **Step: Minimal implementation — `core.py` call sites.** Replace each `screen_frame=_get_screen_frame(state),` in `core.py` with the action-aware derivation. The silence-exit and wrong-pick exits (lines 130, 171) use `"exit"`; the interactive paths (272, 287, 301, 336) use `state.last_directive_action or "stay"`; the snapshot lines at 308 and 346 already capture the frame *before* advance — change those two so the frame is captured *after* `_advance_state` instead. Concretely:

  - Lines 130, 171: `screen_frame=derive_frame(state, "exit"),`
  - Lines 272, 287, 301, 336: `screen_frame=derive_frame(state, state.last_directive_action or "stay"),`
  - Line 308 region (generic interactive advance): delete `screen_frame = _get_screen_frame(state)` before `_advance_state(state)` (line 310) and set `screen_frame=derive_frame(state, "advance")` in the returned `TurnResult` (computed after the advance).
  - Line 346 region (Cat5 celebrate-after-synthesis): delete `screen_frame = _get_screen_frame(state)` (line 346); for the closing branch return `screen_frame=derive_frame(state, "advance")` and for the non-closing tail return `screen_frame=derive_frame(state, "advance")`, both computed after `_advance_state`.

  Example, the generic interactive advance return (replacing lines 307-321):

```python
        response_type = _get_response_type(state.current_step)
        _append_ai_turn(state, turn_response.dialogue)
        _advance_state(state)
        state.turn_count += 1
        if is_terminal(state.current_step):
            state.status = "completed"
        return TurnResult(
            turn_response=turn_response,
            screen_frame=derive_frame(state, "advance"),
            auto_advance=not is_terminal(state.current_step) and not step_needs_user_input(state.current_step),
            response_type=response_type,
            error_exit=state.status == "error",
            debug=_debug(gen_debug, turn_response),
        )
```

  And the Cat5 celebrate-after-synthesis tail (replacing lines 344-373):

```python
    turn_response, gen_debug = await _generate_with_retry(script_agent, state)
    response_type = _get_response_type(state.current_step)
    _append_ai_turn(state, turn_response.dialogue)
    state.turn_count += 1

    if _is_closing_step(state.current_step):
        state.status = "completed"
        _advance_state(state)
        return TurnResult(
            turn_response=turn_response,
            screen_frame=derive_frame(state, "advance"),
            auto_advance=False,
            response_type=response_type,
            error_exit=state.status == "error",
            debug=_debug(gen_debug, turn_response),
        )

    _advance_state(state)
    if is_terminal(state.current_step):
        state.status = "completed"

    return TurnResult(
        turn_response=turn_response,
        screen_frame=derive_frame(state, "advance"),
        auto_advance=not is_terminal(state.current_step) and not step_needs_user_input(state.current_step),
        response_type=response_type,
        error_exit=state.status == "error",
        debug=_debug(gen_debug, turn_response),
    )
```

  Note: this makes the celebrate/closing frame match the post-advance step. The closing branch advances to ENDED before returning, so `derive_frame` would read ENDED. To keep the frame matching the line spoken (the closing line, not ENDED), capture the closing frame BEFORE the terminal advance by computing `screen_frame=derive_frame(state, "advance")` *before* `_advance_state(state)` in the closing branch only:

```python
    if _is_closing_step(state.current_step):
        state.status = "completed"
        screen_frame = derive_frame(state, "advance")
        _advance_state(state)
        return TurnResult(
            turn_response=turn_response,
            screen_frame=screen_frame,
            auto_advance=False,
            response_type=response_type,
            error_exit=state.status == "error",
            debug=_debug(gen_debug, turn_response),
        )
```

- [ ] **Step: Minimal implementation — `directive.py` imports.** In `backend/turn_handling/directive.py`, remove `_get_screen_frame` from the `from .helpers import (...)` block (line 49) and add after that import block (after line 56):

```python
from .finalize import derive_frame
```

- [ ] **Step: Minimal implementation — `directive.py` celebrate branch (lines 1116-1147).** The celebrate branch currently snapshots `celebrate_screen_frame = _get_screen_frame(state)` BEFORE `_advance_state`. Because celebrate must keep its own beat (`celebrate`, not `closing`), derive the frame from the celebrate step *before* advancing:

```python
            turn_response.screen_widget = "achievement_image"
            turn_response.sfx_cue = "badge_awarded"
            _append_ai_turn(state, turn_response.dialogue)
            state.turn_count += 1

            # Frame must match the celebrate line spoken now, not the closing
            # step we advance into below. Derive on the celebrate step first.
            celebrate_frame = derive_frame(state, "advance")
            _advance_state(state)
            return TurnResult(
                turn_response=turn_response,
                screen_frame=celebrate_frame,
                auto_advance=True,
                response_type="celebrate",
                error_exit=False,
                debug=_debug(None, turn_response),
            )
```

- [ ] **Step: Minimal implementation — `directive.py` closing/terminal advance (lines 1162-1192).** Remove `pre_advance_frame = _get_screen_frame(state) if is_closing else None` (line 1171). Derive the closing frame before the terminal advance, and the non-terminal advance frame after:

```python
        if is_closing:
            if state.template_type == "cat5":
                turn_response.screen_widget = "concept_reveal"
            else:
                turn_response.screen_widget = "achievement_image"

        # Closing frame must match the closing line — derive before the advance
        # to ENDED (which has no matching widget).
        closing_frame = derive_frame(state, "advance") if is_closing else None

        _advance_state(state)

        if state.current_step == "STEP_4_SYNTHESIS" and state.synthesis_phase == "invite":
            state.synthesis_phase = "evaluate"
            state.synthesis_prompt_count = 1

        if is_terminal(state.current_step):
            state.status = "completed"
            return TurnResult(
                turn_response=turn_response,
                screen_frame=closing_frame or derive_frame(state, "advance"),
                auto_advance=False,
                response_type="closing",
                error_exit=False,
                debug=_debug(None, turn_response),
            )

        auto_advance = _should_auto_advance(state)
        response_type = _get_response_type(state.current_step)
```

- [ ] **Step: Minimal implementation — `directive.py` final return (line 1226).** Replace `screen_frame=_get_screen_frame(state),` with `screen_frame=derive_frame(state, action),`.

- [ ] **Step: Minimal implementation — `rounds.py` and `helpers.py` callers.** In `backend/turn_handling/rounds.py`, remove `_get_screen_frame` from the `from .helpers import (...)` block (line 31) and add `from .finalize import derive_frame` after the helpers import (after line 39); replace the three `screen_frame=_get_screen_frame(state),` returns (lines ~70, ~116, ~228) with `screen_frame=derive_frame(state, "advance" if not turn_response.stay_on_step else "stay"),` for the main path (line 228) and `screen_frame=derive_frame(state, "stay"),` for the photo-prompt path (line 70) and `screen_frame=derive_frame(state, "advance"),` for the deferred-advance path (line 116). In `backend/turn_handling/helpers.py`, change `_ended_result` (line 204) to `screen_frame=derive_frame(state, "advance"),` and add `from .finalize import derive_frame` — but `finalize` imports `_get_screen_frame` from `helpers`, so to avoid a circular import keep `_ended_result` using the local `_get_screen_frame(state)` and instead stamp the beat inline:

```python
    frame = _get_screen_frame(state)
    frame.beat = "closing"
    return TurnResult(
        turn_response=TurnResponse(...),
        screen_frame=frame,
        ...
    )
```

(Keep `_get_screen_frame` defined/imported in `helpers.py` since `finalize.derive_frame` depends on it — the test in this task only forbids `_get_screen_frame(state)` in `core.py`/`directive.py`.)

- [ ] **Step: Run it, expect PASS** with `uv run pytest backend/tests/test_finalize_frame.py backend/tests/test_activity_text_game_turns.py backend/tests/test_generation_fallback.py -q` from the worktree root.

- [ ] **Step: Run ruff** with `uv run ruff check turn_handling/ && uv run ruff format turn_handling/` from `backend/`.

- [ ] **Step: Commit** with message `refactor(finalize): route turn paths through derive_frame`.

---

### Task 3 (1c): Add `celebrate`/`closing` beats to the manifest for the 3 pilots, fix `_sync_round_from_step`, and update the asset contract test

**Files:**
- Modify: `backend/turn_handling/helpers.py:93-102` (`_sync_round_from_step`)
- Modify: `frontend/public/activity-assets/activity-assets.manifest.json` (add `celebrate`+`closing` beats to the 3 pilots; rename pilot `recap`→removed in favor of explicit beats)
- Modify: `tests/test_activity_text_game_asset_contract.py:32-39` (`_required_beat_ids`)
- Test: `backend/tests/test_activity_text_game_turns.py`, `tests/test_activity_text_game_asset_contract.py`

The pilots gain distinct `celebrate` and `closing` beats (replacing the single `recap`). The 3 pilots are the only ones with `layout` metadata, so the contract test must require the new beats for the representative scope only. `_sync_round_from_step` must not leave `current_round` stale on non-round steps so round-keyed lookups don't go stale on CELEBRATE/CLOSING.

- [ ] **Step: Write the failing test** for `_sync_round_from_step` on non-round steps. Append to `backend/tests/test_activity_text_game_turns.py`:

```python
from turn_handling.helpers import _sync_round_from_step


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
```

- [ ] **Step: Run it, expect FAIL** with `uv run pytest backend/tests/test_activity_text_game_turns.py::test_sync_round_clears_stale_round_on_celebrate_step -q`. Expected: `AssertionError: assert 3 == 0`.

- [ ] **Step: Minimal implementation — `_sync_round_from_step`.** Replace `backend/turn_handling/helpers.py:93-102` with:

```python
def _sync_round_from_step(state: SessionStateModel) -> None:
    """Keep current_round aligned with the active step.

    Round/collect/build steps set ``current_round`` from the step suffix.
    Non-round steps (hook, rules, synthesis, celebrate, closing) clear it to 0
    so round-keyed frame lookups do not go stale (spec §4 cause 2).
    """
    step = state.current_step
    for prefix in ("STEP_3_ROUND_", "STEP_3_COLLECT_", "STEP_3_BUILD_"):
        if step.startswith(prefix):
            try:
                state.current_round = int(step[len(prefix):])
            except ValueError:
                pass
            return
    state.current_round = 0
```

- [ ] **Step: Run it, expect PASS** with `uv run pytest backend/tests/test_activity_text_game_turns.py -q`.

- [ ] **Step: Update the asset contract test** `tests/test_activity_text_game_asset_contract.py`. Replace `_required_beat_ids` (lines 32-39) so the 3 representative pilots require the new `celebrate`/`closing` beats while the other 9 keep `recap`:

```python
def _required_beat_ids(activity_id: str, category: str) -> list[str]:
    recipe = get_demo_recipe(activity_id)
    assert recipe is not None

    round_ids = [f"round_{index}" for index in range(1, recipe.metadata.round_count + 1)]
    if activity_id in REPRESENTATIVE_ACTIVITY_IDS:
        tail = ["synthesis", "celebrate", "closing"] if category == "category_5" else ["celebrate", "closing"]
        return ["intro", "rules", *round_ids, *tail]
    if category == "category_5":
        return ["intro", "rules", *round_ids, "synthesis", "recap"]
    return ["intro", "rules", *round_ids, "recap"]
```

- [ ] **Step: Update the manifest.** In `frontend/public/activity-assets/activity-assets.manifest.json`, for the three pilots (`activity_phoneme_treasure_hunt`, `activity_career_decision_role_play`, `activity_guided_drawing`) replace the single `recap` beat with two beats `celebrate` (usage `celebration`) and `closing` (usage `closing`), each carrying a `single`/`none` layout block identical in shape to the existing pilot `recap` layout but pointing at new `celebrate.png`/`closing.png` srcs. Example for `activity_career_decision_role_play` — replace the `recap` beat object (lines 408-426) with:

```json
        {
          "id": "celebrate",
          "src": "/activity-assets/activity_career_decision_role_play/celebrate.png",
          "usage": "celebration",
          "layout": {
            "mode": "single",
            "selection": "none",
            "safeArea": { "canvas": 480, "safe": 380, "center": 300 },
            "background": { "src": "/activity-assets/activity_career_decision_role_play/celebrate.png", "fit": "cover" },
            "items": []
          }
        },
        {
          "id": "closing",
          "src": "/activity-assets/activity_career_decision_role_play/closing.png",
          "usage": "closing",
          "layout": {
            "mode": "single",
            "selection": "none",
            "safeArea": { "canvas": 480, "safe": 380, "center": 300 },
            "background": { "src": "/activity-assets/activity_career_decision_role_play/closing.png", "fit": "cover" },
            "items": []
          }
        }
```

  Apply the same two-beat replacement to `activity_guided_drawing` and `activity_phoneme_treasure_hunt` (using each pilot's own asset path). NOTE: the actual `celebrate.png`/`closing.png` raster files are produced in Stream 3; until then the asset-existence assertions in `test_activity_text_game_asset_contract.py` and `activityAssets.test.js` will fail on the missing files. Add a step here to create placeholder copies so Stream 1 stays green: `cp` each pilot's existing `recap.png` to `celebrate.png` and `closing.png`.

- [ ] **Step: Create placeholder raster files** so file-existence assertions pass before Stream 3:

```bash
for d in activity_phoneme_treasure_hunt activity_career_decision_role_play activity_guided_drawing; do
  cp "frontend/public/activity-assets/$d/recap.png" "frontend/public/activity-assets/$d/celebrate.png"
  cp "frontend/public/activity-assets/$d/recap.png" "frontend/public/activity-assets/$d/closing.png"
done
```

(run from the worktree root)

- [ ] **Step: Run it, expect PASS** with `uv run pytest tests/test_activity_text_game_asset_contract.py::test_activity_asset_manifest_matches_runtime_recipe_beats -q` from the worktree root. (The pre-existing `carousel`-vs-`picker` failure in `test_representative_activity_layout_contracts_match_touchless_goal` is unrelated to Streams 1-2 and is left as-is.)

- [ ] **Step: Run ruff** with `uv run ruff check turn_handling/helpers.py && uv run ruff format turn_handling/helpers.py` from `backend/`.

- [ ] **Step: Commit** with message `feat(assets): add celebrate and closing beats`.

---

### Task 4 (1b): Replace lossy `beatIdFromSessionState()` with the explicit step→beat table (frontend contract)

**Files:**
- Modify: `frontend/src/activityGame/activityAssets.js:81-95`
- Test: `frontend/tests/activityAssets.test.js`

The frontend mapping currently collapses `CELEBRATE` and `CLOSING` to a single `'recap'`. Replace it with an explicit lookup mirroring `STEP_BEAT_TABLE` in `finalize.py` so both surfaces agree on the beat for the step whose line is spoken now.

- [ ] **Step: Write the failing test.** Replace the `'maps session steps to variable beat ids'` test (`frontend/tests/activityAssets.test.js:262-277`) so celebrate/closing map distinctly, and add the new pilot beats to `STANDARD_BEATS`/`CAT5_BEATS` used by `'maps every activity to an icon and beat assets'` only for representative pilots:

```javascript
  it('maps session steps to distinct beat ids without collapsing celebrate and closing', () => {
    expect(beatIdFromSessionState({ current_step: 'STEP_1_HOOK' })).toBe('intro');
    expect(beatIdFromSessionState({ current_step: 'STEP_2_RULES' })).toBe('rules');
    expect(beatIdFromSessionState({ current_step: 'STEP_2_MISSION' })).toBe('rules');
    expect(beatIdFromSessionState({ current_step: 'STEP_2_SETUP' })).toBe('rules');
    expect(beatIdFromSessionState({ current_step: 'STEP_3_ROUND_3', current_round: 3 })).toBe('round_3');
    expect(beatIdFromSessionState({ current_step: 'STEP_3_COLLECT_1', current_round: 1 })).toBe('round_1');
    expect(beatIdFromSessionState({ current_step: 'STEP_3_BUILD_2', current_round: 2 })).toBe('round_2');
    expect(beatIdFromSessionState({ current_step: 'STEP_4_SYNTHESIS' })).toBe('synthesis');
    expect(beatIdFromSessionState({ current_step: 'STEP_4_CELEBRATE' })).toBe('celebrate');
    expect(beatIdFromSessionState({ current_step: 'STEP_5_CELEBRATE' })).toBe('celebrate');
    expect(beatIdFromSessionState({ current_step: 'STEP_5_CLOSING' })).toBe('closing');
    expect(beatIdFromSessionState({ current_step: 'STEP_6_CLOSING' })).toBe('closing');
    expect(beatIdFromSessionState({ current_step: 'EARLY_EXIT' })).toBe('closing');
  });

  it('prefers the backend screen_frame.beat when present', () => {
    expect(beatIdFromSessionState({ current_step: 'STEP_5_CELEBRATE' }, { beat: 'closing' })).toBe('closing');
  });
```

  Also update the beat lists near the top (lines 16-17) so the representative-pilot assertions in `'maps every activity to an icon and beat assets'` expect the new beats:

```javascript
const STANDARD_BEATS = ['intro', 'rules', 'round_1', 'round_2', 'round_3', 'recap'];
const PILOT_STANDARD_BEATS = ['intro', 'rules', 'round_1', 'round_2', 'round_3', 'celebrate', 'closing'];
const CAT5_BEATS = ['intro', 'rules', 'round_1', 'round_2', 'round_3', 'synthesis', 'celebrate', 'closing'];
```

  and in `'maps every activity to an icon and beat assets'` (lines 75-76) choose the expected list per pilot:

```javascript
      const expectedBeats =
        entry.id === 'activity_phoneme_treasure_hunt'
          ? CAT5_BEATS
          : REPRESENTATIVE_ACTIVITY_IDS.has(entry.id)
            ? PILOT_STANDARD_BEATS
            : STANDARD_BEATS;
```

- [ ] **Step: Run it, expect FAIL** with `npm test -- activityAssets` from `frontend/`. Expected: the celebrate/closing assertions fail (`expected 'recap' to be 'celebrate'`).

- [ ] **Step: Minimal implementation.** Replace `beatIdFromSessionState` in `frontend/src/activityGame/activityAssets.js` (lines 81-95) with an explicit table that mirrors the backend, and prefer a backend-supplied `screenFrame.beat` when present:

```javascript
const STEP_BEAT_TABLE = {
  STEP_1_HOOK: 'intro',
  STEP_2_RULES: 'rules',
  STEP_2_MISSION: 'rules',
  STEP_2_SETUP: 'rules',
  STEP_4_SYNTHESIS: 'synthesis',
  STEP_4_CELEBRATE: 'celebrate',
  STEP_5_CELEBRATE: 'celebrate',
  STEP_5_CLOSING: 'closing',
  STEP_6_CLOSING: 'closing',
  EARLY_EXIT: 'closing',
};

export function beatIdFromSessionState(sessionState, screenFrame) {
  if (screenFrame?.beat) return screenFrame.beat;
  const step = sessionState?.current_step || '';
  if (
    step.startsWith('STEP_3_ROUND_') ||
    step.startsWith('STEP_3_COLLECT_') ||
    step.startsWith('STEP_3_BUILD_')
  ) {
    return roundIdFromStep(step, sessionState?.current_round);
  }
  return STEP_BEAT_TABLE[step] || 'intro';
}
```

- [ ] **Step: Pass the backend beat through the consumer.** In `frontend/src/activityGame/ActivityGameApp.jsx:122`, pass the live screen frame: `const beatId = beatIdFromSessionState(sessionState, screenFrame);` (the component already receives `screenFrame` from `useActivityTextSession`; if not in scope, add it to the destructured hook return / props alongside `sessionState`).

- [ ] **Step: Run it, expect PASS** with `npm test -- activityAssets` from `frontend/`.

- [ ] **Step: Commit** with message `feat(activity-assets): explicit step-beat table`.

---

### Task 5 (Frame semantics): Turn-by-turn backend test per pilot — frame matches the line spoken now

**Files:**
- Create: `backend/tests/test_finalize_frame_sync.py`
- Test: `backend/tests/test_finalize_frame_sync.py`

Assert across a full session per pilot that `screen_frame.beat == beat_for_step(step)` for the step whose line is spoken now, including auto-advance boundaries. The Turn Director path needs LLM calls; to keep the test deterministic we drive `resolve_turn` with a stub `ScriptAgent` whose `generate_turn_from_directive`/`generate_turn` return canned `TurnResponse`s, and the feature flag forced on.

- [ ] **Step: Write the failing test.** Create `backend/tests/test_finalize_frame_sync.py`:

```python
"""Turn-by-turn frame-sync test: screen_frame.beat matches the line spoken now."""

import pytest

from config import get_settings
from recipe_loader import load_instruction_recipe, recipe_to_session_state
from schemas.turn_response import TurnResponse
from turn_handling.core import resolve_turn
from turn_handling.finalize import beat_for_step
from turn_handling.types import TurnInput


class StubScriptAgent:
    """Deterministic ScriptAgent — never calls the provider."""

    last_plan = None

    async def generate_turn(self, state) -> TurnResponse:
        return TurnResponse(
            dialogue=f"[gentle] line for {state.current_step}",
            tone_marker="gentle",
            screen_widget="photo_display",
            screen_widget_params={},
        )

    async def retry_speaker_turn(self, *_args, **_kwargs) -> TurnResponse:
        return await self.generate_turn(_args[0])

    async def generate_turn_from_directive(self, state, directive) -> TurnResponse:
        return TurnResponse(
            dialogue=f"[{directive.emotion_tag}] line for {state.current_step}",
            tone_marker=directive.emotion_tag,
            screen_widget=directive.screen_widget,
            screen_widget_params=directive.screen_widget_params,
            stay_on_step=directive.stay_on_step,
        )


@pytest.fixture()
def director_enabled():
    settings = get_settings()
    previous = settings.turn_director_enabled
    settings.turn_director_enabled = True
    yield
    settings.turn_director_enabled = previous


@pytest.mark.asyncio
async def test_cat1_career_frame_matches_spoken_line(director_enabled) -> None:
    recipe = load_instruction_recipe("activity_career_decision_role_play")
    state = recipe_to_session_state(recipe, "frame-cat1", "T1", "career_decision_role_play")
    agent = StubScriptAgent()

    # Hook -> rules
    result = await resolve_turn(state, TurnInput(text="yes"), agent)
    assert result.screen_frame.beat == beat_for_step(state.current_step, state.current_round)

    # Rules -> round 1
    result = await resolve_turn(state, TurnInput(text="yes"), agent)
    assert result.screen_frame.beat == beat_for_step(state.current_step, state.current_round)
    assert result.screen_frame.beat in {"round_1", "rules"}
```

- [ ] **Step: Run it, expect FAIL** (before Tasks 1-2 land) or PASS (after). Run `uv run pytest backend/tests/test_finalize_frame_sync.py -q` from the worktree root. Until Tasks 1-2 are merged, expect `AssertionError` (frame lags one step); after, expect PASS. Because this Task 5 lands after Tasks 1-2, the first run here should PASS — confirm by running it once and seeing green; if red, the residual desync identifies a missed call site.

- [ ] **Step: Minimal implementation.** No production code — Tasks 1-3 already implement the behavior; this task only adds the assertion harness. If the run is red, the fix is in `core.py`/`directive.py` per Task 2 (a remaining pre-advance frame).

- [ ] **Step: Run it, expect PASS** with `uv run pytest backend/tests/test_finalize_frame_sync.py -q`.

- [ ] **Step: Run ruff** with `uv run ruff check tests/test_finalize_frame_sync.py` from `backend/`.

- [ ] **Step: Commit** with message `test(finalize): assert frame matches spoken line`.

---

### Task 6 (Stream 2 — A): Deterministic contract/role/theme/`do_not_suggest` validator in `finalize_turn` (A-i)

**Files:**
- Modify: `backend/turn_handling/finalize.py`
- Test: `backend/tests/test_finalize_validators.py`

Add validator A: for the current beat, validate the spoken line against the recipe's `SourceStepContract` data + role + structure — stays in role, honors `do_not_suggest_items`, no premature completion, best-effort `acceptable_themes` keyword check. On divergence → one regen seeded with the contract's ideal branch → still bad → deterministic recipe fallback. Deterministic; no per-turn LLM intent classifier.

- [ ] **Step: Write the failing test.** Create `backend/tests/test_finalize_validators.py`:

```python
"""Unit tests for Stream 2 guardrail validators in finalize_turn."""

import pytest

from recipe_loader import load_instruction_recipe, recipe_to_session_state
from schemas.turn_response import TurnResponse
from turn_handling.finalize import _violates_contract, finalize_turn


class _StubAgent:
    last_plan = None

    def __init__(self, replies):
        self._replies = list(replies)

    async def generate_turn(self, state):
        return self._replies.pop(0)

    async def retry_speaker_turn(self, *_a, **_k):
        return self._replies.pop(0)


def _career_state(step: str, current_round: int):
    recipe = load_instruction_recipe("activity_career_decision_role_play")
    state = recipe_to_session_state(recipe, "validator-a", "T1", "career_decision_role_play")
    state.current_step = step
    state.current_round = current_round
    return state


def test_violates_contract_flags_item_suggestion_when_do_not_suggest() -> None:
    state = _career_state("STEP_3_ROUND_1", 1)
    bad = TurnResponse(
        dialogue="[gentle] Go find a pillow and a sock to fight the fire!",
        tone_marker="gentle",
        screen_widget="photo_display",
        screen_widget_params={},
    )
    assert _violates_contract(state, bad, do_not_suggest_items=True) is True


def test_violates_contract_allows_in_role_firefighter_line() -> None:
    state = _career_state("STEP_3_ROUND_1", 1)
    good = TurnResponse(
        dialogue="[gentle] You are the firefighter. Should your team send help now, or check first?",
        tone_marker="gentle",
        screen_widget="photo_display",
        screen_widget_params={},
    )
    assert _violates_contract(state, good, do_not_suggest_items=True) is False


@pytest.mark.asyncio
async def test_finalize_regenerates_then_falls_back_on_contract_divergence() -> None:
    state = _career_state("STEP_3_ROUND_1", 1)
    bad = TurnResponse(
        dialogue="[gentle] Go grab a teddy and a marble!",
        tone_marker="gentle",
        screen_widget="photo_display",
        screen_widget_params={},
    )
    # First (the bad line passed in) -> regen returns another bad line ->
    # finalize must fall back to the deterministic recipe response.
    agent = _StubAgent([bad])  # one corrective regen attempt
    turn, frame = await finalize_turn(
        state, bad, action="stay", script_agent=agent, do_not_suggest_items=True
    )
    # Deterministic fallback is recipe-grounded (firefighter), not a leaked item line.
    assert "teddy" not in turn.dialogue.lower()
    assert "marble" not in turn.dialogue.lower()
    assert frame.beat == "round_1"
```

- [ ] **Step: Run it, expect FAIL** with `uv run pytest backend/tests/test_finalize_validators.py -q`. Expected: `ImportError: cannot import name '_violates_contract'` and `finalize_turn() got an unexpected keyword argument 'script_agent'`.

- [ ] **Step: Minimal implementation.** Extend `backend/turn_handling/finalize.py`. Add imports at top (after the existing imports):

```python
import re

try:
    from ..agents.script_agent import ScriptAgent
    from ..schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from ..schemas.step_instruction import RoundInstruction, StepGoal
except ImportError:
    from agents.script_agent import ScriptAgent
    from schemas.creative_slots import Cat1CreativeSlots, Cat5CreativeSlots
    from schemas.step_instruction import RoundInstruction, StepGoal

from .generation import (
    _has_completion_language,
    _source_fidelity_fallback_response,
    _ITEM_SUGGESTION_RE,
)
```

  Add the contract goal lookup, the validator, and wire it into `finalize_turn`:

```python
def _goal_for_step(state: SessionStateModel) -> "StepGoal | RoundInstruction | None":
    """Return the recipe goal/round for the current step, if any."""
    recipe = state.instruction_recipe
    if recipe is None:
        return None
    instructions = recipe.step_instructions
    step = state.current_step
    if step == "STEP_1_HOOK":
        return instructions.hook
    if step in ("STEP_2_RULES", "STEP_2_MISSION", "STEP_2_SETUP"):
        return instructions.transition
    if step.startswith(_ROUND_PREFIXES):
        round_idx = max(state.current_round - 1, 0)
        if round_idx < len(instructions.rounds):
            return instructions.rounds[round_idx]
    if "CELEBRATE" in step:
        return instructions.celebrate
    if "CLOSING" in step:
        return instructions.closing
    if "SYNTHESIS" in step:
        return instructions.synthesis
    return None


def _violates_contract(
    state: SessionStateModel,
    turn_response: TurnResponse,
    *,
    do_not_suggest_items: bool,
) -> bool:
    """Deterministic A-i contract/role/structure check for the current beat.

    Returns True when the spoken line diverges from the recipe contract:
    suggests findable items when forbidden, declares premature completion on a
    collection round, or drops the role token the contract requires. Theme
    keywords are best-effort and never hard-fail on their own.
    """
    dialogue = turn_response.dialogue

    # do_not_suggest_items: never name specific findable objects.
    if do_not_suggest_items and _ITEM_SUGGESTION_RE.search(dialogue):
        return True

    # Premature completion during an unfinished collection round.
    if (
        state.current_step.startswith("STEP_3_COLLECT_")
        and len(state.collected_photos) < state.total_rounds
        and _has_completion_language(dialogue)
    ):
        return True

    # Role fidelity: when the contract names a role_title, the line should not
    # contradict it. Best-effort — only flag the hard case of a Cat1 decision
    # round that drops the role word entirely AND offers no question.
    if (
        isinstance(state.creative_slots, Cat1CreativeSlots)
        and state.creative_slots.game_mechanic == "decide"
        and state.current_step.startswith("STEP_3_ROUND_")
        and "?" not in dialogue
    ):
        return True

    return False


def _contract_regen_hint(state: SessionStateModel) -> str:
    """Seed a corrective regen with the contract's ideal branch for this beat."""
    goal = _goal_for_step(state)
    ideal = ""
    if goal is not None:
        ideal = goal.source_contract.ai_followups.ideal or goal.source_contract.example_ai_line
    return (
        "CORRECTION: Stay in role and do NOT name specific objects to find. "
        f"Follow the source intent: {ideal}" if ideal else
        "CORRECTION: Stay in role and do NOT name specific objects for the child to find."
    )
```

  Update `finalize_turn` signature and body:

```python
async def finalize_turn(
    state: SessionStateModel,
    turn_response: TurnResponse,
    action: str,
    *,
    script_agent: ScriptAgent | None = None,
    do_not_suggest_items: bool = True,
) -> tuple[TurnResponse, ScreenFrame]:
    """Return the (safe line, matching frame) pair from one resolved state.

    Stream 1 derives the frame; Stream 2 validates the spoken line, regenerates
    once on contract divergence, and falls back deterministically on failure.
    """
    if script_agent is not None and _violates_contract(
        state, turn_response, do_not_suggest_items=do_not_suggest_items
    ):
        try:
            regenerated = await script_agent.generate_turn(state)
        except Exception:
            regenerated = None
        if regenerated is not None and not _violates_contract(
            state, regenerated, do_not_suggest_items=do_not_suggest_items
        ):
            turn_response = regenerated
        else:
            turn_response = _source_fidelity_fallback_response(state)

    screen_frame = derive_frame(state, action)
    return turn_response, screen_frame
```

- [ ] **Step: Run it, expect PASS** with `uv run pytest backend/tests/test_finalize_validators.py backend/tests/test_finalize_frame.py -q`.

- [ ] **Step: Run ruff** with `uv run ruff check turn_handling/finalize.py && uv run ruff format turn_handling/finalize.py` from `backend/`. (Note: `_ITEM_SUGGESTION_RE` and `_source_fidelity_fallback_response` are imported from `generation.py`; reference them so ruff doesn't flag unused — they are used in `_violates_contract`/`finalize_turn`, so no suppression needed.)

- [ ] **Step: Commit** with message `feat(finalize): add contract guardrail validator`.

---

### Task 7 (Stream 2 — B): Broaden the premature-completion regex and enforce stay/advance consistency

**Files:**
- Modify: `backend/turn_handling/generation.py:44-55` (`_COMPLETION_PATTERNS`)
- Modify: `backend/turn_handling/finalize.py` (add `_violates_flow`, wire into `finalize_turn`)
- Test: `backend/tests/test_finalize_validators.py`

Catch creative completion variants ("all 3 spotted!", "search is over") and enforce that an `action=stay` line does not say "next/let's move on".

- [ ] **Step: Write the failing test.** Append to `backend/tests/test_finalize_validators.py`:

```python
from turn_handling.generation import _has_completion_language
from turn_handling.finalize import _violates_flow


def test_completion_regex_catches_creative_variants() -> None:
    assert _has_completion_language("Wow, all 3 spotted!") is True
    assert _has_completion_language("The search is over, friend!") is True
    assert _has_completion_language("Let's find the next one!") is False


def test_violates_flow_flags_advance_language_on_stay() -> None:
    state = _career_state("STEP_3_ROUND_1", 1)
    moving_on = TurnResponse(
        dialogue="[gentle] Great, let's move on to the next part!",
        tone_marker="gentle",
        screen_widget="photo_display",
        screen_widget_params={},
        stay_on_step=True,
    )
    assert _violates_flow(state, moving_on, action="stay") is True


def test_violates_flow_allows_stay_without_advance_language() -> None:
    state = _career_state("STEP_3_ROUND_1", 1)
    staying = TurnResponse(
        dialogue="[gentle] Take your time — should the team send help now or check first?",
        tone_marker="gentle",
        screen_widget="photo_display",
        screen_widget_params={},
        stay_on_step=True,
    )
    assert _violates_flow(state, staying, action="stay") is False
```

- [ ] **Step: Run it, expect FAIL** with `uv run pytest backend/tests/test_finalize_validators.py -q`. Expected: `assert _has_completion_language("Wow, all 3 spotted!") is True` fails (returns False) and `ImportError: cannot import name '_violates_flow'`.

- [ ] **Step: Minimal implementation — broaden regex.** In `backend/turn_handling/generation.py`, extend `_COMPLETION_PATTERNS` (lines 44-55) by adding two alternations before the closing `r")\b"`:

```python
    r"|(?:all|every)\s+\d+\s+(?:spotted|found|collected|done)"
    r"|(?:the\s+)?(?:search|hunt|patrol)\s+is\s+(?:over|complete|done)"
```

- [ ] **Step: Minimal implementation — `_violates_flow`.** Add to `backend/turn_handling/finalize.py`:

```python
_ADVANCE_LANGUAGE_RE = re.compile(
    r"(?i)\b(?:next\s+(?:one|step|round|part)|move\s+on|moving\s+on|let'?s\s+go\s+on"
    r"|on\s+to\s+the\s+next|coming\s+up\s+next)\b"
)


def _violates_flow(state: SessionStateModel, turn_response: TurnResponse, *, action: str) -> bool:
    """Deterministic flow-control check (Stream 2 B).

    A line tied to a stay action must not promise advancing. Premature
    collection completion is also a flow violation when items remain.
    """
    dialogue = turn_response.dialogue
    if (action in ("stay", "need_help", "redirect") or turn_response.stay_on_step) and _ADVANCE_LANGUAGE_RE.search(
        dialogue
    ):
        return True
    if (
        state.current_step.startswith("STEP_3_COLLECT_")
        and len(state.collected_photos) < state.total_rounds
        and _has_completion_language(dialogue)
    ):
        return True
    return False
```

  Wire it into `finalize_turn` by combining with the contract check — change the guard condition:

```python
    needs_fix = _violates_contract(
        state, turn_response, do_not_suggest_items=do_not_suggest_items
    ) or _violates_flow(state, turn_response, action=action)
    if script_agent is not None and needs_fix:
        try:
            regenerated = await script_agent.generate_turn(state)
        except Exception:
            regenerated = None
        regen_ok = regenerated is not None and not _violates_contract(
            state, regenerated, do_not_suggest_items=do_not_suggest_items
        ) and not _violates_flow(state, regenerated, action=action)
        turn_response = regenerated if regen_ok else _source_fidelity_fallback_response(state)
```

- [ ] **Step: Run it, expect PASS** with `uv run pytest backend/tests/test_finalize_validators.py backend/tests/test_activity_text_game_turns.py -q`.

- [ ] **Step: Run ruff** with `uv run ruff check turn_handling/finalize.py turn_handling/generation.py && uv run ruff format turn_handling/finalize.py turn_handling/generation.py` from `backend/`.

- [ ] **Step: Commit** with message `feat(finalize): add flow-control guardrail`.

---

### Task 8 (Stream 2 — C): Relocate + extend device-word/phoneme sanitation into `finalize_turn`; sanitize `example_ai_line` at load

**Files:**
- Modify: `backend/turn_handling/finalize.py` (apply `_enforce_text_only_dialogue` as the last word)
- Modify: `backend/agents/script_agent.py:798-799` (`_append_source_fidelity_lines`) — sanitize `example_ai_line` before it reaches the prompt
- Test: `backend/tests/test_finalize_validators.py`, `backend/tests/test_generation_text_mode.py`

Make `finalize_turn` the single last sanitation step for device-words/phoneme terms, and sanitize the contract's `example_ai_line` at prompt-build time so the LLM never sees device words as "official examples."

- [ ] **Step: Write the failing test.** Append to `backend/tests/test_finalize_validators.py`:

```python
from agents.script_agent import _build_instruction_overlay


@pytest.mark.asyncio
async def test_finalize_sanitizes_device_words_in_text_mode() -> None:
    state = _career_state("STEP_3_ROUND_1", 1)
    state.interaction_mode = "text"
    leaky = TurnResponse(
        dialogue="[gentle] Tap the card when you decide!",
        tone_marker="gentle",
        screen_widget="photo_display",
        screen_widget_params={},
        stay_on_step=True,
    )
    turn, _frame = await finalize_turn(state, leaky, action="stay")
    lower = turn.dialogue.lower()
    assert "tap" not in lower
    assert "card" not in lower


def test_overlay_example_ai_line_sanitized_in_text_mode() -> None:
    recipe = load_instruction_recipe("activity_phoneme_treasure_hunt")
    state = recipe_to_session_state(
        recipe, "overlay-text", "T1", "phoneme_treasure_hunt", interaction_mode="text"
    )
    state.current_step = "STEP_3_COLLECT_1"
    state.current_round = 1

    overlay = _build_instruction_overlay(state)

    # The example line, if it carried a device word, is sanitized before it
    # reaches the model as an "official example."
    assert "tap" not in overlay.lower()
    assert " card " not in overlay.lower()
```

- [ ] **Step: Run it, expect FAIL** with `uv run pytest backend/tests/test_finalize_validators.py -q`. Expected: the device word survives finalize (`assert "tap" not in lower` fails) because `finalize_turn` does not yet sanitize.

- [ ] **Step: Minimal implementation — sanitation in finalize.** In `backend/turn_handling/finalize.py`, import the sanitizer and apply it as the final step before returning. Add to imports:

```python
from .generation import _enforce_text_only_interaction
```

  At the end of `finalize_turn`, before deriving the frame, normalize the chosen response:

```python
    turn_response = _enforce_text_only_interaction(state, turn_response)
    screen_frame = derive_frame(state, action)
    return turn_response, screen_frame
```

  (`_enforce_text_only_interaction` is a no-op when `interaction_mode != "text"` and already wraps `_enforce_text_only_dialogue` including the phoneme replacements, so this is the single last word.)

- [ ] **Step: Minimal implementation — sanitize `example_ai_line` at load.** In `backend/agents/script_agent.py`, the `_append_source_fidelity_lines` function emits `Example AI line: "..."` at lines 798-799. Pass `state` so it can sanitize. Change the helper signature and call site:

  In `_build_instruction_overlay` (line 720), change the call to `_append_source_fidelity_lines(lines, instructions, goal_source, state)`. Update the helper:

```python
def _append_source_fidelity_lines(
    lines: list[str],
    instructions: StepInstruction,
    goal_source: StepGoal | RoundInstruction,
    state: SessionStateModel,
) -> None:
```

  and replace the `example_ai_line` emission (lines 798-799) with a sanitized version:

```python
    if source_contract.example_ai_line:
        safe_example = _enforce_text_only_dialogue(state, source_contract.example_ai_line)
        lines.append(f'Example AI line: "{safe_example}"')
```

  (`_enforce_text_only_dialogue` already exists in this module at line 427 and is a no-op outside text mode, preserving the existing `test_script_overlay_includes_source_dialogue_contract_for_current_step` assertion for the default-mode career state.)

- [ ] **Step: Run it, expect PASS** with `uv run pytest backend/tests/test_finalize_validators.py backend/tests/test_generation_text_mode.py backend/tests/test_activity_source_fidelity.py -q`.

- [ ] **Step: Run ruff** with `uv run ruff check turn_handling/finalize.py agents/script_agent.py && uv run ruff format turn_handling/finalize.py agents/script_agent.py` from `backend/`.

- [ ] **Step: Commit** with message `feat(finalize): centralize device-word sanitation`.

---

### Task 9 (Stream 2 — D): Always return the deterministic fallback on retry exhaustion, enriched with `collected_names`

**Files:**
- Modify: `backend/turn_handling/generation.py:394-416` (`_source_fidelity_fallback_response` — enrich with names) and `:560-571` (exhaustion path of `_generate_with_retry`)
- Test: `backend/tests/test_finalize_validators.py`, `backend/tests/test_generation_fallback.py`

Close the hole where `_generate_with_retry` returns the last (possibly bad) line after exhausting retries — always return the deterministic `_source_fidelity_fallback_response`, enriched with `collected_names`/characters so it reads "Fluffy and Bouncy," not "our friends."

- [ ] **Step: Write the failing test.** Append to `backend/tests/test_finalize_validators.py`:

```python
from turn_handling.generation import _generate_with_retry


class _ExhaustingAgent:
    """Always returns a line that fails plan validation, never raises."""

    last_plan = None

    async def generate_turn(self, state):
        # An item-suggestion line that _validate_plan rejects when
        # do_not_suggest_items is on (Cat5 collection detail).
        return TurnResponse(
            dialogue="[gentle] Go find a pillow and a sock!",
            tone_marker="gentle",
            screen_widget="photo_display",
            screen_widget_params={},
        )

    async def retry_speaker_turn(self, *_a, **_k):
        return await self.generate_turn(_a[0])


@pytest.mark.asyncio
async def test_exhaustion_returns_deterministic_fallback_not_last_bad_line() -> None:
    recipe = load_instruction_recipe("activity_phoneme_treasure_hunt")
    state = recipe_to_session_state(recipe, "exhaust", "T1", "phoneme_treasure_hunt")
    state.current_step = "STEP_3_COLLECT_2"
    state.current_round = 2
    state.collection_phase = "detail"
    state.collected_photos = ["text_find_1"]
    state.collected_names = ["Fluffy", "Bouncy"]

    response, debug = await _generate_with_retry(_ExhaustingAgent(), state)

    assert debug.final_verdict == "exhausted"
    # Not the last bad line.
    assert "pillow" not in response.dialogue.lower()
    assert "sock" not in response.dialogue.lower()


def test_fallback_response_uses_collected_names_not_generic_friends() -> None:
    recipe = load_instruction_recipe("activity_phoneme_treasure_hunt")
    state = recipe_to_session_state(recipe, "names", "T1", "phoneme_treasure_hunt")
    state.current_step = "STEP_5_CELEBRATE"
    state.collected_names = ["Fluffy", "Bouncy"]

    response = _source_fidelity_fallback_response(state)

    lower = response.dialogue.lower()
    assert "fluffy" in lower and "bouncy" in lower
    assert "our friends" not in lower
```

- [ ] **Step: Run it, expect FAIL** with `uv run pytest backend/tests/test_finalize_validators.py -q`. Expected: exhaustion returns the last bad line (`pillow` present) and the fallback has no names.

- [ ] **Step: Minimal implementation — enrich fallback with names.** In `backend/turn_handling/generation.py`, extend `_source_fidelity_fallback_response` (lines 394-416) so celebrate/closing/synthesis steps weave in `collected_names`. After computing `goal_text` / `scenario_text` (line 403) and before building `dialogue` (line 404):

```python
    names = ", ".join(state.collected_names) if state.collected_names else ""
    crew = ""
    if names and ("CELEBRATE" in state.current_step or "CLOSING" in state.current_step or "SYNTHESIS" in state.current_step):
        crew = f" with {names}"
    dialogue = (
        f"[{tone}] {title} is ready: {goal_text}{crew}.{scenario_text} "
        f"You are the {role_title}. What should we try?"
    )
```

  (Replaces the single `dialogue = ...` line; the `crew` clause only triggers on the closing-arc steps so round/hook fallbacks are unchanged and `test_source_fidelity_fallback_uses_current_activity_recipe` still passes.)

- [ ] **Step: Minimal implementation — exhaustion returns deterministic fallback.** In `backend/turn_handling/generation.py`, replace the tail of `_generate_with_retry` (lines 560-571, the "All attempts failed validation — return the last response anyway" block) with:

```python
    # All attempts failed validation — return the deterministic recipe fallback
    # (Stream 2 D) rather than the last (possibly bad) line.
    _record_retry_stat(state.current_step, exhausted=True)
    logger.warning(
        "script_generation: step=%s attempts=%d tier=%s validation=exhausted -> deterministic fallback",
        state.current_step,
        _MAX_GENERATION_ATTEMPTS,
        state.tier,
    )
    state.conversation_history = [t for t in state.conversation_history if not t.text.startswith("CORRECTION:")]
    fallback_response = _source_fidelity_fallback_response(state)
    fallback_response = _enforce_text_only_interaction(state, fallback_response)
    return fallback_response, _make_debug("exhausted")
```

  (Removes the `assert last_response is not None` and the return of `last_response`; `last_response` is still tracked for logging earlier in the loop but no longer returned. If ruff flags `last_response` as unused after this change, keep the assignment inside the loop since it is referenced by the diagnostic log on validation failure — no suppression needed.)

- [ ] **Step: Run it, expect PASS** with `uv run pytest backend/tests/test_finalize_validators.py backend/tests/test_generation_fallback.py backend/tests/test_activity_source_fidelity.py -q`.

- [ ] **Step: Run ruff** with `uv run ruff check turn_handling/generation.py && uv run ruff format turn_handling/generation.py` from `backend/`.

- [ ] **Step: Commit** with message `fix(finalize): deterministic fallback on exhaustion`.

---

### Task 10: Wire `finalize_turn` (with `script_agent`) into the directive and core advance/stay paths

**Files:**
- Modify: `backend/turn_handling/directive.py:1224-1231` (final return) and the celebrate/closing returns
- Modify: `backend/turn_handling/core.py` (interactive stay/advance returns)
- Modify: `backend/turn_handling/rounds.py:226-233` (main generation return)
- Test: `backend/tests/test_finalize_validators.py`, `backend/tests/test_finalize_frame_sync.py`

Tasks 6-9 made `finalize_turn` validate when given a `script_agent`. This task replaces the `derive_frame(...)`-only calls from Task 2 with `await finalize_turn(state, turn_response, action, script_agent=script_agent, do_not_suggest_items=...)` on the live LLM-producing paths, so the validators actually run. Pure deterministic returns (photo prompts, `_ended_result`) keep `derive_frame` (no validation needed).

- [ ] **Step: Write the failing test.** Append to `backend/tests/test_finalize_frame_sync.py` a path-level assertion that the directive final return runs validation (an item-leaking stay line gets sanitized/fallen-back):

```python
@pytest.mark.asyncio
async def test_directive_stay_path_runs_finalize_validation(director_enabled) -> None:
    from turn_handling.directive import _resolve_turn_with_directive
    from schemas.turn_directive import TurnDirective

    recipe = load_instruction_recipe("activity_phoneme_treasure_hunt")
    state = recipe_to_session_state(recipe, "dir-finalize", "T1", "phoneme_treasure_hunt")
    state.current_step = "STEP_3_COLLECT_1"
    state.current_round = 1
    state.collection_phase = "photo"

    class _LeakAgent(StubScriptAgent):
        async def generate_turn_from_directive(self, state, directive):
            return TurnResponse(
                dialogue="[gentle] Go find a pillow!",
                tone_marker="gentle",
                screen_widget=directive.screen_widget,
                screen_widget_params=directive.screen_widget_params,
                stay_on_step=True,
            )

        async def generate_turn(self, state):
            return TurnResponse(
                dialogue="[gentle] Which B word starts with the letter B?",
                tone_marker="gentle",
                screen_widget="photo_display",
                screen_widget_params={},
                stay_on_step=True,
            )

    directive = TurnDirective(
        action="stay",
        reasoning="stay",
        response_direction="Encourage finding a B word.",
        emotion_tag="gentle",
        stay_on_step=True,
    )
    result = await _resolve_turn_with_directive(state, TurnInput(text="hmm"), _LeakAgent(), directive)
    assert "pillow" not in result.turn_response.dialogue.lower()
    assert result.screen_frame.beat == "round_1"
```

- [ ] **Step: Run it, expect FAIL** with `uv run pytest backend/tests/test_finalize_frame_sync.py::test_directive_stay_path_runs_finalize_validation -q`. Expected: `"pillow"` still present (the directive path used `derive_frame` only, no validation).

- [ ] **Step: Minimal implementation — directive final return.** In `backend/turn_handling/directive.py`, make `_resolve_turn_with_directive` return through `finalize_turn`. Add `from .finalize import finalize_turn` to the finalize import (alongside `derive_frame`). Replace the final return (lines 1224-1231):

```python
    turn_response, screen_frame = await finalize_turn(
        state,
        turn_response,
        action,
        script_agent=script_agent,
        do_not_suggest_items=directive.do_not_suggest_items,
    )
    return TurnResult(
        turn_response=turn_response,
        screen_frame=screen_frame,
        auto_advance=auto_advance,
        response_type=response_type,
        error_exit=state.status == "error",
        debug=_debug(None, turn_response),
    )
```

  Note: `_append_ai_turn(state, turn_response.dialogue)` already ran on the non-advance branch (line 1219) before this return. To avoid the validated/fallback dialogue diverging from history, move the `_append_ai_turn` calls so they run on the finalized `turn_response`. For the non-advance branch (line 1219), remove the early `_append_ai_turn` and instead append after finalize. For the advance branch, the dialogue was appended at line 1159 before frame derivation; keep that (advance lines do not run the item-suggestion validator path for stay, but contract/flow checks may swap the line) — to stay correct, append history after finalize in both branches. Concretely: delete the `_append_ai_turn(state, turn_response.dialogue)` at line 1159 and 1219, and add `_append_ai_turn(state, turn_response.dialogue)` immediately after the `finalize_turn` call above (before building the `TurnResult`). Keep the celebrate (line 1124) and closing inline-widget assignments as-is since those return early.

- [ ] **Step: Minimal implementation — core + rounds live paths.** In `backend/turn_handling/core.py`, for the interactive generic-step returns that came from `_generate_with_retry` (the stay return at ~301 and the advance returns), replace `screen_frame=derive_frame(state, ...)` with a `finalize_turn` call wired with `script_agent` and `do_not_suggest_items=True`, appending history after finalize. Apply the same to `backend/turn_handling/rounds.py` main return (lines 226-233):

```python
    turn_response, screen_frame = await finalize_turn(
        state, turn_response, "advance" if not turn_response.stay_on_step else "stay", script_agent=script_agent
    )
    _append_ai_turn(state, turn_response.dialogue)
    state.turn_count += 1
    return TurnResult(
        turn_response=turn_response,
        screen_frame=screen_frame,
        auto_advance=auto_advance or _should_auto_advance(state),
        response_type=_get_response_type(state.current_step),
        error_exit=state.status == "error",
        debug=_build_debug_payload(state, gen_debug, script_agent, turn_response),
    )
```

  (Move the existing `_append_ai_turn` at rounds.py:224 to after finalize; import `finalize_turn` from `.finalize` in both modules. Leave the deterministic photo-prompt and `_ended_result` paths on `derive_frame`/inline beat — they need no validation.)

- [ ] **Step: Run it, expect PASS** with `uv run pytest backend/tests/test_finalize_frame_sync.py backend/tests/test_finalize_validators.py backend/tests/test_activity_text_game_turns.py backend/tests/test_activity_text_game_cat3.py backend/tests/test_generation_fallback.py -q`.

- [ ] **Step: Run the full backend suite** with `uv run pytest -q` from the worktree root to confirm no regressions (the pre-existing `carousel`-vs-`picker` asset failure is the only expected red and is out of scope).

- [ ] **Step: Run ruff** with `uv run ruff check turn_handling/ && uv run ruff format turn_handling/` from `backend/`.

- [ ] **Step: Commit** with message `feat(finalize): wire validators into turn paths`.

---

Key files for the executing agent (all absolute):
- New module: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/backend/turn_handling/finalize.py`
- `/Users/pharrelly/.../backend/turn_handling/{core,directive,rounds,helpers,generation}.py`
- `/Users/pharrelly/.../backend/schemas/visual_composition.py` (add `beat` field), `schemas/step_instruction.py`, `schemas/turn_directive.py`, `schemas/turn_response.py`
- `/Users/pharrelly/.../backend/agents/script_agent.py` (`_enforce_text_only_dialogue` line 427, `_append_source_fidelity_lines` line 759, `example_ai_line` lines 798-799)
- Frontend: `/Users/pharrelly/.../frontend/src/activityGame/activityAssets.js`, `ActivityGameApp.jsx`; manifest `/Users/pharrelly/.../frontend/public/activity-assets/activity-assets.manifest.json`
- Tests (backend): `/Users/pharrelly/.../backend/tests/{test_finalize_frame,test_finalize_frame_sync,test_finalize_validators,test_activity_text_game_turns,test_generation_text_mode,test_activity_source_fidelity,test_activity_text_game_cat3,test_generation_fallback}.py`
- Tests (root/frontend): `/Users/pharrelly/.../tests/test_activity_text_game_asset_contract.py`, `/Users/pharrelly/.../frontend/tests/activityAssets.test.js`

Load-bearing facts confirmed against the code: tests run from worktree root via `uv run pytest` (`pyproject.toml` has `pythonpath=["backend"]`, `testpaths=["tests"]`, `asyncio_mode="auto"`), but the spec's named backend tests live in `backend/tests/` and are run directly with that path. `ScreenFrame` (`schemas/visual_composition.py`) is serialized via `model_dump()` in `server.py:1073`, so an added optional `beat` field surfaces to the frontend. The directive path already persists `state.last_directive_action` (`session_state.py:103`). `_source_fidelity_fallback_response` (`generation.py:394`) and `_ITEM_SUGGESTION_RE`/`_has_completion_language` (`generation.py:44,136`) are reused by the validators. Pre-existing unrelated failure: `tests/test_activity_text_game_asset_contract.py::test_representative_activity_layout_contracts_match_touchless_goal` asserts synthesis `mode == "carousel"` while the manifest has `picker` — out of scope for Streams 1-2.

---

## Stream 3 — Asset regeneration (Codex raster, pilot-complete)

> Run after Stream 1+2. Per pilot: draft prompt → generate via codex:codex-rescue → inspect/select with Read → copy → build → validate → human sign-off. See Integration Note #2 re `_required_beat_ids`.


### Task 1: Career Decision Role Play (Cat1) — full beat scenes + item sprites

**Files:**
- Create: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/{intro,rules,round_1,round_2,round_3,celebrate,closing,icon}.png`
- Create: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/items/{alarm,phone,hose,oil,outside,firefighter}.png`
- Modify: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity-assets.manifest.json:308-427` (regenerated by builder)
- Test: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/tests/test_activity_text_game_asset_contract.py`

> Note (factual-sources policy, spec §6): all career assets are generic objects/characters (a generic firefighter helper, a generic alarm, hose, etc.) — NOT references to a real-world named person/place/brand — so Codex raster generation is permitted. Do not bake in any text, letters, numbers, or logos.

- [ ] **Step: Draft the 8 scene Codex prompts.** Working from the recipe `backend/games/activity_career_decision_role_play.md` step goals (intro = name the firefighter mission + smoke-alarm cue; rules = explain the one-prompt/one-choice loop; round_1 = dispatch decision; round_2 = water hose vs oil tool choice; round_3 = check-people-outside first-safe-action; celebrate = award the "Firefighter Helper" badge; closing = warm goodbye), assemble ONE prompt per scene. Each prompt MUST embed verbatim the style contract text and reference image path. Template per scene (fill `<SUBJECT>`):
```
Generate a single square 512x512 full-bleed children's-book scene illustration. SUBJECT: <SUBJECT>.
STRICT STYLE CONTRACT — follow exactly:
<paste full contents of frontend/public/activity-assets/prompts/wonderlens-activity-style.md>
VISUAL REFERENCE IMAGE (match its palette, linework, composition):
/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/prompts/style-reference-flat-nordic.png
This is a full-bleed scene (exemplar 3 in the reference): softly painterly, content centered in the lens-safe area (canvas 480 / safe 380 / center 300), muted salmon + dusty blue with oatmeal/sage/mustard accents, arc eyes, pale cheeks, sparse dash/circle marks, soft pencil grain.
HARD CONSTRAINTS: no text, no letters, no numbers, no logos, no watermark, no circular mask, no lens border, no rim, no vignette, no black corners, no colored border, no transparent margin.
```
SUBJECTS: intro = "a friendly flat-Nordic firefighter helper waving beside a glowing smoke-alarm cue, inviting/airy mood"; rules = "a simple loop motif — one speech prompt arrow leading to one choice marker lighting up, calm explanatory mood"; round_1 = "a firefighter helper at a station deciding whether to send the team — two soft choice glows"; round_2 = "a water hose and a cooking-oil bottle side by side as two safe-tool options"; round_3 = "a firefighter helper checking that people are safely outside a doorway"; celebrate = "a beaming firefighter helper holding up a round 'helper' badge, confetti dashes, warm congratulatory mood"; closing = "a firefighter helper waving goodbye under a soft warm sky, gentle farewell mood".
- [ ] **Step: Generate scenes via codex:codex-rescue.** For each of the 8 scene prompts, invoke the `codex:codex-rescue` Task subagent (foreground, `--write`) forwarding the drafted prompt so Codex built-in imagegen writes candidate PNGs to `/Users/pharrelly/.codex/generated_images/<uuid>/`. Note each returned output directory.
- [ ] **Step: Inspect + select scene candidates with the Read tool.** Read each candidate PNG (the Read tool renders images). Reject any with text/letters/logos/borders/vignette/black corners or off-palette (mint/blue/purple/black/neon dominance); accept the best on-style full-bleed square with content in the lens-safe center. Record the chosen absolute source path per beat.
- [ ] **Step: Copy chosen scenes into the pilot folder.** Copy each selected PNG to its target name:
```bash
cp "<chosen-intro-src>"     "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/intro.png"
cp "<chosen-rules-src>"     "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/rules.png"
cp "<chosen-round_1-src>"   "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/round_1.png"
cp "<chosen-round_2-src>"   "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/round_2.png"
cp "<chosen-round_3-src>"   "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/round_3.png"
cp "<chosen-celebrate-src>" "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/celebrate.png"
cp "<chosen-closing-src>"   "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/closing.png"
cp "<chosen-icon-src>"      "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/icon.png"
```
(For `icon.png`, reuse the best small recognizable subject — a firefighter-helper face on clean white — generating one extra candidate with the item prompt template below if no scene crop reads well at icon size.)
- [ ] **Step: Draft the 6 item-sprite Codex prompts.** Items are reusable single-subject sprites on clean white (manifest ids: `alarm`, `phone`, `hose`, `oil`, `outside`, `firefighter`). Per item use this template (fill `<SUBJECT>`):
```
Generate a single square 512x512 reusable item sprite: ONE centered <SUBJECT> on clean white with generous white padding.
STRICT STYLE CONTRACT — follow exactly:
<paste full contents of frontend/public/activity-assets/prompts/wonderlens-activity-style.md>
VISUAL REFERENCE IMAGE (match its palette, linework, composition):
/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/prompts/style-reference-flat-nordic.png
This is an item/object on clean white (exemplars 1–2 in the reference): broad flat color fills, linework only for arc eyes/tiny marks/sparse dashes, muted salmon + dusty blue with oatmeal/sage/mustard accents, soft pencil grain, no baked UI frame.
HARD CONSTRAINTS: no text, no letters, no numbers, no logos, no watermark, no circular mask, no border, no rim, no vignette, no black corners, no transparent margin, single subject only.
```
SUBJECTS: alarm = "a round smoke-alarm disc"; phone = "a simple handset / call icon"; hose = "a coiled water hose"; oil = "a small cooking-oil bottle"; outside = "an open doorway showing people safely outside"; firefighter = "a friendly firefighter helper character (head-and-shoulders)".
- [ ] **Step: Generate item sprites via codex:codex-rescue.** Invoke `codex:codex-rescue` (foreground, `--write`) for each of the 6 item prompts; record each `/Users/pharrelly/.codex/generated_images/<uuid>/` output dir.
- [ ] **Step: Inspect + select item candidates with the Read tool.** Read each candidate; accept the best centered single-subject sprite on clean white with no black/colored padding, no text/border. Record chosen absolute source path per item.
- [ ] **Step: Copy chosen item sprites into items/.** 
```bash
cp "<chosen-alarm-src>"       "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/items/alarm.png"
cp "<chosen-phone-src>"       "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/items/phone.png"
cp "<chosen-hose-src>"        "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/items/hose.png"
cp "<chosen-oil-src>"         "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/items/oil.png"
cp "<chosen-outside-src>"     "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/items/outside.png"
cp "<chosen-firefighter-src>" "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_career_decision_role_play/items/firefighter.png"
```
> Note: do NOT yet update `ITEM_CROPS` in `scripts/build_activity_screen_assets.py` for these — the new full-frame sprites are dropped in directly. The builder's `build_items()` will re-crop from scenes only for ids still listed in `ITEM_CROPS`; copying finished 512² sprites in place and (if needed) removing this pilot's stale entries from `ITEM_CROPS` is done in Task 4. For now, leave the in-place sprites authoritative.
- [ ] **Step: Build screen assets for the pilot.** From repo root:
```bash
python3 scripts/build_activity_screen_assets.py
```
Confirm it exits 0 and rewrites `frontend/public/activity-assets/activity-assets.manifest.json` (downscales to 512 + regenerates layout plans). Note: until Task 4 adds the `celebrate`/`closing` beat ids, `plan_for` returns a default `single` layout for them, which is correct for these scene-only beats.
- [ ] **Step: Run the asset contract test, expect career-related items PASS.** From `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/backend`:
```bash
uv run pytest ../tests/test_activity_text_game_asset_contract.py::test_manifest_item_assets_are_sized_and_not_black_padded -q
```
Expect PASS for the new career item sprites (512², no black edges). The `test_activity_asset_manifest_matches_runtime_recipe_beats` test will still FAIL on `celebrate`/`closing` until Task 4 — that is expected and tracked there.
- [ ] **Step: Human sign-off in the visual companion.** Start the app from this worktree, open `/?view=activities`, select Career Decision Role Play, and walk every beat so each scene renders on the device-screen visual companion:
```bash
( cd /Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend && npm run dev )
# open http://localhost:5173/?view=activities — confirm intro→rules→round_1..3→celebrate→closing scenes + item sprites read on-style at lens size, then approve before continuing
```
Wait for explicit human approval of the picked set before moving on.
- [ ] **Step: Commit.** `git add` the new career PNGs + regenerated manifest, then:
```bash
git commit -m "feat(assets): regen career role play pilot art"
```

### Task 2: Guided Drawing (Cat3) — full beat scenes + item sprites

**Files:**
- Create: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_guided_drawing/{intro,rules,round_1,round_2,round_3,celebrate,closing,icon}.png`
- Create: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_guided_drawing/items/{paper,pencil,drawing}.png`
- Modify: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity-assets.manifest.json:458-577` (regenerated by builder)
- Test: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/tests/test_activity_text_game_asset_contract.py`

> Note (factual-sources policy, spec §6): all guided-drawing assets are generic objects (paper, pencil, a child's drawing) and a generic "Guided Artist" character — permitted. No text/letters/numbers/logos baked in.

- [ ] **Step: Draft the 8 scene Codex prompts.** Working from `backend/games/activity_guided_drawing.md` (intro = name the child a "Guided Artist", invite one small step; rules = explain the give-a-step / try-it / report loop, mention paper + pencil; round_1 = draw one big circle; round_2 = add two small ears/petals; round_3 = add one face/detail and say done; celebrate = award the "Guided Artist" title; closing = warm goodbye + suggest another drawing). Use the SCENE template from Task 1 (verbatim style-contract paste + reference-image path + full-bleed scene directives + hard constraints). SUBJECTS: intro = "a cheerful flat-Nordic 'Guided Artist' child at a desk with blank paper, inviting mood"; rules = "a loop motif: a hand drawing one mark, then a small checkmark, calm explanatory mood"; round_1 = "a sheet of paper with one big soft circle drawn on it, pencil resting beside"; round_2 = "the same circle now with two small ears/petals added"; round_3 = "a finished simple face/creature drawing on the paper"; celebrate = "a beaming Guided Artist holding up the finished drawing with a round title badge, confetti dashes"; closing = "a Guided Artist waving goodbye beside the drawing, gentle farewell mood".
- [ ] **Step: Generate scenes via codex:codex-rescue.** Invoke `codex:codex-rescue` (foreground, `--write`) for each of the 8 scene prompts; record each `/Users/pharrelly/.codex/generated_images/<uuid>/` output dir.
- [ ] **Step: Inspect + select scene candidates with the Read tool.** Read each candidate; reject text/border/vignette/black-corner/off-palette outputs; accept the best on-style full-bleed square with lens-safe-centered content. Record chosen source path per beat.
- [ ] **Step: Copy chosen scenes into the pilot folder.**
```bash
cp "<chosen-intro-src>"     "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_guided_drawing/intro.png"
cp "<chosen-rules-src>"     "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_guided_drawing/rules.png"
cp "<chosen-round_1-src>"   "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_guided_drawing/round_1.png"
cp "<chosen-round_2-src>"   "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_guided_drawing/round_2.png"
cp "<chosen-round_3-src>"   "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_guided_drawing/round_3.png"
cp "<chosen-celebrate-src>" "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_guided_drawing/celebrate.png"
cp "<chosen-closing-src>"   "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_guided_drawing/closing.png"
cp "<chosen-icon-src>"      "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_guided_drawing/icon.png"
```
- [ ] **Step: Draft the 3 item-sprite Codex prompts.** Item ids: `paper`, `pencil`, `drawing`. Use the ITEM template from Task 1 (verbatim style-contract paste + reference-image path + clean-white single-subject directives + hard constraints). SUBJECTS: paper = "a single sheet of blank paper, slight curl"; pencil = "a single colored pencil at a gentle angle"; drawing = "a finished simple child's drawing on a sheet". (`paper` and `drawing` carry `shape: rect3x4` per `SHAPES` in the builder — frame the subject for a 3:4 crop tolerance.)
- [ ] **Step: Generate item sprites via codex:codex-rescue.** Invoke `codex:codex-rescue` (foreground, `--write`) for each of the 3 item prompts; record output dirs.
- [ ] **Step: Inspect + select item candidates with the Read tool.** Read each; accept the best centered single-subject sprite on clean white, no black/colored padding, no text/border. Record chosen source path per item.
- [ ] **Step: Copy chosen item sprites into items/.**
```bash
cp "<chosen-paper-src>"   "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_guided_drawing/items/paper.png"
cp "<chosen-pencil-src>"  "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_guided_drawing/items/pencil.png"
cp "<chosen-drawing-src>" "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_guided_drawing/items/drawing.png"
```
> Note: as in Task 1, finished 512² sprites are placed in-place; Task 4 removes this pilot's stale `ITEM_CROPS` entries so the builder does not overwrite them.
- [ ] **Step: Build screen assets.** From repo root:
```bash
python3 scripts/build_activity_screen_assets.py
```
Confirm exit 0 and manifest rewrite. (Guided Drawing rounds keep `single`/`none`/`items:[]` per `test_representative_activity_layout_contracts_match_touchless_goal`; the builder's `plan_for` returns `choice2` for guided rounds in its table, but the test asserts the touchless `single` contract — confirm the build does not break that test in the next step; if it does, that contract drift is out of Stream 3 scope and must be flagged, not silently changed.)
- [ ] **Step: Run the asset contract test, expect guided items PASS.** From `backend/`:
```bash
uv run pytest ../tests/test_activity_text_game_asset_contract.py::test_manifest_item_assets_are_sized_and_not_black_padded -q
```
Expect PASS for the new guided item sprites. `test_activity_asset_manifest_matches_runtime_recipe_beats` still FAILs on `celebrate`/`closing` until Task 4 (expected).
- [ ] **Step: Human sign-off in the visual companion.** With the dev server running (from Task 1), open `/?view=activities`, select Guided Drawing, walk intro→rules→round_1..3→celebrate→closing and confirm each scene + item sprite reads on-style at lens size. Wait for explicit human approval before continuing.
- [ ] **Step: Commit.** `git add` the new guided-drawing PNGs + regenerated manifest, then:
```bash
git commit -m "feat(assets): regen guided drawing pilot art"
```

### Task 3: Phoneme Treasure Hunt (Cat5) — full beat scenes + synthesis + item sprites

**Files:**
- Create: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/{intro,rules,round_1,round_2,round_3,synthesis,celebrate,closing,icon}.png`
- Create: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/items/{ball,cup,book,banana,spoon,leaf,basket,toy_car,sock}.png`
- Modify: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity-assets.manifest.json:20-235` (regenerated by builder)
- Test: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/tests/test_activity_text_game_asset_contract.py`

> Note (factual-sources policy, spec §6): all phoneme assets are generic everyday objects (ball, cup, book, banana, spoon, leaf, basket, toy car, sock) and a generic treasure-hunt scene — permitted. The on-screen art must contain NO letters/numbers (the "B" phoneme is conveyed by object shapes, never a printed glyph), per the wording-leak constraint and the style "no letters/no text" rule.

- [ ] **Step: Draft the 8 scene Codex prompts (intro, rules, round_1..3, synthesis, celebrate, closing).** From `backend/games/activity_phoneme_treasure_hunt.md` (intro = open the B-word treasure hunt; rules = explain finding/naming words that start with the B sound, collecting one per round — convey by sound/objects, never a printed letter; round_1 = a scene cueing the round-1 trio ball/cup/book; round_2 = banana/spoon/leaf; round_3 = basket/toy_car/sock; synthesis = the collected B-treasures forming a tiny "word map"/chant; celebrate = award the treasure-hunt success; closing = warm goodbye). Use the SCENE template from Task 1 (verbatim style-contract paste + reference path + full-bleed directives + hard constraints, including explicit "no letters, no numbers"). SUBJECTS: intro = "a cozy flat-Nordic treasure-hunt nook with a small treasure chest, inviting mood (no letters)"; rules = "a loop motif: an ear/sound wave leading to a collected-treasure marker, calm explanatory mood (no letters)"; round_1 = "a soft shelf scene featuring a ball, a cup, and a book"; round_2 = "a soft tabletop scene featuring a banana, a spoon, and a leaf"; round_3 = "a soft scene featuring a basket, a toy car, and a sock"; synthesis = "three collected treasures (ball, book, banana) arranged in a tiny connected word-map / chain, celebratory-calm"; celebrate = "an open treasure chest glowing with the collected objects and confetti dashes, congratulatory mood"; closing = "a child waving goodbye beside the little treasure chest, gentle farewell mood".
- [ ] **Step: Generate scenes via codex:codex-rescue.** Invoke `codex:codex-rescue` (foreground, `--write`) for each of the 8 scene prompts; record output dirs. (Note: current `round_1/2/3.png` here are 2.1K placeholders — these scene regenerations replace them.)
- [ ] **Step: Inspect + select scene candidates with the Read tool.** Read each candidate; reject any with letters/numbers/text/border/vignette/black-corner/off-palette; accept the best on-style full-bleed square. Record chosen source path per beat.
- [ ] **Step: Copy chosen scenes into the pilot folder.**
```bash
cp "<chosen-intro-src>"     "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/intro.png"
cp "<chosen-rules-src>"     "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/rules.png"
cp "<chosen-round_1-src>"   "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/round_1.png"
cp "<chosen-round_2-src>"   "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/round_2.png"
cp "<chosen-round_3-src>"   "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/round_3.png"
cp "<chosen-synthesis-src>" "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/synthesis.png"
cp "<chosen-celebrate-src>" "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/celebrate.png"
cp "<chosen-closing-src>"   "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/closing.png"
cp "<chosen-icon-src>"      "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/icon.png"
```
- [ ] **Step: Draft the 9 item-sprite Codex prompts.** Item ids (the Cat5 collection + round sets per the manifest and `entity_registry`): `ball`, `cup`, `book`, `banana`, `spoon`, `leaf`, `basket`, `toy_car`, `sock`. Use the ITEM template from Task 1 (verbatim style-contract paste + reference path + clean-white single-subject directives + hard constraints, no letters/numbers). SUBJECTS are the literal objects, one centered per file: `ball` = "a soft round ball"; `cup` = "a simple cup"; `book` = "a closed book"; `banana` = "a single banana"; `spoon` = "a single spoon"; `leaf` = "a single leaf"; `basket` = "a small woven basket"; `toy_car` = "a simple toy car"; `sock` = "a single sock". All carry `shape: circle` (the manifest default), so frame each subject centered for circular cropping.
- [ ] **Step: Generate item sprites via codex:codex-rescue.** Invoke `codex:codex-rescue` (foreground, `--write`) for each of the 9 item prompts; record output dirs.
- [ ] **Step: Inspect + select item candidates with the Read tool.** Read each; accept the best centered single-subject sprite on clean white, no black/colored padding, no text/border. Record chosen source path per item.
- [ ] **Step: Copy chosen item sprites into items/.**
```bash
cp "<chosen-ball-src>"    "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/items/ball.png"
cp "<chosen-cup-src>"     "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/items/cup.png"
cp "<chosen-book-src>"    "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/items/book.png"
cp "<chosen-banana-src>"  "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/items/banana.png"
cp "<chosen-spoon-src>"   "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/items/spoon.png"
cp "<chosen-leaf-src>"    "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/items/leaf.png"
cp "<chosen-basket-src>"  "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/items/basket.png"
cp "<chosen-toy_car-src>" "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/items/toy_car.png"
cp "<chosen-sock-src>"    "/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity_phoneme_treasure_hunt/items/sock.png"
```
> Note: phoneme items are NOT in `ITEM_CROPS` (they are hand-supplied sprites already), so the builder leaves them untouched — placing finished 512² sprites here is authoritative as-is.
- [ ] **Step: Build screen assets.** From repo root:
```bash
python3 scripts/build_activity_screen_assets.py
```
Confirm exit 0 and manifest rewrite. Phoneme rounds keep `choice3`/`device-scroll`/3 items and synthesis keeps `carousel`/`none` per `plan_for` and the layout-contract test.
- [ ] **Step: Run the asset contract tests, expect phoneme item + Cat5 catalog PASS.** From `backend/`:
```bash
uv run pytest ../tests/test_activity_text_game_asset_contract.py::test_cat5_collection_catalog_images_exist ../tests/test_activity_text_game_asset_contract.py::test_manifest_item_assets_are_sized_and_not_black_padded ../tests/test_activity_text_game_asset_contract.py::test_phoneme_runtime_round_items_match_approved_touchless_sets -q
```
Expect PASS (Cat5 catalog images exist; item sprites 512² + no black edges; runtime round sets unchanged). `test_activity_asset_manifest_matches_runtime_recipe_beats` still FAILs on `celebrate`/`closing` until Task 4 (expected).
- [ ] **Step: Human sign-off in the visual companion.** With the dev server running, open `/?view=activities`, select Phoneme Treasure Hunt, walk intro→rules→round_1..3→synthesis→celebrate→closing and confirm scenes + item sprites read on-style with NO visible letters/numbers at lens size. Wait for explicit human approval before continuing.
- [ ] **Step: Commit.** `git add` the new phoneme PNGs + regenerated manifest, then:
```bash
git commit -m "feat(assets): regen phoneme hunt pilot art"
```

### Task 4: Update the asset contract test + builder for the new celebrate/closing beats

**Files:**
- Modify: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/tests/test_activity_text_game_asset_contract.py:32-39` (`_required_beat_ids`)
- Modify: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/scripts/build_activity_screen_assets.py:18-90` (drop stale pilot `ITEM_CROPS` so in-place sprites are not re-cropped)
- Test: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/tests/test_activity_text_game_asset_contract.py`

> Context: Stream 1 (separate workstream) adds the distinct `celebrate` and `closing` beats to the manifest, replacing the single collapsed `recap` for the three pilots; the contract test's `_required_beat_ids` currently emits `recap`. This task updates the test to the spec §4/§6 beat set so the regenerated assets validate. The required beat order becomes Cat1/Cat3: `intro, rules, round_1..N, celebrate, closing`; Cat5: `intro, rules, round_1..N, synthesis, celebrate, closing`.

> INTEGRATION NOTE: **Do NOT redefine `_required_beat_ids` here.** It is owned by Stream 1+2 Task 3, which already changes it to the **representative-gated** form (the 3 pilots require `intro, rules, round_1..N, [synthesis,] celebrate, closing`; the other 9 keep `recap`). Re-defining it here for *all* categories would wrongly require `celebrate`/`closing` on the untouched 9 activities. This Stream 3 task therefore performs ONLY the `ITEM_CROPS` removal + rebuild + validation below.
- [ ] **Step: Drop stale pilot ITEM_CROPS so in-place sprites survive the builder.** In `scripts/build_activity_screen_assets.py`, remove the `activity_career_decision_role_play` and `activity_guided_drawing` entries from the `ITEM_CROPS` dict (lines 24-31 and 43-47) so `build_items()` no longer re-crops those item sprites from scene art and clobbers the finished sprites copied in Tasks 1-2. Delete exactly these two blocks:
```python
    "activity_career_decision_role_play": {
        "alarm": ("round_1.png", (175, 45, 350, 210)),
        "phone": ("round_1.png", (300, 300, 485, 512)),
        "hose": ("round_2.png", (35, 190, 300, 430)),
        "oil": ("round_2.png", (315, 190, 512, 430)),
        "outside": ("round_3.png", (190, 175, 512, 430)),
        "firefighter": ("round_3.png", (0, 210, 190, 420)),
    },
```
and
```python
    "activity_guided_drawing": {
        "paper": ("round_1.png", (95, 95, 350, 315)),
        "pencil": ("round_2.png", (315, 145, 512, 420)),
        "drawing": ("round_3.png", (85, 85, 415, 390)),
    },
```
(Phoneme items were already absent from `ITEM_CROPS`, so no change there.)
- [ ] **Step: Rebuild and re-run the full asset contract suite, expect PASS.** From repo root then `backend/`:
```bash
python3 /Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/scripts/build_activity_screen_assets.py
cd /Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/backend && uv run pytest ../tests/test_activity_text_game_asset_contract.py -q
```
Expect all tests PASS: the manifest beat lists now match `intro, rules, round_1..3, [synthesis,] celebrate, closing`; every beat/item asset exists; item sprites are 512² with no black padding; Cat5 catalog images resolve. (This requires Stream 1's manifest celebrate/closing beats to be present; if they are not yet merged, the build step is the seam — coordinate with Stream 1 before expecting PASS.)
- [ ] **Step: Lint the changed Python.** From `backend/`:
```bash
uv run ruff check ../tests/test_activity_text_game_asset_contract.py ../scripts/build_activity_screen_assets.py
uv run ruff format --check ../tests/test_activity_text_game_asset_contract.py ../scripts/build_activity_screen_assets.py
```
Expect no errors.
- [ ] **Step: Commit.** `git add` the test + builder changes, then:
```bash
git commit -m "test(assets): assert celebrate and closing beats"
```

Key file paths referenced (all absolute):
- Spec: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/docs/plans/2026-05-29-pilot-flow-robustness-and-asset-regen.md`
- Style contract: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/prompts/wonderlens-activity-style.md`
- Reference image: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/prompts/style-reference-flat-nordic.png`
- Builder: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/scripts/build_activity_screen_assets.py`
- Manifest: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/frontend/public/activity-assets/activity-assets.manifest.json`
- Asset contract test: `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game/tests/test_activity_text_game_asset_contract.py`

---

## Stream 4 — Digital Crown scroll picker (layout A, vertical list)

> Frontend-isolated; may overlap Stream 3. One reusable CrownPicker across activity library + Cat3 Done/Help + Cat5 item picker.


### Task 1: Create CrownPicker component with vertical-list layout + ARIA

**Files:**
- Create: `frontend/src/activityGame/CrownPicker.jsx`
- Test: `frontend/tests/CrownPicker.test.jsx`

- [ ] **Step: Write the failing test** (real vitest + @testing-library/react test, globals enabled per `vitest.config.js`, matching `WonderLensDevice.test.jsx` imports and the `cssBlock` CSS-reading helper)

```jsx
// frontend/tests/CrownPicker.test.jsx
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { cwd } from 'node:process';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import CrownPicker from '../src/activityGame/CrownPicker.jsx';

const CSS = readFileSync(join(cwd(), 'src/index.css'), 'utf8');

function cssBlock(selector) {
  const start = CSS.indexOf(`${selector} {`);
  const end = CSS.indexOf('\n}', start);
  return CSS.slice(start, end);
}

const ITEMS = [
  { id: 'ball', label: 'Ball' },
  { id: 'basket', label: 'Basket' },
  { id: 'banana', label: 'Banana' },
];

describe('CrownPicker vertical-list layout', () => {
  it('renders a listbox with one option per item and marks the focused row', () => {
    render(<CrownPicker items={ITEMS} index={1} onStep={vi.fn()} onConfirm={vi.fn()} />);

    const listbox = screen.getByRole('listbox', { name: 'Crown picker' });
    expect(listbox).toBeTruthy();
    const options = screen.getAllByRole('option');
    expect(options).toHaveLength(3);
    expect(screen.getByRole('option', { name: 'Basket' }).getAttribute('aria-selected')).toBe('true');
    expect(screen.getByRole('option', { name: 'Ball' }).getAttribute('aria-selected')).toBe('false');
    expect(listbox.getAttribute('aria-activedescendant')).toBe('crown-picker-option-1');
  });

  it('classes the focused item as current and neighbors as adjacent rings', () => {
    render(<CrownPicker items={ITEMS} index={1} onStep={vi.fn()} onConfirm={vi.fn()} />);

    expect(screen.getByRole('option', { name: 'Basket' }).className).toContain('is-current');
    expect(screen.getByRole('option', { name: 'Ball' }).className).toContain('is-previous');
    expect(screen.getByRole('option', { name: 'Banana' }).className).toContain('is-next');
  });

  it('renders the arc scroll indicator and a green confirm control', () => {
    render(<CrownPicker items={ITEMS} index={0} onStep={vi.fn()} onConfirm={vi.fn()} />);

    expect(document.querySelector('.crown-picker__arc')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Select' })).toBeTruthy();
  });

  it('keeps the focused row centered/enlarged and neighbors scaled and faded in CSS', () => {
    expect(cssBlock('.crown-picker__option.is-current')).toContain('transform: scale(1)');
    expect(cssBlock('.crown-picker__option.is-current')).toContain('opacity: 1');
    expect(cssBlock('.crown-picker__option.is-previous')).toContain('scale(0.72)');
    expect(cssBlock('.crown-picker__option.is-next')).toContain('scale(0.72)');
    expect(cssBlock('.crown-picker__option.is-far')).toContain('scale(0.5)');
    expect(cssBlock('.crown-picker__option.is-adjacent')).toContain('opacity');
  });
});
```

- [ ] **Step: Run it, expect FAIL** (`cd frontend && npm run test -- CrownPicker` — expect `Failed to resolve import "../src/activityGame/CrownPicker.jsx"`)
- [ ] **Step: Minimal implementation** (real JSX component; vertical-list layout, ARIA listbox/option, arc indicator, green confirm — no animation logic yet)

```jsx
// frontend/src/activityGame/CrownPicker.jsx
const PICKER_ID = 'crown-picker';

function offsetClass(index, focusedIndex) {
  const delta = index - focusedIndex;
  if (delta === 0) return 'is-current';
  if (delta === -1) return 'is-adjacent is-previous';
  if (delta === 1) return 'is-adjacent is-next';
  return 'is-far';
}

export default function CrownPicker({
  items = [],
  index = 0,
  onStep,
  onConfirm,
  disabled = false,
  label = 'Crown picker',
  confirmLabel = 'Select',
}) {
  const total = items.length;
  const focusedIndex = total ? Math.max(0, Math.min(index, total - 1)) : 0;

  return (
    <div className="crown-picker" data-testid="crown-picker">
      <ul
        className="crown-picker__list"
        role="listbox"
        aria-label={label}
        aria-disabled={disabled ? 'true' : 'false'}
        aria-activedescendant={total ? `${PICKER_ID}-option-${focusedIndex}` : undefined}
      >
        {items.map((item, itemIndex) => (
          <li
            key={item.id || itemIndex}
            id={`${PICKER_ID}-option-${itemIndex}`}
            className={`crown-picker__option ${offsetClass(itemIndex, focusedIndex)}`}
            role="option"
            aria-selected={itemIndex === focusedIndex ? 'true' : 'false'}
          >
            {item.image || item.src ? (
              <img className="crown-picker__option-image" src={item.image || item.src} alt="" aria-hidden="true" />
            ) : null}
            <span className="crown-picker__option-label">{item.label || item.id || ''}</span>
          </li>
        ))}
      </ul>

      <span className="crown-picker__arc" aria-hidden="true" />

      <div className="crown-picker__controls">
        <button
          type="button"
          className="crown-picker__step crown-picker__step--up"
          aria-label="Previous item"
          disabled={disabled || total <= 1}
          onClick={() => onStep?.(-1)}
        />
        <button
          type="button"
          className="crown-picker__step crown-picker__step--down"
          aria-label="Next item"
          disabled={disabled || total <= 1}
          onClick={() => onStep?.(1)}
        />
        <button
          type="button"
          className="crown-picker__confirm"
          aria-label={confirmLabel}
          disabled={disabled || !total}
          onClick={() => onConfirm?.(focusedIndex)}
        >
          <span className="crown-picker__confirm-arrow" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
```

Then add the CSS block in `frontend/src/index.css` (append after the `.activity-screen-layout--picker` rules near line 611, before `.activity-screen-layout__item {`):

```css
.crown-picker {
  position: relative;
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
}

.crown-picker__list {
  position: relative;
  display: grid;
  grid-template-rows: repeat(5, minmax(0, 1fr));
  width: 78%;
  height: 84%;
  margin: 0;
  padding: 0;
  list-style: none;
  place-items: center;
}

.crown-picker__option {
  grid-area: 1 / 1 / -1 / -1;
  display: grid;
  place-items: center;
  width: 56%;
  opacity: 0;
  transform: scale(0.5);
  transition: opacity 180ms ease, transform 180ms ease;
}

.crown-picker__option-image {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 50%;
  object-fit: cover;
}

.crown-picker__option-label {
  margin-top: 0.32rem;
  color: oklch(0.96 0.01 150);
  font-size: 0.78rem;
  font-weight: 700;
  text-align: center;
}

.crown-picker__option.is-current {
  z-index: 3;
  opacity: 1;
  transform: scale(1);
}

.crown-picker__option.is-adjacent {
  z-index: 2;
  opacity: 0.55;
}

.crown-picker__option.is-previous {
  transform: translateY(-72%) scale(0.72);
}

.crown-picker__option.is-next {
  transform: translateY(72%) scale(0.72);
}

.crown-picker__option.is-far {
  opacity: 0;
  transform: scale(0.5);
}

.crown-picker__arc {
  position: absolute;
  right: 4%;
  top: 50%;
  width: 0.9rem;
  height: 56%;
  border-right: 0.18rem solid oklch(0.82 0.12 145 / 0.7);
  border-radius: 50%;
  transform: translateY(-50%);
}

.crown-picker__controls {
  display: contents;
}

.crown-picker__step {
  position: absolute;
  right: 0;
  width: 18%;
  height: 30%;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.crown-picker__step--up {
  top: 8%;
}

.crown-picker__step--down {
  bottom: 8%;
}

.crown-picker__step:disabled {
  cursor: not-allowed;
}

.crown-picker__confirm {
  position: absolute;
  bottom: 4%;
  left: 50%;
  display: grid;
  place-items: center;
  width: 2.2rem;
  height: 2.2rem;
  border: 0;
  border-radius: 50%;
  background: linear-gradient(96deg, oklch(0.62 0.13 145), oklch(0.57 0.11 145));
  cursor: pointer;
  transform: translateX(-50%);
}

.crown-picker__confirm:disabled {
  cursor: not-allowed;
  filter: grayscale(0.6);
  opacity: 0.5;
}

.crown-picker__confirm-arrow {
  width: 0.7rem;
  height: 0.7rem;
  border-color: oklch(0.99 0.02 145);
  border-style: solid;
  border-width: 0.16rem 0.16rem 0 0;
  transform: rotate(45deg);
}

.crown-picker__step:focus-visible,
.crown-picker__confirm:focus-visible {
  outline: 0.2rem solid oklch(0.7 0.14 170);
  outline-offset: 0.22rem;
}
```

- [ ] **Step: Run it, expect PASS** (`cd frontend && npm run test -- CrownPicker`)
- [ ] **Step: Commit** (`feat(crown): add vertical-list crown picker`)

---

### Task 2: Add crown step + momentum + detent-settle interaction

**Files:**
- Modify: `frontend/src/activityGame/CrownPicker.jsx`
- Test: `frontend/tests/CrownPicker.test.jsx`

- [ ] **Step: Write the failing test** (append a new `describe` to `frontend/tests/CrownPicker.test.jsx`; uses fake timers + `requestAnimationFrame` stub to drive momentum, matching the rAF usage already in the repo)

```jsx
describe('CrownPicker crown interaction', () => {
  it('steps focus by one detent per click via onStep', () => {
    const onStep = vi.fn();
    render(<CrownPicker items={ITEMS} index={1} onStep={onStep} onConfirm={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Next item' }));
    expect(onStep).toHaveBeenLastCalledWith(1);

    fireEvent.click(screen.getByRole('button', { name: 'Previous item' }));
    expect(onStep).toHaveBeenLastCalledWith(-1);
  });

  it('settles momentum onto the nearest detent with one onStep per click', () => {
    vi.useFakeTimers();
    let rafId = 0;
    const callbacks = new Map();
    vi.stubGlobal('requestAnimationFrame', (cb) => {
      rafId += 1;
      callbacks.set(rafId, cb);
      return rafId;
    });
    vi.stubGlobal('cancelAnimationFrame', (id) => callbacks.delete(id));

    const onStep = vi.fn();
    render(<CrownPicker items={ITEMS} index={0} onStep={onStep} onConfirm={vi.fn()} />);

    const down = screen.getByRole('button', { name: 'Next item' });
    fireEvent.wheel(down, { deltaY: 240 });
    // Drain queued animation frames to let momentum decay and settle.
    for (let frame = 0; frame < 30 && callbacks.size; frame += 1) {
      const [[id, cb]] = callbacks;
      callbacks.delete(id);
      cb(performance.now());
    }

    expect(onStep).toHaveBeenCalled();
    onStep.mock.calls.forEach(([delta]) => {
      expect([1, -1]).toContain(delta);
    });

    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('does not fire onStep while disabled', () => {
    const onStep = vi.fn();
    render(<CrownPicker items={ITEMS} index={1} onStep={onStep} onConfirm={vi.fn()} disabled />);

    expect(screen.getByRole('button', { name: 'Next item' }).disabled).toBe(true);
    fireEvent.wheel(screen.getByTestId('crown-picker'), { deltaY: 240 });
    expect(onStep).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step: Run it, expect FAIL** (`cd frontend && npm run test -- CrownPicker` — expect the momentum test to fail because `wheel` produces no `onStep` calls)
- [ ] **Step: Minimal implementation** (add momentum accumulator + rAF eased decay that fires one `onStep(±1)` per crossed detent; respect `disabled`; mirror the `prefersReducedMotion()` helper convention from `ActivityTranscript.jsx`)

Add the imports and helpers at the top of `frontend/src/activityGame/CrownPicker.jsx`:

```jsx
import { useCallback, useEffect, useRef } from 'react';

const DETENT_THRESHOLD = 80;
const MOMENTUM_DECAY = 0.82;
const MOMENTUM_MIN = 8;

function prefersReducedMotion() {
  return typeof window !== 'undefined'
    && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
}
```

Note: the import line above is `import { useCallback, useEffect, useRef } from 'react';` — correct the casing when applying. Replace the function signature/body to wire momentum:

```jsx
export default function CrownPicker({
  items = [],
  index = 0,
  onStep,
  onConfirm,
  disabled = false,
  label = 'Crown picker',
  confirmLabel = 'Select',
}) {
  const total = items.length;
  const focusedIndex = total ? Math.max(0, Math.min(index, total - 1)) : 0;
  const velocityRef = useRef(0);
  const accumulatorRef = useRef(0);
  const frameRef = useRef(0);
  const onStepRef = useRef(onStep);
  onStepRef.current = onStep;

  const stopMomentum = useCallback(() => {
    if (frameRef.current) {
      window.cancelAnimationFrame(frameRef.current);
      frameRef.current = 0;
    }
    velocityRef.current = 0;
    accumulatorRef.current = 0;
  }, []);

  const drainDetents = useCallback(() => {
    while (Math.abs(accumulatorRef.current) >= DETENT_THRESHOLD) {
      const direction = accumulatorRef.current > 0 ? 1 : -1;
      accumulatorRef.current -= direction * DETENT_THRESHOLD;
      onStepRef.current?.(direction);
    }
  }, []);

  const settle = useCallback(() => {
    velocityRef.current *= MOMENTUM_DECAY;
    accumulatorRef.current += velocityRef.current;
    drainDetents();
    if (Math.abs(velocityRef.current) > MOMENTUM_MIN) {
      frameRef.current = window.requestAnimationFrame(settle);
    } else {
      accumulatorRef.current = 0;
      velocityRef.current = 0;
      frameRef.current = 0;
    }
  }, [drainDetents]);

  const handleWheel = useCallback((event) => {
    if (disabled || total <= 1) return;
    accumulatorRef.current += event.deltaY;
    drainDetents();
    if (prefersReducedMotion()) {
      accumulatorRef.current = 0;
      return;
    }
    velocityRef.current = event.deltaY;
    if (!frameRef.current) {
      frameRef.current = window.requestAnimationFrame(settle);
    }
  }, [disabled, drainDetents, settle, total]);

  const step = useCallback((direction) => {
    if (disabled || total <= 1) return;
    stopMomentum();
    onStepRef.current?.(direction);
  }, [disabled, stopMomentum, total]);

  useEffect(() => stopMomentum, [stopMomentum]);

  return (
    <div className="crown-picker" data-testid="crown-picker" onWheel={handleWheel}>
      <ul
        className="crown-picker__list"
        role="listbox"
        aria-label={label}
        aria-disabled={disabled ? 'true' : 'false'}
        aria-activedescendant={total ? `${PICKER_ID}-option-${focusedIndex}` : undefined}
      >
        {items.map((item, itemIndex) => (
          <li
            key={item.id || itemIndex}
            id={`${PICKER_ID}-option-${itemIndex}`}
            className={`crown-picker__option ${offsetClass(itemIndex, focusedIndex)}`}
            role="option"
            aria-selected={itemIndex === focusedIndex ? 'true' : 'false'}
          >
            {item.image || item.src ? (
              <img className="crown-picker__option-image" src={item.image || item.src} alt="" aria-hidden="true" />
            ) : null}
            <span className="crown-picker__option-label">{item.label || item.id || ''}</span>
          </li>
        ))}
      </ul>

      <span className="crown-picker__arc" aria-hidden="true" />

      <div className="crown-picker__controls">
        <button
          type="button"
          className="crown-picker__step crown-picker__step--up"
          aria-label="Previous item"
          disabled={disabled || total <= 1}
          onClick={() => step(-1)}
        />
        <button
          type="button"
          className="crown-picker__step crown-picker__step--down"
          aria-label="Next item"
          disabled={disabled || total <= 1}
          onClick={() => step(1)}
        />
        <button
          type="button"
          className="crown-picker__confirm"
          aria-label={confirmLabel}
          disabled={disabled || !total}
          onClick={() => onConfirm?.(focusedIndex)}
        >
          <span className="crown-picker__confirm-arrow" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step: Run it, expect PASS** (`cd frontend && npm run test -- CrownPicker`)
- [ ] **Step: Commit** (`feat(crown): add momentum detent settle`)

---

### Task 3: Add confirm callback, disabled-during-selection, keyboard (ArrowUp/Down + Enter), and reduced-motion

**Files:**
- Modify: `frontend/src/activityGame/CrownPicker.jsx`
- Test: `frontend/tests/CrownPicker.test.jsx`

- [ ] **Step: Write the failing test** (append a new `describe` to `frontend/tests/CrownPicker.test.jsx` covering confirm, keyboard mapping, disabled confirm, and reduced-motion synchronous stepping)

```jsx
describe('CrownPicker confirm, keyboard, and accessibility', () => {
  it('fires onConfirm with the focused index when the green control is pressed', () => {
    const onConfirm = vi.fn();
    render(<CrownPicker items={ITEMS} index={2} onStep={vi.fn()} onConfirm={onConfirm} />);

    fireEvent.click(screen.getByRole('button', { name: 'Select' }));
    expect(onConfirm).toHaveBeenCalledWith(2);
  });

  it('maps ArrowDown/ArrowUp to step and Enter to confirm', () => {
    const onStep = vi.fn();
    const onConfirm = vi.fn();
    render(<CrownPicker items={ITEMS} index={1} onStep={onStep} onConfirm={onConfirm} />);

    const listbox = screen.getByRole('listbox', { name: 'Crown picker' });
    fireEvent.keyDown(listbox, { key: 'ArrowDown' });
    expect(onStep).toHaveBeenLastCalledWith(1);
    fireEvent.keyDown(listbox, { key: 'ArrowUp' });
    expect(onStep).toHaveBeenLastCalledWith(-1);
    fireEvent.keyDown(listbox, { key: 'Enter' });
    expect(onConfirm).toHaveBeenCalledWith(1);
  });

  it('exposes a keyboard-focusable listbox and ignores keys while disabled', () => {
    const onStep = vi.fn();
    const onConfirm = vi.fn();
    render(<CrownPicker items={ITEMS} index={1} onStep={onStep} onConfirm={onConfirm} disabled />);

    const listbox = screen.getByRole('listbox', { name: 'Crown picker' });
    expect(listbox.getAttribute('tabindex')).toBe('-1');
    expect(screen.getByRole('button', { name: 'Select' }).disabled).toBe(true);
    fireEvent.keyDown(listbox, { key: 'ArrowDown' });
    fireEvent.keyDown(listbox, { key: 'Enter' });
    expect(onStep).not.toHaveBeenCalled();
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it('steps synchronously without momentum when reduced motion is preferred', () => {
    const matchMediaSpy = vi.fn(() => ({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() }));
    vi.stubGlobal('matchMedia', matchMediaSpy);
    const rafSpy = vi.fn();
    vi.stubGlobal('requestAnimationFrame', rafSpy);

    const onStep = vi.fn();
    render(<CrownPicker items={ITEMS} index={0} onStep={onStep} onConfirm={vi.fn()} />);

    fireEvent.wheel(screen.getByTestId('crown-picker'), { deltaY: 160 });
    expect(onStep).toHaveBeenCalledTimes(2);
    expect(rafSpy).not.toHaveBeenCalled();

    vi.unstubAllGlobals();
  });
});
```

- [ ] **Step: Run it, expect FAIL** (`cd frontend && npm run test -- CrownPicker` — expect the keyboard test to fail: `keyDown` does nothing because no `onKeyDown` handler / `tabIndex` exists yet)
- [ ] **Step: Minimal implementation** (add `tabIndex={-1}` and `onKeyDown` to the listbox; reuse the `step`/`onConfirm` already defined)

Add the keyboard handler inside `CrownPicker` (after the `step` callback, before `useEffect`):

```jsx
  const handleKeyDown = useCallback((event) => {
    if (disabled) return;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      step(1);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      step(-1);
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      if (total) onConfirm?.(focusedIndex);
    }
  }, [disabled, focusedIndex, onConfirm, step, total]);
```

Update the `<ul>` opening tag to be keyboard-focusable and wire the handler:

```jsx
      <ul
        className="crown-picker__list"
        role="listbox"
        aria-label={label}
        aria-disabled={disabled ? 'true' : 'false'}
        aria-activedescendant={total ? `${PICKER_ID}-option-${focusedIndex}` : undefined}
        tabIndex={-1}
        onKeyDown={handleKeyDown}
      >
```

- [ ] **Step: Run it, expect PASS** (`cd frontend && npm run test -- CrownPicker`)
- [ ] **Step: Commit** (`feat(crown): add keyboard and confirm a11y`)

---

### Task 4: Integrate CrownPicker into the activity-library surface in ActivityGameApp

**Files:**
- Modify: `frontend/src/activityGame/ActivityGameApp.jsx` (render path around `WonderLensDevice`, lines 308-327; wiring `selectRelativeActivity`/`handleStart`)
- Test: `frontend/tests/ActivityGameApp.test.jsx`

- [ ] **Step: Write the failing test** (append to the existing `describe('ActivityGameApp', ...)` in `frontend/tests/ActivityGameApp.test.jsx`, reusing the file's existing `vi.mock('../src/utils/api.js', ...)`)

```jsx
  it('uses a crown picker to browse and start activities from the library', async () => {
    render(<ActivityGameApp />);

    expect(await screen.findByRole('heading', { name: 'Word Echo Practice' })).toBeTruthy();
    const listbox = screen.getByRole('listbox', { name: 'Crown picker' });
    expect(listbox).toBeTruthy();
    expect(screen.getByRole('option', { name: 'Word Echo Practice' }).getAttribute('aria-selected')).toBe('true');

    fireEvent.keyDown(listbox, { key: 'ArrowDown' });
    expect(screen.getByRole('heading', { name: 'Animal Sound Imitation' })).toBeTruthy();
    expect(screen.getByRole('option', { name: 'Animal Sound Imitation' }).getAttribute('aria-selected')).toBe('true');

    fireEvent.keyDown(listbox, { key: 'ArrowUp' });
    expect(screen.getByRole('heading', { name: 'Word Echo Practice' })).toBeTruthy();
  });
```

- [ ] **Step: Run it, expect FAIL** (`cd frontend && npm run test -- ActivityGameApp` — expect `Unable to find an accessible element with the role "listbox" and name "Crown picker"`)
- [ ] **Step: Minimal implementation** (render `CrownPicker` in `ActivityGameApp.jsx`; build a `crownItems`/`crownIndex`/`crownStep`/`crownConfirm` that switch per surface — library mode here, Cat3/Cat5 in Tasks 5-6)

Add the import at the top of `frontend/src/activityGame/ActivityGameApp.jsx` (after the existing `ActivityLibrary` import on line 4):

```jsx
import CrownPicker from './CrownPicker.jsx';
```

Add the library crown model after `handlePrimaryAction` (line 267) and before `return (`:

```jsx
  const libraryItems = useMemo(
    () => activities.map((activity) => ({ id: activity.id, label: activity.name })),
    [activities],
  );
  const libraryIndex = Math.max(0, activities.findIndex((activity) => activity.id === selectedActivity?.id));

  const crownItems = showCat3Build
    ? cat3Options.map((option) => ({ id: option.value, label: option.label }))
    : showCat5Selection
      ? currentRoundItems.map((item) => ({ id: item.id, label: item.label, image: item.image }))
      : libraryItems;
  const crownIndex = showCat3Build
    ? cat3OptionIndex
    : showCat5Selection
      ? activeCat5ItemIndex
      : libraryIndex;
  const crownDisabled = isDeviceOptionMode
    ? loading || turnPending
    : sessionActive || loading || catalogLoading;
  const crownStep = useCallback((direction) => {
    if (showCat3Build) selectCat3Option(direction);
    else if (showCat5Selection) selectCat5Item(direction);
    else selectRelativeActivity(direction);
  }, [selectCat3Option, selectCat5Item, selectRelativeActivity, showCat3Build, showCat5Selection]);
  const crownConfirm = useCallback(() => {
    if (showCat3Build) void confirmCat3Option();
    else if (showCat5Selection) void confirmCat5Item();
    else void handleStart();
  }, [confirmCat3Option, confirmCat5Item, handleStart, showCat3Build, showCat5Selection]);
```

Render `CrownPicker` immediately before the `<WonderLensDevice ...>` element (inside `.activity-game__device`, after the closing `</div>` of `.activity-game__section-head` on line 307):

```jsx
          <CrownPicker
            items={crownItems}
            index={crownIndex}
            onStep={crownStep}
            onConfirm={crownConfirm}
            disabled={crownDisabled}
            confirmLabel={isDeviceOptionMode ? 'Select' : 'Start'}
          />
```

- [ ] **Step: Run it, expect PASS** (`cd frontend && npm run test -- ActivityGameApp`)
- [ ] **Step: Commit** (`feat(crown): wire library surface to crown picker`)

---

### Task 5: Wire the Cat3 Done/Help surface through the crown picker

**Files:**
- Modify: `frontend/src/activityGame/ActivityGameApp.jsx` (already-defined `crownItems`/`crownStep`/`crownConfirm` Cat3 branch)
- Test: `frontend/tests/ActivityGameApp.test.jsx`

- [ ] **Step: Write the failing test** (append to `describe('ActivityGameApp', ...)`; reuses the file's existing Cat3 `startActivitySession`/`sendTurn` mock shape from the "uses physical device controls for Cat3 build quick actions" test)

```jsx
  it('drives Cat3 Done/Help through the crown picker', async () => {
    vi.mocked(startActivitySession).mockResolvedValue({
      session_id: 'cat3',
      activity_type: 'activity_guided_drawing',
      template_type: 'cat3',
      session_state: {
        status: 'active',
        template_type: 'cat3',
        current_step: 'STEP_3_BUILD_1',
        current_round: 1,
        total_rounds: 3,
        current_build_step: 'Draw one simple line or shape to start the picture.',
        build_materials: ['paper', 'pencil'],
      },
      first_turn: { dialogue: 'Make the first mark.', response_type: 'round' },
    });
    vi.mocked(sendTurn).mockResolvedValue({
      session_state: {
        status: 'active',
        template_type: 'cat3',
        current_step: 'STEP_3_BUILD_1',
        current_round: 1,
        total_rounds: 3,
        current_build_step: 'Draw one simple line or shape to start the picture.',
        build_materials: ['paper', 'pencil'],
      },
      turn: { dialogue: 'I can help with that step.', response_type: 'round' },
    });

    render(<ActivityGameApp />);

    fireEvent.click(await screen.findByRole('button', { name: /Guided Drawing/i }));
    fireEvent.click(screen.getByLabelText('Start activity'));

    const listbox = await screen.findByRole('listbox', { name: 'Crown picker' });
    expect(screen.getByRole('option', { name: 'Done' }).getAttribute('aria-selected')).toBe('true');

    fireEvent.keyDown(listbox, { key: 'ArrowDown' });
    expect(screen.getByRole('option', { name: 'Help' }).getAttribute('aria-selected')).toBe('true');

    fireEvent.keyDown(listbox, { key: 'Enter' });
    expect(vi.mocked(sendTurn)).toHaveBeenCalledWith('cat3', 'help', false);
    expect(await screen.findByText('I can help with that step.')).toBeTruthy();
  });
```

- [ ] **Step: Run it, expect FAIL** (`cd frontend && npm run test -- ActivityGameApp` — expect failure: the Cat3 crown options have stale `index` because `crownIndex` reads `cat3OptionIndex` but the listbox is the old `Cat3BuildPanel`, so `getByRole('listbox', { name: 'Crown picker' })` resolves to the wrong/missing node or selection does not advance)
- [ ] **Step: Minimal implementation** (confirm the Cat3 branch is live: the `crownItems`/`crownIndex`/`crownStep`/`crownConfirm` already handle `showCat3Build` from Task 4; remove the now-redundant in-lens `Cat3BuildPanel` interaction so the crown picker is the single selection surface)

In `frontend/src/activityGame/ActivityGameApp.jsx`, drop the `lensInteraction` Cat3 wiring so the crown picker owns Done/Help. Replace lines 198-203:

```jsx
  const lensInteraction = null;
```

The Cat3 branch of `crownItems`/`crownIndex`/`crownStep`/`crownConfirm` from Task 4 already routes to `cat3Options`, `cat3OptionIndex`, `selectCat3Option`, and `confirmCat3Option`. No further change needed; the `useEffect` on line 209-211 still resets `cat3OptionIndex` per step.

- [ ] **Step: Run it, expect PASS** (`cd frontend && npm run test -- ActivityGameApp` — also confirm the pre-existing "uses physical device controls for Cat3 build quick actions" test still passes, since it reads the same `option` roles)
- [ ] **Step: Commit** (`feat(crown): route cat3 done help via crown picker`)

---

### Task 6: Wire the Cat5 item picker through the crown picker

**Files:**
- Modify: `frontend/src/activityGame/ActivityGameApp.jsx` (Cat5 branch of crown model; `screenLayout` selection coupling)
- Test: `frontend/tests/ActivityGameApp.test.jsx`

- [ ] **Step: Write the failing test** (append to `describe('ActivityGameApp', ...)`; reuses the existing Cat5 mock shape from the "uses physical device controls for Cat5 collection item selection" test)

```jsx
  it('drives Cat5 item selection through the crown picker', async () => {
    vi.mocked(startActivitySession).mockResolvedValue({
      session_id: 'cat5',
      activity_type: 'activity_phoneme_treasure_hunt',
      template_type: 'cat5',
      session_state: {
        status: 'active',
        template_type: 'cat5',
        current_step: 'STEP_3_COLLECT_1',
        current_round: 1,
        total_rounds: 3,
        collection_phase: 'photo',
        collected_photos: [],
        current_round_items: [
          { id: 'ball', label: 'Ball', image: '/activity-assets/activity_phoneme_treasure_hunt/items/ball.png' },
          { id: 'cup', label: 'Cup', image: '/activity-assets/activity_phoneme_treasure_hunt/items/cup.png' },
          { id: 'book', label: 'Book', image: '/activity-assets/activity_phoneme_treasure_hunt/items/book.png' },
        ],
      },
      first_turn: { dialogue: 'Pick the B word.', response_type: 'round' },
    });
    vi.mocked(sendTurn).mockResolvedValue({
      session_state: {
        status: 'active',
        template_type: 'cat5',
        current_step: 'STEP_3_COLLECT_1',
        current_round: 1,
        total_rounds: 3,
        collection_phase: 'detail',
        collected_photos: ['cup'],
      },
      turn: { dialogue: 'Cup it is.', response_type: 'detail' },
    });

    render(<ActivityGameApp />);

    fireEvent.click(await screen.findByRole('button', { name: /Phoneme Treasure Hunt/i }));
    fireEvent.click(screen.getByLabelText('Start activity'));

    const listbox = await screen.findByRole('listbox', { name: 'Crown picker' });
    expect(screen.getByRole('option', { name: 'Ball' }).getAttribute('aria-selected')).toBe('true');

    fireEvent.keyDown(listbox, { key: 'ArrowDown' });
    expect(screen.getByRole('option', { name: 'Cup' }).getAttribute('aria-selected')).toBe('true');

    fireEvent.keyDown(listbox, { key: 'Enter' });
    expect(vi.mocked(sendTurn)).toHaveBeenCalledWith('cat5', '', false, 'cup');
    expect(await screen.findByText('Cup it is.')).toBeTruthy();
  });
```

- [ ] **Step: Run it, expect FAIL** (`cd frontend && npm run test -- ActivityGameApp` — expect `sendTurn` to be called with `'ball'` not `'cup'`: `confirmCat5Item` (line 245-249) hardcodes `activeCat5ItemIndex` but the crown's `onConfirm(focusedIndex)` passes the focused index, which is not yet threaded through)
- [ ] **Step: Minimal implementation** (make `crownConfirm` use the index argument from `CrownPicker.onConfirm` for Cat5; extend `confirmCat5Item` to accept an explicit index)

In `frontend/src/activityGame/ActivityGameApp.jsx`, change `confirmCat5Item` (lines 245-249) to accept an index:

```jsx
  const confirmCat5Item = useCallback(async (itemIndex = activeCat5ItemIndex) => {
    const item = currentRoundItems[itemIndex] || currentRoundItems[0];
    if (!item || loading || turnPending) return;
    await sendCollectionItem(item.id, item.label);
  }, [activeCat5ItemIndex, currentRoundItems, loading, sendCollectionItem, turnPending]);
```

Update `crownConfirm` (from Task 4) to forward the focused index for Cat5:

```jsx
  const crownConfirm = useCallback((focusedIndex) => {
    if (showCat3Build) void confirmCat3Option();
    else if (showCat5Selection) void confirmCat5Item(focusedIndex);
    else void handleStart();
  }, [confirmCat3Option, confirmCat5Item, handleStart, showCat3Build, showCat5Selection]);
```

Keep `selectCat5Item` driving `cat5ItemIndex` so the on-screen `screenLayout` picker (lines 188-197) stays visually in sync with the crown focus via `displayedCat5ItemIndex`.

- [ ] **Step: Run it, expect PASS** (`cd frontend && npm run test -- ActivityGameApp` — also confirm pre-existing Cat5 tests at lines 130-290 still pass, since `Next/Previous device option` buttons remain wired through `selectCat5Item`)
- [ ] **Step: Commit** (`feat(crown): route cat5 item picker via crown`)

---

### Task 7: Review, simplify, and full-suite verification

**Files:**
- Modify: `frontend/src/activityGame/CrownPicker.jsx`, `frontend/src/activityGame/ActivityGameApp.jsx`, `frontend/src/index.css` (cleanup only)
- Test: `frontend/tests/CrownPicker.test.jsx`, `frontend/tests/ActivityGameApp.test.jsx`, `frontend/tests/WonderLensDevice.test.jsx`

- [ ] **Step: Run the full frontend suite, expect PASS** (`cd frontend && npm run test` — all CrownPicker, ActivityGameApp, and WonderLensDevice tests green, including the pre-existing Cat3/Cat5 device-control tests)
- [ ] **Step: Run the linter, expect clean** (`cd frontend && npm run lint` — fix any unused-import or hooks-deps warnings; no suppression comments)
- [ ] **Step: Launch code-reviewer + code-simplifier** (per project rule: review the CrownPicker component and the ActivityGameApp crown-model wiring in parallel; apply only safe reductions — e.g. collapse the three-way ternaries into one surface-selector object if a reviewer flags duplication)
- [ ] **Step: Re-run the full suite after simplification, expect PASS** (`cd frontend && npm run test`)
- [ ] **Step: Commit** (`refactor(crown): simplify surface selection`)