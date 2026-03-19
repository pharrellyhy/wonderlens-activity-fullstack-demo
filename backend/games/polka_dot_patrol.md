---
activity_type: polka_dot_patrol
entity_name: ladybug
category: category_5
display_label: Ladybug
tier: T1
ib_theme: "How We Express Ourselves"
ib_key_concept: Form
concepts_earned: [Form, Connection]
keywords: [ladybug, ladybird, beetle]
feature_keywords: [spot, dot, polka]
photo_features: [red shell, black polka dots, tiny legs, small antennae]

creative_slots:
  observation_angle: pattern
  collection_criterion: "Find things with dots, spots, or circles"
  collection_count: 3
  mission_metaphor: "You are a Polka-Dot Patrol Officer!"
  role_title: Polka-Dot Patrol Officer
  synthesis_type: comparison_chart
  stuck_hint: "Try looking at flowers up close, or at the ground near your feet"
  naming_prompt: "What kind of dots or spots do you see on this?"

collection_catalog:
  correct:
    - id: spotted_mushroom
      label: Spotted mushroom
      image: /icons/spotted_mushroom.png
    - id: dotted_pebble
      label: Dotted pebble
      image: /icons/dotted_pebble.png
    - id: speckled_leaf
      label: Speckled leaf
      image: /icons/speckled_leaf.png
    - id: circle_flower
      label: Flower with circles
      image: /icons/circle_flower.png
  distractors:
    - id: straight_stick
      label: Straight stick
      image: /icons/straight_stick.png
    - id: plain_bark
      label: Plain bark
      image: /icons/plain_bark.png
    - id: long_grass
      label: Long grass blade
      image: /icons/long_grass.png
    - id: smooth_stone
      label: Smooth stone
      image: /icons/smooth_stone.png
    - id: pine_needle
      label: Pine needles
      image: /icons/pine_needle.png
    - id: plain_leaf
      label: Plain leaf
      image: /icons/plain_leaf.png
    - id: forked_twig
      label: Forked twig
      image: /icons/forked_twig.png
    - id: acorn_cap
      label: Acorn cap
      image: /icons/acorn_cap.png

step_instructions:
  hook:
    goal: "React with wonder to the ladybug's spots — notice its red coat with black polka dots, then ask the child an IMAGINATIVE question about what the dots look like or remind them of (e.g. 'Do you think those dots are like little buttons, or maybe tiny windows?')"
    constraint: "T1 max 3 sentences, experience/preference hook, MUST end with an imaginative question about the dots"
    emotion_tag: excited
  transition:
    goal: "Build on the child's response to NATURALLY introduce the Polka-Dot Patrol Officer mission — the ladybug isn't the only spotty thing around! Frame the collection as a detective adventure: find 3 more things with dots/spots/circles nearby. Use a narrative metaphor (patrol, detective, treasure hunt). End with a genuine invitation."
    constraint: "T1 max 3 sentences, build mission from child's response (not a sudden topic switch), frame as invitation not command, end with Would you like to be the Patrol Officer?"
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Spark curiosity about finding the first spotted item — suggest WHERE to look (flowers up close, ground near feet) as an invitation, then ask the child to NAME or describe what they find"
      scenario: "first collection find — spots or dots"
      constraint: "T1 max 3 sentences, invitational phrasing, encourage the child to describe or name the find"
      emotion_tag: encouraging
      acceptable_themes: [flower, dots, spots, petals, pattern, circles]
      escalation_note: "easy first find — accessible items"
    - round_number: 2
      goal: "Celebrate the previous find, then spark curiosity for the next — ask child to COMPARE this find to the first one (bigger dots? tinier speckles?), suggest a new place to look"
      scenario: "second collection find — speckles or spots"
      constraint: "T1 max 3 sentences, invitational phrasing, encourage comparison between finds"
      emotion_tag: curious
      acceptable_themes: [rock, spots, speckles, stone, bark, dots, pattern]
      escalation_note: "moderate — requires more looking"
    - round_number: 3
      goal: "Guide child to find one more spotted item — the third and last one. Build excitement but remind them they still need to FIND it. Ask them to name this final treasure."
      scenario: "third collection find"
      constraint: "T1 max 3 sentences, invitational phrasing, prompt child to go find it"
      emotion_tag: excited
      acceptable_themes: [tree, bark, butterfly, dots, spots, leaf, pattern, bug]
      escalation_note: "peak energy — but child still needs to find this item"
  celebrate:
    goal: "Award the child the title 'Polka-Dot Patrol Officer' with ceremony — recap their spotted discoveries. Celebrate the PROCESS of looking closely and finding patterns everywhere."
    constraint: "T1 max 3 sentences, announce role title ceremonially, reference specific finds from the patrol"
    emotion_tag: proud
  closing:
    goal: "Teach the IB concepts: they noticed the beautiful Form of spots/patterns everywhere, and found a surprising Connection between all these different spotted things. Plant a curiosity seed for next time."
    constraint: "T1 max 3 sentences, name Form and Connection naturally connected to what they discovered, warm goodbye"
    emotion_tag: warm
  synthesis:
    goal: "Look at all spotted treasures together — guide a comparison: how is the SAME pattern (dots/spots) DIFFERENT on each item? Big dots vs tiny speckles vs round circles. Invite child to give each find a fun name (e.g. 'freckle stone', 'polka petal')."
    constraint: "T1 max 3 sentences, comparison + creative naming, frame as invitation"
    emotion_tag: amazed
  early_exit:
    goal: "Gentle goodbye — great patrol work, the polka dots will be waiting next time"
    constraint: "T1 max 3 sentences, no pressure to continue"
    emotion_tag: gentle

screen_frames:
  - widget: photo_display
    widget_params:
      description: "Ladybug photo centered with spots gently highlighted"
    animation: sparkle_highlight
    trigger: on_enter
    sfx_cue: wonder_chime
    widget_label: "Spotted Friend"
    animation_label: "Sparkle highlight"
  - widget: progress_tracker
    widget_params:
      filled: 1
      total: 4
    animation: card_slide_in
    trigger: on_round_1
    sfx_cue: photo_shutter_click
    widget_label: "Find 1: First Spots"
    animation_label: "Card slide in"
  - widget: progress_tracker
    widget_params:
      filled: 2
      total: 4
    animation: celebration_burst
    trigger: on_round_2
    sfx_cue: photo_shutter_click
    widget_label: "Find 2: More Spots"
    animation_label: "Collection burst"
  - widget: progress_tracker
    widget_params:
      filled: 3
      total: 4
    animation: celebration_burst
    trigger: on_round_3
    sfx_cue: mission_complete_fanfare
    widget_label: "Find 3: Final Spots"
    animation_label: "Collection burst"

celebration_frame:
  widget: badge_award
  widget_params:
    title: "Polka-Dot Patrol Officer"
    concepts: [Form, Connection]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: "Badge Earned!"
  animation_label: "Badge reveal"
---

## Polka Dot Patrol

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Type | polka_dot_patrol |
| Category | Category 5 (Out-of-Device Collection) |
| Entity | Ladybug |
| Observation Angle | Pattern |
| Tier | T1 (ages 4-6) |
| IB Theme | How We Express Ourselves |
| IB Concept | Form |
| Collection Count | 3 |
| Synthesis Type | Comparison Chart |

### B. Activity Overview

The child becomes a Polka-Dot Patrol Officer, inspired by a ladybug's spots. They go on a real-world scavenger hunt to find 3 things with dots, spots, or circles nearby. After collecting, they compare how the same pattern (dots) appears differently on each item and give their finds creative names. This teaches Form (noticing visual patterns) and Connection (finding links between different objects).

### C. Interaction Flow

**Hook:** "Wow, look at those amazing polka dots! Do you think those dots are like little buttons, or maybe tiny windows?"

**Transition:** "The ladybug isn't the only spotty thing around! Would you like to be a Polka-Dot Patrol Officer and find 3 more things with dots or spots?"

**Round 1:** "Would you like to look at the flowers up close, or maybe check the ground near your feet? Can you find something with dots or spots?"

**Round 2:** "Amazing find! Now, are the dots on this one bigger or tinier than your first find? Would you like to look somewhere new?"

**Round 3:** "One more to find! Would you like to check the trees or the path? What does your final spotted treasure look like?"

**Synthesis:** "Look at all your spotted treasures together! How are the dots different on each one? Would you like to give each one a fun name?"

**Celebrate:** "You are officially a Polka-Dot Patrol Officer! You found spots everywhere — on flowers, stones, and leaves!"

**Closing:** "You noticed the beautiful Form of spots and patterns everywhere, and found a surprising Connection between all these different things. Keep looking — dots are everywhere!"
