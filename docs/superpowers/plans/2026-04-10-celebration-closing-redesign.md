# Celebration & Closing Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign Cat5 celebrate/closing so the device panel expands to full viewport, the achievement image no longer gets cut off, and IB concepts are surfaced as large circular medallions using existing badge PNGs.

**Architecture:** Stage mode = CSS class on `<main>` derived from `current_step`. Celebrate keeps `achievement_image` widget (simplified). Closing uses a new `concept_reveal` widget with `ConceptMedallion` children. Backend splits the Cat5 celebrate/closing branch in `state_machine.py` into two distinct widgets and fixes a latent bug in the directive celebrate handler (state was being advanced before the screen frame was snapshotted).

**Tech Stack:** React 19 + Tailwind v4 + Vite frontend. Python 3.12 + FastAPI + Pydantic v2 backend. pytest for backend tests (no frontend test framework — verification via `npm run lint` + `npm run build`).

**Spec:** [`docs/superpowers/specs/2026-04-10-celebration-closing-redesign.md`](../specs/2026-04-10-celebration-closing-redesign.md)

---

## Conventions for this plan

- All `uv run pytest` commands run from the repo root (`.worktrees/feat/edu-content-feedback/`). Test files live in `tests/`, not `backend/tests/`.
- All `uv run ruff`, `uv run mypy` commands run from `backend/`.
- All `npm run` commands run from `frontend/`.
- Commits follow conventional format: `feat(scope):`, `fix(scope):`, `refactor(scope):`, `test(scope):`. Keep first line under 50 chars.
- After every task, the task's test commands must pass before committing.
- Never mention Claude as code generator or co-author in commits.

---

## File structure overview

**New files:**
- `frontend/src/widgets/FallbackTrophy.jsx` — extracted gradient-circle fallback from `AchievementImage`
- `frontend/src/widgets/ConceptMedallion.jsx` — single circular medallion with PNG + name pill + star accent
- `frontend/src/widgets/ConceptReveal.jsx` — closing-step widget: title + medallion row + role line
- `frontend/src/components/StageModeFooter.jsx` — 48px footer strip shown during stage mode

**Modified files:**
- `backend/state_machine.py` — split Cat5 celebrate/closing branch into two widgets
- `backend/turn_handling/directive.py` — two edits: celebrate snapshot (critical) + closing widget override for Cat5
- `frontend/src/widgets/AchievementImage.jsx` — simplified: no concepts, no character names, use `FallbackTrophy`
- `frontend/src/components/DeviceScreen.jsx` — register `concept_reveal` in `WIDGET_MAP` and full-panel widget list
- `frontend/src/App.jsx` — derive `stageMode`, apply class, conditional footer
- `frontend/src/index.css` — stage mode CSS rules

**New test files:**
- None — existing `tests/test_state_machine.py` and `tests/test_turn_handler.py` get new tests added to them.

---

## Task 1: Split Cat5 celebrate/closing widgets in state_machine.py

**Files:**
- Test: `tests/test_state_machine.py` (append)
- Modify: `backend/state_machine.py` (the Cat5 celebrate/closing branch around line 325)

### - [ ] Step 1.1: Read the current state_machine.py branch

Run: `grep -n "STEP_5_CELEBRATE\|STEP_6_CLOSING\|achievement_image" backend/state_machine.py`

Expected: you'll see one branch that handles both STEP_5_CELEBRATE and STEP_6_CLOSING together, returning `widget="achievement_image"`, with a conditional `if step == "STEP_6_CLOSING": widget_params["concepts"] = key_concepts`. This is the block to split.

### - [ ] Step 1.2: Add failing tests for the split behavior

Append to `tests/test_state_machine.py`:

```python
from schemas.structured_story import StructuredStory


def test_cat5_celebrate_returns_achievement_image_without_concepts():
    """STEP_5_CELEBRATE should render achievement_image with title only, no concepts."""
    slots = _cat5_slots()
    context = {
        "entity_name": "ladybug",
        "ib_key_concepts": ["Form", "Connection"],
        "collection_phase": "photo",
        "collected_photos": ["speckled_leaf", "circle_flower"],
        "collected_names": [],
        "collected_details": ["big dots", "small dots"],
        "structured_story": None,
        "round_items": [],
    }

    frame = get_screen_frame("STEP_5_CELEBRATE", "cat5", slots, context)

    assert frame.widget == "achievement_image"
    assert frame.widget_params["title"] == "Shape Specialist"
    assert "concepts" not in frame.widget_params, (
        "celebrate should NOT include IB concepts — those belong to closing"
    )
    assert "image_data_url" not in frame.widget_params, (
        "no structured_story in context means no image URL"
    )
    assert frame.animation == "badge_reveal"
    assert frame.sfx_cue == "badge_awarded"


def test_cat5_celebrate_includes_image_when_structured_story_has_achievement_url():
    """When structured_story has an achievement image URL, celebrate passes it through."""
    slots = _cat5_slots()
    structured = StructuredStory(
        scenes=[],
        achievement_description="",
        achievement_image_data_url="data:image/png;base64,FAKE",
    )
    context = {
        "entity_name": "ladybug",
        "ib_key_concepts": ["Form", "Connection"],
        "collection_phase": "photo",
        "collected_photos": ["speckled_leaf"],
        "collected_names": [],
        "collected_details": [],
        "structured_story": structured,
        "round_items": [],
    }

    frame = get_screen_frame("STEP_5_CELEBRATE", "cat5", slots, context)

    assert frame.widget == "achievement_image"
    assert frame.widget_params["image_data_url"] == "data:image/png;base64,FAKE"
    assert "concepts" not in frame.widget_params


def test_cat5_closing_returns_concept_reveal_with_concepts():
    """STEP_6_CLOSING should render concept_reveal widget with concepts, no image."""
    slots = _cat5_slots()
    context = {
        "entity_name": "ladybug",
        "ib_key_concepts": ["Form", "Connection"],
        "collection_phase": "photo",
        "collected_photos": ["speckled_leaf"],
        "collected_names": [],
        "collected_details": [],
        "structured_story": None,
        "round_items": [],
    }

    frame = get_screen_frame("STEP_6_CLOSING", "cat5", slots, context)

    assert frame.widget == "concept_reveal"
    assert frame.widget_params["title"] == "Shape Specialist"
    assert frame.widget_params["concepts"] == ["Form", "Connection"]
    assert "image_data_url" not in frame.widget_params, (
        "closing is concept-focused — no image"
    )
    assert frame.animation == "badge_reveal"
    assert frame.sfx_cue == "celebration_fanfare"


def test_cat1_closing_unchanged():
    """Cat1 closing path must not be affected by the Cat5 split."""
    slots = _cat1_slots()
    context = {
        "entity_name": "dog",
        "ib_key_concepts": ["Perspective"],
        "collection_phase": "photo",
        "collected_photos": [],
        "collected_names": [],
        "collected_details": [],
        "structured_story": None,
        "round_items": [],
    }

    frame = get_screen_frame("STEP_5_CLOSING", "cat1", slots, context)

    # Cat1 uses STEP_5_CLOSING (not STEP_6) and its own badge_award widget
    assert frame.widget == "badge_award"
    assert frame.widget_params["title"] == "IB Concepts"
    assert frame.widget_params["concepts"] == ["Perspective"]
```

### - [ ] Step 1.3: Run tests to verify they fail

Run: `uv run pytest tests/test_state_machine.py::test_cat5_celebrate_returns_achievement_image_without_concepts tests/test_state_machine.py::test_cat5_celebrate_includes_image_when_structured_story_has_achievement_url tests/test_state_machine.py::test_cat5_closing_returns_concept_reveal_with_concepts tests/test_state_machine.py::test_cat1_closing_unchanged -v`

Expected: the 3 Cat5 tests FAIL because the current branch still returns `widget="achievement_image"` at STEP_6_CLOSING and includes `concepts` at STEP_5_CELEBRATE. The Cat1 test should PASS (Cat1 path is unchanged).

### - [ ] Step 1.4: Implement the split in state_machine.py

Find the existing Cat5 celebrate/closing branch in `backend/state_machine.py` (around line 325, anchor: `if template_type == "cat5" and step in ("STEP_5_CELEBRATE", "STEP_6_CLOSING"):`) and replace it with two separate branches:

```python
    # Cat5 celebrate: achievement image only — no concepts, no character names.
    # Concepts live on the closing step so each step has a single focus.
    if template_type == "cat5" and step == "STEP_5_CELEBRATE":
        structured = context.get("structured_story")
        achievement_url = structured.achievement_image_data_url if structured else None
        role_title = creative_slots.role_title if isinstance(creative_slots, Cat5CreativeSlots) else "Explorer"
        widget_params: dict = {"title": role_title}
        if achievement_url:
            widget_params["image_data_url"] = achievement_url
        return ScreenFrame(
            widget="achievement_image",
            widget_params=widget_params,
            animation="badge_reveal",
            trigger="on_correct",
            sfx_cue="badge_awarded",
        )

    # Cat5 closing: concept reveal — large IB concept medallions, no image.
    if template_type == "cat5" and step == "STEP_6_CLOSING":
        role_title = creative_slots.role_title if isinstance(creative_slots, Cat5CreativeSlots) else "Explorer"
        return ScreenFrame(
            widget="concept_reveal",
            widget_params={"title": role_title, "concepts": key_concepts},
            animation="badge_reveal",
            trigger="on_enter",
            sfx_cue="celebration_fanfare",
        )
```

### - [ ] Step 1.5: Run the new tests to verify they pass

Run: `uv run pytest tests/test_state_machine.py::test_cat5_celebrate_returns_achievement_image_without_concepts tests/test_state_machine.py::test_cat5_celebrate_includes_image_when_structured_story_has_achievement_url tests/test_state_machine.py::test_cat5_closing_returns_concept_reveal_with_concepts tests/test_state_machine.py::test_cat1_closing_unchanged -v`

Expected: all 4 tests PASS.

### - [ ] Step 1.6: Run the full state_machine test file to catch regressions

Run: `uv run pytest tests/test_state_machine.py -v`

Expected: all tests in the file PASS (new + old).

### - [ ] Step 1.7: Lint + format + type check

Run: `cd backend && uv run ruff check state_machine.py && uv run ruff format --check state_machine.py && uv run mypy state_machine.py`

Expected: all three commands exit 0. If ruff format suggests changes, run `uv run ruff format state_machine.py`.

### - [ ] Step 1.8: Commit

```bash
git add backend/state_machine.py tests/test_state_machine.py
git commit -m "feat(state_machine): split Cat5 celebrate and closing widgets

STEP_5_CELEBRATE now renders achievement_image with title only.
STEP_6_CLOSING renders new concept_reveal widget with IB concepts.
Cat1 path unchanged."
```

---

## Task 2: Fix celebrate handler pre-advance snapshot (critical)

**Files:**
- Test: `tests/test_turn_handler.py` (append)
- Modify: `backend/turn_handling/directive.py` around line 940 (anchor: `if _is_celebrate_step(state.current_step):`)

### - [ ] Step 2.1: Understand the current celebrate handler flow

Run: `sed -n '938,965p' backend/turn_handling/directive.py`

Expected output shows:
```python
if _is_celebrate_step(state.current_step):
    directive.screen_widget = "achievement_image"
    directive.sfx_cue = "badge_awarded"
    try:
        turn_response = await script_agent.generate_turn_from_directive(state, directive)
    except Exception as e:
        ...
    turn_response.screen_widget = "achievement_image"
    turn_response.sfx_cue = "badge_awarded"
    _append_ai_turn(state, turn_response.dialogue)
    state.turn_count += 1

    # Advance to closing now, so the next auto-advance turn
    # arrives at STEP_6_CLOSING instead of looping at celebrate.
    _advance_state(state)
    return TurnResult(
        turn_response=turn_response,
        screen_frame=_get_screen_frame(state),   # <-- called AFTER advance
        auto_advance=_should_auto_advance(state),
        response_type="celebrate",
        error_exit=False,
        debug=_debug(None, turn_response),
    )
```

The bug: `_get_screen_frame(state)` is called after state has advanced to STEP_6_CLOSING. Under Task 1's new state machine, this returns a `concept_reveal` frame — the achievement image would never reach the frontend during the celebrate turn.

### - [ ] Step 2.2: Add a failing test for the celebrate handler behavior

Append to `tests/test_turn_handler.py`:

```python
async def test_cat5_celebrate_handler_returns_achievement_image_frame(mocker):
    """Celebrate turn must return an achievement_image frame even though state
    advances to STEP_6_CLOSING. The bug before fix: _get_screen_frame was called
    after _advance_state, returning the closing concept_reveal frame instead.
    """
    from turn_handling.directive import _resolve_turn_with_directive
    from schemas.turn_directive import TurnDirective
    from turn_handling.types import TurnInput

    state = _make_state(
        current_step="STEP_5_CELEBRATE",
        status="active",
        template_type="cat5",
    )

    # Mock the script agent so we don't hit an LLM
    mock_script_agent = mocker.MagicMock()
    mock_script_agent.generate_turn_from_directive = mocker.AsyncMock(
        return_value=_make_turn_response(dialogue="[celebrating] You did it!")
    )

    directive = TurnDirective(
        action="advance",
        reasoning="Celebrate acceptance",
        response_direction="Celebrate the child's find.",
        emotion_tag="celebrating",
    )

    result = await _resolve_turn_with_directive(
        state, TurnInput(text=""), mock_script_agent, directive,
    )

    # Critical: the screen frame at celebrate must be achievement_image,
    # NOT concept_reveal (even though state has advanced to closing).
    assert result.screen_frame.widget == "achievement_image", (
        f"celebrate should render achievement_image, got {result.screen_frame.widget}. "
        "This is the pre-advance snapshot bug."
    )
    # State should have advanced to closing for the next auto-advance turn
    assert state.current_step == "STEP_6_CLOSING"
    assert result.response_type == "celebrate"
```

Check whether `_make_state` and `_make_turn_response` helpers already exist in the file — they should, since other tests use them. If they don't, look at how surrounding tests build state and copy that pattern. If you need to adapt, add a comment explaining.

### - [ ] Step 2.3: Run the test to verify it fails

Run: `uv run pytest tests/test_turn_handler.py::test_cat5_celebrate_handler_returns_achievement_image_frame -v`

Expected: FAIL — assertion shows `result.screen_frame.widget == "concept_reveal"` (because after Task 1, STEP_6_CLOSING now returns `concept_reveal`).

### - [ ] Step 2.4: Apply the fix — snapshot before advance

In `backend/turn_handling/directive.py`, find the celebrate handler and change only the portion from `_advance_state(state)` through the `return TurnResult(...)`:

**BEFORE:**

```python
            # Advance to closing now, so the next auto-advance turn
            # arrives at STEP_5_CLOSING instead of looping at celebrate.
            _advance_state(state)
            return TurnResult(
                turn_response=turn_response,
                screen_frame=_get_screen_frame(state),
                auto_advance=_should_auto_advance(state),
                response_type="celebrate",
                error_exit=False,
                debug=_debug(None, turn_response),
            )
```

**AFTER:**

```python
            # Snapshot the celebrate screen frame BEFORE advancing — otherwise
            # _get_screen_frame(state) would return the STEP_6_CLOSING frame
            # (concept_reveal) and the achievement image would never render.
            celebrate_screen_frame = _get_screen_frame(state)

            # Advance to closing so the next auto-advance turn arrives at STEP_6_CLOSING.
            _advance_state(state)

            return TurnResult(
                turn_response=turn_response,
                screen_frame=celebrate_screen_frame,
                auto_advance=_should_auto_advance(state),
                response_type="celebrate",
                error_exit=False,
                debug=_debug(None, turn_response),
            )
```

### - [ ] Step 2.5: Run the test to verify it passes

Run: `uv run pytest tests/test_turn_handler.py::test_cat5_celebrate_handler_returns_achievement_image_frame -v`

Expected: PASS.

### - [ ] Step 2.6: Run the full turn handler test file to catch regressions

Run: `uv run pytest tests/test_turn_handler.py -q`

Expected: all tests PASS. If any test that already touched celebrate flow fails, read its assertions — most likely the test was asserting on the stale closing-frame behavior from before Task 1. Update those assertions to expect `"achievement_image"` at celebrate and `"concept_reveal"` at closing.

### - [ ] Step 2.7: Lint + type check

Run: `cd backend && uv run ruff check turn_handling/directive.py && uv run mypy turn_handling/directive.py`

Expected: exit 0.

### - [ ] Step 2.8: Commit

```bash
git add backend/turn_handling/directive.py tests/test_turn_handler.py
git commit -m "fix(directive): snapshot celebrate frame before advancing

The celebrate handler advances state to STEP_6_CLOSING, then returned
_get_screen_frame(state) — which now resolves to concept_reveal under
the new split. Snapshot the celebrate frame before advancing so the
achievement image actually reaches the frontend during celebrate."
```

---

## Task 3: Route Cat5 closing to concept_reveal in directive.py

**Files:**
- Test: `tests/test_turn_handler.py` (append)
- Modify: `backend/turn_handling/directive.py` around line 981 (anchor: `if is_closing: turn_response.screen_widget = "achievement_image"`)

### - [ ] Step 3.1: Add failing test

Append to `tests/test_turn_handler.py`:

```python
async def test_cat5_closing_handler_sets_concept_reveal_widget(mocker):
    """Cat5 closing handler should set turn_response.screen_widget = 'concept_reveal'."""
    from turn_handling.directive import _resolve_turn_with_directive
    from schemas.turn_directive import TurnDirective
    from turn_handling.types import TurnInput

    state = _make_state(
        current_step="STEP_6_CLOSING",
        status="active",
        template_type="cat5",
    )

    mock_script_agent = mocker.MagicMock()
    mock_script_agent.generate_turn_from_directive = mocker.AsyncMock(
        return_value=_make_turn_response(dialogue="[gentle] You learned about Form and Connection.")
    )

    directive = TurnDirective(
        action="advance",
        reasoning="Closing",
        response_direction="Wrap up warmly.",
        emotion_tag="gentle",
    )

    result = await _resolve_turn_with_directive(
        state, TurnInput(text=""), mock_script_agent, directive,
    )

    assert result.turn_response.screen_widget == "concept_reveal", (
        f"Cat5 closing should set screen_widget to concept_reveal, got {result.turn_response.screen_widget}"
    )


async def test_cat1_closing_handler_keeps_achievement_image_widget(mocker):
    """Cat1 closing must continue to use achievement_image — the Cat5 change is scoped."""
    from turn_handling.directive import _resolve_turn_with_directive
    from schemas.turn_directive import TurnDirective
    from turn_handling.types import TurnInput

    state = _make_state(
        current_step="STEP_5_CLOSING",
        status="active",
        template_type="cat1",
    )

    mock_script_agent = mocker.MagicMock()
    mock_script_agent.generate_turn_from_directive = mocker.AsyncMock(
        return_value=_make_turn_response(dialogue="[gentle] You discovered so much.")
    )

    directive = TurnDirective(
        action="advance",
        reasoning="Closing",
        response_direction="Wrap up warmly.",
        emotion_tag="gentle",
    )

    result = await _resolve_turn_with_directive(
        state, TurnInput(text=""), mock_script_agent, directive,
    )

    assert result.turn_response.screen_widget == "achievement_image", (
        f"Cat1 closing should stay on achievement_image, got {result.turn_response.screen_widget}"
    )
```

### - [ ] Step 3.2: Run tests to verify they fail

Run: `uv run pytest tests/test_turn_handler.py::test_cat5_closing_handler_sets_concept_reveal_widget tests/test_turn_handler.py::test_cat1_closing_handler_keeps_achievement_image_widget -v`

Expected: the Cat5 test FAILS (current code always sets `"achievement_image"` at closing). The Cat1 test PASSES (current behavior is already correct for Cat1).

### - [ ] Step 3.3: Apply the fix

In `backend/turn_handling/directive.py`, find the closing widget override (anchor: `if is_closing: turn_response.screen_widget = "achievement_image"`):

**BEFORE:**

```python
        # For closing, keep the achievement/badge visible
        if is_closing:
            turn_response.screen_widget = "achievement_image"
```

**AFTER:**

```python
        # For closing: Cat5 uses concept_reveal, Cat1 keeps achievement_image
        if is_closing:
            if state.template_type == "cat5":
                turn_response.screen_widget = "concept_reveal"
            else:
                turn_response.screen_widget = "achievement_image"
```

### - [ ] Step 3.4: Run tests to verify they pass

Run: `uv run pytest tests/test_turn_handler.py::test_cat5_closing_handler_sets_concept_reveal_widget tests/test_turn_handler.py::test_cat1_closing_handler_keeps_achievement_image_widget -v`

Expected: both PASS.

### - [ ] Step 3.5: Run full backend test suite

Run: `uv run pytest tests/ -q --ignore=tests/test_ai_quality.py`

Expected: all PASS (tests/test_ai_quality.py requires a live backend and is skipped intentionally).

### - [ ] Step 3.6: Lint + type check

Run: `cd backend && uv run ruff check turn_handling/directive.py && uv run mypy turn_handling/directive.py`

Expected: exit 0.

### - [ ] Step 3.7: Commit

```bash
git add backend/turn_handling/directive.py tests/test_turn_handler.py
git commit -m "feat(directive): route Cat5 closing to concept_reveal widget

Cat1 closing continues to use achievement_image/badge_award. Cat5
closing now sends concept_reveal so the new closing widget receives
the right widget name on turn_response."
```

---

## Task 4: Create FallbackTrophy widget (extraction)

**Files:**
- Create: `frontend/src/widgets/FallbackTrophy.jsx`

### - [ ] Step 4.1: Create the file

```jsx
// frontend/src/widgets/FallbackTrophy.jsx
export default function FallbackTrophy({ title }) {
  return (
    <div className="w-full h-full rounded-3xl
                    bg-gradient-to-br from-[var(--color-sunflower-light)]/30
                                    via-white/50
                                    to-[var(--color-forest)]/10
                    flex flex-col items-center justify-center gap-5">
      <div className="relative">
        <div className="w-40 h-40 max-[380px]:w-32 max-[380px]:h-32
                        rounded-full
                        bg-gradient-to-br from-[var(--color-sunflower)]
                                        via-[var(--color-sunflower-light)]
                                        to-[var(--color-forest)]
                        shadow-xl flex items-center justify-center
                        border-4 border-white/80">
          <div className="w-24 h-24 max-[380px]:w-20 max-[380px]:h-20
                          rounded-full bg-white/70
                          flex items-center justify-center">
            <span className="text-6xl max-[380px]:text-5xl">🏆</span>
          </div>
        </div>
        <div className="absolute -top-3 -right-3 w-6 h-6 rounded-full
                        bg-[var(--color-sunflower)] animate-sparkle-large" />
        <div className="absolute -bottom-2 -left-3 w-5 h-5 rounded-full
                        bg-[var(--color-forest-light)] animate-sparkle-large"
             style={{ animationDelay: '0.8s' }} />
        <div className="absolute top-0 -left-4 w-4 h-4 rounded-full
                        bg-[var(--color-teal)] animate-sparkle-large"
             style={{ animationDelay: '1.4s' }} />
      </div>
      <p className="text-2xl max-[380px]:text-xl font-display font-bold
                    text-[var(--color-forest-dark)]">
        {title || 'Explorer'}
      </p>
    </div>
  );
}
```

### - [ ] Step 4.2: Verify lint

Run: `cd frontend && npm run lint`

Expected: exit 0 (no warnings/errors about the new file).

### - [ ] Step 4.3: Commit

```bash
git add frontend/src/widgets/FallbackTrophy.jsx
git commit -m "feat(widgets): extract FallbackTrophy from AchievementImage"
```

---

## Task 5: Simplify AchievementImage widget

**Files:**
- Modify: `frontend/src/widgets/AchievementImage.jsx` (full rewrite)

### - [ ] Step 5.1: Rewrite AchievementImage to focus on the image

Replace the entire contents of `frontend/src/widgets/AchievementImage.jsx` with:

```jsx
// frontend/src/widgets/AchievementImage.jsx
import FallbackTrophy from './FallbackTrophy';

export default function AchievementImage({ image_data_url, title, animation }) {
  return (
    <div
      className={`relative flex flex-col h-full w-full p-4 ${
        animation === 'badge_reveal' ? 'animate-celebration-large' : ''
      }`}
    >
      {/* Role title — top, centered, generous */}
      <h2
        className="text-2xl max-[380px]:text-xl font-bold font-display text-center
                   text-[var(--color-forest-dark)] tracking-tight pb-3 shrink-0"
      >
        {title || 'Explorer'}
      </h2>

      {/* Achievement image fills remaining space — object-contain respects aspect ratio */}
      <div className="flex-1 min-h-0 w-full flex items-center justify-center">
        {image_data_url ? (
          <img
            src={image_data_url}
            alt="Your adventure"
            className="max-w-full max-h-full rounded-3xl shadow-2xl object-contain animate-fade-in"
          />
        ) : (
          <FallbackTrophy title={title} />
        )}
      </div>
    </div>
  );
}
```

### - [ ] Step 5.2: Verify the old props are gone

Run: `grep -n "concepts\|collectedNames\|sessionState" frontend/src/widgets/AchievementImage.jsx`

Expected: NO matches. If any remain, remove them — the widget should only accept `image_data_url`, `title`, `animation`.

### - [ ] Step 5.3: Verify lint

Run: `cd frontend && npm run lint`

Expected: exit 0.

### - [ ] Step 5.4: Verify build

Run: `cd frontend && npm run build`

Expected: build succeeds. If it fails with an error about unused imports elsewhere in the codebase that previously passed `concepts` or `collected_names` to `AchievementImage`, leave those alone — the new `AchievementImage` just ignores extra props (React is forgiving about extras).

### - [ ] Step 5.5: Commit

```bash
git add frontend/src/widgets/AchievementImage.jsx
git commit -m "refactor(widgets): simplify AchievementImage to title + image only

Removes concept pills and character name pills — both belonged to
other steps. Uses FallbackTrophy for the no-image state."
```

---

## Task 6: Create ConceptMedallion component

**Files:**
- Create: `frontend/src/widgets/ConceptMedallion.jsx`

### - [ ] Step 6.1: Create the file

```jsx
// frontend/src/widgets/ConceptMedallion.jsx
import { asset } from '../utils/basePath';
import { StarIcon } from '../icons';

export default function ConceptMedallion({ concept, delayMs = 0 }) {
  const badgeSrc = asset(`/badges/${concept.toLowerCase()}.png`);

  return (
    <div
      className="flex flex-col items-center gap-2 animate-badge-pop"
      style={{ animationDelay: `${delayMs}ms` }}
    >
      {/* Outer gradient circle — mirrors ExplorerMap ZoneSlot shape */}
      <div className="relative">
        <div
          className="w-[clamp(6rem,22vw,8rem)] h-[clamp(6rem,22vw,8rem)]
                     rounded-full
                     bg-gradient-to-br from-[var(--color-sunflower)]
                                       via-[var(--color-sunflower-light)]
                                       to-[var(--color-forest)]
                     border-[4px] border-white/90
                     shadow-xl
                     flex items-center justify-center
                     animate-gentle-float"
          style={{ animationDelay: `${delayMs + 200}ms` }}
        >
          {/* Inner white disc holds the badge PNG */}
          <div className="w-[78%] h-[78%] rounded-full bg-white/90
                          flex items-center justify-center overflow-hidden">
            <img
              src={badgeSrc}
              alt={concept}
              className="w-[85%] h-[85%] object-contain"
              onError={(e) => {
                // Graceful fallback: if the PNG is missing, show a sparkle emoji
                const parent = e.currentTarget.parentElement;
                if (parent) {
                  parent.innerHTML = '<span class="text-3xl">✨</span>';
                }
              }}
            />
          </div>
        </div>

        {/* Star accent top-right, mirrors ZoneSlot's checkmark accent */}
        <div
          className="absolute -top-1 -right-1 animate-sparkle-large"
          style={{ animationDelay: `${delayMs + 800}ms` }}
        >
          <StarIcon className="w-6 h-6 text-[var(--color-sunflower)] drop-shadow" />
        </div>
      </div>

      {/* Concept name pill — same treatment as ZoneSlot character label */}
      <span
        className="px-4 py-1 bg-white/90 backdrop-blur-sm rounded-full
                   text-base max-[380px]:text-sm
                   font-semibold text-[var(--color-forest-dark)]
                   shadow-sm border border-[var(--color-forest)]/15
                   animate-fade-in"
        style={{ animationDelay: `${delayMs + 400}ms` }}
      >
        {concept}
      </span>
    </div>
  );
}
```

### - [ ] Step 6.2: Verify all 8 badge PNGs exist for graceful lookup

Run: `ls frontend/public/badges/`

Expected output includes: `causation.png`, `change.png`, `connection.png`, `form.png`, `function.png`, `perspective.png`, `reflection.png`, `responsibility.png`.

If any are missing, do NOT create them — the `onError` handler provides graceful degradation. Just note in the commit message if anything unexpected shows up.

### - [ ] Step 6.3: Verify lint

Run: `cd frontend && npm run lint`

Expected: exit 0.

### - [ ] Step 6.4: Commit

```bash
git add frontend/src/widgets/ConceptMedallion.jsx
git commit -m "feat(widgets): add ConceptMedallion for IB concept tokens

Circular medallion using existing /badges/*.png assets, sized larger
than ExplorerMap zone slots (clamp 6-8rem vs 4.5-6rem). Staggered
animation, star accent, graceful fallback to sparkle emoji on load error."
```

---

## Task 7: Create ConceptReveal widget

**Files:**
- Create: `frontend/src/widgets/ConceptReveal.jsx`

### - [ ] Step 7.1: Create the file

```jsx
// frontend/src/widgets/ConceptReveal.jsx
import ConceptMedallion from './ConceptMedallion';

export default function ConceptReveal({ title, concepts = [], animation }) {
  return (
    <div
      className={`flex flex-col items-center justify-center h-full w-full p-6 gap-8
                  bg-gradient-to-b from-[var(--color-sunflower-light)]/20
                                  via-white/40
                                  to-[var(--color-forest)]/5
                  ${animation === 'badge_reveal' ? 'animate-celebration-large' : ''}`}
    >
      {/* Title with flanking sparkle emojis */}
      <div className="flex items-center gap-3">
        <span className="text-3xl animate-sparkle-large">✨</span>
        <h2 className="text-2xl max-[380px]:text-xl font-display font-bold
                       text-[var(--color-forest-dark)] tracking-tight text-center">
          {title || 'Explorer'}
        </h2>
        <span className="text-3xl animate-sparkle-large" style={{ animationDelay: '0.6s' }}>
          ✨
        </span>
      </div>

      {/* Concept medallion row — flex-wrap for 4+ concepts on narrow screens */}
      <div className="flex flex-wrap justify-center items-start gap-6 max-[380px]:gap-4">
        {concepts.map((concept, i) => (
          <ConceptMedallion key={concept} concept={concept} delayMs={i * 250} />
        ))}
      </div>

      {/* Role line */}
      <p className="text-base font-display text-[var(--color-forest-dark)]/80 text-center">
        {`You are now a ${title || 'Explorer'}!`}
      </p>
    </div>
  );
}
```

### - [ ] Step 7.2: Verify lint

Run: `cd frontend && npm run lint`

Expected: exit 0.

### - [ ] Step 7.3: Commit

```bash
git add frontend/src/widgets/ConceptReveal.jsx
git commit -m "feat(widgets): add ConceptReveal widget for STEP_6_CLOSING

Renders role title flanked by sparkles, a flex-wrap row of
ConceptMedallion children staggered 250ms apart, and a role line."
```

---

## Task 8: Create StageModeFooter component

**Files:**
- Create: `frontend/src/components/StageModeFooter.jsx`

### - [ ] Step 8.1: Create the file

```jsx
// frontend/src/components/StageModeFooter.jsx
import { SpeakerIcon } from '../icons';

export default function StageModeFooter({ messages, isSpeaking }) {
  const latestAi = [...(messages || [])].reverse().find((m) => m.role === 'ai');
  if (!latestAi) {
    return <div className="h-12" aria-hidden="true" />;
  }

  return (
    <div className="h-12 flex items-center gap-2 px-4 surface-primary
                    border-t border-black/5
                    animate-fade-in">
      <SpeakerIcon
        className={`w-4 h-4 shrink-0 ${
          isSpeaking
            ? 'text-[var(--color-forest)] animate-pulse'
            : 'text-gray-400'
        }`}
      />
      <p className="text-sm text-gray-700 truncate italic">
        &ldquo;{latestAi.text}&rdquo;
      </p>
    </div>
  );
}
```

Note: if `surface-primary` is not a defined Tailwind / CSS class in this codebase, substitute `bg-white`. Check by running: `grep -rn "surface-primary" frontend/src frontend/public/styles 2>&1 | head -5` — if it's used elsewhere the class is fine; otherwise use `bg-white`.

### - [ ] Step 8.2: Verify lint

Run: `cd frontend && npm run lint`

Expected: exit 0.

### - [ ] Step 8.3: Commit

```bash
git add frontend/src/components/StageModeFooter.jsx
git commit -m "feat(components): add StageModeFooter for celebrate/closing

Thin 48px strip showing the latest AI dialogue line with animated
speaker icon when TTS is playing. No mic, no input — informational only."
```

---

## Task 9: Register concept_reveal in DeviceScreen

**Files:**
- Modify: `frontend/src/components/DeviceScreen.jsx` (two edits: WIDGET_MAP and full-panel widget list)

### - [ ] Step 9.1: Add the import

Near the top of `frontend/src/components/DeviceScreen.jsx`, in the existing group of widget imports, add:

```jsx
import ConceptReveal from '../widgets/ConceptReveal';
```

Place it alphabetically / near `AchievementImage` for tidiness.

### - [ ] Step 9.2: Add to WIDGET_MAP

Find the `WIDGET_MAP` declaration (around line 18) and add the `concept_reveal` entry:

**BEFORE:**

```jsx
const WIDGET_MAP = {
  photo_display: PhotoDisplay,
  progress_tracker: ProgressTracker,
  character_display: CharacterDisplay,
  photo_grid: PhotoGrid,
  photo_recall_grid: PhotoRecallGrid,
  badge_award: BadgeAward,
  story_scene: StoryScene,
  story_loading: StoryLoading,
  achievement_image: AchievementImage,
  explorer_map: ExplorerMap,
};
```

**AFTER:**

```jsx
const WIDGET_MAP = {
  photo_display: PhotoDisplay,
  progress_tracker: ProgressTracker,
  character_display: CharacterDisplay,
  photo_grid: PhotoGrid,
  photo_recall_grid: PhotoRecallGrid,
  badge_award: BadgeAward,
  story_scene: StoryScene,
  story_loading: StoryLoading,
  achievement_image: AchievementImage,
  concept_reveal: ConceptReveal,
  explorer_map: ExplorerMap,
};
```

### - [ ] Step 9.3: Add concept_reveal to the full-panel widget list

Find line 131 (anchor: the ternary that checks `screenFrame.widget === 'explorer_map' || screenFrame.widget === 'story_scene' || ...`) and add `'concept_reveal'`:

**BEFORE:**

```jsx
        {(screenFrame.widget === 'explorer_map' || screenFrame.widget === 'story_scene' || screenFrame.widget === 'story_loading' || screenFrame.widget === 'achievement_image') && WidgetComponent ? (
```

**AFTER:**

```jsx
        {(screenFrame.widget === 'explorer_map' || screenFrame.widget === 'story_scene' || screenFrame.widget === 'story_loading' || screenFrame.widget === 'achievement_image' || screenFrame.widget === 'concept_reveal') && WidgetComponent ? (
```

### - [ ] Step 9.4: Verify lint + build

Run: `cd frontend && npm run lint && npm run build`

Expected: both exit 0.

### - [ ] Step 9.5: Commit

```bash
git add frontend/src/components/DeviceScreen.jsx
git commit -m "feat(device-screen): register concept_reveal widget

Added to WIDGET_MAP and full-panel render branch so the new closing
widget receives the w-full h-full container treatment instead of the
constrained max-w-[17rem] wrapper."
```

---

## Task 10: Add stage mode to App.jsx and CSS

**Files:**
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/index.css` (or wherever `.app-top-panel` is defined — grep to find)

### - [ ] Step 10.1: Locate the CSS file holding `.app-top-panel`

Run: `grep -rn "app-top-panel" frontend/src --include="*.css"`

Expected: one or two hits. If `.app-top-panel` is only referenced via Tailwind utility classes (no CSS class rule), the CSS transition will need to live in a CSS file — likely `frontend/src/index.css` (Tailwind v4 entry point).

Open that file and find where `.app-top-panel` is styled, if anywhere. If not present, you'll add new rules at the end of the file.

### - [ ] Step 10.2: Add stage mode CSS rules

Append to `frontend/src/index.css`:

```css
/* Stage mode — celebrate/closing expand the device panel to full viewport */
.app-top-panel,
.app-main > section[aria-label="Conversation panel"] {
  transition:
    flex-basis 500ms ease-out,
    max-height 500ms ease-out,
    height 500ms ease-out;
}

.stage-mode .app-top-panel {
  flex: 1 1 auto;
  max-height: none;
  height: auto;
}

.stage-mode > section[aria-label="Conversation panel"] {
  flex: 0 0 3rem;
  overflow: hidden;
}
```

### - [ ] Step 10.3: Modify App.jsx — imports

At the top of `frontend/src/App.jsx`, add:

```jsx
import StageModeFooter from './components/StageModeFooter';
```

Place it alphabetically near other `./components/` imports.

### - [ ] Step 10.4: Derive stageMode and apply the class

Find where `sessionState` is used and the `<main>` element is rendered. Near the `return (...)` but before the JSX, add the derivation:

```jsx
  const stageMode = ['STEP_5_CELEBRATE', 'STEP_6_CLOSING'].includes(
    sessionState?.current_step
  );
```

Then update the `<main>` opening tag to include the conditional class. Find the current line (anchor: `className="app-main flex flex-col flex-1 overflow-hidden`):

**BEFORE:**

```jsx
      <main className="app-main flex flex-col flex-1 overflow-hidden px-3 pt-2 pb-3 gap-2.5 sm:gap-3 max-[380px]:px-2 max-[380px]:pt-1.5 max-[380px]:pb-2 max-[380px]:gap-2 max-w-4xl mx-auto w-full">
```

**AFTER:**

```jsx
      <main className={`app-main flex flex-col flex-1 overflow-hidden px-3 pt-2 pb-3 gap-2.5 sm:gap-3 max-[380px]:px-2 max-[380px]:pt-1.5 max-[380px]:pb-2 max-[380px]:gap-2 max-w-4xl mx-auto w-full ${stageMode ? 'stage-mode' : ''}`}>
```

### - [ ] Step 10.5: Conditionally render StageModeFooter in the conversation section

Find the conversation `<section>` block (anchor: `aria-label="Conversation panel"`). Inside it, when `stageMode` is true, render the footer instead of the normal contents.

The simplest change — wrap the inner children in a ternary:

**BEFORE:**

```jsx
        <section className="flex-1 min-h-0 flex flex-col surface-primary overflow-hidden" aria-label="Conversation panel">
          {showRetry ? (
            <div className="flex-1 flex items-center justify-center">
              <RetryButton onRetry={handleRetry} retryCount={retryCount} maxRetries={3} />
            </div>
          ) : showPhotoSelector ? (
            <PhotoSelector onPhotoSelect={startSession} isLoading={loading} />
          ) : (
            <ConversationPanel
              messages={messages}
              onSendMessage={sendMessage}
              onMicToggle={toggleMic}
              isMicActive={isMicActive}
              silenceTimer={silenceTimer}
```

**AFTER:**

Change the opening of the ternary to check `stageMode` first:

```jsx
        <section className="flex-1 min-h-0 flex flex-col surface-primary overflow-hidden" aria-label="Conversation panel">
          {stageMode ? (
            <StageModeFooter messages={messages} isSpeaking={isSpeaking} />
          ) : showRetry ? (
            <div className="flex-1 flex items-center justify-center">
              <RetryButton onRetry={handleRetry} retryCount={retryCount} maxRetries={3} />
            </div>
          ) : showPhotoSelector ? (
            <PhotoSelector onPhotoSelect={startSession} isLoading={loading} />
          ) : (
            <ConversationPanel
              messages={messages}
              onSendMessage={sendMessage}
              onMicToggle={toggleMic}
              isMicActive={isMicActive}
              silenceTimer={silenceTimer}
```

(The rest of the `ConversationPanel` props and closing tags remain unchanged.)

Note: `isSpeaking` may or may not already be destructured/available at this level. If it's not, trace back to the hook that exposes it (search for `isSpeaking` in App.jsx — likely from `useSessionOrchestration`). If not exposed, pass `isSpeaking={false}` for now — the feature still works, just without the pulse animation.

### - [ ] Step 10.6: Verify lint + build

Run: `cd frontend && npm run lint && npm run build`

Expected: both exit 0. If `isSpeaking` isn't defined at App.jsx scope, fix the reference (either add it to the hook destructuring or hardcode `false` as noted above).

### - [ ] Step 10.7: Commit

```bash
git add frontend/src/App.jsx frontend/src/index.css frontend/src/components/StageModeFooter.jsx
git commit -m "feat(app): add stage mode for celebrate/closing

Derives stageMode from current_step, applies .stage-mode class to
<main>, animates the device panel to full viewport via CSS transitions,
and collapses conversation panel to a 48px footer strip showing the
latest AI line."
```

---

## Task 11: Full verification sweep

**Files:** none (verification only)

### - [ ] Step 11.1: Backend test suite

Run: `uv run pytest tests/ -q --ignore=tests/test_ai_quality.py`

Expected: all PASS. Note the pass count — should be higher than before (we added several tests across Tasks 1-3).

### - [ ] Step 11.2: Backend lint + format + type check

Run:

```bash
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy state_machine.py turn_handling/directive.py
```

Expected: all exit 0.

### - [ ] Step 11.3: Frontend lint + build

Run: `cd frontend && npm run lint && npm run build`

Expected: both exit 0.

### - [ ] Step 11.4: Verify no orphaned references to removed props

Run: `grep -rn "collectedNames\|sessionState.*AchievementImage" frontend/src`

Expected: no matches (the AchievementImage widget no longer reads those).

Run: `grep -rn "concepts.*AchievementImage\|AchievementImage.*concepts" frontend/src`

Expected: no matches.

### - [ ] Step 11.5: Confirm stage mode classes reach the DOM

Run: `grep -n "stage-mode" frontend/src/App.jsx frontend/src/index.css`

Expected: at least one hit in App.jsx (the conditional class) and three in index.css (the `.stage-mode` rules).

### - [ ] Step 11.6: Manual E2E smoke test (requires live backend + Vertex AI credentials)

In one terminal:

```bash
cd backend
uv run uvicorn server:app --port 8000
```

In another terminal:

```bash
cd frontend
npm run dev
```

Open the browser to the Vite URL (usually `http://localhost:5173`).

Checklist (repeat for dandelion game, polka_dot_patrol game, and one Cat1 game like mood_changer_dog):

- [ ] Start the game. Play through collection (select the required photos).
- [ ] Reach synthesis. Verify loading screen → scene(s) → last scene auto-advances to celebrate.
- [ ] **At celebrate:** device panel grows to fill the viewport (~500ms smooth transition). Conversation panel collapses to a thin 48px footer showing the latest AI line. Achievement image renders at its natural aspect ratio — **no cutoff**. No character name pills. No concept pills. Only role title above the image.
- [ ] **Auto-advance to closing:** for Cat5, the widget transitions to `ConceptReveal` — title with sparkle emojis, staggered medallion reveal (250ms apart), each medallion uses a PNG from `/badges/`. For Cat1, closing continues to look as before.
- [ ] **Medallion size visibly larger** than collection zone slots — should be roughly 33% bigger.
- [ ] **Role line** at the bottom: "You are now a {role_title}!".
- [ ] Click "new session" — layout animates back to the split view smoothly.
- [ ] **For polka_dot_patrol specifically**, verify both Form and Connection medallions render. Check that `/badges/form.png` and `/badges/connection.png` load correctly (no broken image icons, no fallback sparkles).

### - [ ] Step 11.7: No commit for this task

Verification only. If any check fails, return to the relevant task, fix, re-verify, amend or add a fix commit, then re-run this task's checks.

---

## Open items flagged (for future follow-up)

These are explicitly out of scope for this plan but worth noting:

1. **Tap-to-explain on medallions** — add `onClick` handler that speaks a short definition. Deferred.
2. **Role line i18n** — the string "You are now a {title}!" is hardcoded English in `ConceptReveal.jsx`. Move to backend-sourced copy when i18n lands.
3. **Empty concepts edge case** — all current games have ≥1 concept. If a future game ships with 0, `ConceptReveal` renders title + role line with no medallions. Acceptable degradation.
4. **Exit animation polish** — if the 500ms ease-out reverse feels abrupt at "new session", consider adding a dedicated exit animation. Flag during manual E2E.
5. **Old `badge_award` widget for Cat1** — Cat1 closing still uses `badge_award` (and small concept pills). A future plan could apply the same medallion treatment to Cat1 for visual parity, but that's explicitly out of scope here (spec non-goal).

---

## Rollback plan

If any task breaks prod unexpectedly:

```bash
# Roll back the whole feature by reverting the individual commits
git log --oneline | grep -E "feat\(state_machine\)|fix\(directive\)|feat\(widgets\)|feat\(components\)|refactor\(widgets\)|feat\(device-screen\)|feat\(app\)"
git revert <commit-sha-1> <commit-sha-2> ...  # in reverse order
```

The backend changes (Tasks 1-3) can be rolled back independently from the frontend changes. If only the frontend has a problem, revert Tasks 4-10 and the backend's new `concept_reveal` widget name just gets ignored by the old frontend (the old `AchievementImage` would render as a fallback via `DeviceScreen`'s default widget path, though the backend would be sending a widget name the frontend doesn't know — this may cause a gray "Widget: concept_reveal" placeholder until a full rollback is applied).

**Safer rollback:** revert Task 1 (state_machine split) last, since that's what creates the `concept_reveal` widget name. If you revert backend first and leave frontend in place, you're fine. If you revert frontend first and leave backend in place, the closing screen renders a placeholder.

Recommended order if rolling back: Task 10 → 9 → 8 → 7 → 6 → 5 → 4 → 3 → 2 → 1.
