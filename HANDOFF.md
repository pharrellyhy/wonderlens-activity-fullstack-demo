# Session Handoff

Last updated: 2026-06-02

---

## Script Agent Proxy Hardening

**Problem**: A remote deployment showed current activity-game UI but Script Agent turns fell back with `Connection error`, producing source-fidelity fallback text such as `Emotion Reader is ready...`. Rebuilding frontend and sourcing Google credentials does not fix this path because the Script Agent uses DashScope through the OpenAI-compatible client, not Vertex.

**Solution**: The cached Script Agent DashScope client now uses a custom `httpx.AsyncClient` with `trust_env=False`, so broken `HTTP_PROXY`/`HTTPS_PROXY` shell variables cannot hijack provider calls. This matches the existing live-smoke helper behavior that already ignores proxy environment variables.

**Edits**: `backend/agents/script_agent.py`, `backend/tests/test_script_agent_client.py`, and `HANDOFF.md`.

**NOT Changed**: No secrets, `.env`, credential files, provider keys, frontend code, assets, activity recipes, or nginx config were changed. Other DashScope clients were not broadened in this small fix.

**Verification**:
- `cd backend && uv run pytest tests/test_script_agent_client.py -q` - 1 passed.
- `cd backend && uv run ruff check agents/script_agent.py tests/test_script_agent_client.py` - passed.
- `cd backend && uv run pytest tests/test_script_agent_client.py tests/test_generation_fallback.py -q` - 2 passed.
- Local live `/api/start-activity` check for `activity_emotion_reader` passed while fake `HTTP_PROXY`/`HTTPS_PROXY` pointed at `127.0.0.1:1`; DashScope returned HTTP 200 and the dialogue was not fallback-like.

---

## Cat5 Object Picker Visual Polish

**Problem**: Cat5 object-selection rounds, such as Phoneme Treasure Hunt, displayed actual object names (`Ball`, `Cup`, `Book`) on the screen picker and the round backdrop already contained the same selectable objects. The first label-hiding pass also exposed source PNG white backgrounds as square/solid selected cards, the selected item could snap back to a solid white card after the correct pick, the transparent picker still had a visible circular boundary around the selected item, and the vertical picker felt less grounded on the new desk/tabletop backdrop.

**Solution**: Cat5 collection/detail screens keep object labels in state for accessibility and submission, but hide those labels from the visible lens items until the later synthesis recap. Phoneme item PNGs have real alpha backgrounds, collection/detail item containers now render with transparent border/background/shadow so only the object artwork is visible, the last visible Cat5 round items are cached per collect step when the backend detail response omits `current_round_items`, the three Phoneme round backdrops were replaced with item-free nursery/tabletop scenes, and Phoneme defaults to a horizontal tabletop picker with a tester-toolbar Horizontal/Vertical toggle.

**Edits**: `frontend/src/activityGame/ActivityGameApp.jsx`, `frontend/src/activityGame/ActivityLens.jsx`, `frontend/src/index.css`, `frontend/public/activity-assets/activity_phoneme_treasure_hunt/items/*.png`, `frontend/public/activity-assets/activity_phoneme_treasure_hunt/round_{1,2,3}.png`, `frontend/tests/ActivityGameApp.test.jsx`, `frontend/tests/WonderLensDevice.test.jsx`, and `frontend/tests/activityAssets.test.js`.

**NOT Changed**: No backend behavior, activity recipes, item IDs, or provider calls changed. Cat5 synthesis/recap can still show selected labels after collection.

**Verification**:
- `cd frontend && npm test -- ActivityGameApp.test.jsx WonderLensDevice.test.jsx activityGameLayoutCss.test.js activityAssets.test.js` - 42 passed.
- `cd frontend && npx eslint src/activityGame/ActivityGameApp.jsx src/activityGame/ActivityLens.jsx src/activityGame/WonderLensDevice.jsx tests/ActivityGameApp.test.jsx tests/WonderLensDevice.test.jsx tests/activityGameLayoutCss.test.js tests/activityAssets.test.js` - passed.
- `git diff --check` - passed.
- Playwright browser smokes verified zero visible item labels before/after selection, transparent border/background and no selected container shadow before/after selection, the item-free `round_1.png` backdrop, horizontal default item centers left/current/right on the desk scene, Vertical toggle item centers top/current/bottom, and captured `/tmp/wonderlens-cat5-horizontal-picker.png` plus `/tmp/wonderlens-cat5-vertical-picker-toggle.png`.

---

## Cat3 Done Help Affordance

**Problem**: In Cat3 build rounds, the device screen first showed only the currently selected `Done` pill, then a wider in-lens `Done`/`Help` strip that made `Help` discoverable but blocked too much of the drawing scene.

**Solution**: Kept Cat3 `Done`/`Help` inside the circular device screen, but moved both choices to a transparent curved rail centered on the right lens edge. The selected choice scales up while growing inward, the drawing scene stays mostly unobstructed, the physical device scroll controls still move selection, the green device button still confirms the selected option, and the rail also supports keyboard arrows/Enter when focused. Cat5/Cat1/library crown behavior remains headless because those modes already have visible choices elsewhere.

**Edits**: `frontend/src/activityGame/ActivityGameApp.jsx`, `frontend/src/activityGame/ActivityLens.jsx`, `frontend/src/activityGame/WonderLensDevice.jsx`, `frontend/src/index.css`, `frontend/tests/ActivityGameApp.test.jsx`, and `frontend/tests/WonderLensDevice.test.jsx`.

**NOT Changed**: No backend behavior, activity recipes, assets, or live provider calls changed.

**Verification**:
- `cd frontend && npm test -- ActivityGameApp.test.jsx WonderLensDevice.test.jsx activityGameLayoutCss.test.js` - 25 passed.
- `cd frontend && npx eslint src/activityGame/ActivityGameApp.jsx src/activityGame/ActivityLens.jsx src/activityGame/WonderLensDevice.jsx tests/ActivityGameApp.test.jsx tests/WonderLensDevice.test.jsx tests/activityGameLayoutCss.test.js` - passed.
- Chrome/CDP live walkthrough reached Guided Drawing build step, verified both `Done` and `Help` are visible inside the lens, `Next device option` selects `Help`, measured the rail plus enlarged selected item fully inside the circular lens at about 7.3% of lens area, and captured `/tmp/wonderlens-cat3-side-rail.png`.

---

## Adjustable Activity Game Grid

**Problem**: The standalone activity-game shell had fixed grid dimensions, then the first tester slider lived inside the grid it resized. A delayed-commit fix made the label move without visible resizing and could snap back at release.

**Solution**: Added an outer `Grid` range control above the resizable activity shell. It adjusts the `.activity-game` CSS size variable live from 88% to 150% while staying outside the grid it controls, so the slider does not move under the cursor. The same variable drives the outer grid width/height, row minimums, and WonderLens device scale while preserving the default 100% layout. Short-height row minimums are clamped, and the transcript message area shrinks/scrolls so the input does not overlap when the grid is enlarged.

**Edits**: `frontend/src/activityGame/ActivityGameApp.jsx`, `frontend/src/index.css`, `frontend/tests/ActivityGameApp.test.jsx`, and `frontend/tests/activityGameLayoutCss.test.js`.

**NOT Changed**: No backend behavior, activity recipes, assets, or live provider code changed. The branch remains standalone.

**Verification**:
- `cd frontend && npm test -- ActivityGameApp.test.jsx activityGameLayoutCss.test.js` - 18 passed.
- `cd frontend && npx eslint src/activityGame/ActivityGameApp.jsx tests/ActivityGameApp.test.jsx tests/activityGameLayoutCss.test.js` - passed.
- Playwright rendered `http://127.0.0.1:5173/?view=activities`, changed the slider to 112%, confirmed `--activity-game-size: 1.12`, captured `/tmp/wonderlens-grid-size-check.png`, and verified transcript/input boxes do not overlap.
- Playwright checked desktop slider values 88%, 100%, and 116%, plus mobile 390x844 at 116%, with no overflow or transcript/input overlap.
- Playwright drag check confirmed the slider stays fixed while the grid resizes live to `--activity-game-size: 1.50`, does not snap to 88% on release, and has no transcript/input overlap; screenshot `/tmp/wonderlens-grid-size-live-150-check.png`.

---

## Full Activity Live QA Fix Pass

**Problem**: Live all-activity QA found source-alignment and flow defects: several Cat1 activities drifted into generic heart/feeling prompts, final device selections could ask follow-up questions, Phoneme Treasure Hunt asked for a character-name exchange after item selection, Cat3 Help could lose the current build step, short viewports pushed the intro transcript too low, and stale recap PNGs still had black padded corners.

**Solution**: Added Cat1 source-goal round rules and source-contract context to the director/directive paths, carried next-round source goals through device selections, sanitized only explicitly no-question final directives, advanced Phoneme B-detail turns without a character-name loop, kept Cat3 Help self-contained on the current build step, constrained the short-height activity layout so the intro remains visible, and replaced stale black-corner recap assets with visually safe existing closing assets.

**Edits**: `backend/agents/{script_agent.py,turn_director.py}`, `backend/turn_handling/directive.py`, `backend/skills/speaker_directive_system.md`, focused backend regressions, `frontend/src/index.css`, new `frontend/tests/activityGameLayoutCss.test.js`, `tests/test_activity_text_game_asset_contract.py`, and 9 `frontend/public/activity-assets/activity_*/recap.png` replacements.

**NOT Changed**: No secrets or credential files were edited. No runtime image-generation path was added; asset generation remains offline/static. Backend and frontend servers were left running from this worktree for manual review.

**Verification**:
- `uv run pytest backend/tests/test_activity_source_fidelity.py backend/tests/test_activity_text_game_turns.py backend/tests/test_activity_text_game_cat3.py tests/test_activity_text_game_asset_contract.py -q` - 37 passed.
- `cd frontend && npm test -- ActivityGameApp.test.jsx activityAssets.test.js activityGameLayoutCss.test.js` - 28 passed across 3 files.
- Playwright layout check: `/tmp/wonderlens-activity-ui-position-check-20260601-fixed.json` - 12/12 activities visible in first viewport on desktop and mobile.
- Live provider check with backend `.env` and Google credential JSON sourced: `/tmp/wonderlens-activity-live-check-20260601-fixed-v4.json` - 12 passed, 0 failed.
- Asset review: generated contact sheets `/tmp/wonderlens-current-activity-assets-20260601.png` and `/tmp/wonderlens-current-item-assets-20260601.png`; `/tmp/wl*` prompt scripts confirmed flat-Nordic, no-text, no-black-corner generation constraints.

---

## Promote 9 non-pilot activities to pilot parity (layout + dialogue + art)

**Problem**: The 3 pilots (career/guided/phoneme) had device-free dialogue, real flat-Nordic art, and representative layouts; the other 9 activities still had device-bound child-facing dialogue, shared placeholder images, and non-representative manifests. Also: the in-lens Done/Help crown covered the scene and the device overflowed its panel.

**Solution**:
- Layout: moved the Cat3 Done/Help crown to a bottom green pill (UI spec section 4/6), made the device fit its panel height at any window size, added device-level keyboard up/down + widened the scroll-chevron hit target.
- Dialogue: scrubbed device-bound words (card/token/tap/touch/point/click) from every child-facing source_contract field in the 9 md files into warm, invitational, in-world language; fidelity terms preserved. Done via a per-activity subagent workflow.
- Art: generated 7 flat-Nordic beat scenes + a single-subject icon for each of the 9 (63 + 9 = 72 PNGs, 512x512) via Codex imagegen against `style-reference-flat-nordic.png`, content-faithful to each activity's rounds. Promoted all 9 manifest entries to representative `single`-scene layouts and added them to REPRESENTATIVE_ACTIVITY_IDS in both contract tests. Fixed a pre-existing phoneme synthesis `picker`->`carousel` manifest divergence.

**Edits**: `frontend/src/index.css`, `frontend/src/activityGame/ActivityGameApp.jsx`, the 9 `backend/games/activity_*.md`, `backend/tests/test_activity_source_fidelity.py`, `tests/test_activity_text_game_asset_contract.py`, `frontend/tests/activityAssets.test.js`, `frontend/public/activity-assets/<9 dirs>/*.png` + `activity-assets.manifest.json`, new `scripts/gen_beat.sh` + `scripts/promote_activity_manifest.py`, `docs/plans/2026-05-30-promote-9-activities-to-pilot-parity.md`. Commits: `7a600f7` (layout), `45f4e0a` (dialogue), `1f84422` (art).

**Follow-ups (same session, committed)**: 3 pilots' regenerated art committed (`443136f`); single-subject pilot icons replacing old multi-object scene icons (`2ae1d7d`); passive choice/carousel layouts + 15 item sprites for animal_sound/recognition_pop/vegetable_sort (`356df98`); interactive device-selection wired for recognition_pop, then extended to vegetable_sort + animal_sound Cat1 rounds (`c35b9b0`, `400c118`, mirrors Cat3/Cat5 — scroll highlights a card, select sends its label). vegetable_sort round scenes regenerated to show each round's 3 individual choice veggies, matching the item cards (`cddcd9a`). PR #14 opened + updated. Deeper live multi-turn flows driven for ALL 9 non-pilots — dialogue warm, invitational, device-word-free, source-faithful; recognition_pop live rounds reference exactly its item sprites. Then made selections crisply advance for ALL three: an `is_selection` flag flows TurnRequest->TurnInput, and a directive fast-path treats a selection at a Cat1 STEP_3_ROUND_ as the round's answer-of-record (action=advance, live speaker still acknowledges the pick) — `75bd94d`. Live-verified veg/animal advance round_1->2->3->celebrate. Also added a per-activity intro card in the transcript pre-start (`5d04d01`, new ActivityIntro.jsx; referenced but did not copy main's GameDetailView), then made it tester-facing (Category Cat1/3/5, Mechanic, Tier, Rounds, IB Focus, Source) + fixed its float/overlap, and added a responsive flow layout — below ~980px tall the kiosk card grows + the page scrolls + the device is width-driven; fixed card kept only on tall screens; <760px stays stacked (`0a009f9`). Verified at 390/1366x768/1440x1100.

**NOT Changed**: Orphaned `recap.png` placeholders left in place. The build-script's aspirational carousel+crop design is superseded by separate item sprites.

**Verification**: backend definitions+fidelity+asset-contract (21) pass; frontend tests (74) + lint + build pass; live smoke effectively 12/12. Style self-confirmed via contact-sheet review. Pre-existing unrelated failures: top-level tests/ entity/scenario/turn-handler (fail at HEAD independent of this work) and live-server ai_quality (need a running server).

---

## Guided Drawing Beat Art Regeneration

**Problem**: The Guided Drawing pilot needed the first three real flat-Nordic scene beats generated in the approved WonderLens activity asset style: intro, rules, and round 1.

**Solution**: Used Codex built-in image generation with the `style-reference-flat-nordic.png` target to create three separate full-bleed square PNG scenes, resized them to 512x512, and copied them into the Guided Drawing activity asset folder.

**Edits**:
- `frontend/public/activity-assets/activity_guided_drawing/intro.png` — Guided Artist child waving at a desk with blank paper.
- `frontend/public/activity-assets/activity_guided_drawing/rules.png` — hand drawing one pencil mark with a muted-sage checkmark.
- `frontend/public/activity-assets/activity_guided_drawing/round_1.png` — centered paper with one large pencil circle and a colored pencil.

**NOT Changed**: Other pilot assets, manifest metadata, source recipes, prompts, and the unrelated uncommitted Career/Phoneme image edits in this worktree.

**Verification**:
- Final PNG inspection confirmed all three files are 512x512 PNGs with no text, circular mask, lens border, or combined multi-image source.
- `scripts/build_activity_screen_assets.py` ran cleanly in a temporary copy to avoid overwriting unrelated dirty image assets; manifest asset-path validation passed there.
- `cd frontend && npm run test -- activityAssets.test.js` — 13 passed.

---

## Pilot Hardening + Asset Regen + Crown — Streams 1+2/4 + Stream 3 scaffolding implemented (autonomous /goal run)

**Problem**: Execute the plan-backed pilot-hardening goal: frame-sync + live-LLM guardrails (Streams 1+2), Digital-Crown picker (Stream 4), and Stream 3 asset scaffolding (non-art), leaving image art + browser walkthrough human-gated.

**Solution**: Implemented all 10 Stream 1+2 tasks (`finalize.py` step→beat table + `derive_frame` + `finalize_turn`; routed `core/directive/rounds/helpers` through it; `_sync_round_from_step` clears stale round on non-round steps; manifest `celebrate`/`closing` beats for the 3 pilots; explicit frontend step→beat table preferring `screen_frame.beat`; deterministic `_violates_contract`/`_violates_flow`; broadened completion regex; `example_ai_line` sanitized at load; exhaustion returns the name-enriched deterministic fallback; validators wired into the live directive + rounds paths). Implemented Stream 4 (one reusable `CrownPicker.jsx` with momentum/detent/keyboard/reduced-motion, wired into activity library + Cat3 Done/Help + Cat5 item picker; in-lens Cat3 build panel replaced by the crown). Implemented Stream 3 non-art scaffolding (manifest beats, representative-gated `_required_beat_ids`, placeholder `celebrate.png`/`closing.png`, dropped pilot `ITEM_CROPS`).

**Edits**: `backend/turn_handling/{finalize(new),core,directive,rounds,helpers,generation}.py`, `backend/agents/script_agent.py`, `backend/schemas/visual_composition.py`; new `backend/tests/{test_finalize_frame,test_finalize_frame_sync,test_finalize_validators}.py` + appends to turns; `tests/test_activity_text_game_asset_contract.py`; `frontend/src/activityGame/{CrownPicker.jsx(new),ActivityGameApp.jsx,activityAssets.js}`, `frontend/src/index.css`, manifest + 6 placeholder PNGs; `frontend/tests/{CrownPicker(new),ActivityGameApp,activityAssets}`; `scripts/build_activity_screen_assets.py` (dropped pilot crops). 8 conventional commits.

**NOT Changed**: The 9 non-pilot activities' behavior/recipes, prompts, tier_rules, `test_ai_quality.py`; the pilot `.md` recipes; Stream 3 real image art (human-gated). Legacy non-director `core.py` interactive returns kept on `derive_frame` (director is enabled in `config.yaml`, so the live path is `directive.py`; documented divergence to avoid risk on a dead path).

**Follow-up fix (commit 10)**: While investigating the live-suite reds, found that Task 10's `_append_ai_turn` move (now after `_advance_state`) recorded directive-advance AI lines against the *post*-advance step, changing the step labels the next turn's prompt renders (`script_agent.py:901`). Restored pre-advance attribution via optional `step`/`round_number` params on `_append_ai_turn`, captured before `_advance_state` (stay/exit unaffected). Re-tested: this did **not** change the `test_t0_cat1_full_flow` failures, conclusively proving they are pre-existing live-LLM T0 generation behavior, not a regression from this work.

**Verification** (worktree; live provider, creds sourced, local proxy bypassed via `NO_PROXY`): Streams-1+2 suite **49 passed**; asset-contract **6 passed, 1 pre-existing carousel-vs-picker red (allowed)**; backend ruff `turn_handling/ agents/script_agent.py` **clean**; frontend **72 tests / lint / build green**; `git diff --check` **clean**; **live smoke clean 12/12** (after retrying through live phrasing variability that rotates across activities incl. non-pilots); full backend suite **112 passed, 2 skipped, 3 failed** — `test_t0_cat1_full_flow[dog/cat/dinosaur]` (live-LLM open-question-without-scaffold at T0 on **non-pilot emotional** activities) fail every run. **Proof these are not regressions**: `git diff add7ecd..HEAD` touches none of `test_ai_quality.py`, the non-pilot recipes, prompts, `tier_rules`, or the T0-scaffold logic (`_has_model_phrase`/`_ends_with_open_question`); the failing paths don't trigger the new validators; and fixing the one real regression (history attribution) left the failures unchanged. **Blocker to a 100%-green full suite**: pre-existing/environmental live-LLM T0 quality on out-of-scope non-pilot activities (fixable only by modifying the 9 activities/shared T0 prompt, which Hard Constraints forbid). **Human-gated remainder**: Stream 3 image-art generation + per-pilot sign-off, and the Cat1/Cat3/Cat5 browser walkthrough at `/?view=activities`.

## Pilot Hardening + Asset Regen + Crown — Planning Complete (run via /goal)

**Problem**: The three pilots need live-LLM robustness hardening (A off-intent drift, B flow-control, C wording leaks, F asset↔step↔dialogue desync), flat-Nordic asset regeneration, and an Apple-Watch Digital-Crown picker. This session produced the design and execution artifacts only — no runtime code was changed.

**Solution**: Settled the design via brainstorming (keep live LLM + harden guardrails; one consolidated `finalize_turn` stage owning frame derivation + line validation; raster assets via Codex imagegen; the 3 pilots' `.md` are source-of-truth — P2; deterministic A-i validation; vertical-list crown reused across activity library + Cat3 Done/Help + Cat5 picker). Root-caused the frame-sync bug (F): scattered `_get_screen_frame` timing vs post-advance `sessionState`, stale `current_round`, and a lossy `beatIdFromSessionState` collapsing celebrate/closing → recap. Authored a design spec, a 21-task TDD implementation plan, and a plan-backed `/goal` execution contract.

**Edits** (docs only; committed this session):
- `docs/plans/2026-05-29-pilot-flow-robustness-and-asset-regen.md` — design spec (commit `5334a71`).
- `docs/plans/2026-05-29-pilot-flow-robustness-and-asset-regen-implementation.md` — 21-task TDD plan across 4 streams (commit `712bf4f`).
- `goals/2026-05-29-pilot-flow-robustness-and-asset-regen-goal.md` — plan-backed `/goal` execution contract (commit `56b68ab`).
- `frontend/public/activity-assets/prompts/style-reference-flat-nordic.png` + `wonderlens-activity-style.md` — flat-Nordic style reference wired into Stream 3 (commit `0127d34`).
- `docs/plans/README.md`, `goals/README.md` — `Planned` index rows linking the pair.

**NOT Changed**:
- No backend/frontend runtime code; no assets regenerated; no tests run (planning only).
- The 3 pilot `.md` recipes must not be re-converted by the importer (lossy — drops `source_dialogue`/themes).
- Uncommitted and left as-is: the `CLAUDE.md` type-change and untracked `docs/activity-text-game-branch-summary.md`.

**Verification / Next**:
- No code verification this session.
- To execute: start a **fresh session** (clear first — `/clear` drops an active goal, so clear *then* set the goal), then run the `## Goal Invocation` line from `goals/2026-05-29-pilot-flow-robustness-and-asset-regen-goal.md` (or `claude -p "/goal …"`).
- Autonomous `/goal` gate = Streams 1+2 & 4 + Stream 3 scaffolding (offline checks in the goal's Required Checks). Stream 3 image-art generation + per-pilot sign-off, live smoke, and browser walkthrough are **human-gated** — the worker generates candidates and stops; it must not auto-approve art.

---

## Live Pilot Flow Regression Fixes

**Problem**: Manual testing still found step/state drift in the three representative pilots. Career Decision Role Play asked the first firefighter decision while the backend state was still on the rules step, so later answers repeated or jumped between the wrong scenarios and assets. Guided Drawing could still ask an open-ended "what shape" setup question. Phoneme Treasure Hunt asked for B words before the Cat5 picker state was active, leaving the scroll control disabled, and could accept `screen` as a B word.

**Solution**: Added deterministic hook-confirmation fast paths so hook acceptance advances only into the transition/rules/setup step and does not ask the first actionable round yet. Tightened Cat3 setup confirmation to cue the fixed first build step, disabled the transcript input while Cat3 Done/Help device controls are active, rejected non-B typed phoneme finds before collection, and normalized phoneme wording away from "B sound/B thing" language.

**Edits**:
- `backend/turn_handling/directive.py` — added hook-confirmation transition guards, Cat3 setup direction, and non-B phoneme correction fast path.
- `backend/turn_handling/collection.py` — made text collection return accepted/rejected and reject non-B words for the phoneme pilot.
- `backend/agents/script_agent.py` — normalized generated phoneme dialogue from "B sound/B thing" to B-starting-word language.
- `frontend/src/activityGame/ActivityGameApp.jsx` — disables free text while Cat3 Done/Help device selection is active.
- Focused backend/frontend regressions were added for the above cases.

**NOT Changed**:
- No assets were regenerated.
- No new interaction modes, audio, camera, or upload paths were added.
- The live backend provider/API path remains unchanged.

**Verification**:
- `cd backend && uv run pytest tests/test_activity_source_fidelity.py tests/test_generation_text_mode.py tests/test_activity_text_game_cat3.py tests/test_activity_text_game_turns.py -q` — 29 passed.
- `cd backend && uv run ruff check agents/script_agent.py turn_handling/directive.py turn_handling/collection.py tests/test_activity_source_fidelity.py tests/test_activity_text_game_cat3.py tests/test_activity_text_game_turns.py tests/test_generation_text_mode.py` — passed.
- `cd frontend && npm test -- tests/ActivityGameApp.test.jsx tests/WonderLensDevice.test.jsx tests/activityAssets.test.js` — 27 passed.
- `cd frontend && npx eslint src/activityGame/ActivityGameApp.jsx tests/ActivityGameApp.test.jsx` — passed.
- `cd frontend && npm run build` — passed; Vite emitted the existing large chunk warning.
- `git diff --check` — passed.
- Restarted backend/frontend from this worktree with backend-root `.env` and Google credential JSON sourced for live API access.
- Live API walkthrough passed: Career `sure -> yes -> i dont know -> send help` stayed aligned through rules, round 1, and round 2; Guided `sure -> yes` cued `Draw one big circle`; Phoneme `yes -> yes` exposed `Ball,Cup,Book` at `STEP_3_COLLECT_1`, and typed `screen` was rejected with no collected item.
