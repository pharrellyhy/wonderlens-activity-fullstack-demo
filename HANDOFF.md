# Session Handoff

Last updated: 2026-03-20

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

## Review Game MD Loader Follow-Up: Fail-Fast Startup + Test Fixture Cleanup

**Problem**: Reviewing the new game-MD single-source refactor exposed two real gaps. First, `backend/game_loader.py` only logged parse failures and kept going, so a broken frontmatter file could silently drop a demo game from the registry. Second, `validate_registry()` still reported success when the registry was empty. The local API/schema tests also still had stale fixture/import cleanup issues from the same refactor, including a `what_would_it_say` mechanic value that no longer matches the current `voice_acting` schema.

**Solution**: Tightened the loader/validation path so startup fails loudly instead of accepting partial or empty demo configuration. `_load_demo_games()` now clears stale state before each scan, accumulates parse failures, and raises a `RuntimeError` listing the broken files. `validate_registry()` now rejects an empty registry. I also tightened the local test coverage around those failure paths and updated the stale API fixture/import cleanup so the reviewed test bundle reflects the current schema and loader behavior.

**Edits**:
- `backend/game_loader.py` — clear cached loader state before rescanning; collect parse failures; raise `RuntimeError` when any game MD file with frontmatter fails to parse
- `backend/entity_registry.py` — make `validate_registry()` fail when `ENTITY_REGISTRY` is empty
- local `tests/test_game_parser.py` — added regression coverage proving `_load_demo_games()` raises on a broken game MD file
- local `tests/test_entity_registry.py` — added regression coverage proving `validate_registry()` rejects an empty registry
- local `tests/test_api.py` — updated stale Cat1 fixture mechanic from `what_would_it_say` to `voice_acting`
- local `tests/test_schemas.py` — moved the new `game_loader` import to the module import block so the updated schema test passes lint/format cleanly
- `HANDOFF.md` — added this review/update entry

**NOT Changed**:
- `backend/recipe_loader.py`, `backend/server.py`, and the new `backend/games/*.md` content were reviewed in this pass and left unchanged
- `backend/skills/step_instructions/cat5_step4_synthesis*.md` prompt edits were reviewed and left unchanged
- Deleted recipe/scenario asset files and the removed `images/entity_icons.png` artifact already present in the worktree were not touched in this pass

**Verification**:
- `cd backend && uv run ruff check game_loader.py entity_registry.py recipe_loader.py server.py ../tests/test_game_parser.py ../tests/test_entity_registry.py ../tests/test_schemas.py ../tests/test_api.py ../tests/conftest.py` — PASS
- `cd backend && uv run ruff format --check game_loader.py entity_registry.py recipe_loader.py server.py ../tests/test_game_parser.py ../tests/test_entity_registry.py ../tests/test_schemas.py ../tests/test_api.py ../tests/conftest.py` — PASS
- `cd backend && uv run pytest ../tests/test_game_parser.py ../tests/test_entity_registry.py ../tests/test_schemas.py ../tests/test_api.py -q` — PASS (`115 passed`)

---

## Game MD Files as Single Source of Truth for Demo Entities

**Problem**: Demo entity data was spread across 3 manually-synced sources: `entity_registry.py` (hardcoded config with 140+ lines of Pydantic model instantiation), `recipes/*.json` (step instructions + screen frames), and `scenarios/*.yaml` (interaction scripts). Adding or modifying a game required updating all three, with no cross-validation.

**Solution**: Consolidated all demo entity data into one markdown file per game with YAML frontmatter in `backend/games/`. Created `game_parser.py` to parse frontmatter into existing Pydantic models (`EntityConfig`, `InstructionRecipe`), and `game_loader.py` to scan the games directory at import time and populate the entity registry. The registry module (`entity_registry.py`) now has an empty list that gets populated via `_populate_registry()` called by the game loader. Recipe loading checks game_loader first, falling back to JSON for non-demo entities (e.g. `polka_dot_patrol_hard.json`).

**Edits**:
- `backend/games/{mood_changer_dog,dream_whisperer_cat,time_machine_dinosaur,polka_dot_patrol,fluffy_expedition_dandelion}.md` — **NEW**: 5 game MD files with full YAML frontmatter (entity config, creative slots, step instructions, screen frames, metadata, keywords, collection catalogs)
- `backend/game_parser.py` — **NEW**: `parse_game_file()` extracts YAML frontmatter and builds `EntityConfig` + `InstructionRecipe`
- `backend/game_loader.py` — **NEW**: scans `games/` at import time, calls `_populate_registry()` to fill entity registry
- `backend/entity_registry.py` — removed 140-line hardcoded `ENTITY_REGISTRY` list; added `_populate_registry()` and `_rebuild_lookups()`; changed `validate_registry()` to check for game MD files instead of recipe JSON + scenario YAML
- `backend/recipe_loader.py` — `load_instruction_recipe()` checks `game_loader.get_demo_recipe()` first, JSON fallback for non-demo entities
- `backend/server.py` — added `game_loader` import to trigger registry population at startup
- `tests/conftest.py` — added `game_loader` import; updated `instruction_recipe` fixture to use `get_demo_recipe()` instead of deleted JSON file
- `tests/test_game_parser.py` — **NEW**: 41 tests covering all 5 entities, creative slots, collection catalogs, recipe structure, metadata values
- `tests/test_entity_registry.py` — no structural changes needed (all assertions pass with MD-sourced data)
- `tests/test_schemas.py` — replaced `test_demo_recipe_files_validate` (used deleted JSON path) with `test_demo_game_recipes_validate`

**Deleted**:
- `backend/recipes/{mood_changer_dog,dream_whisperer_cat,time_machine_dinosaur,polka_dot_patrol,fluffy_expedition_dandelion}.json` — replaced by game MD files
- `backend/scenarios/{mood_changer_dog,dream_whisperer_cat,time_machine_dinosaur,polka_dot_patrol,fluffy_expedition_dandelion}.yaml` — replaced by game MD files
- Kept: `polka_dot_patrol_hard.json`, `mood_changer_dog_silent_exit.yaml`, `polka_dot_patrol_hard.yaml`, `dino_time_traveler.yaml`

**NOT Changed**:
- All Pydantic schemas in `backend/schemas/` — unchanged, reused by parser
- Agent modules (`director.py`, `script_agent.py`, `visual_agent.py`, `recipe_assembler.py`) — unchanged
- Step instruction fragments in `backend/skills/step_instructions/` — unchanged
- Frontend — zero changes
- Existing 12 `*_prod.md` design docs in `backend/games/` — no frontmatter, silently skipped by loader

**Verification**:
- `uv run pytest tests/test_game_parser.py tests/test_entity_registry.py -v` — PASS (72 passed)
- `uv run pytest tests/ -k "not e2e" -q` — 195 passed, 27 failed (pre-existing failures from `what_would_it_say` game_mechanic in test fixtures)
- `cd backend && uv run ruff check .` — PASS
- `cd backend && uv run ruff format --check game_parser.py game_loader.py entity_registry.py recipe_loader.py` — PASS

---

## Review Style Fragment Follow-Up: Prompt Interpolation Coverage

**Problem**: The latest style-fragment refactor changed prompt assembly in `backend/agents/script_agent.py`, but the new tests only verified that fragment files existed. Reviewing the actual loader path exposed a real prompt bug: several Cat 1 fragments referenced `{entity_name}`, and `_load_step_instructions()` never replaced that token. That left raw template placeholders in live prompts.

**Solution**: Fixed prompt interpolation by adding `{entity_name}` to the loader replacements, then simplified the fragment-selection branch so the fragmentable step prefixes live in one module constant instead of a per-call local dict with an unused value map. Tightened the local test coverage to exercise `_load_step_instructions()` directly for Cat 1 and Cat 5 fragment paths and replaced one manual `try/except` assertion with `pytest.raises`.

**Edits**:
- `backend/agents/script_agent.py` — added `{entity_name}` replacement in `_load_step_instructions()` and simplified fragment-prefix handling with `_FRAGMENTABLE_STEP_PREFIXES`
- local `tests/test_entity_registry.py` — added direct loader assertions for Cat 1/Cat 5 fragment assembly and interpolation; simplified unknown-entity assertion with `pytest.raises`
- `HANDOFF.md` — added this review/update entry

**NOT Changed**:
- `backend/entity_registry.py` and the new fragment markdown files were reviewed in this pass and left unchanged
- `backend/skills/step_instructions/cat1_step2_rules.md` and `backend/skills/step_instructions/cat5_step4_synthesis.md` were left as-is after review
- `docs/weekly-report-2026-03-13.md` deletion already present in the worktree was not touched

**Verification**:
- `cd backend && uv run ruff check agents/script_agent.py ../tests/test_entity_registry.py` — PASS
- `cd backend && uv run ruff format --check agents/script_agent.py ../tests/test_entity_registry.py` — PASS
- `cd backend && uv run pytest ../tests/test_entity_registry.py -q` — PASS (`31 passed`)
- `cd backend && uv run pytest ../tests/test_api.py -q` — PASS (`24 passed`)

---

## Style-Specific Step Instruction Fragments

**Problem**: All entities within a category shared identical step instruction templates. Cat 5 entities both got the same "compare your finds" synthesis guidance, even though the design doc envisions creative storytelling for dandelion. Cat 1 entities with different game mechanics (voice_acting vs storytelling_chain) received the same generic demo and round instructions.

**Solution**: Implemented a fragment composition system that appends style-specific guidance to shared base templates. The loader in `_load_step_instructions()` looks up a fragment file using the entity's `game_mechanic` (Cat 1) or `synthesis_type` (Cat 5) and appends it after the base template. Fragment files use double-underscore naming: `cat1_step2_rules__voice_acting.md`. If no fragment exists, the base template is used alone (backward-compatible). Reassigned dandelion from `comparison_chart` to `naming_story` synthesis style.

**Edits**:
- `backend/agents/script_agent.py` (~line 135) — added fragment loading logic to `_load_step_instructions()`: determines style key from creative slots, builds fragment filename, appends if exists
- `backend/entity_registry.py` — changed `fluffy_expedition_dandelion` `synthesis_type` from `"comparison_chart"` to `"naming_story"`, updated `naming_prompt`
- `backend/skills/step_instructions/cat1_step2_rules.md` — removed "Game Mechanics Reference" section (now in fragments)
- `backend/skills/step_instructions/cat5_step4_synthesis.md` — removed multi-type reference section (now in fragments)
- `tests/test_entity_registry.py` — added `test_dandelion_synthesis_type_is_naming_story`, added `TestStyleFragments` class with 2 tests verifying fragment files exist for all registered entity styles
- 10 new fragment files in `backend/skills/step_instructions/`:
  - `cat1_step2_rules__voice_acting.md`, `cat1_step2_rules__storytelling_chain.md`, `cat1_step2_rules__riddle_game.md`
  - `cat1_step3_round__voice_acting.md`, `cat1_step3_round__storytelling_chain.md`, `cat1_step3_round__riddle_game.md`
  - `cat5_step3_collect__comparison_chart.md`, `cat5_step3_collect__naming_story.md`
  - `cat5_step4_synthesis__comparison_chart.md`, `cat5_step4_synthesis__naming_story.md`

**NOT Changed**:
- `backend/schemas/creative_slots.py` — `"naming_story"` and `"riddle_game"` already in the Literal types
- Steps 1 (Hook), 4/5 (Celebrate), 5/6 (Closing) — variables handle variation, no fragments needed
- Frontend code — no changes needed
- Other base template files (`cat5_step2_mission.md`, `cat1_step1_hook.md`, etc.) — unchanged

**Verification**:
- `cd backend && uv run ruff check . && uv run ruff format --check agents/script_agent.py` — PASS
- `cd backend && uv run pytest ../tests/test_entity_registry.py -v` — PASS (29 passed)
- `cd backend && uv run pytest ../tests/ -k "not e2e" -q` — PASS (178 passed)

