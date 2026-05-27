---
activity_type: activity_recognition_pop_challenge
activity_set: activity_text_game
source_export_id: concept_recognition_pop_probe
mechanic: compare
entity_name: recognition_pop_challenge
category: category_1
display_label: Recognition Pop Challenge
tier: T1
ib_theme: "How We Express Ourselves"
ib_key_concept: Form
concepts_earned: [Form, Perspective]
keywords: [recognition, match, compare, picture, pop]
feature_keywords: [target, match, different, same]
photo_features: [target card, pop choices, match token]
play_rounds: 3
plain_description: "The child quickly chooses or names the picture that matches a target from a changing set."
steps_summary:
  - "Become a Match Spotter."
  - "Compare three changing target sets."
  - "Explain what looked the same or different."
  - "Earn the Match Spotter badge."
creative_slots:
  game_mechanic: compare
  metaphor: "A pop board where target pictures appear and the child spots the best match."
  role_title: Match Spotter
  round_scenarios:
    - "Find the choice that matches the first target."
    - "Compare two similar choices and pick the best match."
    - "Explain what made the final match the same."
  escalation_axis: "obvious match to close comparison to reasoned match"
  observation_detail: "a target picture beside changing choices"
step_instructions:
  hook:
    goal: "Open Recognition Pop Challenge and invite the child to spot matching forms."
    constraint: "T1 max 3 sentences, end with a match question."
    emotion_tag: curious
  transition:
    goal: "Explain that each round shows a target and asks which choice matches best."
    constraint: "T1 max 3 sentences, include one simple same-or-different example."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Ask which choice matches the first target."
      scenario: "first target match"
      constraint: "T1 max 3 sentences, accept typed labels or descriptions."
      emotion_tag: encouraging
      acceptable_themes: [same, match, target, picture, choice]
      escalation_note: "obvious match"
    - round_number: 2
      goal: "Ask the child to compare two similar choices."
      scenario: "close match comparison"
      constraint: "T1 max 3 sentences, ask what is same or different."
      emotion_tag: curious
      acceptable_themes: [same, different, compare, match, close]
      escalation_note: "similar distractor"
    - round_number: 3
      goal: "Ask for the final match and one reason."
      scenario: "final match reason"
      constraint: "T1 max 3 sentences, connect reason to visible form."
      emotion_tag: proud
      acceptable_themes: [reason, form, same, match, target]
      escalation_note: "reasoned comparison"
  celebrate:
    goal: "Award Match Spotter and recap the comparison clues."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form and Perspective through matching, comparing, and noticing."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate any matching attempt."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Pop board with a target picture and match slots"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Pop Board"
    animation_label: "Target appears"
  - widget: character_display
    widget_params:
      description: "First target and matching choice"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Match 1"
    animation_label: "First pop"
  - widget: character_display
    widget_params:
      description: "Two similar choices beside the target"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Compare"
    animation_label: "Choices pop"
  - widget: character_display
    widget_params:
      description: "Final target match with reason prompt"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Reason"
    animation_label: "Final pop"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Match Spotter
    concepts: [Form, Perspective]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Recognition Pop Challenge

Backend activity definition converted from `concept_recognition_pop_probe`.
