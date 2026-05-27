# AGENTS.md

Project-specific instructions for agents working in `wonderlens-activity-fullstack-demo`.
These rules override global guidance when they are more specific.

## 1) Scope and Priority

- Scope: this file applies to the repository root and all subdirectories unless a deeper `AGENTS.md` exists.
- Priority: system/developer/user direct instructions first, then this file, then global defaults.
- Goal: make small, verifiable changes with minimal risk to demo flow, recipe correctness, and child-facing experience quality.

## 2) Project Snapshot

- Project: WonderLens Activity Demo, a split-view interactive browser demo with a multi-agent backend.
- Source of truth: `docs/wonderlens_activity_demo_build_spec.md` defines the intended architecture, flows, and guardrails for the current project.
- Product flow: user selects a photo and tier, backend generates an activity recipe, frontend renders conversation on the left and screen widgets on the right, and turns advance through recipe lookup plus TTS/ASR support.
- Backend direction: FastAPI service coordinating a Director Agent, Script Agent, Visual Agent, and Recipe Assembler with retry and fallback behavior.
- Frontend direction: React + Vite split-view UI with conversation, widget rendering, silence handling, retry UI, and session controls.
- AI/runtime direction: Gemini via Vertex AI for recipe generation and TTS, with deterministic fallback recipes for demo continuity.

Current repo state:
- `backend/` currently contains scenarios, prompts, tier rules, and fallback recipe assets that feed the demo build.
- `frontend/` exists but is not yet fully scaffolded in the current workspace snapshot.
- `docs/` contains the WonderLens build specification used to guide implementation.

Key files/locations (current and near-term):
- Build spec: `docs/wonderlens_activity_demo_build_spec.md`
- Prompt assets: `backend/prompts/script_system.md`
- Activity scenarios: `backend/scenarios/*.yaml`
- Tier rules: `backend/tier_rules.yaml`
- Fallback recipes: `backend/fallbacks/*.json`
- Planned backend surface from spec: `backend/server.py`, `backend/agents/`, `backend/schemas/`
- Planned frontend surface from spec: `frontend/src/`, `frontend/public/photos/`

## 3) Non-Negotiable Constraints

- Do not mention Claude (or any model) as code generator/co-author in commits, comments, or docs.
- Do not edit secrets or local credentials (`.env`, private keys, cloud credentials) unless explicitly asked.
- Do not perform opportunistic refactors, dependency upgrades, or broad formatting sweeps.
- Treat `docs/wonderlens_activity_demo_build_spec.md` as the primary project brief when repo code is incomplete or still being scaffolded.
- Preserve the multi-agent pipeline shape from the spec: Director plans, Script generates child-facing dialogue, Visual selects screen composition, Recipe Assembler merges and validates.
- Preserve the recipe-based interaction model: after session start, normal turn handling should use pre-generated recipe branches rather than re-calling the LLM per turn unless the user explicitly changes the architecture.
- Keep retry and fallback behavior deterministic and demo-safe; fallback recipes must remain available for supported activities.
- Preserve tier-specific behavior, especially round counts, tone/verbosity constraints, silence timeouts, and graceful exit handling after consecutive silence.
- Prefer adding or updating child-facing copy in prompt/scenario/fallback assets rather than scattering hardcoded strings across the codebase.
- Never revert user changes you did not make.

## 4) Python Code Style

- Target Python 3.12+ only. Do not add compatibility shims for older versions.
- Do not use `__future__` imports in this repo. In particular, skip `from __future__ import annotations`.
- Add type hints to all functions and methods.
- Use PascalCase for classes, snake_case for functions and variables, and UPPERCASE_WITH_UNDERSCORES for constants.
- Keep Python lines at or under 120 characters.
- Write Google-style docstrings for public APIs.
- Prefer dataclasses or Pydantic models for structured data instead of ad hoc dictionaries where shape matters.
- Catch specific exception types. Do not use bare `except:`.
- Keep all imports at the top of the module and order them per PEP 8: standard library, third-party, then local imports. Do not import inside functions, methods, or conditional blocks.

## 5) How to Work

1. Read relevant code paths and the build spec first; state assumptions if behavior is unclear.
2. Make the smallest change that solves the request.
3. Validate immediately with the narrowest useful check.
4. Stop on failing checks, summarize root cause, then fix incrementally.
5. Show concise diffs and list exactly what was verified.
6. Use a git worktree for code changes by default, and switch into that worktree before editing files or running implementation commands. The exception is doc-only or config-only edits, which may be made in the current checkout when appropriate.
7. When creating a git worktree, place it under `.worktrees/` at the project root using the convention `.worktrees/{feat,docs,fix,refactor,style,test,chore}/<worktree-name>`.
8. When working in plan mode or discussing design / implementation plans, write the plan to `docs/plans/` before making code changes. Use the project plan naming convention and make the plan detailed enough for a fresh session to execute.
9. Auto-commit after file changes:
   - After completing a task that edits, creates, deletes, or moves files, run the narrowest relevant validation first.
   - If validation passes, stage and commit the intended task changes before declaring completion.
   - Include untracked files that were created for the task.
   - Do not include unrelated user edits or unrelated generated files in the commit unless the user explicitly asks to commit all changes.
   - Do not commit when validation fails, when the user explicitly asks not to commit, or when a required decision is blocked.
   - Do not push unless the user explicitly asks to push.
   - Use the conventional commit rules in section 6.

## 6) Commit and Pull Request Messages

Use conventional commit format: `type(scope): description`.

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.

```text
feat(agents): add director agent
fix(frontend): resolve silence timer race condition
refactor(assembler): simplify recipe validation
```

Keep the first line under 50 characters. Use present tense.

Use the same conventional format for pull request titles. Do not prefix PR
titles with agent markers such as `[codex]`; the title should describe the
full branch diff, for example `feat(graph): rewrite knowledge graph viz with focus+context`.

PR descriptions should be detailed enough to stand alone for reviewers. Use
real Markdown sections and include, as applicable:

- `## Summary` with concise bullets covering what changed, why it changed, and
  operator/developer impact.
- `## What's in the branch` when the branch has multiple commits, phases, or
  implementation arcs.
- `## Files` summarizing important new, modified, and removed paths.
- `## Test plan` with exact commands and manual checks, using checkboxes when
  the checks are reviewer-facing.
- `## Out of scope / deferred` for known non-goals, tradeoffs, or follow-ups.

## 7) Canonical Commands

Run from repo root unless noted. Verify the referenced manifest or entrypoint exists before running setup or app commands.

```bash
# Inspect repo state
rg --files

# Backend setup/run once backend package files exist
cd backend
uv sync
uv run uvicorn server:app --reload --port 8000

# Frontend setup/run once package.json exists
cd frontend
npm install
npm run dev
```

Validation policy:
- Markdown/docs-only changes: verify with targeted file review and `git diff -- AGENTS.md` (or the changed docs).
- Changed Python files: run the narrowest relevant check available in `backend/` once the backend tooling exists; prefer targeted tests or module-level lint/type checks over broad suite runs.
- Changed frontend files: run the narrowest relevant check available in `frontend/` once the frontend tooling exists; prefer targeted lint/build checks over whole-project runs.
- Flow/contract changes: verify the smallest end-to-end path affected, such as recipe generation, turn progression, fallback loading, or a focused UI path.
- If required tooling is not scaffolded yet, document that clearly and perform manual verification against the build spec and touched files.
- Stop on first failure; summarize root cause before broadening scope.

## 8) Change-Specific Guardrails

- Backend pipeline changes:
  - Keep agent boundaries clear and consistent with the build spec.
  - Preserve schema validation between planning, script generation, visual composition, and final recipe assembly.
  - Keep retry and fallback logic explicit and testable.
- Prompt/scenario/fallback changes:
  - Keep tier rules and scenario intent aligned.
  - Ensure fallback recipes remain compatible with the same recipe schema expected by runtime code.
  - Prefer deterministic assets for demo-critical paths.
- Frontend interaction changes:
  - Preserve the split-view layout concept: conversation panel on the left, device screen on the right.
  - Keep silence timer behavior tied to tier rules and post-TTS timing.
  - Maintain clear states for normal, retrying, fallback, completed, and exited sessions.
- Audio and speech changes:
  - Treat browser speech features and Gemini TTS as runtime-dependent integrations with explicit fallback behavior.
  - Avoid blocking the core demo flow on optional speech features when a text-path fallback exists.
- Config/environment changes:
  - Keep Vertex AI related configuration consistent with documented environment variables.
  - Do not hardcode credentials or machine-specific paths into code or docs.

## 9) Documentation and Session State

Update docs when behavior, operator workflow, or implementation status changes:

- `README.md`: project overview, run instructions, and current architecture once the file exists or is created.
- `docs/wonderlens_activity_demo_build_spec.md`: only update when the project brief itself changes.
- `HANDOFF.md`: add/update a session entry when work meaningfully changes project state or execution status.

`HANDOFF.md` entry format (when the file exists or is created):
- Include: Problem, Solution, Edits, NOT Changed, Verification.
- New entries go at the top (below the header) separated by `---`.
- Keep only the last 10 entries.
- Maintain the `Last updated: YYYY-MM-DD` header date.

Keep docs concise and factual; avoid aspirational text not reflected in code.

## 10) External Docs and Uncertainty

- Use Context7 for library/framework API uncertainty before coding.
- Prefer official docs and repo source over memory when APIs are version-sensitive.
- When WonderLens project behavior is unclear, check the build spec before inferring architecture from partial scaffold files.
- If API uncertainty remains, build a minimal reproducible check locally and report the result.

## 11) Completion Checklist

Before declaring completion:

1. Confirm only intended files changed.
2. Run the smallest relevant verification available for the touched files and capture outcomes.
3. Confirm the change still matches the WonderLens build spec or explicitly note any deliberate divergence.
4. Summarize:
   - files changed
   - checks run (with pass/fail)
   - remaining risks or follow-ups
