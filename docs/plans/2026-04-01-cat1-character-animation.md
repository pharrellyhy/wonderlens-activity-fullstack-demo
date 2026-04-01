# Cat1 Character Animation & Reactive Engagement System — Implementation Plan

**Spec:** `docs/superpowers/specs/2026-04-01-cat1-character-animation-design.md`

## Context

Cat1 games feel like a plain conversation with random SFX. The character is a static PNG with no visual or audio feedback tied to user input. This plan implements three layers of reactivity: AI-generated character video clips (Veo 3.1), CSS-only themed particle overlays, and reactive micro-sounds — all driven by a frontend state machine that responds to game events.

---

## Phase 1: Backend — Add `character_state` to Turn Response

### Step 1.1: Add `character_state` field to TurnResponse schema
**File:** `backend/schemas/turn_response.py`
- Add `character_state: str = Field(default="idle")` to TurnResponse model
- Valid values: idle, listening, thinking, speaking, excited, encouraging, surprised, waving

### Step 1.2: Add emotion→state mapping in server.py
**File:** `backend/server.py`
- Add `_map_character_state(tone_marker, response_type)` helper
- Mapping: excited/celebrating/impressed→"excited", gentle/encouraging→"encouraging", curious/mysterious→"surprised", default→"speaking"
- Step overrides: hook→"waving", celebration→"excited", closing/graceful_exit→"waving"
- Call in `_build_turn_response`, set result on return dict

### Step 1.3: Write backend test
**File:** Create `backend/tests/test_character_state.py`
- Test all emotion_tag values and response_type overrides

### Step 1.4: Propagate character_state through frontend API
**File:** `frontend/src/hooks/useConversation.js`
- Extract `data.turn.character_state` in `applyTurnResponse`
- Include in message object + expose as state variable

**Verification:** `uv run ruff check . && uv run pytest backend/tests/test_character_state.py`

---

## Phase 2: Frontend State Machine — `useCharacterAnimation` Hook

**Depends on:** Phase 1

### Step 2.1: Create useCharacterAnimation hook
**File:** Create `frontend/src/hooks/useCharacterAnimation.js`
- Inputs: isListening, turnPending, isSpeaking, characterState (from API), currentStep, activityType
- Outputs: currentClipUrl, animationState, isOneShot, onClipEnded
- Transitions: mic active→listening, child sends→thinking, AI responds→emotion-matched, TTS plays→speaking, TTS ends→idle, session start/end→waving
- One-shot clips auto-transition to speaking (via video ended event) then idle
- Clip URL: `${BASE}/video/character/${activityType}/${prefix}_${state}.mp4`
- Preload all 8 clips on session start
- Follow ref-heavy pattern from useCharacterSfx.js

### Step 2.2: Add theme config for video paths + particles
**File:** `frontend/src/widgets/gameThemes.js`
- Add `videoBasePath`, `videoPrefix`, `particles` array to dog/cat/dinosaur themes
- Dog particles: 🦴🐾💙, Cat: ⭐🌙✨💜, Dinosaur: 🌿🌋🦶🧡

### Step 2.3: Wire into useSessionOrchestration
**File:** `frontend/src/hooks/useSessionOrchestration.js`
- Call useCharacterAnimation with inputs from speech, conversation, TTS hooks
- Expose animationState, currentClipUrl, isOneShot, onClipEnded

**Verification:** Console-log state transitions during Cat1 session

---

## Phase 3: Video Crossfade in CharacterDisplay

**Depends on:** Phase 2

### Step 3.1: Refactor CharacterDisplay to video
**File:** `frontend/src/widgets/CharacterDisplay.jsx`
- Replace `<img>` with dual `<video>` elements for crossfade
- New props: clipUrl, isOneShot, onClipEnded, animationState
- Crossfade: two absolutely-positioned videos, CSS opacity transition (200ms)
- Loop clips use `loop` attr, one-shots fire onClipEnded on `ended` event
- All videos: playsInline, muted, autoPlay
- Fallback: if clipUrl is falsy, show existing static PNG (Cat5 games unaffected)
- Wait for `canplay` event before starting crossfade (prevent black frames)

### Step 3.2: Pass video props through DeviceScreen
**File:** `frontend/src/components/DeviceScreen.jsx`
- Accept + pass clipUrl, isOneShot, onClipEnded, animationState to CharacterDisplay

### Step 3.3: Pass video props from App.jsx
**File:** `frontend/src/App.jsx`
- Destructure video props from useSessionOrchestration, pass to DeviceScreen

**Verification:** Full round-trip: start session → waving → speak → listening → thinking → AI response → reaction → speaking → idle

---

## Phase 4: Particle Overlay System

**Depends on:** Phase 2 (parallel with Phase 3 and 5)

### Step 4.1: Create ParticleField component
**File:** Create `frontend/src/widgets/ParticleField.jsx`
- Props: animationState, particles (from theme)
- Renders 5-12 absolutely-positioned emoji spans
- CSS class per state: `.particle-idle`, `.particle-excited`, etc.
- Random position, delay, duration per particle for variety
- React.memo — re-renders only on state change
- pointer-events: none, overflow: hidden

### Step 4.2: Add particle CSS keyframe animations
**File:** `frontend/src/index.css`
- New keyframes: particle-float (idle), particle-focus (listening), particle-orbit (thinking), particle-burst (excited), particle-drift-in (encouraging), particle-jump (surprised), particle-sway (speaking), particle-fan (waving)
- `.particle-{state}` classes
- Respect `prefers-reduced-motion`

### Step 4.3: Integrate ParticleField into DeviceScreen
**File:** `frontend/src/components/DeviceScreen.jsx`
- When widget is character_display, render ParticleField as sibling overlay
- Import getThemeForEntity for particle config
- Add subtle background gradient CSS transition based on animationState

**Verification:** Particles appear, change behavior with state. Cat5 unaffected.

---

## Phase 5: Reactive Micro-Sounds

**Depends on:** Phase 2 (parallel with Phase 3 and 4)

### Step 5.1: Extend useCharacterSfx with playMicro
**File:** `frontend/src/hooks/useCharacterSfx.js`
- Add `playMicro(cueId)` — instant playback via Web Audio API
- Path: `${BASE}/sfx/character/${activityType}/micro_${cueId}_v${variant}.wav`
- Volume: 0.3 (MICRO_VOLUME constant)
- 3 variants per cue (random selection, matching existing pattern)
- Uses same buffer cache and AudioContext

### Step 5.2: Wire micro-sound triggers
**File:** `frontend/src/hooks/useSessionOrchestration.js`
- isListening false→true: `playMicro('attention')`
- Transcript arrives: `playMicro('acknowledge')`
- animationState→excited: `playMicro('react_happy')`
- animationState→encouraging: `playMicro('react_gentle')`
- animationState→surprised: `playMicro('react_amazed')`
- Guard with ref to track previous state, prevent double-fire

### Step 5.3: Create placeholder micro-sound assets
- 45 files: 5 cues × 3 variants × 3 characters
- Path: `frontend/public/sfx/character/{activity}/micro_{cueId}_v{1,2,3}.wav`
- Start with silent/placeholder WAVs for development

**Verification:** Micro-sounds play at correct trigger points, low volume

---

## Phase 6: Veo 3.1 Asset Generation Pipeline

**Independent — can run in parallel with all other phases**

### Step 6.1: Create prompt templates YAML
**File:** Create `tools/character_clip_prompts.yaml`
- Base description per character (consistent visual identity)
- State-specific action prompts
- Duration hints (loop: 3-5s, one-shot: 2-3s)
- Resolution: 480×480

### Step 6.2: Create generation CLI script
**File:** Create `tools/generate_character_clips.py`
- Reads prompts from YAML, calls Veo 3.1 via Vertex AI SDK
- Outputs MP4 to `frontend/public/video/character/{activity}/{prefix}_{state}.mp4`
- Flags: --character, --state (selective regen), --dry-run
- Uses same Vertex AI credentials as existing Gemini calls

### Step 6.3: Create video asset directory structure
- `frontend/public/video/character/{mood_changer_dog,dream_whisperer_cat,time_machine_dinosaur}/`

**Verification:** `--dry-run` prints 24 prompts. Full run generates 24 MP4 files.

---

## Dependency Graph

```
Phase 1 (Backend)          Phase 6 (Veo Pipeline)
  1.1→1.2→1.3               6.1→6.2
  1.1→1.4                   6.3 (independent)
      ↓
Phase 2 (State Machine)
  2.1, 2.2→2.3
      ↓
  ┌───┼───┐
  ↓   ↓   ↓
Ph3  Ph4  Ph5   ← can run in parallel
```

## Risk Mitigations

1. **Safari video preload:** Preload only idle+listening eagerly; load others on-demand with PNG fallback
2. **Crossfade black frames:** Wait for `canplay` event before starting opacity transition
3. **Non-Cat1 games:** All features gated on activityType; null clipUrl → existing PNG fallback
4. **prefers-reduced-motion:** All new animations covered by existing media query block

## End-to-End Verification

1. Run `tools/generate_character_clips.py` → verify 24 MP4s
2. Start Cat1 session → walk through full state machine transitions
3. Verify crossfade smoothness (no black frames)
4. Verify particles appear and react to state
5. Verify micro-sounds on mic/message/state events
6. Check video memory on mobile (<50MB target)
7. Verify existing character_sfx + TTS still work
8. Verify Cat5 games are completely unaffected
