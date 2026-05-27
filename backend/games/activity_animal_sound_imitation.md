---
activity_type: activity_animal_sound_imitation
activity_set: activity_text_game
source_export_id: concept_animal_sound_motion_voice
mechanic: motion_voice
entity_name: animal_sound_imitation
category: category_1
display_label: Animal Sound Imitation
tier: T1
ib_theme: "How We Express Ourselves"
ib_key_concept: Form
concepts_earned: [Form, Perspective]
keywords: [animal, sound, imitate, voice, role]
feature_keywords: [animal card, voice, motion, safe]
photo_features: [animal picture, sound cue, performance card]
play_rounds: 3
plain_description: "The AI prompts a familiar animal, and the child imitates its sound or speaks in the animal role."
steps_summary:
  - "Become an Animal Voice Performer."
  - "Try three safe animal voice or role prompts."
  - "Choose a favorite performance moment."
  - "Earn the Animal Voice Performer badge."
creative_slots:
  game_mechanic: motion_voice
  metaphor: "A tiny animal stage where the child can try safe voices and roles."
  role_title: Animal Voice Performer
  round_scenarios:
    - "Try a gentle animal sound."
    - "Change the sound with a new volume or feeling."
    - "Speak one short line in the animal role."
  escalation_axis: "simple sound to variation to role line"
  observation_detail: "an animal cue that suggests a sound or point of view"
step_instructions:
  hook:
    goal: "Open Animal Sound Imitation and invite a safe animal voice performance."
    constraint: "T1 max 3 sentences, remind safe volume, end with a question."
    emotion_tag: playful
  transition:
    goal: "Explain that each round is a small safe voice or role try."
    constraint: "T1 max 3 sentences, give a tiny demo and invite readiness."
    emotion_tag: excited
  rounds:
    - round_number: 1
      goal: "Ask for a gentle animal sound."
      scenario: "first animal voice"
      constraint: "T1 max 3 sentences, encourage safe volume."
      emotion_tag: encouraging
      acceptable_themes: [animal, sound, gentle, voice, safe]
      escalation_note: "simple performance"
    - round_number: 2
      goal: "Ask for the same animal sound with one feeling or volume change."
      scenario: "changed animal voice or volume"
      constraint: "T1 max 3 sentences, keep movement and volume safe."
      emotion_tag: curious
      acceptable_themes: [loud, soft, happy, sleepy, voice]
      escalation_note: "performance variation"
    - round_number: 3
      goal: "Ask for one short line spoken as the animal."
      scenario: "favorite animal-role line"
      constraint: "T1 max 3 sentences, ask for a short typed or spoken-style response."
      emotion_tag: proud
      acceptable_themes: [animal, says, role, line, favorite]
      escalation_note: "role perspective"
  celebrate:
    goal: "Award Animal Voice Performer and recap the safest favorite moment."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form and Perspective through animal features and role voice."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate the child trying a safe voice."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Animal stage card with sound tokens"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Animal Stage"
    animation_label: "Stage opens"
  - widget: character_display
    widget_params:
      description: "Gentle animal sound cue"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Voice 1"
    animation_label: "Sound pulse"
  - widget: character_display
    widget_params:
      description: "Animal voice changes feeling or volume"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Voice 2"
    animation_label: "Voice shift"
  - widget: character_display
    widget_params:
      description: "Animal role line spotlight"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Role Line"
    animation_label: "Spotlight"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Animal Voice Performer
    concepts: [Form, Perspective]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Animal Sound Imitation

Backend activity definition converted from `concept_animal_sound_motion_voice`.
