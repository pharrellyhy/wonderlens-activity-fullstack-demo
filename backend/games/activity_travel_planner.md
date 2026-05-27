---
activity_type: activity_travel_planner
activity_set: activity_text_game
source_export_id: concept_travel_planner_predict
mechanic: predict
entity_name: travel_planner
category: category_1
display_label: Travel Planner
tier: T1
ib_theme: "Where We Are In Place And Time"
ib_key_concept: Form
concepts_earned: [Form, Causation]
keywords: [travel, plan, trip, weather, pack]
feature_keywords: [destination, bag, route, prediction]
photo_features: [travel card, route path, packing tokens]
play_rounds: 3
plain_description: "The child plans a pretend trip by predicting what they might need, what could happen, and what should come next."
steps_summary:
  - "Become a Mini Travel Planner."
  - "Choose what to pack, where to go, and what might happen."
  - "Predict how one choice changes the trip."
  - "Earn the Mini Travel Planner badge."
creative_slots:
  game_mechanic: predict
  metaphor: "A tiny travel desk where each plan choice changes the pretend route."
  role_title: Mini Travel Planner
  round_scenarios:
    - "Choose what to pack for a sunny place."
    - "Choose what to do if the weather changes."
    - "Predict what happens after one travel choice."
  escalation_axis: "simple packing to change response to cause-effect prediction"
  observation_detail: "a route card with packing and weather symbols"
step_instructions:
  hook:
    goal: "Open Travel Planner and invite the child to plan a pretend trip."
    constraint: "T1 max 3 sentences, end with a destination or packing question."
    emotion_tag: curious
  transition:
    goal: "Explain that each round makes one plan and predicts what might happen next."
    constraint: "T1 max 3 sentences, include one sample prediction."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Ask what to pack for the first pretend destination."
      scenario: "sunny place packing choice"
      constraint: "T1 max 3 sentences, invite one item and reason."
      emotion_tag: encouraging
      acceptable_themes: [pack, sun, hat, water, bag]
      escalation_note: "simple planning"
    - round_number: 2
      goal: "Ask what the traveler should do if weather changes."
      scenario: "weather change plan"
      constraint: "T1 max 3 sentences, connect choice to effect."
      emotion_tag: curious
      acceptable_themes: [rain, coat, change, plan, weather]
      escalation_note: "adaptation"
    - round_number: 3
      goal: "Ask the child to predict what happens after a travel choice."
      scenario: "next travel event prediction"
      constraint: "T1 max 3 sentences, ask for a because reason."
      emotion_tag: proud
      acceptable_themes: [next, because, trip, choose, happen]
      escalation_note: "cause and effect"
  celebrate:
    goal: "Award Mini Travel Planner and recap the plan choices."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form and Causation through trip details and choice effects."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate any travel plan."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Travel route card with bag, weather, and path icons"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Trip Map"
    animation_label: "Route appears"
  - widget: character_display
    widget_params:
      description: "Packing choice for a sunny place"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Pack"
    animation_label: "Bag glow"
  - widget: character_display
    widget_params:
      description: "Weather change plan card"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Weather"
    animation_label: "Weather shift"
  - widget: character_display
    widget_params:
      description: "Next event prediction card"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Predict"
    animation_label: "Path glow"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Mini Travel Planner
    concepts: [Form, Causation]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Travel Planner

Backend activity definition converted from `concept_travel_planner_predict`.
