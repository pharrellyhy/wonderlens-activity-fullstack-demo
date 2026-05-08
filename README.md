# WonderLens Activity Demo

A split-view interactive browser demo with a multi-agent backend that validates the WonderLens agent architecture spec. Users select a photo of a toy or nature object, then a multi-agent pipeline generates a structured JSON recipe that drives a guided, voice-enabled activity for young children (ages 2–8).

## Architecture

```
                          ┌─────────────────┐
  Photo Upload ──────────▶│  Director Agent  │  (LLM — creative plan)
                          └────────┬────────┘
                                   │
                      ┌────────────┴────────────┐
                      ▼                          ▼
              ┌──────────────┐          ┌──────────────┐
              │ Script Agent │          │ Visual Agent  │
              │   (LLM)      │          │  (rules)      │
              └──────┬───────┘          └──────┬───────┘
                     │                         │
                     └────────────┬────────────┘
                                  ▼
                      ┌───────────────────┐
                      │ Recipe Assembler   │  (merge + validate)
                      └─────────┬─────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │     Frontend Split-View       │
                │  Conversation │ Device Screen │
                │    (~55%)     │   (~45%)      │
                └───────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 18+
- Google Cloud credentials with Vertex AI access

### Backend

```bash
cd backend
cp .env.example .env   # Fill in your Vertex AI credentials
uv sync
uv run uvicorn server:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # Vite dev server on port 5173
```

Open [http://localhost:5173](http://localhost:5173). Vite proxies `/api` requests to the backend on port 8000.

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON |
| `GOOGLE_CLOUD_PROJECT` | GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | GCP region (e.g. `us-central1`) |
| `DASHSCOPE_API_KEY` | DashScope API key for Qwen-compatible LLM calls |
| `DASHSCOPE_BASE_URL` | DashScope OpenAI-compatible endpoint |
| `DASHSCOPE_MODEL` | Main DashScope model override |
| `DASHSCOPE_CLASSIFIER_MODEL` | Lightweight DashScope classifier model override |
| `LOG_LEVEL` | Logging level (default: `INFO`) |

## Project Structure

```
├── backend/
│   ├── agents/              # Multi-agent pipeline
│   │   ├── director.py       # Creative plan (LLM)
│   │   ├── planner.py        # Round/step planning
│   │   ├── script_agent.py   # Per-turn dialogue generation (LLM)
│   │   ├── visual_agent.py   # Screen widget + frame sequencing (rules)
│   │   ├── recipe_assembler.py # Merge + validate recipe
│   │   ├── pipeline.py       # Pipeline orchestration
│   │   └── turn_director.py  # Per-turn routing
│   ├── turn_handling/       # Step transition logic (decomposed package)
│   │   ├── core.py           # Entry point + dispatch
│   │   ├── directive.py      # Directive interpretation
│   │   ├── rounds.py         # Round progression
│   │   ├── collection.py     # Cat5 2-phase collection loop
│   │   ├── invitation.py     # Invitation step handling
│   │   ├── synthesis.py      # Cat5 synthesis step
│   │   ├── generation.py     # Content generation helpers
│   │   ├── helpers.py        # Shared utilities
│   │   ├── debug.py          # Debug/trace helpers
│   │   └── types.py          # Shared types
│   ├── games/               # Game definitions (*.md with YAML frontmatter)
│   │   ├── cat1/             # Cat1 design reference docs (not loaded at runtime)
│   │   └── cat5/             # Cat5 design reference docs (not loaded at runtime)
│   ├── prompts/             # Agent system prompts
│   ├── scenarios/           # Activity YAML definitions
│   ├── schemas/             # Pydantic models
│   ├── skills/              # Step instruction templates
│   ├── synthesis_formats/   # Cat5 synthesis format templates
│   ├── recipes/             # Cached/authored recipes
│   ├── tools/               # Agent tool definitions
│   ├── server.py            # FastAPI app + endpoints
│   ├── entity_registry.py   # Single source of truth for all entity config
│   ├── recipe_loader.py     # Recipe loading + session state builder
│   ├── state_machine.py     # Step progression + screen frame selection
│   ├── game_loader.py       # Game *.md loader
│   ├── game_parser.py       # YAML frontmatter parser
│   ├── scenarios.py         # Scenario registry
│   ├── config.py            # Runtime config loader
│   ├── db.py                # Session persistence
│   ├── image_gen.py         # Scene image generation (Imagen)
│   ├── character_sounds.py  # Character voice/sound mapping
│   ├── vision.py            # Photo analysis via Gemini
│   ├── stt.py               # Speech-to-text (Vertex AI)
│   └── tts.py               # Text-to-speech (Vertex AI)
├── frontend/
│   └── src/
│       ├── App.jsx         # Main React app
│       ├── components/     # UI components
│       ├── widgets/        # Device screen widgets
│       ├── hooks/          # React hooks
│       └── utils/api.js    # API client
├── scripts/                # Game conversion, icon generation, E2E testing
├── tests/                  # pytest test suite
└── docs/plans/             # Design and implementation plans
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/start` | POST | Start session — runs agent pipeline, returns recipe + first turn |
| `/api/start-deep-link` | POST | Start session from an upstream app deep link |
| `/api/turn` | POST | Process user turn — returns dialogue + screen frame |
| `/api/turn-speak` | POST | Combined turn + TTS — streams JSON header + PCM audio |
| `/api/tts` | POST | Text-to-speech via Vertex AI (fallback: browser SpeechSynthesis) |
| `/api/stt` | POST | Speech-to-text via Vertex AI (fallback: browser Web Speech API) |
| `/api/entities` | GET | List demo entities grouped by category (for frontend) |
| `/api/health` | GET | Health check |

## Agent Pipeline

| Agent | Type | Latency | Role |
|-------|------|---------|------|
| **Director** | LLM (Gemini 2.0 Flash) | ~150ms | Plans creative direction, round count, screen strategy, emotional arc |
| **Script** | LLM (Gemini 2.0 Flash) | ~400ms | Generates contextual, invitational dialogue guided by instruction recipes |
| **Visual** | Rule-based | ~10ms | Selects screen widgets, assigns assets, sequences frames |
| **Assembler** | Merge + validate | — | Combines Script + Visual into a validated JSON recipe |

Demo entities use pre-authored instruction recipes — the Script Agent generates contextual responses per turn guided by step instructions with goals and constraints. Custom photo uploads run the full pipeline. Entity configuration is centralized in `entity_registry.py` with startup validation.

## Demo Activities

18 loadable game definitions across two categories:

### Category 1 — In-Device Verbal (9 games)

The child photographs an object, then plays a voice-based game (voice acting, storytelling, prediction) without leaving the device. 2–4 dialogue rounds with escalating complexity.

| Activity | Entity | Tier | Game Mechanic |
|----------|--------|------|---------------|
| Mood Changer | Dog | T0 | voice_acting |
| Dream Whisperer | Cat | T0 | storytelling_chain |
| Dino Time Machine | Dinosaur | T0 | voice_acting |
| + 6 more | Various | T0–T1 | Various |

### Category 5 — Out-of-Device Collection (9 games)

The child photographs an object, then goes on a real-world scavenger hunt. Each collection round uses a **2-phase loop**:

1. **Phase A (photo):** child picks a photo → AI validates → asks a detail-harvesting question
2. **Phase B (detail):** child responds verbally → AI processes the detail (names a character or records an observation) → advance to next round

After all items are collected, a synthesis step uses the accumulated names/observations for creative activities (storytelling, comparison sorting).

| Activity | Entity | Tier | Synthesis Type |
|----------|--------|------|---------------|
| Polka-Dot Patrol | Ladybug | T1 | comparison_chart |
| Fluffy Expedition | Dandelion | T0 | naming_story |
| Brave Things Hunt | Lion | T0 | comparison_chart |
| Shimmer Spotter Safari | Goldfish | T1 | comparison_chart |
| Sound Detective Agency | Piano | T1 | sorting_game |
| + 4 more | Various | T0–T2 | Various |

**Tiers:** T0 (ages 2–4), T1 (ages 4–6), T2 (ages 6–8)

## Adding New Games

### Game File Format

Each game is a Markdown file in `backend/games/` with YAML frontmatter defining the activity type, creative slots, collection catalog, step instructions, and screen frames. Only top-level `*.md` files with `---` frontmatter are loaded at startup.

### Converting Design Docs

Design documents (`*_prod.md`) in `cat1/` and `cat5/` subdirectories can be converted into loadable game definitions:

**Option 1 — Quick scaffold (no LLM):**

```bash
python scripts/generate_game_frontmatter.py backend/games/cat5/feather_cat5_prod.md \
  --output backend/games/feather_flight_expedition.md
```

Generates a YAML skeleton with TODO markers for manual completion.

**Option 2 — LLM-assisted conversion (recommended):**

```bash
# Single game
uv run python scripts/convert_game.py backend/games/cat5/feather_cat5_prod.md

# Preview without writing
uv run python scripts/convert_game.py backend/games/cat5/feather_cat5_prod.md --dry-run

# All unconverted prod files at top level
uv run python scripts/convert_game.py --all
```

Uses Gemini to extract all fields, with existing games as few-shot references.

**After conversion, verify Cat5 games include:**
- `detail_question_template` — question asked after each correct photo pick (Phase B)
- `sorting_criterion` — ranking dimension for `comparison_chart`/`sorting_game`; empty for `naming_story`
- `collection_catalog` — correct items and distractors

### Generating Icons

```bash
# Collection item icons
uv run python scripts/generate_cat5_icons_gemini.py --mode vertex

# IB concept badge images
uv run python scripts/generate_concept_badges_gemini.py --overwrite
```

## Testing

```bash
cd backend

# Run all tests
uv run pytest ../tests/ -v

# Skip end-to-end tests
uv run pytest ../tests/ -k "not e2e"

# E2E test all demo activities (requires running backend)
python scripts/test_all_activities.py

# Run with coverage
uv run pytest ../tests/ --cov
```

## Code Quality

```bash
cd backend
uv run ruff check .        # Lint
uv run ruff format .       # Format
uv run mypy .              # Type check
```

## License

MIT
