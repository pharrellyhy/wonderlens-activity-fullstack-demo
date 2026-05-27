---
activity_type: activity_partial_reveal_guess
activity_set: activity_text_game
source_export_id: concept_partial_reveal_deduce
mechanic: deduce
entity_name: partial_reveal_guess
category: category_1
display_label: Partial Reveal Guess
tier: T1
ib_theme: "How We Express Ourselves"
ib_key_concept: Form
concepts_earned: [Form, Causation]
keywords: [partial, reveal, clue, guess, object]
feature_keywords: [part, whole, clue, evidence]
photo_features: [hidden picture, visible clue, reveal card]
play_rounds: 3
plain_description: "The screen shows one distinctive part of an animal or object, and the child guesses the whole thing from visible clues."
steps_summary:
  - "Become a Picture Clue Detective."
  - "Make three clue-based guesses as more evidence appears."
  - "Reveal how the clues caused the final answer."
  - "Earn the Picture Clue Detective badge."
creative_slots:
  game_mechanic: deduce
  metaphor: "A mystery lens reveals small clues before the whole picture."
  role_title: Picture Clue Detective
  round_scenarios:
    - "A first visible clue peeks out from a hidden picture."
    - "A second clue appears and changes the best guess."
    - "The whole object is nearly revealed for a final answer."
  escalation_axis: "single clue to added evidence to final reveal"
  observation_detail: "a distinctive visible part that hints at the whole"
step_instructions:
  hook:
    goal: "Open Partial Reveal Guess and invite the child to become a Picture Clue Detective."
    constraint: "T1 max 3 sentences, text-only, end with a question."
    emotion_tag: curious
  transition:
    goal: "Explain that each round uses one clue to make or revise a guess."
    constraint: "T1 max 3 sentences, include one tiny demo guess."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Present one clue and ask for a maybe-guess."
      scenario: "first visible clue"
      constraint: "T1 max 3 sentences, ask what the clue could belong to."
      emotion_tag: curious
      acceptable_themes: [guess, clue, maybe, part, evidence]
      escalation_note: "first clue"
    - round_number: 2
      goal: "Add a second clue and ask whether the guess changes."
      scenario: "second revealed clue"
      constraint: "T1 max 3 sentences, connect evidence to the changed guess."
      emotion_tag: surprised
      acceptable_themes: [change, clue, evidence, maybe, guess]
      escalation_note: "guess revision"
    - round_number: 3
      goal: "Invite the final whole-object guess."
      scenario: "final whole-object guess"
      constraint: "T1 max 3 sentences, ask for a final answer and one reason."
      emotion_tag: proud
      acceptable_themes: [answer, whole, clue, reason, reveal]
      escalation_note: "final deduction"
  celebrate:
    goal: "Reveal the answer and award Picture Clue Detective."
    constraint: "T1 max 3 sentences, recap how clues caused the guess."
    emotion_tag: proud
  closing:
    goal: "Name Form and Causation through visible parts and evidence changing guesses."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and praise clue thinking."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
screen_frames:
  - widget: photo_display
    widget_params:
      description: "A mystery card with one partial clue visible"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Mystery Clue"
    animation_label: "Clue appears"
  - widget: character_display
    widget_params:
      description: "First partial clue on a hidden picture"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Clue 1"
    animation_label: "First clue"
  - widget: character_display
    widget_params:
      description: "Second clue added beside the first"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Clue 2"
    animation_label: "More evidence"
  - widget: character_display
    widget_params:
      description: "Final reveal card ready for a whole-object guess"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Final Guess"
    animation_label: "Reveal glow"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Picture Clue Detective
    concepts: [Form, Causation]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Partial Reveal Guess

Backend activity definition converted from `concept_partial_reveal_deduce`.
