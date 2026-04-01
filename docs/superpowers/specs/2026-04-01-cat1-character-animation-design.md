# Cat1 Character Animation & Reactive Engagement System

**Date:** 2026-04-01
**Status:** Draft
**Scope:** Category 1 In-Device Verbal games (mood_changer_dog, dream_whisperer_cat, time_machine_dinosaur)

## Context

Cat1 games currently feel like a plain conversation with random SFX. The character is a static PNG with a gentle-float CSS animation, and there is no visual or audio feedback tied to user input — all reactions happen only after the backend responds. This makes the experience feel passive rather than alive.

This design introduces three layers of reactivity to make Cat1 games feel like interacting with a responsive character:
1. **AI-generated character video clips** (Veo 3.1) replacing the static PNG
2. **Themed particle overlays** that react to game state
3. **Reactive micro-sounds** triggered by user input events

## Approach: Video + Themed Particles (Approach B)

Selected over:
- **A (Video-only):** Too minimal — rest of screen stays dead while character comes alive
- **C (Full-screen reactive):** Overstimulation risk for 2-4 year olds, significantly more complex to tune

## 1. Character Animation State Machine

Eight states driven by game events, managed by a new `useCharacterAnimation` hook.

### States

| State | Type | Duration | Description |
|-------|------|----------|-------------|
| `idle` | Loop | 3-5s | Gentle breathing, slight movement. Default between interactions. |
| `listening` | Loop | 3-5s | Ears up, leaning in, attentive. Active while child's mic is on. |
| `thinking` | Loop | 3-5s | Head tilt, paw on chin. While API is processing. |
| `speaking` | Loop | 3-5s | Animated as if talking. During TTS playback. |
| `excited` | One-shot | 2-3s | Bouncing, tail wag / prancing / stomping. On correct answers. |
| `encouraging` | One-shot | 2-3s | Soft nod, warm expression. On wrong answers or confusion. |
| `surprised` | One-shot | 1-2s | Wide eyes, jump back. On unexpectedly creative answers. |
| `waving` | One-shot | 2-3s | Hello wave (session start) or goodbye wave (closing). |

### Trigger → State Mapping

| Game Event | Trigger Source | → State | Micro-Sound |
|------------|---------------|---------|-------------|
| Session starts (STEP_1_HOOK) | useSessionOrchestration | `waving` | greeting bark/meow/roar |
| Child activates mic | useSpeechRecognition | `listening` | ear perk / attentive sniff |
| Child stops speaking / sends text | useConversation | `thinking` | thoughtful hum |
| AI response (correct answer) | useConversation + emotion_tag | `excited` → `speaking` | happy bark/purr/stomp |
| AI response (wrong/confused) | useConversation + emotion_tag | `encouraging` → `speaking` | gentle whimper/soft meow |
| AI response (creative answer) | useConversation + emotion_tag | `surprised` → `speaking` | amazed gasp/yelp |
| TTS starts playing | useTTS | `speaking` | — |
| TTS finishes | useTTS | `idle` | — |
| Session ends (STEP_5_CLOSING) | useSessionOrchestration | `waving` | goodbye bark/meow/roar |

### Transition Rules

- **One-shot → loop:** Reaction clips (excited, encouraging, surprised) play once, then auto-transition to `speaking` loop when TTS starts. Video `ended` event triggers the transition.
- **Crossfade:** Two overlapping `<video>` elements. New clip fades in (200ms CSS opacity transition) while old fades out. Prevents jarring cuts.
- **Preloading:** All 8 clips for the current character are preloaded into memory on session start using `video.preload = 'auto'`. ~500KB per clip × 8 = ~4MB per character.

### Backend Emotion → State Mapping

Deterministic map in `server.py` (no LLM call needed):

| emotion_tag values | → character_state |
|---|---|
| `excited`, `celebrating`, `impressed` | `excited` |
| `gentle`, `encouraging` | `encouraging` |
| `curious`, `mysterious` (+ creative answer context) | `surprised` |
| `adventurous`, default | `speaking` |
| STEP_4_CELEBRATE auto-advance | `excited` |
| STEP_5_CLOSING auto-advance | `waving` |

New field `character_state: str` added to `TurnResponse` schema.

## 2. Full-Panel Video Layout

Video fills the entire device panel (no more small icon circle). Round info moves to a bottom gradient overlay.

### Layout

```
┌──────────────────────────────┐
│                              │
│     Video fills entire       │
│     device panel             │
│     (16:9, object-cover)     │
│                              │
│  [particles floating]        │
│                              │
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ ← gradient fade
│  Round 2 · Favorite treat    │ ← bottom overlay
└──────────────────────────────┘
```

- Video element fills the panel with `object-cover` (crops 16:9 to fit viewport)
- Bottom gradient overlay: `linear-gradient(transparent, rgba(0,0,0,0.7))`
- Round badge + scenario description text in the overlay
- ParticleField overlays on top of video

### Video Flow Per Round

The scenario clip is the round's "idle/world" state. Character clips are temporary reactions.

```
🌄 Scenario loop     ← round starts, loops as idle state
🐕 Listening         ← child activates mic, crossfade to character
🐕 Thinking          ← child stops speaking
🐕 Excited           ← AI celebrates (one-shot)
🐕 Speaking           ← TTS plays (loop)
🌄 Scenario loop     ← TTS ends, crossfade BACK to scenario
🌄 New scenario      ← next round, crossfade to new scenario
```

Session start/end use character `waving` clip (no scenario).

## 3. Veo 3.1 Asset Pipeline

### Generation

- **Model:** `veo-3.1-fast-generate-001` via Vertex AI
- **Output:** MP4 (H.264) — universal browser support including Safari
- **Aspect ratio:** 16:9 — matches landscape device panel
- **Duration:** 4s (Veo minimum)
- **Style consistency:** `idle` state generated first per character, a frame extracted via ffmpeg, then used as `image` reference for remaining states
- **Total clips:** 48 (24 character emotion + 24 scenario illustration)

### Character Emotion Clips (24)

```
frontend/public/video/character/
├── mood_changer_dog/
│   ├── dog_idle.mp4, dog_listening.mp4, dog_thinking.mp4, dog_speaking.mp4
│   ├── dog_excited.mp4, dog_encouraging.mp4, dog_surprised.mp4, dog_waving.mp4
├── dream_whisperer_cat/
│   └── cat_{state}.mp4 (×8)
└── time_machine_dinosaur/
    └── dinosaur_{state}.mp4 (×8)
```

### Scenario Illustration Clips (24)

Pre-generated from the fixed round_scenarios in `backend/games/*.md`:

```
frontend/public/video/scenario/
├── mood_changer_dog/
│   ├── scenario_1.mp4  (warm sunshine on belly)
│   ├── scenario_2.mp4  (tripped and went bump)
│   └── ... (8 total)
├── dream_whisperer_cat/
│   └── scenario_{n}.mp4 (×8)
└── time_machine_dinosaur/
    └── scenario_{n}.mp4 (×8)
```

### Generation Tool

CLI script: `tools/generate_character_clips.py`

- Reads prompt templates from `tools/character_clip_prompts.yaml`
- Each character has a base description (consistent across states) + state-specific action/emotion
- Calls Veo 3.1 for each character × state combination
- Saves output to `frontend/public/video/character/`
- Run once at build time, not at runtime

**Prompt structure:**
```yaml
mood_changer_dog:
  base: >
    A cute, friendly stuffed dog toy with blue fur, sitting upright.
    3D rendered toy aesthetic, Pixar-inspired, warm lighting.
    Background: Solid soft blue gradient. No text or UI elements.
  states:
    excited: >
      The dog is bouncing happily, tail wagging rapidly, ears flopping
      with joy. Warm, child-friendly animation style.
    listening: >
      The dog is leaning forward attentively, ears perked up, head
      slightly tilted to one side as if carefully listening.
    # ... etc for each state
```

## 3. Themed Particle Overlay System

CSS-only emoji particles layered on top of character video clips. No Canvas, no JS animation loops.

### Per-Character Particle Themes

| Character | Particles | Palette |
|-----------|-----------|---------|
| Dog (mood_changer_dog) | 🦴 🐾 💙 | Blue gradient |
| Cat (dream_whisperer_cat) | ⭐ 🌙 ✨ 💜 | Violet gradient |
| Dinosaur (time_machine_dinosaur) | 🌿 🌋 🦶 🧡 | Amber gradient |

### Particle Behavior by State

| State | Particle Behavior | Background |
|-------|-------------------|------------|
| `idle` | 3-5 particles, gentle float, low opacity (0.4-0.6) | Default theme gradient |
| `listening` | Particles slow, drift toward character (attention focus) | Slight brighten |
| `thinking` | Particles orbit slowly in circle around character | Subtle pulse |
| `excited` | **Burst!** 8-12 particles explode outward + spin, high opacity. 2s then settle. | Quick flash brighten |
| `encouraging` | Particles drift inward, warm glow. Cozy, reassuring. | Warm shift |
| `surprised` | Particles jump up briefly, settle with sparkle trail | Flash + return |
| `speaking` | Gentle sway matching speech rhythm, medium opacity | Theme default |
| `waving` | Particles fan outward in greeting arc | Warm welcome glow |

### Implementation

- **New component:** `ParticleField.jsx` — wraps CharacterDisplay, renders 5-12 absolutely-positioned emoji `<span>` elements
- **CSS classes per state:** e.g., `.particles-excited` applies burst keyframes, `.particles-idle` applies gentle-float
- **Theme config in `gameThemes.js`:** Each character gets `particles: [{emoji: '🦴', count: 3, baseSize: 16}]`
- **Re-renders only on state change** (not every frame)
- **Background gradient:** DeviceScreen background subtly shifts color via CSS transition on state change

## 4. Reactive Micro-Sounds

Short (<800ms) ambient sounds triggered by user input events. Distinct from the existing character_sfx intro/overlay system, which is longer and tied to AI turns.

### Micro-Sound Categories

| Trigger Event | Cue ID | Duration | Volume | Example (Dog) |
|---|---|---|---|---|
| Child activates mic | `attention` | <500ms | 0.3 | Quick ear-perk sniff |
| Child stops speaking | `acknowledge` | <500ms | 0.25 | Thoughtful "hmm" grunt |
| State → `excited` | `react_happy` | <800ms | 0.4 | Short happy bark |
| State → `encouraging` | `react_gentle` | <600ms | 0.3 | Soft supportive whimper |
| State → `surprised` | `react_amazed` | <600ms | 0.35 | Surprised gasp/yelp |

Note: No separate `celebration_micro` cue — `react_happy` already plays on correct answers when the particle burst fires. Avoid layering two sounds at the same moment.

### Assets

- **Location:** `frontend/public/sfx/character/{activity_type}/micro_{cueId}_v{1-3}.wav`
- **3 variants per cue** to prevent repetition (matching existing pattern)
- **Total new files:** 5 cues × 3 variants × 3 characters = 45 short WAVs (~1KB each)

### Integration

Extend `useCharacterSfx.js` with `playMicro(cueId)`:
- Plays instantly via Web Audio API (no intro/overlay timing)
- Uses existing buffer cache and AudioContext
- Low volume (0.25-0.4) — ambient, not attention-grabbing

## 5. Files to Create or Modify

### New Files

| File | Purpose |
|------|---------|
| `frontend/src/hooks/useCharacterAnimation.js` | State machine hook. Inputs: isListening, isProcessing, isSpeaking, characterState, currentStep. Outputs: currentClipUrl, isOneShot, onClipEnded. |
| `frontend/src/widgets/ParticleField.jsx` | CSS particle overlay component. Receives characterState + theme props. |
| `tools/generate_character_clips.py` | CLI script to generate Veo 3.1 clips via Vertex AI. |
| `tools/character_clip_prompts.yaml` | Prompt templates per character × state. |
| `frontend/public/video/character/` | 24 MP4 video clips (8 states × 3 characters). |
| `frontend/public/sfx/character/*/micro_*.wav` | 45 micro-sound WAV files (5 cues × 3 variants × 3 characters). |

### Modified Files

| File | Change |
|------|--------|
| `frontend/src/widgets/CharacterDisplay.jsx` | Replace `<img>` with dual `<video>` crossfade system. Accept clipUrl, isOneShot, onClipEnded props. |
| `frontend/src/components/DeviceScreen.jsx` | Wrap CharacterDisplay + ParticleField. Pass character state. Add background gradient transition. |
| `frontend/src/hooks/useCharacterSfx.js` | Add `playMicro(cueId)` method for instant short sounds. |
| `frontend/src/hooks/useSessionOrchestration.js` | Wire mic events and turn responses to useCharacterAnimation + playMicro calls. |
| `frontend/src/widgets/gameThemes.js` | Add particle definitions and videoBasePath per character. |
| `frontend/src/index.css` | New particle keyframe animations (burst, orbit, drift, fan-out). |
| `backend/schemas/turn_response.py` | Add `character_state: str` field to TurnResponse. |
| `backend/server.py` | Add emotion_tag → character_state mapping in `_build_turn_response`. |

### Not Changed

| File | Reason |
|------|--------|
| `useCharacterSfx.js` intro/overlay system | Stays untouched — micro-sounds are additive |
| `useSfxPlayer.js` | UI SFX system unchanged |
| Backend agent pipeline | No new LLM calls needed |
| Recipe schema | No structural changes |
| TTS system (`useTTS.js`, `backend/tts.py`) | Unchanged |
| `ConversationPanel.jsx` | No changes in Approach B |

## 6. Verification

1. **Veo clip generation:** Run `tools/generate_character_clips.py` and verify 24 MP4 files are created in `frontend/public/video/character/`
2. **State machine:** Start a Cat1 session and verify state transitions:
   - Session start → WAVING clip plays
   - Activate mic → LISTENING clip
   - Send message → THINKING clip
   - AI responds (correct) → EXCITED → SPEAKING
   - AI responds (wrong) → ENCOURAGING → SPEAKING
   - TTS ends → IDLE
   - Session close → WAVING
3. **Crossfade:** Verify smooth 200ms opacity transitions between clips (no black frames)
4. **Particles:** Verify themed particles appear and change behavior with state
5. **Micro-sounds:** Verify short sounds play on mic activation, message send, and state transitions
6. **Performance:** Check video memory usage on mobile Safari and Chrome (target: <50MB total)
7. **Existing features:** Verify character_sfx intros/overlays and TTS still work correctly alongside new system
