# Activity Assets and Touchless Controls Goal

## Mode

Plan-backed

## Objective

Implement the three-representative activity asset/control pilot for the standalone WonderLens activity text game:

- Cat1: `activity_career_decision_role_play`
- Cat3: `activity_guided_drawing`
- Cat5: `activity_phoneme_treasure_hunt`

Replace the selected runtime display assets with the approved flat Nordic blank-white style, make Cat5 item collection operable through the device scroll rocker plus green start/select button, and verify all 12 activities still work before marking the goal complete.

## Design Source

Authoritative design source:

```text
docs/plans/2026-05-29-activity-assets-touchless-controls.md
```

The plan is authoritative for design rationale, activity choices, asset direction, interaction contracts, file ownership, and verification context. This goal is authoritative for hard constraints, required checks, credential handling, and the final completion gate.

If the plan and goal conflict, stop and document the conflict before changing behavior.

## Hard Constraints

- Work in `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game`.
- Keep the standalone activity game text-only: no STT, TTS, mic, camera, photo upload, or image-recognition controls.
- Runtime display assets must be committed static files under `frontend/public/activity-assets/`; runtime must not call image generation APIs.
- Use Codex built-in imagegen for new bitmap pilots/assets. Do not use a separate image API or external image generation service.
- Preserve original generated images under `/Users/pharrelly/.codex/generated_images/...`; copy selected outputs into the repo when needed.
- Do not create or keep contact-sheet source directories such as `frontend/public/activity-assets/_sources/`.
- Do not edit, print, copy, or commit `.env`, `.elaborate-baton-*.json`, tokens, provider secrets, or credential values.
- Never revert user changes or run destructive git commands.
- Do not mark the goal complete until all 12 activities pass the required live-smoke verification.

## Required Scope

- Update runtime assets and manifest/layout metadata for the three representative activities only, unless a narrow shared manifest/style fix is required.
- Ensure Cat1 remains a passive visual companion with text input as the response path.
- Ensure Cat3 uses scroll-highlight plus start/select for `Done`/`Help`.
- Ensure Cat5 uses scroll-highlight plus start/select for item collection, then restores text input for follow-up detail.
- Update frontend tests and asset-contract tests to cover the new touchless Cat5 behavior and asset expectations.
- Update `HANDOFF.md`, `docs/plans/README.md`, and `goals/README.md` with final execution status.

## Execution Rules

- Inspect current code and assets before editing.
- Use `apply_patch` for manual code/doc edits.
- Keep changes narrowly scoped to the goal.
- Prefer existing repo patterns and helper APIs.
- Add or update tests before changing behavior where practical.
- Run the smallest relevant check after each meaningful change.
- Stop on failing checks, diagnose, and fix before broadening scope.

## Delegated-Agent Rules

The user explicitly requested delegated-agent rules.

Delegated agents may be used only for independent work:

- auditing current assets/manifest entries for one representative activity;
- generating or reviewing candidate image prompts/assets for one representative activity;
- inspecting Cat3/Cat5 interaction code and proposing a minimal implementation path;
- independently running focused verification or reviewing screenshots.

Delegated agents must not edit secrets, credential files, provider config, or overlapping files concurrently. The main executor must integrate all edits, select final runtime assets, run final checks, perform live/browser verification, and decide whether the completion gate is satisfied.

## Mandatory Ordering

1. Confirm current manifest, catalog, and interaction behavior for Cat1/Cat3/Cat5.
2. Add or update focused tests for Cat5 scroll-highlight/start-select behavior before implementing that behavior.
3. Generate/select/copy/resize representative assets and update manifest/layout metadata.
4. Run frontend and asset-contract checks.
5. Start backend with the credential rule below and run live smoke for all 12 activities.
6. Run browser verification for the three representative activities.
7. Update status docs only after verification evidence is known.

## Live Provider Credential Rule

For live backend verification, use the backend root as the credential root:

```bash
MAIN_REPO_ROOT="/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/backend"
set -a
source "$MAIN_REPO_ROOT/.env"
set +a
export GOOGLE_APPLICATION_CREDENTIALS="$(ls "$MAIN_REPO_ROOT"/.elaborate-baton-*.json | head -n 1)"
```

Do not echo, print, edit, copy, or commit any secret value.

## Preconditions

- The worktree exists and contains the current standalone activity text-game feature work.
- `frontend/package.json` and backend `uv` tooling are available.
- Backend credentials exist in the backend root for live-smoke verification.
- If a dev server or backend is already running, reuse or restart it intentionally; do not leave required sessions running at final response.

## Success Criteria

- `activity_career_decision_role_play`, `activity_guided_drawing`, and `activity_phoneme_treasure_hunt` use runtime assets that match the flat Nordic blank-white/broad-flat-fill style direction.
- Assets are separate scene/item PNGs, 512x512, without black padding, baked circular rims, oval masks, or contact-sheet runtime sources.
- Cat1 has no active in-screen choice requirement.
- Cat3 `Done`/`Help` selection is controlled by scroll plus start/select.
- Cat5 item selection is controlled by scroll plus start/select and still sends the existing collection item contract.
- Typed input is disabled only during Cat5 item selection and re-enabled for detail/follow-up turns.
- All 12 activities pass live smoke.

## Required Checks

Run from repo root unless a command explicitly changes directory:

```bash
cd frontend
npm test -- --run tests/activityAssets.test.js tests/ActivityGameApp.test.jsx tests/WonderLensDevice.test.jsx
npx eslint src/activityGame/ActivityGameApp.jsx src/activityGame/ActivityLens.jsx src/activityGame/WonderLensDevice.jsx tests/ActivityGameApp.test.jsx tests/activityAssets.test.js
npm run build
cd ..
```

```bash
uv run pytest backend/tests/test_activity_source_fidelity.py backend/tests/test_activity_text_game_cat3.py tests/test_activity_text_smoke.py tests/test_activity_text_game_asset_contract.py -q
uv run ruff check backend/tests/test_activity_source_fidelity.py backend/tests/test_activity_text_game_cat3.py scripts/run_activity_text_smoke.py tests/test_activity_text_smoke.py tests/test_activity_text_game_asset_contract.py
git diff --check
```

After starting the backend with the credential rule:

```bash
uv run python scripts/run_activity_text_smoke.py --timeout 120
```

Also run browser verification at:

```text
http://127.0.0.1:5173/?view=activities
```

or:

```text
http://localhost:5173/?view=activities
```

Browser verification must cover Cat1 career decision, Cat3 guided drawing, and Cat5 phoneme treasure hunt.

## Final Completion Gate

Set the goal status to complete only after:

- all required checks pass;
- live smoke passes for all 12 activities;
- browser verification confirms the three representative interactions;
- final docs/status files are updated;
- no required backend/frontend/server session is left running for the user request;
- remaining risks, if any, are documented in the final response.

If the same blocker prevents progress for three consecutive goal turns, set the goal status to blocked and document the blocker.

## Goal Invocation

```text
/goal Implement goals/2026-05-29-activity-assets-touchless-controls-goal.md. Stop only when its completion gate is satisfied or a blocker is documented.
```
