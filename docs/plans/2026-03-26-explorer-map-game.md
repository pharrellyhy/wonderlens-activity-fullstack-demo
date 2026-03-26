# Explorer's Map: Transform Cat 5 into an Interactive Canvas Game

## Context

The Cat 5 (Out-of-Device Collection) activities currently feel like "talking to an AI assistant" — the device screen shows static widgets (ProgressTracker circles, PhotoDisplay, PhotoGrid, BadgeAward) while the child interacts via voice. The goal is to transform the entire Cat 5 experience into an interactive game where the device screen becomes a **living, explorable map** that grows and responds as the child collects items. The AI voice becomes a character inside the game world, not an assistant narrating from outside.

**Scope**: Cat 5 activities only (fluffy_expedition_dandelion, polka_dot_patrol). Cat 1 activities are completely unaffected.

---

## Game Design

### Step-by-Step Experience

| Step | Current (Widgets) | New (Explorer's Map) |
|------|-------------------|---------------------|
| **HOOK** | Static photo with sparkle | Photo shrinks into entity character on a stylized map. Fog covers 3 mystery zones. Tap entity to hear it giggle. |
| **MISSION** | Character display | Map zooms out, 3 foggy zones pulse gently. Dotted path appears from entity to first zone. Compass animates in corner. |
| **COLLECT Phase A** | PhotoGallery modal overlay | *PhotoGallery modal unchanged* — this is the real-world bridge. Map visible beneath. |
| **COLLECT Phase A done** | Photo display | Fog lifts on one zone (reveal animation). Collected item appears as character sprite. Terrain grows (grass, flowers). |
| **COLLECT Phase B** | Photo display | New character bounces/waves. Child answers detail question via voice. After AI names it, name label appears above character with celebration animation. |
| **SYNTHESIS** | Static photo grid | All fog cleared. Characters walk/bounce toward center. Connection lines draw between them. Map "comes alive" — colors shift, particles burst as AI tells the story. |
| **CELEBRATE** | Static badge | Badge overlays the map with collected characters circling it. Confetti particles on tap. |
| **CLOSING** | Static badge | Complete vibrant world. Sunset color shift. Characters wave goodbye. |

### Interactivity (Tier-Appropriate)
- **T0 (2-4)**: Tap characters to bounce + SFX. Tap fog zones to see gentle pulse.
- **T1 (4-6)**: Same as T0. Touch interactions are optional — never block voice-first flow.
- All interactions are **discovery-based** — things respond when touched, no "Tap here!" instructions.

---

## Architecture

### Principle
Backend sends **target state** (what should be visible). Frontend **animates toward it**. No animation data in the recipe — the canvas figures out transitions client-side.

### New Files (Frontend — 6 files)

| File | Purpose |
|------|---------|
| `frontend/src/canvas/ExplorerMap.jsx` | Top-level React component. Owns `<canvas>`, ResizeObserver, pointer events. Receives `screenFrame.widget_params` as props. |
| `frontend/src/canvas/useGameEngine.js` | Custom hook: game loop (rAF), animation queue, state diffing, particle system coordination. Exposes imperative `engine` ref. |
| `frontend/src/canvas/sprites.js` | Pure draw functions: `drawBackground`, `drawFogZone`, `drawCharacter`, `drawPath`, `drawNameLabel`, `drawParticles`, `drawBadge`. No React dependency. |
| `frontend/src/canvas/mapLayout.js` | Position computation using fractional coordinates (0-1) so layout scales to any canvas size. `computeZonePositions`, `computeCharacterPosition`. |
| `frontend/src/canvas/animations.js` | Animation presets: `fogReveal`, `characterAppear`, `characterBounce`, `pathDraw`, `confettiRain`, `connectionDraw`, `badgeTransform`, `sunsetShift`. Each is `{ duration, easing, update(t, ctx, target) }`. |
| `frontend/src/canvas/particleSystem.js` | Lightweight emitter for confetti, sparkles, leaves. ~50 particle cap. `emit(type, x, y, count)`, `update(dt)`, `draw(ctx)`. |

### New Files (Backend — 1 file)

| File | Purpose |
|------|---------|
| `backend/schemas/explorer_map.py` | Pydantic model `ExplorerMapState` — the game state payload inside `ScreenFrame.widget_params`. |

### `ExplorerMapState` Schema

```python
class ExplorerMapState(BaseModel):
    game_phase: Literal[
        "hook", "mission",
        "collect_photo", "collect_reveal", "collect_detail", "collect_named",
        "synthesis", "celebrate", "closing",
    ]
    entity_id: str                     # e.g. "dandelion"
    entity_image: str                  # path to entity PNG
    revealed_zones: list[int]          # indices of zones with fog cleared
    characters: list[dict]             # [{id, name, image, zone_index}]
    active_zone: int | None = None     # zone currently animating
    total_zones: int = 3
    animation_cue: str | None = None   # which animation to trigger
    collected_count: int = 0
    badge_title: str = ""
    badge_concepts: list[str] = []
```

### Modified Files

| File | Change |
|------|--------|
| `frontend/src/components/DeviceScreen.jsx` | Add `explorer_map: ExplorerMap` to `WIDGET_MAP`. Add `game_phase` to `getFrameKey`. Pass `isSpeaking` prop through. |
| `frontend/src/App.jsx` | Thread `isSpeaking` down to `DeviceScreen` (already available from `useSessionOrchestration`). |
| `frontend/src/index.css` | Add `--motion-ok` CSS variable for canvas to read `prefers-reduced-motion`. |
| `backend/state_machine.py` | Replace Cat 5 widget returns with `explorer_map` widget + `ExplorerMapState` params. New helper `_build_explorer_map_params(state, game_phase)`. Affects lines 223-334 (Cat 5 branches). |
| `backend/agents/visual_agent.py` | Add `"explorer_map"` to `ALLOWED_WIDGETS`. |
| `backend/turn_handler.py` | Include `collected_names` and `collected_details` in state context dict so `get_screen_frame` can build character data. |

### Canvas Rendering (Single Canvas, Paint Order)

1. Background gradient (entity theme colors)
2. Terrain elements (procedural — circles, arcs for grass/flowers)
3. Fog zones (semi-transparent blobs, opacity tweened by `fogReveal` animation)
4. Dotted paths (`ctx.setLineDash`)
5. Character sprites (PNGs from `/public/icons/`, drawn with bounce/float transforms)
6. Name labels (rounded-rect + text above characters)
7. Connection lines (animated bezier curves during synthesis)
8. Particles (confetti, sparkles, leaves — always on top)
9. UI hints (pulsing circles on tappable elements)

Canvas sizes to container via ResizeObserver + `devicePixelRatio` scaling. Max height ~352px.

### Integration Points

- **SFX**: Existing `DeviceScreen` SFX logic plays `screenFrame.sfx_cue` — no changes needed. Backend sets cues per phase.
- **TTS**: `isSpeaking` prop triggers synthesis animations when AI starts speaking. No frame-accurate sync needed.
- **PhotoGallery**: Unchanged — still overlays during Phase A (`showPhotoGallery` condition in App.jsx already handles this).
- **Cat 1 isolation**: `explorer_map` widget only returned for `template_type == "cat5"`. Cat 1 code paths untouched.

---

## Implementation Sequence

### Phase 1: Foundation (Static Map)
1. Create `backend/schemas/explorer_map.py` — `ExplorerMapState` model
2. Create `frontend/src/canvas/mapLayout.js` — position computation
3. Create `frontend/src/canvas/sprites.js` — static draw functions (background, fog, paths)
4. Create `frontend/src/canvas/ExplorerMap.jsx` — basic canvas with ResizeObserver, static map render
5. Modify `DeviceScreen.jsx` — add `explorer_map` to `WIDGET_MAP`
6. Modify `state_machine.py` — return `explorer_map` for Cat 5 HOOK and MISSION only (test pipeline)

**Checkpoint**: Static map visible in device screen during Cat 5 hook/mission. Cat 1 unaffected.

### Phase 2: Animation Engine
1. Create `frontend/src/canvas/animations.js` — animation presets
2. Create `frontend/src/canvas/useGameEngine.js` — game loop, animation queue
3. Create `frontend/src/canvas/particleSystem.js` — particle emitter
4. Update `ExplorerMap.jsx` — integrate game engine, add fog-reveal + character-appear animations
5. Add ambient animations — entity float, grass sway, occasional leaf particles

**Checkpoint**: Map has running game loop with smooth animations.

### Phase 3: Full Step Coverage
1. Update `state_machine.py` — return `explorer_map` for ALL Cat 5 steps
2. Update `turn_handler.py` — expose `collected_names`/`collected_details` in context
3. Update `visual_agent.py` — add `explorer_map` to allowed widgets
4. Implement all game phases in `ExplorerMap.jsx`:
   - `collect_reveal` → fog clears, character appears
   - `collect_detail` → character bounces
   - `collect_named` → name label draws
   - `synthesis` → characters unite, connection lines
   - `celebrate` → badge overlay + confetti
   - `closing` → sunset shift, characters wave

**Checkpoint**: Complete Cat 5 flow works end-to-end with Explorer's Map.

### Phase 4: Interactivity + Polish
1. Add pointer events to canvas — `onPointerDown`/`onPointerUp`
2. Hit-testing — check pointer overlap with characters/terrain
3. Tap responses — character bounce + SFX, fog pulse, celebration confetti at tap point
4. Thread `isSpeaking` from `App.jsx` → `DeviceScreen` → `ExplorerMap`
5. `prefers-reduced-motion` — disable animations, show static states
6. Performance: cap particles at 50, skip off-screen draws, profile on mobile

**Checkpoint**: Interactive, accessible, production-ready Explorer's Map.

---

## Verification

### Automated
- Backend: `uv run pytest` — existing Cat 5 scenario tests must pass with new widget type
- Backend: `uv run ruff check . && uv run ruff format . && uv run mypy .`
- Run `scripts/run_dandelion_scenarios.py` — verify every turn returns `widget: "explorer_map"`
- Cat 1 regression: run Cat 1 scenarios, verify no `explorer_map` widgets

### Manual Testing Checklist
- [ ] Cat 5 dandelion: full flow hook → closing, all 3 rounds
- [ ] Tap entity during hook — bounces + SFX
- [ ] Fog reveal plays after photo selection
- [ ] Name label appears after AI names item
- [ ] Synthesis: characters animate to center, connection lines draw
- [ ] Badge + confetti during celebration
- [ ] Canvas resizes correctly on browser resize
- [ ] `prefers-reduced-motion` disables animations
- [ ] Mobile touch events work (iOS Safari, Android Chrome)
- [ ] Cat 1 activities completely unaffected
- [ ] PhotoGallery modal still works during Phase A

---

## Pre-Implementation Step
Before writing code, copy this plan to `docs/plans/2026-03-26-explorer-map-game.md` per project conventions.
