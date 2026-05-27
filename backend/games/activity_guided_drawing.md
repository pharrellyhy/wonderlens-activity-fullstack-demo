---
activity_type: activity_guided_drawing
activity_set: activity_text_game
source_export_id: concept_guided_drawing_probe
mechanic: build
entity_name: guided_drawing
category: category_3
display_label: Guided Drawing
tier: T1
ib_theme: "How We Express Ourselves"
ib_key_concept: Form
concepts_earned: [Form, Change]
keywords: [guided drawing, drawing, pencil, paper, build, create]
feature_keywords: [line, shape, detail, drawing]
photo_features: [paper, pencil, simple lines, visible shape]
play_rounds: 3
plain_description: "The AI guides the child to use paper and pencil to complete a simple drawing step by step."
steps_summary:
  - "Set up paper and pencil for a guided drawing."
  - "Add a first line or shape, then report what changed."
  - "Add a second detail and a final finishing choice."
  - "Earn the Guided Artist badge."

creative_slots:
  game_mechanic: build
  metaphor: "The child becomes a Guided Artist who grows a drawing one small step at a time."
  role_title: Guided Artist
  build_materials: [paper, pencil]
  build_steps:
    - "Draw one simple line or shape to start the picture."
    - "Add one small detail that changes what the picture could become."
    - "Choose one finishing mark and describe the finished drawing."
  escalation_axis: "single mark to changed drawing to finished recap"
  observation_detail: "a first line or shape that can change into a drawing"

step_instructions:
  hook:
    goal: "Open Guided Drawing, name the child as a Guided Artist, and invite them to make one small drawing step."
    constraint: "T1 max 3 sentences, text-only, do not claim to see the paper, end with an invitation."
    emotion_tag: curious
  transition:
    goal: "Explain the loop: I give a small drawing step, the child tries it, then types what they did."
    constraint: "T1 max 3 sentences, mention paper and pencil, do not ask for a photo, end by asking if they are ready."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Ask the child to draw one simple line or shape and type what they added."
      scenario: "first line or shape"
      constraint: "T1 max 3 sentences, one small action, no visual assessment."
      emotion_tag: encouraging
      acceptable_themes: [line, circle, square, mark, shape, start]
      escalation_note: "easy first mark"
    - round_number: 2
      goal: "Ask the child to add one detail that changes what the drawing could become."
      scenario: "second guided detail"
      constraint: "T1 max 3 sentences, connect the detail to change, ask for a typed report."
      emotion_tag: curious
      acceptable_themes: [detail, eyes, legs, roof, leaf, change]
      escalation_note: "adds meaning or transformation"
    - round_number: 3
      goal: "Ask the child to add one finishing mark and describe the finished drawing."
      scenario: "finished drawing recap"
      constraint: "T1 max 3 sentences, recap sequence, ask for a short description."
      emotion_tag: proud
      acceptable_themes: [finished, done, drawing, picture, made, changed]
      escalation_note: "closure and reflection"
  celebrate:
    goal: "Award the Guided Artist title and recap the reported drawing sequence."
    constraint: "T1 max 3 sentences, reference reported steps, no visual inspection claims."
    emotion_tag: proud
  closing:
    goal: "Name Form and Change, connecting them to how small marks changed the drawing."
    constraint: "T1 max 3 sentences, warm goodbye, suggest a next guided drawing."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate any drawing effort the child reported."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle

screen_frames:
  - widget: photo_display
    widget_params:
      description: "Guided drawing setup with paper and pencil"
      entity: guided_drawing
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Guided Drawing"
    animation_label: "Ready to draw"
  - widget: character_display
    widget_params:
      description: "A first line or simple shape begins the drawing"
      entity: guided_drawing
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Round 1: First Mark"
    animation_label: "First mark"
  - widget: character_display
    widget_params:
      description: "A small detail changes what the drawing could become"
      entity: guided_drawing
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Round 2: Change It"
    animation_label: "Drawing changes"
  - widget: character_display
    widget_params:
      description: "A finishing mark completes the guided drawing"
      entity: guided_drawing
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Round 3: Finish"
    animation_label: "Finished drawing"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Guided Artist
    concepts: [Form, Change]
    entity: guided_drawing
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Guided Drawing

Backend activity definition converted from `concept_guided_drawing_probe`.
