# CLAUDE.md

This file provides guidance to Claude Code when working with the WonderLens Activity Demo codebase.

## Behavioral Rules

- **DO NOT** mention Claude as code generator or code co-author in commits, comments, or docs
- **Plan before you code** — before starting any implementation work, write a design plan or implementation plan in `docs/plans/` first. No code changes until a plan document exists and covers the approach
- **Do not auto-commit or push** — never automatically commit or push after finishing a feature or task; only commit/push when explicitly asked

## Project Overview

WonderLens Activity Demo is a split-view interactive browser demo with a multi-agent backend that validates the WonderLens agent architecture spec. Users select a photo, then a multi-agent pipeline (Director, Script, Visual, Recipe Assembler) generates a structured JSON recipe. The frontend renders a conversation panel (left) and device screen panel (right) with TTS, ASR, and silence timeout handling.

**Two demo activities:**
- **Category 1** (In-Device Verbal): mood_changer_dog, dream_whisperer_cat, or time_machine_dinosaur
- **Category 5** (Out-of-Device Collection): polka_dot_patrol or fluffy_expedition_dandelion

**Tech stack:** Python 3.12+, FastAPI, Pydantic v2, Gemini 2.0 Flash (Vertex AI), React (JSX), Tailwind CSS, Vite

## Quick Start

```bash
# Terminal 1: Backend
cd backend
cp .env.example .env   # Fill in Vertex AI credentials
uv sync
uv run uvicorn server:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm install
npm run dev   # Vite on port 5173

# Open http://localhost:5173

# Code quality
ruff check backend/             # lint
ruff format backend/            # format
mypy backend/                   # type check
```

Pre-commit hooks run `ruff` and `isort` automatically.

## Architecture

Multi-agent pipeline: Director Agent → Script Agent + Visual Agent → Recipe Assembler → Frontend Renderer.

### Director Agent (`backend/agents/director.py`)
Plans the composition — creative direction, round count, screen strategy, emotional arc. LLM-based (Gemini 2.0 Flash, JSON mode, ~150ms). Does NOT generate child-facing content.

### Script Agent (`backend/agents/script_agent.py`)
Generates all voice/text content — hook, transition, per-round dialogue with branching (correct/incorrect/silence paths), closing speech. LLM-based (Gemini 2.0 Flash, JSON mode, ~400ms).

### Visual Agent (`backend/agents/visual_agent.py`)
Selects screen widgets, assigns assets, sequences frames. Rule-based (no LLM, ~10ms).

### Recipe Assembler (`backend/agents/recipe_assembler.py`)
Merges Script + Visual outputs into a single JSON recipe. Validates schema, hook rule, tier constraints, round count. Retry logic: 3 attempts → fallback recipe.

### Frontend
React split-view: ConversationPanel (left, ~55%) + DeviceScreen (right, ~45%). Pre-generated recipe means after initial /api/start (~580ms), every subsequent turn is near-instant (~5ms recipe lookup).

## Key File Locations

| Purpose | Location |
|---------|----------|
| FastAPI server + endpoints | `backend/server.py` |
| Director Agent | `backend/agents/director.py` |
| Script Agent | `backend/agents/script_agent.py` |
| Visual Agent | `backend/agents/visual_agent.py` |
| Recipe Assembler | `backend/agents/recipe_assembler.py` |
| Pydantic schemas | `backend/schemas/` |
| Agent system prompts | `backend/prompts/` |
| Fallback recipes | `backend/fallbacks/` |
| Activity scenarios (YAML) | `backend/scenarios/` |
| Tier rules | `backend/tier_rules.yaml` |
| Main React app | `frontend/src/App.jsx` |
| React components | `frontend/src/components/` |
| Widget components | `frontend/src/widgets/` |
| React hooks | `frontend/src/hooks/` |
| API client | `frontend/src/utils/api.js` |
| Demo photos | `frontend/public/photos/` |
| Design docs | `docs/plans/` |
| Build spec | `docs/wonderlens_activity_demo_build_spec.md` |

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/start` | Start new session — runs full agent pipeline, returns recipe + first turn |
| `POST /api/turn` | Process one user turn — recipe lookup, returns matched dialogue + screen frame |
| `POST /api/tts` | Text-to-speech — Gemini TTS via Vertex AI, fallback: browser SpeechSynthesis |

## Code Style

- **No `__future__` imports** — this project targets Python 3.12+ exclusively, so `from __future__ import annotations` and other `__future__` imports are unnecessary and should not be used
- **Python 3.12+** compatible
- **Type hints** required on all functions and methods
- **Classes:** PascalCase (e.g., `RecipeAssembler`)
- **Functions/Variables:** snake_case (e.g., `generate_recipe`)
- **Constants:** UPPERCASE_WITH_UNDERSCORES
- **Line length:** 120 characters
- **Docstrings:** Google-style for public APIs
- Use dataclasses/Pydantic for structured data
- Use specific exception types, not bare `except:`
- **All imports at the top of the file** — never import packages inside functions, methods, or conditional blocks; all `import` and `from ... import` statements must appear at the top of the module following PEP 8 import ordering (stdlib → third-party → local)

## Commit Messages

Use conventional commit format: `type(scope): description`

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

```
feat(agents): add director agent
fix(frontend): resolve silence timer race condition
refactor(assembler): simplify recipe validation
```

Keep first line under 50 characters. Use present tense.

## Session Handoff

After completing changes, update `HANDOFF.md` with a detailed entry covering:
- **Problem**: what issue or need prompted the change
- **Solution**: what was done and why
- **Edits**: files modified with key edit descriptions (line references, code context)
- **NOT Changed**: important things deliberately left untouched
- **Verification**: commands to validate the changes

Formatting rules:
- Each entry gets an `---` horizontal rule separator
- New entries go at the top (below the header)
- Keep only the **last 10 entries**; delete older entries from the bottom when adding new ones
- Maintain the `Last updated: YYYY-MM-DD` date in the header

## Auto-Compact Instructions

When the conversation context is automatically compacted, the summary **must** preserve the following in order of priority:

1. **Current task list** — every task's ID, status (pending/in-progress/completed), and any blocking dependencies
2. **Active plan** — which plan file in `docs/plans/` is being followed and which step is currently in progress
3. **Uncommitted work** — files that have been modified but not yet committed, and the intent behind each change
4. **Key decisions made** — any design choices, trade-offs, or user preferences established during the session
5. **Blockers and open questions** — anything unresolved that needs attention before proceeding

After compaction, immediately run `TaskList` to verify task state, and re-read the active plan in `docs/plans/` before resuming work. Do not re-do completed tasks or re-explore code that was already understood.

## MCP Guidelines

Always use context7 when you need code generation, setup or configuration steps, or library/API documentation. Automatically use the Context7 MCP tools to resolve library id and get library docs without being explicitly asked.

## Important Constraints

- Gemini 2.0 Flash via Vertex AI is the LLM — always use JSON mode with Pydantic schema enforcement
- Agent pipeline: Director → Script + Visual (can run in parallel) → Recipe Assembler
- Retry logic: 3 attempts → fallback recipe from `backend/fallbacks/`
- Tier rules loaded from `backend/tier_rules.yaml` — 3 tiers: T0 (2-4), T1 (4-6), T2 (6-8)
- Frontend uses pre-generated recipe for turns (no per-turn LLM calls after /api/start)
- Consecutive silence count ≥ 2 → graceful exit
- Never commit `.env` files or private keys
- Tests use `pytest` with `pytest-mock`
