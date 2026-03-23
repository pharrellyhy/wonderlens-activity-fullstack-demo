# Session Handoff

Last updated: 2026-03-23

---

## Fix: Small-Screen Responsive Sizing Pass

**Problem**: The frontend layout was tuned for larger mobile/tablet widths, but many shell controls, widget cards, badges, progress circles, and icons kept their default sizes all the way down to very small screens. On narrow phones this made the camera viewport and surrounding UI feel oversized and cramped. A follow-up issue remained on short, wide viewports: the fixed-height shell could clip the top device area instead of adapting vertically.

**Solution**: Added a compact-mobile sizing layer for screens under 420px and tightened the highest-pressure UI surfaces under 380px. The pass keeps desktop/tablet styling intact while shrinking spacing, copy, controls, widget chrome, and icon sizes inside the app shell, camera frame, conversation panel, photo selection flow, and device widgets. After follow-up reports that the device panel content still felt oversized, I narrowed the fix to the in-panel layer: `DeviceScreen` now uses a tighter widget wrapper, and the device-only widgets no longer upscale at `sm` width breakpoints. That keeps the camera content sized to the panel instead of to the overall viewport width. After screenshot review (`images/cutoff-1.png`, `images/cutoff-2.png`), I also fixed two concrete overflow cases: the lower-panel photo selector now anchors to the top instead of vertically centering oversized content, and the in-device photo display now sizes by available height rather than by `max-w-md`. I also removed one unused `PhotoGrid` prop surfaced by lint during verification.

**Edits**:
- `frontend/src/index.css` — added global compact-mobile root font scaling for sub-420px screens plus short-viewport shell rules for scrolling/compression under `760px` height
- `frontend/src/App.jsx`, `frontend/src/components/TopBar.jsx`, `frontend/src/components/ToyCameraFrame.jsx`, `frontend/src/components/DeviceScreen.jsx`, `frontend/src/components/ConversationPanel.jsx`, `frontend/src/components/TextInput.jsx` — reduced shell spacing and control/icon sizing for extra-small screens; `DeviceScreen` now applies a tighter wrapper around in-panel widgets
- `frontend/src/components/PhotoSelector.jsx`, `frontend/src/components/GameDetailView.jsx`, `frontend/src/components/PhotoGallery.jsx` — tightened photo picker/detail/gallery layouts and labels on narrow viewports; `PhotoSelector` now top-aligns scrollable content instead of centering it
- `frontend/src/widgets/BadgeAward.jsx`, `frontend/src/widgets/ProgressTracker.jsx`, `frontend/src/widgets/CharacterDisplay.jsx`, `frontend/src/widgets/PhotoGrid.jsx`, `frontend/src/widgets/PhotoDisplay.jsx` — switched oversized widget/icon elements to compact breakpoint rules and `clamp()` sizing; removed `sm`-based device-panel enlargement
- `HANDOFF.md` — added this entry

**NOT Changed**:
- Backend, API contracts, session orchestration logic, and activity behavior — unchanged
- Existing unrelated worktree edits in `frontend/src/components/AiAvatar.jsx` and `frontend/src/components/SfxIndicator.jsx` were left untouched
- No new frontend test runner or browser automation was added in this pass

**Verification**:
- `rg -n "max-\\[380px\\]:|clamp\\(" frontend/src/App.jsx frontend/src/components/TopBar.jsx frontend/src/components/DeviceScreen.jsx frontend/src/components/PhotoSelector.jsx frontend/src/components/PhotoGallery.jsx frontend/src/widgets/BadgeAward.jsx frontend/src/widgets/ProgressTracker.jsx frontend/src/widgets/CharacterDisplay.jsx` — PASS
- `rg -n "sm:w-|sm:h-|sm:text-|sm:p-|sm:gap-" frontend/src/components/DeviceScreen.jsx frontend/src/components/PhotoGallery.jsx frontend/src/widgets/BadgeAward.jsx frontend/src/widgets/ProgressTracker.jsx frontend/src/widgets/CharacterDisplay.jsx frontend/src/widgets/PhotoGrid.jsx frontend/src/widgets/PhotoDisplay.jsx` — PASS
- `rg -n "justify-center h-full p-6|max-w-md aspect-square" frontend/src/components/PhotoSelector.jsx frontend/src/widgets/PhotoDisplay.jsx` — PASS
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

## Review Follow-Up: Harden Game Summary Detail View + Fallback Data

**Problem**: Picking up the new game-detail-view work exposed two concrete frontend gaps and one test gap. First, the fallback summary data embedded in `PhotoSelector.jsx` had already drifted from the backend truth for several demos (`cat`, `dinosaur`, and `dandelion` showed stale tier/concept/mechanic/preview data whenever `/api/entities` failed). Second, the new `GameDetailView.jsx` collectible preview fallback used direct DOM mutation inside `onError`, which is brittle in React. Third, the new `/api/entities` summary payload had no focused regression coverage proving the summary shape or the fallback data stayed aligned.

**Solution**: Kept the backend summary API shape, but added targeted regression coverage around it and simplified the frontend implementation. Moved the fallback category data into a dedicated module so it can be verified independently, synced it to the current backend demo summaries, replaced the DOM-mutation image fallback with a normal React state path, and added a small unmount guard around the entity fetch in `PhotoSelector`.

**Edits**:
- `backend/entity_registry.py` — reviewed and kept the new summary payload path (`tier`/IB metadata on `EntityConfig`, `_build_entity_summary()`, and `summary` in `/api/entities`) unchanged after adding test coverage around it
- `backend/game_parser.py` — reviewed and kept the new metadata plumbing unchanged in this pass
- `frontend/src/components/photoSelectorFallbacks.js` — **NEW**: extracted fallback category/summary data into a dedicated module; synced all 5 demo summaries to the current backend data
- `frontend/src/components/PhotoSelector.jsx` — imports the new fallback module; keeps the detail-view flow but removes the huge inline fallback object and guards against setting fetched categories after unmount
- `frontend/src/components/GameDetailView.jsx` — simplified duplicated label-formatting helpers and replaced the collectible preview `onError` DOM mutation with a small React fallback component
- local `tests/test_api.py` — extended `TestEntitiesEndpoint` with summary-payload assertions
- local `tests/test_photo_selector_fallbacks.py` — **NEW**: Node-backed regression check that imports the frontend fallback module and verifies the fallback summaries match the current demo truth
- `HANDOFF.md` — replaced the draft feature entry with this reviewed follow-up

**NOT Changed**:
- `backend/server.py` — `/api/entities` endpoint shape unchanged; it just serves the richer summary data
- `frontend/src/App.jsx` and the session start flow — unchanged
- Agent pipeline, schemas, step instructions, and other frontend components — unchanged
- Generated badge/icon asset files already modified in the worktree were not changed in this pass

**Verification**:
- `uv run pytest tests/test_api.py::TestEntitiesEndpoint tests/test_photo_selector_fallbacks.py tests/test_entity_registry.py -q` — PASS (`36 passed`)
- `cd backend && uv run ruff check entity_registry.py game_parser.py ../tests/test_api.py ../tests/test_photo_selector_fallbacks.py ../tests/test_entity_registry.py` — PASS
- `cd backend && uv run ruff format --check entity_registry.py game_parser.py ../tests/test_api.py ../tests/test_photo_selector_fallbacks.py ../tests/test_entity_registry.py` — PASS
- `cd frontend && npx eslint src/components/PhotoSelector.jsx src/components/GameDetailView.jsx src/components/photoSelectorFallbacks.js` — PASS
- `cd frontend && npm run build` — PASS

---

## Generate IB Concept Badge Images

**Problem**: The BadgeAward widget rendered a generic CSS gradient circle with an SVG icon for all IB concepts. Every concept looked identical — children couldn't visually distinguish Perspective from Causation or any other concept.

**Solution**: Created a Gemini image generation script following the existing `generate_cat5_icons_gemini.py` pattern, and updated the BadgeAward widget to render concept-specific badge images with a CSS fallback.

**Edits**:
- `scripts/generate_concept_badges_gemini.py` — **NEW**: generates 8 IB concept badge PNGs (256×256) using gemini-2.5-flash-image; reuses shared utilities from existing icon scripts; supports `--only`, `--overwrite`, `--mode` CLI flags
- `frontend/src/widgets/BadgeAward.jsx` — replaced single CSS badge circle with per-concept `<img>` badges; added `ConceptBadge` component with `onError` fallback to CSS gradient; when no concepts provided, keeps original CSS rendering; multiple concepts display in a flex row with staggered `badge-pop` animation
- `frontend/src/index.css` — added `@keyframes badge-pop` and `.animate-badge-pop` for staggered concept badge entrance animation
- `frontend/public/badges/` — **NEW**: output directory for generated badge PNGs (run script to populate)

**NOT Changed**:
- Backend — zero changes; pipeline already passes `concepts: string[]` via widget_params
- `frontend/src/icons/index.js` — BadgeIcon import stays for CSS fallback path
- Existing icon generation scripts — read-only reference
- Props/widget_params contract — unchanged

**Verification**:
- `cd scripts && python generate_concept_badges_gemini.py --overwrite` — generates 8 PNGs into `frontend/public/badges/`
- `cd backend && uv run ruff check ../scripts/generate_concept_badges_gemini.py` — PASS
- Start frontend dev server, run Cat1 session → badge images appear at STEP_4_CELEBRATE and STEP_5_CLOSING
- Start Cat5 session → multiple concept badges display correctly at STEP_5_CELEBRATE and STEP_6_CLOSING
- Rename a badge file → CSS gradient fallback renders correctly

---

## Review Follow-Up: Harden Prod Game Frontmatter Generator + Add Coverage

**Problem**: Picking up the pending prod-game promotion work exposed three concrete gaps in the new generator path. There were no focused tests for the new script, `stop_sign_cat1_prod.md` extracted the wrong awarded role title (`True Safety Hero` instead of `Safety Solver`), `lion_cat5_prod.md` lost detail in its collection criterion (`big strong` instead of `big, strong, or tough`), and Cat5 docs without an explicit Step 2 catchphrase fell back to a TODO mission metaphor even when a clean role title was available. The script also duplicated its frontmatter-building logic between normal and `--dry-run` execution.

**Solution**: Added focused regression coverage for the generator and the new Cat1 mechanics, then simplified the script around a shared `build_frontmatter()` path used by both write and dry-run modes. Tightened extraction precedence so celebration titles beat generic closing praise, improved collection-mission parsing to preserve descriptive criteria and extract collection counts from the prose itself, and defaulted Cat5 mission metaphors to `You are a {role_title}!` when the doc does not provide a better explicit phrase.

**Edits**:
- `scripts/generate_game_frontmatter.py` — simplified generation through shared `build_frontmatter()` plumbing; fixed role-title extraction precedence; improved collection-count / collection-criterion parsing; added Cat5 mission-metaphor fallback to the extracted role title
- local `tests/test_generate_game_frontmatter.py` — **NEW**: batch parseability coverage for all 12 `*_prod.md` files, regression tests for stop-sign role title, lion collection criterion, piano mission-metaphor fallback, and schema validation for `prediction_game` / `helper_hotline`
- `HANDOFF.md` — replaced the draft feature note with this reviewed follow-up entry

**NOT Changed**:
- `backend/schemas/creative_slots.py` — reviewed and left with the new `"prediction_game"` / `"helper_hotline"` literals as authored
- `backend/skills/step_instructions/cat1_step2_rules__prediction_game.md`, `backend/skills/step_instructions/cat1_step3_round__prediction_game.md`, `backend/skills/step_instructions/cat1_step2_rules__helper_hotline.md`, `backend/skills/step_instructions/cat1_step3_round__helper_hotline.md` — reviewed and left unchanged in this pass
- `backend/game_parser.py`, `backend/game_loader.py`, `backend/entity_registry.py`, and existing demo game MD files — unchanged
- Frontend — zero changes

**Verification**:
- `uv run pytest tests/test_generate_game_frontmatter.py -q` — PASS (`5 passed`)
- `uv run pytest tests/test_generate_game_frontmatter.py tests/test_entity_registry.py tests/test_game_parser.py -q` — PASS (`79 passed`)
- `uv run ruff check scripts/generate_game_frontmatter.py tests/test_generate_game_frontmatter.py backend/schemas/creative_slots.py` — PASS
- `uv run ruff format --check scripts/generate_game_frontmatter.py tests/test_generate_game_frontmatter.py backend/schemas/creative_slots.py` — PASS

---

## Review Follow-Up: Restore Hook-to-Step2 Transition + Align Local Tests

**Problem**: Picking up the latest Cat5 synthesis fix exposed one real regression in the new generic interactive-step branch in `backend/turn_handler.py`: after the child replied to `STEP_1_HOOK`, the server advanced state to step 2 but still returned the hook response type/frame instead of the step-2 rules or mission prompt. The local review tests were also partially stale after the synthesis change, still asserting pre-fix behavior for synthesis completion and closing delivery.

**Solution**: Restored the hook-specific transition behavior by special-casing an already-prompted `STEP_1_HOOK` to advance into step 2 before generating the next turn. Kept the newer synthesis behavior intact: synthesis completion still returns the synthesis reply first, then leaves auto-advance to fetch celebration. I also tightened the local tests so they now cover the hook regression directly and match the current synthesis/closing semantics.

**Edits**:
- `backend/turn_handler.py` — special-cased completed `STEP_1_HOOK` handling inside section 7d so the first post-start child reply returns the step-2 prompt; clarified the comment for hook vs. synthesis behavior
- local `tests/test_turn_handler.py` — added a hook-to-mission regression test; updated the synthesis-follow-up assertions to expect the synthesis reply plus `auto_advance=True`
- local `tests/test_api.py` — fixed the closing-delivery test fixture so it enters the already-prompted celebration branch it is meant to validate
- `HANDOFF.md` — added this review/update entry

**NOT Changed**:
- `backend/skills/step_instructions/cat5_step4_synthesis*.md` prompt edits were reviewed and left unchanged in this pass
- Frontend auto-advance/session orchestration code was reviewed against the current backend contract and left unchanged
- `.gitignore` was not changed; the `tests/` tree remains local-only and ignored in this repo snapshot

**Verification**:
- `uv run pytest tests/test_turn_handler.py -q` — PASS (`10 passed`)
- `uv run pytest tests/test_api.py -q` — PASS (`24 passed`)
- `uv run pytest tests/test_turn_handler.py tests/test_api.py -q` — PASS (`34 passed`)
- `cd backend && uv run ruff check turn_handler.py ../tests/test_turn_handler.py ../tests/test_api.py` — PASS
- `cd backend && uv run ruff format --check turn_handler.py ../tests/test_turn_handler.py ../tests/test_api.py` — PASS

---

## Fix Cat5 Synthesis Response Swallowed + Help Request Misclassified

**Problem**: In Cat5 Step 4 (synthesis), when the child responds to the synthesis prompt (e.g. "can you help me"), the AI's synthesis response was never shown. The turn handler advanced to STEP_5_CELEBRATE, generated a new response, and returned only that — the synthesis reply was swallowed. Additionally, "can you help me" was misclassified as "do it for me" instead of "stuck/confused", skipping synthesis entirely.

**Solution**: Two-part fix:
1. **Prompt fix**: Added "can you help me", "help", "I need help" to the stuck/confused bucket in synthesis instructions with explicit `stay_on_step: true`. Added disambiguation note distinguishing "help me" (stuck) from "do it for me" (create content) in both `naming_story` and `comparison_chart` fragments.
2. **Architecture fix**: Rewrote section 7d of `turn_handler.py`. Interactive step completion now returns the current step's response (not the next step's) and sets `auto_advance` for the frontend to fetch the next step. Auto-advance steps use `_already_prompted_on_step` to distinguish: if already generated (Cat1 celebrate from round advance), advance through as before; if not yet generated (Cat5 celebrate after synthesis), generate then advance.

**Edits**:
- `backend/skills/step_instructions/cat5_step4_synthesis.md` — added help request patterns to stuck/confused bucket with `stay_on_step: true`
- `backend/skills/step_instructions/cat5_step4_synthesis__naming_story.md` — added "help me" vs "do it for me" disambiguation note
- `backend/skills/step_instructions/cat5_step4_synthesis__comparison_chart.md` — same disambiguation note
- `backend/turn_handler.py` (section 7d, ~lines 518-610) — rewrote interactive step completion to return step's own response; rewrote auto-advance path with `_already_prompted_on_step` guard

**NOT Changed**:
- `backend/state_machine.py` — step transitions unchanged
- `backend/agents/script_agent.py` — prompt assembly unchanged
- Frontend auto-advance mechanism (`useSessionOrchestration.js`) — unchanged, uses `data.turn.auto_advance`
- Cat1 flows — behavior preserved via `_already_prompted_on_step` guard

**Verification**:
- `cd backend && uv run ruff check turn_handler.py` — PASS
- `cd backend && uv run ruff format --check turn_handler.py` — PASS
- `cd backend && uv run mypy turn_handler.py --ignore-missing-imports` — no new errors

---
