# Three Activity Flow and Layout Fixes Implementation Plan

**Goal:** Fix the Cat1, Cat3, and Cat5 representative activity flow defects before generating any new scene assets.

**Architecture:** Treat recipe/source fidelity as the first layer, then normalize device-screen layout behavior, then add activity-specific runtime screen composition. Static visual assets stay as placeholders until these behavioral contracts pass. Scene asset generation is explicitly blocked until the tests and browser checks in this plan pass.

**Tech Stack:** FastAPI backend activity recipes, Python turn handling tests, React/Vite frontend, Vitest/Testing Library, static `activity-assets.manifest.json` layouts.

---

## Source Inputs

- UI design doc: `/Users/pharrelly/Downloads/活动库视觉规范.docx`
- Design doc section `4. 布局` requires:
  - One image: centered, no core content in the avoid area.
  - One image plus text: image remains primary.
  - Two images: left/right choice layout, `1:1` or `3:4`, selected by voice or scroll.
  - Three images: triangular layout, `1:1` or `3:4`, selected by voice or scroll.
  - Three or more images: scroll layout.
  - Four images: avoid for now because the screen becomes crowded.
- Current representative activities:
  - Cat1: `activity_career_decision_role_play`
  - Cat3: `activity_guided_drawing`
  - Cat5: `activity_phoneme_treasure_hunt`

## Non-Goals

- Do not generate or replace scene assets in this phase.
- Do not add STT, TTS, camera, photo upload, or recognition UI.
- Do not convert all 12 activities to new assets.
- Do not make screen touch the primary interaction. The real device is touchless.

## Task 1: Lock Source Fidelity for the Three Activities

**Files:**
- Modify: `backend/games/activity_career_decision_role_play.md`
- Modify: `backend/games/activity_guided_drawing.md`
- Modify: `backend/games/activity_phoneme_treasure_hunt.md`
- Modify: `backend/tests/test_activity_source_fidelity.py`
- Modify if needed: `backend/agents/script_agent.py`
- Test: `backend/tests/test_activity_source_fidelity.py`
- Test: `backend/tests/test_generation_text_mode.py`

**Step 1: Write failing source-fidelity assertions**

Add assertions that protect these child-facing constraints:

- Career Decision Role Play:
  - Must preserve firefighter sequence: smoke alarm decision, water hose vs cooking oil, check people outside vs run inside alone.
  - Must not use device-specific words in child dialogue: `card`, `cards`, `token`, `tap`, `touch`, `point`, `click`.
  - Must handle uncertainty like "I don't know" by staying on the same decision and offering the bounded choices again, not jumping to the wrong round.
- Guided Drawing:
  - Must be a guided step-by-step drawing flow, not a random drawing prompt.
  - Must bind rounds to a concrete step-card sequence. Example for placeholder assets: shape starter, add feature, finish object.
  - Must not ask open-ended "what could it become?" until after a specific step is completed.
- Phoneme Treasure Hunt:
  - Must ask for items beginning with the letter/sound B, not object noises.
  - Must not ask "what sound does the object make?"
  - Must preserve actual collected items for recap.

Run:

```bash
cd backend
uv run pytest tests/test_activity_source_fidelity.py -q
```

Expected before implementation: fails on the newly added constraints.

**Step 2: Tighten recipes at the source**

Edit the three `backend/games/activity_*.md` files so the runtime instructions, example lines, acceptable themes, screen copy, and follow-up contracts all use the same source language.

For `activity_phoneme_treasure_hunt.md`, replace ambiguous "target sound" prompts with `letter B` / `starts with B` language where the activity needs alphabet matching. Keep "beginning sound" only when paired with the letter, for example "the /b/ sound at the start of B words."

For `activity_guided_drawing.md`, replace the generic build steps with a fixed guided sequence. Until final assets exist, use a neutral placeholder drawing sequence that can be displayed by current assets:

1. Draw one big circle.
2. Add two small ears or petals.
3. Add one face/detail and say it is done.

For `activity_career_decision_role_play.md`, strengthen each round so the director cannot jump rounds on "I don't know"; uncertainty should trigger a bounded repeat of the current choice.

**Step 3: Ensure text-mode sanitation remains enforced**

Confirm `backend/agents/script_agent.py` removes or prevents device-bound words for these imported activities. If the recipe still contains `card` or `token` as source metadata, the child-facing rewrite must use neutral words like `picture`, `choice`, `step`, or `turn`.

Run:

```bash
cd backend
uv run pytest tests/test_generation_text_mode.py tests/test_activity_source_fidelity.py -q
```

Expected after implementation: pass.

## Task 2: Add Layout Primitives from the UI Design Doc

**Files:**
- Modify: `frontend/src/activityGame/activityAssets.js`
- Modify: `frontend/src/activityGame/ActivityLens.jsx`
- Modify: `frontend/src/index.css`
- Modify: `frontend/tests/activityAssets.test.js`
- Modify: `frontend/tests/WonderLensDevice.test.jsx`

**Step 1: Write failing layout tests**

Cover these layout modes:

- `single`: one centered image, no item cards.
- `singleText`: one image with compact text area, text must not cover the core image.
- `choice2`: two images left/right.
- `choice3`: triangular three-image layout.
- `picker`: crown-scroll selector for three or more options.
- No four-image grid for runtime choices.

Run:

```bash
cd frontend
npm test -- activityAssets.test.js WonderLensDevice.test.jsx --runInBand
```

Expected before implementation: fails for the new `picker` and no-four-grid rules.

**Step 2: Implement layout normalization**

Update `activityAssets.js` so manifest layouts normalize to the UI design doc vocabulary:

- `single` for passive beat images.
- `choice2` for two selectable visual choices.
- `choice3` for exactly three selectable visual choices.
- `picker` for three or more scrollable choices when the activity uses the physical scroll button.

Do not let runtime create a four-up visible grid. If a choice set has four items, use `picker`.

**Step 3: Implement renderer support**

Update `ActivityLens.jsx` and CSS:

- Preserve the circular device screen.
- Keep all core image content inside the lens safe area.
- For `choice2`, render left/right with selected state.
- For `choice3`, render triangular positions with selected state.
- For `picker`, render an Apple Watch Digital Crown-style wheel:
  - selected item centered, larger, fully opaque.
  - previous and next items partially visible, smaller, faded.
  - scroll button changes selected item.
  - green start/select confirms the centered item.

Run:

```bash
cd frontend
npm test -- activityAssets.test.js WonderLensDevice.test.jsx --runInBand
```

Expected after implementation: pass.

## Task 3: Fix Cat5 Phoneme Treasure Hunt Interaction

**Files:**
- Modify: `frontend/src/activityGame/ActivityGameApp.jsx`
- Modify: `frontend/src/activityGame/ActivityLens.jsx`
- Modify: `frontend/src/index.css`
- Modify: `frontend/tests/ActivityGameApp.test.jsx`
- Modify if needed: `backend/server.py`
- Modify if needed: `backend/turn_handling/collection.py`

**Step 1: Write failing Cat5 tests**

Add tests for:

- Current round choices render as `picker`, not a static green-border grid.
- Scroll up/down changes the centered item.
- Start/select sends the centered item.
- Typed input is disabled only while choosing an item.
- After collection, the screen can show the chosen item without keeping selection mode active.
- Synthesis/celebration uses `sessionState.collected_photos`, not static manifest items.

Run:

```bash
cd frontend
npm test -- ActivityGameApp.test.jsx --runInBand
```

Expected before implementation: fails for picker mode and dynamic recap.

**Step 2: Make Cat5 recap state-derived**

Update the frontend screen layout builder so `STEP_4_SYNTHESIS` and Cat5 recap compose selected items from `sessionState.collected_photos`.

The dynamic layout should:

- Preserve actual collected IDs.
- Preserve collection order returned by backend state.
- Resolve images from `current_round_items` where available and from the manifest item catalog otherwise.
- Never display static `ball/book/banana` if the user picked `ball/basket/banana`.

**Step 3: Tighten phoneme runtime wording**

Apply Task 1 recipe changes and verify live behavior:

- First prompt asks the child to find/select a B-starting item.
- Wrong pick receives "that starts with another letter/sound" style guidance.
- Correct pick asks for a simple confirmation or next find, not an object noise.

Run:

```bash
cd frontend
npm test -- ActivityGameApp.test.jsx activityAssets.test.js --runInBand
```

Expected after implementation: pass.

## Task 4: Fix Cat3 Guided Drawing Interaction

**Files:**
- Modify: `frontend/src/activityGame/ActivityGameApp.jsx`
- Modify: `frontend/src/activityGame/ActivityLens.jsx`
- Modify: `frontend/src/index.css`
- Modify: `frontend/tests/ActivityGameApp.test.jsx`
- Modify: `backend/games/activity_guided_drawing.md`
- Modify: `backend/tests/test_activity_text_game_cat3.py`

**Step 1: Write failing Cat3 tests**

Add tests for:

- Cat3 screen remains focused on the current drawing step visual.
- `Done` and `Help` are selected by the scroll button.
- Start/select confirms the selected option.
- The Done/Help selector does not cover the central object/scene.
- Text input remains available for optional typed notes unless the selector is explicitly being confirmed.

Run:

```bash
cd frontend
npm test -- ActivityGameApp.test.jsx WonderLensDevice.test.jsx --runInBand
```

Expected before implementation: fails because the current selector is a large centered overlay.

**Step 2: Move Done/Help into a compact control strip**

Replace the current centered overlay with a small, non-blocking bottom or edge control strip inside the safe area.

Design constraints:

- It should behave like a selection status, not a big in-screen button panel.
- It should not cover the drawing object.
- It should use scroll/select affordance language consistent with the physical controls.
- It should remain readable on a light image.

**Step 3: Bind Cat3 prompts to fixed drawing steps**

After Task 1 recipe changes, verify the live flow:

1. AI gives a specific first drawing step.
2. User says `done`.
3. AI gives the next specific step.
4. User says `help`.
5. AI repeats or simplifies the same step instead of inventing a random drawing.

Run:

```bash
cd backend
uv run pytest tests/test_activity_text_game_cat3.py tests/test_activity_source_fidelity.py -q
cd ../frontend
npm test -- ActivityGameApp.test.jsx WonderLensDevice.test.jsx --runInBand
```

Expected after implementation: pass.

## Task 5: Fix Cat1 Career Decision Role Play Runtime Flow

**Files:**
- Modify: `backend/games/activity_career_decision_role_play.md`
- Modify: `backend/tests/test_activity_source_fidelity.py`
- Modify if needed: `backend/turn_handling/directive.py`
- Modify if needed: `backend/agents/script_agent.py`
- Modify: `frontend/src/activityGame/ActivityGameApp.jsx`
- Modify: `frontend/tests/ActivityGameApp.test.jsx`

**Step 1: Write failing Cat1 flow tests**

Add focused tests or smoke-script checks for:

- "I don't know" during the safe-action question keeps the same decision and offers the two choices again.
- The next response does not jump to the water-hose/cooking-oil beat.
- The frontend beat image changes with `current_step` and does not lag on the previous beat after an AI response.
- No Cat1 in-screen picker appears.

Run:

```bash
cd backend
uv run pytest tests/test_activity_source_fidelity.py tests/test_generation_text_mode.py -q
cd ../frontend
npm test -- ActivityGameApp.test.jsx --runInBand
```

Expected before implementation: fails on the uncertainty handling or screen-sync assertion.

**Step 2: Tighten round-specific fallback behavior**

Update recipe and, if required, directive handling so low-confidence answers stay on the current Cat1 round.

For the third round:

- User uncertainty should produce: "That is okay. Should the firefighter check people are safe outside, or run inside alone?"
- It should not answer with tool-choice content.

**Step 3: Verify screen step sync**

If frontend screen assets lag one response behind, inspect whether `sessionState.current_step` is updated after the turn or whether `beatIdFromSessionState` maps Cat1 steps too coarsely. Fix the smallest source:

- Prefer correcting `beatIdFromSessionState` if mapping is wrong.
- Prefer backend state update only if the state itself is wrong.

Expected after implementation: active beat image matches the current backend step.

## Task 6: Browser and Live Smoke Verification

**Files:**
- Use existing: `scripts/run_activity_text_smoke.py`
- Modify only if needed: `scripts/run_activity_text_smoke.py`

**Step 1: Run focused automated tests**

```bash
cd backend
uv run pytest tests/test_activity_source_fidelity.py tests/test_generation_text_mode.py tests/test_activity_text_game_cat3.py -q
cd ../frontend
npm test -- ActivityGameApp.test.jsx WonderLensDevice.test.jsx activityAssets.test.js --runInBand
```

Expected: pass.

**Step 2: Run live smoke with provider credentials**

Use existing backend-root credentials without editing or printing secrets:

```bash
MAIN_REPO_ROOT="/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/backend"
set -a
source "$MAIN_REPO_ROOT/.env"
set +a
export GOOGLE_APPLICATION_CREDENTIALS="$(ls "$MAIN_REPO_ROOT"/.elaborate-baton-*.json | head -n 1)"
```

Then run:

```bash
python scripts/run_activity_text_smoke.py --timeout 120
```

Expected: all 12 activities pass, with focused inspection of the three representatives.

**Step 3: Browser walkthrough**

Open:

```text
http://127.0.0.1:5173/?view=activities
```

Verify:

- Career Decision Role Play:
  - no `card` / `token` wording in child-facing text.
  - "I don't know" repeats the same bounded decision.
  - screen beat follows the dialogue.
- Guided Drawing:
  - step-by-step fixed drawing instructions.
  - compact `Done`/`Help` selector does not cover the drawing.
  - `Help` stays on the current step.
- Phoneme Treasure Hunt:
  - asks for B-starting items.
  - picker is Digital Crown-style.
  - celebration uses the actual selected items.

## Completion Gate

Only after all tasks above pass:

- mark this flow/layout phase complete;
- then start a separate scene-asset generation phase.

Do not regenerate scene assets while any recipe-fidelity, picker, layout, or state-derived recap defect remains open.
