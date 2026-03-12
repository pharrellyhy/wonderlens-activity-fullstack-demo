# WonderLens Activity Demo — Full-Stack Build Spec

> **Created**: 2026-03-12 (v3 — multi-agent architecture)
> **Purpose**: Everything needed to build and run the WonderLens interactive demo locally
> **How to use**: Open Claude Code in the demo repo directory and say: "Read the build spec and build the demo step by step."

---

## 1. What We're Building

A **split-view interactive browser demo** with a **multi-agent backend** that validates the WonderLens agent architecture spec:

1. User selects a photo (from preloaded set or upload)
2. **Director Agent** plans the activity composition (creative brief, modalities, round count)
3. **Script Agent** generates voice dialogue with branching (correct/incorrect/silence paths)
4. **Visual Agent** selects widgets and assets (rule-based in V1)
5. **Recipe Assembler** merges agent outputs into a JSON recipe
6. Frontend renders: left panel = conversation, right panel = screen widgets
7. AI speech played via TTS, user responds via text or mic
8. Silence timeout → re-engagement or graceful exit

**Two demo activities** using Loop 1's tested scenarios:
- **Category 1** (In-Device Verbal): from Loop 1 scenarios (mood_changer_dog, dream_whisperer_cat, or time_machine_dinosaur)
- **Category 5** (Out-of-Device Collection): from Loop 1 scenarios (polka_dot_patrol or fluffy_expedition_dandelion)

---

## 2. Architecture Overview

### The Multi-Agent Pipeline

```
User selects photo + tier
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                         │
│                                                             │
│  ┌───────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │  Director  │──▶│   Script     │   │   Visual     │       │
│  │  Agent     │   │   Agent      │   │   Agent      │       │
│  │ (LLM,150ms│   │ (LLM,400ms) │   │ (rules,10ms) │       │
│  └───────────┘   └──────────────┘   └──────────────┘       │
│        │                │                   │               │
│        └────────────────┼───────────────────┘               │
│                         ▼                                   │
│              ┌─────────────────────┐                        │
│              │  Recipe Assembler   │                        │
│              │  + Validator        │                        │
│              └─────────────────────┘                        │
│                         │                                   │
│                    JSON Recipe                              │
│                         │                                   │
│  Retry logic: fail → retry (up to 3x) → fallback recipe    │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                          │
│                                                             │
│  ┌──────────────────┐  ┌───────────────────────┐            │
│  │ Conversation     │  │ Device Screen          │            │
│  │ Panel (left)     │  │ Panel (right)          │            │
│  │ - chat bubbles   │  │ - widget renderer      │            │
│  │ - text input     │  │ - animation overlay    │            │
│  │ - mic button     │  │ - audio indicator      │            │
│  └──────────────────┘  └───────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### Key Difference from Loop 1

| Aspect | Loop 1 (Prompt Optimization) | Demo (Multi-Agent) |
|---|---|---|
| LLM calls per turn | 1 (monolithic) | 2 (Director + Script) |
| Visual decisions | Inline `[SCREEN]` text parsing | Rule-based Visual Agent, JSON output |
| Output format | Markdown with `[SCREEN]`/`[AUDIO]` | Structured JSON recipe |
| Fallback | None | Default recipes per activity, 3-retry logic |

---

## 3. Tech Stack

| Component | Choice |
|---|---|
| Frontend | React (JSX) + Tailwind CSS (Vite dev server) |
| Backend | FastAPI (Python) — multi-agent pipeline |
| AI | Gemini 2.0 Flash via Vertex AI (`vertexai=True`, JSON mode) |
| TTS | Gemini TTS via Vertex AI — fallback: browser SpeechSynthesis |
| ASR | Browser Web Speech API (SpeechRecognition) |
| Credentials | `.env` with GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION |
| Package mgmt | `uv` for Python, `npm` for frontend |

---

## 4. Project Structure

```
wonderlens-demo/
├── backend/
│   ├── server.py                        — FastAPI server + API endpoints
│   ├── config.py                        — Settings (Pydantic BaseSettings, loads .env)
│   ├── logger.py                        — Structured logging (loguru or stdlib)
│   ├── db.py                            — SQLite via aiosqlite (sessions, turns, analytics)
│   ├── vision.py                        — Vision API (Gemini vision, based on refs/)
│   ├── tts.py                           — TTS API (Gemini TTS, based on refs/)
│   ├── agents/
│   │   ├── director.py                  — Director Agent (LLM, ~150ms)
│   │   ├── script_agent.py              — Script Agent (LLM, ~400ms, based on refs/)
│   │   ├── visual_agent.py              — Visual Agent (rule-based, ~10ms)
│   │   └── recipe_assembler.py          — Merge + validate + fallback
│   ├── skills/                          — Agent skill files (system prompts + rules)
│   │   ├── director.md                  — Director Agent skill
│   │   ├── script.md                    — Script Agent skill (from Loop 1's optimized prompt)
│   │   ├── visual.md                    — Visual Agent skill (rule tables + mappings)
│   │   ├── assembler.md                 — Recipe Assembler skill (validation checklist)
│   │   ├── few_shot.md                  — Few-shot examples for Script Agent
│   │   └── activity_context_template.md — Context injection template
│   ├── schemas/
│   │   ├── composition_plan.py          — Director output Pydantic model
│   │   ├── voice_script.py              — Script Agent output Pydantic model
│   │   ├── visual_composition.py        — Visual Agent output Pydantic model
│   │   └── recipe.py                    — Final JSON recipe Pydantic model
│   ├── fallbacks/
│   │   ├── polka_dot_patrol.json        — Default recipe for Cat 5 demo activity
│   │   └── mood_changer_dog.json        — Default recipe for Cat 1 demo activity
│   ├── refs/                            — Reference implementations (PROVIDED BY USER, read-only)
│   │   ├── ref_llm_call.py              — Reference: how to call Gemini LLM via Vertex AI
│   │   ├── ref_vision.py                — Reference: how to call Gemini Vision API
│   │   ├── ref_tts.py                   — Reference: how to call Gemini TTS API
│   │   └── ref_stt.py                   — Reference: how to do speech recognition
│   ├── scenarios/                       — Activity definitions (YAML, from Loop 1)
│   ├── tier_rules.yaml                  — 3-tier age parameters (from Loop 1)
│   ├── config.yaml                      — App config (agent timeouts, model names, DB path, log level)
│   ├── pyproject.toml
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.jsx                      — Main split-view layout
│   │   ├── components/
│   │   │   ├── ConversationPanel.jsx
│   │   │   ├── DeviceScreen.jsx
│   │   │   ├── ChatBubble.jsx
│   │   │   ├── TextInput.jsx
│   │   │   ├── PhotoSelector.jsx
│   │   │   ├── TopBar.jsx
│   │   │   └── RetryButton.jsx          — Retry/fallback UI
│   │   ├── widgets/
│   │   │   ├── PhotoDisplay.jsx
│   │   │   ├── ProgressTracker.jsx
│   │   │   ├── CharacterDisplay.jsx
│   │   │   ├── PhotoGrid.jsx
│   │   │   ├── BadgeAward.jsx
│   │   │   └── AnimationOverlay.jsx
│   │   ├── hooks/
│   │   │   ├── useConversation.js
│   │   │   ├── useSpeechRecognition.js
│   │   │   ├── useTTS.js
│   │   │   └── useSilenceTimer.js
│   │   └── utils/
│   │       └── api.js                   — Backend API client
│   ├── public/
│   │   └── photos/                      — Preloaded demo photos
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## 5. Agent Skills

Each agent loads a `.md` skill file at startup. The skill serves dual purpose:
1. **At build time**: Claude Code reads it to understand what the agent does → writes the correct code
2. **At runtime**: Gemini reads it as system prompt → behaves according to the skill

```python
# Pattern used by all LLM-based agents:
class SomeAgent:
    def __init__(self):
        self.skill = Path("skills/some_agent.md").read_text()
    
    async def run(self, context):
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{"role": "user", "text": json.dumps(context)}],
            config=GenerateContentConfig(
                system_instruction=self.skill,   # skill IS the system prompt
                response_mime_type="application/json",
            )
        )
        return parse_response(response)
```

### 5.1 skills/director.md

```markdown
## Role

You are the Director Agent for WonderLens, an AI-powered educational camera for children ages 2-8.
You are a creative planner — like a children's TV show producer. You decide WHAT the activity
experience should look like, but you NEVER generate any child-facing dialogue or content.

## Your Job

Given an object a child photographed, an activity type, and an age tier, output a Composition Plan
that tells the Script Agent and Visual Agent what to create.

## Output Format (JSON only, no other text)

{
  "creative_brief": "1-2 sentence creative direction. Be specific to THIS object in THIS context.",
  "modalities": ["voice", "screen"],
  "round_count": <int, constrained by tier: T0=2-4, T1=3-5, T2=3-5>,
  "screen_strategy": "<static|per_round|progressive>",
  "widget_hint": "<primary widget from: photo_display, progress_tracker, character_display, photo_grid, badge_award>",
  "emotional_arc": "<build_excitement|calm_curiosity|playful_surprise|gentle_wonder>",
  "ib_concept_integration": "How to weave the IB key concept into the activity.",
  "closing_concept_targets": ["<related concepts to name in closing, max: T0=1, T1=2, T2=3>"],
  "transition_strategy": "<natural_question|challenge|imagination_prompt|silly_proposal>"
}

## Decision Rules

- For Category 1 (verbal): screen_strategy = "per_round" (new scene each round), widget = "character_display"
- For Category 5 (collection): screen_strategy = "progressive" (slots fill up), widget = "progress_tracker"
- emotional_arc should match the activity metaphor: silly games → playful_surprise, nature exploration → calm_curiosity
- round_count MUST respect tier max. Never exceed it.
- creative_brief must be SPECIFIC to the entity. "A dog activity" is too generic. "Frame around what dogs dream about when they nap" is good.

## What You Do NOT Do

- Do NOT write any dialogue, scripts, or child-facing text
- Do NOT select specific assets or animations (Visual Agent does that)
- Do NOT generate sound effects or music cues (Script Agent handles sfx_cue)
- Keep your output under 150 tokens
```

### 5.2 skills/script.md

This is adapted from Loop 1's optimized `system_prompt.md` — the battle-tested version that produces good conversations. Key additions for multi-agent: it now receives the Director's Composition Plan as input context.

```markdown
## Role

You are the Script Agent for WonderLens. You generate all voice/text content that a child
will hear during an activity. You receive a Composition Plan from the Director Agent and
produce a complete Voice Script with branching dialogue paths.

## Activity Context

{activity_context}

## Composition Plan (from Director)

{composition_plan}

## Output Format (JSON only, no other text)

{
  "hook_line": "<emotional hook, MUST follow hook rule — see below>",
  "transition_line": "<bridge from photo observation to activity>",
  "rounds": [
    {
      "prompt": "<what AI says to prompt the child>",
      "correct_responses": ["<acceptable answers, empty for open-ended>"],
      "on_correct": "<encouraging response + extend with knowledge>",
      "on_incorrect": "<validate attempt, gently redirect>",
      "on_silence": "<gentle re-engagement after timeout>",
      "hint": "<scaffolding if child is stuck>",
      "sfx_cue": "<sound effect key or null>"
    }
  ],
  "closing_speech": "<celebrate FIRST, then name IB concepts naturally as praise>",
  "tomorrow_hook": "<forward hook for next session>"
}

## CRITICAL — Hook Rule (Non-Negotiable)

Your hook_line MUST be a PURE EMOTIONAL REACTION. This is the first thing the child hears.
- Express wonder, delight, amazement about the object
- For T0: Use exclamation + name object + feeling question. "Oh wow, a fluffy doggy! Is it feeling happy today?"
- For T1: Use emotional wonder about a visual feature. "A ladybug! Look at those amazing little spots!"
- For T2: Use experience hook. "A butterfly! Have you ever seen one this close?"
- NEVER ask factual questions (color, count, type, name) in the hook
- NEVER test knowledge in the hook

## Tier Language Rules

{tier_constraints}

## Edge Case Handling

- on_incorrect: ALWAYS validate the child's attempt before redirecting. Never say "wrong."
- on_silence: Gentle, zero-pressure. Offer a simpler version or a choice.
- If the Director's creative_brief mentions a specific angle, follow it in your dialogue.
- Match the Director's emotional_arc: playful_surprise → use humor and absurdity; calm_curiosity → use wonder and questions.
- Match the Director's transition_strategy: silly_proposal → "Want to play TRUE or SILLY?"; natural_question → "I wonder if..."

## Closing Speech Structure

1. Celebrate FIRST — praise what the child accomplished with specifics
2. Award the role title from the activity
3. Name IB concepts NATURALLY (feels like praise, not vocabulary): "You discovered the beautiful Form of..."
4. End with tomorrow_hook
5. Concept count must match tier: T0=1, T1=2, T2=up to 3

## Few-Shot Examples

{few_shot}
```

### 5.3 skills/visual.md

Not a Gemini prompt — this is a rule reference that the Visual Agent code reads and follows. But structured as markdown so Claude Code understands the logic when building `visual_agent.py`.

```markdown
## Role

You are the Visual Agent for WonderLens. You select screen widgets, assign placeholder assets,
and sequence screen frames. In V1, you are RULE-BASED — no LLM calls.

## Decision Tables

### Activity Type → Primary Widget

| Activity Type | Widget | Reason |
|---|---|---|
| mood_changer | character_display | Scene illustrations per emotional scenario |
| dream_whisperer | character_display | Dream scene illustrations per round |
| time_machine | character_display | Time period scene illustrations |
| polka_dot_patrol | progress_tracker | Collection slots fill as child finds items |
| fluffy_expedition | progress_tracker | Collection slots fill as child finds items |
| (any Cat 1 verbal) | character_display | Default for verbal activities |
| (any Cat 5 collection) | progress_tracker | Default for collection activities |

### Screen Strategy → Frame Count

| Strategy | Frames | Logic |
|---|---|---|
| static | 1 | Same frame for entire activity |
| per_round | N = round_count | One frame per round, each with different scene |
| progressive | 1 + N updates | Base frame with progressive slot-filling |

### Emotional Arc → Animation Preset

| Arc | Default Animation | Celebration Animation |
|---|---|---|
| build_excitement | celebration_burst | mission_complete_fanfare |
| calm_curiosity | gentle_pulse | sparkle_highlight |
| playful_surprise | appear | celebration_burst |
| gentle_wonder | sparkle_highlight | badge_reveal |

### Frame Sequencing Rules

1. First frame ALWAYS uses the child's photo (widget: photo_display) with sparkle_highlight
2. Transition to activity widget on round 1
3. Each round updates the widget state (new scene, filled slot, etc.)
4. Last round → celebration_frame with badge_award widget
5. If progressive strategy: update the SAME frame (add items to slots) rather than replacing

### Fallback Rules

- Missing asset → use placeholder text description in widget_params
- Unknown activity type → default to character_display
- T0 override → always include screen (no voice-only in demo)
```

### 5.4 skills/assembler.md

Reference for the Recipe Assembler's validation logic. Read by Claude Code when building `recipe_assembler.py`.

```markdown
## Role

You are the Recipe Assembler for WonderLens. You merge outputs from the Script Agent and
Visual Agent into a single ActivityRecipe JSON, then validate it.

## Merge Rules

1. Take voice_script from Script Agent output
2. Take screen_frames from Visual Agent output
3. If Script Agent round_count != Visual Agent frame_count: pad the shorter array
   - Pad screen_frames by repeating the last frame
   - Pad voice_script rounds by using generic encouragement ("Keep going! You're doing great!")
4. Take metadata from Director Agent's Composition Plan
5. Add celebration_frame from Visual Agent

## Validation Checklist (run in order)

| Check | Severity | On Failure |
|---|---|---|
| JSON schema valid | FATAL | Reject, trigger retry |
| hook_line contains no factual questions | ERROR | Reject, trigger retry |
| round_count within tier limits | WARNING | Truncate to tier max |
| closing_speech names ≤ tier concept max | WARNING | Trim excess concepts |
| All sfx_cue values are from the allowed set | WARNING | Set invalid cues to null |
| voice_script rounds count == screen_frames count | WARNING | Pad shorter to match |

## Retry + Fallback Logic

1. On FATAL or ERROR → retry full pipeline (up to 3 total attempts)
2. On 3rd failure → load fallback recipe from fallbacks/{activity_type}.json
3. On WARNING → fix in place, log warning, continue
4. Return the recipe with a status field: "ok", "fixed_warnings", or "fallback"

## Allowed SFX Cues

wonder_chime, excitement_rising, photo_shutter_click, slot_fill_chime,
mission_accepted, mission_complete_fanfare, celebration_fanfare,
badge_awarded, scene_woosh, game_start_chime
```

---

## 6. Backend: Multi-Agent Pipeline

### 6.1 Director Agent (director.py)

**Purpose**: Plans the composition — creative direction, round count, screen strategy, emotional arc. Does NOT generate any child-facing content.

**Input**: Object context + tier + IB theme + activity type
**Output**: Composition Plan (JSON, ~100 tokens)
**LLM**: Gemini 2.0 Flash with JSON mode, temperature 0.3
**Latency budget**: ~150ms
**Timeout**: 200ms hard cap → use default plan

```python
# Output schema (Pydantic)
class CompositionPlan(BaseModel):
    creative_brief: str           # 1-2 sentence direction
    modalities: list[str]         # ["voice", "screen", "sound_effect"]
    round_count: int              # Constrained by tier
    screen_strategy: str          # "static" | "per_round" | "progressive"
    widget_hint: str | None       # Primary widget suggestion
    emotional_arc: str            # "build_excitement" | "calm_curiosity" | "playful_surprise" | "gentle_wonder"
    ib_concept_integration: str   # How to weave IB concept
    closing_concept_targets: list[str]  # Related concepts for closing
    transition_strategy: str      # "natural_question" | "challenge" | "imagination_prompt" | "silly_proposal"
```

### 6.2 Script Agent (script_agent.py)

**Purpose**: Generates all voice/text content — hook, transition, per-round dialogue with branching, closing speech.

**Input**: Composition Plan + object context + tier rules + activity design
**Output**: Voice Script (JSON, ~300-500 tokens)
**LLM**: Gemini 2.0 Flash with JSON mode, temperature 0.7
**Latency budget**: ~400ms
**Timeout**: 600ms hard cap → use default script

```python
# Output schema (Pydantic)
class VoiceScript(BaseModel):
    hook_line: str                # Emotional hook (MUST follow hook rule)
    transition_line: str          # Bridge to activity
    rounds: list[Round]           # Per-round dialogue
    closing_speech: str           # Celebration + IB concepts
    tomorrow_hook: str            # Cross-session retention

class Round(BaseModel):
    prompt: str                   # AI says this
    correct_responses: list[str]  # Acceptable answers (empty for open-ended)
    on_correct: str               # Response to correct answer
    on_incorrect: str             # Response to incorrect (encouraging)
    on_silence: str               # Response after silence timeout
    hint: str                     # Help if stuck
    sfx_cue: str | None           # Sound effect trigger
```

**Uses Loop 1's optimized system prompt** as the base for the Script Agent's prompt. The key insight from Loop 1: the tier rules injection, hook rule enforcement, and closing structure in `system_prompt.md` are battle-tested.

### 6.3 Visual Agent (visual_agent.py)

**Purpose**: Selects screen widgets, assigns assets, sequences frames. Rule-based in V1 (no LLM).

**Input**: Composition Plan + activity type + available assets
**Output**: Visual Composition (JSON)
**LLM**: None (rule-based)
**Latency**: ~10ms

```python
# Decision tree
ACTIVITY_WIDGET_MAP = {
    "mood_changer": "character_display",
    "dream_whisperer": "character_display",
    "time_machine": "character_display",
    "polka_dot_patrol": "progress_tracker",
    "fluffy_expedition": "progress_tracker",
}

EMOTIONAL_ARC_ANIMATION = {
    "build_excitement": "celebration_burst",
    "calm_curiosity": "idle_bounce",
    "playful_surprise": "appear",
    "gentle_wonder": "sparkle_highlight",
}

# Output schema
class VisualComposition(BaseModel):
    screen_frames: list[ScreenFrame]
    celebration_frame: ScreenFrame | None

class ScreenFrame(BaseModel):
    widget: str                   # Widget primitive ID
    widget_params: dict           # Widget-specific params
    animation: str | None         # Animation preset
    trigger: str                  # "on_enter" | "on_round_N" | "on_correct"
```

### 6.4 Recipe Assembler (recipe_assembler.py)

**Merges** Script Agent + Visual Agent outputs into a single JSON recipe.
**Validates**: schema, hook rule, tier constraints, round count match.

```python
class ActivityRecipe(BaseModel):
    activity_type: str
    voice_script: VoiceScript
    screen_frames: list[ScreenFrame]
    celebration_frame: ScreenFrame | None
    metadata: RecipeMetadata

class RecipeMetadata(BaseModel):
    tier: str
    ib_theme: str
    ib_key_concept: str
    concepts_earned: list[str]
    round_count: int
```

### 6.5 Retry + Fallback Logic

```python
MAX_RETRIES = 3

async def generate_recipe(context) -> ActivityRecipe:
    for attempt in range(MAX_RETRIES):
        try:
            plan = await director_agent.run(context)
            script = await script_agent.run(plan, context)
            visuals = await visual_agent.run(plan, context)
            recipe = assembler.merge(script, visuals, plan)
            validator.check(recipe)  # Raises on FATAL
            return recipe
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                continue  # Retry
    
    # All 3 attempts failed → load fallback
    logger.error("All retries failed, using fallback recipe")
    return load_fallback_recipe(context.activity_type)
```

**Frontend sees**: on each retry, the API returns `{ "status": "retrying", "attempt": N }`. After 3 failures, returns `{ "status": "fallback", "recipe": ... }`. Frontend shows a subtle "Using backup mode" indicator but the experience continues seamlessly.

### 6.6 Config (config.py + config.yaml)

Centralized settings using Pydantic BaseSettings. Loads from `.env` (secrets) and `config.yaml` (app config).

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Vertex AI (from .env)
    google_cloud_project: str
    google_cloud_location: str
    google_application_credentials: str

    # App config (from config.yaml, loaded at startup)
    gemini_model: str = "gemini-2.0-flash"
    director_timeout_ms: int = 200
    director_max_tokens: int = 150
    script_timeout_ms: int = 600
    script_max_tokens: int = 600
    max_retries: int = 3
    db_path: str = "data/demo.db"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
```

```yaml
# config.yaml
gemini_model: "gemini-2.0-flash"
director_timeout_ms: 200
director_max_tokens: 150
script_timeout_ms: 600
script_max_tokens: 600
max_retries: 3
db_path: "data/demo.db"
log_level: "INFO"
```

All agents read timeouts and model names from `Settings` — no hardcoded values in agent code.

### 6.7 Logging (logger.py)

Structured logging with context per request. Every agent call and API request is logged.

```python
# logger.py
import logging
import json
from datetime import datetime

def setup_logger(level: str = "INFO"):
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("wonderlens")

logger = setup_logger()
```

**What gets logged:**

| Event | Level | Fields |
|---|---|---|
| API request received | INFO | endpoint, session_id, tier |
| Director Agent call | INFO | latency_ms, output_tokens, success |
| Script Agent call | INFO | latency_ms, output_tokens, round_count, success |
| Visual Agent call | DEBUG | latency_ms, frame_count |
| Validation warning | WARNING | check_name, detail |
| Validation error | ERROR | check_name, detail, triggering_retry |
| Retry attempt | WARNING | attempt_number, reason |
| Fallback activated | ERROR | activity_type, all_errors |
| Session created | INFO | session_id, tier, scenario |
| Turn processed | INFO | session_id, round, response_type, consecutive_silence |
| Session ended | INFO | session_id, reason (completed/silence_exit/child_exit), total_turns |
| TTS call | DEBUG | text_length, latency_ms |

### 6.8 Database (db.py — SQLite via aiosqlite)

Lightweight persistence for sessions, conversation turns, and analytics. In-memory session state is the primary store; SQLite is the durable backup and analytics source.

```python
# db.py
import aiosqlite
from pathlib import Path

DB_PATH = "data/demo.db"

async def init_db():
    Path("data").mkdir(exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    tier TEXT NOT NULL,
    scenario TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    recipe_status TEXT DEFAULT 'ok',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    end_reason TEXT,
    total_turns INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS turns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    turn_number INTEGER NOT NULL,
    role TEXT NOT NULL,
    text TEXT,
    response_type TEXT,
    screen_widget TEXT,
    sfx_cue TEXT,
    latency_ms INTEGER,
    is_silent BOOLEAN DEFAULT FALSE,
    consecutive_silence INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id),
    agent TEXT NOT NULL,
    latency_ms INTEGER,
    success BOOLEAN,
    fallback_used BOOLEAN DEFAULT FALSE,
    input_tokens INTEGER,
    output_tokens INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_logs_session ON agent_logs(session_id);
""";
```

**Usage pattern:**

```python
# In server.py — on session start
async with aiosqlite.connect(DB_PATH) as db:
    await db.execute(
        "INSERT INTO sessions (session_id, tier, scenario) VALUES (?, ?, ?)",
        (session_id, tier, scenario)
    )
    await db.commit()

# In server.py — on each turn
async with aiosqlite.connect(DB_PATH) as db:
    await db.execute(
        "INSERT INTO turns (session_id, turn_number, role, text, response_type, ...) VALUES (?, ?, ...)",
        (session_id, turn_num, "ai", dialogue, response_type, ...)
    )
    await db.commit()

# In agents — log agent performance
async with aiosqlite.connect(DB_PATH) as db:
    await db.execute(
        "INSERT INTO agent_logs (session_id, agent, latency_ms, success, ...) VALUES (?, ?, ...)",
        (session_id, "director", latency, True, ...)
    )
    await db.commit()
```

**What the DB gives you:**
- Session replay: reconstruct any demo conversation from `turns` table
- Agent performance: which agents are slow, failing, falling back to defaults
- Usage analytics: how many sessions, average turns, common exit reasons
- Debug: when something goes wrong, full audit trail per session

---

## 7. API Endpoints

### POST /api/start

Starts a new activity session. Runs vision on the uploaded photo, then the full agent pipeline.

**Request:** `multipart/form-data`
```
photo: <file upload>        — The image the child photographed
tier: "T1"                  — Age tier
```

**Response:**
```json
{
  "session_id": "uuid",
  "vision_result": {
    "entity": "ladybug",
    "confidence": 0.95,
    "scene": "outdoor park",
    "features": ["red", "spotted", "insect", "on leaf"]
  },
  "recipe": { ... full ActivityRecipe ... },
  "first_turn": {
    "dialogue": "Oh WOW — a ladybug! Look at those beautiful little spots!",
    "tone": "gasping_delight",
    "screen_frame": { "widget": "photo_display", ... },
    "audio": { "sfx": "wonder_chime" }
  },
  "status": "ok"
}
```

**Logic:**
1. Receive uploaded photo
2. Call Vision API (Gemini Vision, see `refs/ref_vision.py`) → get entity, features, scene
3. Match vision result to a scenario (or use generic activity template if no exact match)
4. Create session in DB
5. Run full agent pipeline (Director → Script → Visual → Assemble), passing vision_result as context
6. The recipe contains ALL rounds pre-generated
7. Return vision_result + recipe + first turn (hook_line)

### POST /api/turn

Processes one child turn. Unlike Loop 1 (which re-called Gemini each turn), the demo uses the **pre-generated recipe** — the Script Agent already generated all rounds with branching paths.

**Request:**
```json
{
  "session_id": "uuid",
  "text": "It has lots of spots!",
  "is_silent": false
}
```

**Response:**
```json
{
  "turn": {
    "dialogue": "They are just everywhere! You're now a Polka-Dot Patrol Officer!",
    "tone": "excited",
    "screen_frame": { "widget": "progress_tracker", "widget_params": { "filled": 1, "total": 4 } },
    "audio": { "sfx": "mission_accepted" },
    "response_type": "on_correct"
  },
  "session_state": {
    "status": "active",
    "current_round": 1,
    "consecutive_silence": 0
  }
}
```

**Logic:**
1. Load session + recipe
2. Determine which round we're in
3. Match child's response to branching path:
   - If `is_silent` → use `on_silence` from current round
   - If text matches `correct_responses` → use `on_correct`
   - Else → use `on_incorrect`
4. Track consecutive silence
5. If `consecutive_silence >= 2` → return graceful exit (from recipe's `closing_speech` shortened, or a hardcoded warm goodbye)
6. Advance to next round
7. Return the matched response + corresponding screen frame

### POST /api/tts

**Request:** `{ "text": "...", "tier": "T0" }`
**Response:** audio/wav stream
**Logic:** Gemini TTS via Vertex AI, tier-adjusted voice settings. Fallback: return 204, frontend uses browser SpeechSynthesis.

---

## 8. Frontend: Split View Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  WonderLens Demo          [Tier: T0 ▾]  [Activity: ▾]  [New Session]│
├─────────────────────────────────┬────────────────────────────────────┤
│                                 │                                    │
│   CONVERSATION PANEL (~55%)     │   DEVICE SCREEN (~45%)             │
│                                 │                                    │
│   ┌───────────────────────┐     │   ┌──────────────────────────┐     │
│   │ 🤖 Oh WOW — a         │     │   │                          │     │
│   │ ladybug! Look at       │     │   │   [Active Widget Here]   │     │
│   │ those spots!           │     │   │                          │     │
│   │      ⌄ gasping_delight │     │   │                          │     │
│   └───────────────────────┘     │   └──────────────────────────┘     │
│           ┌───────────────────┐ │                                    │
│           │ It has lots       │ │   ┌──────────────────────────┐     │
│           │ of spots! 👦      │ │   │ 🔊 wonder_chime          │     │
│           └───────────────────┘ │   └──────────────────────────┘     │
│                                 │                                    │
│   ┌────────────────────┬──────┐ │   ┌──────────────────────────┐     │
│   │ Type here...       │ 🎤  │ │   │ ⟳ Retry (if error)       │     │
│   └────────────────────┴──────┘ │   └──────────────────────────┘     │
│   ⏱️ Silence: 6s / 10s          │                                    │
├─────────────────────────────────┴────────────────────────────────────┤
│  Round: 1/3  │  Latency: 580ms  │  Tier: T1  │  Status: active      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 9. Frontend: Interaction Flow

### Full Turn Cycle (Recipe-Based)

Unlike Loop 1 (which called Gemini per turn), the demo pre-generates the full recipe at session start. Each subsequent turn just looks up the correct branch from the pre-generated script:

```
1. Session starts:
   POST /api/start → receives full recipe (all rounds pre-generated)
   Show hook_line + first screen_frame
   Play TTS for hook_line
                    │
2. TTS finishes speaking → start silence timer
                    │
3. User types/speaks OR silence timer fires
                    │
4. POST /api/turn { text, is_silent }
   Backend matches response to branching path in recipe
   Returns matched dialogue + screen_frame + audio
   (NO Gemini call — just recipe lookup, ~5ms)
                    │
5. SIMULTANEOUSLY:
   ├── Left panel: add AI chat bubble
   ├── Right panel: render screen_frame from recipe
   ├── Audio: play sfx_cue
   └── TTS: speak dialogue
                    │
6. TTS finishes → start silence timer → wait for input
                    │
7. Repeat until all rounds done → show closing_speech + celebration_frame
```

**Key advantage**: after the initial /api/start call (~580ms), every subsequent turn is near-instant (~5ms) because it's just recipe lookup, not LLM generation.

### Silence Timer

```javascript
const SILENCE_TIMEOUTS = { T0: 10000, T1: 8000, T2: 6000 };

// Timer starts AFTER TTS finishes speaking
// Timer clears when user starts typing/speaking
// Timer fires → POST /api/turn { is_silent: true }
```

### Error/Retry UI

```
Normal flow:    Recipe loads → conversation flows smoothly
Retry flow:     /api/start fails → show "Oops! Let's try again" button
                User clicks → retry (up to 3x)
                After 3 fails → auto-load fallback recipe, show "Using backup mode" badge
Fallback flow:  Conversation works with pre-authored default recipe
                Subtle indicator that fallback is active (for demo reviewer, not child)
```

---

## 10. Age-Tier Rules (3 tiers)

From `tier_rules.yaml` (tested in Loop 1):

| Parameter | T0 (2-4) | T1 (4-6) | T2 (6-8) |
|---|---|---|---|
| Words/sentence | 5-10 | 10-15 | 15-20 |
| Max sentences/turn | 2 | 3 | 4 |
| Hook rule | Personal feeling | Experience/preference | Opinion/connection |
| Closing concepts | 1 | 2 | Up to 3 |
| Response style | Simple, playful | Curious, encouraging | Conversational, peer |
| Silent timeout | 10s | 8s | 6s |
| Round count | 2-4 | 3-5 | 3-5 |

---

## 11. Consecutive Silence & Exit

**Backend** tracks `consecutive_silence` per session:
- Child responds → reset to 0
- Silent → increment
- Count reaches 2 → return graceful exit response (warm goodbye, celebrate what was done, tomorrow hook, NO concepts)

**Frontend**: when `session_state.status` changes to `"exited"`, disable input, show "Session ended — [New Session] button".

---

## 12. Files from Loop 1 to Reuse

| Loop 1 File | Destination in Demo | Notes |
|---|---|---|
| `system_prompt.md` (optimized) | `backend/skills/script.md` (base content) | Battle-tested hook rule, tier rules, closing structure |
| `tier_rules.yaml` | `backend/tier_rules.yaml` | 3-tier system, validated |
| `scenarios/*.yaml` | `backend/scenarios/` | Activity definitions + detailed_interaction_script |
| `few_shot.md` | `backend/skills/few_shot.md` | Script Agent few-shot examples |
| `activity_context_template.md` | `backend/skills/activity_context_template.md` | Context injection template |
| `simulate.py` functions | `backend/agents/*.py` | Reuse: `build_tier_constraints()`, `call_gemini()`, Vertex AI client setup |

---

## 13. Fallback Recipes

Pre-authored default recipes for each demo activity. These are the "safe" versions that work without LLM generation. Build from the scenario YAML's `detailed_interaction_script` — manually convert to the ActivityRecipe JSON format.

Each fallback has:
- Generic hook_line that works for the entity category
- 3 rounds with branching (correct/incorrect/silence)
- Closing speech with correct tier concept count
- Screen frames with appropriate widgets
- Celebration frame

### Backend Python Dependencies (pyproject.toml)

```toml
[project]
name = "wonderlens-activity-demo"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.20.0",
    "google-genai>=1.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "aiosqlite>=0.19.0",
    "pyyaml>=6.0",
    "python-dotenv>=1.0.0",
]
```

---

## 14. Build Order

1. **Set up repo structure** — directories, copy Loop 1 files, install deps
2. **Build config** — `config.py` (Pydantic BaseSettings) + `config.yaml` (app defaults)
3. **Build logger** — `logger.py` (structured logging with event types)
4. **Build database** — `db.py` (aiosqlite, schema init, sessions/turns/agent_logs tables)
5. **Create skill files** — write `skills/director.md`, `skills/script.md`, `skills/visual.md`, `skills/assembler.md` (content defined in Section 5 above)
6. **Define Pydantic schemas** — CompositionPlan, VoiceScript, VisualComposition, ActivityRecipe
7. **Build Director Agent** — loads `skills/director.md` as system prompt, Gemini JSON mode, default plan fallback, logs to agent_logs
8. **Build Script Agent** — loads `skills/script.md` as system prompt, Gemini JSON mode, branching output, logs to agent_logs
9. **Build Visual Agent** — implements rules from `skills/visual.md`, no LLM call, logs to agent_logs
10. **Build Recipe Assembler** — implements rules from `skills/assembler.md`, merge + validate + retry (3x → fallback), logs all validation results
11. **Build fallback recipes** — 2 pre-authored JSON files in `fallbacks/`
12. **Build FastAPI endpoints** — /api/start, /api/turn, /api/tts (all write to sessions/turns DB)
13. **Test backend** — `uv run uvicorn server:app --reload`, test with curl, verify DB populated
14. **Scaffold frontend** — Vite + React + Tailwind
15. **Build App.jsx** — split view layout
16. **Build ConversationPanel** — chat bubbles, input, photo selector
17. **Build DeviceScreen** — widget switcher
18. **Build 5 priority widgets** — PhotoDisplay, ProgressTracker, CharacterDisplay, PhotoGrid, BadgeAward
19. **Build useConversation hook** — API client, recipe state, turn matching
20. **Build useSilenceTimer** — tier-specific timeout
21. **Build retry/fallback UI** — retry button, fallback indicator
22. **Build useSpeechRecognition** — mic button
23. **Build useTTS** — Gemini TTS or browser fallback
24. **Wire everything end-to-end**
25. **Polish** — animations, transitions, loading states

---

## 15. Running Locally

```bash
# Terminal 1: Backend
cd wonderlens-demo/backend
cp .env.example .env   # Fill in Vertex AI credentials
uv sync
uv run uvicorn server:app --reload --port 8000

# Terminal 2: Frontend  
cd wonderlens-demo/frontend
npm install
npm run dev   # Vite on port 5173

# Open http://localhost:5173
# Select a photo, pick a tier, start the conversation
```

---

## 16. What NOT to Build

- Camera/photo capture (user uploads or selects from preloaded photos)
- Parent app / parent reports
- User accounts / persistence
- Multi-session continuity
- kidSAFE compliance UI
- Asset Factory
- All 35 activity types (just 2 for demo)
- Audio Agent (folded into Script Agent sfx_cue)
- Interaction Agent (folded into Script Agent branching)

---

## 17. Reference Documents

| Doc | What to Read |
|---|---|
| `docs/wonderlens_activity_reference_v4.html` | Widget types, animation presets |
| `docs/age-tier-guidance-dashboard.html` | Tier parameters (source for tier_rules.yaml) |
| `docs/WonderLens_activity_design_0307.docx` | Activity design examples |

---

*End of bootstrap — ready to build.*
