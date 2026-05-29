# Session Handoff

Last updated: 2026-05-29

---

## Three-Activity Asset and Touchless Control Implementation

**Problem**: The approved representative pilot needed to move from plan to verified implementation: flat Nordic runtime assets for the three selected activities, Cat5 touchless item selection through the device controls, Cat1/Cat3 behavior preservation, and all-activity live smoke before declaring the goal complete.

**Solution**: Implemented the three-activity pilot in the feature worktree. Cat1 Career Decision Role Play remains a passive visual companion with text as the response path. Cat3 Guided Drawing keeps `Done`/`Help` on the device and uses the right scroll rocker plus green start/select button. Cat5 Phoneme Treasure Hunt now uses the same scroll-highlight/start-select model for item collection, keeps typed input disabled only during item selection, and re-enables text input for the detail prompt while preserving the selected item highlight. The Cat5 runtime round item sets are now deterministic and match the approved manifest/art sets.

**Edits**:
- `frontend/public/activity-assets/activity_career_decision_role_play/**`, `activity_guided_drawing/**`, `activity_phoneme_treasure_hunt/**` — replaced only the three representative runtime assets and added separate item assets where needed.
- `frontend/public/activity-assets/activity-assets.manifest.json` — added pilot layout metadata only for the three representative activities.
- `backend/entity_registry.py` — added deterministic Cat5 round sets for `activity_phoneme_treasure_hunt`.
- `frontend/src/activityGame/ActivityGameApp.jsx`, `ActivityLens.jsx`, `WonderLensDevice.jsx`, `frontend/src/index.css` — implemented touchless Cat5 item selection and preserved Cat3 physical-control selection.
- `frontend/tests/ActivityGameApp.test.jsx`, `frontend/tests/WonderLensDevice.test.jsx`, `frontend/tests/activityAssets.test.js`, `tests/test_activity_text_game_asset_contract.py` — added/updated regressions for pilot scope, Cat5 scroll/select, Cat5 text unlock, selected item continuity, and asset contracts.

**NOT Changed**:
- Standalone activity mode remains text-only; no STT, TTS, mic, camera, photo upload, or image-recognition controls were added.
- Non-representative activity PNGs and manifest layout metadata were restored to stay outside the three-activity pilot scope.
- Runtime uses committed static PNGs only; no runtime image generation API is called.

**Verification**:
- `npm test -- --run tests/activityAssets.test.js tests/ActivityGameApp.test.jsx tests/WonderLensDevice.test.jsx` — 20 passed.
- `npx eslint src/activityGame/ActivityGameApp.jsx src/activityGame/ActivityLens.jsx src/activityGame/WonderLensDevice.jsx tests/ActivityGameApp.test.jsx tests/activityAssets.test.js` — passed.
- `npm run build` — passed; Vite emitted the existing large chunk warning.
- `uv run pytest backend/tests/test_activity_source_fidelity.py backend/tests/test_activity_text_game_cat3.py tests/test_activity_text_smoke.py tests/test_activity_text_game_asset_contract.py -q` — 25 passed.
- `uv run ruff check backend/tests/test_activity_source_fidelity.py backend/tests/test_activity_text_game_cat3.py scripts/run_activity_text_smoke.py tests/test_activity_text_smoke.py tests/test_activity_text_game_asset_contract.py backend/entity_registry.py` — passed.
- `git diff --check` — passed.
- Restarted backend from this worktree while sourcing the backend-root `.env` and Google credential JSON path without printing secret values.
- `uv run python scripts/run_activity_text_smoke.py --timeout 120` — 12 passed, 0 failed.
- Browser verification at `http://127.0.0.1:5173/?view=activities` passed for Cat1/Cat3/Cat5; screenshots: `/tmp/wonderlens-browser-verification/career-cat1-passive.png`, `/tmp/wonderlens-browser-verification/guided-cat3-scroll-select.png`, `/tmp/wonderlens-browser-verification/phoneme-cat5-scroll-select.png`.

---

## Three-Activity Plan-Backed Goal

**Problem**: The next implementation pass needed a concrete execution contract for the approved representative rollout: Cat1/Cat3/Cat5 assets, Cat5 touchless controls, delegated-agent boundaries, and a completion rule that verifies all 12 activities before declaring the goal achieved.

**Solution**: Created a plan-backed goal pair for the three representative activities: `activity_career_decision_role_play`, `activity_guided_drawing`, and `activity_phoneme_treasure_hunt`. The plan records the settled interaction model for Cat1 passive visuals, Cat3 `Done`/`Help` scroll-confirm, and Cat5 item scroll-confirm. The goal records hard constraints, delegated-agent rules, live credential handling, required checks, and the final completion gate requiring all 12 activities to pass live smoke.

**Edits**:
- `docs/plans/2026-05-29-activity-assets-touchless-controls.md` — added the detailed implementation plan.
- `goals/2026-05-29-activity-assets-touchless-controls-goal.md` — added the plan-backed goal file and goal invocation.
- `docs/plans/README.md` — added the plan index for plan-goal workflow entries.
- `goals/README.md` — added the goal index.

**NOT Changed**:
- No runtime assets, frontend code, backend code, or interaction behavior were changed in this pass.
- No active `/goal` run was started.
- No secrets or credential files were read or modified.

**Verification**:
- `git diff --check -- docs/plans/2026-05-29-activity-assets-touchless-controls.md goals/2026-05-29-activity-assets-touchless-controls-goal.md docs/plans/README.md goals/README.md` — passed.

---

## Blank-White Object and Character Asset Pilot

**Problem**: The flat Nordic direction was closer, but the generated assets still carried a warm beige background wash. The banana pilot was close, while the firefighter helmet showed a mismatched internal stroke/contour treatment. The user wants to test blank white backgrounds, refined people, and small multi-object activity scenes before replacing the runtime asset set.

**Solution**: Updated the active asset style contract so reusable item, object, and character assets are centered on blank clean white or barely tinted white padding, while full-screen scene beats can still use full-bleed square art. Added a stroke-system rule that matches the banana pilot: broad flat color fills, linework only for arc eyes/tiny facial marks/sparse texture dashes, and no helmet panel strokes or internal contour bands. Generated Codex built-in imagegen pilots for visual review: banana/object variants, refined people, and small multi-object activity scenes.

**Generated Pilots**:
- `/Users/pharrelly/.codex/generated_images/019e6796-207e-78b1-99ac-215bbe71abf1/ig_04db5e2559360fe0016a184b389cf881969c760b48134b6ad4.png`
- `/Users/pharrelly/.codex/generated_images/019e6796-207e-78b1-99ac-215bbe71abf1/ig_04db5e2559360fe0016a184c00a8148196b9d26727df7e6f20.png`
- `/Users/pharrelly/.codex/generated_images/019e6796-207e-78b1-99ac-215bbe71abf1/ig_04db5e2559360fe0016a184c4daab0819684fbfb6215d7e4e3.png`
- `/Users/pharrelly/.codex/generated_images/019e6796-207e-78b1-99ac-215bbe71abf1/ig_04db5e2559360fe0016a184c751b748196b3e7420d50870025.png`
- `/Users/pharrelly/.codex/generated_images/019e6796-207e-78b1-99ac-215bbe71abf1/ig_04db5e2559360fe0016a184cc712c481968edfa2865f65083b.png`
- `/Users/pharrelly/.codex/generated_images/019e6796-207e-78b1-99ac-215bbe71abf1/ig_04db5e2559360fe0016a18501806a08196a5b617cc660c7411.png`
- `/Users/pharrelly/.codex/generated_images/019e6796-207e-78b1-99ac-215bbe71abf1/ig_04db5e2559360fe0016a1850733a7481968b89a58246265990.png`
- `/Users/pharrelly/.codex/generated_images/019e6796-207e-78b1-99ac-215bbe71abf1/ig_04db5e2559360fe0016a18515f61d481969a9fc992992e19db.png`
- `/Users/pharrelly/.codex/generated_images/019e6796-207e-78b1-99ac-215bbe71abf1/ig_04db5e2559360fe0016a1851a6f7e881968d8a54db533cd703.png`
- `/Users/pharrelly/.codex/generated_images/019e6796-207e-78b1-99ac-215bbe71abf1/ig_04db5e2559360fe0016a18535dc5b081968b165ab3e3adff29.png`
- `/Users/pharrelly/.codex/generated_images/019e6796-207e-78b1-99ac-215bbe71abf1/ig_04db5e2559360fe0016a185565495c81969c1315c5282eeb80.png`
- `/Users/pharrelly/.codex/generated_images/019e6796-207e-78b1-99ac-215bbe71abf1/ig_04db5e2559360fe0016a1855bfd3188196b1f432f866a90a00.png`
- `/Users/pharrelly/.codex/generated_images/019e6796-207e-78b1-99ac-215bbe71abf1/ig_04db5e2559360fe0016a1856114aec8196bd2ddbd23e2649bb.png`

**Current Read**:
- Best object direction: banana variants and object-only recognition scene.
- Best people direction: the later plain helper is closest; firefighter people still drift because helmet/body details introduce shadow bands.
- Best activity scene direction: object-only clusters work better than person-plus-object compositions for this style.

**Edits**:
- `frontend/public/activity-assets/prompts/wonderlens-activity-style.md` — changed the style contract from warm ivory/peach washes to blank clean white or barely tinted white backgrounds for reusable object/person assets, then added the banana-matched stroke-system rule.
- `frontend/tests/activityAssets.test.js` — updated the prompt contract assertion to require the blank-white asset direction and stroke-system constraints.

**NOT Changed**:
- Runtime assets were not overwritten.
- No frontend runtime code or backend behavior changed.
- The generated pilots remain in Codex's generated image folder until the user approves a scale-out direction.

**Verification**:
- `npm test -- --run tests/activityAssets.test.js` — 8 passed.
- `git diff --check -- HANDOFF.md frontend/public/activity-assets/prompts/wonderlens-activity-style.md frontend/tests/activityAssets.test.js` — passed.

---

## Flat Nordic Asset Pilot Pass

**Problem**: The latest regenerated display assets were moving in the right direction but still read as sculpted toy/material art instead of the requested flat Nordic visual style. The active asset prompt still included depth-oriented language that pulled Codex imagegen toward rendered volume.

**Solution**: Changed the activity asset style contract to flat Nordic vector only, using the user's nursery-wall-art prompt structure and screenshot references: asymmetric simple animal silhouettes, large blocky body shapes, muted salmon/dusty blue/oat color blocks, sparse black decorative strokes, thin colored-pencil linework, soft peach/off-white wash, clean composition, and generous negative space. Added a regression assertion so the active style prompt no longer contains light/depth generation terms or contact-sheet language. Generated reference-driven Animal Sound pilots for visual review, plus earlier firefighter and banana probes.

**Edits**:
- `frontend/public/activity-assets/prompts/wonderlens-activity-style.md` — replaced the light-depth style contract with flat Nordic vector/nursery-wall-art direction.
- `frontend/tests/activityAssets.test.js` — updated prompt contract coverage to require the flat Nordic vector terms and reject depth/contact-sheet language.

**NOT Changed**:
- The existing runtime PNG assets were not batch-replaced in this pass.
- The generated pilot images remain in Codex's generated image folder until the flat-vector direction is approved for scale-out.
- No app runtime code or backend behavior changed.

**Verification**:
- `npm test -- --run tests/activityAssets.test.js` — 8 passed.
- Manual pilot review found the Animal Sound scene closest to target; the second firefighter and banana prompts reduced the remaining raised/depth cues and are the current candidates for approval.

---

## Activity Visual Layout and Interaction Completion

**Problem**: The metadata-driven lens renderer still had placeholder per-beat layouts and no complete item-asset contract for all 12 standalone activities. Cat5 collection still needed to use the same rendered screen assets for its live choices, Cat3/Cat5 behavior needed regression coverage, and the live Recognition Pop directive path could still generate physical-input wording such as "point out" even after the non-directive text normalizer was fixed.

**Solution**: Added a deterministic asset/layout build script that generates all item sprites and rewrites the manifest with explicit safe-area layout metadata for every runtime beat across all 12 activities. The manifest now uses `single`, `choice2`, `choice3`, and `carousel` modes with activity-specific circle/3:4 item cards. Cat5 live `current_round_items` are projected into the same screen layout renderer, with transparent hit targets over the rendered item cards, so selections still send the existing `photo_id` contract. Cat3 remains physical-control driven with in-lens Done/Help highlighting. Recognition Pop text-only enforcement now runs inside the shared speaker layer, including the Turn Director directive path.

**Edits**:
- `scripts/build_activity_screen_assets.py` — added the reusable item extraction and manifest layout builder.
- `frontend/public/activity-assets/activity-assets.manifest.json`, `frontend/public/activity-assets/**/items/*.png`, `frontend/public/activity-assets/_sources/phoneme_collection_sheet.png` — added explicit beat layouts and 59 item sprites; the Cat5 source sheet came from Codex imagegen and is not referenced at runtime.
- `frontend/src/activityGame/ActivityGameApp.jsx`, `ActivityLens.jsx`, `frontend/src/index.css` — render Cat5 live choices through the screen layout system and keep transparent selection hit targets over the visual cards.
- `backend/games/activity_phoneme_treasure_hunt.md` — points Cat5 collection catalog items at activity-specific item art.
- `backend/agents/script_agent.py`, `backend/turn_handling/generation.py`, `backend/tests/test_generation_text_mode.py` — moved text-only Recognition Pop wording enforcement into the speaker layer and added directive-path coverage.
- `frontend/public/activity-assets/prompts/wonderlens-activity-style.md` — documented the new beat-plus-item asset workflow.
- `frontend/tests/activityAssets.test.js`, `frontend/tests/ActivityGameApp.test.jsx`, `tests/test_activity_text_game_asset_contract.py` — added full layout metadata, Cat5 visual-selection, item dimension, and black-padding regressions.

**NOT Changed**:
- The standalone activity game remains text-only: no mic, TTS, camera, or photo-upload controls were added.
- Runtime still uses committed static assets; no image generation API is called by the app.
- Cat5 still sends existing `/api/turn` `photo_id` selections; Cat3 quick actions remain text turns.

**Verification**:
- `npm test -- --run tests/activityAssets.test.js tests/ActivityGameApp.test.jsx tests/WonderLensDevice.test.jsx` — 18 passed.
- `npx eslint src/activityGame/ActivityGameApp.jsx src/activityGame/ActivityLens.jsx tests/ActivityGameApp.test.jsx tests/activityAssets.test.js` — passed.
- `npm run build` — passed; Vite emitted the existing large chunk warning.
- `uv run pytest backend/tests/test_generation_text_mode.py backend/tests/test_activity_source_fidelity.py backend/tests/test_activity_text_game_cat3.py tests/test_activity_text_smoke.py tests/test_activity_text_game_asset_contract.py -q` — 28 passed.
- `uv run ruff check backend/agents/script_agent.py backend/turn_handling/generation.py backend/tests/test_generation_text_mode.py scripts/build_activity_screen_assets.py tests/test_activity_text_game_asset_contract.py tests/test_activity_text_smoke.py backend/tests/test_activity_source_fidelity.py backend/tests/test_activity_text_game_cat3.py` — passed.
- Restarted backend from the feature worktree while sourcing `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/backend/.env` and `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/backend/.elaborate-baton-480304-r8-a8a39bcb34f1.json`.
- `uv run python scripts/run_activity_text_smoke.py activity_recognition_pop_challenge --timeout 120` — 1 passed, 0 failed.
- `uv run python scripts/run_activity_text_smoke.py --timeout 120` — 12 passed, 0 failed.
- Browser/Playwright verification at `http://127.0.0.1:5173/?view=activities` captured `/tmp/wonderlens-browser-audit/01_activity_layout.png`, `/tmp/wonderlens-browser-audit/03_guided_drawing_build.png`, and `/tmp/wonderlens-browser-audit/04_phoneme_selection.png`; confirmed idle exit count 0, active exit count 1, Cat3 Done/Help build controls visible on the device, Cat5 three screen-selection hit targets visible with text input disabled, and no console errors.
- `git diff --check` — passed.

---

## Metadata-Driven Device Screen Layout Renderer

**Problem**: The device lens still treated each activity beat as one full-screen bitmap. The UI design guidance allows one, two, or three-plus visual assets inside the circular screen, with circle and 3:4 rectangle treatments, while keeping the real device screen touchless and controlled by the side scroll rocker plus start/select button.

**Solution**: Added a normalized `screenLayoutForBeat` asset contract and wired it into the standalone activity device. Beats without metadata still render as one full-screen asset. Beats with metadata can now render `single`, `choice2`, `choice3`, or `carousel` layouts, with visual-only circle/3:4 item cards, selected-state styling, and safe-area defaults matching the 480/380/300 spec. Added starter manifest metadata for Phoneme Treasure Hunt carousel, Guided Drawing single-screen, and Recognition Pop two-choice layouts, using existing assets as placeholders until the next activity-specific regeneration pass.

**Edits**:
- `frontend/src/activityGame/activityAssets.js` — added `beatForId` and `screenLayoutForBeat` normalization.
- `frontend/src/activityGame/ActivityLens.jsx`, `WonderLensDevice.jsx`, `ActivityGameApp.jsx` — pass and render metadata-driven screen layouts inside the circular lens.
- `frontend/src/index.css` — added the reusable screen composition styles for single, two-choice, three-choice, carousel, circle, rectangle, and selected states.
- `frontend/public/activity-assets/activity-assets.manifest.json` — added the screen style metadata and representative per-beat layout metadata.
- `frontend/tests/activityAssets.test.js`, `frontend/tests/WonderLensDevice.test.jsx` — added renderer and visual-only layout coverage.

**Verification**:
- `npm test -- --run tests/activityAssets.test.js tests/WonderLensDevice.test.jsx` — 11 passed.
- `npm run build` — passed; Vite emitted the existing large chunk warning.
- Chrome headless screenshot at `http://localhost:5173/?view=activities` rendered the screenshot-style layout, preserved device proportions, and loaded the device lens visual without a reachability issue.

---

## Activity Layout, Cat3 Controls, and Asset Flow Alignment

**Problem**: The standalone activity view had two `Exit activity` controls, still carried the earlier adjustable transcript-width toolbar, and no longer matched the preferred WonderLens Prototype layout. Cat3 Guided Drawing repeated the build-step card inside the device lens and used on-screen buttons even though the physical device screen should be touchless. Animal Sound Imitation also showed a fixed rabbit/cat/puppy asset sequence while the live dialogue could drift to a dog-only path; the same asset/dialogue mismatch risk existed for Recognition Pop and Partial Reveal because their assets are fixed but their recipes were still generic.

**Solution**: Reworked `/?view=activities` into the screenshot-style frame: green top bar, activity list plus device preview, metrics row, and full-width transcript panel. The transcript-width toolbar is gone, leaving only the library `Exit activity` button during an active session. Cat3 now shows only a compact in-lens `Done`/`Help` selector, moves the highlight with the physical scroll rocker, and confirms with the green start/select button. The three asset-specific recipes now name the exact visible sequences: Animal Sound uses rabbit, cat meow, and puppy; Recognition Pop uses the red apple target with blue car, strawberry, cherries, and basketball distractors; Partial Reveal uses cat ears, cat paws, and cat face.

**Verification**:
- `npm test -- ActivityGameApp.test.jsx WonderLensDevice.test.jsx` — 10 passed.
- `npm run build` — passed; Vite emitted the existing large chunk warning.
- `uv run pytest backend/tests/test_activity_source_fidelity.py -q` — 4 passed.
- Restarted backend from the feature worktree while sourcing `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/backend/.env` and the Google credential JSON from the same backend root.
- Live `POST /api/start-activity` for Animal Sound produced a rabbit/cat/puppy opener, and the first accepted turn asked for the rabbit sniff rather than dog-only dialogue.
- Browser verification at `http://localhost:5173/?view=activities` confirmed the screenshot-style layout, single exit location, visual companion in the device lens, and tightened activity-list metadata.

---

## Recognition Pop Text Wording Fix

**Problem**: Live Recognition Pop Challenge turns repeatedly ended with "type left, right, this, that..." and the activity opener used "card" language. Server logs showed this was generated by the backend, not the frontend: the converted Recognition Pop recipe contained child-facing `left/right/this/that` and `target card` wording, and `_enforce_text_only_interaction` appended that exact suffix whenever a Recognition Pop response lacked both `type` and `left/right`.

**Solution**: Replaced the child-facing Recognition Pop recipe language with picture/match wording and removed the hard `left/right/this/that` requirement from the text-only normalizer. The normalizer still rewrites physical input verbs (`point`, `tap`, `click`, `touch`) for text-only Recognition Pop, but now keeps existing questions concise and only adds a natural fallback prompt when a generated line has no choice cue. The live smoke helper now forbids the old suffix instead of treating it as a successful text-choice prompt.

**Edits**:
- `backend/games/activity_recognition_pop_challenge.md` — changed target/card and left-right wording to target picture, matching picture, and short description phrasing while preserving the imported source asset id.
- `backend/turn_handling/generation.py` — changed Recognition Pop text-mode enforcement to avoid the repeated suffix, normalize `card(s)` to `picture(s)`, and add only a natural fallback prompt when needed.
- `backend/tests/test_generation_text_mode.py` — added regressions for no old suffix, concise existing questions, natural fallback prompt, and recipe child-facing wording.
- `scripts/run_activity_text_smoke.py`, `tests/test_activity_text_smoke.py` — updated the live smoke contract to forbid old Recognition Pop wording.

**NOT Changed**:
- Recognition Pop remains text-only in standalone mode.
- The source asset id `recognition_challenge_cards_01` remains in the recipe for source fidelity.
- No frontend UI changes were made for this fix.

**Verification**:
- `uv run pytest backend/tests/test_generation_text_mode.py tests/test_activity_text_smoke.py -q` — 15 passed.
- `uv run pytest backend/tests/test_activity_source_fidelity.py backend/tests/test_generation_fallback.py backend/tests/test_activity_text_game_api.py -q` — 8 passed.
- `uv run ruff check backend/turn_handling/generation.py backend/tests/test_generation_text_mode.py scripts/run_activity_text_smoke.py tests/test_activity_text_smoke.py` — passed.
- Restarted backend on `127.0.0.1:8000` with the original backend `.env` and Google credential JSON sourced.
- `uv run python scripts/run_activity_text_smoke.py activity_recognition_pop_challenge --base-url http://localhost:8000` — 1 passed, 0 failed.
- Manual live Recognition Pop run reached Round 2 and produced no `left/right/this/that` suffix and no child-facing `card` wording.

---

## Cat3/Cat5 Standalone Interaction Modes

**Problem**: The standalone `/?view=activities` text game was treating all activity categories as plain typed chat. That regressed Cat5, where the full demo expects screen item selection, and left Cat3 without a guided build checkpoint surface. The hook also allowed a stale in-flight turn response to repopulate session state after `Exit activity`.

**Solution**: Added category-specific lens interactions while keeping the standalone view text-only. Cat5 now renders selectable current-round items in the device lens during collection photo phases and sends selections as `photo_id` turns. Once the selected item is recorded for the current round, the grid yields to text input for the follow-up detail answer even if the backend still reports `collection_phase: photo`. Cat3 now renders a guided build panel with the current build step, materials, and `Done`/`Help` quick text actions while leaving typed input enabled. Backend Cat3 session state now exposes `build_materials` and `current_build_step`. The session hook now uses a generation/session guard so reset invalidates pending turn/start responses.

**Edits**:
- `backend/server.py` — exposes Cat3 `build_materials` and round-indexed `current_build_step` from `_session_state_dict`.
- `backend/tests/test_activity_text_game_cat3.py` — added Cat3 session-state regression coverage.
- `frontend/src/activityGame/ActivityGameApp.jsx` — derives Cat5/Cat3 interaction modes, disables typed input only during active Cat5 item selection, and unlocks text detail input after the current item is collected.
- `frontend/src/activityGame/ActivityLens.jsx`, `WonderLensDevice.jsx`, `frontend/src/index.css` — render compact Cat5 selection and Cat3 build panels inside the circular lens.
- `frontend/src/activityGame/useActivityTextSession.js` — added `sendCollectionItem(photoId, label)` and guarded stale async responses after reset/session changes.
- `frontend/tests/ActivityGameApp.test.jsx`, `frontend/tests/useActivityTextSession.test.jsx` — added Cat5 item-selection, Cat5 post-selection unlock, Cat3 build quick-action, and stale-response reset regressions.

**NOT Changed**:
- Standalone activity mode remains text-only: no STT/TTS/photo upload controls were added.
- Cat5 still uses the existing backend `/api/turn` `photo_id` contract.
- Cat3 quick actions are text turns (`done`, `help`); no drawing/canvas input was added.
- Existing backend activity recipes and visual assets are unchanged in this pass.

**Verification**:
- `npm test -- ActivityGameApp.test.jsx useActivityTextSession.test.jsx WonderLensDevice.test.jsx` — 15 passed.
- `uv run pytest backend/tests/test_activity_text_game_cat3.py backend/tests/test_activity_text_game_api.py -q` — 6 passed.
- `uv run ruff check backend/server.py backend/tests/test_activity_text_game_cat3.py` — passed.
- `npm run lint` — passed.
- `npm run build` — passed; Vite emitted the existing large chunk warning.
- Browser verification at `http://localhost:5173/?view=activities` against the restarted backend confirmed Cat3 build controls appear with typed input enabled, Cat5 screen item selection appears with typed input disabled, item selection writes the selected label into the transcript, and the live backend response is handled by yielding back to text input once the current item is recorded.

---

## Activity Source Dialogue Fidelity Layer

**Problem**: The converted `backend/games/activity_*.md` files loaded and preserved source keywords, but dropped the richer source-package dialogue contracts that made the original full demo feel better: runtime instructions, example AI lines, child response branches, AI follow-ups, source intent locks, and screen/fallback contracts.

**Solution**: Added a source-dialogue fidelity layer to the imported activity recipes. Each converted activity now carries a `source_dialogue` block generated from its matching autodesign `prod.md` and `spec.md`. The parser maps those blocks into typed recipe models, and the Script Agent overlay now passes the current step's source intent, example line, branches, follow-ups, and screen contract into the dialogue prompt while still respecting the current interaction mode.

**Edits**:
- `backend/games/activity_*.md` — added source intent/detail-floor notes plus per-step `source_dialogue` contracts for all 12 imported activities.
- `backend/schemas/step_instruction.py`, `backend/game_parser.py` — added typed source branch/step contracts and parser mapping.
- `backend/agents/script_agent.py` — added source fidelity details to the activity-specific prompt overlay.
- `backend/tests/test_activity_source_fidelity.py` — added regressions proving imported activities preserve source dialogue contracts and the career firefighter round overlay includes them.

**NOT Changed**:
- No interaction-mode changes yet; Cat3/Cat5 screen interaction work remains next.
- The standalone activity game remains text-only.
- Existing non-imported demo games continue to load with empty/default source contracts.

**Verification**:
- `uv run ruff check backend/schemas/step_instruction.py backend/game_parser.py backend/agents/script_agent.py backend/tests/test_activity_source_fidelity.py` — passed.
- `uv run pytest backend/tests/test_activity_source_fidelity.py backend/tests/test_generation_text_mode.py tests/test_activity_text_smoke.py -q` — 14 passed.
- `uv run pytest tests/test_game_parser.py backend/tests/test_activity_text_game_definitions.py backend/tests/test_activity_text_game_api.py backend/tests/test_activity_text_game_cat3.py backend/tests/test_generation_fallback.py tests/test_activity_text_game_asset_contract.py -q` — 54 passed.
- Manual overlay check confirmed `activity_career_decision_role_play` round 1 now includes the source intent lock, firefighter example AI line, ideal/unexpected/no-response branches, follow-ups, and screen fallback in `_build_instruction_overlay`.
