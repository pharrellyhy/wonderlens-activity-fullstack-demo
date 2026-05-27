---
activity_type: activity_vegetable_sort
activity_set: activity_text_game
source_export_id: concept_vegetable_sort_sort
mechanic: sort
entity_name: vegetable_sort
category: category_1
display_label: Vegetable Sort
tier: T1
ib_theme: "How We Organize Ourselves"
ib_key_concept: Form
concepts_earned: [Form]
keywords: [vegetable, sort, group, color, shape]
feature_keywords: [vegetable, category, form, rule]
photo_features: [vegetable cards, basket groups, sort rule]
play_rounds: 3
plain_description: "The child sorts vegetables by a visible or meaningful rule such as color, shape, size, or use."
steps_summary:
  - "Become a Veggie Sorter."
  - "Sort three vegetable groups by clear rules."
  - "Explain the sorting rule."
  - "Earn the Veggie Sorter badge."
creative_slots:
  game_mechanic: sort
  metaphor: "A little market table where vegetables jump into matching baskets."
  role_title: Veggie Sorter
  round_scenarios:
    - "Sort vegetables by color."
    - "Sort vegetables by shape or size."
    - "Choose the best basket rule and explain it."
  escalation_axis: "visible color to shape to child-chosen rule"
  observation_detail: "vegetable cards with clear colors and shapes"
step_instructions:
  hook:
    goal: "Open Vegetable Sort and invite the child to organize veggie cards."
    constraint: "T1 max 3 sentences, end with a sorting question."
    emotion_tag: curious
  transition:
    goal: "Explain that each round sorts by one rule and the child types the group or rule."
    constraint: "T1 max 3 sentences, include one sample basket."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Ask which vegetables belong together by color."
      scenario: "color basket sort"
      constraint: "T1 max 3 sentences, invite a short typed answer."
      emotion_tag: encouraging
      acceptable_themes: [color, green, red, yellow, basket]
      escalation_note: "color sort"
    - round_number: 2
      goal: "Ask which vegetables belong together by shape or size."
      scenario: "shape or size basket sort"
      constraint: "T1 max 3 sentences, ask for one reason."
      emotion_tag: curious
      acceptable_themes: [shape, long, round, big, small]
      escalation_note: "form comparison"
    - round_number: 3
      goal: "Ask the child to choose a sorting rule and name it."
      scenario: "child-chosen basket rule"
      constraint: "T1 max 3 sentences, accept plausible rules."
      emotion_tag: proud
      acceptable_themes: [sort, rule, basket, group, same]
      escalation_note: "child-created rule"
  celebrate:
    goal: "Award Veggie Sorter and recap the sorting rules."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form through visible vegetable features and groups."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate any sorting idea."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Market table with vegetable cards and empty baskets"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Veggie Table"
    animation_label: "Basket glow"
  - widget: character_display
    widget_params:
      description: "Vegetables sorted by color"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Color"
    animation_label: "Color sort"
  - widget: character_display
    widget_params:
      description: "Vegetables sorted by shape or size"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Shape"
    animation_label: "Shape sort"
  - widget: character_display
    widget_params:
      description: "Child chooses a basket rule"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Rule"
    animation_label: "Rule glow"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Veggie Sorter
    concepts: [Form]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Vegetable Sort

Backend activity definition converted from `concept_vegetable_sort_sort`.
