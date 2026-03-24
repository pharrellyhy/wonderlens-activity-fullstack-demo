# Session Handoff

Last updated: 2026-03-24

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

## Review Follow-Up: Deep Link Direct Game Entry

**Problem**: Reviewing the new deep-link entry flow exposed two concrete issues in the freshly modified code. First, the implementation had drifted from the plan: the frontend was forwarding `context=/handoff/conversation.json` straight to the backend, and the backend tried to read that value as a local filesystem path. That would miss the real handoff file in normal browser usage and also widened the API surface unnecessarily. Second, the new `startDeepLinkSession()` frontend wrapper swallowed errors, so `App.jsx` still cleared the deep-link URL after a failed start and made the failure look like a handled success. The new backend path also had no focused regression coverage yet.

**Solution**: Kept the new deep-link feature, but aligned it to the intended browser-driven handoff flow. The frontend now fetches and validates the optional handoff JSON itself, then sends structured conversation turns to `POST /api/start-deep-link`. The backend accepts that structured payload directly, stores it on session state, and uses it in the Script Agent prompt without reading arbitrary paths from the request. The deep-link orchestration path now rethrows failures so the URL is only cleared after a real successful start. I also added focused local regression coverage for entity lookup and the new API endpoint.

**Edits**:
- `backend/schemas/session_state.py` — added structured `UpstreamConversationTurn` plus typed `upstream_conversation` storage on `SessionStateModel`
- `backend/entity_registry.py` — kept the new `lookup_by_entity_name()` helper after review; it is now covered by regression tests
- `backend/server.py` — changed `DeepLinkStartRequest` to accept `conversation_context` directly and removed backend-side file-path reading from the deep-link start flow
- `backend/agents/script_agent.py` — switched upstream-context prompt assembly to the typed `UpstreamConversationTurn` objects while keeping the shortened hook override
- `frontend/src/utils/api.js` — changed `startDeepLinkSession()` to send `conversation_context` instead of a path string
- `frontend/src/hooks/useConversation.js` — updated `startDeepLink()` to accept the validated conversation array from the app shell
- `frontend/src/hooks/useSessionOrchestration.js` — changed the deep-link start wrapper to rethrow on failure so failed starts do not look successful upstream
- `frontend/src/App.jsx` — now fetches and sanitizes the optional `context` JSON file client-side, then clears the URL only after a successful deep-link start
- local `tests/test_deep_link.py` — **NEW**: regression coverage for `lookup_by_entity_name()`, successful deep-link start with upstream conversation context, and unknown-entity 400 responses
- `HANDOFF.md` — replaced the draft feature note with this reviewed follow-up

**NOT Changed**:
- Existing `/api/start` and its multipart photo-upload flow — unchanged
- State machine, turn handler, visual agent, and step instruction files — unchanged; the deep-link behavior is layered on top
- `backend/schemas/recipe.py` and `backend/tts.py` formatting-only deltas already in the worktree were reviewed and left unchanged in this pass
- There is still no frontend test runner configured for this path, so the new automated coverage in this pass is backend/local only

**Verification**:
- `uv run pytest tests/test_deep_link.py -q` — PASS (`3 passed`)
- `uv run ruff check backend/server.py backend/agents/script_agent.py backend/entity_registry.py backend/schemas/session_state.py tests/test_deep_link.py` — PASS
- `uv run ruff format --check backend/server.py backend/agents/script_agent.py backend/entity_registry.py backend/schemas/session_state.py tests/test_deep_link.py` — PASS
- `cd frontend && npx eslint src/App.jsx src/hooks/useConversation.js src/hooks/useSessionOrchestration.js src/utils/api.js` — PASS
- `cd frontend && npm run build` — PASS

---

## Fix: LLM Conversation Flow Guardrails (Premature Completion + Synthesis Skip)

**Problem**: Two related LLM reliability issues in Cat5 conversation flow:
1. During collection rounds (`STEP_3_COLLECT`), the Script Agent says things like "perfect final treasure" when items still remain (e.g., 2/3 collected), contradicting the actual progress numbers injected into the prompt
2. During synthesis (`STEP_4_SYNTHESIS`), the Script Agent sets `stay_on_step: false` on responses that end with questions or invitations, causing the system to auto-advance to celebration before the child can respond (e.g., user says "inspire me", AI suggests names ending with "?", system immediately jumps to celebration)

**Solution**: Three-layer fix combining backend guardrails with prompt improvements:
1. **Collection completion language guardrail**: Regex-based detection of premature completion patterns ("final treasure", "mission complete", "all done", etc.) in collection responses when `remaining_count > 0`. On detection, injects a corrective hint into conversation history, regenerates, then removes the hint. Single retry to avoid loops.
2. **Synthesis `stay_on_step` guardrail**: Overrides `stay_on_step` to `true` when (a) the synthesis dialogue ends with `?`, or (b) fewer than 2 child turns on synthesis — ensuring minimum engagement.
3. **Prompt fixes**: Added explicit "inspire me" handling in `cat5_step4_synthesis.md` as `stay_on_step: true`. Added FORBIDDEN WORDS list in `cat5_step3_collect.md` when `remaining_count > 0`.

**Edits**:
- `backend/turn_handler.py` — added `import re` at top; added `_COMPLETION_PATTERNS` regex and `_has_completion_language()` helper in photo validation section; added collection completion language guardrail in section 7c (after line 468 generate); added synthesis `stay_on_step` override in section 7d (after line 549 generate)
- `backend/skills/step_instructions/cat5_step4_synthesis.md` — added "Inspire me" / "give me ideas" / "show me" as explicit handling case with `stay_on_step: true`
- `backend/skills/step_instructions/cat5_step3_collect.md` — added FORBIDDEN WORDS clause under the `remaining_count > 0` rule

**NOT Changed**:
- `backend/state_machine.py` — step transitions unchanged
- `backend/agents/script_agent.py` — prompt assembly unchanged
- Frontend auto-advance logic (`useSessionOrchestration.js`) — correctly follows backend signals
- Cat1 flows — not affected by these Cat5-specific guardrails

**Verification**:
- `cd backend && uv run ruff check turn_handler.py` — PASS
- `cd backend && uv run ruff format --check turn_handler.py` — PASS

---

## Review Follow-Up: CharacterDisplay Redesign + PhotoSelector Cleanup

**Problem**: The latest CharacterDisplay redesign moved the widget to per-entity themed scene cards, but it still needed a review pass before handoff. The main risks were whether the runtime `entity` values and icon assets actually matched the new theme map, whether the animation override only affected `character_display`, and whether the related `PhotoSelector.jsx` edits had left dead code behind. That review found one concrete issue: the upload zone had been intentionally disabled in the UI, but the component still carried its old drag-and-drop state and handlers, which now failed frontend lint.

**Solution**: Kept the redesigned scene-window approach, confirmed the backend/frontend contract still passes simple entity names (`dog`, `cat`, `dinosaur`, `ladybug`, `dandelion`) and that matching icon assets exist in `frontend/public/icons/`, and preserved the one-shot animation remap in `DeviceScreen`. Simplified `PhotoSelector.jsx` by removing the unused upload state/handlers so the disabled upload UI matches the code path that is actually live.

**Edits**:
- `frontend/src/index.css` — added `@keyframes gentle-float` and `.animate-gentle-float` for the subtle character float motion
- `frontend/src/widgets/gameThemes.js` — **NEW**: per-game theme config mapping entity name to gradient, accent styling, character PNG, and decorative elements
- `frontend/src/widgets/CharacterDisplay.jsx` — replaced round-based SVG icon rotation with the themed scene-card layout using `getThemeForEntity()`, character PNGs, corner decorations, and a round badge
- `frontend/src/components/DeviceScreen.jsx` — remaps `sparkle_highlight`/`gentle_pulse` to `appear` only for the `character_display` widget before rendering `AnimationOverlay`
- `frontend/src/components/PhotoSelector.jsx` — removed the now-unused drag/drop upload state and handlers left behind after the upload area was converted to a disabled placeholder
- `docs/plans/character-display-redesign.md` — **NEW**: design plan for the widget redesign

**NOT Changed**:
- Backend — zero changes; the existing `entity` prop flow was reviewed and left intact
- Other widgets (`BadgeAward`, `PhotoGrid`, `ProgressTracker`, `PhotoDisplay`) — unchanged
- `frontend/src/widgets/AnimationOverlay.jsx` — unchanged; only the caller-side animation value changes for `character_display`
- No dedicated frontend test files exist yet for this widget/theme flow, so no new automated tests were added in this pass

**Verification**:
- `cd frontend && npx eslint src/components/DeviceScreen.jsx src/components/PhotoSelector.jsx src/widgets/CharacterDisplay.jsx src/widgets/gameThemes.js` — PASS
- `cd frontend && npm run build` — PASS
- Manual contract review — confirmed backend screen-frame payloads pass simple entity names and the corresponding PNG assets exist under `frontend/public/icons/`

---
