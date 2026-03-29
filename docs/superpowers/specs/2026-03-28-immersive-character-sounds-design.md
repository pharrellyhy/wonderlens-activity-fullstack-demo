# Immersive Character & Environment Sounds

## Problem

The current audio system has two layers — TTS voice (Gemini) and 10 fixed UI SFX cues
(chimes, fanfares, wooshes) that only trigger at predetermined game steps. There are no
character-specific sounds (no dog barks, cat purrs, dinosaur roars), no environmental
ambience, and no dynamic triggering. Every sound fires at the same fixed moment in the
step pipeline. This makes the game feel mechanical rather than immersive.

## Goal

Add a character & environment sound system where short audio clips (barks, purrs, roars,
birdsong, thunder, etc.) play dynamically during gameplay — triggered by the LLM at
contextually appropriate moments, overlapping with TTS dialogue for a rich, immersive
audio experience.

## Decisions

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Sound type | Pre-recorded clips alongside TTS | TTS voice stays human; character/environment clips add atmosphere |
| Trigger model | Script-driven (LLM places cues) | Context-aware, dynamic, fits any conversational moment |
| Sound source | Pre-recorded WAV library (placeholders first) | Zero latency, reliable, high quality when assets finalized |
| Scope | All 5 activities | Dog, Cat, Dinosaur (character + environment), Polka Dot & Fluffy (nature + discovery) |
| Audio mixing | Overlap with TTS | Character sounds play at marked positions even while TTS speaks |
| Timing model | 3 slots: intro / overlay / outro | Best balance of immersion and reliability without fragile text parsing |

## Architecture: Structured Cue Field with Three Timing Slots

### Why Not Inline Markers?

Inline text markers (`[dog_bark_happy]` in dialogue) were considered but rejected:
- Collides with existing bracket syntax for emotion tags and Gemini TTS tags
- Duration is unknown during streaming TTS (`speakFromStream`), breaking position-based timing
- Fragile regex parsing with defensive edge-case handling needed

The chosen approach uses a structured JSON field in the TurnResponse. The LLM outputs a
`character_sfx` array alongside dialogue — no text parsing required.

### Timing Slots

| Slot | When it fires | Use case |
|------|--------------|----------|
| `intro` | Before TTS starts (max 1.2s wait) | Character reacts before narrator speaks — bark, roar, thunder |
| `overlay` | 300ms after TTS play begins | Ambient presence during speech — purring, breeze, jungle ambience |
| `outro` | After TTS `onended` event | Closing reaction — satisfied pant, discovery sparkle |

### Data Flow

```
Script Agent LLM
  → TurnResponse JSON with character_sfx: [{cue, timing}, ...]
  → validate_character_sfx() drops invalid cues, caps at 2 per turn
  → _build_turn_response() includes character_sfx in JSON response
  → /api/turn-speak binary: [JSON with character_sfx][OGG/Opus audio]
  → Frontend parses JSON
  → useCharacterSfx hook orchestrates playback around TTS
```

## Sound Library

### Definition Format

**File: `backend/data/character_sounds.yaml`**

Each activity defines its available sounds. Fields:
- `id`: Unique sound identifier, used in cue references and file names
- `category`: Semantic grouping (bark, purr, environment, etc.) — included in the
  prompt so the LLM can reason about sound variety (avoid two barks in a row)
- `energy`: low/medium/high — included in the prompt to help the LLM match sound
  intensity to the emotional moment. Not used for volume control (all sounds play at 0.4).

```yaml
mood_changer_dog:
  sounds:
    # Character sounds
    - id: dog_bark_happy
      category: bark
      energy: high
    - id: dog_bark_curious
      category: bark
      energy: medium
    - id: dog_pant_content
      category: pant
      energy: low
    - id: dog_whimper_sad
      category: whimper
      energy: low
    - id: dog_yip_playful
      category: bark
      energy: high
    - id: dog_growl_dramatic
      category: growl
      energy: medium
    - id: dog_sniff_curious
      category: sniff
      energy: low
    - id: dog_howl_dramatic
      category: howl
      energy: high
    - id: dog_tail_thump
      category: ambient
      energy: low
    - id: dog_shake_excitement
      category: ambient
      energy: medium
    # Environment sounds
    - id: env_birds_chirp
      category: environment
      energy: low
    - id: env_breeze_gentle
      category: environment
      energy: low
    - id: env_leaves_rustle
      category: environment
      energy: low
    - id: env_sunshine_warm
      category: environment
      energy: low
    - id: env_rain_soft
      category: environment
      energy: low
    - id: env_thunder_distant
      category: environment
      energy: medium
```

```yaml
dream_whisperer_cat:
  sounds:
    # Character sounds
    - id: cat_purr_soft
      category: purr
      energy: low
    - id: cat_meow_curious
      category: meow
      energy: medium
    - id: cat_meow_happy
      category: meow
      energy: medium
    - id: cat_hiss_surprised
      category: hiss
      energy: high
    - id: cat_chirp_excited
      category: chirp
      energy: medium
    - id: cat_yawn_sleepy
      category: yawn
      energy: low
    - id: cat_paw_knead
      category: ambient
      energy: low
    # Environment sounds
    - id: env_fireplace_crackle
      category: environment
      energy: low
    - id: env_rain_window
      category: environment
      energy: low
    - id: env_clock_tick
      category: environment
      energy: low
    - id: env_blanket_rustle
      category: environment
      energy: low
    - id: env_wind_chime
      category: environment
      energy: low
```

```yaml
time_machine_dinosaur:
  sounds:
    # Character sounds
    - id: dino_roar_friendly
      category: roar
      energy: high
    - id: dino_stomp_heavy
      category: stomp
      energy: high
    - id: dino_growl_playful
      category: growl
      energy: medium
    - id: dino_chirp_small
      category: chirp
      energy: low
    - id: dino_rumble_deep
      category: rumble
      energy: medium
    - id: dino_chomp_munching
      category: chomp
      energy: medium
    # Environment sounds
    - id: env_jungle_ambience
      category: environment
      energy: low
    - id: env_volcano_rumble
      category: environment
      energy: medium
    - id: env_waterfall_distant
      category: environment
      energy: low
    - id: env_prehistoric_wind
      category: environment
      energy: low
    - id: env_time_whoosh
      category: environment
      energy: medium
```

```yaml
polka_dot_patrol:
  sounds:
    - id: nature_birds_chirp
      category: nature
      energy: low
    - id: nature_breeze_gentle
      category: nature
      energy: low
    - id: nature_leaves_rustle
      category: nature
      energy: low
    - id: nature_cricket_chirp
      category: nature
      energy: low
    - id: discovery_sparkle
      category: discovery
      energy: medium
    - id: discovery_gasp
      category: discovery
      energy: medium
```

```yaml
fluffy_expedition_dandelion:
  sounds:
    - id: nature_wind_soft
      category: nature
      energy: low
    - id: nature_dandelion_puff
      category: nature
      energy: low
    - id: nature_grass_rustle
      category: nature
      energy: low
    - id: nature_bees_buzz
      category: nature
      energy: low
    - id: discovery_sparkle
      category: discovery
      energy: medium
    - id: discovery_oooh
      category: discovery
      energy: medium
```

### Asset File Structure

```
frontend/public/sfx/
  ├── wonder_chime_v1.wav          # existing UI SFX (unchanged)
  ├── ...
  └── character/
      ├── mood_changer_dog/
      │   ├── dog_bark_happy_v1.wav
      │   ├── dog_bark_happy_v2.wav
      │   ├── dog_bark_happy_v3.wav
      │   ├── env_birds_chirp_v1.wav
      │   └── ...
      ├── dream_whisperer_cat/
      │   └── ...
      ├── time_machine_dinosaur/
      │   └── ...
      ├── polka_dot_patrol/
      │   └── ...
      └── fluffy_expedition_dandelion/
          └── ...
```

Each sound has 3 variations (`_v1`, `_v2`, `_v3`). Placeholder assets will be short
synthetic tones generated with `sox` or similar. Total: ~80 sounds x 3 variations = ~240 files.

## Backend Changes

### New Module: `backend/character_sounds.py`

```python
@lru_cache(maxsize=1)
def load_character_sound_library() -> dict[str, ActivitySoundLibrary]:
    """Load and cache the character sound YAML config."""

def validate_character_sfx(
    activity_type: str,
    cues: list[CharacterSfxCue],
) -> list[CharacterSfxCue]:
    """Validate cue IDs against activity's library, cap at 2 per turn.
    Drop invalid cues silently (LLM hallucinations)."""

def get_sound_list_for_prompt(activity_type: str) -> str:
    """Format available sounds as a text block for prompt injection."""
```

### Schema Changes: `backend/schemas/turn_response.py`

```python
class CharacterSfxCue(BaseModel):
    cue: str = Field(description="Sound ID, e.g. dog_bark_happy, env_thunder_distant")
    timing: str = Field(
        default="intro",
        description="When to play: intro (before TTS), overlay (during TTS), outro (after TTS)"
    )

class TurnResponse(BaseModel):
    # ... existing fields ...
    character_sfx: list[CharacterSfxCue] = Field(default_factory=list)
```

### Server Changes: `backend/server.py`

In `_build_turn_response()`:
```python
result["character_sfx"] = [c.model_dump() for c in turn.character_sfx]
```

No changes to the TTS pipeline or binary protocol — character sounds are
purely frontend-driven from the JSON portion.

### Script Agent Changes: `backend/agents/script_agent.py`

The `_format_system_prompt()` method injects the character sound list from
`get_sound_list_for_prompt(activity_type)` into the system prompt. The existing
`_clean_dialogue()` function does NOT need changes — character sound data flows
through the structured `character_sfx` field, not through dialogue text.

### Prompt Changes: `backend/skills/script_turn.md`

New section added to Output Rules:

```
## Character & Environment Sounds

You may include 0-2 character or environment sound effects per turn in the
`character_sfx` array. Each entry specifies a `cue` (sound ID) and `timing`:

- "intro": Sound plays BEFORE your speech. Use for character reactions or
  scene-setting (a bark before you say "He's excited!", thunder before
  describing a storm).
- "overlay": Sound plays DURING your speech. Use for ambient presence
  (soft purring while you describe the cat, gentle breeze while exploring).
- "outro": Sound plays AFTER your speech. Use for closing reactions
  (satisfied pant, discovery sparkle after the child answers).

Available sounds for this activity:
{character_sound_list}

Guidelines:
- Not every turn needs a sound. Alternate for natural rhythm.
- Max 2 cues per turn.
- Match sound energy to the emotional moment.
- "intro" character sounds create anticipation.
- "overlay" environment sounds build atmosphere.
```

## Frontend Changes

### New Hook: `frontend/src/hooks/useCharacterSfx.js`

Separate from `useSfxPlayer` (which remains unchanged for UI SFX).

**Responsibilities:**
- `preload(activityType)` — On session start, prefetch all WAV files for the
  activity into browser cache via `new Audio(url)` for each variation
- Audio pool of 2-3 `Audio` elements for polyphonic playback
- `playForTurn(cueList, { onIntrosDone })` — orchestrates timing:
  1. Play all `intro` cues simultaneously
  2. Call `onIntrosDone` after max intro duration or 1.2s cap
  3. Expose `startOverlays()` — called 300ms after TTS begins
  4. Expose `playOutros()` — called when TTS finishes
- Random variation selection (same pattern as `useSfxPlayer`)
- Audio unlock: participates in gesture-based unlock alongside TTS/SFX
- Volume: 0.4 (slightly below TTS, blends without overwhelming)

### Updated Orchestration: `frontend/src/hooks/useSessionOrchestration.js`

```
New AI message arrives:
  1. Extract character_sfx from turn response
  2. If character_sfx has "intro" cues:
     → Play intros via useCharacterSfx
     → On intros done (or 1.2s cap) → start TTS
  3. If no "intro" cues:
     → Start TTS immediately
  4. 300ms after TTS starts → call startOverlays()
  5. TTS onended → call playOutros() → then handleSpeakingDone()
```

### Unchanged Systems

- `useSfxPlayer.js` — 10 UI SFX cues, triggered by DeviceScreen on screen frame changes
- `DeviceScreen.jsx` — No changes
- `useTTS.js` — No changes
- `SfxIndicator.jsx` — No changes (or optionally extend to show character sounds too)

## TTS Disabled Behavior

When the user toggles TTS off, character sounds still play. They are atmosphere,
not narration. The orchestration flow simplifies:
- `intro` cues play immediately
- `overlay` cues play 300ms after intro finishes (since there's no TTS to anchor to)
- `outro` cues play after overlay finishes
- Then `handleSpeakingDone()` fires as usual

## Coexistence with Existing SFX

The character sound system runs on a **separate audio channel** from UI SFX:
- UI SFX (`useSfxPlayer`): triggered by screen frame changes, one-at-a-time
- Character sounds (`useCharacterSfx`): triggered per-turn from JSON, polyphonic

Both can play simultaneously (e.g., `scene_woosh` UI transition + `dog_bark_happy`
character intro). The volume levels are balanced:
- TTS voice: browser default (~1.0)
- UI SFX: 0.5
- Character sounds: 0.4

## Placeholder Asset Strategy

Start with synthetic placeholder sounds to prove the system end-to-end:
- Generate short WAV files (0.3-1.5s) using `sox` tone generation
- Different frequencies/patterns for different sound categories
- Replace with high-quality assets (AI-generated or library-sourced) later

## Volume & Frequency Guardrails

For young children (T0 = ages 2-4):
- Character sounds capped at 2 per turn (enforced by backend validation)
- LLM prompted to alternate turns with/without sounds
- Volume at 0.4 (gentle, not startling)
- No sudden loud sounds — `energy: high` sounds (roars, barks) still use moderate volume
- `intro` timing has a 1.2s cap to prevent long delays before speech

## Testing Strategy

- **Backend unit tests**: YAML loading, cue validation (valid/invalid/hallucinated IDs),
  prompt injection formatting, TurnResponse serialization with character_sfx
- **Frontend manual testing**: Verify timing feels natural, sounds overlap correctly
  with TTS, preloading works, audio unlock includes character sounds
- **Integration**: Run full game session, verify character sounds appear in turn
  responses and play at correct moments
- **Prompt quality**: Run multiple sessions per activity, check that the LLM places
  cues naturally and doesn't over/under-use them

## Files to Modify

| File | Change |
|------|--------|
| `backend/data/character_sounds.yaml` | New — sound library definitions |
| `backend/character_sounds.py` | New — loader, validator, prompt helper |
| `backend/schemas/turn_response.py` | Add `CharacterSfxCue` model and `character_sfx` field |
| `backend/agents/script_agent.py` | Inject sound list into system prompt |
| `backend/skills/script_turn.md` | Add character sound instructions section |
| `backend/server.py` | Include `character_sfx` in `_build_turn_response()` |
| `frontend/src/hooks/useCharacterSfx.js` | New — preload, play, timing orchestration |
| `frontend/src/hooks/useSessionOrchestration.js` | Wire character sounds into turn flow |
| `frontend/public/sfx/character/` | New — placeholder WAV assets (~240 files) |
