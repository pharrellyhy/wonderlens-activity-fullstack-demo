# Plan: Promote 9 non-pilot activities to pilot parity

Date: 2026-05-30
Branch/worktree: `feat/activity-text-game` (`.worktrees/feat/activity-text-game`)

## Goal (from user)
For the 9 non-pilot activities, replicate the 3-pilot treatment:
1. Generate all art assets (flat-Nordic beat scenes + item sprites + icon).
2. Improve the activity `.md` files + dialogue quality, faithful to the autodesign source packages, using the live API for validation.
3. On rate limits: wait a few minutes and retry — do NOT stop.
4. Replace the activity profile/icon images.
5. Use TDD, subagents, dynamic workflow.
Self-confirm visual quality (no user sign-off required this round, per user).

## The 3 pilots (reference / done)
- `activity_career_decision_role_play` (category_1, decide)  ← cat1 structural exemplar for the 9
- `activity_guided_drawing` (category_3, build)
- `activity_phoneme_treasure_hunt` (category_5, collect)

## The 9 non-pilots (all category_1)
animal_sound_imitation (motion_voice), constellation_star_count (enumerate),
emotion_reader (care), partial_reveal_guess (deduce), recognition_pop_challenge (compare),
story_challenge_unlock (imagine), travel_planner (predict), vegetable_sort (sort),
word_echo_practice (remember).

## Key files / pipeline
- Activity defs (the "md files"): `backend/games/activity_<id>.md` (YAML front-matter + `step_instructions` + `source_dialogue`).
- Autodesign source packages (canonical content; fidelity anchor):
  `/Users/pharrelly/codebase/github/wonderlens-activity-autodesign/runs/20260521_163621_workbook_review_packet_full/activity_packages/<source_export_id>/{prod.md,spec.md,tag_block.yaml,dashboard.template.yaml,recap.template.yaml}`
  (source_export_id e.g. `concept_animal_sound_motion_voice`).
- Assets: `frontend/public/activity-assets/<activity_id>/{intro,rules,round_1..3,celebrate,closing,recap,[synthesis],icon}.png` + `items/*.png`.
- Manifest: `frontend/public/activity-assets/activity-assets.manifest.json`.
- Manifest/crop builder (already has ITEM_CROPS + layout specs for ALL 9): `scripts/build_activity_screen_assets.py`.
- Style spec (flat-Nordic): `frontend/public/activity-assets/prompts/wonderlens-activity-style.md` + `style-reference-flat-nordic.png`.
- Image gen for pilots: **Codex built-in imagegen** (`codex exec --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox -i <ref> < promptfile` → outputs in `~/.codex/generated_images/<uuid>/`). NOTE backend/image_gen.py is the Gemini *watercolor* runtime path — NOT the pilot flat-Nordic art path.

## Contracts / TDD targets
- `tests/test_activity_text_game_asset_contract.py`:
  - `_required_beat_ids`: representative (pilots) → `intro,rules,round_1..N,(synthesis if cat5),celebrate,closing` WITH `layout` metadata; non-representative cat1 → `intro,rules,round_1..N,recap` and MUST NOT have `layout`.
  - `REPRESENTATIVE_ACTIVITY_IDS` set (line ~13) gates the above. Promoting a 9 → add it here.
  - item sprites must be 512x512, not black-padded.
- `backend/tests/test_activity_source_fidelity.py`:
  - `SOURCE_FIDELITY_CONTRACTS` required/forbidden terms per activity (already passing for the 9 — preserve them).
  - `test_representative_child_facing_dialogue_avoids_device_bound_words` runs for REPRESENTATIVE ids only → promoted activities' `source_contract` child-facing text must avoid: card/cards/token/tokens/tap/touch/point/click.
  - `REPRESENTATIVE_ACTIVITY_IDS` (line ~22) — also update when promoting.
- `backend/tests/test_activity_text_game_definitions.py`: all 12 load, recipes have round_count>=3.
- Frontend `frontend/tests/activityAssets.test.js`: manifest structure, beats exist, style ref doc.
- Live smoke: `scripts/run_activity_text_smoke.py` / `tests/test_activity_text_smoke.py` (12-activity live flow). Use repo `.env` (Vertex/Gemini + dashscope). Test against LIVE provider.

## Execution phases (commit per phase / per activity)
### Phase B-content (workflow, parallel, testable; no imagegen)
For each of the 9: read its source package prod.md/spec.md + `activity_career_decision_role_play.md` as the cat1 structural exemplar + its fidelity required-terms. Produce/expand `source_dialogue.source_contract` for every step (hook, transition, round_1..N, celebrate, closing) with `runtime_instruction`, `example_ai_line`, `child_responses{ideal,unexpected,no_response}`, `ai_followups{...}`, `screen`. Constraints: faithful to source pkg; keep all fidelity required terms; NO device-bound words in child-facing text; T1 ≤3 sentences; invitational tone. Validate: backend definitions + fidelity + parser tests. Commit.

### Phase B-assets (per activity, serial Codex imagegen)
Generate flat-Nordic beat scenes (intro, rules, round_1..3, celebrate, closing; 512x512) per style spec, using style-reference-flat-nordic.png as `-i` ref. Capture each output dir via `comm -13 <(before) <(after)` to avoid the newest-dir race. Copy into `frontend/public/activity-assets/<id>/`. Then run `scripts/build_activity_screen_assets.py` to crop items + build manifest layouts. Verify asset-contract + item-size tests.

### Phase B-promote
Add the 9 to `REPRESENTATIVE_ACTIVITY_IDS` in BOTH test files; ensure manifest has celebrate/closing + layout for them. Run full backend + frontend + asset-contract + smoke.

### Phase B-icons
Replace each `icon.png` with on-style art (or derive from intro). Verify.

### Final
Update HANDOFF.md + goal docs; run full suite + live smoke; self-confirm visuals via Playwright; commit. Art is human-gated for final sign-off but user authorized autonomous self-confirm this round.

## PROGRESS (2026-05-30)
- DONE + committed `7a600f7`: layout fix (bottom-pill crown + device fit + keyboard/chevron).
- DONE + committed `45f4e0a`: device-word scrub for 9 md + fidelity REPRESENTATIVE promotion + this plan.
- Asset pipeline proven: `scripts/gen_beat.sh` (race-safe Codex imagegen → 512² PNG). animal_sound: all 7 beats generated + on-style (verified). Other 8: beats generating via `/tmp/wl_prompts/gen_all8.sh` (bg task; serial; rate-limit retry). Scene descriptions in `/tmp/wl_prompts/scenes.json`, prompts composed by `/tmp/wl_prompts/compose.py`.
- `scripts/promote_activity_manifest.py <id> [rounds]`: rewrites an activity's manifest entry to representative `single` scene layouts (intro,rules,round_1..N,celebrate,closing). animal_sound already promoted in working tree.
- Decision: the 9 use `single`-mode scene layouts (like career pilot), NOT the build-script's aspirational carousel+crop design (crops don't match freely-generated art). Note divergence from build_activity_screen_assets.py.
- FIXED pre-existing failure: phoneme synthesis manifest `picker`→`carousel` (matches build-script source line 238 + the touchless-goal test).
- REMAINING: (1) finish 8-activity beat gen + verify contact sheets, regen failures; (2) run promote_activity_manifest.py for all 9; (3) add 9 to REPRESENTATIVE_ACTIVITY_IDS in tests/test_activity_text_game_asset_contract.py; (4) replace 9 icons (dedicated single-subject art or from a beat); (5) run asset-contract + frontend activityAssets + definitions/fidelity; (6) live smoke; (7) commit (art per-activity or one asset commit) + HANDOFF.

## Gotchas
- Parallel Codex imagegen races on `~/.codex/generated_images` newest-dir → SERIALIZE or capture-by-diff.
- Don't promote (contract change) until BOTH content + celebrate/closing art + layouts exist for that activity, or asset-contract test breaks.
- Keep `backend/image_gen.py` (Gemini watercolor) out of the pilot art path.
- Rate limits: wait 2-5 min, retry; never abort the run.
