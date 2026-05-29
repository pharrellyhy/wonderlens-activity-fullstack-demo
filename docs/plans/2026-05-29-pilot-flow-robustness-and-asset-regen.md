# Pilot Flow Robustness + Asset Regeneration + Crown UI — Design Spec

Date: 2026-05-29
Branch: `feat/activity-text-game`
Status: design approved (brainstorming complete) — implementation plan to follow

## 1. Purpose

Harden the three pilot activities of the standalone text-game surface (`/?view=activities`), regenerate their on-screen art, and make device navigation feel like an Apple-Watch Digital Crown — without changing the live-LLM nature of the experience.

Pilots:
- **Cat1** `activity_career_decision_role_play` (firefighter decisions)
- **Cat3** `activity_guided_drawing` (guided build steps, Done/Help)
- **Cat5** `activity_phoneme_treasure_hunt` (B-starting word collection)

## 2. Decisions locked (during brainstorming)

| # | Decision |
|---|----------|
| D1 | **Keep live LLM**, harden guardrails (not full scripting). No fixed demo date; variety/personalization matter. |
| D2 | Target failure modes: **A** off-intent drift, **B** flow-control errors, **C** wording leaks, **F** asset↔step↔dialogue desync. |
| D3 | **Option 1 — consolidated finalization stage** owns both "is this line safe to speak" and "what frame matches it." |
| D4 | Assets: **raster via Codex built-in imagegen**, driven through the `codex:codex-rescue` runtime (proven non-interactive). Vector rejected (quality). |
| D5 | Asset scope: **pilot-complete** — regenerate the full beat-scene set + item sprites for all 3 pilots. |
| D6 | **P2 — the 3 pilots' current `.md` are source-of-truth.** Never run the lossy importer over them. (See §9.) |
| D7 | **A-i — deterministic contract/role/flow/completion validation**, themes best-effort. No per-turn LLM re-check. |
| D8 | Sequencing: **F-fix → guardrails → assets → crown UI.** |
| D9 | **Stream 4 — Digital Crown scroll picker, layout A (vertical list)**, one reusable component across all three device-navigation surfaces. |

## 3. Architecture: a single turn-finalization stage

New module `backend/turn_handling/finalize.py` with one function, `finalize_turn(...)`, invoked on **every** path that builds a `TurnResponse` — the directive path (`_resolve_turn_with_directive`) **and** the non-directive paths (start-hook generation, silence handling, invitation, synthesis, and fast-path early returns in `core.py`/`directive.py`). It returns the `(dialogue, screen_frame)` pair derived from the **same resolved state**, so they cannot desync. Any `TurnResponse`-producing site that bypasses `finalize_turn` would retain the old scattered behavior, so the implementation must route them all through it (verified by grepping for residual `_get_screen_frame` callers).

```
resolve_turn → [directive resolved: action + final step + dialogue]
                      │
                      ▼
   finalize_turn(state, directive, dialogue):
     (1) validate spoken line → corrective regen (failure-only) → deterministic fallback   [Stream 2]
     (2) derive frame from (action, final step) → attach                                    [Stream 1]
                      │
                      ▼
            TurnResponse  (safe line + matching frame, one unit)
```

Latency budget: validators are deterministic on the happy path (zero added LLM cost); at most **one** corrective regeneration on failure.

## 4. Stream 1 — Frame-sync fix (F)

Root cause (confirmed, high confidence; three converging causes):

1. **Timing inconsistency.** `_get_screen_frame(state)` is computed *before* `_advance_state()` in some paths (`core.py:307-308`, `345-346`) but the serialized `sessionState` reflects the *post*-advance step; the frontend derives the beat from `sessionState.current_step` (post-advance) while the backend `screen_frame` is pre-advance → permanent one-step lag.
2. **Stale `current_round`.** `_sync_round_from_step` (`helpers.py:93-102`) only updates `current_round` for `STEP_3_*_N`; on CELEBRATE/CLOSING it keeps the old round, so round-keyed frame lookups go stale.
3. **Lossy step→beat mapping + missing beats.** `beatIdFromSessionState()` (`activityAssets.js:92-93`) collapses both `CELEBRATE` and `CLOSING` → `'recap'`; the manifest has only one `recap` beat for Cat1/Cat3 (intro, rules, round_1-3, recap) and no distinct celebrate/closing beats for Cat5.

Fix (three parts):

- **1a. Directive-driven single derivation.** Replace the ~12 scattered `_get_screen_frame(state)` calls (`core.py:131/171/272/287/301/308/336/346`; `directive.py:1130/1171/1187/1226`) and the two ad-hoc pre-advance snapshots (`directive.py:1128-1142` celebrate, `1171-1187` closing) with **one** `derive_frame(state, action)` call inside `finalize_turn`, computed from the **resolved post-advance step** — the same `current_step` the frontend reads. Leverage the already-persisted `state.last_directive_action`.
- **1b. Explicit step→beat table.** Replace the lossy `includes()` mapping in `activityAssets.js` with an explicit step→beat lookup, defined once and used as the shared contract by both backend `derive_frame` and the frontend. No more two-steps-collapse-to-one-beat collisions.
- **1c. Add missing beats + sync round.** Add distinct `celebrate` and `closing` beats to the manifest for all 3 pilots (Cat1/Cat3: 6→8 beats; Cat5 gains celebrate/closing after synthesis). Fix `_sync_round_from_step` so `current_round` is not left stale on non-round steps (defense-in-depth). **These new beats are exactly the new art Stream 3 generates** — the seam between streams.

**Frame semantics:** the frame represents **the step whose line is being spoken now** (not a preview of the next step). Asserted in tests.

## 5. Stream 2 — Guardrail validators (inside `finalize_turn`)

Deterministic by default; at most one corrective regen on failure; deterministic fallback on exhaustion.

- **A (off-intent drift → contracts become blocking), A-i deterministic.** For the current beat, validate the line against the recipe's `SourceStepContract` data + role + structure: stays in-role, honors `do_not_suggest_items`, matches the beat's `acceptable_themes`/keywords (best-effort), no premature completion. On divergence → one regen seeded with the contract's *ideal* branch → still bad → deterministic recipe fallback. No per-turn LLM intent classifier.
- **B (flow-control sanity, deterministic).** Broaden the premature-completion regex to catch creative variants ("all 3 spotted!", "search is over"); enforce stay/advance consistency (an `action=stay` line must not say "next/let's move on"); correct celebrate→closing pacing (pairs with §4).
- **C (wording, deterministic — relocate + extend).** Move the device-word + phoneme-term regex (currently split across `script_agent.py:427-465` and `generation.py:419-424`) into `finalize_turn` as the single last word, **and** sanitize `example_ai_line` strings at load so the LLM never sees device words as "official examples."
- **D (exhaustion fallback — closes the hole).** After max retries, **always** return the deterministic `_source_fidelity_fallback_response` instead of the last (possibly bad) line — and enrich it with `collected_names`/characters where available (so it reads "Fluffy and Bouncy," not "our friends").

## 6. Stream 3 — Asset regeneration (Codex raster, pilot-complete)

Per pilot, full beat set (incl. new `celebrate`/`closing`) + item sprites:

1. Enumerate assets from the expanded manifest (beats + items).
2. Draft each prompt = subject (beat/recipe + manifest item id) + the style contract (`frontend/public/activity-assets/prompts/wonderlens-activity-style.md` + the autodesign `docs/activity_asset_generation_workflow.md` style section).
3. Drive Codex via `codex:codex-rescue` → candidate PNGs in `~/.codex/generated_images/` (1254², downscaled to 512 by the builder).
4. Inspect candidates (Read tool renders images) and select the best on-style one: square ≥512, no text/letters/logos/borders/vignette/black corners; centered subject + clean white padding for items; full-bleed for scenes with content in the lens-safe center.
5. Copy selected into `frontend/public/activity-assets/<id>/` (scenes) and `.../items/` (sprites).
6. Run `python3 scripts/build_activity_screen_assets.py` (downscale + manifest layout plans).
7. Validate: `tests/test_activity_text_game_asset_contract.py` (manifest↔recipe beats, file existence, 512², no black padding) — updated for the new celebrate/closing beats.
8. **Show the picked set per pilot in the visual companion for sign-off before building.**

Constraints:
- **Factual-sources policy honored:** pilot assets are generic objects/characters — not reference-bound real-world references — so generation is permitted.
- Preserve the naming/shape/safe-area contract (`canvas:480/safe:380/center:300`; item ids; shapes circle/rect3x4).

Rough volume: ~7–8 beats + ~3–6 items × 3 pilots ≈ **30–45 final assets** (more candidates generated), approved pilot-by-pilot.

## 7. Stream 4 — Digital Crown scroll picker (interaction polish)

Make device-driven navigation feel like an Apple-Watch Digital Crown via a single reusable component.

**Layout (chosen: A — vertical crown list):**
- Vertical stack inside the circular lens; focused item centered & enlarged (full opacity); neighbors scale down (~0.72 at ±1, ~0.5 at ±2) and fade, masked by the lens circle.
- Arc scroll indicator hugging the right inner edge tracks crown position; a selection pill/ring marks the focused row.

**Interaction model:**
- **Crown = the device's right-side scroll control:** up/down zones step focus by one detent; sustained input = momentum scroll with eased settle onto the nearest detent (one item per "click").
- **Detent feedback:** focus snaps to center with a subtle scale/opacity "tick."
- **Confirm = green start/select button** → selects the focused item.
- Text input disabled while a crown selection is active (existing touchless rule).
- **Accessibility:** keyboard (ArrowUp/ArrowDown + Enter) maps to crown step + confirm; ARIA listbox/option roles; respects `prefers-reduced-motion` (disable momentum/scale animation, keep instant focus).

**Surfaces (all three, one component):**
- **Cat5 item picker** — existing `confirmCat5Item` → `sendCollectionItem(photo_id)`.
- **Cat3 Done/Help** — 2-item; existing `confirmCat3Option` → `sendMessage('done'|'help')`.
- **Activity library** — selecting which activity to start.

**Component:** new `frontend/src/activityGame/CrownPicker.jsx` (+ CSS), consumed by `ActivityGameApp.jsx`/`ActivityLens.jsx` and `ActivityLibrary.jsx`; replaces the ad-hoc per-surface selection logic with one prop-driven `{items, index, onStep, onConfirm, disabled}` API.

**Isolation:** frontend-only (no backend change). Depends on Stream 1 only insofar as the Cat5 picker shows the correct beat → sequence after Stream 1; may overlap Stream 3.

**Out of scope:** real hardware crown integration (browser approximation only).

## 8. Testing

- **F (frame-sync):** new backend turn-by-turn test per pilot asserting `screen_frame.beat == expected_beat(step)` across a full session incl. auto-advance boundaries (hook→rules→rounds→[synthesis]→celebrate→closing); frontend test mirrors the step→beat table.
- **Guardrails:** unit tests per validator — completion-language variants, device-word/phoneme sanitation, contract divergence → regen → fallback, exhaustion → deterministic fallback (not last bad line) using character names. Extend `test_generation_text_mode` / `test_activity_source_fidelity` / `test_activity_text_game_cat3` / `test_activity_text_game_turns`.
- **Assets:** update `test_activity_text_game_asset_contract.py` for the new beats; run build + validators.
- **Crown UI (Stream 4):** `CrownPicker` unit tests — focus stepping, momentum settle to detent, clamp/wrap behavior, confirm fires the correct per-surface callback, disabled-during-selection, reduced-motion path, keyboard mapping, ARIA roles. Extend `tests/WonderLensDevice.test.jsx` and `tests/ActivityGameApp.test.jsx` for the three surfaces.
- **Live:** restart backend/frontend from this worktree; walk all 3 pilots end-to-end — frame matches line at every beat (F acceptance) + guardrail behaviors + full visuals + crown navigation feel.

## 9. Source-of-truth & provenance (P2)

The 3 pilot `.md` were **hand-authored in fullstack**: skeleton export (`ccf700a`) → hand-written `source_dialogue` contracts + original `acceptable_themes`/`source_intent_lock` (`0cd088b`) → firefighter/B-word refinement (`62b2870`). **No converter reproduces this format** — the `autodesign_importer.py` (`30c5a8a`) emits no `source_dialogue`; the non-lossy "parity converter" is planned-but-unbuilt in the autodesign repo, which itself treats these pilots as the quality-floor *target*.

Therefore:
- The pilots' current `.md` are **authoritative**. We never hand-edit them in ways a re-convert would clobber, and we never run the lossy importer over them.
- All hardening lives **code-side** (`finalize_turn`, load-time sanitation, step→beat table) and reads contract data at runtime — safe against any future re-conversion.
- Re-conversion (and the eventual non-lossy parity converter) applies to the **other 9 / new** activities — that is the autodesign parity project, out of scope here.

## 10. Sequencing & process

1. **Stream 1** (finalize stage + directive-driven frame + step→beat table + manifest celebrate/closing beats + round sync) → verify frames sync with placeholder art.
2. **Stream 2** (validators into the same stage) → verify safety behaviors.
3. **Stream 3** (asset regeneration) → verify final visuals.
4. **Stream 4** (crown picker; frontend-isolated, may overlap Stream 3) → verify navigation feel + accessibility.

Process: implementation plan via the writing-plans skill → `docs/plans/`. After each stream, run code-reviewer + code-simplifier before "done." Update `HANDOFF.md`. Python tooling via `uv run` (ruff check/format, mypy, pytest). Code style: no `__future__`, imports at top, no `noqa`/`type: ignore`, line length 120, Google docstrings. Commit at logical checkpoints (the no-auto-commit rule was lifted on 2026-05-29); **never attribute Claude as author/co-author** in commits.

## 11. Out of scope

- Merging the 8 deferred `main` commits (autodesign import feature) — integrate later.
- The non-lossy "runtime conversion parity" converter and pushing pilot refinements upstream (autodesign project).
- Re-converting / hardening the other 9 activities.
- Real hardware crown integration; vector/SVG assets; full deterministic scripting; STT/TTS/photo/real-device scope.
- Provider note (not a change): runtime uses DashScope/Qwen, while CLAUDE.md says Gemini — flagged, not addressed here.

## 12. Risks / open

- `acceptable_themes` are pilot-specific only because they're hand-authored; theme checks are best-effort and must not hard-fail valid-but-novel child input.
- Asset volume (30–45) means several Codex passes; per-pilot sign-off controls quality and cost.
- Frame-semantics choice (match-current-line) is asserted in tests; revisit only if a beat genuinely needs preview-ahead.
- Crown momentum/detent feel is tuning-sensitive; reduced-motion and keyboard parity are required, not optional.

## 13. Key files

Backend: `turn_handling/finalize.py` (new), `turn_handling/core.py`, `turn_handling/directive.py`, `turn_handling/rounds.py`, `turn_handling/helpers.py`, `turn_handling/generation.py`, `agents/script_agent.py`, `schemas/turn_directive.py`, `schemas/step_instruction.py`, `game_parser.py`, `games/activity_{career_decision_role_play,guided_drawing,phoneme_treasure_hunt}.md`.
Frontend: `src/activityGame/CrownPicker.jsx` (new), `src/activityGame/activityAssets.js`, `src/activityGame/ActivityLens.jsx`, `src/activityGame/useActivityTextSession.js`, `src/activityGame/ActivityGameApp.jsx`, `src/activityGame/ActivityLibrary.jsx`, `src/index.css`.
Assets: `public/activity-assets/activity-assets.manifest.json`, `public/activity-assets/<pilot>/(items/)`, `public/activity-assets/prompts/wonderlens-activity-style.md`, `scripts/build_activity_screen_assets.py`.
Tests: `tests/test_activity_text_game_asset_contract.py`, `tests/test_generation_text_mode.py`, `tests/test_activity_source_fidelity.py`, `tests/test_activity_text_game_cat3.py`, `tests/test_activity_text_game_turns.py`, `tests/WonderLensDevice.test.jsx`, `tests/ActivityGameApp.test.jsx`.
