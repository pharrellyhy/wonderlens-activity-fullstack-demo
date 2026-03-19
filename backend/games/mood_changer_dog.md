---
activity_type: mood_changer_dog
entity_name: dog
category: category_1
display_label: Stuffed Dog
tier: T0
ib_theme: "Who We Are"
ib_key_concept: Perspective
concepts_earned: [Perspective]
keywords: [dog, puppy, stuffed dog, toy dog]
feature_keywords: [plush, stuffed, toy]
photo_features: [floppy ears, soft fur, cute face, fluffy body]

creative_slots:
  game_mechanic: voice_acting
  metaphor: "This fluffy dog friend has so many feelings inside!"
  role_title: Emotion Translator
  round_scenarios:
    - warm sunshine on belly
    - tripped and went bump
    - favorite treat arrives
  escalation_axis: comfortable to excited
  observation_detail: "those cute floppy ears and super soft fur"

step_instructions:
  hook:
    goal: "React with wonder to the stuffed dog — notice its soft fur and floppy ears, then ask the child an EMOTIONAL question about the dog's current mood or feelings (e.g. 'How does it look today — happy, sleepy, or a little bored?')"
    constraint: "T0 max 2 sentences, personal feeling hook, MUST end with an emotional question (never factual)"
    emotion_tag: excited
  transition:
    goal: "Introduce the voice_acting game — explain that you will describe something happening to the dog and the child says what the dog would say or feel. Include ONE demo round with the answer shown (e.g. 'If the dog's favorite ball went missing, it might sigh and say Oh no, where is my ball?'). End with a genuine invitation."
    constraint: "T0 max 3 sentences, demo round WITH answer included, end with Would you like to try?"
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Set the scene vividly: morning time, warm sunshine pouring onto the dog's belly, the dog stretches and yawns — then ask what the dog says or feels"
      scenario: "Morning! The warm sunshine lands on the doggy's belly. It stretches out with a big yawn!"
      constraint: "T0 max 2 sentences, paint the scene with sensory details, then ask what the dog would say"
      emotion_tag: warm
      acceptable_themes: [happy, cozy, warm, comfy, nice, sleepy, relaxed]
      escalation_note: "comfortable, familiar — easiest round"
    - round_number: 2
      goal: "Set the scene vividly: the dog trips and goes bump — a surprising little tumble — then ask what the dog says or does"
      scenario: "Oops! The doggy trips and goes bump on its bottom! What a surprise!"
      constraint: "T0 max 2 sentences, use onomatopoeia (bump, oops, whoa), then ask what the dog would say"
      emotion_tag: surprised
      acceptable_themes: [surprised, startled, oh no, ouch, shocked, scared, whoa]
      escalation_note: "unexpected contrast — moderate intensity"
    - round_number: 3
      goal: "Set the scene vividly: the owner brings the dog's absolute favorite treat — the dog can smell it — then ask how the dog reacts"
      scenario: "Sniff sniff! The owner brings the doggy's favorite treat! It smells SO good!"
      constraint: "T0 max 2 sentences, build excitement with sensory details (smell, wagging), then ask what the dog does"
      emotion_tag: excited
      acceptable_themes: [excited, happy, yay, wag, treats, hungry, eager, jump]
      escalation_note: "peak excitement — most energetic round"
  celebrate:
    goal: "Award the child the title 'Emotion Translator' with fanfare — recap the specific emotions explored (happy in sunshine, surprised by the bump, excited for treats). Make the child feel like a champion."
    constraint: "T0 max 2 sentences, announce role title ceremonially, reference specific moments from the game"
    emotion_tag: proud
  closing:
    goal: "Teach the IB concept: the same dog feels different things when different things happen — that's the magic of Perspective (everyone sees the world a little differently). Then plant a curiosity seed for next time."
    constraint: "T0 max 2 sentences, name Perspective naturally connected to what they experienced, warm goodbye"
    emotion_tag: warm
  early_exit:
    goal: "Gentle goodbye that validates whatever they did — they are a great friend to the dog"
    constraint: "T0 max 2 sentences, no pressure to continue"
    emotion_tag: gentle

screen_frames:
  - widget: photo_display
    widget_params:
      description: "Photo of the stuffed dog on the bed with a soft golden glow"
    animation: sparkle_highlight
    trigger: on_enter
    sfx_cue: wonder_chime
    widget_label: "Your Fluffy Friend"
    animation_label: "Sparkle highlight"
  - widget: character_display
    widget_params:
      description: "Illustration of a cozy dog napping in a sunbeam"
    animation: gentle_pulse
    trigger: on_round_1
    sfx_cue: scene_woosh
    widget_label: "Round 1: Warm Sunshine"
    animation_label: "Gentle glow"
  - widget: character_display
    widget_params:
      description: "Illustration of a dog looking surprised after a little bump"
    animation: scene_transition
    trigger: on_round_2
    sfx_cue: scene_woosh
    widget_label: "Round 2: Oops, a Bump!"
    animation_label: "Scene transition"
  - widget: character_display
    widget_params:
      description: "Illustration of a dog wagging its tail excitedly for a treat"
    animation: gentle_pulse
    trigger: on_round_3
    sfx_cue: celebration_fanfare
    widget_label: "Round 3: Treat Time!"
    animation_label: "Gentle glow"

celebration_frame:
  widget: badge_award
  widget_params:
    title: "Emotion Translator"
    concepts: [Perspective]
  animation: badge_reveal
  trigger: on_correct
  sfx_cue: badge_awarded
  widget_label: "Badge Earned!"
  animation_label: "Badge reveal"
---

## Mood Changer Dog

### A. Basic Info

| Field | Value |
|-------|-------|
| Activity Type | mood_changer_dog |
| Category | Category 1 (In-Device Verbal) |
| Entity | Stuffed Dog |
| Game Mechanic | Voice Acting |
| Tier | T0 (ages 2-4) |
| IB Theme | Who We Are |
| IB Concept | Perspective |

### B. Activity Overview

The child explores emotions through a stuffed dog's perspective. The AI presents vivid scenarios (warm sunshine, a surprise bump, a favorite treat) and the child imagines what the dog would say or feel. This voice-acting game helps young children practice perspective-taking by stepping into someone else's emotional shoes.

### C. Interaction Flow

**Hook:** "Oh wow, look at this fluffy friend! Those floppy ears and soft fur... How does the doggy look today — happy, sleepy, or a little bored?"

**Transition:** "Would you like to play a fun game? I'll tell you something that happens to the doggy, and you tell me what the doggy would say! Like... if the dog's favorite ball went missing, it might sigh and say 'Oh no, where is my ball?' Would you like to try?"

**Round 1 (Warm Sunshine):** "Morning! The warm sunshine lands on the doggy's belly. It stretches out with a big yawn! What do you think the doggy says?"

**Round 2 (Bump):** "Oops! The doggy trips and goes bump on its bottom! What a surprise! What does the doggy say?"

**Round 3 (Treat):** "Sniff sniff! The owner brings the doggy's favorite treat! It smells SO good! What does the doggy do?"

**Celebrate:** "You are officially an Emotion Translator! You helped the doggy feel cozy in the sunshine, surprised by the bump, and SO excited for that treat!"

**Closing:** "You know what? The same doggy felt so many different things — that's the magic of Perspective. See you next time, friend!"
