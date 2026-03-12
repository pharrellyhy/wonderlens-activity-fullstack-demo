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
│   ├── prompts/           # Agent system prompts
│   ├── scenarios/         # Activity YAML definitions
│   ├── schemas/           # Pydantic models
│   ├── skills/            # Activity context templates
│   ├── fallbacks/         # Fallback recipes (used after 3 retries)
│   ├── server.py          # FastAPI app + endpoints
│   ├── vision.py          # Photo analysis via Gemini
│   ├── stt.py             # Speech-to-text (Vertex AI)
│   ├── tts.py             # Text-to-speech (Vertex AI)
│   └── config.yaml        # Runtime configuration
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
| `/api/start` | POST | Start session — runs full agent pipeline, returns recipe + first turn |
| `/api/turn` | POST | Process user turn — recipe lookup, returns matched dialogue + screen frame |
| `/api/tts` | POST | Text-to-speech via Vertex AI (fallback: browser SpeechSynthesis) |
| `/api/stt` | POST | Speech-to-text via Vertex AI (fallback: browser Web Speech API) |
| `/api/health` | GET | Health check |

## Agent Pipeline

| Agent | Type | Latency | Role |
|-------|------|---------|------|
| **Director** | LLM (Gemini 2.0 Flash) | ~150ms | Plans creative direction, round count, screen strategy, emotional arc |
| **Script** | LLM (Gemini 2.0 Flash) | ~400ms | Generates all voice/text content with branching dialogue paths |
| **Visual** | Rule-based | ~10ms | Selects screen widgets, assigns assets, sequences frames |
| **Assembler** | Merge + validate | — | Combines Script + Visual into a validated JSON recipe |

The pipeline runs once at session start (~580ms total). After that, each turn is a recipe lookup (~5ms). If generation fails after 3 retries, a pre-built fallback recipe is used.

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
# Run all unit/integration tests (66 tests)
uv run pytest

# Run with coverage
uv run pytest --cov

# Skip end-to-end tests
uv run pytest -m "not e2e"

# End-to-end only (requires running backend + frontend servers)
uv run pytest -m e2e
```

## Code Quality

```bash
uv run ruff check .        # Lint
uv run ruff format .       # Format
uv run mypy .              # Type check
```

## Tech Stack

- **Backend:** Python 3.12+, FastAPI, Pydantic v2, uvicorn
- **LLM:** Gemini 2.0 Flash via Vertex AI (JSON mode)
- **Frontend:** React 19, Tailwind CSS v4, Vite 7
- **Speech:** Vertex AI TTS/STT with browser API fallbacks
- **Testing:** pytest, pytest-asyncio, pytest-mock
- **Linting:** ruff, mypy
