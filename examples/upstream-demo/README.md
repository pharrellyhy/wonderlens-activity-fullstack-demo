# Upstream Demo App

Minimal upstream app demonstrating deep link handoff to WonderLens.

Simulates a multi-turn conversation with a child, then hands off to the WonderLens game via deep link.

## Setup

```bash
# Terminal 1: WonderLens backend
cd backend
uv run uvicorn server:app --reload --port 8000

# Terminal 2: WonderLens frontend
cd frontend
npm run dev

# Terminal 3: This upstream demo
cd examples/upstream-demo
pip install fastapi uvicorn
python app.py
```

## Usage

1. Open http://localhost:3000
2. Pick an entity and tier
3. Click **Start Conversation** — watch the simulated chat play out
4. Click **Hand Off to WonderLens** — saves the conversation JSON and redirects to the WonderLens game

The WonderLens game starts immediately with a shortened hook that references the upstream conversation.
