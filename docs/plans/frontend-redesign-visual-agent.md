# Frontend Redesign + LLM Visual Agent

## Context

The current frontend uses a dark glassmorphic left/right split layout with small widgets, emoji icons, and no sound effect display. The Visual Agent is rule-based with fixed widget mappings. This redesign transforms the UI into a child-friendly cartoon nature/explorer theme with a top/bottom layout, toy camera device frame, larger SVG-based widgets, visible SFX indicators, category-grouped landing page, and an LLM-powered Visual Agent for context-aware visuals.

**Requirements:**
1. Landing page shows activities grouped by category (Cat1 vs Cat5)
2. Sound effects displayed visually with human-readable labels
3. Widgets and animations are larger and use natural language descriptions
4. Visual Agent becomes LLM-based for context-aware widget/animation/SFX generation
5. Top/bottom split layout with toy camera device frame
6. Cartoon nature/explorer style with SVG icons (no emoji)

**Design choices:**
- Camera style: Toy camera (chunky, Fisher-Price style)
- Layout: Camera top (~42%), conversation bottom (~58%)
- Color palette: Nature/explorer (Forest Green #4CAF50, Sky Blue #87CEEB, Warm Brown #8D6E63, Sunflower #FFC107, Ocean Teal #26A69A)
- Backend scope: Full stack — Visual Agent becomes LLM-based

---

## Phase 1: Backend — LLM-Based Visual Agent + Schema Enrichment

**Goal:** Convert Visual Agent from rule-based to LLM-based, add human-readable label fields to ScreenFrame, store generated frames in session state.

### 1.1 Schema changes — `backend/schemas/visual_composition.py`
Add to `ScreenFrame`:
- `sfx_cue: str | None = None` — sound effect ID
- `sfx_label: str | None = None` — e.g. "A magical wonder chime"
- `animation_label: str | None = None` — e.g. "A gentle sparkle highlights the photo"
- `widget_label: str | None = None` — e.g. "Your adventure photo"

### 1.2 Visual Agent prompt — create `backend/prompts/visual_system.md`
Instructs Gemini 2.0 Flash to generate a `VisualComposition` based on:
- Input: entity, activity_type, emotional_arc, screen_strategy, round_count, scene, key_concepts
- Output: list of ScreenFrame with context-aware widget selection, natural-language labels, and appropriate SFX cues
- Constrain widget choices to: `photo_display | character_display | progress_tracker | photo_grid | badge_award`
- Constrain SFX to known set: `wonder_chime | scene_woosh | celebration_fanfare | photo_shutter_click | slot_fill_chime | mission_accepted | mission_complete_fanfare | badge_awarded | excitement_rising | game_start_chime`

### 1.3 Rewrite Visual Agent — `backend/agents/visual_agent.py`
- Make `run()` async, call Gemini via OpenAI client (same pattern as `DirectorAgent`)
- Use `response_format=VisualComposition` for Pydantic JSON mode
- Keep current rule-based logic as `_rule_based_fallback()` for when LLM fails
- Validate output: widget names and sfx_cue values must be in allowed sets
- Timeout: 5 seconds

### 1.4 Pipeline integration — `backend/agents/pipeline.py`
- Import and instantiate `VisualAgent`
- After Director returns plan, run Visual Agent in parallel with Script Agent's hook turn:
  ```python
  visual_task = asyncio.create_task(visual_agent.run(plan, context))
  script_task = asyncio.create_task(script_agent.generate_turn(state))
  visual_result, first_turn = await asyncio.gather(visual_task, script_task)
  ```
- Store result: `state.visual_frames = visual_result.screen_frames`, `state.celebration_frame = visual_result.celebration_frame`

### 1.5 Session state — `backend/schemas/session_state.py`
Add fields to `SessionStateModel`:
- `visual_frames: list[ScreenFrame] = Field(default_factory=list)`
- `celebration_frame: ScreenFrame | None = None`

### 1.6 State machine + server — `backend/state_machine.py`, `backend/server.py`
- `get_screen_frame()`: add `visual_frames: list[ScreenFrame] | None = None` parameter. If provided, match by trigger first (e.g. `on_round_2` for `STEP_3_ROUND_2`). Fall back to current hardcoded logic.
- `server.py` `_build_turn_response()`: include `sfx_label` in the `audio` dict. The `screen_frame.model_dump()` will already include the new label fields.
- All call sites of `get_screen_frame()` in `server.py` (lines 235, 302, 396, 528): pass `state.visual_frames`

### 1.7 SFX fallback labels — `backend/agents/visual_agent.py`
```python
SFX_LABELS = {
    "wonder_chime": "A magical wonder chime",
    "scene_woosh": "Scene transition whoosh",
    "celebration_fanfare": "Celebration fanfare",
    "photo_shutter_click": "Camera shutter click",
    "slot_fill_chime": "Collection slot filled",
    "mission_accepted": "Mission accepted fanfare",
    "mission_complete_fanfare": "Mission complete celebration",
    "badge_awarded": "Badge awarded sparkle",
    "excitement_rising": "Excitement rising",
    "game_start_chime": "Game start chime",
}
```
Used by `_rule_based_fallback()` to populate `sfx_label` when LLM isn't used.

### Verification
```bash
cd backend && uv run ruff check . && uv run ruff format . && uv run mypy . && uv run pytest
```
Manual test: `POST /api/start` returns screen frames with label fields populated.

---

## Phase 2: Frontend — Theme Foundation + SVG Icons

**Goal:** Replace dark glassmorphic theme with nature/explorer cartoon style. Create SVG icon system. No emoji anywhere.

### 2.1 CSS theme overhaul — `frontend/src/index.css`
- Replace `bg-mesh` dark gradient with light sky/nature background (sky blue gradient with subtle cloud shapes)
- Replace `.glass` / `.glass-strong` / `.glass-subtle` with:
  - `.surface-primary`: white bg, `border: 2px solid #4CAF50`, rounded-2xl
  - `.surface-card`: off-white `#FFF8E1`, subtle shadow
  - `.surface-accent`: sky blue tint
- Add CSS custom properties:
  ```css
  --color-forest: #4CAF50;
  --color-sky: #87CEEB;
  --color-brown: #8D6E63;
  --color-sunflower: #FFC107;
  --color-teal: #26A69A;
  ```
- Add larger animation keyframes: `sparkle-large`, `celebration-large`, `slide-up-large`
- Add `.border-vine` decorative class

### 2.2 SVG icon components — create `frontend/src/icons/`
Create individual SVG React components (inline SVG, no external deps):

| Component | Replaces |
|-----------|----------|
| `CameraIcon.jsx` | camera emoji in TopBar |
| `CompassIcon.jsx` | AI avatar emoji in ChatBubble |
| `BinocularsIcon.jsx` | Cat1 category icon |
| `MagnifyingGlassIcon.jsx` | Cat5 category icon |
| `BadgeIcon.jsx` | trophy emoji in BadgeAward |
| `StarIcon.jsx` | star/sparkle emoji in BadgeAward |
| `CheckmarkIcon.jsx` | checkmark in ProgressTracker |
| `SpeakerIcon.jsx` | new SFX indicator |
| `PhotoFrameIcon.jsx` | camera emoji fallback |
| `DogIcon.jsx` | dog emoji on landing |
| `CatIcon.jsx` | cat emoji on landing |
| `DinosaurIcon.jsx` | dinosaur emoji on landing |
| `LadybugIcon.jsx` | ladybug emoji on landing |
| `DandelionIcon.jsx` | dandelion emoji on landing |
| `LeafIcon.jsx` | decorative leaf/vine element |
| `index.js` | barrel export |

Each follows: `export default function XIcon({ className = "w-6 h-6", ...props })`

### Verification
`npm run dev` — app loads with new colors, no emoji visible. Visual inspection.

---

## Phase 3: Frontend — Layout + Toy Camera Frame

**Goal:** Change from left/right to top/bottom split. Wrap device screen in toy camera SVG frame.

### 3.1 Toy camera frame — create `frontend/src/components/ToyCameraFrame.jsx`
- SVG-based cartoon toy camera body wrapping `{children}`
- Chunky rounded shape with Forest Green body, Sunflower shutter button, Warm Brown viewfinder circle
- Central viewport where children render (rounded-2xl, overflow-hidden)
- Decorative: grip texture right side, small "WonderLens" text, lens ring
- Responsive: fills container width, maintains aspect ratio

### 3.2 Layout restructure — `frontend/src/App.jsx`
```jsx
<main className="flex flex-col flex-1 overflow-hidden p-3 gap-3">
  {/* TOP ~42% — Device Screen in Toy Camera */}
  <section className="h-[42%] flex-shrink-0">
    <ToyCameraFrame>
      {showPhotoGallery ? <PhotoGallery /> : <DeviceScreen />}
    </ToyCameraFrame>
  </section>

  {/* BOTTOM ~58% — Conversation */}
  <section className="flex-1 min-h-0 flex flex-col surface-primary rounded-3xl overflow-hidden">
    {showPhotoSelector ? <PhotoSelector /> : <ConversationPanel />}
  </section>
</main>
```
- Remove all `md:flex-row`, `md:w-[55%]`, `md:w-[45%]` responsive breakpoints
- Update TopBar and footer to match new theme

### 3.3 TopBar — `frontend/src/components/TopBar.jsx`
- Replace indigo/purple with Forest Green gradient
- Use `CameraIcon` SVG, leaf accents
- Nature-themed tier selector and session button

### 3.4 Footer — inline in `App.jsx`
- Green accent, nature card style, SVG status indicators

### Verification
Visual check at common viewport sizes. Camera frame visible with content inside. No overflow issues.

---

## Phase 4: Frontend — Bigger Widgets + SFX Display

**Goal:** Make widgets much larger with natural-language labels. Show SFX cues visually.

### 4.1 SFX indicator — create `frontend/src/components/SfxIndicator.jsx`
- Props: `{ sfxCue, sfxLabel }`
- Renders a pill/badge: `SpeakerIcon` + sfxLabel text
- Teal background, white text, animated entrance (fade + slide)
- Frontend fallback map for label generation if backend doesn't provide one:
  ```javascript
  const SFX_LABELS = { wonder_chime: "Magical wonder chime", ... }
  ```
- Auto-hides after 3s or on next frame change

### 4.2 DeviceScreen integration — `frontend/src/components/DeviceScreen.jsx`
- Render `SfxIndicator` below widget area, fed from `screenFrame.sfx_cue` and `screenFrame.sfx_label`
- Show `widget_label` as descriptive header above widget
- Show `animation_label` as subtle annotation
- Replace debug footer (raw variable names) with human-readable labels

### 4.3 Widget enlargements

**PhotoDisplay.jsx** — `w-64 h-64` -> `w-full max-w-md aspect-square`. Replace camera emoji with `PhotoFrameIcon`. Nature-themed border.

**ProgressTracker.jsx** — `w-16 h-16` circles -> `w-20 h-20`. `CheckmarkIcon` SVG. Forest Green filled, Sky Blue empty. Larger description text.

**CharacterDisplay.jsx** — `max-w-sm` -> `max-w-lg w-full`. Remove `ROUND_EMOJIS` array entirely. Use themed SVG icons (compass, binoculars, magnifying glass, leaf, star) per round. Explorer palette colors.

**PhotoGrid.jsx** — `w-28 h-28` -> `w-36 h-36`. `PhotoFrameIcon` placeholder. Vine border accents.

**BadgeAward.jsx** — `w-32 h-32` -> `w-44 h-44`. `BadgeIcon` + `StarIcon` SVGs. Sunflower + Forest Green gradient. Explorer badge aesthetic.

**AnimationOverlay.jsx** — Map to larger animation classes. Add CSS particle overlay effects for sparkle/celebration.

### Verification
All widgets render larger inside camera frame. SFX pill visible during sessions. No emoji anywhere.

---

## Phase 5: Frontend — Landing Page Categories

**Goal:** Group activities by category on photo selection screen.

### 5.1 PhotoSelector redesign — `frontend/src/components/PhotoSelector.jsx`
Replace flat `DEMO_PHOTOS` array with categorized structure:
```javascript
const CATEGORIES = [
  {
    id: 'cat1',
    title: 'In-Device Verbal',
    subtitle: 'Imagine stories with your photo friend!',
    Icon: BinocularsIcon,
    photos: [
      { id: 'dog', label: 'Stuffed Dog', src: '/photos/dog.jpg', Icon: DogIcon },
      { id: 'cat', label: 'Cat', src: '/photos/cat.jpg', Icon: CatIcon },
      { id: 'dinosaur', label: 'Dinosaur', src: '/photos/dinosaur.jpg', Icon: DinosaurIcon },
    ],
  },
  {
    id: 'cat5',
    title: 'Out-of-Device Collection',
    subtitle: 'Go on a real-world scavenger hunt!',
    Icon: MagnifyingGlassIcon,
    photos: [
      { id: 'ladybug', label: 'Ladybug', src: '/photos/ladybug.jpg', Icon: LadybugIcon },
      { id: 'dandelion', label: 'Dandelion', src: '/photos/dandelion.jpg', Icon: DandelionIcon },
    ],
  },
];
```
- Category headers with SVG icon + title + description
- Larger photo cards (128-160px) with SVG icon fallback
- Leaf/vine divider between categories
- Upload zone matches nature theme
- Remove all `fallbackEmoji` references

### Verification
Landing page shows two category sections. SVG fallbacks work. Upload zone themed.

---

## Phase 6: Frontend — Theme Consistency Pass

**Goal:** Update remaining components to match nature/explorer theme.

### Files to update:
- `ChatBubble.jsx` — Green compass SVG avatar (replace emoji), nature-themed bubble colors
- `ConversationPanel.jsx` — Green/teal accents, nature empty state, themed typing indicator
- `TextInput.jsx` — Green-themed input, Teal mic button
- `RetryButton.jsx` — Nature-themed retry styling
- `PhotoGallery.jsx` — Larger elements, SVG icons, vine borders

---

## Files Summary

### New files (19)
- `backend/prompts/visual_system.md`
- `frontend/src/icons/` — 15 SVG components + `index.js`
- `frontend/src/components/ToyCameraFrame.jsx`
- `frontend/src/components/SfxIndicator.jsx`

### Modified files (21)
| File | Changes |
|------|---------|
| `backend/schemas/visual_composition.py` | Add 4 label fields to ScreenFrame |
| `backend/agents/visual_agent.py` | Rewrite to async LLM-based + fallback |
| `backend/agents/pipeline.py` | Run Visual Agent in parallel, store frames |
| `backend/schemas/session_state.py` | Add visual_frames, celebration_frame |
| `backend/state_machine.py` | get_screen_frame() accepts visual_frames |
| `backend/server.py` | Pass visual_frames, include sfx_label in response |
| `frontend/src/index.css` | Full theme overhaul |
| `frontend/src/App.jsx` | Top/bottom layout, ToyCameraFrame |
| `frontend/src/components/TopBar.jsx` | Nature theme |
| `frontend/src/components/DeviceScreen.jsx` | SFX indicator, labels, larger |
| `frontend/src/components/PhotoSelector.jsx` | Category grouping, SVG |
| `frontend/src/components/ConversationPanel.jsx` | Theme |
| `frontend/src/components/ChatBubble.jsx` | SVG avatar, theme |
| `frontend/src/components/TextInput.jsx` | Theme |
| `frontend/src/components/PhotoGallery.jsx` | Theme, larger |
| `frontend/src/widgets/PhotoDisplay.jsx` | Larger, SVG |
| `frontend/src/widgets/ProgressTracker.jsx` | Larger, SVG |
| `frontend/src/widgets/CharacterDisplay.jsx` | Remove emoji, SVG, larger |
| `frontend/src/widgets/PhotoGrid.jsx` | Larger, SVG |
| `frontend/src/widgets/BadgeAward.jsx` | SVG badge, larger |
| `frontend/src/widgets/AnimationOverlay.jsx` | Larger animations |

---

## End-to-End Verification

1. **Backend**: `cd backend && uv run ruff check . && uv run ruff format . && uv run mypy . && uv run pytest`
2. **Frontend**: `cd frontend && npm run dev`
3. **Manual flow**: Open http://localhost:5173 -> verify landing page shows 2 categories with SVG icons -> select a photo -> verify toy camera frame renders at top -> verify widgets are large with labels -> verify SFX indicator appears -> complete a session -> verify badge uses SVG
4. **Check**: No emoji anywhere in the rendered UI
5. **Check**: Screen frames in API responses include `sfx_label`, `widget_label`, `animation_label`
