# Pilot Flow Robustness, Asset Regeneration, and Crown UI Goal

## Mode

Plan-backed.

Use this file as the Claude Code `/goal` (and Codex `/goal`) execution contract. It defines the outcome, constraints, checks, ordering, and stop condition for a fresh, context-light session.

## Objective

Harden the three pilot activities of the standalone text-game surface (`/?view=activities`) and modernize their visuals, without changing the live-LLM nature of the experience:

- **Frame-sync (F):** the on-screen asset always matches the current step and the spoken line.
- **Guardrails (A/B/C/D):** live-LLM dialogue stays on-intent, flow-correct, device-word-clean, and never ships a bad line on retry exhaustion.
- **Assets:** regenerate the 3 pilots' beat scenes + item sprites in the flat-Nordic style (human-gated).
- **Crown UI:** an Apple-Watch Digital-Crown vertical-list picker reused across all device-navigation surfaces.

Pilots: `activity_career_decision_role_play` (Cat1), `activity_guided_drawing` (Cat3), `activity_phoneme_treasure_hunt` (Cat5).

## Design Source

Authoritative implementation plan (task-by-task, with code):

```text
docs/plans/2026-05-29-pilot-flow-robustness-and-asset-regen-implementation.md
```

Design rationale and decisions:

```text
docs/plans/2026-05-29-pilot-flow-robustness-and-asset-regen.md
```

The plan is authoritative for design rationale, file ownership, exact code, and task order. This goal is authoritative for constraints, required checks, credential handling, and the completion gate. If the goal and the plan conflict, stop and document the conflict before changing behavior. If the plan and current code conflict, inspect the code and make the smallest change that satisfies this goal.

## Design Decisions

- Keep live LLM; harden guardrails (no full scripting).
- One backend turn-finalization stage (`backend/turn_handling/finalize.py`) owns both frame derivation and line validation, so dialogue and frame derive from one resolved state.
- Guardrail A is deterministic (contract/role/flow/completion); no per-turn LLM intent classifier.
- Assets are raster, generated via Codex built-in imagegen; the 3 pilots' current `.md` recipes are source-of-truth and must not be re-converted by the importer.
- Crown picker is layout A (vertical list), one reusable `CrownPicker.jsx` across the activity library, Cat3 Done/Help, and the Cat5 item picker.

## Hard Constraints

- Work only in `/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/.worktrees/feat/activity-text-game`.
- Keep the standalone activity game text-only: no STT, TTS, mic, camera, photo upload, or image-recognition controls.
- Do not run the autodesign importer over the 3 pilot `.md` files; do not hand-edit the pilot `.md` recipes in ways a re-convert would clobber.
- Do not touch the other 9 activities except where a shared test/contract requires it; they keep their single `recap` beat.
- `_required_beat_ids` in `tests/test_activity_text_game_asset_contract.py` is edited exactly once (Stream 1+2 Task 3, representative-gated). Stream 3 must not redefine it.
- **Stream 3 image art is human-gated:** generate candidates and request explicit human sign-off per pilot; never auto-approve generated art, and do not treat asset generation as autonomously complete.
- Do not edit, print, copy, or commit `.env`, `.elaborate-baton-*.json`, tokens, or provider secrets.
- No destructive git commands, broad formatting sweeps, dependency upgrades, or unrelated refactors. Do not revert user changes.
- Python: no `__future__`, imports at top, type hints, line length 120, no `noqa`/`type: ignore`. Commit at each task; never attribute Claude/AI in commits.

## Required Scope

- **Stream 1+2 (backend, Tasks 1-10):** `finalize.py` (step→beat table, `derive_frame`, validators); route all `TurnResponse` paths through it; explicit frontend step→beat table; manifest `celebrate`/`closing` beats for the 3 pilots; `_sync_round_from_step` round-clear; wire `finalize_turn` (with `script_agent`) into the live paths.
- **Stream 3 (assets, Tasks 1-4, human-gated art):** per pilot, regenerate beat scenes + item sprites via Codex; inspect/select; copy; `build_activity_screen_assets.py`; drop stale pilot `ITEM_CROPS`; asset-contract test green.
- **Stream 4 (crown, Tasks 1-7):** `CrownPicker.jsx` (+ CSS), momentum/detent/keyboard/reduced-motion, wired into all three surfaces.

## Execution Rules

- Read the source plan before editing; follow its TDD steps (failing test → minimal impl → pass → commit).
- Keep changes narrowly scoped; run the smallest relevant check after each coherent change.
- Stop on failing checks, diagnose root cause, and fix before broadening scope.
- After each stream, run `code-reviewer` and `code-simplifier` over that stream's diff before declaring it done (project rule).
- Surface every Required Check's command output in the conversation, and re-run the suite right before the completion gate so current evidence is in the transcript.
- Update `HANDOFF.md`, `goals/README.md`, and `docs/plans/README.md` with final status only after verification evidence is known.

## Mandatory Ordering

1. Confirm the source plan exists and read it.
2. Stream 1+2 first (frame-sync before validators; wire `finalize_turn` last so validators run on live paths).
3. Stream 4 next (frontend-isolated; may overlap Stream 3).
4. Stream 3 last: code/test/manifest scaffolding (beats, contract test, `ITEM_CROPS`, placeholder rasters) is autonomous; **image art generation pauses for human sign-off per pilot.**
5. Automated checks before any live smoke; live smoke before browser walkthrough.

## Delegated-Agent Rules

The project requires `code-reviewer` + `code-simplifier` sub-agents after each change. Delegation is otherwise narrow, disjoint-ownership only:

- code-quality / correctness review lane → `code-review-specialist` or `feature-dev:code-reviewer`.
- complexity reduction lane → `code-simplifier`.
- independent source/intent audit or broad search → `Explore` or `general-purpose`.

Delegated agents must not edit secrets, run destructive git, edit the same file concurrently, generate/approve assets, or decide final completion. The main session integrates edits, runs final checks, handles credentials and commits, and decides the gate.

## Live Provider Credential Rule

All testing and verification must hit the **live provider** (not mocked-only). The credential files live in the **main repo's `backend/`** (verified present there; the worktree has none of its own). Source them before running the backend, tests, or live smoke, without exposing values:

```bash
REPO_BACKEND="/Users/pharrelly/codebase/github/wonderlens-activity-fullstack-demo/backend"
set -a
source "$REPO_BACKEND/.env"
set +a
export GOOGLE_APPLICATION_CREDENTIALS="$REPO_BACKEND/.elaborate-baton-480304-r8-a8a39bcb34f1.json"
```

Do not echo, print, edit, copy, or commit any secret value. The autonomous completion gate includes the live smoke, so credentials must be sourced before the verification phase.

## Preconditions

- The worktree and both source docs (plan + spec) exist.
- Backend `uv` tooling, `frontend/package.json`, `scripts/build_activity_screen_assets.py`, and `scripts/run_activity_text_smoke.py` are available.
- Live provider credentials exist in the main repo `backend/` (`.env` + `.elaborate-baton-480304-r8-a8a39bcb34f1.json`) for live-provider testing.
- Codex CLI is available for Stream 3 art (reached via the `codex:codex-rescue` runtime); its outputs land in `~/.codex/generated_images/`.
- Reuse or intentionally restart any running servers; leave none unexpectedly running at completion.

## Success Criteria

### Frame-sync (Stream 1)
- `screen_frame.beat` equals the beat for the current (post-advance) step across a full session per pilot, including auto-advance boundaries; celebrate and closing render distinct beats.

### Guardrails (Stream 2)
- Off-intent/item-suggestion and premature-completion lines are caught and regenerated, then fall back to deterministic recipe text on divergence.
- An `action=stay` line never promises advancing; broadened completion regex catches creative variants.
- Device words / B-sound phrasing are sanitized as the single last step; `example_ai_line` is sanitized at load.
- Retry exhaustion returns the deterministic fallback (enriched with collected names), never the last bad line.

### Crown UI (Stream 4)
- One `CrownPicker` (vertical list, focused-centered, arc indicator) drives the activity library, Cat3 Done/Help, and Cat5 item picker; momentum/detent, keyboard (ArrowUp/Down + Enter), disabled-during-selection, and reduced-motion all work.

### Assets (Stream 3 — human-gated, outside the autonomous gate)
- The 3 pilots' beat scenes + item sprites are regenerated in the flat-Nordic style, approved per pilot by a human, and pass the asset-contract test; no letters/logos/borders.

## Required Checks

Run from the worktree root unless a command changes directory.

Backend (Streams 1+2):

```bash
uv run pytest backend/tests/test_finalize_frame.py backend/tests/test_finalize_frame_sync.py backend/tests/test_finalize_validators.py backend/tests/test_activity_text_game_turns.py backend/tests/test_activity_source_fidelity.py backend/tests/test_activity_text_game_cat3.py backend/tests/test_generation_text_mode.py backend/tests/test_generation_fallback.py -q
```

Asset contract + full backend suite:

```bash
cd backend && uv run pytest ../tests/test_activity_text_game_asset_contract.py -q && uv run pytest -q && cd ..
```

Backend lint:

```bash
cd backend && uv run ruff check turn_handling/ agents/script_agent.py && uv run ruff format --check turn_handling/ agents/script_agent.py && cd ..
```

Frontend (Stream 4 + assets):

```bash
cd frontend && npm run test && npm run lint && npm run build && cd ..
```

Repository:

```bash
git diff --check
```

Live verification (REQUIRED — source credentials per the Live Provider Credential Rule first, then run against the live provider and surface output; do not substitute mocks):

```bash
uv run python scripts/run_activity_text_smoke.py --timeout 120
```

Human-gated full acceptance (not part of the autonomous gate): per-pilot art sign-off in the browser; Cat1/Cat3/Cat5 browser walkthrough at `http://127.0.0.1:5173/?view=activities`.

## Final Completion Gate

Autonomous completion (transcript-provable) is reached when, with command output shown in the conversation:

- every Stream 1+2 and Stream 4 task checkbox is done;
- the backend Streams-1+2 suite, the asset-contract test, the full backend suite, and backend ruff all pass (the only allowed red is the pre-existing, out-of-scope `test_representative_activity_layout_contracts_match_touchless_goal` carousel-vs-picker case — call it out if seen);
- `npm run test`, `npm run lint`, and `npm run build` pass in `frontend/`;
- `git diff --check` is clean;
- the live smoke (`scripts/run_activity_text_smoke.py --timeout 120`) passes against the **live provider** with credentials sourced and output shown in the conversation;
- Stream 3's non-art scaffolding (manifest celebrate/closing beats, representative-gated `_required_beat_ids`, dropped pilot `ITEM_CROPS`, placeholder rasters) is in place and the asset-contract test is green.

Then **stop and hand off** the human-gated remainder: Stream 3 image-art generation + per-pilot sign-off, and the Cat1/Cat3/Cat5 browser walkthrough. Do not mark the goal `Completed` until that human acceptance also passes; record it as `Active` with the autonomous gate met until then.

## Goal Invocation

Run in Claude Code goal mode (requires v2.1.139+), or Codex `/goal`. The autonomous loop targets Streams 1+2 and 4 plus Stream 3 scaffolding; image art stays human-gated.

```text
/goal Implement goals/2026-05-29-pilot-flow-robustness-and-asset-regen-goal.md — read it and its Design Source plan fully and obey the Hard Constraints, Mandatory Ordering, and human-gated Stream 3 art rule. Done when all Stream 1+2 and Stream 4 tasks are complete and, with command output shown in the conversation: `uv run pytest backend/tests/test_finalize_frame.py backend/tests/test_finalize_frame_sync.py backend/tests/test_finalize_validators.py backend/tests/test_activity_text_game_turns.py backend/tests/test_activity_source_fidelity.py backend/tests/test_activity_text_game_cat3.py backend/tests/test_generation_text_mode.py backend/tests/test_generation_fallback.py -q` passes; `cd backend && uv run pytest ../tests/test_activity_text_game_asset_contract.py -q && uv run pytest -q && cd ..` passes (the carousel-vs-picker case is the only allowed pre-existing red); backend ruff is clean; `cd frontend && npm run test && npm run lint && npm run build` passes; and `git diff --check` is clean; and `uv run python scripts/run_activity_text_smoke.py --timeout 120` passes against the live provider (source the main-repo backend `.env` and `.elaborate-baton-480304-r8-a8a39bcb34f1.json` first) with output shown. For Stream 3, complete only the non-art scaffolding and STOP for human art sign-off — do not auto-approve generated images. Or stop after 60 turns and report the blocker.
```
