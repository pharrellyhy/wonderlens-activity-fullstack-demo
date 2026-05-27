---
activity_type: activity_constellation_star_count
activity_set: activity_text_game
source_export_id: concept_constellation_star_count_enumerate
mechanic: enumerate
entity_name: constellation_star_count
category: category_1
display_label: Constellation Star Count
tier: T1
ib_theme: "How The World Works"
ib_key_concept: Form
concepts_earned: [Form]
keywords: [constellation, star, count, sky, pattern]
feature_keywords: [stars, number, pattern, group]
photo_features: [star card, constellation dots, counting path]
play_rounds: 3
plain_description: "The screen shows a small constellation or star group, and the child counts how many stars are visible."
steps_summary:
  - "Become a Star Counter."
  - "Count three star groups."
  - "Compare how star forms make different patterns."
  - "Earn the Star Counter badge."
creative_slots:
  game_mechanic: enumerate
  metaphor: "A small night-sky map where each counted star lights a path."
  role_title: Star Counter
  round_scenarios:
    - "Count a small group of stars."
    - "Count a second group with a different shape."
    - "Count a final constellation and compare the pattern."
  escalation_axis: "small group to changed pattern to final count"
  observation_detail: "visible star dots arranged in a pattern"
step_instructions:
  hook:
    goal: "Open Constellation Star Count and invite the child to count visible stars."
    constraint: "T1 max 3 sentences, end with a counting question."
    emotion_tag: curious
  transition:
    goal: "Explain that each round asks for a typed number and a quick look at the star shape."
    constraint: "T1 max 3 sentences, include one tiny example."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Ask the child to count the first small star group."
      scenario: "first star group"
      constraint: "T1 max 3 sentences, invite a number answer."
      emotion_tag: encouraging
      acceptable_themes: [one, two, three, count, stars]
      escalation_note: "small count"
    - round_number: 2
      goal: "Ask the child to count a changed star pattern."
      scenario: "second star pattern"
      constraint: "T1 max 3 sentences, connect count to pattern."
      emotion_tag: curious
      acceptable_themes: [count, stars, pattern, more, less]
      escalation_note: "changed arrangement"
    - round_number: 3
      goal: "Ask for the final count and a short comparison."
      scenario: "final constellation count"
      constraint: "T1 max 3 sentences, ask which group looked bigger or smaller."
      emotion_tag: proud
      acceptable_themes: [count, final, pattern, bigger, smaller]
      escalation_note: "count plus comparison"
  celebrate:
    goal: "Award Star Counter and recap the counted groups."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form through star groups, numbers, and pattern shapes."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate any counting attempt."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Night-sky card with a small constellation"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Star Map"
    animation_label: "Stars sparkle"
  - widget: character_display
    widget_params:
      description: "First small star group"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Count 1"
    animation_label: "First stars"
  - widget: character_display
    widget_params:
      description: "Second star group in a new shape"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Count 2"
    animation_label: "Pattern shift"
  - widget: character_display
    widget_params:
      description: "Final constellation count"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Final Count"
    animation_label: "Final stars"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Star Counter
    concepts: [Form]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Constellation Star Count

Backend activity definition converted from `concept_constellation_star_count_enumerate`.
