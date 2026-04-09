# Scene-by-Scene Story Images + Achievement Image — Design Spec

## Context

The edu team wants richer visual feedback in Cat5 games:
1. **Story scenes with companion images** — During synthesis, deliver the story scene-by-scene with a generated watercolor illustration for each scene, instead of narrating the whole story at once
2. **Achievement summary image** — After all tasks, generate a custom illustration showing all collected characters together, not just static badges

Both features share an Imagen 3 image generation layer via Vertex AI.

## Architecture Overview

```
Synthesis "generate" phase:
  1. LLM generates structured 3-scene story (JSON with narration + image prompts)
  2. 4 Imagen 3 calls in parallel (3 scene images + 1 achievement image)
  3. Store base64 images in session state
  4. Show animated loading mascot while generating (~5-10s)
  
Scene delivery (new phases: scene_1, scene_2, scene_3):
  Each scene = one auto-advance turn:
    - TTS narrates the scene text
    - Device screen shows watercolor illustration via new StoryScene widget
    - Auto-advance to next scene when TTS finishes
  After last scene → STEP_5_CELEBRATE

Celebrate step:
  - Show photo_recall_grid briefly (2-3s)
  - Transition to achievement_image widget (generated illustration of all characters)
```

---

## Feature 1: Image Generation Infrastructure

### New module: `backend/image_gen.py`

Follows the same dual-auth pattern as `tts.py` and `stt.py`:
- If `google_cloud_project` set → Vertex AI client
- Otherwise → API key client
- Model: `imagen-3.0-generate-002` (Imagen 3 via Vertex AI)

**Functions:**
- `generate_image(prompt: str, aspect_ratio: str = "16:9") → bytes | None` — single Imagen call, returns PNG bytes or None on failure
- `generate_scene_images(scenes: list[dict]) → list[bytes | None]` — parallel generation via `asyncio.gather`
- Retry: 2 attempts per image, graceful fallback to None

**Imagen prompt template:**
```
Soft watercolor children's storybook illustration. {scene_description}. 
Gentle pastel tones, warm lighting, no text or words in the image.
```

**Image delivery:** Base64-encoded strings in API response. Frontend renders as `data:image/png;base64,...` data URLs. No file storage needed.

### Config additions (`backend/config.py`):
- `imagen_model: str = "imagen-3.0-generate-002"` — configurable model name
- `imagen_enabled: bool = True` — feature flag to disable image gen

---

## Feature 2: Scene-by-Scene Synthesis

### Modified story generation

**Step instruction changes** (`cat5_step4_synthesis__story_generation.md`):
- Story must be output as structured JSON with exactly 3 scenes
- Each scene: `{narration: str, image_description: str}`
- Plus an `achievement_description` for the final celebration image
- Scene narration lengths: T0 = 2-3 sentences, T1 = 3-4 sentences, T2 = 4-5 sentences per scene

**Schema: `StructuredStory`** (new Pydantic model in `backend/schemas/`):
```python
class StoryScene(BaseModel):
    narration: str
    image_description: str
    image_base64: str | None = None

class StructuredStory(BaseModel):
    scenes: list[StoryScene]  # exactly 3
    achievement_description: str
    achievement_image_base64: str | None = None
```

### Modified synthesis flow (`backend/turn_handling/synthesis.py`)

**When `synthesis_phase == "generate"`:**
1. Generate structured story via LLM (Script Agent with modified prompt)
2. Kick off 4 parallel Imagen calls (3 scenes + 1 achievement)
3. Store `StructuredStory` in session state
4. Set `synthesis_phase = "scene_1"` 
5. Return loading response: dialogue = "[excited] Ooh, let me think of a story about {characters}..." with widget = `story_loading`

**New phases `scene_1`, `scene_2`, `scene_3`:**
- Each returns one scene's narration as dialogue + scene image as widget data
- Screen widget: `story_scene` with `{image_base64, scene_number, total_scenes}`
- `auto_advance: true` — frontend advances to next scene after TTS finishes
- After `scene_3`: advance to STEP_5_CELEBRATE

### Turn Director changes (`backend/agents/turn_director.py`)

Scene delivery is **deterministic** — no Turn Director involvement needed. The turn handler serves pre-generated scenes directly, similar to how deterministic photo prompts work in collection. The Turn Director only handles the interactive invite/evaluate phases.

### Session state additions (`backend/schemas/session_state.py`):
- `structured_story: StructuredStory | None = None`
- `current_scene: int = 0` (0 = not started, 1-3 = delivering scenes)

---

## Feature 3: Achievement Summary Image

### Generation
Already generated during synthesis phase 2 (in parallel with scene images). Stored in `structured_story.achievement_image_base64`.

### Display at STEP_5_CELEBRATE

**Sequence:**
1. `photo_recall_grid` widget shown first (2-3s) — the child's actual collected photos
2. Transition to `achievement_image` widget — the Imagen-generated watercolor illustration
3. TTS plays celebration speech over both transitions

**Fallback:** If achievement image generation failed, stay on `photo_recall_grid`.

### Step instruction changes (`cat5_step5_celebrate.md`):
- Screen widget: `achievement_image` (falls back to `photo_recall_grid` if no image available)

---

## Feature 4: Animated Loading State

### New widget: `StoryLoading` (`frontend/src/widgets/StoryLoading.jsx`)

Shown while Imagen generates images (~5-10s):
- The activity's entity character with a gentle "thinking" CSS animation (floating/bobbing)
- Text: "Creating your story..." with animated dots
- Soft background matching the activity's theme colors
- Uses existing `CharacterDisplay` entity image as the mascot base

### Conversation panel during loading:
- AI message: "[excited] Ooh, let me think of a story about {characters}..."
- This is the `dialogue` returned by the generate phase

---

## Frontend Changes

### New widgets:
1. **`StoryScene.jsx`** — Full-width watercolor illustration with scene counter
   - Props: `image_base64`, `scene_number`, `total_scenes`
   - Fade-in animation on mount
   - Scene counter badge: "1 of 3"

2. **`StoryLoading.jsx`** — Animated loading with entity mascot
   - Props: `entity` (for mascot image)
   - Floating/bobbing CSS animation
   - "Creating your story..." text with animated dots

3. **`AchievementImage.jsx`** — Generated achievement illustration
   - Props: `image_base64`, `title` (role title), `characters` (names)
   - Fade-in from photo_recall_grid
   - Role title overlaid at top, character names at bottom

### DeviceScreen.jsx changes:
- Register 3 new widgets in `WIDGET_MAP`: `story_scene`, `story_loading`, `achievement_image`
- Import the 3 new components

### Auto-advance logic:
- `useSessionOrchestration.js` or `App.jsx` needs to detect scene turns and auto-advance after TTS completes
- Pattern: when `auto_advance: true` in API response, trigger next `/api/turn` call after speaking done

---

## Files Affected

| Area | Files |
|------|-------|
| New: image gen module | `backend/image_gen.py` |
| New: structured story schema | `backend/schemas/structured_story.py` |
| Config | `backend/config.py` (imagen_model, imagen_enabled) |
| Synthesis flow | `backend/turn_handling/synthesis.py` |
| Session state | `backend/schemas/session_state.py` |
| Step instructions | `cat5_step4_synthesis.md`, `cat5_step4_synthesis__story_generation.md`, `cat5_step5_celebrate.md` |
| Server | `backend/server.py` (pass image data in response) |
| New: frontend widgets | `StoryScene.jsx`, `StoryLoading.jsx`, `AchievementImage.jsx` |
| Frontend registry | `frontend/src/components/DeviceScreen.jsx` |
| Frontend orchestration | `frontend/src/hooks/useSessionOrchestration.js` or `App.jsx` (auto-advance) |

## Out of Scope
- Cat1 games (no collection/synthesis, so no scene images)
- Persistent image storage (images are ephemeral per session)
- Image caching across sessions
- Custom art styles per activity (single "soft watercolor" style for now)

## Verification
1. Start a Cat5 game (e.g., fluffy_expedition_dandelion)
2. Complete 3 collection rounds
3. Enter synthesis → see loading animation with entity mascot
4. Story delivers scene-by-scene: narration plays, watercolor image appears per scene
5. After 3 scenes → celebrate step shows photo recall, then achievement illustration
6. If Imagen is unavailable: story still delivers (text-only), celebrate shows photo_recall_grid
7. `uv run pytest` — all existing tests still pass
8. `npx vite build` — frontend builds clean
