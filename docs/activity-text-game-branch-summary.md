# Activity Text Game Branch Summary

Last updated: 2026-05-29

Branch: `feat/activity-text-game`

Latest commit reviewed: `5838984 fix(activity): stabilize pilot flow`

Manual test entry point: `http://127.0.0.1:5173/?view=activities`

Backend endpoint: `http://127.0.0.1:8000`

## Original Implementation Requirements

The branch started from these product and engineering requirements:

- Build a standalone WonderLens frontend game surface in a feature worktree while following the existing fullstack demo repo conventions.
- Keep it in the same worktree and call the existing demo backend/provider APIs instead of creating a separate backend.
- Use the provided prototype device appearance as the visual companion, preserving the real device proportions.
- Include the physical device controls: top-right scroll control, left side grip, right side scroll button, and green start/select button.
- Support text input and text output only for this v1. STT, TTS, photo upload, and image recognition should stay out of this standalone surface for now.
- Use "activity" wording in the UI instead of "concept", except where the product phrase is explicitly "Core IB Key Concepts".
- Source backend-root `.env` and the backend-root `.elaborate-baton-*.json` credential file for live API verification without editing or printing secrets.
- Use the existing activity-package/import work as the conversion base where possible.
- Add a source-fidelity layer so converted `activity_*.md` files preserve the original activity intent and avoid lower-quality dialogue drift.
- Preserve existing Cat1 and Cat5 activity intent where appropriate, and add the missing Cat3 guided-build interaction.
- Use a touchless device-screen model: the screen is visual feedback only; navigation/selection happens through the physical scroll and start/select controls.
- Match the preferred layout from the UI reference: top green header, left activity library, device preview, metrics row, and bottom transcript.
- Support three representative pilot activities first:
  - Cat1: `activity_career_decision_role_play`
  - Cat3: `activity_guided_drawing`
  - Cat5: `activity_phoneme_treasure_hunt`
- Use a reusable workflow for adding new activities later: import package, preserve source intent, define screen layouts, add assets, and verify with tests/smoke.
- Move asset direction toward flat Nordic vector / Scandinavian minimal children's illustration:
  - no clay/plasticine look
  - no black backgrounds
  - no baked circular rims or contact sheets
  - separate reusable item/scene assets
  - blank or clean white backgrounds for reusable object/person assets
  - scene assets only where they are beat-aligned and style-consistent

## Implemented In This Branch

### Standalone Activity UI

- Added the `/?view=activities` frontend route for the standalone activity game surface.
- Added an activity library, device preview, transcript, and text input flow.
- Reworked the layout toward the preferred prototype screenshot: green top bar, left activity list, centered device preview, metrics row, and transcript area.
- Replaced "concept" UI wording with "activity" wording in the standalone surface.
- Added activity switching lockout while an activity is active. The user must exit the current activity before switching.
- Kept one active-session exit path after earlier duplicate-exit cleanup.
- Added transcript auto-scroll, focus return to the text input after sending, and input disabling when an activity is finished or when a device-only selection is active.
- Kept this surface text-only: no mic, TTS, camera, upload, or recognition controls are exposed.

### Device Appearance And Controls

- Implemented a prototype-shaped WonderLens device component with preserved proportions.
- Iterated side-control placement and shape based on the prototype image:
  - left green side grip
  - right top scroll rocker
  - lower green start/select button
- Split the top-right scroll control into upper/lower click zones for up/down activity or option navigation.
- Added visible arrow/function affordances around the scroll and start/select controls.
- Kept the device lens as a visual display, not a touchscreen-first interaction surface.

### Backend Activity Catalog And Recipes

- Added an activity catalog flow for the imported activity text game set.
- Imported/converted 12 activities into `backend/games/activity_*.md`.
- Added source-fidelity tests and guardrails for converted activity recipes.
- Added or tightened text-mode child-facing behavior for the representative pilot activities.
- Added text-only wording sanitation for device-bound words such as "card", "token", "tap", "click", "touch", and "point" where they were leaking into child-facing responses.
- Fixed earlier Recognition Pop wording that appended instructions like "type left, right, this, that".

### Representative Activity Behavior

Cat1, Career Decision Role Play:

- Uses a passive visual companion on the device screen.
- Keeps text input as the response path.
- Hardened firefighter decision sequence around:
  - smoke alarm / send help
  - water hose vs cooking oil
  - checking people outside vs running inside alone
- Added uncertainty handling so inputs like "I don't know" should repeat bounded choices instead of jumping to an unrelated round.

Cat3, Guided Drawing:

- Uses fixed guided drawing steps instead of open-ended "draw anything" prompting.
- Moves `Done` / `Help` selection onto the physical control model.
- Lets the scroll rocker switch the highlighted `Done` / `Help` option.
- Lets the green start/select button confirm the highlighted action.
- Disables free text while the device-only `Done` / `Help` selection is active.

Cat5, Phoneme Treasure Hunt:

- Uses B-starting word/object collection rather than object-noise prompting.
- Uses a crown-style picker model for selectable items.
- Lets the scroll rocker move the selected item.
- Lets the green start/select button confirm the selected item through the existing `photo_id` collection contract.
- Re-enables text input after item selection for the follow-up/detail response.
- Uses state-derived recap data from `sessionState.collected_photos` instead of static recap items.

### Asset And Screen Layout Infrastructure

- Added a manifest-driven activity lens renderer.
- Added layout modes for device-screen composition, including:
  - `single`
  - `singleText`
  - `choice2`
  - `choice3`
  - `picker`
- Added safe-area-aware visual composition inside the circular lens.
- Added item/beat manifest metadata for runtime assets.
- Added static runtime assets for the pilot activities and item sprites for selection flows.
- Added an asset style prompt at `frontend/public/activity-assets/prompts/wonderlens-activity-style.md`.
- Iterated image-generation direction with Codex internal imagegen pilots, but the app itself does not call image generation at runtime.

### Verification Added Or Run

The latest committed work reports these focused checks as passing:

- Backend:
  - `uv run pytest tests/test_activity_source_fidelity.py tests/test_generation_text_mode.py tests/test_activity_text_game_cat3.py tests/test_activity_text_game_turns.py -q`
  - 29 passed
- Backend lint:
  - `uv run ruff check agents/script_agent.py turn_handling/directive.py turn_handling/collection.py tests/test_activity_source_fidelity.py tests/test_activity_text_game_cat3.py tests/test_activity_text_game_turns.py tests/test_generation_text_mode.py`
- Frontend:
  - `npm test -- tests/ActivityGameApp.test.jsx tests/WonderLensDevice.test.jsx tests/activityAssets.test.js`
  - 27 passed
- Frontend lint:
  - `npx eslint src/activityGame/ActivityGameApp.jsx tests/ActivityGameApp.test.jsx`
- Frontend build:
  - `npm run build`
  - passed with the existing Vite large chunk warning
- Live checks:
  - backend/frontend restarted from this worktree
  - live API walkthroughs for Career, Guided Drawing, and Phoneme covered the latest known failure paths
  - earlier branch verification also ran `scripts/run_activity_text_smoke.py --timeout 120` with all 12 activities passing

## Key Files

Frontend activity surface:

- `frontend/src/activityGame/ActivityGameApp.jsx`
- `frontend/src/activityGame/WonderLensDevice.jsx`
- `frontend/src/activityGame/ActivityLens.jsx`
- `frontend/src/activityGame/ActivityLibrary.jsx`
- `frontend/src/activityGame/ActivityTranscript.jsx`
- `frontend/src/activityGame/ActivityTextInput.jsx`
- `frontend/src/activityGame/activityAssets.js`
- `frontend/src/activityGame/useActivityTextSession.js`
- `frontend/src/index.css`

Frontend assets:

- `frontend/public/activity-assets/activity-assets.manifest.json`
- `frontend/public/activity-assets/prompts/wonderlens-activity-style.md`
- `frontend/public/activity-assets/activity_career_decision_role_play/`
- `frontend/public/activity-assets/activity_guided_drawing/`
- `frontend/public/activity-assets/activity_phoneme_treasure_hunt/`

Backend activity/runtime:

- `backend/activity_catalog.py`
- `backend/entity_registry.py`
- `backend/games/activity_*.md`
- `backend/agents/script_agent.py`
- `backend/agents/turn_director.py`
- `backend/turn_handling/directive.py`
- `backend/turn_handling/collection.py`
- `backend/turn_handling/generation.py`

Plans/goals:

- `docs/plans/2026-05-27-activity-text-game.md`
- `docs/plans/2026-05-29-three-activity-flow-layout-fixes.md`
- `docs/plans/2026-05-29-activity-assets-touchless-controls.md`
- `goals/2026-05-29-three-activity-flow-layout-fixes-goal.md`
- `goals/2026-05-29-activity-assets-touchless-controls-goal.md`

## Not Yet Implemented Or Still Needs Improvement

### Dialogue And Flow Robustness

- The app still depends on live LLM generation for many child-facing responses. Deterministic guards cover the known issues, but they do not make every line fully scripted.
- A stronger demo-safe option would be scripted turn templates for the three pilot activities, or stricter post-processing for each step.
- Source-fidelity coverage is strongest for the manually tuned activities. The remaining imported activities still need deeper activity-by-activity review if they become demo-critical.
- The current tests cover known regressions, but they cannot prove every live LLM branch will stay aligned under all child responses.

### Assets

- The final approved asset style is not fully applied across all runtime assets.
- Several runtime assets were generated or committed before the final flat Nordic direction was settled.
- Full scene assets are not complete for every beat. The current implementation is stronger for item/object assets and layout infrastructure than for rich beat-matched scenes.
- The branch has imagegen pilots and a style prompt, but it has not fully regenerated all pilot activity scene assets in the final blank-white flat Nordic style.
- There is no complete automated "new activity asset pack" generator that produces final approved assets, manifest entries, item catalogs, and screenshots in one visible workflow.

### Interaction Polish

- Cat3 and Cat5 use the physical scroll/select model, but the selection UI could still be polished further with better motion, clearer focus transitions, and less visual blocking.
- The crown-style picker is implemented as a browser approximation. There is no real hardware crown integration.
- The device screen currently supports manifest-driven layouts, but multi-asset scene composition for every activity is still a developing convention.

### Product Scope Deferred From V1

- STT/audio input is not exposed.
- TTS/audio output is not exposed.
- Photo upload and image recognition are not exposed.
- Real device integration is not implemented.
- Live activity metrics in the UI are still lightweight demo metrics and may need deeper connection to backend latency/token data.

### Testing And Operations

- Latest live manual verification focused on Career Decision Role Play, Guided Drawing, and Phoneme Treasure Hunt. Earlier smoke covered all 12 activities, but not every edge path in every activity.
- Broader responsive QA is still needed across browser sizes and target devices.
- `npm run build` passes but still emits the existing Vite large chunk warning.
- The branch summary itself is documentation-only and has not changed runtime behavior.

## Suggested Next Steps

1. Decide whether the three pilot activities should become deterministic scripted demos or remain live-LLM demos with stronger guardrails.
2. Regenerate and replace only the three pilot activities' runtime assets in the final flat Nordic style before scaling to all 12.
3. Add a visible new-activity authoring workflow:
   - import activity package
   - validate source fidelity
   - define beat layouts
   - generate/select assets
   - add item catalog
   - run smoke and browser checks
4. Add browser screenshot regression checks for the three representative interaction modes.
5. Audit the remaining nine activities for source drift and asset/dialogue mismatch before using them in a formal demo.
