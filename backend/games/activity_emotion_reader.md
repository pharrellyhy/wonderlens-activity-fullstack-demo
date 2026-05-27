---
activity_type: activity_emotion_reader
activity_set: activity_text_game
source_export_id: concept_emotion_reader_care
mechanic: care
entity_name: emotion_reader
category: category_1
display_label: Emotion Reader
tier: T1
ib_theme: "Who We Are"
ib_key_concept: Form
concepts_earned: [Form, Responsibility]
keywords: [emotion, feeling, face, body, help]
feature_keywords: [expression, feeling, cue, caring]
photo_features: [face card, body cue, feeling token]
play_rounds: 3
plain_description: "The child notices an obvious expression or body cue and thinks about what feeling or help might fit."
steps_summary:
  - "Become a Feeling Helper."
  - "Read three simple feeling cues."
  - "Choose kind responses that fit."
  - "Earn the Feeling Helper badge."
creative_slots:
  game_mechanic: care
  metaphor: "A caring station where visible cues help the child choose kind actions."
  role_title: Feeling Helper
  round_scenarios:
    - "A character shows one obvious feeling cue."
    - "A second cue changes what help might fit."
    - "The child chooses a kind response for the feeling."
  escalation_axis: "notice cue to infer feeling to choose help"
  observation_detail: "a visible face or body cue"
step_instructions:
  hook:
    goal: "Open Emotion Reader and invite the child to notice a feeling cue."
    constraint: "T1 max 3 sentences, nonjudgmental, end with a question."
    emotion_tag: gentle
  transition:
    goal: "Explain that each round notices a cue, names a feeling, and chooses kind help."
    constraint: "T1 max 3 sentences, include one caring demo."
    emotion_tag: warm
  rounds:
    - round_number: 1
      goal: "Ask what feeling might match one visible cue."
      scenario: "visible face or body cue"
      constraint: "T1 max 3 sentences, offer two feeling choices if useful."
      emotion_tag: curious
      acceptable_themes: [happy, sad, scared, tired, feeling]
      escalation_note: "name a feeling"
    - round_number: 2
      goal: "Ask what help could fit a second feeling cue."
      scenario: "possible feeling cue"
      constraint: "T1 max 3 sentences, keep help gentle and realistic."
      emotion_tag: warm
      acceptable_themes: [help, kind, ask, hug, rest]
      escalation_note: "connect cue to need"
    - round_number: 3
      goal: "Ask the child to choose a kind response."
      scenario: "kind help choice"
      constraint: "T1 max 3 sentences, praise caring reasoning."
      emotion_tag: proud
      acceptable_themes: [care, help, feeling, kind, responsible]
      escalation_note: "responsible action"
  celebrate:
    goal: "Award Feeling Helper and recap the kind choices."
    constraint: "T1 max 3 sentences, do not judge emotions as right or wrong."
    emotion_tag: proud
  closing:
    goal: "Name Form and Responsibility through visible cues and caring choices."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate noticing feelings."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Feeling card with one clear expression cue"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Feeling Cue"
    animation_label: "Cue glow"
  - widget: character_display
    widget_params:
      description: "First expression or body cue"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Notice"
    animation_label: "Cue pulse"
  - widget: character_display
    widget_params:
      description: "Second feeling cue with help choices"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Feeling"
    animation_label: "Help choices"
  - widget: character_display
    widget_params:
      description: "Kind response card"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Help"
    animation_label: "Kind glow"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Feeling Helper
    concepts: [Form, Responsibility]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Emotion Reader

Backend activity definition converted from `concept_emotion_reader_care`.
