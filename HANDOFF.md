# Session Handoff

Last updated: 2026-03-25

---

## Review Follow-Up: Let Cat5 Synthesis Finish After One Child Reply

**Problem**: Reviewing the newer Cat5 synthesis prompt updates exposed one stale backend guardrail in `backend/turn_handler.py`. The synthesis handler still forced `stay_on_step` unless it had seen two child turns on `STEP_4_SYNTHESIS`, but the reviewed prompt contract now caps synthesis at one child contribution before the AI finishes the activity. In practice, that meant valid first replies like "tickle!" or "ok" would be held on synthesis for an unnecessary extra turn.

**Solution**: Narrowed the synthesis completion guardrail to the actual requirement: block completion only until the first child synthesis reply exists, while still forcing `stay_on_step` when the AI ends with a question or when synthesis has not received any child reply yet. I added a focused regression test for the first-child-reply completion path.

**Edits**:
- `backend/turn_handler.py` — changed the Cat5 synthesis guardrail from "at least 2 child turns" to "at least 1 child turn" so the backend matches the updated synthesis contract
- local `tests/test_turn_handler.py` — added regression coverage proving a single child synthesis reply can complete synthesis and advance to celebrate
- `HANDOFF.md` — added this review follow-up entry

**NOT Changed**:
- `backend/state_machine.py` and the Cat5 detail-photo screen-frame work — reviewed earlier and left unchanged in this follow-up
- Cat5 prompt files in `backend/skills/step_instructions/` — their newer one-reply synthesis contract was kept as the source of truth; no additional prompt edits were needed here
- Frontend synthesis UI/device widget wiring — reviewed against the backend step transition and left unchanged

**Verification**:
- `uv run pytest tests/test_turn_handler.py::test_synthesis_can_finish_after_first_child_reply -q` — PASS (`1 passed`)
- `uv run pytest tests/test_turn_handler.py -q` — PASS (`20 passed`)
- `uv run ruff check backend/turn_handler.py tests/test_turn_handler.py` — PASS
- `uv run ruff format --check backend/turn_handler.py tests/test_turn_handler.py` — PASS

---

## Review Follow-Up: Simplify Cat5 Screen-Frame Enrichment

**Problem**: Reviewing the latest Cat5 progress-indicator fix exposed one concrete implementation issue in the newly modified frame path. `backend/state_machine.py` was still mutating matched Visual Agent `ScreenFrame` objects in place when it injected `roundNumber` and Cat5 `progress_tracker` counts. That works in the happy path, but it makes the visual-frame list stateful and harder to reason about, especially once the Cat5 collect path started adding more step-specific widget params like `filled`, `total`, and `description`.

**Solution**: Kept the current Cat5 behavior, but simplified the implementation around small helpers and immutable frame enrichment. Cat5 detail-photo URL resolution, detail-frame construction, and collect-progress widget params now live in dedicated helpers, and matched Visual Agent frames are copied before round-specific params are added. That preserves the reviewed runtime behavior while avoiding template mutation and making the Cat5 collect path easier to follow.

**Edits**:
- `backend/state_machine.py` — extracted helpers for Cat5 detail photo URL lookup, detail-frame construction, and collect progress params; replaced in-place Visual Agent frame mutation with copied frame enrichment via `_with_round_context()`
- local `tests/test_state_machine.py` — extended the Cat5 collect visual-frame regression to assert that matched `widget_params` remain unchanged after `get_screen_frame()` returns
- `HANDOFF.md` — added this review follow-up entry

**NOT Changed**:
- `backend/turn_handler.py` and the two-phase collection state flow — reviewed and left unchanged in this follow-up
- `frontend/src/components/DeviceScreen.jsx` and the `photoUrl` fallback wiring — reviewed against the current frame contract and left unchanged
- Prompt/docs edits in `backend/skills/step_instructions/`, `README.md`, and `docs/game-pipeline-overview.md` — reviewed and left unchanged in this pass

**Verification**:
- `uv run pytest tests/test_state_machine.py::TestGetScreenFrameWithVisualFrames::test_cat5_collect_visual_frame_gets_progress_counts -q` — PASS (`1 passed`)
- `uv run pytest tests/test_state_machine.py tests/test_api.py -q` — PASS (`49 passed`)
- `uv run ruff check backend/state_machine.py tests/test_state_machine.py` — PASS
- `uv run ruff format --check backend/state_machine.py tests/test_state_machine.py` — PASS

---

## Fix: Cat5 Collect Progress Indicator Uses Real Total

**Problem**: The Cat5 two-phase collection loop could show an incorrect collect indicator in the device screen, as seen in `images/issue-4.png`. The root cause was in `backend/state_machine.py`: when a collect step used a Visual Agent frame, the matched frame only got `roundNumber`, so a `progress_tracker` widget fell back to its own default `total=4`. The Cat5 hardcoded collect fallback also used the round number itself as `filled`, which made progress semantics depend on step index instead of the actual number of collected photos.

**Solution**: Moved the Cat5 collect-frame enrichment back into the state machine contract. Detail phase now always short-circuits to `photo_display`, even when visual frames are present. Photo phase collect frames now populate `progress_tracker` with `filled=len(collected_photos)` and the real `collection_count`, so the widget shows the correct number of slots and the right active slot. I added focused regression coverage for both the visual-frame and fallback paths.

**Edits**:
- `backend/state_machine.py` — short-circuits Cat5 detail mode before Visual Agent frame matching; enriches Cat5 collect `progress_tracker` frames with real `filled`/`total` values from collection state; aligns the hardcoded collect fallback to use collected-photo count instead of round index
- local `tests/test_state_machine.py` — added regression coverage for Visual Agent collect frames receiving real progress counts and for detail mode ignoring matched collect visuals in favor of the just-collected photo
- `HANDOFF.md` — added this fix entry

**NOT Changed**:
- `frontend/src/widgets/ProgressTracker.jsx` — widget defaults and rendering logic unchanged; the fix is upstream in frame generation
- `frontend/src/App.jsx` footer/session labels — reviewed and left unchanged
- Turn handling, prompt files, and Cat1 state-machine behavior — unchanged

**Verification**:
- `uv run pytest tests/test_state_machine.py tests/test_api.py -q` — PASS (`49 passed`)
- `uv run ruff check backend/state_machine.py tests/test_state_machine.py` — PASS
- `uv run ruff format --check backend/state_machine.py tests/test_state_machine.py` — PASS

---

## Review Follow-Up: Fix Cat5 2-Phase Turn Transition + Add Coverage

**Problem**: Reviewing the new Cat5 two-phase collection loop exposed two concrete flow bugs and a missing-test gap. In `backend/turn_handler.py`, the new Phase B branch reset `collection_phase` back to `photo` before generating the AI response, so the prompt and screen-frame logic were reading the wrong phase during the child's detail reply. The same branch also failed to advance non-final rounds after the child answered the detail question, which would leave the session stuck on the previous round's item set. The fresh two-phase behavior also had no focused backend regression coverage yet.

**Solution**: Kept the two-phase design, but tightened the transition contract around the detail-response branch. Phase B now stays in `detail` mode while the Script Agent generates the acknowledgement/name-processing turn, then advances to the next collection round only after that response is built. Final detail replies now use the existing auto-advance path to bridge cleanly into the first synthesis prompt, preserving the just-collected photo view during the final Phase B response. I also removed the old "child detail as placeholder name" behavior and replaced it with a small best-effort name extractor so `collected_names` only stores actual generated names when they are obvious in the dialogue. Finally, I added focused unit, state-machine, and API coverage for the reviewed flow.

**Edits**:
- `backend/turn_handler.py` — kept Phase B in `detail` mode during generation, advanced non-final detail replies into the next collect round, routed final detail replies through `round_advance_pending` auto-advance into synthesis, reset Cat5 phase when consuming the pending auto-advance, and replaced fake placeholder-name storage with guarded detail/name helpers
- local `tests/test_turn_handler.py` — added regression coverage for correct-photo entry into detail mode, detail replies advancing to the next round, and final detail replies auto-bridging into synthesis; updated the synthesis completion fixture to satisfy the current two-child-turn guardrail
- local `tests/test_state_machine.py` — added a Cat5 detail-phase frame assertion so the hardcoded fallback maps detail mode to `photo_display`
- local `tests/test_api.py` — updated the stale Cat5 collection expectations to match the reviewed two-phase contract and added an API-level regression for detail replies advancing into the next collection round
- `HANDOFF.md` — added this review follow-up entry

**NOT Changed**:
- `backend/skills/step_instructions/cat5_step3_collect*.md` and `backend/skills/step_instructions/cat5_step4_synthesis*.md` — prompt wording was reviewed and left unchanged in this follow-up
- `frontend/src/App.jsx` and the existing `collection_phase` gallery gating — reviewed against the corrected backend contract and left as-is
- Cat1 flow handling, deep-link behavior, and other backend endpoints — unchanged

**Verification**:
- `uv run pytest tests/test_turn_handler.py tests/test_state_machine.py tests/test_api.py -q` — PASS (`57 passed`)
- `uv run ruff check backend/turn_handler.py tests/test_turn_handler.py tests/test_state_machine.py tests/test_api.py` — PASS
- `uv run ruff format --check backend/turn_handler.py tests/test_turn_handler.py tests/test_state_machine.py tests/test_api.py` — PASS

---

## Feature: Cat5 2-Phase Collection Loop

**Problem**: Cat5 collection used a single-phase loop (photo -> react -> advance) where the AI was explicitly forbidden from asking text/verbal questions during collection. New game designs require a 2-phase loop where each round has Phase A (child selects photo, AI validates and asks a detail-harvesting question) and Phase B (child responds verbally, AI processes detail/names character, then advances). This enables richer per-find engagement — naming characters in naming_story, capturing observations in comparison_chart.

**Solution**: Implemented the full 2-phase collection loop across backend and frontend, following the plan in `docs/plans/cat5-2phase-collection-loop.md`.

**Edits**:
- `backend/schemas/session_state.py` — added `CollectionPhase` type alias, `collection_phase`, `collected_details`, `collected_names` fields to `SessionStateModel`
- `backend/schemas/creative_slots.py` — added `detail_question_template` and `sorting_criterion` optional fields to `Cat5CreativeSlots`
- `backend/games/polka_dot_patrol.md` — added `detail_question_template` and `sorting_criterion` values to creative_slots frontmatter
- `backend/games/fluffy_expedition_dandelion.md` — added `detail_question_template` and `sorting_criterion` values to creative_slots frontmatter
- `backend/turn_handler.py` — added Phase B handler (section 7b½) for detail responses; added Phase A->B transition after correct photo pick; added guardrail forcing stay_on_step during detail phase; updated collection-complete override to only trigger in photo phase; passed collection_phase and collected_photos in state context
- `backend/agents/script_agent.py` — added `{collection_phase}`, `{detail_question_template}`, `{sorting_criterion}`, `{collected_names}`, `{collected_details}` template variables for Cat5
- `backend/skills/step_instructions/cat5_step3_collect.md` — major rewrite: 2-phase loop with Phase A (photo) and Phase B (detail) sections, `{collection_phase}` variable
- `backend/skills/step_instructions/cat5_step3_collect__naming_story.md` — rewrite: Phase A asks detail question, Phase B generates character name from child's response
- `backend/skills/step_instructions/cat5_step3_collect__comparison_chart.md` — rewrite: Phase A asks about observation differences, Phase B acknowledges and connects to previous finds
- `backend/skills/step_instructions/cat5_step4_synthesis.md` — updated: references collected data from hunt, removed fresh-naming approach
- `backend/skills/step_instructions/cat5_step4_synthesis__naming_story.md` — updated: characters already named during collection, synthesis is now story co-creation
- `backend/skills/step_instructions/cat5_step4_synthesis__comparison_chart.md` — updated: observations already captured, synthesis is sorting by criterion
- `backend/skills/step_instructions/cat5_step1_hook.md` — added warm start vs cold start terminology
- `backend/skills/step_instructions/cat5_step2_mission.md` — added 3-part mission pattern and role assignment emphasis
- `backend/skills/step_instructions/cat5_step5_celebrate.md` — added reflective WHY question
- `backend/prompts/script_system.md` — aligned concept counts: T0=1, T1=2, T2=3 (was T0=0, T1=1)
- `backend/server.py` — exposed `collection_phase`, `collected_names`, `collected_details` in session state dict
- `backend/state_machine.py` — Phase B shows `photo_display` of just-collected item instead of `progress_tracker`
- `frontend/src/App.jsx` — gated photo gallery on `collection_phase !== 'detail'`

**NOT Changed**:
- Cat1 flows — not affected by Cat5-specific changes
- Frontend widget components — no new widgets needed, existing `photo_display` and `progress_tracker` handle both phases
- State machine step sequence — steps unchanged, only screen frame selection differs by phase
- Agent pipeline (Director, Visual, Recipe Assembler) — unchanged

**Verification**:
- `cd backend && uv run ruff check . && uv run ruff format --check .` — PASS
- `cd backend && uv run pytest` — PASS (0 collected — no test files in scope)
- Manual test: Start fluffy_expedition_dandelion session, verify Phase A shows photo gallery, Phase B hides gallery and shows collected photo
- Manual test: Start polka_dot_patrol session, verify detail questions and observation capture

---

## Fix Follow-Up: Re-Center Tall Collection Gallery View

**Problem**: The previous tall-device-panel follow-up fixed `DeviceScreen`, but the whitespace shown in `images/issue-3.png` was actually coming from the collection flow rendered by `PhotoGallery`. That component had been hard-switched to `justify-start` during the earlier small-screen compression pass, so on taller viewports the gallery cluster stayed pinned near the top of the camera viewport and left excessive blank space below.

**Solution**: Restored centered layout for the collection gallery by default and kept the old top-alignment behavior only for short viewports where clipping risk is real. `PhotoGallery` now uses a dedicated `device-gallery-layout` class with default `justify-center`, and the existing `@media (max-height: 760px)` block flips that class back to `justify-content: flex-start`. That preserves the short-screen safety fix while re-centering the gallery on taller screens.

**Edits**:
- `frontend/src/components/PhotoGallery.jsx` — switched the root gallery container back to centered layout by default, using a dedicated layout class and balanced vertical padding
- `frontend/src/index.css` — added the short-viewport override for `.device-gallery-layout` inside the existing `max-height: 760px` rules
- local `tests/test_device_screen_layout.py` — extended the source-level regression checks to cover default gallery centering plus the short-height override
- `HANDOFF.md` — added this follow-up entry

**NOT Changed**:
- `frontend/src/components/DeviceScreen.jsx` and `frontend/src/widgets/AnimationOverlay.jsx` — left as-is from the previous tall-panel fix
- `frontend/src/components/ToyCameraFrame.jsx` and individual gallery card styling — unchanged
- Backend, APIs, and session logic — unchanged

**Verification**:
- `uv run pytest tests/test_device_screen_layout.py -q` — PASS (`3 passed`)
- `cd frontend && npx eslint src/components/PhotoGallery.jsx src/components/DeviceScreen.jsx src/widgets/AnimationOverlay.jsx` — PASS
- `cd frontend && npm run build` — PASS

---

## Fix: Re-Center Tall Device Panel Widgets

**Problem**: On taller viewports, the device panel widget area in the toy camera could pin the active widget cluster too close to the top of the white viewport, leaving a large blank region underneath. The screenshot in `images/issue-1.png` showed the collection progress card no longer visually centered when there was enough vertical space available.

**Solution**: Kept the existing device-panel structure but tightened the centering contract around the animated widget wrapper. `DeviceScreen` now uses a full-height grid-centered content slot for the main widget area, and `AnimationOverlay` now accepts an optional `className` so the animation wrapper can participate in layout instead of only applying transitions. That keeps the animated widget container centered vertically on tall screens while preserving the existing animation mapping and compact behavior on smaller devices.

**Edits**:
- `frontend/src/components/DeviceScreen.jsx` — changed the main widget region from a flex-centered box to a full-height `grid place-items-center` container and passed a full-size centering class into `AnimationOverlay`
- `frontend/src/widgets/AnimationOverlay.jsx` — added optional `className` support so layout classes can be composed with the animation classes
- local `tests/test_device_screen_layout.py` — **NEW**: source-level regression checks for the tall-viewport centering contract
- `HANDOFF.md` — added this entry

**NOT Changed**:
- `frontend/src/components/ToyCameraFrame.jsx` and individual device widgets — unchanged in this fix
- Conversation panel layout and tall-screen shell sizing outside the device widget slot — unchanged
- Backend and API/session orchestration logic — unchanged

**Verification**:
- `uv run pytest tests/test_device_screen_layout.py -q` — PASS (`2 passed`)
- `cd frontend && npx eslint src/components/DeviceScreen.jsx src/widgets/AnimationOverlay.jsx` — PASS
- `cd frontend && npm run build` — PASS

---

## Review Follow-Up: Harden Batch Game Setup CLI Tools + Add Coverage

**Problem**: Picking up the new batch game setup tooling exposed three concrete gaps in the fresh scripts. `scripts/convert_game.py` validated written files, but `--dry-run` skipped `game_parser` validation entirely even though the handoff and plan described it as a safe validation path. Both scripts also failed when the user supplied a nested custom output path whose parent directories did not already exist. In `scripts/generate_icon.py`, the game-frontmatter scan was duplicated across two functions and used broad `except Exception` handling that made the file-walking path harder to reason about.

**Solution**: Kept the new CLI surface intact and tightened the implementation around the failure paths. `convert_game.py` now imports `parse_game_file` at module load, validates dry-run output through a temporary `.md` file before printing it, and creates parent directories for custom output destinations. `generate_icon.py` now creates the actual output directory for custom icon paths, shares non-prod game frontmatter loading through a single helper, and narrows the auto-client fallback to configuration errors instead of swallowing arbitrary exceptions. I also added focused local regression tests for both scripts so these path-handling and dry-run guarantees are exercised without calling Gemini.

**Edits**:
- `scripts/convert_game.py` — kept the new converter flow, added dry-run parser validation via a temporary file, created parent directories before writing custom outputs, moved `parse_game_file` to module scope, and narrowed auto-mode client fallback handling
- `scripts/generate_icon.py` — created parent directories for custom output paths, extracted shared non-prod frontmatter loading for both metadata enrichment and missing-icon discovery, and replaced broad exception fallback in auto mode with `RuntimeError`-only handling
- local `tests/test_convert_game.py` — **NEW**: regression coverage for nested custom output paths and `--dry-run` validation behavior
- local `tests/test_generate_icon.py` — **NEW**: regression coverage for nested custom output paths and non-prod missing-icon discovery
- `HANDOFF.md` — replaced the draft batch-tool entry with this reviewed follow-up

**NOT Changed**:
- `docs/plans/batch-game-setup.md` — implementation plan preserved as written
- Backend `game_parser`, `entity_registry`, `game_loader`, and existing game markdown assets — unchanged in this follow-up
- Frontend runtime code and icon assets — unchanged
- Existing Gemini/OpenAI helper scripts (`generate_cat5_icons_*`, `regenerate_character_icons.py`) — read-only reuse only

**Verification**:
- `uv run pytest tests/test_convert_game.py tests/test_generate_icon.py -q` — PASS (`4 passed`)
- `uv run ruff check scripts/convert_game.py scripts/generate_icon.py tests/test_convert_game.py tests/test_generate_icon.py` — PASS
- `uv run ruff format --check scripts/convert_game.py scripts/generate_icon.py tests/test_convert_game.py tests/test_generate_icon.py` — PASS
- Networked CLI runs still require Gemini credentials; they were not exercised in this review pass

---

## Fix: Small-Screen Responsive Sizing Pass

**Problem**: The frontend layout was tuned for larger mobile/tablet widths, but many shell controls, widget cards, badges, progress circles, and icons kept their default sizes all the way down to very small screens. On narrow phones this made the camera viewport and surrounding UI feel oversized and cramped. A follow-up issue remained on short, wide viewports: the fixed-height shell could clip the top device area instead of adapting vertically.

**Solution**: Added a compact-mobile sizing layer for screens under 420px and tightened the highest-pressure UI surfaces under 380px. The pass keeps desktop/tablet styling intact while shrinking spacing, copy, controls, widget chrome, and icon sizes inside the app shell, camera frame, conversation panel, photo selection flow, and device widgets. After follow-up reports that the device panel content still felt oversized, I narrowed the fix to the in-panel layer: `DeviceScreen` now uses a tighter widget wrapper, and the device-only widgets no longer upscale at `sm` width breakpoints. That keeps the camera content sized to the panel instead of to the overall viewport width. After screenshot review (`images/cutoff-1.png`, `images/cutoff-2.png`, `images/IMG_5974.jpg`, `images/IMG_5976.PNG`), I also fixed four concrete issues: the lower-panel photo selector now anchors to the top instead of vertically centering oversized content, the in-device photo display now sizes by available height rather than by `max-w-md`, the in-camera collection gallery is now top-aligned and denser so its header no longer hides under the frame, and the collection progress-dot row has been reduced again so it stays inside the bottom of the camera viewport. In the latest pass, the device photo widget was switched from `object-cover` to `object-contain` and given a smaller height cap so images like the dandelion no longer look zoomed inside the camera frame. Separately, the text input now uses a 16px font size on mobile to prevent iOS Safari auto-zoom from pushing the send button off-screen. I also removed one unused `PhotoGrid` prop surfaced by lint during verification.

**Edits**:
- `frontend/src/index.css` — added global compact-mobile root font scaling for sub-420px screens plus short-viewport shell rules for scrolling/compression under `760px` height
- `frontend/src/App.jsx`, `frontend/src/components/TopBar.jsx`, `frontend/src/components/ToyCameraFrame.jsx`, `frontend/src/components/DeviceScreen.jsx`, `frontend/src/components/ConversationPanel.jsx`, `frontend/src/components/TextInput.jsx` — reduced shell spacing and control/icon sizing for extra-small screens; `DeviceScreen` now applies a tighter wrapper around in-panel widgets with a smaller max width; `TextInput` now keeps the mobile input at 16px to avoid browser zoom
- `frontend/src/components/PhotoSelector.jsx`, `frontend/src/components/GameDetailView.jsx`, `frontend/src/components/PhotoGallery.jsx` — tightened photo picker/detail/gallery layouts and labels on narrow viewports; `PhotoSelector` now top-aligns scrollable content instead of centering it; `PhotoGallery` now top-aligns and compresses in-camera collection layouts, including a smaller final progress-dot row
- `frontend/src/widgets/BadgeAward.jsx`, `frontend/src/widgets/ProgressTracker.jsx`, `frontend/src/widgets/CharacterDisplay.jsx`, `frontend/src/widgets/PhotoGrid.jsx`, `frontend/src/widgets/PhotoDisplay.jsx` — switched oversized widget/icon elements to compact breakpoint rules and `clamp()` sizing; removed `sm`-based device-panel enlargement; `PhotoDisplay` now uses a smaller height cap and `object-contain`
- `HANDOFF.md` — added this entry

**NOT Changed**:
- Backend, API contracts, session orchestration logic, and activity behavior — unchanged
- Existing unrelated worktree edits in `frontend/src/components/AiAvatar.jsx` and `frontend/src/components/SfxIndicator.jsx` were left untouched
- No new frontend test runner or browser automation was added in this pass

**Verification**:
- `rg -n "max-\\[380px\\]:|clamp\\(" frontend/src/App.jsx frontend/src/components/TopBar.jsx frontend/src/components/DeviceScreen.jsx frontend/src/components/PhotoSelector.jsx frontend/src/components/PhotoGallery.jsx frontend/src/widgets/BadgeAward.jsx frontend/src/widgets/ProgressTracker.jsx frontend/src/widgets/CharacterDisplay.jsx` — PASS
- `rg -n "sm:w-|sm:h-|sm:text-|sm:p-|sm:gap-" frontend/src/components/DeviceScreen.jsx frontend/src/components/PhotoGallery.jsx frontend/src/widgets/BadgeAward.jsx frontend/src/widgets/ProgressTracker.jsx frontend/src/widgets/CharacterDisplay.jsx frontend/src/widgets/PhotoGrid.jsx frontend/src/widgets/PhotoDisplay.jsx` — PASS
- `rg -n "justify-center h-full p-6|max-w-md aspect-square" frontend/src/components/PhotoSelector.jsx frontend/src/widgets/PhotoDisplay.jsx` — PASS
- `rg -n "text-sm max-\\[380px\\]:text-xs" frontend/src/components/TextInput.jsx` — PASS (no matches; mobile input no longer uses sub-16px text)
- `cd frontend && npm run lint` — PASS
- `cd frontend && npm run build` — PASS

---

## Review Follow-Up: Mobile TTS Playback Unlock

**Problem**: The recent TTS refactor switched playback from `AudioContext` scheduling to an `<audio>` element backed by WAV blobs, but `useTTS.unlock()` had been left as a no-op. On mobile browsers, that broke autoplay policy handling: the real `audio.play()` happened after async fetch/stream work instead of inside the original tap gesture, so TTS was blocked even though desktop browsers still worked.

**Solution**: Restored a real gesture-time unlock path for TTS. `useTTS.unlock()` now primes the same audio element with a silent WAV during the user gesture, resets it immediately, and leaves it ready for later async playback. The hook keeps the WAV-blob playback approach, preserves cleanup on stop/end/error, and still falls back to browser speech when backend TTS is unavailable.

**Edits**:
- `frontend/src/hooks/useTTS.js` — added a silent WAV data URI plus a real `unlock()` implementation for the shared audio element; added explicit audio-element/url cleanup helpers; kept `playsInline` and restored consistent stop behavior for fallback speech
- `HANDOFF.md` — added this mobile TTS follow-up entry

**NOT Changed**:
- `frontend/src/hooks/useSessionOrchestration.js` — existing `unlockTTS()` call sites were already correct and did not need changes in this follow-up
- `frontend/src/App.jsx` — no behavior changes in this pass
- Backend TTS endpoints and streaming contract — unchanged
- There is still no automated mobile-browser playback test in this repo, so final confirmation remains manual on-device

**Verification**:
- Manual verification on mobile browser — PASS (user confirmed TTS now plays)
- `cd frontend && npx eslint src/hooks/useTTS.js src/hooks/useSessionOrchestration.js src/App.jsx` — PASS
- `cd frontend && npm run build` — PASS

---
