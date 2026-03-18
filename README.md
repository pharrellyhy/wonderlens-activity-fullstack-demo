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
| `LOG_LEVEL` | Logging level (default: `INFO`) |

## Project Structure

```
├── backend/
│   ├── agents/            # Director, Script, Visual, Recipe Assembler
│   ├── entity_registry.py # Single source of truth for all entity config
│   ├── prompts/           # Agent system prompts
│   ├── recipes/           # Instruction-based recipe JSON files
│   ├── scenarios/         # Activity YAML definitions
│   ├── schemas/           # Pydantic models
│   ├── skills/            # Step instruction templates
│   ├── server.py          # FastAPI app + endpoints
│   ├── turn_handler.py    # Unified step transition logic
│   ├── recipe_loader.py   # Recipe loading + session state builder
│   ├── state_machine.py   # Step progression + screen frame selection
│   ├── vision.py          # Photo analysis via Gemini
│   ├── stt.py             # Speech-to-text (Vertex AI)
│   └── tts.py             # Text-to-speech (Vertex AI)
├── frontend/
│   └── src/
│       ├── App.jsx         # Main React app
│       ├── components/     # UI components
│       ├── widgets/        # Device screen widgets
│       ├── hooks/          # React hooks
│       └── utils/api.js    # API client
├── tests/                  # pytest test suite
└── docs/plans/             # Design documents
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/start` | POST | Start session — runs agent pipeline, returns recipe + first turn |
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

| Activity | Entity | Category | Tier | Ages |
|----------|--------|----------|------|------|
| Mood Changer | Stuffed dog | Cat 1 — In-Device Verbal | T0 | 3–4 |
| Dream Whisperer | Stuffed cat | Cat 1 — In-Device Verbal | T0 | 3–4 |
| Dino Time Machine | Toy dinosaur | Cat 1 — In-Device Verbal | T0 | 3–4 |
| The Polka-Dot Patrol | Ladybug | Cat 5 — Collection/Tracking | T1 | 4–6 |
| The Fluffy Things Expedition | Dandelion | Cat 5 — Collection/Tracking | T1 | 4–6 |

**Tiers:** T0 (ages 2–4), T1 (ages 4–6), T2 (ages 6–8)

## Testing

```bash
cd backend

# Run all tests
uv run pytest ../tests/ -v

# Skip end-to-end tests
uv run pytest ../tests/ -k "not e2e"

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
