---
activity_type: dream_whisperer_cat
entity_name: cat
category: category_1
display_label: Cat
tier: T0
ib_theme: "Who We Are"
ib_key_concept: Reflection
concepts_earned: [Reflection]
keywords: [cat, kitten, stuffed cat]
feature_keywords: [plush, stuffed, toy]
photo_features: [soft paws, fluffy fur, closed eyes, peaceful expression]

creative_slots:
  game_mechanic: storytelling_chain
  metaphor: "This sleepy cat is dreaming the most magical dreams!"
  role_title: Dream Whisperer
  round_scenarios:
    - floating on a cloud in the sky
    - swimming in a milk ocean
    - magical garden of favorites
  escalation_axis: familiar to fantastical
  observation_detail: "those soft little paws and fluffy fur"

step_instructions:
  hook:
    goal: "React with wonder to the sleeping cat — notice its soft paws and peaceful face, then ask the child an EMOTIONAL question about what the cat might be dreaming about (e.g. 'Do you think it's having a sweet dream right now?')"
    constraint: "T0 max 2 sentences, personal feeling hook, MUST end with an emotional question (never factual)"
    emotion_tag: excited
  transition:
    goal: "Introduce the storytelling_chain game — explain that you will set a dream scene and the child tells what the cat sees or finds. Include ONE demo round with the answer shown (e.g. 'If the cat dreamed about a garden, it might find a yarn tree!'). End with genuine invitation."
    constraint: "T0 max 3 sentences, demo round WITH answer included, end with Would you like to peek into its dreams?"
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Set the dream scene vividly: the cat's whiskers twitch — it's floating on a fluffy cloud high in the sky! Everything is soft and sparkly — then ask what the cat sees up there"
      scenario: "The cat's whiskers are twitching! It's floating on a big fluffy cloud way up in the sky!"
      constraint: "T0 max 2 sentences, paint the dream with magical sensory details, then ask what the cat sees"
      emotion_tag: dreamy
      acceptable_themes: [birds, stars, moon, sun, rainbow, sky, clouds, butterflies, flying]
      escalation_note: "familiar sky imagery — gentle start"
    - round_number: 2
      goal: "Set the dream scene vividly: the cat's paws are paddling — it's swimming in a magical warm milk ocean! Splish splash — then ask what the cat finds down there"
      scenario: "Now the cat's paws are paddling! It's swimming in a magical ocean made of warm milk! Splish splash!"
      constraint: "T0 max 2 sentences, use playful sound words, then ask what the cat discovers"
      emotion_tag: curious
      acceptable_themes: [fish, treasure, shells, pearl, seaweed, coral, mermaid, boat]
      escalation_note: "fantastical but safe — moderate imagination"
    - round_number: 3
      goal: "Set the dream scene vividly: the cat is purring SO loudly — it found a magical garden where everything is made of its favorite things! — then ask what grows in this dream garden"
      scenario: "Listen — the cat is purring so loudly! It found a magical garden where EVERYTHING is made of its favorite things!"
      constraint: "T0 max 2 sentences, build wonder and excitement, then ask what grows in the garden"
      emotion_tag: excited
      acceptable_themes: [treats, yarn, catnip, fish, toys, flowers, mice, food, tuna]
      escalation_note: "peak creativity — most fantastical round"
  celebrate:
    goal: "Award the child the title 'Dream Whisperer' with fanfare — recap the three magical dreams they peeked into (cloud sky, milk ocean, dream garden). Make the child feel like a dream expert."
    constraint: "T0 max 2 sentences, announce role title ceremonially, reference specific dreams from the game"
    emotion_tag: proud
  closing:
    goal: "Teach the IB concept: the child used their imagination to think about what someone else might feel and dream — that's the magic of Reflection (thinking about thinking). Plant a curiosity seed for next time."
    constraint: "T0 max 2 sentences, name Reflection naturally connected to what they experienced, warm goodbye"
    emotion_tag: warm
  early_exit:
    goal: "Gentle goodbye — the cat is still dreaming happily, they can peek at more dreams anytime"
    constraint: "T0 max 2 sentences, no pressure to continue"
    emotion_tag: gentle

screen_frames:
  - widget: photo_display
    widget_params:
      description: "Cat photo centered with a dreamy soft-focus glow"
    animation: sparkle_highlight
    trigger: on_enter
    sfx_cue: wonder_chime
    widget_label: "Sleepy Cat Friend"
    animation_label: "Dreamy glow"
  - widget: character_display
    widget_params:
      description: "Illustration of a cat floating on a fluffy cloud in a starry sky"
    animation: scene_transition
    trigger: on_round_1
    sfx_cue: scene_woosh
    widget_label: "Dream 1: Cloud Adventure"
    animation_label: "Scene transition"
  - widget: character_display
    widget_params:
      description: "Illustration of a cat swimming in a magical milk ocean"
    animation: scene_transition
    trigger: on_round_2
    sfx_cue: scene_woosh
    widget_label: "Dream 2: Milk Ocean"
    animation_label: "Scene transition"
  - widget: character_display
    widget_params:
      description: "Illustration of a cat in a magical garden full of treats and toys"
    animation: gentle_pulse
    trigger: on_round_3
    sfx_cue: celebration_fanfare
    widget_label: "Dream 3: Magic Garden"
    animation_label: "Gentle glow"

celebration_frame:
  widget: badge_award
  widget_params:
    title: "Dream Whisperer"
    concepts: [Reflection]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: "Badge Earned!"
  animation_label: "Badge reveal"
---

## Dream Whisperer Cat

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Type | dream_whisperer_cat |
| Category | Category 1 (In-Device Verbal) |
| Entity | Cat |
| Game Mechanic | Storytelling Chain |
| Tier | T0 (ages 2-4) |
| IB Theme | Who We Are |
| IB Concept | Reflection |

### B. Activity Overview

The child peeks into a sleeping cat's dreams through a storytelling chain game. The AI sets vivid dream scenes (floating on clouds, swimming in a milk ocean, exploring a magical garden) and the child imagines what the cat discovers in each dream. This imaginative exercise helps young children practice reflection — thinking about what someone else might experience.

### C. Interaction Flow

**Hook:** "Oh look at this sleepy cat! Those soft little paws and fluffy fur... Do you think it's having a sweet dream right now?"

**Transition:** "Would you like to peek into its dreams? I'll describe where the cat is dreaming, and you tell me what it finds! Like... if the cat dreamed about a garden, it might find a yarn tree! Would you like to peek into its dreams?"

**Round 1 (Cloud):** "The cat's whiskers are twitching! It's floating on a big fluffy cloud way up in the sky! What does the cat see up there?"

**Round 2 (Milk Ocean):** "Now the cat's paws are paddling! It's swimming in a magical ocean made of warm milk! Splish splash! What does the cat find?"

**Round 3 (Magic Garden):** "Listen — the cat is purring so loudly! It found a magical garden where EVERYTHING is made of its favorite things! What grows in this dream garden?"

**Celebrate:** "You are officially a Dream Whisperer! You peeked into cloud adventures, milk ocean swims, and a magical dream garden!"

**Closing:** "You used your imagination to think about what someone else might dream — that's the magic of Reflection. Sweet dreams, friend!"
