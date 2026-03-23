# Deep Link Integration Guide

How to launch a WonderLens game directly from an upstream app, skipping the game selection screen.

---

## Quick Start

1. Save the upstream conversation to a JSON file served by the WonderLens frontend.
2. Redirect the user to the WonderLens URL with query parameters.

```
https://<wonderlens-host>/?entity=dinosaur&tier=T0&context=/handoff/conversation.json
```

The game starts immediately with a shortened hook that references the upstream conversation.

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

If an unknown entity is passed, the backend returns HTTP 400 with the list of available entities:

```json
{
  "error": "Unknown entity",
  "available_entities": ["dinosaur", "dog", "cat", "ladybug", "dandelion"]
}
```

---

## Conversation Context File

The `context` parameter points to a JSON file that the upstream app writes before redirecting. The file must be a JSON array of conversation turns:

```json
[
  { "role": "child", "text": "I see a big dinosaur!" },
  { "role": "ai", "text": "What do you notice about it?" },
  { "role": "child", "text": "It has spikes on its back!" }
]
```

### Turn schema

| Field  | Type   | Values          | Description |
|--------|--------|-----------------|-------------|
| `role` | string | `"child"`, `"ai"` | Who said it. |
| `text` | string | —               | What was said. |

### Rules

- The file must be served from a URL the browser can fetch (same origin, or CORS-enabled).
- Turns with invalid `role` values or missing `text` are silently filtered out.
- If the file is missing, unreachable, or malformed, the game starts normally without upstream context (the hook will not reference a prior conversation).
- There is no size limit, but only the conversation content matters to the game — keep it to the relevant exchanges.

### Where to put the file

For local development, drop it in `frontend/public/handoff/`:

```bash
mkdir -p frontend/public/handoff

cat > frontend/public/handoff/conversation.json << 'EOF'
[
  { "role": "child", "text": "I see a big dinosaur!" },
  { "role": "ai", "text": "What do you notice about it?" },
  { "role": "child", "text": "It has spikes on its back!" }
]
EOF
```

Then use `?context=/handoff/conversation.json` in the URL.

For production, the upstream app should write the file to a location served by the same host, or a CORS-enabled endpoint.

---

## What Happens

1. **Frontend** parses the URL parameters on page load.
2. **Frontend** fetches the conversation JSON file (if `context` is provided), validates it, and extracts `{role, text}` turns.
3. **Frontend** calls `POST /api/start-deep-link` with the entity, tier, and validated conversation turns.
4. **Backend** looks up the entity, builds the game session, and generates a **shortened hook** (1-2 sentences) that:
   - Briefly acknowledges what the child was just discussing (referencing a detail from the upstream conversation).
   - Immediately invites the child into the game using invitational language ("Would you like to...?").
5. The game proceeds normally from there (STEP_2 rules/mission, STEP_3 rounds, etc.).
6. The URL is cleaned up via `replaceState` after a successful start, so a browser refresh returns to the normal game selection screen.

---

## Backend API (Direct Use)

If the upstream app prefers to call the backend API directly instead of using the URL redirect flow:

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
| `conversation_context` | array  | No       | `[]`    | Upstream conversation turns. Each turn has `role` (`"ai"` or `"child"`) and `text`. |

**Success response (200):**

```json
{
  "session_id": "uuid",
  "vision_result": { "entity": "dinosaur", "category": "", "scene": "", "features": [] },
  "first_turn": {
    "dialogue": "[excited] Those spikes sound amazing! Would you like to take your dinosaur on a time travel adventure?",
    "tone_marker": "excited",
    "screen_frame": { ... },
    "audio": { ... },
    "response_type": "hook"
  },
  "activity_type": "time_machine_dinosaur",
  "template_type": "cat1",
  "session_state": { ... },
  "photo_url": "/icons/dinosaur.png",
  "status": "ok",
  "latency_ms": 580
}
```

**Error response — unknown entity (400):**

```json
{
  "error": "Unknown entity",
  "available_entities": ["dinosaur", "dog", "cat", "ladybug", "dandelion"]
}
```

---

## Examples

### Minimal (no conversation context)

```
https://localhost:5173/?entity=dog
```

Starts the Mood Changer Dog game at tier T0 with a normal-length hook.

### With conversation context

```bash
# 1. Write the conversation file
cat > frontend/public/handoff/dino-chat.json << 'EOF'
[
  { "role": "child", "text": "I found a dinosaur with big teeth!" },
  { "role": "ai", "text": "Wow, what kind of dinosaur do you think it is?" },
  { "role": "child", "text": "A T-Rex! It looks scary but cool." }
]
EOF

# 2. Open this URL
# http://localhost:5173/?entity=dinosaur&tier=T1&context=/handoff/dino-chat.json
```

The game starts with a shortened hook like: *"A T-Rex with big teeth — that does sound cool! Would you like to take your dinosaur on a time travel adventure?"*

### With tier override

```
https://localhost:5173/?entity=cat&tier=T2
```

Starts Dream Whisperer Cat at tier T2 (ages 6-8) with no upstream context.

### Direct API call

```bash
curl -X POST http://localhost:8000/api/start-deep-link \
  -H 'Content-Type: application/json' \
  -d '{
    "entity": "ladybug",
    "tier": "T0",
    "conversation_context": [
      {"role": "child", "text": "I see spots on this bug!"},
      {"role": "ai", "text": "How many spots can you count?"},
      {"role": "child", "text": "Five!"}
    ]
  }'
```
