---
activity_type: activity_word_echo_practice
activity_set: activity_text_game
source_export_id: concept_word_echo_remember
mechanic: remember
entity_name: word_echo_practice
category: category_1
display_label: Word Echo Practice
tier: T1
ib_theme: "How We Express Ourselves"
ib_key_concept: Form
concepts_earned: [Form, Connection]
keywords: [word, echo, repeat, remember, phrase]
feature_keywords: [word card, echo, memory, repeat]
photo_features: [word card, echo token, memory trail]
play_rounds: 3
plain_description: "The AI says a simple word or phrase and the child repeats it back in a playful echo round."
steps_summary:
  - "Become an Echo Player."
  - "Echo three short word or phrase prompts."
  - "Remember the echo pattern."
  - "Earn the Echo Player badge."
creative_slots:
  game_mechanic: remember
  metaphor: "An echo trail where each repeated word lights the next step."
  role_title: Echo Player
  round_scenarios:
    - "Echo one simple word."
    - "Echo a two-word phrase."
    - "Remember and echo a favorite pair."
  escalation_axis: "single word to short phrase to remembered pair"
  observation_detail: "a word card that starts an echo trail"
step_instructions:
  hook:
    goal: "Open Word Echo Practice and invite the child into an echo trail."
    constraint: "T1 max 3 sentences, text-only, end with a readiness question."
    emotion_tag: warm
  transition:
    goal: "Explain that the AI gives a word or phrase and the child types it back."
    constraint: "T1 max 3 sentences, include one tiny demo."
    emotion_tag: playful
  rounds:
    - round_number: 1
      goal: "Give one simple word to echo."
      scenario: "first echo word"
      constraint: "T1 max 3 sentences, accept close typed repeats."
      emotion_tag: encouraging
      acceptable_themes: [echo, repeat, word, same, remember]
      escalation_note: "single word"
    - round_number: 2
      goal: "Give a short phrase to echo."
      scenario: "echo variation prompt"
      constraint: "T1 max 3 sentences, split the phrase if needed."
      emotion_tag: curious
      acceptable_themes: [phrase, echo, repeat, remember, words]
      escalation_note: "two-word phrase"
    - round_number: 3
      goal: "Ask the child to echo or recall a favorite word pair."
      scenario: "remembered echo pair"
      constraint: "T1 max 3 sentences, support partial recall."
      emotion_tag: proud
      acceptable_themes: [remember, echo, pair, favorite, words]
      escalation_note: "recall closure"
  celebrate:
    goal: "Award Echo Player and recap the echo trail."
    constraint: "T1 max 3 sentences."
    emotion_tag: proud
  closing:
    goal: "Name Form and Connection through word shapes and repeated links."
    constraint: "T1 max 3 sentences, warm goodbye."
    emotion_tag: warm
  early_exit:
    goal: "Gently close and validate any echo attempt."
    constraint: "T1 max 3 sentences, no pressure."
    emotion_tag: gentle
screen_frames:
  - widget: photo_display
    widget_params:
      description: "Word echo card with three empty trail lights"
    animation: sparkle_highlight
    trigger: on_enter
    widget_label: "Echo Trail"
    animation_label: "Trail lights"
  - widget: character_display
    widget_params:
      description: "Single word echo card"
    animation: gentle_pulse
    trigger: on_round_1
    widget_label: "Word"
    animation_label: "First echo"
  - widget: character_display
    widget_params:
      description: "Two-word phrase echo card"
    animation: scene_transition
    trigger: on_round_2
    widget_label: "Phrase"
    animation_label: "Phrase echo"
  - widget: character_display
    widget_params:
      description: "Remembered word pair card"
    animation: gentle_pulse
    trigger: on_round_3
    widget_label: "Recall"
    animation_label: "Recall glow"
celebration_frame:
  widget: badge_award
  widget_params:
    title: Echo Player
    concepts: [Form, Connection]
  animation: badge_reveal
  trigger: on_correct
  widget_label: "Badge Earned"
  animation_label: "Badge reveal"
---

## Word Echo Practice

Backend activity definition converted from `concept_word_echo_remember`.
