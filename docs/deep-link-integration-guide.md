# Deep Link Integration Guide

How to launch a WonderLens game directly from an upstream app, skipping the game selection screen.

---

## How It Works

The upstream app **redirects the browser** to the WonderLens URL. WonderLens handles everything from there — the upstream app does not call any WonderLens API directly.

```
Upstream App                                  WonderLens
────────────                                  ──────────
1. Conversation with child
2. Save conversation to a
   JSON file at a served URL
3. Redirect browser to ──────────────────────▶ 4. Page loads
   /?entity=dinosaur                           5. Parses URL params
   &tier=T0                                    6. Fetches context JSON file
   &context=/handoff/conv.json                 7. Calls POST /api/start-deep-link
                                               8. Renders game immediately
                                                  (shortened hook referencing
                                                   the upstream conversation)
                                               9. Game proceeds normally
                                                  (STEP_2 → STEP_3 → ...)
```

The child sees the WonderLens game start immediately — no game selection, no summary screen.

---

## Upstream Integration Steps

### Step 1: Save the conversation

When the upstream conversation ends, write the conversation history to a JSON file that the browser can fetch after redirect. The file must be a JSON array of `{role, text}` objects:

```json
[
  { "role": "child", "text": "I found a dinosaur with big spikes!" },
  { "role": "ai", "text": "What do you think they were for?" },
  { "role": "child", "text": "Maybe to protect it from other dinosaurs!" }
]
```

Where to put it depends on your deployment:

| Setup | Where to save | Context URL |
|-------|--------------|-------------|
| Same host | `frontend/public/handoff/conversation.json` | `/handoff/conversation.json` |
| Separate host | Any CORS-enabled endpoint | Full URL: `https://upstream.com/handoff/conversation.json` |
| Local dev | `frontend/public/handoff/` | `/handoff/conversation.json` |

### Step 2: Redirect to WonderLens

```js
// Upstream app code — after conversation ends:
window.location.href = 'https://<wonderlens-host>/?entity=dinosaur&tier=T0&context=/handoff/conversation.json';
```

That's it. WonderLens takes over from here.

---

## End-to-End Example (Upstream App Code)

```js
// ── Upstream app: conversation ends, hand off to WonderLens ──

// The conversation that just happened
const conversation = [
  { role: 'child', text: 'I found a dinosaur with big spikes!' },
  { role: 'ai',    text: 'Wow, those spikes look amazing! What do you think they were for?' },
  { role: 'child', text: 'Maybe to protect it from other dinosaurs!' },
  { role: 'ai',    text: 'That is a great idea — like natural armor! Would you like to play a game with this dinosaur?' },
  { role: 'child', text: 'Yes!' },
];

// 1. Save conversation to a file the browser can fetch after redirect.
//    How you do this depends on your backend. Examples:
//
//    Express:  app.post('/handoff/save', (req, res) => { fs.writeFileSync('public/handoff/conversation.json', JSON.stringify(req.body)); res.sendStatus(200); });
//    Django:   write to STATIC_ROOT/handoff/conversation.json
//    S3:       upload to s3://bucket/handoff/conversation.json with public-read ACL
//
await fetch('/handoff/save', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(conversation),
});

// 2. Redirect to WonderLens — the game starts immediately.
const wonderlensHost = 'https://wonderlens.example.com';
const entity = 'dinosaur';          // which game to play
const tier = 'T0';                  // age tier: T0 (2-4), T1 (4-6), T2 (6-8)
const contextPath = '/handoff/conversation.json';

window.location.href = `${wonderlensHost}/?entity=${entity}&tier=${tier}&context=${encodeURIComponent(contextPath)}`;

// The child now sees:
//   "[excited] Those spikes sound like natural armor! Would you like to
//    take your dinosaur on a time travel adventure?"
//
// Game proceeds: STEP_2 (rules) → STEP_3 (rounds) → STEP_4 (celebrate) → STEP_5 (closing)
```

---

## URL Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `entity`  | Yes      | —       | Entity name to play. See [supported entities](#supported-entities). |
| `tier`    | No       | `T0`    | Age tier: `T0` (ages 2-4), `T1` (ages 4-6), `T2` (ages 6-8). |
| `context` | No       | —       | URL path to a JSON file containing the upstream conversation. |

---

## Supported Entities

| Entity name | Game | Category |
|-------------|------|----------|
| `dinosaur`  | Time Machine Dinosaur | Cat 1 (In-Device Verbal) |
| `dog`       | Mood Changer Dog | Cat 1 (In-Device Verbal) |
| `cat`       | Dream Whisperer Cat | Cat 1 (In-Device Verbal) |
| `ladybug`   | Polka Dot Patrol | Cat 5 (Out-of-Device Collection) |
| `dandelion` | Fluffy Expedition Dandelion | Cat 5 (Out-of-Device Collection) |

Entity lookup is case-insensitive. Common keywords also work (e.g., `dino` maps to `dinosaur`).

If an unknown entity is passed, the game shows an error. The backend returns HTTP 400 with available entities:

```json
{
  "error": "Unknown entity",
  "available_entities": ["dinosaur", "dog", "cat", "ladybug", "dandelion"]
}
```

---

## Conversation Context File

### Turn schema

| Field  | Type   | Values             | Description |
|--------|--------|--------------------|-------------|
| `role` | string | `"child"`, `"ai"`  | Who said it. |
| `text` | string | —                  | What was said. |

### Rules

- The file must be served from a URL the browser can fetch (same origin, or CORS-enabled).
- Turns with invalid `role` values or missing `text` are silently filtered out.
- If the file is missing, unreachable, or malformed, the game starts normally without upstream context (the hook will not be shortened or reference a prior conversation).
- Keep it to the relevant exchanges — only the conversation content matters.

---

## What the Child Sees

### With upstream context

The game opens with a **shortened hook** (1-2 sentences):

> *"Those spikes sound like natural armor! Would you like to take your dinosaur on a time travel adventure?"*

The hook references a specific detail from the upstream conversation, then immediately invites the child into the game.

### Without upstream context

If `context` is omitted or the file can't be loaded, the game opens with a **normal-length hook** — the full observation + wonder sequence as if the child selected the game from the menu.

### After the hook

The game proceeds identically in both cases: STEP_2 (rules/mission) → STEP_3 (gameplay rounds) → celebration → closing.

### On browser refresh

The URL parameters are cleared after a successful start (`replaceState`), so refreshing returns to the normal game selection screen.

---

## Quick Test (Local Dev)

```bash
# 1. Start backend + frontend
cd backend && uv run uvicorn server:app --reload --port 8000 &
cd frontend && npm run dev &

# 2. Create a test conversation file
mkdir -p frontend/public/handoff
cat > frontend/public/handoff/conversation.json << 'EOF'
[
  { "role": "child", "text": "I found a dinosaur with big spikes!" },
  { "role": "ai", "text": "What do you think they were for?" },
  { "role": "child", "text": "Maybe to protect it from other dinosaurs!" }
]
EOF

# 3. Open in browser — game starts immediately
open "http://localhost:5173/?entity=dinosaur&tier=T0&context=/handoff/conversation.json"
```

More examples:

```
# Minimal — no conversation context, default tier
http://localhost:5173/?entity=dog

# Cat 5 game with tier override
http://localhost:5173/?entity=ladybug&tier=T1&context=/handoff/conversation.json

# Keyword lookup (dino → dinosaur)
http://localhost:5173/?entity=dino&tier=T2
```

---

## Backend API Reference

The WonderLens frontend calls this API internally. Upstream apps normally **do not** call this — they redirect the browser instead. This reference is provided for testing and custom integrations.

### `POST /api/start-deep-link`

**Request body:**

```json
{
  "entity": "dinosaur",
  "tier": "T0",
  "conversation_context": [
    { "role": "child", "text": "I see a big dinosaur!" },
    { "role": "ai", "text": "What do you notice about it?" },
    { "role": "child", "text": "It has spikes on its back!" }
  ]
}
```

| Field                  | Type   | Required | Default | Description |
|------------------------|--------|----------|---------|-------------|
| `entity`               | string | Yes      | —       | Entity name (case-insensitive). |
| `tier`                 | string | No       | `"T0"`  | Age tier. |
| `conversation_context` | array  | No       | `[]`    | Upstream conversation turns (`role` + `text`). |

**Success response (200):**

```json
{
  "session_id": "uuid",
  "vision_result": { "entity": "dinosaur", "category": "", "scene": "", "features": [] },
  "first_turn": {
    "dialogue": "[excited] Those spikes sound amazing! Would you like to take your dinosaur on a time travel adventure?",
    "tone_marker": "excited",
    "screen_frame": { "..." : "..." },
    "audio": { "..." : "..." },
    "response_type": "hook"
  },
  "activity_type": "time_machine_dinosaur",
  "template_type": "cat1",
  "session_state": { "..." : "..." },
  "photo_url": "/icons/dinosaur.png",
  "status": "ok",
  "latency_ms": 580
}
```

**Test with curl:**

```bash
curl -X POST http://localhost:8000/api/start-deep-link \
  -H 'Content-Type: application/json' \
  -d '{
    "entity": "dinosaur",
    "tier": "T0",
    "conversation_context": [
      {"role": "child", "text": "I see a big dinosaur!"},
      {"role": "ai", "text": "What do you notice about it?"},
      {"role": "child", "text": "It has spikes on its back!"}
    ]
  }'
```
