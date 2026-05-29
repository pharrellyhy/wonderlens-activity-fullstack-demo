# Three-Activity Asset and Touchless Control Plan

Status: Completed
Date: 2026-05-29

## Objective

Implement a controlled runtime pilot for the standalone WonderLens activity text game using three representative activities:

- Cat1: `activity_career_decision_role_play`
- Cat3: `activity_guided_drawing`
- Cat5: `activity_phoneme_treasure_hunt`

The pilot must replace only the needed runtime display assets for those representatives, align their device-screen layouts with the approved flat Nordic asset direction, and make Cat5 item selection use the same touchless physical-control model as Cat3. Completion requires proving that all 12 activities still work through catalog, asset, frontend, backend, live-smoke, and browser verification.

## Current Evidence

The worktree is:

```text
/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game
```

Initial relevant implementation:

- `frontend/public/activity-assets/activity-assets.manifest.json` maps all 12 activity ids to beat assets; this pilot adds layout metadata only for the three representative activities.
- `frontend/src/activityGame/activityAssets.js` normalizes `screenLayoutForBeat`, beat ids, layout modes, and device-scroll metadata.
- `frontend/src/activityGame/ActivityGameApp.jsx` already supports Cat3 `Done`/`Help` selection through the right scroll rocker and green start/select button.
- `frontend/src/activityGame/ActivityLens.jsx` renders visual device-screen layouts without visible touch targets.
- `scripts/run_activity_text_smoke.py` has live-smoke coverage for all 12 imported activity ids.
- `tests/test_activity_text_game_asset_contract.py` verifies manifest/catalog parity, runtime recipe beats, item existence, no contact-sheet sources, and item sizing/black-padding constraints.

## Execution Result

Completed on 2026-05-29.

- Cat1 Career Decision Role Play uses passive beat visuals only; text input remains the response path.
- Cat3 Guided Drawing keeps `Done`/`Help` selection on the device, moved by the right scroll rocker and confirmed by the green start/select button.
- Cat5 Phoneme Treasure Hunt uses right scroll rocker highlight plus green start/select for collection items, then restores text input for follow-up detail.
- Cat5 runtime round item sets now match the approved visual sets: `ball/cup/book`, `banana/spoon/leaf`, and `basket/toy car/sock`.
- Pilot layout metadata and regenerated assets are scoped to the three representative activities; non-representative activity assets stay outside this pilot.
- Live smoke passed for all 12 activities, and browser verification passed for the three representative interactions.

Recent visual iteration established the active asset direction:

- Blank clean white or barely tinted white background for reusable item, object, and character assets.
- Banana-like flat Nordic vector treatment: broad flat color fills, sparse short texture dashes, minimal facial marks.
- No clay, plasticine, toy render, bevels, glossy highlights, heavy shadows, black backgrounds, circular rims, contact sheets, or baked lens borders.
- Object-only activity clusters are more reliable than person-plus-object scenes for maintaining visual consistency.
- Firefighter/person assets are prone to helmet shadow bands and panel strokes, so firefighter scenes should favor object-only clusters unless a character is essential.

The active style contract is:

```text
frontend/public/activity-assets/prompts/wonderlens-activity-style.md
```

## Settled Interaction Model

### Cat1: Passive Visual Companion

Representative: `activity_career_decision_role_play`.

Screen behavior:

- Show beat-matched scene/object-cluster imagery only.
- Do not expose selectable screen choices during active Cat1 turns.
- Use text input for the child response.

Device controls:

- Before starting, the top-right scroll rocker moves activity selection up/down.
- During an active Cat1 session, activity selection is locked.
- The green start/select button starts the activity only; it should not confirm in-screen choices during Cat1.

### Cat3: Build Checkpoint

Representative: `activity_guided_drawing`.

Screen behavior:

- Show the current drawing/build step visual.
- Overlay a compact `Done`/`Help` selector only during `STEP_3_BUILD_*`.
- Keep text input enabled for freeform notes.

Device controls:

- Top-right scroll rocker cycles highlighted option: `Done` <-> `Help`.
- Green start/select button confirms the highlighted option and sends `done` or `help`.

### Cat5: Item Collection

Representative: `activity_phoneme_treasure_hunt`.

Screen behavior:

- Show 2-3 item assets as selectable visual choices for collection phases.
- Highlight exactly one item at a time.
- Disable typed text input during item selection.
- Re-enable typed input after the selected item is recorded, for the detail/follow-up answer.

Device controls:

- Top-right scroll rocker moves the highlight through available items.
- Green start/select button confirms the highlighted item and sends the existing `photo_id` collection contract through `sendCollectionItem`.
- Screen touch/click must not be the primary interaction. Hidden tester click targets may be removed. If retained for automated or browser convenience, they must not be the only usable path and must not create a visible touch affordance.

## Asset Architecture

Use committed static assets only. Runtime must not call image generation APIs.

Generate candidate bitmap assets with Codex built-in imagegen, then copy selected outputs from:

```text
/Users/pharrelly/.codex/generated_images/...
```

into:

```text
frontend/public/activity-assets/<activity_id>/
frontend/public/activity-assets/<activity_id>/items/
```

Keep generated originals in place. Resize final committed PNGs to 512x512. Do not create or keep `frontend/public/activity-assets/_sources/`.

### Cat1 Asset Direction

For `activity_career_decision_role_play`, prefer object-only safety clusters:

- helmet without badge/panel strokes
- hose
- water drop
- alarm bell
- safe house/outside
- phone/call icon only if the source dialogue requires it

Avoid large firefighter people in runtime beat scenes unless a beat explicitly needs a helper character. If using a helper, it must match the simplified flat person pilot, not the older storybook/clay direction.

### Cat3 Asset Direction

For `activity_guided_drawing`, use simple build-step visuals:

- paper
- pencil
- shape/line/starter mark
- completion/celebration mark

The screen should not repeat long rules already shown in the transcript. It should support the checkpoint state and leave the transcript as the source of instruction text.

### Cat5 Asset Direction

For `activity_phoneme_treasure_hunt`, use separate item assets that match the collection catalog and source dialogue:

- Round 1: ball, cup, book
- Round 2: banana, spoon, leaf
- Round 3: basket, toy car, sock
- Synthesis/recap may reuse selected item assets in composed layouts.

Use object clusters and individual item PNGs, not a contact sheet.

## Implementation Areas

Frontend interaction files:

- `frontend/src/activityGame/ActivityGameApp.jsx`
- `frontend/src/activityGame/ActivityLens.jsx`
- `frontend/src/activityGame/WonderLensDevice.jsx`
- `frontend/src/activityGame/activityAssets.js`
- `frontend/src/index.css`
- `frontend/tests/ActivityGameApp.test.jsx`
- `frontend/tests/WonderLensDevice.test.jsx`
- `frontend/tests/activityAssets.test.js`

Asset and manifest files:

- `frontend/public/activity-assets/activity-assets.manifest.json`
- `frontend/public/activity-assets/prompts/wonderlens-activity-style.md`
- `frontend/public/activity-assets/activity_career_decision_role_play/**`
- `frontend/public/activity-assets/activity_guided_drawing/**`
- `frontend/public/activity-assets/activity_phoneme_treasure_hunt/**`
- `scripts/build_activity_screen_assets.py`, only if the current build script needs to stop overwriting individually generated item art.

Backend files should be touched only when a source-dialogue or live-contract mismatch is found during verification:

- `backend/games/activity_career_decision_role_play.md`
- `backend/games/activity_guided_drawing.md`
- `backend/games/activity_phoneme_treasure_hunt.md`
- `backend/tests/test_activity_source_fidelity.py`
- `backend/tests/test_activity_text_game_cat3.py`
- `scripts/run_activity_text_smoke.py`

## Delegated-Agent Rules

The user explicitly requested delegated-agent rules for this goal. Delegation is allowed, but only for independent work with clear ownership.

Allowed delegated-agent tasks:

- Asset audit agent: inspect current runtime assets and manifest entries for the three representative activities, then report exact files to replace.
- Cat1/Cat3/Cat5 asset-generation agents: propose imagegen prompts and candidate selections for one representative activity each.
- Interaction agent: inspect Cat3/Cat5 control code and propose the minimal Cat5 scroll-highlight/select change.
- Verification agent: independently run focused tests or review screenshots after integration.

Rules:

- Delegated agents must not edit `.env`, credential JSON files, secrets, tokens, or provider configuration.
- Delegated agents must not run destructive git commands or revert user changes.
- Delegated agents must not edit the same file concurrently without a local integrator reconciling ownership first.
- Delegated agents may generate preview images, but the main executor must select, copy, resize, commit references, and verify final runtime assets.
- The main executor remains responsible for final integration, browser verification, live smoke, and deciding whether the completion gate is satisfied.

## Verification Strategy

The implementation is not complete until all activities pass, not only the three representatives.

Automated frontend checks should cover:

- Cat1 active session does not expose in-screen selection controls.
- Cat3 scroll changes highlighted `Done`/`Help`; start/select sends the highlighted text action.
- Cat5 scroll changes highlighted item; start/select sends the selected item through `sendCollectionItem`.
- Cat5 typed input is disabled only during item selection and re-enabled after item collection.
- All manifest assets exist, are 512x512 PNGs, and keep valid layout metadata.

Automated backend/contract checks should cover:

- All 12 activity catalog entries still match manifest entries.
- Runtime recipe beat ids still match manifest beat ids.
- Cat5 collection catalog item images exist and use activity-specific assets.
- Source-fidelity tests still protect the fixed visible sequences for activities such as animal sound, partial reveal, recognition pop, career decision, guided drawing, and phoneme treasure.

Live verification must include:

- `scripts/run_activity_text_smoke.py --timeout 120` against the running backend, with all 12 activities passing.
- Browser verification at `http://127.0.0.1:5173/?view=activities` or `http://localhost:5173/?view=activities`.
- Manual/browser walkthrough of the three representative activities:
  - Cat1: start career decision, confirm text input remains the response path and no screen selection is required.
  - Cat3: start guided drawing, scroll `Done`/`Help`, confirm with start/select.
  - Cat5: start phoneme treasure, scroll item highlight, confirm with start/select, then confirm text input returns for the follow-up.

## Live Provider Credential Rule

Live-smoke checks require the existing backend provider credentials. Do not edit, print, copy, or commit secret values.

Use this pattern from a shell that will run the backend:

```bash
MAIN_REPO_ROOT="/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/backend"
set -a
source "$MAIN_REPO_ROOT/.env"
set +a
export GOOGLE_APPLICATION_CREDENTIALS="$(ls "$MAIN_REPO_ROOT"/.elaborate-baton-*.json | head -n 1)"
```

Here `MAIN_REPO_ROOT` points to the backend root because the `.env` and `.elaborate-baton-*.json` credential file live there.

## Non-Goals

- Do not add STT, TTS, camera, photo upload, or live image recognition controls to this standalone text-game surface.
- Do not replace all 12 activity asset sets in this goal.
- Do not change the backend provider architecture.
- Do not reintroduce contact sheets, baked circular masks, black backgrounds, or clay/light-3D visual language.
- Do not make the device screen touch-first.

## Open Risks

- Imagegen may still produce storybook or helmet-panel artifacts for firefighter characters. Prefer object-only scenes and regenerate if the visual audit fails.
- `scripts/build_activity_screen_assets.py` may overwrite hand-selected item assets if rerun without adjustment. Inspect before using it.
- The manifest currently carries older style naming in some metadata. If touched, update it to match the flat Nordic direction without causing broad unrelated churn.
- Browser automation should verify actual visible state because the circular device crop can hide asset edge issues that file-level checks will not catch.

## Completion Gate

The implementation can be considered complete only when:

- The three representative runtime asset sets are updated and visually match the flat Nordic blank-white/flat-fill style contract.
- Cat1, Cat3, and Cat5 interaction behavior matches the touchless contracts above.
- The required automated frontend/backend checks pass.
- Live smoke passes for all 12 activities.
- Browser verification confirms the three representative activities behave correctly on the device preview.
- `HANDOFF.md`, `docs/plans/README.md`, and `goals/README.md` reflect the final status after execution.
