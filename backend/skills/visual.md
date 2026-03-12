## Visual Agent — Rule Tables

The Visual Agent is rule-based (no LLM). It selects screen widgets, assigns assets, and sequences
frames based on deterministic mappings from the Director Agent's Composition Plan.

---

## Activity Type to Primary Widget Mapping

| Activity Type (Category) | Primary Widget       | Secondary Widget  | Notes                                      |
|--------------------------|----------------------|-------------------|--------------------------------------------|
| Category 1 (Verbal)      | character_display    | photo_display     | Show scene illustrations for each round    |
| Category 5 (Collection)  | progress_tracker     | photo_grid        | Track collected items, show grid at synthesis |

---

## Screen Strategy to Frame Count Logic

| Screen Strategy | Frame Count                          | Description                                      |
|-----------------|--------------------------------------|--------------------------------------------------|
| static          | 1 frame for all rounds               | Same visual throughout (rare, simple activities)  |
| per_round       | 1 frame per round + hook + closing   | New scene illustration each round                 |
| progressive     | 1 frame per round + hook + closing   | Slots fill progressively as child finds items     |

Frame count formula:
- **static**: `total_frames = 3` (hook + activity + closing)
- **per_round**: `total_frames = 2 + round_count` (hook + N rounds + closing)
- **progressive**: `total_frames = 2 + round_count` (hook + N rounds + closing)

---

## Emotional Arc to Animation Preset Mapping

| Emotional Arc       | Hook Animation      | Round Animation    | Closing Animation      |
|---------------------|---------------------|--------------------|------------------------|
| build_excitement    | sparkle_highlight   | scene_transition   | celebration_burst      |
| calm_curiosity      | gentle_pulse        | scene_transition   | concept_reveal         |
| playful_surprise    | sparkle_highlight   | celebration_burst  | mission_complete_fanfare |
| gentle_wonder       | gentle_pulse        | card_slide_in      | badge_reveal           |

---

## Frame Sequencing Rules

Each frame in the sequence must specify: widget, description, animation, and position.

### Hook Frame (always first)
- Widget: `photo_display`
- Description: Entity photo centered with ambient glow
- Animation: From emotional_arc mapping (hook column)

### Round Frames
- Widget: From activity type mapping (primary widget)
- Description: Contextual to the round content
- Animation: From emotional_arc mapping (round column)
- For progressive strategy: include progress count in description

### Synthesis Frame (if applicable, before closing)
- Widget: `photo_grid` (collection activities) or `character_display` (verbal activities)
- Animation: `connection_lines_draw` (collection) or `concept_reveal` (verbal)

### Closing Frame (always last)
- Widget: `badge_award`
- Description: Role badge with IB concept words
- Animation: From emotional_arc mapping (closing column), then `badge_reveal`

---

## Widget Specifications

| Widget             | Purpose                         | Required Fields                        |
|--------------------|---------------------------------|----------------------------------------|
| photo_display      | Show child's photo              | image_url, animation, overlay_text     |
| progress_tracker   | Track collection progress       | total_slots, filled_slots, items[]     |
| character_display  | Show scene illustration         | scene_description, animation           |
| photo_grid         | Display collected photos        | photos[], layout (e.g., "2x2")        |
| badge_award        | Award role badge                | badge_name, concepts[], animation      |

---

## Fallback Rules

| Condition                          | Fallback Action                                      |
|------------------------------------|------------------------------------------------------|
| Unknown activity type              | Use photo_display as primary widget, static strategy  |
| Missing emotional_arc              | Default to gentle_wonder                              |
| Round count exceeds tier max       | Clamp to tier maximum                                 |
| Missing widget_hint from Director  | Infer from activity type mapping above                |
| Animation not in allowed list      | Default to gentle_pulse                               |

### Allowed Animations
sparkle_highlight, gentle_pulse, celebration_burst, scene_transition, card_slide_in, badge_reveal,
mission_complete_fanfare, concept_reveal, connection_lines_draw

### Allowed SFX Cues
wonder_chime, excitement_rising, photo_shutter_click, slot_fill_chime, mission_accepted,
mission_complete_fanfare, celebration_fanfare, badge_awarded, scene_woosh, game_start_chime
