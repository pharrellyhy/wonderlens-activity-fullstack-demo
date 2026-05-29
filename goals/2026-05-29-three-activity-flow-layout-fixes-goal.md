# Three Activity Flow and Layout Fixes Goal

## Mode

Plan-backed.

Use this file as the Codex goal-mode execution contract. It defines the outcome, constraints, checks, and stop condition for a fresh session.

## Objective

Fix the Cat1, Cat3, and Cat5 representative activity flow and device-screen layout defects before generating any new scene assets.

The finished system must:

- preserve source intent for `activity_career_decision_role_play`, `activity_guided_drawing`, and `activity_phoneme_treasure_hunt`;
- align device-screen layouts with the UI design doc section `4. 布局`;
- keep the standalone frontend text-only and touchless, using the physical scroll rocker plus green start/select button for screen choices;
- verify all 12 activities still pass live smoke before the goal is complete.

## Design Source

Authoritative implementation plan:

```text
docs/plans/2026-05-29-three-activity-flow-layout-fixes.md
```

Supporting reference:

```text
/Users/pharrelly/Downloads/活动库视觉规范.docx
```

Use the plan for product behavior, file ownership, tests, browser checks, and sequencing. Use this goal file for hard constraints, delegated-agent rules, credential handling, and the final completion gate.

If this goal and the plan conflict, this goal wins for safety and completion gates. If the plan and current code conflict, inspect the code and make the smallest change that satisfies the goal.

## Design Decisions

- Fix recipe/source fidelity before layout polish or asset generation.
- Do not regenerate scene assets in this phase. Existing static images may remain as placeholders until behavior and layout are correct.
- The UI design doc layout vocabulary is the target: one centered image, optional image plus text, two-image left/right choice, three-image triangular choice, and scroll/picker for three or more choices. Avoid four-up runtime grids.
- Cat1 Career Decision Role Play remains text-response only with passive beat visuals. No active screen picker should appear.
- Cat3 Guided Drawing uses a fixed step-by-step drawing sequence. `Done` and `Help` are selected with the scroll rocker and confirmed with the green start/select button.
- Cat5 Phoneme Treasure Hunt asks for B-starting items, uses a Digital Crown-style picker, and composes recap/celebration from actual selected items.

## Hard Constraints

- Work in `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game`.
- Do not generate or replace scene assets until this goal's completion gate passes.
- Keep the standalone activity game text-only: no STT, TTS, mic, camera, photo upload, or image-recognition controls.
- Do not make screen touch/click the primary interaction.
- Do not edit, print, copy, or commit `.env`, `.elaborate-baton-*.json`, tokens, provider secrets, or credential values.
- Do not perform destructive git commands, broad formatting sweeps, dependency upgrades, or unrelated refactors.
- Do not revert user changes. Work with the existing dirty worktree.
- Do not mark complete until live smoke passes for all 12 activities and browser verification covers the three representatives.

## Required Scope

Cover these outcome areas:

- source-fidelity and child-facing language for the three representative activities;
- layout primitives and renderer behavior for `single`, `singleText`, `choice2`, `choice3`, and `picker`;
- Cat5 dynamic recap using `sessionState.collected_photos`, not static manifest items;
- Cat3 compact non-blocking `Done`/`Help` selector;
- Cat1 uncertainty handling and screen-step sync;
- focused backend/frontend tests and live/browser verification.

The detailed task breakdown lives in the source plan. Do not duplicate the old asset-generation goal. This goal supersedes any earlier claim that the three representative activity work is complete when behavior/layout defects remain open.

## Execution Rules

- Read the source plan before editing.
- Use TDD for behavior changes where practical.
- Use `apply_patch` for manual code and doc edits.
- Keep changes narrowly scoped to this goal.
- Run the smallest relevant check after each coherent change.
- Stop on failing checks, diagnose root cause, and fix before broadening scope.
- Update `HANDOFF.md` and `goals/README.md` with final status only after verification evidence is known.

## Delegated-Agent Rules

The user explicitly requested delegated-agent rules for this goal.

Delegated agents may be used only for independent work with disjoint ownership:

- recipe/source-fidelity audit for one representative activity;
- frontend layout or interaction code inspection without editing overlapping files;
- focused implementation of one isolated activity flow after tests are written;
- independent screenshot/browser review;
- focused backend or frontend test verification.

Delegated agents must not:

- edit `.env`, credential JSON files, secrets, tokens, provider config, or production data;
- run destructive git commands or revert user changes;
- edit the same file concurrently with another agent;
- generate or replace scene assets during this goal;
- decide final completion status.

The main executor must integrate all edits, resolve file ownership, run final automated checks, perform live/browser verification, update status docs, and decide whether the completion gate is satisfied.

## Mandatory Ordering

1. Confirm the source plan exists and read it.
2. Fix source-fidelity and child-facing wording before scene/layout asset work.
3. Implement layout primitives before activity-specific picker and selector polish.
4. Fix Cat5, Cat3, and Cat1 activity behavior against focused tests.
5. Run focused automated backend/frontend checks.
6. Run live smoke only after focused automated checks pass.
7. Run browser walkthrough only after backend and frontend are running against the verified code.
8. Do not start scene asset generation until this goal is complete.

## Live Provider Credential Rule

For live backend verification, source general API keys and environment variables from the backend root, and point Google/Vertex AI at the backend-root `.elaborate-baton-*.json` credential file:

```bash
MAIN_REPO_ROOT="/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/backend"
set -a
source "$MAIN_REPO_ROOT/.env"
set +a
export GOOGLE_APPLICATION_CREDENTIALS="$(ls "$MAIN_REPO_ROOT"/.elaborate-baton-*.json | head -n 1)"
```

Do not echo, print, edit, copy, or commit any secret value.

## Preconditions

- The worktree exists at `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game`.
- The source plan exists at `docs/plans/2026-05-29-three-activity-flow-layout-fixes.md`.
- `frontend/package.json`, backend `uv` tooling, and `scripts/run_activity_text_smoke.py` are available.
- Backend provider credentials exist in the backend root for live-smoke verification.
- If backend or frontend servers are already running, reuse or restart intentionally and do not leave unexpected sessions running at completion.

## Success Criteria

### Source Fidelity

- Career Decision Role Play preserves the firefighter sequence: smoke alarm decision, water hose vs cooking oil, check people outside vs run inside alone.
- Career Decision Role Play handles "I don't know" by staying on the current bounded decision instead of jumping to another beat.
- Guided Drawing gives a fixed step-by-step drawing sequence and does not ask the child to draw randomly.
- Guided Drawing `Help` repeats or simplifies the current step rather than inventing a new drawing.
- Phoneme Treasure Hunt asks for B-starting items and does not ask what noise an object makes.
- Child-facing dialogue avoids device-bound words such as `card`, `cards`, `token`, `tap`, `touch`, `point`, and `click` unless a test explicitly allows a non-child-facing source reference.

### Layout And Interaction

- `single`, `singleText`, `choice2`, `choice3`, and `picker` layouts are normalized and rendered intentionally.
- Four visible choice images are not rendered as a crowded four-up grid.
- Cat5 uses a Digital Crown-style picker: selected item centered, adjacent items visible but de-emphasized, scroll rocker changes selection, and green start/select confirms.
- Cat5 typed input is disabled only during item selection and returns for follow-up/detail turns.
- Cat5 synthesis/celebration uses actual `sessionState.collected_photos` in backend order.
- Cat3 `Done`/`Help` selector is compact and non-blocking, with scroll/select control.
- Cat1 does not expose an in-screen picker and its device visual matches the current step.

### Verification

- Focused backend tests pass.
- Focused frontend tests pass.
- Live smoke passes for all 12 activities.
- Browser walkthrough passes for Career Decision Role Play, Guided Drawing, and Phoneme Treasure Hunt.

## Required Checks

Run from repo root unless a command explicitly changes directory.

Backend:

```bash
cd backend
uv run pytest tests/test_activity_source_fidelity.py tests/test_generation_text_mode.py tests/test_activity_text_game_cat3.py -q
cd ..
```

Frontend:

```bash
cd frontend
npm test -- tests/ActivityGameApp.test.jsx tests/WonderLensDevice.test.jsx tests/activityAssets.test.js
npx eslint src/activityGame/ActivityGameApp.jsx src/activityGame/ActivityLens.jsx src/activityGame/WonderLensDevice.jsx src/activityGame/activityAssets.js tests/ActivityGameApp.test.jsx tests/WonderLensDevice.test.jsx tests/activityAssets.test.js
npm run build
cd ..
```

Repository:

```bash
git diff --check
```

Live smoke after starting the backend with the credential rule:

```bash
uv run python scripts/run_activity_text_smoke.py --timeout 120
```

Browser verification at:

```text
http://127.0.0.1:5173/?view=activities
```

or:

```text
http://localhost:5173/?view=activities
```

Browser verification must cover:

- Career Decision Role Play: no child-facing `card` or `token` wording, "I don't know" repeats the same bounded decision, and screen beat follows dialogue.
- Guided Drawing: fixed step-by-step instructions, compact `Done`/`Help`, `Help` stays on current step.
- Phoneme Treasure Hunt: B-starting prompt, Digital Crown-style picker, celebration uses actual selected items.

## Final Completion Gate

Set the goal status to complete only after:

- required scope is implemented or an explicit user-approved deferral is documented;
- all success criteria are met;
- required automated checks pass;
- live smoke passes for all 12 activities;
- browser verification confirms the three representative interactions;
- `HANDOFF.md` and `goals/README.md` are updated with factual status;
- no required backend/frontend/server session is left running unexpectedly;
- no secrets are included in artifacts.

If the same blocker prevents progress for three consecutive goal turns, set the goal status to blocked and document the blocker.

## Goal Invocation

```text
/goal Implement goals/2026-05-29-three-activity-flow-layout-fixes-goal.md. Stop only when its completion gate is satisfied or a blocker is documented.
```
