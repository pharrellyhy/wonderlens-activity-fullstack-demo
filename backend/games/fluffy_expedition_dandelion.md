---
activity_type: fluffy_expedition_dandelion
entity_name: dandelion
category: category_5
display_label: Dandelion
tier: T0
ib_theme: "Sharing the Planet"
ib_key_concept: Connection
concepts_earned: [Connection]
keywords: [dandelion, flower]
feature_keywords: [fluffy, dandelion, soft, fuzzy]
photo_features: [white fluffy seeds, round seed head, thin stem, delicate structure]

creative_slots:
  observation_angle: texture
  collection_criterion: "Find things that are fluffy, fuzzy, or soft"
  collection_count: 3
  mission_metaphor: "You are a Fluffy Expedition Explorer!"
  role_title: Fluffy Expedition Explorer
  synthesis_type: naming_story
  stuck_hint: "Try touching things around you — look for anything soft or fuzzy"
  naming_prompt: "What would you name this fluffy friend?"

collection_catalog:
  correct:
    - id: fuzzy_moss
      label: Fuzzy moss
      image: /icons/fuzzy_moss.png
    - id: fluffy_seed
      label: Fluffy seed head
      image: /icons/fluffy_seed.png
    - id: soft_petal
      label: Soft petal
      image: /icons/soft_petal.png
    - id: woolly_caterpillar
      label: Woolly caterpillar
      image: /icons/woolly_caterpillar.png
  distractors:
    - id: hard_rock
      label: Hard rock
      image: /icons/hard_rock.png
    - id: spiky_pinecone
      label: Spiky pinecone
      image: /icons/spiky_pinecone.png
    - id: rough_bark
      label: Rough bark
      image: /icons/rough_bark.png
    - id: sharp_thorn
      label: Sharp thorn
      image: /icons/sharp_thorn.png
    - id: dry_leaf
      label: Dry crunchy leaf
      image: /icons/dry_leaf.png
    - id: smooth_pebble
      label: Smooth pebble
      image: /icons/smooth_pebble.png
    - id: stiff_branch
      label: Stiff branch
      image: /icons/stiff_branch.png
    - id: brittle_shell
      label: Brittle shell
      image: /icons/brittle_shell.png

step_instructions:
  hook:
    goal: "React with wonder to the dandelion's fluffiness — notice its white seeds like tiny parachutes, then ask the child an IMAGINATIVE question about what the seeds look like or what they might do (e.g. 'Where do you think all those tiny parachutes are going to fly to?')"
    constraint: "T0 max 2 sentences, personal feeling hook, MUST end with an imaginative question about the fluffiness"
    emotion_tag: excited
  transition:
    goal: "Build on the child's response to NATURALLY introduce the Fluffy Expedition Explorer mission — the dandelion isn't the only soft thing around! Frame the collection as an explorer adventure. Invite the child to find 3 more fluffy/fuzzy/soft things nearby. End with a genuine invitation."
    constraint: "T0 max 2 sentences, build mission from child's response (not a sudden topic switch), frame as invitation not command, end with Would you like to be the explorer?"
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Spark curiosity about finding the first fluffy item — suggest WHERE to look or WHAT to touch as an invitation, then ask the child to describe HOW it feels (fuzzy? silky? puffy?)"
      scenario: "first fluffy find"
      constraint: "T0 max 2 sentences, invitational phrasing, encourage the child to describe the texture"
      emotion_tag: encouraging
      acceptable_themes: [cloud, cotton, fur, feather, wool, moss, grass, blanket, fluffy, soft, fuzzy]
      escalation_note: "easy first find — common soft items"
    - round_number: 2
      goal: "Celebrate the previous find, then spark curiosity for the next — ask child to COMPARE how this one feels different from the first (softer? fuzzier? more like a cloud?), suggest a new place to look"
      scenario: "second fluffy find"
      constraint: "T0 max 2 sentences, invitational phrasing, encourage comparison between textures"
      emotion_tag: curious
      acceptable_themes: [pet, pillow, carpet, sweater, plush, stuffed, teddy, hair, soft, fuzzy, fluffy]
      escalation_note: "moderate — requires more exploration"
    - round_number: 3
      goal: "Guide child to find one more fluffy or soft item — the third and last one. Build excitement but remind them they still need to FIND it. Ask them to give this treasure a fun name."
      scenario: "third fluffy find"
      constraint: "T0 max 2 sentences, invitational phrasing, prompt child to go find it"
      emotion_tag: excited
      acceptable_themes: [cloud, cotton, feather, moss, flower, seed, fluffy, soft, fuzzy, fur, wool]
      escalation_note: "peak energy — but child still needs to find this item"
  celebrate:
    goal: "Award the child the title 'Fluffy Expedition Explorer' with ceremony — recap their soft discoveries. Celebrate the PROCESS of touching and feeling different textures."
    constraint: "T0 max 2 sentences, announce role title ceremonially, reference specific finds from the expedition"
    emotion_tag: proud
  closing:
    goal: "Teach the IB concept: they found soft treasures all connected by fluffiness — that's the beauty of Connection (finding how different things are linked together). Plant a curiosity seed for next time."
    constraint: "T0 max 2 sentences, name Connection naturally connected to what they discovered, warm goodbye"
    emotion_tag: warm
  synthesis:
    goal: "Look at all fluffy treasures together — guide a comparison: how does softness come in DIFFERENT forms? Fuzzy vs silky vs puffy. Invite child to give each find a fun texture name (e.g. 'cloud puff', 'fuzzy friend')."
    constraint: "T0 max 2 sentences, comparison + creative naming, frame as invitation"
    emotion_tag: amazed
  early_exit:
    goal: "Gentle goodbye — wonderful fluffy expedition, soft treasures will be waiting for their next adventure"
    constraint: "T0 max 2 sentences, no pressure to continue"
    emotion_tag: gentle

screen_frames:
  - widget: photo_display
    widget_params:
      description: "Dandelion photo centered with seeds gently floating"
    animation: sparkle_highlight
    trigger: on_enter
    sfx_cue: wonder_chime
    widget_label: "Fluffy Dandelion"
    animation_label: "Seeds floating"
  - widget: progress_tracker
    widget_params:
      filled: 1
      total: 4
    animation: card_slide_in
    trigger: on_round_1
    sfx_cue: photo_shutter_click
    widget_label: "Find 1: First Fluffy"
    animation_label: "Card slide in"
  - widget: progress_tracker
    widget_params:
      filled: 2
      total: 4
    animation: celebration_burst
    trigger: on_round_2
    sfx_cue: photo_shutter_click
    widget_label: "Find 2: More Fluff"
    animation_label: "Collection burst"
  - widget: progress_tracker
    widget_params:
      filled: 3
      total: 4
    animation: celebration_burst
    trigger: on_round_3
    sfx_cue: mission_complete_fanfare
    widget_label: "Find 3: Final Fluff"
    animation_label: "Collection burst"

celebration_frame:
  widget: badge_award
  widget_params:
    title: "Fluffy Expedition Explorer"
    concepts: [Connection]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: "Badge Earned!"
  animation_label: "Badge reveal"
---

## Fluffy Expedition Dandelion

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Type | fluffy_expedition_dandelion |
| Category | Category 5 (Out-of-Device Collection) |
| Entity | Dandelion |
| Observation Angle | Texture |
| Tier | T0 (ages 2-4) |
| IB Theme | Sharing the Planet |
| IB Concept | Connection |
| Collection Count | 3 |
| Synthesis Type | Naming Story |

### B. Activity Overview

The child becomes a Fluffy Expedition Explorer, inspired by a dandelion's soft seeds. They go on a real-world scavenger hunt to find 3 things that are fluffy, fuzzy, or soft nearby. After collecting, they compare different textures and give their finds creative names. This teaches Connection — finding how different things are linked together through shared qualities.

### C. Interaction Flow

**Hook:** "Oh wow, look at all those tiny fluffy parachutes! Where do you think they're going to fly to?"

**Transition:** "The dandelion isn't the only soft thing around! Would you like to be a Fluffy Expedition Explorer and find 3 more fluffy or fuzzy things?"

**Round 1:** "Would you like to touch things around you and feel for something soft or fuzzy? How does it feel?"

**Round 2:** "Great find! Is this one softer or fuzzier than your first treasure? Would you like to look somewhere new?"

**Round 3:** "One more fluffy treasure to find! Would you like to give this last one a fun name?"

**Synthesis:** "Look at all your fluffy treasures! How is the softness different on each one — fuzzy, silky, or puffy? Would you like to give each one a texture name?"

**Celebrate:** "You are officially a Fluffy Expedition Explorer! You found softness in moss, seeds, and petals!"

**Closing:** "You found soft treasures all connected by fluffiness — that's the beauty of Connection. Keep feeling — softness is everywhere!"
